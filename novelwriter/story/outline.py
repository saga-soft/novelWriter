"""
novelWriter - GUI Story Outline
===============================

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

from time import time
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt6.QtGui import QFontMetrics, QPainter, QPalette
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QFrame, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import checkInt
from novelwriter.constants import nwUnicode
from novelwriter.extensions.expandpanel import NExpandablePanel
from novelwriter.extensions.modified import NTreeView
from novelwriter.models.outlinemodel import OutlineModel
from novelwriter.types import (
    QtAlignLeftMiddle,
    QtAlignLeftTop,
    QtElideRight,
    QtHeaderInteractive,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSelected,
    QtTransparent,
)

if TYPE_CHECKING:
    from novelwriter.story.storyview import GuiStoryView

LINE_FLAGS = int(Qt.TextFlag.TextSingleLine) | int(QtAlignLeftMiddle)
TOP_FLAGS = int(Qt.TextFlag.TextSingleLine) | int(QtAlignLeftTop)
WRAP_FLAGS = int(Qt.TextFlag.TextWordWrap) | int(QtAlignLeftTop)

ROW_PAD = 3
ROW_RADIUS = 6


class GuiStoryOutlineControls(NExpandablePanel):
    """GUI: Project Story Outline Controls."""

    def __init__(self, parent: GuiStoryView) -> None:
        super().__init__(parent)
        self._contentWidget: GuiStoryOutline | None = None
        self.setTitle(self.tr("Story Outline"))

    def setContentWidget(self, widget: GuiStoryOutline) -> None:
        """Set the content widget for the outline controls."""
        self._contentWidget = widget


class GuiStoryOutline(NTreeView):
    """GUI: Project Story Outline.

    An item view of the chapters and scenes of a novel, with sections
    nested under scenes. Each row is rendered as three lines of text
    by the outline delegate: the heading title, the document and line
    number it belongs to, and its word and character count.
    """

    C_TITLE = 0
    C_CHARS = 1
    C_SYNOPSIS = 2

    def __init__(self, parent: GuiStoryView) -> None:
        super().__init__(parent=parent)

        self._model = OutlineModel()
        self._delegate = _OutlineDelegate(self)

        # Build State
        self._built = False
        self._lastHandle: str | None = None
        self._lastBuild = 0.0

        self.setModel(self._model)
        self.setItemDelegate(self._delegate)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setUniformRowHeights(False)
        self.setAllColumnsShowFocus(True)
        self.setHeaderHidden(False)
        self.setDragEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.initViewport()
        self._disableNativeHighlight()

        if header := self.header():  # pragma: no branch
            header.setStretchLastSection(True)
            header.setMinimumSectionSize(60)
            header.setSectionResizeMode(self.C_TITLE, QtHeaderInteractive)
            header.setSectionResizeMode(self.C_CHARS, QtHeaderInteractive)
            header.setSectionResizeMode(self.C_SYNOPSIS, QtHeaderInteractive)
            header.resizeSection(self.C_TITLE, 260)
            header.resizeSection(self.C_CHARS, 160)

    ##
    #  Methods
    ##

    def initViewport(self) -> None:
        """Initialise viewport settings."""
        if CONFIG.hideVScroll:
            self.setVerticalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setVerticalScrollBarPolicy(QtScrollAsNeeded)
        if CONFIG.hideHScroll:
            self.setHorizontalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(QtScrollAsNeeded)

    def updateTheme(self) -> None:
        """Update theme elements."""
        self._disableNativeHighlight()
        self._delegate.updateTheme()
        if viewport := self.viewport():  # pragma: no branch
            viewport.update()

    def _disableNativeHighlight(self) -> None:
        """Make the native row selection highlight transparent so it does
        not clash with the delegate's level-coloured selection box, which
        is drawn only around the text. Reapplied on theme changes as the
        palette is otherwise refreshed from the application palette.
        """
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Highlight, QtTransparent)
        self.setPalette(palette)

    def refresh(self, rootHandle: str | None, force: bool = False) -> None:
        """Rebuild the outline from the project index, but only if there
        is a genuine change since the last build, or if forced.
        """
        index = SHARED.project.index
        if force or not self._built or rootHandle != self._lastHandle or index.indexChangedSince(self._lastBuild):
            self._model.buildOutline(index, rootHandle)
            self._built = True
            self._lastHandle = rootHandle
            self._lastBuild = time()

    def clear(self) -> None:
        """Clear the outline."""
        self._model.clear()
        self._built = False
        self._lastHandle = None
        self._lastBuild = 0.0

    def restoreColumnWidths(self, widths: list[Any]) -> None:
        """Apply saved column widths to the header. Malformed values are
        silently ignored so the stored format can safely change.
        """
        for column, width in enumerate(widths):
            if (width := checkInt(width, 0)) > 0:
                self.setColumnWidth(column, width)

    def saveColumnWidths(self) -> list[int]:
        """Return the current column widths as a list."""
        columns = range(self._model.columnCount(QModelIndex()))
        return [self.columnWidth(c) for c in columns]

    ##
    #  Overrides
    ##

    def drawRow(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint the level-coloured box and border wrapping the row text
        before the native cell and branch painting. The native selection
        highlight is transparent (see _disableNativeHighlight), so the
        cells, indent and fold arrow don't pick up a mismatched
        highlight; the selection is shown by the box instead.
        """
        if node := self._model.node(index):
            first = index.sibling(index.row(), self.C_TITLE)
            selected = self._isRowSelected(first)
            block = option.rect.adjusted(0, ROW_PAD, -ROW_PAD, -ROW_PAD)
            block.setLeft(self.visualRect(first).left())
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.fillRect(option.rect, self.palette().base())
            painter.setPen(node.style.border)
            painter.setBrush(node.style.highlight if selected else node.style.background)
            painter.drawRoundedRect(block.adjusted(0, 0, -1, -1), ROW_RADIUS, ROW_RADIUS)
            painter.restore()

        super().drawRow(painter, option, index)

    def _isRowSelected(self, index: QModelIndex) -> bool:
        """Return whether the given row index is selected."""
        return bool(sm.isSelected(index)) if (sm := self.selectionModel()) else False


