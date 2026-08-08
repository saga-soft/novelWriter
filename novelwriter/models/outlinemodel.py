"""
novelWriter - Outline Model
===========================

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

from typing import TYPE_CHECKING, NamedTuple

from PyQt6.QtCore import QAbstractItemModel, QModelIndex, Qt

from novelwriter import SHARED
from novelwriter.constants import nwKeyWords, nwLabels, nwStats, nwStyles, nwUnicode, trConst, trStats

if TYPE_CHECKING:
    from novelwriter.core.index import Index
    from novelwriter.core.indexdata import IndexHeading
    from novelwriter.core.item import ProjectItem

logger = logging.getLogger(__name__)

NODE_FLAGS = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class _TrCache(NamedTuple):
    sWords: str
    sChars: str
    kPov: str
    kFocus: str
    kChars: str


class OutlineNode:
    """Core: Outline Model Node Class.

    A single row in the story outline tree, representing one chapter,
    scene or section heading. The tree is entirely rebuilt on demand
    from the project index, so nodes hold plain copies of the values
    needed for display rather than a live reference to the index data.
    """

    __slots__ = (
        "_characters",
        "_children",
        "_counts",
        "_document",
        "_handle",
        "_heading",
        "_item",
        "_key",
        "_parent",
        "_row",
        "_title",
        "_tr",
    )

    def __init__(
        self,
        handle: str,
        key: str,
        item: ProjectItem | None,
        heading: IndexHeading | None,
        tr: _TrCache,
    ) -> None:
        self._handle = handle
        self._key = key
        self._item = item
        self._heading: IndexHeading | None = heading
        self._tr: _TrCache = tr

        # Parsed Data
        self._title = ""
        self._document = ""
        self._counts = ""
        self._characters = ""

        # Tree Structure
        self._row = 0
        self._parent: OutlineNode | None = None
        self._children: list[OutlineNode] = []

        self.refresh()

    ##
    #  Properties
    ##

    @property
    def handle(self) -> str:
        """The handle of the document the heading belongs to."""
        return self._handle

    @property
    def key(self) -> str:
        """The heading key within its document."""
        return self._key

    @property
    def title(self) -> str:
        """The heading title."""
        return self._title

    @property
    def label(self) -> str:
        """The name of the document the heading belongs to."""
        return self._document

    @property
    def counts(self) -> str:
        """The word and character counts of the heading."""
        return self._counts

    @property
    def characters(self) -> str:
        """The character references of the heading."""
        return self._characters

    @property
    def synopsis(self) -> str:
        """The synopsis of the heading."""
        if hItem := self._heading:
            return hItem.synopsis
        return ""

    ##
    #  Data Access
    ##

    def row(self) -> int:
        """Return the node's row number."""
        return self._row

    def parent(self) -> OutlineNode | None:
        """Return the parent of the node."""
        return self._parent

    def child(self, row: int) -> OutlineNode | None:
        """Return a child of the node."""
        if 0 <= row < len(self._children):
            return self._children[row]
        return None

    def childCount(self) -> int:
        """Return the number of children of the node."""
        return len(self._children)

    def addChild(self, child: OutlineNode) -> None:
        """Add a child node to this node."""
        child._parent = self
        child._row = len(self._children)
        self._children.append(child)

    def data(self, column: int, role: Qt.ItemDataRole) -> None:
        """Return display data for the node."""
        return

    def flags(self) -> Qt.ItemFlag:
        """Return flags for the node."""
        return NODE_FLAGS

    ##
    #  Data Maintenance
    ##

    def refresh(self) -> None:
        """Refresh data values."""
        tr = self._tr
        if h := self._heading:
            refs = h.getReferences()
            self._title = h.title
            self._counts = f"{h.wordCount:n} {tr.sWords}  {nwUnicode.U_BULL}  {h.charCount:n} {tr.sChars}"

            pov = refs[nwKeyWords.POV_KEY]
            focus = refs[nwKeyWords.FOCUS_KEY]
            chars = refs[nwKeyWords.CHAR_KEY]

            characters = []
            if pov:
                characters.append(f"{tr.kPov}: {', '.join(pov)}")
            if focus:
                if characters:
                    characters.append(f"  {nwUnicode.U_BULL}  ")
                characters.append(f"{tr.kFocus}: {', '.join(focus)}")
            if chars:
                if characters:
                    characters.append(f"  {nwUnicode.U_BULL}  ")
                characters.append(f"{tr.kChars}: {', '.join(chars)}")
            self._characters = "".join(characters)

        if i := self._item:
            self._document = i.itemName


