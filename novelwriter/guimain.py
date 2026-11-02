"""
novelWriter - GUI Main Window
=============================

This file is a part of novelWriter
Copyright (C) 2018 Veronica Berglyd Olsen and novelWriter contributors

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

import gc
import logging
import sys

from datetime import datetime
from pathlib import Path
from time import time
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QCloseEvent, QCursor, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED, __hexversion__, __version__
from novelwriter.common import formatVersion, hexToInt, minmax, safeIsFile
from novelwriter.constants import nwConst
from novelwriter.dialogs.about import GuiAbout
from novelwriter.dialogs.preferences import GuiNeedsUpdate, GuiPreferences
from novelwriter.dialogs.projectsettings import GuiProjectSettings
from novelwriter.dialogs.wordlist import GuiWordList
from novelwriter.editor.docpanes import GuiDocPanes
from novelwriter.enum import nwFocus, nwView
from novelwriter.extensions.progressbars import NProgressSimple
from novelwriter.gui.itemdetails import GuiItemDetails
from novelwriter.gui.mainmenu import GuiMainMenu
from novelwriter.gui.noveltree import GuiNovelView
from novelwriter.gui.projtree import GuiProjectView
from novelwriter.gui.search import GuiProjectSearch
from novelwriter.gui.sidebar import GuiSideBar
from novelwriter.gui.statusbar import GuiMainStatus
from novelwriter.manuscript.manuscript import GuiManuscript
from novelwriter.story.storyview import GuiStoryView
from novelwriter.tools.dictionaries import GuiDictionaries
from novelwriter.tools.welcome import GuiWelcome
from novelwriter.tools.writingstats import GuiWritingStats

logger = logging.getLogger(__name__)


class GuiMain(QMainWindow):
    """Main GUI Window.

    The Main GUI window class is the entry point of the application. It
    is split up into GUI components, assembled in the init function.
    Tools and dialog windows are created on demand, but may be cached by
    the Qt library and reused unless explicitly freed after use.
    """

    def __init__(self) -> None:
        super().__init__()

        logger.debug("Create: GUI")
        self.setObjectName("GuiMain")

        # System Info
        # ===========

        logger.info("OS: %s", CONFIG.osType)
        logger.info("Kernel: %s", CONFIG.kernelVer)
        logger.info("Host: %s", CONFIG.hostName)
        logger.info("Qt: %s (0x%06x)", CONFIG.verQtString, CONFIG.verQtValue)
        logger.info("PyQt: %s (0x%06x)", CONFIG.verPyQtString, CONFIG.verPyQtValue)
        logger.info("Python: %s (0x%08x)", CONFIG.verPyString, sys.hexversion)
        logger.info("GUI Language: %s", CONFIG.guiLocale)

        # Core Classes
        # ============

        # Internal Variables
        self._lastTotalCount = 0
        self._treePaneHidden = False

        # Initialise UserData Instance
        SHARED.initSharedData(self)

        # Prepare Main Window
        self._setWindowSize(CONFIG.mainWinSize)
        self._updateWindowTitle()

        nwIcon = CONFIG.assetPath("icons") / "novelwriter.svg"
        self.nwIcon = QIcon(str(nwIcon)) if safeIsFile(nwIcon) else QIcon()
        self.setWindowIcon(self.nwIcon)
        QApplication.setWindowIcon(self.nwIcon)

        # Build the GUI
        # =============

        # Main GUI Elements
        self.mainStatus = GuiMainStatus(self)
        self.projView = GuiProjectView(self)
        self.projSearch = GuiProjectSearch(self)
        self.novelView = GuiNovelView(self)
        self.docPanes = GuiDocPanes(self)

        self.docEditor = self.docPanes.docEditor
        self.docViewer = self.docPanes.docViewer
        self.docViewerPanel = self.docPanes.docViewerPanel

        self.itemDetails = GuiItemDetails(self)
        self.storyView = GuiStoryView(self)
        self.mainMenu = GuiMainMenu(self)
        self.sideBar = GuiSideBar(self)

        # Project Tree Stack
        self.projStack = QStackedWidget(self)
        self.projStack.addWidget(self.projView)
        self.projStack.addWidget(self.novelView)
        self.projStack.addWidget(self.projSearch)
        self.projStack.currentChanged.connect(self._projStackChanged)

        # Project Tree View
        self.treePane = QWidget(self)
        self.treeBox = QVBoxLayout()
        self.treeBox.setContentsMargins(0, 0, 0, 0)
        self.treeBox.setSpacing(4)
        self.treeBox.addWidget(self.projStack)
        self.treeBox.addWidget(self.itemDetails)
        self.treePane.setLayout(self.treeBox)

        # Splitter : Project Tree / Document Area
        self.splitMain = QSplitter(Qt.Orientation.Horizontal)
        self.splitMain.setContentsMargins(0, 0, 0, 0)
        self.splitMain.addWidget(self.treePane)
        self.splitMain.addWidget(self.docPanes)
        self.splitMain.setOpaqueResize(False)
        self.splitMain.setHandleWidth(4)
        self.splitMain.setSizes([max(s, 100) for s in CONFIG.mainPanePos])
        self.splitMain.setCollapsible(0, False)
        self.splitMain.setCollapsible(1, False)
        self.splitMain.setStretchFactor(0, 0)
        self.splitMain.setStretchFactor(1, 1)

        # Main Stack : Editor / Story View
        self.mainStack = QStackedWidget(self)
        self.mainStack.addWidget(self.splitMain)
        self.mainStack.addWidget(self.storyView)

        # Progress Bar
        self.mainProgress = NProgressSimple(self)
        self.mainProgress.setFixedHeight(2)

        # Assemble Main Window Elements
        self.mainBox = QHBoxLayout()
        self.mainBox.addWidget(self.sideBar)
        self.mainBox.addWidget(self.mainStack)
        self.mainBox.setContentsMargins(0, 0, 4, 0)
        self.mainBox.setSpacing(0)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.mainBox)
        self.outerBox.addWidget(self.mainProgress)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(0)

        self.mainWidget = QWidget(self)
        self.mainWidget.setLayout(self.outerBox)

        self.setMenuBar(self.mainMenu)
        self.setCentralWidget(self.mainWidget)
        self.setStatusBar(self.mainStatus)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)  # Issue #1147

        # Connect Signals
        # ===============

        SHARED.focusModeChanged.connect(self._focusModeChanged)
        SHARED.indexAvailable.connect(self.storyView.indexHasAppeared)
        SHARED.mainClockTick.connect(self._timeTick)
        SHARED.projectItemChanged.connect(self.itemDetails.onProjectItemChanged)
        SHARED.projectItemChanged.connect(self.projView.onProjectItemChanged)
        SHARED.projectStatusChanged.connect(self.mainStatus.updateProjectStatus)
        SHARED.projectStatusMessage.connect(self.mainStatus.setStatusMessage)
        SHARED.rootFolderChanged.connect(self.novelView.updateRootItem)
        SHARED.rootFolderChanged.connect(self.projSearch.updateRootItem)
        SHARED.rootFolderChanged.connect(self.projView.updateRootItem)
        SHARED.rootFolderChanged.connect(self.storyView.updateRootItem)
        SHARED.spellLanguageChanged.connect(self.mainStatus.setLanguage)

        self.mainMenu.requestDocAction.connect(self.docPanes.passDocumentAction)
        self.mainMenu.requestDocInsert.connect(self.docPanes.passDocumentInsert)
        self.mainMenu.requestDocInsertText.connect(self.docPanes.passDocumentInsert)
        self.mainMenu.requestDocKeyWordInsert.connect(self.docEditor.insertKeyWord)
        self.mainMenu.requestFocusChange.connect(self._switchFocus)
        self.mainMenu.requestViewChange.connect(self.changeView)

        self.sideBar.requestViewChange.connect(self.changeView)

        self.projView.openDocumentRequest.connect(self.docPanes.openDocumentInMode)
        self.projView.projectSettingsRequest.connect(self.showProjectSettingsDialog)
        self.projView.selectedItemChanged.connect(self.itemDetails.updateViewBox)

        self.novelView.openDocumentRequest.connect(self.docPanes.openDocumentInMode)
        self.novelView.selectedItemChanged.connect(self.itemDetails.updateViewBox)

        self.projSearch.openDocumentRequest.connect(self.docPanes.openDocumentInMode)
        self.projSearch.openDocumentSelectRequest.connect(self.docPanes.openDocumentSelection)
        self.projSearch.selectedItemChanged.connect(self.itemDetails.updateViewBox)

        self.storyView.openDocumentRequest.connect(self.docPanes.openDocumentInMode)

        self.docEditor.docTextChanged.connect(self.projSearch.textChanged)
        self.docEditor.editedStatusChanged.connect(self.mainStatus.updateDocumentStatus)
        self.docEditor.itemHandleChanged.connect(self.novelView.setActiveHandle)
        self.docEditor.itemHandleChanged.connect(self.projView.setActiveHandle)
        self.docEditor.requestNewNoteCreation.connect(SHARED.createNewNote)
        self.docEditor.requestProjectItemRenamed.connect(self.projView.renameTreeItem)
        self.docEditor.requestProjectItemSelected.connect(self.projView.setSelectedHandle)
        self.docEditor.spellCheckStateChanged.connect(self.mainMenu.setSpellCheckState)
        self.docEditor.toggleFocusModeRequest.connect(self.toggleFocusMode)

        self.docViewer.requestProjectItemSelected.connect(self.projView.setSelectedHandle)

        # OS Theme Support
        # ================

        self._themeHints = None
        self._themeChangedSlot = None
        if CONFIG.checkMinQtVersion(0x060500):  # pragma: no branch
            self._themeHints = QGuiApplication.styleHints()
            if self._themeHints is not None:  # pragma: no branch

                @pyqtSlot(Qt.ColorScheme)
                def colorSchemeChangedSlot(schemeHint: Qt.ColorScheme) -> None:
                    self.checkThemeUpdate(schemeHint=schemeHint)

                self._themeHints.colorSchemeChanged.connect(colorSchemeChangedSlot)
                self._themeChangedSlot = colorSchemeChangedSlot

        # Finalise Initialisation
        # =======================

        # Set Up Auto-Save Project Timer
        self.asProjTimer = QTimer(self)
        self.asProjTimer.timeout.connect(self._autoSaveProject)

        # Set Up Auto-Save Document Timer
        self.asDocTimer = QTimer(self)
        self.asDocTimer.timeout.connect(self._autoSaveDocument)

        # Set Up Garbage Collector Timer
        self.gcTimer = QTimer(self)
        self.gcTimer.setInterval(5000)
        self.gcTimer.timeout.connect(self._runGarbageCollect)

        # Initialise Main GUI
        self.initMain()
        self.asProjTimer.start()
        self.asDocTimer.start()
        self.gcTimer.start()
        self.mainStatus.clearStatus()

        logger.debug("Ready: GUI")
        logger.info("novelWriter is ready ...")
        self.mainStatus.setStatusMessage(self.tr("novelWriter is ready ..."))
        CONFIG.splashMessage("novelWriter is ready ...")

    def initMain(self) -> None:
        """Initialise elements that depend on user settings."""
        self.asProjTimer.setInterval(int(CONFIG.autoSaveProj * 1000))
        self.asDocTimer.setInterval(int(CONFIG.autoSaveDoc * 1000))

    def postLaunchTasks(self, cmdOpen: str | None) -> None:
        """Process tasks after the main window has been created."""
        QApplication.processEvents()
        app = QApplication.instance()
        if isinstance(app, QApplication):
            app.focusChanged.connect(self.docPanes.onFocusChanged)

        # Check that config loaded fine
        if CONFIG.hasError:
            SHARED.error(CONFIG.errorText())

        if cmdOpen:
            QApplication.processEvents()
            logger.info("Command line path: %s", cmdOpen)
            self.openProject(cmdOpen)

        if not SHARED.hasProject:
            self.showWelcomeDialog()

        # If this is a new release, let the user know
        if hexToInt(CONFIG.lastNotes) < hexToInt(__hexversion__):
            CONFIG.lastNotes = __hexversion__
            SHARED.info([
                self.tr("You are now running novelWriter version {0}.").format(formatVersion(__version__)),
                self.tr("Please check the {0}release notes{1} for further details.").format(
                    f"<a href='{nwConst.URL_RELEASES}'>", "</a>"
                ),
            ])

            if CONFIG.installSource == "launchpad":  # pragma: no cover
                SHARED.info(
                    "Your version of novelWriter was installed from the Ubuntu Launcpad PPA repository. "
                    "This install method is deprecated, and will soon stop working. "
                    "See <a href='https://novelwriter.io/download/install_linux.html'>Installing on Linux</a> "
                    "for information on how to migrate.",
                    log=False,
                )

    ##
    #  Project Actions
    ##

    def closeProject(self, isYes: bool = False) -> bool:
        """Close the project if one is open. isYes is passed on from the
        close application event so the user doesn't get prompted twice
        to confirm.
        """
        if not SHARED.hasProject:
            # There is no project loaded, everything OK
            return True

        if not isYes:
            msgYes = SHARED.question([
                self.tr("Close the current project?"),
                self.tr("Changes are saved automatically."),
            ])
            if not msgYes:
                return False

        self.docPanes.saveDocument()
        saveOK = self.saveProject()
        doBackup = False
        if SHARED.project.data.doBackup and CONFIG.backupOnClose:
            doBackup = True
            if CONFIG.askBeforeBackup:
                doBackup = SHARED.question(self.tr("Backup the current project?"))

        if doBackup:
            SHARED.project.backupProject(False)

        if saveOK:
            self.docPanes.closeProjectTasks()
            self.storyView.closeProjectTasks()
            self.novelView.closeProjectTasks()
            self.projView.closeProjectTasks()
            self.projSearch.closeProjectTasks()
            self.itemDetails.clearDetails()
            self.mainStatus.clearStatus()

            SHARED.closeProject()

            self._updateWindowTitle()
            self.changeView(nwView.PROJECT)

        return saveOK

    def openProject(self, projFile: str | Path | None) -> bool:
        """Open a project from a projFile path."""
        if projFile is None:
            return False

        # Make sure any open project is cleared out first
        if not self.closeProject():
            return False

        # Switch main tab to editor view
        self.changeView(nwView.PROJECT)

        # Try to open the project
        tStart = time()
        if not SHARED.openProject(projFile):
            # The project open failed.
            lockStatus = SHARED.projectLock
            if lockStatus is None:
                # The project is not locked, so failed for some other
                # reason handled by the project class.
                return False

            lockText = self.tr(
                "The project is already open by another instance of "
                "novelWriter, and is therefore locked. Override lock "
                "and continue anyway?"
            )
            lockInfo = self.tr(
                "Note: If the program or the computer previously "
                "crashed, the lock can safely be overridden. However, "
                "overriding it is not recommended if the project is "
                "open in another instance of novelWriter. Doing so "
                "may corrupt the project."
            )
            try:
                lockDetails = self.tr(
                    "The project was locked by the computer '{0}' ({1} {2}), last active on {3}."
                ).format(
                    lockStatus[0],
                    lockStatus[1],
                    lockStatus[2],
                    CONFIG.localDateTime(datetime.fromtimestamp(int(lockStatus[3]))),
                )
            except Exception:
                lockDetails = ""

            if SHARED.question(lockText, info=lockInfo, details=lockDetails, warn=True):
                if not SHARED.openProject(projFile, clearLock=True):
                    return False
            else:
                return False

        # Update GUI
        self._updateWindowTitle(SHARED.project.data.name)
        self.mainStatus.setRefTime(SHARED.project.projOpened)
        self.mainStatus.initProjectSettings()
        self.projView.openProjectTasks()
        self.novelView.openProjectTasks()
        self.storyView.openProjectTasks()
        self.projSearch.openProjectTasks()
        self._updateStatusWordCount()

        # Must run after the project tree is populated
        self.docPanes.openProjectTasks()

        # Check if we need to rebuild the index
        if SHARED.project.index.indexRebuild:
            if not SHARED.project.index.indexUpgrade:
                SHARED.warn(self.tr("The project index is broken. Rebuilding index."))
            self.rebuildIndex()

        # Make sure the changed status is set to false on things opened
        self.docEditor.setDocumentChanged(False)
        SHARED.project.setProjectChanged(False)
        SHARED.reportSpellCheckStatus()

        logger.debug("Project loaded in %.3f ms", (time() - tStart) * 1000)

        return True

    def saveProject(self, autoSave: bool = False) -> bool:
        """Save the current project."""
        if SHARED.hasProject:
            return SHARED.saveProject(autoSave=autoSave)
        return False

    ##
    #  Tree Item Actions
    ##

    @pyqtSlot()
    def openSelectedItem(self) -> None:
        """Open the selected item in the tree view that is currently
        active. Used by the main menu's Open Document action to forward
        the request to whichever tree widget is visible.
        """
        if SHARED.hasProject:
            if self.projView.treeHasFocus():
                self.projView.projTree.openSelectedItem()
            elif self.novelView.treeHasFocus():
                self.novelView.novelTree.openSelectedItem()
            else:
                logger.warning("No item selected")

    def rebuildIndex(self) -> None:
        """Rebuild the entire index."""
        if SHARED.hasProject:
            logger.info("Rebuilding index ...")
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
            tStart = time()

            SHARED.project.index.rebuild()
            SHARED.project.tree.refreshAllItems()

            tEnd = time()
            self.mainStatus.setStatusMessage(
                self.tr("Indexing completed in {0} ms").format(f"{(tEnd - tStart) * 1000.0:.1f}")
            )
            self._updateStatusWordCount()
            QApplication.restoreOverrideCursor()

            SHARED.info(self.tr("The project index has been successfully rebuilt."))

    ##
    #  Main Dialogs
    ##

    @pyqtSlot()
    def showWelcomeDialog(self) -> None:
        """Open the welcome dialog."""
        dialog = GuiWelcome(self)
        if CONFIG.moveMainWin and (screen := SHARED.mainScreen):
            dialog.move(screen.geometry().center() - dialog.rect().center())
        dialog.openProjectRequest.connect(self._openProjectFromWelcome)
        dialog.exec()

    @pyqtSlot()
    def showPreferencesDialog(self) -> None:
        """Open the preferences dialog."""
        dialog = GuiPreferences(self)
        dialog.newPreferencesReady.connect(self._processConfigChanges)
        dialog.exec()

    @pyqtSlot()
    @pyqtSlot(int)
    def showProjectSettingsDialog(self, focusTab: int = GuiProjectSettings.PAGE_SETTINGS) -> None:
        """Open the project settings dialog."""
        if SHARED.hasProject:
            dialog = GuiProjectSettings(self, gotoPage=focusTab)
            dialog.newProjectSettingsReady.connect(self._processProjectSettingsChanges)
            dialog.exec()

    @pyqtSlot()
    def showBuildManuscriptDialog(self) -> None:
        """Open the build manuscript dialog."""
        if SHARED.hasProject:
            if not (dialog := SHARED.findTopLevelWidget(GuiManuscript)):
                dialog = GuiManuscript(self)
            dialog.activateDialog()
            dialog.loadContent()

    @pyqtSlot()
    def showProjectWordListDialog(self) -> None:
        """Open the project word list dialog."""
        if SHARED.hasProject:
            dialog = GuiWordList(self)
            dialog.newWordListReady.connect(self._processWordListChanges)
            dialog.exec()

    @pyqtSlot()
    def showWritingStatsDialog(self) -> None:
        """Open the session stats dialog."""
        if SHARED.hasProject:
            if not (dialog := SHARED.findTopLevelWidget(GuiWritingStats)):
                dialog = GuiWritingStats(self)
            dialog.activateDialog()
            dialog.populateGUI()

    @pyqtSlot()
    def showAboutNWDialog(self) -> None:
        """Show the novelWriter about dialog."""
        dialog = GuiAbout(self)
        dialog.exec()

    @pyqtSlot()
    def showAboutQtDialog(self) -> None:
        """Show the Qt about dialog."""
        msgBox = QMessageBox(self)
        msgBox.aboutQt(self, "About Qt")

    @pyqtSlot()
    def showDictionariesDialog(self) -> None:
        """Show the download dictionaries dialog and update language
        list when closed.
        """
        dialog = GuiDictionaries(self)
        dialog.activateDialog()
        if not dialog.initDialog():
            dialog.close()
            SHARED.error(self.tr("Could not initialise the dialog."))
            return

        dialog.finished.connect(self.mainMenu.updateSpellCheckLanguages)

    ##
    #  Main Window Actions
    ##

    def closeMain(self) -> bool:
        """Save everything, and close novelWriter."""
        if (
            SHARED.hasProject
            and CONFIG.askBeforeExit
            and not SHARED.question([
                self.tr("Do you want to exit novelWriter?"),
                self.tr("Changes are saved automatically."),
            ])
        ):
            return False

        logger.info("Exiting novelWriter")

        if not SHARED.focusMode:
            if not self.treePane.isHidden():  # Note: not the same as isVisible()
                CONFIG.mainPanePos = self.splitMain.sizes()
            CONFIG.searchPanePos = self.projSearch.splitSizes()

        self.docPanes.saveLayout()
        CONFIG.showDetailsPanel = self.itemDetails.isExpanded()
        wFull = Qt.WindowState.WindowFullScreen
        if self.windowState() & wFull != wFull:
            # Ignore window size if in full screen mode
            CONFIG.setMainWinSize(self.geometry())

        if SHARED.hasProject:
            self.closeProject(True)
        CONFIG.saveConfig()

        self.asProjTimer.stop()
        self.asDocTimer.stop()

        QApplication.quit()

        return True

    def checkThemeUpdate(self, *, schemeHint: Any | None = None) -> None:
        """Load theme if mode changed."""
        if SHARED.theme.loadTheme(schemeHint=schemeHint):
            self.refreshThemeColors(syntax=True)
            self.docPanes.initPanes()

            # This also forces the icon to update if there was already a message on the status bar (#2886)
            meta = SHARED.theme.themeInfo
            self.mainStatus.setStatusMessage(self.tr('Loaded theme "{0}" by {1}').format(meta.name, meta.author))

    def refreshThemeColors(self, syntax: bool = False, force: bool = False) -> None:
        """Refresh the GUI theme."""
        SHARED.theme.loadTheme(force=force)
        SHARED.project.updateTheme()
        self.setPalette(QApplication.palette())
        self.docPanes.updateTheme(syntax=syntax)
        self.sideBar.updateTheme()
        self.projView.updateTheme()
        self.novelView.updateTheme()
        self.projSearch.updateTheme()
        self.storyView.updateTheme()
        self.itemDetails.updateTheme()
        self.mainStatus.updateTheme()
        SHARED.project.tree.refreshAllItems()

        if dialog := SHARED.findTopLevelWidget(GuiManuscript):
            dialog.updateTheme()

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the closing event of the GUI and call the close
        function to handle all the close process steps.
        """
        if self.closeMain():
            if self._themeHints is not None and self._themeChangedSlot is not None:
                self._themeHints.colorSchemeChanged.disconnect(self._themeChangedSlot)
            self.docEditor.clearEditor()  # Extra safety to clear widgets
            event.accept()
        else:
            event.ignore()

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def toggleFullScreenMode(self) -> None:
        """Toggle full screen mode."""
        self.setWindowState(self.windowState() ^ Qt.WindowState.WindowFullScreen)

    @pyqtSlot()
    def toggleTreePane(self) -> None:
        """Toggle the tree pane visibility."""
        if self.mainStack.currentWidget() == self.splitMain and not SHARED.focusMode:
            self.treePane.setVisible(not self.treePane.isVisible())

    @pyqtSlot()
    def toggleFocusMode(self) -> None:
        """Toggle focus mode."""
        if self.docEditor.docHandle:
            SHARED.setFocusMode(not SHARED.focusMode)

    ##
    #  Private Slots
    ##

    @pyqtSlot(bool)
    def _focusModeChanged(self, focusMode: bool) -> None:
        """Handle change of focus mode. The Main GUI Focus Mode hides
        tree, view, statusbar and menu.
        """
        if focusMode:
            logger.debug("Activating Focus Mode")
            self._treePaneHidden = self.treePane.isHidden()
            self.changeView(nwView.EDITOR)
            self.docEditor.setFocus()
        else:
            logger.debug("Deactivating Focus Mode")

        cursorVisible = self.docEditor.cursorIsVisible()
        isVisible = not focusMode
        self.treePane.setVisible(isVisible and not self._treePaneHidden)
        self.mainStatus.setFocusMode(focusMode)
        self.mainMenu.setVisible(isVisible)
        self.sideBar.setVisible(isVisible)
        self.docPanes.setFocusMode(focusMode)

        if cursorVisible:
            self.docEditor.ensureCursorVisible(centre=False)

    @pyqtSlot(nwFocus)
    def _switchFocus(self, paneNo: nwFocus) -> None:
        """Switch focus between main GUI views."""
        if paneNo == nwFocus.TREE:
            # Decision Matrix
            #  vM | vP | fP | vN | fN | Focus
            # ----|----|----|----|----|---------
            #  T  | T  | T  | F  | F  | Novel
            #  T  | T  | F  | F  | F  | Project
            #  T  | F  | F  | T  | T  | Project
            #  T  | F  | F  | T  | F  | Novel
            #  T  | F  | F  | F  | F  | Project
            #  F  | T  | T  | F  | F  | Project
            #  F  | T  | F  | F  | F  | Project
            #  F  | F  | F  | T  | T  | Novel
            #  F  | F  | F  | T  | F  | Novel
            #  F  | F  | F  | F  | F  | Project

            vM = self.mainStack.currentWidget() is self.splitMain
            vP = self.projStack.currentWidget() is self.projView
            vN = self.projStack.currentWidget() is self.novelView
            fP = self.projView.treeHasFocus()
            fN = self.novelView.treeHasFocus()

            self.changeView(nwView.EDITOR, exitFocus=True)
            if (vM and ((vP and fP) or (vN and not fN))) or (not vM and vN):
                self.changeView(nwView.NOVEL, exitFocus=True, forceVisible=True)
                self.novelView.setTreeFocus()
            else:
                self.changeView(nwView.PROJECT, exitFocus=True, forceVisible=True)
                self.projView.setTreeFocus()

        elif paneNo == nwFocus.DOCUMENT:
            self.changeView(nwView.EDITOR, exitFocus=True)
            self.docPanes.cycleFocus()

        elif paneNo == nwFocus.STORY:
            if self.mainStack.currentWidget() is self.storyView:
                self.storyView.cycleTabs()
            else:
                self.changeView(nwView.STORY, exitFocus=True)

        else:  # pragma: no cover
            pass

    @pyqtSlot(GuiNeedsUpdate)
    def _processConfigChanges(self, update: GuiNeedsUpdate) -> None:
        """Refresh GUI based on flags from the Preferences dialog."""
        logger.debug("Applying new preferences")
        self.initMain()
        self.docPanes.saveDocument()

        if update.tree and not update.theme:
            # These are also updated by a theme refresh
            SHARED.project.tree.refreshAllItems()
            self.novelView.refreshCurrentTree()

        if update.theme:
            self.refreshThemeColors(syntax=update.syntax, force=True)
        self.docPanes.applySettings(update)
        if update.viewport:
            self.projView.initViewport()
            self.novelView.initViewport()
        if update.spelling:
            SHARED.updateSpellCheckLanguage(reload=True)

        self.projSearch.initSettings()
        self.storyView.initSettings()
        self.mainStatus.initSettings()

        # Force update of word count
        self._lastTotalCount = 0
        self._updateStatusWordCount()

        if update.restart:
            SHARED.info(self.tr("Some changes will not be applied until novelWriter has been restarted."))

    @pyqtSlot()
    def _processProjectSettingsChanges(self) -> None:
        """Refresh data dependent on project settings."""
        logger.debug("Applying new project settings")
        SHARED.updateSpellCheckLanguage()
        self.docEditor.updateReplaceKeys()
        self.docViewer.reloadText()
        self.itemDetails.refreshDetails()
        self.mainMenu.setSelectedProjectSpellCheckLanguage()
        self.mainStatus.initProjectSettings()
        self._updateWindowTitle(SHARED.project.data.name)

    @pyqtSlot()
    def _processWordListChanges(self) -> None:
        """Reload project word list."""
        logger.debug("Reloading word list")
        SHARED.updateSpellCheckLanguage(reload=True)
        self.docEditor.spellCheckDocument()

    @pyqtSlot(Path)
    def _openProjectFromWelcome(self, path: Path) -> None:
        """Handle an open project request from the welcome dialog."""
        QApplication.processEvents()
        self.openProject(path)
        if not SHARED.hasProject:
            self.showWelcomeDialog()

    @pyqtSlot(nwView)
    @pyqtSlot(nwView, bool)
    def changeView(
        self,
        view: nwView,
        isSideBar: bool = False,
        *,
        exitFocus: bool = False,
        forceVisible: bool = False,
    ) -> None:
        """Handle the requested change of view."""
        if exitFocus:
            SHARED.setFocusMode(False)

        isMain = self.mainStack.currentWidget() == self.splitMain
        isSame = False
        canToggle = False

        if view == nwView.EDITOR:
            # Only change the main stack, but not the project stack
            self.mainStack.setCurrentWidget(self.splitMain)
        elif view == nwView.PROJECT:
            isSame = isMain and self.projStack.currentWidget() == self.projView
            canToggle = True
            self.mainStack.setCurrentWidget(self.splitMain)
            self.projStack.setCurrentWidget(self.projView)
        elif view == nwView.NOVEL:
            isSame = isMain and self.projStack.currentWidget() == self.novelView
            canToggle = True
            self.mainStack.setCurrentWidget(self.splitMain)
            self.projStack.setCurrentWidget(self.novelView)
        elif view == nwView.SEARCH:
            isSame = isMain and self.projStack.currentWidget() == self.projSearch
            canToggle = True
            self.mainStack.setCurrentWidget(self.splitMain)
            self.projStack.setCurrentWidget(self.projSearch)
            self.projSearch.beginSearch(self.docEditor.getSelectedText() if self.docEditor.anyFocus() else "")
        elif view == nwView.STORY:
            self.mainStack.setCurrentWidget(self.storyView)
            self.storyView.viewStory()
        else:  # pragma: no cover
            pass

        if canToggle:
            if forceVisible or not isSame:
                self.treePane.setVisible(True)
            elif isSideBar:
                self.treePane.setVisible(not self.treePane.isVisible())

        # Set active status
        isMain = self.mainStack.currentWidget() == self.splitMain
        isNovel = self.projStack.currentWidget() == self.novelView
        self.novelView.setActive(isMain and isNovel)

    @pyqtSlot()
    def _timeTick(self) -> None:
        """Process time tick of the main timer."""
        if SHARED.hasProject:
            currTime = time()
            editIdle = currTime - self.docEditor.lastActive > CONFIG.userIdleTime
            userIdle = QApplication.applicationState() != Qt.ApplicationState.ApplicationActive
            self.mainStatus.setUserIdle(editIdle or userIdle)
            SHARED.updateIdleTime(currTime, editIdle or userIdle)
            self.mainStatus.updateTime(idleTime=SHARED.projectIdleTime)
            if int(currTime) % 5 == 0:
                self._updateStatusWordCount()
                if CONFIG.memInfo:  # pragma: no cover
                    self.mainStatus.memInfo()

    @pyqtSlot()
    def _autoSaveProject(self) -> None:
        """Autosave of the project. This is a timer-activated slot."""
        doSave = SHARED.hasProject
        doSave &= SHARED.project.projChanged
        doSave &= SHARED.project.storage.isOpen()
        if doSave:
            logger.debug("Auto-saving project")
            self.saveProject(autoSave=True)

    @pyqtSlot()
    def _autoSaveDocument(self) -> None:
        """Autosave of the document. This is a timer-activated slot."""
        if SHARED.hasProject and self.docEditor.docChanged:
            logger.debug("Auto-saving document")
            self.docPanes.saveDocument()

    @pyqtSlot()
    def _runGarbageCollect(self) -> None:
        """Run the cyclic garbage collector on the main thread, since
        automatic collection is disabled at startup. See #2927.
        """
        gc.collect()

    @pyqtSlot()
    def _updateStatusWordCount(self) -> None:
        """Update the word count on the status bar."""
        if not SHARED.hasProject:
            self.mainStatus.setProjectStats(0, 0)
            self.mainStatus.updateGoals(0, 0)

        currentTotalCount = SHARED.project.currentTotalCount
        if self._lastTotalCount != currentTotalCount or SHARED.project.countsDirty:
            self._lastTotalCount = currentTotalCount

            data = SHARED.project.data
            SHARED.project.updateCounts()
            if CONFIG.incNotesWCount:
                if CONFIG.useCharCount:
                    iTotal = sum(data.initCounts[2:])
                    cTotal = sum(data.currCounts[2:])
                else:
                    iTotal = sum(data.initCounts[:2])
                    cTotal = sum(data.currCounts[:2])
            else:
                if CONFIG.useCharCount:
                    iTotal = data.initCounts[2]
                    cTotal = data.currCounts[2]
                else:
                    iTotal = data.initCounts[0]
                    cTotal = data.currCounts[0]

            self.mainStatus.setProjectStats(cTotal, cTotal - iTotal)
            self.mainStatus.updateGoals(data.targetLastCount, data.dailyProgress)

    @pyqtSlot(int)
    def _projStackChanged(self, index: int) -> None:
        """Process project view tab change."""
        sHandle = None
        widget = self.projStack.widget(index)
        if widget == self.projView:
            sHandle = self.projView.getSelectedHandle()
        elif widget == self.novelView:
            sHandle, _ = self.novelView.getSelectedHandle()
        self.itemDetails.updateViewBox(sHandle)

    ##
    #  Internal Functions
    ##

    def _setWindowSize(self, size: list[int]) -> None:
        """Set the main window size."""
        if len(size) == 2 and (screen := SHARED.mainScreen):
            availSize = screen.availableSize()
            width = minmax(size[0], 900, availSize.width())
            height = minmax(size[1], 500, availSize.height())
            self.resize(width, height)
            if width != size[0] or height != size[1] or CONFIG.moveMainWin:
                self.move(screen.geometry().center() - self.rect().center())

    def _updateWindowTitle(self, projName: str | None = None) -> None:
        """Set the window title and add the project's name."""
        self.setWindowTitle(" - ".join(filter(None, [projName, CONFIG.appName])))
