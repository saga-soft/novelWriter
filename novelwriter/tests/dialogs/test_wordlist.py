"""
novelWriter - Word List Tests
=============================

This file is a part of novelWriter
Copyright (C) 2021 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QFileDialog

from novelwriter import SHARED
from novelwriter.core.project import NWProject
from novelwriter.core.spellcheck import UserDictionary
from novelwriter.dialogs.wordlist import GuiWordList
from novelwriter.types import QtAccepted

from tests.helpers import buildTestProject, checkDialogFreedOnClose
from tests.mocked import causeOSError


@pytest.mark.gui
def testGuiWordList_Main(qtbot, monkeypatch, nwGUI, fncPath, projPath):
    """Test the word list editor."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    monkeypatch.setattr(GuiWordList, "exec", lambda *a: None)
    monkeypatch.setattr(GuiWordList, "result", lambda *a: QtAccepted)
    monkeypatch.setattr(GuiWordList, "accept", lambda *a: None)

    # Load the dialog
    nwGUI.mainMenu.aEditWordList.activate(QAction.ActionEvent.Trigger)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiWordList) is not None, timeout=1000)

    wList = SHARED.findTopLevelWidget(GuiWordList)
    assert isinstance(wList, GuiWordList)
    wList.show()

    # List should be blank
    assert wList.listBox.count() == 0

    # Add words
    userDict = UserDictionary(SHARED.project)
    userDict.add("word_a")
    userDict.add("word_c")
    userDict.add("word_g")
    userDict.add("word_f")
    userDict.add("word_b")
    userDict.save()

    wList._loadWordList()

    # Check that the content was loaded
    assert wList.listBox.item(0).text() == "word_a"  # type: ignore
    assert wList.listBox.item(1).text() == "word_b"  # type: ignore
    assert wList.listBox.item(2).text() == "word_c"  # type: ignore
    assert wList.listBox.item(3).text() == "word_f"  # type: ignore
    assert wList.listBox.item(4).text() == "word_g"  # type: ignore
    assert wList.listBox.count() == 5

    # Add a blank word, which is ignored
    wList.newEntry.setText("   ")
    wList._doAdd()
    assert wList.listBox.count() == 5

    # Add an existing word, which is ignored
    wList.newEntry.setText("word_c")
    wList._doAdd()
    assert wList.listBox.count() == 5

    # Add a new word
    wList.newEntry.setText("word_d")
    wList._doAdd()
    assert wList.listBox.count() == 6

    # Check that the content now
    assert wList.listBox.item(0).text() == "word_a"  # type: ignore
    assert wList.listBox.item(1).text() == "word_b"  # type: ignore
    assert wList.listBox.item(2).text() == "word_c"  # type: ignore
    assert wList.listBox.item(3).text() == "word_d"  # type: ignore
    assert wList.listBox.item(4).text() == "word_f"  # type: ignore
    assert wList.listBox.item(5).text() == "word_g"  # type: ignore

    # Delete a word
    wList.newEntry.setText("delete_me")
    wList._doAdd()
    assert wList.listBox.item(0).text() == "delete_me"  # type: ignore

    delItem = wList.listBox.findItems("delete_me", Qt.MatchFlag.MatchExactly)[0]
    assert delItem.text() == "delete_me"
    delItem.setSelected(True)
    wList._doDelete()
    assert wList.listBox.findItems("delete_me", Qt.MatchFlag.MatchExactly) == []
    assert wList.listBox.item(0).text() == "word_a"  # type: ignore

    # Import/Export
    # =============
    expFile = fncPath / "wordlist_export.txt"
    impFile = fncPath / "wordlist_import.txt"
    wList.show()

    # Export File, Cancelled
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: ("", ""))
        wList.exportButton.click()
        assert not expFile.exists()

    # Export File, OS Error
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(expFile), ""))
        mp.setattr("builtins.open", causeOSError)
        wList.exportButton.click()
        assert not expFile.exists()

    # Export File, OK
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getSaveFileName", lambda *a, **k: (str(expFile), ""))
        wList.exportButton.click()
        assert expFile.exists()
        assert expFile.read_text() == "word_a\nword_b\nword_c\nword_d\nword_f\nword_g"

    # Write File
    impFile.write_text("word_d\nword_e\nword_f\tword_g word_h word_i\n\n\n")

    # Import File, Cancelled
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))
        wList.importButton.click()
        assert wList.listBox.count() == 6

    # Import File, OS Error
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(impFile), ""))
        mp.setattr("builtins.open", causeOSError)
        wList.importButton.click()
        assert wList.listBox.count() == 6

    # Import File, OK
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(impFile), ""))
        wList.importButton.click()
        assert wList.listBox.count() == 9

    # Save and Check List
    wList._doSave()
    userDict.load()
    assert len(list(userDict)) == 9
    assert "word_a" in userDict
    assert "word_b" in userDict
    assert "word_c" in userDict
    assert "word_d" in userDict
    assert "word_e" in userDict
    assert "word_f" in userDict
    assert "word_g" in userDict
    assert "word_h" in userDict
    assert "word_i" in userDict

    # qtbot.stop()


@pytest.mark.gui
def testGuiWordList_MemoryLeakRegression(qtbot, nwGUI, projPath):
    """Test that the dialog is freed when it is closed."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    checkDialogFreedOnClose(qtbot, lambda: GuiWordList(nwGUI))
