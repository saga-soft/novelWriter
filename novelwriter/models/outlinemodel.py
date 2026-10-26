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
import math

from typing import TYPE_CHECKING, NamedTuple

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor, QIcon

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatPercent
from novelwriter.constants import nwLabels, nwStyles, trConst, trLabel, trUnit
from novelwriter.enum import nwStdLabel, nwStdUnit
from novelwriter.story.storysettings import COMMENT_SYNOPSIS
from novelwriter.types import QtAccessibleTextRole, QtDisplayRole, QtTransparent

if TYPE_CHECKING:
    from novelwriter.core.index import Index
    from novelwriter.core.indexdata import IndexHeading

logger = logging.getLogger(__name__)

NODE_FLAGS = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable


class _TrCache(NamedTuple):
    sWords: str
    sChars: str
    sPage: str
    sSynopsis: str
    sStory: str
    sNote: str
    sKeys: dict[str, str]
    sLevels: dict[str, str]


class NodeStyle(NamedTuple):
    """Core: Outline Node Style Class."""

    border: QColor
    background: QColor
    highlight: QColor


BLANK_STYLE = NodeStyle(QtTransparent, QtTransparent, QtTransparent)


class OutlineNode:
    """Core: Outline Model Node Class.

    A single heading row, holding copies of the values for display.
    """

    __slots__ = (
        "_cCount",
        "_chars",
        "_columns",
        "_entries",
        "_handle",
        "_heading",
        "_join",
        "_key",
        "_level",
        "_lists",
        "_progress",
        "_status",
        "_style",
        "_title",
        "_tr",
        "_wCount",
        "_words",
    )

    def __init__(
        self,
        handle: str,
        key: str,
        heading: IndexHeading | None,
        tr: _TrCache,
        style: NodeStyle,
        columns: list[tuple[str, ...]] | None = None,
        join: bool = False,
    ) -> None:
        self._handle = handle
        self._key = key
        self._heading: IndexHeading | None = heading
        self._tr: _TrCache = tr
        self._columns = columns or []
        self._join = join

        # Parsed Data
        self._level = 0
        self._title = ""
        self._cCount = 0
        self._wCount = 0
        self._words = ""
        self._chars = ""
        self._progress = ""
        self._status: tuple[str, QIcon] | None = None
        self._lists: dict[str, list[str]] = {}
        self._entries: list[list[tuple[str, str, str, str]]] = []
        self._style = style

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
    def level(self) -> int:
        """The heading level."""
        return self._level

    @property
    def counts(self) -> str:
        """The word or character count, as set in the preferences."""
        return self._chars if CONFIG.useCharCount else self._words

    @property
    def progress(self) -> str:
        """The page and story progress of the heading, if set."""
        return self._progress

    @property
    def status(self) -> tuple[str, QIcon] | None:
        """The status label and icon of the heading's document, if set."""
        return self._status

    @property
    def style(self) -> NodeStyle:
        """The style for the heading's structural level."""
        return self._style

    ##
    #  Data Access
    ##

    def refSpans(self, keyword: str, tags: set[str]) -> list[tuple[int, int]]:
        """Return the start and length of the given tag keys in refs."""
        spans = []
        pos = 0
        for name in self._lists.get(keyword, ()):
            if name.lower() in tags:
                spans.append((pos, len(name)))
            pos += len(name) + 2
        return spans

    def entries(self, column: int) -> list[tuple[str, str, str, str]]:
        """Return the key, label, short label and text of the entries
        of a column. The short label is used when an icon is shown.
        """
        return self._entries[column] if 0 <= column < len(self._entries) else []

    def accessibleTitle(self) -> str:
        """Return the title column content as plain text."""
        level = self._tr.sLevels.get(self._heading.level, "") if self._heading else ""
        title = f"{level}: {self._title}" if level else self._title
        status = self._status[0] if self._status else ""
        return ", ".join(t for t in (title, self.counts, self._progress, status) if t)

    def accessibleEntries(self, column: int) -> str:
        """Return the entries of a column as plain text, with full labels."""
        entries = (f"{label}: {text}" if label else text for _, label, _, text in self.entries(column))
        return ", ".join(entries)

    ##
    #  Data Maintenance
    ##

    def setProgress(self, page: int, fraction: float) -> None:
        """Set the page number and word count progress fraction."""
        self._progress = f"{self._tr.sPage.format(f'{page:n}')} ({formatPercent(fraction, prec=1)})"

    def setStatus(self, label: str, icon: QIcon) -> None:
        """Set the status label and icon."""
        self._status = (label, icon)

    def addCounts(self, chars: int, words: int) -> None:
        """Add the character and word counts of a child heading."""
        self._cCount += chars
        self._wCount += words
        self._formatCounts()

    def refresh(self) -> None:
        """Refresh data values."""
        tr = self._tr
        if h := self._heading:
            self._level = nwStyles.H_LEVEL.get(h.level, 0)
            self._title = h.title
            self._cCount = h.charCount
            self._wCount = h.wordCount
            self._formatCounts()

            self._lists = {k: v for k, v in h.getReferences().items() if v}

            kinds = {"story": tr.sStory, "note": tr.sNote}
            lookup = {k: (tr.sKeys.get(k, k), "", ", ".join(v)) for k, v in self._lists.items()}
            lookup[COMMENT_SYNOPSIS] = (tr.sSynopsis, "", h.synopsis)

            # Comment keys are matched regardless of spelling
            for key, text in h.comments.items():
                kind, _, name = key.partition(".")
                if kind in kinds and name:
                    name = name.title()
                    lookup[key.lower()] = (f"{kinds[kind]} ({name})", name, text)

            self._entries = []
            for keys in self._columns:
                entries = []
                for key in keys:
                    label, short, text = lookup.get(key, ("", "", ""))
                    if text:
                        parts = [text.replace("\n\n", " ")] if self._join else text.split("\n\n")
                        entries.extend((key, label, short, p) for p in parts)
                self._entries.append(entries)

    ##
    #  Internal Functions
    ##

    def _formatCounts(self) -> None:
        """Format the count labels."""
        self._words = f"{self._wCount:n} {self._tr.sWords}"
        self._chars = f"{self._cCount:n} {self._tr.sChars}"


