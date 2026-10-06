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

from pathlib import Path
from shutil import copyfile

import pytest

from PyQt6.QtCore import QAbstractAnimation
from PyQt6.QtWidgets import QFileDialog, QLabel

from novelwriter import SHARED
from novelwriter.constants import nwFiles
from novelwriter.enum import nwChange, nwView
from novelwriter.shared import _GuiAlert
from novelwriter.story.outline import GuiOutlineViewSettings, GuiStoryOutlineView
from novelwriter.story.storysettings import OutlineViewSettings, StoryViewCollection, StoryViewSettings
from novelwriter.story.storyviewbase import GuiStorySettingsBase, GuiStoryViewBase

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


@pytest.mark.gui
def testStoryView_ManageViews(monkeypatch, nwGUI, prjLipsum):
    """Test adding, copying, moving and deleting story views."""
    storyView = nwGUI.storyView
    tabMain = storyView.tabMain

    # No views are loaded or added without a project
    nwGUI._changeView(nwView.STORY)
    storyView.addView.click()
    assert storyView._views is None
    assert tabMain.count() == 0
    assert storyView.addView.isEnabled() is False
    assert storyView.novelValue.isEnabled() is False

    assert nwGUI.openProject(prjLipsum)
    assert storyView.addView.isEnabled() is True
    viewsFile = SHARED.project.storage.getMetaFile(nwFiles.VIEWS_FILE)
    assert isinstance(viewsFile, Path)
    viewsFile.unlink(missing_ok=True)

    def tabNames():
        return [tabMain.tabText(i) for i in range(tabMain.count())]

    def savedNames():
        return [v.name for v in StoryViewCollection(SHARED.project).storyViews()]

    # Views are not loaded until the story view is shown
    storyView.addView.click()
    assert tabMain.count() == 0
    assert not viewsFile.exists()

    # A default outline view is created on first show
    nwGUI._changeView(nwView.STORY)
    assert tabNames() == ["Outline"]
    assert savedNames() == ["Outline"]
    assert isinstance(tabMain.currentWidget(), GuiStoryOutlineView)

    # Only known view kinds get a tab
    assert storyView._addTab(StoryViewSettings()) == -1

    # Add and copy views
    storyView.addView.click()
    assert tabNames() == ["Outline", "Outline"]
    assert tabMain.currentIndex() == 1

    storyView.copyView.click()
    assert tabNames() == ["Outline", "Outline", "Outline 2"]
    assert tabMain.currentIndex() == 2
    assert savedNames() == ["Outline", "Outline", "Outline 2"]

    # Moving a view is not saved immediately
    tabBar = tabMain.tabBar()
    assert tabBar is not None
    tabBar.moveTab(2, 0)
    assert tabNames() == ["Outline 2", "Outline", "Outline"]
    assert savedNames() == ["Outline", "Outline", "Outline 2"]

    # Showing the view again does not reload the views
    nwGUI._changeView(nwView.STORY)
    assert tabMain.count() == 3

    # Refresh and theme update
    storyView.refreshView.click()
    storyView.updateTheme()
    storyView.updateRootItem("", nwChange.UPDATE)

    # Delete a view, but cancel
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        storyView.delView.click()
    assert tabMain.count() == 3

    # Delete the current view
    tabMain.setCurrentIndex(0)
    storyView.delView.click()
    assert tabNames() == ["Outline", "Outline"]
    assert savedNames() == ["Outline", "Outline"]

    # The views, their order, and the current view are restored on reopen
    tabBar.moveTab(1, 0)
    tabMain.setCurrentIndex(1)
    viewIDs = [tabMain.widget(i).settings.viewID for i in range(tabMain.count())]  # type: ignore
    assert nwGUI.closeProject(isYes=True)
    assert tabMain.count() == 0
    assert storyView.novelValue.count() == 0
    assert storyView.novelValue.isEnabled() is False
    assert storyView.addView.isEnabled() is False
    assert nwGUI.openProject(prjLipsum)
    nwGUI._changeView(nwView.STORY)
    assert [tabMain.widget(i).settings.viewID for i in range(tabMain.count())] == viewIDs  # type: ignore
    assert tabMain.currentIndex() == 1

    # All views can be deleted
    storyView.delView.click()
    storyView.delView.click()
    assert tabMain.count() == 0
    assert savedNames() == []

    # Copy, edit and delete do nothing with no views
    storyView.copyView.click()
    storyView.editView.click()
    storyView.delView.click()
    assert tabMain.count() == 0

    # A new view can be added to an empty list
    storyView.addView.click()
    assert tabNames() == ["Outline"]
    assert savedNames() == ["Outline"]

    # Closing with no views clears the last view
    storyView.delView.click()
    assert nwGUI.closeProject(isYes=True)
    assert nwGUI.openProject(prjLipsum)
    assert StoryViewCollection(SHARED.project).lastView == ""


