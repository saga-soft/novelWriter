"""
novelWriter - Project Options Cache
===================================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

import json
import logging

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from novelwriter import SHARED
from novelwriter.common import checkBool, checkFloat, checkInt, checkString, jsonEncode, safeExists
from novelwriter.constants import nwFiles
from novelwriter.error import logException

if TYPE_CHECKING:
    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

_T_Enum = TypeVar("_T_Enum", bound=Enum)

VALID_MAP: dict[str, set[str]] = {
    "GuiWritingStats": {
        "winWidth",
        "winHeight",
        "widthCol0",
        "widthCol1",
        "widthCol2",
        "widthCol3",
        "sortCol",
        "sortOrder",
        "incNovel",
        "incNotes",
        "hideZeros",
        "hideNegative",
        "groupByDay",
        "showIdleTime",
        "histMax",
    },
    "GuiDocSplit": {
        "spLevel",
        "intoFolder",
        "docHierarchy",
    },
    "GuiProjectSettings": {
        "winWidth",
        "winHeight",
        "replaceColW",
        "statusColW",
        "importColW",
    },
    "GuiWordList": {
        "winWidth",
        "winHeight",
    },
    "GuiNovelView": {
        "lastCol",
        "lastColSize",
    },
    "GuiBuildSettings": {
        "winWidth",
        "winHeight",
        "treeWidth",
        "filterWidth",
        "autoPreview",
    },
    "GuiManuscript": {
        "winWidth",
        "winHeight",
        "optsWidth",
        "viewWidth",
        "listHeight",
        "detailsHeight",
        "detailsWidth",
        "detailsExpanded",
        "statsExpanded",
        "showNewPage",
    },
    "GuiManuscriptBuild": {
        "winWidth",
        "winHeight",
        "fmtWidth",
        "sumWidth",
    },
    "GuiDocViewerPanel": {
        "colWidths",
        "hideInactive",
    },
    "GuiNovelDetails": {
        "winWidth",
        "winHeight",
        "widthCol0",
        "widthCol1",
        "widthCol2",
        "widthCol3",
        "widthCol4",
        "wordsPerPage",
        "countFrom",
        "clearDouble",
        "novelRoot",
    },
    "GuiProjectSearch": {
        "searchFilters",
    },
    "GuiStoryOutline": {
        "colWidths",
    },
}


class OptionState:
    """Core: GUI Options Storage.

    A class for storing the state of the GUI. The data is stored per
    project. Settings that should be project-independent are stored in
    the Config instead.
    """

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._state = {}

    ##
    #  Load and Save Cache
    ##

    def loadSettings(self) -> bool:
        """Load the options dictionary from the project."""
        stateFile = self._project.storage.getMetaFile(nwFiles.OPTS_FILE)
        if not isinstance(stateFile, Path):
            return False

        data = {}
        if safeExists(stateFile):
            logger.debug("Loading GUI options file")
            try:
                with open(stateFile, mode="r", encoding="utf-8") as inFile:
                    data = json.load(inFile)
            except Exception:
                logger.error("Failed to load GUI options file")
                logException()
                return False

        # Filter out unused variables
        state = data.get("novelWriter.guiOptions", {})
        for aGroup in state:
            if aGroup in VALID_MAP:
                self._state[aGroup] = {}
                for anOpt in state[aGroup]:
                    if anOpt in VALID_MAP[aGroup]:
                        self._state[aGroup][anOpt] = state[aGroup][anOpt]

        return True

    def saveSettings(self) -> bool:
        """Save the options dictionary to the project."""
        stateFile = self._project.storage.getMetaFile(nwFiles.OPTS_FILE)
        if not isinstance(stateFile, Path):
            return False

        logger.debug("Saving GUI options file")
        try:
            with open(stateFile, mode="w+", encoding="utf-8") as fObj:
                data = {"novelWriter.guiOptions": self._state}
                fObj.write(jsonEncode(data, nmax=4))
        except Exception as exc:
            SHARED.appendErrorMessage(exc)
            logger.error("Failed to save GUI options file")
            logException()
            return False

        return True

    ##
    #  Setters
    ##

    def setValue(self, group: str, name: str, value: Any) -> bool:
        """Save a value, with a given group and name."""
        if group not in VALID_MAP:
            logger.error("Unknown option group '%s'", group)
            return False

        if name not in VALID_MAP[group]:
            logger.error("Unknown option name '%s'", name)
            return False

        if group not in self._state:
            self._state[group] = {}

        if isinstance(value, Enum):
            self._state[group][name] = value.name
        else:
            self._state[group][name] = value

        return True

    ##
    #  Getters
    ##

    def getValue(self, group: str, name: str, default: Any) -> Any:
        """Return an arbitrary type value, if it exists. Otherwise,
        return the default value.
        """
        if group in self._state:
            return self._state[group].get(name, default)
        return default

    def getList(self, group: str, name: str, default: list[Any]) -> list[Any]:
        """Return the value as a list, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state and isinstance(value := self._state[group].get(name, default), list):
            return value
        return default

    def getDict(self, group: str, name: str, default: dict[str, Any]) -> dict[str, Any]:
        """Return the value as a dict, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state and isinstance(value := self._state[group].get(name, default), dict):
            return value
        return default

    def getString(self, group: str, name: str, default: str) -> str:
        """Return the value as a string, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state:
            return checkString(self._state[group].get(name, default), default)
        return default

    def getInt(self, group: str, name: str, default: int) -> int:
        """Return the value as an int, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state:
            return checkInt(self._state[group].get(name, default), default)
        return default

    def getFloat(self, group: str, name: str, default: float) -> float:
        """Return the value as a float, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state:
            return checkFloat(self._state[group].get(name, default), default)
        return default

    def getBool(self, group: str, name: str, default: bool) -> bool:
        """Return the value as a bool, if it exists. Otherwise, return
        the default value.
        """
        if group in self._state:
            return checkBool(self._state[group].get(name, default), default)
        return default

    def getEnum(self, group: str, name: str, lookup: type, default: _T_Enum) -> _T_Enum:
        """Return the value mapped to an enum. Otherwise return the
        default value.
        """
        if issubclass(lookup, type(default)) and group in self._state and name in self._state[group]:
            value = self._state[group][name]
            if value in lookup.__members__:
                return lookup[value]
        return default
