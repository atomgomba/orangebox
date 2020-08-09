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
    """Inter frames hold deltas
    """
    INTRA = 'I'
    """Intra frames are key frames
    """
    GPS = 'G'
    """Frames for GPS data
    """
    SLOW = 'S'
    """Slow frames are saved at a lower frequency
    """
    GPS_HOME = 'H'
    """Frame for GPS home position
    """
    EVENT = 'E'
    """Frames for log events
    """


class FieldDef:
    """Holds data for a field definition. Field definitions describe the fields within a given type of frame.

    :param frame_type: Type of frame
    :type frame_type: FrameType
    :param name: Name of the field
    :param signed: Not used
    :param predictor: Numerical index of a predictor function
    :param encoding: Number indicating the value encoding type
    :param decoderfun: Decoder callable (set by `.Reader` dynamically)
    :type decoderfun: Optional[Decoder]
    :param predictorfun: Predictor callable (set by `.Reader` dynamically)
    :type predictorfun: Optional[Predictor]
    """
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
"""
:param type: Type of frame
:type type: FrameType
:param data: Frame data
:type data: tuple
"""

Headers = Dict[str, Union[str, Number, List[Number]]]
DecodedValue = Union[int, Tuple]
Decoder = Callable[[Iterator[int], Optional["Context"]], DecodedValue]
Predictor = Callable[[int, "Context"], int]
FieldDefs = Dict[FrameType, List[FieldDef]]

Event = namedtuple('Event', 'type data')
"""
:param type: Type of event
:type type: EventType
:param data: Arbitrary data for the event
:type data: dict
"""

EventParser = Callable[[Iterator[int]], Optional[dict]]
