"""
novelWriter - Manuscript Tool Tests
===================================

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

import sys

from unittest.mock import MagicMock

import pytest

from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtGui import QAction, QDesktopServices
from PyQt6.QtPrintSupport import QPrintPreviewDialog
from PyQt6.QtWidgets import QListWidgetItem

from novelwriter import SHARED
from novelwriter.constants import nwHeadFmt, nwStats
from novelwriter.core.project import NWProject
from novelwriter.manuscript.buildsettings import BuildSettings
from novelwriter.manuscript.manusbuild import GuiManuscriptBuild
from novelwriter.manuscript.manuscript import GuiManuscript
from novelwriter.manuscript.manussettings import GuiBuildSettings

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiManuscript_Init(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """Test the init/main functionality of the GuiManuscript dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    SHARED.project.storage.getDocument(C.hChapterDoc).writeDocument("## A Chapter\n\n\t\tHi")
    allText = "New Novel\nBy Jane Doe\n\n\nA Chapter\n\t\tHi"

    nwGUI.mainMenu.aBuildManuscript.activate(QAction.ActionEvent.Trigger)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiManuscript) is not None, timeout=1000)
    manus = SHARED.findTopLevelWidget(GuiManuscript)
    assert isinstance(manus, GuiManuscript)
    manus.show()
    assert manus.docPreview.toPlainText().strip() == ""

    # First load should have create a default build
    assert manus.buildList.count() == 1

    # Loading again should not add a new build
    manus.loadContent()
    assert manus.buildList.count() == 1

    # Build a preview
    manus.buildList.clearSelection()
    manus.buildList.setCurrentRow(0)
    document = manus.docPreview.document()
    assert document is not None
    with qtbot.waitSignal(document.contentsChanged):
        manus.btnPreview.click()
    assert manus.docPreview.toPlainText().strip() == allText

    # Trigger a theme update, which is only a visual refresh, but it shouldn't crash
    manus.updateTheme()

    nwGUI.closeProject()  # This should auto-close the manuscript tool

    # qtbot.stop()


