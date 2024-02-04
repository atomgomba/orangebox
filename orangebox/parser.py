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
    """Parse and iterate over decoded frames.
    """

    def __init__(self, reader: Reader):
        """
        :param reader: The `.Reader` used to iterate over the relevant bits of bytes
        :type reader: Reader
        """
        self._reader = reader
        self._events = []  # type: List[Event]
        self._headers = {}  # type: Headers
        self._field_names = []  # type: List[str]
        self._end_of_log = False
        self._ctx = None  # type: Optional[Context]
        self.set_log_index(reader.log_index)

    def set_log_index(self, index: int):
        """Select a log by index within the file. Calling this method will set the new index for the underlying
        `.Reader` object and also update the header information as a side effect. The state of the parser will be reset.

        The first index is 1. You can get the maximum number of logs from `.Reader.log_count`.

        See also `.Reader.set_log_index()`.

        :param index: The selected log index
        """
        self._events = []
        self._end_of_log = False
        reader = self._reader
        reader.set_log_index(index)
        self._headers = {k: v for k, v in reader.headers.items() if "Field" not in k}
        self._ctx = Context(self._headers, reader.field_defs)
        self._field_names = []
        for ftype in [FrameType.INTRA, FrameType.SLOW, FrameType.GPS]:
            # Note: retaining the order above is important for communality with bb-log-viewer
            # Note 2: GPS_home is not written out by the blackbox-log-viewer (but added as offset to GPS_coord)
            # Note 3: GPS mysteriously contains a "time" field. This is correctly skipped by the filter below
            if ftype in reader.field_defs:
                self._field_names += filter(lambda x: x is not None and x not in self._field_names,
                                            map(lambda x: x.name, reader.field_defs[ftype]))

    @staticmethod
    def load(path: str, log_index: int = 1) -> "Parser":
        """Factory method to create a parser for a log file.

        :param path: Path to blackbox log file
        :param log_index: Index within log file (defaults to 1)
        :rtype: Parser
        """
        return Parser(Reader(path, log_index))

    def frames(self) -> Iterator[Frame]:
        """Return an iterator for the current frames.

        :rtype: Iterator[Frame]
        """
        field_defs = self._reader.field_defs
        last_slow = None  # type: Optional[Frame]
        last_gps = None  # type: Optional[Frame]
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
                last_frame_is_corrupt = True
                continue

            ctx.frame_type = ftype
            last_frame_is_corrupt = False
            last_frame_pos = reader.tell() - 1

            if ftype == FrameType.EVENT:
                # parse event frame (event frames do not depend on field defs)
                if not self._parse_event_frame(reader):
                    ctx.invalid_frame_count += 1
                ctx.read_frame_count += 1
                if self._end_of_log:
                    _log.info(
                        "Frames: total: {total:d}, parsed: {parsed:d}, skipped: {skipped:d} invalid: {invalid:d} ({invalid_percent:.2f}%)"
                        .format(**ctx.stats))
                    break
                continue

            if ftype not in field_defs:
                _log.warning("No field def found for frame type {!r}".format(ftype))
                ctx.invalid_frame_count += 1
                ctx.read_frame_count += 1
                continue

            # decode INTRA, INTER, SLOW, GPS or GPS_HOME frame
            frame = self._parse_frame(field_defs[ftype], reader)

            # store these frames to append them to subsequent frames:
            if ftype == FrameType.SLOW:
                last_slow = frame
                ctx.read_frame_count += 1
                continue
            elif ftype == FrameType.GPS:
                last_gps = frame
                ctx.read_frame_count += 1
                continue
            elif ftype == FrameType.GPS_HOME:
                ctx.add_frame(frame)
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

            # add in extra frames (GPS, GPS_HOME and SLOW)
            extra_data = []

            # add slow frames (list of empty strings if not available to ensure
            # the right amount of ',' are written out at least)
            if FrameType.SLOW in field_defs:
                if last_slow:
                    extra_data += last_slow.data
                else:
                    extra_data += [""] * len(field_defs[FrameType.SLOW])

            # add GPS frames the way blackbox-log-viewer seems to do it
            if FrameType.GPS in field_defs:
                if last_gps:
                    extra_data += list(last_gps.data[1:])  # skip time
                else:
                    extra_data += [""] * (len(field_defs[FrameType.GPS]) - 1)

            frame = Frame(ftype, frame.data + tuple(extra_data))

            try:
                FrameType(chr(reader.value()))
            except ValueError:
                _log.debug("Dropping {:s} Frame #{:d} because it's corrupt"
                           .format(ftype.value, ctx.read_frame_count + 1))
                ctx.invalid_frame_count += 1
                continue
            ctx.read_frame_count += 1
            ctx.add_frame(frame)
            yield frame

    def _parse_frame(self, fdefs: List[FieldDef], reader: Reader) -> Frame:
        result = ()
        ctx = self._ctx
        ctx.field_index = 0
        field_count = ctx.field_def_counts[ctx.frame_type]
        while ctx.field_index < field_count:
            # make current frame available in context
            ctx.current_frame = result
            fdef = fdefs[ctx.field_index]
            # decode current field value
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

    def _parse_event_frame(self, reader: Reader) -> bool:
        byte = next(reader)
        try:
            event_type = EventType(byte)
        except ValueError:
            _log.warning("Unknown event type: {!r}".format(byte))
            return False
        _log.debug("New event frame #{:d}: {:s}".format(self._ctx.read_frame_count + 1, event_type.name))
        parser = event_map[event_type]  # type: EventParser
        event_data = parser(reader)
        self.events.append(Event(event_type, event_data))
        if event_type == EventType.LOG_END:
            self._end_of_log = True
        return True

    @property
    def headers(self) -> Headers:
        """Headers key-value map. This will not contain the headers describing the field definitions. To get the raw
        headers see `.Reader` instead. Key is a string, value can be a string, a number or a list of numbers.

        :type: dict
        """
        return dict(self._headers)

    @property
    def events(self) -> List[Event]:
        """Log events found during parsing. All the events are available only after parsing has finished.

        :type: List[Event]
        """
        return list(self._events)

    @property
    def field_names(self) -> List[str]:
        """A list of all field names found in the current header.

        :type: List[str]
        """
        return list(self._field_names)

    @property
    def reader(self) -> Reader:
        """Return the underlying `.Reader` object.

        :type: Reader
        """
        return self._reader
