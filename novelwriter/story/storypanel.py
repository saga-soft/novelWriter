"""
novelWriter - GUI Story Panel
=============================

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

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QVBoxLayout, QWidget

from novelwriter.extensions.expandpanel import NExpandablePanelGroup
from novelwriter.story.outline import GuiStoryOutline, GuiStoryOutlineControls

if TYPE_CHECKING:
    from novelwriter.story.storyview import GuiStoryView


class GuiStoryPanel(QWidget):
    """GUI: Project Story Panel."""

    def __init__(self, parent: GuiStoryView) -> None:
        super().__init__(parent)

        # Default View
        self.outlineContent = GuiStoryOutline(parent)
        self.outlineControls = GuiStoryOutlineControls(parent)
        self.outlineControls.setContentWidget(self.outlineContent)

        # Panel
        self.fillerWidget = QWidget(self)

        self.panels = NExpandablePanelGroup(self)
        self.panels.addWidget(self.outlineControls)
        self.panels.addWidget(self.fillerWidget)

        self.panels.setStretchFactor(0, 0)
        self.panels.setStretchFactor(1, 1)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.panels)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        self.outlineControls.updateTheme()
        self.outlineContent.updateTheme()
