"""
novelWriter - Custom Widget: Paged SideBar
==========================================

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

from PyQt6.QtCore import QPoint, QRectF, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPolygon
from PyQt6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QLabel,
    QStyleOptionToolButton,
    QToolBar,
    QToolButton,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.types import (
    QtAlignLeft,
    QtMouseOver,
    QtNoBrush,
    QtNoPen,
    QtPaintAntiAlias,
    QtSizeExpanding,
    QtSizeFixed,
)


class NPagedSideBar(QToolBar):
    """Extensions: Paged Side Bar.

    A side bar widget that holds buttons that mimic tabs. It is designed
    to be used in combination with a QStackedWidget for options panels.
    """

    buttonClicked = pyqtSignal(int)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._labelCol = None
        self._spacerHeight = self.fontMetrics().height() // 2
        self._buttons: dict[int, _PagedToolButton] = {}

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._group.buttonClicked.connect(self._buttonClicked)

        self.setMovable(False)
        self.setOrientation(Qt.Orientation.Vertical)

        stretch = QWidget(self)
        stretch.setSizePolicy(QtSizeExpanding, QtSizeExpanding)
        self._stretchAction = self.addWidget(stretch)

    def button(self, buttonId: int) -> _PagedToolButton:
        """Return a specific button."""
        return self._buttons[buttonId]

    def setLabelColor(self, color: QColor) -> None:
        """Set the text color for the labels."""
        self._labelCol = color
        for widget in self.children():
            if isinstance(widget, _NPagedToolLabel):
                widget.setTextColor(color)

    def addLabel(self, text: str) -> None:
        """Add a new label to the toolbar."""
        label = _NPagedToolLabel(self, self._labelCol)
        label.setText(text)
        self.insertWidget(self._stretchAction, label)

    def addButton(self, text: str, buttonId: int = -1) -> None:
        """Add a new button to the toolbar."""
        button = _PagedToolButton(self)
        button.setText(text)
        button.setAccessibleName(text)
        self.insertWidget(self._stretchAction, button)
        self._group.addButton(button, id=buttonId)
        self._buttons[buttonId] = button

    def setSelected(self, buttonId: int) -> None:
        """Set the selected button."""
        if button := self._group.button(buttonId):
            button.setChecked(True)

    ##
    #  Private Slots
    ##

    @pyqtSlot("QAbstractButton*")
    def _buttonClicked(self, button: QAbstractButton) -> None:
        """Handle a button click in the group and emit its id."""
        buttonId = self._group.id(button)
        if buttonId != -1:
            self.buttonClicked.emit(buttonId)


class _PagedToolButton(QToolButton):
    __slots__ = ("_aH", "_bH", "_tM")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self.setSizePolicy(QtSizeExpanding, QtSizeFixed)
        self.setCheckable(True)

        fH = self.fontMetrics().height()
        self._bH = round(fH * 1.7)
        self._tM = (self._bH - fH) // 2
        self._aH = 2 * fH // 7
        self.setFixedHeight(self._bH)

    def sizeHint(self) -> QSize:
        """Return a size hint that includes the arrow."""
        return super().sizeHint() + QSize(4 * self._aH, 0)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Overload the paint event to draw a simple, left aligned text
        label, with a highlight when selected and a transparent base
        colour when hovered.
        """
        opt = QStyleOptionToolButton()
        opt.initFrom(self)

        painter = QPainter(self)
        painter.setRenderHint(QtPaintAntiAlias, True)
        painter.setPen(QtNoPen)
        painter.setBrush(QtNoBrush)

        width = self.width()
        height = self.height()
        palette = self.palette()

        if opt.state & QtMouseOver == QtMouseOver:  # pragma: no cover
            painter.setBrush(SHARED.theme.activeBase)
            painter.drawRoundedRect(0, 0, width, height, 4, 4)

        if self.isChecked():
            painter.setBrush(palette.highlight())
            painter.setOpacity(0.8)
            painter.drawRoundedRect(0, 0, width, height, 4, 4)
            textCol = palette.highlightedText().color()
        else:
            textCol = palette.text().color()

        tW = width - 24
        tH = height - 2 * self._tM

        painter.setPen(textCol)
        painter.setOpacity(1.0)
        painter.drawText(QRectF(12, self._tM, tW, tH), QtAlignLeft, self.text())

        tC = self.height() // 2
        tW = self.width() - self._aH - 12
        if self.isChecked():
            painter.setBrush(textCol)
        painter.drawPolygon(
            QPolygon([
                QPoint(tW, tC - self._aH),
                QPoint(tW + self._aH, tC),
                QPoint(tW, tC + self._aH),
            ])
        )
        painter.end()


class _NPagedToolLabel(QLabel):
    __slots__ = ("_bH", "_tM", "_textCol")

    def __init__(self, parent: QWidget, textColor: QColor | None = None) -> None:
        super().__init__(parent=parent)

        self.setSizePolicy(QtSizeExpanding, QtSizeFixed)

        fH = self.fontMetrics().height()
        self._bH = round(fH * 1.7)
        self._tM = (self._bH - fH) // 2
        self.setFixedHeight(self._bH)

        self._textCol = textColor or self.palette().text().color()

    def setTextColor(self, textColor: QColor | None = None) -> None:
        """Set a new text colour."""
        self._textCol = textColor or self.palette().text().color()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Overload the paint event to draw a simple, left aligned text
        label that matches the button style.
        """
        tW = self.width() - 8
        tH = self.height() - 2 * self._tM

        painter = QPainter(self)
        painter.setRenderHint(QtPaintAntiAlias, True)
        painter.setPen(QtNoPen)
        painter.setPen(self._textCol)
        painter.setOpacity(1.0)
        painter.drawText(QRectF(4, self._tM, tW, tH), QtAlignLeft, self.text())
        painter.end()
