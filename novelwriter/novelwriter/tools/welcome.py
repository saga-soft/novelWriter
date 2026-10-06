"""
novelWriter - GUI Welcome Dialog
================================

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

from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from PyQt6.QtCore import QAbstractListModel, QModelIndex, QObject, QPoint, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent, QPainter, QPaintEvent, QPalette, QPen, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMenu,
    QScrollArea,
    QStackedWidget,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatInt, makeFileNameSafe, qtAddAction, safeIsFile
from novelwriter.constants import nwFiles
from novelwriter.core.coretools import ProjectBuilder
from novelwriter.enum import nwItemClass, nwStandardButton
from novelwriter.extensions.configlayout import NColorLabel, NWrappedWidgetBox
from novelwriter.extensions.modified import NDialog, NIconButton, NSpinBox
from novelwriter.extensions.switch import NSwitch
from novelwriter.extensions.versioninfo import VersionInfoWidget
from novelwriter.types import (
    QtAccessibleTextRole,
    QtAlignLeft,
    QtAlignRightTop,
    QtDisplayRole,
    QtKeyDown,
    QtKeyEnter,
    QtKeyReturn,
    QtKeyUp,
    QtScrollAsNeeded,
    QtSelected,
    QtWidgetShortcut,
)

logger = logging.getLogger(__name__)

PANEL_ALPHA = 178
SAMPLE_KEY = "%CREATE_SAMPLE%"
SAMPLE_NAME = "Sample Project"


class GuiWelcome(NDialog):
    """GUI: Welcome Dialog.

    This is the main dialog shown when novelWriter launches or when the
    user wants to create or open another project.
    """

    openProjectRequest = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiWelcome")
        self.setObjectName("GuiWelcome")

        self.setWindowTitle(self.tr("Welcome"))
        self.setMinimumWidth(650)
        self.setMinimumHeight(450)
        self.resize(*CONFIG.welcomeWinSize)

        # Elements
        # ========

        self.bgImage = SHARED.theme.getDecoration("welcome")
        self.nwImage = SHARED.theme.getDecoration("nw-text", h=36)

        self.nwLogo = QLabel(self)
        self.nwLogo.setPixmap(SHARED.theme.getPixmap("novelwriter", 128, 128))

        self.nwLabel = QLabel(self)
        self.nwLabel.setPixmap(self.nwImage)

        self.nwInfo = VersionInfoWidget(self)

        self.tabOpen = _OpenProjectPage(self)
        self.tabOpen.openProjectRequest.connect(self._openProjectPath)

        self.tabNew = _NewProjectPage(self)
        self.tabNew.openProjectRequest.connect(self._openProjectPath)

        self.mainStack = QStackedWidget(self)
        self.mainStack.addWidget(self.tabOpen)
        self.mainStack.addWidget(self.tabNew)

        # Buttons
        # =======

        self.btnList = SHARED.theme.getStandardButton(nwStandardButton.LIST, self)
        self.btnList.clicked.connect(self._showOpenProjectPage)

        self.btnNew = SHARED.theme.getStandardButton(nwStandardButton.NEW, self)
        self.btnNew.clicked.connect(self._showNewProjectPage)

        self.btnBrowse = SHARED.theme.getStandardButton(nwStandardButton.BROWSE, self)
        self.btnBrowse.clicked.connect(self._browseForProject)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.closeDialog)

        self.btnCreate = SHARED.theme.getStandardButton(nwStandardButton.CREATE, self)
        self.btnCreate.clicked.connect(self.tabNew.createNewProject)

        self.btnOpen = SHARED.theme.getStandardButton(nwStandardButton.OPEN, self)
        self.btnOpen.clicked.connect(self._openSelectedItem)

        self.btnBox = QHBoxLayout()
        self.btnBox.addStretch(1)
        self.btnBox.addWidget(self.btnList)
        self.btnBox.addWidget(self.btnNew)
        self.btnBox.addWidget(self.btnBrowse)
        self.btnBox.addWidget(self.btnCancel)
        self.btnBox.addWidget(self.btnCreate)
        self.btnBox.addWidget(self.btnOpen)
        self._setButtonVisibility()

        # Assemble
        # ========

        self.innerBox = QVBoxLayout()
        self.innerBox.addSpacing(16)
        self.innerBox.addWidget(self.nwLabel)
        self.innerBox.addWidget(self.nwInfo)
        self.innerBox.addSpacing(8)
        self.innerBox.addWidget(self.mainStack)
        self.innerBox.addSpacing(16)
        self.innerBox.addLayout(self.btnBox)

        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.nwLogo, 3, QtAlignRightTop)
        self.outerBox.addLayout(self.innerBox, 9)
        self.outerBox.setContentsMargins(128, 48, 24, 48)

        self.setLayout(self.outerBox)
        self.setSizeGripEnabled(True)

        logger.debug("Ready: GuiWelcome")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiWelcome")

    ##
    #  Events
    ##

    def paintEvent(self, event: QPaintEvent) -> None:
        """Overload the paint event to draw the background image."""
        hWin = self.height()
        hPix = min(hWin, 600)
        tMode = Qt.TransformationMode.SmoothTransformation
        painter = QPainter(self)
        painter.drawPixmap(0, hWin - hPix, self.bgImage.scaledToHeight(hPix, tMode))
        painter.end()
        super().paintEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the user closing the window and save settings."""
        self._saveSettings()
        event.accept()
        self.softDelete()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _showNewProjectPage(self) -> None:
        """Show the create new project page."""
        self.mainStack.setCurrentWidget(self.tabNew)
        self._setButtonVisibility()
        self.tabNew.enterForm()

    @pyqtSlot()
    def _showOpenProjectPage(self) -> None:
        """Show the open exiting project page."""
        self.mainStack.setCurrentWidget(self.tabOpen)
        self._setButtonVisibility()

    @pyqtSlot()
    def _browseForProject(self) -> None:
        """Browse for a project to open."""
        if path := SHARED.getProjectFolder(self, CONFIG.homePath()):
            self._openProjectPath(path)

    @pyqtSlot()
    def _openSelectedItem(self) -> None:
        """Open the currently selected project item."""
        if self.mainStack.currentWidget() == self.tabOpen:
            self.tabOpen.openSelectedItem()

    @pyqtSlot(Path)
    def _openProjectPath(self, path: Path) -> None:
        """Emit a project open signal."""
        if isinstance(path, Path):
            # Hide before emitting the open project signal so that any
            # close/backup dialogs don't pop up over it.
            self.hide()
            self.openProjectRequest.emit(path)
        self.close()

    ##
    #  Internal Functions
    ##

    def _saveSettings(self) -> None:
        """Save the user GUI settings."""
        logger.debug("Saving State: GuiWelcome")
        CONFIG.setWelcomeWinSize(self.geometry())

    def _setButtonVisibility(self) -> None:
        """Change the visibility of the dialog buttons."""
        listMode = self.mainStack.currentWidget() == self.tabOpen
        self.btnList.setVisible(not listMode)
        self.btnNew.setVisible(listMode)
        self.btnBrowse.setVisible(listMode)
        self.btnCreate.setVisible(not listMode)
        self.btnOpen.setVisible(listMode)
        if listMode:
            self.btnOpen.setFocus()
        else:
            self.btnCreate.setFocus()


