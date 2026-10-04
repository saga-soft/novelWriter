"""
novelWriter - Edit Link Dialog
==============================

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

import logging

from PyQt6.QtWidgets import QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout, QWidget

from novelwriter import SHARED
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.modified import NDialog
from novelwriter.types import QtAccepted, QtRoleAccept, QtRoleReject

logger = logging.getLogger(__name__)


class GuiEditLink(NDialog):
    """GUI: Edit Markdown Link Dialog."""

    def __init__(self, parent: QWidget, text: str = "", url: str = "") -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiEditLink")
        self.setObjectName("GuiEditLink")
        self.setWindowTitle(self.tr("Link"))

        self.edtText = QLineEdit(self)
        self.edtText.setMinimumWidth(220)
        self.edtText.setText(text)

        self.edtUrl = QLineEdit(self)
        self.edtUrl.setMinimumWidth(220)
        self.edtUrl.setText(url)

        (self.edtUrl if text else self.edtText).setFocus()

        self.formBox = QFormLayout()
        self.formBox.addRow(self.tr("Link Text"), self.edtText)
        self.formBox.addRow(self.tr("URL"), self.edtUrl)

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
        self.outerBox.setSpacing(12)
        self.outerBox.addLayout(self.formBox, 1)
        self.outerBox.addWidget(self.btnBox, 0)

        self.setLayout(self.outerBox)

        logger.debug("Ready: GuiEditLink")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiEditLink")

    @property
    def linkText(self) -> str:
        return self.edtText.text().strip()

    @property
    def linkUrl(self) -> str:
        return self.edtUrl.text().strip()

    @classmethod
    def getLink(cls, parent: QWidget, text: str = "", url: str = "") -> tuple[str, str, bool]:
        """Pop the dialog and return the result."""
        dialog = cls(parent, text=text, url=url)
        dialog.exec()
        linkText = dialog.linkText
        linkUrl = dialog.linkUrl
        accepted = dialog.result() == QtAccepted
        dialog.softDelete()
        return linkText, linkUrl, accepted
