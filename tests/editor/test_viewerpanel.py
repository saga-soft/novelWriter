"""
novelWriter - Document Viewer Panel Tests
=========================================

This file is a part of novelWriter.

Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors.

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
from PyQt6.QtGui import QIcon
from pytestqt.qtbot import QtBot

from novelwriter import SHARED
from novelwriter.constants import nwLists
from novelwriter.core.item import ProjectItem
from novelwriter.core.options import OptionState
from novelwriter.core.project import NWProject
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.enum import nwChange
from novelwriter.guimain import GuiMain
from novelwriter.types import QtDisplayRole

from tests.helpers import C, MockRnd, buildTestProject


@pytest.mark.gui
def testGuiDocViewerPanel_BackRefs(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    nwGUI: GuiMain,
    projPath: Path,
    mockRnd: MockRnd,
):
    """Test the document viewer backreference panel."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.projView.projTree.expandAll()
    viewPanel = nwGUI.docViewerPanel
    tabBackRefs = viewPanel.tabBackRefs

    nwGUI.docPanes.openDocument(C.hSceneDoc)
    nwGUI.docPanes.viewDocument(C.hSceneDoc)

    # Hide/Show
    nwGUI.docPanes._toggleViewerPanelVisibility()
    assert viewPanel.isVisible() is False
    nwGUI.docPanes._toggleViewerPanelVisibility()
    assert viewPanel.isVisible() is True

    # Initial State
    assert tabBackRefs.topLevelItemCount() == 0

    # Add Two Tags
    hJane = "0000000000011"
    nwGUI.docEditor.setPlainText("### New Scene\n\n@char: Jane, John\n\n")
    nwGUI.docPanes.saveDocument()
    cursor = nwGUI.docEditor.textCursor()
    cursor.setPosition(22)
    nwGUI.docEditor._processTag(cursor, create=True)
    cursor.setPosition(28)
    nwGUI.docEditor._processTag(cursor, create=True)
    nwGUI.docPanes.viewDocument(hJane)
    assert tabBackRefs.topLevelItemCount() == 1

    # Check Backreference
    item = tabBackRefs.topLevelItem(0)
    assert item is not None
    assert item.text(tabBackRefs.C_DOC) == "New Scene"
    assert item.text(tabBackRefs.C_TITLE) == "New Scene"

    # Update Title
    nwGUI.docEditor.setPlainText("### Scene One\n\n@char: Jane, John\n\n")
    nwGUI.docPanes.saveDocument()
    item = tabBackRefs.topLevelItem(0)
    assert item is not None
    assert item.text(tabBackRefs.C_DOC) == "New Scene"
    assert item.text(tabBackRefs.C_TITLE) == "Scene One"

    # Update Label
    SHARED.project.tree[C.hSceneDoc].setName("First Scene")  # type: ignore
    nwGUI.projView.renameTreeItem(C.hSceneDoc)
    item = tabBackRefs.topLevelItem(0)
    assert item is not None
    assert item.text(tabBackRefs.C_DOC) == "First Scene"
    assert item.text(tabBackRefs.C_TITLE) == "Scene One"

    # Clear Index
    SHARED.project.index.clear()
    assert tabBackRefs.topLevelItemCount() == 0

    # Rebuild Index
    SHARED.project.index.rebuild()
    assert tabBackRefs.topLevelItemCount() == 1

    # Test Update Theme
    tabBackRefs._editIcon = None  # type: ignore
    tabBackRefs._viewIcon = None  # type: ignore
    tabBackRefs.updateTheme()
    assert isinstance(tabBackRefs._editIcon, QIcon)
    assert isinstance(tabBackRefs._viewIcon, QIcon)

    # Click the Edit Button
    nwGUI.docPanes.openDocument(C.hChapterDoc)
    assert nwGUI.docEditor.docHandle == C.hChapterDoc
    refsModel = tabBackRefs.model()
    assert refsModel is not None
    tabBackRefs._treeItemClicked(refsModel.index(0, tabBackRefs.C_EDIT))
    assert nwGUI.docEditor.docHandle == C.hSceneDoc

    # Click the View Button
    assert nwGUI.docViewer.docHandle == hJane
    tabBackRefs._treeItemClicked(refsModel.index(0, tabBackRefs.C_VIEW))
    assert nwGUI.docViewer.docHandle == C.hSceneDoc

    # Clicking any other column does nothing
    nwGUI.docPanes.viewDocument(hJane)
    assert nwGUI.docViewer.docHandle == hJane
    tabBackRefs._treeItemClicked(refsModel.index(0, tabBackRefs.C_DOC))
    assert nwGUI.docViewer.docHandle == hJane

    # Double-Click
    nwGUI.docPanes.viewDocument(hJane)
    assert nwGUI.docViewer.docHandle == hJane
    tabBackRefs._treeItemDoubleClicked(refsModel.index(0, tabBackRefs.C_DOC))
    assert nwGUI.docViewer.docHandle == C.hSceneDoc

    # Double-clicking the edit/view columns does nothing
    nwGUI.docPanes.viewDocument(hJane)
    assert nwGUI.docViewer.docHandle == hJane
    tabBackRefs._treeItemDoubleClicked(refsModel.index(0, tabBackRefs.C_EDIT))
    assert nwGUI.docViewer.docHandle == hJane

    # Regression: Adding/removing references while viewing target should refresh panel
    nwGUI.docPanes.viewDocument(hJane)
    assert nwGUI.docViewer.docHandle == hJane
    assert tabBackRefs.topLevelItemCount() == 1

    nwGUI.docPanes.openDocument(C.hSceneDoc)
    nwGUI.docEditor.setPlainText("### Scene One\n\nNo references in this section.\n")
    nwGUI.docPanes.saveDocument()
    assert tabBackRefs.topLevelItemCount() == 0

    nwGUI.docEditor.setPlainText("### Scene One\n\n@char: Jane\n")
    nwGUI.docPanes.saveDocument()
    assert tabBackRefs.topLevelItemCount() == 1

    # A None handle just clears the content
    tabBackRefs.refreshContent(None)
    assert tabBackRefs.topLevelItemCount() == 0

    # A stale back-reference to a deleted item is skipped
    with monkeypatch.context() as mp:
        mp.setattr(type(SHARED.project.index), "getBackReferenceList", lambda *a: {"0000000000000": ("T0001", None)})
        tabBackRefs.refreshContent(hJane)
        assert tabBackRefs.topLevelItemCount() == 0

    # qtbot.stop()


