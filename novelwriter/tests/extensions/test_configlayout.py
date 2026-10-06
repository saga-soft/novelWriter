"""
novelWriter - ConfigLayout Extension Tests
==========================================

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

from PyQt6.QtWidgets import QLabel

from novelwriter.extensions.configlayout import NScrollableForm

from tests.helpers import SimpleDialog


@pytest.mark.gui
def testNScrollableForm_Main(qtbot, mockGUI):
    """Test the NScrollableForm class."""
    dialog = SimpleDialog()
    form = NScrollableForm(dialog)
    dialog.addWidget(form)
    dialog.show()
    qtbot.addWidget(dialog)

    # Add a group label with no identifier
    form.addGroupLabel("Group One")
    assert form._sections == {}

    # Add a group label with an identifier
    form.addGroupLabel("Group Two", identifier=1)
    assert 1 in form._sections

    # Add a row with a plain widget, and one with a list containing
    # a widget, a spacing int, and an item that is neither (ignored)
    widgetA = QLabel("A", form)
    form.addRow("Row A", widgetA, helpText="Help A", unit="Stuff", editable="rowA")
    assert "Row A" in form.labels

    widgetB = QLabel("B", form)
    form.addRow("Row B", [widgetB, 8, "not-a-widget-or-int"])  # type: ignore
    assert "Row B" in form.labels

    form.finalise()

    # Set help text for a known and an unknown key
    form.setHelpText("rowA", "Updated Help")
    form.setUnitText("rowA", "Things")
    form.setHelpText("unknownKey", "Ignored")
    form.setUnitText("unknownKey", "Ignored")

    # Scroll to a known and an unknown section identifier
    form.scrollToSection(1)
    form.scrollToSection(9999)

    # Scroll to a known and an unknown label
    form.scrollToLabel("Row A")
    form.scrollToLabel("Unknown Label")
