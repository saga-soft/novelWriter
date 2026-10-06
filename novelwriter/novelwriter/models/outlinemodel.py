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
from PyQt6.QtGui import QColor

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatPercent
from novelwriter.constants import nwLabels, nwStats, nwStyles, nwUnicode, trConst, trLabel, trStats
from novelwriter.enum import nwStdLabel
from novelwriter.story.storysettings import COMMENT_SYNOPSIS
from novelwriter.types import QtDisplayRole, QtTransparent

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
        "_chars",
        "_columns",
        "_entries",
        "_handle",
        "_heading",
        "_key",
        "_level",
        "_lists",
        "_progress",
        "_style",
        "_title",
        "_tr",
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
    ) -> None:
        self._handle = handle
        self._key = key
        self._heading: IndexHeading | None = heading
        self._tr: _TrCache = tr
        self._columns = columns or []

        # Parsed Data
        self._level = 0
        self._title = ""
        self._words = ""
        self._chars = ""
        self._progress = ""
        self._lists: dict[str, list[str]] = {}
        self._entries: list[list[tuple[str, str, str]]] = []
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

    def entries(self, column: int) -> list[tuple[str, str, str]]:
        """Return the key, label and text of the entries of a column."""
        return self._entries[column] if 0 <= column < len(self._entries) else []

    ##
    #  Data Maintenance
    ##

    def setProgress(self, page: int, fraction: float) -> None:
        """Set the page number and word count progress fraction."""
        self._progress = f"{self._tr.sPage.format(f'{page:n}')} ({formatPercent(fraction, prec=1)})"

    def refresh(self) -> None:
        """Refresh data values."""
        tr = self._tr
        if h := self._heading:
            self._level = nwStyles.H_LEVEL.get(h.level, 0)
            self._title = h.title
            self._words = f"{h.wordCount:n} {tr.sWords}"
            self._chars = f"{h.charCount:n} {tr.sChars}"

            self._lists = {k: v for k, v in h.getReferences().items() if v}

            kinds = {"story": tr.sStory, "note": tr.sNote}
            lookup = {k: (tr.sKeys.get(k, k), ", ".join(v)) for k, v in self._lists.items()}
            lookup[COMMENT_SYNOPSIS] = (tr.sSynopsis, h.synopsis)

            # Comment keys are matched regardless of spelling
            for key, text in h.comments.items():
                kind, _, name = key.partition(".")
                if kind in kinds and name:
                    lookup[key.lower()] = (f"{kinds[kind]} ({name.title()})", text)

            self._entries = []
            for keys in self._columns:
                entries = []
                for key in keys:
                    label, text = lookup.get(key, ("", ""))
                    if text:
                        entries.append((key, label, nwUnicode.U_LSEP.join(t for t in text.split("\n") if t)))
                self._entries.append(entries)


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
            sWords=trStats(nwLabels.STATS_NAME[nwStats.WORDS]),
            sChars=trStats(nwLabels.STATS_NAME[nwStats.CHARS]),
            sPage=self.tr("Page {0}"),
            sSynopsis="",
            sStory="",
            sNote="",
            sKeys={k: trConst(v) for k, v in nwLabels.KEY_NAME.items()},
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

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> None:
        """Return display data for a node."""
        return

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
    ) -> None:
        """Rebuild the outline for the given heading levels and columns.
        If count per page is set, the page and progress of each heading
        is added, with partitions and chapters starting on a new page.
        """
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
        count = 0
        pages = 0
        start = 0
        for tHandle, sTitle, hItem in index.iterNovelStructure(rHandle=rootHandle):
            level = nwStyles.H_LEVEL.get(hItem.level, 0)
            if countPerPage > 0 and level <= 2:
                span = math.ceil((count - start) / countPerPage)
                pages += span + span % 2 if clearDouble else span
                start = count
            if level in levels and not (level == 1 and hItem.modified):
                style = self._styles.get(level, BLANK_STYLE)
                node = OutlineNode(tHandle, sTitle, hItem, labels, style, keys)
                nodes.append(node)
                if countPerPage > 0:
                    progress.append((node, pages + 1 + (count - start) // countPerPage, count))
            count += hItem.charCount if useChars else hItem.wordCount

        total = max(count, target)
        for node, page, before in progress:
            node.setProgress(page, before / total if total else 0.0)

        self._nodes = nodes
        self._headers = self._fixed + [name for name, _ in columns]
        self.endResetModel()
