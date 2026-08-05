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

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QSplitter, QStackedWidget, QVBoxLayout, QWidget

from novelwriter import CONFIG
from novelwriter.story.storypanel import GuiStoryPanel


class GuiStoryView(QWidget):
    """GUI: Project Story View."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.storyPanel = GuiStoryPanel(self)
        self.contentStack = QStackedWidget(self)

        self.splitMain = QSplitter(Qt.Orientation.Horizontal)
        self.splitMain.setContentsMargins(0, 0, 0, 0)
        self.splitMain.addWidget(self.storyPanel)
        self.splitMain.addWidget(self.contentStack)
        self.splitMain.setOpaqueResize(False)
        self.splitMain.setHandleWidth(4)
        self.splitMain.setSizes([max(s, 100) for s in CONFIG.storyPanePos])
        self.splitMain.setCollapsible(0, False)
        self.splitMain.setCollapsible(1, False)
        self.splitMain.setStretchFactor(0, 0)
        self.splitMain.setStretchFactor(1, 1)
        self.splitMain.splitterMoved.connect(self._saveSplitterSizes)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.splitMain)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""

    def openProjectTasks(self) -> None:
        """Run open project tasks."""

    def closeProjectTasks(self) -> None:
        """Run closing project tasks."""

    ##
    #  Private Slots
    ##

    @pyqtSlot(int, int)
    def _saveSplitterSizes(self, pos: int, index: int) -> None:
        """Save the splitter sizes when moved by the user."""
        CONFIG.storyPanePos = self.splitMain.sizes()
