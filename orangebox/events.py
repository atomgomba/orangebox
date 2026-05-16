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

import struct
from typing import Dict, Optional

from .decoders import _unsigned_vb, _signed_vb
from .reader import Reader
from .tools import map_to
from .types import EventParser, EventType

END_OF_LOG_MESSAGE = b"End of log"

event_map = dict()  # type: Dict[EventType, EventParser]


@map_to(EventType.SYNC_BEEP, event_map)
def sync_beep(data: Reader) -> Optional[dict]:
    return {
        "time": _unsigned_vb(data),
    }


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


@map_to(EventType.IMU_FAILURE, event_map)
def imu_failure(data: Reader) -> Optional[dict]:
    return {
        "code": _unsigned_vb(data),
    }


@map_to(EventType.INFLIGHT_ADJUSTMENT, event_map)
def inflight_adjustment(data: Reader) -> Optional[dict]:
    func = next(data)
    assert func is not None
    value = 0
    if func & 0x80:
        # read float32
        for i in range(4):
            next_value = next(data)
            assert next_value is not None
            value |= next_value << (i * 8)
        value = struct.unpack("<f", value.to_bytes(4, "little"))[0]
    else:
        value = _signed_vb(data)
    return {
        "func": func,
        "value": value,
    }


@map_to(EventType.LOGGING_RESUME, event_map)
def logging_resume(data: Reader) -> Optional[dict]:
    return {
        "iter": _unsigned_vb(data),
        "time": _unsigned_vb(data),
    }


@map_to(EventType.DISARM, event_map)
def disarm(data: Reader) -> Optional[dict]:
    return {
        "reason": _unsigned_vb(data),
    }


@map_to(EventType.GOV_STATE, event_map)
def gov_state(data: Reader) -> Optional[dict]:
    return {
        "gov": _unsigned_vb(data),
    }


@map_to(EventType.RESCUE_STATE, event_map)
def rescue_state(data: Reader) -> Optional[dict]:
    return {
        "rescue": _unsigned_vb(data),
    }


@map_to(EventType.AIRBORNE_STATE, event_map)
def airborne_state(data: Reader) -> Optional[dict]:
    return {
        "airborne": _unsigned_vb(data),
    }


@map_to(EventType.CUSTOM_DATA, event_map)
def custom_data(data: Reader) -> Optional[dict]:
    length = next(data)
    cust_data = ""
    for _ in range(length):
        cust_data += f"{next(data):02X}"
    return {
        "data": cust_data,
    }


@map_to(EventType.CUSTOM_STRING, event_map)
def custom_string(data: Reader) -> Optional[dict]:
    length = next(data)
    cust_data = ""
    for _ in range(length):
        cust_data += chr(next(data))
    return {
        "data": cust_data,
    }


@map_to(EventType.LOG_END, event_map)
def logging_end(data: Reader) -> Optional[dict]:
    if not data.has_subsequent(END_OF_LOG_MESSAGE):
        raise ValueError("Invalid 'End of log' message")
    return None
