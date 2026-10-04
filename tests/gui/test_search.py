"""
novelWriter - GUI Project Search Tests
======================================

This file is a part of novelWriter
Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors

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

from time import time

import pytest

from PyQt6.QtCore import QModelIndex, QRect, Qt
from PyQt6.QtGui import QAction, QPainter, QPixmap
from PyQt6.QtWidgets import QStyleOptionViewItem

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwItemClass, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.core.projectsearch import DocSearch
from novelwriter.enum import nwChange, nwDocMode, nwView
from novelwriter.types import QtDisplayRole, QtKeyDown, QtKeyReturn, QtKeyUp

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiProjectSearch_Interaction(qtbot, nwGUI, fncPath, mockRnd, ipsumText):
    """Test running a search and interacting with the result tree via
    the keyboard, mouse and selection.
    """
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    project.storage.getDocument(C.hChapterDoc).writeDocument("## New Chapter\n\n" + ipsumText[0])
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + ipsumText[1])

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    root = QModelIndex()

    # Run a search that hits both documents
    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert model.rowCount(root) == 2

    # Pressing return while the search box has focus re-runs the search
    search.searchText.setFocus()
    qtbot.keyClick(search.searchText, QtKeyReturn)
    assert model.rowCount(root) == 2

    chapterIdx = model.index(0, 0, root)
    sceneIdx = model.index(1, 0, root)
    assert model.data(chapterIdx, QtDisplayRole) == "New Chapter"
    assert model.data(sceneIdx, QtDisplayRole) == "New Scene"

    firstResult = model.index(0, 0, chapterIdx)
    handle, start, length = model.result(firstResult)
    assert handle == C.hChapterDoc

    # Move down from the search box selects the first result
    search.searchText.setFocus()
    qtbot.keyClick(search, QtKeyDown)
    assert search.searchResult.currentIndex() == chapterIdx

    # Right does nothing special, and doesn't clear the selection
    qtbot.keyClick(search, Qt.Key.Key_Right)
    assert search.searchResult.currentIndex() == chapterIdx

    # Move up from the top result returns focus to the search box
    qtbot.keyClick(search, QtKeyUp)
    assert search.searchText.hasFocus() is True

    # Selecting a document-level row emits its handle
    search.searchResult.setCurrentIndex(chapterIdx)
    assert nwGUI.itemDetails._handle == C.hChapterDoc

    # Selecting a match row emits its document's handle
    search.searchResult.setCurrentIndex(firstResult)
    assert nwGUI.itemDetails._handle == handle

    # Other change types for the selected item are ignored by the details panel
    nwGUI.itemDetails.onProjectItemChanged(handle, nwChange.CREATE)
    assert nwGUI.itemDetails._handle == handle

    # Press return on the selected match to open it at its position
    search.searchResult.setFocus()
    with qtbot.waitSignal(search.openDocumentSelectRequest, timeout=1000) as signal:
        qtbot.keyClick(search.searchResult, QtKeyReturn)
    assert signal.args == [handle, start, length, False]

    with qtbot.waitSignal(search.openDocumentRequest, timeout=1000) as signal:
        qtbot.keyClick(search.searchResult, QtKeyReturn, Qt.KeyboardModifier.ShiftModifier)
    assert signal.args == [handle, nwDocMode.VIEW, "", True]

    assert nwGUI.docEditor.docHandle == handle

    # Double-click on a match opens it at its position
    with qtbot.waitSignal(search.openDocumentSelectRequest, timeout=1000) as signal:
        search._searchResultDoubleClicked(firstResult)
    assert signal.args == [handle, start, length, True]

    # Double-click on a document-level entry does nothing
    with qtbot.assertNotEmitted(search.openDocumentSelectRequest):
        search._searchResultDoubleClicked(chapterIdx)

    # Press return with no selection does nothing
    search.searchResult.setCurrentIndex(QModelIndex())
    search.searchResult.setFocus()
    with qtbot.assertNotEmitted(search.openDocumentSelectRequest):
        qtbot.keyClick(search.searchResult, QtKeyReturn)


@pytest.mark.gui
def testGuiProjectSearch_Options(qtbot, nwGUI, fncPath, mockRnd, ipsumText):
    """Test the case sensitive, whole word, and RegEx search options."""
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    sceneText = ipsumText[0] + "\n\n" + ipsumText[1]
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + sceneText)

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    root = QModelIndex()

    def totalCount() -> int:
        return sum(model.rowCount(model.index(i, 0, root)) for i in range(model.rowCount(root)))

    # Case Sensitive
    # The text has both "Lorem" and a lower case "lorem"
    caseSensitive = len(re.findall(r"Lorem", sceneText))
    caseInsensitive = len(re.findall(r"Lorem", sceneText, re.IGNORECASE))
    assert caseInsensitive > caseSensitive > 0

    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert totalCount() == caseInsensitive

    # A real click, rather than setChecked, also triggers a refresh of the current search
    qtbot.mouseClick(search.tbCase, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjCase is True
    assert totalCount() == caseSensitive
    qtbot.mouseClick(search.tbCase, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjCase is False

    # Whole Words
    # "Lor" only ever occurs as part of a longer word, so it has hits as a
    # substring, but none as a whole word
    search.beginSearch("Lor")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert totalCount() > 0

    qtbot.mouseClick(search.tbWord, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjWord is True
    assert totalCount() == 0
    qtbot.mouseClick(search.tbWord, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjWord is False

    # RegEx
    # As plain text, the pattern below is not found, but it is as an alternation
    search.beginSearch("(dolor|dolorem)")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert totalCount() == 0

    # The result is empty at this point, so the toggle itself has nothing to
    # refresh, and the search must be re-run explicitly
    qtbot.mouseClick(search.tbRegEx, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjRegEx is True
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    expected = len(re.findall(r"dolor|dolorem", sceneText, re.IGNORECASE))
    assert expected > 0
    assert totalCount() == expected
    qtbot.mouseClick(search.tbRegEx, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjRegEx is False


@pytest.mark.gui
def testGuiProjectSearch_AutoReplace(qtbot, nwGUI, fncPath, mockRnd):
    """Test the auto-replace symbols feature of the search box."""
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch

    # Auto-replace is off by default, so typed text is left untouched
    assert CONFIG.searchProjAuto is False
    qtbot.keyClicks(search.searchText, "Test...")
    assert search.searchText.text() == "Test..."

    search.searchText.clear()

    # Turn auto-replace on, and check that it now converts the text as it is typed
    qtbot.mouseClick(search.tbAuto, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjAuto is True
    qtbot.keyClicks(search.searchText, "Test...")
    assert search.searchText.text() == f"Test{nwUnicode.U_HELLIP}"

    qtbot.mouseClick(search.tbAuto, Qt.MouseButton.LeftButton)
    assert CONFIG.searchProjAuto is False


@pytest.mark.gui
def testGuiProjectSearch_FilterPanel(nwGUI, fncPath, mockRnd, ipsumText):
    """Test that toggling the switches in the search filter panel
    updates the underlying DocSearch filters and triggers a live
    refresh of the current search.
    """
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    project.storage.getDocument(C.hSceneDoc).writeDocument("### Lorem Heading\n\n" + ipsumText[0])

    # A Trash root is not a searchable class, and must be skipped when
    # building the list of root folder filters
    project.newRoot(nwItemClass.TRASH)

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    search.openProjectTasks()

    docSearch = search.searchObject
    switches = {k: v.switch for k, v in search.searchFilters.filterOpt._entries.items()}
    model = search._model
    root = QModelIndex()

    def totalCount() -> int:
        return sum(model.rowCount(model.index(i, 0, root)) for i in range(model.rowCount(root)))

    # There is one match in the heading, and one in the body text
    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    withHeading = totalCount()
    assert withHeading == 2

    # Excluding headings drops the heading match, but keeps the body match,
    # and toggling it back on restores the original count
    switches["text:includeHeadings"].setChecked(False)
    assert docSearch._textHeadings is False
    assert totalCount() == 1
    switches["text:includeHeadings"].setChecked(True)
    assert docSearch._textHeadings is True
    assert totalCount() == withHeading

    # Excluding novel documents drops every match, since the test project
    # has no other documents with content
    switches["docs:includeNovel"].setChecked(False)
    assert docSearch._docsNovel is False
    assert totalCount() == 0
    switches["docs:includeNovel"].setChecked(True)
    assert docSearch._docsNovel is True
    assert totalCount() == withHeading

    # Deselecting the Novel root folder switch is equivalent to skipping it
    rootSwitch = switches[f"root:{C.hNovelRoot}"]
    rootSwitch.setChecked(False)
    assert docSearch._skipRoots == [C.hNovelRoot]
    assert totalCount() == 0
    rootSwitch.setChecked(True)
    assert docSearch._skipRoots == []
    assert totalCount() == withHeading

    search.closeProjectTasks()


@pytest.mark.gui
def testGuiProjectSearch_LiveRefresh(nwGUI, fncPath, mockRnd, ipsumText):
    """Test the live per-document refresh triggered while a document is
    being edited, which keeps stale match positions from lingering.
    """
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + ipsumText[0])

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    root = QModelIndex()

    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert model.rowCount(root) == 1
    sceneIdx = model.index(0, 0, root)
    assert model.rowCount(sceneIdx) == 1

    firstEntry = model.entry(C.hSceneDoc)
    assert firstEntry is not None

    # Open the document and add another occurrence, but don't save it
    assert nwGUI.openDocument(C.hSceneDoc)
    nwGUI.docEditor.setPlainText(nwGUI.docEditor.getText() + "\n\nLorem again.")

    # An older timestamp is considered stale and is ignored
    search.textChanged(C.hSceneDoc, firstEntry[1] - 1.0)
    assert model.rowCount(sceneIdx) == 1

    # A newer timestamp triggers a re-search of the live, unsaved editor text
    search.textChanged(C.hSceneDoc, time() + 1000.0)
    sceneIdx = model.index(0, 0, root)
    assert model.rowCount(sceneIdx) == 2

    # A document that has never been searched is ignored
    search.textChanged(C.hTitlePage, time() + 1000.0)
    assert model.entry(C.hTitlePage) is None

    # A live refresh that yields no results is a no-op, leaving the stale entry
    nwGUI.docEditor.setPlainText("### New Scene\n\nNothing to see here.")
    search.textChanged(C.hSceneDoc, time() + 2000.0)
    sceneIdx = model.index(0, 0, root)
    assert model.rowCount(sceneIdx) == 2


@pytest.mark.gui
def testGuiProjectSearch_EdgeCases(nwGUI, fncPath, mockRnd, ipsumText):
    """Test empty search text, re-entrant search calls, and closing the project."""
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + ipsumText[0])

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    root = QModelIndex()

    # Refresh with no prior search does nothing
    search.refreshCurrentSearch()
    assert model.rowCount(root) == 0

    # An explicit theme update also refreshes the toolbar icons
    search.updateTheme()

    # Run a search
    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert model.rowCount(root) == 1

    # A re-entrant search call is a no-op
    search._blocked = True
    search._processSearch()
    assert model.rowCount(root) == 1
    search._blocked = False

    # An empty search text clears the result without searching
    search.searchText.setText("")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert model.rowCount(root) == 0

    # Re-run the search, then close the project, which clears the model
    search.beginSearch("Lorem")
    search.searchAction.activate(QAction.ActionEvent.Trigger)
    assert model.rowCount(root) == 1

    search.closeProjectTasks()
    assert model.rowCount(root) == 0


@pytest.mark.gui
def testGuiProjectSearch_ReentrancyGuard(nwGUI, fncPath, mockRnd, ipsumText, monkeypatch):
    """Regression test for the processSearch re-entrancy guard."""
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    project = SHARED.project
    project.storage.getDocument(C.hChapterDoc).writeDocument("## New Chapter\n\n" + ipsumText[0])
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + ipsumText[1])

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    root = QModelIndex()

    search.beginSearch("Lorem")

    realIterSearch = DocSearch.iterSearch

    def nestedIterSearch(self, project, searchText):
        for i, result in enumerate(realIterSearch(self, project, searchText)):
            if i == 0:
                # Simulate a nested invocation entering mid-iteration
                search._processSearch()
                # The nested call must see the guard held and skip its body
                assert search._blocked is True
            yield result

    monkeypatch.setattr(DocSearch, "iterSearch", nestedIterSearch)

    search._processSearch()

    # The guard is released once the outer call actually finishes
    assert search._blocked is False
    # The model reflects the completed outer search, undisturbed by the nested no-op call
    assert model.rowCount(root) == 2


@pytest.mark.gui
def testGuiProjectSearch_DelegatePaint(nwGUI, fncPath, mockRnd):
    """Test the search result delegate's paint code directly for the
    branches not exercised by normal interaction: eliding a match whose
    context overflows the available width, and a zero-length match.
    """
    mockRnd.reset()
    buildTestProject(NWProject(), fncPath)
    nwGUI.openProject(fncPath)
    item = SHARED.project.tree[C.hSceneDoc]
    assert item is not None

    nwGUI._changeView(nwView.SEARCH)
    search = nwGUI.projSearch
    model = search._model
    delegate = search._matchDelegate
    root = QModelIndex()

    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 80, 20)
    option.font = search.searchResult.font()
    pixmap = QPixmap(80, 20)

    # A match with more context than fits the available width is
    # elided on the right
    model.setResult(item, [(0, 5, "MATCH" + " and then some more trailing text", 0)], False)
    matchIdx = model.index(0, 0, model.index(0, 0, root))
    painter = QPainter(pixmap)
    delegate.paint(painter, option, matchIdx)
    painter.end()

    # A zero-length match skips the highlight fill, but still renders
    model.setResult(item, [(5, 0, "some context text", 5)], False)
    matchIdx = model.index(0, 0, model.index(0, 0, root))
    painter = QPainter(pixmap)
    delegate.paint(painter, option, matchIdx)
    painter.end()
