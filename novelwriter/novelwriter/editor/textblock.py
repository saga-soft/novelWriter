"""
novelWriter - GUI Text Block Data
=================================

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

import re

from PyQt6.QtGui import QTextBlockUserData

from novelwriter import SHARED
from novelwriter.text.patterns import REGEX_PATTERNS

RX_URL = REGEX_PATTERNS.url
RX_LINK = REGEX_PATTERNS.markdownLink
RX_WORDS = REGEX_PATTERNS.wordSplit
RX_FMT_SC = REGEX_PATTERNS.shortcodePlain
RX_FMT_SV = REGEX_PATTERNS.shortcodeValue
RX_MULTI_SPACE = re.compile(r" {2,}")
RX_TRAIL_SPACE = re.compile(r"[ \t]+$")

T_TextMeta = tuple[int, int, str, str]
T_TextCheck = tuple[int, int, str]
T_TextMetaList = list[T_TextMeta]
T_TextCheckList = list[T_TextCheck]


class TextBlockData(QTextBlockUserData):
    """Custom QTextBlock Data.

    Custom data stored in a single text block. The spell check state is
    cached here and used when correcting misspelled text. All cached
    positions are in UTF-16 units, matching Qt document positions.
    """

    __slots__ = (
        "_formatErrors",
        "_metaData",
        "_offset",
        "_rawText",
        "_revision",
        "_spellErrors",
        "_text",
        "_utf16Map",
    )

    def __init__(self) -> None:
        super().__init__()
        self._text = ""
        self._rawText = ""
        self._offset = 0
        self._revision = 0
        self._utf16Map: list[int] | None = None
        self._metaData: T_TextMetaList = []
        self._spellErrors: T_TextCheckList = []
        self._formatErrors: T_TextCheckList = []

    ##
    #  Properties
    ##

    @property
    def metaData(self) -> T_TextMetaList:
        """Return meta data from last check."""
        return self._metaData

    @property
    def spellErrors(self) -> T_TextCheckList:
        """Return spell error data from last check."""
        return self._spellErrors

    @property
    def formatErrors(self) -> T_TextCheckList:
        """Return format error data from last check."""
        return self._formatErrors

    @property
    def revision(self) -> int:
        """Return the revision number of the cached text."""
        return self._revision

    ##
    #  Methods
    ##

    def clear(self) -> None:
        """Clear all cached data."""
        self._text = ""
        self._rawText = ""
        self._offset = 0
        self._revision += 1
        self._utf16Map = None
        self._metaData = []
        self._spellErrors = []
        self._formatErrors = []

    def checkData(self) -> tuple[str, str, int, list[int] | None]:
        """Return a snapshot of the text for external spell and format
        checking. The spell text has shortcodes, URLs and Markdown link
        syntax stripped, while the format text is the raw, unmodified
        block text.
        """
        return self._text, self._rawText, self._offset, self._utf16Map

    def setMetaData(self, metaData: T_TextMetaList) -> None:
        """Store meta data only as an alternative to processText."""
        self._metaData = metaData

    def setSpellErrors(self, errors: T_TextCheckList) -> None:
        """Store spell error data computed from a text snapshot."""
        self._spellErrors = errors

    def setFormatErrors(self, errors: T_TextCheckList) -> None:
        """Store format error data computed from a text snapshot."""
        self._formatErrors = errors

    def processText(self, text: str, offset: int, utf16Map: list[int] | None) -> None:
        """Extract meta data from the text. The map, when set, converts
        cached positions to UTF-16 units. Cached spell and format errors
        are cleared and left for the debounced background check to
        recompute.
        """
        self._spellErrors = []
        self._formatErrors = []
        self._metaData = []
        self._rawText = text
        if "[" in text:
            # Strip shortcodes
            for regEx in [RX_FMT_SC, RX_FMT_SV]:
                for res in regEx.finditer(text, offset):
                    if (s := res.start(0)) >= 0 and (e := res.end(0)) >= 0:  # pragma: no branch
                        pad = " " * (e - s)
                        text = f"{text[:s]}{pad}{text[e:]}"

        if "](" in text:
            # Strip Markdown links
            for res in RX_LINK.finditer(text, offset):
                if (s := res.start(0)) >= 0 and (e := res.end(0)) >= 0:  # pragma: no branch
                    ts, te = res.start(2), res.end(2)
                    text = f"{text[:s]}{' ' * (ts - s)}{text[ts:te]}{' ' * (e - te)}{text[e:]}"
                    if utf16Map:
                        s = utf16Map[s]
                        e = utf16Map[e]
                    self._metaData.append((s, e, res.group(4), "link"))

        if "://" in text:
            # Strip URLs
            for res in RX_URL.finditer(text, offset):
                if (s := res.start(0)) >= 0 and (e := res.end(0)) >= 0:  # pragma: no branch
                    pad = " " * (e - s)
                    text = f"{text[:s]}{pad}{text[e:]}"
                    if utf16Map:
                        s = utf16Map[s]
                        e = utf16Map[e]
                    self._metaData.append((s, e, res.group(0), "url"))

        self._text = text.replace("\u02bc", "'").replace("_", " ")
        self._offset = offset
        self._revision += 1
        self._utf16Map = utf16Map

    def spellCheck(self) -> T_TextCheckList:
        """Run the spell checker and cache the result, and return the
        list of spell check errors.
        """
        self._spellErrors = spellCheckText(self._text, self._offset, self._utf16Map)
        return self._spellErrors

    def formatCheck(self) -> T_TextCheckList:
        """Run the multi-space and trailing-space check and cache the
        result, and return the list of format errors.
        """
        self._formatErrors = formatCheckText(self._rawText, self._offset, self._utf16Map)
        return self._formatErrors


def spellCheckText(text: str, offset: int, utf16Map: list[int] | None) -> T_TextCheckList:
    """Spell check a piece of text and return the list of errors. This
    function does not touch any Qt document classes, so it is safe to
    call from a worker thread.
    """
    spell = SHARED.spelling
    if utf16Map:
        return [
            (utf16Map[r.start(0)], utf16Map[r.end(0)], w)
            for r in RX_WORDS.finditer(text, offset)
            if (w := r.group(0)) and not (w.isnumeric() or w.isupper() or spell.checkWord(w))
        ]
    return [
        (r.start(0), r.end(0), w)
        for r in RX_WORDS.finditer(text, offset)
        if (w := r.group(0)) and not (w.isnumeric() or w.isupper() or spell.checkWord(w))
    ]


def formatCheckText(text: str, offset: int, utf16Map: list[int] | None) -> T_TextCheckList:
    """Check a piece of text for runs of multiple spaces and trailing
    whitespace, and return the list of matches. This function does not
    touch any Qt document classes, so it is safe to call from a worker
    thread.
    """
    results: T_TextCheckList = []
    for res in RX_MULTI_SPACE.finditer(text, offset):
        s, e = res.start(0), res.end(0)
        if utf16Map:
            s, e = utf16Map[s], utf16Map[e]
        results.append((s, e, "multi"))

    if res := RX_TRAIL_SPACE.search(text, offset):
        s, e = res.start(0), res.end(0)
        if utf16Map:
            s, e = utf16Map[s], utf16Map[e]
        results.append((s, e, "trail"))

    return results
