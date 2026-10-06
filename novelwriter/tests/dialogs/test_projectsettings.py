"""
novelWriter - Project Settings Dialog Tests
===========================================

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

from datetime import date

import pytest

from PyQt6.QtCore import QDate
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import QColorDialog, QFileDialog, QToolButton

from novelwriter import CONFIG, SHARED
from novelwriter.core.project import NWProject
from novelwriter.core.spellcheck import SpellEnchant
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.dialogs.projectsettings import GuiProjectSettings
from novelwriter.enum import nwItemType, nwStatusShape
from novelwriter.types import QtAccepted, QtMouseLeft

from tests.helpers import C, buildTestProject, checkDialogFreedOnClose
from tests.mocked import causeOSError

KEY_DELAY = 1


@pytest.mark.gui
def testGuiProjectSettings_Dialog(qtbot, monkeypatch, nwGUI):
    """Test the main dialog class. Saving settings is not tested in this
    test, but are instead tested in the individual tab tests.
    """
    # Block the GUI blocking thread
    monkeypatch.setattr(GuiProjectSettings, "exec", lambda *a: None)
    monkeypatch.setattr(GuiProjectSettings, "result", lambda *a: QtAccepted)

    # Check that we cannot open when there is no project
    nwGUI.mainMenu.aProjectSettings.activate(QAction.ActionEvent.Trigger)
    assert SHARED.findTopLevelWidget(GuiProjectSettings) is None

    # Pretend we have a project
    SHARED.project._valid = True
    SHARED.project.data.setSpellLang("en")

    # Get the dialog object
    nwGUI.mainMenu.aProjectSettings.activate(QAction.ActionEvent.Trigger)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiProjectSettings) is not None, timeout=1000)

    projSettings = SHARED.findTopLevelWidget(GuiProjectSettings)
    assert isinstance(projSettings, GuiProjectSettings)
    projSettings.show()
    qtbot.addWidget(projSettings)

    # Switch Tabs
    projSettings.sidebar.button(GuiProjectSettings.PAGE_SETTINGS).click()
    assert projSettings.mainStack.currentWidget() == projSettings.settingsPage

    projSettings.sidebar.button(GuiProjectSettings.PAGE_GOALS).click()
    assert projSettings.mainStack.currentWidget() == projSettings.goalsPage

    projSettings.sidebar.button(GuiProjectSettings.PAGE_STATUS).click()
    assert projSettings.mainStack.currentWidget() == projSettings.statusPage

    projSettings.sidebar.button(GuiProjectSettings.PAGE_IMPORT).click()
    assert projSettings.mainStack.currentWidget() == projSettings.importPage

    projSettings.sidebar.button(GuiProjectSettings.PAGE_REPLACE).click()
    assert projSettings.mainStack.currentWidget() == projSettings.replacePage

    # Selecting an unknown page does nothing
    projSettings.sidebar.setSelected(9999)

    # A button that isn't part of the sidebar's group is ignored
    otherButton = QToolButton()
    projSettings.sidebar._buttonClicked(otherButton)
    assert projSettings.mainStack.currentWidget() == projSettings.replacePage

    # Clean Up
    projSettings.close()
    # qtbot.stop()


@pytest.mark.gui
def testGuiProjectSettings_SettingsPage(qtbot, monkeypatch, nwGUI, fncPath, projPath, mockRnd):
    """Test the settings page of the dialog."""
    languages = [("en", "English"), ("de", "German")]
    monkeypatch.setattr(SpellEnchant, "listDictionaries", lambda *a: languages)

    (fncPath / "nw_en.qm").touch()
    (fncPath / "nw_de.qm").touch()
    (fncPath / "project_en.json").touch()
    (fncPath / "project_de.json").touch()
    CONFIG._nwLangPath = fncPath

    # Create new project
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    mockRnd.reset()
    CONFIG.setBackupPath(fncPath)

    # Set some values
    project = SHARED.project
    project.data.setLanguage("en")
    project.data.setSpellLang("en")
    project.data.setAuthor("Jane Smith")
    project.data.setAutoReplace({"A": "B", "C": "D"})

    # Create Dialog
    projSettings = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_SETTINGS)
    projSettings.show()
    qtbot.addWidget(projSettings)

    # Settings Tab
    settings = projSettings.settingsPage

    assert settings.projName.text() == "New Project"
    assert settings.projAuthor.text() == "Jane Smith"
    assert settings.projLang.currentData() == "en"
    assert settings.spellLang.currentData() == "en"
    assert settings.noBackup.isChecked() is False

    settings.projName.setText("Project Name")
    settings.projAuthor.setText("Jane Doe")
    settings.projLang.setCurrentIndex(settings.projLang.findData("de"))
    settings.spellLang.setCurrentIndex(settings.spellLang.findData("de"))
    settings.noBackup.setChecked(True)

    projSettings._doSave()
    assert project.data.name == "Project Name"
    assert project.data.author == "Jane Doe"
    assert project.data.language == "de"
    assert project.data.spellLang == "de"
    assert project.data.doBackup is False

    nwGUI._processProjectSettingsChanges()
    assert nwGUI.windowTitle() == "Project Name - novelWriter"

    # Without Enchant, only the default spell check entry is available
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "hasEnchant", False)
        noEnchant = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_SETTINGS)
        qtbot.addWidget(noEnchant)
        assert noEnchant.settingsPage.spellLang.count() == 1

    # qtbot.stop()


@pytest.mark.gui
def testGuiProjectSettings_GoalsPage(qtbot, nwGUI, projPath, mockRnd):
    """Test the goals page of the dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    project = SHARED.project

    # Create Dialog
    projSettings = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_GOALS)
    projSettings.show()
    qtbot.addWidget(projSettings)

    goals = projSettings.goalsPage

    # No deadline is set by default, so the date field and the auto-goal
    # switch must both start out disabled
    assert goals.targetDeadlineEnabled.isChecked() is False
    assert goals.targetDeadline.isEnabled() is False
    assert goals.dailyGoalAuto.isEnabled() is False

    # Enabling the deadline switch enables the date field and the auto-goal switch
    goals.targetDeadlineEnabled.setChecked(True)
    assert goals.targetDeadline.isEnabled() is True
    assert goals.dailyGoalAuto.isEnabled() is True

    # The count mode defaults to words, which is reflected in both the
    # switch and the unit labels next to the target fields
    assert goals.countCharacters.isChecked() is False
    assert goals._editableUnit["targetCount"].text() == "words"
    assert goals._editableUnit["dailyGoal"].text() == "words"

    # Toggling the switch updates both unit labels to characters
    goals.countCharacters.setChecked(True)
    assert goals._editableUnit["targetCount"].text() == "characters"
    assert goals._editableUnit["dailyGoal"].text() == "characters"

    # Set some values and save
    goals.targetCount.setValue(50000)
    goals.targetDeadline.setDate(QDate(2030, 1, 1))
    goals.dailyGoal.setValue(500)
    goals.dailyGoalAuto.setChecked(True)

    projSettings._doSave()
    assert project.data.targetCount == 50000
    assert project.data.targetCountChars is True
    assert project.data.targetDeadline == date(2030, 1, 1)
    assert project.data.dailyGoal == 500
    assert project.data.dailyGoalAuto is True

    # Disabling the deadline switch disables the date field and the
    # auto-goal switch again, and clears the deadline on save
    goals.targetDeadlineEnabled.setChecked(False)
    assert goals.targetDeadline.isEnabled() is False
    assert goals.dailyGoalAuto.isEnabled() is False

    projSettings._doSave()
    assert project.data.targetDeadline is None

    # qtbot.stop()


