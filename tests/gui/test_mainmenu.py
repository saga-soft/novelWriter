"""
novelWriter - GUI Main Menu Tests
=================================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

from unittest.mock import MagicMock

import pytest

from PyQt6.QtGui import QAction, QDesktopServices, QTextBlock
from PyQt6.QtWidgets import QFileDialog

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwKeyWords, nwShortcode, nwStats, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.editor.editor import GuiDocEditor
from novelwriter.enum import nwDocAction, nwDocInsert, nwFocus, nwView
from novelwriter.shared import _GuiAlert
from novelwriter.types import QtKeepAnchor, QtMoveRight, QtSelectWord

from tests.helpers import C, buildTestProject, writeFile


@pytest.mark.gui
def testGuiMainMenu_Slots(qtbot, monkeypatch, nwGUI, projPath):
    """Test the main menu slots."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Open Manual
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        CONFIG._manuals = {"manual": projPath / "manual.pdf"}
        CONFIG._manuals["manual"].touch()
        nwGUI.mainMenu._openUserManualFile()
        assert openUrl.called is True
        assert "manual.pdf" in openUrl.call_args[0][0].url()

    # No Manual Available
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        CONFIG._manuals = {}
        nwGUI.mainMenu._openUserManualFile()
        assert openUrl.called is False
        nwGUI.mainMenu._buildHelpMenu()
        assert "User Manual (PDF)" not in [a.text() for a in nwGUI.mainMenu.helpMenu.actions()]

    # Spell Checking
    assert SHARED.project.data.spellLang is None
    nwGUI.mainMenu._changeSpelling("en")
    assert SHARED.project.data.spellLang == "en"

    # Add Dictionaries Menu Entry
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "osWindows", True)
        nwGUI.mainMenu._buildToolsMenu()
        assert "Add Dictionaries" in [a.text() for a in nwGUI.mainMenu.toolsMenu.actions()]