class _OutlineDelegate(QStyledItemDelegate):
    """GUI: Story Outline Row Delegate.

    Paints each row over three lines of height. The title column shows
    the heading title, the document and line number, and the word and
    character count. The characters column shows the point of view and
    focus on one line, and the associated characters wrapped below. The
    synopsis column shows the synopsis stretched over the remaining
    width. Content taller than the row is clipped.
    """

    __slots__ = ("_fm", "_fmB", "_lineHeight", "_margin", "_rowHeight", "_textCol")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._margin = 8
        self._rowHeight = 0
        self._lineHeight = 0
        self.updateTheme()

    def updateTheme(self) -> None:
        """Refresh the cached theme fonts and colours."""
        self._fm = QFontMetrics(SHARED.theme.guiFont)
        self._fmB = QFontMetrics(SHARED.theme.guiFontB)
        self._lineHeight = self._fmB.height() + 2 * self._margin + 2 * ROW_PAD
        self._rowHeight = self._lineHeight + 2 * self._fm.height()
        self._textCol = QApplication.palette().text().color()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return the row height: one line for partitions, three lines for
        all other rows.
        """
        model = index.model()
        if isinstance(model, OutlineModel) and (node := model.node(index)) and node.level == 1:
            return QSize(option.rect.width(), self._lineHeight)
        return QSize(option.rect.width(), self._rowHeight)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint a story outline row."""
        model = index.model()
        if not isinstance(model, OutlineModel) or not (node := model.node(index)):
            super().paint(painter, option, index)
            return

        rect = option.rect
        selected = bool(option.state & QtSelected)
        palette = QApplication.palette()

        painter.save()
        painter.setClipRect(rect)
        if selected:
            painter.setPen(palette.highlightedText().color())
        else:
            painter.setPen(self._textCol)

        pad = ROW_PAD + self._margin
        x = rect.x() + pad
        y = rect.y() + pad
        w = max(0, rect.width() - 2 * pad)
        h = max(0, rect.height() - 2 * pad)

        if node.level == 1:
            if index.column() == GuiStoryOutline.C_TITLE:
                painter.setFont(SHARED.theme.guiFontB)
                title = self._fmB.elidedText(node.title, QtElideRight, w)
                painter.drawText(QRect(x, y, w, h), LINE_FLAGS, title)
            painter.restore()
            return

        match index.column():
            case GuiStoryOutline.C_TITLE:
                hTitle = self._fmB.height()
                hLine = self._fm.height()

                painter.setFont(SHARED.theme.guiFontB)
                title = self._fmB.elidedText(node.title, QtElideRight, w)
                painter.drawText(QRect(x, y, w, hTitle), LINE_FLAGS, title)

                painter.setFont(SHARED.theme.guiFont)
                label = self._fm.elidedText(node.label, QtElideRight, w)
                painter.drawText(QRect(x, y + hTitle, w, hLine), LINE_FLAGS, label)

                counts = self._fm.elidedText(node.counts, QtElideRight, w)
                painter.drawText(QRect(x, y + hTitle + hLine, w, hLine), LINE_FLAGS, counts)

            case GuiStoryOutline.C_CHARS:
                hLine = self._fm.height()
                maxX = x + w

                # Line 1: Point of View and Focus
                xPos = x
                for label, value in (node.pov, node.focus):
                    if not value:
                        continue
                    if xPos > x:
                        painter.setFont(SHARED.theme.guiFont)
                        sep = f"  {nwUnicode.U_BULL}  "
                        painter.drawText(QRect(xPos, y, maxX - xPos, hLine), LINE_FLAGS, sep)
                        xPos += self._fm.horizontalAdvance(sep)
                    xPos = self._paintLabelled(painter, xPos, y, maxX, hLine, label, value)

                # Line 2: Characters
                label, value = node.characters
                if value:
                    yChar = y + hLine
                    text = f"{label}: "
                    painter.setFont(SHARED.theme.guiFontB)
                    painter.drawText(QRect(x, yChar, w, hLine), TOP_FLAGS, text)
                    labelW = self._fmB.horizontalAdvance(text)
                    painter.setFont(SHARED.theme.guiFont)
                    painter.drawText(QRect(x + labelW, yChar, w - labelW, h - hLine), WRAP_FLAGS, value)

            case GuiStoryOutline.C_SYNOPSIS:
                painter.setFont(SHARED.theme.guiFont)
                painter.drawText(QRect(x, y, w, h), WRAP_FLAGS, node.synopsis)

        painter.restore()

    def _paintLabelled(self, painter: QPainter, x: int, y: int, maxX: int, h: int, label: str, value: str) -> int:
        """Paint a bold label followed by a regular value on one line,
        and return the x position after the value.
        """
        text = f"{label}: "
        painter.setFont(SHARED.theme.guiFontB)
        painter.drawText(QRect(x, y, maxX - x, h), LINE_FLAGS, text)
        x += self._fmB.horizontalAdvance(text)

        painter.setFont(SHARED.theme.guiFont)
        value = self._fm.elidedText(value, QtElideRight, maxX - x)
        painter.drawText(QRect(x, y, maxX - x, h), LINE_FLAGS, value)
        return x + self._fm.horizontalAdvance(value)
