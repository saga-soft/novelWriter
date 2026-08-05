"""
novelWriter - GUI Story View
============================

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

from PyQt6.QtWidgets import QWidget


class GuiStoryView(QWidget):
    """GUI: Project Story View."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""

    def openProjectTasks(self) -> None:
        """Run open project tasks."""

    def closeProjectTasks(self) -> None:
        """Run closing project tasks."""
