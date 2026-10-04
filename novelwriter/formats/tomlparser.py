"""
novelWriter - TOML Config Parser
================================

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
import tomllib

from enum import Enum
from pathlib import Path
from typing import TypeVar

from PyQt6.QtGui import QFont

from novelwriter.common import checkBool, checkFloat, checkInt, checkPath, checkString

logger = logging.getLogger(__name__)

_T_Enum = TypeVar("_T_Enum", bound=Enum)

T_TomlValue = str | int | float | bool | Path | list[str] | list[int] | Enum | QFont
T_TomlObject = dict[str, T_TomlValue]
T_TomlConfig = dict[str, T_TomlObject]


class NTomlParser:
    """Core: Toml Config Parser.

    This is a wrapper around the standard tomllib module. By default it
    assumes a two level section and key/value structure. If flat is set,
    it instead assumes a single flat level of key/value pairs with no
    sections at all. Either way, values may not be nested any deeper
    than this. The get* methods and _value take an optional section,
    which should always be None when flat is set.
    """

    def __init__(self, flat: bool = False) -> None:
        self._flat = flat
        self._data: T_TomlConfig = {}
        self._root: T_TomlObject = {}

    def read(self, path: Path) -> None:
        """Read and parse TOML data from a file."""
        with open(path, mode="r", encoding="utf-8") as fileObj:
            self.readString(fileObj.read())

    def readString(self, text: str) -> None:
        """Read and parse TOML data from a string."""
        data = tomllib.loads(text)
        if self._flat:
            self._root = self._filterRoot(data)
        else:
            self._data = {}
            for section, values in data.items():
                if not isinstance(values, dict):
                    logger.error("Invalid config section '%s', expected key/value pairs", section)
                    continue
                self._data[section] = self._filterSection(section, values)

    def write(self, path: Path, data: T_TomlConfig | T_TomlObject) -> None:
        """Write a dict of sections, or a flat dict, to a file."""
        with open(path, mode="w", encoding="utf-8") as fileObj:
            fileObj.write(self.writeString(data))

    def writeString(self, data: T_TomlConfig | T_TomlObject) -> str:
        """Format a dict of sections, or a flat dict, as TOML."""
        if self._flat:
            lines = [f"{key} = {self._dump(value)}" for key, value in data.items()]  # type: ignore[union-attr]
            return "\n".join(lines) + "\n" if lines else ""

        lines = []
        for section, values in data.items():
            if not isinstance(values, dict):
                logger.error("Invalid config section '%s', expected key/value pairs", section)
                continue
            lines.append(f"[{section}]")
            for key, value in values.items():
                lines.append(f"{key} = {self._dump(value)}")
            lines.append("")

        return "\n".join(lines) + "\n" if lines else ""

    def getStr(self, section: str | None, option: str, default: str) -> str:
        """Read string value."""
        return checkString(self._value(section, option), default)

    def getInt(self, section: str | None, option: str, default: int) -> int:
        """Read integer value."""
        return checkInt(self._value(section, option), default)

    def getFloat(self, section: str | None, option: str, default: float) -> float:
        """Read float value."""
        return checkFloat(self._value(section, option), default)

    def getBool(self, section: str | None, option: str, default: bool) -> bool:
        """Read boolean value."""
        return checkBool(self._value(section, option), default)

    def getPath(self, section: str | None, option: str, default: Path) -> Path:
        """Read a Path value."""
        return checkPath(self._value(section, option), default)

    def getStrList(self, section: str | None, option: str, default: list[str]) -> list[str]:
        """Read string list, keeping the length of the default."""
        result = default.copy() if isinstance(default, list) else []
        data = self._value(section, option)
        if isinstance(data, list):
            for i in range(min(len(data), len(result))):
                result[i] = str(data[i])
        return result

    def getIntList(self, section: str | None, option: str, default: list[int]) -> list[int]:
        """Read integer list, keeping the length of the default."""
        result = default.copy() if isinstance(default, list) else []
        data = self._value(section, option)
        if isinstance(data, list):
            for i in range(min(len(data), len(result))):
                result[i] = checkInt(data[i], result[i])
        return result

    def getEnum(self, section: str | None, option: str, default: _T_Enum) -> _T_Enum:
        """Read enum value."""
        data = self._value(section, option)
        if isinstance(data, str):
            return type(default).__members__.get(data.upper(), default)
        return default

    ##
    # Internal Functions
    ##

    def _value(self, section: str | None, option: str) -> T_TomlValue | None:
        """Look up a raw value, or None if the section or option is unset."""
        return (self._data.get(section, {}) if section else self._root).get(option)

    @staticmethod
    def _filterSection(section: str, values: dict) -> T_TomlObject:
        """Drop any further nested tables from a section, which aren't
        supported, logging each one that is dropped.
        """
        entry: T_TomlObject = {}
        for key, value in values.items():
            if isinstance(value, dict):
                logger.error("Invalid config entry '%s.%s', nested tables are not supported", section, key)
                continue
            entry[key] = value
        return entry

    @staticmethod
    def _filterRoot(values: dict) -> T_TomlObject:
        """Drop any tables from a flat, section-less document, which
        aren't supported, logging each one that is dropped.
        """
        entry: T_TomlObject = {}
        for key, value in values.items():
            if isinstance(value, dict):
                logger.error("Invalid config entry '%s', sections are not supported in flat mode", key)
                continue
            entry[key] = value
        return entry

    @staticmethod
    def _dump(value: T_TomlValue) -> str:
        """Format a value as a TOML literal."""
        if isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return "[" + ", ".join(NTomlParser._dump(v) for v in value) + "]"
        elif isinstance(value, Enum):
            return f'"{value.name}"'
        elif isinstance(value, QFont):
            return f'"{value.toString()}"'
        return NTomlParser._dumpStr(str(value))

    @staticmethod
    def _dumpStr(value: str) -> str:
        """Format a string as a quoted TOML basic string."""
        escaped = (
            value
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\t", "\\t")
            .replace("\n", "\\n")
            .replace("\r", "\\r")
        )
        return f'"{escaped}"'
