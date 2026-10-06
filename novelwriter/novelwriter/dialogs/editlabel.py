"""
novelWriter - Edit Label Dialog
===============================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtWidgets import QDialogButtonBox, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout, QWidget

from novelwriter import SHARED
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.modified import NDialog
from novelwriter.types import QtAccepted, QtRoleAccept, QtRoleReject

logger = logging.getLogger(__name__)


class GuiEditLabel(NDialog):
    """GUI: Edit Item Label Dialog."""

    def __init__(self, parent: QWidget, text: str = "", info: str = "") -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiEditLabel")
        self.setObjectName("GuiEditLabel")
        self.setWindowTitle(self.tr("Item Label"))

        # Item Label
        self.edtValue = QLineEdit(self)
        self.edtValue.setMinimumWidth(220)
        self.edtValue.setMaxLength(200)
        self.edtValue.setText(text)
        self.edtValue.selectAll()

        self.lblValue = QLabel(self.tr("Label"), self)
        self.lblValue.setBuddy(self.lblValue)

        # Buttons
        self.btnOk = SHARED.theme.getStandardButton(nwStandardButton.OK, self)
        self.btnOk.clicked.connect(self.accept)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.reject)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnOk, QtRoleAccept)
        self.btnBox.addButton(self.btnCancel, QtRoleReject)

        # Assemble
        self.innerBox = QHBoxLayout()
        self.innerBox.addWidget(self.lblValue, 0)
        self.innerBox.addWidget(self.edtValue, 1)
        self.innerBox.setSpacing(12)

        self.outerBox = QVBoxLayout()
        self.outerBox.setSpacing(12)
        if info:
            self.outerBox.addWidget(QLabel(info), 0)
        self.outerBox.addLayout(self.innerBox, 1)
        self.outerBox.addWidget(self.btnBox, 0)

        self.setLayout(self.outerBox)

        logger.debug("Ready: GuiEditLabel")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiEditLabel")

    @property
    def itemLabel(self) -> str:
        return self.edtValue.text()

    @classmethod
    def getLabel(cls, parent: QWidget, text: str, info: str = "") -> tuple[str, bool]:
        """Pop the dialog and return the result."""
        dialog = cls(parent, text=text, info=info)
        dialog.exec()
        label = dialog.itemLabel
        accepted = dialog.result() == QtAccepted
        dialog.softDelete()
        return label, accepted