@pytest.mark.gui
def testGuiMainMenu_EditFormat(qtbot, monkeypatch, nwGUI, prjLipsum):
    """Test the main menu Edit and Format entries."""
    monkeypatch.setattr(GuiDocEditor, "hasFocus", lambda *a: True)
    mainMenu = nwGUI.mainMenu
    docEditor = nwGUI.docEditor

    # Test Document Action with No Project
    assert docEditor.docAction(nwDocAction.COPY) is False

    assert nwGUI.openProject(prjLipsum) is True
    x = 72

    # Split By Chapter
    assert nwGUI.openDocument("4c4f28287af27") is True
    docEditor.setCursorPosition(x + 3)
    cleanText = docEditor.getText()[x : x + 47]

    # Bold
    mainMenu.aFmtBold.activate(QAction.ActionEvent.Trigger)
    fmtStr = "**Pellentesque** nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 51] == fmtStr
    mainMenu.aFmtBold.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Italic
    mainMenu.aFmtItalic.activate(QAction.ActionEvent.Trigger)
    fmtStr = "_Pellentesque_ nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 49] == fmtStr
    mainMenu.aFmtItalic.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Strikethrough
    mainMenu.aFmtStrike.activate(QAction.ActionEvent.Trigger)
    fmtStr = "~~Pellentesque~~ nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 51] == fmtStr
    mainMenu.aFmtStrike.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Should get us back to plain
    mainMenu.aFmtBold.activate(QAction.ActionEvent.Trigger)
    mainMenu.aFmtItalic.activate(QAction.ActionEvent.Trigger)
    mainMenu.aFmtItalic.activate(QAction.ActionEvent.Trigger)
    mainMenu.aFmtBold.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Double Quotes
    mainMenu.aFmtDQuote.activate(QAction.ActionEvent.Trigger)
    fmtStr = "\u201cPellentesque\u201d nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 49] == fmtStr
    mainMenu.aEditUndo.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Single Quotes
    mainMenu.aFmtSQuote.activate(QAction.ActionEvent.Trigger)
    fmtStr = "\u2018Pellentesque\u2019 nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 49] == fmtStr
    mainMenu.aEditUndo.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Block Formats
    # =============
    # cSpell:ignore Pellentesque erat nulla posuere commodo
    docEditor.setCursorPosition(x + 3)

    # Header 1
    mainMenu.aFmtHead1.activate(QAction.ActionEvent.Trigger)
    fmtStr = "# Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 49] == fmtStr

    # Header 2
    mainMenu.aFmtHead2.activate(QAction.ActionEvent.Trigger)
    fmtStr = "## Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 50] == fmtStr

    # Header 3
    mainMenu.aFmtHead3.activate(QAction.ActionEvent.Trigger)
    fmtStr = "### Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 51] == fmtStr

    # Header 4
    mainMenu.aFmtHead4.activate(QAction.ActionEvent.Trigger)
    fmtStr = "#### Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 52] == fmtStr

    # Title Format
    mainMenu.aFmtTitle.activate(QAction.ActionEvent.Trigger)
    fmtStr = "#! Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 50] == fmtStr

    # Unnumbered Chapter
    mainMenu.aFmtUnNum.activate(QAction.ActionEvent.Trigger)
    fmtStr = "##! Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 51] == fmtStr

    # Hard Scene
    mainMenu.aFmtHardSc.activate(QAction.ActionEvent.Trigger)
    fmtStr = "###! Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 52] == fmtStr

    # Clear Format
    mainMenu.aFmtNoFormat.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Comment On
    mainMenu.aFmtComment.activate(QAction.ActionEvent.Trigger)
    fmtStr = "% Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 49] == fmtStr

    # Comment Off
    mainMenu.aFmtComment.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Check comment with no space before text
    docEditor.setCursorPosition(x)
    docEditor.insertText("%")
    fmtStr = "%Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 48] == fmtStr

    mainMenu.aFmtNoFormat.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Undo/Redo
    mainMenu.aEditUndo.activate(QAction.ActionEvent.Trigger)
    fmtStr = "%Pellentesque nec erat ut nulla posuere commodo."
    assert docEditor.getText()[x : x + 48] == fmtStr
    mainMenu.aEditRedo.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 47] == cleanText

    # Cut, Copy and Paste
    docEditor.setCursorPosition(x)
    docEditor._makeSelection(QtSelectWord)

    mainMenu.aEditCut.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 50] == (" nec erat ut nulla posuere commodo. Curabitur nisi")

    mainMenu.aEditPaste.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 50] == ("Pellentesque nec erat ut nulla posuere commodo. Cu")

    docEditor.setCursorPosition(x)
    docEditor._makeSelection(QtSelectWord)

    mainMenu.aEditCopy.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 50] == ("Pellentesque nec erat ut nulla posuere commodo. Cu")

    docEditor.setCursorPosition(x)
    mainMenu.aEditPaste.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[x : x + 50] == ("PellentesquePellentesque nec erat ut nulla posuere")
    mainMenu.aEditUndo.activate(QAction.ActionEvent.Trigger)

    # Select Paragraph/All
    docEditor.setCursorPosition(x + 3)
    mainMenu.aSelectPar.activate(QAction.ActionEvent.Trigger)
    cursor = docEditor.textCursor()
    assert cursor.selectedText() == (
        "Pellentesque nec erat ut nulla posuere commodo. Curabitur nisi augue, imperdiet et porta "
        "imperdiet, efficitur id leo. Cras finibus arcu at nibh commodo congue. Proin suscipit "
        "placerat condimentum. Aenean ante enim, cursus id lorem a, blandit venenatis nibh. "
        "Maecenas suscipit porta elit, sit amet porta felis porttitor eu. Sed a dui nibh. "
        "Phasellus sed faucibus dui. Pellentesque felis nulla, ultrices non efficitur quis, "
        "rutrum id mi. Mauris tempus auctor nisl, in bibendum enim pellentesque sit amet. Proin "
        "nunc lacus, imperdiet nec posuere ac, interdum non lectus."
    )

    docEditor.setCursorPosition(x + 3)
    mainMenu.aSelectAll.activate(QAction.ActionEvent.Trigger)
    cursor = docEditor.textCursor()
    assert len(cursor.selectedText()) == 1929

    # Clear the Text
    docEditor.clear()
    assert docEditor.isEmpty

    # Alignment & Indent
    # ==================

    cleanText = "A single, short paragraph.\n\n"
    docEditor.setPlainText(cleanText)
    docEditor.setCursorPosition(0)

    # Left Align
    mainMenu.aFmtAlignLeft.activate(QAction.ActionEvent.Trigger)
    fmtStr = "A single, short paragraph. <<"
    assert docEditor.getText()[:29] == fmtStr

    # Right Align
    mainMenu.aFmtAlignRight.activate(QAction.ActionEvent.Trigger)
    fmtStr = ">> A single, short paragraph."
    assert docEditor.getText()[:29] == fmtStr

    # Centre Align
    mainMenu.aFmtAlignCentre.activate(QAction.ActionEvent.Trigger)
    fmtStr = ">> A single, short paragraph. <<"
    assert docEditor.getText()[:32] == fmtStr

    # Left Indent
    mainMenu.aFmtIndentLeft.activate(QAction.ActionEvent.Trigger)
    fmtStr = "> A single, short paragraph."
    assert docEditor.getText()[:28] == fmtStr

    # Right Indent
    mainMenu.aFmtIndentRight.activate(QAction.ActionEvent.Trigger)
    fmtStr = "> A single, short paragraph. <"
    assert docEditor.getText()[:30] == fmtStr

    # No Format
    mainMenu.aFmtNoFormat.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText()[:30] == cleanText

    # Other Checks

    # Replace Quotes
    docEditor.setPlainText(
        "### New Text\n\n"
        "Text with 'single' quotes and 'tricky stuff's'.\n\n"
        'Also text with "double" quotes which are "less tricky".\n\n'
    )

    mainMenu.aSelectAll.activate(QAction.ActionEvent.Trigger)
    mainMenu.aFmtReplSng.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == (
        "### New Text\n\n"
        "Text with \u2018single\u2019 quotes and \u2018tricky stuff\u2019s\u2019.\n\n"
        'Also text with "double" quotes which are "less tricky".\n\n'
    )

    mainMenu.aSelectAll.activate(QAction.ActionEvent.Trigger)
    mainMenu.aFmtReplDbl.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == (
        "### New Text\n\n"
        "Text with \u2018single\u2019 quotes and \u2018tricky stuff\u2019s\u2019.\n\n"
        "Also text with \u201cdouble\u201d quotes which are \u201cless tricky\u201d.\n\n"
    )

    # Remove in-paragraph line breaks
    docEditor.setPlainText(
        "### New Text\n\n"
        "@char: Someone\n"
        "@location: Somewhere\n\n"
        "% Some comment ...\n\n"
        "Here is some text\non multiple\nlines.\n\n"
        "With another paragraph\nhere."
    )
    mainMenu.aFmtRmBreaks.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == (
        "### New Text\n\n"
        "@char: Someone\n"
        "@location: Somewhere\n\n"
        "% Some comment ...\n\n"
        "Here is some text on multiple lines.\n\n"
        "With another paragraph here.\n"
    )

    docEditor.setPlainText(
        "### New Text\n\n"
        "@char: Someone\n"
        "@location: Somewhere\n\n"
        "% Some comment ...\n\n"
        "Here is some text\non multiple\nlines.\n\n"
        "With another paragraph\nhere."
    )
    cursor = docEditor.textCursor()
    cursor.setPosition(74)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, 29)
    docEditor.setTextCursor(cursor)
    mainMenu.aFmtRmBreaks.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == (
        "### New Text\n\n"
        "@char: Someone\n"
        "@location: Somewhere\n\n"
        "% Some comment ...\n\n"
        "Here is some text on multiple lines.\n\n"
        "With another paragraph\nhere."
    )

    # Test Invalid Document Action
    assert not docEditor.docAction(nwDocAction.NO_ACTION)

    # Test Invalid Formats
    docEditor.setPlainText(
        "### New Text\n\n"
        "@tag: Bod\n\n"
        "Text with 'single' quotes and 'tricky stuff's'.\n\n"
        'Also text with "double" quotes which are "less tricky".\n\n'
    )

    # Cannot Format Tag
    docEditor.setCursorPosition(17)
    assert not docEditor._formatBlock(nwDocAction.BLOCK_TXT)

    # Invalid Action
    docEditor.setCursorPosition(30)
    assert not docEditor._formatBlock(nwDocAction.NO_ACTION)

    # Ensure No Changes
    assert docEditor.getText() == (
        "### New Text\n\n"
        "@tag: Bod\n\n"
        "Text with 'single' quotes and 'tricky stuff's'.\n\n"
        'Also text with "double" quotes which are "less tricky".\n\n'
    )

    # qtbot.stop()


