"""
novelWriter - GUI Doc Merge Dialog
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

from PyQt6.QtCore import Qt, pyqtSlot
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
from novelwriter.extensions.modified import NDialog
from novelwriter.extensions.switch import NSwitch
from novelwriter.types import QtAccepted, QtRoleAccept, QtRoleReject, QtRoleReset, QtUserRole

logger = logging.getLogger(__name__)


class GuiDocMerge(NDialog):
    """GUI: Document Merge Tool."""

    D_HANDLE = QtUserRole

    def __init__(self, parent: QWidget, sHandle: str, itemList: list[str]) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocMerge")
        self.setObjectName("GuiDocMerge")
        self.setWindowTitle(self.tr("Merge Documents"))

        self._data = {}

        self.headLabel = QLabel(self.tr("Documents to Merge"), self)
        self.headLabel.setFont(SHARED.theme.guiFontB)
        self.helpLabel = NColorLabel(
            self.tr("Drag and drop items to change the order, or uncheck to exclude."),
            self,
            color=SHARED.theme.helpText,
            wrap=True,
        )

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        self.listBox = QListWidget(self)
        self.listBox.setIconSize(iSz)
        self.listBox.setMinimumWidth(400)
        self.listBox.setMinimumHeight(180)
        self.listBox.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.listBox.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.listBox.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Merge Options
        self.trashSwitch = NSwitch(self, height=iPx)
        self.trashLabel = QLabel(self.tr("Move merged items to Trash"), self)
        self.trashLabel.setBuddy(self.trashSwitch)

        self.optBox = QGridLayout()
        self.optBox.addWidget(self.trashLabel, 0, 0)
        self.optBox.addWidget(self.trashSwitch, 0, 1)
        self.optBox.setHorizontalSpacing(12)
        self.optBox.setColumnStretch(2, 1)

        # Buttons
        self.btnOk = SHARED.theme.getStandardButton(nwStandardButton.OK, self)
        self.btnOk.clicked.connect(self.accept)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.reject)

        self.btnReset = SHARED.theme.getStandardButton(nwStandardButton.RESET, self)
        self.btnReset.clicked.connect(self._resetList)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnOk, QtRoleAccept)
        self.btnBox.addButton(self.btnCancel, QtRoleReject)
        self.btnBox.addButton(self.btnReset, QtRoleReset)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.setSpacing(0)
        self.outerBox.addWidget(self.headLabel)
        self.outerBox.addWidget(self.helpLabel)
        self.outerBox.addSpacing(8)
        self.outerBox.addWidget(self.listBox)
        self.outerBox.addSpacing(8)
        self.outerBox.addLayout(self.optBox)
        self.outerBox.addSpacing(12)
        self.outerBox.addWidget(self.btnBox)
        self.setLayout(self.outerBox)

        # Load Content
        self._loadContent(sHandle, itemList)

        logger.debug("Ready: GuiDocMerge")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiDocMerge")

    def data(self) -> dict:
        """Return the user's choices."""
        finalItems = []
        for i in range(self.listBox.count()):
            item = self.listBox.item(i)
            if item is not None and item.checkState() == Qt.CheckState.Checked:
                finalItems.append(item.data(self.D_HANDLE))

        self._data["moveToTrash"] = self.trashSwitch.isChecked()
        self._data["finalItems"] = finalItems

        return self._data

    @classmethod
    def getData(cls, parent: QWidget, handle: str, items: list[str]) -> tuple[dict, bool]:
        """Pop the dialog and return the result."""
        dialog = cls(parent, handle, items)
        dialog.exec()
        data = dialog.data()
        accepted = dialog.result() == QtAccepted
        dialog.softDelete()
        return data, accepted

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _resetList(self) -> None:
        """Reset the content of the list box to its original state."""
        logger.debug("Resetting list box content")
        if sHandle := self._data.get("sHandle"):
            itemList = self._data.get("origItems", [])
            self._loadContent(sHandle, itemList)

    ##
    #  Internal Functions
    ##

    def _loadContent(self, sHandle: str, itemList: list[str]) -> None:
        """Load content from a given list of items."""
        self._data = {}
        self._data["sHandle"] = sHandle
        self._data["origItems"] = itemList
        self.listBox.clear()
        for tHandle in itemList:
            if (nwItem := SHARED.project.tree[tHandle]) and nwItem.isFileType():
                item = QListWidgetItem()
                item.setIcon(nwItem.getMainIcon())
                item.setText(nwItem.itemName)
                item.setData(self.D_HANDLE, tHandle)
                item.setCheckState(Qt.CheckState.Checked)
                self.listBox.addItem(item)
