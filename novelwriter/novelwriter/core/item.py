"""
novelWriter - Project Item
==========================

This file is a part of novelWriter
Copyright (C) 2018 Veronica Berglyd Olsen and novelWriter contributors

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

from typing import TYPE_CHECKING, Any

from novelwriter import CONFIG, SHARED
from novelwriter.common import checkInt, isHandle, isItemClass, isItemLayout, isItemType, simplified, yesNo
from novelwriter.constants import nwLabels, nwStyles, trConst
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType

if TYPE_CHECKING:
    from PyQt6.QtGui import QFont, QIcon

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)


class ProjectItem:
    """Core: Item Data Class.

    This class holds all the project information about a project item.
    Each item must be associated with a project and have a valid handle.
    Only the ProjectTree class should create instances of this class,
    and must ensure that the handle is valid for all items in the tree.
    """

    __slots__ = (
        "_active",
        "_charCount",
        "_charInit",
        "_class",
        "_cursorPos",
        "_dailyTarget",
        "_expanded",
        "_handle",
        "_heading",
        "_import",
        "_layout",
        "_name",
        "_order",
        "_paraCount",
        "_parent",
        "_project",
        "_root",
        "_status",
        "_type",
        "_wordCount",
        "_wordInit",
    )

    def __init__(self, project: NWProject, handle: str) -> None:

        self._project = project
        self._name = ""
        self._handle = handle
        self._parent = None
        self._root = None
        self._order = 0
        self._type = nwItemType.NO_TYPE
        self._class = nwItemClass.NO_CLASS
        self._layout = nwItemLayout.NO_LAYOUT
        self._status = None
        self._import = None
        self._active = True
        self._expanded = False

        # Document Meta Data
        self._heading = "H0"  # The main heading
        self._charCount = 0  # Current character count
        self._wordCount = 0  # Current word count
        self._paraCount = 0  # Current paragraph count
        self._cursorPos = 0  # Last cursor position
        self._charInit = 0  # Initial character count
        self._wordInit = 0  # Initial word count

        # Internals
        self._dailyTarget = False  # Whether the item is included in the project goal

    def __repr__(self) -> str:
        """Return a string representation of the item."""
        return f"<ProjectItem handle={self._handle}, parent={self._parent}, name='{self._name}'>"

    def __bool__(self) -> bool:
        """Check the truthiness of the class. The handle used to be
        initiated to None, but this is no longer the case. It should
        always evaluate to True since 2.1-beta1, although unpack and the
        ProjectTree class can leave it as an empty string.
        """
        return bool(self._handle)

    ##
    #  Properties
    ##

    @property
    def itemName(self) -> str:
        return self._name

    @property
    def itemHandle(self) -> str:
        return self._handle

    @property
    def itemParent(self) -> str | None:
        return self._parent

    @property
    def itemRoot(self) -> str | None:
        return self._root

    @property
    def itemOrder(self) -> int:
        return self._order

    @property
    def itemType(self) -> nwItemType:
        return self._type

    @property
    def itemClass(self) -> nwItemClass:
        return self._class

    @property
    def itemLayout(self) -> nwItemLayout:
        return self._layout

    @property
    def itemStatus(self) -> str | None:
        return self._status

    @property
    def itemImport(self) -> str | None:
        return self._import

    @property
    def isActive(self) -> bool:
        return self._active

    @property
    def isExpanded(self) -> bool:
        return self._expanded

    @property
    def mainHeading(self) -> str:
        return self._heading

    @property
    def charCount(self) -> int:
        return self._charCount

    @property
    def wordCount(self) -> int:
        return self._wordCount

    @property
    def paraCount(self) -> int:
        return self._paraCount

    @property
    def mainCount(self) -> int:
        return self._charCount if CONFIG.useCharCount else self._wordCount

    @property
    def initCount(self) -> int:
        return self._charInit if CONFIG.useCharCount else self._wordInit

    @property
    def cursorPos(self) -> int:
        return self._cursorPos

    ##
    #  Pack/Unpack/Duplicate Data
    ##

    def pack(self) -> dict:
        """Pack all the data in the class instance into a dictionary."""
        item: dict[str, str] = {}
        meta: dict[str, str] = {}
        name: dict[str, str] = {}

        item["handle"] = str(self._handle)
        item["parent"] = str(self._parent)
        item["root"] = str(self._root)
        item["order"] = str(self._order)
        item["type"] = str(self._type.name)
        item["class"] = str(self._class.name)
        meta["expanded"] = yesNo(self._expanded)
        name["status"] = str(self._status)
        name["import"] = str(self._import)

        if self._type == nwItemType.FILE:
            item["layout"] = str(self._layout.name)
            meta["heading"] = str(self._heading)
            meta["charCount"] = str(self._charCount)
            meta["wordCount"] = str(self._wordCount)
            meta["paraCount"] = str(self._paraCount)
            meta["cursorPos"] = str(self._cursorPos)
            name["active"] = yesNo(self._active)

        return {
            "name": str(self._name),
            "itemAttr": item,
            "metaAttr": meta,
            "nameAttr": name,
        }

    def unpack(self, data: dict) -> bool:
        """Set the values from a data dictionary."""
        item = data.get("itemAttr", {})
        meta = data.get("metaAttr", {})
        name = data.get("nameAttr", {})

        handle = item.get("handle", "")
        if isHandle(handle):
            self._handle = handle
        else:
            logger.error("Item does not have a handle")
            return False

        self.setName(data.get("name", ""))
        self.setParent(item.get("parent", None))
        self.setRoot(item.get("root", None))
        self.setOrder(item.get("order", 0))
        self.setType(item.get("type", nwItemType.NO_TYPE))
        self.setClass(item.get("class", nwItemClass.NO_CLASS))
        self.setExpanded(meta.get("expanded", False))
        self.setStatus(name.get("status", None))
        self.setImport(name.get("import", None))

        if self._type == nwItemType.FILE:
            self.setLayout(item.get("layout", nwItemLayout.NO_LAYOUT))
            self.setMainHeading(meta.get("heading", "H0"))
            self.setCharCount(meta.get("charCount", 0))
            self.setWordCount(meta.get("wordCount", 0))
            self.setParaCount(meta.get("paraCount", 0))
            self.setCursorPos(meta.get("cursorPos", 0))
            self.setActive(name.get("active", True))

        # Make some checks to ensure consistency
        if self._type == nwItemType.ROOT:
            self._root = self._handle  # Root items are their own ancestor
            self._parent = None  # Root items cannot have a parent

        if self._type != nwItemType.FILE:
            # Reset values that should only be set for files
            self._layout = nwItemLayout.NO_LAYOUT
            self._heading = "H0"
            self._active = False
            self._charCount = 0
            self._wordCount = 0
            self._paraCount = 0
            self._cursorPos = 0

        self._charInit = self._charCount
        self._wordInit = self._wordCount

        self._updateDailyTarget()

        return True

    @classmethod
    def duplicate(cls, source: ProjectItem, handle: str) -> ProjectItem:
        """Make a copy of an item."""
        new = cls(source._project, handle)
        new._name = source._name
        new._parent = source._parent
        new._root = source._root
        new._order = source._order
        new._type = source._type
        new._class = source._class
        new._layout = source._layout
        new._status = source._status
        new._import = source._import
        new._active = source._active
        new._expanded = source._expanded
        new._heading = source._heading
        new._charCount = source._charCount
        new._wordCount = source._wordCount
        new._paraCount = source._paraCount
        new._cursorPos = source._cursorPos
        new._charInit = source._charInit
        new._wordInit = source._wordInit
        new._dailyTarget = source._dailyTarget
        return new

    ##
    #  Action Methods
    ##

    def notifyToRefresh(self) -> None:
        """Notify the project model/view that item data has changed."""
        self._project.tree.refreshItems([self._handle])

    def notifyNovelStructureChange(self) -> None:
        """Notify that the structure of a novel has changed."""
        if self._root and self._class == nwItemClass.NOVEL:
            self._project.tree.novelStructureChanged(self._root)

    ##
    #  Lookup Methods
    ##

    def describeMe(self) -> str:
        """Return a string description of the item."""
        descKey = "none"
        if self._type == nwItemType.ROOT:
            descKey = "root"
        elif self._type == nwItemType.FOLDER:
            descKey = "folder"
        elif self._type == nwItemType.FILE:
            if self._layout == nwItemLayout.DOCUMENT:
                if self._heading == "H1":
                    descKey = "doc_h1"
                elif self._heading == "H2":
                    descKey = "doc_h2"
                elif self._heading == "H3":
                    descKey = "doc_h3"
                elif self._heading == "H4":
                    descKey = "doc_h4"
                else:
                    descKey = "document"
            elif self._layout == nwItemLayout.NOTE:
                descKey = "note"

        return trConst(nwLabels.ITEM_DESCRIPTION.get(descKey, ""))

    def getMainIconStyle(self) -> str:
        """Get the main item icon style."""
        return SHARED.theme.getItemIconStyle(self._type, self._class, self._layout, self._heading)

    def getMainIcon(self) -> QIcon:
        """Get the main item icon."""
        return SHARED.theme.getItemIcon(self._type, self._class, self._layout, self._heading)

    def getMainFont(self) -> QFont:
        """Get the main item icon."""
        if CONFIG.emphLabels and self._layout == nwItemLayout.DOCUMENT:
            if self._heading == "H1":
                return SHARED.theme.guiFontBU
            elif self._heading == "H2":
                return SHARED.theme.guiFontB
        return SHARED.theme.guiFont

    def getImportStatus(self) -> tuple[str, QIcon]:
        """Return the relevant importance or status label and icon for
        the current item based on its class.
        """
        if self.isNovelLike():
            entry = self._project.data.itemStatus[self._status]
        else:
            entry = self._project.data.itemImport[self._import]
        return entry.name, entry.icon

    def getActiveStatus(self) -> tuple[str, QIcon]:
        """Return the relevant active status label and icon for
        the current item based on its type.
        """
        if self.isFileType():
            icon = "checked:active" if self._active else "unchecked:inactive"
            text = trConst(nwLabels.ACTIVE_NAME[self._active])
        else:
            icon = "noncheckable:disabled"
            text = ""
        return text, SHARED.theme.getIcon(icon)

    ##
    #  Checker Methods
    ##

    def isNovelLike(self) -> bool:
        """Check if the item is of a novel-like class."""
        return self._class in (
            nwItemClass.NOVEL,
            nwItemClass.ARCHIVE,
            nwItemClass.TEMPLATE,
        )

    def isTemplateFile(self) -> bool:
        """Check if the item is a template file."""
        return self._type == nwItemType.FILE and self._class == nwItemClass.TEMPLATE

    def documentAllowed(self) -> bool:
        """Check if the item is allowed to be of document layout."""
        return self._class in (
            nwItemClass.NOVEL,
            nwItemClass.ARCHIVE,
            nwItemClass.TEMPLATE,
            nwItemClass.TRASH,
        )

    def isInactiveClass(self) -> bool:
        """Check if the item is in an inactive class."""
        return self._class in (
            nwItemClass.NO_CLASS,
            nwItemClass.ARCHIVE,
            nwItemClass.TEMPLATE,
            nwItemClass.TRASH,
        )

    def isSearchableClass(self) -> bool:
        """Check if the item is in a searchable class."""
        return self._class not in (
            nwItemClass.NO_CLASS,
            nwItemClass.TEMPLATE,
            nwItemClass.TRASH,
        )

    def isRootType(self) -> bool:
        """Check if item is a root item."""
        return self._type == nwItemType.ROOT

    def isFolderType(self) -> bool:
        """Check if item is a folder item."""
        return self._type == nwItemType.FOLDER

    def isFileType(self) -> bool:
        """Check if item is a file item."""
        return self._type == nwItemType.FILE

    def isNoteLayout(self) -> bool:
        """Check if item is a project note."""
        return self._layout == nwItemLayout.NOTE

    def isDocumentLayout(self) -> bool:
        """Check if item is a novel document."""
        return self._layout == nwItemLayout.DOCUMENT

    def dailyProgress(self) -> tuple[int, int]:
        """Return the total word count and session change for items
        included in the project goal.
        """
        data = self._project.data
        if self._dailyTarget and self._root not in data.targetSkipRoots:
            if data.targetCountChars:
                return self._charCount, self._charCount - self._charInit
            else:
                return self._wordCount, self._wordCount - self._wordInit
        return 0, 0

    ##
    #  Special Setters
    ##

    def setClassDefaults(self, itemClass: nwItemClass) -> None:
        """Set the default values based on the item's class and the
        project settings.
        """
        if self._parent is not None and itemClass != self._class:
            # Only update for child items
            self.setClass(itemClass)
            if self._type == nwItemType.FILE:
                # Notify the index of the class change
                self._project.index.refreshHandle(self._handle)

        if self._layout == nwItemLayout.NO_LAYOUT:
            # If no layout is set, pick one
            if self.isNovelLike():
                self.setLayout(nwItemLayout.DOCUMENT)
            else:
                self.setLayout(nwItemLayout.NOTE)
        elif not self.documentAllowed():
            # Change layout to note if it is not in an allowed folder
            self.setLayout(nwItemLayout.NOTE)

        if self._status is None:
            self.setStatus("New")  # This forces a default value lookup

        if self._import is None:
            self.setImport("New")  # This forces a default value lookup

    ##
    #  Set Item Values
    ##

    def setName(self, name: Any) -> None:
        """Set the item name."""
        if isinstance(name, str):
            self._name = simplified(name)
        else:
            self._name = ""

    def setParent(self, handle: Any) -> None:
        """Set the parent handle, and ensure it is valid."""
        if handle is None:
            self._parent = None
        elif isHandle(handle):
            self._parent = handle
        else:
            self._parent = None

    def setRoot(self, handle: Any) -> None:
        """Set the root handle, and ensure it is valid."""
        if handle is None:
            self._root = None
        elif isHandle(handle):
            self._root = handle
        else:
            self._root = None

        if self._dailyTarget:
            # May have moved between skipped/non-skipped roots
            self._project.markCountsDirty()

    def setOrder(self, order: Any) -> None:
        """Set the item order, and ensure that it is valid. This value
        is purely a meta value, and not actually used by novelWriter at
        the moment.
        """
        self._order = checkInt(order, 0)

    def setType(self, value: Any) -> None:
        """Set the item type from either a proper nwItemType, or set it
        from a string representing an nwItemType.
        """
        if isinstance(value, nwItemType):
            self._type = value
        elif isItemType(value):
            self._type = nwItemType[value]
        else:
            logger.error("Unrecognised item type '%s'", value)
            self._type = nwItemType.NO_TYPE

    def setClass(self, value: Any) -> None:
        """Set the item class from either a proper nwItemClass, or set
        it from a string representing an nwItemClass.
        """
        if isinstance(value, nwItemClass):
            self._class = value
        elif isItemClass(value):
            self._class = nwItemClass[value]
        else:
            logger.error("Unrecognised item class '%s'", value)
            self._class = nwItemClass.NO_CLASS
        self._processDailyTarget()

    def setLayout(self, value: Any) -> None:
        """Set the item layout from either a proper nwItemLayout, or set
        it from a string representing an nwItemLayout.
        """
        if isinstance(value, nwItemLayout):
            self._layout = value
        elif isItemLayout(value):
            self._layout = nwItemLayout[value]
        else:
            logger.error("Unrecognised item layout '%s'", value)
            self._layout = nwItemLayout.NO_LAYOUT
        self._processDailyTarget()

    def setStatus(self, value: Any) -> None:
        """Set the item status by looking it up in the valid status
        items of the current project.
        """
        self._status = self._project.data.itemStatus.check(value)

    def setImport(self, value: Any) -> None:
        """Set the item importance by looking it up in the valid import
        items of the current project.
        """
        self._import = self._project.data.itemImport.check(value)

    def setActive(self, state: Any) -> None:
        """Set the active flag."""
        if isinstance(state, bool):
            self._active = state
        else:
            self._active = False
        self._processDailyTarget()

    def setExpanded(self, state: Any) -> None:
        """Set the expanded status of an item in the project tree."""
        if isinstance(state, bool):
            self._expanded = state
        else:
            self._expanded = False

    ##
    #  Set Document Meta Data
    ##

    def setMainHeading(self, value: str) -> None:
        """Set the main heading level."""
        if value in nwStyles.H_LEVEL:
            self._heading = value

    def setCharCount(self, count: Any) -> None:
        """Set the character count, and ensure that it is an integer."""
        if isinstance(count, int):
            self._charCount = max(0, count)
        else:
            self._charCount = 0

    def setWordCount(self, count: Any) -> None:
        """Set the word count, and ensure that it is an integer."""
        if isinstance(count, int):
            self._wordCount = max(0, count)
        else:
            self._wordCount = 0

    def setParaCount(self, count: Any) -> None:
        """Set the paragraph count, and ensure that it is an integer."""
        if isinstance(count, int):
            self._paraCount = max(0, count)
        else:
            self._paraCount = 0

    def setCursorPos(self, position: Any) -> None:
        """Set the cursor position, and ensure that it is an integer."""
        if isinstance(position, int):
            self._cursorPos = max(0, position)
        else:
            self._cursorPos = 0

    ##
    #  Internal Functions
    ##

    def _updateDailyTarget(self) -> None:
        """Update whether the item is included in the project goal. This
        does not check if the item is skipped.
        """
        self._dailyTarget = self._active and self._class == nwItemClass.NOVEL and self._layout == nwItemLayout.DOCUMENT

    def _processDailyTarget(self) -> None:
        """Update the daily target status of the item and notify the
        project of any changes.
        """
        oldStatus = self._dailyTarget
        self._updateDailyTarget()
        if oldStatus != self._dailyTarget:
            self._project.markCountsDirty()
