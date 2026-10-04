"""
novelWriter - Edit Link Dialog Tests
====================================

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

from novelwriter.dialogs.editlink import GuiEditLink
from novelwriter.types import QtAccepted, QtRejected


@pytest.mark.gui
def testGuiEditLink_Main(qtbot, monkeypatch, mockGUI):
    """Test the link editor dialog."""
    monkeypatch.setattr(GuiEditLink, "exec", lambda *a: None)

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "result", lambda *a: QtAccepted)
        text, url, dlgOk = GuiEditLink.getLink(None, text="A Link", url="https://example.com")  # type: ignore
        assert dlgOk is True
        assert text == "A Link"
        assert url == "https://example.com"

    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "result", lambda *a: QtRejected)
        text, url, dlgOk = GuiEditLink.getLink(None, text="A Link", url="https://example.com")  # type: ignore
        assert dlgOk is False
        assert text == "A Link"
        assert url == "https://example.com"

    # Blank fields are stripped, and are the default when nothing is passed
    with monkeypatch.context() as mp:
        mp.setattr(GuiEditLink, "result", lambda *a: QtAccepted)
        text, url, dlgOk = GuiEditLink.getLink(None)  # type: ignore
        assert dlgOk is True
        assert text == ""
        assert url == ""
