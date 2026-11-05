"""
novelWriter - QTextDocument to Text Converter
=============================================

This file is a part of novelWriter.

Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors.

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

from PyQt6.QtGui import QFont, QTextCharFormat, QTextDocument, QTextListFormat

from novelwriter import CONFIG
from novelwriter.constants import nwShortcode, nwUnicode
from novelwriter.types import (
    QtAlignAbsolute,
    QtAlignHCenter,
    QtAlignLeft,
    QtAlignRight,
    QtLayoutRTL,
    QtVAlignSub,
    QtVAlignSuper,
)

if TYPE_CHECKING:
    from PyQt6.QtGui import QTextBlock

logger = logging.getLogger(__name__)

SHORTCODES = {
    "bold": (nwShortcode.BOLD_O, nwShortcode.BOLD_C),
    "italic": (nwShortcode.ITALIC_O, nwShortcode.ITALIC_C),
    "strike": (nwShortcode.STRIKE_O, nwShortcode.STRIKE_C),
    "underline": (nwShortcode.ULINE_O, nwShortcode.ULINE_C),
    "sup": (nwShortcode.SUP_O, nwShortcode.SUP_C),
    "sub": (nwShortcode.SUB_O, nwShortcode.SUB_C),
}


# Nesting order for wrapping active formats, innermost first. Italic
# must be innermost of the three Markdown-eligible formats.
MARKDOWN_FMTS = ("underline", "sub", "sup", "italic", "strike", "bold")
MARKDOWN_TAGS = {
    "italic": "_",
    "strike": "~~",
}

UNORDERED_LISTS = (
    QTextListFormat.Style.ListDisc,
    QTextListFormat.Style.ListCircle,
    QTextListFormat.Style.ListSquare,
)


def _markdownTag(name: str) -> str:
    """Return the Markdown tag for a given format name."""
    if name == "bold":
        return "*" if CONFIG.singleStarBold else "**"
    return MARKDOWN_TAGS.get(name, "")


def _isWordChar(char: str) -> bool:
    """Check if a character counts as a word character."""
    return char.isalnum() or char == "_"


class FromQTextDocument:
    """Core: Convert a QTextDocument to novelWriter's Text Format."""

    __slots__ = ("_document", "_preserveSoftBreak", "_result")

    def __init__(self, document: QTextDocument) -> None:

        # Internal Variables
        self._document = document
        self._result: list[str] = []

        # Settings
        self._preserveSoftBreak = True

    ##
    #  Setters
    ##

    def setPreserveSoftBreak(self, state: bool) -> None:
        """Set whether soft line breaks should be preserved as hard
        line breaks, or collapsed into a single space.
        """
        self._preserveSoftBreak = state

    ##
    #  Methods
    ##

    def convertText(self) -> str:
        """Convert the document one block at a time. Yields the number
        of blocks processed so far as a progress counter.
        """
        self._result = []
        block = self._document.begin()
        while block.isValid():
            if (level := block.blockFormat().headingLevel()) > 0:
                self._addHeading(block, level)
            elif block.textList():
                self._addListItem(block)
            else:
                self._addParagraph(block)
            block = block.next()

        return "\n".join(self._result)

    ##
    #  Internal Functions
    ##

    def _addHeading(self, block: QTextBlock, level: int) -> None:
        """Add a heading block to the result."""
        text = self._resolveSoftBreaks(block.text())
        if level <= 4:
            self._result.append(f"{'#' * level} {text}")
        else:
            bold = "*" if CONFIG.singleStarBold else "**"
            self._result.append(f"{bold}{text}{bold}")
        self._result.append("")

    def _addParagraph(self, block: QTextBlock) -> None:
        """Add a regular text block to the result."""
        text = self._formatBlock(block)
        if text.strip():
            self._result.append(self._applyAlignment(block, text))
        self._result.append("")

    def _addListItem(self, block: QTextBlock) -> None:
        """Add a list item block to the result. Nested lists are
        flattened, and a list only ends when the list type changes.
        """
        marker = self._listMarker(block)
        text = self._formatBlock(block)
        if text.strip():
            self._result.append(f"{marker}{text.strip()}")
        if self._listMarker(block.next()) != marker:
            self._result.append("")

    def _listMarker(self, block: QTextBlock) -> str:
        """Return the list marker for a block, if it is a list item."""
        if block.isValid() and (qList := block.textList()):
            return "* " if qList.format().style() in UNORDERED_LISTS else "#. "
        return ""

    def _applyAlignment(self, block: QTextBlock, text: str) -> str:
        """Wrap aligned paragraphs in novelWriter's alignment markers.
        Alignment to the leading side of the text direction is the
        default and is left as-is.
        """
        align = block.blockFormat().alignment()
        if align & QtAlignHCenter:
            return f">> {text} <<"

        rtl = block.textDirection() == QtLayoutRTL
        if align & (QtAlignLeft if rtl and align & QtAlignAbsolute else QtAlignRight):
            return f"{text} <<" if rtl else f">> {text}"

        return text

    def _resolveSoftBreaks(self, text: str) -> str:
        """Convert soft line break characters to either a Markdown
        hard line break, or a single space.
        """
        if self._preserveSoftBreak:
            return text.replace(nwUnicode.U_LSEP, "\n")
        return text.replace(nwUnicode.U_LSEP, " ")

    def _formatBlock(self, block: QTextBlock) -> str:
        """Format the text of a block, applying inline formatting to
        each of its fragments. Adjacent Qt fragments that carry the
        same effective formatting are merged first, as Qt's HTML
        round trip can split a single formatted run into several
        fragments that differ only in formatting-irrelevant
        properties like anchors (see #2978).
        """
        blockText = block.text()
        merged: list[tuple[str, dict[str, bool]]] = []
        it = block.begin()
        while not it.atEnd():
            if (frag := it.fragment()).isValid():  # pragma: no branch
                text = frag.text()
                active = self._activeFormats(frag.charFormat())
                if merged and merged[-1][1] == active:
                    prevText, _ = merged[-1]
                    merged[-1] = (prevText + text, active)
                else:
                    merged.append((text, active))
            it += 1

        parts = []
        offset = 0
        for text, active in merged:
            parts.append(self._formatFragment(text, offset, blockText, active))
            offset += len(text)

        return self._resolveSoftBreaks("".join(parts))

    def _activeFormats(self, cFormat: QTextCharFormat) -> dict[str, bool]:
        """Extract the set of Markdown-relevant formats that are
        active for a given character format.
        """
        align = cFormat.verticalAlignment()
        return {
            "underline": cFormat.fontUnderline(),
            "sub": align == QtVAlignSub,
            "sup": align == QtVAlignSuper,
            "strike": cFormat.fontStrikeOut(),
            "italic": cFormat.fontItalic(),
            "bold": cFormat.fontWeight() >= QFont.Weight.Bold,
        }

    def _formatFragment(self, text: str, start: int, blockText: str, active: dict[str, bool]) -> str:
        """Wrap a single formatted text fragment in the appropriate
        Markdown syntax or novelWriter shortcode.
        """
        core = text.strip()
        if not core:
            return text

        lead = text[: len(text) - len(text.lstrip())]
        trail = text[len(lead) + len(core) :]

        coreStart = start + len(lead)
        coreEnd = coreStart + len(core)
        cleanEdges = (coreStart == 0 or not _isWordChar(blockText[coreStart - 1])) and (
            coreEnd >= len(blockText) or not _isWordChar(blockText[coreEnd])
        )

        for name in MARKDOWN_FMTS:
            if not active[name]:
                continue
            if name in ("bold", "italic", "strike") and cleanEdges:
                tag = _markdownTag(name)
                core = f"{tag}{core}{tag}"
            else:
                cOpen, cClose = SHORTCODES[name]
                core = f"{cOpen}{core}{cClose}"

        return f"{lead}{core}{trail}"
