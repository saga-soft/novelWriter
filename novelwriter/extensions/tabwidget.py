"""
novelWriter - Custom Widget: Tab Widget
=======================================

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import QApplication, QTabBar, QTabWidget, QWidget

from novelwriter import SHARED
from novelwriter.types import QtAlignCenter, QtMouseLeft

if TYPE_CHECKING:
    from PyQt6.QtCore import QRect
    from PyQt6.QtGui import QColor, QMouseEvent


class NTabWidget(QTabWidget):
    """Custom: Modified QTabWidget.

    A tab widget that highlights the currently selected tab's label
    using the app theme.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.setTabBar(NTabBar(self))
        self.setDocumentMode(True)

    def refreshTheme(self) -> None:
        """Refresh the tab colours for theme updates."""
        if (tabBar := self.tabBar()) is not None:  # pragma: no branch
            tabBar.update()


class NTabBar(QTabBar):
    """Custom: Modified QTabBar.

    A tab bar that highlights the currently selected tab's label
    using the app theme.
    """

    __slots__ = ("_dragDist", "_dragGrab", "_dragIndex", "_dragStart", "_dragWidth", "_dragX")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.setDrawBase(False)

        # Drag State
        self._dragIndex = -1
        self._dragStart = 0
        self._dragGrab = 0
        self._dragWidth = 0
        self._dragDist = 0
        self._dragX = -1

    def tabSizeHint(self, index: int) -> QSize:
        """Reduce the tab height by shrinking the margin above and below the text."""
        size = super().tabSizeHint(index)
        return QSize(size.width(), size.height() - 4)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Record the start of a potential tab drag."""
        super().mousePressEvent(event)
        if self.isMovable() and event.button() == QtMouseLeft:
            pos = event.position().toPoint()
            index = self.tabAt(pos)
            rect = self.tabRect(index)
            self._dragIndex = index
            self._dragStart = pos.x()
            self._dragGrab = pos.x() - rect.left()
            self._dragWidth = rect.width()
            self._dragDist = QApplication.startDragDistance()
            self._dragX = -1

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Drag the pressed tab, replacing Qt's drag, which our custom
        painting cannot follow.
        """
        if self._dragIndex < 0 or not self.isMovable():
            super().mouseMoveEvent(event)
            return
        if not (event.buttons() & QtMouseLeft):
            self._endDrag()
            return

        x = event.position().toPoint().x()
        if x == self._dragX or (self._dragX < 0 and abs(x - self._dragStart) < self._dragDist):
            return

        self._dragX = x
        left = x - self._dragGrab
        index = self._dragIndex
        if left > self.tabRect(index).left():
            right = left + self._dragWidth
            last = self.count() - 1
            while index < last and right > self.tabRect(index + 1).center().x():
                self.moveTab(index, index + 1)
                index += 1
        else:
            while index > 0 and left < self.tabRect(index - 1).center().x():
                self.moveTab(index, index - 1)
                index -= 1
        self._dragIndex = index
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """End a tab drag."""
        self._endDrag()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Highlight the currently selected tab with the theme highlight colour."""
        painter = QPainter(self)
        palette = self.palette()
        textCol = palette.text().color()
        selected = self.currentIndex()
        count = self.count()
        width = self.width()
        drag = self._dragIndex if self._dragX >= 0 and 0 <= self._dragIndex < count else -1

        for i in range(count):
            if i == drag or not self.isTabVisible(i):
                continue
            rect = self.tabRect(i)
            if rect.right() >= 0 and rect.left() <= width:
                self._drawTab(painter, rect, i, i == selected, textCol)

        # The dragged tab is drawn last at the cursor, leaving its slot empty
        if drag >= 0:
            rect = self.tabRect(drag)
            rect.moveLeft(max(0, min(self._dragX - self._dragGrab, width - rect.width())))
            if drag != selected:
                painter.fillRect(rect, palette.window())
            self._drawTab(painter, rect, drag, drag == selected, textCol)

    def _drawTab(self, painter: QPainter, rect: QRect, index: int, selected: bool, textCol: QColor) -> None:
        """Draw a single tab."""
        if selected:
            painter.fillRect(rect, SHARED.theme.activeBase)
            painter.setPen(SHARED.theme.accentText)
            painter.drawLine(rect.left(), rect.top(), rect.right(), rect.top())
        else:
            painter.setPen(textCol)
        painter.drawText(rect, QtAlignCenter, self.tabText(index))

    def _endDrag(self) -> None:
        """Reset the drag state."""
        if self._dragX >= 0:
            self.update()
        self._dragIndex = -1
        self._dragX = -1
