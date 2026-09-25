"""
novelWriter - Main GUI Windows Tests
====================================

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

import shutil

from pathlib import Path
from shutil import copyfile
from unittest.mock import MagicMock, Mock

import pytest

from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QCloseEvent, QGuiApplication, QPalette, QStyleHints
from PyQt6.QtWidgets import QApplication, QFileDialog, QInputDialog, QWidget

from novelwriter import CONFIG, SHARED, __hexversion__
from novelwriter.common import jsonEncode
from novelwriter.config import DEF_GUI_DARK, DEF_GUI_LIGHT
from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.dialogs.preferences import GuiNeedsUpdate
from novelwriter.editor.editor import GuiDocEditor
from novelwriter.enum import (
    nwDocAction,
    nwDocMode,
    nwFocus,
    nwItemClass,
    nwItemType,
    nwState,
    nwTheme,
    nwView,
    nwVimMode,
)
from novelwriter.gui.noveltree import GuiNovelView
from novelwriter.gui.projtree import GuiProjectTree, GuiProjectView
from novelwriter.guimain import GuiMain
from novelwriter.manuscript.manuscript import GuiManuscript
from novelwriter.shared import _GuiAlert
from novelwriter.tools.welcome import GuiWelcome
from novelwriter.tools.writingstats import GuiWritingStats
from novelwriter.types import (
    QtKeyBackspace,
    QtKeyEnter,
    QtKeyEscape,
    QtKeyLeft,
    QtKeyReturn,
    QtKeyRight,
    QtModCtrl,
    QtModShift,
    QtScrollAlwaysOff,
)

from tests.helpers import NWD_IGNORE, XML_IGNORE, C, buildTestProject, cmpFiles
from tests.mocked import causeOSError

KEY_DELAY = 1


@pytest.mark.gui
def testGuiMain_ProjectBlocker(nwGUI):
    """Test the blocking of features when there's no project open."""
    # Test no-project blocking
    assert nwGUI.closeProject() is True
    assert nwGUI.saveProject() is False
    assert nwGUI.openDocument(None) is False
    assert nwGUI.viewDocument(None) is False
    assert nwGUI.importDocument() is False

    # These should all just do nothing and not raise
    nwGUI.closeDocument()
    nwGUI.rebuildIndex()
    nwGUI.openSelectedItem()
    nwGUI.openNextDocument(C.hSceneDoc, False, True)
    nwGUI._autoSaveProject()
    nwGUI.showProjectSettingsDialog()
    nwGUI.showNovelDetailsDialog()
    nwGUI.showBuildManuscriptDialog()
    nwGUI.showProjectWordListDialog()
    nwGUI.showWritingStatsDialog()


@pytest.mark.gui
def testGuiMain_Launch(qtbot, monkeypatch, nwGUI, projPath, fncPath):
    """Test the handling of launch tasks."""
    monkeypatch.setattr(GuiWelcome, "exec", lambda *a: None)
    CONFIG.lastNotes = "0x0"
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Open Lipsum project
    nwGUI.postLaunchTasks(projPath)
    assert SHARED.hasProject is True
    nwGUI.closeProject()
    assert SHARED.hasProject is False

    # Launch tasks still run fine without a QApplication instance to connect to
    with monkeypatch.context() as mp:
        mp.setattr(QApplication, "instance", lambda: None)
        nwGUI.postLaunchTasks(None)

    # Open as if called from Welcome
    nwGUI._openProjectFromWelcome(projPath)
    assert SHARED.hasProject is True
    nwGUI.closeProject()
    assert SHARED.hasProject is False

    # Open as if called from Welcome, invalid path
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI, "showWelcomeDialog", lambda *a: None)
        nwGUI._openProjectFromWelcome(None)
        assert SHARED.hasProject is False

    # Project open fails
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "openProject", lambda *a: False)
        assert nwGUI.openProject(projPath) is False

    # Handle locked project
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "openProject", lambda *a, **k: False)
        SHARED._lockedBy = ["a", "b", "c", "d"]
        assert nwGUI.openProject(projPath) is False
        SHARED._lockedBy = None

    assert nwGUI.openProject(projPath) is True
    nwGUI.closeProject()

    # Opening a project with no documents at all leaves the editor and
    # viewer empty
    emptyPath = fncPath / "empty"
    emptyPath.mkdir()
    project = SHARED.project
    project.storage.createNewProject(emptyPath)
    project.setDefaultStatusImport()
    project.data.setName("Empty")
    project.newRoot(nwItemClass.NOVEL)
    project.session.startSession()
    project.saveProject()
    project.closeProject(0.0)

    assert nwGUI.openProject(emptyPath) is True
    assert nwGUI.docEditor.docHandle is None
    assert nwGUI.docViewer.docHandle is None
    nwGUI.closeProject()

    # A broken index caused by a version upgrade does not show the
    # "index is broken" warning, but still rebuilds the index
    assert nwGUI.openProject(projPath) is True
    nwGUI.closeProject()

    warnMock = Mock()
    rebuildMock = Mock()
    with monkeypatch.context() as mp:
        mp.setattr(type(SHARED.project.index), "indexRebuild", property(lambda self: True))
        mp.setattr(type(SHARED.project.index), "indexUpgrade", property(lambda self: True))
        mp.setattr(SHARED, "warn", warnMock)
        mp.setattr(nwGUI, "rebuildIndex", rebuildMock)
        assert nwGUI.openProject(projPath) is True

    assert not any("index is broken" in str(call) for call in warnMock.call_args_list)
    assert rebuildMock.called is True
    nwGUI.closeProject()

    # Check that closes can be blocked
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert nwGUI.openProject(projPath) is True
        assert nwGUI.closeMain() is False
    nwGUI.closeProject()

    # Check that latest release info is set
    assert CONFIG.lastNotes != "0x0"

    # Set some config error
    CONFIG._hasError = True
    CONFIG._errData.append("Foo")

    # Check that project open dialog launches
    nwGUI.postLaunchTasks(None)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiWelcome) is not None, timeout=1000)
    welcome = SHARED.findTopLevelWidget(GuiWelcome)
    assert isinstance(welcome, GuiWelcome)
    welcome.show()
    welcome.close()

    # Config errors should be cleared
    assert SHARED.lastAlert == ["Foo"]
    assert CONFIG._hasError is False

    # The welcome dialog isn't repositioned when moveMainWin is disabled
    CONFIG.moveMainWin = False
    nwGUI.showWelcomeDialog()

    # Window sizing tolerates an invalid size list, and skips moving the
    # window when the size already matches the available screen
    nwGUI._setWindowSize([100])  # Wrong length, should not raise

    mockScreen = MagicMock()
    mockScreen.availableSize.return_value = QSize(1000, 700)
    mockScreen.geometry.return_value = QRect(0, 0, 1000, 700)
    with monkeypatch.context() as mp:
        mp.setattr(type(SHARED), "mainScreen", property(lambda self: mockScreen))
        CONFIG.moveMainWin = False
        nwGUI._setWindowSize([1000, 700])

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_IndexRebuild(qtbot, monkeypatch, nwGUI, projPath):
    """Test that a genuinely invalid index cache, as opposed to one
    from a version upgrade, triggers the "index is broken" warning as
    well as a rebuild of the index.
    """
    buildTestProject(NWProject(), projPath)
    indexFile = projPath / "meta" / nwFiles.INDEX_FILE
    assert indexFile.is_file()

    # Corrupt the cached index file on disk
    indexFile.write_text("{not valid json", encoding="utf-8")

    warnMock = Mock()
    rebuildMock = Mock()
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "warn", warnMock)
        mp.setattr(nwGUI, "rebuildIndex", rebuildMock)
        assert nwGUI.openProject(projPath) is True

    assert SHARED.project.index.indexUpgrade is False
    assert any("index is broken" in str(call) for call in warnMock.call_args_list)
    assert rebuildMock.called is True
    nwGUI.closeProject()


