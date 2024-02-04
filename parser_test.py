#!/usr/bin/env python3
import csv
import logging
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from orangebox import Parser
# noinspection PyProtectedMember
from orangebox.tools import _trycast
from orangebox.types import FrameType


def compare(frame_index, parser, frame, csv_frame, show_all_fields):
    reader = parser.reader
    stats = []
    mismatched_num = 0
    intra_inter_len = len(reader.field_defs[FrameType.INTER])

    for i, value in enumerate(frame.data):
        csv_value = _trycast(csv_frame[i])

        fdef = None
        if i < intra_inter_len:
            fdef = reader.field_defs[FrameType.INTER][i]
        else:
            cur_max_len = intra_inter_len
            if FrameType.SLOW in reader.field_defs:
                slowLen = len(reader.field_defs[FrameType.SLOW])
                if i < (cur_max_len + slowLen):
                    fdef = reader.field_defs[FrameType.SLOW][i - cur_max_len]
                else:
                    cur_max_len += slowLen

            if fdef is None and FrameType.GPS in reader.field_defs:
                gps_len = len(reader.field_defs[FrameType.GPS])
                # time is never actually written out, skip over it
                if i < (cur_max_len + gps_len - 1):
                    fdef = reader.field_defs[FrameType.GPS][i+1 - cur_max_len]
                else:
                    raise IndexError(f"Somehow index {i} is higher than the number of field definitions")

        if csv_value == value:
            if show_all_fields:
                stats.append("  field #{:d} '{:s}' value: {} encoding: {:d} predictor: {:d}".format(
                    i, fdef.name, str(csv_value), fdef.encoding, fdef.predictor
                ))
            continue
        mismatched_num += 1
        stats.append("  [!] field #{:d} '{:s}' value: {} != [{}] encoding: {:d} predictor: {:d}".format(
            i, fdef.name, str(csv_value), str(value), fdef.encoding, fdef.predictor
        ))
    if 0 < mismatched_num:
        print("Frame {} #{:d} ends at 0x{:X}".format(frame.type.value, frame_index + 1, parser.reader.tell()))
        print("\n".join(stats))
        print("  # of mismatches: {:d}".format(mismatched_num))


def main(path: str, csv_path: str, show_all_fields: bool, log_index: int):
    parser = Parser.load(path, log_index=log_index)
    csv_frames = []
    for i, row in enumerate(csv.reader(open(csv_path))):
        if len(row) == 2:
            # skip log headers
            continue
        csv_frames.append(row)
    for i, frame in enumerate(parser.frames()):
        # add i + 1 to skip field headers in CSV
        compare(frame.data[0], parser, frame, csv_frames[i + 1], show_all_fields)


if __name__ == "__main__":
    # noinspection PyTypeChecker
    argparser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    argparser.add_argument("path", help="Path to a .BFL file")
    argparser.add_argument("csv_path", help="Path to a .CSV file for verification")
    argparser.add_argument("-i", "--index", type=int, dest="log_index", default=1,
                           help="Log index number (In case of merged input)")
    argparser.add_argument("-a", "--show-all-fields", action="store_true",
                           help="Show all fields of differing frames")
    argparser.add_argument("-v", dest="verbosity", action="count", default=0,
                           help="Control verbosity (can be used multiple times)")

    args = argparser.parse_args()

    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    if args.verbosity >= len(levels):
        raise IndexError("Verbosity must be 0 <= n < 4")
    logging.basicConfig(level=levels[args.verbosity],
                        format='%(asctime)s %(name)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    main(args.path, args.csv_path, args.show_all_fields, args.log_index)
