"""
novelWriter - Document Editor Tests
===================================

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

import re

from pathlib import Path
from time import time
from unittest.mock import MagicMock

import pytest

from PyQt6.QtCore import QEvent, QMimeData, QPoint, QPointF, QRect, Qt, QThreadPool, QUrl, QVariant
from PyQt6.QtGui import (
    QAction,
    QClipboard,
    QColor,
    QDesktopServices,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QFont,
    QMouseEvent,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextOption,
    QWheelEvent,
)
from PyQt6.QtWidgets import QApplication, QMenu, QTextEdit

from novelwriter import CONFIG, SHARED
from novelwriter.common import decodeMimeHandles, utf16CharMap
from novelwriter.constants import nwConst, nwKeyWords, nwUnicode
from novelwriter.core.item import ProjectItem
from novelwriter.core.project import NWProject
from novelwriter.core.spellcheck import SpellEnchant
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.dialogs.editlink import GuiEditLink
from novelwriter.editor.editor import GuiDocEditor, _TagAction
from novelwriter.editor.editsearch import GuiDocEditSearch
from novelwriter.editor.textblock import TextBlockData, formatCheckText
from novelwriter.enum import nwComment, nwDocAction, nwDocInsert, nwItemClass, nwItemLayout, nwState, nwVimMode
from novelwriter.shared import _GuiAlert
from novelwriter.text.counting import standardCounter
from novelwriter.types import (
    QtAlignJustify,
    QtAlignLeft,
    QtImCurrentSelection,
    QtImCursorRectangle,
    QtKeepAnchor,
    QtKeyEscape,
    QtKeyReturn,
    QtModCtrl,
    QtModNone,
    QtMouseLeft,
    QtMoveAnchor,
    QtMoveRight,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSelectDocument,
    QtSelectWord,
)

from tests.helpers import C, buildTestProject, writeFile
from tests.mocked import causeOSError

KEY_DELAY = 1


def getMenuForPos(editor: GuiDocEditor, pos: int, select: bool = False) -> QMenu | None:
    """Create a context menu for a text position and return the menu
    object.
    """
    cursor = editor.textCursor()
    cursor.setPosition(pos)
    if select:
        cursor.select(QtSelectWord)
    editor.setTextCursor(cursor)
    editor._openContextFromCursor()
    for obj in editor.children():
        if isinstance(obj, QMenu) and obj.objectName() == "ContextMenu":
            return obj
    return None


@pytest.mark.gui
def testGuiDocEditor_Init(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test initialising the editor."""
    # Open project
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    docEditor.setPlainText(f"### Lorem Ipsum\n\n{ipsumText[0]}")
    nwGUI.saveDocument()

    # Check Defaults
    qDoc = docEditor.document()
    assert qDoc.defaultTextOption().alignment() == QtAlignLeft
    assert docEditor.verticalScrollBarPolicy() == QtScrollAsNeeded
    assert docEditor.horizontalScrollBarPolicy() == QtScrollAsNeeded
    assert CONFIG.fmtPadThin is False
    assert docEditor.docHeader.itemTitle.text() == (
        "<font style='color: #ff303030'>"
        "<a href='#0000000000008' style='color: #ff303030; text-decoration: none'>Novel</a>"
        "  \u203a  "
        "<a href='#000000000000d' style='color: #ff303030; text-decoration: none'>New Folder</a>"
        "  \u203a  "
        "<a href='#000000000000f' style='color: #ff303030; text-decoration: none'>New Scene</a>"
        "</font>"
    )
    assert docEditor.docHeader._docOutline == {0: "### New Scene"}

    # Check that editor handles settings
    CONFIG.textFont = QFont()
    CONFIG.doJustify = True
    CONFIG.showTabsNSpaces = True
    CONFIG.showLineEndings = True
    CONFIG.hideVScroll = True
    CONFIG.hideHScroll = True
    CONFIG.fmtPadThin = True
    CONFIG.showFullPath = False

    docEditor.initEditor()

    qDoc = docEditor.document()
    assert CONFIG.textFont == qDoc.defaultFont()
    assert qDoc.defaultTextOption().alignment() == QtAlignJustify
    assert qDoc.defaultTextOption().flags() & QTextOption.Flag.ShowTabsAndSpaces
    assert qDoc.defaultTextOption().flags() & QTextOption.Flag.ShowLineAndParagraphSeparators
    assert docEditor.verticalScrollBarPolicy() == QtScrollAlwaysOff
    assert docEditor.horizontalScrollBarPolicy() == QtScrollAlwaysOff
    assert CONFIG.fmtPadThin is True
    assert docEditor.docHeader.itemTitle.text() == (
        "<font style='color: #ff303030'>"
        "<a href='#000000000000f' style='color: #ff303030; text-decoration: none'>New Scene</a>"
        "</font>"
    )

    # Header
    # ======

    # Go to outline
    docEditor.setCursorLine(3)
    docEditor.docHeader.outlineMenu.actions()[0].trigger()
    assert docEditor.getCursorPosition() == 0

    # Non-integer data is ignored
    otherAction = QAction(docEditor.docHeader)
    otherAction.setData("not-an-int")
    docEditor.docHeader._gotoBlock(otherAction)
    assert docEditor.getCursorPosition() == 0

    # Select item from header
    with qtbot.waitSignal(docEditor.requestProjectItemSelected, timeout=1000) as signal:
        docEditor.docHeader._processLabelLink(f"#{docEditor.docHeader._docHandle}")
        assert signal.args == [docEditor.docHeader._docHandle, True]

    # A link that isn't a project item reference is ignored
    with qtbot.assertNotEmitted(docEditor.requestProjectItemSelected, wait=100):
        docEditor.docHeader._processLabelLink("https://example.com")

    # An invalid handle, with the full path setting off, leaves the
    # title unchanged
    assert CONFIG.showFullPath is False
    titleBefore = docEditor.docHeader.itemTitle.text()
    docEditor.docHeader.setHandle(C.hInvalid)
    assert docEditor.docHeader.itemTitle.text() == titleBefore

    # Toggle tool bar from header
    with qtbot.waitSignal(docEditor.docHeader.toggleToolBarRequest, timeout=1000):
        docEditor.docHeader.tbButton.click()

    # Toggle focus mode from header
    with qtbot.waitSignal(docEditor.toggleFocusModeRequest, timeout=1000):
        docEditor.docHeader.minmaxButton.click()

    # Close from header
    with qtbot.waitSignal(docEditor.docHeader.closeDocumentRequest, timeout=1000):
        docEditor.docHeader.closeButton.click()

    assert docEditor.docHeader.tbButton.isVisible() is False
    assert docEditor.docHeader.searchButton.isVisible() is False
    assert docEditor.docHeader.closeButton.isVisible() is False
    assert docEditor.docHeader.minmaxButton.isVisible() is False
    assert docEditor.docHeader.itemTitle.text() == ""

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_LoadText(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test loading text into the editor."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    longText = "### Lorem Ipsum\n\n{0}".format("\n\n".join(ipsumText * 20))
    docEditor.replaceText(longText)
    nwGUI.saveDocument()
    nwGUI.closeDocument()

    # Invalid handle
    assert docEditor.loadText("abcdefghijklm") is False

    # Regular open
    assert docEditor.loadText(C.hSceneDoc) is True

    # Regular open, with line number (1 indexed)
    assert docEditor.loadText(C.hSceneDoc, tLine=4) is True
    cursPos = docEditor.getCursorPosition()
    assert docEditor.document().findBlock(cursPos).blockNumber() == 3

    # Load empty document
    docEditor.replaceText("")
    nwGUI.saveDocument()
    assert docEditor.loadText(C.hSceneDoc) is True
    assert docEditor.toPlainText() == ""

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_SaveText(qtbot, monkeypatch, caplog, nwGUI, projPath, ipsumText, mockRnd):
    """Test saving text from the editor."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    longText = "### Lorem Ipsum\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(longText)

    # Missing item
    nwItem = docEditor._nwItem
    docEditor._nwItem = None
    assert docEditor.saveText() is False
    docEditor._nwItem = nwItem

    # Unknown handle
    docEditor._docHandle = "0123456789abcdef"
    assert docEditor.saveText() is False
    docEditor._docHandle = C.hSceneDoc

    # Cause error when saving
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert docEditor.saveText() is False
        assert "Could not save document." in caplog.text

    # Change header level
    assert SHARED.project.tree[C.hSceneDoc].itemLayout == nwItemLayout.DOCUMENT  # type: ignore
    docEditor.replaceText(longText[1:])
    assert docEditor.saveText() is True
    assert SHARED.project.tree[C.hSceneDoc].itemLayout == nwItemLayout.DOCUMENT  # type: ignore

    # Regular save
    assert docEditor.saveText() is True

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_SaveTextEdgeCases(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test defensive branches in saveText not covered by the main save
    text test: a write failure with no hash mismatch, and a successful
    forced overwrite after a hash mismatch.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### Lorem Ipsum\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(text)

    nwDocument = docEditor._nwDocument
    assert nwDocument is not None

    # A write failure that isn't due to a hash mismatch does not prompt
    # the user to overwrite, and simply reports the error
    with monkeypatch.context() as mp:
        mp.setattr(type(nwDocument), "writeDocument", lambda *a, **k: False)
        mp.setattr(type(nwDocument), "hashError", property(lambda self: False))
        assert docEditor.saveText() is False
        assert SHARED.lastAlert[0] == "Could not save document."

    # A hash mismatch that the user confirms overwriting for, and which
    # then succeeds, is treated as a successful save
    writeFile(Path(nwDocument.fileLocation), "Changed outside of novelWriter")
    docEditor.setDocumentChanged(True)
    assert docEditor.saveText() is True
    assert docEditor.docChanged is False


@pytest.mark.gui
def testGuiDocEditor_DragAndDrop(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test drag and drop in the editor."""
    docEditor = nwGUI.docEditor

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hTitlePage) is True
    assert docEditor.docHandle == C.hTitlePage

    middle = docEditor.viewport().rect().center()
    action = Qt.DropAction.MoveAction
    mouse = Qt.MouseButton.NoButton

    model = SHARED.project.tree.model
    docMime = model.mimeData([model.indexFromHandle(C.hSceneDoc)])
    noneMime = QMimeData()
    noneMime.setData("plain/text", b"")
    assert decodeMimeHandles(docMime) == [C.hSceneDoc]

    # Drag Enter
    mockEnter = MagicMock()
    docEvent = QDragEnterEvent(middle, action, docMime, mouse, QtModNone)
    noneEvent = QDragEnterEvent(middle, action, noneMime, mouse, QtModNone)
    with monkeypatch.context() as mp:
        mp.setattr(QTextEdit, "dragEnterEvent", mockEnter)

        # Document Enter
        docEditor.dragEnterEvent(docEvent)
        assert docEvent.isAccepted() is True
        assert mockEnter.call_count == 0

        # Regular Enter
        docEditor.dragEnterEvent(noneEvent)
        assert mockEnter.call_count == 1

    # Drag Move
    mockMove = MagicMock()
    docEvent = QDragMoveEvent(middle, action, docMime, mouse, QtModNone)
    noneEvent = QDragMoveEvent(middle, action, noneMime, mouse, QtModNone)
    with monkeypatch.context() as mp:
        mp.setattr(QTextEdit, "dragMoveEvent", mockMove)

        # Document Move
        docEditor.dragMoveEvent(docEvent)
        assert docEvent.isAccepted() is True
        assert mockMove.call_count == 0

        # Regular Move
        docEditor.dragMoveEvent(noneEvent)
        assert mockMove.call_count == 1

    # Drop
    middle = QPointF(docEditor.viewport().rect().center())
    mockDrop = MagicMock()
    docEvent = QDropEvent(middle, action, docMime, mouse, QtModNone)
    noneEvent = QDropEvent(middle, action, noneMime, mouse, QtModNone)
    with monkeypatch.context() as mp:
        mp.setattr(QTextEdit, "dropEvent", mockDrop)

        # Document Drop
        docEditor.dropEvent(docEvent)
        assert mockDrop.call_count == 0
        assert docEditor.docHandle == C.hSceneDoc

        # Regular Move
        docEditor.dropEvent(noneEvent)
        assert mockDrop.call_count == 1

        # A dropped handle that isn't a file (e.g. a folder) does nothing
        folderMime = model.mimeData([model.indexFromHandle(C.hChapterDir)])
        folderEvent = QDropEvent(middle, action, folderMime, mouse, QtModNone)
        docEditor.dropEvent(folderEvent)
        assert docEditor.docHandle == C.hSceneDoc


