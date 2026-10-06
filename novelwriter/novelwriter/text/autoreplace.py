"""
novelWriter - GUI AutoReplace
=============================

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

import logging

from typing import TYPE_CHECKING

from novelwriter import CONFIG
from novelwriter.types import QtKeepAnchor, QtMoveLeft

if TYPE_CHECKING:
    from PyQt6.QtGui import QTextCursor
    from PyQt6.QtWidgets import QLineEdit

logger = logging.getLogger(__name__)


class TextAutoReplace:
    """Encapsulates the editor auto replace feature."""

    def __call__(self, text: str, cursor: QTextCursor) -> bool:
        """Auto-replace text elements based on main configuration.
        Returns True if anything was changed.
        """
        aPos = cursor.position()
        bPos = cursor.positionInBlock()
        block = cursor.block()
        length = block.length() - 1
        if length < 1 or bPos - 1 > length:
            return False

        cursor.movePosition(QtMoveLeft, QtKeepAnchor, min(4, bPos))
        last = cursor.selectedText()
        delete, insert = self._determine(last, bPos)

        check = insert
        padBefore = CONFIG.fmtPadBefore
        padAfter = CONFIG.fmtPadAfter
        if padBefore and check and check in padBefore and not (check == ":" and length > 1 and text[0] == "@"):
            delete = max(delete, 1)
            chkPos = len(last) - delete - 1
            if chkPos >= 0 and last[chkPos].isspace():
                # Strip existing space before inserting a new (#1061)
                delete += 1
            padChar = "\u202f" if CONFIG.fmtPadThin else "\u00a0"
            insert = padChar + insert

        if padAfter and check and check in padAfter and not (check == ":" and length > 1 and text[0] == "@"):
            delete = max(delete, 1)
            padChar = "\u202f" if CONFIG.fmtPadThin else "\u00a0"
            insert = insert + padChar

        if delete > 0:
            cursor.setPosition(aPos)
            cursor.movePosition(QtMoveLeft, QtKeepAnchor, delete)
            cursor.insertText(insert)
            return True

        return False

    def _determine(self, text: str, pos: int) -> tuple[int, str]:
        """Determine what to replace, if anything."""
        t1 = text[-1:]
        t2 = text[-2:]
        t3 = text[-3:]
        t4 = text[-4:]

        if CONFIG.doReplaceDQuote and t1 == '"':
            # Process Double Quote
            if (
                pos == 1
                or (t2[:1].isspace() and t2.endswith('"'))
                or (pos == 2 and t2 == '>"')
                or (pos == 3 and t3 == '>>"')
                or (pos == 2 and t2 == '_"')
                or (t3[:1].isspace() and t3.endswith('_"'))
                or (pos == 3 and t3 in ('**"', '=="', '~~"'))
                or (t4[:1].isspace() and t4.endswith(('**"', '=="', '~~"')))
            ):
                return 1, CONFIG.fmtDQuoteOpen
            else:
                return 1, CONFIG.fmtDQuoteClose

        if CONFIG.doReplaceSQuote and t1 == "'":
            # Process Single Quote
            if (
                pos == 1
                or (t2[:1].isspace() and t2.endswith("'"))
                or (pos == 2 and t2 == ">'")
                or (pos == 3 and t3 == ">>'")
                or (pos == 2 and t2 == "_'")
                or (t3[:1].isspace() and t3.endswith("_'"))
                or (pos == 3 and t3 in ("**'", "=='", "~~'"))
                or (t4[:1].isspace() and t4.endswith(("**'", "=='", "~~'")))
            ):
                return 1, CONFIG.fmtSQuoteOpen
            else:
                return 1, CONFIG.fmtSQuoteClose

        if CONFIG.doReplaceDash and t1 == "-":
            # Process Dashes
            if t4 == "----":
                return 4, "\u2015"  # Horizontal bar
            elif t3 == "---":
                return 3, "\u2014"  # Long dash
            elif t2 == "--":
                return 2, "\u2013"  # Short dash
            elif t2 == "\u2013-":
                return 2, "\u2014"  # Long dash
            elif t2 == "\u2014-":
                return 2, "\u2015"  # Horizontal bar

        if CONFIG.doReplaceDots and t3 == "...":
            # Process Dots
            return 3, "\u2026"  # Ellipsis

        if t1 == "\u2028":  # Line separator
            # This resolves issue #1150
            return 1, "\u2029"  # Paragraph separator

        return 0, t1


class LineEditAutoReplace(TextAutoReplace):
    """Encapsulates the line edit auto replace feature."""

    def __call__(self, edit: QLineEdit) -> bool:
        """Auto-replace text elements based on main configuration.
        Returns True if anything was changed.
        """
        pos = edit.cursorPosition()
        text = edit.text()
        length = len(text)
        if length < 1:
            return False

        edit.setSelection(max(0, pos - 4), min(4, pos))
        last = edit.selectedText()
        edit.deselect()
        delete, insert = self._determine(last, pos)

        if delete > 0:
            edit.setSelection(max(0, pos - delete), min(delete, pos))
            edit.insert(insert)
            edit.deselect()
            return True

        return False