@pytest.mark.gui
def testGuiDocViewerPanel_Tags(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    nwGUI: GuiMain,
    projPath: Path,
    mockRnd: MockRnd,
):
    """Test the document viewer tags panels."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.projView.projTree.expandAll()
    viewPanel = nwGUI.docViewerPanel

    nwGUI.docPanes.openDocument(C.hSceneDoc)
    nwGUI.docPanes.viewDocument(C.hSceneDoc)

    assert len(viewPanel.kwTabs) == len(nwLists.USER_CLASSES)
    assert len(viewPanel.idTabs) == len(nwLists.USER_CLASSES)

    # Add Two Tags
    hJane = "0000000000011"
    hJohn = "0000000000012"
    nwGUI.docEditor.setPlainText("### New Scene\n\n@char: Jane, John\n\n")
    nwGUI.docPanes.saveDocument()
    cursor = nwGUI.docEditor.textCursor()
    cursor.setPosition(22)
    nwGUI.docEditor._processTag(cursor, create=True)
    cursor.setPosition(28)
    nwGUI.docEditor._processTag(cursor, create=True)

    # Check Panel Tab Visibility
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["CHARACTER"]) is True
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["PLOT"]) is False
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["WORLD"]) is False
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["TIMELINE"]) is False
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["OBJECT"]) is False
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["ENTITY"]) is False
    assert viewPanel.mainTabs.isTabVisible(viewPanel.idTabs["CUSTOM"]) is False

    # Check Character Tab
    charTab = viewPanel.kwTabs["CHARACTER"]
    viewPanel.mainTabs.setCurrentIndex(viewPanel.idTabs["CHARACTER"])
    assert charTab.topLevelItemCount() == 2
    item = charTab.topLevelItem(0)
    assert item is not None
    assert item.text(charTab.C_NAME) == "Jane"
    assert item.text(charTab.C_DOC) == "Jane"
    assert item.text(charTab.C_TITLE) == "Jane"
    item = charTab.topLevelItem(1)
    assert item is not None
    assert item.text(charTab.C_NAME) == "John"
    assert item.text(charTab.C_DOC) == "John"
    assert item.text(charTab.C_TITLE) == "John"
    assert item.data(charTab.C_USES, QtDisplayRole) == 1

    # Edit Jane
    nwGUI.docPanes.openDocument(hJane)
    nwGUI.docEditor.setPlainText("# Jane Smith\n\n@tag: Janey\n\n")
    nwGUI.docPanes.saveDocument()
    SHARED.project.tree[hJane].setName("Awesome Jane")  # type: ignore
    nwGUI.projView.renameTreeItem(hJane)
    item = charTab.topLevelItem(0)
    assert item is not None
    assert item.text(charTab.C_NAME) == "Janey"
    assert item.text(charTab.C_DOC) == "Awesome Jane"
    assert item.text(charTab.C_TITLE) == "Jane Smith"
    assert item.data(charTab.C_USES, QtDisplayRole) == 0

    # Counts update when references change, and sort numerically
    assert SHARED.project.index.scanText(
        C.hSceneDoc, "### Scene\n@char: Janey\n" + "".join(f"### S{i}\n@char: John\n" for i in range(10))
    )
    charTab.sortByColumn(charTab.C_USES, Qt.SortOrder.AscendingOrder)
    assert [charTab.topLevelItem(i).data(charTab.C_USES, QtDisplayRole) for i in range(2)] == [1, 10]  # type: ignore

    # Clear Index
    SHARED.project.index.clear()
    assert charTab.topLevelItemCount() == 0

    # Rebuild Index
    SHARED.project.index.rebuild()
    assert charTab.topLevelItemCount() == 2

    # Test Update Theme
    charTab._classIcon = None  # type: ignore
    charTab._editIcon = None  # type: ignore
    charTab._viewIcon = None  # type: ignore
    charTab.updateTheme()
    assert isinstance(charTab._classIcon, QIcon)
    assert isinstance(charTab._editIcon, QIcon)
    assert isinstance(charTab._viewIcon, QIcon)

    # Remove Non-Existing Tag
    caplog.clear()
    viewPanel.updateChangedTags(["foo"], ["bar"])
    assert charTab.topLevelItemCount() == 2
    assert "Could not remove tag" in caplog.text

    # View/Edit John
    assert nwGUI.docEditor.docHandle == hJane
    charModel = charTab.model()
    assert charModel is not None
    charTab._treeItemClicked(charModel.index(1, charTab.C_EDIT))
    assert nwGUI.docEditor.docHandle == hJohn
    assert nwGUI.docViewer.docHandle == C.hSceneDoc
    charTab._treeItemClicked(charModel.index(1, charTab.C_VIEW))
    assert nwGUI.docViewer.docHandle == hJohn

    # Clicking any other column does nothing
    charTab._treeItemClicked(charModel.index(0, charTab.C_NAME))
    assert nwGUI.docViewer.docHandle == hJohn

    charTab._treeItemDoubleClicked(charModel.index(0, charTab.C_NAME))
    assert nwGUI.docViewer.docHandle == hJane

    # Double-clicking the edit/view columns does nothing
    charTab._treeItemDoubleClicked(charModel.index(0, charTab.C_EDIT))
    assert nwGUI.docViewer.docHandle == hJane

    # Hide Inactive Tags
    viewPanel.aInactive.setChecked(True)
    assert charTab.topLevelItemCount() == 2

    nwJohn = SHARED.project.tree[hJohn]
    assert isinstance(nwJohn, ProjectItem)
    nwJohn.setActive(False)
    nwJohn.notifyToRefresh()
    assert charTab.topLevelItemCount() == 1

    # Update Labels
    item = charTab.topLevelItem(0)
    assert item is not None
    assert item.text(charTab.C_IMPORT) == "New"
    SHARED.project.data.itemImport.add(C.iNew, "Stuff", "#646464", "SQUARE", 0)
    viewPanel.updateStatusLabels("i")
    item = charTab.topLevelItem(0)
    assert item is not None
    assert item.text(charTab.C_IMPORT) == "Stuff"

    # A stale tag reference with no resolved item is skipped
    indexClass = type(SHARED.project.index)
    with monkeypatch.context() as mp:
        mp.setattr(indexClass, "getDocumentTags", lambda *a: ["stale"])
        mp.setattr(indexClass, "getSingleTag", lambda *a: ("", "", None, None))
        viewPanel.onProjectItemChanged(hJane, nwChange.UPDATE)
        assert charTab.topLevelItemCount() == 1

    with monkeypatch.context() as mp:
        mp.setattr(indexClass, "getTagsData", lambda *a, **k: [("stale", "", "", None, None)])
        viewPanel._loadAllTags()
        assert charTab.topLevelItemCount() == 1

    # Open Project Tasks
    # ==================

    # Column widths that aren't a dict, or entries that aren't lists, are silently ignored
    SHARED.project.options.setValue("GuiDocViewerPanel", "colWidths", "not-a-dict")
    viewPanel.openProjectTasks()

    SHARED.project.options.setValue("GuiDocViewerPanel", "colWidths", {"CHARACTER": "not-a-list", "BOGUS": [1, 2]})
    viewPanel.openProjectTasks()

    # A sanity check also guards against a non-dict getting past getDict itself
    with monkeypatch.context() as mp:
        mp.setattr(OptionState, "getDict", lambda *a, **k: "not-a-dict")
        viewPanel.openProjectTasks()

    # A column width list that's too short is ignored
    widths = charTab.getColumnWidths()
    charTab.setColumnWidths([1, 2])
    assert charTab.getColumnWidths() == widths

    # qtbot.stop()
