"""
novelWriter - Splash Screen
===========================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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
from time import sleep

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QPainter, QPixmap
from PyQt6.QtWidgets import QSplashScreen

logger = logging.getLogger(__name__)

SPLASH_IMG = Path(__file__).parent / "assets" / "images" / "splash.png"


class NSplashScreen(QSplashScreen):
    """GUI: App Launch Splash Screen.

    A small splash screen that is shown as novelWriter starts up. Its
    primary purpose is to provide user feedback that the app is being
    initiated when there are delays in the process while Qt waits for
    responses from the OS, or has to load particularly large data sets
    like when the system has a lot of fonts installed.
    """

    __slots__ = ("_color", "_rect", "_text")

    def __init__(self) -> None:
        super().__init__(pixmap=QPixmap(str(SPLASH_IMG)), flags=Qt.WindowType.WindowStaysOnTopHint)

        logger.debug("Create: NSplashScreen")

        font = self.font()
        font.setPointSizeF(12.0)
        self.setFont(font)
        self._color = QColor(26, 52, 78)
        self._rect = QRect(144, 110, 440, 30)
        self._text = ""

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: NSplashScreen")

    def drawContents(self, painter: QPainter) -> None:
        """Draw the text message."""
        painter.setPen(self._color)
        painter.drawText(self._rect, Qt.AlignmentFlag.AlignLeft, self._text)

    def showStatus(self, message: str) -> None:
        """Update the status message."""
        self._text = message
        self.showMessage(message)
        if message:
            logger.info("[Splash] %s", message)
        sleep(0.025)