@pytest.mark.gui
def testGuiMain_ProjectTreeItems(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test handling of project tree items based on GUI focus states."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.rebuildIndex()  # A project built off-GUI has no index cache to load
    nwGUI.closeDocument()  # Opening the project auto-restores a document

    sHandle = "000000000000f"
    nwGUI.openSelectedItem()
    assert nwGUI.docEditor.docHandle is None

    # Project Tree has focus
    nwGUI._changeView(nwView.PROJECT)
    nwGUI._switchFocus(nwFocus.TREE)
    nwGUI.projStack.setCurrentIndex(0)
    with monkeypatch.context() as mp:
        mp.setattr(GuiProjectTree, "hasFocus", lambda *a: True)
        mp.setattr(GuiNovelView, "treeHasFocus", lambda *a: False)
        assert nwGUI.docEditor.docHandle is None
        nwGUI.projView.projTree.setSelectedHandle(sHandle)
        nwGUI.projView.projTree.openSelectedItem()
        assert nwGUI.docEditor.docHandle == sHandle
        nwGUI.closeDocument()

        # A selected item that isn't a file is ignored
        nwGUI.projView.projTree.setSelectedHandle(C.hChapterDir)
        nwGUI.openSelectedItem()
        assert nwGUI.docEditor.docHandle is None

    # Novel Tree has focus
    nwGUI._changeView(nwView.NOVEL)
    with monkeypatch.context() as mp:
        mp.setattr(GuiProjectView, "treeHasFocus", lambda *a: False)
        mp.setattr(GuiNovelView, "treeHasFocus", lambda *a: True)
        assert nwGUI.docEditor.docHandle is None

        model = nwGUI.novelView.novelTree._getModel()
        assert model is not None

        # No selection is ignored
        nwGUI.novelView.novelTree.setCurrentIndex(model.createIndex(9999, 0))
        nwGUI.novelView.novelTree.openSelectedItem()
        assert nwGUI.docEditor.docHandle is None

        nwGUI.novelView.novelTree.setCurrentIndex(model.createIndex(2, 0))
        nwGUI.novelView.novelTree.openSelectedItem()
        assert nwGUI.docEditor.docHandle == sHandle
        nwGUI.closeDocument()

        # The main GUI dispatcher also routes to the novel tree
        nwGUI.openSelectedItem()
        assert nwGUI.docEditor.docHandle == sHandle
        nwGUI.closeDocument()

        # ... and to viewing the document when Shift is held
        with monkeypatch.context() as mpShift:
            mpShift.setattr(QApplication, "keyboardModifiers", lambda: QtModShift)
            nwGUI.openSelectedItem()
        assert nwGUI.docViewer.docHandle == sHandle
        nwGUI.closeDocViewer()

    # Internal open-document slots ignore a missing or invalid handle
    nwGUI._openDocument(None, nwDocMode.EDIT, "", True)
    assert nwGUI.docEditor.docHandle is None

    nwGUI._openDocumentSelection(C.hInvalid, 0, 3, True)
    assert nwGUI.docEditor.docHandle is None

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_UpdateTheme(qtbot, nwGUI):
    """Test updating the theme in the GUI."""
    theme = SHARED.theme
    CONFIG.themeMode = nwTheme.DARK
    CONFIG.darkTheme = DEF_GUI_DARK
    CONFIG.lightTheme = DEF_GUI_LIGHT
    theme.loadTheme()
    assert theme.isDarkTheme is True

    nwGUI._processConfigChanges(GuiNeedsUpdate(False, True, False, False, False, False, False, False, False))
    nwGUI._processConfigChanges(GuiNeedsUpdate(True, True, True, True, True, True, True, True, True))

    # Check editor syntax
    syntax = SHARED.theme.syntaxTheme
    assert nwGUI.docEditor.palette().color(QPalette.ColorRole.Window) == syntax.back
    assert nwGUI.docEditor.docHeader.palette().color(QPalette.ColorRole.Window) == syntax.back
    assert nwGUI.docViewer.palette().color(QPalette.ColorRole.Window) == syntax.back
    assert nwGUI.docViewer.docHeader.palette().color(QPalette.ColorRole.Window) == syntax.back

    # Update by check
    CONFIG.themeMode = nwTheme.LIGHT
    nwGUI.checkThemeUpdate()
    assert theme.isDarkTheme is False

    # Checking again without any further change does nothing
    nwGUI.checkThemeUpdate()
    assert theme.isDarkTheme is False

    # qtbot.stop()


@pytest.mark.gui
@pytest.mark.skipif(not CONFIG.checkMinQtVersion(0x060500), reason="Requires Qt 6.5+")
def testGuiMain_OSThemeChangeAndClose(qtbot, monkeypatch, nwGUI, projPath):
    """Test that the OS colour scheme change signal reaches the theme
    loader via the connected slot, that isDesktopDarkMode falls back to
    the palette check when there is no styleHints object, and that the
    close event handles both a blocked close and a missing theme hints
    object.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    CONFIG.themeMode = nwTheme.AUTO
    CONFIG.darkTheme = DEF_GUI_DARK
    CONFIG.lightTheme = DEF_GUI_LIGHT

    # Emitting the real OS signal reaches the connected slot, which
    # feeds the explicit colour scheme through to the theme loader. The
    # desktop hint is mocked to agree, since checkThemeUpdate's own
    # refreshThemeColors() call reloads the theme again without the
    # explicit scheme, falling back to the live desktop hint.
    assert nwGUI._themeHints is not None
    with monkeypatch.context() as mp:
        mp.setattr(QStyleHints, "colorScheme", lambda *a: Qt.ColorScheme.Dark)
        nwGUI._themeHints.colorSchemeChanged.emit(Qt.ColorScheme.Dark)
    assert SHARED.theme.isDarkTheme is True

    with monkeypatch.context() as mp:
        mp.setattr(QStyleHints, "colorScheme", lambda *a: Qt.ColorScheme.Light)
        nwGUI._themeHints.colorSchemeChanged.emit(Qt.ColorScheme.Light)
    assert SHARED.theme.isDarkTheme is False

    # With no styleHints object at all, isDesktopDarkMode falls back to
    # the palette check instead of raising
    with monkeypatch.context() as mp:
        mp.setattr(QGuiApplication, "styleHints", staticmethod(lambda: None))
        SHARED.theme.isDesktopDarkMode()

    # A blocked close ignores the event and leaves the hints connected
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        event = QCloseEvent()
        nwGUI.closeEvent(event)
        assert event.isAccepted() is False

    # The theme hint object must be explicitly disconnected, since it is
    # connected to a singleton and will therefore bleed over into other tests
    nwGUI._themeHints.colorSchemeChanged.disconnect(nwGUI._themeChangedSlot)
    nwGUI._themeHints = None
    event = QCloseEvent()
    nwGUI.closeEvent(event)
    assert event.isAccepted() is True


@pytest.mark.gui
def testGuiMain_ProcessConfigChanges_LightweightSettings(qtbot, nwGUI, projPath, mockRnd):
    """Test the lightweight settings path of _processConfigChanges, which
    must refresh the document headers on every call, but must only reset
    Vim mode when the Vim setting itself changed (issue: an unrelated
    preferences save must not silently drop the user out of Insert mode).
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc)
    assert nwGUI.viewDocument(C.hSceneDoc)

    docEditor = nwGUI.docEditor
    docViewer = nwGUI.docViewer

    CONFIG.vimMode = True
    docEditor._vim.setMode(nwVimMode.INSERT)

    # Clear the headers so we can tell if they were refreshed
    docEditor.docHeader._docHandle = None
    docViewer.docHeader._docHandle = None

    # A save where nothing relevant changed, and Vim was not touched,
    # must still refresh the headers, but must not reset Vim mode
    noChange = GuiNeedsUpdate(
        restart=False,
        tree=False,
        theme=False,
        syntax=False,
        spelling=False,
        vim=False,
        editor=False,
        viewer=False,
        viewport=False,
    )
    nwGUI._processConfigChanges(noChange)
    assert docEditor.docHeader._docHandle == C.hSceneDoc
    assert docViewer.docHeader._docHandle == C.hSceneDoc
    assert docEditor._vim.mode == nwVimMode.INSERT

    # A save where the Vim setting changed must reset the mode to Normal
    vimChanged = GuiNeedsUpdate(
        restart=False,
        tree=False,
        theme=False,
        syntax=False,
        spelling=False,
        vim=True,
        editor=False,
        viewer=False,
        viewport=False,
    )
    nwGUI._processConfigChanges(vimChanged)
    assert docEditor._vim.mode == nwVimMode.NORMAL

    # A save that fully reinitialises the editor and viewer must not
    # additionally run the lightweight path
    docEditor._vim.setMode(nwVimMode.INSERT)
    fullReinit = GuiNeedsUpdate(
        restart=False,
        tree=False,
        theme=False,
        syntax=False,
        spelling=False,
        vim=False,
        editor=True,
        viewer=True,
        viewport=False,
    )
    nwGUI._processConfigChanges(fullReinit)
    assert docEditor._vim.mode == nwVimMode.NORMAL

    # A viewport-only change must reinitialise the viewport on both the
    # editor and viewer even though neither is otherwise reinitialised
    CONFIG.hideVScroll = True
    CONFIG.hideHScroll = True
    viewportOnly = GuiNeedsUpdate(
        restart=False,
        tree=False,
        theme=False,
        syntax=False,
        spelling=False,
        vim=False,
        editor=False,
        viewer=False,
        viewport=True,
    )
    nwGUI._processConfigChanges(viewportOnly)
    assert docEditor.verticalScrollBarPolicy() == QtScrollAlwaysOff
    assert docEditor.horizontalScrollBarPolicy() == QtScrollAlwaysOff
    assert docViewer.verticalScrollBarPolicy() == QtScrollAlwaysOff
    assert docViewer.horizontalScrollBarPolicy() == QtScrollAlwaysOff

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_Editing(qtbot, monkeypatch, nwGUI, projPath, tstPaths, mockRnd):
    """Test the document editor."""
    monkeypatch.setattr(GuiProjectTree, "hasFocus", lambda *a: True)
    monkeypatch.setattr(GuiDocEditor, "hasFocus", lambda *a: True)
    monkeypatch.setattr(QInputDialog, "getText", lambda *a, text: (text, True))
    monkeypatch.setattr(GuiEditLabel, "getLabel", lambda *a, text: (text, True))

    # Create new, save, close project
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.saveProject()
    assert nwGUI.closeProject()

    assert len(SHARED.project.tree) == 0
    assert len(SHARED.project.tree._items) == 0
    assert len(SHARED.project.tree._nodes) == 0
    assert SHARED.project.data.name == ""
    assert SHARED.project.data.author == ""
    assert SHARED.project.data.spellCheck is False

    # Check the files
    projFile = projPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "guiEditor_Main_Initial_nwProject.nwx"
    compFile = tstPaths.refDir / "guiEditor_Main_Initial_nwProject.nwx"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)

    # Re-open project
    assert nwGUI.openProject(projPath)

    # Check that we loaded the data
    assert len(SHARED.project.tree) == 9
    assert SHARED.project.tree.model.root.childCount() == 5
    assert SHARED.project.tree.trash is not None  # Created automatically
    assert SHARED.project.data.name == "New Project"
    assert SHARED.project.data.author == "Jane Doe"
    assert SHARED.project.data.spellCheck is False

    # Check that tree items have been created
    assert SHARED.project.tree[C.hNovelRoot] is not None
    assert SHARED.project.tree[C.hPlotRoot] is not None
    assert SHARED.project.tree[C.hCharRoot] is not None
    assert SHARED.project.tree[C.hWorldRoot] is not None
    assert SHARED.project.tree[C.hTitlePage] is not None
    assert SHARED.project.tree[C.hChapterDir] is not None
    assert SHARED.project.tree[C.hChapterDoc] is not None
    assert SHARED.project.tree[C.hSceneDoc] is not None

    nwGUI.mainMenu.aSpellCheck.setChecked(True)
    nwGUI.mainMenu._toggleSpellCheck()

    # Change some settings
    CONFIG.hideHScroll = True
    CONFIG.hideVScroll = True
    CONFIG.autoScroll = False

    # Add a Character File
    nwGUI._changeView(nwView.PROJECT)
    nwGUI.projView.projTree.expandAll()
    nwGUI.projView.projTree.clearSelection()
    nwGUI.projView.projTree.setSelectedHandle(C.hCharRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, None, isNote=True)
    nwGUI.projView.projTree.expandAll()
    nwGUI.openSelectedItem()

    # Text Editor
    # ===========

    # Syntax Highlighting
    CONFIG.dialogStyle = 3
    CONFIG.dialogLine = "\u2013"
    CONFIG.altDialogOpen = "<|"
    CONFIG.altDialogClose = "|>"

    docEditor = nwGUI.docEditor
    docEditor._qDocument.syntaxHighlighter.initHighlighter()

    # Type something into the document
    nwGUI.docEditor.setFocus()
    qtbot.keyClick(docEditor, "a", modifier=QtModCtrl, delay=KEY_DELAY)
    for c in "# Jane Doe":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@tag: Jane":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "This is a file about Jane.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Add a Plot File
    nwGUI.projView.projTree.expandAll()
    nwGUI.projView.projTree.clearSelection()
    nwGUI.projView.projTree.setSelectedHandle(C.hPlotRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, None, isNote=True)
    nwGUI.projView.projTree.expandAll()
    nwGUI.openSelectedItem()

    # Type something into the document
    nwGUI.docEditor.setFocus()
    qtbot.keyClick(docEditor, "a", modifier=QtModCtrl, delay=KEY_DELAY)
    for c in "# Main Plot":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@tag: MainPlot":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "This is a file [i]detailing[/i] the main plot.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Add a World File
    nwGUI.projView.projTree.expandAll()
    nwGUI.projView.projTree.clearSelection()
    nwGUI.projView.projTree.setSelectedHandle(C.hWorldRoot)
    nwGUI.projView.projTree.newTreeItem(nwItemType.FILE, None, isNote=True)
    nwGUI.projView.projTree.expandAll()
    nwGUI.openSelectedItem()

    # Add Some Text
    docEditor.replaceText("Hello World!")
    assert docEditor.getText() == "Hello World!"
    docEditor.replaceText("")

    # Type something into the document
    nwGUI.docEditor.setFocus()
    qtbot.keyClick(docEditor, "a", modifier=QtModCtrl, delay=KEY_DELAY)
    for c in "# Main Location":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@tag: Home":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "This is a file describing Jane's home.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Trigger autosaves before making more changes
    nwGUI._autoSaveDocument()
    nwGUI._autoSaveProject()

    # Select the 'New Scene' file
    nwGUI.projView.projTree.expandAll()
    nwGUI.projView.projTree.clearSelection()
    nwGUI.projView.projTree.setSelectedHandle(C.hSceneDoc)
    nwGUI.openSelectedItem()

    # Type something into the document
    nwGUI.docEditor.setFocus()
    qtbot.keyClick(docEditor, "a", modifier=QtModCtrl, delay=KEY_DELAY)
    for c in "# Novel":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "## Chapter":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "@pov: Jane":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@plot: MainPlot":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "### Scene":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "% How about a comment?":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@pov: Jane":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@plot: MainPlot":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    for c in "@location: Home":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "#### Some Section":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "@char: Jane":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "This is a paragraph of nonsense text.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Don't allow Shift+Enter to insert a line separator (issue #1150)
    for c in "This is another paragraph":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyEnter, modifier=QtModShift, delay=KEY_DELAY)
    for c in "with a line separator in it.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Auto-Replace
    # ============

    for c in (
        "This is another paragraph of much longer nonsense text. It is in fact 1 very very NONSENSICAL nonsense text! "
    ):
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "We can also try replacing \"quotes\", even single 'quotes' are replaced. ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "Isn't that nice? ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "We can hyphen-ate, make dashes -- and even longer dashes --- if we want. ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "We can even go on to a ---- hotizontal bar. ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "Ellipsis? Not a problem either ... ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "How about three hyphens - -":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyBackspace, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    for c in "- for long dash? It works too. ":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    for c in "Even four hyphens - - -":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyBackspace, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyBackspace, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    for c in "- for a horizontal works!":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Dialogue
    # ========

    for c in '"Full line double quoted text."':
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "'Full line single quoted text.'":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Insert spaces before and after quotes
    CONFIG.fmtPadBefore = "\u201d"
    CONFIG.fmtPadAfter = "\u201c"
    docEditor.initEditor()

    for c in 'Some "double quoted text with spaces padded". Ok?':
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)

    # Check that we can insert a line break in the text without
    # triggering the padding (Issue #2586)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyLeft, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyRight, delay=KEY_DELAY)

    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    CONFIG.fmtPadBefore = ""
    CONFIG.fmtPadAfter = ""
    docEditor.initEditor()

    # Dialogue Line
    for c in "-- Hi, I am a character speaking.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Narrator Break
    CONFIG.narratorBreak = "\u2013"
    docEditor = nwGUI.docEditor
    docEditor._qDocument.syntaxHighlighter.initHighlighter()

    for c in "-- Hi, I am also a character speaking, -- said another character. -- How are you?":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    # Special Formatting
    # ==================

    # Insert spaces before colon, but ignore tags
    CONFIG.fmtPadBefore = ":"
    docEditor.initEditor()

    for c in "@object: NoSpaceAdded":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "% synopsis: Space before this is OK.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "%Footnote.abc: A simple footnote.":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "Add space before this colon: See?":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "But don't add a double space : See?":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    CONFIG.fmtPadBefore = ""
    docEditor.initEditor()

    # Indent and Align
    # ================

    nwGUI._switchFocus(nwView.EDITOR)
    for c in '\t"Tab-indented text"':
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in '>"Paragraph-indented text"':
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in '>>"Right-aligned text"':
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in "\t'Tab-indented text'":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in ">'Paragraph-indented text'":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    for c in ">>'Right-aligned text'":
        qtbot.keyClick(docEditor, c, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)
    qtbot.keyClick(docEditor, QtKeyReturn, delay=KEY_DELAY)

    docEditor._updateDocCounts(0, 0, 0)

    # Check Files
    # ===========

    # Save the document
    assert docEditor.docChanged
    nwGUI.saveDocument()
    assert docEditor.docChanged is False
    nwGUI.forceSaveDocument()
    assert docEditor.docChanged is False
    nwGUI.rebuildIndex()

    # Open and view the edited document
    nwGUI.docViewer.setFocus()
    assert nwGUI.openDocument(C.hSceneDoc)
    assert nwGUI.viewDocument(C.hSceneDoc)
    assert nwGUI.saveProject()
    assert nwGUI.closeViewerPanel()

    # Check the files
    projFile = projPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "guiEditor_Main_Final_nwProject.nwx"
    compFile = tstPaths.refDir / "guiEditor_Main_Final_nwProject.nwx"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=(*XML_IGNORE, "<spellCheck"))

    projFile = projPath / "content" / "000000000000f.md"
    testFile = tstPaths.outDir / "guiEditor_Main_Final_000000000000f.md"
    compFile = tstPaths.refDir / "guiEditor_Main_Final_000000000000f.md"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    projFile = projPath / "content" / "0000000000011.md"
    testFile = tstPaths.outDir / "guiEditor_Main_Final_0000000000011.md"
    compFile = tstPaths.refDir / "guiEditor_Main_Final_0000000000011.md"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    projFile = projPath / "content" / "0000000000012.md"
    testFile = tstPaths.outDir / "guiEditor_Main_Final_0000000000012.md"
    compFile = tstPaths.refDir / "guiEditor_Main_Final_0000000000012.md"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    projFile = projPath / "content" / "0000000000013.md"
    testFile = tstPaths.outDir / "guiEditor_Main_Final_0000000000013.md"
    compFile = tstPaths.refDir / "guiEditor_Main_Final_0000000000013.md"
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_Viewing(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test the document viewer."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.closeProject()

    # View before a project is open does nothing
    assert nwGUI.splitView.isVisible() is False
    assert nwGUI.viewDocument(None) is False
    assert nwGUI.splitView.isVisible() is False

    # Open project requires a path
    assert nwGUI.openProject(None) is False
    assert SHARED.hasProject is False

    # Open the test project, properly
    nwGUI.openProject(projPath)
    assert nwGUI.docEditor.docHandle == C.hTitlePage

    # If editor has focus, open that document
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: True)
        nwGUI.viewDocument(None)
        assert nwGUI.docViewer.docHandle == C.hTitlePage
    nwGUI.closeDocViewer()

    # If editor does not have focus, open selected handle
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        nwGUI.projView.projTree.setSelectedHandle(C.hSceneDoc)
        nwGUI.viewDocument(None)
        assert nwGUI.docViewer.docHandle == C.hSceneDoc

    # If there is no selection, get last selected
    SHARED.project.data.setLastHandle(C.hChapterDoc, "viewer")
    assert SHARED.project.data.getLastHandle("viewer") == C.hChapterDoc
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        nwGUI.projView.projTree.clearSelection()
        nwGUI.viewDocument(None)
        assert nwGUI.docViewer.docHandle == C.hChapterDoc

    # If all fails, don't open anything
    SHARED.project.data.setLastHandle(None, "viewer")
    assert SHARED.project.data.getLastHandle("viewer") is None
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        nwGUI.projView.projTree.clearSelection()
        assert nwGUI.viewDocument(None) is False

    # If editor doc was edited and requested for the viewer, save it first
    nwGUI.openDocument(C.hSceneDoc)
    nwGUI.docEditor.setPlainText("### New Scene\n\nWith some stuff in it!\n\n")
    assert nwGUI.docEditor.docChanged is True

    nwGUI.viewDocument(C.hSceneDoc)
    assert nwGUI.docViewer.toPlainText() == "New Scene\nWith some stuff in it!"

    # Open with keypress
    nwGUI.closeDocViewer()
    assert nwGUI.docViewer.docHandle is None
    nwGUI.projView.setSelectedHandle(C.hSceneDoc)
    nwGUI.projView.projTree.setFocus()
    qtbot.keyClick(nwGUI.projView.projTree, QtKeyReturn, modifier=QtModShift, delay=KEY_DELAY)
    assert nwGUI.docViewer.docHandle == C.hSceneDoc

    # If the viewer fails to load the document, nothing else happens
    nwGUI.closeDocViewer()
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docViewer, "loadText", lambda *a, **k: False)
        assert nwGUI.viewDocument(C.hSceneDoc) is True
    assert nwGUI.splitView.isVisible() is False

    # If the editor's cursor isn't visible when the viewer panel first
    # appears, its visibility isn't restored either
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "cursorIsVisible", lambda: False)
        assert nwGUI.viewDocument(C.hSceneDoc) is True
    assert nwGUI.splitView.isVisible() is True

    # Closing the viewer panel doesn't restore cursor visibility either,
    # if the cursor wasn't visible to begin with
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "cursorIsVisible", lambda: False)
        assert nwGUI.closeViewerPanel() is True

    # Reloading the viewer only saves the editor first if the two
    # panels show the same document
    nwGUI.openDocument(C.hChapterDoc)
    nwGUI.viewDocument(C.hSceneDoc)
    assert nwGUI.docEditor.docHandle != nwGUI.docViewer.docHandle
    nwGUI._reloadViewer()  # Should not raise, and skip saving the editor

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_Features(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test various features of the main window."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.closeDocument()  # Opening the project auto-restores a document
    cHandle = SHARED.project.newFile("Jane", C.hCharRoot)
    newDoc = SHARED.project.storage.getDocument(cHandle)
    newDoc.writeDocument("# Jane\n\n@tag: Jane\n\n")
    nwGUI.rebuildIndex()

    assert SHARED.focusMode is False

    # Focus Mode
    # ==========

    # No document open, so not allowing focus mode
    nwGUI.toggleFocusMode()
    assert nwGUI.treePane.isVisible() is True
    assert nwGUI.mainStatus.isVisible() is True
    assert nwGUI.mainMenu.isVisible() is True
    assert nwGUI.sideBar.isVisible() is True

    # Open a file only in the editor, with the viewer untouched and the
    # cursor hidden: toggling focus mode doesn't touch the viewer panel
    # or try to restore cursor visibility
    assert nwGUI.openDocument(C.hSceneDoc)
    assert nwGUI.docViewer.docHandle is None
    assert nwGUI.splitView.isVisible() is False
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "cursorIsVisible", lambda: False)
        nwGUI.toggleFocusMode()
        assert SHARED.focusMode is True
        nwGUI.toggleFocusMode()
        assert SHARED.focusMode is False

    # Open a file in editor and viewer
    assert nwGUI.openDocument(C.hSceneDoc)
    assert nwGUI.viewDocument(C.hSceneDoc)

    # Enable focus mode
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    assert nwGUI.treePane.isVisible() is False
    assert nwGUI.mainStatus.isVisible() is False
    assert nwGUI.mainMenu.isVisible() is False
    assert nwGUI.sideBar.isVisible() is False
    assert nwGUI.splitView.isVisible() is False

    # Disable focus mode
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is False
    assert nwGUI.treePane.isVisible() is True
    assert nwGUI.mainStatus.isVisible() is True
    assert nwGUI.mainMenu.isVisible() is True
    assert nwGUI.sideBar.isVisible() is True
    assert nwGUI.splitView.isVisible() is True

    # Closing editor disables focus mode
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    nwGUI.closeDocument()
    assert SHARED.focusMode is False
    nwGUI.openDocument(C.hSceneDoc)

    # Pressing Escape turns off focus mode. Focus mode puts focus on the
    # editor itself, which is where GuiDocEditor.keyPressEvent handles it.
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    assert nwGUI.docEditor.hasFocus() is True
    qtbot.keyClick(nwGUI.docEditor, QtKeyEscape)
    assert SHARED.focusMode is False

    # If search is active, focus is in the search box instead, and Escape
    # there just closes the search, leaving focus mode untouched
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    nwGUI.docEditor.beginSearch()
    assert nwGUI.docEditor.docSearch.searchBox.hasFocus() is True
    qtbot.keyClick(nwGUI.docEditor.docSearch.searchBox, QtKeyEscape)
    assert nwGUI.docEditor.searchVisible() is False
    assert SHARED.focusMode is True

    # If search is active but focus is in the editor itself rather than
    # the search box, Escape still closes the search, this time via the
    # editor's own keyPressEvent rather than the search box's event filter
    nwGUI.docEditor.beginSearch()
    nwGUI.docEditor.setFocus()
    assert nwGUI.docEditor.hasFocus() is True
    assert nwGUI.docEditor.searchVisible() is True
    qtbot.keyClick(nwGUI.docEditor, QtKeyEscape)
    assert nwGUI.docEditor.searchVisible() is False
    assert SHARED.focusMode is True

    # With search closed, Vim mode off, and Focus Mode inactive, Escape
    # does nothing
    nwGUI.toggleFocusMode()
    assert nwGUI.docEditor.searchVisible() is False
    assert CONFIG.vimMode is False
    assert SHARED.focusMode is False
    qtbot.keyClick(nwGUI.docEditor, QtKeyEscape)

    # Full Screen Mode
    # ================

    fullScreen = Qt.WindowState.WindowFullScreen
    assert nwGUI.windowState() & fullScreen != fullScreen
    nwGUI.toggleFullScreenMode()
    assert nwGUI.windowState() & fullScreen == fullScreen
    nwGUI.toggleFullScreenMode()
    assert nwGUI.windowState() & fullScreen != fullScreen

    # SideBar Menu
    # ============

    # Just make sure the custom event handler executes and doesn't fail
    nwGUI.sideBar.mSettings.show()
    nwGUI.sideBar.mSettings.hide()

    # Redirect Tag Open
    # =================

    nwGUI.closeDocument()
    nwGUI.closeDocViewer()
    assert nwGUI.docEditor.docHandle is None
    assert nwGUI.docViewer.docHandle is None
    nwGUI._followTag("John", nwDocMode.EDIT)  # Doesn't exist
    assert nwGUI.docEditor.docHandle is None
    assert nwGUI.docViewer.docHandle is None
    nwGUI._followTag("Jane", nwDocMode.EDIT)
    assert nwGUI.docEditor.docHandle == cHandle
    assert nwGUI.docViewer.docHandle is None
    nwGUI._followTag("Jane", nwDocMode.VIEW)
    assert nwGUI.docEditor.docHandle == cHandle
    assert nwGUI.docViewer.docHandle == cHandle

    # Errors Handling
    # ===============

    # Cannot edit a folder
    assert nwGUI.openDocument(C.hChapterDir) is False

    # Handle I/O error
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert nwGUI.openDocument(C.hChapterDoc) is False

    # Import Document
    # ===============

    # Importing into an empty document does not prompt for overwrite
    # confirmation
    assert nwGUI.openDocument(C.hSceneDoc)
    nwGUI.docEditor.replaceText("")
    assert nwGUI.docEditor.isEmpty is True

    importFile = projPath / "import.txt"
    importFile.write_text("Imported text.", encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(importFile), ""))
        assert nwGUI.importDocument() is True
    assert nwGUI.docEditor.getText() == "Imported text."

    # Dialogs
    # =======

    # Reopening the manuscript and writing stats dialogs reuses the
    # existing instance rather than creating a new one
    nwGUI.showBuildManuscriptDialog()
    manuscriptDialog = SHARED.findTopLevelWidget(GuiManuscript)
    assert manuscriptDialog is not None
    nwGUI.showBuildManuscriptDialog()
    assert SHARED.findTopLevelWidget(GuiManuscript) is manuscriptDialog
    manuscriptDialog.close()
    manuscriptDialog.softDelete()

    nwGUI.showWritingStatsDialog()
    statsDialog = SHARED.findTopLevelWidget(GuiWritingStats)
    assert statsDialog is not None
    nwGUI.showWritingStatsDialog()
    assert SHARED.findTopLevelWidget(GuiWritingStats) is statsDialog
    statsDialog.close()
    statsDialog.softDelete()

    # qtbot.stop()


