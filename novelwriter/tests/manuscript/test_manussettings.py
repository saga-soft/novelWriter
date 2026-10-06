"""
novelWriter - Manuscript Build Settings Dialog Tests
====================================================

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

import pytest

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QAction, QFont

from novelwriter import CONFIG, SHARED
from novelwriter.common import describeFont
from novelwriter.constants import nwHeadFmt, nwStyles, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.extensions.modified import NFontDialog
from novelwriter.manuscript.buildsettings import BuildSettings, FilterMode
from novelwriter.manuscript.manussettings import GuiBuildSettings, _FilterTab, _FormattingTab, _HeadingsTab
from novelwriter.shared import _GuiAlert

from tests.helpers import C, buildTestProject, checkDialogFreedOnClose


@pytest.mark.gui
def testGuiBuildSettings_Init(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the initialisation of the GuiBuildSettings dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    build = BuildSettings()

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    # Flip through pages
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 1)
    assert button is not None
    button.click()
    assert isinstance(bSettings.toolStack.currentWidget(), _FormattingTab)

    button = bSettings.sidebar._group.button(bSettings.OPT_HEADINGS)
    assert button is not None
    button.click()
    assert isinstance(bSettings.toolStack.currentWidget(), _HeadingsTab)

    button = bSettings.sidebar._group.button(bSettings.OPT_FILTERS)
    assert button is not None
    button.click()
    assert isinstance(bSettings.toolStack.currentWidget(), _FilterTab)

    # Check dialog buttons
    triggered = False

    @pyqtSlot(BuildSettings)
    def _testNewSettingsReady(new: BuildSettings, refresh: bool):
        nonlocal triggered
        assert new.buildID == build.buildID
        triggered = True

    # Capture Apply button
    with qtbot.waitSignal(bSettings.newSettingsReady, timeout=5000):
        bSettings.newSettingsReady.connect(_testNewSettingsReady)
        bSettings._dialogButtonClicked(bSettings.btnApply)

    assert triggered

    # Capture Save button
    triggered = False

    with qtbot.waitSignal(bSettings.newSettingsReady, timeout=5000):
        bSettings.newSettingsReady.connect(_testNewSettingsReady)
        bSettings._dialogButtonClicked(bSettings.btnSave)

    assert triggered

    # Close manually
    # This pops the ask to save dialog, which is automatically handled
    triggered = False
    build._changed = True
    bSettings.show()

    with qtbot.waitSignal(bSettings.newSettingsReady, timeout=5000):
        bSettings.newSettingsReady.connect(_testNewSettingsReady)
        bSettings._build._changed = True
        bSettings.close()

    assert triggered

    # Close manually, but decline to save the changes
    triggered = False
    bSettings.show()
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        bSettings._build._changed = True
        bSettings.close()
    assert triggered is False
    assert bSettings._build.changed is False

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_Filter(qtbot, nwGUI, projPath, mockRnd):
    """Test the Filter Tab of the GuiBuildSettings dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    build = BuildSettings()

    switchMap = {
        "incNovel": "doc:filter.includeNovel",
        "incNotes": "doc:filter.includeNotes",
        "incInactive": "doc:filter.includeInactive",
        "novelRoot": f"root:{C.hNovelRoot}",
        "plotRoot": f"root:{C.hPlotRoot}",
        "charRoot": f"root:{C.hCharRoot}",
        "worldRoot": f"root:{C.hWorldRoot}",
    }

    hPlotDoc = SHARED.project.newFile("Main Plot", C.hPlotRoot)
    hCharDoc = SHARED.project.newFile("Jane Doe", C.hCharRoot)
    SHARED.project.tree[hPlotDoc].setActive(False)  # type: ignore

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    filterTab = bSettings.optTabSelect
    button = bSettings.sidebar._group.button(bSettings.OPT_FILTERS)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is filterTab

    # Check content
    assert filterTab.optTree.topLevelItemCount() == 4  # The 4 root folders
    assert filterTab.filterOpt._index == 10  # 2 headers, 1 sep, 3 opt and 4 roots

    # Un-toggle note folders
    filterTab.filterOpt._entries[switchMap["worldRoot"]].switch.setChecked(False)  # World Root
    assert filterTab.optTree.topLevelItemCount() == 3
    assert C.hWorldRoot in sBuild._skipRoot

    filterTab.filterOpt._entries[switchMap["charRoot"]].switch.setChecked(False)  # Char Root
    assert filterTab.optTree.topLevelItemCount() == 2
    assert C.hCharRoot in sBuild._skipRoot

    filterTab.filterOpt._entries[switchMap["plotRoot"]].switch.setChecked(False)  # Plot Root
    assert filterTab.optTree.topLevelItemCount() == 1
    assert C.hPlotRoot in sBuild._skipRoot

    # Reset Plot and Char
    filterTab.filterOpt._entries[switchMap["plotRoot"]].switch.setChecked(True)
    filterTab.filterOpt._entries[switchMap["charRoot"]].switch.setChecked(True)
    assert filterTab.optTree.topLevelItemCount() == 3

    # Switch off novel docs
    filterTab.filterOpt._entries[switchMap["incNovel"]].switch.setChecked(False)
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (False, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (False, FilterMode.FILTERED),
        C.hSceneDoc: (False, FilterMode.FILTERED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.FILTERED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.FILTERED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Switch on note docs
    filterTab.filterOpt._entries[switchMap["incNotes"]].switch.setChecked(True)
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (False, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (False, FilterMode.FILTERED),
        C.hSceneDoc: (False, FilterMode.FILTERED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.FILTERED),  # Set to inactive
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (True, FilterMode.FILTERED),  # Now enabled
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Switch on inactive docs
    filterTab.filterOpt._entries[switchMap["incInactive"]].switch.setChecked(True)
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (False, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (False, FilterMode.FILTERED),
        C.hSceneDoc: (False, FilterMode.FILTERED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (True, FilterMode.FILTERED),  # Now enabled
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (True, FilterMode.FILTERED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Set chapter and scene docs to included
    filterTab._treeMap[C.hChapterDoc].setSelected(True)
    filterTab._treeMap[C.hSceneDoc].setSelected(True)
    filterTab.includedButton.click()
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (False, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.INCLUDED),  # Now included
        C.hSceneDoc: (True, FilterMode.INCLUDED),  # Now included
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (True, FilterMode.FILTERED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (True, FilterMode.FILTERED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Set char and plot docs to excluded
    filterTab.optTree.clearSelection()
    filterTab._treeMap[hPlotDoc].setSelected(True)  # type: ignore
    filterTab._treeMap[hCharDoc].setSelected(True)  # type: ignore
    filterTab.excludedButton.click()
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (False, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.INCLUDED),
        C.hSceneDoc: (True, FilterMode.INCLUDED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.EXCLUDED),  # Now excluded
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.EXCLUDED),  # Now excluded
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Switch on novel docs
    filterTab.filterOpt._entries[switchMap["incNovel"]].switch.setChecked(True)
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),  # Now enabled
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.INCLUDED),
        C.hSceneDoc: (True, FilterMode.INCLUDED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.EXCLUDED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.EXCLUDED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Selecting only novel root should iterate through all children
    filterTab.optTree.clearSelection()
    filterTab._treeMap[C.hNovelRoot].setSelected(True)
    filterTab.resetButton.click()
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.EXCLUDED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.EXCLUDED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Set everything back to filtered
    filterTab.optTree.clearSelection()
    filterTab._treeMap[C.hNovelRoot].setSelected(True)
    filterTab._treeMap[C.hSceneDoc].setSelected(True)
    filterTab._treeMap[hPlotDoc].setSelected(True)  # type: ignore
    filterTab._treeMap[hCharDoc].setSelected(True)  # type: ignore
    filterTab.resetButton.click()
    assert sBuild.buildItemFilter(SHARED.project) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (True, FilterMode.FILTERED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        hCharDoc: (True, FilterMode.FILTERED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTrashRoot: (False, FilterMode.SKIPPED),
    }

    # Check handling of invalid project items
    assert list(filterTab._treeMap.keys()) == [
        C.hNovelRoot,
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
        C.hPlotRoot,
        hPlotDoc,
        C.hCharRoot,
        hCharDoc,
    ]
    SHARED.project.tree[hCharDoc].setRoot(None)  # type: ignore
    SHARED.project.tree[hPlotDoc].setParent(None)  # type: ignore
    filterTab._populateTree()
    assert list(filterTab._treeMap.keys()) == [
        C.hNovelRoot,
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
        C.hPlotRoot,
        C.hCharRoot,
    ]

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_Headings(qtbot, nwGUI):
    """Test the Headings Tab of the GuiBuildSettings dialog."""
    build = BuildSettings()

    ttTitle = f"Part: {nwHeadFmt.TITLE}"
    chTitle = f"Chapter: {nwHeadFmt.TITLE}"
    unTitle = f"Interlude: {nwHeadFmt.TITLE}"
    scTitle = f"Scene: {nwHeadFmt.TITLE}"
    shTitle = f"Hard Scene: {nwHeadFmt.TITLE}"
    sxTitle = f"Section: {nwHeadFmt.TITLE}"

    build.setValue("headings.fmtPart", ttTitle)
    build.setValue("headings.fmtChapter", chTitle)
    build.setValue("headings.fmtUnnumbered", unTitle)
    build.setValue("headings.fmtScene", scTitle)
    build.setValue("headings.fmtAltScene", shTitle)
    build.setValue("headings.fmtSection", sxTitle)
    build.setValue("headings.hideScene", False)
    build.setValue("headings.hideSection", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    headTab = bSettings.optTabHeadings
    button = bSettings.sidebar._group.button(bSettings.OPT_HEADINGS)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is headTab

    # Check initial values
    assert headTab.fmtPart.text() == ttTitle
    assert headTab.fmtChapter.text() == chTitle
    assert headTab.fmtUnnumbered.text() == unTitle
    assert headTab.fmtScene.text() == scTitle
    assert headTab.fmtAScene.text() == shTitle
    assert headTab.fmtSection.text() == sxTitle
    assert headTab.swtScene.isChecked() is False
    assert headTab.swtSection.isChecked() is False

    # Edit in Turn
    # ============

    # Nothing to apply
    assert headTab._editing == 0
    assert headTab.editTextBox.isEnabled() is False
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Inserting text with no heading selected for editing does nothing
    headTab._insertIntoForm(nwHeadFmt.TITLE)
    assert headTab.editTextBox.toPlainText() == ""

    # Title
    headTab.btnPart.click()
    assert headTab._editing == headTab.EDIT_TITLE
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == ttTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Chapter
    headTab.btnChapter.click()
    assert headTab._editing == headTab.EDIT_CHAPTER
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == chTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Unnumbered
    headTab.btnUnnumbered.click()
    assert headTab._editing == headTab.EDIT_UNNUM
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == unTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Scene
    headTab.btnScene.click()
    assert headTab._editing == headTab.EDIT_SCENE
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == scTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Hard Scene
    headTab.btnAScene.click()
    assert headTab._editing == headTab.EDIT_HSCENE
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == shTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Section
    headTab.btnSection.click()
    assert headTab._editing == headTab.EDIT_SECTION
    assert headTab.editTextBox.isEnabled() is True
    assert headTab.editTextBox.toPlainText() == sxTitle
    headTab.btnApply.click()
    assert headTab.editTextBox.isEnabled() is False

    # Edit a Heading
    # ==============
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    # Create new format of all bits
    headTab.btnChapter.click()
    allFmt = (
        f"{nwHeadFmt.TITLE}{nwHeadFmt.CH_NUM}{nwHeadFmt.CH_WORD}{nwHeadFmt.CH_ROMU}"
        f"{nwHeadFmt.CH_ROML}{nwHeadFmt.SC_NUM}{nwHeadFmt.SC_ABS}"
    )
    headTab.editTextBox.clear()
    assert headTab.editTextBox.toPlainText() == ""
    headTab.aInsTitle.trigger()
    headTab.aInsChNum.trigger()
    headTab.aInsChWord.trigger()
    headTab.aInsChRomU.trigger()
    headTab.aInsChRomL.trigger()
    headTab.aInsScNum.trigger()
    headTab.aInsScAbs.trigger()
    assert headTab.editTextBox.toPlainText() == allFmt
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtChapter") == allFmt

    # Check complex format
    headTab.btnChapter.click()
    headTab.editTextBox.setPlainText(f"Chapter {nwHeadFmt.CH_NUM}\n{nwHeadFmt.TITLE}\n")
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtChapter") == (f"Chapter {nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")

    # Set all to plain title
    headTab.btnPart.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtPart") == nwHeadFmt.TITLE

    headTab.btnChapter.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtChapter") == nwHeadFmt.TITLE

    headTab.btnUnnumbered.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtUnnumbered") == nwHeadFmt.TITLE

    headTab.btnScene.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtScene") == nwHeadFmt.TITLE

    headTab.btnAScene.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtAltScene") == nwHeadFmt.TITLE

    headTab.btnSection.click()
    headTab.editTextBox.setPlainText(nwHeadFmt.TITLE)
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtSection") == nwHeadFmt.TITLE

    # Check that horizontal rule replaces all
    headTab.btnScene.click()
    headTab.aInsTitle.trigger()
    headTab.aInsHRule.trigger()
    headTab.btnApply.click()
    assert sBuild.getStr("headings.fmtScene") == nwHeadFmt.HRULE

    # Check hide switches
    headTab.swtPart.setChecked(True)
    headTab.swtChapter.setChecked(True)
    headTab.swtUnnumbered.setChecked(True)
    headTab.swtScene.setChecked(True)
    headTab.swtAScene.setChecked(True)
    headTab.swtSection.setChecked(True)
    headTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getBool("headings.hidePart") is True
    assert sBuild.getBool("headings.hideChapter") is True
    assert sBuild.getBool("headings.hideUnnumbered") is True
    assert sBuild.getBool("headings.hideScene") is True
    assert sBuild.getBool("headings.hideAltScene") is True
    assert sBuild.getBool("headings.hideSection") is True

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_HeadingsAutoReplace(qtbot, nwGUI):
    """Test the auto-replace symbols feature of the heading edit box."""
    build = BuildSettings()

    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    headTab = bSettings.optTabHeadings
    button = bSettings.sidebar._group.button(bSettings.OPT_HEADINGS)
    assert button is not None
    button.click()

    headTab.btnChapter.click()
    assert headTab.editTextBox.isEnabled() is True
    headTab.editTextBox.clear()

    # Auto-replace is on by default, so typed text is converted as it is typed
    assert CONFIG.doReplace is True
    qtbot.keyClicks(headTab.editTextBox, "Some text...")
    assert headTab.editTextBox.toPlainText() == f"Some text{nwUnicode.U_HELLIP}"

    # Turning it off leaves typed text untouched
    CONFIG.doReplace = False
    headTab.editTextBox.clear()
    qtbot.keyClicks(headTab.editTextBox, "Some text...")
    assert headTab.editTextBox.toPlainText() == "Some text..."

    # Inserting several characters at once, as the menu actions do, is not affected
    CONFIG.doReplace = True
    headTab.editTextBox.clear()
    headTab.editTextBox.insertPlainText("Some text...")
    assert headTab.editTextBox.toPlainText() == "Some text..."

    bSettings._dialogButtonClicked(bSettings.btnClose)


@pytest.mark.gui
def testGuiBuildSettings_FormatTextContent(qtbot, nwGUI):
    """Test the Text Content settings."""
    build = BuildSettings()

    build.setValue("text.includeBodyText", False)
    build.setValue("text.includeSynopsis", False)
    build.setValue("text.includeComments", False)
    build.setValue("text.includeStory", False)
    build.setValue("text.includeNotes", False)
    build.setValue("text.includeKeywords", False)
    build.setValue("text.ignoredKeywords", "")

    build.setValue("text.addNoteHeadings", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 1)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.incBodyText.isChecked() is False
    assert fmtTab.incSynopsis.isChecked() is False
    assert fmtTab.incComments.isChecked() is False
    assert fmtTab.incStory.isChecked() is False
    assert fmtTab.incNotes.isChecked() is False
    assert fmtTab.incKeywords.isChecked() is False
    assert fmtTab.ignoredKeywords.text() == ""

    assert fmtTab.addNoteHead.isChecked() is False

    # Toggle switches
    fmtTab.incBodyText.setChecked(True)
    fmtTab.incSynopsis.setChecked(True)
    fmtTab.incComments.setChecked(True)
    fmtTab.incStory.setChecked(True)
    fmtTab.incNotes.setChecked(True)
    fmtTab.incKeywords.setChecked(True)

    fmtTab.addNoteHead.setChecked(True)

    # Test cleanup of ignored keywords
    fmtTab.ignoredKeywords.setText("@stuff, @pizza, @object")  # First two are invalid
    fmtTab._updateIgnoredKeywords("@custom")  # Adding a new should trigger cleanup
    assert fmtTab.ignoredKeywords.text() in ("@custom, @object", "@object, @custom")

    # Selecting a keyword from the menu should also trigger cleanup
    fmtTab.mnKeywords.actions()[0].trigger()
    assert fmtTab.ignoredKeywords.text() != ""
    fmtTab.ignoredKeywords.setText("@custom, @object")

    # Non-string data is ignored
    otherAction = QAction(fmtTab)
    otherAction.setData(1)
    fmtTab._ignoredKeywordSelected(otherAction)
    assert fmtTab.ignoredKeywords.text() == "@custom, @object"

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getBool("text.includeBodyText") is True
    assert sBuild.getBool("text.includeSynopsis") is True
    assert sBuild.getBool("text.includeComments") is True
    assert sBuild.getBool("text.includeStory") is True
    assert sBuild.getBool("text.includeNotes") is True
    assert sBuild.getBool("text.includeKeywords") is True
    assert sBuild.getStr("text.ignoredKeywords") in ("@custom, @object", "@object, @custom")

    assert sBuild.getBool("text.addNoteHeadings") is True

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_FormatTextFormat(monkeypatch, qtbot, nwGUI):
    """Test the Text Format settings."""
    build = BuildSettings()

    build.setValue("format.buildLang", "en_US")
    build.setValue("format.textFont", "")  # Will fall back to config value
    build.setValue("format.lineHeight", 1.2)

    build.setValue("format.justifyText", False)
    build.setValue("format.justifyOnBreak", False)
    build.setValue("format.stripUnicode", False)
    build.setValue("format.replaceTabs", False)
    build.setValue("format.keepBreaks", True)
    build.setValue("format.showDialogue", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 2)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.lineHeight.value() == 1.2

    assert fmtTab.justifyText.isChecked() is False
    assert fmtTab.justifyOnBreak.isChecked() is False
    assert fmtTab.stripUnicode.isChecked() is False
    assert fmtTab.replaceTabs.isChecked() is False
    assert fmtTab.keepBreaks.isChecked() is True
    assert fmtTab.showDialogue.isChecked() is False

    # Change values
    testFont = QFont("Arial", 11)
    fmtTab._textFont = testFont
    fmtTab.textFont.setText(describeFont(testFont))
    fmtTab.lineHeight.setValue(1.15)

    fmtTab.justifyText.setChecked(True)
    fmtTab.justifyOnBreak.setChecked(True)
    fmtTab.stripUnicode.setChecked(True)
    fmtTab.replaceTabs.setChecked(True)
    fmtTab.keepBreaks.setChecked(False)
    fmtTab.showDialogue.setChecked(True)

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getStr("format.textFont") == testFont.toString()
    assert sBuild.getFloat("format.lineHeight") == 1.15

    assert sBuild.getBool("format.justifyText") is True
    assert sBuild.getBool("format.justifyOnBreak") is True
    assert sBuild.getBool("format.stripUnicode") is True
    assert sBuild.getBool("format.replaceTabs") is True
    assert sBuild.getBool("format.keepBreaks") is False
    assert sBuild.getBool("format.showDialogue") is True

    # Check that the font dialog doesn't fail
    with monkeypatch.context() as mp:
        font = QFont()
        font.setFamily("Times")
        font.setPointSize(10)
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (font, True))

        fmtTab.btnTextFont.click()
        assert fmtTab._textFont == font

    # Cancelling the font dialog leaves the font unchanged
    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (font, False))
        fmtTab.btnTextFont.click()
        assert fmtTab._textFont == font

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_FormatHeadingFormat(monkeypatch, qtbot, nwGUI):
    """Test the Heading Format settings."""
    build = BuildSettings()

    build.setValue("format.colorHeadings", True)
    build.setValue("format.boldHeadings", True)
    build.setValue("format.upperHeadings", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 2)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.colorHeadings.isChecked() is True
    assert fmtTab.boldHeadings.isChecked() is True
    assert fmtTab.upperHeadings.isChecked() is False

    # Change values
    fmtTab.colorHeadings.setChecked(False)
    fmtTab.boldHeadings.setChecked(False)
    fmtTab.upperHeadings.setChecked(True)

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getBool("format.colorHeadings") is False
    assert sBuild.getBool("format.boldHeadings") is False
    assert sBuild.getBool("format.upperHeadings") is True

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_FormatFirstLineIndent(monkeypatch, qtbot, nwGUI):
    """Test the First Line Indent settings."""
    build = BuildSettings()

    build.setValue("format.firstLineIndent", False)
    build.setValue("format.firstIndentWidth", 1.4)
    build.setValue("format.indentFirstPar", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 3)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.firstIndent.isChecked() is False
    assert fmtTab.indentWidth.value() == 1.4
    assert fmtTab.indentFirstPar.isChecked() is False

    # Change values
    fmtTab.firstIndent.setChecked(True)
    fmtTab.indentWidth.setValue(2.0)
    fmtTab.indentFirstPar.setChecked(True)

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getBool("format.firstLineIndent") is True
    assert sBuild.getFloat("format.firstIndentWidth") == 2.0
    assert sBuild.getBool("format.indentFirstPar") is True

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


def testGuiBuildSettings_SizeAndMargins(monkeypatch, qtbot, nwGUI):
    """Test the Size & Margins settings."""
    build = BuildSettings()

    build.setValue("format.titleSize", nwStyles.H_SIZES[0])
    build.setValue("format.h1Size", nwStyles.H_SIZES[1])
    build.setValue("format.h2Size", nwStyles.H_SIZES[2])
    build.setValue("format.h3Size", nwStyles.H_SIZES[3])
    build.setValue("format.h4Size", nwStyles.H_SIZES[4])
    build.setValue("format.titleMarginT", nwStyles.T_MARGIN["H0"][0])
    build.setValue("format.titleMarginB", nwStyles.T_MARGIN["H0"][1])
    build.setValue("format.h1MarginT", nwStyles.T_MARGIN["H1"][0])
    build.setValue("format.h1MarginB", nwStyles.T_MARGIN["H1"][1])
    build.setValue("format.h2MarginT", nwStyles.T_MARGIN["H2"][0])
    build.setValue("format.h2MarginB", nwStyles.T_MARGIN["H2"][1])
    build.setValue("format.h3MarginT", nwStyles.T_MARGIN["H3"][0])
    build.setValue("format.h3MarginB", nwStyles.T_MARGIN["H3"][1])
    build.setValue("format.h4MarginT", nwStyles.T_MARGIN["H4"][0])
    build.setValue("format.h4MarginB", nwStyles.T_MARGIN["H4"][1])
    build.setValue("format.textMarginT", nwStyles.T_MARGIN["TT"][0])
    build.setValue("format.textMarginB", nwStyles.T_MARGIN["TT"][1])
    build.setValue("format.sepMarginT", nwStyles.T_MARGIN["SP"][0])
    build.setValue("format.sepMarginB", nwStyles.T_MARGIN["SP"][1])

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 3)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.titleSize.value() == nwStyles.H_SIZES[0]
    assert fmtTab.h1Size.value() == nwStyles.H_SIZES[1]
    assert fmtTab.h2Size.value() == nwStyles.H_SIZES[2]
    assert fmtTab.h3Size.value() == nwStyles.H_SIZES[3]
    assert fmtTab.h4Size.value() == nwStyles.H_SIZES[4]
    assert fmtTab.titleMarginT.value() == nwStyles.T_MARGIN["H0"][0]
    assert fmtTab.titleMarginB.value() == nwStyles.T_MARGIN["H0"][1]
    assert fmtTab.h1MarginT.value() == nwStyles.T_MARGIN["H1"][0]
    assert fmtTab.h1MarginB.value() == nwStyles.T_MARGIN["H1"][1]
    assert fmtTab.h2MarginT.value() == nwStyles.T_MARGIN["H2"][0]
    assert fmtTab.h2MarginB.value() == nwStyles.T_MARGIN["H2"][1]
    assert fmtTab.h3MarginT.value() == nwStyles.T_MARGIN["H3"][0]
    assert fmtTab.h3MarginB.value() == nwStyles.T_MARGIN["H3"][1]
    assert fmtTab.h4MarginT.value() == nwStyles.T_MARGIN["H4"][0]
    assert fmtTab.h4MarginB.value() == nwStyles.T_MARGIN["H4"][1]
    assert fmtTab.textMarginT.value() == nwStyles.T_MARGIN["TT"][0]
    assert fmtTab.textMarginB.value() == nwStyles.T_MARGIN["TT"][1]
    assert fmtTab.sepMarginT.value() == nwStyles.T_MARGIN["SP"][0]
    assert fmtTab.sepMarginB.value() == nwStyles.T_MARGIN["SP"][1]

    # Change values
    fmtTab.titleSize.setValue(1.0)
    fmtTab.h1Size.setValue(1.0)
    fmtTab.h2Size.setValue(1.0)
    fmtTab.h3Size.setValue(1.0)
    fmtTab.h4Size.setValue(1.0)
    fmtTab.titleMarginT.setValue(1.0)
    fmtTab.titleMarginB.setValue(1.0)
    fmtTab.h1MarginT.setValue(1.0)
    fmtTab.h1MarginB.setValue(1.0)
    fmtTab.h2MarginT.setValue(1.0)
    fmtTab.h2MarginB.setValue(1.0)
    fmtTab.h3MarginT.setValue(1.0)
    fmtTab.h3MarginB.setValue(1.0)
    fmtTab.h4MarginT.setValue(1.0)
    fmtTab.h4MarginB.setValue(1.0)
    fmtTab.textMarginT.setValue(1.0)
    fmtTab.textMarginB.setValue(1.0)
    fmtTab.sepMarginT.setValue(1.0)
    fmtTab.sepMarginB.setValue(1.0)

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getFloat("format.titleSize") == 1.0
    assert sBuild.getFloat("format.h1Size") == 1.0
    assert sBuild.getFloat("format.h2Size") == 1.0
    assert sBuild.getFloat("format.h3Size") == 1.0
    assert sBuild.getFloat("format.h4Size") == 1.0
    assert sBuild.getFloat("format.titleMarginT") == 1.0
    assert sBuild.getFloat("format.titleMarginB") == 1.0
    assert sBuild.getFloat("format.h1MarginT") == 1.0
    assert sBuild.getFloat("format.h1MarginB") == 1.0
    assert sBuild.getFloat("format.h2MarginT") == 1.0
    assert sBuild.getFloat("format.h2MarginB") == 1.0
    assert sBuild.getFloat("format.h3MarginT") == 1.0
    assert sBuild.getFloat("format.h3MarginB") == 1.0
    assert sBuild.getFloat("format.h4MarginT") == 1.0
    assert sBuild.getFloat("format.h4MarginB") == 1.0
    assert sBuild.getFloat("format.textMarginT") == 1.0
    assert sBuild.getFloat("format.textMarginB") == 1.0
    assert sBuild.getFloat("format.sepMarginT") == 1.0
    assert sBuild.getFloat("format.sepMarginB") == 1.0

    # Reset values
    fmtTab.btnTitleProps.click()
    fmtTab.btnH1Props.click()
    fmtTab.btnH2Props.click()
    fmtTab.btnH3Props.click()
    fmtTab.btnH4Props.click()
    fmtTab.btnTextProps.click()
    fmtTab.btnSepProps.click()

    assert fmtTab.titleSize.value() == nwStyles.H_SIZES[0]
    assert fmtTab.h1Size.value() == nwStyles.H_SIZES[1]
    assert fmtTab.h2Size.value() == nwStyles.H_SIZES[2]
    assert fmtTab.h3Size.value() == nwStyles.H_SIZES[3]
    assert fmtTab.h4Size.value() == nwStyles.H_SIZES[4]
    assert fmtTab.titleMarginT.value() == nwStyles.T_MARGIN["H0"][0]
    assert fmtTab.titleMarginB.value() == nwStyles.T_MARGIN["H0"][1]
    assert fmtTab.h1MarginT.value() == nwStyles.T_MARGIN["H1"][0]
    assert fmtTab.h1MarginB.value() == nwStyles.T_MARGIN["H1"][1]
    assert fmtTab.h2MarginT.value() == nwStyles.T_MARGIN["H2"][0]
    assert fmtTab.h2MarginB.value() == nwStyles.T_MARGIN["H2"][1]
    assert fmtTab.h3MarginT.value() == nwStyles.T_MARGIN["H3"][0]
    assert fmtTab.h3MarginB.value() == nwStyles.T_MARGIN["H3"][1]
    assert fmtTab.h4MarginT.value() == nwStyles.T_MARGIN["H4"][0]
    assert fmtTab.h4MarginB.value() == nwStyles.T_MARGIN["H4"][1]
    assert fmtTab.textMarginT.value() == nwStyles.T_MARGIN["TT"][0]
    assert fmtTab.textMarginB.value() == nwStyles.T_MARGIN["TT"][1]
    assert fmtTab.sepMarginT.value() == nwStyles.T_MARGIN["SP"][0]
    assert fmtTab.sepMarginB.value() == nwStyles.T_MARGIN["SP"][1]

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_FormatPageLayout(monkeypatch, qtbot, nwGUI):
    """Test the First Line Indent settings."""
    build = BuildSettings()

    build.setValue("format.pageUnit", "mm")
    build.setValue("format.pageSize", "Custom")
    build.setValue("format.pageWidth", 180.0)
    build.setValue("format.pageHeight", 250.0)
    build.setValue("format.topMargin", 25.0)
    build.setValue("format.bottomMargin", 25.0)
    build.setValue("format.leftMargin", 15.0)
    build.setValue("format.rightMargin", 15.0)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 4)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.pageUnit.currentData() == "mm"
    assert fmtTab.pageSize.currentData() == "Custom"
    assert fmtTab.pageWidth.value() == 180.0
    assert fmtTab.pageHeight.value() == 250.0
    assert fmtTab.topMargin.value() == 25.0
    assert fmtTab.bottomMargin.value() == 25.0
    assert fmtTab.leftMargin.value() == 15.0
    assert fmtTab.rightMargin.value() == 15.0

    # Change values
    fmtTab.pageUnit.setCurrentIndex(fmtTab.pageUnit.findData("cm"))
    fmtTab.pageSize.setCurrentIndex(fmtTab.pageSize.findData("A4"))

    # Save values
    fmtTab.saveContent()

    assert fmtTab.pageUnit.currentData() == "cm"
    assert fmtTab.pageSize.currentData() == "A4"
    assert fmtTab.pageWidth.value() == 21.0
    assert fmtTab.pageHeight.value() == 29.7
    assert fmtTab.topMargin.value() == 2.5
    assert fmtTab.bottomMargin.value() == 2.5
    assert fmtTab.leftMargin.value() == 1.5
    assert fmtTab.rightMargin.value() == 1.5

    # Stale/unknown unit and page size values are ignored on load
    bSettings._build.setValue("format.pageUnit", "furlongs")
    bSettings._build.setValue("format.pageSize", "Tabloid")
    unitBefore = fmtTab.pageUnit.currentData()
    sizeBefore = fmtTab.pageSize.currentData()
    bSettings.loadContent()
    assert fmtTab.pageUnit.currentData() == unitBefore
    assert fmtTab.pageSize.currentData() == sizeBefore

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_FormatOutput(qtbot, nwGUI):
    """Test the format-specific settings."""
    build = BuildSettings()

    build.setValue("doc.pageHeader", nwHeadFmt.DOC_AUTO)
    build.setValue("doc.pageCountOffset", 0)

    build.setValue("html.addStyles", False)
    build.setValue("html.preserveTabs", False)

    # Create the dialog and populate it
    bSettings = GuiBuildSettings(nwGUI, build)
    bSettings.show()
    bSettings.loadContent()

    fmtTab = bSettings.optTabFormatting
    button = bSettings.sidebar._group.button(bSettings.OPT_FORMATTING + 5)
    assert button is not None
    button.click()
    assert bSettings.toolStack.currentWidget() is fmtTab

    # Check initial values
    assert fmtTab.pageHeader.text() == nwHeadFmt.DOC_AUTO
    assert fmtTab.pageCountOffset.value() == 0

    assert fmtTab.htmlAddStyles.isChecked() is False
    assert fmtTab.htmlPreserveTabs.isChecked() is False

    # Change Values
    fmtTab.pageCountOffset.setValue(1)
    fmtTab.pageHeader.setText("Stuff")
    fmtTab.metaLanguage.setText("en-gb")

    fmtTab._refreshMetaLang()
    assert fmtTab.lblMetaLanguage.text() == "British English"

    # Toggle all
    fmtTab.htmlAddStyles.setChecked(True)
    fmtTab.htmlPreserveTabs.setChecked(True)

    # Save values
    fmtTab.saveContent()
    sBuild = bSettings._build
    assert sBuild.buildID == build.buildID

    assert sBuild.getStr("doc.pageHeader") == "Stuff"
    assert sBuild.getInt("doc.pageCountOffset") == 1
    assert sBuild.getStr("doc.metaLanguage") == "en-GB"

    assert sBuild.getBool("html.addStyles") is True
    assert sBuild.getBool("html.preserveTabs") is True

    # Reset header format
    fmtTab.btnPageHeader.click()
    assert fmtTab.pageHeader.text() == nwHeadFmt.DOC_AUTO

    # Finish
    bSettings._dialogButtonClicked(bSettings.btnClose)
    # qtbot.stop()


@pytest.mark.gui
def testGuiBuildSettings_MemoryLeakRegression(qtbot, nwGUI, projPath, mockRnd):
    """Test that the dialog is freed when it is closed."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    def factory() -> GuiBuildSettings:
        dialog = GuiBuildSettings(nwGUI, BuildSettings())
        dialog.loadContent()
        return dialog

    checkDialogFreedOnClose(qtbot, factory)
