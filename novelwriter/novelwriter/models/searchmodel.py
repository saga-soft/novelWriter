"""
novelWriter - Search Result Model
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

import logging

from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PyQt6.QtGui import QBrush, QIcon

from novelwriter import SHARED
from novelwriter.common import minmax
from novelwriter.types import (
    QtAlignRight,
    QtDecorationRole,
    QtDisplayRole,
    QtForegroundRole,
    QtTextAlignmentRole,
    QtUserRole,
)

if TYPE_CHECKING:
    from novelwriter.core.item import ProjectItem
    from novelwriter.core.projectsearch import T_SearchResults

logger = logging.getLogger(__name__)

C_FACTOR = 0x0100

C_LABEL_TEXT = 0x0000 | QtDisplayRole
C_LABEL_ICON = 0x0000 | QtDecorationRole
C_LABEL_SPAN = 0x0000 | QtUserRole
C_COUNT_TEXT = 0x0100 | QtDisplayRole
C_COUNT_ALIGN = 0x0100 | QtTextAlignmentRole
C_COUNT_COLOR = 0x0100 | QtForegroundRole

T_SearchData = str | QIcon | QBrush | Qt.AlignmentFlag | tuple[int, int] | None


class SearchNode:
    """Core: Search Result Node Class.

    A top-level node represents a document with one or more search
    hits. Each of its children represents a single hit's context and
    its position within that document.
    """

    C_NAME = 0
    C_COUNT = 1

    __slots__ = ("_cache", "_children", "_handle", "_item", "_parent", "_result", "_row")

    def __init__(self, handle: str, result: tuple[int, int] | None = None) -> None:
        self._handle = handle
        self._result = result
        self._item: ProjectItem | None = None
        self._parent: SearchNode | None = None
        self._children: list[SearchNode] = []
        self._row = 0
        self._cache: dict[int, T_SearchData] = {}

    ##
    #  Properties
    ##

    @property
    def handle(self) -> str:
        """The document handle of the node."""
        return self._handle

    @property
    def result(self) -> tuple[int, int] | None:
        """The (start, length) position of a match, or None for a
        document-level node.
        """
        return self._result

    ##
    #  Data Access
    ##

    def row(self) -> int:
        """Return the node's row number."""
        return self._row

    def parent(self) -> SearchNode | None:
        """Return the parent of the node, or None for a top-level node."""
        return self._parent

    def child(self, row: int) -> SearchNode | None:
        """Return a child of the node."""
        if 0 <= row < len(self._children):
            return self._children[row]
        return None

    def childCount(self) -> int:
        """Return the number of children of the node."""
        return len(self._children)

    def data(self, column: int, role: int) -> T_SearchData:
        """Return cached node data."""
        return self._cache.get(C_FACTOR * column | role)

    ##
    #  Data Edit
    ##

    def setDocumentData(self, item: ProjectItem, count: str, color: QBrush) -> None:
        """Set the display data for a document-level node."""
        self._item = item
        self._cache[C_LABEL_TEXT] = item.itemName
        self._cache[C_LABEL_ICON] = item.getMainIcon()
        self._cache[C_COUNT_TEXT] = count
        self._cache[C_COUNT_ALIGN] = QtAlignRight
        self._cache[C_COUNT_COLOR] = color

    def refreshIcon(self) -> None:
        """Refresh the cached icon from the node's project item."""
        if self._item is not None:  # pragma: no branch
            self._cache[C_LABEL_ICON] = self._item.getMainIcon()

    def setMatchData(self, context: str, span: tuple[int, int]) -> None:
        """Set the display data for a match-level node."""
        self._cache[C_LABEL_TEXT] = context
        self._cache[C_LABEL_SPAN] = span

    def setChildren(self, children: list[SearchNode]) -> None:
        """Set the node's children, and update their parent and row."""
        self._children = children
        for row, child in enumerate(children):
            child._parent = self  # noqa: SLF001
            child._row = row  # noqa: SLF001

    def setRow(self, row: int) -> None:
        """Set the node's own row number."""
        self._row = row


