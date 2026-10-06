"""
novelWriter - Dictionary Downloader Tests
=========================================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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

from pathlib import Path
from zipfile import ZipFile

import enchant
import pytest

from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFileDialog

from novelwriter import SHARED
from novelwriter.tools.dictionaries import GuiDictionaries

from tests.mocked import causeException, causeOSError


@pytest.mark.gui
def testGuiDictionaries_Main(qtbot, monkeypatch, nwGUI, fncPath):
    """Test the Dictionaries downloader tool."""
    # Must also create the enchant folder, see issue #1874
    enchPath = fncPath / "enchant"
    monkeypatch.setattr(enchant, "get_user_config_dir", lambda *a: str(enchPath))

    # Fail to open
    with monkeypatch.context() as mp:
        mp.setattr(enchant, "get_user_config_dir", lambda *a: causeException)
        nwGUI.showDictionariesDialog()
        assert SHARED.lastAlert[0] == "Could not initialise the dialog."

    # Open the tool
    nwGUI.showDictionariesDialog()
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiDictionaries) is not None, timeout=1000)

    nwDicts = SHARED.findTopLevelWidget(GuiDictionaries)
    assert isinstance(nwDicts, GuiDictionaries)
    assert nwDicts.isVisible()
    assert nwDicts.inPath.text() == str(enchPath)

    # Allow Open Dir
    SHARED._lastAlert = []
    with monkeypatch.context() as mp:
        mp.setattr(QDesktopServices, "openUrl", lambda *a: None)
        nwDicts._doOpenInstallLocation()
        assert SHARED.lastAlert == []

    # Fail Open Dir
    nwDicts.inPath.setText("/foo/bar")
    nwDicts._doOpenInstallLocation()
    assert SHARED.lastAlert[0] == "Path not found."
    nwDicts.inPath.setText(str(fncPath))

    # Create Mock Dicts
    foDict = fncPath / "freeoffice.sox"
    with ZipFile(foDict, mode="w") as zipObj:
        zipObj.writestr("en_GB.aff", "foobar")
        zipObj.writestr("en_GB.dic", "foobar")
        zipObj.writestr("README.txt", "foobar")

    loDict = fncPath / "libreoffice.oxt"
    with ZipFile(loDict, mode="w") as zipObj:
        zipObj.writestr("en_US/en_US.aff", "foobar")
        zipObj.writestr("en_US/en_US.dic", "foobar")
        zipObj.writestr("README.txt", "foobar")

    emDict = fncPath / "empty.oxt"
    with ZipFile(emDict, mode="w") as zipObj:
        zipObj.writestr("README.txt", "foobar")

    noFile = fncPath / "foobar.oxt"
    noDict = fncPath / "foobar.sox"
    noDict.write_bytes(b"foobar")

    assert nwDicts.infoBox.toPlainText().splitlines()[-1] == ("Additional dictionaries found: 0")

    # Import Free Office Dictionary
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(foDict), ""))
        nwDicts._doBrowseHunspell()
        assert nwDicts.huInput.text() == str(foDict)
        nwDicts._doImportHunspell()
        assert (enchPath / "hunspell").is_dir()
        assert (enchPath / "hunspell" / "en_GB.aff").is_file()
        assert (enchPath / "hunspell" / "en_GB.dic").is_file()
        assert nwDicts.infoBox.blockCount() == 3

    # Import Libre Office Dictionary
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(loDict), ""))
        nwDicts._doBrowseHunspell()
        assert nwDicts.huInput.text() == str(loDict)
        nwDicts._doImportHunspell()
        assert (enchPath / "hunspell").is_dir()
        assert (enchPath / "hunspell" / "en_US.aff").is_file()
        assert (enchPath / "hunspell" / "en_US.dic").is_file()
        assert nwDicts.infoBox.blockCount() == 5

    # Handle Unreadable File
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(noDict), ""))
        nwDicts._doBrowseHunspell()
        assert nwDicts.huInput.text() == str(noDict)
        nwDicts._doImportHunspell()
        assert nwDicts.infoBox.blockCount() == 7

    # Handle File w/No Dicts
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(emDict), ""))
        nwDicts._doBrowseHunspell()
        assert nwDicts.huInput.text() == str(emDict)
        nwDicts._doImportHunspell()
        assert nwDicts.infoBox.blockCount() == 8
        assert nwDicts.infoBox.toPlainText().splitlines()[-1] == ("Could not process dictionary file")

    # Handle Non-Existing File
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(noFile), ""))
        nwDicts._doBrowseHunspell()
        nwDicts._doImportHunspell()
        assert nwDicts.infoBox.blockCount() == 9
        assert nwDicts.infoBox.toPlainText().splitlines()[-1] == ("Could not process dictionary file")

    # Re-init and fail to scan for dictionaries
    with monkeypatch.context() as mp:
        mp.setattr(Path, "iterdir", causeOSError)
        nwDicts.initDialog()

    # Re-init
    nwDicts.initDialog()
    assert nwDicts.infoBox.blockCount() == 10
    assert nwDicts.infoBox.toPlainText().splitlines()[-1] == ("Additional dictionaries found: 2")

    # Browsing without selecting a file leaves the input unchanged
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
        huInputBefore = nwDicts.huInput.text()
        nwDicts._doBrowseHunspell()
        assert nwDicts.huInput.text() == huInputBefore

    # Importing without an install path does nothing
    blockCount = nwDicts.infoBox.blockCount()
    installPath = nwDicts._installPath
    nwDicts._installPath = None
    nwDicts._doImportHunspell()
    assert nwDicts.infoBox.blockCount() == blockCount
    nwDicts._installPath = installPath

    nwDicts.close()
    nwDicts.softDelete()

    # qtbot.stop()
