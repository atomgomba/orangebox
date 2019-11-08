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
from typing import Dict, Iterator, List, Optional, Union

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

    def __init__(self, path: str):
        self.headers = dict()  # type: Headers
        self.field_defs = dict()  # type: Dict[FrameType, List[FieldDef]]
        self._path = path
        self._frame_data_ptr = 0
        byteptr = 0
        with open(path, "rb") as f:
            while True:
                f.seek(byteptr)
                data = f.readline()
                if not data:
                    # nothing left to read
                    break
                numbytes = self._read_header_line(data)
                if numbytes is None:
                    _log.debug("End of headers at {:d}".format(byteptr))
                    self._frame_data = data + f.read()  # type: bytes
                    self._frame_data_len = len(self._frame_data)  # type: int
                    break
                byteptr += numbytes + 1
        self._build_field_defs()

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

    def _read_header_line(self, data: bytes) -> Optional[int]:
        if data[0] != 72:  # 72 == ord('H')
            # not a header line
            return None
        line = data.decode().replace("H ", "", 1)
        name, value = line.split(':', 1)
        self.headers[name.strip()] = [_trycast(s.strip()) for s in value.split(',')] if ',' in value \
            else _trycast(value.strip())
        return len(data) - 1

    def _build_field_defs(self):
        """Use the read headers to populate the `field_defs` property.
        """
        headers = self.headers
        field_defs = self.field_defs
        predictors = predictor_map
        decoders = decoder_map
        for frametype in FrameType:
            # field header format: 'Field <FrameType> <Property>'
            for header_key, header_value in headers.items():
                if "Field " + frametype.value not in header_key:
                    # skip headers unrelated to defining fields
                    continue
                if frametype not in field_defs:
                    field_defs[frametype] = [FieldDef(frametype) for _ in range(len(header_value))]
                prop = header_key.split(" ", 2)[-1]
                for i, framedefval in enumerate(header_value):
                    field_defs[frametype][i].__dict__[prop] = framedefval
                    if prop == "predictor":
                        if framedefval not in predictors:
                            raise RuntimeError("No predictor found for {:d}".format(framedefval))
                        else:
                            field_defs[frametype][i].predictorfun = predictors[framedefval]
                    elif prop == "encoding":
                        if framedefval not in decoders:
                            raise RuntimeError("No decoder found for {:d}".format(framedefval))
                        else:
                            decoder = decoders[framedefval]
                            if decoder.__name__.endswith("_versioned"):
                                # short circuit calls to versioned decoders
                                # noinspection PyArgumentList
                                decoder = decoder(headers.get("Data version"))
                            field_defs[frametype][i].decoderfun = decoder
        # copy field names from INTRA to INTER defs
        for i, fdef in enumerate(field_defs[FrameType.INTER]):
            fdef.name = field_defs[FrameType.INTRA][i].name
