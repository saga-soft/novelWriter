"""
novelWriter - Quotes Dialog Tests
=================================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import QItemSelectionModel
from PyQt6.QtWidgets import QListWidgetItem

from novelwriter.dialogs.quotes import GuiQuoteSelect
from novelwriter.types import QtAccepted, QtRejected


@pytest.mark.gui
def testGuiQuoteSelect_Main(qtbot, monkeypatch, nwGUI):
    """Test the quote symbols dialog."""
    monkeypatch.setattr(GuiQuoteSelect, "exec", lambda *a: None)

    nwQuot = GuiQuoteSelect(nwGUI)
    nwQuot.show()

    lastItem = ""
    for i in range(nwQuot.listBox.count()):
        anItem = nwQuot.listBox.item(i)
        assert isinstance(anItem, QListWidgetItem)
        nwQuot.listBox.clearSelection()
        nwQuot.listBox.setCurrentItem(anItem, QItemSelectionModel.SelectionFlag.Select)
        lastItem = anItem.text()[2]
        assert nwQuot.previewLabel.text() == lastItem

    nwQuot.accept()
    assert nwQuot.result() == QtAccepted
    assert nwQuot.selectedQuote == lastItem
    nwQuot.close()

    # Test Class Method
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "result", lambda *a: QtAccepted)
        assert GuiQuoteSelect.getQuote(nwGUI, current="X") == ("X", True)

    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "result", lambda *a: QtRejected)
        assert GuiQuoteSelect.getQuote(nwGUI, current="X") == ("X", False)

    # qtbot.stop()
