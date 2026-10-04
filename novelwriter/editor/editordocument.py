"""
novelWriter - GUI Text Document
===============================

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

import logging

from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSizeF, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QTextBlock, QTextBlockFormat, QTextCursor, QTextDocument
from PyQt6.QtWidgets import QApplication

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwConst
from novelwriter.editor.highlighter import GuiDocHighlighter
from novelwriter.editor.textblock import TextBlockData
from novelwriter.types import QtPropLineHeight

if TYPE_CHECKING:
    from collections.abc import Iterable

    from PyQt6.QtCore import QObject

logger = logging.getLogger(__name__)

LAYOUT_SETTLE_DELAY = 150  # milliseconds of quiet before the layout is considered settled


class GuiTextDocument(QTextDocument):
    """Custom: Modified QTextDocument.

    A special text document format that incorporates a few additional
    features including spell checking.
    """

    layoutSettled = pyqtSignal()

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent=parent)

        self._handle = None
        self._syntax = GuiDocHighlighter(self)

        # Layout Busy Tracking
        # QTextDocument builds its layout lazily in the background, in
        # bursts of work reported via documentSizeChanged.
        self._layoutBusy = False
        self._settleTimer = QTimer(self)
        self._settleTimer.setSingleShot(True)
        self._settleTimer.setInterval(LAYOUT_SETTLE_DELAY)
        self._settleTimer.timeout.connect(self._layoutHasSettled)
        if layout := self.documentLayout():  # pragma: no branch
            layout.documentSizeChanged.connect(self._layoutGrew)

        logger.debug("Ready: GuiTextDocument")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiTextDocument")

    ##
    #  Properties
    ##

    @property
    def syntaxHighlighter(self) -> GuiDocHighlighter:
        """Return the document's syntax highlighter object."""
        return self._syntax

    ##
    #  Setters
    ##

    def setLineHeight(self, height: float) -> None:
        """Apply a line height to all blocks in the document."""
        self.markLayoutBusy()
        blockFormat = QTextBlockFormat()
        blockFormat.setLineHeight(int(height * 100), QtPropLineHeight)
        cursor = QTextCursor(self)
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(blockFormat)

    def setBottomMargin(self, margin: float) -> None:
        """Set the bottom margin of the document's root frame."""
        if not self.isLayoutBusy() and (rootFrame := self.rootFrame()):  # pragma: no branch
            frameFormat = rootFrame.frameFormat()
            if frameFormat.bottomMargin() != margin:
                frameFormat.setBottomMargin(margin)
                rootFrame.setFrameFormat(frameFormat)

    ##
    #  Methods
    ##

    def isLayoutBusy(self) -> bool:
        """Return True if the document's lazily built layout is
        currently mid-burst after a full-document change.
        """
        return self._layoutBusy

    def markLayoutBusy(self) -> None:
        """Flag the layout as busy ahead of an operation that forces a
        re-layout. Must be called before such an operation.
        """
        if self.characterCount() > nwConst.BIG_DOC_LIMIT:
            self._layoutBusy = True
            self._settleTimer.start()

    def setTextContent(self, text: str, tHandle: str) -> None:
        """Set the text content of the document."""
        self._syntax.setHandle(tHandle)

        self.blockSignals(True)
        self.setUndoRedoEnabled(False)
        self.clear()

        tStart = time()

        self.setPlainText(text)
        self.setLineHeight(CONFIG.lineHeight)
        count = self.lineCount()

        tMid = time()

        self.setUndoRedoEnabled(True)
        self.blockSignals(False)
        self._syntax.rehighlight()
        QApplication.processEvents()

        self.markLayoutBusy()

        tEnd = time()

        logger.debug("Loaded %d text blocks in %.3f ms", count, 1000 * (tMid - tStart))
        logger.debug("Highlighted document in %.3f ms", 1000 * (tEnd - tMid))

    def metaDataAtPos(self, pos: int) -> tuple[str, str]:
        """Check if there is meta data available at a given position in
        the document, and if so, return it.
        """
        cursor = QTextCursor(self)
        cursor.setPosition(pos)
        block = cursor.block()
        data = block.userData()
        if block.isValid() and isinstance(data, TextBlockData) and (check := pos - block.position()) >= 0:
            for cPos, cEnd, cData, cType in data.metaData:
                if cPos <= check <= cEnd:
                    return cData, cType
        return "", ""

    def spellErrorAtPos(self, pos: int) -> tuple[str, int, int, list[str]]:
        """Check if there is a misspelled word at a given position in
        the document, and if so, return it with its start and end
        positions within the block.
        """
        cursor = QTextCursor(self)
        cursor.setPosition(pos)
        block = cursor.block()
        data = block.userData()
        if block.isValid() and isinstance(data, TextBlockData) and (check := pos - block.position()) >= 0:
            for start, end, word in data.spellErrors:
                if start <= check <= end:
                    return word, start, end, SHARED.spelling.suggestWords(word)
        return "", -1, -1, []

    def iterBlockByType(self, cType: int, maxCount: int = 1000) -> Iterable[QTextBlock]:
        """Iterate over all text blocks of a given type."""
        count = 0
        block = self.begin()
        while block.isValid():
            if block.userState() & cType > 0:
                yield block
                count += 1
                if count >= maxCount:
                    return
            block = block.next()

    ##
    #  Private Slots
    ##

    @pyqtSlot(QSizeF)
    def _layoutGrew(self, size: QSizeF) -> None:
        """Restart the settle debounce whenever the lazily built layout
        grows, while a busy-marked operation is in progress.
        """
        if self._layoutBusy:
            self._settleTimer.start()

    @pyqtSlot()
    def _layoutHasSettled(self) -> None:
        """Fire once the layout has been quiet for LAYOUT_SETTLE_DELAY
        ms, meaning it's safe to do things that need it, such as
        ensureCursorVisible.
        """
        self._layoutBusy = False
        self.layoutSettled.emit()