@pytest.mark.gui
def testGuiDocEditor_MetaData(qtbot, nwGUI, projPath, mockRnd):
    """Test extracting various meta data and other values."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    # Get Text
    # This should replace line and paragraph separators, but preserve
    # non-breaking spaces.
    newText = "### New Scene\u2029\u2029Some\u2028text.\u2029More\u00a0text.\u2029"
    docEditor.replaceText(newText)
    assert docEditor.getText() == ("### New Scene\n\nSome\ntext.\nMore\u00a0text.\n")

    # Check Properties
    assert docEditor.docChanged is True
    assert docEditor.docHandle == C.hSceneDoc
    assert docEditor.lastActive > 0.0
    assert docEditor.isEmpty is False

    # Cursor Position
    docEditor.setCursorPosition(10)
    assert docEditor.getCursorPosition() == 10
    assert SHARED.project.tree[C.hSceneDoc].cursorPos != 10  # type: ignore
    docEditor.saveCursorPosition()
    assert SHARED.project.tree[C.hSceneDoc].cursorPos == 10  # type: ignore

    docEditor.setCursorLine(None)
    assert docEditor.getCursorPosition() == 10
    docEditor.setCursorLine(3)
    assert docEditor.getCursorPosition() == 15

    # An out-of-range line number does not move the cursor
    docEditor.setCursorLine(1000)
    assert docEditor.getCursorPosition() == 15

    # Cursor Selection
    docEditor.setCursorSelection(0, 3)
    assert docEditor.textCursor().selectedText() == "###"

    # Invalid selections are ignored
    docEditor.setCursorSelection(-1, 3)
    assert docEditor.textCursor().selectedText() == "###"
    docEditor.setCursorSelection(0, 0)
    assert docEditor.textCursor().selectedText() == "###"

    # Reveal Location
    docEditor.revealLocation()
    assert SHARED.lastAlert[0] == "Document Details"

    nwDocument = docEditor._nwDocument
    docEditor._nwDocument = None
    docEditor.revealLocation()
    assert SHARED.lastAlert[0] == "Document Details"  # Unchanged, nothing happened
    docEditor._nwDocument = nwDocument

    # Document Changed Signal
    docEditor._docChanged = False
    with qtbot.waitSignal(docEditor.editedStatusChanged, raising=True, timeout=100):
        docEditor.setDocumentChanged(True)
    assert docEditor._docChanged is True

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_ContextMenu(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """Test the editor context menu."""
    monkeypatch.setattr(QMenu, "exec", lambda *a: None)
    monkeypatch.setattr(QMenu, "setParent", lambda *a: None)

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    sceneItem = SHARED.project.tree[C.hSceneDoc]
    assert sceneItem is not None

    docText = "### A Scene\n\n@pov: Jane\n\nSome text ...\n\n... and a link to http://example.com\n\n"
    docEditor.setPlainText(docText)
    assert docEditor.getText() == docText

    # Rename Item from Heading
    ctxMenu = getMenuForPos(docEditor, 1)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Set as Document Name",
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLabel, "getLabel", lambda a, text: (text, True))
        assert sceneItem.itemName == "New Scene"
        ctxMenu.actions()[0].trigger()
        assert sceneItem.itemName == "A Scene"
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Open Link
    ctxMenu = getMenuForPos(docEditor, 63)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Open URL",
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Create Character
    ctxMenu = getMenuForPos(docEditor, 21)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Create Note for Tag",
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.actions()[0].trigger()
    janeItem = SHARED.project.tree["0000000000011"]
    assert janeItem is not None
    assert janeItem.itemName == "Jane"
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Follow Character Tag
    ctxMenu = getMenuForPos(docEditor, 21)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "View Tag Source",
        "Edit Tag Source",
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.actions()[0].trigger()
    assert nwGUI.docViewer.docHandle == "0000000000011"
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Select Word
    ctxMenu = getMenuForPos(docEditor, 31)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.actions()[3].trigger()
    assert docEditor.textCursor().selectedText() == "text"
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Select Paragraph
    ctxMenu = getMenuForPos(docEditor, 31)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.actions()[4].trigger()
    assert docEditor.textCursor().selectedText() == "Some text ..."
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Select All
    ctxMenu = getMenuForPos(docEditor, 31)
    assert ctxMenu is not None
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    ctxMenu.actions()[2].trigger()
    assert docEditor.textCursor().selectedText() == docEditor.document().toRawText()
    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Copy Text
    clipboard = QApplication.clipboard()
    assert clipboard is not None

    ctxMenu = getMenuForPos(docEditor, 31, True)
    assert ctxMenu is not None
    assert docEditor.textCursor().selectedText() == "text"
    actions = [x.text() for x in ctxMenu.actions() if x.text()]
    assert actions == [
        "Cut",
        "Copy",
        "Paste",
        "Select All",
        "Select Word",
        "Select Paragraph",
        "More Actions",
    ]
    clipboard.clear()
    ctxMenu.actions()[1].trigger()
    assert clipboard.text(QClipboard.Mode.Clipboard) == "text"

    # Cut Text
    clipboard.clear()
    ctxMenu.actions()[0].trigger()
    assert clipboard.text(QClipboard.Mode.Clipboard) == "text"
    assert "text" not in docEditor.getText()

    # Paste Text
    ctxMenu.actions()[2].trigger()
    assert docEditor.getText() == docText

    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_SpellChecking(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document spell checker."""
    monkeypatch.setattr(QMenu, "exec", lambda *a: None)
    monkeypatch.setattr(QMenu, "setParent", lambda *a: None)

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # The test must not depend on which dictionaries are available on
    # the host system, so all words are accepted from the start, and
    # the spell check worker must run synchronously
    monkeypatch.setattr(SpellEnchant, "checkWord", lambda *a: True)
    monkeypatch.setattr(SHARED, "runInThreadPool", lambda r: r.run())

    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(text)

    # Toggle State
    # ============

    # No language set
    SHARED.spelling._language = None
    SHARED.project.data.setSpellCheck(False)
    docEditor.toggleSpellCheck(True)
    assert SHARED.project.data.spellCheck is False

    # No spell checker available
    SHARED.spelling._language = "en"
    docEditor.toggleSpellCheck(True)
    assert SHARED.project.data.spellCheck is True

    CONFIG.hasEnchant = False
    docEditor.toggleSpellCheck(True)
    assert SHARED.project.data.spellCheck is False
    CONFIG.hasEnchant = True
    docEditor.toggleSpellCheck(True)
    assert SHARED.project.data.spellCheck is True

    # Plain Toggle
    docEditor.toggleSpellCheck(None)
    assert SHARED.project.data.spellCheck is False

    # Run SpellCheck
    # ==============
    SHARED.project.data.setSpellCheck(True)
    LORAX = "Lorax\U0001f03a"

    cursor = docEditor.textCursor()
    cursor.setPosition(16)
    data = cursor.block().userData()
    assert cursor.block().text().startswith("Lorem")
    assert isinstance(data, TextBlockData)
    data._spellErrors = [(0, 5, "Lorem")]

    # No known position
    assert docEditor._qDocument.spellErrorAtPos(-1) == ("", -1, -1, [])

    # Multiple entries: the first doesn't match, the second does
    blockPos = cursor.block().position()
    data._spellErrors = [(0, 5, "Lorem"), (6, 11, "ipsum")]
    with monkeypatch.context() as mp:
        mp.setattr(SpellEnchant, "suggestWords", lambda *a: [])
        assert docEditor._qDocument.spellErrorAtPos(blockPos + 8) == ("ipsum", 6, 11, [])

    # No entry matches the given position
    assert docEditor._qDocument.spellErrorAtPos(blockPos + 20) == ("", -1, -1, [])

    # Meta data lookup follows the same pattern
    data._metaData = [(0, 5, "Lorem", "url"), (6, 11, "ipsum", "url")]
    assert docEditor._qDocument.metaDataAtPos(-1) == ("", "")
    assert docEditor._qDocument.metaDataAtPos(blockPos + 8) == ("ipsum", "url")
    assert docEditor._qDocument.metaDataAtPos(blockPos + 20) == ("", "")

    data._spellErrors = [(0, 5, "Lorem")]

    # The spell error should be rendered as an extra selection
    docEditor._updateCheckSelections()
    spellSel = [
        s
        for s in docEditor.extraSelections()
        if s.format.underlineStyle() == QTextCharFormat.UnderlineStyle.SpellCheckUnderline
    ]
    assert len(spellSel) == 1
    assert spellSel[0].cursor.selectionStart() == blockPos
    assert spellSel[0].cursor.selectionEnd() == blockPos + 5

    # With spell check disabled, the selections should be cleared
    SHARED.project.data.setSpellCheck(False)
    docEditor._updateCheckSelections()
    assert docEditor._spellSelections == []
    SHARED.project.data.setSpellCheck(True)

    # With Suggestion
    with monkeypatch.context() as mp:
        mp.setattr(SpellEnchant, "suggestWords", lambda *a: [LORAX])
        suggestion = f"{nwUnicode.U_ENDASH} {LORAX}"

        ctxMenu = getMenuForPos(docEditor, 16)
        assert ctxMenu is not None
        actions = [x.text() for x in ctxMenu.actions()]
        assert "Spelling Suggestion(s)" in actions
        assert suggestion in actions
        ctxMenu.actions()[actions.index(suggestion)].trigger()
        QApplication.processEvents()
        assert docEditor.getText() == text.replace("Lorem", LORAX, 1)
        ctxMenu.setObjectName("")
        ctxMenu.deleteLater()

    # Update Entry
    data._spellErrors = [(0, 7, LORAX)]

    # Without Suggestion
    with monkeypatch.context() as mp:
        mp.setattr(SpellEnchant, "suggestWords", lambda *a: [])

        ctxMenu = getMenuForPos(docEditor, 16)
        assert ctxMenu is not None
        actions = [x.text() for x in ctxMenu.actions()]
        assert f"{nwUnicode.U_ENDASH} No Suggestions" in actions
        assert docEditor.getText() == text.replace("Lorem", LORAX, 1)
        ctxMenu.setObjectName("")
        ctxMenu.deleteLater()

    # Add to Dictionary
    with monkeypatch.context() as mp:
        mp.setattr(SpellEnchant, "suggestWords", lambda *a: [])

        ctxMenu = getMenuForPos(docEditor, 16)
        assert ctxMenu is not None
        actions = [x.text() for x in ctxMenu.actions()]
        assert "Ignore Word" in actions
        assert "Add Word to Dictionary" in actions

        assert LORAX not in SHARED.spelling._userDict
        ctxMenu.actions()[actions.index("Ignore Word")].trigger()
        assert LORAX not in SHARED.spelling._userDict
        ctxMenu.actions()[actions.index("Add Word to Dictionary")].trigger()
        assert LORAX in SHARED.spelling._userDict
        ctxMenu.setObjectName("")
        ctxMenu.deleteLater()

    # No spelling error at the clicked position: no spelling actions
    with monkeypatch.context() as mp:
        mp.setattr(SpellEnchant, "suggestWords", lambda *a: [])

        ctxMenu = getMenuForPos(docEditor, blockPos + 20)
        assert ctxMenu is not None
        actions = [x.text() for x in ctxMenu.actions()]
        assert "Ignore Word" not in actions
        assert "Spelling Suggestion(s)" not in actions
        ctxMenu.setObjectName("")
        ctxMenu.deleteLater()

    # Editing a block flags it for the debounced spell check
    docEditor._dirtyBlocks.clear()
    docEditor.setCursorPosition(blockPos + 5)
    docEditor.textCursor().insertText("x")
    assert docEditor._dirtyBlocks != {}
    assert docEditor._timerTextCheck.isActive()

    # Running the check dispatches the dirty blocks to the worker
    docEditor._dispatchTextCheck()
    assert docEditor._dirtyBlocks == {}
    assert docEditor._checkJob is None

    # An error under the caret is not underlined
    data = docEditor.textCursor().block().userData()
    assert isinstance(data, TextBlockData)
    data._spellErrors = [(0, 5, "Lorem")]
    docEditor.setCursorPosition(blockPos + 3)
    docEditor._updateCheckSelections()
    assert docEditor._suppressed is True
    assert docEditor._spellSelections == []

    # Moving the caret out of the word restores the underline
    docEditor.setCursorPosition(blockPos + 10)
    docEditor._updateCheckSelections()
    assert docEditor._suppressed is False
    assert len(docEditor._spellSelections) == 1

    # Background Spell Pass
    # =====================
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.constants.nwConst.CHECK_PASS_CHUNK", 2)

        # A full pass runs chunked worker jobs until the document is
        # done, which with a synchronous worker completes immediately
        docEditor._beginCheckPass()
        assert docEditor._checkPassPos is None
        assert docEditor._checkJob is None

        # A full spell check notifies when the pass completes
        docEditor.spellCheckDocument()
        assert docEditor._spellPassNotify is False

    # Results from a cancelled job are dropped
    docEditor._textCheckResults(docEditor._checkJobId + 1, [])
    assert docEditor._checkJob is None

    # Results for blocks modified while checking are discarded
    block = docEditor.textCursor().block()
    data = block.userData()
    assert isinstance(data, TextBlockData)
    data._spellErrors = []
    docEditor._checkJobId += 1
    docEditor._checkJob = (docEditor._checkJobId, [(block, data, data.revision - 1)])
    docEditor._textCheckResults(docEditor._checkJobId, [(0, [(0, 5, "wrong")], [])])
    assert data.spellErrors == []
    assert docEditor._checkJob is None

    # No new dispatch is made while a job is still in flight
    docEditor._dirtyBlocks[block.blockNumber()] = block
    docEditor._checkJob = (docEditor._checkJobId, [])
    docEditor._dispatchTextCheck()
    assert docEditor._dirtyBlocks != {}
    docEditor._checkJob = None
    docEditor._dirtyBlocks.clear()

    # qtbot.stop()


def testGuiDocEditor_FormatCheckText():
    """Test the raw multi-space and trailing-space checker function."""
    # Multiple runs of multiple spaces
    assert formatCheckText("one  two   three", 0, None) == [(3, 5, "multi"), (8, 11, "multi")]

    # Trailing space only
    assert formatCheckText("one two ", 0, None) == [(7, 8, "trail")]

    # A trailing run is reported as both kinds
    assert formatCheckText("one  two  ", 0, None) == [(3, 5, "multi"), (8, 10, "multi"), (8, 10, "trail")]

    # No errors
    assert formatCheckText("one two three", 0, None) == []

    # The offset is respected
    assert formatCheckText("one  two", 4, None) == []

    # Positions are translated through a UTF-16 map
    text = "a\U0001f605  b "
    utf16Map = utf16CharMap(text)
    assert formatCheckText(text, 0, utf16Map) == [(3, 5, "multi"), (6, 7, "trail")]

    # A URL padded to spaces of equal length by TextBlockData.processText
    # must not be mistaken for a real run of multiple spaces, or every
    # comment/text line containing a URL would be flagged
    data = TextBlockData()
    text = "See http://example.com for details.  "
    data.processText(text, 0, None)
    assert formatCheckText(data._text, 0, None) == [(3, 23, "multi"), (35, 37, "multi"), (35, 37, "trail")]
    assert data.formatCheck() == [(35, 37, "multi"), (35, 37, "trail")]

    # A cached spell/format error may hold a position past the end of a
    # shortened block, e.g. right after an undo removes previously typed
    # text. processText() must drop the stale cache immediately, rather
    # than waiting for the debounced recheck, or the stale, out-of-range
    # positions can briefly render into the following block
    data.setSpellErrors([(0, 100, "wrong")])
    data.setFormatErrors([(0, 100, "multi")])
    data.processText("short", 0, None)
    assert data.spellErrors == []
    assert data.formatErrors == []


def testGuiDocEditor_ProcessTextLinks():
    """Test that TextBlockData detects Markdown links, and does not
    also flag the URL they contain as a separate bare URL.
    """
    data = TextBlockData()

    # A bare URL is kept in the spell text, and recorded as a "url"
    text = "See http://example.com for details."
    data.processText(text, 0, None)
    assert data._text == "See                    for details."
    assert data.metaData == [(4, 22, "http://example.com", "url")]

    # A Markdown link has its brackets and URL blanked from the spell
    # text, keeping only the link text, and is recorded as a "link"
    # with the target URL
    text = "See [a link](http://example.com) for details."
    data.processText(text, 0, None)
    assert data._text == "See  a link                      for details."
    assert data.metaData == [(4, 32, "http://example.com", "link")]

    # The URL inside a Markdown link must not also be picked up as a
    # separate bare URL, while an unrelated bare URL still is
    text = "See [a link](http://example.com) and http://other.com too."
    data.processText(text, 0, None)
    assert data.metaData == [
        (4, 32, "http://example.com", "link"),
        (37, 53, "http://other.com", "url"),
    ]

    # A Markdown link's positions are translated through a UTF-16 map
    # when the block contains a 4 byte Unicode character
    text = "\U0001f605 [a link](http://example.com) done."
    utf16Map = utf16CharMap(text)
    data.processText(text, 0, utf16Map)
    assert data.metaData == [(3, 31, "http://example.com", "link")]

    # A bare "file://" URL has no "http" substring, so the bare URL
    # check must not be gated on that alone, or it would be missed
    text = "See file:///tmp/note.txt here."
    data.processText(text, 0, None)
    assert data.metaData == [(4, 24, "file:///tmp/note.txt", "url")]

    # A Markdown link's target need not be a URL with a "://" scheme,
    # so the link check must not be gated on that either
    text = "See [reference](internal-note) here."
    data.processText(text, 0, None)
    assert data.metaData == [(4, 30, "internal-note", "link")]


