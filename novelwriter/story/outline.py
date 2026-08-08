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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt6.QtGui import QFontMetrics, QPainter
from PyQt6.QtWidgets import QAbstractItemView, QApplication, QFrame, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.extensions.expandpanel import NExpandablePanel
from novelwriter.extensions.modified import NTreeView
from novelwriter.models.outlinemodel import OutlineModel
from novelwriter.types import (
    QtAlignLeftMiddle,
    QtAlignLeftTop,
    QtElideRight,
    QtHeaderFixed,
    QtHeaderStretch,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSelected,
)

if TYPE_CHECKING:
    from novelwriter.story.storyview import GuiStoryView

LINE_FLAGS = int(Qt.TextFlag.TextSingleLine) | int(QtAlignLeftMiddle)
WRAP_FLAGS = int(Qt.TextFlag.TextWordWrap) | int(QtAlignLeftTop)


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

        self.setModel(self._model)
        self.setItemDelegate(self._delegate)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setUniformRowHeights(True)
        self.setAllColumnsShowFocus(True)
        self.setHeaderHidden(True)
        self.setDragEnabled(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        self.initViewport()

        if header := self.header():  # pragma: no branch
            header.setStretchLastSection(False)
            header.setSectionResizeMode(self.C_TITLE, QtHeaderFixed)
            header.setSectionResizeMode(self.C_CHARS, QtHeaderFixed)
            header.setSectionResizeMode(self.C_SYNOPSIS, QtHeaderStretch)
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
        self._delegate.updateTheme()
        if viewport := self.viewport():  # pragma: no branch
            viewport.update()

    def refresh(self, rootHandle: str | None) -> None:
        """Rebuild the outline from the project index."""
        self._model.buildOutline(SHARED.project.index, rootHandle)
        self.expandAll()

    def clear(self) -> None:
        """Clear the outline."""
        self._model.clear()


class _OutlineDelegate(QStyledItemDelegate):
    """GUI: Story Outline Row Delegate.

    Paints each row as three lines of text: in the title column, the
    heading title, the document and line number, and the word and
    character count; in the characters column, the associated
    characters; and in the synopsis column, the synopsis text
    stretched over the remaining width and clipped to the same three
    lines of height.
    """

    __slots__ = ("_fmSmall", "_fmTitle", "_margin", "_rowHeight", "_textCol")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._margin = 4
        self._rowHeight = 0
        self.updateTheme()

    def updateTheme(self) -> None:
        """Refresh the cached theme fonts and colours."""
        self._fmTitle = QFontMetrics(SHARED.theme.guiFontB)
        self._fmSmall = QFontMetrics(SHARED.theme.guiFontSmall)
        self._rowHeight = self._fmTitle.height() + 2 * self._fmSmall.height() + 2 * self._margin
        self._textCol = QApplication.palette().text().color()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Return a fixed row height for three lines of text."""
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
            painter.fillRect(rect, palette.highlight())
            painter.setPen(palette.highlightedText().color())
        else:
            painter.setPen(self._textCol)

        x = rect.x() + self._margin
        y = rect.y() + self._margin
        w = max(0, rect.width() - 2 * self._margin)
        h = max(0, rect.height() - 2 * self._margin)

        match index.column():
            case GuiStoryOutline.C_TITLE:
                hTitle = self._fmTitle.height()
                hSmall = self._fmSmall.height()

                painter.setFont(SHARED.theme.guiFontB)
                title = self._fmTitle.elidedText(node.title, QtElideRight, w)
                painter.drawText(QRect(x, y, w, hTitle), LINE_FLAGS, title)

                painter.setFont(SHARED.theme.guiFontSmall)
                label = self._fmSmall.elidedText(node.label, QtElideRight, w)
                painter.drawText(QRect(x, y + hTitle, w, hSmall), LINE_FLAGS, label)

                counts = self._fmSmall.elidedText(node.counts, QtElideRight, w)
                painter.drawText(QRect(x, y + hTitle + hSmall, w, hSmall), LINE_FLAGS, counts)

            case GuiStoryOutline.C_CHARS:
                painter.setFont(SHARED.theme.guiFontSmall)
                text = self._fmSmall.elidedText(node.characters, QtElideRight, w)
                painter.drawText(QRect(x, y, w, h), LINE_FLAGS, text)

            case GuiStoryOutline.C_SYNOPSIS:
                painter.setFont(SHARED.theme.guiFontSmall)
                painter.drawText(QRect(x, y, w, h), WRAP_FLAGS, node.synopsis)

        painter.restore()
