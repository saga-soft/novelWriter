"""
novelWriter - GUI About Dialog
==============================

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

from typing import TYPE_CHECKING

from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QDialogButtonBox, QFrame, QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatLink, readTextFile
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.configlayout import NColorLabel
from novelwriter.extensions.modified import NDialog
from novelwriter.extensions.versioninfo import VersionInfoWidget
from novelwriter.types import QtAlignRightTop, QtRoleDestruct

if TYPE_CHECKING:
    from PyQt6.QtGui import QCloseEvent

logger = logging.getLogger(__name__)


class GuiAbout(NDialog):
    """GUI: About novelWriter Dialog."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiAbout")
        self.setObjectName("GuiAbout")

        self.setWindowTitle(self.tr("About novelWriter"))
        self.resize(700, 500)

        baseCol = self.palette().window().color()
        basePalette = self.palette()
        basePalette.setColor(QPalette.ColorRole.Base, baseCol)

        # Logo and Banner
        self.nwImage = SHARED.theme.getDecoration("nw-text", h=36)

        self.nwLogo = QLabel(self)
        self.nwLogo.setPixmap(SHARED.theme.getPixmap("novelwriter", 128, 128))

        self.nwLabel = QLabel(self)
        self.nwLabel.setPixmap(self.nwImage)

        self.nwInfo = VersionInfoWidget(self)

        self.nwLicence = QLabel(
            self.tr("This application is licenced under {0}").format(
                formatLink("https://www.gnu.org/licenses/gpl-3.0.html", "GPL v3.0")
            ),
            self,
        )
        self.nwLicence.setOpenExternalLinks(True)

        # Credits
        self.lblCredits = NColorLabel(self.tr("Credits"), self, scale=1.6, bold=True)

        self.txtCredits = QTextBrowser(self)
        self.txtCredits.setOpenExternalLinks(True)
        self.txtCredits.setFrameStyle(QFrame.Shape.NoFrame)
        self.txtCredits.setPalette(basePalette)
        self.txtCredits.setViewportMargins(0, 8, 8, 0)

        # Buttons
        self.btnClose = SHARED.theme.getStandardButton(nwStandardButton.CLOSE, self)
        self.btnClose.clicked.connect(self.closeDialog)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnClose, QtRoleDestruct)

        # Assemble
        self.innerBox = QVBoxLayout()
        self.innerBox.addSpacing(16)
        self.innerBox.addWidget(self.nwLabel)
        self.innerBox.addWidget(self.nwInfo)
        self.innerBox.addSpacing(8)
        self.innerBox.addWidget(self.nwLicence)
        self.innerBox.addSpacing(8)
        self.innerBox.addWidget(self.lblCredits)
        self.innerBox.addWidget(self.txtCredits)
        self.innerBox.addSpacing(16)
        self.innerBox.addWidget(self.btnBox)

        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.nwLogo, 0, QtAlignRightTop)
        self.outerBox.addLayout(self.innerBox, 1)

        self.setLayout(self.outerBox)
        self.setSizeGripEnabled(True)

        self._fillCreditsPage()

        logger.debug("Ready: GuiAbout")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiAbout")

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the close event and perform cleanup."""
        event.accept()
        self.softDelete()

    ##
    #  Internal Functions
    ##

    def _fillCreditsPage(self) -> None:
        """Load the content for the Credits page."""
        if html := readTextFile(CONFIG.assetPath("text") / "credits_en.htm"):
            self.txtCredits.setHtml(html)
        else:
            self.txtCredits.setHtml("Error loading credits text ...")
