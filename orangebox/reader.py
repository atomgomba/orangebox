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
from typing import BinaryIO, Dict, Iterator, List, Optional, Union

from .decoders import decoder_map
from .predictors import predictor_map
from .types import FieldDef, FrameType, Headers, Number

MAX_FRAME_SIZE = 256

_log = logging.getLogger(__name__)


def _trycast(s: str) -> Union[Number, str]:
    """Try to cast a string to the most appropriate numeric type.
    """
    if s.startswith("0x"):
        return int(s, 16)
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


class Reader:
    """Reads a flight log and stores raw data in a structured way. Does not do any real parsing.

    TODO: detecting and informing the user about possible file corruption (missing headers, etc.)
    """

    def __init__(self, path: str, log_index: Optional[int] = None):
        self.headers = dict()  # type: Headers
        self.field_defs = dict()  # type: Dict[FrameType, List[FieldDef]]
        self._log_index = log_index or 1
        self._header_size = 0
        self._path = path
        self._frame_data_ptr = 0
        self._log_pointers = []  # type: List[int]
        self._frame_data = b''
        self._frame_data_len = 0
        with open(path, "rb") as f:
            if not f.seekable():
                msg = "Input file must be seekable"
                _log.critical(msg)
                raise IOError(msg)
            first_line = self._parse_headers(f)
            self._find_pointers(f, first_line)
        if log_index is not None:
            self.log_index = log_index
        self._build_field_defs()

    def _parse_headers(self, f: BinaryIO) -> bytes:
        byteptr = 0
        first_line = ""
        self._header_size = 0
        while True:
            f.seek(byteptr)
            line = f.readline()
            if not line:
                # nothing left to read
                break
            self._header_size += len(line)
            has_next = self._parse_header_line(line)  # type: int
            if not has_next:
                _log.debug("End of headers at {:d} (found: {:d})".format(byteptr, len(self.headers.keys())))
                break
            if not first_line:
                first_line = line
            byteptr += len(line)
        return first_line

    def _find_pointers(self, f: BinaryIO, first_line: bytes):
        f.seek(0)
        content = f.read()
        new_index = content.find(first_line)
        step = len(first_line)
        while -1 < new_index:
            self._log_pointers.append(new_index)
            new_index = content.find(first_line, new_index + step + 1)

    @property
    def log_index(self) -> int:
        return self._log_index

    @log_index.setter
    def log_index(self, index: int):
        if index < 1 or self.log_count < index:
            raise RuntimeError("Invalid log_index: {:d} (1 <= x < {:d})".format(index, self.log_count))
        start = self._log_pointers[index - 1]
        with open(self._path, "rb") as f:
            f.seek(start + self._header_size)
            size = self._log_pointers[index] - start if index < self.log_count else None
            self._frame_data = f.read(size) if size is not None else f.read()
        self._log_index = index
        self._frame_data_ptr = 0
        self._frame_data_len = len(self._frame_data)
        _log.info("Log index #{:d} out of {:d} (starts at: {:d})".format(self._log_index, self.log_count, start))

    def tell(self) -> int:
        return self._frame_data_ptr

    def seek(self, n: int):
        self._frame_data_ptr = n

    def value(self) -> int:
        return self._frame_data[self._frame_data_ptr]

    def has_subsequent(self, data: bytes) -> bool:
        return self._frame_data[self._frame_data_ptr:self._frame_data_ptr + len(data)] == data

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

    def _parse_header_line(self, data: bytes) -> bool:
        """Parse a header line and return its resulting character length.

        Return None if the line cannot be parsed.
        """
        if data[0] != 72:  # 72 == ord('H')
            # not a header line
            return False
        line = data.decode().replace("H ", "", 1)
        name, value = line.split(':', 1)
        self.headers[name.strip()] = [_trycast(s.strip()) for s in value.split(',')] if ',' in value \
            else _trycast(value.strip())
        return True

    def _build_field_defs(self):
        """Use the read headers to populate the `field_defs` property.
        """
        headers = self.headers
        field_defs = self.field_defs
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
                                decoder = decoder(headers.get("Data version"))
                            field_defs[frame_type][i].decoderfun = decoder
        # copy field names from INTRA to INTER defs
        if FrameType.INTER not in field_defs:
            # partial header information
            return
        for i, fdef in enumerate(field_defs[FrameType.INTER]):
            fdef.name = field_defs[FrameType.INTRA][i].name

    @property
    def log_count(self) -> int:
        return len(self._log_pointers)