class SearchResultModel(QAbstractItemModel):
    """GUI: Project Search Result Model.

    A two-level model where each top-level row is a document with one
    or more search hits, and each child row is a single hit within it.
    """

    __slots__ = ("_color", "_map", "_rows")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[SearchNode] = []
        self._map: dict[str, tuple[int, float]] = {}
        self._color = QBrush(SHARED.theme.accentText)
        logger.debug("Ready: SearchResultModel")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: SearchResultModel")

    ##
    #  Model Interface
    ##

    def rowCount(self, parent: QModelIndex) -> int:
        """Return the number of rows for an entry."""
        if parent.isValid():
            return parent.internalPointer().childCount()
        return len(self._rows)

    def columnCount(self, parent: QModelIndex) -> int:
        """Return the number of columns for an entry."""
        return 2

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        """Get the index of a child item of a parent."""
        parent = parent or QModelIndex()
        if self.hasIndex(row, column, parent):
            if parent.isValid():
                if child := parent.internalPointer().child(row):  # pragma: no branch
                    return self.createIndex(row, column, child)
            elif row < len(self._rows):  # pragma: no branch
                return self.createIndex(row, column, self._rows[row])
        return QModelIndex()

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get the parent model index of another index."""
        if index.isValid() and (parent := index.internalPointer().parent()):
            return self.createIndex(parent.row(), 0, parent)
        return QModelIndex()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> T_SearchData:
        """Return display data for a search node."""
        if index.isValid():
            return index.internalPointer().data(index.column(), role)
        return None

    ##
    #  Data Access
    ##

    def handle(self, index: QModelIndex) -> str | None:
        """Return the document handle of a node."""
        if index.isValid():
            return index.internalPointer().handle
        return None

    def result(self, index: QModelIndex) -> tuple[str, int, int] | None:
        """Return the (handle, start, length) of a match node, or None
        if the index refers to a document-level node.
        """
        if index.isValid():
            node: SearchNode = index.internalPointer()
            if node.result is not None:
                return node.handle, node.result[0], node.result[1]
        return None

    def entry(self, handle: str) -> tuple[int, float] | None:
        """Return the (row, timestamp) of a document's last update."""
        return self._map.get(handle)

    def indexFromHandle(self, handle: str) -> QModelIndex:
        """Return the index of a document-level node."""
        if (entry := self._map.get(handle)) and 0 <= entry[0] < len(self._rows):
            return self.createIndex(entry[0], 0, self._rows[entry[0]])
        return QModelIndex()

    ##
    #  Data Edit
    ##

    def clear(self) -> None:
        """Clear the model."""
        self.beginResetModel()
        self._rows = []
        self._map = {}
        self.endResetModel()

    def setResult(self, nwItem: ProjectItem, results: T_SearchResults, capped: bool) -> None:
        """Insert or update the search results for a document."""
        if not results:
            return

        handle = nwItem.itemHandle
        ext = "+" if capped else ""

        node = SearchNode(handle)
        node.setDocumentData(nwItem, f"({len(results):n}{ext})", self._color)
        node.setChildren(self._buildMatches(handle, results))

        row = self._map.get(handle, (len(self._rows), 0.0))[0]
        if 0 <= row < len(self._rows):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._rows[row]
            self.endRemoveRows()

        self.beginInsertRows(QModelIndex(), row, row)
        node.setRow(row)
        self._rows.insert(row, node)
        self.endInsertRows()

        self._map[handle] = (row, time())

    ##
    #  Other Methods
    ##

    def updateTheme(self) -> None:
        """Update the highlight color and document icons."""
        self._color = QBrush(SHARED.theme.accentText)
        if self._rows:
            for node in self._rows:
                node.refreshIcon()
            first = self.index(0, SearchNode.C_NAME)
            last = self.index(len(self._rows) - 1, SearchNode.C_COUNT)
            self.dataChanged.emit(first, last)

    ##
    #  Internal Functions
    ##

    def _buildMatches(self, handle: str, results: T_SearchResults) -> list[SearchNode]:
        """Build the child match nodes for a document."""
        matches = []
        for start, length, context, offset in results:
            match = SearchNode(handle, (start, length))
            hlStart = minmax(offset, 0, len(context))
            hlEnd = minmax(offset + length, hlStart, len(context))
            match.setMatchData(context, (hlStart, hlEnd))
            matches.append(match)
        return matches
