"""
novelWriter - Document Viewer Tests
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

from unittest.mock import MagicMock

import pytest

from PyQt6.QtCore import QEvent, QMimeData, QPointF, Qt, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QDragEnterEvent, QDragMoveEvent, QDropEvent, QMouseEvent, QTextCursor
from PyQt6.QtWidgets import QApplication, QMenu, QTextBrowser

from novelwriter import CONFIG, SHARED
from novelwriter.common import decodeMimeHandles
from novelwriter.constants import nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.enum import nwChange, nwDocAction
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.types import QtModNone, QtMouseLeft, QtMouseMiddle, QtSelectBlock, QtSelectWord

from tests.helpers import C, buildTestProject
from tests.mocked import causeException


@pytest.mark.gui
def testGuiDocViewer_OpenAndNavigate(qtbot, nwGUI, projPath, mockRnd):
    """Test opening documents in the viewer and navigating to them via
    the project tree and the header link.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    # Select a document in the project tree
    nwGUI.projView.setSelectedHandle(C.hSceneDoc)
    nwGUI.openDocument(C.hSceneDoc)

    # Can only open a document
    assert docViewer.loadText(C.hNovelRoot) is False

    # Middle-click the selected item
    index = SHARED.project.tree.model.indexFromHandle(C.hSceneDoc)
    rect = nwGUI.projView.projTree.visualRect(index)
    qtbot.mouseClick(nwGUI.projView.projTree.viewport(), QtMouseMiddle, pos=rect.center())
    assert docViewer.docHandle == C.hSceneDoc

    # Clear selection
    nwGUI.projView.projTree.clearSelection()
    assert nwGUI.projView.projTree.getSelectedHandle() is None

    # Re-select via header link
    docViewer.docHeader._processLabelLink(f"#{C.hSceneDoc}")
    assert nwGUI.projView.projTree.getSelectedHandle() == C.hSceneDoc

    # A non-hash link does nothing
    nwGUI.projView.projTree.clearSelection()
    docViewer.docHeader._processLabelLink("not-a-link")
    assert nwGUI.projView.projTree.getSelectedHandle() is None

    # Reload the text
    origText = docViewer.toPlainText()
    docViewer.setPlainText("Oops, all gone!")
    docViewer.docHeader._refreshDocument()
    assert docViewer.toPlainText() == origText

    # Open in editor
    nwGUI.closeDocument()
    assert docEditor.docHandle is None
    docViewer.docHeader._editDocument()
    assert docEditor.docHandle == docViewer.docHandle

    # With no document handle, editing does nothing
    nwGUI.closeDocument()
    assert docEditor.docHandle is None
    docViewer.docHeader._docHandle = None
    docViewer.docHeader._editDocument()
    assert docEditor.docHandle is None


