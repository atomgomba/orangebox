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

from typing import Dict

from .context import Context
from .defaults import HeaderDefaults
from .tools import map_to
from .types import FrameType, Number, Predictor

predictor_map = dict()  # type: Dict[int, Predictor]


@map_to(0, predictor_map)
def _noop(new: Number, _: Context) -> Number:
    return new


@map_to(1, predictor_map)
def _previous(new: Number, ctx: Context) -> Number:
    return new + ctx.get_past_value(0, 0)


@map_to(2, predictor_map)
def _straight_line(new: Number, ctx: Context) -> Number:
    prev = ctx.get_past_value(0)
    prev2 = ctx.get_past_value(1, prev)
    return new + 2 * prev - prev2


@map_to(3, predictor_map)
def _average2(new: Number, ctx: Context) -> Number:
    prev = ctx.get_past_value(0)
    prev2 = ctx.get_past_value(1, prev)
    return new + int((prev + prev2) / 2)


@map_to(4, predictor_map)
def _minthrottle(new: Number, ctx: Context) -> Number:
    return new + ctx.headers.get("minthrottle", HeaderDefaults.minthrottle)


@map_to(5, predictor_map)
def _motor0(new: Number, ctx: Context) -> Number:
    return new + ctx.get_current_value_by_name(FrameType.INTRA, "motor[0]")


@map_to(6, predictor_map)
def _increment(_: Number, ctx: Context) -> Number:
    return 1 + ctx.get_past_value(0) + ctx.count_skipped_frames()


@map_to(7, predictor_map)
def _home_coord_0(new: Number, ctx: Context) -> Number:
    if not ctx.last_gps_home_frame.data:
        return 0
    return new + ctx.last_gps_home_frame.data[0]


@map_to(256, predictor_map)
def _home_coord_1(new: Number, ctx: Context) -> Number:
    if not ctx.last_gps_home_frame.data:
        return 0
    return new + ctx.last_gps_home_frame.data[1]


@map_to(8, predictor_map)
def _1500(new: Number, _: Context) -> Number:
    return new + 1500


@map_to(9, predictor_map)
def _vbatref(new: Number, ctx: Context) -> Number:
    return new + ctx.headers.get("vbatref", HeaderDefaults.vbatref)


@map_to(10, predictor_map)
def _last_main_frame_time(new: Number, ctx: Context) -> Number:
    # TODO: test this
    return new + ctx.get_past_value(1, 0)


@map_to(11, predictor_map)
def _minmotor(new: Number, ctx: Context) -> Number:
    # index 0 is the minimum motor output
    return new + ctx.headers.get("motorOutput", HeaderDefaults.motor_output)[0]
