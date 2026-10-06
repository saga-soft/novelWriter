"""
novelWriter - Session Log Tests
===============================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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
from time import sleep

import pytest

from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject
from novelwriter.core.sessions import SessionLog

from tests.helpers import buildTestProject
from tests.mocked import causeOSError


@pytest.mark.core
def testNWSessionLog_Main(monkeypatch, mockGUI, fncPath):
    """Test log file handling of the SessionLog class."""
    project = NWProject()
    buildTestProject(project, fncPath)

    logFile = project.storage.getMetaFile(nwFiles.SESS_FILE)
    assert isinstance(logFile, Path)

    # Set some mock word counts
    project.data.setInitCounts(50, 60, 500, 600)
    project.data.setCurrCounts(160, 150, 1600, 1500)

    # The project init should already have created the session
    sessLog = project.session
    assert isinstance(sessLog, SessionLog)
    assert sessLog.start > 0.0

    # Starting the session again should reset the timer
    currTime = sessLog.start
    sleep(0.015)  # Make sure we don't hit clock resolution issues on Windows
    sessLog.startSession()
    assert sessLog.start > currTime

    # There should not be a logfile
    assert not logFile.exists()
    assert len(list(sessLog.iterRecords())) == 0

    # Create the initial and first records
    assert sessLog.appendSession(0.8) is True
    assert logFile.exists()  # Logfile now exists
    records = list(sessLog.iterRecords())
    assert len(records) == 2
    assert records[0]["type"] == "initial"
    assert records[0]["offset"] == 110  # Sum of initial word counts
    assert records[1]["type"] == "record"
    assert records[1]["novel"] == 160
    assert records[1]["notes"] == 150
    assert records[1]["cnovel"] == 1600
    assert records[1]["cnotes"] == 1500
    assert records[1]["idle"] == 1  # Should be rounded to full seconds

    # Adding another record without changing word count should do nothing
    project.data.setInitCounts(160, 150, 1600, 1500)
    project.data.setCurrCounts(160, 150, 1600, 1500)
    assert sessLog.appendSession(1.6) is False
    assert len(list(sessLog.iterRecords())) == 2

    # But adding when count has changed should
    project.data.setInitCounts(160, 150, 1600, 1500)
    project.data.setCurrCounts(270, 240, 2700, 2400)
    sessLog._start -= 350.0  # Backdate the session start to allow logging
    assert sessLog.appendSession(1.6) is True
    records = list(sessLog.iterRecords())
    assert len(records) == 3
    assert records[2]["novel"] == 270
    assert records[2]["notes"] == 240
    assert records[2]["idle"] == 2  # Should be rounded to full seconds

    # Make file path unresolvable, and try appending another record
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert sessLog.appendSession(1.6) is False
    assert len(list(sessLog.iterRecords())) == 3

    # Make the file open fail, and check that it's handled
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert sessLog.appendSession(1.6) is False
    assert len(list(sessLog.iterRecords())) == 3

    # Make the file load fail, and check that it's handled
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert len(list(sessLog.iterRecords())) == 0

    # Make file path unresolvable
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert len(list(sessLog.iterRecords())) == 0