@pytest.mark.gui
def testGuiDocViewer_Selection(qtbot, monkeypatch, nwGUI, projPath, mockRnd, ipsumText):
    """Test text selection and document actions in the viewer, and the
    context menu these selections feed into.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText(f"### Scene\n\n{ipsumText[0]}\n\n{ipsumText[1]}\n\n")
    nwGUI.saveDocument()
    nwGUI.viewDocument(C.hSceneDoc)

    text = docViewer.toPlainText()
    wordPos = text.index("laoreet")

    # Select word
    cursor = docViewer.textCursor()
    cursor.setPosition(wordPos)
    docViewer.setTextCursor(cursor)
    docViewer._makeSelection(QtSelectWord)

    clipboard = QApplication.clipboard()
    assert clipboard is not None
    clipboard.clear()

    # Cut (the viewer is read-only, so this just copies)
    assert docViewer.docAction(nwDocAction.CUT) is True
    assert clipboard.text() == "laoreet"
    clipboard.clear()

    # Copy
    assert docViewer.docAction(nwDocAction.COPY) is True
    assert clipboard.text() == "laoreet"
    clipboard.clear()

    # Select Paragraph
    assert docViewer.docAction(nwDocAction.SEL_PARA) is True
    cursor = docViewer.textCursor()
    assert cursor.selectedText() == ipsumText[0]
    cursor.clearSelection()
    docViewer.setTextCursor(cursor)

    # The same paragraph, selected by position instead
    docViewer._makePosSelection(QtSelectBlock, docViewer.cursorRect().center())
    cursor = docViewer.textCursor()
    assert cursor.selectedText() == ipsumText[0]
    cursor.clearSelection()
    docViewer.setTextCursor(cursor)

    # Select the very first block, which has no preceding separator
    cursor = docViewer.textCursor()
    cursor.setPosition(0)
    docViewer.setTextCursor(cursor)
    docViewer._makeSelection(QtSelectBlock)
    cursor = docViewer.textCursor()
    assert not cursor.selectedText().startswith(nwUnicode.U_PSEP)
    cursor.clearSelection()
    docViewer.setTextCursor(cursor)

    # Select All
    assert docViewer.docAction(nwDocAction.SEL_ALL) is True
    cursor = docViewer.textCursor()
    assert len(cursor.selectedText()) == len(text)

    # Other actions
    assert docViewer.docAction(nwDocAction.NO_ACTION) is False

    # Open context menu with a selection
    menuOpened = False

    def mockExec(*a):
        nonlocal menuOpened
        menuOpened = True

    cursor = docViewer.textCursor()
    cursor.setPosition(wordPos)
    docViewer.setTextCursor(cursor)
    docViewer._makeSelection(QtSelectWord)
    with monkeypatch.context() as mp:
        mp.setattr(QMenu, "exec", mockExec)
        docViewer._openContextMenu(docViewer.cursorRect().center())
        assert menuOpened

    # Open context menu with no selection
    menuOpened = False
    cursor = docViewer.textCursor()
    cursor.clearSelection()
    docViewer.setTextCursor(cursor)
    with monkeypatch.context() as mp:
        mp.setattr(QMenu, "exec", mockExec)
        docViewer._openContextMenu(docViewer.cursorRect().center())
        assert menuOpened

    # Close document
    docViewer.docHeader._closeDocument()
    assert docViewer.docHandle is None

    # Action on no document
    assert docViewer.docAction(nwDocAction.COPY) is False


@pytest.mark.gui
def testGuiDocViewer_Zoom(qtbot, nwGUI, projPath, mockRnd, ipsumText):
    """Test zooming the viewer font via docAction, and resetting it
    back to the configured font size.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText(f"### Scene\n\n{ipsumText[0]}\n\n")
    nwGUI.saveDocument()
    nwGUI.viewDocument(C.hSceneDoc)

    basePt = docViewer.font().pointSizeF()

    assert docViewer.docAction(nwDocAction.ZOOM_IN) is True
    assert docViewer.font().pointSizeF() == basePt + 1

    assert docViewer.docAction(nwDocAction.ZOOM_OUT) is True
    assert docViewer.font().pointSizeF() == basePt

    assert docViewer.docAction(nwDocAction.ZOOM_IN) is True
    assert docViewer.docAction(nwDocAction.ZOOM_IN) is True
    assert docViewer.font().pointSizeF() == basePt + 2

    assert docViewer.docAction(nwDocAction.ZOOM_RESET) is True
    assert docViewer.font().pointSizeF() == basePt


