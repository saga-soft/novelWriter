"""
novelWriter - Test Suite Mocked Classes
=======================================

This file is a part of novelWriter.

Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors.

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

from typing import Any, NoReturn
from unittest.mock import MagicMock

from PyQt6.QtCore import QSize, Qt, QTranslator
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import QWidget

from novelwriter.extensions.modified import NPushButton


class MockGuiMain(QWidget):
    """Mock main GUI."""

    def __init__(self):
        super().__init__()
        self.mainStatus = MagicMock()
        self.docEditor = MagicMock()
        self.docViewer = MagicMock()
        self.mainProgress = MagicMock()
        self.projPath = ""

    def postLaunchTasks(self, cmdOpen: str | None) -> None:
        """Skip the post-launch tasks."""
        return

    def setStatus(self, message: str) -> None:
        """Ignore the status message."""
        return

    def openProject(self, projPath: str) -> None:
        """Record the project path."""
        self.projPath = projPath

    def rebuildIndex(self):
        """Skip rebuilding the index."""
        return

    def closeMain(self):
        """Return a marker string."""
        return "closeMain"

    def close(self):
        """Return a marker string."""
        return "close"


class MockTheme:
    """Mock GUI theme."""

    def __init__(self):
        self.baseIconHeight = 20
        self.fontPixelSize = 20
        self.guiFont = QFont()
        self.guiFontB = QFont()
        self.guiFontBU = QFont()

    def initThemes(self) -> None:
        """Skip initialising the themes."""
        return

    def getPixmap(self, *a: Any) -> QPixmap:
        """Return an empty pixmap."""
        return QPixmap()

    def getHeaderDecoration(self, *a: Any) -> QPixmap:
        """Return an empty pixmap."""
        return QPixmap()

    def getStandardButton(self, *a: Any) -> NPushButton:
        """Return a minimal push button."""
        return NPushButton(None, "", QSize(1, 1))  # type: ignore

    def getIcon(self, *a: Any) -> QIcon:
        """Return an empty icon."""
        return QIcon()

    def getItemIcon(self, *a: Any, **k: Any) -> QIcon:
        """Return an empty icon."""
        return QIcon()


class MockApp:
    """Mock application."""

    def __init__(self):
        self._direction = Qt.LayoutDirection.LeftToRight

    def installTranslator(self, language: QTranslator) -> None:
        """Ignore the translator."""
        return

    def setLayoutDirection(self, direction: Qt.LayoutDirection) -> None:
        """Store the layout direction."""
        self._direction = direction

    def layoutDirection(self) -> Qt.LayoutDirection:
        """Return the stored layout direction."""
        return self._direction


# Error Functions
# ===============
# Mock functions that will raise errors instead.


def causeOSError(*args: Any, **kwargs: Any) -> NoReturn:
    """Raise an OSError."""
    raise OSError("Mock OSError")


def causeException(*args: Any, **kwargs: Any) -> NoReturn:
    """Raise an Exception."""
    raise Exception("Mock Exception")