@pytest.mark.gui
def testGuiManuscript_Builds(qtbot, nwGUI, projPath):
    """Test the handling of builds in the GuiManuscript dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    manus = GuiManuscript(nwGUI)
    manus.show()
    manus.loadContent()

    # Delete the default build, while it is open
    manus.buildList.clearSelection()
    manus.buildList.setCurrentRow(0)
    with qtbot.waitSignal(manus.tbEdit.clicked, timeout=5000):
        manus.tbEdit.click()

    manus._editSelectedBuild()

    manus.buildList.clearSelection()
    manus.buildList.setCurrentRow(0)
    manus.tbDel.click()
    assert manus.buildList.count() == 0

    # Create a new build
    manus.tbAdd.click()
    bSettings = SHARED.findTopLevelWidget(GuiBuildSettings)
    assert isinstance(bSettings, GuiBuildSettings)
    bSettings.editBuildName.setText("Test Build")
    bSettings.swtAutoPreview.setChecked(False)
    build = None

    @pyqtSlot(BuildSettings)
    def _testNewSettingsReady(new: BuildSettings, refresh: bool):
        nonlocal build
        build = new

    with qtbot.waitSignal(bSettings.newSettingsReady, timeout=5000):
        bSettings.newSettingsReady.connect(_testNewSettingsReady)
        bSettings.btnSave.click()

    assert isinstance(build, BuildSettings)
    assert build.name == "Test Build"
    assert manus.buildList.count() == 1

    # Edit the new build
    manus.buildList.clearSelection()
    manus.buildList.setCurrentRow(0)
    with qtbot.waitSignal(manus.tbEdit.clicked, timeout=5000):
        manus.tbEdit.click()

    manus._editSelectedBuild()
    bSettings = SHARED.findTopLevelWidget(GuiBuildSettings)
    assert isinstance(bSettings, GuiBuildSettings)
    build = None

    with qtbot.waitSignal(bSettings.newSettingsReady, timeout=5000):
        bSettings.newSettingsReady.connect(_testNewSettingsReady)
        bSettings.btnApply.click()  # Should leave the dialog open

    assert isinstance(build, BuildSettings)
    assert build.name == "Test Build"
    assert manus.buildList.count() == 1

    # Copy the build
    manus._buildMap[build.buildID].setSelected(True)
    manus._copySelectedBuild()
    assert manus.buildList.count() == 2

    new = manus._getSelectedBuild()
    assert new is not None
    assert new.name == "Test Build 2"

    # Processing first build with refresh should change selection
    manus.docPreview._docTime = 0
    manus._processNewSettings(build, True)
    assert manus.docPreview._docTime > 0  # Refreshed
    current = manus._getSelectedBuild()
    assert current is not None
    assert current.name == "Test Build"

    # Processing new build without refresh should keep selection
    manus.docPreview._docTime = 0
    manus._processNewSettings(new, False)
    assert manus.docPreview._docTime == 0  # No refresh
    current = manus._getSelectedBuild()
    assert current is not None
    assert current.name == "Test Build"

    # With no builds available, editing, copying, deleting or building
    # from an empty list all do nothing
    manus.buildList.clear()
    assert manus._getSelectedBuild() is None
    manus._editSelectedBuild()
    manus._copySelectedBuild()
    manus._deleteSelectedBuild()
    manus._buildManuscript()
    manus._updateBuildsList()  # Restore the list from the underlying collection
    assert manus.buildList.count() == 2

    # An item whose build ID isn't in the collection is treated as no selection
    bogus = QListWidgetItem()
    bogus.setData(GuiManuscript.D_KEY, "0000000000000")
    manus.buildList.insertItem(0, bogus)
    manus.buildList.clearSelection()
    manus.buildList.setCurrentRow(0)
    assert manus._getSelectedBuild() is None
    manus.buildList.takeItem(0)

    # Deleting a build with no open settings dialog for it just removes it
    manus.buildList.clearSelection()
    for i in range(manus.buildList.count()):
        item = manus.buildList.item(i)
        if item is not None and item.data(GuiManuscript.D_KEY) == new.buildID:
            item.setSelected(True)
            break
    else:
        raise AssertionError
    countBefore = manus.buildList.count()
    manus._deleteSelectedBuild()
    assert manus.buildList.count() == countBefore - 1

    # Trigger a theme update, which should propagate to settings
    nwGUI.refreshThemeColors()

    # Close the dialog should also close the child dialogs
    manus.btnClose.click()
    if isinstance(bSettings, GuiBuildSettings):
        # May have been garbage collected, but if it isn't, it should be hidden
        assert bSettings.isVisible() is False

    # qtbot.stop()


@pytest.mark.gui
def testGuiManuscript_Features(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """Test other features of the GuiManuscript dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    nwGUI.openDocument(C.hTitlePage)
    nwGUI.docEditor.setPlainText(
        "#! My Novel\n\n"
        "# Part One\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
        "#### Section\n\n"
        "Text\n\n"
    )
    nwGUI.saveDocument()
    # qtbot.stop()

    manus = GuiManuscript(nwGUI)
    manus.show()
    manus.loadContent()

    manus.buildList.setCurrentRow(0)
    build = manus._getSelectedBuild()
    assert isinstance(build, BuildSettings)

    # Previews
    # ========

    # No build selected
    manus.buildList.clear()
    manus.btnPreview.click()
    qtbot.wait(200)  # Should be enough to run the build
    assert manus.docPreview.toPlainText().strip() == ""
    manus._updateBuildsList()

    # Preview the first
    first = manus.buildList.item(0)
    assert isinstance(first, QListWidgetItem)
    build = manus._builds.getBuild(first.data(GuiManuscript.D_KEY))
    assert isinstance(build, BuildSettings)
    build.setValue("headings.fmtScene", nwHeadFmt.TITLE)
    build.setValue("headings.fmtAltScene", nwHeadFmt.TITLE)
    manus._builds.setBuild(build)

    manus.buildList.setCurrentRow(0)
    document = manus.docPreview.document()
    assert document is not None
    with qtbot.waitSignal(document.contentsChanged):
        manus.btnPreview.click()
    assert manus.docPreview.toPlainText().strip() != ""

    # Check Outline
    assert manus.buildOutline._outline == {
        "000000000000c:T0001": "TT|My Novel",
        "000000000000c:T0002": "PT|Part One",
        "000000000000c:T0003": "CH|Chapter One",
        "000000000000c:T0004": "SC|Scene One",
        "000000000000c:T0005": "SC|Scene Two",
        "000000000000c:T0006": "CH|Chapter Two",
        "000000000000c:T0007": "SC|Scene Three",
        "000000000000c:T0008": "SC|Scene Four",
        "000000000000e:T0001": "CH|New Chapter",
        "000000000000f:T0001": "SC|New Scene",
    }
    listView = manus.buildOutline.listView
    assert listView.topLevelItemCount() == 5
    keyRole = manus.buildOutline.D_LINE

    assert (item := listView.topLevelItem(0))
    assert item.data(0, keyRole) == "000000000000c:T0001"
    assert (item := listView.topLevelItem(1))
    assert item.data(0, keyRole) == "000000000000c:T0002"
    assert (item := listView.topLevelItem(2))
    assert item.data(0, keyRole) == "000000000000c:T0003"
    assert (item := listView.topLevelItem(3))
    assert item.data(0, keyRole) == "000000000000c:T0006"
    assert (item := listView.topLevelItem(4))
    assert item.data(0, keyRole) == "000000000000e:T0001"

    # Click outline
    item = listView.topLevelItem(4)
    assert item is not None
    with qtbot.waitSignal(manus.buildOutline.outlineEntryClicked) as signal:
        manus.buildOutline._onItemClick(item)
        assert signal.args == ["000000000000e:T0001"]

    # Preview Navigation
    assert manus.docPreview.source() == QUrl("#000000000000e:T0001")
    manus.docPreview.navigateTo("000000000000c:T0002")
    assert manus.docPreview.source() == QUrl("#000000000000c:T0002")
    manus.docPreview._linkClicked(QUrl("#000000000000c:T0003"))
    assert manus.docPreview.source() == QUrl("#000000000000c:T0003")
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        manus.docPreview._linkClicked(QUrl("http://www.example.com"))
        assert openUrl.called is True
        assert openUrl.call_args[0][0] == QUrl("http://www.example.com")

    # Check Preview Stats
    assert manus.countsLabel.text() == "Words: 25\u2003Characters: 117"
    assert manus.buildStats.cWords.text(1) == "25"
    assert manus.buildStats.cChars.text(1) == "117"
    assert manus.buildStats.cDialog.text(1) == "\u2014"

    # Check Preview Stats w/Dialogue
    dialogData = {
        nwStats.WORDS: 25,
        nwStats.CHARS: 117,
        nwStats.CHARS_TEXT: 100,
        nwStats.CHARS_DIALOG: 25,
    }
    manus._updateCountsLabel(dialogData, True)
    assert manus.countsLabel.text() == "Words: 25\u2003Characters: 117\u2003Dialogue: 25.0\u202f%"
    manus.buildStats.updateStats(dialogData, True)
    assert manus.buildStats.cDialog.text(1) == "25.0\u202f%"
    assert manus.buildStats.cDialogChars.text(1) == "25"

    # Tests are too fast to trigger this one, so we trigger it manually to ensure it isn't failing
    manus.docPreview._postUpdate()

    # Builds
    # ======

    build._changed = True
    manus.buildList.clearSelection()
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.manuscript.manusbuild.GuiManuscriptBuild.exec", lambda *a: None)

        manus.buildList.setCurrentRow(0)
        manus.btnBuild.click()
        for obj in manus.children():
            if isinstance(obj, GuiManuscriptBuild):
                obj.close()
                break
        else:
            raise AssertionError

    # An unchanged build is not written back to the collection
    build._changed = False
    manus.buildList.clearSelection()
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.manuscript.manusbuild.GuiManuscriptBuild.exec", lambda *a: None)

        manus.buildList.setCurrentRow(0)
        manus.btnBuild.click()
        for obj in manus.children():
            if isinstance(obj, GuiManuscriptBuild):
                obj.close()
                break
        else:
            raise AssertionError

    # Outline entries with an unrecognised prefix are skipped
    manus.buildOutline.updateOutline({"stale:T0001": "XX|Stale Entry"}, force=True)
    assert manus.buildOutline.listView.topLevelItemCount() == 0

    # Preview link edge cases
    manus.docPreview._linkClicked(QUrl(""))  # An empty link does nothing
    with monkeypatch.context() as mp:
        openUrl = MagicMock()
        mp.setattr(QDesktopServices, "openUrl", openUrl)
        manus.docPreview._linkClicked(QUrl("ftp://example.com"))  # Neither internal nor http(s)
        assert openUrl.called is False

    # Finish
    manus.close()
    # qtbot.stop()


@pytest.mark.gui
@pytest.mark.skipif(sys.platform.startswith("darwin"), reason="Not running on Darwin")
def testGuiManuscript_Print(monkeypatch, qtbot, nwGUI, projPath):
    """Test the print feature of the GuiManuscript dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    manus = GuiManuscript(nwGUI)
    manus.show()
    manus.loadContent()

    manus.buildList.setCurrentRow(0)
    document = manus.docPreview.document()
    assert document is not None
    with qtbot.waitSignal(document.contentsChanged):
        manus.btnPreview.click()
    assert manus.docPreview.toPlainText().strip() != ""

    with monkeypatch.context() as mp:
        mp.setattr(QPrintPreviewDialog, "exec", lambda *a: None)
        manus.btnPrint.click()
        for obj in manus.children():
            if isinstance(obj, QPrintPreviewDialog):
                obj.show()
                obj.close()
                break
        else:
            raise AssertionError

    # Finish
    manus.close()
    # qtbot.stop()
