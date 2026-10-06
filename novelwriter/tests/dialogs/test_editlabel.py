"""
novelWriter - Edit Label Dialog Tests
=====================================

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

from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.types import QtAccepted, QtRejected


@pytest.mark.gui
def testGuiEditLabel_Main(qtbot, monkeypatch):
    """Test the label editor dialog."""
    monkeypatch.setattr(GuiEditLabel, "exec", lambda *a: None)

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLabel, "result", lambda *a: QtAccepted)
        newLabel, dlgOk = GuiEditLabel.getLabel(None, text="Stuff")  # type: ignore
        assert dlgOk is True
        assert newLabel == "Stuff"

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLabel, "result", lambda *a: QtRejected)
        newLabel, dlgOk = GuiEditLabel.getLabel(None, text="Stuff", info="Hi")  # type: ignore
        assert dlgOk is False
        assert newLabel == "Stuff"
