"""
novelWriter - Shared Data Class
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

import logging
import re

from enum import Enum
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, TypeVar

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices, QFont, QScreen
from PyQt6.QtWidgets import QApplication, QFileDialog, QGridLayout, QMessageBox, QSpacerItem, QWidget

from novelwriter.common import appendIfSet, formatFileFilter, joinLines
from novelwriter.constants import nwFiles
from novelwriter.core.spellcheck import SpellEnchant
from novelwriter.enum import nwChange, nwItemClass, nwStandardButton
from novelwriter.types import QtSizeExpanding, QtSizeMinimum

if TYPE_CHECKING:
    from collections.abc import Callable

    from novelwriter.core.project import NWProject
    from novelwriter.core.status import T_StatusKind
    from novelwriter.gui.theme import GuiTheme
    from novelwriter.guimain import GuiMain
    from novelwriter.types import T_MsgSeverity

logger = logging.getLogger(__name__)

NWidget = TypeVar("NWidget", bound=QWidget)
T_Msg = str | list[str]

RX_HTML = re.compile(r"<.*?>")


class SharedData(QObject):
    """Shared Data Singleton.

    This is the class instantiated as the SHARED singleton. It holds
    various globally needed data and pointers to important objects like
    the main GUI, the current project, and the GUI theme.
    """

    __slots__ = (
        "_cachedErrors",
        "_clock",
        "_focusMode",
        "_gui",
        "_idleRefTime",
        "_idleTime",
        "_lastAlert",
        "_lockedBy",
        "_project",
        "_spelling",
        "_theme",
    )

    focusModeChanged = pyqtSignal(bool)
    indexAvailable = pyqtSignal()
    indexChangedRefs = pyqtSignal(list)
    indexChangedTags = pyqtSignal(list, list)
    indexCleared = pyqtSignal()
    mainClockTick = pyqtSignal()
    novelStructureChanged = pyqtSignal(str)
    projectItemChanged = pyqtSignal(str, Enum)
    projectStatusChanged = pyqtSignal(bool)
    projectStatusMessage = pyqtSignal(str, str)
    rootFolderChanged = pyqtSignal(str, Enum)
    spellLanguageChanged = pyqtSignal(str, str)
    statusLabelsChanged = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        # Objects
        self._gui = None
        self._theme = None
        self._project = None
        self._spelling = None

        # Settings
        self._lockedBy = None
        self._lastAlert = []
        self._idleTime = 0.0
        self._idleRefTime = time()
        self._focusMode = False
        self._cachedErrors = []

        self._clock = QTimer(self)
        self._clock.setInterval(1000)
        self._clock.timeout.connect(lambda: self.mainClockTick.emit())

    ##
    #  Properties
    ##

    @property
    def mainGui(self) -> GuiMain:
        """Return the Main GUI instance."""
        if self._gui is None:
            raise RuntimeError("SharedData class not fully initialised")
        return self._gui

    @property
    def theme(self) -> GuiTheme:
        """Return the GUI Theme instance."""
        if self._theme is None:
            raise RuntimeError("SharedData class not fully initialised")
        return self._theme

    @property
    def project(self) -> NWProject:
        """Return the active NWProject instance."""
        if self._project is None:
            raise RuntimeError("SharedData class not fully initialised")
        return self._project

    @property
    def spelling(self) -> SpellEnchant:
        """Return the active NWProject instance."""
        if self._spelling is None:
            raise RuntimeError("SharedData class not fully initialised")
        return self._spelling

    @property
    def focusMode(self) -> bool:
        """Return the Focus Mode state."""
        return self._focusMode

    @property
    def hasProject(self) -> bool:
        """Return True if the project instance is populated."""
        return self.project.isValid

    @property
    def projectLock(self) -> list | None:
        """Return cached lock information for the last project."""
        return self._lockedBy

    @property
    def projectIdleTime(self) -> float:
        """Return the session idle time."""
        return self._idleTime

    @property
    def lastAlert(self) -> list[str]:
        """Return the last alert message."""
        return self._lastAlert

    @property
    def mainScreen(self) -> QScreen | None:
        """Return the screen of the main window."""
        return QApplication.screenAt(self.mainGui.rect().center())

    ##
    #  Setters
    ##

    def setFocusMode(self, state: bool) -> None:
        """Set focus mode on or off."""
        if state is not self._focusMode:
            self._focusMode = state
            self.focusModeChanged.emit(state)

    ##
    #  Methods
    ##

    def initTheme(self, theme: GuiTheme) -> None:
        """Initialise the GUI theme. This must be called before the GUI
        is created.
        """
        self._theme = theme
        self._theme.initThemes()

    def initSharedData(self, gui: GuiMain) -> None:
        """Initialise the SharedData instance. This must be called as
        soon as the Main GUI is created to ensure the SHARED singleton
        has the properties needed for operation.
        """
        self._clock.start()
        self._gui = gui
        self._resetProject()
        logger.debug("Ready: SharedData")
        if pool := QThreadPool.globalInstance():  # pragma: no branch
            logger.debug("Thread Pool Max Count: %d", pool.maxThreadCount())

    def closeDocument(self, tHandle: str | None = None) -> None:
        """Close the document editor, optionally a specific document."""
        if tHandle is None or tHandle == self.mainGui.docEditor.docHandle:
            self.mainGui.closeDocument()
        if tHandle is None or tHandle == self.mainGui.docViewer.docHandle:
            self.mainGui.closeViewerPanel()

    def saveEditor(self, tHandle: str | None = None) -> None:
        """Save the editor content, optionally a specific document."""
        docEditor = self.mainGui.docEditor
        if self.hasProject and docEditor.docHandle and (tHandle is None or tHandle == docEditor.docHandle):
            logger.debug("Saving editor document before action")
            docEditor.saveText()

    def openProject(self, path: str | Path, clearLock: bool = False) -> bool:
        """Open a project."""
        if self.project.isValid:
            logger.error("A project is already open")
            return False

        self._lockedBy = None
        status = self.project.openProject(path, clearLock=clearLock)
        if status is False:
            # We must cache the lock status before resetting the project
            self._lockedBy = self.project.lockStatus
            self._resetProject()

        self.updateSpellCheckLanguage(reload=True)
        self._resetIdleTimer()

        return status

    def saveProject(self, autoSave: bool = False) -> bool:
        """Save the current project."""
        if not self.project.isValid:
            logger.error("There is no project open")
            return False
        return self.project.saveProject(autoSave=autoSave)

    def closeProject(self) -> None:
        """Close the current project."""
        self._closeToolDialogs()
        self.project.closeProject(self._idleTime)
        self._resetProject()
        self._resetIdleTimer()

    def updateSpellCheckLanguage(self, reload: bool = False) -> None:
        """Update the active spell check language from settings."""
        from novelwriter import CONFIG

        language = self.project.data.spellLang or CONFIG.spellLanguage
        if language != self.spelling.spellLanguage or reload:
            self.spelling.setLanguage(language)
            _, provider = self.spelling.describeDict()
            self.spellLanguageChanged.emit(language, provider)

    def reportSpellCheckStatus(self) -> None:
        """Report the state of the spell checker."""
        spell = self.spelling
        if (req := spell.requestedLanguage) is not None and req != spell.spellLanguage:
            self.warn(self.tr("Could not load spell checking for language code '{0}'.").format(req))

    def updateIdleTime(self, currTime: float, userIdle: bool) -> None:
        """Update the idle time record. If the userIdle flag is True,
        the user idle counter is updated with the time difference since
        the last time this function was called. Otherwise, only the
        reference time is updated.
        """
        if userIdle:
            self._idleTime += currTime - self._idleRefTime
        self._idleRefTime = currTime

    def initMainProgress(self, maximum: int, inclusive: bool = False) -> None:
        """Start a session for the main progress bar."""
        if gui := self._gui:
            gui.mainProgress.setMaximum(maximum - (1 if inclusive else 0))
            gui.mainProgress.setValue(0)

    def incMainProgress(self) -> None:
        """Increment the value for the main progress bar."""
        if gui := self._gui:
            gui.mainProgress.setValue(gui.mainProgress.value() + 1)
            QApplication.processEvents()

    def clearMainProgress(self, delay: float = 1.0) -> None:
        """Clear the main progress bar."""
        if gui := self._gui:
            QTimer.singleShot(int(delay * 1000), gui.mainProgress.reset)

    def newStatusMessage(self, message: str | Exception, severity: T_MsgSeverity = "info") -> None:
        """Request a new status message."""
        self.projectStatusMessage.emit(str(message), severity)

    def setGlobalProjectState(self, state: bool) -> None:
        """Change the global project status."""
        self.projectStatusChanged.emit(state)

    def runInThreadPool(self, runnable: QRunnable, priority: int = 0) -> None:
        """Queue a runnable in the application thread pool."""
        if pool := QThreadPool.globalInstance():
            pool.start(runnable, priority=priority)

    def getProjectPath(self, parent: QWidget, path: str | Path | None = None, allowZip: bool = False) -> Path | None:
        """Open the file dialog and select a novelWriter project file."""
        label = self.tr("novelWriter Project File or Zip File") if allowZip else self.tr("novelWriter Project File")
        ext = f"{nwFiles.PROJ_FILE} *.zip" if allowZip else nwFiles.PROJ_FILE
        fFilter = formatFileFilter([(label, ext), "*"])
        selected, _ = QFileDialog.getOpenFileName(parent, self.tr("Open Project"), str(path or ""), filter=fFilter)
        return Path(selected) if selected else None

    def getProjectFolder(self, parent: QWidget, path: str | Path | None = None) -> Path | None:
        """Open the folder dialog and select a project folder."""
        location = QFileDialog.getExistingDirectory(
            parent,
            self.tr("Select Project Folder"),
            str(path),
            options=QFileDialog.Option.ShowDirsOnly,
        )
        return Path(location) if location else None

    def getFont(self, current: QFont, native: bool) -> tuple[QFont, bool]:
        """Open the font dialog and select a font."""
        from novelwriter.extensions.modified import NFontDialog

        return NFontDialog.selectFont(current, self.mainGui, self.tr("Select Font"), native)

    def findTopLevelWidget(self, kind: type[NWidget]) -> NWidget | None:
        """Find a top level widget."""
        for widget in self.mainGui.children():
            if isinstance(widget, kind):
                return widget
        return None

    ##
    #  Public Slots
    ##

    @pyqtSlot(str)
    def openWebsite(self, url: str) -> None:
        """Open a URL in the system's default browser."""
        QDesktopServices.openUrl(QUrl(url))

    @pyqtSlot(str, nwItemClass)
    def createNewNote(self, tag: str, itemClass: nwItemClass) -> None:
        """Process new note request."""
        self.project.createNewNote(tag, itemClass)

    ##
    #  Signal Proxies
    ##

    def emitIndexChangedTags(self, project: NWProject, updated: list[str], deleted: list[str]) -> None:
        """Emit the indexChangedTags signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.indexChangedTags.emit(updated, deleted)

    def emitIndexChangedRefs(self, project: NWProject, updated: list[str]) -> None:
        """Emit the indexChangedRefs signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.indexChangedRefs.emit(updated)

    def emitIndexCleared(self, project: NWProject) -> None:
        """Emit the indexCleared signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.indexCleared.emit()

    def emitIndexAvailable(self, project: NWProject) -> None:
        """Emit the indexAvailable signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.indexAvailable.emit()

    def emitStatusLabelsChanged(self, project: NWProject, kind: T_StatusKind) -> None:
        """Emit the statusLabelsChanged signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.statusLabelsChanged.emit(kind)

    def emitProjectItemChanged(self, project: NWProject, handle: str, change: nwChange) -> None:
        """Emit the projectItemChanged signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.projectItemChanged.emit(handle, change)

    def emitRootFolderChanged(self, project: NWProject, handle: str, change: nwChange) -> None:
        """Emit the rootFolderChanged signal."""
        if self._project and self._project.data.uuid == project.data.uuid:
            self.rootFolderChanged.emit(handle, change)

    ##
    #  Error Cache
    ##

    def clearErrorCache(self) -> None:
        """Clear all cached errors."""
        self._cachedErrors = []

    def appendErrorMessage(self, message: str | Exception) -> None:
        """Append an error message to the error cache."""
        if isinstance(message, Exception):
            message = f"{type(message).__name__}: {message!s}"
        self._cachedErrors.append(message)

    def errorCache(self) -> list[str]:
        """Return all cached errors and clear cache."""
        errors = self._cachedErrors
        self._cachedErrors = []
        return errors

    ##
    #  Alert Boxes
    ##

    def info(self, text: T_Msg, info: str = "", details: str = "", log: bool = True) -> None:
        """Open an information alert box."""
        alert = _GuiAlert(self.mainGui, self.theme)
        alert.setMessage(text, info, details)
        alert.setAlertType(_GuiAlert.INFO, False)
        self._lastAlert = alert.logMessage
        if log:
            self._logMessage(self._lastAlert, logger.info)
        alert.pop()

    def warn(self, text: T_Msg, info: str = "", details: str = "", log: bool = True) -> None:
        """Open a warning alert box."""
        alert = _GuiAlert(self.mainGui, self.theme)
        alert.setMessage(text, info, details)
        alert.setAlertType(_GuiAlert.WARN, False)
        self._lastAlert = alert.logMessage
        if log:
            self._logMessage(self._lastAlert, logger.warning)
        alert.pop()

    def error(
        self,
        text: T_Msg,
        info: str = "",
        details: str = "",
        log: bool = True,
        exc: Exception | None = None,
    ) -> None:
        """Open an error alert box."""
        alert = _GuiAlert(self.mainGui, self.theme)
        alert.setMessage(text, info, details)
        alert.setAlertType(_GuiAlert.ERROR, False)
        if exc:
            alert.setException(exc)
        self._lastAlert = alert.logMessage
        if log:
            self._logMessage(self._lastAlert, logger.error)
        alert.pop()

    def question(self, text: T_Msg, info: str = "", details: str = "", warn: bool = False) -> bool:
        """Open a question box."""
        alert = _GuiAlert(self.mainGui, self.theme)
        alert.setMessage(text, info, details)
        alert.setAlertType(_GuiAlert.WARN if warn else _GuiAlert.ASK, True)
        self._lastAlert = alert.logMessage
        alert.pop()
        return alert.finalState

    ##
    #  Internal Functions
    ##

    def _logMessage(self, message: list[str], log: Callable) -> None:
        """Print message to log."""
        for text in message:
            log(RX_HTML.sub("", text), stacklevel=3)

    def _resetProject(self) -> None:
        """Create a new project and spell checking instance."""
        from novelwriter.core.project import NWProject

        if isinstance(self._project, NWProject):
            self._project.clear()
            del self._project
            del self._spelling
        self._project = NWProject()
        self._spelling = SpellEnchant(self._project)
        self.updateSpellCheckLanguage()
        self._focusMode = False

    def _resetIdleTimer(self) -> None:
        """Reset the timer data for the idle timer."""
        self._idleRefTime = time()
        self._idleTime = 0.0

    def _closeToolDialogs(self) -> None:
        """Close all open tool dialogs."""
        from novelwriter.extensions.modified import NToolDialog

        for widget in self.mainGui.children():
            if isinstance(widget, NToolDialog):
                widget.close()


