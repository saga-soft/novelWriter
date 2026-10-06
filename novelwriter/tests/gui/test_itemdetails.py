"""
novelWriter - GUI Item Details Tests
====================================

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

from novelwriter import SHARED
from novelwriter.common import elide
from novelwriter.constants import nwLabels, trConst
from novelwriter.core.project import NWProject
from novelwriter.enum import nwChange

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiItemDetails_Display(qtbot, nwGUI, projPath, mockRnd):
    """Test that the details panel displays the data of the currently
    selected item, and updates or clears it as expected.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    itemDetails = nwGUI.itemDetails
    tree = SHARED.project.tree

    # A document item populates all the fields
    chapter = tree[C.hChapterDoc]
    assert chapter is not None

    itemDetails.updateViewBox(C.hChapterDoc)
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)
    assert itemDetails.statusData.text() == chapter.getImportStatus()[0]
    assert itemDetails.classData.text() == trConst(nwLabels.CLASS_NAME[chapter.itemClass])
    assert itemDetails.usageData.text() == chapter.describeMe()
    assert itemDetails.cCountData.text() == f"{chapter.charCount:n}"
    assert itemDetails.wCountData.text() == f"{chapter.wordCount:n}"
    assert itemDetails.pCountData.text() == f"{chapter.paraCount:n}"

    # A non-file item shows dashes for the counts instead
    folder = tree[C.hChapterDir]
    assert folder is not None
    assert folder.isFileType() is False

    itemDetails.updateViewBox(C.hChapterDir)
    assert itemDetails.labelData.text() == elide(folder.itemName, 100)
    assert itemDetails.cCountData.text() == "\u2013"
    assert itemDetails.wCountData.text() == "\u2013"
    assert itemDetails.pCountData.text() == "\u2013"

    # An invalid handle clears the details instead
    itemDetails.updateViewBox(C.hInvalid)
    assert itemDetails.labelData.text() == ""
    assert itemDetails.cCountData.text() == ""

    # A project item change for a different handle is ignored
    itemDetails.updateViewBox(C.hChapterDoc)
    itemDetails.onProjectItemChanged(C.hSceneDoc, nwChange.UPDATE)
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)

    # A create change for the current handle is not acted upon
    itemDetails.onProjectItemChanged(C.hChapterDoc, nwChange.CREATE)
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)

    # A project item change for the currently viewed handle refreshes it
    itemDetails.onProjectItemChanged(C.hChapterDoc, nwChange.UPDATE)
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)

    itemDetails.onProjectItemChanged(C.hChapterDoc, nwChange.DELETE)
    assert itemDetails.labelData.text() == ""

    # Explicitly requesting a refresh reloads the current handle
    itemDetails.updateViewBox(C.hChapterDoc)
    itemDetails.refreshDetails()
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)


@pytest.mark.gui
def testGuiItemDetails_DelayedRefresh(qtbot, nwGUI, projPath, mockRnd):
    """Test that the details panel does not refresh its content while
    collapsed, and instead applies the pending update once expanded.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    itemDetails = nwGUI.itemDetails
    chapter = SHARED.project.tree[C.hChapterDoc]
    assert chapter is not None

    # Populate the panel while expanded, then collapse it
    itemDetails.updateViewBox(C.hChapterDoc)
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)

    itemDetails.setExpanded(False)
    assert itemDetails.isExpanded() is False

    # While collapsed, an update is deferred rather than applied
    scene = SHARED.project.tree[C.hSceneDoc]
    assert scene is not None

    itemDetails.updateViewBox(C.hSceneDoc)
    assert itemDetails._refresh == {"handle": C.hSceneDoc}
    assert itemDetails.labelData.text() == elide(chapter.itemName, 100)

    # Expanding the panel applies the deferred update
    itemDetails.setExpanded(True)
    assert itemDetails.isExpanded() is True
    assert itemDetails._refresh is None
    assert itemDetails.labelData.text() == elide(scene.itemName, 100)
