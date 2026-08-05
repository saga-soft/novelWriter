"""
novelWriter - GUI Side Bar Tests
================================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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

from novelwriter import CONFIG
from novelwriter.constants import nwLabels
from novelwriter.enum import nwTheme, nwView


@pytest.mark.gui
def testGuiSideBar_ViewChange(qtbot, nwGUI):
    """Test the view change buttons on the side bar."""
    sidebar = nwGUI.sideBar
    buttons = [
        (sidebar.tbProject, nwView.PROJECT),
        (sidebar.tbNovel, nwView.NOVEL),
        (sidebar.tbSearch, nwView.SEARCH),
        (sidebar.tbStory, nwView.STORY),
    ]
    for button, view in buttons:
        with qtbot.waitSignal(sidebar.requestViewChange, timeout=1000) as signal:
            button.click()
        assert signal.args == [view]


@pytest.mark.gui
def testGuiSideBar_CycleColourTheme(monkeypatch, nwGUI):
    """Test theme cycle feature on the side bar."""
    CONFIG.themeMode = nwTheme.AUTO
    sidebar = nwGUI.sideBar
    monkeypatch.setattr(sidebar.mainGui, "checkThemeUpdate", lambda *a: None)

    # Run 3 Cycles
    for _ in range(3):
        # Cycle Light
        sidebar._cycleColorTheme()
        assert CONFIG.themeMode == nwTheme.LIGHT
        assert sidebar.tbTheme.toolTip() == nwLabels.THEME_MODE_LABEL[nwTheme.LIGHT]

        # Cycle Dark
        sidebar._cycleColorTheme()
        assert CONFIG.themeMode == nwTheme.DARK
        assert sidebar.tbTheme.toolTip() == nwLabels.THEME_MODE_LABEL[nwTheme.DARK]

        # Cycle Auto
        sidebar._cycleColorTheme()
        assert CONFIG.themeMode == nwTheme.AUTO
        assert sidebar.tbTheme.toolTip() == nwLabels.THEME_MODE_LABEL[nwTheme.AUTO]
