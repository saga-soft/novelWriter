"""
novelWriter - Story View Settings
=================================

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

import json
import logging
import uuid

from pathlib import Path
from typing import TYPE_CHECKING, Any, NamedTuple, Self

from PyQt6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication

from novelwriter.common import checkUuid, jsonEncode, safeExists
from novelwriter.constants import nwFiles, nwKeyWords
from novelwriter.enum import nwComment
from novelwriter.error import logException
from novelwriter.text.formats import MODIFIERS

if TYPE_CHECKING:
    from collections.abc import Iterable

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

T_ViewValue = str | int | float | bool

COMMENT_SYNOPSIS = "synopsis"
MAX_COLUMN_KEYS = 5

# The Settings Template
# =====================
# Each entry contains a tuple on the form: (type, default)

# fmt: off
SETTINGS_TEMPLATE: dict[str, tuple[type, T_ViewValue]] = {
    "outline.syntaxColors":    (bool, False),
    "outline.rowLines":        (int, 3),

    "outline.showParts":       (bool, True),
    "outline.showScenes":      (bool, True),
    "outline.showChapters":    (bool, True),
    "outline.showSections":    (bool, False),

    "outline.showProgress":    (bool, True),
    "outline.countPerPage":    (int, 350),
    "outline.clearDoublePage": (bool, True),
    "outline.useTargetCount":  (bool, True),
}

SETTINGS_LABELS = {
    "outline.defaultName":     QT_TRANSLATE_NOOP("StoryViews", "Outline"),

    "outline.grpAppearance":   QT_TRANSLATE_NOOP("StoryViews", "Appearance"),
    "outline.syntaxColors":    QT_TRANSLATE_NOOP("StoryViews", "Use syntax colours"),
    "outline.rowLines":        QT_TRANSLATE_NOOP("StoryViews", "Row height"),

    "outline.grpDocuments":    QT_TRANSLATE_NOOP("StoryViews", "Documents"),
    "outline.showParts":       QT_TRANSLATE_NOOP("StoryViews", "Show partitions"),
    "outline.showChapters":    QT_TRANSLATE_NOOP("StoryViews", "Show chapters"),
    "outline.showScenes":      QT_TRANSLATE_NOOP("StoryViews", "Show scenes"),
    "outline.showSections":    QT_TRANSLATE_NOOP("StoryViews", "Show sections"),

    "outline.grpProgress":     QT_TRANSLATE_NOOP("StoryViews", "Progression"),
    "outline.showProgress":    QT_TRANSLATE_NOOP("StoryViews", "Show story progression"),
    "outline.countPerPage":    QT_TRANSLATE_NOOP("StoryViews", "Count per page"),
    "outline.clearDoublePage": QT_TRANSLATE_NOOP("StoryViews", "Clear double page"),
    "outline.useTargetCount":  QT_TRANSLATE_NOOP("StoryViews", "Relative to project target"),

    "outline.pgColumns":       QT_TRANSLATE_NOOP("StoryViews", "Columns"),

    "outline.defCharacters":   QT_TRANSLATE_NOOP("StoryViews", "Characters"),
    "outline.defPlot":         QT_TRANSLATE_NOOP("StoryViews", "Plot"),
    "outline.defWorld":        QT_TRANSLATE_NOOP("StoryViews", "World"),
    "outline.defComments":     QT_TRANSLATE_NOOP("StoryViews", "Comments"),
}
# fmt: on


def newColumnID() -> str:
    """Generate a new short outline column ID."""
    return uuid.uuid4().hex[:8]


def isColumnKey(key: str) -> bool:
    """Check if a key is a valid outline column key."""
    if key in nwKeyWords.CAN_LOOKUP:
        return True
    modifier, _, name = key.partition(".")
    match MODIFIERS.get(modifier):
        case nwComment.SYNOPSIS:
            return not name
        case nwComment.STORY | nwComment.NOTE:
            return bool(name)
    return False


class StoryViewSettings:
    """Story: Story View Settings Class.

    The settings of a single story view, packed to and from JSON.
    """

    __slots__ = ("_changed", "_name", "_order", "_prefix", "_settings", "_state", "_stateChanged", "_uuid")

    KIND = "none"

    def __init__(self) -> None:
        self._prefix = f"{self.KIND}."
        self._changed = False
        self._stateChanged = False

        self._name = self.defaultName
        self._uuid = str(uuid.uuid4())
        self._order = 0
        self._settings = {k: v[1] for k, v in SETTINGS_TEMPLATE.items() if k.startswith(self._prefix)}
        self._state: dict[str, Any] = {}

    @classmethod
    def fromDict(cls, data: dict) -> StoryViewSettings | None:
        """Create a story view settings object from a dict."""
        match data.get("kind"):
            case "outline":
                new = OutlineViewSettings()
            case _:
                return None
        new.unpack(data)
        return new

    ##
    #  Properties
    ##

    @property
    def name(self) -> str:
        """Return the story view name."""
        return self._name

    @property
    def defaultName(self) -> str:
        """Return the story view default name."""
        return QCoreApplication.translate("StoryViews", SETTINGS_LABELS.get(f"{self.KIND}.defaultName", "None"))

    @property
    def viewID(self) -> str:
        """Return the view ID as a UUID."""
        return self._uuid

    @property
    def order(self) -> int:
        """Return the story view order."""
        return self._order

    @property
    def changed(self) -> bool:
        """The changed status of the story view."""
        return self._changed

    @property
    def stateChanged(self) -> bool:
        """The changed status of the story view state."""
        return self._stateChanged

    ##
    #  Setters
    ##

    def setName(self, name: str) -> None:
        """Set the story view display name."""
        self._name = str(name)

    def setViewID(self, value: str | uuid.UUID) -> None:
        """Set a UUID view ID, or generate one if invalid."""
        self._uuid = checkUuid(value, "") or str(uuid.uuid4())

    def setOrder(self, value: int) -> None:
        """Set the story view order."""
        if isinstance(value, int):
            self._order = value

    def setState(self, key: str, value: Any) -> None:
        """Set a JSON compatible view state value, validated by the view."""
        old = self._state.get(key)
        if isinstance(value, dict) and isinstance(old, dict):
            # Dict equality ignores order, which is part of the state
            changed = list(value.items()) != list(old.items())
        else:
            changed = value != old
        if changed:
            self._state[key] = value
            self._stateChanged = True

    def setValue(self, key: str, value: T_ViewValue) -> None:
        """Set a specific value for a story view setting."""
        if (d := SETTINGS_TEMPLATE.get(key)) and isinstance(value, d[0]):
            self._changed |= value != self._settings[key]
            self._settings[key] = value

    ##
    #  Getters
    ##

    @staticmethod
    def getLabel(key: str) -> str:
        """Extract the GUI label for a specific setting."""
        return QCoreApplication.translate("StoryViews", SETTINGS_LABELS.get(key, "ERROR"))

    def getState(self, key: str) -> Any:
        """Return a view state value, or None if not set."""
        return self._state.get(key)

    def getBool(self, key: str) -> bool:
        """Type safe value access for bools."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return bool(value)

    def getInt(self, key: str) -> int:
        """Type safe value access for integers."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return int(value) if isinstance(value, int | float) else 0

    ##
    #  Methods
    ##

    def resetChangedState(self) -> None:
        """Reset the changed status of the settings object."""
        self._changed = False
        self._stateChanged = False

    def updateSettings(self, source: StoryViewSettings) -> None:
        """Update the name and settings values from another object."""
        self._name = source.name
        self._settings = source._settings.copy()

    def copy(self) -> Self:
        """Return an identical copy of the settings."""
        new = type(self)()
        new.unpack(self.pack())
        return new

    def pack(self) -> dict:
        """Pack all content into a JSON compatible dictionary."""
        logger.debug("Collecting story view setting for '%s'", self._name)
        return {
            "kind": self.KIND,
            "name": self._name,
            "uuid": self._uuid,
            "order": self._order,
            "settings": self._settings.copy(),
            "state": self._state.copy(),
        }

    def unpack(self, data: dict) -> None:
        """Unpack a dictionary and populate the class."""
        settings = data.get("settings", {})
        state = data.get("state", {})

        self.setName(data.get("name", ""))
        self.setViewID(data.get("uuid", ""))
        self.setOrder(data.get("order", 0))

        self._settings = {k: v[1] for k, v in SETTINGS_TEMPLATE.items() if k.startswith(self._prefix)}
        if isinstance(settings, dict):
            for key, value in settings.items():
                if isinstance(key, str) and key.startswith(self._prefix) and isinstance(value, T_ViewValue):
                    self.setValue(key, value)

        self._state = state.copy() if isinstance(state, dict) else {}
        self._changed = False
        self._stateChanged = False

    @classmethod
    def duplicate(cls, source: StoryViewSettings) -> StoryViewSettings:
        """Make a copy of another story view."""
        new = source.copy()
        new.setViewID("")
        new.setName(f"{source.name} 2")
        return new


class OutlineColumn(NamedTuple):
    """Story: Outline Column."""

    cid: str
    name: str
    keys: tuple[str, ...]


class OutlineViewSettings(StoryViewSettings):
    """Story: Outline View Settings Class."""

    __slots__ = ("_columns",)

    KIND = "outline"

    def __init__(self) -> None:
        super().__init__()
        self._columns = self._defaultColumns()

    ##
    #  Properties
    ##

    @property
    def columns(self) -> list[OutlineColumn]:
        """Return the outline columns."""
        return self._columns.copy()

    ##
    #  Setters
    ##

    def setColumns(self, columns: list[OutlineColumn]) -> None:
        """Set the outline columns. A new order alone is not a change."""
        columns = self._checkColumns([{"id": c.cid, "name": c.name, "keys": c.keys} for c in columns])
        self._changed |= set(columns) != set(self._columns)
        self._columns = columns

    ##
    #  Methods
    ##

    def updateSettings(self, source: StoryViewSettings) -> None:
        """Update the name, settings values and outline columns."""
        super().updateSettings(source)
        if isinstance(source, OutlineViewSettings):  # pragma: no branch
            self._columns = source.columns

    def pack(self) -> dict:
        """Pack all content into a JSON compatible dictionary."""
        data = super().pack()
        data["columns"] = [{"id": c.cid, "name": c.name, "keys": list(c.keys)} for c in self._columns]
        return data

    def unpack(self, data: dict) -> None:
        """Unpack a dictionary and populate the class."""
        super().unpack(data)
        columns = data.get("columns")
        if isinstance(columns, list):
            self._columns = self._checkColumns([c for c in columns if isinstance(c, dict)])
        else:
            self._columns = self._defaultColumns()

    ##
    #  Internal Functions
    ##

    def _defaultColumns(self) -> list[OutlineColumn]:
        """Return the default outline columns."""
        return [
            OutlineColumn(
                newColumnID(),
                self.getLabel("outline.defCharacters"),
                (nwKeyWords.POV_KEY, nwKeyWords.FOCUS_KEY, nwKeyWords.CHAR_KEY),
            ),
            OutlineColumn(
                newColumnID(),
                self.getLabel("outline.defPlot"),
                (nwKeyWords.PLOT_KEY, nwKeyWords.TIME_KEY),
            ),
            OutlineColumn(
                newColumnID(),
                self.getLabel("outline.defWorld"),
                (nwKeyWords.WORLD_KEY,),
            ),
            OutlineColumn(
                newColumnID(),
                self.getLabel("outline.defComments"),
                (COMMENT_SYNOPSIS,),
            ),
        ]

    @staticmethod
    def _checkColumns(entries: list[dict]) -> list[OutlineColumn]:
        """Return valid outline columns, with unique IDs and keys."""
        columns = []
        ids = set()
        used = set()
        for entry in entries:
            cid = entry.get("id")
            name = entry.get("name")
            keys = entry.get("keys")
            if not isinstance(name, str) or not isinstance(keys, list | tuple):
                continue
            if not isinstance(cid, str) or not cid or cid in ids:
                cid = newColumnID()
            valid = []
            for key in keys:
                if isinstance(key, str) and isColumnKey(key := key.lower()) and key not in used:
                    valid.append(key)
                    used.add(key)
            ids.add(cid)
            columns.append(OutlineColumn(cid, name, tuple(valid[:MAX_COLUMN_KEYS])))
        return columns


class StoryViewCollection:
    """Story: Story View Collection Class.

    All story views of a project, saved as a single JSON file.
    """

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._lastView = ""
        self._highlight = ""
        self._views: dict[str, StoryViewSettings] = {}
        self._unknown: dict[str, dict] = {}
        self._loadCollection()

    def __len__(self) -> int:
        """Return the number of story views."""
        return len(self._views)

    ##
    #  Properties
    ##

    @property
    def lastView(self) -> str:
        """Return the last active view ID."""
        return self._lastView

    @property
    def highlight(self) -> str:
        """Return the highlighted reference tag key."""
        return self._highlight

    ##
    #  Getters
    ##

    def getStoryView(self, viewID: str) -> StoryViewSettings | None:
        """Get a specific story views settings object."""
        return self._views.get(viewID, None)

    ##
    #  Setters
    ##

    def setStoryView(self, view: StoryViewSettings) -> None:
        """Set story views settings data in the collection."""
        if isinstance(view, StoryViewSettings):
            self._views[view.viewID] = view
            self._saveCollection()

    def setStoryViewsState(self, lastView: str, highlight: str, order: list[str]) -> None:
        """Set the last view, the highlight and the view order, and save
        if anything changed.
        """
        changed = (
            lastView != self._lastView
            or highlight != self._highlight
            or any(v.stateChanged for v in self._views.values())
        )
        self._lastView = lastView
        self._highlight = highlight
        for i, key in enumerate(order):
            if (view := self._views.get(key)) and view.order != i:
                view.setOrder(i)
                changed = True
        if changed:
            self._saveCollection()
            for view in self._views.values():
                view.resetChangedState()

    ##
    #  Methods
    ##

    def removeStoryView(self, viewID: str) -> None:
        """Remove a story view from the collection."""
        self._views.pop(viewID, None)
        self._saveCollection()

    def storyViews(self) -> Iterable[StoryViewSettings]:
        """Iterate over all available story views."""
        yield from sorted(self._views.values(), key=lambda x: x.order)

    ##
    #  Internal Functions
    ##

    def _loadCollection(self) -> bool:
        """Load story view collections file."""
        viewsFile = self._project.storage.getMetaFile(nwFiles.VIEWS_FILE)
        if not isinstance(viewsFile, Path):
            return False
        if not safeExists(viewsFile):
            return True

        logger.debug("Loading story views file")
        try:
            with open(viewsFile, mode="r", encoding="utf-8") as inFile:
                data = json.load(inFile)
        except Exception:
            logger.error("Failed to load story views file")
            logException()
            return False

        if not isinstance(data, dict):
            logger.error("Story views file is not a JSON object")
            return False

        views = data.get("novelWriter.storyViews", None)
        if not isinstance(views, dict):
            logger.error("No novelWriter.storyViews in the story views file")
            return False

        for key, entry in views.items():
            if key == "lastView":
                self._lastView = str(entry)
            elif key == "highlight":
                self._highlight = str(entry)
            elif isinstance(entry, dict):
                if view := StoryViewSettings.fromDict(entry):
                    self._views[view.viewID] = view
                else:
                    # Preserve views from newer versions
                    logger.warning("Unknown story view kind '%s'", entry.get("kind"))
                    self._unknown[key] = entry

        return True

    def _saveCollection(self) -> bool:
        """Save story view collections file."""
        viewsFile = self._project.storage.getMetaFile(nwFiles.VIEWS_FILE)
        if not isinstance(viewsFile, Path):
            return False

        logger.debug("Saving story views file")
        try:
            data: dict[str, str | dict] = {
                "lastView": self._lastView,
                "highlight": self._highlight,
            }
            data.update(self._unknown)
            data.update({k: v.pack() for k, v in self._views.items()})
            with open(viewsFile, mode="w+", encoding="utf-8") as outFile:
                outFile.write(jsonEncode({"novelWriter.storyViews": data}, nmax=4))
        except Exception:
            logger.error("Failed to save story views file")
            logException()
            return False

        return True