@pytest.mark.gui
def testGuiDocEditor_FormatChecking(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the document multi-space and trailing-space checker."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    monkeypatch.setattr(SHARED, "runInThreadPool", lambda r: r.run())

    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\nA  double space, and a trailing space \n"
    docEditor.replaceText(text)

    blockPos = text.index("A  double")

    # With the feature disabled, no markers are generated
    CONFIG.showMultiSpaces = False
    docEditor._beginCheckPass()
    assert docEditor._formatSelections == []

    # With the feature enabled, both errors are found and rendered as
    # extra selections with the same format, regardless of kind
    CONFIG.showMultiSpaces = True
    docEditor._beginCheckPass()

    data = docEditor.textCursor().document().findBlock(blockPos).userData()
    assert isinstance(data, TextBlockData)
    assert data.formatErrors == [(1, 3, "multi"), (37, 38, "trail")]

    formatSel = sorted(
        (
            s
            for s in docEditor.extraSelections()
            if s.format.underlineStyle() == QTextCharFormat.UnderlineStyle.SingleUnderline
        ),
        key=lambda s: s.cursor.selectionStart(),
    )
    assert len(formatSel) == 2
    assert formatSel[0].cursor.selectionStart() == blockPos + 1
    assert formatSel[0].cursor.selectionEnd() == blockPos + 3

    assert formatSel[1].cursor.selectionStart() == blockPos + 37
    assert formatSel[1].cursor.selectionEnd() == blockPos + 38

    # A trailing space right under the caret is not yet flagged, since
    # it's a natural, transient state while the line is still being
    # typed. Other errors in the same block remain visible
    docEditor.setCursorPosition(blockPos + 38)
    docEditor._updateCheckSelections()
    assert docEditor._suppressed is True
    assert len(docEditor._formatSelections) == 1
    assert docEditor._formatSelections[0].cursor.selectionStart() == blockPos + 1

    # Moving the caret elsewhere in the same block, away from the
    # trailing space itself, does not suppress it
    docEditor.setCursorPosition(blockPos + 5)
    docEditor._updateCheckSelections()
    assert docEditor._suppressed is False
    assert len(docEditor._formatSelections) == 2

    # Toggling the feature back off clears the markers
    CONFIG.showMultiSpaces = False
    docEditor._beginCheckPass()
    assert docEditor._formatSelections == []


@pytest.mark.gui
def testGuiDocEditor_UpdateSyntaxColors(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """A theme change must immediately re-colour any extra selections
    that already exist, rather than waiting for the cursor to move or
    for the spell/format check cache to be invalidated by an edit.
    """
    monkeypatch.setattr(SHARED, "runInThreadPool", lambda r: r.run())

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\nA  double space, and a trailing space \n"
    docEditor.replaceText(text)
    blockPos = text.index("A  double")

    # Build a format error selection
    CONFIG.showMultiSpaces = True
    docEditor._beginCheckPass()
    data = docEditor.textCursor().document().findBlock(blockPos).userData()
    assert isinstance(data, TextBlockData)
    assert data.formatErrors != []

    # Build a spell error selection
    SHARED.project.data.setSpellCheck(True)
    data._spellErrors = [(0, 1, "A")]
    docEditor._updateCheckSelections()
    assert docEditor._spellSelections != []

    # Build a search match selection
    docEditor.highlightSearchSelections([blockPos], [blockPos + 1])
    assert len(docEditor._searchSelections) == 1

    # Build the current line highlight selection
    CONFIG.lineHighlight = True
    docEditor.setCursorPosition(blockPos)
    assert docEditor._selection.cursor.position() == blockPos

    # Change the theme colours and refresh the syntax colours only,
    # without moving the cursor or editing the document
    SHARED.theme.syntaxTheme.error = QColor(1, 2, 3)
    SHARED.theme.syntaxTheme.spell = QColor(10, 11, 12)
    SHARED.theme.searchCol = QColor(4, 5, 6)
    SHARED.theme.syntaxTheme.line = QColor(7, 8, 9)
    docEditor.updateSyntaxColors()

    formatSel = next(
        s
        for s in docEditor.extraSelections()
        if s.format.underlineStyle() == QTextCharFormat.UnderlineStyle.SingleUnderline
    )
    assert formatSel.format.underlineColor() == QColor(1, 2, 3)

    spellSel = next(
        s
        for s in docEditor.extraSelections()
        if s.format.underlineStyle() == QTextCharFormat.UnderlineStyle.SpellCheckUnderline
    )
    assert spellSel.format.underlineColor() == QColor(10, 11, 12)

    searchSel = next(
        s
        for s in docEditor.extraSelections()
        if s.cursor.selectionStart() == blockPos and s.cursor.selectionEnd() == blockPos + 1
    )
    assert searchSel.format.background().color() == QColor(4, 5, 6)

    lineSel = docEditor.extraSelections()[0]
    assert lineSel.cursor.hasSelection() is False
    assert lineSel.format.background().color() == QColor(7, 8, 9)


@pytest.mark.gui
def testGuiDocEditor_Actions(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document actions. This is not an extensive test of the
    action features, just that the actions are actually called. The
    various action features are tested when their respective functions
    are tested.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(text)
    doc = docEditor.document()

    # Check that the reset colour state works (used for action errors)
    docEditor.changeFocusState(True)
    assert docEditor.docHeader.itemTitle._state == nwState.NORMAL
    docEditor.docHeader.itemTitle.setColorState(nwState.ERROR)
    docEditor.docHeader._resetColourState()
    assert docEditor.docHeader.itemTitle._state == nwState.NORMAL

    # Select/Cut/Copy/Paste/Undo/Redo
    # ===============================

    clipboard = QApplication.clipboard()
    assert clipboard is not None
    clipboard.clear()

    # Select All
    assert docEditor.docAction(nwDocAction.SEL_ALL) is True
    cursor = docEditor.textCursor()
    assert cursor.hasSelection() is True
    assert cursor.selectedText() == text.replace("\n", "\u2029")
    cursor.clearSelection()

    # Select Paragraph
    docEditor.setCursorPosition(1000)
    assert docEditor.getCursorPosition() == 1000
    assert docEditor.docAction(nwDocAction.SEL_PARA) is True
    cursor = docEditor.textCursor()
    assert cursor.selectedText() == ipsumText[1]

    # Cut Selected Text
    docEditor.replaceText(text)
    docEditor.setCursorPosition(1000)
    assert docEditor.docAction(nwDocAction.SEL_PARA) is True
    assert docEditor.docAction(nwDocAction.CUT) is True

    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    assert newPara[0] == "### A Scene"
    assert newPara[1] == ipsumText[0]
    assert newPara[2] == ipsumText[2]
    assert newPara[3] == ipsumText[3]
    assert newPara[4] == ipsumText[4]

    # Paste Back In
    assert docEditor.docAction(nwDocAction.PASTE) is True
    assert docEditor.getText() == text

    # Copy Next Paragraph
    docEditor.replaceText(text)
    docEditor.setCursorPosition(1500)
    assert docEditor.docAction(nwDocAction.SEL_PARA) is True
    assert docEditor.docAction(nwDocAction.COPY) is True

    # Paste at End
    docEditor.setCursorPosition(doc.characterCount())
    cursor = docEditor.textCursor()
    cursor.insertBlock()
    cursor.insertBlock()

    assert docEditor.docAction(nwDocAction.PASTE) is True
    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    assert newPara[5] == ipsumText[4]
    assert newPara[6] == ipsumText[2]

    clipboard.clear()

    # Emphasis/Undo/Redo
    # ==================

    text = f"### A Scene\n\n{ipsumText[0]}"
    docEditor.replaceText(text)

    # Emphasis
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.MD_ITALIC) is True
    assert docEditor.getText() == text.replace("consectetur", "_consectetur_")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.MD_ITALIC) is False

    # Strong
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.MD_BOLD) is True
    assert docEditor.getText() == text.replace("consectetur", "**consectetur**")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.MD_BOLD) is False

    # Strikeout
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.MD_STRIKE) is True
    assert docEditor.getText() == text.replace("consectetur", "~~consectetur~~")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.MD_STRIKE) is False

    # Mark
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.MD_MARK) is True
    assert docEditor.getText() == text.replace("consectetur", "==consectetur==")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.MD_MARK) is False

    # Redo
    assert docEditor.docAction(nwDocAction.REDO) is True
    assert docEditor.getText() == text.replace("consectetur", "==consectetur==")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    # Shortcodes
    # ==========

    text = f"### A Scene\n\n{ipsumText[0]}"
    docEditor.replaceText(text)

    # Italic
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_ITALIC) is True
    assert docEditor.getText() == text.replace("consectetur", "[i]consectetur[/i]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_ITALIC) is False

    # Bold
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_BOLD) is True
    assert docEditor.getText() == text.replace("consectetur", "[b]consectetur[/b]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_BOLD) is False

    # Strikethrough
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_STRIKE) is True
    assert docEditor.getText() == text.replace("consectetur", "[s]consectetur[/s]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_STRIKE) is False

    # Underline
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_ULINE) is True
    assert docEditor.getText() == text.replace("consectetur", "[u]consectetur[/u]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_ULINE) is False

    # Mark
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_MARK) is True
    assert docEditor.getText() == text.replace("consectetur", "[m]consectetur[/m]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_MARK) is False

    # Superscript
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_SUP) is True
    assert docEditor.getText() == text.replace("consectetur", "[sup]consectetur[/sup]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_SUP) is False

    # Subscript
    docEditor.setCursorPosition(46)
    assert docEditor.docAction(nwDocAction.SC_SUB) is True
    assert docEditor.getText() == text.replace("consectetur", "[sub]consectetur[/sub]")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.SC_SUB) is False

    # Quotes
    # ======

    text = f"### A Scene\n\n{ipsumText[0]}"
    docEditor.replaceText(text)

    # Add Single Quotes
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.S_QUOTE) is True
    assert docEditor.getText() == text.replace("consectetur", "\u2018consectetur\u2019")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    # Add Double Quotes
    docEditor.setCursorPosition(50)
    assert docEditor.docAction(nwDocAction.D_QUOTE) is True
    assert docEditor.getText() == text.replace("consectetur", "\u201cconsectetur\u201d")
    assert docEditor.docAction(nwDocAction.UNDO) is True
    assert docEditor.getText() == text

    # Replace Single Quotes
    repText = text.replace("consectetur", "'consectetur'")
    docEditor.replaceText(repText)
    assert docEditor.docAction(nwDocAction.SEL_ALL) is True
    assert docEditor.docAction(nwDocAction.REPL_SNG) is True
    assert docEditor.getText() == text.replace("consectetur", "\u2018consectetur\u2019")

    # Replace Double Quotes
    repText = text.replace("consectetur", '"consectetur"')
    docEditor.replaceText(repText)
    assert docEditor.docAction(nwDocAction.SEL_ALL) is True
    assert docEditor.docAction(nwDocAction.REPL_DBL) is True
    assert docEditor.getText() == text.replace("consectetur", "\u201cconsectetur\u201d")

    # Remove Line Breaks
    # ==================

    text = f"### A Scene\n\n{ipsumText[0]}"
    repText = text[:100] + text[100:].replace(" ", "\n", 3)
    docEditor.replaceText(repText)
    assert docEditor.docAction(nwDocAction.RM_BREAKS) is True
    assert docEditor.getText().strip() == text.strip()

    # Format Block
    # ============

    text = "## Scene Title\n\nScene text.\n\n"
    docEditor.replaceText(text)

    # Header 1
    docEditor.setCursorPosition(0)
    assert docEditor.docAction(nwDocAction.BLOCK_H1) is True
    assert docEditor.getText() == "# Scene Title\n\nScene text.\n\n"

    # Header 2
    docEditor.setCursorPosition(0)
    assert docEditor.docAction(nwDocAction.BLOCK_H2) is True
    assert docEditor.getText() == "## Scene Title\n\nScene text.\n\n"

    # Header 3
    docEditor.setCursorPosition(0)
    assert docEditor.docAction(nwDocAction.BLOCK_H3) is True
    assert docEditor.getText() == "### Scene Title\n\nScene text.\n\n"

    # Header 4
    docEditor.setCursorPosition(0)
    assert docEditor.docAction(nwDocAction.BLOCK_H4) is True
    assert docEditor.getText() == "#### Scene Title\n\nScene text.\n\n"

    # Comment
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.BLOCK_COM) is True
    assert docEditor.getText() == "#### Scene Title\n\n% Scene text.\n\n"

    # Ignore Text
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.BLOCK_IGN) is True
    assert docEditor.getText() == "#### Scene Title\n\n%~ Scene text.\n\n"

    # Text
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "#### Scene Title\n\nScene text.\n\n"

    # Align Left
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.ALIGN_L) is True
    assert docEditor.getText() == "#### Scene Title\n\nScene text. <<\n\n"

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.ALIGN_L) is False

    # Align Right
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.ALIGN_R) is True
    assert docEditor.getText() == "#### Scene Title\n\n>> Scene text.\n\n"

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.ALIGN_R) is False

    # Align Centre
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.ALIGN_C) is True
    assert docEditor.getText() == "#### Scene Title\n\n>> Scene text. <<\n\n"

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.ALIGN_C) is False

    # Indent Left
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.INDENT_L) is True
    assert docEditor.getText() == "#### Scene Title\n\n> Scene text.\n\n"

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.INDENT_L) is False

    # Indent Right
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.INDENT_R) is True
    assert docEditor.getText() == "#### Scene Title\n\n> Scene text. <\n\n"

    docEditor.setCursorPosition(0)  # Blocked on headings
    assert docEditor.docAction(nwDocAction.INDENT_R) is False

    # Text (Reset)
    docEditor.setCursorPosition(20)
    assert docEditor.docAction(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "#### Scene Title\n\nScene text.\n\n"

    # Invalid Actions
    # ===============

    # No Document Handle
    docEditor._docHandle = None
    assert docEditor.docAction(nwDocAction.BLOCK_TXT) is False
    docEditor._docHandle = C.hSceneDoc

    # Wrong Action Type
    assert docEditor.docAction(None) is False

    # Unknown Action
    assert docEditor.docAction(nwDocAction.NO_ACTION) is False

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_Zoom(qtbot, nwGUI, projPath, mockRnd):
    """Test zooming the editor font via docAction and Ctrl+Scroll, and
    resetting it back to the configured font size.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    basePt = docEditor.font().pointSizeF()

    # Zoom in and out via docAction (menu and shortcut path)
    assert docEditor.docAction(nwDocAction.ZOOM_IN) is True
    assert docEditor.font().pointSizeF() == basePt + 1

    assert docEditor.docAction(nwDocAction.ZOOM_OUT) is True
    assert docEditor.font().pointSizeF() == basePt

    assert docEditor.docAction(nwDocAction.ZOOM_IN) is True
    assert docEditor.docAction(nwDocAction.ZOOM_IN) is True
    assert docEditor.font().pointSizeF() == basePt + 2

    assert docEditor.docAction(nwDocAction.ZOOM_RESET) is True
    assert docEditor.font().pointSizeF() == basePt

    # Zoom in and out with Ctrl+Scroll wheel
    position = QPointF(10, 10)
    zoomInEvent = QWheelEvent(
        position,
        position,
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        QtModCtrl,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    docEditor.wheelEvent(zoomInEvent)
    assert docEditor.font().pointSizeF() == basePt + 1

    zoomOutEvent = QWheelEvent(
        position,
        position,
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.MouseButton.NoButton,
        QtModCtrl,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    docEditor.wheelEvent(zoomOutEvent)
    assert docEditor.font().pointSizeF() == basePt

    # A no-op Ctrl+Scroll (no vertical delta) does not zoom either way
    noopEvent = QWheelEvent(
        position,
        position,
        QPoint(0, 0),
        QPoint(0, 0),
        Qt.MouseButton.NoButton,
        QtModCtrl,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    docEditor.wheelEvent(noopEvent)
    assert docEditor.font().pointSizeF() == basePt

    # A regular (non-Ctrl) wheel scroll does not zoom, and instead falls
    # through to the normal scroll handling
    scrollEvent = QWheelEvent(
        position,
        position,
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.MouseButton.NoButton,
        QtModNone,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    docEditor.wheelEvent(scrollEvent)
    assert docEditor.font().pointSizeF() == basePt


@pytest.mark.gui
def testGuiDocEditor_Navigation(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test editor navigation."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor: GuiDocEditor = nwGUI.docEditor

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText[:3]))
    docEditor.replaceText(text)
    assert docEditor.textCursor().blockNumber() == 0

    steps = [
        (0, 0),  # No change
        (1, 2),  # First paragraph
        (1, 4),  # Second paragraph
        (1, 6),  # Third paragraph
        (1, 6),  # Third paragraph, end of document
        (-1, 4),  # Second paragraph
        (-1, 2),  # First paragraph
        (-1, 0),  # Title
        (-1, 0),  # First paragraph, start of document
    ]

    for step, pos in steps:
        docEditor._skipToParagraph(step)
        assert docEditor.textCursor().blockNumber() == pos


@pytest.mark.gui
def testGuiDocEditor_ToolBar(qtbot, nwGUI, projPath, mockRnd):
    """Test the document actions. This is not an extensive test of the
    action features, just that the actions are actually called. The
    various action features are tested when their respective functions
    are tested.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True

    docEditor = nwGUI.docEditor
    docToolBar = docEditor.docToolBar

    text = (
        "### A Scene\n\n"
        "Text bold one\n\n"
        "Text bold two\n\n"
        "Text italic one\n\n"
        "Text italic two\n\n"
        "Text strikethrough one\n\n"
        "Text strikethrough two\n\n"
        "Text underline one\n\n"
        "Text superscript one\n\n"
        "Text subscript one\n\n"
    )
    length = len(text)
    docEditor.replaceText(text)
    assert len(docEditor.getText()) == length

    # Show the ToolBar
    assert docToolBar.isVisible() is False
    docEditor._toggleToolBarVisibility()
    assert docToolBar.isVisible() is True

    # Markdown
    # ========

    # Click Bold
    docEditor.setCursorPosition(20)
    docToolBar.tbBoldMD.click()
    assert len(docEditor.getText()) == length + 4

    # Click Italic
    docEditor.setCursorPosition(54)
    docToolBar.tbItalicMD.click()
    assert len(docEditor.getText()) == length + 6

    # Click Strikethrough
    docEditor.setCursorPosition(90)
    docToolBar.tbStrikeMD.click()
    assert len(docEditor.getText()) == length + 10

    # Shortcodes
    # ==========

    # Click Bold
    docEditor.setCursorPosition(39)
    docToolBar.tbBold.click()
    assert len(docEditor.getText()) == length + 17

    # Click Italic
    docEditor.setCursorPosition(80)
    docToolBar.tbItalic.click()
    assert len(docEditor.getText()) == length + 24

    # Click Strikethrough
    docEditor.setCursorPosition(132)
    docToolBar.tbStrike.click()
    assert len(docEditor.getText()) == length + 31

    # Click Underline
    docEditor.setCursorPosition(163)
    docToolBar.tbUnderline.click()
    assert len(docEditor.getText()) == length + 38

    # Click Superscript
    docEditor.setCursorPosition(190)
    docToolBar.tbSuperscript.click()
    assert len(docEditor.getText()) == length + 49

    # Click Subscript
    docEditor.setCursorPosition(223)
    docToolBar.tbSubscript.click()
    assert len(docEditor.getText()) == length + 60

    # Check Result
    assert docEditor.getText() == (
        "### A Scene\n\n"
        "Text **bold** one\n\n"
        "Text [b]bold[/b] two\n\n"
        "Text _italic_ one\n\n"
        "Text [i]italic[/i] two\n\n"
        "Text ~~strikethrough~~ one\n\n"
        "Text [s]strikethrough[/s] two\n\n"
        "Text [u]underline[/u] one\n\n"
        "Text [sup]superscript[/sup] one\n\n"
        "Text [sub]subscript[/sub] one\n\n"
    )

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_Insert(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document insert functions."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    text = f"### A Scene\n\n{ipsumText[0]}"

    # Insert Text
    # ===========

    # No Document Handle
    docEditor.replaceText(text)
    docEditor._docHandle = None
    docEditor.setCursorPosition(24)
    docEditor.insertText("Stuff")
    assert docEditor.getText() == text
    docEditor._docHandle = C.hSceneDoc

    # Insert String
    docEditor.replaceText(text)
    docEditor.setCursorPosition(24)
    docEditor.insertText(", ipsumer,")
    assert docEditor.getText() == text[:24] + ", ipsumer," + text[24:]

    # Single Quotes
    docEditor.replaceText(text)
    docEditor.setCursorPosition(41)
    docEditor.insertText(nwDocInsert.QUOTE_LS)
    docEditor.setCursorPosition(53)
    docEditor.insertText(nwDocInsert.QUOTE_RS)
    assert docEditor.getText() == text.replace("consectetur", "\u2018consectetur\u2019")

    # Double Quotes
    docEditor.replaceText(text)
    docEditor.setCursorPosition(41)
    docEditor.insertText(nwDocInsert.QUOTE_LD)
    docEditor.setCursorPosition(53)
    docEditor.insertText(nwDocInsert.QUOTE_RD)
    assert docEditor.getText() == text.replace("consectetur", "\u201cconsectetur\u201d")

    # Invalid Inserts
    docEditor.replaceText(text)
    docEditor.insertText(nwDocInsert.NO_INSERT)
    assert docEditor.getText() == text
    docEditor.insertText(123)
    assert docEditor.getText() == text

    # Insert Comments
    # ===============

    docEditor.replaceText(text)
    count = docEditor.document().characterCount()

    # Invalid Position
    docEditor.setCursorPosition(12)
    docEditor.insertText(nwDocInsert.FOOTNOTE)
    assert docEditor.getText() == text

    # Valid Position
    docEditor.setCursorPosition(count)
    docEditor.insertText(nwDocInsert.FOOTNOTE)
    assert "[footnote:" in docEditor.getText()
    assert "%Footnote." in docEditor.getText()
    assert docEditor.getCursorPosition() > count

    # No document open: nothing is inserted
    textBefore = docEditor.getText()
    docHandle = docEditor._docHandle
    docEditor._docHandle = None
    docEditor._insertCommentStructure(nwComment.FOOTNOTE)
    assert docEditor.getText() == textBefore
    docEditor._docHandle = docHandle

    # Not a footnote comment: nothing is inserted
    docEditor._insertCommentStructure(nwComment.SYNOPSIS)
    assert docEditor.getText() == textBefore

    # Insert KeyWords
    # ===============

    text = f"### A Scene\n\n\n{ipsumText[0]}"
    docEditor.replaceText(text)
    docEditor.setCursorLine(3)

    # Invalid Keyword
    docEditor.insertKeyWord("stuff")
    assert docEditor.getText() == text

    # Invalid Block
    with monkeypatch.context() as mp:
        mp.setattr(QTextBlock, "isValid", lambda *a, **k: False)
        docEditor.insertKeyWord(nwKeyWords.POV_KEY)
        assert docEditor.getText() == text

    # Valid Keyword
    docEditor.insertKeyWord(nwKeyWords.POV_KEY)
    docEditor.insertText("Jane\n")
    assert docEditor.getText() == text.replace("\n\n\n", "\n\n@pov: Jane\n\n", 1)

    # Insert In-Block
    docEditor.setCursorPosition(20)
    docEditor.insertKeyWord(nwKeyWords.CHAR_KEY)
    docEditor.insertText("John")
    assert docEditor.getText() == text.replace("\n\n\n", "\n\n@pov: Jane\n@char: John\n\n", 1)

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_TextManipulation(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test the text manipulation functions."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(text)

    # Wrap Selection
    # ==============

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText[0:2]))
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)

    # Wrap Equal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._wrapSelection("=")
    assert docEditor.getText() == text.replace("consectetur", "=consectetur=")

    # Wrap Unequal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._wrapSelection("=", "*")
    assert docEditor.getText() == text.replace("consectetur", "=consectetur*")

    # Past Paragraph
    docEditor.replaceText(text)
    cursor = docEditor.textCursor()
    cursor.setPosition(13, QtMoveAnchor)
    cursor.setPosition(1000, QtKeepAnchor)
    docEditor.setTextCursor(cursor)
    docEditor._wrapSelection("=")

    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    assert newPara[1] == "=" + ipsumText[0] + "="
    assert newPara[2] == ipsumText[1]

    # Toggle Format
    # =============

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText[0:2]))

    # Block format repetition
    docEditor.replaceText(text)
    docEditor.setCursorPosition(39)
    docEditor._toggleFormat(1, "=")
    assert docEditor.getText() == text.replace("amet", "=amet=", 1)
    docEditor._toggleFormat(1, "=")
    assert docEditor.getText() == text.replace("amet", "=amet=", 1)

    # Wrap Single Equal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._toggleFormat(1, "=")
    assert docEditor.getText() == text.replace("consectetur", "=consectetur=")

    # Past Paragraph
    docEditor.replaceText(text)
    cursor = docEditor.textCursor()
    cursor.setPosition(13, QtMoveAnchor)
    cursor.setPosition(1000, QtKeepAnchor)
    docEditor.setTextCursor(cursor)
    docEditor._toggleFormat(1, "=")

    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    assert newPara[1] == "=" + ipsumText[0] + "="
    assert newPara[2] == ipsumText[1]

    # Wrap Double Equal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._toggleFormat(2, "=")
    assert docEditor.getText() == text.replace("consectetur", "==consectetur==")

    # Toggle Double Equal with Selection
    docEditor.replaceText(text)
    docEditor.setCursorSelection(41, 11)
    docEditor._toggleFormat(2, "=")
    assert docEditor.getText() == text.replace("consectetur", "==consectetur==")
    assert docEditor.getSelectedText() == "consectetur"
    docEditor._toggleFormat(2, "=")
    assert docEditor.getText() == text
    assert docEditor.getSelectedText() == "consectetur"

    # Toggle Double Equal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._toggleFormat(2, "=")
    docEditor._toggleFormat(2, "=")
    assert docEditor.getText() == text

    # Toggle Triple+Double Equal
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._toggleFormat(3, "=")
    docEditor._toggleFormat(2, "=")
    assert docEditor.getText() == text.replace("consectetur", "=consectetur=")

    # Toggle Unequal
    repText = text.replace("consectetur", "=consectetur==")
    docEditor.replaceText(repText)
    docEditor.setCursorPosition(45)
    docEditor._toggleFormat(1, "=")
    assert docEditor.getText() == text.replace("consectetur", "consectetur=")
    docEditor._toggleFormat(1, "=")
    assert docEditor.getText() == repText

    # Replace Quotes
    # ==============

    # No Selection
    text = "### A Scene\n\n{0}".format(ipsumText[0].replace("consectetur", "=consectetur="))
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._replaceQuotes("=", "<", ">")
    assert docEditor.getText() == text

    # First Paragraph Selected
    # This should not replace anything in second paragraph
    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText[0:2]).replace("ipsum", "=ipsum="))
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    assert docEditor.docAction(nwDocAction.SEL_PARA)
    docEditor._replaceQuotes("=", "<", ">")

    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    assert newPara[1] == ipsumText[0].replace("ipsum", "<ipsum>")
    assert newPara[2] == ipsumText[1].replace("ipsum", "=ipsum=")

    # Edge of Document
    text = ipsumText[0].replace("Lorem", "=Lorem=")
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    assert docEditor.docAction(nwDocAction.SEL_ALL)
    docEditor._replaceQuotes("=", "<", ">")
    assert docEditor.getText() == text.replace("=Lorem=", "<Lorem>")

    # Remove Line Breaks
    # ==================

    parOne = ipsumText[0].replace(" ", "\n", 5)
    parTwo = ipsumText[1].replace(" ", "\n", 5)

    # Check Blocks
    cursor = docEditor.textCursor()
    cursor.clearSelection()
    text = f"### A Scene\n\n{parOne}\n\n{parTwo}"
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    assert len(docEditor._selectedBlocks(cursor)) == 0

    cursor.select(QtSelectDocument)
    assert len(docEditor._selectedBlocks(cursor)) == 15

    # Remove All
    text = f"### A Scene\n\n{parOne}\n\n{parTwo}"
    docEditor.replaceText(text)
    docEditor.setCursorPosition(45)
    docEditor._removeInParLineBreaks()
    assert docEditor.getText() == "### A Scene\n\n{0}\n".format("\n\n".join(ipsumText[0:2]))

    # Remove in First Paragraph
    # Second paragraphs should remain unchanged
    text = f"### A Scene\n\n{parOne}\n\n{parTwo}"
    docEditor.replaceText(text)
    cursor = docEditor.textCursor()
    cursor.setPosition(16, QtMoveAnchor)
    cursor.setPosition(680, QtKeepAnchor)
    docEditor.setTextCursor(cursor)
    docEditor._removeInParLineBreaks()

    newText = docEditor.getText()
    newPara = list(filter(str.strip, newText.split("\n")))
    twoBits = parTwo.split()
    assert newPara[1] == ipsumText[0]
    assert newPara[2] == twoBits[0]
    assert newPara[3] == twoBits[1]
    assert newPara[4] == twoBits[2]
    assert newPara[5] == twoBits[3]
    assert newPara[6] == twoBits[4]
    assert newPara[7] == " ".join(twoBits[5:])

    # Remove on an Empty Document
    # No blocks are selected, so there is nothing to clean up
    docEditor.replaceText("")
    docEditor._removeInParLineBreaks()
    assert docEditor.getText() == "\n"

    # Remove Ending on a Heading
    # The trailing heading isn't accumulated as paragraph text
    text = f"### A Scene\n\n{parOne}\n\n### Another Heading"
    docEditor.replaceText(text)
    docEditor.docAction(nwDocAction.SEL_ALL)
    docEditor._removeInParLineBreaks()
    assert docEditor.getText() == f"### A Scene\n\n{ipsumText[0]}\n\n### Another Heading\n"

    # Key Press Events
    # ================
    text = f"### A Scene\n\n{parOne}\n\n{parTwo}"
    docEditor.replaceText(text)
    assert docEditor.getText() == text

    # Select All
    qtbot.keyClick(docEditor, Qt.Key.Key_A, modifier=QtModCtrl, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, Qt.Key.Key_Delete, delay=KEY_DELAY)
    assert docEditor.getText() == ""

    # Undo
    qtbot.keyClick(docEditor, Qt.Key.Key_Z, modifier=QtModCtrl, delay=KEY_DELAY)
    assert docEditor.getText() == text

    # Redo
    qtbot.keyClick(docEditor, Qt.Key.Key_Y, modifier=QtModCtrl, delay=KEY_DELAY)
    assert docEditor.getText() == ""

    # Let the auto-scroll animation, if one was triggered by a cursor
    # move above, finish before the widget tree is torn down
    qtbot.wait(150)

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_BlockFormatting(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the block formatting function."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    # Invalid and Generic
    # ===================

    text = f"### A Scene\n\n{ipsumText[0]}"
    docEditor.replaceText(text)

    # Invalid Block
    docEditor.setCursorPosition(0)
    with monkeypatch.context() as mp:
        mp.setattr(QTextBlock, "isValid", lambda *a, **k: False)
        assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is False

    # Keyword
    docEditor.replaceText("@pov: Jane\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is False
    assert docEditor.getText() == "@pov: Jane\n\n"
    assert docEditor.getCursorPosition() == 5

    # Unsupported Format
    docEditor.replaceText("% Comment\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.NO_ACTION) is False

    # Block Stripping : Left Side
    # ===========================

    # Strip Comment w/Space
    docEditor.replaceText("% Comment\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Comment\n\n"
    assert docEditor.getCursorPosition() == 3

    # Strip Comment wo/Space
    docEditor.replaceText("%Comment\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Comment\n\n"
    assert docEditor.getCursorPosition() == 4

    # Strip Header 1
    docEditor.replaceText("# Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 3

    # Strip Header 2
    docEditor.replaceText("## Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 2

    # Strip Header 3
    docEditor.replaceText("### Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 1

    # Strip Header 4
    docEditor.replaceText("#### Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 0

    # Strip Novel Title
    docEditor.replaceText("#! Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 2

    # Strip Unnumbered Chapter
    docEditor.replaceText("##! Title\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 1

    # Strip Hard Scene
    docEditor.replaceText("###! Title\n\n")
    docEditor.setCursorPosition(6)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 1

    # Strip Text
    docEditor.replaceText("Generic text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Generic text\n\n"
    assert docEditor.getCursorPosition() == 5

    # Strip Left Angle Brackets : Double w/Space
    docEditor.replaceText(">> Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 2

    # Strip Left Angle Brackets : Single w/Space
    docEditor.replaceText("> Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 3

    # Strip Left Angle Brackets : Double wo/Space
    docEditor.replaceText(">>Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 3

    # Strip Left Angle Brackets : Single wo/Space
    docEditor.replaceText(">Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 4

    # Block Stripping : Right Side
    # ============================

    # Strip Right Angle Brackets : Double w/Space
    docEditor.replaceText("Some text <<\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 5

    # Strip Right Angle Brackets : Single w/Space
    docEditor.replaceText("Some text <\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 5

    # Strip Right Angle Brackets : Double wo/Space
    docEditor.replaceText("Some text<<\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 5

    # Strip Right Angle Brackets : Single wo/Space
    docEditor.replaceText("Some text<\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 5

    # Block Stripping : Both Sides
    # ============================

    docEditor.replaceText(">> Some text <<\n\n")
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"

    docEditor.replaceText(">Some text <<\n\n")
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"

    docEditor.replaceText(">Some text<\n\n")
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Some text\n\n"

    # New Formats
    # ===========

    # Comment
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_COM) is True
    assert docEditor.getText() == "% Some text\n\n"
    assert docEditor.getCursorPosition() == 7

    # Toggle Comment w/Space
    docEditor.replaceText("% Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_COM) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 3

    # Toggle Comment wo/Space
    docEditor.replaceText("%Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_COM) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 4

    # Toggle Ignore Text w/Space
    docEditor.replaceText("%~ Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_IGN) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 2

    # Toggle Ignore Text wo/Space
    docEditor.replaceText("%~Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_IGN) is True
    assert docEditor.getText() == "Some text\n\n"
    assert docEditor.getCursorPosition() == 3

    # Header 1
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_H1) is True
    assert docEditor.getText() == "# Some text\n\n"
    assert docEditor.getCursorPosition() == 7

    # Header 2
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_H2) is True
    assert docEditor.getText() == "## Some text\n\n"
    assert docEditor.getCursorPosition() == 8

    # Header 3
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_H3) is True
    assert docEditor.getText() == "### Some text\n\n"
    assert docEditor.getCursorPosition() == 9

    # Header 4
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_H4) is True
    assert docEditor.getText() == "#### Some text\n\n"
    assert docEditor.getCursorPosition() == 10

    # Novel Title
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TTL) is True
    assert docEditor.getText() == "#! Some text\n\n"
    assert docEditor.getCursorPosition() == 8

    # Unnumbered Chapter
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_UNN) is True
    assert docEditor.getText() == "##! Some text\n\n"
    assert docEditor.getCursorPosition() == 9

    # Hard Scene
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.BLOCK_HSC) is True
    assert docEditor.getText() == "###! Some text\n\n"
    assert docEditor.getCursorPosition() == 10

    # Left Indent
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.INDENT_L) is True
    assert docEditor.getText() == "> Some text\n\n"
    assert docEditor.getCursorPosition() == 7

    # Right Indent
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.INDENT_R) is True
    assert docEditor.getText() == "Some text <\n\n"
    assert docEditor.getCursorPosition() == 5

    # Right/Left Indent
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.INDENT_L) is True
    assert docEditor._formatBlock(nwDocAction.INDENT_R) is True
    assert docEditor.getText() == "> Some text <\n\n"
    assert docEditor.getCursorPosition() == 7

    # Left Align
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.ALIGN_L) is True
    assert docEditor.getText() == "Some text <<\n\n"
    assert docEditor.getCursorPosition() == 5

    # Right Align
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.ALIGN_R) is True
    assert docEditor.getText() == ">> Some text\n\n"
    assert docEditor.getCursorPosition() == 8

    # Centre Align
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.ALIGN_C) is True
    assert docEditor.getText() == ">> Some text <<\n\n"
    assert docEditor.getCursorPosition() == 8

    # Left/Right Align (Overrides)
    docEditor.replaceText("Some text\n\n")
    docEditor.setCursorPosition(5)
    assert docEditor._formatBlock(nwDocAction.ALIGN_L) is True
    assert docEditor._formatBlock(nwDocAction.ALIGN_R) is True
    assert docEditor.getText() == ">> Some text\n\n"
    assert docEditor.getCursorPosition() == 8

    # Other Checks
    # ============

    # Final Cursor Position Out of Range
    docEditor.replaceText("#### Title\n\n")
    docEditor.setCursorPosition(3)
    assert docEditor._formatBlock(nwDocAction.BLOCK_TXT) is True
    assert docEditor.getText() == "Title\n\n"
    assert docEditor.getCursorPosition() == 5

    # Third Line
    # This also needs to add a new block
    docEditor.replaceText("#### Title\n\nThe Text\n\n")
    docEditor.setCursorLine(3)
    assert docEditor._formatBlock(nwDocAction.BLOCK_COM) is True
    assert docEditor.getText() == "#### Title\n\n% The Text\n\n"

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_MultiBlockFormatting(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test the block formatting function."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    text = "### A Scene\n\n@char: Jane, John\n\n" + "\n\n".join(ipsumText) + "\n\n"
    docEditor.replaceText(text)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "Lorem",
        "",
        "Nulla",
        "",
        "Nulla",
        "",
        "Pelle",
        "",
        "Integ",
        "",
    ]

    # Toggle Comment
    cursor = docEditor.textCursor()
    cursor.setPosition(50)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, 2000)
    docEditor.setTextCursor(cursor)

    docEditor._iterFormatBlocks(nwDocAction.BLOCK_COM)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "% Lor",
        "",
        "% Nul",
        "",
        "% Nul",
        "",
        "% Pel",
        "",
        "Integ",
        "",
    ]

    # Un-toggle the second
    cursor = docEditor.textCursor()
    cursor.setPosition(800)
    docEditor.setTextCursor(cursor)

    docEditor._iterFormatBlocks(nwDocAction.BLOCK_COM)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "% Lor",
        "",
        "Nulla",
        "",
        "% Nul",
        "",
        "% Pel",
        "",
        "Integ",
        "",
    ]

    # Un-toggle all
    cursor = docEditor.textCursor()
    cursor.setPosition(50)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, 3000)
    docEditor.setTextCursor(cursor)

    docEditor._iterFormatBlocks(nwDocAction.BLOCK_COM)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "Lorem",
        "",
        "Nulla",
        "",
        "Nulla",
        "",
        "Pelle",
        "",
        "Integ",
        "",
    ]

    # Toggle Ignore Text
    cursor = docEditor.textCursor()
    cursor.setPosition(50)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, 2000)
    docEditor.setTextCursor(cursor)

    docEditor._iterFormatBlocks(nwDocAction.BLOCK_IGN)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "%~ Lo",
        "",
        "%~ Nu",
        "",
        "%~ Nu",
        "",
        "%~ Pe",
        "",
        "Integ",
        "",
    ]

    # Clear all paragraphs
    cursor = docEditor.textCursor()
    cursor.setPosition(50)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, 3000)
    docEditor.setTextCursor(cursor)

    docEditor._iterFormatBlocks(nwDocAction.BLOCK_TXT)
    assert [x[:5] for x in docEditor.getText().splitlines()] == [
        "### A",
        "",
        "@char",
        "",
        "Lorem",
        "",
        "Nulla",
        "",
        "Nulla",
        "",
        "Pelle",
        "",
        "Integ",
        "",
    ]

    # Final text should be identical to initial text
    assert docEditor.getText() == text

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_Tags(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document editor tags functionality."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    # Create Scene
    text = "### A Scene\n\n@char: Jane, John\n\n@object: Gun\n\n@:\n\n" + ipsumText[0] + "\n\n"
    docEditor.replaceText(text)

    # Create Character
    text = "### Jane Doe\n\n@tag: Jane\n\n" + ipsumText[1] + "\n\n"
    cHandle = SHARED.project.newFile("Jane Doe", C.hCharRoot)
    nwGUI.openDocument(cHandle)
    docEditor.replaceText(text)
    nwGUI.saveDocument()

    # Follow Tag
    # ==========
    nwGUI.openDocument(C.hSceneDoc)

    # Empty Block
    docEditor.setCursorLine(2)
    assert docEditor._processTag() == _TagAction.NONE

    # Not On Tag
    docEditor.setCursorLine(1)
    assert docEditor._processTag() == _TagAction.NONE

    # On Tag Keyword
    docEditor.setCursorPosition(15)
    assert docEditor._processTag() == _TagAction.NONE

    # On Known Tag, No Follow
    docEditor.setCursorPosition(22)
    assert docEditor._processTag(follow=False) == _TagAction.FOLLOW
    assert docViewer._docHandle is None

    # On Known Tag, Follow
    docEditor.setCursorPosition(22)
    position = QPointF(docEditor.cursorRect().center())
    event = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseLeft, QtMouseLeft, QtModCtrl)
    assert docViewer._docHandle is None
    docEditor.mouseReleaseEvent(event)
    assert docViewer._docHandle == cHandle
    assert nwGUI.closeViewerPanel() is True
    assert docViewer._docHandle is None

    # A mouse release without the Ctrl modifier does not follow the tag
    event = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseLeft, QtMouseLeft, QtModNone)
    docEditor.mouseReleaseEvent(event)
    assert docViewer._docHandle is None

    # On Known Tag, Follow and Edit
    assert docEditor._processTag(follow=True, edit=True) == _TagAction.FOLLOW
    assert docEditor._docHandle == cHandle

    # On Unknown Tag, Create It
    nwGUI.openDocument(C.hSceneDoc)
    assert "0000000000012" not in SHARED.project.tree
    docEditor.setCursorPosition(28)
    assert docEditor._processTag(create=True) == _TagAction.CREATE
    assert "0000000000012" in SHARED.project.tree

    # On Unknown Tag, Missing Root
    assert "0000000000013" not in SHARED.project.tree
    docEditor.setCursorPosition(42)
    assert docEditor._processTag(create=True) == _TagAction.CREATE
    oHandle = SHARED.project.tree.findRoot(nwItemClass.OBJECT)
    assert oHandle == "0000000000013"

    oItem = SHARED.project.tree["0000000000014"]
    assert oItem is not None
    assert oItem.itemParent == "0000000000013"

    docEditor.setCursorPosition(47)
    assert docEditor._processTag() == _TagAction.NONE

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_HoverCard(qtbot, nwGUI, projPath, mockRnd):
    """Test the mouse-driven reference tag hover card: the debounce
    timer is only started when the block under the cursor holds any
    meta data at all, showing the card requires the more precise
    position check inside _showHoverCard() to also resolve to a tag,
    and moving off a tag or leaving the editor entirely schedules a
    delayed hide rather than closing it outright.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    cHandle = SHARED.project.newFile("Jane Doe", C.hCharRoot)
    assert nwGUI.openDocument(cHandle) is True
    docEditor.replaceText("# Jane Doe\n\n@tag: Jane\n\n")
    nwGUI.saveDocument()

    nwGUI.openDocument(C.hSceneDoc)
    docEditor.replaceText("### A Scene\n\n@char: Jane\n\n")

    def moveTo(position: int) -> QPoint:
        docEditor.setCursorPosition(position)
        point = docEditor.cursorRect().center()
        event = QMouseEvent(
            QEvent.Type.MouseMove, QPointF(point), Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, QtModNone
        )
        docEditor.mouseMoveEvent(event)
        return point

    # Hovering over the "Jane" tag starts the debounce timer, and once
    # it fires, the card resolves and shows the tag
    moveTo(22)
    assert docEditor._timerHover.isActive() is True
    docEditor._showHoverCard()
    assert docEditor._hoverCard.isVisible() is True
    assert "Jane" in docEditor._hoverCard._label.text()

    # A position within the same block that isn't over the tag itself
    # does not resolve, so _showHoverCard() schedules a hide instead
    # of showing the card, even though the block holds meta data
    docEditor.setCursorPosition(15)
    docEditor._hoverPos = docEditor.cursorRect().center()
    docEditor._showHoverCard()
    assert docEditor._hoverCard._hideTimer.isActive() is True
    docEditor._hoverCard._hideTimer.stop()

    # Moving onto a block with no meta data at all stops the timer and
    # schedules a hide without ever re-checking the exact position
    moveTo(4)
    assert docEditor._timerHover.isActive() is False
    assert docEditor._hoverCard._hideTimer.isActive() is True
    docEditor._hoverCard._hideTimer.stop()

    # Leaving the editor entirely also schedules a delayed hide, giving
    # the mouse a chance to reach the card itself
    moveTo(22)
    docEditor.leaveEvent(QEvent(QEvent.Type.Leave))
    assert docEditor._timerHover.isActive() is False
    assert docEditor._hoverCard._hideTimer.isActive() is True

    # A tag update prunes the corresponding hover card cache entry, by
    # its lower-cased key, so a stale synopsis or title cannot be shown
    # after the tag it belongs to has changed
    docEditor._hoverCard._cache["jane"] = "<p>Stale</p>"
    docEditor._hoverCard._tag = "jane"
    docEditor.updateChangedTags(["jane"], [])
    assert "jane" not in docEditor._hoverCard._cache
    assert docEditor._hoverCard._tag == ""

    # No updated or deleted tags is a no-op
    docEditor._hoverCard._cache["jane"] = "<p>Cached</p>"
    docEditor.updateChangedTags([], [])
    assert docEditor._hoverCard._cache == {"jane": "<p>Cached</p>"}


@pytest.mark.gui
def testGuiDocEditor_ProcessTagEdgeCases(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test defensive branches in tag processing not covered by the
    main tags test: an exhausted tag search, a cursor past the last
    tag's end, a missing document handle, and a declined note-creation
    prompt.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    docEditor.replaceText("### A Scene\n\n@char: Jane\n\n")

    docEditor.setCursorLine(3)
    block = docEditor.textCursor().block()

    index = SHARED.project.index
    with monkeypatch.context() as mp:
        mp.setattr(type(index), "scanThis", lambda self, text: (True, ["@char", "Jane"], [2, 5]))
        mp.setattr(type(index), "checkThese", lambda self, tBits, tHandle: [True, True])

        # Cursor before any tag's start position: the search is
        # exhausted without ever finding a candidate tag.
        cursor = QTextCursor(block)
        cursor.setPosition(block.position())
        assert docEditor._processTag(cursor=cursor) == _TagAction.NONE

        # Cursor past the end of the last candidate tag: the search
        # breaks on the first candidate, but it doesn't cover the cursor.
        cursor = QTextCursor(block)
        cursor.setPosition(block.position() + 10)
        assert docEditor._processTag(cursor=cursor) == _TagAction.NONE

    # Missing document handle: nothing can be looked up
    docHandle = docEditor._docHandle
    docEditor._docHandle = None
    assert docEditor._processTag() == _TagAction.NONE
    docEditor._docHandle = docHandle

    # No document handle for the rename-emit helper either
    docEditor._docHandle = None
    docEditor._emitRenameItem(block)
    docEditor._docHandle = docHandle

    # User declines to create a new note for a genuinely unknown tag
    docEditor.setCursorPosition(docEditor.getText().find("Jane") + 1)
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        countBefore = len(SHARED.project.tree)
        result = docEditor._processTag(create=True)
        assert result & _TagAction.CREATE
        assert len(SHARED.project.tree) == countBefore


@pytest.mark.gui
def testGuiDocEditor_MoveTextToNewDocument(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the moving text to new document feature."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text, info: (text, True))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor: GuiDocEditor = nwGUI.docEditor

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText))
    docEditor.replaceText(text)

    # Move from cursor
    nHandle = "0000000000011"
    docEditor.setCursorLine(6)
    docEditor.docAction(nwDocAction.MOVE_TEXT)
    item = SHARED.project.tree[nHandle]
    assert isinstance(item, ProjectItem)
    assert item.itemName == "New Scene (1)"
    assert nwGUI.openDocument(nHandle) is True
    assert docEditor.getText() == "### New Scene (1)\n\n{0}\n".format("\n\n".join(ipsumText[2:]))

    # New from selection, with existing header
    nHandle = "0000000000012"
    docEditor.setCursorLine(5)
    sPos = docEditor.getCursorPosition()
    docEditor.insertText("### Another Scene\n\n")

    # Select new title plus next paragraph
    docEditor.setCursorLine(8)
    ePos = docEditor.getCursorPosition()
    cursor = docEditor.textCursor()
    cursor.setPosition(sPos)
    cursor.movePosition(QtMoveRight, QtKeepAnchor, ePos - sPos)
    docEditor.setTextCursor(cursor)

    # Move to new document
    docEditor.docAction(nwDocAction.MOVE_TEXT)
    item = SHARED.project.tree[nHandle]
    assert isinstance(item, ProjectItem)
    assert item.itemName == "Another Scene"
    assert nwGUI.openDocument(nHandle) is True
    assert docEditor.getText() == f"### Another Scene\n\n{ipsumText[3]}\n"

    # An empty document has no text to select, so nothing happens
    emptyHandle = SHARED.project.newFile("Empty", C.hNovelRoot)
    assert nwGUI.openDocument(emptyHandle) is True
    countBefore = len(SHARED.project.tree)
    docEditor.docAction(nwDocAction.MOVE_TEXT)
    assert len(SHARED.project.tree) == countBefore

    # Cancelling the label dialog does not create a new document
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor.docAction(nwDocAction.SEL_ALL)
    countBefore = len(SHARED.project.tree)
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLabel, "getLabel", lambda *a, text, info: (text, False))
        docEditor.docAction(nwDocAction.MOVE_TEXT)
    assert len(SHARED.project.tree) == countBefore

    # A failure to write the new document leaves no new item behind
    docEditor.docAction(nwDocAction.SEL_ALL)
    countBefore = len(SHARED.project.tree)
    with monkeypatch.context() as mp:
        mp.setattr(type(SHARED.project), "writeNewFile", lambda *a, **k: False)
        docEditor.docAction(nwDocAction.MOVE_TEXT)
    assert len(SHARED.project.tree) == countBefore + 1  # The new (empty) file is still created

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_Links(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document editor links functionality."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor
    docEditor.replaceText("### Scene\n\nFoo http://www.example.com bar.\n\n")

    docEditor.setCursorPosition(20)
    position = QPointF(docEditor.cursorRect().center())
    event = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseLeft, QtMouseLeft, QtModCtrl)

    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        docEditor.mouseReleaseEvent(event)
        assert openUrl.called is True
        assert openUrl.call_args[0][0] == QUrl("http://www.example.com")

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_FormatLink(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test formatting a link under the cursor via the edit dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    # Cancelling the dialog is a no-op, regardless of context
    docEditor.replaceText("Foo http://example.com bar.")
    docEditor.setCursorPosition(6)
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", lambda *a, text="", url="": (text, url, False))
        docEditor.docAction(nwDocAction.MD_LINK)
    assert docEditor.getText() == "Foo http://example.com bar."

    # A bare URL under the cursor is detected via TextBlockData and its
    # URL is passed to the dialog, with no link text
    captured = {}

    def fakeBareUrl(*_a, text="", url=""):
        captured["text"], captured["url"] = text, url
        return "a link", url, True

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", fakeBareUrl)
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert captured == {"text": "", "url": "http://example.com"}
    assert docEditor.getText() == "Foo [a link](http://example.com) bar."

    # An existing Markdown link under the cursor has both its text and
    # URL passed to the dialog, and the whole construct is replaced
    docEditor.replaceText("Foo [a link](http://example.com) bar.")
    docEditor.setCursorPosition(10)
    captured.clear()

    def fakeEditLink(*_a, text="", url=""):
        captured["text"], captured["url"] = text, url
        return "new text", "http://new.example.com", True

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", fakeEditLink)
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert captured == {"text": "a link", "url": "http://example.com"}
    assert docEditor.getText() == "Foo [new text](http://new.example.com) bar."

    # With no link or selection at the cursor, a new link is inserted
    docEditor.replaceText("Foo bar.")
    docEditor.setCursorPosition(4)
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", lambda *a, text="", url="": ("site", "http://site.com", True))
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert docEditor.getText() == "Foo [site](http://site.com)bar."

    # A selection with no identified link pre-fills the link text
    docEditor.replaceText("Foo bar baz.")
    cursor = docEditor.textCursor()
    cursor.setPosition(4)
    cursor.setPosition(7, QtKeepAnchor)
    docEditor.setTextCursor(cursor)
    captured.clear()
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", fakeEditLink)
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert captured == {"text": "bar", "url": ""}
    assert docEditor.getText() == "Foo [new text](http://new.example.com) baz."

    # A blank URL from the dialog is a no-op
    docEditor.replaceText("Foo bar.")
    docEditor.setCursorPosition(4)
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", lambda *a, text="", url="": ("text", "", True))
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert docEditor.getText() == "Foo bar."

    # With more than one identified URL in the block, the one matching
    # the cursor position is picked, not just the first one
    docEditor.replaceText("Foo http://one.com and http://two.com bar.")
    docEditor.setCursorPosition(30)
    captured.clear()
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", fakeBareUrl)
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert captured == {"text": "", "url": "http://two.com"}

    # An empty block has no TextBlockData at all, which must not be
    # mistaken for an identified link
    docEditor.replaceText("")
    docEditor.setCursorPosition(0)
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "getLink", lambda *a, text="", url="": ("site", "http://site.com", True))
        assert docEditor.docAction(nwDocAction.MD_LINK) is True
    assert docEditor.getText() == "[site](http://site.com)"

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_InternalSlotEdgeCases(qtbot, nwGUI, projPath, mockRnd):
    """Test defensive branches in a few internal slots and functions
    that aren't covered by their respective feature tests.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    docEditor.replaceText("### A Scene\n\nSome text.\n\n")

    # A content change at an invalid document position is ignored
    docEditor._docChange(-1, 0, 1)

    # With line highlighting off, the cursor moved slot doesn't set up an extra selection
    CONFIG.lineHighlight = False
    docEditor._cursorMoved()

    # Mime data insertion with no source, or a source with no text, is a no-op
    text = docEditor.getText()
    docEditor.insertFromMimeData(None)
    assert docEditor.getText() == text

    emptyMime = QMimeData()
    docEditor.insertFromMimeData(emptyMime)
    assert docEditor.getText() == text

    # With auto-select disabled, or with an existing selection, the
    # cursor is returned unchanged
    docEditor.setPlainText("hello world")
    docEditor.setCursorPosition(2)

    CONFIG.autoSelect = False
    assert docEditor._autoSelect().hasSelection() is False

    CONFIG.autoSelect = True
    docEditor.docAction(nwDocAction.SEL_ALL)
    assert docEditor._autoSelect().selectedText() == "hello world"

    # A word that is the entire (and only) block, with the cursor at
    # its start, exhausts both the backward and forward scans
    docEditor.setPlainText("hello")
    docEditor.setCursorPosition(0)
    cursor = docEditor._autoSelect()
    assert cursor.selectedText() != ""

    # Copying a selection must only put plain text on the clipboard,
    # not also HTML, regardless of the widget's rich text rendering
    docEditor.setPlainText("first\n\nsecond")
    docEditor.docAction(nwDocAction.SEL_ALL)
    mime = docEditor.createMimeDataFromSelection()
    assert mime.hasHtml() is False
    assert mime.text() == "first\n\nsecond"


@pytest.mark.gui
def testGuiDocEditor_UpdateDocMargins(qtbot, nwGUI, projPath, mockRnd):
    """Test that the margins collapse to the viewport padding when no
    fixed text width or Focus Mode is in effect.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    CONFIG.textWidth = 0
    SHARED.setFocusMode(False)
    docEditor.updateDocMargins()


@pytest.mark.gui
def testGuiDocEditor_ScrollPastEnd(qtbot, nwGUI, projPath, mockRnd):
    """Test the scroll-past-end feature, which fakes QPlainTextEdit's
    centerOnScroll via a bottom margin on the document's root frame.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor
    docEditor.resize(400, 300)

    rootFrame = docEditor.document().rootFrame()

    CONFIG.scrollPastEnd = True
    docEditor.updateDocMargins()
    assert rootFrame.frameFormat().bottomMargin() > 0
    maxWithScrollPastEnd = docEditor.verticalScrollBar().maximum()

    CONFIG.scrollPastEnd = False
    docEditor.updateDocMargins()
    assert rootFrame.frameFormat().bottomMargin() == 0
    assert docEditor.verticalScrollBar().maximum() < maxWithScrollPastEnd


@pytest.mark.gui
def testGuiDocEditor_TypewriterScrolling(qtbot, nwGUI, projPath, mockRnd):
    """Test the typewriter scrolling (auto-scroll) feature, which
    animates the scrollbar by the actual pixel movement of the cursor.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor
    docEditor.resize(400, 300)

    docEditor.setPlainText("Text\n\n" * 100)
    cursor = docEditor.textCursor()
    cursor.setPosition(0)
    docEditor.setTextCursor(cursor)
    docEditor.verticalScrollBar().setValue(0)

    CONFIG.autoScroll = True
    CONFIG.autoScrollPos = 30

    vBar = docEditor.verticalScrollBar()
    assert vBar.value() == 0

    # Move the cursor down past the auto-scroll threshold by inserting
    # newlines, which advances the cursor without hitting the MOVE_KEYS
    # exclusion used for arrow-key navigation
    for _ in range(30):
        qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    qtbot.wait(200)  # Let the scroll animation finish
    assert vBar.value() > 0


@pytest.mark.gui
def testGuiDocEditor_LineHeight(qtbot, nwGUI, projPath, mockRnd):
    """Test that CONFIG.lineHeight is applied to all blocks in the
    document, both on load and when settings are refreshed.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    document = docEditor.document()

    def allBlocksHaveLineHeight(height: int) -> bool:
        block = document.firstBlock()
        while block.isValid():
            if block.blockFormat().lineHeight() != height:
                return False
            block = block.next()
        return True

    CONFIG.lineHeight = 1.50
    assert docEditor.loadText(C.hSceneDoc) is True
    assert allBlocksHaveLineHeight(150)

    CONFIG.lineHeight = 2.00
    docEditor.initEditor()
    assert allBlocksHaveLineHeight(200)


@pytest.mark.gui
def testGuiDocEditor_LineHeightPaste(qtbot, nwGUI, projPath, mockRnd):
    """Test that pasting multi-line text keeps the configured line
    height on every resulting block, including the ones created after
    a line break in the pasted text (Issue #2874).
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    document = docEditor.document()

    def allBlocksHaveLineHeight(height: int) -> bool:
        block = document.firstBlock()
        while block.isValid():
            if block.blockFormat().lineHeight() != height:
                return False
            block = block.next()
        return True

    CONFIG.lineHeight = 1.50
    assert docEditor.loadText(C.hSceneDoc) is True
    assert allBlocksHaveLineHeight(150)

    docEditor.setCursorPosition(0)
    mime = QMimeData()
    mime.setText("Pasted first line.\nPasted second line.\nPasted third line.")
    docEditor.insertFromMimeData(mime)

    assert docEditor.getText().startswith("Pasted first line.\nPasted second line.\nPasted third line.")
    assert allBlocksHaveLineHeight(150)


@pytest.mark.gui
def testGuiDocEditor_InsertFromMimeData_Markdown(qtbot, nwGUI, projPath, mockRnd):
    """Test that pasting Markdown mime data is converted to
    novelWriter's own text format before being inserted, and that a
    Markdown paste that converts to an empty string is a no-op.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor

    assert docEditor.loadText(C.hSceneDoc) is True
    docEditor.setCursorPosition(0)

    mime = QMimeData()
    mime.setData(nwConst.MIME_MARKDOWN, b"# Title\n\nSome **bold** text.\n")
    docEditor.insertFromMimeData(mime)

    assert docEditor.getText().startswith("# Title\n\nSome **bold** text.")

    text = docEditor.getText()
    emptyMd = QMimeData()
    emptyMd.setData(nwConst.MIME_MARKDOWN, b"")
    docEditor.insertFromMimeData(emptyMd)

    assert docEditor.getText() == text

    # A rich text (HTML) paste with a meaningful leading space (as a
    # non-breaking space, which is how rich text sources encode a
    # leading space that would otherwise collapse in HTML) must only
    # have the blank line added by the HTML-to-text conversion
    # stripped, not the leading space itself
    docEditor.replaceText("A cat.")
    docEditor.setCursorPosition(1)

    htmlMime = QMimeData()
    htmlMime.setHtml("<p>&nbsp;big</p>")
    docEditor.insertFromMimeData(htmlMime)

    assert docEditor.getText().startswith("A\u00a0big cat.")


@pytest.mark.gui
def testGuiDocEditor_InsertFromMimeData_Urls(qtbot, nwGUI, projPath, mockRnd):
    """Test that dropped file and web URLs are inserted as properly
    encoded URLs rather than as raw, unencoded text.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    assert docEditor.loadText(C.hSceneDoc) is True
    docEditor.setCursorPosition(0)

    # A local file path with a space, as provided by a file manager drag,
    # must be percent-encoded so that it is recognised as a single URL
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/some/path/my file.txt")])
    docEditor.insertFromMimeData(mime)
    assert docEditor.getText().startswith("file:///some/path/my%20file.txt")

    # Multiple dropped files are inserted one per line
    docEditor.replaceText("")
    docEditor.setCursorPosition(0)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/some/one.txt"), QUrl.fromLocalFile("/some/two.txt")])
    docEditor.insertFromMimeData(mime)
    assert docEditor.getText().startswith("file:///some/one.txt\nfile:///some/two.txt")

    # A regular web URL is preserved as-is
    docEditor.replaceText("")
    docEditor.setCursorPosition(0)
    mime = QMimeData()
    mime.setUrls([QUrl("https://example.com/page")])
    docEditor.insertFromMimeData(mime)
    assert docEditor.getText().startswith("https://example.com/page")


@pytest.mark.gui
def testGuiDocEditor_PasteAsPlainText(qtbot, nwGUI, projPath, mockRnd):
    """Test that the Ctrl+Shift+V shortcut always inserts the
    clipboard's plain text, ignoring any HTML or Markdown formatting
    also present on the clipboard.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    assert docEditor.loadText(C.hSceneDoc) is True
    docEditor.setCursorPosition(0)

    clipboard = QApplication.clipboard()
    assert clipboard is not None
    clipboard.clear()

    mime = QMimeData()
    mime.setHtml("<p><b>Bold</b> text.</p>")
    mime.setText("Plain text.")
    clipboard.setMimeData(mime)

    docEditor._pasteAsPlainText()

    assert docEditor.getText().startswith("Plain text.")


@pytest.mark.gui
def testGuiDocEditor_LineHeightDoubleReturn(qtbot, nwGUI, projPath, mockRnd):
    """Test that a blank-line paragraph break (two consecutive Return
    presses) works normally with a non-default line height set on
    every block. Qt's own Return handling otherwise treats the second
    Return, landing on an empty block whose format isn't bare default,
    as a request to reset the block back to default formatting instead
    of inserting a new one (meant for escaping list/heading formatting
    in rich-text editors), silently eating the keypress.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor

    CONFIG.lineHeight = 1.50
    assert docEditor.loadText(C.hSceneDoc) is True

    qtbot.keyClicks(docEditor, "# Heading")
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClicks(docEditor, "Body text.")

    assert docEditor.getText().startswith("# Heading\n\nBody text.")


@pytest.mark.gui
def testGuiDocEditor_CursorVisibility(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the custom ensure cursor visible feature."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    docEditor.setPlainText("### Scene\n\n" + "".join(["Text\n\n"] * 100))
    assert docEditor.cursorIsVisible() is True

    # Scroll Down
    cursor = docEditor.textCursor()
    cursor.setPosition(605)
    docEditor.setTextCursor(cursor)
    docEditor.verticalScrollBar().setValue(0)
    assert docEditor.verticalScrollBar().value() == 0
    docEditor.ensureCursorVisible(centre=False)
    assert docEditor.verticalScrollBar().value() > 0
    assert docEditor.cursorIsVisible() is True

    # Scroll Up
    cursor = docEditor.textCursor()
    cursor.setPosition(0)
    docEditor.setTextCursor(cursor)
    docEditor.verticalScrollBar().setValue(200)
    assert docEditor.verticalScrollBar().value() > 100
    docEditor.ensureCursorVisible(centre=False)
    assert docEditor.verticalScrollBar().value() < 100
    assert docEditor.cursorIsVisible() is True

    # Centre Cursor
    viewport = docEditor.viewport()
    cursor = docEditor.textCursor()
    cursor.setPosition(300)
    docEditor.setTextCursor(cursor)
    docEditor.verticalScrollBar().setValue(0)
    docEditor.ensureCursorVisible(centre=True)
    cRect = docEditor.cursorRect()
    cCentre = (cRect.top() + cRect.bottom()) // 2
    assert abs(cCentre - viewport.height() // 2) <= 1
    assert docEditor.cursorIsVisible() is True

    # Centre Cursor, Already Visible
    # Even if the cursor is already visible but off-centre, centre=True
    # should still move it, rather than no-op like centre=False does
    vBarAfterCentre = docEditor.verticalScrollBar().value()
    docEditor.verticalScrollBar().setValue(vBarAfterCentre - 5)
    assert docEditor.cursorIsVisible() is True
    docEditor.ensureCursorVisible(centre=True)
    assert docEditor.verticalScrollBar().value() == vBarAfterCentre
    cRect = docEditor.cursorRect()
    cCentre = (cRect.top() + cRect.bottom()) // 2
    assert abs(cCentre - viewport.height() // 2) <= 1

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_ReplaceNextEdgeCases(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test defensive branches in replaceNext not covered by the main
    search test: replacing with match-case disabled, and a selection
    that doesn't match the last recorded find.
    """
    monkeypatch.setattr(GuiDocEditor, "anyFocus", lambda *a: True)

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor
    docSearch = docEditor.docSearch

    docEditor.replaceText("### Scene\n\nFoo Bar Foo\n\n")
    docEditor.beginSearch()
    docSearch.setSearchText("Foo")
    docSearch.setReplaceText("Baz")

    # With match-case disabled, the replacement text is used verbatim
    CONFIG.searchMatchCap = False
    docEditor.setCursorPosition(0)
    docEditor._lastFind = None
    docEditor.replaceNext()  # First call just finds and selects "Foo"
    docEditor.replaceNext()  # Second call performs the replacement
    assert docEditor.getText().count("Baz") == 1

    # A selection that doesn't match the last recorded find is treated
    # as a user selection, and is left untouched
    docEditor.setCursorPosition(0)
    docEditor._lastFind = None
    docEditor.replaceNext()  # Selects and records the next "Foo"
    assert docEditor.textCursor().hasSelection() is True
    textBefore = docEditor.getText()
    docEditor._lastFind = (0, 0)  # Deliberately mismatched
    docEditor.replaceNext()
    assert docEditor.getText() == textBefore


@pytest.mark.gui
def testGuiDocEditor_WordCounters(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the word counter."""
    docEditor = nwGUI.docEditor

    class MockThreadPool:
        def __init__(self):
            self._runObj = None

        def start(self, runObj, priority=0):
            self._runObj = runObj

        def runnable(self):
            return self._runObj

        def waitForDone(self, msecs=-1):
            return True

        def clear(self):
            pass

    threadPool = MockThreadPool()
    monkeypatch.setattr(QThreadPool, "globalInstance", lambda *a: threadPool)
    docEditor._timerDoc.blockSignals(True)
    docEditor._timerSel.blockSignals(True)

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.closeDocument()  # Opening the project auto-restores a document

    # Run on an empty document
    docEditor._runDocumentTasks()
    assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"
    docEditor._updateDocCounts(0, 0, 0)
    assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"

    docEditor._runSelCounter()
    assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"
    docEditor._updateSelCounts(0, 0, 0)
    assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"

    # Open a document and populate it
    assert nwGUI.openDocument(C.hSceneDoc) is True
    SHARED.project.tree[C.hSceneDoc]._wordInit = 0  # type: ignore
    SHARED.project.tree[C.hSceneDoc]._charInit = 0  # type: ignore
    SHARED.project.tree[C.hSceneDoc]._wordCount = 0  # type: ignore
    docEditor.docFooter.updateMainCount(0, False)

    text = "\n\n".join(ipsumText)
    cC, wC, pC = standardCounter(text)
    docEditor.replaceText(text)

    # Check that a busy counter is blocked
    with monkeypatch.context() as mp:
        mp.setattr(docEditor._docCounter, "_busy", True)
        docEditor._runDocumentTasks()
        assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"

    with monkeypatch.context() as mp:
        mp.setattr(docEditor._selCounter, "_busy", True)
        docEditor.docAction(nwDocAction.SEL_ALL)
        docEditor._runSelCounter()
        assert docEditor.docFooter.wordsText.text() == "Words: 0 (+0)"
        docEditor.setCursorPosition(0)

    # Opening the document already dispatched its own initial word count,
    # which must complete before the real dispatch below can proceed
    runnable = threadPool.runnable()
    assert runnable is not None
    runnable.run()
    assert docEditor._docCounter.busy is False

    # Run the full word counter
    docEditor._lastEdit = time()  # Simulate an edit since the last run
    docEditor._runDocumentTasks()
    assert docEditor._docCounter.busy is True

    # The dispatcher also guards against re-dispatch on its own, not
    # just via the busy check in the calling code
    dispatched = threadPool.runnable()
    docEditor._docCounter.count("some other text")
    assert threadPool.runnable() is dispatched

    runnable = threadPool.runnable()
    assert runnable is not None
    runnable.run()
    assert docEditor._docCounter.busy is False
    assert SHARED.project.tree[C.hSceneDoc]._charCount == cC  # type: ignore
    assert SHARED.project.tree[C.hSceneDoc]._wordCount == wC  # type: ignore
    assert SHARED.project.tree[C.hSceneDoc]._paraCount == pC  # type: ignore
    assert docEditor.docFooter.wordsText.text() == f"Words: {wC} (+{wC})"

    # While a selection is active, the main word count footer is left
    # alone since the selection counter takes precedence
    docEditor.docAction(nwDocAction.SEL_ALL)
    assert docEditor.textCursor().hasSelection() is True
    footerBefore = docEditor.docFooter.wordsText.text()
    docEditor._updateDocCounts(cC, wC + 1, pC)
    assert docEditor.docFooter.wordsText.text() == footerBefore
    docEditor.setCursorPosition(0)

    # Select all text and run the selection word counter
    docEditor.docAction(nwDocAction.SEL_ALL)
    docEditor._runSelCounter()
    assert docEditor._selCounter.busy is True

    runnable = threadPool.runnable()
    assert runnable is not None
    runnable.run()
    assert docEditor._selCounter.busy is False
    assert docEditor.docFooter.wordsText.text() == f"Selected: {wC}"

    # A repeated run with no edit since the last one is skipped entirely
    threadPool._runObj = None
    docEditor._lastEdit = time() - 100.0
    docEditor._runDocumentTasks()
    assert threadPool.runnable() is None

    # A genuine new edit makes the next run go ahead again
    docEditor._lastEdit = time()
    docEditor._runDocumentTasks()
    assert threadPool.runnable() is not None

    assert docEditor._timerDoc.isSingleShot() is True
    assert docEditor._timerSel.isSingleShot() is True

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_Search(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test the document editor search functionality."""
    monkeypatch.setattr(GuiDocEditor, "hasFocus", lambda *a: True)

    def matchesIn(source: str, pattern: str, case: bool = False, word: bool = False, regex: bool = False):
        """Compute the search hits the same way the editor's own find
        logic would, so expected results follow from the text itself
        rather than from hardcoded positions.
        """
        pat = pattern if regex else re.escape(pattern)
        if word and not regex:
            pat = rf"\b{pat}\b"
        flags = 0 if case else re.IGNORECASE
        return [(m.start(), m.end()) for m in re.finditer(pat, source, flags)]

    def setToggle(button, state: bool) -> None:
        """Click a checkable tool button until it reaches the wanted state."""
        if button.isChecked() != state:
            button.click()

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Add a couple of extra scenes to search across for the "next file" tests
    secondHandle = SHARED.project.newFile("Second Scene", C.hChapterDir)
    thirdHandle = SHARED.project.newFile("Third Scene", C.hChapterDir)
    fourthHandle = SHARED.project.newFile("Fourth Scene", C.hChapterDir)
    assert secondHandle
    assert thirdHandle
    assert fourthHandle

    secondText = "### Second Scene\n\nFirst kumquat here. Second kumquat there.\n"
    thirdText = "### Third Scene\n\nNothing special here.\n"
    fourthText = "### Fourth Scene\n\nStill nothing special.\n"
    for handle, content in ((secondHandle, secondText), (thirdHandle, thirdText), (fourthHandle, fourthText)):
        doc = SHARED.project.storage.getDocument(handle)
        doc.writeDocument(content)
        SHARED.project.index.reIndexHandle(handle)

    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor: GuiDocEditor = nwGUI.docEditor
    docSearch: GuiDocEditSearch = docEditor.docSearch

    text = "### A Scene\n\n{0}".format("\n\n".join(ipsumText[:3]))
    docEditor.replaceText(text)
    origText = docEditor.getText()

    def findAll(pattern: str, case: bool = False, word: bool = False, regex: bool = False):
        return matchesIn(docEditor.getText(), pattern, case, word, regex)

    # Select the word "est"
    anyMatches = findAll("est")
    wordMatches = findAll("est", word=True)
    assert len(wordMatches) < len(anyMatches)  # Whole word search is more restrictive

    wStart, wEnd = wordMatches[1]
    docEditor.setCursorPosition(wStart + 1)
    docEditor._makeSelection(QtSelectWord)
    cursor = docEditor.textCursor()
    assert cursor.selectedText() == "est"

    # Activate search
    nwGUI.mainMenu.aFind.activate(QAction.ActionEvent.Trigger)
    assert docSearch.isVisible()
    assert docSearch.searchText == "est"

    idx = anyMatches.index((wStart, wEnd))

    # Find next by enter key
    monkeypatch.setattr(docSearch.searchBox, "hasFocus", lambda: True)
    qtbot.keyClick(docSearch.searchBox, QtKeyReturn, delay=KEY_DELAY)
    idx += 1
    assert docEditor.getCursorPosition() == anyMatches[idx][1]

    # Find next by button
    qtbot.mouseClick(docSearch.searchButton, QtMouseLeft, delay=KEY_DELAY)
    idx += 1
    assert docEditor.getCursorPosition() == anyMatches[idx][1]

    # Activate loop search
    setToggle(docSearch.tbLoop, True)
    assert CONFIG.searchLoop is True

    # Find next by menu Search > Find Next until it wraps back to the first hit
    for _ in range(len(anyMatches) - idx):
        nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == anyMatches[0][1]

    # Close search
    docSearch.tbCancel.click()
    assert docSearch.isVisible() is False
    docEditor.setCursorPosition(0)

    # Toggle search again with header button
    qtbot.mouseClick(docEditor.docHeader.searchButton, QtMouseLeft, delay=KEY_DELAY)
    docSearch.setSearchText("")
    assert docSearch.isVisible() is True

    # Search for non-existing
    docEditor.setCursorPosition(0)
    docSearch.setSearchText("abcdef")
    qtbot.mouseClick(docSearch.searchButton, QtMouseLeft, delay=KEY_DELAY)
    assert docEditor.getCursorPosition() == 0  # No result

    # Enable RegEx search
    setToggle(docSearch.tbRegEx, True)
    assert CONFIG.searchRegEx is True

    # Set invalid RegEx
    docEditor.setCursorPosition(0)
    docSearch.setSearchText(r"\bSus[")
    qtbot.mouseClick(docSearch.searchButton, QtMouseLeft, delay=KEY_DELAY)
    assert docEditor.getCursorPosition() == 0  # No result

    # Set dangerous RegEx (issue #1015)
    # If this doesn't get caught, the app will hang
    docEditor.setCursorPosition(0)
    docSearch.setSearchText(r".*")
    qtbot.mouseClick(docSearch.searchButton, QtMouseLeft, delay=KEY_DELAY)
    assert docEditor.getCursorPosition() == docEditor.getText().index("\n")  # Matches the heading line only

    # Set valid RegEx
    susMatches = findAll(r"\bSus", regex=True)
    docSearch.setSearchText(r"\bSus")
    qtbot.mouseClick(docSearch.searchButton, QtMouseLeft, delay=KEY_DELAY)
    assert docEditor.getCursorPosition() == susMatches[0][1]

    # Find next and then prev
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == susMatches[1][1]
    nwGUI.mainMenu.aFindPrev.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == susMatches[0][1]

    # Make RegEx case sensitive
    setToggle(docSearch.tbCase, True)
    assert CONFIG.searchCase is True

    # Find next/prev (one result, since only "Suspendisse" is capitalised)
    susCaseMatches = findAll(r"\bSus", regex=True, case=True)
    assert len(susCaseMatches) == 1
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == susCaseMatches[0][1]
    nwGUI.mainMenu.aFindPrev.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == susCaseMatches[0][1]
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == susCaseMatches[0][1]

    # Trigger replace. This resets the search box to the current selection, so
    # the search text must be restored afterwards.
    nwGUI.mainMenu.aReplace.activate(QAction.ActionEvent.Trigger)
    docSearch.setSearchText(r"\bSus")
    docSearch.setReplaceText("foo")

    # Disable RegEx case sensitive
    setToggle(docSearch.tbCase, False)
    assert CONFIG.searchCase is False

    # Toggle replace preserve case
    setToggle(docSearch.tbMatchCap, True)
    assert CONFIG.searchMatchCap is True

    # Replace "Sus" with "Foo" via menu, landing on the capitalised "Suspendisse"
    susCiMatches = findAll(r"\bSus", regex=True)
    assert len(susCiMatches) == 3
    docEditor.setCursorPosition(susCiMatches[1][1])
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    nwGUI.mainMenu.aReplaceNext.activate(QAction.ActionEvent.Trigger)
    replacedAt = susCiMatches[2][0]
    assert docEditor.getText()[replacedAt : replacedAt + 11] == "Foopendisse"

    # The replaced hit no longer counts as a match
    susRemaining = findAll(r"\bSus", regex=True)
    assert len(susRemaining) == len(susCiMatches) - 1

    # Find next/prev still works after the replace
    posBefore = docEditor.getCursorPosition()
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    posAfter = docEditor.getCursorPosition()
    assert posAfter in [e for _, e in susRemaining]
    assert posAfter != posBefore
    nwGUI.mainMenu.aFindPrev.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == posBefore

    # Replace "sus" with "foo" via replace button
    assert docEditor.textCursor().selectedText() == "sus"
    qtbot.mouseClick(docSearch.replaceButton, QtMouseLeft, delay=KEY_DELAY)
    susAfterButton = findAll(r"\bSus", regex=True)
    assert len(susAfterButton) == len(susRemaining) - 1

    # Revert last two replaces
    assert docEditor.docAction(nwDocAction.UNDO)
    assert docEditor.docAction(nwDocAction.UNDO)
    assert docEditor.getText() == origText

    # Disable RegEx search
    setToggle(docSearch.tbRegEx, False)
    assert CONFIG.searchRegEx is False

    # Close search and select "est" again
    docSearch.tbCancel.click()
    wordMatches = findAll("est", word=True)
    wStart, wEnd = wordMatches[0]
    docEditor.setCursorPosition(wStart + 1)
    docEditor._makeSelection(QtSelectWord)
    cursor = docEditor.textCursor()
    assert cursor.selectedText() == "est"

    # Activate search again
    nwGUI.mainMenu.aFind.activate(QAction.ActionEvent.Trigger)
    assert docSearch.isVisible()
    assert docSearch.searchText == "est"

    # Enable full word search
    setToggle(docSearch.tbWord, True)
    assert CONFIG.searchWord is True

    # Word search steps through the whole-word hits only
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == wordMatches[1][1]
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.getCursorPosition() == wordMatches[2][1]

    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "_docHandle", None)
        docEditor.setCursorPosition(len(docEditor.getText()))
        docEditor.findNext()
        assert docEditor.getCursorPosition() == wordMatches[0][1]

        docEditor.setCursorPosition(0)
        docEditor.findNext(goBack=True)
        assert docEditor.getCursorPosition() == wordMatches[-1][1]

        cursorPos = docEditor.getCursorPosition()
        docEditor.openNextFindDocument(docEditor, False)
        assert docEditor.getCursorPosition() == cursorPos

    # Enable next doc search
    setToggle(docSearch.tbProject, True)
    assert CONFIG.searchNextFile is True

    # Next match, jumping to the next document that has a hit
    secondMatches = matchesIn(secondText, "kumquat", word=True)
    docSearch.setSearchText("kumquat")
    docEditor.setCursorPosition(0)

    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == secondHandle
    assert docEditor.getCursorPosition() == secondMatches[0][1]
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == secondHandle
    assert docEditor.getCursorPosition() == secondMatches[1][1]
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == thirdHandle  # No hits here, so just moves on
    nwGUI.mainMenu.aFindPrev.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == secondHandle
    assert docEditor.getCursorPosition() == secondMatches[-1][1]

    # Next doc, no match anywhere, so it just keeps advancing one document at a time
    docSearch.setSearchText("abcdef")
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == thirdHandle
    nwGUI.mainMenu.aFindNext.activate(QAction.ActionEvent.Trigger)
    assert docEditor.docHandle == fourthHandle

    # Toggle Replace
    docEditor.beginReplace()

    # MonkeyPatch the focus cycle. We can't really test this very well, other than
    # check that the tabs aren't captured when the main editor has focus
    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "hasFocus", lambda: True)
        mp.setattr(docSearch.searchBox, "hasFocus", lambda: False)
        mp.setattr(docSearch.replaceBox, "hasFocus", lambda: False)
        assert docEditor.focusNextPrevChild(True) is False
        assert docSearch.cycleFocus() is False

    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "hasFocus", lambda: False)
        mp.setattr(docSearch.searchBox, "hasFocus", lambda: True)
        mp.setattr(docSearch.replaceBox, "hasFocus", lambda: False)
        assert docEditor.focusNextPrevChild(True) is True
        assert docSearch.cycleFocus() is True

    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "hasFocus", lambda: False)
        mp.setattr(docSearch.searchBox, "hasFocus", lambda: False)
        mp.setattr(docSearch.replaceBox, "hasFocus", lambda: True)
        assert docEditor.focusNextPrevChild(True) is True
        assert docSearch.cycleFocus() is True
        docSearch.closeSearch()
        assert docSearch.isVisible() is False
        assert docEditor.focusNextPrevChild(True) is True

    # While the completer popup is open, Tab must stay with the editor
    # even if hasFocus() is momentarily wrong, which has been observed
    # to happen on macOS right after the popup, a separate top-level
    # window, is shown
    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "hasFocus", lambda: False)
        popup = docEditor._completer.popup()
        assert popup is not None
        mp.setattr(popup, "isVisible", lambda: True)
        assert docEditor.focusNextPrevChild(True) is False

    # Replace Text
    # ============
    assert nwGUI.openDocument(C.hSceneDoc) is True

    setToggle(docSearch.tbCase, True)
    setToggle(docSearch.tbWord, False)
    setToggle(docSearch.tbRegEx, False)
    setToggle(docSearch.tbLoop, False)
    setToggle(docSearch.tbProject, False)
    docEditor.setCursorPosition(0)

    # Replace Next
    docSearch.searchBox.setText("a")
    docSearch.replaceBox.setText("A")
    aMatches = findAll("a", case=True)

    # No focus
    with monkeypatch.context() as mp:
        mp.setattr(docEditor, "anyFocus", lambda: False)
        docEditor.findNext()
        assert docEditor.textCursor().selectedText() == ""
        docEditor.replaceNext()
        assert docEditor.textCursor().selectedText() == ""

    # Search not open
    docSearch.closeSearch()
    assert docSearch.isVisible() is False
    docEditor.findNext()
    assert docSearch.isVisible() is True
    docSearch.closeSearch()
    assert docSearch.isVisible() is False
    docEditor.replaceNext()
    assert docSearch.isVisible() is True
    docEditor.toggleSearch()
    assert docSearch.isVisible() is False
    docEditor.toggleSearch()
    assert docSearch.isVisible() is True

    # Find first entry
    docEditor.replaceNext()
    assert docEditor.textCursor().selectedText() == "a"
    assert docEditor.getCursorPosition() == aMatches[0][1]

    # Treat the search as a user selection. Since "A" preserves the case of the
    # matched (lowercase) text, the replacement is a no-op character-wise, but it
    # still counts as a real replace-and-advance, landing on the next hit.
    docEditor._lastFind = None
    docEditor.replaceNext()
    assert docEditor.textCursor().selectedText() == "a"
    assert docEditor.getCursorPosition() == aMatches[1][1]

    # Iterate through the rest, each call replacing the current hit and
    # advancing to the next one
    lastIdx = 13
    for i in range(2, lastIdx + 1):
        docEditor.replaceNext()
        assert docEditor.textCursor().selectedText() == "a"
        assert docEditor.getCursorPosition() == aMatches[i][1]
    assert docEditor._lastFind == aMatches[lastIdx]

    # Search for something that doesn't exist
    docSearch.searchBox.setText("abcdef")
    docEditor._lastFind = None
    docEditor.replaceNext()
    assert docEditor.textCursor().selectedText() == ""

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocEditor_SearchAutoReplace(qtbot, nwGUI, projPath, mockRnd):
    """Test the auto-replace symbols feature of the search and replace boxes."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True

    docEditor = nwGUI.docEditor
    docSearch: GuiDocEditSearch = docEditor.docSearch

    docEditor.toggleSearch()
    assert docSearch.isVisible()

    # Auto-replace is off by default, so typed text is left untouched
    assert CONFIG.searchAuto is False
    qtbot.keyClicks(docSearch.searchBox, "Test...", delay=KEY_DELAY)
    assert docSearch.searchText == "Test..."

    qtbot.keyClicks(docSearch.replaceBox, "Test...", delay=KEY_DELAY)
    assert docSearch.replaceText == "Test..."

    docSearch.searchBox.clear()
    docSearch.replaceBox.clear()

    # Turn auto-replace on, and check that it now converts the text as it is typed
    docSearch.tbAuto.click()
    assert CONFIG.searchAuto is True
    qtbot.keyClicks(docSearch.searchBox, "Test...", delay=KEY_DELAY)
    assert docSearch.searchText == f"Test{nwUnicode.U_HELLIP}"

    qtbot.keyClicks(docSearch.replaceBox, "Test...", delay=KEY_DELAY)
    assert docSearch.replaceText == f"Test{nwUnicode.U_HELLIP}"

    docSearch.tbAuto.click()
    assert CONFIG.searchAuto is False


@pytest.mark.gui
def testGuiDocEditor_BigFixes(qtbot, nwGUI):
    """Test specific bug fixes in the editor."""
    docEditor = nwGUI.docEditor

    # Cursor rectangle should take into account viewport margins (Issues #2267 and #2517)
    vM = docEditor.viewportMargins()
    cR = docEditor.inputMethodQuery(QtImCursorRectangle)
    assert isinstance(cR, QRect)
    assert cR.left() >= vM.left()
    assert cR.top() >= vM.top()

    # This one should simply not crash, and return a plain QVariant (Issue #2622)
    cV = docEditor.inputMethodQuery(QtImCurrentSelection)
    assert isinstance(cV, QVariant)


@pytest.mark.gui
def testGuiDocEditor_Vim_EnableVimMode(qtbot, nwGUI, projPath, mockRnd):
    """Test that enabling CONFIG.vimMode activates vim behavior."""
    inputDelay = 2
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    CONFIG.vimMode = True

    def resetText():
        """Reset test text."""
        docEditor.setPlainText("Line1\nLine2\nLine3")
        return docEditor.getText()

    original_text = resetText()

    # Normal mode: hjkl should NOT change text
    for key in "hjkl":
        qtbot.keyClick(docEditor, key, delay=inputDelay)
        assert docEditor.getText() == original_text

    # Enter insert mode with "i"
    qtbot.keyClick(docEditor, "i", delay=inputDelay)
    qtbot.keyClicks(docEditor, "TEST", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)

    # Text must have changed now
    new_text = docEditor.getText()
    assert new_text != original_text
    assert "TEST" in new_text


@pytest.mark.gui
def testGuiDocEditor_Vim_StateInsertModeNoOp(qtbot, nwGUI, projPath, mockRnd):
    """Test that the vim state machine ignores command keys while in
    INSERT mode, which is a state neither the NORMAL nor VISUAL mode
    key handlers ever pass through.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)
    docEditor = nwGUI.docEditor

    vim = docEditor._vim
    vim.setMode(nwVimMode.INSERT)
    vim.pushCommandKey("d")
    assert vim.command == ""
    vim.setCommand("d")
    assert vim.command == ""