@pytest.mark.gui
def testGuiDocViewer_Links(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test clicking links in the document viewer."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    # Create a tagged character to link to
    hBob = "0000000000011"
    text = "### Scene\n\n@char: Bob\n\nSome text mentioning Bob.\n"
    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText(text)
    nwGUI.saveDocument()
    cursor = docEditor.textCursor()
    cursor.setPosition(text.index("Bob"))
    docEditor._processTag(cursor, create=True)

    nwGUI.viewDocument(C.hSceneDoc)

    # A tag link navigates to the tagged item
    docViewer._linkClicked(QUrl("#tag_bob"))
    assert docViewer.docHandle == hBob

    # Other links should just trigger a navigate call
    with qtbot.waitSignal(docViewer.sourceChanged, timeout=1000) as signal:
        docViewer._linkClicked(QUrl("#somewhere_else"))
        assert signal.args[0].url() == "#somewhere_else"

    # Web links should trigger the browser
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        docViewer._linkClicked(QUrl("http://www.example.com"))
        assert openUrl.called is True
        assert openUrl.call_args[0][0] == QUrl("http://www.example.com")

    # File links should also trigger the browser, see issue with clicking
    # a "file://" link only working in the editor, not the viewer
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        docViewer._linkClicked(QUrl("file:///tmp/note.txt"))
        assert openUrl.called is True
        assert openUrl.call_args[0][0] == QUrl("file:///tmp/note.txt")

    # An empty link does nothing
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        docViewer._linkClicked(QUrl(""))
        assert openUrl.called is False

    # An unrecognised link scheme does nothing
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        docViewer._linkClicked(QUrl("mailto:test@example.com"))
        assert openUrl.called is False


@pytest.mark.gui
def testGuiDocViewer_HoverCard(qtbot, nwGUI, projPath, mockRnd):
    """Test the mouse-driven reference tag hover card in the viewer:
    the debounce timer only starts when hovering a '#tag_' anchor,
    showing the card requires _showHoverCard() to also resolve the
    anchor into a tag, and moving off the anchor or leaving the viewer
    entirely schedules a delayed hide rather than closing it outright.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    hBob = "0000000000010"
    text = "### Scene\n\n@char: Bob\n\nSome text mentioning Bob.\n"
    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText(text)
    nwGUI.saveDocument()
    cursor = docEditor.textCursor()
    cursor.setPosition(text.index("Bob"))
    docEditor._processTag(cursor, create=True)
    assert hBob in SHARED.project.tree

    nwGUI.viewDocument(C.hSceneDoc)

    document = docViewer.document()
    assert document is not None

    def charCentre(position: int) -> QPointF:
        # The midpoint between the cursor rects on either side of the
        # character lands solidly inside its glyph, unlike a cursor
        # boundary rect's own centre, which anchorAt() may not hit-test
        # as being over the character on either side of it
        left = QTextCursor(document)
        left.setPosition(position)
        right = QTextCursor(document)
        right.setPosition(position + 1)
        leftRect = docViewer.cursorRect(left)
        rightRect = docViewer.cursorRect(right)
        return QPointF((leftRect.x() + rightRect.x()) / 2, leftRect.center().y())

    def moveTo(position: int) -> None:
        point = charCentre(position)
        event = QMouseEvent(QEvent.Type.MouseMove, point, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton, QtModNone)
        docViewer.mouseMoveEvent(event)

    plainText = docViewer.toPlainText()
    anchorPos = plainText.find("Bob")
    assert anchorPos >= 0
    plainPos = plainText.find("Some text")
    assert plainPos >= 0

    # Hovering over the tag anchor starts the debounce timer, and once
    # it fires, the card resolves and shows the tag
    moveTo(anchorPos + 1)
    assert docViewer._timerHover.isActive() is True
    docViewer._showHoverCard()
    assert docViewer._hoverCard.isVisible() is True
    assert "Bob" in docViewer._hoverCard._label.text()

    # A position with no anchor at all stops the timer and schedules a
    # hide instead of closing the card immediately. _hoverPos is only
    # ever updated on the anchor branch of mouseMoveEvent, so it must
    # be set directly here to point _showHoverCard() at the plain text.
    moveTo(plainPos + 1)
    assert docViewer._timerHover.isActive() is False
    assert docViewer._hoverCard._hideTimer.isActive() is True
    docViewer._hoverCard._hideTimer.stop()

    # _showHoverCard() re-checks the position itself, and also
    # schedules a hide if it no longer resolves to a tag anchor
    docViewer._hoverPos = charCentre(plainPos + 1).toPoint()
    docViewer._showHoverCard()
    assert docViewer._hoverCard._hideTimer.isActive() is True
    docViewer._hoverCard._hideTimer.stop()

    # Leaving the viewer entirely also schedules a delayed hide, giving
    # the mouse a chance to reach the card itself
    moveTo(anchorPos + 1)
    docViewer.leaveEvent(QEvent(QEvent.Type.Leave))
    assert docViewer._timerHover.isActive() is False
    assert docViewer._hoverCard._hideTimer.isActive() is True

    # A tag update prunes the corresponding hover card cache entry, by
    # its lower-cased key, so a stale synopsis or title cannot be shown
    # after the tag it belongs to has changed
    docViewer._hoverCard._cache["bob"] = "<p>Stale</p>"
    docViewer._hoverCard._tag = "bob"
    docViewer.updateChangedTags(["bob"], [])
    assert "bob" not in docViewer._hoverCard._cache
    assert docViewer._hoverCard._tag == ""

    # No updated or deleted tags is a no-op
    docViewer._hoverCard._cache["bob"] = "<p>Cached</p>"
    docViewer.updateChangedTags([], [])
    assert docViewer._hoverCard._cache == {"bob": "<p>Cached</p>"}

    docViewer._hoverCard.hide()


@pytest.mark.gui
def testGuiDocViewer_MouseNavigation(qtbot, nwGUI, projPath, mockRnd, ipsumText):
    """Test navigating the view history with the mouse back/forward
    buttons, including the edge cases at either end of the history.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    # Make the scene long enough to produce a visible scroll bar, so
    # that the scroll position is also exercised while navigating
    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText("### Scene\n\n" + "\n\n".join(ipsumText))
    nwGUI.saveDocument()

    nwGUI.viewDocument(C.hChapterDoc)
    assert docViewer.docHandle == C.hChapterDoc
    nwGUI.viewDocument(C.hSceneDoc)
    assert docViewer.docHandle == C.hSceneDoc
    assert docViewer.verticalScrollBar().isVisible() is True

    viewport = docViewer.viewport()
    center = viewport.rect().center()
    qtbot.mouseClick(viewport, Qt.MouseButton.BackButton, pos=center, delay=100)
    assert docViewer.docHandle == C.hChapterDoc
    qtbot.mouseClick(viewport, Qt.MouseButton.ForwardButton, pos=center, delay=100)
    assert docViewer.docHandle == C.hSceneDoc

    # A regular left-click does not trigger navigation
    qtbot.mouseClick(viewport, QtMouseLeft, pos=center, delay=100)
    assert docViewer.docHandle == C.hSceneDoc

    # Already at the newest entry, so forward does nothing
    docViewer.navForward()
    assert docViewer.docHandle == C.hSceneDoc

    # Navigate all the way back, then backward does nothing further
    docViewer.navBackward()
    assert docViewer.docHandle == C.hChapterDoc
    docViewer.navBackward()
    assert docViewer.docHandle == C.hChapterDoc

    # Return to the newest entry
    docViewer.navForward()
    assert docViewer.docHandle == C.hSceneDoc


@pytest.mark.gui
def testGuiDocViewer_ScrollAndMargins(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the scroll bar and document margin behaviour of the
    viewer, along with the navigateTo edge cases.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docViewer = nwGUI.docViewer

    nwGUI.viewDocument(C.hSceneDoc)

    # Scroll bar default on empty document
    docViewer.clear()
    assert docViewer.scrollPosition == 0
    docViewer.reloadText()

    # Flip some settings
    CONFIG.doJustify = True
    CONFIG.hideVScroll = True
    CONFIG.hideHScroll = True
    docViewer.initViewer()
    assert docViewer.verticalScrollBar().isVisible() is False
    assert docViewer.horizontalScrollBar().isVisible() is False

    # Setting the scroll position does nothing when the bar is hidden
    docViewer.setScrollPosition(10)

    # A text width of 0 disables the centred margin calculation
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "textWidth", 0)
        docViewer.updateDocMargins()

    # A non-hash anchor, or a non-string one, does nothing
    with qtbot.assertNotEmitted(docViewer.sourceChanged):
        docViewer.navigateTo("not-an-anchor")
        docViewer.navigateTo(None)  # type: ignore


@pytest.mark.gui
def testGuiDocViewer_HeaderTitle(qtbot, nwGUI, projPath, mockRnd):
    """Test the document header title breadcrumb and outline menu."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docViewer = nwGUI.docViewer

    nwGUI.viewDocument(C.hChapterDoc)

    # Change document title
    nwItem = SHARED.project.tree[C.hChapterDoc]
    nwItem.setName("Test Title")  # type: ignore
    assert nwItem.itemName == "Test Title"  # type: ignore
    docViewer.onProjectItemChanged(C.hChapterDoc, nwChange.UPDATE)
    title = docViewer.docHeader.itemTitle.text()
    assert "New Folder" in title
    assert "Test Title" in title
    assert title.index("New Folder") < title.index("Test Title")

    # Title without full path
    CONFIG.showFullPath = False
    docViewer.onProjectItemChanged(C.hChapterDoc, nwChange.UPDATE)
    title = docViewer.docHeader.itemTitle.text()
    assert "New Folder" not in title
    assert "Test Title" in title

    # An invalid handle does not update the title
    docViewer.docHeader.setHandle(C.hInvalid)
    assert docViewer.docHeader.itemTitle.text() == title
    CONFIG.showFullPath = True

    # A title entry (T0000) is excluded from the outline menu
    docViewer.docHeader._docOutline = {}
    docViewer.docHeader.setOutline({"T0000": ("Title", 1), "T0001": ("Chapter One", 1)})
    assert [a.text() for a in docViewer.docHeader.outlineMenu.actions()] == ["Chapter One"]

    # Selecting an entry from the outline menu navigates to it
    docViewer.docHeader.outlineMenu.actions()[0].trigger()

    # Non-string data is ignored
    otherAction = QAction(docViewer.docHeader)
    otherAction.setData(1)
    docViewer.docHeader._gotoHeader(otherAction)


@pytest.mark.gui
def testGuiDocViewer_FooterAndErrors(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the document footer show/hide toggles for synopsis,
    comments and notes, as well as error handling when rendering
    fails.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    nwGUI.openDocument(C.hSceneDoc)
    docEditor.setPlainText(
        "### Scene\n\n"
        "%Synopsis: A short synopsis.\n\n"
        "% A plain comment.\n\n"
        "%Note: A note about something.\n\n"
        "Some body text.\n\n"
    )
    nwGUI.saveDocument()

    nwGUI.viewDocument(C.hSceneDoc)
    fullLength = len(docViewer.toPlainText())

    with qtbot.waitSignal(docViewer.togglePanelVisibility, timeout=1000):
        docViewer.docFooter.showHide.click()

    docViewer.docFooter._doToggleSynopsis(False)
    noSynopLength = len(docViewer.toPlainText())
    assert noSynopLength < fullLength
    docViewer.docFooter._doToggleSynopsis(True)

    docViewer.docFooter._doToggleComments(False)
    noCommentLength = len(docViewer.toPlainText())
    assert noCommentLength < fullLength
    docViewer.docFooter._doToggleComments(True)

    docViewer.docFooter._doToggleNotes(False)
    noNotesLength = len(docViewer.toPlainText())
    assert noNotesLength < fullLength
    docViewer.docFooter._doToggleNotes(True)

    # Crash the HTML rendering
    with monkeypatch.context() as mp:
        mp.setattr(ToQTextDocument, "doConvert", causeException)
        assert docViewer.loadText(C.hSceneDoc) is False
        assert docViewer.toPlainText() == "An error occurred while generating the preview."

    # Call the update theme function
    # This only checks that it doesn't fail, functionality tested elsewhere
    docViewer.updateTheme()


@pytest.mark.gui
def testGuiDocViewer_DragAndDrop(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test drag and drop in the viewer."""
    docViewer = nwGUI.docViewer

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hTitlePage) is True
    assert nwGUI.viewDocument(C.hTitlePage) is True
    assert docViewer.docHandle == C.hTitlePage

    middle = docViewer.viewport().rect().center()
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
        mp.setattr(QTextBrowser, "dragEnterEvent", mockEnter)

        # Document Enter
        docViewer.dragEnterEvent(docEvent)
        assert docEvent.isAccepted() is True
        assert mockEnter.call_count == 0

        # Regular Enter
        docViewer.dragEnterEvent(noneEvent)
        assert mockEnter.call_count == 1

    # Drag Move
    mockMove = MagicMock()
    docEvent = QDragMoveEvent(middle, action, docMime, mouse, QtModNone)
    noneEvent = QDragMoveEvent(middle, action, noneMime, mouse, QtModNone)
    with monkeypatch.context() as mp:
        mp.setattr(QTextBrowser, "dragMoveEvent", mockMove)

        # Document Move
        docViewer.dragMoveEvent(docEvent)
        assert docEvent.isAccepted() is True
        assert mockMove.call_count == 0

        # Regular Move
        docViewer.dragMoveEvent(noneEvent)
        assert mockMove.call_count == 1

    # Drop
    mockDrop = MagicMock()
    middle = QPointF(docViewer.viewport().rect().center())
    docEvent = QDropEvent(middle, action, docMime, mouse, QtModNone)
    noneEvent = QDropEvent(middle, action, noneMime, mouse, QtModNone)
    with monkeypatch.context() as mp:
        mp.setattr(QTextBrowser, "dropEvent", mockDrop)

        # Document Drop
        docViewer.dropEvent(docEvent)
        assert mockDrop.call_count == 0
        assert docViewer.docHandle == C.hSceneDoc

        # Regular Move
        docViewer.dropEvent(noneEvent)
        assert mockDrop.call_count == 1

        # Dropping a folder (not a file) does nothing
        folderMime = model.mimeData([model.indexFromHandle(C.hCharRoot)])
        assert decodeMimeHandles(folderMime) == [C.hCharRoot]
        folderEvent = QDropEvent(middle, action, folderMime, mouse, QtModNone)
        docViewer.dropEvent(folderEvent)
        assert docViewer.docHandle == C.hSceneDoc
