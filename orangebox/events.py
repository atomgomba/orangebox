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

from typing import Dict, Optional

from .decoders import _unsigned_vb
from .reader import Reader
from .tools import map_to
from .types import EventParser, EventType

END_OF_LOG_MESSAGE = b'End of log\x00'

event_map = dict()  # type: Dict[EventType, EventParser]


@map_to(EventType.SYNC_BEEP, event_map)
def sync_beep(data: Reader) -> Optional[dict]:
    return {"time": _unsigned_vb(data), }


@map_to(EventType.FLIGHT_MODE, event_map)
def flight_mode(data: Reader) -> Optional[dict]:
    return {
        "new_flags": _unsigned_vb(data),
        "old_flags": _unsigned_vb(data),
    }


@map_to(EventType.AUTOTUNE_TARGETS, event_map)
def autotune_targets(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.AUTOTUNE_CYCLE_START, event_map)
def autotune_cycle_start(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.AUTOTUNE_CYCLE_RESULT, event_map)
def autotune_cycle_result(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.GTUNE_CYCLE_RESULT, event_map)
def gtune_cycle_result(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.CUSTOM_BLANK, event_map)
def custom_blank(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.TWITCH_TEST, event_map)
def twitch_test(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.INFLIGHT_ADJUSTMENT, event_map)
def inflight_adjustment(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.LOGGING_RESUME, event_map)
def logging_resume(_: Reader) -> Optional[dict]:
    # TODO
    pass


@map_to(EventType.LOG_END, event_map)
def logging_end(data: Reader) -> Optional[dict]:
    if not data.has_subsequent(END_OF_LOG_MESSAGE):
        raise ValueError("Invalid 'End of log' message")
    return None
