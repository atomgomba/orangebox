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

from typing import Dict, Optional, Tuple, Union

from .types import FieldDefs, Frame, FrameType, Headers, Number


class Context:
    """Used to keep track of parsing info for field predictors and decoders.
    """

    def __init__(self, headers: Headers, field_defs: FieldDefs):
        self.headers = headers  # type: Headers
        self.data_version = headers.get("Data version", 1)  # type: int
        self.field_defs = field_defs  # type: FieldDefs
        self.field_def_counts = {k: len(v) for k, v in field_defs.items()}  # type: Dict[FrameType, int]
        self.frame_count = 0  # count of parsed frames
        self.frame_type = None  # type: Optional[FrameType]
        self.field_index = 0  # index of current field
        self.past_frames = (
            Frame(FrameType.INTRA, b''),
            Frame(FrameType.INTRA, b''),
            Frame(FrameType.INTRA, b''))  # type: Tuple[Frame, Frame, Frame]
        self.last_gps_frame = Frame(FrameType.GPS, b'')
        self.last_gps_home_frame = Frame(FrameType.GPS_HOME, b'')
        self.current_frame = tuple()  # the current (possibly yet incomplete) frame
        self.last_iter = -1
        self._names_to_indices = dict()  # type: Dict[FrameType, Dict[str, int]]
        for ftype in FrameType:
            if ftype in self.field_defs:
                self._names_to_indices[ftype] = dict()
                for i, fdef in enumerate(self.field_defs[ftype]):
                    self._names_to_indices[ftype][fdef.name] = i
        self.read_frame_count = 0  # count of all frames been read
        self.invalid_frame_count = 0  # count of invalid frames
        self.i_interval = self.headers.get("I interval", 1)  # type: int
        self.skipped_frames = 0
        if self.i_interval < 1:
            self.i_interval = 1
        # determine logging frequency (interval of INTRA frames)
        p_interval = self.headers.get("P interval", 0)  # type: Union[int, str]
        if isinstance(p_interval, int):
            self.p_interval_num = 1
            self.p_interval_denom = p_interval
        else:
            num, denom = p_interval.split('/')
            self.p_interval_num = int(num)
            self.p_interval_denom = int(denom)

    def add_frame(self, frame: Frame):
        if frame.type == FrameType.INTRA:
            # override history with current INTRA frame
            self.past_frames = (frame, frame, frame)
        elif frame.type == FrameType.GPS:
            self.last_gps_frame = frame
        elif frame.type == FrameType.GPS_HOME:
            self.last_gps_home_frame = frame
        else:
            self.past_frames = (frame, self.past_frames[0], self.past_frames[1])
        self.frame_count += 1

    def get_past_value(self, age: int, default: Number = 0) -> Number:
        try:
            return self.past_frames[age].data[self.field_index]
        except (KeyError, IndexError):
            return default

    def get_current_value_by_name(self,
                                  frame_type: FrameType,
                                  field_name: str,
                                  default: Number = 0) -> Number:
        try:
            return self.current_frame[self._names_to_indices[frame_type][field_name]]
        except (KeyError, IndexError):
            return default

    def should_have_frame_at(self, index: int) -> bool:
        return (index % self.i_interval + self.p_interval_num - 1) % \
               self.p_interval_denom < self.p_interval_num

    def count_skipped_frames(self) -> int:
        if self.last_iter == -1:
            return 0
        index = self.last_iter + 1
        while not self.should_have_frame_at(index):
            index += 1
        return index - self.last_iter - 1

    @property
    def stats(self) -> dict:
        return {
            "total": self.read_frame_count,
            "parsed": self.frame_count,
            "skipped": self.read_frame_count - self.frame_count - self.invalid_frame_count,
            "invalid": self.invalid_frame_count,
            "invalid_percent": self.invalid_frame_count / self.read_frame_count * 100 if 0 < self.read_frame_count else 0,
        }