@pytest.mark.gui
def testStoryView_SettingsDialog(monkeypatch, nwGUI, prjLipsum):
    """Test editing story views with the settings dialog."""
    assert nwGUI.openProject(prjLipsum)
    storyView = nwGUI.storyView
    tabMain = storyView.tabMain
    viewsFile = SHARED.project.storage.getMetaFile(nwFiles.VIEWS_FILE)
    assert isinstance(viewsFile, Path)
    viewsFile.unlink(missing_ok=True)
    nwGUI._changeView(nwView.STORY)

    def openDialog() -> GuiOutlineViewSettings:
        storyView.editView.click()
        viewID = tabMain.currentWidget().settings.viewID  # type: ignore
        dialog = next(d for d in storyView._iterSettingsDialogs() if d.viewID == viewID)
        assert isinstance(dialog, GuiOutlineViewSettings)
        return dialog

    def savedValues():
        return [(v.name, v.getBool("outline.showScenes")) for v in StoryViewCollection(SHARED.project).storyViews()]

    asked = 0
    answer = True
    rebuilt = 0

    def question(*args, **kwargs) -> bool:
        nonlocal asked
        asked += 1
        return answer

    def refresh(self, rootHandle, force=False) -> None:
        nonlocal rebuilt
        rebuilt += int(force)

    monkeypatch.setattr(SHARED, "question", question)
    monkeypatch.setattr(GuiStoryOutlineView, "refresh", refresh)

    # Opening the dialog again reuses the open one
    dialog = openDialog()
    assert openDialog() is dialog

    # Saving updates the view and its tab, and rebuilds it
    dialog.viewName.setText("Scenes")
    dialog.showScenes.setChecked(False)
    dialog.btnSave.click()
    assert SHARED.findTopLevelWidget(GuiOutlineViewSettings) is None
    assert tabMain.tabText(0) == "Scenes"
    assert savedValues() == [("Scenes", False)]
    assert rebuilt == 1

    # A rename is saved on close without asking, and without a rebuild
    dialog = openDialog()
    dialog.viewName.setText("  Only  Scenes ")
    dialog.close()
    assert tabMain.tabText(0) == "Only Scenes"
    assert savedValues() == [("Only Scenes", False)]
    assert asked == 0
    assert rebuilt == 1

    # An empty name resolves to the default name
    dialog = openDialog()
    dialog.viewName.setText(" ")
    dialog.btnSave.click()
    assert tabMain.tabText(0) == "Outline"
    assert savedValues() == [("Outline", False)]
    assert rebuilt == 1

    # Closing without changes emits nothing
    dialog = openDialog()
    dialog.close()
    assert asked == 0
    assert rebuilt == 1

    # The page count unit follows the project count mode
    dialog = openDialog()
    assert "words" in [w.text() for w in dialog.findChildren(QLabel)]
    dialog.close()
    SHARED.project.data.setProjectTarget(0, None, True)

    # The sidebar, title and theme are handled by the base class
    dialog = openDialog()
    assert "characters" in [w.text() for w in dialog.findChildren(QLabel)]
    assert dialog.sidebar.accessibleName() == dialog.windowTitle()
    button = dialog.sidebar._group.button(1)
    assert button is not None
    button.click()
    storyView.updateTheme()

    # The Close button asks to save changes, which can be declined
    answer = False
    dialog.showScenes.setChecked(True)
    dialog.btnClose.click()
    assert SHARED.findTopLevelWidget(GuiOutlineViewSettings) is None
    assert savedValues() == [("Outline", False)]
    assert asked == 1
    assert rebuilt == 1
    answer = True

    # Settings for unknown views are ignored
    storyView._applyViewSettings(OutlineViewSettings())
    assert rebuilt == 1

    # Saving keeps the order, as it belongs to the tabs
    settings = tabMain.currentWidget().settings  # type: ignore
    dialog = openDialog()
    settings.setOrder(5)
    dialog.btnSave.click()
    assert settings.order == 5

    # Views without a settings dialog cannot be edited
    index = tabMain.addTab(GuiStoryViewBase(storyView, OutlineViewSettings()), "Base")
    tabMain.setCurrentIndex(index)
    storyView.editView.click()
    assert list(storyView._iterSettingsDialogs()) == []

    # Only the tab of the changed view is renamed
    renamed = settings.copy()
    renamed.setName("Renamed")
    storyView._applyViewSettings(renamed)
    assert tabMain.tabText(0) == "Renamed"
    assert tabMain.tabText(index) == "Base"
    renamed.setName("Outline")
    storyView._applyViewSettings(renamed)
    storyView._removeTab(index)

    # A view that is hidden when its settings change is rebuilt when shown
    dialog = openDialog()
    dialog.showSections.setChecked(True)
    nwGUI._changeView(nwView.PROJECT)
    dialog.btnSave.click()
    assert rebuilt == 1
    nwGUI._changeView(nwView.STORY)
    assert rebuilt == 2
    nwGUI._changeView(nwView.PROJECT)
    nwGUI._changeView(nwView.STORY)
    assert rebuilt == 2

    # Deleting a view discards only its own open dialog, without asking
    asked = 0
    other = openDialog()
    storyView.addView.click()
    dialog = openDialog()
    dialog.showScenes.setChecked(False)
    storyView.delView.click()
    assert asked == 1
    assert list(storyView._iterSettingsDialogs()) == [other]
    assert savedValues() == [("Outline", False)]

    # Closing the project closes the dialog, and saves the changes without a rebuild
    assert openDialog() is other
    other.showScenes.setChecked(True)
    count = rebuilt
    assert nwGUI.closeProject(isYes=True)
    assert asked == 2
    assert rebuilt == count
    assert SHARED.findTopLevelWidget(GuiOutlineViewSettings) is None

    # Settings changes are ignored with no project open
    storyView._applyViewSettings(OutlineViewSettings())
    assert rebuilt == count

    assert nwGUI.openProject(prjLipsum)
    assert savedValues() == [("Outline", True)]


