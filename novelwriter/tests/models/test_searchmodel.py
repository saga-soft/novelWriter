"""
novelWriter - Search Model Tests
================================

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

import pytest

from PyQt6.QtCore import QModelIndex
from PyQt6.QtGui import QBrush
from PyQt6.QtTest import QAbstractItemModelTester

from novelwriter import SHARED
from novelwriter.core.project import NWProject
from novelwriter.models.searchmodel import SearchNode, SearchResultModel
from novelwriter.types import QtDisplayRole, QtForegroundRole, QtUserRole

from tests.helpers import C, buildTestProject


@pytest.mark.core
def testSearchNode_Basics():
    """Test the search node class in isolation."""
    node = SearchNode("0000000000001")

    # A fresh node has no children and no result
    assert node.handle == "0000000000001"
    assert node.result is None
    assert node.row() == 0
    assert node.parent() is None
    assert node.childCount() == 0
    assert node.child(0) is None
    assert node.child(-1) is None

    # Setting children updates their parent and row
    child = SearchNode("0000000000001", (0, 4))
    node.setChildren([child])
    assert node.childCount() == 1
    assert node.child(0) is child
    assert node.child(1) is None
    assert child.parent() is node
    assert child.row() == 0

    node.setRow(3)
    assert node.row() == 3


@pytest.mark.core
def testSearchModel_ModelTest(mockGUI, mockRnd, fncPath):
    """Run the Qt model tester on the model."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    title = project.tree[C.hTitlePage]
    scene = project.tree[C.hSceneDoc]
    assert title is not None
    assert scene is not None

    model = SearchResultModel()
    QAbstractItemModelTester(model)

    model.setResult(title, [(0, 4, "Text one", 0)], False)
    model.setResult(scene, [(0, 4, "Text two", 0), (10, 5, "Text three", 0)], False)
    model.setResult(title, [(0, 4, "Text one", 0), (20, 4, "Text four", 0)], False)
    model.updateTheme()
    model.clear()


@pytest.mark.core
def testSearchModel_Interface(mockGUI, mockRnd, fncPath):
    """Test the search result model and node data access."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    title = project.tree[C.hTitlePage]
    scene = project.tree[C.hSceneDoc]
    assert title is not None
    assert scene is not None

    model = SearchResultModel()
    root = QModelIndex()

    # Empty model
    assert model.rowCount(root) == 0
    assert model.columnCount(root) == 2
    assert model.index(0, 0, root).isValid() is False
    assert model.parent(root).isValid() is False
    assert model.data(root, QtDisplayRole) is None
    assert model.handle(root) is None
    assert model.result(root) is None
    assert model.entry(title.itemHandle) is None
    assert model.indexFromHandle(title.itemHandle).isValid() is False

    # Populate with two documents, one capped
    model.setResult(title, [(0, 4, "Text one", 0)], False)
    model.setResult(scene, [(0, 4, "Text two", 5), (10, 5, "Text three", 5)], True)
    assert model.rowCount(root) == 2

    titleIdx = model.index(0, 0, root)
    sceneIdx = model.index(1, 0, root)
    assert titleIdx.isValid() is True
    assert sceneIdx.isValid() is True

    # Document-level data
    assert model.data(titleIdx, QtDisplayRole) == "Title Page"
    assert model.data(model.index(0, 1, root), QtDisplayRole) == "(1)"
    assert model.data(sceneIdx, QtDisplayRole) == "New Scene"
    assert model.data(model.index(1, 1, root), QtDisplayRole) == "(2+)"
    assert model.data(model.index(1, 1, root), QtForegroundRole) == QBrush(SHARED.theme.accentText)
    assert model.handle(titleIdx) == title.itemHandle
    assert model.handle(sceneIdx) == scene.itemHandle
    assert model.result(titleIdx) is None
    assert model.result(sceneIdx) is None

    # Match-level data
    assert model.rowCount(sceneIdx) == 2
    match0 = model.index(0, 0, sceneIdx)
    match1 = model.index(1, 0, sceneIdx)
    assert model.data(match0, QtDisplayRole) == "Text two"
    assert model.data(match1, QtDisplayRole) == "Text three"
    assert model.handle(match0) == scene.itemHandle
    assert model.result(match0) == (scene.itemHandle, 0, 4)
    assert model.result(match1) == (scene.itemHandle, 10, 5)

    # Match-level highlight span, clamped to the context text's bounds
    assert model.data(match0, QtUserRole) == (5, 8)
    assert model.data(match1, QtUserRole) == (5, 10)

    # Parent lookups
    assert model.parent(match0) == sceneIdx
    assert model.parent(sceneIdx).isValid() is False

    # Handle bookkeeping
    entry = model.entry(title.itemHandle)
    assert entry is not None
    assert entry[0] == 0
    assert model.entry("0000000000000") is None
    assert model.indexFromHandle(scene.itemHandle) == sceneIdx
    assert model.indexFromHandle("0000000000000").isValid() is False


@pytest.mark.core
def testSearchModel_Edit(qtbot, mockGUI, mockRnd, fncPath):
    """Test inserting, updating, and clearing search results."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    title = project.tree[C.hTitlePage]
    chapter = project.tree[C.hChapterDoc]
    scene = project.tree[C.hSceneDoc]
    assert title is not None
    assert chapter is not None
    assert scene is not None

    model = SearchResultModel()
    root = QModelIndex()

    # Adding a document with no results is a no-op
    model.setResult(title, [], False)
    assert model.rowCount(root) == 0

    # Documents are appended in the order they are added
    model.setResult(title, [(0, 4, "one", 0)], False)
    model.setResult(chapter, [(0, 4, "two", 0)], False)
    model.setResult(scene, [(0, 4, "three", 0)], False)
    assert [model.data(model.index(i, 0, root), QtDisplayRole) for i in range(3)] == [
        "Title Page",
        "New Chapter",
        "New Scene",
    ]

    # Updating a document replaces it in its own row, leaving siblings alone
    model.setResult(chapter, [(0, 5, "updated", 0)], False)
    assert model.rowCount(root) == 3
    assert [model.data(model.index(i, 0, root), QtDisplayRole) for i in range(3)] == [
        "Title Page",
        "New Chapter",
        "New Scene",
    ]
    chapterIdx = model.index(1, 0, root)
    assert model.rowCount(chapterIdx) == 1
    assert model.data(model.index(0, 0, chapterIdx), QtDisplayRole) == "updated"

    # The (row, timestamp) entry is refreshed on every update, which is what
    # allows a live per-document refresh to tell a stale result apart
    firstEntry = model.entry(chapter.itemHandle)
    assert firstEntry is not None
    model.setResult(chapter, [(0, 5, "updated again", 0)], False)
    secondEntry = model.entry(chapter.itemHandle)
    assert secondEntry is not None
    assert secondEntry[0] == firstEntry[0]
    assert secondEntry[1] >= firstEntry[1]

    # Theme updates refresh the count column color and emit dataChanged
    with qtbot.waitSignal(model.dataChanged):
        model.updateTheme()

    # Clear resets the model completely
    model.clear()
    assert model.rowCount(root) == 0
    assert model.entry(title.itemHandle) is None
