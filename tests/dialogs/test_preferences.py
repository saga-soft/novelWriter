"""
novelWriter - Preferences Dialog Test
=====================================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QAction, QFont, QFontDatabase, QKeyEvent
from PyQt6.QtWidgets import QFileDialog

from novelwriter import CONFIG, SHARED
from novelwriter.config import DEF_GUI_DARK, DEF_GUI_LIGHT, DEF_TREECOL
from novelwriter.constants import nwUnicode
from novelwriter.core.spellcheck import SpellEnchant
from novelwriter.dialogs.preferences import GuiNeedsUpdate, GuiPreferences
from novelwriter.dialogs.quotes import GuiQuoteSelect
from novelwriter.extensions.modified import NFontDialog
from novelwriter.gui.theme import ThemeEntry
from novelwriter.types import QtKeyEscape, QtModNone

from tests.helpers import checkDialogFreedOnClose

KEY_DELAY = 1


@pytest.mark.gui
def testGuiPreferences_Main(qtbot, monkeypatch, nwGUI, tstPaths):
    """Test the preferences dialog loading."""
    monkeypatch.setattr(SpellEnchant, "listDictionaries", lambda *a: [("en", "English [en]")])
    monkeypatch.setattr(GuiPreferences, "exec", lambda *a: None)

    # Load GUI with standard values
    nwGUI.mainMenu.aPreferences.activate(QAction.ActionEvent.Trigger)
    qtbot.waitUntil(lambda: SHARED.findTopLevelWidget(GuiPreferences) is not None, timeout=1000)
    prefs = SHARED.findTopLevelWidget(GuiPreferences)
    assert isinstance(prefs, GuiPreferences)
    prefs.show()

    # Check Languages
    languages = [prefs.guiLocale.itemData(i) for i in range(prefs.guiLocale.count())]
    assert len(languages) > 0
    assert "en_GB" in languages

    # Check GUI Themes
    themes = [prefs.lightTheme.itemData(i) for i in range(prefs.lightTheme.count())]
    assert DEF_GUI_LIGHT in themes

    themes = [prefs.darkTheme.itemData(i) for i in range(prefs.darkTheme.count())]
    assert DEF_GUI_DARK in themes

    # Check Spell Checking
    spelling = [prefs.spellLanguage.itemData(i) for i in range(prefs.spellLanguage.count())]
    assert len(spelling) == 1
    assert spelling == ["en"]

    prefs.close()

    # Check Fallback Values
    CONFIG.hasEnchant = False
    prefs = GuiPreferences(nwGUI)
    prefs.show()

    # Check Spell Checking
    spelling = [prefs.spellLanguage.itemData(i) for i in range(prefs.spellLanguage.count())]
    assert len(spelling) == 1
    assert spelling == [""]

    prefs.close()

    # qtbot.stop()


@pytest.mark.gui
def testGuiPreferences_Actions(qtbot, monkeypatch, nwGUI):
    """Test the preferences dialog actions."""
    monkeypatch.setattr(SpellEnchant, "listDictionaries", lambda *a: [("en", "English [en]")])
    prefs = GuiPreferences(nwGUI)
    with qtbot.waitExposed(prefs):
        prefs.show()

    # Check Navigation
    vBar = prefs.mainForm.verticalScrollBar()
    assert vBar is not None
    old = -1
    with qtbot.waitSignal(vBar.valueChanged) as value:
        prefs.sidebar.button(1).click()
        assert value.args[0] > old
        old = value.args[0]
    with qtbot.waitSignal(vBar.valueChanged) as value:
        prefs.sidebar.button(2).click()
        assert value.args[0] > old
        old = value.args[0]
    with qtbot.waitSignal(vBar.valueChanged) as value:
        prefs.sidebar.button(3).click()
        assert value.args[0] > old
        old = value.args[0]

    # Check Search
    prefs.searchText.setText("Display language")
    with qtbot.waitSignal(vBar.valueChanged) as value:
        prefs._gotoSearch()
        assert value.args[0] < old

    # Check Save Button
    prefs.show()
    with qtbot.waitSignal(prefs.newPreferencesReady) as signal:
        prefs.btnSave.click()
        assert len(signal.args) == 1
        assert isinstance(signal.args[0], GuiNeedsUpdate)

    # Check Close Button
    prefs.show()
    prefs.btnCancel.click()
    assert prefs.isHidden() is True

    # Close Using Escape Key
    prefs.show()
    event = QKeyEvent(QEvent.Type.KeyPress, QtKeyEscape, QtModNone)
    prefs.keyPressEvent(event)
    assert prefs.isHidden() is True

    # Other keys do not close the dialog
    prefs.show()
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, QtModNone)
    prefs.keyPressEvent(event)
    assert prefs.isHidden() is False

    # qtbot.stop()


@pytest.mark.gui
def testGuiPreferences_Settings(qtbot, monkeypatch, nwGUI, fncPath, tstPaths):
    """Test the preferences dialog settings."""
    spelling = [("en", "English [en]"), ("de", "Deutch [de]")]
    monkeypatch.setattr(SpellEnchant, "listDictionaries", lambda *a: spelling)

    (fncPath / "nw_en_US.qm").touch()
    (fncPath / "project_en_US.json").touch()
    CONFIG._nwLangPath = fncPath
    SHARED.theme._allThemes = {
        "theme1": ThemeEntry(name="Theme 1", dark=False, path=fncPath),
        "theme2": ThemeEntry(name="Theme 2", dark=False, path=fncPath),
        "theme3": ThemeEntry(name="Theme 3", dark=True, path=fncPath),
        "theme4": ThemeEntry(name="Theme 4", dark=True, path=fncPath),
    }

    prefs = GuiPreferences(nwGUI)
    with qtbot.waitExposed(prefs):
        prefs.show()

    # Appearance
    prefs.guiLocale.setCurrentIndex(prefs.guiLocale.findData("en_US"))
    prefs.lightTheme.setCurrentIndex(prefs.lightTheme.findData("theme1"))
    prefs.darkTheme.setCurrentIndex(prefs.darkTheme.findData("theme3"))
    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (QFont(), False))
        prefs.guiFontButton.click()  # Cancelled, so no change

    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (QFont(), True))
        prefs.nativeFont.setChecked(True)  # Use OS font dialog
        prefs.guiFontButton.click()

    prefs.hideVScroll.setChecked(True)
    prefs.hideHScroll.setChecked(True)
    prefs.useCharCount.setChecked(True)

    assert CONFIG.guiLocale != "en_US"
    assert CONFIG.lightTheme == "default_light"
    assert CONFIG.darkTheme == "default_dark"
    assert CONFIG.guiFont.family() != ""
    assert CONFIG.hideVScroll is False
    assert CONFIG.hideHScroll is False
    assert CONFIG.useCharCount is False

    # Document Style
    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (QFont(), False))
        prefs.textFontButton.click()  # Cancelled, so no change

    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "selectFont", lambda *a, **k: (QFont(), True))
        prefs.nativeFont.setChecked(False)  # Use Qt font dialog
        prefs.textFontButton.click()

    prefs.showFullPath.setChecked(False)
    prefs.incNotesWCount.setChecked(False)

    assert CONFIG.textFont.family() != ""
    assert CONFIG.showFullPath is True
    assert CONFIG.incNotesWCount is True

    # Project View
    prefs.iconColTree.setCurrentData("faded", "default")
    prefs.iconColDocs.setChecked(True)
    prefs.emphLabels.setChecked(False)

    assert CONFIG.iconColTree == DEF_TREECOL
    assert CONFIG.iconColDocs is False
    assert CONFIG.emphLabels is True

    # Behaviour
    prefs.autoSaveDoc.stepUp()
    prefs.autoSaveProj.stepUp()
    prefs.askBeforeExit.setChecked(False)
    prefs.moveMainWin.setChecked(False)

    assert CONFIG.autoSaveDoc == 30
    assert CONFIG.autoSaveProj == 60
    assert CONFIG.askBeforeExit is True
    assert CONFIG.moveMainWin is True

    # Project Backup
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: "")
        prefs.backupGetPath.click()  # Cancelled, so no change

    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a, **k: str(tstPaths.testDir))
        prefs.backupGetPath.click()
        assert prefs.backupPath == str(tstPaths.testDir)

    prefs.backupInterval.setCurrentData("day", "session")
    prefs.backupOnClose.setChecked(True)
    assert prefs.askBeforeBackup.isEnabled() is True
    prefs.askBeforeBackup.setChecked(False)

    assert CONFIG._backupPath != tstPaths.testDir
    assert CONFIG.backupInterval == "session"
    assert CONFIG.backupOnClose is False
    assert CONFIG.askBeforeBackup is True

    # Session Timer
    prefs.stopWhenIdle.setChecked(False)
    prefs.userIdleTime.stepUp()

    assert CONFIG.stopWhenIdle is True
    assert CONFIG.userIdleTime == 300

    # Text Flow
    prefs.textWidth.stepDown()
    prefs.focusWidth.stepDown()
    prefs.hideFocusFooter.setChecked(True)
    prefs.doJustify.setChecked(True)
    prefs.textMargin.stepUp()
    prefs.tabWidth.stepUp()
    prefs.lineHeight.stepUp()

    assert CONFIG.textWidth == 700
    assert CONFIG.focusWidth == 800
    assert CONFIG.hideFocusFooter is False
    assert CONFIG.doJustify is False
    assert CONFIG.textMargin == 40
    assert CONFIG.tabWidth == 40
    assert CONFIG.lineHeight == 1.15

    # Text Editing
    prefs.spellLanguage.setCurrentIndex(prefs.spellLanguage.findData("de"))
    prefs.autoSelect.setChecked(False)
    prefs.cursorWidth.setValue(5)
    prefs.scaleHeadings.setChecked(False)
    prefs.singleStarBold.setChecked(True)
    prefs.lineHighlight.setChecked(False)
    prefs.showTabsNSpaces.setChecked(True)
    prefs.showLineEndings.setChecked(True)

    assert CONFIG.spellLanguage != "de"
    assert CONFIG.autoSelect is True
    assert CONFIG.cursorWidth == 1
    assert CONFIG.scaleHeadings is True
    assert CONFIG.singleStarBold is False
    assert CONFIG.lineHighlight is True
    assert CONFIG.showTabsNSpaces is False
    assert CONFIG.showLineEndings is False

    # Editor Scrolling
    prefs.scrollPastEnd.setChecked(False)
    prefs.autoScroll.setChecked(False)
    prefs.autoScrollPos.stepUp()

    assert CONFIG.scrollPastEnd is True
    assert CONFIG.autoScroll is True
    assert CONFIG.autoScrollPos == 30

    # Text Highlighting
    prefs.dialogStyle.setCurrentData(3, 0)
    prefs.allowOpenDial.setChecked(False)
    prefs.dialogLine.setText(nwUnicode.U_EMDASH)
    prefs.narratorBreak.setCurrentData(nwUnicode.U_EMDASH, "")
    prefs.narratorDialog.setCurrentData(nwUnicode.U_EMDASH, "")
    prefs.altDialogOpen.setText("%")  # Symbol also tests for #2455
    prefs.altDialogClose.setText("%")  # Symbol also tests for #2455
    prefs.highlightEmph.setChecked(False)
    prefs.dottedModCodes.setChecked(True)
    prefs.showMultiSpaces.setChecked(True)

    actions = {a.data(): a for a in prefs.mnLineSymbols.actions()}
    actions[nwUnicode.U_ENDASH].trigger()
    assert prefs.dialogLine.text() == f"{nwUnicode.U_ENDASH} {nwUnicode.U_EMDASH}"

    assert CONFIG.dialogStyle == 2
    assert CONFIG.allowOpenDial is True
    assert CONFIG.dialogLine == ""
    assert CONFIG.narratorBreak == ""
    assert CONFIG.narratorDialog == ""
    assert CONFIG.altDialogOpen == ""
    assert CONFIG.altDialogClose == ""
    assert CONFIG.highlightEmph is True
    assert CONFIG.dottedModCodes is False
    assert CONFIG.showMultiSpaces is False

    # Text Automation
    prefs.doReplaceSQuote.setChecked(False)
    prefs.doReplaceDQuote.setChecked(False)
    prefs.doReplaceDash.setChecked(False)
    prefs.doReplaceDots.setChecked(False)
    prefs.doReplace.setChecked(False)
    prefs.fmtPadBefore.setText("!?:")
    prefs.fmtPadAfter.setText("¡¿")
    prefs.fmtPadThin.setChecked(True)

    assert prefs.doReplaceSQuote.isEnabled() is False
    assert prefs.doReplaceDQuote.isEnabled() is False
    assert prefs.doReplaceDash.isEnabled() is False
    assert prefs.doReplaceDots.isEnabled() is False
    assert prefs.fmtPadThin.isEnabled() is False

    assert CONFIG.doReplace is True
    assert CONFIG.doReplaceSQuote is True
    assert CONFIG.doReplaceDQuote is True
    assert CONFIG.doReplaceDash is True
    assert CONFIG.doReplaceDots is True
    assert CONFIG.fmtPadBefore == ""
    assert CONFIG.fmtPadAfter == ""
    assert CONFIG.fmtPadThin is False

    # Quotation Style
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_LSAQUO, False))
        prefs.btnSQuoteOpen.click()  # Cancelled, so no change
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_LSAQUO, True))
        prefs.btnSQuoteOpen.click()
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_RSAQUO, False))
        prefs.btnSQuoteClose.click()  # Cancelled, so no change
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_RSAQUO, True))
        prefs.btnSQuoteClose.click()
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_LAQUO, False))
        prefs.btnDQuoteOpen.click()  # Cancelled, so no change
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_LAQUO, True))
        prefs.btnDQuoteOpen.click()
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_RAQUO, False))
        prefs.btnDQuoteClose.click()  # Cancelled, so no change
    with monkeypatch.context() as mp:
        mp.setattr(GuiQuoteSelect, "getQuote", lambda *a, **k: (nwUnicode.U_RAQUO, True))
        prefs.btnDQuoteClose.click()

    assert CONFIG.fmtSQuoteOpen == nwUnicode.U_LSQUO
    assert CONFIG.fmtSQuoteClose == nwUnicode.U_RSQUO
    assert CONFIG.fmtDQuoteOpen == nwUnicode.U_LDQUO
    assert CONFIG.fmtDQuoteClose == nwUnicode.U_RDQUO

    # Features
    assert CONFIG.vimMode is False

    prefs.vimMode.setChecked(True)

    # Save Settings
    with monkeypatch.context() as mp:
        mp.setattr(QFontDatabase, "families", lambda *a: ["TestFont"])
        with qtbot.waitSignal(prefs.newPreferencesReady) as signal:
            prefs.btnSave.click()
            assert signal.args == [
                GuiNeedsUpdate(
                    restart=True,
                    tree=True,
                    theme=True,
                    syntax=True,
                    spelling=True,
                    vim=True,
                    editor=True,
                    viewport=True,
                    viewer=True,
                )
            ]

    # Check Settings
    # ==============

    # Appearance
    assert CONFIG.guiLocale == "en_US"
    assert CONFIG.lightTheme == "theme1"
    assert CONFIG.darkTheme == "theme3"
    assert CONFIG.guiFont == QFont()
    assert CONFIG.hideVScroll is True
    assert CONFIG.hideHScroll is True
    assert CONFIG.useCharCount is True

    # Document Style
    assert CONFIG.textFont == QFont()
    assert CONFIG.showFullPath is False
    assert CONFIG.incNotesWCount is False

    # Project View
    assert CONFIG.iconColTree == "faded"
    assert CONFIG.iconColDocs is True
    assert CONFIG.emphLabels is False

    # Behaviour
    assert CONFIG.autoSaveDoc == 31
    assert CONFIG.autoSaveProj == 61
    assert CONFIG.askBeforeExit is False
    assert CONFIG.moveMainWin is False

    # Project Backup
    assert CONFIG._backupPath == tstPaths.testDir
    assert CONFIG.backupInterval == "day"
    assert CONFIG.backupOnClose is True
    assert CONFIG.askBeforeBackup is False

    # Session Timer
    assert CONFIG.stopWhenIdle is False
    assert CONFIG.userIdleTime == 330

    # Text Flow
    assert CONFIG.textWidth == 690
    assert CONFIG.focusWidth == 790
    assert CONFIG.hideFocusFooter is True
    assert CONFIG.doJustify is True
    assert CONFIG.textMargin == 41
    assert CONFIG.tabWidth == 41
    assert CONFIG.lineHeight == 1.2

    # Text Editing
    assert CONFIG.spellLanguage == "de"
    assert CONFIG.autoSelect is False
    assert CONFIG.cursorWidth == 5
    assert CONFIG.scaleHeadings is False
    assert CONFIG.singleStarBold is True
    assert CONFIG.lineHighlight is False
    assert CONFIG.showTabsNSpaces is True
    assert CONFIG.showLineEndings is True

    # Editor Scrolling
    assert CONFIG.scrollPastEnd is False
    assert CONFIG.autoScroll is False
    assert CONFIG.autoScrollPos == 31

    # Text Highlighting
    assert CONFIG.dialogStyle == 3
    assert CONFIG.allowOpenDial is False
    assert CONFIG.dialogLine == f"{nwUnicode.U_ENDASH}{nwUnicode.U_EMDASH}"
    assert CONFIG.narratorBreak == nwUnicode.U_EMDASH
    assert CONFIG.narratorDialog == nwUnicode.U_EMDASH
    assert CONFIG.altDialogOpen == "%"
    assert CONFIG.altDialogClose == "%"
    assert CONFIG.highlightEmph is False
    assert CONFIG.dottedModCodes is True
    assert CONFIG.showMultiSpaces is True

    # Text Automation
    assert CONFIG.doReplace is False
    assert CONFIG.doReplaceSQuote is False
    assert CONFIG.doReplaceDQuote is False
    assert CONFIG.doReplaceDash is False
    assert CONFIG.doReplaceDots is False
    assert CONFIG.fmtPadBefore == "!:?"
    assert CONFIG.fmtPadAfter == "¡¿"
    assert CONFIG.fmtPadThin is True

    # Quotation Style
    assert CONFIG.fmtSQuoteOpen == nwUnicode.U_LSAQUO
    assert CONFIG.fmtSQuoteClose == nwUnicode.U_RSAQUO
    assert CONFIG.fmtDQuoteOpen == nwUnicode.U_LAQUO
    assert CONFIG.fmtDQuoteClose == nwUnicode.U_RAQUO

    # Features
    assert CONFIG.vimMode is True  # Note that the question box answers "yes" in tests
    assert SHARED.lastAlert == [
        "Are you sure you want to enable Vim mode?",
        "This changes how the editor accepts input.",
    ]

    # qtbot.stop()


@pytest.mark.gui
def testGuiPreferences_MemoryLeakRegression(qtbot, monkeypatch, nwGUI):
    """Test that the dialog is freed when it is closed."""
    monkeypatch.setattr(SpellEnchant, "listDictionaries", lambda *a: [("en", "English [en]")])
    checkDialogFreedOnClose(qtbot, lambda: GuiPreferences(nwGUI))