@pytest.mark.gui
def testGuiProjectSettings_StatusImport(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the status and importance pages of the dialog."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Set some values
    project = SHARED.project
    project.tree[C.hTitlePage].setStatus(C.sFinished)  # type: ignore
    project.tree[C.hChapterDoc].setStatus(C.sDraft)  # type: ignore
    project.tree[C.hSceneDoc].setStatus(C.sDraft)  # type: ignore

    nwGUI.projView.projTree.setSelectedHandle(C.hPlotRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, hLevel=1, isNote=True)
    nwGUI.projView.projTree.setSelectedHandle(C.hCharRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, hLevel=1, isNote=True)
    nwGUI.projView.projTree.setSelectedHandle(C.hWorldRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, hLevel=1, isNote=True)

    hPlotNote = "0000000000011"
    hCharNote = "0000000000012"
    hWorldNote = "0000000000013"

    project.tree[hPlotNote].setImport(C.iMajor)  # type: ignore
    project.tree[hCharNote].setImport(C.iMajor)  # type: ignore
    project.tree[hWorldNote].setImport(C.iMain)  # type: ignore

    project.tree.refreshAllItems()
    project.countStatus()

    assert [e.count for _, e in project.data.itemStatus.iterItems()] == [2, 0, 2, 1]
    # The Trash root, created when the project is opened, also counts
    # towards the default "New" import flag
    assert [e.count for _, e in project.data.itemImport.iterItems()] == [4, 0, 2, 1]

    # Create Dialog
    projSettings = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_STATUS)
    projSettings.show()
    qtbot.addWidget(projSettings)

    # Status Tab
    # ==========

    status = projSettings.statusPage

    assert status.changed is False
    assert status.getNewList() == []
    assert status.listBox.topLevelItemCount() == 4

    # Nothing happens when no item is selected
    status.listBox.clearSelection()
    status.delButton.click()
    assert status.listBox.topLevelItemCount() == 4
    status._onNameEdit("Ignored")

    # Cancelling the colour dialog does nothing
    with monkeypatch.context() as mp:
        mp.setattr(QColorDialog, "getColor", lambda *a: QColor())
        status.listBox.setCurrentItem(status.listBox.topLevelItem(0))
        status.colorButton.click()

    # Can't delete the first item (it's in use)
    status.listBox.clearSelection()
    status.listBox.setCurrentItem(status.listBox.topLevelItem(0))
    status.delButton.click()
    assert status.listBox.topLevelItemCount() == 4

    # Can delete the second item
    status.listBox.clearSelection()
    status.listBox.setCurrentItem(status.listBox.topLevelItem(1))
    status.delButton.click()
    assert status.listBox.topLevelItemCount() == 3

    # Add a new item
    with monkeypatch.context() as mp:
        mp.setattr(QColorDialog, "getColor", lambda *a: QColor(20, 30, 40))
        status.addButton.click()
        status.listBox.setCurrentItem(status.listBox.topLevelItem(3))
        status._onNameEdit("Final")
        status.colorButton.click()
        shapeAction = QAction(status)
        shapeAction.setData(nwStatusShape.CIRCLE)
        status._shapeSelected(shapeAction)
        assert status.listBox.topLevelItemCount() == 4

        # Non-shape data is ignored
        otherAction = QAction(status)
        otherAction.setData("not-a-shape")
        status._shapeSelected(otherAction)

    assert status.changed is True
    update = status.getNewList()

    assert update[0][0] == C.sNew
    assert update[0][1].name == "New"
    assert update[0][1].color.getRgb() == (108, 108, 108, 255)
    assert update[0][1].shape == nwStatusShape.STAR

    assert update[1][0] == C.sDraft
    assert update[1][1].name == "Draft"
    assert update[1][1].color.getRgb() == (163, 156, 52, 255)
    assert update[1][1].shape == nwStatusShape.CIRCLE_T

    assert update[2][0] == C.sFinished
    assert update[2][1].name == "Finished"
    assert update[2][1].color.getRgb() == (41, 102, 41, 255)
    assert update[2][1].shape == nwStatusShape.STAR

    assert update[3][0] is None
    assert update[3][1].name == "Final"
    assert update[3][1].color.getRgb() == (20, 30, 40, 255)
    assert update[3][1].shape == nwStatusShape.CIRCLE

    # Move items, none selected -> no change
    status.listBox.clearSelection()
    status._moveItem(1)
    assert [x[0] for x in status.getNewList()] == [C.sNew, C.sDraft, C.sFinished, None]

    # Move items, first selected, move up -> no change
    status.listBox.clearSelection()
    status.listBox.setCurrentItem(status.listBox.topLevelItem(0))
    status._moveItem(-1)
    assert [x[0] for x in status.getNewList()] == [C.sNew, C.sDraft, C.sFinished, None]

    # Move items, last selected, move up -> allowed
    status.listBox.clearSelection()
    status.listBox.setCurrentItem(status.listBox.topLevelItem(3))
    status._moveItem(-1)
    assert [x[0] for x in status.getNewList()] == [C.sNew, C.sDraft, None, C.sFinished]

    # Move items, same selected, move down -> allowed
    status._moveItem(1)
    assert [x[0] for x in status.getNewList()] == [C.sNew, C.sDraft, C.sFinished, None]

    # Importance Tab
    # ==============

    importance = projSettings.importPage
    projSettings._sidebarClicked(GuiProjectSettings.PAGE_IMPORT)

    # Delete unused entry
    importance.listBox.clearSelection()
    importance.listBox.setCurrentItem(importance.listBox.topLevelItem(1))
    importance.delButton.click()
    assert importance.listBox.topLevelItemCount() == 3

    # Add a new entry
    with monkeypatch.context() as mp:
        mp.setattr(QColorDialog, "getColor", lambda *a: QColor(20, 30, 40))
        importance.addButton.click()
        importance.listBox.clearSelection()
        importance.listBox.setCurrentItem(importance.listBox.topLevelItem(3))
        importance._onNameEdit("Final")
        importance.colorButton.click()
        shapeAction = QAction(importance)
        shapeAction.setData(nwStatusShape.TRIANGLE)
        importance._shapeSelected(shapeAction)
        assert importance.listBox.topLevelItemCount() == 4

    assert importance.changed is True
    update = importance.getNewList()

    assert update[0][0] == C.iNew
    assert update[0][1].name == "New"
    assert update[0][1].color.getRgb() == (179, 90, 179, 255)
    assert update[0][1].shape == nwStatusShape.SQUARE

    assert update[1][0] == C.iMajor
    assert update[1][1].name == "Major"
    assert update[1][1].color.getRgb() == (179, 90, 179, 255)
    assert update[1][1].shape == nwStatusShape.BLOCK_3

    assert update[2][0] == C.iMain
    assert update[2][1].name == "Main"
    assert update[2][1].color.getRgb() == (179, 90, 179, 255)
    assert update[2][1].shape == nwStatusShape.BLOCK_4

    assert update[3][0] is None
    assert update[3][1].name == "Final"
    assert update[3][1].color.getRgb() == (20, 30, 40, 255)
    assert update[3][1].shape == nwStatusShape.TRIANGLE

    # Check Project
    projSettings._doSave()

    statusItems = dict(project.data.itemStatus.iterItems())
    assert statusItems[C.sNew].name == "New"
    assert statusItems[C.sDraft].name == "Draft"
    assert statusItems[C.sFinished].name == "Finished"
    assert statusItems["s000014"].name == "Final"

    importItems = dict(project.data.itemImport.iterItems())
    assert importItems[C.iNew].name == "New"
    assert importItems[C.iMajor].name == "Major"
    assert importItems[C.iMain].name == "Main"
    assert importItems["i000015"].name == "Final"

    # qtbot.stop()