class _OpenProjectPage(QWidget):
    openProjectRequest = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Panel Background
        baseCol = self.palette().base().color()
        baseCol.setAlpha(PANEL_ALPHA)
        basePalette = self.palette()
        basePalette.setColor(QPalette.ColorRole.Base, baseCol)

        # List View
        self.listModel = _ProjectListModel(self)
        self.itemDelegate = _ProjectListItem(self)

        self.listWidget = QListView(self)
        self.listWidget.setItemDelegate(self.itemDelegate)
        self.listWidget.setModel(self.listModel)
        self.listWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.listWidget.setFrameStyle(QFrame.Shape.NoFrame)
        self.listWidget.setPalette(basePalette)
        self.listWidget.clicked.connect(self._projectSelected)
        self.listWidget.doubleClicked.connect(self._projectDoubleClicked)
        self.listWidget.customContextMenuRequested.connect(self._openContextMenu)

        if selectionModel := self.listWidget.selectionModel():  # pragma: no branch
            selectionModel.currentChanged.connect(self._selectionChange)

        # Info / Tool
        self.aMissing = QAction(self)
        self.aMissing.setIcon(SHARED.theme.getIcon("alert_warn:warning"))
        self.aMissing.setToolTip(self.tr("The project path is not reachable."))

        self.selectedPath = QLineEdit(self)
        self.selectedPath.setReadOnly(True)
        self.selectedPath.setFrame(False)
        self.selectedPath.setPalette(basePalette)
        self.selectedPath.setTextMargins(4, 4, 4, 4)
        self.selectedPath.addAction(self.aMissing, QLineEdit.ActionPosition.TrailingPosition)
        self._trPath = self.tr("Path")

        self.keyEnter = QShortcut(self.listWidget)
        self.keyEnter.setKeys([QtKeyEnter, QtKeyReturn])
        self.keyEnter.setContext(QtWidgetShortcut)
        self.keyEnter.activated.connect(self.openSelectedItem)

        self.keyDelete = QShortcut(self)
        self.keyDelete.setKey("Del")
        self.keyDelete.activated.connect(self._deleteSelectedItem)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.listWidget)
        self.outerBox.addWidget(self.selectedPath)
        self.outerBox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.outerBox)

        self._selectFirstItem()

    ##
    #  Events
    ##

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """Capture key press events."""
        if event and event.key() in (QtKeyUp, QtKeyDown):
            self.listWidget.setFocus()
            self.listWidget.keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def openSelectedItem(self) -> None:
        """Open the currently selected project item."""
        if (sel := self.listWidget.selectedIndexes()) and (entry := self.listModel.entry(sel[0])):
            self._processOpenProjectRequest(entry.path)

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex, QModelIndex)
    def _selectionChange(self, current: QModelIndex, previous: QModelIndex) -> None:
        """Process user changing which item is selected."""
        self._projectSelected(current)

    @pyqtSlot(QModelIndex)
    def _projectSelected(self, index: QModelIndex) -> None:
        """Process single click on project item."""
        value = entry.path if (entry := self.listModel.entry(index)) else ""
        value = "" if value == SAMPLE_KEY else value
        text = f"{self._trPath}: {value}"
        self.selectedPath.setText(text)
        self.selectedPath.setToolTip(text)
        self.selectedPath.setCursorPosition(0)
        self.aMissing.setVisible(value != "" and not safeIsFile(Path(value) / nwFiles.PROJ_FILE))

    @pyqtSlot(QModelIndex)
    def _projectDoubleClicked(self, index: QModelIndex) -> None:
        """Process double click on project item."""
        if entry := self.listModel.entry(index):
            self._processOpenProjectRequest(entry.path)

    @pyqtSlot()
    def _deleteSelectedItem(self) -> None:
        """Delete the currently selected project item."""
        if (sel := self.listWidget.selectedIndexes()) and (entry := self.listModel.entry(sel[0])):
            text = self.tr("Remove '{0}' from the recent projects list? The project files will not be deleted.").format(
                entry.title
            )
            if SHARED.question(text):
                self.listModel.removeEntry(sel[0])
            self._selectFirstItem()

    @pyqtSlot("QPoint")
    def _openContextMenu(self, pos: QPoint) -> None:
        """Open the custom context menu."""
        ctxMenu = QMenu(self)
        ctxMenu.setObjectName("ContextMenu")  # Used for testing
        action = qtAddAction(ctxMenu, self.tr("Open Project"))
        action.triggered.connect(self.openSelectedItem)
        action = qtAddAction(ctxMenu, self.tr("Remove Project"))
        action.triggered.connect(self._deleteSelectedItem)
        ctxMenu.exec(self.mapToGlobal(pos))
        ctxMenu.setParent(None)

    ##
    #  Internal Functions
    ##

    def _processOpenProjectRequest(self, path: str) -> None:
        """Process an open project request which may involve create."""
        if path == SAMPLE_KEY:
            if location := SHARED.getProjectFolder(self, CONFIG.homePath()):
                sample = location / SAMPLE_NAME
                data = {
                    "name": SAMPLE_NAME,
                    "path": sample,
                    "sample": True,
                }
                builder = ProjectBuilder()
                if builder.buildProject(data):
                    self.openProjectRequest.emit(sample)
            else:
                SHARED.error(self.tr("You must select a location for the example project."))
                return
        else:
            self.openProjectRequest.emit(Path(path))

    def _selectFirstItem(self) -> None:
        """Select the first item, if any are available."""
        index = self.listModel.index(0)
        self.listWidget.setCurrentIndex(index)
        self._projectSelected(index)