@pytest.mark.gui
def testGuiMainMenu_Insert(qtbot, monkeypatch, nwGUI, fncPath, projPath, mockRnd):
    """Test the Insert menu."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    assert nwGUI.openDocument(C.hSceneDoc) is True
    mainMenu = nwGUI.mainMenu
    docEditor = nwGUI.docEditor
    docEditor.clear()

    # Test Faulty Inserts
    docEditor.insertText("hello world")
    assert docEditor.getText() == "hello world"
    docEditor.clear()

    docEditor.insertText(nwDocInsert.NO_INSERT)
    assert docEditor.isEmpty

    docEditor.insertText(None)
    assert docEditor.isEmpty

    # qtbot.stop()
    docEditor.clear()

    # Check Menu Entries
    mainMenu.aInsENDash.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_ENDASH
    docEditor.clear()

    mainMenu.aInsEMDash.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_EMDASH
    docEditor.clear()

    mainMenu.aInsHorBar.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_HBAR
    docEditor.clear()

    mainMenu.aInsFigDash.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_FGDASH
    docEditor.clear()

    mainMenu.aInsQuoteLS.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == CONFIG.fmtSQuoteOpen
    docEditor.clear()

    mainMenu.aInsQuoteRS.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == CONFIG.fmtSQuoteClose
    docEditor.clear()

    mainMenu.aInsQuoteLD.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == CONFIG.fmtDQuoteOpen
    docEditor.clear()

    mainMenu.aInsQuoteRD.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == CONFIG.fmtDQuoteClose
    docEditor.clear()

    mainMenu.aInsMSApos.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_MAPOS
    docEditor.clear()

    mainMenu.aInsEllipsis.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_HELLIP
    docEditor.clear()

    mainMenu.aInsPrime.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_PRIME
    docEditor.clear()

    mainMenu.aInsDPrime.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_DPRIME
    docEditor.clear()

    mainMenu.aInsBullet.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_BULL
    docEditor.clear()

    mainMenu.aInsHyBull.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_HYBULL
    docEditor.clear()

    mainMenu.aInsFlower.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_FLOWER
    docEditor.clear()

    mainMenu.aInsPerMille.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_PERMIL
    docEditor.clear()

    mainMenu.aInsDegree.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_DEGREE
    docEditor.clear()

    mainMenu.aInsMinus.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_MINUS
    docEditor.clear()

    mainMenu.aInsTimes.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_TIMES
    docEditor.clear()

    mainMenu.aInsDivide.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_DIVIDE
    docEditor.clear()

    mainMenu.aInsNBSpace.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_NBSP
    docEditor.clear()

    mainMenu.aInsThinSpace.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_THSP
    docEditor.clear()

    mainMenu.aInsThinNBSpace.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == nwUnicode.U_THNBSP
    docEditor.clear()

    # Insert Keywords
    # ===============

    for action, key in zip(mainMenu.mInsKeywords.actions(), nwKeyWords.ALL_KEYS, strict=False):
        docEditor.setPlainText("Stuff")
        action.activate(QAction.ActionEvent.Trigger)
        assert docEditor.getText() == f"Stuff\n{key}: "

    # Faulty Keyword Inserts
    assert not docEditor.insertKeyWord("blabla")
    with monkeypatch.context() as mp:
        mp.setattr(QTextBlock, "isValid", lambda *a, **k: False)
        assert not docEditor.insertKeyWord(nwKeyWords.TAG_KEY)

    # Insert Fields
    # =============

    for action, field in zip(mainMenu.mInsField.actions(), nwStats.ALL_FIELDS, strict=False):
        value = nwShortcode.FIELD_VALUE.format(field)
        docEditor.setPlainText("Stuff ")
        docEditor.setCursorPosition(6)
        action.activate(QAction.ActionEvent.Trigger)
        assert docEditor.getText() == f"Stuff {value}"

    docEditor.clear()

    # Insert Special Comments
    # =======================

    docEditor.setPlainText("Stuff\n")
    mainMenu.aInsSynopsis.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "Stuff\n%Synopsis: \n"

    docEditor.setPlainText("Stuff\n")
    mainMenu.aInsShort.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "Stuff\n%Short: \n"

    # Breaks and Vertical Space
    # =========================

    docEditor.setPlainText("### Stuff\n")
    mainMenu.aInsNewPage.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "[newpage]\n### Stuff\n"

    docEditor.setPlainText("Line OneLine Two\n")
    docEditor.setCursorPosition(8)
    mainMenu.aInsLineBreak.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "Line One[br]Line Two\n"

    docEditor.setPlainText("### Stuff\n")
    mainMenu.aInsVSpaceS.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "[vspace]\n### Stuff\n"

    docEditor.setPlainText("### Stuff\n")
    mainMenu.aInsVSpaceM.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "[vspace:2]\n### Stuff\n"

    docEditor.clear()

    # Insert Text from File
    # =====================

    nwGUI.closeDocument()

    # First, with no path
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
    assert not nwGUI.importDocument()

    # Then with a path, but an invalid one
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (" ", ""))
    assert not nwGUI.importDocument()

    # Then a valid path, but bot a file that exists
    iFile = fncPath / "import.txt"
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(iFile), ""))
    assert not nwGUI.importDocument()

    # Create the file and try again, but with no target document open
    writeFile(iFile, "Foo")
    assert not nwGUI.importDocument()

    # Open the document from before, and add some text to it
    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText("Bar")
    assert docEditor.getText() == "Bar"

    # The document isn't empty, so the message box should pop
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert not nwGUI.importDocument()
        assert docEditor.getText() == "Bar"

    # Finally, accept the replaced text, this time we use the menu entry to trigger it
    mainMenu.aImportFile.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getText() == "Foo"

    # Reveal File Location
    # ====================

    mainMenu.aFileDetails.activate(QAction.ActionEvent.Trigger)
    path = str(projPath / "content" / "000000000000f.md")
    assert SHARED.lastAlert[-1] == f"File Location: {path}"

    # Focus and View Change
    # =====================

    with qtbot.waitSignal(mainMenu.requestFocusChange, timeout=1000) as signal:
        mainMenu.aFocusTree.activate(QAction.ActionEvent.Trigger)
    assert signal.args == [nwFocus.TREE]

    with qtbot.waitSignal(mainMenu.requestFocusChange, timeout=1000) as signal:
        mainMenu.aFocusDocument.activate(QAction.ActionEvent.Trigger)
    assert signal.args == [nwFocus.DOCUMENT]

    with qtbot.waitSignal(mainMenu.requestFocusChange, timeout=1000) as signal:
        mainMenu.aFocusStory.activate(QAction.ActionEvent.Trigger)
    assert signal.args == [nwFocus.STORY]

    with qtbot.waitSignal(mainMenu.requestViewChange, timeout=1000) as signal:
        mainMenu.aFindProj.activate(QAction.ActionEvent.Trigger)
    assert signal.args == [nwView.SEARCH]

    # qtbot.stop()
