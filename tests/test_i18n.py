"""
novelWriter - GUI i18n Tests
============================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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

import sys

import pytest

from PyQt6.QtWidgets import QApplication, QDialog

from novelwriter import CONFIG, SHARED
from novelwriter.core.project import NWProject
from novelwriter.dialogs.about import GuiAbout
from novelwriter.dialogs.preferences import GuiPreferences
from novelwriter.dialogs.projectsettings import GuiProjectSettings
from novelwriter.dialogs.wordlist import GuiWordList
from novelwriter.manuscript.manuscript import GuiManuscript
from novelwriter.tools.dictionaries import GuiDictionaries
from novelwriter.tools.welcome import GuiWelcome
from novelwriter.tools.writingstats import GuiWritingStats

from tests.helpers import buildTestProject

LANG_DATA = CONFIG.listLanguages(CONFIG.LANG_NW)


@pytest.mark.gui
@pytest.mark.skipif(sys.platform != "linux", reason="Linux Only")
@pytest.mark.skipif(not LANG_DATA, reason="No i18n Data")
@pytest.mark.parametrize("language", [a for a, b in LANG_DATA])
def testGuiI18n_Localisation(qtbot, monkeypatch, language, nwGUI, projPath):
    """Test loading the gui with a specific language."""
    monkeypatch.setattr(QDialog, "exec", lambda *a: None)

    # Set the test language
    CONFIG.guiLocale = language
    CONFIG.initLocalisation(QApplication.instance())  # type: ignore

    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    nwGUI.show()

    def showDialog(func, dType) -> None:
        func()
        qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(dType) is not None, timeout=1000)
        dialog = SHARED.findTopLevelWidget(dType)
        assert isinstance(dialog, dType)
        assert dialog is not None
        dialog.deleteLater()

    showDialog(nwGUI.showWelcomeDialog, GuiWelcome)
    showDialog(nwGUI.showPreferencesDialog, GuiPreferences)
    showDialog(nwGUI.showProjectSettingsDialog, GuiProjectSettings)
    showDialog(nwGUI.showBuildManuscriptDialog, GuiManuscript)
    showDialog(nwGUI.showProjectWordListDialog, GuiWordList)
    showDialog(nwGUI.showWritingStatsDialog, GuiWritingStats)
    showDialog(nwGUI.showAboutNWDialog, GuiAbout)
    showDialog(nwGUI.showDictionariesDialog, GuiDictionaries)

    qtbot.wait(20)
    nwGUI.closeMain()