@pytest.mark.gui
def testStoryView_LastHandle(nwGUI, prjLipsum):
    """Test that the selected novel folder is restored on reopen."""
    assert nwGUI.openProject(prjLipsum)
    storyView = nwGUI.storyView
    novelValue = storyView.novelValue
    rootHandle = novelValue.firstHandle
    assert rootHandle is not None

    # An invalid list format is rejected
    listFormat = novelValue._listFormat
    novelValue.setListFormat("No placeholder here")
    assert novelValue._listFormat == listFormat

    # Select the root folder, then the "All Novel Folders" entry
    novelValue.setCurrentIndex(novelValue.findData(rootHandle))
    assert SHARED.project.data.getLastHandle("story") == rootHandle
    novelValue.setCurrentIndex(novelValue.count() - 1)
    assert SHARED.project.data.getLastHandle("story") is None

    # Select the root folder, and reopen the project
    novelValue.setCurrentIndex(novelValue.findData(rootHandle))
    assert nwGUI.closeProject(isYes=True)
    assert nwGUI.openProject(prjLipsum)
    assert storyView.novelValue.handle == rootHandle


@pytest.mark.gui
def testStoryView_LazyLoad(nwGUI, prjLipsum):
    """Test that views are only built when shown."""
    assert nwGUI.openProject(prjLipsum)
    storyView = nwGUI.storyView
    tabMain = storyView.tabMain
    novelValue = storyView.novelValue
    rootHandle = novelValue.firstHandle
    assert rootHandle is not None

    def built():
        return [tabMain.widget(i).outlineContent._built for i in range(tabMain.count())]  # type: ignore

    # Create two extra views, and reopen with the first view active
    nwGUI._changeView(nwView.STORY)
    storyView.addView.click()
    storyView.addView.click()
    tabMain.setCurrentIndex(0)
    assert nwGUI.closeProject(isYes=True)
    assert nwGUI.openProject(prjLipsum)
    assert tabMain.count() == 0

    # Only the active view is built when the story view is first shown
    nwGUI._changeView(nwView.STORY)
    assert built() == [True, False, False]

    # Other views are built when switched to
    tabMain.setCurrentIndex(2)
    assert built() == [True, False, True]

    # Preferences are applied without building any views
    storyView.initSettings()
    assert built() == [True, False, True]

    # Changing the novel while hidden does not rebuild the view
    current = tabMain.currentWidget().outlineContent  # type: ignore
    nwGUI._changeView(nwView.PROJECT)
    novelValue.setCurrentIndex(novelValue.findData(rootHandle))
    assert current._lastHandle is None

    # It is rebuilt when the story view is shown again
    nwGUI._changeView(nwView.STORY)
    assert current._lastHandle == rootHandle

    # Rebuilding the index while visible rebuilds the current view
    revision = current._lastRevision
    nwGUI.rebuildIndex()
    assert current._lastRevision == SHARED.project.index.indexRevision
    assert current._lastRevision > revision


