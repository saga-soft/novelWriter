"""
novelWriter - GUI Editor Vim Mode
=================================

This file is a part of novelWriter
Copyright (C) 2025 Alexis Dumelie, Veronica Berglyd Olsen and
novelWriter contributors

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

from PyQt6.QtCore import Qt

from novelwriter.enum import nwDocAction, nwVimMode
from novelwriter.types import (
    QtKeepAnchor,
    QtKeyDown,
    QtKeyEnd,
    QtKeyHome,
    QtKeyLeft,
    QtKeyPageDown,
    QtKeyPageUp,
    QtKeyRight,
    QtKeyUp,
    QtModCtrl,
    QtModShift,
    QtMoveDown,
    QtMoveEnd,
    QtMoveEndOfBlock,
    QtMoveEndOfWord,
    QtMoveLeft,
    QtMoveNextChar,
    QtMoveNextWord,
    QtMovePreviousWord,
    QtMoveRight,
    QtMoveStart,
    QtMoveStartOfBlock,
    QtMoveUp,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from PyQt6.QtGui import QKeyEvent, QTextCursor

    from novelwriter.editor.editor import GuiDocEditor

logger = logging.getLogger(__name__)

NAV_KEYS = (QtKeyLeft, QtKeyRight, QtKeyUp, QtKeyDown, QtKeyHome, QtKeyEnd, QtKeyPageUp, QtKeyPageDown)


class EditorVimMode:
    """Editor Component: Vim Mode."""

    __slots__ = ("_callback", "_editor", "_vim")

    def __init__(self, editor: GuiDocEditor, callback: Callable[[nwVimMode], None]) -> None:

        self._editor = editor
        self._vim = VimState()
        self._callback = callback

    ##
    #  Setters
    ##

    def setVimMode(self, mode: nwVimMode) -> None:
        """Change the vim mode."""
        if mode == nwVimMode.NORMAL:
            cursor = self.textCursor()
            cursor.clearSelection()
            self.setTextCursor(cursor)
        self._vim.setMode(mode)
        self._callback(mode)

    def setTextCursor(self, cursor: QTextCursor) -> None:
        """Set the text cursor."""
        self._editor.setTextCursor(cursor)

    ##
    #  Methods
    ##

    def textCursor(self) -> QTextCursor:
        """Return a new text cursor."""
        return self._editor.textCursor()

    def cancel(self) -> bool:
        """Cancel the current mode or pending command, if any."""
        if self._vim.mode != nwVimMode.NORMAL:
            self.setVimMode(nwVimMode.NORMAL)
            return True
        elif self._vim.command:
            self._vim.resetCommand()
            return True
        return False

    def processVimKeyEvent(self, event: QKeyEvent) -> bool:
        """Process a keypress for vim actions."""
        if self._vim.mode == nwVimMode.INSERT or self._editor.isReadOnly():
            return False
        elif self._vim.mode == nwVimMode.NORMAL and event.key() in NAV_KEYS and not event.modifiers() & QtModShift:
            self._vim.resetCommand()
            return False
        elif self._vim.mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            self._handleVimVisualMode(event)
        elif self._handleVimNormalModeModeSwitching(event):
            return True
        else:
            self._handleVimNormalMode(event)
        return True

    ##
    #  Internal Functions
    ##

    def _handleVimNormalModeModeSwitching(self, event: QKeyEvent) -> bool:
        """Handle key events for Vim mode switching in NORMAL mode."""
        if (text := event.text()) == "i":
            self.setVimMode(nwVimMode.INSERT)
            return True
        elif text == "I":
            cursor = self.textCursor()
            cursor.movePosition(QtMoveStartOfBlock)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            return True
        elif text == "v":
            self.setVimMode(nwVimMode.VISUAL)
            cursor = self.textCursor()
            cursor.movePosition(QtMoveRight, QtKeepAnchor)
            self.setTextCursor(cursor)
            return True
        elif text == "V":
            self.setVimMode(nwVimMode.V_LINE)
            cursor = self.textCursor()
            self._selectBlocks(cursor)
            self.setTextCursor(cursor)
            return True
        return False  # Not a mode switching motion

    def _handleVimNormalMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode NORMAL mode motions."""
        key = event.text()
        cursor = self.textCursor()
        if event.key() == Qt.Key.Key_R and event.modifiers() == QtModCtrl:
            key = "<C-r>"

        if key in self._vim.PREFIX_KEYS or key in self._vim.SUFFIX_KEYS:
            self._vim.pushCommandKey(key)
        else:
            self._vim.setCommand(key)

        if (command := self._vim.command) == "dd":
            self._selectBlocks(cursor)
            self._deleteBlocks(cursor)
            self._vim.resetCommand()

        elif command == "x":
            if not cursor.atBlockEnd():
                cursor.movePosition(QtMoveRight, QtKeepAnchor)
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
                cursor.movePosition(QtMoveNextChar)
                cursor.movePosition(QtMoveEndOfWord)

            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "dw":
            blockEnd = cursor.block().position() + cursor.block().length() - 1
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            if cursor.position() > blockEnd:
                cursor.setPosition(blockEnd, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "db":
            cursor.movePosition(QtMovePreviousWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "de":
            # Extend selection to end of current/next word
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            if cursor.position() == origPos:  # Already at end-of-word
                cursor.movePosition(QtMoveNextChar, QtKeepAnchor)
                cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)

            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "d$":
            cursor.movePosition(QtMoveEndOfBlock, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "yw":
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
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
            self._selectBlocks(cursor)
            self._vim.yankToInternal(cursor.selectedText(), lineWise=True)
            self._vim.resetCommand()

        elif command == "p":
            if text := self._vim.pasteFromInternal():
                if self._vim.lineWise:
                    cursor.movePosition(QtMoveEndOfBlock)
                    cursor.insertText("\n" + text)
                else:
                    if not cursor.atBlockEnd():
                        cursor.movePosition(QtMoveRight)
                    cursor.insertText(text)
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "P":
            if text := self._vim.pasteFromInternal():
                if self._vim.lineWise:
                    cursor.movePosition(QtMoveStartOfBlock)
                    cursor.insertText(text + "\n")
                else:
                    cursor.insertText(text)
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "o":
            cursor.movePosition(QtMoveEndOfBlock)
            cursor.insertText("\n")
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "O":
            cursor.movePosition(QtMoveStartOfBlock)
            cursor.insertText("\n")
            cursor.movePosition(QtMoveUp)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "$":
            cursor.movePosition(QtMoveEndOfBlock)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "0":
            cursor.movePosition(QtMoveStartOfBlock)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "a":
            cursor.movePosition(QtMoveRight)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "A":
            cursor.movePosition(QtMoveEndOfBlock)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "u":
            self._editor.docAction(nwDocAction.UNDO)
            self._vim.resetCommand()

        elif command == "<C-r>":
            self._editor.docAction(nwDocAction.REDO)
            self._vim.resetCommand()

        elif command == "zz":
            self._editor.ensureCursorVisible(centre=True)
            self._vim.resetCommand()

        # Single-step navigation
        elif command == "h":
            if not cursor.atBlockStart():
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
            if not cursor.atBlockEnd():
                cursor.movePosition(QtMoveRight)
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif len(command) > 1 or command not in self._vim.PREFIX_KEYS:
            # Not a known command or a pending prefix
            self._vim.resetCommand()

    def _handleVimVisualMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode VISUAL and VLINE mode motions."""
        key = event.text()
        cursor = self.textCursor()

        # -- VISUAL mode PREFIX
        if key in self._vim.VISUAL_PREFIX_KEYS:
            self._vim.pushCommandKey(key)
        else:
            # If adding non-repeating visual mode motions,
            # need to add a suffix case, see normal mode.
            self._vim.setCommand(key)

        # --- VISUAL / VISUALLINE mode ---
        lineWise = self._vim.mode == nwVimMode.V_LINE
        if (command := self._vim.command) in ("d", "x"):
            if lineWise:
                self._deleteBlocks(cursor)
            else:
                self._vim.yankToInternal(cursor.selectedText())
                cursor.removeSelectedText()
                self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "y":
            self._vim.yankToInternal(cursor.selectedText(), lineWise=lineWise)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "v":
            if self._vim.mode == nwVimMode.VISUAL:
                self.setVimMode(nwVimMode.NORMAL)
            else:
                self.setVimMode(nwVimMode.VISUAL)

        elif command == "V":
            if self._vim.mode == nwVimMode.V_LINE:
                self.setVimMode(nwVimMode.NORMAL)
            else:
                self.setVimMode(nwVimMode.V_LINE)

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
            if not cursor.atBlockStart():
                cursor.movePosition(QtMoveLeft, QtKeepAnchor)
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "l":
            if not cursor.atBlockEnd():
                cursor.movePosition(QtMoveRight, QtKeepAnchor)
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "j":
            cursor.movePosition(QtMoveDown, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "k":
            cursor.movePosition(QtMoveUp, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "$":
            cursor.movePosition(QtMoveEndOfBlock, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "0":
            cursor.movePosition(QtMoveStartOfBlock, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "G":
            cursor.movePosition(QtMoveEnd, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif len(command) > 1 or command not in self._vim.VISUAL_PREFIX_KEYS:
            # Not a known command or a pending prefix
            self._vim.resetCommand()

        # V-LINE mode always selects whole lines
        if self._vim.mode == nwVimMode.V_LINE:
            cursor = self.textCursor()
            self._selectBlocks(cursor)
            self.setTextCursor(cursor)

    def _selectBlocks(self, cursor: QTextCursor) -> None:
        """Extend the selection to whole blocks, keeping its direction."""
        forward = cursor.anchor() <= cursor.position()
        position = cursor.position()
        cursor.setPosition(cursor.anchor())
        cursor.movePosition(QtMoveStartOfBlock if forward else QtMoveEndOfBlock)
        cursor.setPosition(position, QtKeepAnchor)
        cursor.movePosition(QtMoveEndOfBlock if forward else QtMoveStartOfBlock, QtKeepAnchor)

    def _deleteBlocks(self, cursor: QTextCursor) -> None:
        """Delete the selected blocks, including the block separator."""
        cursor.beginEditBlock()
        self._vim.yankToInternal(cursor.selectedText(), lineWise=True)
        cursor.removeSelectedText()
        if cursor.block().next().isValid():
            cursor.deleteChar()
        else:
            cursor.deletePreviousChar()
            cursor.movePosition(QtMoveStartOfBlock)
        cursor.endEditBlock()
        self.setTextCursor(cursor)


class VimState:
    """Minimal Vim state machine."""

    __slots__ = ("_buffer", "_command", "_lineWise", "_mode")

    PREFIX_KEYS = "dygz"
    VISUAL_PREFIX_KEYS = "g"
    SUFFIX_KEYS = "web$"

    def __init__(self) -> None:
        self._mode: nwVimMode = nwVimMode.NORMAL
        self._buffer = ""
        self._lineWise = False
        self._command = ""

    @property
    def mode(self) -> nwVimMode:
        """Return current vim mode."""
        return self._mode

    @property
    def command(self) -> str:
        """Return the current vim command."""
        return self._command

    @property
    def lineWise(self) -> bool:
        """Return True if the vim buffer holds whole lines."""
        return self._lineWise

    def setMode(self, mode: nwVimMode) -> None:
        """Switch vim mode."""
        if mode != self._mode:
            logger.debug("Vim Mode changed to %s", mode.name)
            self._mode = mode
            self.resetCommand()

    def resetCommand(self) -> None:
        """Reset internal vim command."""
        self._command = ""

    def pushCommandKey(self, key: str) -> None:
        """Push key to the current command building stack."""
        if self._mode != nwVimMode.INSERT:
            self._command += key

    def setCommand(self, key: str) -> None:
        """Set the state of the current vim command."""
        if self._mode != nwVimMode.INSERT:
            self._command = key

    def yankToInternal(self, text: str, lineWise: bool = False) -> None:
        """Put text into internal vim buffer."""
        self._buffer = text
        self._lineWise = lineWise

    def pasteFromInternal(self) -> str:
        """Paste from the internal vim buffer."""
        return self._buffer
