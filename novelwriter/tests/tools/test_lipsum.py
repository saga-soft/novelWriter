"""
novelWriter - Lorem Ipsum Tool Tests
====================================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtGui import QAction

from novelwriter import SHARED
from novelwriter.core.project import NWProject
from novelwriter.enum import nwDocInsert
from novelwriter.tools.lipsum import GuiLipsum

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiLipsum_Main(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the Lorem Ipsum tool."""
    # Check that we cannot open when there is no project
    nwGUI.mainMenu.aLipsumText.activate(QAction.ActionEvent.Trigger)
    assert SHARED.findTopLevelWidget(GuiLipsum) is None

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwLipsum = GuiLipsum(nwGUI)

    # Generate paragraphs
    nwGUI.docEditor.setCursorPosition(100)  # End of document
    nwLipsum.paraCount.setValue(2)
    nwLipsum._doInsert()
    assert "Lorem ipsum" in nwLipsum.lipsumText

    # Generate random paragraph
    nwGUI.docEditor.setCursorPosition(1000)  # End of document
    nwLipsum.randSwitch.setChecked(True)
    nwLipsum.paraCount.setValue(1)
    nwLipsum._doInsert()
    assert len(nwLipsum.lipsumText) > 0

    nwLipsum.setObjectName("")
    nwLipsum.close()

    # Trigger insertion in document
    assert nwGUI.openDocument(C.hSceneDoc) is True
    nwGUI.docEditor.setCursorLine(3)
    with monkeypatch.context() as mp:
        mp.setattr(GuiLipsum, "exec", lambda *a: None)
        mp.setattr(GuiLipsum, "lipsumText", "FooBar")
        with qtbot.waitSignal(nwGUI.docEditor.textChanged):
            nwGUI.docEditor.insertText(nwDocInsert.LIPSUM)
        assert nwGUI.docEditor.getText() == "### New Scene\n\nFooBar"

    # qtbot.stop()