class OutlineModel(QAbstractItemModel):
    """Core: Outline Model Class.

    A tree of chapter, scene and section headings for a single novel
    root, built fresh from the project index whenever buildOutline is
    called. Scenes nest under the last seen chapter, and sections nest
    under the last seen scene, falling back to the tree root when no
    such ancestor exists.
    """

    __slots__ = ("_labels", "_root")

    def __init__(self) -> None:
        super().__init__()
        self._labels = _TrCache(
            sWords=trStats(nwLabels.STATS_NAME[nwStats.WORDS]),
            sChars=trStats(nwLabels.STATS_NAME[nwStats.CHARS]),
            kPov=trConst(nwLabels.KEY_NAME[nwKeyWords.POV_KEY]),
            kFocus=trConst(nwLabels.KEY_NAME[nwKeyWords.FOCUS_KEY]),
            kChars=trConst(nwLabels.KEY_NAME[nwKeyWords.CHAR_KEY]),
        )
        self._root = OutlineNode("", "", None, None, self._labels)

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: OutlineModel")

    ##
    #  Model Interface
    ##

    def rowCount(self, index: QModelIndex) -> int:
        """Return the number of rows for an entry."""
        node = index.internalPointer() if index.isValid() else self._root
        return node.childCount()

    def columnCount(self, index: QModelIndex) -> int:
        """Return the number of columns for an entry."""
        return 3

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Get the parent model index of another index."""
        if index.isValid() and (node := index.internalPointer()) and (parent := node.parent()):
            return QModelIndex() if parent is self._root else self.createIndex(parent.row(), 0, parent)
        return QModelIndex()

    def index(self, row: int, column: int, parent: QModelIndex | None = None) -> QModelIndex:
        """Get the index of a child item of a parent."""
        parent = parent or QModelIndex()
        if self.hasIndex(row, column, parent):
            node = parent.internalPointer() if parent.isValid() else self._root
            if child := node.child(row):
                return self.createIndex(row, column, child)
        return QModelIndex()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> None:
        """Return display data for a node."""
        return

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return flags for a node."""
        if index.isValid():
            return index.internalPointer().flags()
        return Qt.ItemFlag.NoItemFlags

    ##
    #  Data Access
    ##

    def node(self, index: QModelIndex) -> OutlineNode | None:
        """Return the node for a given model index."""
        return index.internalPointer() if index.isValid() else None

    ##
    #  Methods
    ##

    def clear(self) -> None:
        """Clear the outline tree."""
        self.beginResetModel()
        self._root = OutlineNode("", "", None, None, self._labels)
        self.endResetModel()

    def buildOutline(self, index: Index, rootHandle: str | None) -> None:
        """Rebuild the outline tree from the project index."""
        self.beginResetModel()
        root = OutlineNode("", "", None, None, self._labels)
        chapter: OutlineNode | None = None
        scene: OutlineNode | None = None
        for tHandle, sTitle, hItem in index.iterNovelStructure(rHandle=rootHandle):
            level = nwStyles.H_LEVEL.get(hItem.level, 0)
            if level < 2:
                continue

            if (nwItem := SHARED.project.tree[tHandle]) is None:
                continue

            node = OutlineNode(tHandle, sTitle, nwItem, hItem, self._labels)
            if level == 2:
                root.addChild(node)
                chapter = node
                scene = None
            elif level == 3:
                (chapter or root).addChild(node)
                scene = node
            else:
                (scene or chapter or root).addChild(node)

        self._root = root
        self.endResetModel()
