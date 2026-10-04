"""
novelWriter - GUI Editor Hover Card
===================================

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

import html
import logging

from enum import Enum

from PyQt6.QtCore import QEvent, QPoint, QRectF, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QEnterEvent, QPainter, QPainterPath, QPaintEvent, QPen, QRegion
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from novelwriter import SHARED
from novelwriter.core.indexdata import TT_NONE
from novelwriter.enum import nwDocMode
from novelwriter.extensions.modified import NFlatIconTextButton
from novelwriter.types import QtPaintAntiAlias

logger = logging.getLogger(__name__)


class GuiDocHoverCard(QFrame):
    """GUI: Editor Reference Tag Hover Card.

    A small, permanently owned popup used by the editor to show
    information about a reference tag when the mouse hovers over it.
    The widget is kept hidden until needed, and caches the assembled
    text so it does not need to be rebuilt every time the same tag is
    hovered again.
    """

    openDocumentRequest = pyqtSignal(str, Enum, str, bool)

    HIDE_DELAY = 200

    __slots__ = (
        "_backColor",
        "_borderColor",
        "_buttonBox",
        "_cache",
        "_editBtn",
        "_hideTimer",
        "_label",
        "_layout",
        "_separator",
        "_tag",
        "_viewBtn",
    )

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent, Qt.WindowType.ToolTip)

        self.setObjectName("GuiDocHoverCard")
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        iSz = SHARED.theme.baseIconSize

        self._tag = ""
        self._cache: dict[str, str] = {}
        self._backColor = QColor()
        self._borderColor = QColor()

        self._hideTimer = QTimer(self)
        self._hideTimer.setSingleShot(True)
        self._hideTimer.setInterval(self.HIDE_DELAY)
        self._hideTimer.timeout.connect(self.hide)

        self._label = QLabel(self)
        self._label.setFrameStyle(QFrame.Shape.NoFrame)
        self._label.setTextFormat(Qt.TextFormat.RichText)
        self._label.setWordWrap(True)

        self._separator = QWidget(self)
        self._separator.setFixedHeight(1)

        self._viewBtn = NFlatIconTextButton(self, iSz, "view:action", self.tr("View"))
        self._viewBtn.clicked.connect(self._onViewClicked)

        self._editBtn = NFlatIconTextButton(self, iSz, "edit:change", self.tr("Edit"))
        self._editBtn.clicked.connect(self._onEditClicked)

        self._buttonBox = QHBoxLayout()
        self._buttonBox.addWidget(self._viewBtn)
        self._buttonBox.addWidget(self._editBtn)
        self._buttonBox.addStretch(1)
        self._buttonBox.setContentsMargins(0, 0, 0, 0)

        self._layout = QVBoxLayout()
        self._layout.addWidget(self._label)
        self._layout.addSpacing(6)
        self._layout.addWidget(self._separator)
        self._layout.addSpacing(2)
        self._layout.addLayout(self._buttonBox)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(8, 6, 8, 6)

        self.setLayout(self._layout)

        self.updateTheme()
        self.hide()

    def updateTheme(self) -> None:
        """Update the widget's colours to match the editor's theme."""
        syntax = SHARED.theme.syntaxTheme

        self._backColor = syntax.back
        self._borderColor = syntax.hidden
        self._label.setStyleSheet(f"color: {syntax.text.name()};")
        self._separator.setStyleSheet(f"background-color: {syntax.hidden.name()};")

        self._viewBtn.setFont(SHARED.theme.guiFontSmall)
        self._editBtn.setFont(SHARED.theme.guiFontSmall)
        self._viewBtn.refreshTheme()
        self._editBtn.refreshTheme()

        self.clearCache()  # The HTML has hardcoded colours
        self.update()

    def setTag(self, tag: str) -> bool:
        """Assemble and cache the hover text for a given reference tag,
        looked up from the project index, and update the label. Returns
        True if the tag resolved to any content to display.
        """
        tag = tag.lower()
        if tag != self._tag:
            self._tag = tag
            if tag and tag not in self._cache:
                self._cache[tag] = self._buildText(tag)
            text = self._cache.get(tag, "")
            self._label.setText(text)
        return bool(self._label.text())

    def clearCache(self) -> None:
        """Clear the cached hover text, e.g. when the project index has
        changed and cached entries may be stale.
        """
        self._tag = ""
        self._cache = {}

    def pruneCache(self, remove: list[str]) -> None:
        """Remove any cached text that has changed."""
        self._tag = ""
        for tag in remove:
            self._cache.pop(tag, None)

    def showAt(self, pos: QPoint, viewportWidth: int, viewportHeight: int) -> None:
        """Show the hover card with its top-left corner at pos."""
        self._label.setMaximumWidth(min(viewportWidth // 2, 600))
        self._label.setMaximumHeight(min(viewportHeight // 4, 600))
        self._hideTimer.stop()
        self.adjustSize()
        self.setMask(QRegion(self._roundedPath().toFillPolygon().toPolygon()))
        self.move(pos)
        self.show()

    def scheduleHide(self) -> None:
        """Request that the card be hidden after a short delay, so the
        mouse has time to move from the editor onto the card itself
        without it closing, similar to VS Code's hover widget.
        """
        self._hideTimer.start()

    ##
    #  Events
    ##

    def enterEvent(self, event: QEnterEvent) -> None:
        """Cancel a pending hide when the mouse enters the card."""
        self._hideTimer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Hide the card once the mouse leaves it."""
        self.hide()
        super().leaveEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Hand-paint the rounded background and border."""
        painter = QPainter(self)
        painter.setRenderHint(QtPaintAntiAlias, True)
        painter.fillPath(self._roundedPath(), self._backColor)
        painter.setPen(QPen(self._borderColor, 1))
        painter.drawPath(self._roundedPath(0.5))
        painter.end()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _onViewClicked(self) -> None:
        """Forward a view request for the currently shown tag."""
        tHandle, sTitle = SHARED.project.index.getTagSource(self._tag)
        if tHandle:
            self.openDocumentRequest.emit(tHandle, nwDocMode.VIEW, sTitle, True)

    @pyqtSlot()
    def _onEditClicked(self) -> None:
        """Forward an edit request for the currently shown tag."""
        tHandle, sTitle = SHARED.project.index.getTagSource(self._tag)
        if tHandle:
            self.openDocumentRequest.emit(tHandle, nwDocMode.EDIT, sTitle, True)

    ##
    #  Internal Functions
    ##

    def _roundedPath(self, inset: float = 0.0) -> QPainterPath:
        """Return a rounded rectangle path covering the widget, used for
        both the widget mask and the hand-painted background/border.
        """
        rect = QRectF(self.rect())
        if inset:
            rect = rect.adjusted(inset, inset, -inset, -inset)
        path = QPainterPath()
        path.addRoundedRect(rect, 6, 6)
        return path

    def _buildText(self, tag: str) -> str:
        """Assemble the HTML hover text for a given reference tag."""
        index = SHARED.project.index
        name, _, iItem, hItem = index.getSingleTag(tag)
        if not name or iItem is None:
            return ""

        syntax = SHARED.theme.syntaxTheme
        name = html.escape(name)
        display = html.escape(index.getTagDisplay(tag))
        if name == display:
            lines = [f'<p><span style="color: {syntax.tag.name()};">{name}</span></p>']
        else:
            head = f'<p><span style="color: {syntax.tag.name()};">{name}</span>'
            sep = f'<span style="color: {syntax.text.name()};"> | </span>'
            tail = f'<span style="color: {syntax.opt.name()};">{display}</span></p>'
            lines = [head + sep + tail]

        if hItem:
            if hItem.key != TT_NONE and hItem.title:
                title = html.escape(hItem.title)
                titleSize = round(self._label.font().pointSizeF() * 1.25)
                style = f"color: {syntax.head.name()}; font-size: {titleSize}pt; font-weight: 600;"
                lines.append(f'<p><span style="{style}">{title}</span></p>')
            if synopsis := hItem.synopsis:
                for para in synopsis.split("\n\n"):
                    lines.append(f'<p><span style="color: {syntax.note.name()};">{html.escape(para)}</span></p>')

        logger.debug("Built hover card text for tag '%s'", tag)

        return "".join(lines)
