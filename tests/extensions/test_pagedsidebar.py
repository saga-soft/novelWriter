"""
novelWriter - PagedSideBar Extension Tests
==========================================

This file is a part of novelWriter.

Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors.

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

import pytest

from PyQt6.QtCore import Qt
from pytestqt.qtbot import QtBot

from novelwriter.extensions.pagedsidebar import NPagedSideBar

from tests.helpers import SimpleDialog
from tests.mocked import MockGuiMain


@pytest.mark.gui
def testNPagedSideBar_ButtonDirection(qtbot: QtBot, mockGUI: MockGuiMain):
    """Test that the button arrow is mirrored in RTL layouts."""
    dialog = SimpleDialog()
    sideBar = NPagedSideBar(dialog)
    sideBar.addButton("", 1)
    dialog.addWidget(sideBar)
    qtbot.addWidget(dialog)
    dialog.show()

    button = sideBar.button(1)
    button.setChecked(True)

    def arrowSpan() -> tuple[int, int]:
        image = button.grab().toImage()
        color = button.palette().highlightedText().color()
        row = image.height() // 2
        xs = [x for x in range(image.width()) if image.pixelColor(x, row) == color]
        return min(xs), max(xs)

    width = button.width()
    aH = button._aH

    # LTR places the arrow at the right edge
    aL, aR = arrowSpan()
    assert aL >= width - aH - 13
    assert aR <= width - 12

    # RTL places the arrow at the left edge
    button.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    aL, aR = arrowSpan()
    assert aL >= 12
    assert aR <= aH + 12
