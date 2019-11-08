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
from typing import Iterator, List, Optional

from .context import Context
from .events import event_map
from .reader import Reader
from .types import Event, EventParser, EventType, FieldDef, Frame, FrameType, Headers

MAX_TIME_JUMP = 10 * 1000000
MAX_ITER_JUMP = 500 * 10

_log = logging.getLogger(__name__)


class Parser:
    """Takes a `reader.Reader` instance and generates the final data output.

    TODO: detecting and informing the user about possible file corruption
    """

    def __init__(self, reader: Reader):
        self.headers = {k: v for k, v in reader.headers.items() if "Field" not in k}  # type: Headers
        self.field_names = []
        for fdef in reader.field_defs.values():
            self.field_names += filter(lambda x: x is not None and x not in self.field_names,
                                       map(lambda x: x.name, fdef))
        self.events = []  # type: List[Event]
        self._reader = reader
        self._end_of_log = False
        self._ctx = Context(self.headers, reader.field_defs)

    def frames(self) -> Iterator[Frame]:
        field_defs = self._reader.field_defs
        last_slow = None  # type: Optional[Frame]
        ctx = self._ctx  # type: Context
        reader = self._reader
        last_time = None
        last_iter = 0
        last_frame_pos = 0
        last_frame_is_corrupt = False
        for byte in reader:
            try:
                ftype = FrameType(chr(byte))
            except ValueError:
                if not last_frame_is_corrupt:
                    reader.seek(last_frame_pos + 1)
                    ctx.invalid_frame_count += 1
                    ctx.read_frame_count += 1
                last_frame_is_corrupt = True
                continue
            last_frame_is_corrupt = False
            last_frame_pos = reader.tell() - 1
            ctx.frame_type = ftype
            if ftype == FrameType.EVENT:
                # parse event frame
                self._parse_event(reader)
                ctx.read_frame_count += 1
                if self._end_of_log:
                    _log.info(
                        "Frames: total: {total:d}, parsed: {parsed:d}, invalid: {invalid:d} ({invalid_percent:.2f}%)"
                        .format(**ctx.stats))
                    break
                continue
            # decode frame
            frame = self._parse_frame(field_defs[ftype], reader)
            if ftype == FrameType.SLOW:
                # store this frame to append it to the subsequent non-SLOW frame
                last_slow = frame
                ctx.read_frame_count += 1
                continue
            # validate frame
            current_time = ctx.get_current_value_by_name(ftype, "time")
            if last_time is not None and last_time >= current_time and MAX_TIME_JUMP < current_time - last_time:
                _log.debug("Invalid {:s} Frame #{:d} due to time desync".format(ftype.value, ctx.read_frame_count + 1))
                last_time = current_time
                ctx.read_frame_count += 1
                ctx.invalid_frame_count += 1
                continue
            last_time = current_time
            current_iter = ctx.get_current_value_by_name(ftype, "loopIteration")
            ctx.last_iter = current_iter
            if last_iter >= current_iter and MAX_ITER_JUMP < current_iter + last_iter:
                _log.debug("Skipping {:s} Frame #{:d} due to iter desync".format(ftype.value, ctx.read_frame_count + 1))
                last_iter = current_iter
                ctx.read_frame_count += 1
                ctx.invalid_frame_count += 1
                continue
            last_iter = current_iter
            if last_slow is not None:
                # append data from previous SLOW frame
                frame = Frame(ftype, frame.data + last_slow.data)
            try:
                FrameType(chr(reader.value()))
            except ValueError:
                _log.debug("Dropping {:s} Frame #{:d} because it's corrupt"
                           .format(ftype.value, ctx.read_frame_count + 1))
                continue
            ctx.read_frame_count += 1
            ctx.add_frame(frame)
            yield frame

    @staticmethod
    def load(path: str) -> "Parser":
        return Parser(Reader(path))

    @property
    def reader(self) -> Reader:
        return self._reader

    @property
    def context(self) -> Context:
        return self._ctx

    @property
    def last_event(self) -> Optional[Event]:
        return None if not self.events else self.events[-1]

    def _parse_frame(self, fdefs: List[FieldDef], reader: Reader) -> Frame:
        result = ()
        ctx = self._ctx
        ctx.field_index = 0
        field_count = ctx.field_def_counts[ctx.frame_type]
        while ctx.field_index < field_count:
            # update available parsed data
            ctx.current_frame = result
            # decode field value
            fdef = fdefs[ctx.field_index]
            rawvalue = fdef.decoderfun(reader, ctx)
            # apply predictions
            if isinstance(rawvalue, tuple):
                value = ()
                for v in rawvalue:
                    fdef = fdefs[ctx.field_index]
                    value += (fdef.predictorfun(v, ctx),)
                    ctx.field_index += 1
                result += value
            else:
                value = fdef.predictorfun(rawvalue, ctx)
                ctx.field_index += 1
                result += (value,)
        return Frame(ctx.frame_type, result)

    def _parse_event(self, reader: Reader):
        events = event_map
        byte = next(reader)
        ctx = self._ctx
        try:
            event_type = EventType(byte)
        except ValueError:
            _log.debug("Unknown event type: '{:d}'".format(byte))
            return None
        _log.debug("New Event Frame #{:d}: {:s}".format(ctx.read_frame_count + 1, event_type.name))
        parser = events[event_type]  # type: EventParser
        event_data = parser(reader)
        self.events.append(Event(event_type, event_data))
        if event_type == EventType.LOG_END:
            self._end_of_log = True
            return
