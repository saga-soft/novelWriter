"""
novelWriter - GUI Story Outline
===============================

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

from PyQt6.QtWidgets import QWidget

from novelwriter.extensions.expandpanel import NExpandablePanel

if TYPE_CHECKING:
    from novelwriter.story.storyview import GuiStoryView


class GuiStoryOutlineControls(NExpandablePanel):
    """GUI: Project Story Outline Controls."""

    def __init__(self, parent: GuiStoryView) -> None:
        super().__init__(parent)
        self._contentWidget: GuiStoryOutline | None = None

    def setContentWidget(self, widget: GuiStoryOutline) -> None:
        """Set the content widget for the outline controls."""
        self._contentWidget = widget


class GuiStoryOutline(QWidget):
    """GUI: Project Story Outline."""

    def __init__(self, parent: GuiStoryView) -> None:
        super().__init__(parent)