@pytest.mark.gui
def testGuiProjectSettings_StatusImportExport(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the status and importance import/export."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Create Dialog
    projSettings = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_STATUS)
    projSettings.show()
    qtbot.addWidget(projSettings)

    status = projSettings.statusPage
    assert status.listBox.topLevelItemCount() == 4
    expFile = projPath / "status.csv"

    # Export Cancelled
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
        status._exportLabels()
    assert expFile.is_file() is False

    # Import Cancelled
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
        status._importLabels()
    assert status.listBox.topLevelItemCount() == 4

    # Export Error
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(expFile), ""))
        mp.setattr("builtins.open", causeOSError)
        status._exportLabels()

    assert expFile.is_file() is False

    # Export File
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(expFile), ""))
        status._exportLabels()

    assert expFile.is_file() is True
    assert expFile.read_text().split() == [
        "STAR,#6c6c6c,New",
        "TRIANGLE,#a62a2d,Note",
        "CIRCLE_T,#a39c34,Draft",
        "STAR,#296629,Finished",
    ]

    # Import Error
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(expFile), ""))
        mp.setattr("builtins.open", causeOSError)
        status._importLabels()

    assert status.listBox.topLevelItemCount() == 4
    assert status.changed is False

    # Import File
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(expFile), ""))
        status._importLabels()

    assert status.listBox.topLevelItemCount() == 8
    assert status.changed is True

    item4 = status.listBox.topLevelItem(4)
    assert item4 is not None
    assert item4.text(0) == "New"

    item5 = status.listBox.topLevelItem(5)
    assert item5 is not None
    assert item5.text(0) == "Note"

    item6 = status.listBox.topLevelItem(6)
    assert item6 is not None
    assert item6.text(0) == "Draft"

    item7 = status.listBox.topLevelItem(7)
    assert item7 is not None
    assert item7.text(0) == "Finished"

    # Invalid rows in the import file are skipped
    badFile = projPath / "status_bad.csv"
    badFile.write_text("NOT_A_SHAPE,#000000,Bad\nSTAR,#123456,Good\n", encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(badFile), ""))
        status._importLabels()
    assert status.listBox.topLevelItemCount() == 9

    projSettings.close()


