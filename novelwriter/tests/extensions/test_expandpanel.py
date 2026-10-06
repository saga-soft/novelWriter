"""
novelWriter - ExpandPanel Extension Tests
=========================================

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

from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QWIDGETSIZE_MAX, QLabel, QVBoxLayout

from novelwriter.extensions.expandpanel import NExpandablePanel, NExpandablePanelGroup
from novelwriter.extensions.modified import NSplitterHandle
from novelwriter.types import QtMouseLeft

from tests.helpers import SimpleDialog


@pytest.mark.gui
def testNExpandablePanel_Main(qtbot, mockGUI):
    """Test the NExpandablePanel class."""
    dialog = SimpleDialog()
    panel = NExpandablePanel(dialog)
    dialog.addWidget(panel)
    dialog.show()
    qtbot.addWidget(dialog)

    changes = []
    panel.expandedStateChanged.connect(changes.append)

    # Default state is expanded, with a default title
    assert panel.isExpanded() is True
    assert panel._ep_widget.isVisible() is True
    assert panel._ep_toggle.isChecked() is True
    assert panel._ep_label.text() == "Unnamed"

    # Set a title
    panel.setTitle("My Panel")
    assert panel._ep_label.text() == "My Panel"

    # Set the content layout
    content = QVBoxLayout()
    content.addWidget(QLabel("Some content", panel))
    panel.setContentLayout(content)
    assert panel._ep_widget.layout() is content

    # Set the header background role
    panel.setHeaderBackgroundRole(QPalette.ColorRole.Highlight)
    assert panel._ep_headerBox.backgroundRole() == QPalette.ColorRole.Highlight
    assert panel._ep_headerBox.autoFillBackground() is True

    # Click the toggle button to collapse the panel, which locks its
    # height to that of the header
    qtbot.mouseClick(panel._ep_toggle, QtMouseLeft)
    assert panel.isExpanded() is False
    assert panel._ep_widget.isVisible() is False
    assert panel._ep_toggle.isChecked() is False
    assert panel.maximumHeight() == panel.minimumSizeHint().height()
    assert changes == [False]

    # Click the title label to expand the panel again, which lifts the
    # height restriction
    qtbot.mouseClick(panel._ep_label, QtMouseLeft)
    assert panel.isExpanded() is True
    assert panel._ep_widget.isVisible() is True
    assert panel._ep_toggle.isChecked() is True
    assert panel.maximumHeight() == QWIDGETSIZE_MAX
    assert changes == [False, True]

    # Set the expanded state directly, which must also update the toggle
    # button so its icon stays in sync with the actual state
    panel.setExpanded(False)
    assert panel.isExpanded() is False
    assert panel._ep_widget.isVisible() is False
    assert panel._ep_toggle.isChecked() is False
    assert changes == [False, True, False]

    panel.setExpanded(True)
    assert panel.isExpanded() is True
    assert panel._ep_widget.isVisible() is True
    assert panel._ep_toggle.isChecked() is True
    assert changes == [False, True, False, True]

    # Setting the same state again should not change anything, or emit
    panel.setExpanded(True)
    assert panel.isExpanded() is True
    assert panel._ep_widget.isVisible() is True
    assert changes == [False, True, False, True]

    # The internal slot itself also guards against a redundant state,
    # regardless of how it is invoked
    panel._toggleExpanded(True)
    assert panel.isExpanded() is True
    assert changes == [False, True, False, True]

    # Update the theme
    panel.updateTheme()


@pytest.mark.gui
def testNExpandablePanelGroup_Main(qtbot, mockGUI):
    """Test the NExpandablePanelGroup class."""
    dialog = SimpleDialog()
    group = NExpandablePanelGroup(dialog)
    dialog.addWidget(group)

    panel = NExpandablePanel()
    panel.setTitle("Panel")
    content = QVBoxLayout()
    content.addWidget(QLabel("Some content that needs space", panel))
    panel.setContentLayout(content)

    other = QLabel("Other pane")

    group.addWidget(panel)
    group.addWidget(other)
    dialog.resize(400, 600)
    dialog.show()
    qtbot.addWidget(dialog)
    qtbot.wait(10)

    # Adding a panel connects its state change, tracks its size, and
    # applies the group's header background role
    assert panel in group._expandedSizes
    assert panel._ep_headerBox.backgroundRole() == QPalette.ColorRole.AlternateBase
    assert panel._ep_headerBox.autoFillBackground() is True

    # Both panes start expanded, so the handle between them is resizable
    handle = group.handle(1)
    assert isinstance(handle, NSplitterHandle)
    assert handle._resizable is True

    # A size of zero or less does not overwrite the remembered expanded
    # size, since it does not represent a meaningful size to restore to
    beforeSize = group._expandedSizes[panel]
    group.setPanelSizes([0, 200])
    assert group._expandedSizes[panel] == beforeSize

    # Setting sizes is remembered as the panel's expanded size. The actual
    # on-screen pixel sizes are not checked here, as QSplitter distributes
    # them proportionally to fit the available space, not verbatim.
    group.setPanelSizes([150, 200])
    assert group._expandedSizes[panel] == 150
    qtbot.wait(10)
    expandedHeight = group.sizes()[0]

    # Collapsing the panel locks it to its header height, remembers the
    # actual size it had, and disables the now-useless handle
    panel.setExpanded(False)
    qtbot.wait(10)
    collapsedHeight = panel.minimumSizeHint().height()
    assert group.sizes()[0] == collapsedHeight
    assert group.panelSizes()[0] == expandedHeight
    assert handle._resizable is False

    # Expanding it again grows the panel back out and re-enables the handle.
    # The exact pixel value may differ from what was remembered, since the
    # other pane may since have grown to fill the space that was freed up,
    # leaving less than requested for the splitter to redistribute back
    panel.setExpanded(True)
    qtbot.wait(10)
    assert group.sizes()[0] > collapsedHeight
    assert handle._resizable is True

    # Adding a panel that starts out collapsed keeps the handle disabled
    # and does not reserve space it cannot actually use
    collapsed = NExpandablePanel()
    collapsed.setTitle("Collapsed")
    collapsed.setExpanded(False)
    group.addWidget(collapsed)
    qtbot.wait(10)

    lastHandle = group.handle(2)
    assert isinstance(lastHandle, NSplitterHandle)
    assert lastHandle._resizable is False
    assert group.sizes()[2] == collapsed.minimumSizeHint().height()
