"""
novelWriter - GUI Editor Runnables
==================================

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

from PyQt6.QtCore import QObject, QRunnable, pyqtBoundSignal, pyqtSignal, pyqtSlot

from novelwriter import SHARED
from novelwriter.editor.textblock import T_TextCheckList, formatCheckText, spellCheckText
from novelwriter.text.counting import standardCounter

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

T_TextCheckPayload = list[tuple[int, str, str, int, list[int] | None]]


class WordCounterDispatcher(QObject):
    """Dispatches BackgroundWordCounter jobs to the thread pool, one at
    a time, and forwards the results to a fixed callback.
    """

    _countsReady = pyqtSignal(int, int, int)

    def __init__(self, parent: QObject, callback: Callable[[int, int, int], None]) -> None:
        super().__init__(parent)
        self._busy = False
        self._callback = callback
        self._countsReady.connect(self._onCountsReady)

    @property
    def busy(self) -> bool:
        """Return True if a count job is currently in flight."""
        return self._busy

    def count(self, text: str) -> None:
        """Dispatch a new count job, unless one is already running."""
        if not self._busy:
            self._busy = True
            SHARED.runInThreadPool(BackgroundWordCounter(text, self._countsReady))

    @pyqtSlot(int, int, int)
    def _onCountsReady(self, cCount: int, wCount: int, pCount: int) -> None:
        """Clear the busy state before forwarding the result, so the
        callback is free to dispatch another count job right away.
        """
        self._busy = False
        self._callback(cCount, wCount, pCount)


class BackgroundWordCounter(QRunnable):
    """The Off-GUI Thread Word Counter.

    A one-shot runnable for the word counter, run in the thread pool
    off the main GUI thread.
    """

    def __init__(self, text: str, signal: pyqtBoundSignal) -> None:
        super().__init__()
        self._text = text
        self._signal = signal

    @pyqtSlot()
    def run(self) -> None:
        """Overloaded run function for the word counter, forwarding the
        call to the function that does the actual counting.
        """
        cC, wC, pC = standardCounter(self._text)
        self._signal.emit(cC, wC, pC)


class TextCheckDispatcher(QObject):
    """Dispatches BackgroundTextCheck jobs to the thread pool and
    forwards the results to a fixed callback.
    """

    _resultsReady = pyqtSignal(int, list)

    def __init__(self, parent: QObject, callback: Callable[[int, list], None]) -> None:
        super().__init__(parent)
        self._resultsReady.connect(callback)

    def dispatch(self, jobId: int, payload: T_TextCheckPayload, checkSpell: bool, checkFormat: bool) -> None:
        """Dispatch a new text check job."""
        SHARED.runInThreadPool(BackgroundTextCheck(jobId, payload, checkSpell, checkFormat, self._resultsReady))


class BackgroundTextCheck(QRunnable):
    """The Off-GUI Thread Text Checker.

    A one-shot runnable that spell and/or format checks a batch of
    text block snapshots in the thread pool off the main GUI thread.
    """

    def __init__(
        self,
        jobId: int,
        payload: T_TextCheckPayload,
        checkSpell: bool,
        checkFormat: bool,
        signal: pyqtBoundSignal,
    ) -> None:
        super().__init__()
        self._jobId = jobId
        self._payload = payload
        self._checkSpell = checkSpell
        self._checkFormat = checkFormat
        self._signal = signal

    @pyqtSlot()
    def run(self) -> None:
        """Spell and format check the text snapshots and emit the results."""
        results: list[tuple[int, T_TextCheckList, T_TextCheckList]] = []
        for index, spellText, formatText, offset, utf16Map in self._payload:
            spellErrors = spellCheckText(spellText, offset, utf16Map) if self._checkSpell else []
            formatErrors = formatCheckText(formatText, offset, utf16Map) if self._checkFormat else []
            results.append((index, spellErrors, formatErrors))
        self._signal.emit(self._jobId, results)