@pytest.mark.gui
def testGuiDocEditor_Vim_InsertMode(qtbot, nwGUI, projPath, mockRnd):
    """Test vim hjkl movements and insert commands (i, I, A)."""
    inputDelay = 2
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    CONFIG.vimMode = True

    def resetText():
        """Reset test text."""
        docEditor.setPlainText("Line1\nLine2\nLine3")
        return docEditor.getText()

    # Insert Mode
    # ===========

    # i: Insert before cursor
    resetText()
    qtbot.keyClick(docEditor, "i", delay=inputDelay)
    qtbot.keyClicks(docEditor, "X", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)
    assert "X" in docEditor.getText()

    # I: Insert at beginning of line
    resetText()
    qtbot.keyClick(docEditor, QtKeyEscape)
    qtbot.keyClick(docEditor, "h", delay=inputDelay)  # Move forward 1
    qtbot.keyClick(docEditor, "h", delay=inputDelay)  # Move forward 1
    qtbot.keyClick(docEditor, "I", delay=inputDelay)
    qtbot.keyClicks(docEditor, "START", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)
    lines = docEditor.getText().splitlines()
    assert lines[0].startswith("START")

    # A: Append at end of line
    resetText()
    qtbot.keyClick(docEditor, "A", delay=inputDelay)
    qtbot.keyClicks(docEditor, "END", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)
    lines = docEditor.getText().splitlines()
    assert lines[0].endswith("END")

    # o: Open new line below
    resetText()
    qtbot.keyClick(docEditor, "o", delay=inputDelay)
    qtbot.keyClicks(docEditor, "below", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)
    lines = docEditor.getText().splitlines()
    assert "below" in lines[1]  # Inserted after Line1

    # O: Open new line above
    resetText()
    qtbot.keyClick(docEditor, "O", delay=inputDelay)
    qtbot.keyClicks(docEditor, "above", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape)
    lines = docEditor.getText().splitlines()
    assert "above" in lines[0]  # Inserted before Line1

    # INSERT MODE MOTIONS
    # ===================

    # i: Insert before cursor
    resetText()
    qtbot.keyClick(docEditor, "i", delay=inputDelay)
    qtbot.keyClicks(docEditor, "TEST", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=inputDelay)
    assert "TEST" in docEditor.getText()

    # aX: Append after cursor
    resetText()
    qtbot.keyClick(docEditor, "a", delay=inputDelay)
    qtbot.keyClicks(docEditor, "X", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=inputDelay)
    assert "X" in docEditor.getText()

    # New line below
    resetText()
    qtbot.keyClick(docEditor, "o", delay=inputDelay)
    qtbot.keyClicks(docEditor, "below", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=inputDelay)
    lines = docEditor.getText().splitlines()
    assert "below" in lines[1]

    # New line above
    resetText()
    qtbot.keyClick(docEditor, "O", delay=inputDelay)
    qtbot.keyClicks(docEditor, "above", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=inputDelay)
    lines = docEditor.getText().splitlines()
    assert "above" in lines[0]


