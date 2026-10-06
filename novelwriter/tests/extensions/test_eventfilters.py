"""
novelWriter - Wheel Event Filter Tests
======================================

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

import pytest

from PyQt6.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from PyQt6.QtGui import QKeyEvent, QWheelEvent
from PyQt6.QtWidgets import QWidget

from novelwriter.extensions.eventfilters import WheelEventFilter
from novelwriter.types import QtModNone, QtModShift


class MockWidget(QWidget):
    def __init__(self):
        super().__init__(None)
        self.count = 0

    def wheelEvent(self, event: QWheelEvent) -> None:
        self.count += 1


@pytest.mark.gui
def testWheelEventFilter_Main():
    """Test the WheelEventFilter class."""
    obj = QObject()
    widget = MockWidget()
    eFilter = WheelEventFilter(widget)
    assert widget.count == 0

    # Sending a key event does nothing
    event = QKeyEvent(QEvent.Type.KeyPress, 1, QtModShift)
    eFilter.eventFilter(obj, event)
    assert widget.count == 0

    # Sending a mouse wheel event forwards it
    pos = QPoint(0, 0)
    posF = QPointF(0.0, 0.0)
    event = QWheelEvent(
        posF,
        posF,
        pos,
        pos,
        Qt.MouseButton.NoButton,
        QtModNone,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    eFilter.eventFilter(obj, event)
    assert widget.count == 1

    # But ignore if we're locked
    eFilter._locked = True
    eFilter.eventFilter(obj, event)
    assert widget.count == 1