class _ProjectListItem(QStyledItemDelegate):
    __slots__ = ("_dFont", "_dPen", "_hPx", "_icon", "_pPx", "_tFont")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        fPx = SHARED.theme.fontPixelSize
        tPx = SHARED.theme.fontPixelSizeLarge
        iPx = tPx + fPx

        self._pPx = (iPx + 4, tPx + 4)  # Painter coordinates
        self._hPx = 8 + tPx + fPx  # Fixed height

        self._tFont = SHARED.theme.guiFontLargeB
        self._dFont = SHARED.theme.guiFont
        self._dPen = QPen(SHARED.theme.helpText)

        self._icon = SHARED.theme.getPixmap("proj_nwx", iPx, iPx)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint a project entry on the canvas."""
        if isinstance(entry := index.data(QtDisplayRole), _ProjectListEntry):  # pragma: no branch
            rect = option.rect
            tFlag = Qt.TextFlag.TextSingleLine
            x, y = self._pPx

            painter.save()
            if bool(option.state & QtSelected):
                painter.setOpacity(0.25)
                painter.fillRect(rect, QApplication.palette().text())
                painter.setOpacity(1.0)

            painter.drawPixmap(2, rect.top() + 6, self._icon)
            painter.setFont(self._tFont)
            painter.drawText(rect.adjusted(x, 4, 0, 0), tFlag, entry.title)
            painter.setFont(self._dFont)
            painter.setPen(self._dPen)
            painter.drawText(rect.adjusted(x, y, 0, 0), tFlag, entry.details)
            painter.restore()

    def sizeHint(self, opt: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        """Set the size hint to fixed height."""
        return QSize(opt.rect.width(), self._hPx)


class _ProjectListEntry(NamedTuple):
    title: str
    path: str
    details: str
    accessible: str


class _ProjectListModel(QAbstractListModel):
    __slots__ = ("_data",)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent=parent)

        self._data: list[_ProjectListEntry] = []

        words = self.tr("Word Count")
        opened = self.tr("Last Opened")
        records = sorted(CONFIG.recentProjects.listEntries(), key=lambda x: x[3], reverse=True)
        for path, title, count, time in records:
            when = CONFIG.localDate(datetime.fromtimestamp(time))
            self._data.append(
                _ProjectListEntry(
                    title=title,
                    path=path,
                    details=f"{opened}: {when}, {words}: {formatInt(count)}",
                    accessible=f"{title}, {opened} {when}, {words} {formatInt(count)}",
                )
            )

        if not self._data:
            details = self.tr("Select to create an example project")
            self._data.append(
                _ProjectListEntry(title=SAMPLE_NAME, path=SAMPLE_KEY, details=details, accessible=details)
            )

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        """Return the size of the model."""
        return len(self._data)

    def entry(self, index: QModelIndex) -> _ProjectListEntry | None:
        """Return an entry in the model."""
        if index.isValid() and 0 <= (idx := index.row()) < len(self._data):
            return self._data[idx]
        return None

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> _ProjectListEntry | str | None:
        """Return data for an individual item."""
        if entry := self.entry(index):
            if role == QtDisplayRole:
                return entry
            elif role == QtAccessibleTextRole:
                return entry.accessible
        return None

    def removeEntry(self, index: QModelIndex) -> bool:
        """Remove an entry in the model."""
        if entry := self.entry(index):
            self.beginRemoveRows(index.parent(), index.row(), index.row())
            self._data.pop(index.row())
            self.endRemoveRows()
            CONFIG.recentProjects.remove(entry.path)
            return True
        return False


class _NewProjectPage(QWidget):
    openProjectRequest = pyqtSignal(Path)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Main Form
        # =========

        self.projectForm = _NewProjectForm(self)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setWidget(self.projectForm)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(QtScrollAsNeeded)
        self.scrollArea.setVerticalScrollBarPolicy(QtScrollAsNeeded)

        self.enterForm = self.projectForm.enterForm

        # Assemble
        # ========

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.scrollArea)
        self.outerBox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.outerBox)

        # Styles
        # ======

        base = self.palette().base().color()
        base.setAlpha(PANEL_ALPHA)

        panelPalette = self.palette()
        panelPalette.setColor(QPalette.ColorRole.Base, base)
        panelPalette.setColor(QPalette.ColorRole.Window, base)

        self.scrollArea.setFrameStyle(QFrame.Shape.NoFrame)
        self.scrollArea.setPalette(panelPalette)
        self.projectForm.setPalette(panelPalette)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def createNewProject(self) -> None:
        """Create a new project from the data in the form."""
        data = self.projectForm.getProjectData()
        if not data.get("name"):
            SHARED.error(self.tr("A project name is required."))
            return
        builder = ProjectBuilder()
        if builder.buildProject(data) and (path := builder.projPath):
            self.openProjectRequest.emit(path)
        return


class _NewProjectForm(QWidget):
    FILL_BLANK = 0
    FILL_SAMPLE = 1
    FILL_COPY = 2

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._basePath = CONFIG.lastPath("project")
        self._fillMode = self.FILL_BLANK
        self._copyPath = None

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        # Project Settings
        # ================

        # Project Name
        self.projName = QLineEdit(self)
        self.projName.setMaxLength(200)
        self.projName.setPlaceholderText(self.tr("Required"))
        self.projName.textChanged.connect(self._updateProjPath)

        self.projNameLabel = QLabel(self.tr("Project Name"), self)
        self.projNameLabel.setBuddy(self.projName)

        # Author
        self.projAuthor = QLineEdit(self)
        self.projAuthor.setMaxLength(200)
        self.projAuthor.setPlaceholderText(self.tr("Optional"))
        self.projAuthor.setText(CONFIG.lastAuthor)

        self.projAuthorLabel = QLabel(self.tr("Author"), self)
        self.projAuthorLabel.setBuddy(self.projAuthor)

        # Project Path
        self.projPath = QLineEdit(self)
        self.projPath.setReadOnly(True)

        self.browsePath = NIconButton(self, iSz, "browse:system")
        self.browsePath.setToolTip(self.tr("Browse for new project path"))
        self.browsePath.clicked.connect(self._doBrowse)

        self.pathBox = QHBoxLayout()
        self.pathBox.addWidget(self.projPath)
        self.pathBox.addWidget(self.browsePath)

        self.projPathLabel = QLabel(self.tr("Project Path"), self)
        self.projPathLabel.setBuddy(self.projPath)

        # Fill Project
        self.projFill = QLineEdit(self)
        self.projFill.setReadOnly(True)

        self.browseFill = NIconButton(self, iSz, "document_add:add")
        self.browseFill.setToolTip(self.tr("Fill new project"))

        self.fillMenu = QMenu(self.browseFill)

        self.fillBlank = qtAddAction(
            self.fillMenu,
            self.tr("Create a fresh project"),
            icon=SHARED.theme.getIcon("document:file"),
        )
        self.fillBlank.triggered.connect(self._setFillBlank)

        self.fillSample = qtAddAction(
            self.fillMenu,
            self.tr("Create an example project"),
            icon=SHARED.theme.getIcon("document_add:add"),
        )
        self.fillSample.triggered.connect(self._setFillSample)

        self.fillCopy = qtAddAction(
            self.fillMenu,
            self.tr("Copy an existing project"),
            icon=SHARED.theme.getIcon("project_copy:action"),
        )
        self.fillCopy.triggered.connect(self._setFillCopy)

        self.browseFill.setMenu(self.fillMenu)

        self.fillBox = QHBoxLayout()
        self.fillBox.addWidget(self.projFill)
        self.fillBox.addWidget(self.browseFill)

        self.projFillLabel = QLabel(self.tr("Prefill Project"), self)
        self.projFillLabel.setBuddy(self.projFill)

        # Project Form
        self.projectForm = QFormLayout()
        self.projectForm.setAlignment(QtAlignLeft)
        self.projectForm.addRow(self.projNameLabel, self.projName)
        self.projectForm.addRow(self.projAuthorLabel, self.projAuthor)
        self.projectForm.addRow(self.projPathLabel, self.pathBox)
        self.projectForm.addRow(self.projFillLabel, self.fillBox)

        # Chapters and Scenes
        # ===================

        self.numChapters = NSpinBox(self, minVal=0, maxVal=200)
        self.numChapters.setFixedNumbersWidth(3)
        self.numChapters.setValue(0)
        self.numChapters.setToolTip(self.tr("Set to 0 to only add scenes"))

        self.chapterBox = NWrappedWidgetBox(self.tr("Add {0} chapter documents"), self.numChapters)
        self.chapterBox.addStretch(1)

        self.numScenes = NSpinBox(self, minVal=0, maxVal=200)
        self.numScenes.setFixedNumbersWidth(3)
        self.numScenes.setValue(0)

        self.sceneBox = NWrappedWidgetBox(self.tr("Add {0} scene documents (to each chapter)"), self.numScenes)
        self.sceneBox.addStretch(1)

        self.novelForm = QVBoxLayout()
        self.novelForm.addLayout(self.chapterBox)
        self.novelForm.addLayout(self.sceneBox)

        # Project Notes
        # =============

        self.addPlot = NSwitch(self, height=iPx)
        self.addPlot.setChecked(True)
        self.addPlot.clicked.connect(self._syncSwitches)

        self.addChar = NSwitch(self, height=iPx)
        self.addChar.setChecked(True)
        self.addChar.clicked.connect(self._syncSwitches)

        self.addWorld = NSwitch(self, height=iPx)
        self.addWorld.setChecked(False)
        self.addWorld.clicked.connect(self._syncSwitches)

        self.addNotes = NSwitch(self, height=iPx)
        self.addNotes.setChecked(False)

        self.notesForm = QFormLayout()
        self.notesForm.setAlignment(QtAlignLeft)
        self.notesForm.addRow(self.tr("Add a folder for plot notes"), self.addPlot)
        self.notesForm.addRow(self.tr("Add a folder for character notes"), self.addChar)
        self.notesForm.addRow(self.tr("Add a folder for location notes"), self.addWorld)
        self.notesForm.addRow(self.tr("Add example notes to the above"), self.addNotes)

        # Assemble
        # ========

        self.lblChSc = NColorLabel(self.tr("Chapters and Scenes"), self, scale=1.15, bold=True)
        self.lblNotes = NColorLabel(self.tr("Project Notes"), self, scale=1.15, bold=True)
        self.lblNew = NColorLabel(self.tr("Create New Project"), self, scale=1.15, bold=True)

        self.extraBox = QVBoxLayout()
        self.extraBox.addWidget(self.lblChSc)
        self.extraBox.addLayout(self.novelForm)
        self.extraBox.addSpacing(16)
        self.extraBox.addWidget(self.lblNotes)
        self.extraBox.addLayout(self.notesForm)
        self.extraBox.setContentsMargins(0, 0, 0, 0)

        self.extraWidget = QWidget(self)
        self.extraWidget.setLayout(self.extraBox)
        self.extraWidget.setContentsMargins(0, 0, 0, 0)

        self.formBox = QVBoxLayout()
        self.formBox.addWidget(self.lblNew)
        self.formBox.addLayout(self.projectForm)
        self.formBox.addSpacing(16)
        self.formBox.addWidget(self.extraWidget)
        self.formBox.addStretch(1)

        self.setLayout(self.formBox)

        self._updateProjPath()
        self._updateFillInfo()

    def enterForm(self) -> None:
        """Focus the project name field when entering the form."""
        self.projName.setFocus()
        self.projName.selectAll()

    def getProjectData(self) -> dict:
        """Collect form data and return it as a dictionary."""
        roots = []
        if self.addPlot.isChecked():
            roots.append(nwItemClass.PLOT)
        if self.addChar.isChecked():
            roots.append(nwItemClass.CHARACTER)
        if self.addWorld.isChecked():
            roots.append(nwItemClass.WORLD)
        return {
            "name": self.projName.text().strip(),
            "author": self.projAuthor.text().strip(),
            "path": self.projPath.text(),
            "blank": self._fillMode == self.FILL_BLANK,
            "sample": self._fillMode == self.FILL_SAMPLE,
            "template": self._copyPath if self._fillMode == self.FILL_COPY else None,
            "chapters": self.numChapters.value(),
            "scenes": self.numScenes.value(),
            "roots": roots,
            "notes": self.addNotes.isChecked(),
        }

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _doBrowse(self) -> None:
        """Select a project folder."""
        if path := SHARED.getProjectFolder(self, self._basePath):
            self._basePath = path
            self._updateProjPath()
            CONFIG.setLastPath("project", path)

    @pyqtSlot()
    def _updateProjPath(self) -> None:
        """Update the path box to show the full project path."""
        projName = makeFileNameSafe(self.projName.text().strip())
        self.projPath.setText(str(self._basePath / projName))

    @pyqtSlot()
    def _syncSwitches(self) -> None:
        """Check if the add notes option should also be switched off."""
        addPlot = self.addPlot.isChecked()
        addChar = self.addChar.isChecked()
        addWorld = self.addWorld.isChecked()
        if not (addPlot or addChar or addWorld):
            self.addNotes.setChecked(False)

    @pyqtSlot()
    def _setFillBlank(self) -> None:
        """Set fill mode to blank project."""
        self._fillMode = self.FILL_BLANK
        self._updateFillInfo()

    @pyqtSlot()
    def _setFillSample(self) -> None:
        """Set fill mode to sample project."""
        self._fillMode = self.FILL_SAMPLE
        self._updateFillInfo()

    @pyqtSlot()
    def _setFillCopy(self) -> None:
        """Set fill mode to copy project."""
        if copyPath := SHARED.getProjectPath(self, allowZip=True):
            self._fillMode = self.FILL_COPY
            self._copyPath = copyPath
            self._updateFillInfo()

    ##
    #  Internal Functions
    ##

    def _updateFillInfo(self) -> None:
        """Update the text of the project fill box."""
        text = ""
        if self._fillMode == self.FILL_BLANK:
            text = self.tr("Fresh Project")
        elif self._fillMode == self.FILL_SAMPLE:
            text = self.tr("Example Project")
        elif self._fillMode == self.FILL_COPY:
            text = self.tr("Template: {0}").format(str(self._copyPath))
        else:  # pragma: no cover
            pass

        self.projFill.setText(text)
        self.projFill.setToolTip(text)
        self.projFill.setCursorPosition(0)
        self.extraWidget.setVisible(self._fillMode == self.FILL_BLANK)
