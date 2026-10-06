"""
novelWriter - GUI Editor History
================================

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

import logging

from typing import TYPE_CHECKING

from novelwriter import CONFIG

if TYPE_CHECKING:
    from novelwriter.editor.viewer import GuiDocViewer

logger = logging.getLogger(__name__)


class GuiDocViewHistory:
    """GUI: Document Viewer History.

    This class holds the navigation history for the viewer panel, which
    is used for backward/forward navigation.
    """

    def __init__(self, docViewer: GuiDocViewer) -> None:
        self.docViewer = docViewer
        self._navHistory = []
        self._posHistory = []
        self._currPos = -1
        self._prevPos = -1

    def clear(self) -> None:
        """Clear the view history."""
        logger.debug("View history cleared")
        self._navHistory = []
        self._posHistory = []
        self._currPos = -1
        self._prevPos = -1

    def append(self, tHandle: str) -> bool:
        """Append a document handle and its scroll bar position to the
        history, but only if the document is different than the current
        active entry. Any further entries are truncated.
        """
        if self._currPos >= 0 and self._currPos < len(self._navHistory) and tHandle == self._navHistory[self._currPos]:
            logger.debug("Not updating view hsitory")
            return False

        self._truncateHistory(self._currPos)

        self._navHistory.append(tHandle)
        self._posHistory.append(0)

        self._prevPos = self._currPos
        self._currPos = len(self._navHistory) - 1
        self._updateScrollBar()
        self._updateNavButtons()

        self._dumpHistory()

        logger.debug("Added '%s' to view history", tHandle)

        return True

    def forward(self) -> None:
        """Navigate to the next entry in the view history."""
        newPos = self._currPos + 1
        if newPos < len(self._navHistory):
            logger.debug("Move forward in view history")
            self._prevPos = self._currPos
            self._updateScrollBar()
            self.docViewer.loadText(self._navHistory[newPos], updateHistory=False)
            self.docViewer.setScrollPosition(self._posHistory[newPos])
            self._currPos = newPos
            self._updateNavButtons()
            self._dumpHistory()

    def backward(self) -> None:
        """Navigate to the previous entry in the view history."""
        newPos = self._currPos - 1
        if newPos >= 0:
            logger.debug("Move backward in view history")
            self._prevPos = self._currPos
            self._updateScrollBar()
            self.docViewer.loadText(self._navHistory[newPos], updateHistory=False)
            self.docViewer.setScrollPosition(self._posHistory[newPos])
            self._currPos = newPos
            self._updateNavButtons()
            self._dumpHistory()

    ##
    #  Internal Functions
    ##

    def _updateScrollBar(self) -> None:
        """Update the scrollbar position of the previous entry."""
        if self._prevPos >= 0 and self._prevPos < len(self._posHistory):
            self._posHistory[self._prevPos] = self.docViewer.scrollPosition

    def _updateNavButtons(self) -> None:
        """Update the navigation buttons in the document header."""
        self.docViewer.docHeader.updateNavButtons(0, len(self._navHistory) - 1, self._currPos)

    def _truncateHistory(self, atPos: int) -> None:
        """Truncate the navigation history to the given position. Also
        enforces a maximum length of the navigation history to 20.
        """
        nSkip = 1 if atPos > 19 else 0
        self._navHistory = self._navHistory[nSkip : atPos + 1]
        self._posHistory = self._posHistory[nSkip : atPos + 1]
        self._currPos -= nSkip
        self._prevPos -= nSkip

    def _dumpHistory(self) -> None:
        """Debug function to dump history to the logger. Since it is a
        for loop, it is skipped entirely if log level isn't DEBUG.
        """
        if CONFIG.isDebug:  # pragma: no cover
            for i, (h, p) in enumerate(zip(self._navHistory, self._posHistory, strict=False)):
                a = ">" if i == self._currPos else " "
                logger.debug(f"History {i + 1:02d}: {a} {h:13s} [x:{p}]")  # noqa: G004
