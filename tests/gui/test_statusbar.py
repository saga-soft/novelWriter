"""
novelWriter - GUI Status Bar Tests
==================================

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

import time

from pathlib import Path

import pytest

from pytestqt.qtbot import QtBot

from novelwriter import CONFIG, SHARED
from novelwriter.core.project import NWProject
from novelwriter.guimain import GuiMain

from tests.helpers import C, MockRnd, buildTestProject


@pytest.mark.gui
def testGuiStatusBar_Main(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    nwGUI: GuiMain,
    projPath: Path,
    mockRnd: MockRnd,
):
    """Test the various features of the status bar."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    cHandle = SHARED.project.newFile("A Note", C.hCharRoot)
    newDoc = SHARED.project.storage.getDocument(cHandle)
    newDoc.writeDocument("# A Note\n\n")
    nwGUI.rebuildIndex()

    status = nwGUI.mainStatus

    # Reference Time
    refTime = time.time()
    status.setRefTime(refTime)
    assert status._refTime == refTime

    # Project Status
    status.setProjectStatus(None)
    assert status.projIcon.state is None
    assert status.projIcon.accessibleName() == "Project"
    status.setProjectStatus(False)
    assert status.projIcon.state is False
    assert status.projIcon.accessibleName() == "Project: Unsaved"
    status.setProjectStatus(True)
    assert status.projIcon.state is True
    assert status.projIcon.accessibleName() == "Project: Saved"
    assert status.projIcon.toolTip() == "Project: Saved"

    # Document Status
    status.setDocumentStatus(None)
    assert status.docIcon.state is None
    status.setDocumentStatus(False)
    assert status.docIcon.state is False
    status.setDocumentStatus(True)
    assert status.docIcon.state is True
    assert status.docIcon.accessibleName() == "Editor: Saved"

    # Idle Status
    CONFIG.stopWhenIdle = False
    status.setUserIdle(True)
    status.updateTime()
    assert status._userIdle is False
    assert status.timeText.text() == "00:00:00"

    CONFIG.stopWhenIdle = True
    status.setUserIdle(True)
    status.updateTime(5)
    assert status._userIdle is True
    assert status.timeText.text() != "00:00:00"

    status.setUserIdle(False)
    status.updateTime(5)
    assert status._userIdle is False
    assert status.timeText.text() != "00:00:00"

    # Show/Hide Timer
    assert status.timeText.isVisible() is True
    assert CONFIG.showSessionTime is True
    status._onClickTimerLabel()
    assert status.timeText.isVisible() is False
    assert CONFIG.showSessionTime is False
    status._onClickTimerLabel()
    assert status.timeText.isVisible() is True
    assert CONFIG.showSessionTime is True

    # Language
    status.setLanguage("None", "None")
    assert status.langText.text() == "None"
    status.setLanguage("en", "None")
    assert status.langText.text() == "American English"

    # Project Stats
    SHARED.project.data._initCounts = [0, 0, 0, 0]
    CONFIG.incNotesWCount = False
    nwGUI._lastTotalCount = 0
    nwGUI._updateStatusWordCount()
    assert status.statsText.text() == "Words: 9 (+9)"

    # Update again, but through time tick
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.guimain.time", lambda *a: 50.0)
        CONFIG.incNotesWCount = True
        nwGUI._lastTotalCount = 0
        nwGUI._timeTick()
        assert status.statsText.text() == "Words: 11 (+11)"

    # Switch to character count
    CONFIG.useCharCount = True
    status.initSettings()
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.guimain.time", lambda *a: 50.0)
        CONFIG.incNotesWCount = True
        nwGUI._lastTotalCount = 0
        nwGUI._timeTick()
        assert status.statsText.text() == "Characters: 46 (+46)"
        CONFIG.incNotesWCount = False
        nwGUI._lastTotalCount = 0
        nwGUI._timeTick()
        assert status.statsText.text() == "Characters: 40 (+40)"

    # Goal Progress Bars
    SHARED.project.data.setDailyTarget(500, False)
    SHARED.project.data.setProjectTarget(2000, None, False)
    status.updateGoals(100, 50)
    assert status.dayProg.isVisible() is True
    assert status.dayProg.maximum() == 500
    assert status.dayProg.value() == 50
    assert status.projProg.isVisible() is True
    assert status.projProg.maximum() == 2000
    assert status.projProg.value() == 100

    # Reset Daily Progress
    assert status.dayReset.isVisible() is True
    SHARED.project.data.resetDailyProgress()
    SHARED.project.data.setDailyProgress(150, 150)
    assert SHARED.project.data.dailyProgress == 150

    # Declining the confirmation leaves the progress untouched
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "question", lambda *a, **k: False)
        status._resetDailyProgress()
    assert SHARED.project.data.dailyProgress == 150

    # Confirming resets the progress to zero
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "question", lambda *a, **k: True)
        status._resetDailyProgress()
    assert SHARED.project.data.dailyProgress == 0

    # Focus Mode hides the statusbar by default
    status.setFocusMode(True)
    assert status.isVisible() is False
    status.setFocusMode(False)
    assert status.isVisible() is True

    # Focus Mode with goals only shows the goals
    CONFIG.goalInFocusMode = True
    status.setFocusMode(True)
    assert status.isVisible() is True
    assert status.dayProg.isVisible() is True
    assert status.projProg.isVisible() is True
    assert status.messageBox.isVisible() is False
    assert status.langText.isVisible() is False
    assert status.statsText.isVisible() is False
    assert status.timeText.isVisible() is False

    # Without goals, the statusbar is hidden
    SHARED.project.data.setDailyTarget(0, False)
    SHARED.project.data.setProjectTarget(0, None, False)
    status.updateGoals(100, 50)
    assert status.isVisible() is False
    SHARED.project.data.setProjectTarget(2000, None, False)
    status.updateGoals(100, 50)
    assert status.isVisible() is True

    # Changing the setting in Focus Mode is applied
    CONFIG.goalInFocusMode = False
    status.initSettings()
    assert status.isVisible() is False
    CONFIG.goalInFocusMode = True
    status.initSettings()
    assert status.isVisible() is True

    # Leaving Focus Mode respects the hidden timer
    CONFIG.showSessionTime = False
    status.setFocusMode(False)
    assert status.isVisible() is True
    assert status.messageBox.isVisible() is True
    assert status.langText.isVisible() is True
    assert status.statsText.isVisible() is True
    assert status.timeIcon.isVisible() is True
    assert status.timeText.isVisible() is False

    # Set message
    status.messageBox.setMessage("Hi!", "info", 10000)
    assert status.messageBox._text.text() == "Hi!"
    status.messageBox.clearMessage()
    assert status.messageBox._text.text() == ""

    # qtbot.stop()
