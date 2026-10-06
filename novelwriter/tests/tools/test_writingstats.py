"""
novelWriter - Writing Stats Dialog Tests
========================================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

import json

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog

from novelwriter import SHARED
from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject
from novelwriter.tools.writingstats import GuiWritingStats
from novelwriter.types import QtMouseLeft

from tests.helpers import buildTestProject, checkDialogFreedOnClose
from tests.mocked import causeOSError


@pytest.mark.gui
def testGuiWritingStats_Main(qtbot, monkeypatch, nwGUI, projPath, tstPaths):
    """Test the full writing stats tool."""
    # Create a project to work on
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    project = SHARED.project
    assert nwGUI.saveProject()
    sessFile = projPath / "meta" / nwFiles.SESS_FILE

    # Open the Writing Stats dialog
    nwGUI.mainMenu.aWritingStats.activate(QAction.ActionEvent.Trigger)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiWritingStats) is not None, timeout=1000)

    sessLog = SHARED.findTopLevelWidget(GuiWritingStats)
    assert isinstance(sessLog, GuiWritingStats)

    # Test Loading
    # ============

    # No initial logfile
    assert not sessFile.is_file()
    assert list(project.session.iterRecords()) == []

    # Make an invalid logfile
    data = (
        '{"type": "initial", "offset": 123}\n'
        '{"type": "record", "start": "foo", "end": "bar", "novel": 840, "notes": 376, "idle": 394}'
    )
    sessFile.write_text(data, encoding="utf-8")
    sessLog._loadLogFile()
    assert sessLog.wordOffset == 123
    assert len(sessLog.logData) == 0

    # Make a test log file
    data = [
        project.session.createInitial(123),
        project.session.createRecord("2020-01-01 21:00:00", "2020-01-01 21:00:05", 6, 0, 0),
        project.session.createRecord("2020-01-03 21:00:00", "2020-01-03 21:00:15", 125, 0, 0),
        project.session.createRecord("2020-01-03 21:30:00", "2020-01-03 21:30:15", 125, 5, 0),
        project.session.createRecord("2020-01-06 21:00:00", "2020-01-06 21:00:10", 125, 5, 0),
    ]
    sessFile.write_text("".join(data), encoding="utf-8")
    sessLog._loadLogFile()
    assert sessLog.wordOffset == 123
    assert len(sessLog.logData) == 4

    # A record with an unrecognised type is skipped
    data = (
        '{"type": "initial", "offset": 123}\n'
        '{"type": "unknown"}\n'
        f"{project.session.createRecord('2020-01-01 21:00:00', '2020-01-01 21:00:05', 6, 0, 0)}"
    )
    sessFile.write_text(data, encoding="utf-8")
    sessLog._loadLogFile()
    assert len(sessLog.logData) == 1
    sessLog.closeDialog()

    # Grouping by day with no log data does nothing
    emptyLog = GuiWritingStats(nwGUI)
    assert emptyLog.logData == []
    qtbot.mouseClick(emptyLog.swtGroupByDay, QtMouseLeft)
    assert emptyLog.listBox.topLevelItemCount() == 0
    emptyLog.closeDialog()


@pytest.mark.gui
def testGuiWritingStats_Export(qtbot, monkeypatch, nwGUI, projPath, tstPaths):
    """Test the export feature."""
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda ss, tt, pp, options: (pp, ""))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    project = SHARED.project
    assert nwGUI.saveProject()
    sessFile = projPath / "meta" / nwFiles.SESS_FILE
    sessLog = GuiWritingStats(nwGUI)

    data = [
        project.session.createInitial(1075),
        project.session.createRecord("2021-01-31 19:00:00", "2021-01-31 19:30:00", 700, 375, 0),
        project.session.createRecord("2021-02-01 19:00:00", "2021-02-01 19:30:00", 700, 375, 10),
        project.session.createRecord("2021-02-01 20:00:00", "2021-02-01 20:30:00", 600, 275, 20),
        project.session.createRecord("2021-02-02 19:00:00", "2021-02-02 19:30:00", 750, 425, 30),
        project.session.createRecord("2021-02-02 20:00:00", "2021-02-02 20:30:00", 690, 365, 40),
        project.session.createRecord("2021-02-03 19:00:00", "2021-02-03 19:30:00", 680, 355, 50),
        project.session.createRecord("2021-02-04 19:00:00", "2021-02-04 19:30:00", 700, 375, 60),
        project.session.createRecord("2021-02-05 19:00:00", "2021-02-05 19:30:00", 500, 175, 70),
        project.session.createRecord("2021-02-06 19:00:00", "2021-02-06 19:30:00", 600, 275, 80),
        project.session.createRecord("2021-02-07 19:00:00", "2021-02-07 19:30:00", 600, 275, 90),
    ]
    sessFile.write_text("".join(data), encoding="utf-8")
    sessLog.populateGUI()

    # Make the saving fail
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
        assert not sessLog._saveData(sessLog.FMT_CSV)
        assert not sessLog._saveData(sessLog.FMT_JSON)
        assert not sessLog._saveData(None)  # type: ignore
        saveJSON, saveCSV = sessLog.saveMenu.actions()
        saveJSON.trigger()
        saveCSV.trigger()

    # Sort by time
    sessLog.listBox.sortByColumn(sessLog.C_TIME, Qt.SortOrder.AscendingOrder)

    assert sessLog.novelWords.text() == f"{600:n}"
    assert sessLog.notesWords.text() == f"{275:n}"
    assert sessLog.totalWords.text() == f"{875:n}"

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{300:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-120:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-20:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{40:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-400:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{200:n}"

    assert sessLog._saveData(sessLog.FMT_CSV)
    assert sessLog._saveData(sessLog.FMT_JSON)

    # Check the exported files
    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.load(inFile)

    assert jsonData == [
        {
            "date": "2021-01-31 19:00:00",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-01 20:00:00",
            "length": 1800.0,
            "newWords": -200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 20,
        },
        {
            "date": "2021-02-02 19:00:00",
            "length": 1800.0,
            "newWords": 300,
            "novelWords": 750,
            "noteWords": 425,
            "idleTime": 30,
        },
        {
            "date": "2021-02-02 20:00:00",
            "length": 1800.0,
            "newWords": -120,
            "novelWords": 690,
            "noteWords": 365,
            "idleTime": 40,
        },
        {
            "date": "2021-02-03 19:00:00",
            "length": 1800.0,
            "newWords": -20,
            "novelWords": 680,
            "noteWords": 355,
            "idleTime": 50,
        },
        {
            "date": "2021-02-04 19:00:00",
            "length": 1800.0,
            "newWords": 40,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-05 19:00:00",
            "length": 1800.0,
            "newWords": -400,
            "novelWords": 500,
            "noteWords": 175,
            "idleTime": 70,
        },
        {
            "date": "2021-02-06 19:00:00",
            "length": 1800.0,
            "newWords": 200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
    ]

    # I/O Error
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert not sessLog._loadLogFile()
        assert not sessLog._saveData(sessLog.FMT_CSV)


@pytest.mark.gui
def testGuiWritingStats_Filters(qtbot, monkeypatch, nwGUI, projPath, tstPaths):
    """Test the filters."""
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda ss, tt, pp, options: (pp, ""))

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    project = SHARED.project
    assert nwGUI.saveProject()
    sessFile = projPath / "meta" / nwFiles.SESS_FILE
    sessLog = GuiWritingStats(nwGUI)

    data = [
        project.session.createInitial(1075),
        project.session.createRecord("2021-01-31 19:00:00", "2021-01-31 19:30:00", 700, 375, 0),
        project.session.createRecord("2021-02-01 19:00:00", "2021-02-01 19:30:00", 700, 375, 10),
        project.session.createRecord("2021-02-01 20:00:00", "2021-02-01 20:30:00", 600, 275, 20),
        project.session.createRecord("2021-02-02 19:00:00", "2021-02-02 19:30:00", 750, 425, 30),
        project.session.createRecord("2021-02-02 20:00:00", "2021-02-02 20:30:00", 690, 365, 40),
        project.session.createRecord("2021-02-03 19:00:00", "2021-02-03 19:30:00", 680, 355, 50),
        project.session.createRecord("2021-02-04 19:00:00", "2021-02-04 19:30:00", 700, 375, 60),
        project.session.createRecord("2021-02-05 19:00:00", "2021-02-05 19:30:00", 500, 175, 70),
        project.session.createRecord("2021-02-06 19:00:00", "2021-02-06 19:30:00", 600, 275, 80),
        project.session.createRecord("2021-02-07 19:00:00", "2021-02-07 19:30:00", 600, 275, 90),
    ]
    sessFile.write_text("".join(data), encoding="utf-8")
    sessLog.populateGUI()
    sessLog.listBox.sortByColumn(sessLog.C_TIME, Qt.SortOrder.AscendingOrder)

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{300:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-120:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-20:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{40:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-400:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{200:n}"

    # No Novel Files
    qtbot.mouseClick(sessLog.swtIncNovel, QtMouseLeft)
    assert sessLog._saveData(sessLog.FMT_JSON)

    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.loads(inFile.read())

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-100:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{150:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-60:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-10:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{20:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{100:n}"

    assert jsonData == [
        {
            "date": "2021-01-31 19:00:00",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-01 20:00:00",
            "length": 1800.0,
            "newWords": -100,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 20,
        },
        {
            "date": "2021-02-02 19:00:00",
            "length": 1800.0,
            "newWords": 150,
            "novelWords": 750,
            "noteWords": 425,
            "idleTime": 30,
        },
        {
            "date": "2021-02-02 20:00:00",
            "length": 1800.0,
            "newWords": -60,
            "novelWords": 690,
            "noteWords": 365,
            "idleTime": 40,
        },
        {
            "date": "2021-02-03 19:00:00",
            "length": 1800.0,
            "newWords": -10,
            "novelWords": 680,
            "noteWords": 355,
            "idleTime": 50,
        },
        {
            "date": "2021-02-04 19:00:00",
            "length": 1800.0,
            "newWords": 20,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-05 19:00:00",
            "length": 1800.0,
            "newWords": -200,
            "novelWords": 500,
            "noteWords": 175,
            "idleTime": 70,
        },
        {
            "date": "2021-02-06 19:00:00",
            "length": 1800.0,
            "newWords": 100,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
    ]

    # No Note Files
    qtbot.mouseClick(sessLog.swtIncNovel, QtMouseLeft)
    qtbot.mouseClick(sessLog.swtIncNotes, QtMouseLeft)
    assert sessLog._saveData(sessLog.FMT_JSON)

    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.load(inFile)

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-100:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{150:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-60:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-10:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{20:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{100:n}"

    assert jsonData == [
        {
            "date": "2021-01-31 19:00:00",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-01 20:00:00",
            "length": 1800.0,
            "newWords": -100,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 20,
        },
        {
            "date": "2021-02-02 19:00:00",
            "length": 1800.0,
            "newWords": 150,
            "novelWords": 750,
            "noteWords": 425,
            "idleTime": 30,
        },
        {
            "date": "2021-02-02 20:00:00",
            "length": 1800.0,
            "newWords": -60,
            "novelWords": 690,
            "noteWords": 365,
            "idleTime": 40,
        },
        {
            "date": "2021-02-03 19:00:00",
            "length": 1800.0,
            "newWords": -10,
            "novelWords": 680,
            "noteWords": 355,
            "idleTime": 50,
        },
        {
            "date": "2021-02-04 19:00:00",
            "length": 1800.0,
            "newWords": 20,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-05 19:00:00",
            "length": 1800.0,
            "newWords": -200,
            "novelWords": 500,
            "noteWords": 175,
            "idleTime": 70,
        },
        {
            "date": "2021-02-06 19:00:00",
            "length": 1800.0,
            "newWords": 100,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
    ]

    # No Negative Entries
    qtbot.mouseClick(sessLog.swtIncNotes, QtMouseLeft)
    qtbot.mouseClick(sessLog.swtHideNegative, QtMouseLeft)
    assert sessLog._saveData(sessLog.FMT_JSON)

    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.load(inFile)

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{300:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{40:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{200:n}"

    assert jsonData == [
        {
            "date": "2021-01-31 19:00:00",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-02 19:00:00",
            "length": 1800.0,
            "newWords": 300,
            "novelWords": 750,
            "noteWords": 425,
            "idleTime": 30,
        },
        {
            "date": "2021-02-04 19:00:00",
            "length": 1800.0,
            "newWords": 40,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-06 19:00:00",
            "length": 1800.0,
            "newWords": 200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
    ]

    # Un-hide Zero Entries
    qtbot.mouseClick(sessLog.swtHideNegative, QtMouseLeft)
    qtbot.mouseClick(sessLog.swtHideZeros, QtMouseLeft)
    assert sessLog._saveData(sessLog.FMT_JSON)

    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.load(inFile)

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{0:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{300:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-120:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-20:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{40:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-400:n}"

    item = sessLog.listBox.topLevelItem(8)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{200:n}"

    item = sessLog.listBox.topLevelItem(9)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{0:n}"

    assert jsonData == [
        {
            "date": "2021-01-31 19:00:00",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-01 19:00:00",
            "length": 1800.0,
            "newWords": 0,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 10,
        },
        {
            "date": "2021-02-01 20:00:00",
            "length": 1800.0,
            "newWords": -200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 20,
        },
        {
            "date": "2021-02-02 19:00:00",
            "length": 1800.0,
            "newWords": 300,
            "novelWords": 750,
            "noteWords": 425,
            "idleTime": 30,
        },
        {
            "date": "2021-02-02 20:00:00",
            "length": 1800.0,
            "newWords": -120,
            "novelWords": 690,
            "noteWords": 365,
            "idleTime": 40,
        },
        {
            "date": "2021-02-03 19:00:00",
            "length": 1800.0,
            "newWords": -20,
            "novelWords": 680,
            "noteWords": 355,
            "idleTime": 50,
        },
        {
            "date": "2021-02-04 19:00:00",
            "length": 1800.0,
            "newWords": 40,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-05 19:00:00",
            "length": 1800.0,
            "newWords": -400,
            "novelWords": 500,
            "noteWords": 175,
            "idleTime": 70,
        },
        {
            "date": "2021-02-06 19:00:00",
            "length": 1800.0,
            "newWords": 200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
        {
            "date": "2021-02-07 19:00:00",
            "length": 1800.0,
            "newWords": 0,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 90,
        },
    ]

    # Toggle Idle Time
    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_IDLE) == "4\u202f%"

    qtbot.mouseClick(sessLog.swtShowIdleTime, QtMouseLeft)

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_IDLE) == "00:01:10"

    # Group by Day
    qtbot.mouseClick(sessLog.swtGroupByDay, QtMouseLeft)
    assert sessLog._saveData(sessLog.FMT_JSON)

    jsonStats = tstPaths.tmpDir / "sessionStats.json"
    with open(jsonStats, mode="r", encoding="utf-8") as inFile:
        jsonData = json.load(inFile)

    item = sessLog.listBox.topLevelItem(0)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{1:n}"

    item = sessLog.listBox.topLevelItem(1)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-200:n}"

    item = sessLog.listBox.topLevelItem(2)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{180:n}"

    item = sessLog.listBox.topLevelItem(3)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-20:n}"

    item = sessLog.listBox.topLevelItem(4)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{40:n}"

    item = sessLog.listBox.topLevelItem(5)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{-400:n}"

    item = sessLog.listBox.topLevelItem(6)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{200:n}"

    item = sessLog.listBox.topLevelItem(7)
    assert item is not None
    assert item.text(sessLog.C_COUNT) == f"{0:n}"

    assert jsonData == [
        {
            "date": "2021-01-31",
            "length": 1800.0,
            "newWords": 1,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 0,
        },
        {
            "date": "2021-02-01",
            "length": 3600.0,
            "newWords": -200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 30,
        },
        {
            "date": "2021-02-02",
            "length": 3600.0,
            "newWords": 180,
            "novelWords": 690,
            "noteWords": 365,
            "idleTime": 70,
        },
        {
            "date": "2021-02-03",
            "length": 1800.0,
            "newWords": -20,
            "novelWords": 680,
            "noteWords": 355,
            "idleTime": 50,
        },
        {
            "date": "2021-02-04",
            "length": 1800.0,
            "newWords": 40,
            "novelWords": 700,
            "noteWords": 375,
            "idleTime": 60,
        },
        {
            "date": "2021-02-05",
            "length": 1800.0,
            "newWords": -400,
            "novelWords": 500,
            "noteWords": 175,
            "idleTime": 70,
        },
        {
            "date": "2021-02-06",
            "length": 1800.0,
            "newWords": 200,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 80,
        },
        {
            "date": "2021-02-07",
            "length": 1800.0,
            "newWords": 0,
            "novelWords": 600,
            "noteWords": 275,
            "idleTime": 90,
        },
    ]

    # qtbot.stop()

    sessLog.closeDialog()
    nwGUI.closeProject()


@pytest.mark.gui
def testGuiWritingStats_MemoryLeakRegression(qtbot, nwGUI, projPath):
    """Test that the dialog is freed when it is closed."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    checkDialogFreedOnClose(qtbot, lambda: GuiWritingStats(nwGUI))
