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

from typing import Dict, Iterator, Optional

from .context import Context
from .tools import map_to, sign_extend_14bit, sign_extend_16bit, sign_extend_24bit, sign_extend_2bit, sign_extend_4bit, \
    sign_extend_6bit, sign_extend_8bit
from .types import DecodedValue, Decoder

decoder_map = dict()  # type: Dict[int, Decoder]


@map_to(0, decoder_map)
def _signed_vb(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    value = _unsigned_vb(data, ctx)
    value = ((value % 0x100000000) >> 1) ^ -(value & 1)
    return value


# noinspection PyUnusedLocal
@map_to(1, decoder_map)
def _unsigned_vb(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    shift, result = 0, 0
    for i in range(5):
        byte = next(data)
        result = result | ((byte & ~0x80) << shift)
        if byte < 128:
            # reached final byte
            return result
        shift += 7
    # integer too long
    return 0


@map_to(3, decoder_map)
def _neg_14bit(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    return -sign_extend_14bit(_unsigned_vb(data, ctx))


@map_to(6, decoder_map)
def _tag8_8svb(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    # count adjacent fields with same encoding
    group_count = 8
    fdeflen = ctx.field_def_counts[ctx.frame_type]
    for i in range(ctx.field_index + 1, ctx.field_index + 8):
        if i == fdeflen:
            group_count = (fdeflen-1) - ctx.field_index
            break
        if ctx.field_defs[ctx.frame_type][i].encoding != 6:
            group_count = i - ctx.field_index
            break
    if group_count == 1:
        # single field
        return _signed_vb(data, ctx)
    else:
        # multiple fields
        header = next(data)
        values = ()
        for _ in range(group_count):
            values += (_signed_vb(data, ctx) if header & 0x01 else 0,)
            header >>= 1
        return values


# noinspection PyUnusedLocal
@map_to(7, decoder_map)
def _tag2_3s32(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    lead = next(data)
    shifted = lead >> 6
    if shifted == 0:  # 2bit fields
        v1 = sign_extend_2bit((lead >> 4) & 0x03)
        v2 = sign_extend_2bit((lead >> 2) & 0x03)
        v3 = sign_extend_2bit(lead & 0x03)
        return v1, v2, v3
    elif shifted == 1:  # 4bit fields
        v1 = sign_extend_4bit(lead & 0x0F)
        lead = next(data)
        v2 = sign_extend_4bit(lead >> 4)
        v3 = sign_extend_4bit(lead & 0x0F)
        return v1, v2, v3
    elif shifted == 2:  # 6bit fields
        v1 = sign_extend_6bit(lead & 0x3F)
        lead = next(data)
        v2 = sign_extend_6bit(lead & 0x3F)
        lead = next(data)
        v3 = sign_extend_6bit(lead & 0x3F)
        return v1, v2, v3
    elif shifted == 3:  # fields are 8, 16 or 24bit
        values = ()
        for _ in range(3):
            field_type = lead & 0x03
            if field_type == 0:  # 8bit
                v1 = next(data)
                values += (sign_extend_8bit(v1),)
            elif field_type == 1:  # 16bit
                v1 = next(data)
                v2 = next(data)
                values += (sign_extend_16bit(v1 | (v2 << 8)),)
            elif field_type == 2:  # 24bit
                v1 = next(data)
                v2 = next(data)
                v3 = next(data)
                values += (sign_extend_24bit(v1 | (v2 << 8) | (v3 << 16)),)
            elif field_type == 3:  # 32bit
                v1 = next(data)
                v2 = next(data)
                v3 = next(data)
                v4 = next(data)
                values += (v1 | (v2 << 8) | (v3 << 16) | (v4 << 24),)
            lead >>= 2
        return values
    return 0, 0, 0


@map_to(8, decoder_map)
def _tag8_4s16_versioned(data_version: int) -> Decoder:
    if data_version < 2:
        return _tag8_4s16_v1
    else:
        return _tag8_4s16_v2


def _tag8_4s16_v1(_: Iterator[int], __: Optional[Context] = None) -> DecodedValue:
    # TODO
    return "TODO:tag8_4s16_v1"


# noinspection PyUnusedLocal
def _tag8_4s16_v2(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    selector = next(data)
    values = ()
    nibble_index = 0
    buffer = 0
    for _ in range(4):
        field_type = selector & 0x03
        if field_type == 0:  # field zero
            values += (0,)
        elif field_type == 1:  # field 4bit
            if nibble_index == 0:
                buffer = next(data)
                values += (sign_extend_4bit(buffer >> 4),)
                nibble_index = 1
            else:
                values += (sign_extend_4bit(buffer & 0x0F),)
                nibble_index = 0
        elif field_type == 2:  # field 8bit
            if nibble_index == 0:
                values += (sign_extend_8bit(next(data)),)
            else:
                v1 = (buffer & 0x0F) << 4
                buffer = next(data)
                v1 |= buffer >> 4
                values += (sign_extend_8bit(v1),)
        elif field_type == 3:  # field 16bit
            if nibble_index == 0:
                v1 = next(data)
                v2 = next(data)
                values += (sign_extend_16bit((v1 << 8) | v2),)
            else:
                v1 = next(data)
                v2 = next(data)
                values += (sign_extend_16bit(((buffer & 0x0F) << 12) | (v1 << 4) | (v2 >> 4)),)
                buffer = v2
        selector >>= 2
    return values


# noinspection PyUnusedLocal
@map_to(9, decoder_map)
def _null(data: Iterator[int], ctx: Optional[Context] = None) -> DecodedValue:
    return 0


@map_to(10, decoder_map)
def _tag2_3svariable(_: Iterator[int], __: Optional[Context] = None) -> DecodedValue:
    # TODO
    return "TODO:tag2_3svariable"
