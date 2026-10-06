"""
novelWriter - Progress Bar Tests
================================

This file is a part of novelWriter
Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors

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

from time import sleep

import pytest

from PyQt6.QtGui import QColor

from novelwriter.extensions.progressbars import NColorRangeProgress, NProgressCircle, NProgressSimple

from tests.helpers import SimpleDialog


@pytest.mark.gui
def testNProgressCircle_Main(qtbot):
    """Test the NProgressCircle class."""
    dialog = SimpleDialog()
    progress = NProgressCircle(dialog, 200, 16)

    with qtbot.waitExposed(dialog):
        # This ensures the paint event is executed
        dialog.show()

    dialog.resize(200, 200)
    progress.setColors(
        QColor(255, 255, 255),
        QColor(255, 192, 192),
        QColor(255, 0, 0),
        QColor(0, 0, 0),
    )

    progress.setMaximum(100)
    for i in range(1, 101):
        progress.setValue(i)
        sleep(0.0025)
        assert progress.value() == i

    progress.setCentreText("Done!")
    assert progress._text == "Done!"

    # Track and text colours are optional
    progress.setColors(back=QColor(255, 255, 255), bar=QColor(255, 0, 0))

    # qtbot.stop()


@pytest.mark.gui
def testNProgressSimple_Main(qtbot):
    """Test the NProgressSimple class."""
    dialog = SimpleDialog()
    progress = NProgressSimple(dialog)

    with qtbot.waitExposed(dialog):
        # This ensures the paint event is executed
        dialog.show()

    progress.setMaximum(100)
    for i in range(1, 101):
        progress.setValue(i)
        sleep(0.0025)
        assert progress.value() == i

    # qtbot.stop()


@pytest.mark.gui
def testNColorRangeProgress_Main(qtbot, mockGUI):
    """Test the NColorRangeProgress class."""
    dialog = SimpleDialog()
    progress = NColorRangeProgress(dialog, 200, 20, 2)

    with qtbot.waitExposed(dialog):
        # This ensures the paint event is executed
        dialog.show()

    progress.setMaximum(100)
    progress.setBarRangeColors(start="#ff0000", end="#00ff00", mid="#ffff00")
    for i in range(0, 101, 5):
        progress.setValue(i)
        sleep(0.0025)
        assert progress.value() == i

    # A non-colour value is ignored
    before = progress._pRange
    progress.setBarColor(None)  # type: ignore
    assert progress._pRange is before

    # A fixed, single colour range
    progress.setBarColor("#0000ff")
    progress.setValue(50)
    sleep(0.0025)

    # Custom centre text
    progress.setCentreText("Done!")
    assert progress._text == "Done!"
    sleep(0.0025)

    # A theme refresh re-applies the current colour range settings
    progress.refreshTheme()

    # qtbot.stop()
