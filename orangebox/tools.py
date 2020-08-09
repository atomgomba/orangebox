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

from struct import pack, unpack
from typing import Any, Callable, Union

from orangebox.types import Number


def map_to(key: Any, amap: dict) -> Callable:
    def decorator(fun: Callable) -> Callable:
        amap[key] = fun
        return fun

    return decorator


def toint32(word):
    return unpack('i', pack('I', word))[0]


def sign_extend_24bit(bits):
    return toint32(bits | 0xFF000000) if bits & 0x800000 else bits


def sign_extend_16bit(word):
    return toint32(word | 0xFFFF0000) if word & 0x8000 else word


def sign_extend_14bit(word):
    return toint32(word | 0xFFFFC000) if word & 0x2000 else word


def sign_extend_8bit(byte):
    return toint32(byte | 0xFFFFFF00) if byte & 0x80 else byte


def sign_extend_7bit(byte):
    return toint32(byte | 0xFFFFFF80) if byte & 0x40 else byte


def sign_extend_6bit(byte):
    return toint32(byte | 0xFFFFFFC0) if byte & 0x20 else byte


def sign_extend_5bit(byte):
    return toint32(byte | 0xFFFFFFE0) if byte & 0x10 else byte


def sign_extend_4bit(nibble):
    return toint32(nibble | 0xFFFFFFF0) if nibble & 0x08 else nibble


def sign_extend_2bit(byte) -> int:
    return toint32(byte | 0xFFFFFFFC) if byte & 0x02 else byte


def _trycast(s: str) -> Union[Number, str]:
    """Try to cast a string to the most appropriate numeric type.
    """
    if s.startswith("0x"):
        return int(s, 16)
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s