@pytest.mark.gui
def testStoryView_Highlight(qtbot, nwGUI, prjLipsum):
    """Test highlighting a reference in the views."""
    assert nwGUI.openProject(prjLipsum)
    storyView = nwGUI.storyView
    tabMain = storyView.tabMain
    combo = storyView.highlightValue
    lineEdit = combo.lineEdit()
    assert lineEdit is not None

    def highlights():
        return [tabMain.widget(i).outlineContent._delegate._highlight for i in range(tabMain.count())]  # type: ignore

    # The references are listed when the view is shown
    nwGUI._changeView(nwView.STORY)
    assert [combo.itemData(i) for i in range(combo.count())] == ["", "bod", "europe", "main"]
    assert [combo.itemText(i) for i in range(combo.count())] == ["", "Bod", "Europe", "Main"]

    # The completer matches any part of the name
    completer = combo.completer()
    assert completer is not None
    assert completer.popup() is not None
    completer.setCompletionPrefix("UR")
    assert completer.completionCount() == 1
    assert completer.currentCompletion() == "Europe"

    # Selecting a reference highlights it in all views, also new ones
    combo.setCurrentIndex(combo.findData("bod"))
    assert highlights() == [{"bod"}]
    storyView.addView.click()
    assert highlights() == [{"bod"}, {"bod"}]

    # Matching text selects a reference, and other text is reverted
    lineEdit.setText("europe")
    lineEdit.editingFinished.emit()
    assert combo.currentData() == "europe"
    lineEdit.setText("Eur")
    lineEdit.editingFinished.emit()
    assert combo.currentText() == "Europe"
    assert highlights() == [{"europe"}, {"europe"}]

    # Clearing the text clears the highlight
    lineEdit.clear()
    assert combo.currentIndex() == 0
    assert highlights() == [set(), set()]

    # The selection is kept when the list is rebuilt
    combo.setCurrentIndex(combo.findData("main"))
    storyView.updateTheme()
    assert combo.currentData() == "main"
    assert highlights() == [{"main"}, {"main"}]

    # A reference that no longer exists is cleared
    storyView._highlight = {"gone"}
    nwGUI.rebuildIndex()
    assert combo.currentIndex() == 0
    assert highlights() == [set(), set()]

    # Closing the project saves the highlight, and clears the list
    combo.setCurrentIndex(combo.findData("bod"))
    assert nwGUI.closeProject(isYes=True)
    assert combo.count() == 0
    assert storyView._highlight == set()
    assert not combo.isEnabled()
    storyView.updateTheme()
    assert combo.count() == 0

    # The highlight is restored when the views are loaded
    assert nwGUI.openProject(prjLipsum)
    nwGUI._changeView(nwView.STORY)
    assert combo.currentData() == "bod"
    assert highlights() == [{"bod"}, {"bod"}]

    # Let the clear button fade out
    running = QAbstractAnimation.State.Running
    qtbot.waitUntil(lambda: all(a.state() != running for a in combo.findChildren(QAbstractAnimation)))


@pytest.mark.gui
def testStoryView_BaseClass(qtbot, nwGUI):
    """Test the story view base class."""
    settings = OutlineViewSettings()
    view = GuiStoryViewBase(nwGUI, settings)
    qtbot.addWidget(view)
    assert view.settings is settings

    # The default implementations do nothing
    view.updateTheme()
    view.initSettings()
    view.refresh(None)
    view.saveViewState()
    view.setHighlight({"bod"})
    assert view.settingsDialog() is None


@pytest.mark.gui
def testStoryView_SettingsPages(qtbot, nwGUI):
    """Test the story view settings dialog base class pages."""

    class Dialog(GuiStorySettingsBase):
        def buildPages(self) -> None:
            self.first = QLabel("First", self)
            self.last = QLabel("Last", self)
            self.setPageLabel("Before")
            self.setPageLabel("After", after=True)
            self.addPage(self.last, "Last", 2, after=True)
            self.addPage(self.first, "First", 1)

        def buildForm(self) -> None:
            self.form.addGroupLabel("Group", self.FORM_SECTION + 1)

    # The default implementation has only the form
    dialog = GuiStorySettingsBase(nwGUI, OutlineViewSettings())
    assert dialog.toolStack.count() == 1
    assert dialog.sidebar.findChildren(QLabel) == []
    assert dialog.toolStack.currentWidget() is dialog.form
    dialog.discardAndClose()

    # Pages are placed before and after the form, and the first is selected
    dialog = Dialog(nwGUI, OutlineViewSettings())
    stack = dialog.toolStack
    assert [stack.widget(i) for i in range(stack.count())] == [dialog.first, dialog.form, dialog.last]
    assert [b.text() for b in dialog.sidebar._group.buttons()] == ["First", "Last"]
    assert [x.text() for x in dialog.sidebar.findChildren(QLabel)] == ["Before", "After"]
    assert dialog.sidebar._group.checkedId() == 1
    assert stack.currentWidget() is dialog.first

    # Selecting a page or a form section switches the stack
    dialog._stackPageSelected(2)
    assert stack.currentWidget() is dialog.last
    dialog._stackPageSelected(GuiStorySettingsBase.FORM_SECTION + 1)
    assert stack.currentWidget() is dialog.form
    dialog.discardAndClose()
