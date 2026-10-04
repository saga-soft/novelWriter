"""
novelWriter - Novel Model Tests
===============================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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
from PyQt6.QtTest import QAbstractItemModelTester

from novelwriter.core.indexdata import IndexHeading
from novelwriter.core.project import NWProject
from novelwriter.enum import nwNovelExtra
from novelwriter.models.novelmodel import NovelModel
from novelwriter.types import QtDisplayRole

from tests.helpers import C, buildTestProject


@pytest.mark.core
def testNovelModel_ModelTest(nwGUI):
    """Run the Qt model tester on the model."""
    model = NovelModel()
    QAbstractItemModelTester(model)


@pytest.mark.core
def testNovelModel_Interface(nwGUI, fncPath, mockRnd):
    """Test the novel model interface."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    model = project.index.getNovelModel(C.hNovelRoot)
    assert isinstance(model, NovelModel)

    root = QModelIndex()
    assert root.row() == -1

    # Initial structure
    assert model.rowCount(root) == 3
    assert model.columnCount(root) == 3
    assert model.rowCount(model.createIndex(0, 0)) == 0
    assert model.columnCount(model.createIndex(0, 0)) == 0
    assert model.data(model.createIndex(0, 0), QtDisplayRole) == "New Novel"
    assert model.handle(model.createIndex(0, 0)) == C.hTitlePage
    assert model.key(model.createIndex(0, 0)) == "T0001"

    # Clear the model and check error handling
    model.beginResetModel()
    model.clear()
    model.endResetModel()

    assert model.data(root, QtDisplayRole) is None
    assert model.handle(root) is None
    assert model.key(root) is None


@pytest.mark.core
def testNovelModel_Extra(nwGUI, fncPath, mockRnd):
    """Test the novel model extra column."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    root = QModelIndex()
    model = project.index.getNovelModel(C.hNovelRoot)
    assert isinstance(model, NovelModel)
    assert model.rowCount(root) == 3

    project.index._tagsIndex.add("Jane", "Jane", "0000000000000", "T0001", "CHARACTER")
    project.index._tagsIndex.add("John", "John", "0000000000000", "T0001", "CHARACTER")
    project.index._tagsIndex.add("Main", "Main", "0000000000000", "T0001", "PLOT")
    project.index._tagsIndex.add("Side", "Side", "0000000000000", "T0001", "PLOT")

    scene = project.index._itemIndex[C.hSceneDoc]
    assert scene is not None
    scene.addHeadingRef("T0001", ["Jane"], "@pov")
    scene.addHeadingRef("T0001", ["John"], "@focus")
    scene.addHeadingRef("T0001", ["Main"], "@plot")
    scene.addHeadingRef("T0001", ["Side"], "@plot")

    # No extra by default
    assert model.columns == 3
    assert model._extraKey == ""
    assert model._extraLabel == ""

    # Point of view
    model.setExtraColumn(nwNovelExtra.POV)
    model.refresh(scene)
    assert model.columns == 4
    assert model._extraKey == "@pov"
    assert model._extraLabel == "Point of View"
    assert model.data(model.createIndex(2, 2), QtDisplayRole) == "Jane"

    model.setExtraColumn(nwNovelExtra.HIDDEN)
    assert model.columns == 3

    # Focus
    model.setExtraColumn(nwNovelExtra.FOCUS)
    model.refresh(scene)
    assert model.columns == 4
    assert model._extraKey == "@focus"
    assert model._extraLabel == "Focus"
    assert model.data(model.createIndex(2, 2), QtDisplayRole) == "John"

    model.setExtraColumn(nwNovelExtra.HIDDEN)
    assert model.columns == 3

    # Plot
    model.setExtraColumn(nwNovelExtra.PLOT)
    model.refresh(scene)
    assert model.columns == 4
    assert model._extraKey == "@plot"
    assert model._extraLabel == "Plot"
    assert model.data(model.createIndex(2, 2), QtDisplayRole) == "Main, Side"

    model.setExtraColumn(nwNovelExtra.HIDDEN)
    assert model.columns == 3


@pytest.mark.core
def testNovelModel_Data(nwGUI, fncPath, mockRnd):
    """Test the novel model data methods."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    root = QModelIndex()
    model = project.index.getNovelModel(C.hNovelRoot)
    assert isinstance(model, NovelModel)
    assert model.rowCount(root) == 3

    title = project.index._itemIndex[C.hTitlePage]
    chapter = project.index._itemIndex[C.hChapterDoc]
    scene = project.index._itemIndex[C.hSceneDoc]

    assert title is not None
    assert chapter is not None
    assert scene is not None

    # Clear the model and try to refresh
    model.beginResetModel()
    model.clear()
    model.endResetModel()
    assert model.rowCount(root) == 0

    # Cannot refresh an empty model
    assert model.refresh(title) is False

    # Add all back
    model.beginResetModel()
    model.append(title)
    model.append(chapter)
    model.append(scene)
    model.endResetModel()

    # Add headings to scene
    scene.addHeading(IndexHeading(scene._cache, "T0002", 10, "H4", "A Section"))
    scene.addHeading(IndexHeading(scene._cache, "T0003", 10, "H4", "Another Section"))
    assert model.refresh(scene) is True
    assert [model.data(model.createIndex(i, 0), QtDisplayRole) for i in range(model.rowCount(root))] == [
        "New Novel",
        "New Chapter",
        "New Scene",
        "A Section",
        "Another Section",
    ]

    # Remove new headings
    del scene._headings["T0002"]
    del scene._headings["T0003"]
    assert model.refresh(scene) is True
    assert [model.data(model.createIndex(i, 0), QtDisplayRole) for i in range(model.rowCount(root))] == [
        "New Novel",
        "New Chapter",
        "New Scene",
    ]
