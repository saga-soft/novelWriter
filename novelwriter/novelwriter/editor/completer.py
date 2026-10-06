"""
novelWriter - GUI Command Completer
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

import bisect
import logging

from typing import NamedTuple

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QBrush, QColor, QKeyEvent, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QCompleter, QWidget

from novelwriter import SHARED
from novelwriter.constants import nwKeyWords
from novelwriter.types import QtKeyEnter, QtKeyEscape, QtKeyLeft, QtKeyReturn, QtKeyTab, QtUserRole

logger = logging.getLogger(__name__)


class CompleterAction(NamedTuple):
    """Values needed to complete a completer action."""

    pos: int
    length: int
    value: str


class CommandCompleter(QCompleter):
    """GuiWidget: Command Completer Popup.

    This is a completion popup populated from the user's defined tags
    and keys. It also helps to type the meta data keyword on a new
    line starting with @ or %. The update functions should be called
    on every keystroke on a line starting with @ or %.
    """

    __slots__ = ("_model",)

    insertText = pyqtSignal(int, int, str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._model = QStandardItemModel(self)
        self.setModel(self._model)
        self.setWidget(parent)
        self.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setMaxVisibleItems(15)
        self.activated[QModelIndex].connect(self._emitComplete)  # type: ignore[index]

    def updateMetaText(self, text: str, pos: int) -> bool:
        """Update the popup options based on the line of meta text."""
        self._model.clear()
        kw, sep, _ = text.partition(":")
        if pos <= len(kw):
            lookup = kw.rstrip()
            offset = 0
            length = len(lookup)
            suffix = "" if sep else ":"
            self.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            options = sorted(nwKeyWords.VALID_KEYS)
            color = SHARED.theme.syntaxTheme.key
        else:
            status, tBits, tPos = SHARED.project.index.scanThis(text)
            if not status:
                return False
            index = bisect.bisect_right(tPos, pos) - 1
            lookup = tBits[index] if index > 0 else ""
            offset = tPos[index] if lookup else pos
            length = len(lookup)
            suffix = ""
            self.setFilterMode(Qt.MatchFlag.MatchContains)
            options = sorted(SHARED.project.index.getKeyWordTags(kw.strip()))
            color = SHARED.theme.syntaxTheme.tag

        for value in options:
            self._addOption(value, CompleterAction(pos=offset, length=length, value=value + suffix), color)

        self.setCompletionPrefix(lookup)
        return self.completionCount() > 0

    def updateCommentText(self, text: str, pos: int) -> bool:
        """Update the popup options based on the line of comment text."""
        self._model.clear()
        cmd, sep, _ = text.partition(":")
        if pos > len(cmd):
            return False

        clean = text[1:].lstrip()[:6].lower()
        if clean[:6] == "story.":
            pre, _, key = cmd.partition(".")
            lookup = key.rstrip()
            offset = len(pre) + 1
            length = len(lookup)
            suffix = "" if sep else ": "
            self.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            options = sorted(SHARED.project.index.getStoryKeys())
            color = SHARED.theme.syntaxTheme.val
        elif clean[:5] == "note.":
            pre, _, key = cmd.partition(".")
            lookup = key.rstrip()
            offset = len(pre) + 1
            length = len(lookup)
            suffix = "" if sep else ": "
            self.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            options = sorted(SHARED.project.index.getNoteKeys())
            color = SHARED.theme.syntaxTheme.val
        elif pos < 12:
            lookup = cmd.rstrip()
            offset = 0
            length = len(lookup)
            suffix = ""
            self.setFilterMode(Qt.MatchFlag.MatchStartsWith)
            options = ["%Synopsis: ", "%Short: ", "%Story", "%Note"]
            color = SHARED.theme.syntaxTheme.mod
        else:
            return False

        for value in options:
            rep = value + suffix
            self._addOption(rep.rstrip(":. "), CompleterAction(pos=offset, length=length, value=rep), color)

        self.setCompletionPrefix(lookup)
        return self.completionCount() > 0

    def handleKeyPress(self, event: QKeyEvent, key: int) -> bool:
        """Handle a key press while the popup is visible. Returns True
        if the event has been fully handled, in which case the caller
        should stop further processing of the event.
        """
        popup = self.popup()
        if popup is None or not popup.isVisible():
            return False
        if key in (QtKeyReturn, QtKeyEnter, QtKeyTab):
            if (selection := popup.selectionModel()) and (indexes := selection.selectedIndexes()):
                # An entry has been explicitly highlighted with Up or
                # Down, so accept it directly. Note that currentIndex()
                # is not a suitable check here: it can be valid even
                # without an explicit selection, which would swallow a
                # plain Return.
                self._emitComplete(indexes[0])
                popup.hide()
                return True
            # Nothing is highlighted, so this key still does its
            # normal job, and the stale popup just closes
            popup.hide()
        elif key == QtKeyEscape:
            popup.hide()
            event.ignore()
            return True
        elif key == QtKeyLeft:
            popup.hide()
        return False

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex)
    def _emitComplete(self, index: QModelIndex) -> None:
        """Emit the signal to indicate a selection has been made."""
        if isinstance(data := index.data(QtUserRole), CompleterAction):
            self.insertText.emit(data.pos, data.length, data.value)

    ##
    #  Internal Functions
    ##

    def _addOption(self, label: str, data: CompleterAction, color: QColor) -> None:
        """Add a single entry to the popup's model."""
        item = QStandardItem(label)
        item.setEditable(False)
        item.setData(data, QtUserRole)
        item.setForeground(QBrush(color))
        self._model.appendRow(item)
