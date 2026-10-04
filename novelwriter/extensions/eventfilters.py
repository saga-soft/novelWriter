"""
novelWriter - Custom Objects: Event Filters
===========================================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtGui import QStatusTipEvent, QWheelEvent

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget


class WheelEventFilter(QObject):
    """Extensions: Wheel Event Filter.

    An event filter that filters mouse wheel events for a widget and
    forward them to the root widget. This solves the lack of mouse wheel
    scrolling response in margins of widgets like the editor and viewer.

    Solves: #1425
    Reference: https://stackoverflow.com/a/17739995/5825851
    """

    __slots__ = ("_locked", "_parent")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._parent = parent
        self._locked = False

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter events of type QWheelEvent and forward them to the
        parent widget's wheelEvent handler.
        """
        if self._locked:
            return False
        if isinstance(event, QWheelEvent):
            # Recursion protection may be redundant, but a comment on
            # StackOverflow points to Qt 5.12 as the change, and we
            # still support Qt 5.10
            self._locked = True
            self._parent.wheelEvent(event)
            self._locked = False
        return False


class StatusTipFilter(QObject):
    """Filter: Remove StatusBar ToolTips."""

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Filter out status tip events on menus."""
        return True if isinstance(event, QStatusTipEvent) else super().eventFilter(obj, event)
