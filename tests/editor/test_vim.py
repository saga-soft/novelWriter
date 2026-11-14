"""
novelWriter - Editor Vim Mode Tests
===================================

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

from pathlib import Path

import pytest

from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from novelwriter import CONFIG, SHARED
from novelwriter.core.project import NWProject
from novelwriter.dialogs.preferences import GuiNeedsUpdate
from novelwriter.editor.editor import GuiDocEditor
from novelwriter.editor.vim import VimState
from novelwriter.enum import nwVimMode
from novelwriter.guimain import GuiMain
from novelwriter.types import QtKeyEscape, QtKeyRight, QtModCtrl, QtModShift

from tests.helpers import C, MockRnd, buildTestProject

KEY_DELAY = 2
VIM_CHANGED = GuiNeedsUpdate(
    restart=False,
    tree=False,
    theme=False,
    syntax=False,
    spelling=False,
    vim=True,
    editor=False,
    viewer=False,
    viewport=False,
)


def openVimEditor(nwGUI: GuiMain, projPath: Path) -> GuiDocEditor:
    """Open the scene document in the editor with vim mode enabled."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.docPanes.openDocument(C.hSceneDoc)
    CONFIG.vimMode = True
    nwGUI._processConfigChanges(VIM_CHANGED)
    return nwGUI.docEditor


def resetText(docEditor: GuiDocEditor) -> str:
    """Reset the editor to the standard test text."""
    docEditor.setPlainText("Line1\nLine2\nLine3")
    return docEditor.getText()


def getLines(docEditor: GuiDocEditor) -> list[str]:
    """Return the non-empty lines of the editor text."""
    return list(filter(str.strip, docEditor.getText().splitlines()))


def testVimState_InsertModeNoOp():
    """Test that the vim state ignores command keys in INSERT mode."""
    vim = VimState()
    vim.setMode(nwVimMode.INSERT)
    vim.pushCommandKey("d")
    assert vim.command == ""
    vim.setCommand("d")
    assert vim.command == ""


