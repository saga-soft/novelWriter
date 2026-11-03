"""
novelWriter - GUI Document Vim Mode
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

import logging

from typing import TYPE_CHECKING

from novelwriter import CONFIG
from novelwriter.enum import nwDocAction, nwVimMode
from novelwriter.types import (
    QtKeepAnchor,
    QtMoveDown,
    QtMoveEnd,
    QtMoveEndOfLine,
    QtMoveEndOfWord,
    QtMoveLeft,
    QtMoveNextChar,
    QtMoveNextWord,
    QtMovePreviousWord,
    QtMoveRight,
    QtMoveStart,
    QtMoveStartOfLine,
    QtMoveUp,
    QtSelectLine,
)

if TYPE_CHECKING:
    from PyQt6.QtGui import QKeyEvent, QTextCursor

    from novelwriter.editor.editor import GuiDocEditor

logger = logging.getLogger(__name__)


class DocumentVimMode:
    """Gui Widget: Editor Vim Mode."""

    __slots__ = ("_editor", "_vim")

    def __init__(self, editor: GuiDocEditor) -> None:

        self._editor = editor
        self._vim = VimState()

    def setVimMode(self, mode: nwVimMode) -> None:
        """Change the vim mode."""
        if CONFIG.vimMode:
            if mode == nwVimMode.NORMAL:
                cursor = self.textCursor()
                cursor.clearSelection()
                self.setTextCursor(cursor)
            self._vim.setMode(mode)
            self._editor.docFooter.updateVimModeStatusBar(mode)
        else:
            self._editor.docFooter.updateVimModeStatusBar(None)

    def setTextCursor(self, cursor: QTextCursor) -> None:
        """Set the text cursor."""
        self._editor.setTextCursor(cursor)

    def textCursor(self) -> QTextCursor:
        """Return a new text cursor."""
        return self._editor.textCursor()

    def processVimKeyEvent(self, event: QKeyEvent) -> bool:
        """Process a keypress for vim actions."""
        if self._vim.mode != nwVimMode.INSERT:
            if self._handleVimNormalModeModeSwitching(event):
                return True

            if self._vim.mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
                self._handleVimVisualMode(event)
            else:
                self._handleVimNormalMode(event)

            return True

        return False

    ##
    #  Internal Functions
    ##

    def _handleVimNormalModeModeSwitching(self, event: QKeyEvent) -> bool:
        """Handle key events for Vim mode switching in NORMAL mode."""
        if (text := event.text()) == "i":
            self.setVimMode(nwVimMode.INSERT)
        elif text == "I":
            cursor = self.textCursor()
            cursor.movePosition(QtMoveStartOfLine)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            return True
        elif text == "v":
            self.setVimMode(nwVimMode.VISUAL)
            cursor = self.textCursor()
            cursor.movePosition(QtMoveRight, QtKeepAnchor, 1)
            self.setTextCursor(cursor)
            return True
        elif text == "V":
            self.setVimMode(nwVimMode.V_LINE)
            cursor = self.textCursor()
            cursor.select(QtSelectLine)
            self.setTextCursor(cursor)
            return True
        return False  # Not a mode switching motion

    def _handleVimNormalMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode NORMAL mode motions."""
        key = event.text()
        cursor = self.textCursor()
        # -- NORMAL mode PREFIX
        if self._vim.mode == nwVimMode.NORMAL:
            if key in self._vim.PREFIX_KEYS or key in self._vim.SUFFIX_KEYS:
                self._vim.pushCommandKey(key)
            else:
                self._vim.setCommand(key)

        if (command := self._vim.command) == "dd":
            cursor.beginEditBlock()
            cursor.select(QtSelectLine)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            cursor.setPosition(cursor.selectionEnd())
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "x":
            cursor.movePosition(QtMoveRight, QtKeepAnchor, 1)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "w":
            cursor.movePosition(QtMoveNextWord)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "b":
            cursor.movePosition(QtMovePreviousWord)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "e":
            # Try to move to end of the current word
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord)

            # If we didn't move (we were already at end of a word),
            # step forward one character (if possible) and then move to the next EndOfWord.
            if cursor.position() == origPos:
                textLen = len(self._editor.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar)
                    cursor.movePosition(QtMoveEndOfWord)

            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "dw":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "db":
            cursor.beginEditBlock()
            cursor.movePosition(QtMovePreviousWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "de":
            cursor.beginEditBlock()
            # Extend selection to end of current/next word
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            if cursor.position() == origPos:  # Already at end-of-word
                textLen = len(self._editor.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar, QtKeepAnchor)
                    cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "d$":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveEndOfLine, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "yw":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "gg":
            cursor.movePosition(QtMoveStart)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "G":
            cursor.movePosition(QtMoveEnd)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "yy":
            cursor.select(QtSelectLine)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "p":
            if text := self._vim.pasteFromInternal():
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveEndOfLine)
                cursor.insertText("\n" + text)
                cursor.endEditBlock()
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "P":
            if text := self._vim.pasteFromInternal():
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveStartOfLine)
                cursor.insertText(text + "\n")
                cursor.endEditBlock()
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "o":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveEndOfLine)
            cursor.insertText("\n")
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "O":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveStartOfLine)
            cursor.insertText("\n")
            cursor.movePosition(QtMoveUp)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "$":
            cursor.movePosition(QtMoveEndOfLine)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "a":
            cursor.movePosition(QtMoveRight)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            self._vim.resetCommand()

        elif command == "A":
            cursor.movePosition(QtMoveEndOfLine)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            self._vim.resetCommand()

        elif command == "u":
            self._editor.docAction(nwDocAction.UNDO)
            self._vim.resetCommand()

        elif command == "zz":
            self.setTextCursor(cursor)
            self._editor.ensureCursorVisible(centre=True)
            self._vim.resetCommand()

        # Single-step navigation
        elif command == "h":
            cursor.movePosition(QtMoveLeft)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "j":
            cursor.movePosition(QtMoveDown)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "k":
            cursor.movePosition(QtMoveUp)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "l":
            cursor.movePosition(QtMoveRight)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

    def _handleVimVisualMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode VISUAL and VLINE mode motions."""
        key = event.text()
        cursor = self.textCursor()

        # -- VISUAL mode PREFIX
        if key in self._vim.VISUAL_PREFIX_KEYS:
            self._vim.pushCommandKey(key)
        else:
            # If adding none repeating visual mode motions,
            # need to add a suffix case, see normal mode.
            self._vim.setCommand(key)

        # --- VISUAL / VISUALLINE mode ---
        if (command := self._vim.command) in ("d", "x"):
            cursor.beginEditBlock()
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "y":
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "w":
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "b":
            cursor.movePosition(QtMovePreviousWord, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "e":
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            if cursor.position() == origPos:
                textLen = len(self._editor.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar, QtKeepAnchor)
                    cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)

            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "gg":
            cursor.movePosition(QtMoveStart, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        # Handle motions (extend selection)
        elif command == "h":
            cursor.movePosition(QtMoveLeft, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "l":
            cursor.movePosition(QtMoveRight, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "j":
            cursor.movePosition(QtMoveDown, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "k":
            cursor.movePosition(QtMoveUp, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "$":
            cursor.movePosition(QtMoveEndOfLine, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "0":
            cursor.movePosition(QtMoveStartOfLine, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "G":
            cursor.movePosition(QtMoveEnd, QtKeepAnchor)
            self.setTextCursor(cursor)


class VimState:
    """Minimal Vim state machine."""

    __slots__ = ("_internalClipboard", "_mode", "_normalCommand", "_visualCommand")

    PREFIX_KEYS = "dygz"
    VISUAL_PREFIX_KEYS = "g"
    SUFFIX_KEYS = "web$"

    def __init__(self) -> None:
        self._mode: nwVimMode = nwVimMode.NORMAL
        self._normalCommand = ""
        self._visualCommand = ""
        self._internalClipboard = ""
        self.setMode(nwVimMode.NORMAL)

    @property
    def mode(self) -> nwVimMode:
        """Return current vim mode."""
        return self._mode

    @property
    def command(self) -> str:
        """Return the current vim command."""
        if self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            return self._visualCommand
        else:
            return self._normalCommand

    def setMode(self, mode: nwVimMode) -> None:
        """Switch vim mode."""
        if mode != self._mode:
            logger.debug("Vim Mode changed to %s", mode.name)
            self._mode = mode
            self.resetCommand()

    def resetCommand(self) -> None:
        """Reset internal vim command."""
        self._normalCommand = ""
        self._visualCommand = ""

    def pushCommandKey(self, key: str) -> None:
        """Push key to the current command building stack."""
        if self._mode is nwVimMode.NORMAL:
            self._normalCommand += key
        elif self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            self._visualCommand += key

    def setCommand(self, key: str) -> None:
        """Set the state of the current vim command."""
        if self._mode is nwVimMode.NORMAL:
            self._normalCommand = key
        elif self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            self._visualCommand = key

    def yankToInternal(self, text: str) -> None:
        """Put text into internal vim buffer."""
        self._internalClipboard = text

    def pasteFromInternal(self) -> str:
        """Paste from the internal vim clipboard."""
        return self._internalClipboard
