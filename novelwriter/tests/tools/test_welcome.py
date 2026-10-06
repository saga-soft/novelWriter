"""
novelWriter - Welcome Dialog Tests
==================================

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

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog, QMenu

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwFiles
from novelwriter.core.coretools import ProjectBuilder
from novelwriter.core.projectdata import ProjectData
from novelwriter.enum import nwItemClass
from novelwriter.shared import _GuiAlert
from novelwriter.tools.welcome import SAMPLE_KEY, SAMPLE_NAME, GuiWelcome, _ProjectListEntry
from novelwriter.types import (
    QtAccessibleTextRole,
    QtDecorationRole,
    QtDisplayRole,
    QtFontRole,
    QtKeyDown,
    QtKeyLeft,
    QtKeyRight,
    QtKeyUp,
    QtMouseLeft,
    QtTextAlignmentRole,
    QtToolTipRole,
    QtUserRole,
)


@pytest.mark.gui
def testGuiWelcome_Main(qtbot, monkeypatch, nwGUI, fncPath):
    """Test the main Welcome window."""
    welcome = GuiWelcome(nwGUI)
    with qtbot.waitExposed(welcome):
        # This ensures the paint event is executed
        welcome.show()

    # By default, the project list is shown
    assert welcome.mainStack.currentIndex() == 0

    # Show the new project form
    welcome.btnNew.click()
    assert welcome.mainStack.currentIndex() == 1

    # Revert to project list
    welcome.btnList.click()
    assert welcome.mainStack.currentIndex() == 0

    # Cancelling the browse dialog does nothing
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "getProjectFolder", lambda *a, **k: None)
        with qtbot.assertNotEmitted(welcome.openProjectRequest, wait=100):
            welcome.btnBrowse.click()

    # Open a project
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "getProjectFolder", lambda *a, **k: fncPath)
        with qtbot.waitSignal(welcome.openProjectRequest) as signal:
            welcome.btnBrowse.click()
        assert signal.args
        assert signal.args[0] == fncPath

    # Opening the selected item only applies while on the Open tab
    welcome.btnNew.click()
    assert welcome.mainStack.currentIndex() == 1
    with monkeypatch.context() as mp:
        openMock = MagicMock()
        mp.setattr(welcome.tabOpen, "openSelectedItem", openMock)
        welcome._openSelectedItem()
        assert openMock.called is False
    welcome.btnList.click()
    assert welcome.mainStack.currentIndex() == 0

    # A non-Path value emits nothing, but still closes the dialog
    with monkeypatch.context() as mp:
        mp.setattr(welcome, "close", lambda *a: None)
        with qtbot.assertNotEmitted(welcome.openProjectRequest, wait=100):
            welcome._openProjectPath(None)  # type: ignore

    # Create sample project when list is empty
    assert welcome.tabOpen.listModel.rowCount() == 1
    selected = welcome.tabOpen.listModel.index(0, 0).data()
    assert selected[0] == SAMPLE_NAME
    assert selected[1] == SAMPLE_KEY
    welcome.tabOpen._selectFirstItem()

    # A folder must be selected
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: None)
        welcome.tabOpen._processOpenProjectRequest(SAMPLE_KEY)

    assert SHARED.lastAlert[0] == "You must select a location for the example project."

    # Successful
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: fncPath)
        welcome.tabOpen._processOpenProjectRequest(SAMPLE_KEY)

    assert (fncPath / SAMPLE_NAME).is_dir()

    # But can't create a duplicate
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: fncPath)
        welcome.tabOpen._processOpenProjectRequest(SAMPLE_KEY)

    assert SHARED.lastAlert[0] == "The target folder already exists. Please choose another folder."

    # qtbot.stop()
    welcome.close()


@pytest.mark.gui
def testGuiWelcome_Open(qtbot, monkeypatch, nwGUI):
    """Test the open tab in the Welcome window."""
    monkeypatch.setattr(QMenu, "exec", lambda *a: None)
    monkeypatch.setattr(QMenu, "setParent", lambda *a: None)

    data1 = ProjectData(SHARED.project)
    data2 = ProjectData(SHARED.project)

    data1.setUuid(None)
    data2.setUuid(None)
    data1.setName("Project One")
    data2.setName("Project Two")
    data1.setCurrCounts(12345, 0)
    data2.setCurrCounts(54321, 0)

    CONFIG.recentProjects.update("/stuff/project_one", data1, 1690000000)
    CONFIG.recentProjects.update("/stuff/project_two", data2, 1700000000)
    dateOne = CONFIG.localDate(datetime.fromtimestamp(1700000000))
    dateTwo = CONFIG.localDate(datetime.fromtimestamp(1690000000))

    welcome = GuiWelcome(nwGUI)
    with qtbot.waitExposed(welcome):
        welcome.show()

    assert welcome.mainStack.currentIndex() == 0
    tabOpen = welcome.tabOpen
    listModel = tabOpen.listModel
    vPort = tabOpen.listWidget.viewport()

    posOne = tabOpen.listWidget.rectForIndex(listModel.createIndex(0, 0)).center()
    posTwo = tabOpen.listWidget.rectForIndex(listModel.createIndex(1, 0)).center()

    # Check items, which should be in opposite order
    entry = listModel.data(listModel.createIndex(0, 0), QtDisplayRole)
    assert isinstance(entry, _ProjectListEntry)
    assert entry.title == "Project Two"
    assert entry.path == "/stuff/project_two"
    assert entry.details == f"Last Opened: {dateOne}, Word Count: 54.3\u2009k"
    assert entry.accessible == f"Project Two, Last Opened {dateOne}, Word Count 54.3\u2009k"
    assert listModel.data(listModel.createIndex(0, 0), QtAccessibleTextRole) == entry.accessible

    entry = listModel.data(listModel.createIndex(1, 0), QtDisplayRole)
    assert isinstance(entry, _ProjectListEntry)
    assert entry.title == "Project One"
    assert entry.path == "/stuff/project_one"
    assert entry.details == f"Last Opened: {dateTwo}, Word Count: 12.3\u2009k"
    assert entry.accessible == f"Project One, Last Opened {dateTwo}, Word Count 12.3\u2009k"
    assert listModel.data(listModel.createIndex(1, 0), QtAccessibleTextRole) == entry.accessible

    # Check other model data roles
    assert listModel.data(listModel.createIndex(0, 0), QtDecorationRole) is None
    assert listModel.data(listModel.createIndex(0, 0), QtFontRole) is None
    assert listModel.data(listModel.createIndex(0, 0), QtTextAlignmentRole) is None
    assert listModel.data(listModel.createIndex(0, 0), QtToolTipRole) is None
    assert listModel.data(listModel.createIndex(0, 0), QtUserRole) is None

    # Check out of range index
    assert listModel.data(listModel.createIndex(2, 0), QtDisplayRole) is None

    # Change selection with arrow keys
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"
    qtbot.keyClick(tabOpen, QtKeyLeft)  # Does nothing
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"
    qtbot.keyClick(tabOpen, QtKeyRight)  # Does nothing
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"
    qtbot.keyClick(tabOpen, QtKeyDown)  # Selects lower
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_one"
    qtbot.keyClick(tabOpen, QtKeyDown)  # Does nothing (already on last)
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_one"
    qtbot.keyClick(tabOpen, QtKeyUp)  # Selects upper
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"
    qtbot.keyClick(tabOpen, QtKeyUp)  # Does nothing (already on first)
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"

    # Single click item
    qtbot.mouseClick(vPort, QtMouseLeft, pos=posOne, delay=10)
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_two"
    qtbot.mouseClick(vPort, QtMouseLeft, pos=posTwo, delay=10)
    assert tabOpen.selectedPath.text() == "Path: /stuff/project_one"

    # Double click item
    qtbot.mouseClick(vPort, QtMouseLeft, pos=posTwo, delay=10)
    with monkeypatch.context() as mp:
        mp.setattr(welcome, "close", lambda *a: None)
        with qtbot.waitSignal(welcome.openProjectRequest, timeout=5000) as signal:
            qtbot.mouseDClick(vPort, QtMouseLeft, pos=posTwo, delay=10)
        assert signal.args
        assert signal.args[0] == Path("/stuff/project_one")

    # Press open button
    qtbot.mouseClick(vPort, QtMouseLeft, pos=posTwo, delay=10)
    with monkeypatch.context() as mp:
        mp.setattr(welcome, "close", lambda *a: None)
        with qtbot.waitSignal(welcome.openProjectRequest, timeout=5000) as signal:
            welcome.btnOpen.click()
        assert signal.args
        assert signal.args[0] == Path("/stuff/project_one")

    # Context Menu
    def getMenuForPos(pos: QPoint) -> QMenu | None:
        tabOpen._openContextMenu(pos)
        for obj in tabOpen.children():
            if isinstance(obj, QMenu) and obj.objectName() == "ContextMenu":
                return obj
        return None

    qtbot.mouseClick(vPort, QtMouseLeft, pos=posOne, delay=10)
    ctxMenu = getMenuForPos(posOne)
    assert isinstance(ctxMenu, QMenu)
    assert ctxMenu.actions()[0].text() == "Open Project"
    assert ctxMenu.actions()[1].text() == "Remove Project"

    # Open item from context menu
    with monkeypatch.context() as mp:
        mp.setattr(welcome, "close", lambda *a: None)
        with qtbot.waitSignal(welcome.openProjectRequest, timeout=5000) as signal:
            ctxMenu.actions()[0].activate(QAction.ActionEvent.Trigger)
        assert signal.args
        assert signal.args[0] == Path("/stuff/project_two")

    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Delete item from context menu
    ctxMenu = getMenuForPos(posOne)
    assert isinstance(ctxMenu, QMenu)
    ctxMenu.actions()[1].activate(QAction.ActionEvent.Trigger)
    assert len(CONFIG.recentProjects.listEntries()) == 1

    ctxMenu.setObjectName("")
    ctxMenu.deleteLater()

    # Check removing entry error handling
    assert listModel.data(listModel.createIndex(1, 0), QtDisplayRole) is None
    assert listModel.removeEntry(listModel.createIndex(1, 0)) is False

    # With nothing selected, opening or deleting the selection does nothing
    tabOpen.listWidget.clearSelection()
    tabOpen.listWidget.selectionModel().clearCurrentIndex()  # type: ignore
    with qtbot.assertNotEmitted(welcome.openProjectRequest, wait=100):
        tabOpen.openSelectedItem()

    countBefore = len(CONFIG.recentProjects.listEntries())
    tabOpen._deleteSelectedItem()
    assert len(CONFIG.recentProjects.listEntries()) == countBefore

    # Double-clicking an invalid index does nothing
    with qtbot.assertNotEmitted(welcome.openProjectRequest, wait=100):
        tabOpen._projectDoubleClicked(listModel.createIndex(99, 0))

    # Declining the delete confirmation leaves the entry in place
    qtbot.mouseClick(vPort, QtMouseLeft, pos=posOne, delay=10)
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        countBefore = len(CONFIG.recentProjects.listEntries())
        tabOpen._deleteSelectedItem()
        assert len(CONFIG.recentProjects.listEntries()) == countBefore

    # qtbot.stop()
    welcome.close()


@pytest.mark.gui
def testGuiWelcome_New(qtbot, caplog, monkeypatch, nwGUI, fncPath):
    """Test the new project tab in the Welcome window."""
    welcome = GuiWelcome(nwGUI)
    with qtbot.waitExposed(welcome):
        welcome.show()

    welcome.btnNew.click()
    assert welcome.mainStack.currentIndex() == 1
    tabNew = welcome.tabNew
    newForm = tabNew.projectForm

    # Cancelling the browse dialog leaves the path unchanged
    pathBefore = newForm.projPath.text()
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: "")
        newForm.browsePath.click()
        assert newForm.projPath.text() == pathBefore

    # Populate the path
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: fncPath)
        newForm.browsePath.click()
        assert newForm.projPath.text() == str(fncPath)

    # Turning off root folders should disable notes switch
    newForm.addNotes.setChecked(True)
    newForm.addPlot.setChecked(False)
    newForm.addChar.setChecked(False)
    newForm.addWorld.setChecked(False)
    newForm._syncSwitches()
    assert newForm.addNotes.isChecked() is False

    # With at least one root folder enabled, the notes switch is untouched
    newForm.addNotes.setChecked(True)
    newForm.addPlot.setChecked(True)
    newForm._syncSwitches()
    assert newForm.addNotes.isChecked() is True
    newForm.addPlot.setChecked(False)

    # Change fill info to sample
    newForm.fillSample.trigger()
    assert newForm._fillMode == newForm.FILL_SAMPLE
    assert newForm.projFill.text() == "Example Project"
    assert newForm.extraWidget.isVisible() is False

    # Cancelling the template picker leaves the fill mode unchanged
    fillModeBefore = newForm._fillMode
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "getProjectPath", lambda *a, **k: None)
        newForm.fillCopy.trigger()
        assert newForm._fillMode == fillModeBefore

    # Change fill info to template
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "getProjectPath", lambda *a, **k: fncPath)
        newForm.fillCopy.trigger()
        assert newForm._fillMode == newForm.FILL_COPY
        assert newForm.projFill.text() == f"Template: {fncPath}"
        assert newForm.extraWidget.isVisible() is False

    # Change back to fill blank using the menu
    newForm.fillMenu.actions()[0].activate(QAction.ActionEvent.Trigger)
    assert newForm._fillMode == newForm.FILL_BLANK
    assert newForm.projFill.text() == "Fresh Project"
    assert newForm.extraWidget.isVisible() is True

    # Creating a project without a name, pops an error
    caplog.clear()
    welcome.btnCreate.click()
    assert "A project name is required." in caplog.text

    # Set some more values, and extract data
    projPath = fncPath / "Test Project"
    newForm.projName.setText("Test Project")
    newForm.projAuthor.setText("Jane Smith")
    newForm.addPlot.setChecked(True)
    newForm.addChar.setChecked(True)
    newForm.addWorld.setChecked(True)
    newForm.addNotes.setChecked(True)
    newForm.numChapters.setValue(10)
    newForm.numScenes.setValue(6)
    assert newForm.getProjectData() == {
        "name": "Test Project",
        "author": "Jane Smith",
        "path": str(projPath),
        "blank": True,
        "sample": False,
        "template": None,
        "chapters": 10,
        "scenes": 6,
        "roots": [nwItemClass.PLOT, nwItemClass.CHARACTER, nwItemClass.WORLD],
        "notes": True,
    }

    # A failed build does not request opening the project
    with monkeypatch.context() as mp:
        mp.setattr(ProjectBuilder, "buildProject", lambda *a, **k: False)
        with qtbot.assertNotEmitted(welcome.openProjectRequest, wait=100):
            welcome.btnCreate.click()
    assert not (projPath / nwFiles.PROJ_FILE).exists()

    # Create a project with these values
    with qtbot.waitSignal(welcome.openProjectRequest, timeout=5000) as signal:
        welcome.btnCreate.click()
    assert signal.args
    assert signal.args[0] == projPath
    assert (projPath / nwFiles.PROJ_FILE).exists()

    # qtbot.stop()
    welcome.close()