@pytest.mark.gui
def testEditorVimMode_Init(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test enabling, refreshing and disabling vim mode in the editor."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.docPanes.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor
    docFooter = docEditor.docFooter
    mainMenu = nwGUI.mainMenu

    # Disabled by default
    assert docEditor._vimMode is None
    assert docFooter.vimStatus.isHidden() is True
    assert mainMenu.aViewDoc.shortcut().toString() == "Ctrl+R"
    assert mainMenu.aCloseView.shortcut().toString() == "Ctrl+Shift+R"

    # Enable from settings, which also releases conflicting shortcuts
    CONFIG.vimMode = True
    nwGUI._processConfigChanges(VIM_CHANGED)
    vimMode = docEditor._vimMode
    assert vimMode is not None
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docFooter._vimMode == nwVimMode.NORMAL
    assert docFooter.vimStatus.isHidden() is False
    assert mainMenu.aViewDoc.shortcut().isEmpty() is True
    assert mainMenu.aCloseView.shortcut().isEmpty() is True

    # Mode changes are reported to the footer
    qtbot.keyClick(docEditor, "i", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.INSERT
    assert docFooter._vimMode == nwVimMode.INSERT

    # Escape returns to NORMAL mode first, then cancels a pending
    # command, and then leaves Focus Mode
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docFooter._vimMode == nwVimMode.NORMAL
    assert SHARED.focusMode is True
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    assert vimMode._vim.command == ""
    assert SHARED.focusMode is True
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    assert SHARED.focusMode is False

    # Commands are ignored when the editor is read-only
    text = docEditor.getText()
    docEditor.setReadOnly(True)
    qtbot.keyClicks(docEditor, "xV", delay=KEY_DELAY)
    assert docEditor.getText() == text
    assert vimMode._vim.mode == nwVimMode.NORMAL
    docEditor.setReadOnly(False)

    # Unrelated settings changes don't reset the mode
    vimMode.setVimMode(nwVimMode.INSERT)
    docEditor.initSettings()
    assert vimMode._vim.mode == nwVimMode.INSERT

    # Re-initialising the editor keeps the instance, but resets the mode
    vimMode._vim.yankToInternal("Text")
    docEditor.initEditor()
    assert docEditor._vimMode is vimMode
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert vimMode._vim.pasteFromInternal() == "Text"

    # Loading a document resets the mode
    vimMode.setVimMode(nwVimMode.INSERT)
    assert nwGUI.docPanes.openDocument(C.hChapterDoc)
    assert vimMode._vim.mode == nwVimMode.NORMAL

    # Disable from settings, which also restores the shortcuts
    CONFIG.vimMode = False
    nwGUI._processConfigChanges(VIM_CHANGED)
    assert docEditor._vimMode is None
    assert docFooter._vimMode is None
    assert docFooter.vimStatus.isHidden() is True
    assert mainMenu.aViewDoc.shortcut().toString() == "Ctrl+R"
    assert mainMenu.aCloseView.shortcut().toString() == "Ctrl+Shift+R"


@pytest.mark.gui
def testEditorVimMode_InsertMode(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim commands entering INSERT mode."""
    docEditor = openVimEditor(nwGUI, projPath)

    # NORMAL mode doesn't insert text
    originalText = resetText(docEditor)
    for key in "hjkl":
        qtbot.keyClick(docEditor, key, delay=KEY_DELAY)
        assert docEditor.getText() == originalText

    # i: Insert before cursor
    resetText(docEditor)
    qtbot.keyClick(docEditor, "i", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "X", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert "X" in docEditor.getText()

    # I: Insert at beginning of line
    resetText(docEditor)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "I", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "START", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert docEditor.getText().splitlines()[0].startswith("START")

    # a: Append after cursor
    resetText(docEditor)
    qtbot.keyClick(docEditor, "a", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "X", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert "X" in docEditor.getText()

    # A: Append at end of line
    resetText(docEditor)
    qtbot.keyClick(docEditor, "A", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "END", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert docEditor.getText().splitlines()[0].endswith("END")

    # o: Open new line below
    resetText(docEditor)
    qtbot.keyClick(docEditor, "o", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "below", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert "below" in docEditor.getText().splitlines()[1]

    # O: Open new line above
    resetText(docEditor)
    qtbot.keyClick(docEditor, "O", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "above", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert "above" in docEditor.getText().splitlines()[0]

    # A/I: Append and insert at the ends of a wrapped paragraph
    para = " ".join(["word"] * 500)
    docEditor.setPlainText(para)
    docEditor.setCursorPosition(5)
    qtbot.keyClick(docEditor, "A", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "X", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    qtbot.keyClick(docEditor, "I", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "Y", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert docEditor.getText() == f"Y{para}X"


@pytest.mark.gui
def testEditorVimMode_NormalMode(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim NORMAL mode motions."""
    docEditor = openVimEditor(nwGUI, projPath)

    # b: Move to beginning of word
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + 2)
    qtbot.keyClicks(docEditor, "b", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("Line2")

    # e: Move to end of current word
    text = resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # e: Move to end of next word when already at end
    docEditor.setPlainText("Line1 lineExtra Line2 Line3")
    text = docEditor.getText()
    docEditor.setCursorPosition(len("Line1"))
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("lineExtra") + len("lineExtra")

    # e: At the end of the document, there's nowhere further to move
    docEditor.setPlainText("Line1")
    docEditor.setCursorPosition(5)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 5

    # $: Move to end of line
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "$", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # a: Move right and enter INSERT mode
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "a", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 1
    qtbot.keyClicks(docEditor, "TEST", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    assert docEditor.getText().startswith(("LTESSTine1", "LTESTine1"))

    # w: Move forward by word
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "w", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # l: Move right
    resetText(docEditor)
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 1

    # h: Move left
    resetText(docEditor)
    docEditor.setCursorPosition(2)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 1

    # h/l: Don't move past the start or end of the line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("Line2")
    docEditor.setCursorPosition(len("Line1"))
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # Navigation keys move the cursor and cancel a pending command
    text = resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 1
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText() == text

    # Navigation keys with Shift are ignored
    qtbot.keyClick(docEditor, QtKeyRight, QtModShift, delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 1
    assert docEditor.textCursor().hasSelection() is False

    # 0: Move to beginning of line
    resetText(docEditor)
    docEditor.setCursorPosition(3)
    qtbot.keyClick(docEditor, "0", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # $: Move to end of line after a motion
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)  # Otherwise "$" is not always captured
    qtbot.keyClick(docEditor, "$", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # gg: Move to start of document
    resetText(docEditor)
    qtbot.keyClick(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "g", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # zz: Centre view
    qtbot.keyClick(docEditor, "z", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "z", delay=KEY_DELAY)

    # G: Move to end of document
    text = resetText(docEditor)
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len(text)

    # $/0: Move to the end and start of a wrapped paragraph
    para = " ".join(["word"] * 500)
    docEditor.setPlainText(para)
    docEditor.setCursorPosition(5)
    qtbot.keyClick(docEditor, "$", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len(para)
    qtbot.keyClick(docEditor, "0", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # Unknown keys are discarded
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "qw", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # Unknown prefixed commands are discarded
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "dgdd", delay=KEY_DELAY)
    assert "Line1" not in docEditor.getText()


@pytest.mark.gui
def testEditorVimMode_Delete(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim delete commands."""
    docEditor = openVimEditor(nwGUI, projPath)
    vimMode = docEditor._vimMode
    assert vimMode is not None

    # dd: Delete line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "dd", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine3"

    # dd: Delete last line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3"))
    qtbot.keyClicks(docEditor, "dd", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2"
    assert docEditor.textCursor().position() == text.find("Line2")

    # dd: Delete a wrapped paragraph
    text = " ".join(["word"] * 500)
    docEditor.setPlainText(f"{text}\nLine2")
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "dd", delay=KEY_DELAY)
    assert docEditor.getText() == "Line2"
    assert vimMode._vim.pasteFromInternal() == text

    # d$: Delete to end of a wrapped paragraph
    docEditor.setPlainText(f"{text}\nLine2")
    docEditor.setCursorPosition(5)
    qtbot.keyClicks(docEditor, "d$", delay=KEY_DELAY)
    assert docEditor.getText() == "word \nLine2"

    # x: Delete character
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "x", delay=KEY_DELAY)
    assert getLines(docEditor)[0] == "ine1"

    # x: Don't delete the line break at the end of the line
    text = resetText(docEditor)
    docEditor.setCursorPosition(len("Line1"))
    qtbot.keyClicks(docEditor, "x", delay=KEY_DELAY)
    assert docEditor.getText() == text

    # dw: Delete word
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "dw", delay=KEY_DELAY)
    assert docEditor.getText() == "\nLine2\nLine3"

    # dw: Don't delete the line break at the end of the line
    text = resetText(docEditor)
    docEditor.setCursorPosition(len("Line1"))
    qtbot.keyClicks(docEditor, "dw", delay=KEY_DELAY)
    assert docEditor.getText() == text

    # d$: Delete to end of line
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "d$", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line2", "Line3"]

    # de: Delete to end of word
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "de", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line1", "Line3"]

    # de: Delete next word when already at end of word
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + len("Line2"))
    qtbot.keyClicks(docEditor, "de", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line1", "Line2"]

    # de: At the end of the document, there's nothing to delete
    docEditor.setPlainText("Line1")
    docEditor.setCursorPosition(5)
    qtbot.keyClicks(docEditor, "de", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1"

    # db: Delete word backwards
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "w", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "db", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line2", "Line3"]


@pytest.mark.gui
def testEditorVimMode_YankPaste(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim yank and paste commands."""
    docEditor = openVimEditor(nwGUI, projPath)
    vimMode = docEditor._vimMode
    assert vimMode is not None

    # p/P: Pasting with nothing yanked does nothing
    resetText(docEditor)
    assert vimMode._vim.pasteFromInternal() == ""
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2\nLine3"
    qtbot.keyClicks(docEditor, "P", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2\nLine3"

    # yy + p: Paste after current line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "yy", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line1", "Line2", "Line2", "Line3"]

    # yy + P: Paste before current line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3"))
    qtbot.keyClicks(docEditor, "yy", delay=KEY_DELAY)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "P", delay=KEY_DELAY)
    assert getLines(docEditor) == ["Line1", "Line3", "Line2", "Line3"]

    # yy: Yank a wrapped paragraph without moving the cursor
    para = " ".join(["word"] * 500)
    docEditor.setPlainText(f"{para}\nLine2")
    docEditor.setCursorPosition(5)
    qtbot.keyClicks(docEditor, "yy", delay=KEY_DELAY)
    assert vimMode._vim.pasteFromInternal() == para
    assert vimMode._vim.lineWise is True
    assert docEditor.textCursor().position() == 5

    # yw + p: Paste word after the cursor
    text = resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "yw", delay=KEY_DELAY)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLLine1ine2\nLine3"

    # x + p: Paste character at the end of a line
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "x", delay=KEY_DELAY)
    docEditor.setCursorPosition(len("ine1"))
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText() == "ine1L\nLine2\nLine3"

    # x + P: Paste character before the cursor
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "xP", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2\nLine3"


@pytest.mark.gui
def testEditorVimMode_VisualMode(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim VISUAL and V-LINE mode selection, yank and paste."""
    docEditor = openVimEditor(nwGUI, projPath)
    vimMode = docEditor._vimMode
    assert vimMode is not None
    originalText = resetText(docEditor)

    # v: Select, yank and paste
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3") + 1)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "j", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "k", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "y", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "p", delay=KEY_DELAY)
    text = docEditor.getText()
    assert "Line3" in text or text.endswith("n")

    # V: Select line, yank and paste
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClick(docEditor, "V", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "j", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "h", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "k", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "y", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "j", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText().splitlines() == ["Line1", "Line2", "Line3", "Line2"]

    # w: Extend selection by word
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "w", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len("Line1")

    # 0: Extend selection to start of line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + 3)
    qtbot.keyClicks(docEditor, "0", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("Line2")

    # a: Not a visual command, so nothing happens
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3") + 2)
    position = docEditor.textCursor().position()
    qtbot.keyClicks(docEditor, "a", delay=KEY_DELAY)
    assert docEditor.getText() == text
    assert docEditor.textCursor().position() == position

    # b: Extend selection to start of word
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + 2)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "b", delay=KEY_DELAY)
    assert docEditor.textCursor().selectedText() == "Li"

    # e: Extend selection to end of word
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().selectedText() == "Line1"

    # e: Extend selection to end of next word
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    docEditor.setPlainText("Line1 lineExtra Line2 Line3")
    docEditor.setCursorPosition(len("Line1") - 1)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert "lineExtra" in docEditor.textCursor().selectedText()

    # e: At the end of the document, there's nowhere further to extend
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    docEditor.setPlainText("Line1")
    docEditor.setCursorPosition(5)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 5

    # ggvG: Select all, delete and undo
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    resetText(docEditor)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText().strip() == ""
    qtbot.keyClick(docEditor, "u", delay=KEY_DELAY)
    assert docEditor.getText() == originalText

    # Ctrl+R: Redo and undo again
    qtbot.keyClick(docEditor, Qt.Key.Key_R, QtModCtrl, delay=KEY_DELAY)
    assert docEditor.getText().strip() == ""
    qtbot.keyClick(docEditor, "u", delay=KEY_DELAY)
    assert docEditor.getText() == originalText

    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # Gvgg: Select all backwards, delete and undo
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText().strip() == ""
    qtbot.keyClick(docEditor, "u", delay=KEY_DELAY)
    assert docEditor.getText() == originalText

    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # vly: Yank selection and paste
    resetText(docEditor)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "l", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "y", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "p", delay=KEY_DELAY)
    assert "Li" in docEditor.getText()

    # v$d: Delete to end of line
    resetText(docEditor)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "$", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText().splitlines()[0].strip() == ""

    # Vjy: Yank lines and paste
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClick(docEditor, "V", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "j", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "y", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText().splitlines().count("Line2") > 1

    # VGd: Delete all lines
    resetText(docEditor)
    qtbot.keyClick(docEditor, "V", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText().strip() == ""

    # Motions don't leave a pending command
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3"))
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "jgg", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # Unknown keys are discarded
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "qgg", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 0

    # v: Leave VISUAL mode
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    text = resetText(docEditor)
    line2 = text.find("Line2")
    docEditor.setCursorPosition(line2 + 2)
    qtbot.keyClicks(docEditor, "vv", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docEditor.textCursor().hasSelection() is False

    # V: Switch from VISUAL to V-LINE mode
    qtbot.keyClicks(docEditor, "vV", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.V_LINE
    assert docEditor.textCursor().selectedText() == "Line2"

    # v: Switch from V-LINE to VISUAL mode
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.VISUAL
    assert docEditor.textCursor().selectedText() == "Line2"

    # V: Leave V-LINE mode
    qtbot.keyClicks(docEditor, "VV", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docEditor.textCursor().hasSelection() is False

    # V: Keep the direction of a backwards selection
    docEditor.setCursorPosition(text.find("Line3") + 2)
    qtbot.keyClicks(docEditor, "vkV", delay=KEY_DELAY)
    cursor = docEditor.textCursor()
    assert vimMode._vim.mode == nwVimMode.V_LINE
    assert cursor.position() == line2
    assert cursor.anchor() == len(text)

    # i: Not a visual command, so nothing happens
    qtbot.keyClick(docEditor, "i", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.V_LINE
    assert docEditor.getText() == text

    # V: Select and delete whole wrapped paragraphs
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    para = " ".join(["word"] * 500)
    docEditor.setPlainText(f"{para}\nLine2\nLine3")
    docEditor.setCursorPosition(5)
    qtbot.keyClick(docEditor, "V", delay=KEY_DELAY)
    assert docEditor.textCursor().selectedText() == para
    qtbot.keyClick(docEditor, "j", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == len(f"{para}\nLine2")
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
    assert docEditor.getText() == "Line3"
    assert vimMode._vim.lineWise is True

    # h/l: Don't extend past the start or end of the line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "vhh", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("Line2")
    qtbot.keyClicks(docEditor, "$l", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == text.find("Line3") - 1
