"""
novelWriter - GUI Build Manuscript
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

import logging

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QApplication,
    QDialogButtonBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.common import makeFileNameSafe, openExternalPath, safeExists, safeIsDir
from novelwriter.constants import nwLabels
from novelwriter.core.item import ProjectItem
from novelwriter.enum import nwBuildFmt, nwStandardButton, nwToolButton
from novelwriter.extensions.configlayout import NColorLabel
from novelwriter.extensions.modified import NDialog, NPushButton
from novelwriter.extensions.progressbars import NProgressSimple
from novelwriter.manuscript.docbuild import DocumentBuilder
from novelwriter.types import QtAlignCenter, QtRoleAction, QtRoleDestruct, QtUserRole

if TYPE_CHECKING:
    from PyQt6.QtGui import QCloseEvent

    from novelwriter.manuscript.buildsettings import BuildSettings

logger = logging.getLogger(__name__)


class GuiManuscriptBuild(NDialog):
    """GUI Tools: Build Manuscript Dialog.

    This is the tool for running the build itself. It can be accessed
    independently of the Build Manuscript Tool.
    """

    D_KEY = QtUserRole

    def __init__(self, parent: QWidget, build: BuildSettings) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiManuscriptBuild")
        self.setObjectName("GuiManuscriptBuild")

        self._parent = parent
        self._build = build

        self.setWindowTitle(self.tr("Build Manuscript"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        iSz = SHARED.theme.baseIconSize
        bSz = SHARED.theme.toolButtonIconSize

        pOptions = SHARED.project.options
        self.resize(
            pOptions.getInt("GuiManuscriptBuild", "winWidth", 620),
            pOptions.getInt("GuiManuscriptBuild", "winHeight", 360),
        )

        # Output Format
        # =============

        self.lblFormat = QLabel(self.tr("Output Format"), self)
        self.listFormats = QListWidget(self)
        self.listFormats.setIconSize(iSz)
        current = None
        for key in nwBuildFmt:
            item = QListWidgetItem()
            item.setText(nwLabels.BUILD_FMT[key])
            item.setData(self.D_KEY, key)
            self.listFormats.addItem(item)
            if key == self._build.lastFormat:
                current = item
        if current:
            self.listFormats.setCurrentItem(current)

        self.formatBox = QVBoxLayout()
        self.formatBox.addWidget(self.lblFormat, 0)
        self.formatBox.addWidget(self.listFormats, 1)
        self.formatBox.setContentsMargins(0, 0, 0, 0)

        self.formatWidget = QWidget(self)
        self.formatWidget.setLayout(self.formatBox)
        self.formatWidget.setContentsMargins(0, 0, 0, 0)

        # Table of Contents
        # =================

        self.lblContent = QLabel(self.tr("Table of Contents"), self)

        self.listContent = QListWidget(self)
        self.listContent.setIconSize(iSz)
        self.listContent.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        self.contentBox = QVBoxLayout()
        self.contentBox.addWidget(self.lblContent, 0)
        self.contentBox.addWidget(self.listContent, 0)
        self.contentBox.setContentsMargins(0, 0, 0, 0)

        self.contentWidget = QWidget(self)
        self.contentWidget.setLayout(self.contentBox)
        self.contentWidget.setContentsMargins(0, 0, 0, 0)

        # Dialog Controls
        # ===============

        self.lblMain = NColorLabel(
            self.tr("Build: {0}").format(self._build.name),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.HEADER_SCALE,
        )

        # Build Path
        self.lblPath = QLabel(self.tr("Path"), self)
        self.buildPath = QLineEdit(self)
        self.btnBrowse = SHARED.theme.getIconButton(nwToolButton.BROWSE, self)

        self.pathBox = QHBoxLayout()
        self.pathBox.addWidget(self.buildPath)
        self.pathBox.addWidget(self.btnBrowse)
        self.pathBox.setSpacing(8)

        # Build Name
        self.lblName = QLabel(self.tr("File Name"), self)
        self.buildName = QLineEdit(self)
        self.btnReset = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnReset.setToolTip(self.tr("Reset file name to default"))

        self.nameBox = QHBoxLayout()
        self.nameBox.addWidget(self.buildName)
        self.nameBox.addWidget(self.btnReset)
        self.nameBox.setSpacing(8)

        # Build Progress
        self.buildProgress = NProgressSimple(self)
        self.buildProgress.setMinimum(0)
        self.buildProgress.setValue(0)
        self.buildProgress.setTextVisible(False)
        self.buildProgress.setFixedHeight(8)

        # Build Box
        self.buildBox = QGridLayout()
        self.buildBox.addWidget(self.lblPath, 0, 0)
        self.buildBox.addLayout(self.pathBox, 0, 1)
        self.buildBox.addWidget(self.lblName, 1, 0)
        self.buildBox.addLayout(self.nameBox, 1, 1)
        self.buildBox.setHorizontalSpacing(8)
        self.buildBox.setVerticalSpacing(4)

        # Dialog Buttons
        self.btnOpen = NPushButton(self, self.tr("Open Folder"), bSz, "browse:system")
        self.btnOpen.setAutoDefault(False)

        self.btnBuild = SHARED.theme.getStandardButton(nwStandardButton.BUILD, self)
        self.btnBuild.setAutoDefault(True)

        self.btnClose = SHARED.theme.getStandardButton(nwStandardButton.CLOSE, self)
        self.btnClose.setAutoDefault(False)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnOpen, QtRoleAction)
        self.btnBox.addButton(self.btnBuild, QtRoleAction)
        self.btnBox.addButton(self.btnClose, QtRoleDestruct)

        # Assemble GUI
        # ============

        self.mainSplit = QSplitter(self)
        self.mainSplit.addWidget(self.formatWidget)
        self.mainSplit.addWidget(self.contentWidget)
        self.mainSplit.setHandleWidth(16)
        self.mainSplit.setCollapsible(0, False)
        self.mainSplit.setCollapsible(1, False)
        self.mainSplit.setStretchFactor(0, 0)
        self.mainSplit.setStretchFactor(1, 1)
        self.mainSplit.setSizes([
            pOptions.getInt("GuiManuscriptBuild", "fmtWidth", 360),
            pOptions.getInt("GuiManuscriptBuild", "sumWidth", 360),
        ])

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.lblMain, 0, QtAlignCenter)
        self.outerBox.addSpacing(16)
        self.outerBox.addWidget(self.mainSplit, 1)
        self.outerBox.addSpacing(4)
        self.outerBox.addWidget(self.buildProgress, 0)
        self.outerBox.addSpacing(4)
        self.outerBox.addLayout(self.buildBox, 0)
        self.outerBox.addSpacing(16)
        self.outerBox.addWidget(self.btnBox, 0)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)

        self.btnBuild.setFocus()
        self._populateContentList()
        self.buildPath.setText(str(self._build.lastBuildPath))
        if self._build.lastBuildName:
            self.buildName.setText(self._build.lastBuildName)
        else:
            self._doResetBuildName()

        # Signals
        self.btnReset.clicked.connect(self._doResetBuildName)
        self.btnBrowse.clicked.connect(self._doSelectPath)
        self.btnBox.clicked.connect(self._dialogButtonClicked)
        self.listFormats.itemSelectionChanged.connect(self._resetProgress)

        logger.debug("Ready: GuiManuscriptBuild")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiManuscriptBuild")

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the user closing the window so we can save GUI
        settings.
        """
        self._saveSettings()
        event.accept()
        self.softDelete()

    ##
    #  Private Slots
    ##

    @pyqtSlot("QAbstractButton*")
    def _dialogButtonClicked(self, button: QAbstractButton) -> None:
        """Handle button clicks from the dialog button box."""
        if button == self.btnBuild:
            self._runBuild()
        elif button == self.btnOpen:
            self._openOutputFolder()
        elif button == self.btnClose:
            self.close()

    @pyqtSlot()
    def _doSelectPath(self) -> None:
        """Select a folder for output."""
        bPath = Path(self.buildPath.text())
        bPath = bPath if safeIsDir(bPath) else self._build.lastBuildPath
        savePath = QFileDialog.getExistingDirectory(self, self.tr("Select Folder"), str(bPath))
        if savePath:
            self.buildPath.setText(savePath)

    @pyqtSlot()
    def _doResetBuildName(self) -> None:
        """Generate a default build name."""
        bName = f"{SHARED.project.data.name} - {self._build.name}"
        self.buildName.setText(bName)
        self._build.setLastBuildName(bName)

    @pyqtSlot()
    def _resetProgress(self) -> None:
        """Set the progress bar back to 0."""
        self.buildProgress.setValue(0)

    ##
    #  Internal Functions
    ##

    def _runBuild(self) -> bool:
        """Run the currently selected build."""
        bFormat = self._getSelectedFormat()
        if not isinstance(bFormat, nwBuildFmt):
            return False

        bName = self.buildName.text().strip()
        if not bName:
            self._doResetBuildName()
            bName = self.buildName.text().strip()

        self.buildProgress.setValue(0)
        bPath = Path(self.buildPath.text())
        if not safeIsDir(bPath):
            SHARED.error(self.tr("Output folder does not exist."))
            return False

        bExt = nwLabels.BUILD_EXT[bFormat]
        buildPath = (bPath / makeFileNameSafe(bName)).with_suffix(bExt)

        if safeExists(buildPath) and not SHARED.question(
            self.tr("The file already exists. Do you want to overwrite it?")
        ):
            return False

        # Make sure editor content is saved before we start
        SHARED.saveEditor()

        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        docBuild = DocumentBuilder(SHARED.project, self._build)
        docBuild.queueAll()

        self.buildProgress.setMaximum(len(docBuild))
        for i, _ in docBuild.iterBuildDocument(buildPath, bFormat):
            self.buildProgress.setValue(i + 1)

        QApplication.restoreOverrideCursor()

        self._build.setLastBuildPath(bPath)
        self._build.setLastBuildName(bName)
        self._build.setLastFormat(bFormat)

        QTimer.singleShot(3000, self._resetProgress)

        return True

    def _getSelectedFormat(self) -> nwBuildFmt | None:
        """Get the currently selected format."""
        items = self.listFormats.selectedItems()
        if items and isinstance(items[0], QListWidgetItem):
            return items[0].data(self.D_KEY)
        return None

    def _saveSettings(self) -> None:
        """Save the user GUI settings."""
        logger.debug("Saving State: GuiManuscriptBuild")
        mainSplit = self.mainSplit.sizes()
        pOptions = SHARED.project.options
        pOptions.setValue("GuiManuscriptBuild", "winWidth", self.width())
        pOptions.setValue("GuiManuscriptBuild", "winHeight", self.height())
        pOptions.setValue("GuiManuscriptBuild", "fmtWidth", mainSplit[0])
        pOptions.setValue("GuiManuscriptBuild", "sumWidth", mainSplit[1])
        pOptions.saveSettings()

    def _populateContentList(self) -> None:
        """Build the content list."""
        rootMap = {}
        filtered = self._build.buildItemFilter(SHARED.project)
        self.listContent.clear()
        for nwItem in SHARED.project.tree:
            tHandle = nwItem.itemHandle
            rHandle = nwItem.itemRoot

            if tHandle is None or rHandle is None or not nwItem.isFileType():
                continue

            if filtered.get(tHandle, (False, 0))[0]:
                if rHandle not in rootMap:
                    rItem = SHARED.project.tree[rHandle]
                    if isinstance(rItem, ProjectItem):
                        rootMap[rHandle] = rItem.itemName

                rootName = rootMap.get(rHandle, "??????")
                item = QListWidgetItem(f"{rootName}: {nwItem.itemName}")
                item.setIcon(nwItem.getMainIcon())
                self.listContent.addItem(item)

    def _openOutputFolder(self) -> None:
        """Open the build folder in the system's file explorer."""
        openExternalPath(Path(self.buildPath.text()))
