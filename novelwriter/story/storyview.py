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

from novelwriter import CONFIG, SHARED
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

        self.showContent(self.storyPanel.outlineContent)

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        self.storyPanel.updateTheme()

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        options = SHARED.project.options
        outline = self.storyPanel.outlineContent
        outline.refresh(SHARED.project.data.getLastHandle("story"))
        outline.restoreColumnWidths(options.getList("GuiStoryOutline", "colWidths", []))

    def closeProjectTasks(self) -> None:
        """Run closing project tasks."""
        options = SHARED.project.options
        outline = self.storyPanel.outlineContent
        options.setValue("GuiStoryOutline", "colWidths", outline.saveColumnWidths())
        outline.clear()

    def showContent(self, widget: QWidget) -> None:
        """Add a widget to the content stack, if needed, and show it.

        This is the switchboard a foldable panel's "generate" action
        will call to lazily add and activate its content widget.
        """
        if self.contentStack.indexOf(widget) == -1:
            self.contentStack.addWidget(widget)
        self.contentStack.setCurrentWidget(widget)

    ##
    #  Private Slots
    ##

    @pyqtSlot(int, int)
    def _saveSplitterSizes(self, pos: int, index: int) -> None:
        """Save the splitter sizes when moved by the user."""
        CONFIG.storyPanePos = self.splitMain.sizes()
