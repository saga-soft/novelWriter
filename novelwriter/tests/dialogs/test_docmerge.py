"""
novelWriter - Merge Dialog Tests
================================

This file is a part of novelWriter
Copyright (C) 2021 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import Qt

from novelwriter.core.project import NWProject
from novelwriter.dialogs.docmerge import GuiDocMerge
from novelwriter.types import QtAccepted, QtRejected, QtUserRole

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiDocMerge_Main(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the merge documents tool."""
    monkeypatch.setattr(GuiDocMerge, "exec", lambda *a: None)
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Check that the dialog kan handle invalid items
    nwMerge = GuiDocMerge(nwGUI, C.hInvalid, [C.hInvalid])
    qtbot.addWidget(nwMerge)
    nwMerge.show()
    assert nwMerge.listBox.count() == 0
    nwMerge.reject()

    # Load items from chapter dir
    nwMerge = GuiDocMerge(nwGUI, C.hChapterDir, [C.hChapterDir, C.hChapterDoc, C.hSceneDoc])
    qtbot.addWidget(nwMerge)
    nwMerge.show()

    assert nwMerge.listBox.count() == 2

    itemOne = nwMerge.listBox.item(0)
    itemTwo = nwMerge.listBox.item(1)

    assert itemOne is not None
    assert itemTwo is not None

    assert itemOne.data(QtUserRole) == C.hChapterDoc
    assert itemTwo.data(QtUserRole) == C.hSceneDoc

    assert itemOne.checkState() == Qt.CheckState.Checked
    assert itemTwo.checkState() == Qt.CheckState.Checked

    data = nwMerge.data()
    assert data["sHandle"] == C.hChapterDir
    assert data["origItems"] == [C.hChapterDir, C.hChapterDoc, C.hSceneDoc]
    assert data["moveToTrash"] is False
    assert data["finalItems"] == [C.hChapterDoc, C.hSceneDoc]

    # Uncheck second item and toggle trash switch
    itemTwo.setCheckState(Qt.CheckState.Unchecked)
    nwMerge.trashSwitch.setChecked(True)

    data = nwMerge.data()
    assert data["sHandle"] == C.hChapterDir
    assert data["origItems"] == [C.hChapterDir, C.hChapterDoc, C.hSceneDoc]
    assert data["moveToTrash"] is True
    assert data["finalItems"] == [C.hChapterDoc]

    # Restore default values
    nwMerge._resetList()

    data = nwMerge.data()
    assert data["sHandle"] == C.hChapterDir
    assert data["origItems"] == [C.hChapterDir, C.hChapterDoc, C.hSceneDoc]
    assert data["moveToTrash"] is True
    assert data["finalItems"] == [C.hChapterDoc, C.hSceneDoc]

    # Reset with no handle set does nothing
    nwMerge._data.pop("sHandle", None)
    nwMerge._resetList()
    nwMerge.close()

    # Test Class Method
    with monkeypatch.context() as mp:
        mp.setattr(GuiDocMerge, "result", lambda *a: QtAccepted)
        data, status = GuiDocMerge.getData(nwGUI, C.hChapterDir, [C.hChapterDir, C.hChapterDoc, C.hSceneDoc])
        assert data["sHandle"] == C.hChapterDir
        assert status is True

    with monkeypatch.context() as mp:
        mp.setattr(GuiDocMerge, "result", lambda *a: QtRejected)
        data, status = GuiDocMerge.getData(nwGUI, C.hChapterDir, [C.hChapterDir, C.hChapterDoc, C.hSceneDoc])
        assert data["sHandle"] == C.hChapterDir
        assert status is False

    # qtbot.stop()
