"""
novelWriter - Outline Model Tester
==================================

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

from types import SimpleNamespace

import pytest

from PyQt6.QtCore import QModelIndex, Qt
from PyQt6.QtTest import QAbstractItemModelTester

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwKeyWords
from novelwriter.models.outlinemodel import BLANK_STYLE, NODE_FLAGS, OutlineModel, OutlineNode
from novelwriter.types import QtDisplayRole


@pytest.mark.core
def testOutlineModel_ModelTest(nwGUI, prjLipsum):
    """Run the Qt model tester on the model."""
    model = OutlineModel()
    QAbstractItemModelTester(model)

    assert nwGUI.openProject(prjLipsum)
    model.buildOutline(SHARED.project.index, None, {1, 2, 3, 4})
    QAbstractItemModelTester(model)


@pytest.mark.core
def testOutlineModel_Interface(nwGUI, prjLipsum):
    """Test the outline model interface."""
    assert nwGUI.openProject(prjLipsum)
    index = SHARED.project.index
    root = QModelIndex()

    model = OutlineModel()
    assert model.rowCount(root) == 0
    assert model.columnCount(root) == 1

    # All levels
    model.buildOutline(index, None, {1, 2, 3, 4})
    assert model.rowCount(root) == 12
    assert model.rowCount(model.index(0, 0)) == 0
    assert model.columnCount(model.index(0, 0)) == 0

    # Filtered levels keep the story order
    model.buildOutline(index, None, {2})
    assert model.rowCount(root) == 3
    assert [model.node(model.index(r, 0)).title for r in range(3)] == [  # type: ignore
        "Prologue",
        "Chapter One",
        "Chapter Two",
    ]

    # Headers
    horizontal = Qt.Orientation.Horizontal
    assert model.headerData(OutlineModel.C_TITLE, horizontal, QtDisplayRole) == "Story"
    assert model.headerData(99, horizontal, QtDisplayRole) is None
    assert model.headerData(0, Qt.Orientation.Vertical, QtDisplayRole) is None
    assert model.headerData(0, horizontal, Qt.ItemDataRole.ToolTipRole) is None

    # Data and flags
    assert model.data(model.index(0, 0), QtDisplayRole) is None
    assert model.flags(model.index(0, 0)) == NODE_FLAGS
    assert model.flags(root) == Qt.ItemFlag.NoItemFlags

    # Nodes
    assert model.node(root) is None
    assert model.node(model.createIndex(99, 0)) is None

    node = model.node(model.index(1, 0))
    assert isinstance(node, OutlineNode)
    assert node.handle == "fb609cd8319dc"
    assert node.key == "T0001"
    assert node.title == "Chapter One"
    assert node.level == 2
    assert node.counts == "67 Words"
    CONFIG.useCharCount = True
    assert node.counts == "419 Characters"
    assert node.style is not BLANK_STYLE
    assert node.progress == ""

    # Spans of tag keys in the references
    node._lists[nwKeyWords.CHAR_KEY] = ["Jane", "John", "Jack"]
    assert node.refSpans(nwKeyWords.CHAR_KEY, {"john", "jack"}) == [(6, 4), (12, 4)]
    assert node.refSpans(nwKeyWords.POV_KEY, {"bod"}) == [(0, 3)]
    assert node.refSpans(nwKeyWords.POV_KEY, {"jane"}) == []
    assert node.refSpans(nwKeyWords.MENTION_KEY, {"bod"}) == []

    # A node without a heading is blank
    blank = OutlineNode("", "", None, model._labels, BLANK_STYLE)
    assert blank.level == 0
    assert blank.title == ""
    assert blank.entries(0) == []

    # Clear the model
    model.clear()
    assert model.rowCount(root) == 0


@pytest.mark.core
def testOutlineModel_Columns(nwGUI, prjLipsum):
    """Test the outline model columns."""
    assert nwGUI.openProject(prjLipsum)
    index = SHARED.project.index
    root = QModelIndex()
    horizontal = Qt.Orientation.Horizontal
    model = OutlineModel()

    # Columns hold references and comments, where comment keys match
    # regardless of spelling, and empty entries are skipped
    heading = index.getItemHeading("fb609cd8319dc", "T0001")
    assert heading is not None
    heading.setComment("story", "Goal", "Find\n\nthe key")
    heading.setComment("note", "Consistency", "Check")
    columns = [
        ("Comments", ("synopsis", "story.goal")),
        ("Notes", ("note.consistency", "note.missing")),
        ("Refs", ("@pov", "@mention")),
    ]
    model.buildOutline(index, None, {2}, columns=columns)
    assert model.columnCount(root) == 4
    assert model.headerData(OutlineModel.C_COLUMNS, horizontal, QtDisplayRole) == "Comments"
    assert model.headerData(OutlineModel.C_COLUMNS + 1, horizontal, QtDisplayRole) == "Notes"
    assert model.headerData(OutlineModel.C_COLUMNS + 2, horizontal, QtDisplayRole) == "Refs"
    commented = model.node(model.index(1, 0))
    assert isinstance(commented, OutlineNode)
    synopsis, goal = commented.entries(0)
    assert synopsis[:2] == ("synopsis", "Synopsis")
    assert synopsis[2].startswith("Lorem ipsum dolor sit amet")
    assert goal == ("story.goal", "Story Structure (Goal)", "Find\u2028the key")
    assert commented.entries(1) == [("note.consistency", "Note (Consistency)", "Check")]
    assert commented.entries(2) == [("@pov", "Point of View", "Bod")]
    assert commented.entries(3) == []


@pytest.mark.core
def testOutlineModel_Progress(nwGUI, prjLipsum):
    """Test the outline model page and progress calculation."""
    assert nwGUI.openProject(prjLipsum)
    index = SHARED.project.index
    model = OutlineModel()

    # Progress, with partitions and chapters starting on a new page
    model.buildOutline(index, None, {1, 2, 3, 4}, 100)
    progress = [model.node(model.index(r, 0)).progress for r in range(12)]  # type: ignore
    assert progress[0] == "Page 1 (0.0\u202f%)"
    assert progress[1] == "Page 4 (7.3\u202f%)"
    assert progress[3] == "Page 6 (10.6\u202f%)"
    assert progress[5] == "Page 8 (18.7\u202f%)"
    assert progress[8] == "Page 17 (46.3\u202f%)"
    assert progress[11] == "Page 27 (81.9\u202f%)"

    # Clear double page starts partitions and chapters on odd pages
    model.buildOutline(index, None, {1, 2, 3, 4}, 100, True)
    progress = [model.node(model.index(r, 0)).progress for r in range(12)]  # type: ignore
    assert progress[0] == "Page 1 (0.0\u202f%)"
    assert progress[1] == "Page 5 (7.3\u202f%)"
    assert progress[3] == "Page 9 (10.6\u202f%)"
    assert progress[5] == "Page 11 (18.7\u202f%)"
    assert progress[8] == "Page 21 (46.3\u202f%)"
    assert progress[11] == "Page 31 (81.9\u202f%)"

    # Without titles and chapters, pages run on and clear double is ignored
    scenes = [e for e in index.iterNovelStructure() if e[2].level == "H3"]
    scenesOnly = SimpleNamespace(iterNovelStructure=lambda rHandle: iter(scenes))
    expected = [
        "Page 1 (0.0\u202f%)",
        "Page 2 (8.6\u202f%)",
        "Page 5 (23.4\u202f%)",
        "Page 10 (45.2\u202f%)",
        "Page 15 (73.1\u202f%)",
    ]
    for clearDouble in (False, True):
        model.buildOutline(scenesOnly, None, {3}, 100, clearDouble)  # type: ignore
        assert [model.node(model.index(r, 0)).progress for r in range(5)] == expected  # type: ignore

    # Filtered levels still count all words
    model.buildOutline(index, None, {2}, 100)
    progress = [model.node(model.index(r, 0)).progress for r in range(3)]  # type: ignore
    assert progress == ["Page 4 (7.3\u202f%)", "Page 6 (10.6\u202f%)", "Page 17 (46.3\u202f%)"]

    # A smaller target is ignored, and a larger one is used instead
    model.buildOutline(index, None, {2}, 100, False, 1000)
    assert model.node(model.index(2, 0)).progress == "Page 17 (46.3\u202f%)"  # type: ignore
    model.buildOutline(index, None, {2}, 100, False, 6000)
    assert model.node(model.index(2, 0)).progress == "Page 17 (23.2\u202f%)"  # type: ignore

    # Character counts are used for both pages and progress
    model.buildOutline(index, None, {2}, 1000, False, 0, True)
    progress = [model.node(model.index(r, 0)).progress for r in range(3)]  # type: ignore
    assert progress == ["Page 4 (6.5\u202f%)", "Page 6 (9.7\u202f%)", "Page 14 (45.6\u202f%)"]
    model.buildOutline(index, None, {2}, 1000, False, 100000, True)
    progress = [model.node(model.index(r, 0)).progress for r in range(3)]  # type: ignore
    assert progress == ["Page 4 (1.3\u202f%)", "Page 6 (2.0\u202f%)", "Page 14 (9.2\u202f%)"]
