"""
novelWriter - GUI TextAutoReplace Tests
=======================================

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

from PyQt6.QtGui import QTextCursor, QTextDocument
from PyQt6.QtWidgets import QLineEdit

from novelwriter import CONFIG
from novelwriter.constants import nwUnicode
from novelwriter.text.autoreplace import LineEditAutoReplace, TextAutoReplace


@pytest.mark.gui
def testTextAutoReplace_Symbols():
    """Test the editor auto-replace functionality."""
    CONFIG.fmtSQuoteOpen = nwUnicode.U_LSQUO
    CONFIG.fmtSQuoteClose = nwUnicode.U_RSQUO
    CONFIG.fmtDQuoteOpen = nwUnicode.U_LDQUO
    CONFIG.fmtDQuoteClose = nwUnicode.U_RDQUO

    CONFIG.doReplaceSQuote = True
    CONFIG.doReplaceDQuote = True
    CONFIG.doReplaceDash = True
    CONFIG.doReplaceDots = True

    ar = TextAutoReplace()

    def prep(text: str) -> tuple[str, int]:
        return text, len(text)

    # Double Quote Open
    assert ar._determine(*prep('"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('Stuff "')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('>"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('>>"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('_"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep(' _"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('\u00a0_"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('**"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep(' **"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('\u00a0**"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('=="')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep(' =="')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('\u00a0=="')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('~~"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep(' ~~"')) == (1, nwUnicode.U_LDQUO)
    assert ar._determine(*prep('\u00a0~~"')) == (1, nwUnicode.U_LDQUO)

    # Double Quote Close
    assert ar._determine(*prep('Stuff"')) == (1, nwUnicode.U_RDQUO)

    # Single Quote Open
    assert ar._determine(*prep("'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("Stuff '")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(">'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(">>'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("_'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(" _'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("\u00a0_'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("**'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(" **'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("\u00a0**'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("=='")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(" =='")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("\u00a0=='")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("~~'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep(" ~~'")) == (1, nwUnicode.U_LSQUO)
    assert ar._determine(*prep("\u00a0~~'")) == (1, nwUnicode.U_LSQUO)

    # Single Quote Close
    assert ar._determine(*prep("Stuff'")) == (1, nwUnicode.U_RSQUO)

    # Dashes
    assert ar._determine(*prep("-")) == (0, "-")
    assert ar._determine(*prep("--")) == (2, nwUnicode.U_ENDASH)
    assert ar._determine(*prep("---")) == (3, nwUnicode.U_EMDASH)
    assert ar._determine(*prep("----")) == (4, nwUnicode.U_HBAR)
    assert ar._determine(*prep("\u2013-")) == (2, nwUnicode.U_EMDASH)
    assert ar._determine(*prep("\u2014-")) == (2, nwUnicode.U_HBAR)

    # Ellipsis
    assert ar._determine(*prep(".")) == (0, ".")
    assert ar._determine(*prep("..")) == (0, ".")
    assert ar._determine(*prep("...")) == (3, nwUnicode.U_HELLIP)

    # Block Typed Line Separator (#1150)
    assert ar._determine(*prep("Text\u2028")) == (1, nwUnicode.U_PSEP)


@pytest.mark.gui
def testTextAutoReplace_Process():
    """Test the editor auto-replace functionality."""
    CONFIG.fmtDQuoteOpen = nwUnicode.U_LAQUO
    CONFIG.fmtDQuoteClose = nwUnicode.U_RAQUO

    CONFIG.doReplaceDQuote = True
    CONFIG.doReplaceDots = True

    ar = TextAutoReplace()
    doc = QTextDocument()

    def prep(text: str) -> tuple[str, QTextCursor]:
        doc.setPlainText(text)
        cursor = QTextCursor(doc)
        cursor.setPosition(len(text))
        return text, cursor

    # Nothing to Process
    assert ar(*prep("")) is False

    # Standard Auto-Replace
    assert ar(*prep("Text ...")) is True
    assert doc.toRawText() == "Text \u2026"

    # Pad Before, Normal
    CONFIG.fmtPadBefore = ":\u00bb"
    CONFIG.fmtPadThin = False
    assert ar(*prep("Text:")) is True
    assert doc.toRawText() == "Text\u00a0:"
    assert ar(*prep("Text :")) is True  # See #1061
    assert doc.toRawText() == "Text\u00a0:"
    assert ar(*prep('Text"')) is True
    assert doc.toRawText() == "Text\u00a0\u00bb"
    assert ar(*prep("@Synopsis:")) is False
    assert doc.toRawText() == "@Synopsis:"

    # Pad Before, Thin
    CONFIG.fmtPadBefore = ":\u00bb"
    CONFIG.fmtPadThin = True
    assert ar(*prep("Text:")) is True
    assert doc.toRawText() == "Text\u202f:"
    assert ar(*prep("Text :")) is True  # See #1061
    assert doc.toRawText() == "Text\u202f:"

    # Pad After, Normal
    CONFIG.fmtPadAfter = "\u00ab"
    CONFIG.fmtPadThin = False
    assert ar(*prep('Text "')) is True
    assert doc.toRawText() == "Text \u00ab\u00a0"

    # Pad After, Thin
    CONFIG.fmtPadAfter = "\u00ab"
    CONFIG.fmtPadThin = True
    assert ar(*prep('Text "')) is True
    assert doc.toRawText() == "Text \u00ab\u202f"


@pytest.mark.gui
def testTextAutoReplace_LineEdit(qtbot):
    """Test the line edit auto-replace functionality."""
    CONFIG.fmtDQuoteOpen = nwUnicode.U_LAQUO
    CONFIG.fmtDQuoteClose = nwUnicode.U_RAQUO

    CONFIG.doReplaceDQuote = True
    CONFIG.doReplaceDots = True

    ar = LineEditAutoReplace()
    edit = QLineEdit()
    qtbot.addWidget(edit)

    def prep(text: str) -> QLineEdit:
        edit.setText(text)
        edit.setCursorPosition(len(text))
        return edit

    # Nothing to Process
    assert ar(prep("")) is False
    assert ar(prep("Text")) is False

    # Standard Auto-Replace
    assert ar(prep("Text ...")) is True
    assert edit.text() == "Text \u2026"

    # Double Quote Open
    assert ar(prep('Text "')) is True
    assert edit.text() == "Text \u00ab"

    # Double Quote Close
    assert ar(prep('Text"')) is True
    assert edit.text() == "Text\u00bb"

    # Cursor Not at the End of the Text
    edit.setText('Text "More')
    edit.setCursorPosition(6)
    assert ar(edit) is True
    assert edit.text() == "Text \u00abMore"
    assert edit.cursorPosition() == 6
