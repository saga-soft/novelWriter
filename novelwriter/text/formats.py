"""
novelWriter - Text Formats
==========================

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

from novelwriter.enum import nwComment

MODIFIERS = {
    "synopsis": nwComment.SYNOPSIS,
    "short": nwComment.SHORT,
    "note": nwComment.NOTE,
    "footnote": nwComment.FOOTNOTE,
    "story": nwComment.STORY,
}
KEY_REQ = {
    "synopsis": 0,  # Key not allowed
    "short": 0,  # Key not allowed
    "note": 1,  # Key optional
    "footnote": 2,  # Key required
    "story": 2,  # Key required
}


def _checkModKey(modifier: str, key: str) -> bool:
    """Check if a modifier and key set are ok."""
    if modifier in MODIFIERS:
        if key == "":
            return KEY_REQ[modifier] < 2
        elif key.replace("_", "").isalnum():
            return KEY_REQ[modifier] > 0
    return False


def processComment(text: str) -> tuple[nwComment, str, str, int, int]:
    """Extract comment style, key and text. Should only be called on
    text starting with a %.
    """
    if text[:2] == "%~":
        return nwComment.IGNORE, "", text[2:].lstrip(), 0, 0

    check = text[1:].strip()
    start, _, content = check.partition(":")
    modifier, _, key = start.rstrip().partition(".")
    if content and (clean := modifier.lower()) and _checkModKey(clean, key):
        col = text.find(":") + 1
        dot = text.find(".", 0, col) + 1
        return MODIFIERS[clean], key, content.lstrip(), dot, col

    return nwComment.PLAIN, "", check, 0, 0


def processHeading(line: str) -> tuple[str, str]:
    """Split a heading into its heading level and text value."""
    if line.startswith("# "):
        return "H1", line[2:].strip()
    elif line.startswith("## "):
        return "H2", line[3:].strip()
    elif line.startswith("### "):
        return "H3", line[4:].strip()
    elif line.startswith("#### "):
        return "H4", line[5:].strip()
    elif line.startswith("#! "):
        return "H1", line[3:].strip()
    elif line.startswith("##! "):
        return "H2", line[4:].strip()
    elif line.startswith("###! "):
        return "H3", line[5:].strip()
    return "H0", ""
