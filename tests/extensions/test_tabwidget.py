"""
novelWriter - Tab Widget Tests
==============================

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

import pytest

from PyQt6.QtCore import QEvent, QPointF, Qt
from PyQt6.QtGui import QMouseEvent, QPixmap
from PyQt6.QtWidgets import QWidget

from novelwriter.extensions.tabwidget import NTabBar, NTabWidget
from novelwriter.types import QtModNone, QtMouseLeft, QtMouseMiddle


def mouseEvent(kind: QEvent.Type, x: int, button: Qt.MouseButton, buttons: Qt.MouseButton) -> QMouseEvent:
    """Create a mouse event at a given x position on the tab bar."""
    return QMouseEvent(kind, QPointF(x, 10), button, buttons, QtModNone)


@pytest.mark.gui
def testNTabWidget_Paint(qtbot, nwGUI):
    """Test the NTabWidget and NTabBar paint logic."""
    tabs = NTabWidget(None)  # type: ignore
    qtbot.addWidget(tabs)
    for i in range(6):
        tabs.addTab(QWidget(), f"Tab Number {i} With a Long Label")

    bar = tabs.tabBar()
    assert bar is not None

    # A normal paint, with every tab fitting inside the bar, must not fail
    bar.resize(1200, 30)
    bar.render(QPixmap(1200, 30))

    # Shrinking the bar below the combined tab width leaves later tabs
    # positioned outside the paintable area, which must be skipped rather
    # than painted, and must still not fail
    bar.resize(60, 30)
    bar.render(QPixmap(60, 30))

    tabs.refreshTheme()


@pytest.mark.gui
def testNTabWidget_Drag(qtbot, nwGUI):
    """Test dragging tabs on the NTabBar."""
    tabs = NTabWidget(None)  # type: ignore
    qtbot.addWidget(tabs)
    for name in ("Alpha", "Beta", "Gamma"):
        tabs.addTab(QWidget(), name)

    bar = tabs.tabBar()
    assert isinstance(bar, NTabBar)
    bar.resize(600, 30)

    moves = []
    bar.tabMoved.connect(lambda a, b: moves.append((a, b)))

    def names():
        return [bar.tabText(i) for i in range(bar.count())]

    def press(x, button=QtMouseLeft):
        bar.mousePressEvent(mouseEvent(QEvent.Type.MouseButtonPress, x, button, button))

    def move(x, buttons=QtMouseLeft):
        bar.mouseMoveEvent(mouseEvent(QEvent.Type.MouseMove, x, Qt.MouseButton.NoButton, buttons))

    def release(x):
        bar.mouseReleaseEvent(mouseEvent(QEvent.Type.MouseButtonRelease, x, QtMouseLeft, Qt.MouseButton.NoButton))

    first = bar.tabRect(0).center().x()
    last = bar.tabRect(2).center().x()

    # Not movable: Qt handles the events, and nothing is moved
    press(first)
    move(last)
    release(last)
    assert names() == ["Alpha", "Beta", "Gamma"]

    # Movable, but not the left button, does not start a drag
    tabs.setMovable(True)
    press(first, QtMouseMiddle)
    move(last)
    release(last)
    assert names() == ["Alpha", "Beta", "Gamma"]

    # Moving less than the drag distance does not start a drag
    press(first)
    move(first + 1)
    assert bar._dragX == -1
    release(first + 1)
    assert moves == []

    # Drag the first tab to the end
    press(first)
    move(bar.width())
    assert names() == ["Beta", "Gamma", "Alpha"]
    assert moves == [(0, 1), (1, 2)]
    assert bar._dragIndex == 2
    bar.render(QPixmap(600, 30))

    release(bar.width())
    assert bar._dragIndex == -1
    assert bar._dragX == -1
    bar.render(QPixmap(600, 30))

    # Drag the last tab to the start, while it isn't the current tab
    moves.clear()
    press(bar.tabRect(2).center().x())
    tabs.setCurrentIndex(0)
    move(0)
    assert names() == ["Alpha", "Beta", "Gamma"]
    assert moves == [(2, 1), (1, 0)]
    bar.render(QPixmap(600, 30))

    # A move without the button held ends the drag
    move(last, Qt.MouseButton.NoButton)
    assert bar._dragIndex == -1
    assert bar._dragX == -1
    release(last)
    assert names() == ["Alpha", "Beta", "Gamma"]