@pytest.mark.gui
def testGuiMain_CloseMain(qtbot, nwGUI, projPath, mockRnd):
    """Test closeMain's pane-size and window-state save skips, across a
    project close/reopen cycle..
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # closeMain skips saving pane sizes while Focus Mode is active
    assert nwGUI.openDocument(C.hSceneDoc)
    nwGUI.toggleFocusMode()
    assert SHARED.focusMode is True
    assert nwGUI.closeMain() is True

    # closeMain skips saving the window size while in full screen mode
    assert nwGUI.openProject(projPath) is True
    nwGUI.setWindowState(nwGUI.windowState() | Qt.WindowState.WindowFullScreen)
    assert nwGUI.closeMain() is True


@pytest.mark.gui
def testGuiMain_OpenClose(qtbot, monkeypatch, nwGUI: GuiMain, projPath, fncPath, mockRnd):
    """Test opening and closing projects and documents."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    # Check open document and prev/next with no wraparound
    nwGUI.openNextDocument(C.hSceneDoc, False, True)  # Backwards
    assert nwGUI.docEditor._docHandle == C.hChapterDoc
    nwGUI.openNextDocument(C.hChapterDoc, False, False)  # Forwards
    assert nwGUI.docEditor._docHandle == C.hSceneDoc

    # Check open document and prev/next with wraparound
    nwGUI.openNextDocument(C.hSceneDoc, True, False)  # Forwards
    assert nwGUI.docEditor._docHandle == C.hTitlePage
    nwGUI.openNextDocument(C.hTitlePage, True, True)  # Backwards
    assert nwGUI.docEditor._docHandle == C.hSceneDoc

    # Check with handle that is not a document, should do nothing
    nwGUI.openDocument(C.hSceneDoc)
    assert nwGUI.docEditor._docHandle == C.hSceneDoc
    nwGUI.openNextDocument(C.hNovelRoot, True, True)
    assert nwGUI.docEditor._docHandle == C.hSceneDoc

    # No wraparound at the very first or last document stays put
    allDocs = SHARED.project.tree.allDocs()
    firstDoc = allDocs[0]
    lastDoc = allDocs[-1]

    nwGUI.openDocument(firstDoc)
    nwGUI.openNextDocument(firstDoc, False, True)  # Backwards, no wraparound
    assert nwGUI.docEditor.docHandle == firstDoc

    nwGUI.openDocument(lastDoc)
    nwGUI.openNextDocument(lastDoc, False, False)  # Forwards, no wraparound
    assert nwGUI.docEditor.docHandle == lastDoc

    # Autosaving does nothing when there are no changes to save
    assert nwGUI.saveProject() is True
    assert SHARED.project.projChanged is False
    nwGUI._autoSaveProject()

    assert nwGUI.docEditor.docChanged is False
    nwGUI._autoSaveDocument()

    # Open some test documents
    nwGUI.openDocument(C.hSceneDoc)
    nwGUI.viewDocument(C.hTitlePage)

    # Handle broken index on project open
    idxData = jsonEncode({"novelWriter.meta": {"version": __hexversion__}})
    nwGUI.closeProject()
    idxPath: Path = projPath / "meta" / nwFiles.INDEX_FILE
    assert idxPath.read_text(encoding="utf-8") != "{}"
    idxPath.write_text(idxData, encoding="utf-8")

    nwGUI.openProject(projPath)
    nwGUI.saveProject()
    assert idxPath.read_text(encoding="utf-8") != "{}"
    assert nwGUI.docEditor.docHandle == C.hSceneDoc
    assert nwGUI.docViewer.docHandle == C.hTitlePage

    # Block closing
    assert SHARED.hasProject is True
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert nwGUI.openProject(projPath) is False
        assert SHARED.hasProject is True

    # Don't open on lockfile question: No
    lockPath: Path = projPath / nwFiles.PROJ_LOCK
    lockBack: Path = projPath / f"{nwFiles.PROJ_LOCK}.bak"

    shutil.copyfile(lockPath, lockBack)
    nwGUI.closeProject()
    shutil.copyfile(lockBack, lockPath)

    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert nwGUI.openProject(projPath) is False

    assert nwGUI.openProject(projPath) is True

    # Backup on close
    backDir = CONFIG.backupPath() / SHARED.project.data.name
    assert not backDir.exists()

    CONFIG.backupOnClose = True
    assert nwGUI.openProject(projPath) is True
    nwGUI.closeProject()
    assert backDir.exists()
    assert len(list(backDir.iterdir())) > 0

    # Backing up without prompting first, when askBeforeBackup is disabled
    CONFIG.askBeforeBackup = False
    questionMock = Mock()
    backupMock = Mock()
    with monkeypatch.context() as mp:
        mp.setattr(SHARED, "question", questionMock)
        mp.setattr(type(SHARED.project), "backupProject", backupMock)
        assert nwGUI.openProject(projPath) is True
        assert nwGUI.closeProject(isYes=True) is True
    assert questionMock.called is False
    assert backupMock.called is True


