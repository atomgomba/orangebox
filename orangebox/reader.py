# Orangebox - Cleanflight/Betaflight blackbox data parser.
# Copyright (C) 2019  Károly Kiripolszky
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging
from typing import BinaryIO, Dict, Iterator, List, Optional

from .decoders import decoder_map
from .defaults import HeaderDefaults
from .errors import InvalidHeaderException
from .predictors import predictor_map
from .tools import _is_ascii, _trycast
from .types import FieldDef, FrameType, Headers

MAX_FRAME_SIZE = 256

_log = logging.getLogger(__name__)


class Reader:
    """Implements a file-like object for reading a flight log and store the raw data in a structured way. Does not do
    any real parsing, the iterator just yields bytes.
    """

    def __init__(self,
                 path: str,
                 log_index: Optional[int] = None,
                 allow_invalid_header: bool = False):
        """
        :param path: Path to a log file
        :param log_index: Session index within log file. If set to `None` (the default) there will be no session selected and headers and frame data won't be read until the first call to `.set_log_index()`.
        :param allow_invalid_header: Allow skipping of badly formatted headers
        """
        self._headers = {}  # type: Headers
        self._field_defs = {}  # type: Dict[FrameType, List[FieldDef]]
        self._log_index = 0
        self._header_size = 0
        self._path = path
        _log.info("Processing: " + path)
        self._frame_data_ptr = 0
        self._log_pointers = []  # type: List[int]
        self._frame_data = b''
        self._frame_data_len = 0
        self._allow_invalid_header = allow_invalid_header
        with open(path, "rb") as f:
            if not f.seekable():
                msg = "Input file must be seekable"
                _log.critical(msg)
                raise IOError(msg)
            self._find_pointers(f)
        if log_index is not None:
            self.set_log_index(log_index)

    def set_log_index(self, index: int):
        """Set the current log index and read its corresponding frame data as raw bytes, plus parse the raw headers of
        the selected log.

        :param index: The selected log index
        :raise RuntimeError: If ``index`` is smaller than 1 or greater than `.log_count`
        """
        if index == self._log_index:
            return
        if index < 1 or self.log_count < index:
            raise RuntimeError("Invalid log_index: {:d} (1 <= x < {:d})".format(index, self.log_count))
        start = self._log_pointers[index - 1]
        with open(self._path, "rb") as f:
            f.seek(start)
            self._update_headers(f)
            f.seek(start + self._header_size)
            size = self._log_pointers[index] - start - self._header_size if index < self.log_count else None
            self._frame_data = f.read(size) if size is not None else f.read()
        self._log_index = index
        self._frame_data_ptr = 0
        self._frame_data_len = len(self._frame_data)
        self._build_field_defs()
        _log.info("Log #{:d} out of {:d} (start: 0x{:X}, size: {:d})"
                  .format(self._log_index, self.log_count, start, self._frame_data_len))

    def _update_headers(self, f: BinaryIO):
        start = f.tell()
        while True:
            line = self._read_header_line(f)
            has_next = self._parse_header_line(line)
            if not has_next:
                _log.debug(
                    "End of headers at {0:d} (0x{0:X}) (headers: {1:d})".format(f.tell(), len(self._headers.keys())))
                HeaderDefaults.inspect(self._headers)
                break
        self._header_size = f.tell() - start

    def _read_header_line(self, f: BinaryIO) -> Optional[bytes]:
        """Read the next header line up to a linefeed or invalid character.
        """
        result = bytes()
        while True:
            byte = f.read(1)
            if not byte:
                return result
            elif byte == b'I' and len(result) == 0:
                f.seek(-1, 1)
                return None
            elif byte == b'\n':
                return result + b'\n'
            elif not _is_ascii(byte) and result.startswith(b'H'):
                if self._allow_invalid_header:
                    _log.warning(f"Invalid byte in header: {byte} (read: {result})")
                    invalid_part = len(result) - result.find(b'I') + 1
                    f.seek(-invalid_part, 1)
                    return None
                else:
                    raise InvalidHeaderException(result, f.tell())
            result += byte

    def _parse_header_line(self, data: Optional[bytes]) -> bool:
        """Parse a header line and return `False` if it's invalid.
        """
        if not data or data[0] != 72:  # 72 == ord('H')
            # not a header line
            return False
        line = data.decode().replace("H ", "", 1)
        try:
            name, value = line.split(':', 1)
        except ValueError:
            _log.warning(f"Header line has invalid format: '{line}'")
            return False
        self._headers[name.strip()] = [_trycast(s.strip()) for s in value.split(',')] if ',' in value \
            else _trycast(value.strip())
        return True

    def _find_pointers(self, f: BinaryIO):
        start = f.tell()
        first_line = f.readline()
        f.seek(start)
        content = f.read()
        new_index = content.find(first_line)
        step = len(first_line)
        while -1 < new_index:
            self._log_pointers.append(new_index)
            new_index = content.find(first_line, new_index + step + 1)

    def _build_field_defs(self):
        """Use the read headers to populate the `field_defs` property.
        """
        headers = self._headers
        field_defs = self._field_defs
        predictors = predictor_map
        decoders = decoder_map
        for frame_type in FrameType:
            # field header format: 'Field <FrameType> <Property>'
            for header_key, header_value in headers.items():
                if "Field " + frame_type.value not in header_key:
                    # skip headers unrelated to defining fields
                    continue
                if frame_type not in field_defs:
                    field_defs[frame_type] = [FieldDef(frame_type) for _ in range(len(header_value))]
                prop = header_key.split(" ", 2)[-1]
                for i, framedef_value in enumerate(header_value):
                    fdef_name = field_defs[frame_type][i].name
                    if fdef_name == "GPS_coord[1]" and framedef_value == 7:
                        framedef_value = 256  # catch latitude
                    field_defs[frame_type][i].__dict__[prop] = framedef_value
                    if prop == "predictor":
                        if framedef_value not in predictors:
                            raise RuntimeError("No predictor found for {:d}".format(framedef_value))
                        else:
                            field_defs[frame_type][i].predictorfun = predictors[framedef_value]
                    elif prop == "encoding":
                        if framedef_value not in decoders:
                            raise RuntimeError("No decoder found for {:d}".format(framedef_value))
                        else:
                            decoder = decoders[framedef_value]
                            if decoder.__name__.endswith("_versioned"):
                                # short circuit calls to versioned decoders
                                # noinspection PyArgumentList
                                decoder = decoder(headers.get("Data version", HeaderDefaults.data_version))
                            field_defs[frame_type][i].decoderfun = decoder
        if FrameType.INTER not in field_defs:
            # partial or missing header information
            return
        # copy field names from INTRA to INTER defs
        for i, fdef in enumerate(field_defs[FrameType.INTER]):
            fdef.name = field_defs[FrameType.INTRA][i].name

    @property
    def log_index(self) -> int:
        """Return the currently set log index. May return 0 if `.set_log_index()` haven't been called yet.

        :type: int
        """
        return self._log_index

    @property
    def log_count(self) -> int:
        """The number of logs in the current file.

        :type: int
        """
        return len(self._log_pointers)

    @property
    def log_pointers(self) -> List[int]:
        """List of byte pointers to the start of each log file, including headers.

        :type: List[int]
        """
        return list(self._log_pointers)

    @property
    def headers(self) -> Headers:
        """Dict of parsed headers.

        :type: dict
        """
        return dict(self._headers)

    @property
    def field_defs(self) -> Dict[FrameType, List[FieldDef]]:
        """Dict of built field definitions.

        :type: dict
        """
        return dict(self._field_defs)

    def value(self) -> int:
        """Get current byte value.
        """
        return self._frame_data[self._frame_data_ptr]

    def has_subsequent(self, data: bytes) -> bool:
        """Return `True` if upcoming bytes equal ``data``.
        """
        return self._frame_data[self._frame_data_ptr:self._frame_data_ptr + len(data)] == data

    def tell(self) -> int:
        """IO protocol
        """
        return self._frame_data_ptr

    def seek(self, n: int):
        """IO protocol
        """
        self._frame_data_ptr = n

    def __iter__(self) -> Iterator[Optional[int]]:
        return self

    def __next__(self) -> Optional[int]:
        if self._frame_data_len == self._frame_data_ptr:
            return None
        byte = self._frame_data[self._frame_data_ptr]
        self._frame_data_ptr += 1
        return byte

    def __len__(self) -> int:
        return self._frame_data_len