class _GuiAlert(QMessageBox):
    INFO = 0
    WARN = 1
    ERROR = 2
    ASK = 3

    def __init__(self, parent: QWidget, theme: GuiTheme) -> None:
        super().__init__(parent=parent)
        self._theme = theme
        self._message = []
        self._state = False
        logger.debug("Ready: _GuiAlert")

    def __del__(self) -> None:  # pragma: no cover
        logger.debug("Delete: _GuiAlert")

    @property
    def logMessage(self) -> list[str]:
        return self._message

    @property
    def finalState(self) -> bool:
        return self._state

    def pop(self) -> int:
        """Make sure the message box isn't too small."""
        # See https://stackoverflow.com/a/50549396
        self._spacer = QSpacerItem(20 * self._theme.fontPixelSize, 0, QtSizeMinimum, QtSizeExpanding)
        if isinstance(layout := self.layout(), QGridLayout):  # pragma: no branch
            layout.addItem(self._spacer, layout.rowCount(), 0, 1, layout.columnCount())
        return self.exec()

    def setMessage(self, text: T_Msg, info: str, details: str) -> None:
        """Set the alert box message."""
        self._message = text if isinstance(text, list) else [text]
        appendIfSet(self._message, info)
        appendIfSet(self._message, details)
        self.setText(joinLines(text, "<br>"))
        self.setInformativeText(info)
        self.setDetailedText(details)

    def setException(self, exception: Exception) -> None:
        """Add exception details."""
        info = self.informativeText()
        text = f"<b>{type(exception).__name__}</b>: {exception!s}"
        self.setInformativeText(f"{info}<br>{text}" if info else text)

    def setAlertType(self, level: int, isYesNo: bool) -> None:
        """Set the type of alert and whether the dialog should have
        Yes/No buttons or just an Ok button.
        """
        if isYesNo:
            self._btnYes = self._theme.getStandardButton(nwStandardButton.YES, self)
            self._btnYes.clicked.connect(self._onAccept)
            self._btnNo = self._theme.getStandardButton(nwStandardButton.NO, self)
            self._btnNo.clicked.connect(self._onReject)
            self.addButton(self._btnYes, QMessageBox.ButtonRole.YesRole)
            self.addButton(self._btnNo, QMessageBox.ButtonRole.NoRole)
        else:
            self._btnOk = self._theme.getStandardButton(nwStandardButton.OK, self)
            self._btnOk.clicked.connect(self._onAccept)
            self.addButton(self._btnOk, QMessageBox.ButtonRole.AcceptRole)

        pSz = 2 * self._theme.fontPixelSize
        if level == self.INFO:
            self.setIconPixmap(self._theme.getPixmap("alert_info:info", pSz, pSz))
            self.setWindowTitle(self.tr("Information"))
        elif level == self.WARN:
            self.setIconPixmap(self._theme.getPixmap("alert_warn:warning", pSz, pSz))
            self.setWindowTitle(self.tr("Warning"))
        elif level == self.ERROR:
            self.setIconPixmap(self._theme.getPixmap("alert_error:error", pSz, pSz))
            self.setWindowTitle(self.tr("Error"))
        elif level == self.ASK:
            self.setIconPixmap(self._theme.getPixmap("alert_question:info", pSz, pSz))
            self.setWindowTitle(self.tr("Question"))
        else:  # pragma: no cover
            pass

    @pyqtSlot()
    def _onAccept(self) -> None:
        """Process accepted state."""
        self._state = True
        self.close()

    @pyqtSlot()
    def _onReject(self) -> None:
        """Process rejected state."""
        self._state = False
        self.close()