@pytest.mark.gui
def testGuiMain_OpenDocument_ReentrancyGuard(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test that openDocument ignores a re-entrant call made while a
    document switch is already in progress.

    This models what happens holding F3 with project-wide loop search
    enabled: loadText calls QApplication.processEvents while a switch
    is still in progress, and if that dispatches an already-queued
    key-repeat event, it can re-trigger another document switch before
    the first one has finished.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    reentered = []
    realProcessEvents = QApplication.processEvents

    def reentrantProcessEvents(*args, **kwargs):
        if not reentered:
            reentered.append(True)
            assert nwGUI.openDocument(C.hChapterDoc) is False
        return realProcessEvents(*args, **kwargs)

    monkeypatch.setattr(QApplication, "processEvents", staticmethod(reentrantProcessEvents))

    assert nwGUI.openDocument(C.hSceneDoc) is True
    assert reentered == [True]
    assert nwGUI.docEditor.docHandle == C.hSceneDoc


@pytest.mark.gui
def testGuiMain_FocusView(qtbot, monkeypatch, nwGUI, projPath, mockRnd):
    """Test switching focus and view of the main window."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    nwGUI.openDocument(C.hSceneDoc)
    nwGUI.viewDocument(C.hSceneDoc)

    # Toggle Focus
    # ============
    nwGUI.docEditor.setFocus()
    assert nwGUI.docEditor.anyFocus()

    # Simulate focus change to viewer
    nwGUI._appFocusChanged(None, nwGUI.docViewer)
    assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.INACTIVE
    assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.NORMAL

    # Simulate focus change to editor
    nwGUI._appFocusChanged(None, nwGUI.docEditor)
    assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.NORMAL
    assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.INACTIVE

    # Simulate focus change to an unrelated widget: neither is focused
    nwGUI._appFocusChanged(None, QWidget())
    assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.INACTIVE
    assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.INACTIVE

    # Focus Tree
    # ==========
    assert nwGUI.projStack.currentWidget() == nwGUI.projView

    # Switch from editor to project tree
    nwGUI.docEditor.setFocus()
    nwGUI._switchFocus(nwFocus.TREE)
    assert nwGUI.projStack.currentWidget() == nwGUI.projView

    # Triggering again should switch to novel view
    nwGUI._switchFocus(nwFocus.TREE)
    assert nwGUI.projStack.currentWidget() == nwGUI.novelView

    # Switch from editor to novel view
    nwGUI.docEditor.setFocus()
    nwGUI._switchFocus(nwFocus.TREE)
    assert nwGUI.projStack.currentWidget() == nwGUI.novelView

    # Triggering again should switch back to project tree
    nwGUI._switchFocus(nwFocus.TREE)
    assert nwGUI.projStack.currentWidget() == nwGUI.projView

    # If in search mode, should default to project tree
    nwGUI._changeView(nwView.SEARCH)
    nwGUI._switchFocus(nwFocus.TREE)
    assert nwGUI.projStack.currentWidget() == nwGUI.projView

    # Focus Document
    # ==============
    nwGUI._switchFocus(nwFocus.TREE)

    def mockEmitEditorFocus(*a):
        nwGUI._appFocusChanged(None, nwGUI.docEditor)

    def mockEmitViewerFocus(*a):
        nwGUI._appFocusChanged(None, nwGUI.docViewer)

    # Switch to viewer
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: True)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docEditor, "setFocus", mockEmitEditorFocus)
        mp.setattr(nwGUI.docViewer, "setFocus", mockEmitViewerFocus)
        nwGUI._switchFocus(nwFocus.DOCUMENT)
        assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.INACTIVE
        assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.NORMAL

    # Call again to switch to editor
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: True)
        mp.setattr(nwGUI.docEditor, "setFocus", mockEmitEditorFocus)
        mp.setattr(nwGUI.docViewer, "setFocus", mockEmitViewerFocus)
        nwGUI._switchFocus(nwFocus.DOCUMENT)
        assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.NORMAL
        assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.INACTIVE

    # Default to editor
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docEditor, "setFocus", mockEmitEditorFocus)
        mp.setattr(nwGUI.docViewer, "setFocus", mockEmitViewerFocus)
        nwGUI._switchFocus(nwFocus.DOCUMENT)
        assert nwGUI.docEditor.docHeader.itemTitle._state == nwState.NORMAL
        assert nwGUI.docViewer.docHeader.itemTitle._state == nwState.INACTIVE

    # Pass Actions
    # ============

    # Pass to editor
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: True)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: False)
        nwGUI._passDocumentAction(nwDocAction.SEL_ALL)
        assert nwGUI.docEditor.textCursor().hasSelection() is True

    # Pass to viewer
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: True)
        nwGUI._passDocumentAction(nwDocAction.SEL_ALL)
        assert nwGUI.docViewer.textCursor().hasSelection() is True

    # Pass to neither, since neither has focus: nothing changes
    hadSelection = nwGUI.docEditor.textCursor().hasSelection()
    with monkeypatch.context() as mp:
        mp.setattr(nwGUI.docEditor, "hasFocus", lambda *a: False)
        mp.setattr(nwGUI.docViewer, "hasFocus", lambda *a: False)
        nwGUI._passDocumentAction(nwDocAction.MOVE_TEXT)
        assert nwGUI.docEditor.textCursor().hasSelection() is hadSelection

    # qtbot.stop()