@pytest.mark.gui
def testGuiDocEditor_Vim_DeleteYankPaste(qtbot, nwGUI, projPath, mockRnd):
    """Test vim delete (dd, x), yank (yy) and paste (p, P) commands."""
    inputDelay = 2
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    CONFIG.vimMode = True

    def resetText():
        """Reset test text."""
        docEditor.setPlainText("Line1\nLine2\nLine3")
        return docEditor.getText()

    # p/P: Pasting with nothing yanked yet does nothing
    resetText()
    assert docEditor._vim.pasteFromInternal() == ""
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "p", delay=inputDelay)
    assert docEditor.getText() == "Line1\nLine2\nLine3"
    qtbot.keyClicks(docEditor, "P", delay=inputDelay)
    assert docEditor.getText() == "Line1\nLine2\nLine3"

    # dd: Delete entire line
    resetText()
    docEditor.setCursorPosition(docEditor.getText().find("Line2"))
    qtbot.keyClicks(docEditor, "dd", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line1", "Line3"]

    # x: Delete single character
    resetText()
    docEditor.setCursorPosition(0)
    qtbot.keyClicks(docEditor, "x", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines[0] == "ine1"  # 'L' deleted

    # p: Paste after current line
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClicks(docEditor, "yy", delay=inputDelay)  # Yank Line2
    qtbot.keyClicks(docEditor, "p", delay=inputDelay)  # Paste after Line2
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line1", "Line2", "Line2", "Line3"]

    # P: Paste before current line (using Line3)
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    docEditor.setCursorPosition(line2_pos)
    line3_pos = docEditor.getText().find("Line3")
    docEditor.setCursorPosition(line3_pos)
    qtbot.keyClicks(docEditor, "yy", delay=inputDelay)  # Yank Line3
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClicks(docEditor, "P", delay=inputDelay)  # Paste before Line2
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line1", "Line3", "Line2", "Line3"]

    # dw: Delete word (from Line1 up to next word boundary)
    resetText()
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClicks(docEditor, "dw", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line2", "Line3"]

    # d$: Delete line
    resetText()
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClicks(docEditor, "d$", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line2", "Line3"]

    # de: Delete word (from Line1 up to end of word boundary)
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClicks(docEditor, "de", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line1", "Line3"]

    # de: Delete word already at end of word
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    end_pos = docEditor.getText().find("Line2") + len("Line2")
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClicks(docEditor, "de", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line1", "Line2"]

    # de: Already at the very end of the document, nowhere further to delete
    docEditor.setPlainText("Line1")
    end_pos = len(docEditor.getText())
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClicks(docEditor, "de", delay=inputDelay)
    assert docEditor.getText() == "Line1"

    # db: Delete word back (from Line2 up to end of word boundary)
    resetText()
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClicks(docEditor, "w", delay=inputDelay)  # End of line1
    qtbot.keyClicks(docEditor, "db", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines == ["Line2", "Line3"]

    # yw: Yank word (yank Line1)
    resetText()
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClicks(docEditor, "yw", delay=inputDelay)
    # Move to start of Line2 and paste
    docEditor.setCursorPosition(docEditor.getText().find("Line2"))
    qtbot.keyClicks(docEditor, "p", delay=inputDelay)
    lines = list(filter(str.strip, docEditor.getText().splitlines()))
    assert lines[0] == "Line1"
    assert lines[1] == "Line2"
    assert lines[2] == "Line1"
    assert lines[3] == "Line3"


@pytest.mark.gui
def testGuiDocEditor_Vim_VisualMode(qtbot, nwGUI, projPath, mockRnd):
    """Test vim visual mode selection, yank and paste."""
    inputDelay = 2
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    CONFIG.vimMode = True

    def resetText():
        """Reset test text."""
        docEditor.setPlainText("Line1\nLine2\nLine3")
        return docEditor.getText()

    original_text = resetText()

    # Visual mode with yy
    resetText()
    docEditor.setCursorPosition(docEditor.getText().find("Line3") + 1)  # Inside Line3
    qtbot.keyClick(docEditor, "v", delay=inputDelay)
    qtbot.keyClick(docEditor, "j", delay=inputDelay)
    qtbot.keyClick(docEditor, "h", delay=inputDelay)
    qtbot.keyClick(docEditor, "k", delay=inputDelay)
    qtbot.keyClick(docEditor, "l", delay=inputDelay)
    qtbot.keyClicks(docEditor, "y", delay=inputDelay)
    qtbot.keyClick(docEditor, "p", delay=inputDelay)
    text = docEditor.getText()
    assert "Line3" in text or text.endswith("n")

    # Line-wise visual mode (V) with yank and paste
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClick(docEditor, "V", delay=inputDelay)  # Line-wise visual mode
    qtbot.keyClick(docEditor, "j", delay=inputDelay)
    qtbot.keyClick(docEditor, "h", delay=inputDelay)
    qtbot.keyClick(docEditor, "k", delay=inputDelay)
    qtbot.keyClick(docEditor, "l", delay=inputDelay)
    qtbot.keyClick(docEditor, "y", delay=inputDelay)  # Yank Line2
    qtbot.keyClick(docEditor, "j", delay=inputDelay)  # Move to Line3
    qtbot.keyClick(docEditor, "p", delay=inputDelay)  # Paste Line2 after Line3

    lines = docEditor.getText().splitlines()
    assert lines == ["Line1", "Line2", "Line3", "Line2"]

    # Visual mode with w motion
    resetText()
    docEditor.setCursorPosition(0)  # start of Line1
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "w", delay=inputDelay)  # Move by word
    cursor_pos = docEditor.textCursor().position()
    expected_pos = docEditor.getText().find("Line1") + len("Line1")
    assert cursor_pos == expected_pos

    # 0: Move to start of line
    resetText()
    line2_pos = docEditor.getText().find("Line2") + 3  # Middle of Line2
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClicks(docEditor, "0", delay=inputDelay)
    cursor_pos = docEditor.textCursor().position()

    # Start of Line2
    expected_pos = docEditor.getText().find("Line2")
    assert cursor_pos == expected_pos

    # No-op command 'a': nothing happens
    resetText()
    line3_pos = docEditor.getText().find("Line3") + 2
    docEditor.setCursorPosition(line3_pos)
    text_before = docEditor.getText()
    cursor_before = docEditor.textCursor().position()
    qtbot.keyClicks(docEditor, "a", delay=inputDelay)
    text_after = docEditor.getText()
    cursor_after = docEditor.textCursor().position()

    # Nothing should have changed
    assert text_after == text_before
    assert cursor_after == cursor_before

    resetText()
    start_pos = docEditor.getText().find("Line2") + 2  # Inside "Line2"
    docEditor.setCursorPosition(start_pos)
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "b", delay=inputDelay)
    selected = docEditor.textCursor().selectedText()

    # Should have selected from inside "Line2" back to its start
    assert selected == "Li"

    resetText()
    start_pos = docEditor.getText().find("Line1")  # Start of "Line1"
    docEditor.setCursorPosition(start_pos)
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    selected = docEditor.textCursor().selectedText()
    # Should have selected "Line1"
    assert selected == "Line1"

    docEditor.setPlainText("Line1 lineExtra Line2 Line3")
    end_pos = docEditor.getText().find("Line1") + len("Line1") - 1
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    selected = docEditor.textCursor().selectedText().strip()
    # Should have selected whitespace + "lineExtra"
    assert "lineExtra" in selected

    # At the very end of the document, there's nowhere further to extend to
    docEditor.setPlainText("Line1")
    end_pos = len(docEditor.getText())
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    assert docEditor.textCursor().position() == end_pos

    resetText()
    # Visual select all with ggVG
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)  # Go to start
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClick(docEditor, "G", delay=inputDelay)  # Extend to end of file

    # Delete selection
    qtbot.keyClick(docEditor, "d", delay=inputDelay)
    assert docEditor.getText().strip() == ""  # Everything deleted

    # Undo
    qtbot.keyClick(docEditor, "u", delay=inputDelay)
    restored_text = docEditor.getText()
    assert restored_text == original_text

    # Move back to start
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    cursor_pos = docEditor.textCursor().position()
    assert restored_text[cursor_pos] == "L"  # First char restored

    # Visual select all with Gvgg
    qtbot.keyClick(docEditor, "G", delay=inputDelay)  # End of file
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual mode
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)  # Extend select to start

    # Delete selection
    qtbot.keyClick(docEditor, "d", delay=inputDelay)
    assert docEditor.getText().strip() == ""  # Everything deleted

    # Undo
    qtbot.keyClick(docEditor, "u", delay=inputDelay)
    restored_text = docEditor.getText()
    assert restored_text == original_text

    # Move back to start
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    qtbot.keyClicks(docEditor, "g", delay=inputDelay)
    cursor_pos = docEditor.textCursor().position()
    assert restored_text[cursor_pos] == "L"  # First char restored

    # VISUAL MODE MOTIONS
    resetText()
    qtbot.keyClick(docEditor, "v", delay=inputDelay)  # Enter visual
    qtbot.keyClick(docEditor, "l", delay=inputDelay)  # Extend selection
    qtbot.keyClick(docEditor, "y", delay=inputDelay)  # Yank selection
    qtbot.keyClick(docEditor, "p", delay=inputDelay)  # Paste it
    assert "Li" in docEditor.getText()

    resetText()
    qtbot.keyClick(docEditor, "v", delay=inputDelay)
    qtbot.keyClick(docEditor, "$", delay=inputDelay)  # Extend to EOL
    qtbot.keyClick(docEditor, "d", delay=inputDelay)  # Delete
    line0 = docEditor.getText().splitlines()[0]
    assert line0.strip() == ""  # first line emptied

    # VISUAL LINE MODE MOTIONS
    resetText()
    line2_pos = docEditor.getText().find("Line2")
    docEditor.setCursorPosition(line2_pos)
    qtbot.keyClick(docEditor, "V", delay=inputDelay)  # Vline mode
    qtbot.keyClick(docEditor, "j", delay=inputDelay)  # Extend
    qtbot.keyClick(docEditor, "y", delay=inputDelay)  # Yank
    qtbot.keyClick(docEditor, "p", delay=inputDelay)  # Paste
    lines = docEditor.getText().splitlines()
    assert lines.count("Line2") > 1

    resetText()
    qtbot.keyClick(docEditor, "V", delay=inputDelay)  # Vline select
    qtbot.keyClick(docEditor, "G", delay=inputDelay)  # Extend to EOF
    qtbot.keyClick(docEditor, "d", delay=inputDelay)  # Delete all
    assert docEditor.getText().strip() == ""


@pytest.mark.gui
def testGuiDocEditor_Vim_NormalMode(qtbot, nwGUI, projPath, mockRnd):
    """Test vim NORMAL mode commands."""
    inputDelay = 2
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    CONFIG.vimMode = True

    def resetText():
        """Reset test text."""
        docEditor.setPlainText("Line1\nLine2\nLine3")
        return docEditor.getText()

    originalText = resetText()

    # NORMAL MODE: hjkl should NOT modify text
    for key in "hjkl":
        qtbot.keyClick(docEditor, key)
        assert docEditor.getText() == originalText

    # b: Move to beginning of word
    resetText()
    start_pos = docEditor.getText().find("Line2") + 2  # Inside the word
    docEditor.setCursorPosition(start_pos)
    qtbot.keyClicks(docEditor, "b", delay=inputDelay)
    cursorPos = docEditor.textCursor().position()
    expectedPos = docEditor.getText().find("Line2")  # Beginning of Line2
    assert cursorPos == expectedPos

    # e: Move to end of current word
    resetText()
    start_pos = docEditor.getText().find("Line1")  # Start of Line1
    docEditor.setCursorPosition(start_pos)
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    cursorPos = docEditor.textCursor().position()
    expectedPos = docEditor.getText().find("Line1") + len("Line1")
    assert cursorPos == expectedPos

    # e: Move to end of next word when already at end
    docEditor.setPlainText("Line1 lineExtra Line2 Line3")
    end_pos = docEditor.getText().find("Line1") + len("Line1")
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    cursorPos = docEditor.textCursor().position()
    expectedPos = docEditor.getText().find("lineExtra") + len("lineExtra")
    assert cursorPos == expectedPos

    # e: At the very end of the document, there's nowhere further to move
    docEditor.setPlainText("Line1")
    end_pos = len(docEditor.getText())
    docEditor.setCursorPosition(end_pos)
    qtbot.keyClicks(docEditor, "e", delay=inputDelay)
    assert docEditor.textCursor().position() == end_pos

    # $: Move to end of first line
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClick(docEditor, "$", delay=inputDelay)
    cursorPos = docEditor.textCursor().position()
    text = docEditor.getText().splitlines()[0]
    assert cursorPos == len(text)  # Cursor at end of first line

    # a: Move right and enter insert mode
    docEditor.setCursorPosition(0)  # Start of Line1 again
    qtbot.keyClick(docEditor, "a", delay=inputDelay)
    # Cursor should have moved one character right
    cursorPos = docEditor.textCursor().position()
    assert cursorPos == 1
    # Insert some text
    qtbot.keyClicks(docEditor, "TEST", delay=inputDelay)
    qtbot.keyClick(docEditor, QtKeyEscape, delay=inputDelay)
    newText = docEditor.getText()
    assert newText.startswith(("LTESSTine1", "LTESTine1"))

    # w: Move forward by word
    resetText()
    docEditor.setCursorPosition(0)  # Start of "Line1"
    qtbot.keyClicks(docEditor, "w", delay=inputDelay)
    cursorPos = docEditor.textCursor().position()
    # Cursor should now be at end of "Line1"
    expectedPos = docEditor.getText().find("Line1") + len("Line1")
    assert cursorPos == expectedPos

    # NORMAL MODE MOTIONS
    resetText()
    qtbot.keyClick(docEditor, "l", delay=inputDelay)  # Move right
    assert docEditor.textCursor().position() == 1

    resetText()
    qtbot.keyClick(docEditor, "0", delay=inputDelay)  # Beginning of line
    assert docEditor.textCursor().position() == 0

    resetText()
    docEditor.setCursorPosition(0)  # Start of Line1
    qtbot.keyClick(docEditor, "h", delay=inputDelay)

    # Move otherwise "$" is somehow not captured always
    qtbot.keyClick(docEditor, "l", delay=inputDelay)

    qtbot.keyClick(docEditor, "$", delay=inputDelay)  # End of line
    cursorPos = docEditor.textCursor().position()
    assert cursorPos == len("Line1")

    resetText()
    qtbot.keyClick(docEditor, "g", delay=inputDelay)
    qtbot.keyClick(docEditor, "g", delay=inputDelay)  # Top of buffer
    assert docEditor.textCursor().position() == 0

    qtbot.keyClick(docEditor, "z", delay=inputDelay)
    qtbot.keyClick(docEditor, "z", delay=inputDelay)  # Center view

    resetText()
    qtbot.keyClick(docEditor, "G", delay=inputDelay)  # Bottom of buffer
    cursorPos = docEditor.textCursor().position()
    assert cursorPos == len(docEditor.getText())


@pytest.mark.gui
def testGuiDocEditor_BigDocLifecycle(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test that loading, navigating, and refreshing a large document
    queues cursor moves and keeps the editor read-only until settled.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    docEditor = nwGUI.docEditor

    unit = "\n\n".join(ipsumText)
    reps = nwConst.BIG_DOC_LIMIT // len(unit) + 2
    text = "### Big Doc\n\n" + "\n\n".join([unit] * reps)

    docEditor.replaceText(text)
    nwGUI.saveDocument()
    nwGUI.closeDocument()

    cursPos = len(text) - 500
    item = SHARED.project.tree[C.hSceneDoc]
    assert item is not None
    item.setCursorPos(cursPos)

    # Loading queues the saved cursor position and stays read-only
    assert docEditor.loadText(C.hSceneDoc) is True
    assert docEditor._qDocument.isLayoutBusy() is True
    assert docEditor.isReadOnly() is True
    assert docEditor._queuePos == cursPos
    assert docEditor.getCursorPosition() != cursPos

    # A spell check pass is also skipped while busy
    docEditor._checkPassPos = 99
    docEditor.spellCheckDocument()
    assert docEditor._checkPassPos == 99

    with qtbot.waitSignal(docEditor._qDocument.layoutSettled, timeout=5000):
        pass

    assert docEditor._qDocument.isLayoutBusy() is False
    assert docEditor.isReadOnly() is False
    assert docEditor._queuePos is None
    assert docEditor.getCursorPosition() == cursPos

    # Moving to a line in the still-large, now settled document queues again
    targetLine = docEditor._qDocument.blockCount()
    assert targetLine > 1
    docEditor.setCursorLine(targetLine)
    assert docEditor._qDocument.isLayoutBusy() is True
    assert docEditor._queuePos is not None

    with qtbot.waitSignal(docEditor._qDocument.layoutSettled, timeout=5000):
        pass

    assert docEditor._queuePos is None
    block = docEditor._qDocument.findBlockByNumber(targetLine - 1)
    assert docEditor.getCursorPosition() == block.position()

    # Refreshing the editor, e.g. on a settings change, re-marks it busy too
    docEditor.initEditor()
    assert docEditor._qDocument.isLayoutBusy() is True
    assert docEditor.isReadOnly() is True

    with qtbot.waitSignal(docEditor._qDocument.layoutSettled, timeout=5000):
        pass

    assert docEditor._qDocument.isLayoutBusy() is False
    assert docEditor.isReadOnly() is False
