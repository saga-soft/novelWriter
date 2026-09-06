"""
novelWriter - GUI Story View Tests
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

from shutil import copyfile

import pytest

from PyQt6.QtWidgets import QFileDialog

from novelwriter.enum import nwView

from tests.helpers import cmpFiles


@pytest.mark.gui
def testStoryView_ExportData(monkeypatch, nwGUI, prjLipsum, fncPath, tstPaths):
    """Test exporting the story view outline data to a CSV file."""
    assert nwGUI.openProject(prjLipsum)
    nwGUI.rebuildIndex()
    nwGUI._changeView(nwView.STORY)

    storyView = nwGUI.storyView
    csvFile = fncPath / "outline.csv"

    # Cancelling the save dialog writes nothing
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
        storyView.exportData.click()
    assert not csvFile.exists()

    # Export the outline data to a CSV file
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(csvFile), ""))
        storyView.exportData.click()
    assert csvFile.exists()

    testFile = tstPaths.outDir / "guiStoryView_export.csv"
    compFile = tstPaths.refDir / "guiStoryView_export.csv"
    copyfile(csvFile, testFile)
    assert cmpFiles(testFile, compFile)
