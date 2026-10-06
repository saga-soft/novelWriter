"""
novelWriter - Project Item Status
=================================

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

import dataclasses
import logging
import random

from typing import TYPE_CHECKING, Literal, TypeGuard

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPixmap, QPolygonF

from novelwriter import SHARED
from novelwriter.common import simplified
from novelwriter.constants import nwLabels
from novelwriter.enum import nwStatusShape
from novelwriter.types import QtPaintAntiAlias, QtTransparent

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = logging.getLogger(__name__)

CUSTOM_COL = "custom"


@dataclasses.dataclass
class StatusEntry:
    """DataClass: Status Label Values."""

    name: str
    color: QColor
    theme: str
    shape: nwStatusShape
    icon: QIcon
    count: int = 0

    @classmethod
    def duplicate(cls, source: StatusEntry) -> StatusEntry:
        """Create a deep copy of the source object."""
        status = dataclasses.replace(source)
        status.color = QColor(source.color)
        status.icon = QIcon(source.icon)
        return status


NO_ENTRY = StatusEntry("", QColor(0, 0, 0), CUSTOM_COL, nwStatusShape.SQUARE, QIcon(), 0)

T_UpdateEntry = list[tuple[str | None, StatusEntry]]
T_StatusKind = Literal["s", "i"]


class ItemStatus:
    """Core: Status/Importance Label Class."""

    STATUS = "s"
    IMPORT = "i"

    __slots__ = ("_default", "_height", "_prefix", "_store")

    def __init__(self, prefix: T_StatusKind) -> None:
        self._store: dict[str, StatusEntry] = {}
        self._default = None
        self._prefix = prefix[:1]
        self._height = SHARED.theme.baseIconHeight

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: ItemStatus")

    def __len__(self) -> int:
        """Return the number of entries in the status list."""
        return len(self._store)

    def __getitem__(self, key: str | None) -> StatusEntry:
        """Return the entry associated with a given key."""
        if key and key in self._store:
            return self._store[key]
        elif self._default is not None:
            return self._store[self._default]
        return NO_ENTRY

    ##
    #  Methods
    ##

    def add(self, key: str | None, name: str, color: str, shape: str, count: int) -> str:
        """Add or update a status entry. If the key is invalid, a new
        key is generated.
        """
        qColor = SHARED.theme.parseColor(color)
        theme = color if color in nwLabels.THEME_COLORS else CUSTOM_COL

        try:
            iShape = nwStatusShape[shape]
        except KeyError:
            iShape = nwStatusShape.SQUARE

        key = self._checkKey(key)
        name = simplified(name)
        icon = self.createIcon(self._height, qColor, iShape)
        self._store[key] = StatusEntry(name, qColor, theme, iShape, icon, count)

        if self._default is None:
            self._default = key

        return key

    def update(self, update: T_UpdateEntry) -> None:
        """Update the list of statuses."""
        self._store.clear()
        for key, entry in update:
            self._store[self._checkKey(key)] = entry

        # Check if we need a new default
        if self._default not in self._store:
            self._default = next(iter(self._store)) if self._store else None

    def check(self, value: str) -> str:
        """Check the key against the stored status names."""
        if self._isKey(value) and value in self._store:
            return value
        elif self._default is not None:
            return self._default
        return ""

    def resetCounts(self) -> None:
        """Clear the counts of references to the status entries."""
        for entry in self._store.values():
            entry.count = 0

    def increment(self, key: str | None) -> None:
        """Increment the counter for a given entry."""
        if key and key in self._store:
            self._store[key].count += 1

    def pack(self) -> Iterable[tuple[str, dict]]:
        """Pack the status entries into a dictionary."""
        for key, entry in self._store.items():
            if entry.theme == CUSTOM_COL:
                color = entry.color.name(QColor.NameFormat.HexRgb)
            else:
                color = entry.theme
            yield (
                entry.name,
                {
                    "key": key,
                    "count": str(entry.count),
                    "color": color,
                    "shape": entry.shape.name,
                },
            )
        return

    def iterItems(self) -> Iterable[tuple[str, StatusEntry]]:
        """Yield entries from the status icons."""
        yield from self._store.items()

    def fromRaw(self, data: list[str]) -> StatusEntry | None:
        """Create a StatusEntry from a list of three strings consisting
        of shape, colour, and name. This entry is not automatically
        added to the list of entries.
        """
        try:
            shape = nwStatusShape[str(data[0])]
            color = QColor(str(data[1]))
            theme = CUSTOM_COL if data[1].startswith("#") else data[1]
            icon = ItemStatus.createIcon(self._height, color, shape)
            return StatusEntry(simplified(data[2]), color, theme, shape, icon)
        except Exception:
            logger.error("Could not parse entry %s", data)
        return None

    def refreshIcons(self) -> None:
        """Refresh all icons."""
        for entry in self._store.values():
            if entry.theme != CUSTOM_COL:
                entry.color = SHARED.theme.parseColor(entry.theme)
            entry.icon = ItemStatus.createIcon(self._height, entry.color, entry.shape)

    @staticmethod
    def createIcon(height: int, color: QColor, shape: nwStatusShape) -> QIcon:
        """Generate an icon for a status label."""
        pixmap = QPixmap(48, 48)
        pixmap.fill(QtTransparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QtPaintAntiAlias)
        painter.fillPath(_SHAPES.getShape(shape), color)
        painter.end()

        return QIcon(
            pixmap.scaled(
                height,
                height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    ##
    #  Internal Functions
    ##

    def _newKey(self) -> str:
        """Generate a new key for a status flag. This method is
        recursive, but should only fail if there is an issue with the
        random number generator or the user has added a lot of status
        flags. The Python recursion limit is given the job to handle
        the extreme case and will cause an app crash.
        """
        key = f"{self._prefix}{random.getrandbits(24):06x}"
        if key in self._store:
            key = self._newKey()
        return key

    def _isKey(self, value: str | None) -> TypeGuard[str]:
        """Check if a value is a key or not."""
        if not isinstance(value, str):
            return False
        if len(value) != 7:
            return False
        if value[0] != self._prefix:
            return False
        return all(c in "0123456789abcdef" for c in value[1:])

    def _checkKey(self, key: str | None) -> str:
        """Check key is valid, and if not, generate one."""
        return key if self._isKey(key) else self._newKey()


class _ShapeCache:
    def __init__(self) -> None:
        self._cache: dict[nwStatusShape, QPainterPath] = {}

    def getShape(self, shape: nwStatusShape) -> QPainterPath:
        """Return a painter shape for an icon."""
        if shape in self._cache:
            return self._cache[shape]

        path = QPainterPath()
        if shape == nwStatusShape.SQUARE:
            path.addRoundedRect(2.0, 2.0, 44.0, 44.0, 4.0, 4.0)
        elif shape == nwStatusShape.TRIANGLE:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 3.00),
                    QPointF(43.92, 37.50),
                    QPointF(4.08, 37.50),
                ])
            )
        elif shape == nwStatusShape.NABLA:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 48.00),
                    QPointF(4.08, 14.50),
                    QPointF(43.92, 14.50),
                ])
            )
        elif shape == nwStatusShape.DIAMOND:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 2.00),
                    QPointF(44.00, 24.00),
                    QPointF(24.00, 46.00),
                    QPointF(4.00, 24.00),
                ])
            )
        elif shape == nwStatusShape.PENTAGON:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 1.50),
                    QPointF(45.87, 17.39),
                    QPointF(37.52, 43.11),
                    QPointF(10.48, 43.11),
                    QPointF(2.13, 17.39),
                ])
            )
        elif shape == nwStatusShape.HEXAGON:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 1.50),
                    QPointF(43.92, 13.00),
                    QPointF(43.92, 36.00),
                    QPointF(24.00, 47.50),
                    QPointF(4.08, 36.00),
                    QPointF(4.08, 13.00),
                ])
            )
        elif shape == nwStatusShape.STAR:
            path.addPolygon(
                QPolygonF([
                    QPointF(24.00, 0.50),
                    QPointF(31.05, 14.79),
                    QPointF(46.83, 17.08),
                    QPointF(35.41, 28.21),
                    QPointF(38.11, 43.92),
                    QPointF(24.00, 36.50),
                    QPointF(9.89, 43.92),
                    QPointF(12.59, 28.21),
                    QPointF(1.17, 17.08),
                    QPointF(15.37, 16.16),
                ])
            )
        elif shape == nwStatusShape.PACMAN:
            path.moveTo(24.0, 24.0)
            path.arcTo(2.0, 2.0, 44.0, 44.0, 40.0, 280.0)
        elif shape == nwStatusShape.CIRCLE_Q:
            path.moveTo(24.0, 24.0)
            path.arcTo(2.0, 2.0, 44.0, 44.0, 0.0, 90.0)
        elif shape == nwStatusShape.CIRCLE_H:
            path.moveTo(24.0, 24.0)
            path.arcTo(2.0, 2.0, 44.0, 44.0, -90.0, 180.0)
        elif shape == nwStatusShape.CIRCLE_T:
            path.moveTo(24.0, 24.0)
            path.arcTo(2.0, 2.0, 44.0, 44.0, -180.0, 270.0)
        elif shape == nwStatusShape.CIRCLE:
            path.addEllipse(2.0, 2.0, 44.0, 44.0)
        elif shape == nwStatusShape.BARS_1:
            path.addRoundedRect(2.0, 2.0, 8.0, 44.0, 4.0, 4.0)
        elif shape == nwStatusShape.BARS_2:
            path.addRoundedRect(2.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(14.0, 2.0, 8.0, 44.0, 4.0, 4.0)
        elif shape == nwStatusShape.BARS_3:
            path.addRoundedRect(2.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(14.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(26.0, 2.0, 8.0, 44.0, 4.0, 4.0)
        elif shape == nwStatusShape.BARS_4:
            path.addRoundedRect(2.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(14.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(26.0, 2.0, 8.0, 44.0, 4.0, 4.0)
            path.addRoundedRect(38.0, 2.0, 8.0, 44.0, 4.0, 4.0)
        elif shape == nwStatusShape.BLOCK_1:
            path.addRoundedRect(2.0, 2.0, 20.0, 20.0, 4.0, 4.0)
        elif shape == nwStatusShape.BLOCK_2:
            path.addRoundedRect(2.0, 2.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(24.0, 2.0, 20.0, 20.0, 4.0, 4.0)
        elif shape == nwStatusShape.BLOCK_3:
            path.addRoundedRect(2.0, 2.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(2.0, 24.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(24.0, 2.0, 20.0, 20.0, 4.0, 4.0)
        elif shape == nwStatusShape.BLOCK_4:
            path.addRoundedRect(2.0, 2.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(2.0, 24.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(24.0, 2.0, 20.0, 20.0, 4.0, 4.0)
            path.addRoundedRect(24.0, 24.0, 20.0, 20.0, 4.0, 4.0)
        else:  # pragma: no cover
            pass

        self._cache[shape] = path

        return path


# Create Singleton
_SHAPES = _ShapeCache()
