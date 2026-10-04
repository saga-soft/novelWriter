"""
novelWriter - Project Data
==========================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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
import uuid

from datetime import date
from typing import TYPE_CHECKING, Any, Literal

from novelwriter import CONFIG
from novelwriter.common import (
    checkBool,
    checkDateNone,
    checkInt,
    checkStringNone,
    checkUuid,
    isHandle,
    makeFileNameSafe,
    simplified,
)
from novelwriter.core.status import ItemStatus

if TYPE_CHECKING:
    from collections.abc import Sequence

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

T_LastHandle = Literal["editor", "viewer", "novel", "story"]


class ProjectData:
    """Core: Project Data Class.

    The class holds all project data from the main XML file, aside from
    the list of project items.
    """

    __slots__ = (
        "_author",
        "_autoCount",
        "_autoReplace",
        "_currCounts",
        "_dailyGoal",
        "_dailyGoalAuto",
        "_dailyLastCount",
        "_dailyLastDate",
        "_dailyProgress",
        "_doBackup",
        "_editTime",
        "_import",
        "_indexRevision",
        "_initCounts",
        "_language",
        "_lastHandle",
        "_name",
        "_project",
        "_remainingCount",
        "_saveCount",
        "_spellCheck",
        "_spellLang",
        "_status",
        "_targetCount",
        "_targetCountChars",
        "_targetDeadline",
        "_targetLastCount",
        "_targetSkipRoots",
        "_titleFormat",
        "_uuid",
    )

    def __init__(self, project: NWProject) -> None:

        self._project = project

        # Project Meta
        self._uuid = ""
        self._name = ""
        self._author = ""
        self._saveCount = 0
        self._autoCount = 0
        self._editTime = 0
        self._indexRevision = 0

        # Project Settings
        self._doBackup = True
        self._language = None
        self._spellCheck = False
        self._spellLang = None

        # Writing Target
        self._targetCount = 0
        self._targetCountChars = CONFIG.useCharCount
        self._targetLastCount = 0
        self._targetDeadline = None
        self._targetSkipRoots: set[str] = set()
        self._remainingCount = 0
        self._dailyGoal = 0
        self._dailyGoalAuto = False
        self._dailyProgress = 0
        self._dailyLastCount = 0
        self._dailyLastDate = None

        # Project Dictionaries
        self._initCounts = [0, 0, 0, 0]
        self._currCounts = [0, 0, 0, 0]
        self._lastHandle: dict[str, str | None] = {
            "editor": None,
            "viewer": None,
            "novel": None,
            "story": None,
        }
        self._autoReplace: dict[str, str] = {}
        self._titleFormat: dict[str, str] = {
            "title": "%title%",
            "chapter": "%title%",
            "unnumbered": "%title%",
            "scene": "* * *",
            "section": "",
        }

        self._status = ItemStatus(ItemStatus.STATUS)
        self._import = ItemStatus(ItemStatus.IMPORT)

    ##
    #  Properties
    ##

    @property
    def uuid(self) -> str:
        """Return the project ID."""
        return self._uuid

    @property
    def name(self) -> str:
        """Return the project name."""
        return self._name

    @property
    def fileSafeName(self) -> str:
        """Return the project name in a file name safe format."""
        return makeFileNameSafe(self._name)

    @property
    def author(self) -> str:
        """Return the project author."""
        return self._author

    @property
    def saveCount(self) -> int:
        """Return the count of project saves."""
        return self._saveCount

    @property
    def autoCount(self) -> int:
        """Return the count of project auto-saves."""
        return self._autoCount

    @property
    def editTime(self) -> int:
        """Return the number of seconds the project has been edited."""
        return self._editTime

    @property
    def indexRevision(self) -> int:
        """Return the last known index revision number."""
        return self._indexRevision

    @property
    def doBackup(self) -> bool:
        """Return the backup setting."""
        return self._doBackup

    @property
    def targetCount(self) -> int:
        """Return the project goal."""
        return self._targetCount

    @property
    def targetCountChars(self) -> bool:
        """Return the project goal count type."""
        return self._targetCountChars

    @property
    def targetLastCount(self) -> int:
        """Return the last recorded target count."""
        return self._targetLastCount

    @property
    def targetDeadline(self) -> date | None:
        """Return the project deadline."""
        return self._targetDeadline

    @property
    def targetSkipRoots(self) -> set[str]:
        """Return the set of target skip root handles."""
        return self._targetSkipRoots

    @property
    def dailyGoal(self) -> int:
        """Return the daily goal."""
        return self._dailyGoal

    @property
    def dailyGoalAuto(self) -> bool:
        """Return the automatic daily goal setting."""
        return self._dailyGoalAuto

    @property
    def dailyLastCount(self) -> int:
        """Return the current daily goal."""
        return self._dailyLastCount

    @property
    def dailyProgress(self) -> int:
        """Return the current daily progress."""
        return self._dailyProgress

    @property
    def language(self) -> str | None:
        """Return the project language setting."""
        return self._language

    @property
    def spellCheck(self) -> bool:
        """Return the spell check enabled setting."""
        return self._spellCheck

    @property
    def spellLang(self) -> str | None:
        """Return the spell check language."""
        return self._spellLang

    @property
    def initCounts(self) -> tuple[int, int, int, int]:
        """Return the initial count of words and characters for novel
        and note documents.
        """
        return self._initCounts[0], self._initCounts[1], self._initCounts[2], self._initCounts[3]

    @property
    def currCounts(self) -> tuple[int, int, int, int]:
        """Return the current count of words and characters for novel
        and note documents.
        """
        return self._currCounts[0], self._currCounts[1], self._currCounts[2], self._currCounts[3]

    @property
    def lastHandle(self) -> dict[str, str | None]:
        """Return the dictionary of last used handles for various
        components of the GUI.
        """
        return self._lastHandle

    @property
    def autoReplace(self) -> dict[str, str]:
        """Return the auto-replace dictionary."""
        return self._autoReplace

    @property
    def itemStatus(self) -> ItemStatus:
        """Return the status settings object."""
        return self._status

    @property
    def itemImport(self) -> ItemStatus:
        """Return the importance settings object."""
        return self._import

    ##
    #  Methods
    ##

    def incSaveCount(self) -> None:
        """Increment the save count by one."""
        self._saveCount += 1
        self._project.setProjectChanged(True)

    def incAutoCount(self) -> None:
        """Increment the auto save count by one."""
        self._autoCount += 1
        self._project.setProjectChanged(True)

    ##
    #  Getters
    ##

    def getLastHandle(self, component: str) -> str | None:
        """Retrieve the last used handle for a given component."""
        return self._lastHandle.get(component, None)

    def getEffectiveDailyGoal(self) -> int:
        """Return the effective daily goal, which is either the set daily
        goal or the automatically calculated goal based on project target
        and deadline.
        """
        if (
            self._dailyGoalAuto
            and self._remainingCount > 0
            and self._targetDeadline is not None
            and self._targetDeadline >= date.today()
        ):
            return self._remainingCount // ((self._targetDeadline - date.today()).days + 1)
        return self._dailyGoal

    ##
    #  Setters
    ##

    def setUuid(self, value: Any) -> None:
        """Set the project id."""
        value = checkUuid(value, "")
        if not value:
            self._uuid = str(uuid.uuid4())
        elif value != self._uuid:
            self._uuid = value
            self._project.setProjectChanged(True)

    def setName(self, value: str | None) -> None:
        """Set a new project name."""
        if value != self._name:
            self._name = simplified(str(value or ""))
            self._project.setProjectChanged(True)

    def setAuthor(self, value: str | None) -> None:
        """Set the author value."""
        if value != self._author:
            self._author = simplified(str(value or ""))
            self._project.setProjectChanged(True)

    def setSaveCount(self, value: Any) -> None:
        """Set the save count from last session."""
        self._saveCount = checkInt(value, 0)
        self._project.setProjectChanged(True)

    def setAutoCount(self, value: Any) -> None:
        """Set the auto save count from last session."""
        self._autoCount = checkInt(value, 0)
        self._project.setProjectChanged(True)

    def setEditTime(self, value: Any) -> None:
        """Set the edit time from last session."""
        self._editTime = checkInt(value, 0)
        self._project.setProjectChanged(True)

    def setIndexRevision(self, value: Any) -> None:
        """Set the index revision number from last session."""
        self._indexRevision = checkInt(value, 0)

    def setDoBackup(self, value: Any) -> None:
        """Set the do write backup flag."""
        if value != self._doBackup:
            self._doBackup = checkBool(value, False)
            self._project.setProjectChanged(True)

    def setProjectTarget(self, count: str | int | None, deadline: str | date | None, countChars: bool) -> None:
        """Set the project goal."""
        if (
            (updateCounts := countChars != self._targetCountChars)
            or count != self._targetCount
            or deadline != self._targetDeadline
        ):
            self._targetCount = checkInt(count, 0)
            self._targetDeadline = checkDateNone(deadline, None)
            self._targetCountChars = checkBool(countChars, True)
            self._project.setProjectChanged(True)
            if updateCounts:
                self._project.markCountsDirty()

    def setTargetSkipRoots(self, updated: list[str]) -> None:
        """Set the target skip root handles dictionary."""
        skipRoots = {str(handle) for handle in updated}
        if skipRoots != self._targetSkipRoots:
            self._targetSkipRoots = skipRoots
            self._project.updateCounts()
            self._project.setProjectChanged(True)

    def setDailyTarget(self, value: Any, auto: Any) -> None:
        """Set the daily goal."""
        if value != self._dailyGoal or auto != self._dailyGoalAuto:
            self._dailyGoal = checkInt(value, 0)
            self._dailyGoalAuto = checkBool(auto, False)
            self._project.setProjectChanged(True)

    def setDailyProgress(self, session: int, target: int) -> None:
        """Set the current daily and project goal progress."""
        if self._dailyLastDate != date.today():
            # The date has changed since the last update or was not set.
            # In either case, we shift to a new day with new counts.
            self._dailyLastCount -= self._dailyProgress
            self._dailyLastDate = date.today()

        self._dailyProgress = self._dailyLastCount + session
        self._remainingCount = self._targetCount - (target - self._dailyProgress)
        self._targetLastCount = target

    def setLanguage(self, value: str | None) -> None:
        """Set the project language."""
        if value != self._language:
            self._language = checkStringNone(value, None)
            self._project.setProjectChanged(True)

    def setSpellCheck(self, value: Any) -> None:
        """Set the spell check flag."""
        if value != self._spellCheck:
            self._spellCheck = checkBool(value, False)
            self._project.setProjectChanged(True)

    def setSpellLang(self, value: str | None) -> None:
        """Set the spell check language."""
        if value != self._spellLang:
            self._spellLang = checkStringNone(value, None)
            self._project.setProjectChanged(True)

    def setLastHandle(self, value: str | None, component: T_LastHandle) -> None:
        """Set a last used handle into the handle registry for a given
        component.
        """
        if isinstance(component, str):
            self._lastHandle[component] = checkStringNone(value, None)
            self._project.setProjectChanged(True)

    def setCurrCounts(self, wNovel: Any = None, wNotes: Any = None, cNovel: Any = None, cNotes: Any = None) -> None:
        """Set the count totals for novel and note files."""
        if wNovel is not None:
            self._currCounts[0] = checkInt(wNovel, 0)
        if wNotes is not None:
            self._currCounts[1] = checkInt(wNotes, 0)
        if cNovel is not None:
            self._currCounts[2] = checkInt(cNovel, 0)
        if cNotes is not None:
            self._currCounts[3] = checkInt(cNotes, 0)

    def setAutoReplace(self, value: dict) -> None:
        """Set the auto-replace dictionary."""
        if isinstance(value, dict):
            self._autoReplace = {}
            for key, entry in value.items():
                if isinstance(key, str) and isinstance(entry, str) and (cleanKey := simplified(key)):
                    self._autoReplace[cleanKey] = simplified(entry)
            self._project.setProjectChanged(True)

    ##
    #  XML Init Setters
    ##

    def setInitLastHandles(self, value: Any) -> None:
        """Set the full last handles dictionary to a new set of values.
        This is intended to be used at project load.
        """
        if isinstance(value, dict):
            for key, entry in value.items():
                if key in self._lastHandle:
                    self._lastHandle[key] = str(entry) if isHandle(entry) else None
            self._project.setProjectChanged(True)

    def setInitTargetSkipRoots(self, value: Sequence[str]) -> None:
        """Set the initial target skip root handles dictionary."""
        self._targetSkipRoots = {str(handle) for handle in value}

    def setInitDailyTarget(self, value: Any, last: Any) -> None:
        """Set the initial daily goal."""
        if (lastDate := checkDateNone(last, None)) == date.today():
            self._dailyLastCount = checkInt(value, self._dailyLastCount)
            self._dailyLastDate = lastDate
        else:
            self._dailyLastCount = 0
            self._dailyLastDate = date.today()

    def setInitCounts(self, wNovel: Any = None, wNotes: Any = None, cNovel: Any = None, cNotes: Any = None) -> None:
        """Set the count totals for novel and note files."""
        if wNovel is not None:
            count = checkInt(wNovel, 0)
            self._initCounts[0] = count
            self._currCounts[0] = count
        if wNotes is not None:
            count = checkInt(wNotes, 0)
            self._initCounts[1] = count
            self._currCounts[1] = count
        if cNovel is not None:
            count = checkInt(cNovel, 0)
            self._initCounts[2] = count
            self._currCounts[2] = count
        if cNotes is not None:
            count = checkInt(cNotes, 0)
            self._initCounts[3] = count
            self._currCounts[3] = count

    ##
    #  Methods
    ##

    def resetDailyProgress(self) -> None:
        """Reset the daily progress counter to zero without affecting
        the overall project target progress.
        """
        self._dailyLastDate = date.today()
        self._dailyLastCount -= self._dailyProgress
        self._dailyProgress = 0
        self._remainingCount = self._targetCount - self._targetLastCount
        self._project.setProjectChanged(True)
