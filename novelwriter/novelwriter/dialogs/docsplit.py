"""
novelWriter - GUI Doc Split Dialog
==================================

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

import logging

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.configlayout import NColorLabel
from novelwriter.extensions.modified import NComboBox, NDialog
from novelwriter.extensions.switch import NSwitch
from novelwriter.types import QtAccepted, QtRoleAccept, QtRoleReject, QtUserRole

logger = logging.getLogger(__name__)


class GuiDocSplit(NDialog):
    """GUI: Document Split Tool."""

    LINE_ROLE = QtUserRole
    LEVEL_ROLE = QtUserRole + 1
    LABEL_ROLE = QtUserRole + 2

    def __init__(self, parent: QWidget, sHandle: str) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocSplit")
        self.setObjectName("GuiDocSplit")

        self._data = {}
        self._text = []

        self.setWindowTitle(self.tr("Split Document"))

        self.headLabel = QLabel(self.tr("Document Headings"), self)
        self.headLabel.setFont(SHARED.theme.guiFontB)
        self.helpLabel = NColorLabel(
            self.tr("Select the maximum level to split into files."),
            self,
            color=SHARED.theme.helpText,
            wrap=True,
        )

        # Values
        iPx = SHARED.theme.baseIconHeight

        options = SHARED.project.options
        spLevel = options.getInt("GuiDocSplit", "spLevel", 3)
        intoFolder = options.getBool("GuiDocSplit", "intoFolder", True)
        docHierarchy = options.getBool("GuiDocSplit", "docHierarchy", True)

        # Heading Selection
        self.listBox = QListWidget(self)
        self.listBox.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.listBox.setMinimumWidth(400)
        self.listBox.setMinimumHeight(180)

        self.splitLevel = NComboBox(self)
        self.splitLevel.addItem(self.tr("Split on Heading Level 1 (Partition)"), 1)
        self.splitLevel.addItem(self.tr("Split up to Heading Level 2 (Chapter)"), 2)
        self.splitLevel.addItem(self.tr("Split up to Heading Level 3 (Scene)"), 3)
        self.splitLevel.addItem(self.tr("Split up to Heading Level 4 (Section)"), 4)
        if (spIndex := self.splitLevel.findData(spLevel)) != -1:
            self.splitLevel.setCurrentIndex(spIndex)
        self.splitLevel.currentIndexChanged.connect(self._reloadList)

        # Split Options
        self.folderSwitch = NSwitch(self, height=iPx)
        self.folderSwitch.setChecked(intoFolder)
        self.folderLabel = QLabel(self.tr("Split into a new folder"), self)
        self.folderLabel.setBuddy(self.folderSwitch)

        self.hierarchySwitch = NSwitch(self, height=iPx)
        self.hierarchySwitch.setChecked(docHierarchy)
        self.hierarchyLabel = QLabel(self.tr("Create document hierarchy"), self)
        self.hierarchyLabel.setBuddy(self.hierarchySwitch)

        self.trashSwitch = NSwitch(self, height=iPx)
        self.trashLabel = QLabel(self.tr("Move split document to Trash"), self)
        self.trashLabel.setBuddy(self.trashSwitch)

        self.optBox = QGridLayout()
        self.optBox.addWidget(self.folderLabel, 0, 0)
        self.optBox.addWidget(self.folderSwitch, 0, 1)
        self.optBox.addWidget(self.hierarchyLabel, 1, 0)
        self.optBox.addWidget(self.hierarchySwitch, 1, 1)
        self.optBox.addWidget(self.trashLabel, 2, 0)
        self.optBox.addWidget(self.trashSwitch, 2, 1)
        self.optBox.setVerticalSpacing(8)
        self.optBox.setHorizontalSpacing(12)
        self.optBox.setColumnStretch(3, 1)

        # Buttons
        self.btnOk = SHARED.theme.getStandardButton(nwStandardButton.OK, self)
        self.btnOk.clicked.connect(self.accept)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.reject)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnOk, QtRoleAccept)
        self.btnBox.addButton(self.btnCancel, QtRoleReject)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.setSpacing(0)
        self.outerBox.addWidget(self.headLabel)
        self.outerBox.addWidget(self.helpLabel)
        self.outerBox.addSpacing(8)
        self.outerBox.addWidget(self.listBox)
        self.outerBox.addWidget(self.splitLevel)
        self.outerBox.addSpacing(8)
        self.outerBox.addLayout(self.optBox)
        self.outerBox.addSpacing(12)
        self.outerBox.addWidget(self.btnBox)
        self.setLayout(self.outerBox)

        # Load Content
        self._loadContent(sHandle)

        logger.debug("Ready: GuiDocSplit")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiDocSplit")

    def data(self) -> tuple[dict, list[str]]:
        """Return the user's choices. Also save the users options for
        the next time the dialog is used.
        """
        headerList = [
            (item.data(self.LINE_ROLE), item.data(self.LEVEL_ROLE), item.data(self.LABEL_ROLE))
            for i in range(self.listBox.count())
            if (item := self.listBox.item(i))  # pragma: no branch
        ]

        spLevel = self.splitLevel.currentData()
        intoFolder = self.folderSwitch.isChecked()
        docHierarchy = self.hierarchySwitch.isChecked()
        moveToTrash = self.trashSwitch.isChecked()

        self._data["spLevel"] = spLevel
        self._data["headerList"] = headerList
        self._data["intoFolder"] = intoFolder
        self._data["docHierarchy"] = docHierarchy
        self._data["moveToTrash"] = moveToTrash

        logger.debug("Saving State: GuiDocSplit")
        options = SHARED.project.options
        options.setValue("GuiDocSplit", "spLevel", spLevel)
        options.setValue("GuiDocSplit", "intoFolder", intoFolder)
        options.setValue("GuiDocSplit", "docHierarchy", docHierarchy)

        return self._data, self._text

    @classmethod
    def getData(cls, parent: QWidget, handle: str) -> tuple[dict, list[str], bool]:
        """Pop the dialog and return the result."""
        dialog = cls(parent, handle)
        dialog.exec()
        data, text = dialog.data()
        accepted = dialog.result() == QtAccepted
        dialog.softDelete()
        return data, text, accepted

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _reloadList(self) -> None:
        """Reload the content of the list box."""
        if sHandle := self._data.get("sHandle"):
            self._loadContent(sHandle)

    ##
    #  Internal Functions
    ##

    def _loadContent(self, sHandle: str) -> None:
        """Load content from a given source item."""
        self._data = {}
        self._data["sHandle"] = sHandle

        self.listBox.clear()

        nwItem = SHARED.project.tree[sHandle]
        if nwItem is None or not nwItem.isFileType():
            return

        spLevel = self.splitLevel.currentData()
        if not self._text:
            self._text = SHARED.project.storage.getDocumentText(sHandle).splitlines()

        for i, line in enumerate(self._text):
            pos = -1
            level = 0
            label = line.strip()
            if line.startswith("# ") and spLevel >= 1:
                pos = i
                level = 1
                label = line[2:].strip()
            elif line.startswith("## ") and spLevel >= 2:
                pos = i
                level = 2
                label = line[3:].strip()
            elif line.startswith("### ") and spLevel >= 3:
                pos = i
                level = 3
                label = line[4:].strip()
            elif line.startswith("#### ") and spLevel >= 4:
                pos = i
                level = 4
                label = line[5:].strip()
            elif line.startswith("#! ") and spLevel >= 1:
                pos = i
                level = 1
                label = line[3:].strip()
            elif line.startswith("##! ") and spLevel >= 2:
                pos = i
                level = 2
                label = line[4:].strip()
            elif line.startswith("###! ") and spLevel >= 3:
                pos = i
                level = 3
                label = line[5:].strip()

            if pos >= 0 and level > 0:
                trItem = QListWidgetItem()
                trItem.setText(line.strip())
                trItem.setData(self.LINE_ROLE, pos)
                trItem.setData(self.LEVEL_ROLE, level)
                trItem.setData(self.LABEL_ROLE, label)
                self.listBox.addItem(trItem)

        return
