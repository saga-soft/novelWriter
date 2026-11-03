"""
novelWriter - Editor Vim Mode Tests
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

from pathlib import Path

import pytest

from pytestqt.qtbot import QtBot

from novelwriter import CONFIG
from novelwriter.core.project import NWProject
from novelwriter.editor.editor import GuiDocEditor
from novelwriter.editor.vim import VimState
from novelwriter.enum import nwVimMode
from novelwriter.guimain import GuiMain
from novelwriter.types import QtKeyEscape

from tests.helpers import C, MockRnd, buildTestProject

KEY_DELAY = 2


def openVimEditor(nwGUI: GuiMain, projPath: Path) -> GuiDocEditor:
    """Open the scene document in the editor with vim mode enabled."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.docPanes.openDocument(C.hSceneDoc)
    CONFIG.vimMode = True
    nwGUI.docEditor.initSettings(updateVimMode=True)
    return nwGUI.docEditor


def resetText(docEditor: GuiDocEditor) -> str:
    """Reset the editor to the standard test text."""
    docEditor.setPlainText("Line1\nLine2\nLine3")
    return docEditor.getText()


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

    # Disabled by default
    assert docEditor._vimMode is None
    assert docFooter.vimStatus.isHidden() is True

    # Enable from settings
    CONFIG.vimMode = True
    docEditor.initSettings(updateVimMode=True)
    vimMode = docEditor._vimMode
    assert vimMode is not None
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docFooter._vimMode == nwVimMode.NORMAL
    assert docFooter.vimStatus.isHidden() is False

    # Mode changes are reported to the footer
    qtbot.keyClick(docEditor, "i", delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.INSERT
    assert docFooter._vimMode == nwVimMode.INSERT

    # Escape returns to NORMAL mode
    qtbot.keyClick(docEditor, QtKeyEscape, delay=KEY_DELAY)
    assert vimMode._vim.mode == nwVimMode.NORMAL
    assert docFooter._vimMode == nwVimMode.NORMAL

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

    # Disable from settings
    CONFIG.vimMode = False
    docEditor.initSettings(updateVimMode=True)
    assert docEditor._vimMode is None
    assert docFooter._vimMode is None
    assert docFooter.vimStatus.isHidden() is True


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

    # 0: Move to beginning of line
    resetText(docEditor)
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


@pytest.mark.gui
def testEditorVimMode_DeleteYankPaste(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim delete, yank and paste commands."""
    docEditor = openVimEditor(nwGUI, projPath)
    vimMode = docEditor._vimMode
    assert vimMode is not None

    def getLines() -> list[str]:
        return list(filter(str.strip, docEditor.getText().splitlines()))

    # p/P: Pasting with nothing yanked does nothing
    resetText(docEditor)
    assert vimMode._vim.pasteFromInternal() == ""
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2\nLine3"
    qtbot.keyClicks(docEditor, "P", delay=KEY_DELAY)
    assert docEditor.getText() == "Line1\nLine2\nLine3"

    # dd: Delete line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "dd", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line3"]

    # x: Delete character
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "x", delay=KEY_DELAY)
    assert getLines()[0] == "ine1"

    # yy + p: Paste after current line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "yy", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line2", "Line2", "Line3"]

    # yy + P: Paste before current line
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line3"))
    qtbot.keyClicks(docEditor, "yy", delay=KEY_DELAY)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "P", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line3", "Line2", "Line3"]

    # dw: Delete word
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "dw", delay=KEY_DELAY)
    assert getLines() == ["Line2", "Line3"]

    # d$: Delete to end of line
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "d$", delay=KEY_DELAY)
    assert getLines() == ["Line2", "Line3"]

    # de: Delete to end of word
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "de", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line3"]

    # de: Delete next word when already at end of word
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + len("Line2"))
    qtbot.keyClicks(docEditor, "de", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line2"]

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
    assert getLines() == ["Line2", "Line3"]

    # yw: Yank word
    text = resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "yw", delay=KEY_DELAY)
    docEditor.setCursorPosition(text.find("Line2"))
    qtbot.keyClicks(docEditor, "p", delay=KEY_DELAY)
    assert getLines() == ["Line1", "Line2", "Line1", "Line3"]


@pytest.mark.gui
def testEditorVimMode_VisualMode(qtbot: QtBot, nwGUI: GuiMain, projPath: Path, mockRnd: MockRnd):
    """Test vim VISUAL and V-LINE mode selection, yank and paste."""
    docEditor = openVimEditor(nwGUI, projPath)
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
    text = resetText(docEditor)
    docEditor.setCursorPosition(text.find("Line2") + 2)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "b", delay=KEY_DELAY)
    assert docEditor.textCursor().selectedText() == "Li"

    # e: Extend selection to end of word
    resetText(docEditor)
    docEditor.setCursorPosition(0)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().selectedText() == "Line1"

    # e: Extend selection to end of next word
    docEditor.setPlainText("Line1 lineExtra Line2 Line3")
    docEditor.setCursorPosition(len("Line1") - 1)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert "lineExtra" in docEditor.textCursor().selectedText()

    # e: At the end of the document, there's nowhere further to extend
    docEditor.setPlainText("Line1")
    docEditor.setCursorPosition(5)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "e", delay=KEY_DELAY)
    assert docEditor.textCursor().position() == 5

    # ggvG: Select all, delete and undo
    resetText(docEditor)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "g", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "v", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "G", delay=KEY_DELAY)
    qtbot.keyClick(docEditor, "d", delay=KEY_DELAY)
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