class OutlineModel(QAbstractTableModel):
    """Core: Outline Model Class.

    A flat list of the headings of a novel, in story order.
    """

    __slots__ = ("_fixed", "_headers", "_labels", "_nodes", "_styles")

    C_TITLE = 0
    C_COLUMNS = 1

    def __init__(self) -> None:
        super().__init__()
        self._fixed = [trLabel(nwStdLabel.STORY)]
        self._headers = self._fixed.copy()
        self._labels = _TrCache(
            sWords=trUnit(nwStdUnit.WORDS),
            sChars=trUnit(nwStdUnit.CHARS),
            sPage=self.tr("Page {0}"),
            sSynopsis="",
            sStory="",
            sNote="",
            sKeys={k: trConst(v) for k, v in nwLabels.KEY_NAME.items()},
            sLevels={k: trConst(v) for k, v in nwStyles.T_LABEL.items()},
        )

        # Colours
        theme = SHARED.theme
        self._styles: dict[int, NodeStyle] = {}
        for key in nwStyles.H_LEVEL.values():
            color = theme.getStructureColor(key)
            border = QColor(color)
            border.setAlphaF(0.7)
            background = QColor(color)
            background.setAlphaF(0.1)
            highlight = QColor(color)
            highlight.setAlphaF(0.2)
            self._styles[key] = NodeStyle(border, background, highlight)

        self._nodes: list[OutlineNode] = []

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: OutlineModel")

    ##
    #  Model Interface
    ##

    def rowCount(self, parent: QModelIndex) -> int:
        """Return the number of rows."""
        return 0 if parent.isValid() else len(self._nodes)

    def columnCount(self, parent: QModelIndex) -> int:
        """Return the number of columns."""
        return 0 if parent.isValid() else len(self._headers)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> str | None:
        """Return accessible text for a node, as the delegate paints the rest."""
        if role == QtAccessibleTextRole and (node := self.node(index)):
            if index.column() == self.C_TITLE:
                return node.accessibleTitle()
            return node.accessibleEntries(index.column() - self.C_COLUMNS)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole) -> str | None:
        """Return the header labels for the outline columns."""
        if orientation == Qt.Orientation.Horizontal and role == QtDisplayRole:
            return self._headers[section] if 0 <= section < len(self._headers) else None
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return flags for a node."""
        return NODE_FLAGS if index.isValid() else Qt.ItemFlag.NoItemFlags

    ##
    #  Data Access
    ##

    def node(self, index: QModelIndex) -> OutlineNode | None:
        """Return the node for a given model index."""
        if index.isValid() and 0 <= (row := index.row()) < len(self._nodes):
            return self._nodes[row]
        return None

    ##
    #  Methods
    ##

    def clear(self) -> None:
        """Clear the outline."""
        self.beginResetModel()
        self._nodes = []
        self.endResetModel()

    def buildOutline(
        self,
        index: Index,
        rootHandle: str | None,
        levels: set[int],
        countPerPage: int = 0,
        clearDouble: bool = False,
        target: int = 0,
        useChars: bool = False,
        columns: list[tuple[str, tuple[str, ...]]] | None = None,
        showStatus: bool = False,
        inactiveParts: bool = False,
        subCounts: bool = False,
        joinComments: bool = False,
    ) -> None:
        """Rebuild the outline for the given heading levels and columns.
        If count per page is set, the page and progress of each heading
        is added, with partitions and chapters starting on a new page.
        Inactive partitions are not counted. Sub counts add the counts
        of the following lower level headings to each heading. Repeated
        comments are joined into one entry if join comments is set.
        """
        tree = SHARED.project.tree
        self.beginResetModel()

        columns = columns or []
        keys = [k for _, k in columns]
        labels = self._labels._replace(
            sSynopsis=trLabel(nwStdLabel.SYNOPSIS),
            sStory=trLabel(nwStdLabel.STORY_STRUCTURE),
            sNote=trLabel(nwStdLabel.NOTE),
        )
        nodes: list[OutlineNode] = []
        progress: list[tuple[OutlineNode, int, int]] = []
        scopes: list[tuple[int, OutlineNode | None]] = []

        count = 0
        pages = 0
        start = 0
        for tHandle, sTitle, hItem in index.iterNovelStructure(rHandle=rootHandle, activeOnly=not inactiveParts):
            level = nwStyles.H_LEVEL.get(hItem.level, 0)
            item = tree[tHandle]
            active = bool(item and item.isActive)
            if not (active or level == 1):
                continue

            if active and countPerPage > 0 and level <= 2:
                span = math.ceil((count - start) / countPerPage)
                pages += span + span % 2 if clearDouble else span
                start = count

            node = None
            if level in levels and not (level == 1 and hItem.modified):
                style = self._styles.get(level, BLANK_STYLE)
                node = OutlineNode(tHandle, sTitle, hItem, labels, style, keys, joinComments)
                nodes.append(node)
                if showStatus and item:
                    node.setStatus(*item.getImportStatus())
                if active and countPerPage > 0:
                    progress.append((node, pages + 1 + (count - start) // countPerPage, count))

            if active and subCounts:
                while scopes and scopes[-1][0] >= level:
                    scopes.pop()
                for _, parent in scopes:
                    if parent:
                        parent.addCounts(hItem.charCount, hItem.wordCount)
                scopes.append((level, node))

            if active:
                count += hItem.charCount if useChars else hItem.wordCount

        total = max(count, target)
        for node, page, before in progress:
            node.setProgress(page, before / total if total else 0.0)

        self._nodes = nodes
        self._headers = self._fixed + [name for name, _ in columns]

        self.endResetModel()
