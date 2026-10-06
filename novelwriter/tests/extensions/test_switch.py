"""
novelWriter - Switch Tests
==========================

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

import pytest

from PyQt6.QtCore import QEvent, QPointF
from PyQt6.QtGui import QEnterEvent, QMouseEvent

from novelwriter.extensions.switch import NSwitch
from novelwriter.types import QtModNone, QtMouseLeft

from tests.helpers import SimpleDialog


@pytest.mark.gui
def testNSwitch_Main(qtbot):
    """Test the NSwitch class. This is mostly a check that all the calls
    work as the result is visual.
    """
    dialog = SimpleDialog()
    switch = NSwitch(dialog, 40)

    with qtbot.waitExposed(dialog):
        # This ensures the paint event is executed
        dialog.show()

    dialog.resize(200, 100)

    switch.setEnabled(False)
    switch.setChecked(False)
    switch.repaint()
    qtbot.wait(20)

    switch.setChecked(True)
    switch.repaint()
    qtbot.wait(20)

    switch.setEnabled(True)
    switch.setChecked(False)
    switch.repaint()
    qtbot.wait(20)

    switch.setChecked(True)
    switch.repaint()
    qtbot.wait(20)

    button = QtMouseLeft
    modifier = QtModNone
    event = QMouseEvent(QEvent.Type.MouseButtonRelease, QPointF(), button, button, modifier)
    switch.mouseReleaseEvent(event)

    event = QEnterEvent(QPointF(), QPointF(), QPointF())
    switch.enterEvent(event)

    # qtbot.stop()
