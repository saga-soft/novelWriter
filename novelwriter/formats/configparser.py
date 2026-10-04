"""
novelWriter - INI Config Parser
===============================

This file is a part of novelWriter
Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""  # noqa

from __future__ import annotations

import logging

from configparser import ConfigParser
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

from novelwriter.common import checkInt, checkPath

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

_T_Enum = TypeVar("_T_Enum", bound=Enum)


class NConfigParser(ConfigParser):
    """Core: Adapted Config Parser.

    This is a subclass of the standard config parser that adds type safe
    helper functions, and support for lists. It also turns off
    interpolation, which would require % symbols to be escaped (#2455).

    It is kept for backwards compatibility with old config files.
    """

    def __init__(self) -> None:
        super().__init__(interpolation=None)

    def read(self, path: Path) -> None:
        """Read and parse config data from a file, mirroring write()."""
        with open(path, mode="r", encoding="utf-8") as fileObj:
            self.read_string(fileObj.read())

    def getStr(self, section: str, option: str, default: str) -> str:
        """Read string value."""
        return self.get(section, option, fallback=default)

    def getInt(self, section: str, option: str, default: int) -> int:
        """Read integer value."""
        try:
            return self.getint(section, option, fallback=default)
        except ValueError:
            logger.error("Could not read '%s':'%s' from config", section, option)
        return default

    def getFloat(self, section: str, option: str, default: float) -> float:
        """Read float value."""
        try:
            return self.getfloat(section, option, fallback=default)
        except ValueError:
            logger.error("Could not read '%s':'%s' from config", section, option)
        return default

    def getBool(self, section: str, option: str, default: bool) -> bool:
        """Read boolean value."""
        try:
            return self.getboolean(section, option, fallback=default)
        except ValueError:
            logger.error("Could not read '%s':'%s' from config", section, option)
        return default

    def getPath(self, section: str, option: str, default: Path) -> Path:
        """Read a Path value."""
        return checkPath(self.get(section, option, fallback=default), default)

    def getStrList(self, section: str, option: str, default: list[str]) -> list[str]:
        """Read string list."""
        result = default.copy() if isinstance(default, list) else []
        if self.has_option(section, option):
            data = self.get(section, option, fallback="").split(",")
            for i in range(min(len(data), len(result))):
                result[i] = data[i].strip()
        return result

    def getIntList(self, section: str, option: str, default: list[int]) -> list[int]:
        """Read integer list."""
        result = default.copy() if isinstance(default, list) else []
        if self.has_option(section, option):
            data = self.get(section, option, fallback="").split(",")
            for i in range(min(len(data), len(result))):
                result[i] = checkInt(data[i].strip(), result[i])
        return result

    def getEnum(self, section: str, option: str, default: _T_Enum) -> _T_Enum:
        """Read enum value."""
        if self.has_option(section, option):
            data = self.get(section, option, fallback="")
            return type(default).__members__.get(data.upper(), default)
        return default