@pytest.mark.gui
def testGuiProjectSettings_Replace(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the auto-replace page of the dialog."""
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Set some values
    project = SHARED.project
    project.data.setAutoReplace({"A": "B", "C": "D"})

    # Create Dialog
    projSettings = GuiProjectSettings(nwGUI, GuiProjectSettings.PAGE_REPLACE)
    projSettings.show()
    qtbot.addWidget(projSettings)

    # Auto-Replace Tab
    # ================

    replace = projSettings.replacePage

    assert replace.listBox.topLevelItem(0).text(0) == "<A>"  # type: ignore
    assert replace.listBox.topLevelItem(0).text(1) == "B"  # type: ignore
    assert replace.listBox.topLevelItem(1).text(0) == "<C>"  # type: ignore
    assert replace.listBox.topLevelItem(1).text(1) == "D"  # type: ignore
    assert replace.listBox.topLevelItemCount() == 2

    # Nothing to save or delete
    replace.listBox.clearSelection()
    replace._onEntryDeleted()
    assert replace.listBox.topLevelItemCount() == 2

    # Create a new entry
    qtbot.mouseClick(replace.addButton, QtMouseLeft)
    assert replace.listBox.topLevelItemCount() == 3
    assert replace.listBox.topLevelItem(2).text(0) == "<keyword3>"  # type: ignore
    assert replace.listBox.topLevelItem(2).text(1) == ""  # type: ignore

    # Edit the entry
    newItem = replace.listBox.topLevelItem(2)
    replace.listBox.setCurrentItem(newItem)
    replace._onKeyEdit("Th is ")
    replace._onValueEdit("With This Stuff ")
    assert newItem.text(0) == "<This>"  # type: ignore
    assert newItem.text(1) == "With This Stuff "  # type: ignore

    # A key that strips to empty is not applied
    replace._onKeyEdit("!!!")
    assert newItem.text(0) == "<This>"  # type: ignore

    # Nothing happens for key/value edits when no item is selected
    replace.listBox.clearSelection()
    replace._onKeyEdit("Other")
    replace._onValueEdit("Other")
    assert newItem.text(0) == "<This>"  # type: ignore
    assert newItem.text(1) == "With This Stuff "  # type: ignore

    # Items whose key strips to empty are skipped when building the new list
    newItem.setText(0, "!!!")  # type: ignore
    assert "This" not in replace.getNewList()
    newItem.setText(0, "<This>")  # type: ignore

    # Create a new entry again
    replace.listBox.clearSelection()
    qtbot.mouseClick(replace.addButton, QtMouseLeft)
    assert replace.listBox.topLevelItemCount() == 4

    # The list is sorted, so we must find it
    newIdx = -1
    for i in range(replace.listBox.topLevelItemCount()):
        if replace.listBox.topLevelItem(i).text(0) == "<keyword4>":  # type: ignore
            newIdx = i
            break
    assert newIdx >= 0

    # Then delete the new item
    replace.listBox.setCurrentItem(replace.listBox.topLevelItem(newIdx))
    qtbot.mouseClick(replace.delButton, QtMouseLeft)
    assert replace.listBox.topLevelItemCount() == 3

    # Check Project
    projSettings._doSave()
    assert project.data.autoReplace == {"A": "B", "C": "D", "This": "With This Stuff"}

    # qtbot.stop()


@pytest.mark.gui
def testGuiProjectSettings_MemoryLeakRegression(qtbot, nwGUI, projPath, mockRnd):
    """Test that the dialog is freed when it is closed."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    checkDialogFreedOnClose(qtbot, lambda: GuiProjectSettings(nwGUI))
