"""
novelWriter - SwitchBox Extension Tests
=======================================

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

import pytest

from novelwriter.extensions.switch import NSwitch
from novelwriter.extensions.switchbox import NSwitchBox

from tests.helpers import SimpleDialog, checkWidgetFreedOnRelease


@pytest.mark.gui
def testNSwitchBox_AddAndState(qtbot, mockGUIwithTheme):
    """Test adding labels, items and separators, and reading and
    writing the resulting switch state.
    """
    dialog = SimpleDialog()
    box = NSwitchBox(dialog, 20)
    dialog.addWidget(box)
    qtbot.addWidget(dialog)

    box.addLabel("Group")
    box.addItem("Alpha", "item:alpha", icon="filter", default=True)
    box.addItem("Beta", "item:beta", default=False)
    box.addSeparator()

    assert isinstance(box._entries["item:alpha"].switch, NSwitch)
    assert isinstance(box._entries["item:beta"].switch, NSwitch)
    assert box._entries["item:alpha"].label.text() == "Alpha"
    assert box._entries["item:alpha"].pixmap is not None
    assert box._entries["item:beta"].pixmap is None

    assert box.getSwitchState() == {"item:alpha": True, "item:beta": False}

    box.setSwitchState({"item:alpha": False, "item:beta": True, "item:missing": True})
    assert box.getSwitchState() == {"item:alpha": False, "item:beta": True}

    # Toggling a switch emits the identifier and the new state
    with qtbot.waitSignal(box.switchToggled, timeout=1000) as signal:
        box._entries["item:alpha"].switch.setChecked(True)
    assert signal.args == ["item:alpha", True]

    # Updating the theme refreshes the icon pixmaps of items that have one
    box.updateTheme()


@pytest.mark.gui
def testNSwitchBox_UpdateInPlace(qtbot, mockGUIwithTheme):
    """Test that re-adding an existing identifier updates the entry in
    place rather than appending a duplicate, and keeps the current
    switch state instead of resetting it to the new default.
    """
    dialog = SimpleDialog()
    box = NSwitchBox(dialog, 20)
    dialog.addWidget(box)
    qtbot.addWidget(dialog)

    box.addItem("Original Name", "item:root", icon="filter", default=True)
    box.addItem("Other", "item:other", default=False)
    assert len(box._entries) == 2
    originalSwitch = box._entries["item:root"].switch

    # The user has since toggled the switch off
    originalSwitch.setChecked(False)

    # Re-adding the same identifier must not create a new row or switch,
    # must update the label text, and must not reset the switch state
    # even though a new default is provided
    box.addItem("Renamed", "item:root", icon="filter", default=True)
    assert len(box._entries) == 2
    assert box._entries["item:root"].switch is originalSwitch
    assert box._entries["item:root"].label.text() == "Renamed"
    assert originalSwitch.isChecked() is False

    # The same applies to an item that has no icon, where the icon branch
    # of the in-place update must simply be skipped
    otherSwitch = box._entries["item:other"].switch
    box.addItem("Other Renamed", "item:other", default=True)
    assert box._entries["item:other"].switch is otherSwitch
    assert box._entries["item:other"].label.text() == "Other Renamed"
    assert otherSwitch.isChecked() is False
    assert box._entries["item:other"].pixmap is None


@pytest.mark.gui
def testNSwitchBox_RemoveItem(qtbot, mockGUIwithTheme):
    """Test removing items from the switch box, including items that
    were never added and items without an icon.
    """
    dialog = SimpleDialog()
    box = NSwitchBox(dialog, 20)
    dialog.addWidget(box)
    qtbot.addWidget(dialog)

    box.addItem("Alpha", "item:alpha", icon="filter", default=True)
    box.addItem("Beta", "item:beta", default=False)
    assert set(box._entries) == {"item:alpha", "item:beta"}

    # Removing an item drops it from the internal tracking dict
    box.removeItem("item:alpha")
    assert "item:alpha" not in box._entries
    assert box.getSwitchState() == {"item:beta": False}

    # Removing an item without an icon works the same way
    box.removeItem("item:beta")
    assert box.getSwitchState() == {}

    # Removing an identifier that was never added, or already removed,
    # is a no-op
    box.removeItem("item:alpha")
    box.removeItem("item:unknown")
    assert box.getSwitchState() == {}

    # The identifier can be reused afterwards, appending a fresh row
    box.addItem("Alpha Again", "item:alpha", icon="filter", default=True)
    assert box.getSwitchState() == {"item:alpha": True}


@pytest.mark.gui
def testNSwitchBox_Clear(qtbot, mockGUIwithTheme):
    """Test that clear() resets all internal tracking dicts, and that
    the widget remains usable afterwards.
    """
    dialog = SimpleDialog()
    box = NSwitchBox(dialog, 20)
    dialog.addWidget(box)
    qtbot.addWidget(dialog)

    box.addLabel("Group")
    box.addItem("Alpha", "item:alpha", icon="filter", default=True)
    assert box.getSwitchState() != {}

    box.clear()
    assert box._entries == {}
    assert box.getSwitchState() == {}

    box.addItem("Beta", "item:beta", default=True)
    assert box.getSwitchState() == {"item:beta": True}


@pytest.mark.gui
def testNSwitchBox_MemoryLeakRegression(qtbot, mockGUIwithTheme):
    """Test that the box is freed by reference count alone once
    released, even though its switches connect back to it. This guards
    against a self-pinning closure connected to a switch in the box's
    own widget subtree, which would otherwise keep the box alive until
    the cyclic garbage collector happens to run.
    """

    def build() -> NSwitchBox:
        box = NSwitchBox(None, 20)  # type: ignore
        box.addLabel("Group")
        box.addItem("Alpha", "item:alpha", icon="filter", default=True)
        box.addItem("Beta", "item:beta", default=False)
        box.removeItem("item:alpha")
        box.clear()
        box.addItem("Gamma", "item:gamma", icon="filter", default=True)
        return box

    checkWidgetFreedOnRelease(build)
