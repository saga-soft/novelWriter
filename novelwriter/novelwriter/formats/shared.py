"""
novelWriter - Formats Shared
============================

This file is a part of novelWriter
Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors

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

import re

from enum import Flag, IntEnum

from PyQt6.QtGui import QColor

ESCAPES = {
    r"\*": "*",
    r"\~": "~",
    r"\=": "=",
    r"\_": "_",
    r"\[": "[",
    r"\]": "]",
    r"\ ": "",
}
RX_ESC = re.compile("|".join([re.escape(k) for k in ESCAPES]), flags=re.DOTALL)


def stripEscape(text: str) -> str:
    """Strip escaped Markdown characters from paragraph text."""
    if "\\" in text:
        return RX_ESC.sub(lambda x: ESCAPES[x.group(0)], text)
    return text


class TextDocumentTheme:
    """Default document theme."""

    text: QColor = QColor(0, 0, 0)
    highlight: QColor = QColor(255, 255, 166)
    head: QColor = QColor(66, 113, 174)
    link: QColor = QColor(66, 113, 174)
    comment: QColor = QColor(100, 100, 100)
    note: QColor = QColor(129, 55, 9)
    code: QColor = QColor(66, 113, 174)
    modifier: QColor = QColor(129, 55, 9)
    keyword: QColor = QColor(245, 135, 31)
    tag: QColor = QColor(66, 113, 174)
    optional: QColor = QColor(66, 113, 174)
    dialog: QColor = QColor(66, 113, 174)
    altdialog: QColor = QColor(129, 55, 9)


# Enums
# =====


class TextFmt(IntEnum):
    """Text Format.

    An enum indicating the beginning or end of a text format region.
    They must be paired with a position, and apply to locations in a
    text block.
    """

    B_B = 1  # Begin bold
    B_E = 2  # End bold
    I_B = 3  # Begin italics
    I_E = 4  # End italics
    D_B = 5  # Begin strikeout
    D_E = 6  # End strikeout
    U_B = 7  # Begin underline
    U_E = 8  # End underline
    M_B = 9  # Begin mark
    M_E = 10  # End mark
    SUP_B = 11  # Begin superscript
    SUP_E = 12  # End superscript
    SUB_B = 13  # Begin subscript
    SUB_E = 14  # End subscript
    COL_B = 15  # Begin colour
    COL_E = 16  # End colour
    ANM_B = 17  # Begin anchor name
    ANM_E = 18  # End anchor name
    ARF_B = 19  # Begin anchor link
    ARF_E = 20  # End anchor link
    HRF_B = 21  # Begin href link
    HRF_E = 22  # End href link
    FNOTE = 23  # Footnote marker
    FIELD = 24  # Data field
    STRIP = 25  # Strip the format code


class BlockTyp(IntEnum):
    """Text Block Type.

    An enum indicating the type of a text block.
    """

    EMPTY = 1  # Empty line (new paragraph)
    TITLE = 2  # Title
    PART = 3  # Partition
    HEAD1 = 4  # Heading 1 or Chapter
    HEAD2 = 5  # Heading 2 or Scene
    HEAD3 = 6  # Heading 3 or Section
    HEAD4 = 7  # Heading 4
    TEXT = 8  # Text line
    SEP = 9  # Scene separator
    HRULE = 10  # Horizontal rule
    SKIP = 11  # Paragraph break
    SUMMARY = 12  # Synopsis/short comment
    NOTE = 13  # Note
    COMMENT = 14  # Comment
    KEYWORD = 15  # Tag/reference keywords


class BlockFmt(Flag):
    """Text Block Format.

    An enum of flags that can be combined to format a text block.
    """

    NONE = 0x0000  # No special style
    LEFT = 0x0001  # Left aligned
    RIGHT = 0x0002  # Right aligned
    CENTRE = 0x0004  # Centred
    JUSTIFY = 0x0008  # Justified
    PBB = 0x0010  # Page break before
    PBA = 0x0020  # Page break after
    Z_TOP = 0x0040  # Zero top margin
    Z_BTM = 0x0080  # Zero bottom margin
    IND_L = 0x0100  # Left indentation
    IND_R = 0x0200  # Right indentation
    IND_T = 0x0400  # Text indentation

    # Masks
    ALIGNED = LEFT | RIGHT | CENTRE | JUSTIFY


# Types
# =====

# A list of formats for a single text string, consisting of:
# text position, text format, and meta data
T_Formats = list[tuple[int, TextFmt, str]]

# A note or comment with text and associated text formats
T_Note = tuple[str, T_Formats]

# A tokenized text block, consisting of:
# type, header number, text, text formats, and block format
T_Block = tuple[BlockTyp, str, str, T_Formats, BlockFmt]
