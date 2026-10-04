"""
novelWriter - Novel Model
=========================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QIcon, QPixmap

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwKeyWords, nwLabels, nwStyles, trConst
from novelwriter.enum import nwNovelExtra
from novelwriter.types import (
    QtAccessibleTextRole,
    QtAlignRight,
    QtDecorationRole,
    QtDisplayRole,
    QtTextAlignmentRole,
    QtToolTipRole,
)

if TYPE_CHECKING:
    from novelwriter.core.indexdata import IndexHeading, IndexNode

logger = logging.getLogger(__name__)

C_FACTOR = 0x0100
R_HANDLE = 0xFF01
R_KEY = 0xFF02

T_NodeData = str | QIcon | QPixmap | Qt.AlignmentFlag | None


class NovelModel(QAbstractTableModel):
    """Core: Novel Model Class."""

    __slots__ = ("_columns", "_extraKey", "_extraLabel", "_more", "_rows")

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[dict[int, T_NodeData]] = []
        self._more = SHARED.theme.getIcon("more_arrow:tool")
        self._columns = 3
        self._extraKey = ""
        self._extraLabel = ""

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: NovelModel")

    ##
    #  Properties
    ##

    @property
    def columns(self) -> int:
        """Return the number of columns."""
        return self._columns

    ##
    #  Setters
    ##

    def setExtraColumn(self, extra: nwNovelExtra) -> None:
        """Set extra data column settings."""
        match extra:
            case nwNovelExtra.HIDDEN:
                self._columns = 3
                self._extraKey = ""
                self._extraLabel = ""
            case nwNovelExtra.POV:
                self._columns = 4
                self._extraKey = nwKeyWords.POV_KEY
                self._extraLabel = trConst(nwLabels.KEY_NAME[nwKeyWords.POV_KEY])
            case nwNovelExtra.FOCUS:
                self._columns = 4
                self._extraKey = nwKeyWords.FOCUS_KEY
                self._extraLabel = trConst(nwLabels.KEY_NAME[nwKeyWords.FOCUS_KEY])
            case nwNovelExtra.PLOT:
                self._columns = 4
                self._extraKey = nwKeyWords.PLOT_KEY
                self._extraLabel = trConst(nwLabels.KEY_NAME[nwKeyWords.PLOT_KEY])
            case _:  # pragma: no cover
                pass

    ##
    #  Model Interface
    ##

    def rowCount(self, parent: QModelIndex) -> int:
        """Return the number of rows."""
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex) -> int:
        """Return the number of columns."""
        return 0 if parent.isValid() else self._columns

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> T_NodeData:
        """Return display data for a node."""
        try:
            return self._rows[index.row()].get(C_FACTOR * index.column() | role)
        except Exception:
            logger.error("Novel model index is inconsistent")
        return None

    def handle(self, index: QModelIndex) -> str | None:
        """Return item handle for the row."""
        try:
            return self._rows[index.row()].get(R_HANDLE)  # type: ignore
        except Exception:
            logger.error("Novel model index is inconsistent")
        return None

    def key(self, index: QModelIndex) -> str | None:
        """Return item handle for the row."""
        try:
            return self._rows[index.row()].get(R_KEY)  # type: ignore
        except Exception:
            logger.error("Novel model index is inconsistent")
        return None

    ##
    #  Data Methods
    ##

    def clear(self) -> None:
        """Clear the model.
        Begin/end reset model must be handled by the caller.
        """
        self._rows.clear()

    def append(self, node: IndexNode) -> None:
        """Append a node to the model.
        Begin/end reset model must be handled by the caller.
        """
        handle = node.handle
        self._rows.extend(self._generateEntry(handle, key, head) for key, head in node.items() if key != "T0000")

    def refresh(self, node: IndexNode) -> bool:
        """Refresh an index node."""
        handle = node.handle
        current = [i for i, row in enumerate(self._rows) if row.get(R_HANDLE) == handle]
        if not current:
            logger.warning("No novel model entries for '%s'", handle)
            return False

        cols = self._columns - 1
        first = current[0]
        last = current[-1]

        remains = []
        for key, head in node.items():
            if key != "T0000":
                if current:
                    j = current.pop(0)
                    self._rows[j] = self._generateEntry(handle, key, head)
                else:
                    remains.append((key, head))

        self.dataChanged.emit(self.createIndex(first, 0), self.createIndex(last, cols))

        if remains:
            # Inserting is safe for out of bounds indices
            self.beginInsertRows(QModelIndex(), last + 1, last + len(remains))
            for k, (key, head) in enumerate(remains, last + 1):
                self._rows.insert(k, self._generateEntry(handle, key, head))
            self.endInsertRows()
        elif current:
            # Deleting ranges are safe for out of bounds indices
            self.beginRemoveRows(QModelIndex(), current[0], current[-1])
            del self._rows[current[0] : current[-1] + 1]
            self.endRemoveRows()

        return True

    ##
    #  Internal Functions
    ##

    def _generateEntry(self, handle: str, key: str, head: IndexHeading) -> dict[int, T_NodeData]:
        """Generate a cache entry."""
        iLevel = nwStyles.H_LEVEL.get(head.level, 0)
        countValue = f"{head.mainCount:n}"
        countInfo = f"{countValue} {CONFIG.countUnit}"

        data = {}
        data[C_FACTOR * 0 | QtToolTipRole] = head.title
        data[C_FACTOR * 0 | QtDisplayRole] = head.title
        data[C_FACTOR * 0 | QtDecorationRole] = SHARED.theme.getHeaderDecoration(iLevel)
        data[C_FACTOR * 1 | QtDisplayRole] = countValue
        data[C_FACTOR * 1 | QtToolTipRole] = countInfo
        data[C_FACTOR * 1 | QtAccessibleTextRole] = countInfo
        data[C_FACTOR * 1 | QtTextAlignmentRole] = QtAlignRight
        if self._columns == 3:
            data[C_FACTOR * 2 | QtDecorationRole] = self._more
        else:
            if self._extraKey and (refs := head.getReferencesByKeyword(self._extraKey)):
                text = ", ".join(refs)
                data[C_FACTOR * 2 | QtDisplayRole] = text
                data[C_FACTOR * 2 | QtToolTipRole] = f"<b>{self._extraLabel}:</b> {text}"
                data[C_FACTOR * 2 | QtAccessibleTextRole] = f"{self._extraLabel}: {text}"
            data[C_FACTOR * 3 | QtDecorationRole] = self._more
        data[R_HANDLE] = handle
        data[R_KEY] = key
        return data
