"""
novelWriter - Test Suite Mocked Classes
=======================================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

from unittest.mock import MagicMock

from PyQt6.QtCore import QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QWidget

from novelwriter.extensions.modified import NPushButton


class MockGuiMain(QWidget):
    def __init__(self):
        super().__init__()
        self.mainStatus = MagicMock()
        self.docEditor = MagicMock()
        self.docViewer = MagicMock()
        self.mainProgress = MagicMock()
        self.projPath = ""

    def postLaunchTasks(self, cmdOpen):
        return

    def setStatus(self, message):
        return

    def openProject(self, projPath):
        self.projPath = projPath

    def rebuildIndex(self):
        return

    def closeMain(self):
        return "closeMain"

    def close(self):
        return "close"


class MockTheme:
    def __init__(self):
        self.baseIconHeight = 20
        self.fontPixelSize = 20
        self.guiFont = QFont()
        self.guiFontB = QFont()
        self.guiFontBU = QFont()

    def initThemes(self) -> None:
        return

    def getPixmap(self, *a) -> QPixmap:
        return QPixmap()

    def getHeaderDecoration(self, *a) -> QPixmap:
        return QPixmap()

    def getStandardButton(self, *a) -> NPushButton:
        return NPushButton(None, "", QSize(1, 1))  # type: ignore

    def getIcon(self, *a) -> QIcon:
        return QIcon()

    def getItemIcon(self, *a, **k) -> QIcon:
        return QIcon()


class MockApp:
    def __init__(self):
        return

    def installTranslator(self, language):
        return


# Error Functions
# ===============
# Mock functions that will raise errors instead.


def causeOSError(*args, **kwargs):
    """Raise an OSError."""
    raise OSError("Mock OSError")


def causeException(*args, **kwargs):
    """Raise an Exception."""
    raise Exception("Mock Exception")
