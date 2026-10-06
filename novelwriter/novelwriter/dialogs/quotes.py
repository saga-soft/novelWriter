"""
novelWriter - GUI Quotes Dialog
===============================

This file is a part of novelWriter
Copyright (C) 2021 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import QSize, pyqtSlot
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import (
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.constants import nwQuotes, trConst
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.modified import NDialog
from novelwriter.types import QtAccepted, QtAlignCenter, QtAlignTop, QtRoleAccept, QtRoleReject, QtUserRole

logger = logging.getLogger(__name__)


class GuiQuoteSelect(NDialog):
    """GUI: Quote Selector Dialog."""

    _selected = ""

    D_KEY = QtUserRole

    def __init__(self, parent: QWidget, current: str = '"') -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiQuoteSelect")
        self.setObjectName("GuiQuoteSelect")
        self.setWindowTitle(self.tr("Select Quote Style"))

        self.outerBox = QVBoxLayout()
        self.innerBox = QHBoxLayout()
        self.labelBox = QVBoxLayout()

        self._selected = current

        lblFont = self.font()
        lblFont.setPointSizeF(4 * lblFont.pointSizeF())
        metrics = QFontMetrics(self.font())

        # Preview Label
        self.previewLabel = QLabel(current, self)
        self.previewLabel.setFont(lblFont)
        self.previewLabel.setFixedSize(QSize(4 * metrics.maxWidth(), 5 * metrics.height()))
        self.previewLabel.setAlignment(QtAlignCenter)
        self.previewLabel.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Plain)

        # Quote Symbols
        self.listBox = QListWidget(self)
        self.listBox.itemSelectionChanged.connect(self._selectedSymbol)

        minSize = 100
        for sKey, sLabel in nwQuotes.SYMBOLS.items():
            text = f"[ {sKey} ] {trConst(sLabel)}"
            minSize = max(minSize, metrics.boundingRect(text).width())
            qtItem = QListWidgetItem(text)
            qtItem.setData(self.D_KEY, sKey)
            self.listBox.addItem(qtItem)
            if sKey == current:
                self.listBox.setCurrentItem(qtItem)

        self.listBox.setMinimumWidth(minSize + 40)
        self.listBox.setMinimumHeight(150)

        # Buttons
        self.btnOk = SHARED.theme.getStandardButton(nwStandardButton.OK, self)
        self.btnOk.clicked.connect(self.accept)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.reject)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnOk, QtRoleAccept)
        self.btnBox.addButton(self.btnCancel, QtRoleReject)

        # Assemble
        self.labelBox.addWidget(self.previewLabel, 0, QtAlignTop)
        self.labelBox.addStretch(1)

        self.innerBox.addLayout(self.labelBox)
        self.innerBox.addWidget(self.listBox)

        self.outerBox.addLayout(self.innerBox)
        self.outerBox.addWidget(self.btnBox)

        self.setLayout(self.outerBox)

        logger.debug("Ready: GuiQuoteSelect")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiQuoteSelect")

    @property
    def selectedQuote(self) -> str:
        """Return the selected quote symbol."""
        return self._selected

    @classmethod
    def getQuote(cls, parent: QWidget, current: str = "") -> tuple[str, bool]:
        """Pop the dialog and return the result."""
        dialog = cls(parent, current=current)
        dialog.exec()
        quote = dialog._selected
        accepted = dialog.result() == QtAccepted
        dialog.softDelete()
        return quote, accepted

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _selectedSymbol(self) -> None:
        """Update the preview label and the selected quote style."""
        if items := self.listBox.selectedItems():
            quote = items[0].data(self.D_KEY)
            self.previewLabel.setText(quote)
            self._selected = quote
