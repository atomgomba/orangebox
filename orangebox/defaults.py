# Orangebox - Cleanflight/Betaflight blackbox data parser.
# Copyright (C) 2024  Károly Kiripolszky
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

from .types import Headers

_log = logging.getLogger(__name__)


class HeaderDefaults:
    defaults = {
        "Data version": 1,
        "I interval": 1,
        "P interval": 0,
        "minthrottle": 0,
        "motorOutput": [0, 0],
        "vbatref": 0,
    }

    @classmethod
    def inspect(cls, headers: Headers):
        """Inspect headers and log a warning on missing values which are expected.
        """
        for header in cls.defaults.keys():
            if header not in headers.keys():
                default = cls.defaults.get(header)
                _log.warning(f"Header not found in file: {header} (using default value: {default})")

    @classmethod
    @property
    def data_version(cls) -> int:
        return cls.defaults["Data version"]

    @classmethod
    @property
    def i_interval(cls) -> int:
        return cls.defaults["I interval"]

    @classmethod
    @property
    def p_interval(cls) -> int:
        return cls.defaults["P interval"]

    @classmethod
    @property
    def minthrottle(cls) -> int:
        return cls.defaults["minthrottle"]

    @classmethod
    @property
    def motor_output(cls) -> int:
        return cls.defaults["motorOutput"]

    @classmethod
    @property
    def vbatref(cls) -> int:
        return cls.defaults["vbatref"]
