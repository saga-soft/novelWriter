"""
novelWriter - Text Counting Functions
=====================================

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

from novelwriter.constants import nwRegEx, nwUnicode

RX_SC = re.compile(nwRegEx.FMT_SC)
RX_SV = re.compile(nwRegEx.FMT_SV)
RX_LO = re.compile(r"(?i)(?<!\\)(\[(?:vspace|newpage|new page)(:\d+)?)(?<!\\)(\])")


def preProcessText(text: str, keepHeaders: bool = True) -> list[str]:
    """Strip formatting codes from the text and split into lines."""
    if not isinstance(text, str):
        return []

    # We need to treat dashes as word separators for counting words.
    # The check+replace approach is much faster than direct replace for
    # large texts, and a bit slower for small texts, but in the latter
    # case it doesn't really matter.
    if nwUnicode.U_ENDASH in text:
        text = text.replace(nwUnicode.U_ENDASH, " ")
    if nwUnicode.U_EMDASH in text:
        text = text.replace(nwUnicode.U_EMDASH, " ")

    ignore = "%@" if keepHeaders else "%@#"

    result = []
    for line in text.splitlines():
        line = line.rstrip()
        if line:
            if line[0] in ignore:
                continue
            if line[0] == ">":
                line = line.lstrip(">").lstrip(" ")
        if line:  # Above block can return empty line (Issue #1816)
            if line[-1] == "<":
                line = line.rstrip("<").rstrip(" ")
            if "[" in line:
                # Strip shortcodes and special formatting
                # RegEx is slow, so we do this only when necessary
                line = RX_SC.sub("", line)
                line = RX_SV.sub("", line)
                line = RX_LO.sub("", line)

        result.append(line)

    return result


def standardCounter(text: str) -> tuple[int, int, int]:
    """Return a standard count.

    A counter that counts paragraphs, words and characters. This is the
    standard counter that includes headings in the word and character
    counts.
    """
    cCount = 0
    wCount = 0
    pCount = 0
    prevEmpty = True

    for line in preProcessText(text):
        countPara = True
        if not line:
            prevEmpty = True
            continue

        if line[0] == "#":
            if line[:5] == "#### ":
                line = line[5:]
                countPara = False
            elif line[:4] == "### ":
                line = line[4:]
                countPara = False
            elif line[:3] == "## ":
                line = line[3:]
                countPara = False
            elif line[:2] == "# ":
                line = line[2:]
                countPara = False
            elif line[:3] == "#! ":
                line = line[3:]
                countPara = False
            elif line[:4] == "##! ":
                line = line[4:]
                countPara = False
            elif line[:5] == "###! ":
                line = line[5:]
                countPara = False

        wCount += len(line.split())
        cCount += len(line)
        if countPara and prevEmpty:
            pCount += 1

        prevEmpty = not countPara

    return cCount, wCount, pCount


def bodyTextCounter(text: str) -> tuple[int, int, int]:
    """Return a body text count.

    A counter that counts body text words, characters, and characters
    without white spaces.
    """
    wCount = 0
    cCount = 0
    sCount = 0

    for line in preProcessText(text, keepHeaders=False):
        words = line.split()
        wCount += len(words)
        cCount += len(line)
        sCount += len("".join(words))

    return wCount, cCount, sCount
