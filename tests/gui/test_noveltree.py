"""
novelWriter - GUI Novel View Tests
==================================

This file is a part of novelWriter.

Copyright (C) 2021 Veronica Berglyd Olsen and novelWriter contributors.

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

from PyQt6.QtCore import QModelIndex, QPoint
from PyQt6.QtWidgets import QInputDialog, QToolTip
from pytestqt.qtbot import QtBot

from novelwriter import CONFIG, SHARED
from novelwriter.core.project import NWProject
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.enum import nwFocus, nwItemType, nwNovelExtra, nwView
from novelwriter.guimain import GuiMain
from novelwriter.models.novelmodel import NovelModel
from novelwriter.types import QtDisplayRole

from tests.helpers import C, MockRnd, buildTestProject


@pytest.mark.gui
def testGuiNovelView_Content(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    nwGUI: GuiMain,
    projPath: Path,
    mockRnd: MockRnd,
):
    """Test navigating the novel tree."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    nwGUI._switchFocus(nwFocus.TREE)
    nwGUI.projView.projTree.clearSelection()
    nwGUI.projView.projTree.setSelectedHandle(C.hCharRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE)

    contentPath = SHARED.project.storage.contentPath
    assert isinstance(contentPath, Path)
    cHandle = "0000000000011"

    (contentPath / f"{cHandle}.md").write_text("# Jane Doe\n\n@tag: Jane\n\n", encoding="utf-8")
    (contentPath / f"{C.hSceneDoc}.md").write_text(
        (
            "### Scene One\n\n"
            "@pov: Jane\n"
            "@focus: Jane\n\n"
            "% Synopsis: This is a scene.\n\n"
            "This is some text in the edited scene."
        ),
        encoding="utf-8",
    )

    novelView = nwGUI.novelView
    novelTree = nwGUI.novelView.novelTree
    novelBar = nwGUI.novelView.novelBar

    # Show/Hide Scrollbars
    # ====================

    CONFIG.hideVScroll = True
    CONFIG.hideHScroll = True
    novelView.initViewport()
    vBar = novelTree.verticalScrollBar()
    hBar = novelTree.horizontalScrollBar()
    assert vBar is not None
    assert hBar is not None
    assert not vBar.isVisible()
    assert not hBar.isVisible()

    CONFIG.hideVScroll = False
    CONFIG.hideHScroll = False
    novelView.initViewport()
    assert vBar.isEnabled()
    assert hBar.isEnabled()

    # Populate Tree
    # =============
    root = QModelIndex()

    novelView.setTreeFocus()
    nwGUI.changeView(nwView.NOVEL)

    # Clear tree
    novelView.setCurrentNovel(None)
    assert novelTree._getModel() is None

    # Reload
    novelView.refreshCurrentTree()
    model = novelTree._getModel()
    assert isinstance(model, NovelModel)

    # Check the items
    assert model.rowCount(root) == 3
    assert model.columnCount(root) == 3
    assert model.data(model.createIndex(2, 1), QtDisplayRole) == "2"  # Word Count

    nwGUI.rebuildIndex()  # This should update the word count to the edited scene
    assert model.data(model.createIndex(2, 1), QtDisplayRole) == "10"  # Word Count

    # Child counts are included in the parent headings, if enabled
    chapter = SHARED.project.index.getItemHeading(C.hChapterDoc, "T0001")
    assert chapter is not None
    assert novelBar.aSubCounts.isChecked() is True
    assert model.data(model.createIndex(1, 1), QtDisplayRole) == f"{chapter.mainCount + 10}"
    novelBar.aSubCounts.trigger()
    assert CONFIG.novelViewSubCounts is False
    assert model.data(model.createIndex(1, 1), QtDisplayRole) == f"{chapter.mainCount}"
    novelBar.aSubCounts.trigger()
    assert CONFIG.novelViewSubCounts is True
    assert model.data(model.createIndex(1, 1), QtDisplayRole) == f"{chapter.mainCount + 10}"

    # Extra Column
    # ============
    novelBar.setLastColType(nwNovelExtra.POV)
    assert model.rowCount(root) == 3
    assert model.columnCount(root) == 4

    # Scene column should contain the POV character
    assert model.data(model.createIndex(2, 2), QtDisplayRole) == "Jane"

    # Resize the last column
    assert novelTree.lastColSize == 25
    with monkeypatch.context() as mp:
        mp.setattr(QInputDialog, "getInt", lambda *a, **k: (40, True))
        novelBar._selectLastColumnSize()
    assert novelTree.lastColSize == 40

    # Cancelling the dialog leaves the size unchanged
    with monkeypatch.context() as mp:
        mp.setattr(QInputDialog, "getInt", lambda *a, **k: (60, False))
        novelBar._selectLastColumnSize()
    assert novelTree.lastColSize == 40

    # Open Items
    # ==========

    # Clear selection
    novelTree.clearSelection()
    assert novelView.getSelectedHandle() == (None, None)

    # Select scene
    novelTree.setCurrentIndex(model.createIndex(2, 0))
    assert novelView.getSelectedHandle() == (C.hSceneDoc, "T0001")

    # Double-click item
    novelTree._onDoubleClick(model.createIndex(2, 0))
    assert nwGUI.docEditor.docHandle == C.hSceneDoc

    # Middle-click item
    novelTree._onMiddleClick(model.createIndex(2, 0))
    assert nwGUI.docViewer.docHandle == C.hSceneDoc

    # Clicks on an invalid index do nothing
    novelTree._onSingleClick(QModelIndex())
    novelTree._onDoubleClick(QModelIndex())
    novelTree._onMiddleClick(QModelIndex())

    # Clicks with no model set do nothing
    novelTree.clearContent()
    novelTree._onSingleClick(model.createIndex(2, 0))
    novelTree._onDoubleClick(model.createIndex(2, 0))
    novelTree._onMiddleClick(model.createIndex(2, 0))
    novelTree.setModel(model)

    # Item Meta
    # =========

    toolTip = ""

    def showText(pos: QPoint, text: str) -> None:
        nonlocal toolTip
        toolTip = text

    with monkeypatch.context() as mp:
        mp.setattr(QToolTip, "showText", showText)

        toolTip = ""
        novelTree._onSingleClick(model.createIndex(2, 3))
        assert toolTip == (
            "<p><b>Point of View:</b> Jane<br><b>Focus:</b> Jane</p><p><b>Synopsis:</b> This is a scene.</p>"
        )

        # A click on a non-meta column does not pop the tooltip
        toolTip = ""
        novelTree._onSingleClick(model.createIndex(2, 0))
        assert toolTip == ""

        toolTip = ""
        novelTree._popMetaBox(QPoint(1, 1), C.hInvalid, "T0001")
        assert toolTip == ""

        # A heading with no synopsis and no references shows the fallback text
        SHARED.project.index.scanText(
            C.hSceneDoc,
            "### Scene One\n\n@pov: Jane\n@focus: Jane\n\n% Synopsis: This is a scene.\n\nText.\n\n"
            "### Scene Two\n\nJust some plain text with no tags.\n",
        )
        toolTip = ""
        novelTree._popMetaBox(QPoint(1, 1), C.hSceneDoc, "T0002")
        assert toolTip == "No meta data"

    # Active Status
    # =============
    assert novelBar._refresh == {C.hNovelRoot: False}

    # Add a document while tree in focus
    nwGUI.changeView(nwView.PROJECT)
    assert novelBar._active is False
    nwGUI.projView.projTree.setSelectedHandle(C.hChapterDir)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, hLevel=3)
    assert novelBar._refresh == {C.hNovelRoot: True}

    # Switch back and check that the refresh status is reset
    nwGUI.changeView(nwView.NOVEL)
    assert novelBar._refresh == {C.hNovelRoot: False}

    # Close
    # qtbot.stop()
    nwGUI.closeProject()
