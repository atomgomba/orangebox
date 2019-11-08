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

from collections import namedtuple
from enum import Enum, IntEnum
from typing import Callable, Dict, Iterator, List, Optional, Tuple, Union


class FrameType(Enum):
    INTER = 'P'
    INTRA = 'I'
    GPS = 'G'
    SLOW = 'S'
    GPS_HOME = 'H'
    EVENT = 'E'


class FieldDef:
    def __init__(self,
                 frame_type: FrameType,
                 name: Optional[str] = None,
                 signed: Optional[int] = None,
                 predictor: Optional[int] = None,
                 encoding: Optional[int] = None,
                 decoderfun: Optional["Decoder"] = None,
                 predictorfun: Optional["Predictor"] = None):
        self.type = frame_type
        self.name = name
        self.signed = signed
        self.predictor = predictor
        self.encoding = encoding
        self.decoderfun = decoderfun  # type: Decoder
        self.predictorfun = predictorfun  # type: Predictor

    def __repr__(self):
        return "<FrameDef type={type} name='{name}' signed={signed} predictor={predictor} encoding={encoding}>".format(
            **self.__dict__)


class EventType(IntEnum):
    SYNC_BEEP = 0

    AUTOTUNE_CYCLE_START = 10
    AUTOTUNE_CYCLE_RESULT = 11
    AUTOTUNE_TARGETS = 12
    INFLIGHT_ADJUSTMENT = 13
    LOGGING_RESUME = 14

    GTUNE_CYCLE_RESULT = 20

    FLIGHT_MODE = 30  # New Event type

    TWITCH_TEST = 40  # Feature for latency testing

    CUSTOM = 250  # Virtual Event Code - Never part of Log File.
    CUSTOM_BLANK = 251  # Virtual Event Code - Never part of Log File. - No line shown
    LOG_END = 255


Number = Union[int, float]
Frame = namedtuple('Frame', 'type data')
Headers = Dict[str, Union[str, Number, List[Number]]]
DecodedValue = Union[int, Tuple]
Decoder = Callable[[Iterator[int], Optional["Context"]], DecodedValue]
Predictor = Callable[[int, "Context"], int]
FieldDefs = Dict[FrameType, List[FieldDef]]
Event = namedtuple('Event', 'type data')
EventParser = Callable[[Iterator[int]], Optional[dict]]
