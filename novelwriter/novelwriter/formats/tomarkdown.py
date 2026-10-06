"""
novelWriter - Markdown Text Converter
=====================================

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

import logging

from typing import TYPE_CHECKING

from novelwriter.constants import nwUnicode
from novelwriter.formats.shared import BlockFmt, BlockTyp, T_Formats, TextFmt
from novelwriter.formats.tokenizer import COMMENT_BLOCKS, Tokenizer

if TYPE_CHECKING:
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)


# Standard Markdown
STD_MD = {
    TextFmt.B_B: "**",
    TextFmt.B_E: "**",
    TextFmt.I_B: "_",
    TextFmt.I_E: "_",
    TextFmt.D_B: "",
    TextFmt.D_E: "",
    TextFmt.U_B: "",
    TextFmt.U_E: "",
    TextFmt.M_B: "",
    TextFmt.M_E: "",
    TextFmt.SUP_B: "",
    TextFmt.SUP_E: "",
    TextFmt.SUB_B: "",
    TextFmt.SUB_E: "",
    TextFmt.STRIP: "",
}

# Extended Markdown
EXT_MD = {
    TextFmt.B_B: "**",
    TextFmt.B_E: "**",
    TextFmt.I_B: "_",
    TextFmt.I_E: "_",
    TextFmt.D_B: "~~",
    TextFmt.D_E: "~~",
    TextFmt.U_B: "",
    TextFmt.U_E: "",
    TextFmt.M_B: "==",
    TextFmt.M_E: "==",
    TextFmt.SUP_B: "^",
    TextFmt.SUP_E: "^",
    TextFmt.SUB_B: "~",
    TextFmt.SUB_E: "~",
    TextFmt.STRIP: "",
}


class ToMarkdown(Tokenizer):
    """Core: Markdown Document Writer.

    Extend the Tokenizer class to writer Markdown output. It supports
    both Standard Markdown and Extended Markdown. The class also
    supports concatenating novelWriter markup files.
    """

    __slots__ = ("_extended", "_usedFields", "_usedNotes")

    def __init__(self, project: NWProject, extended: bool) -> None:
        super().__init__(project)
        self._extended = extended
        self._usedNotes: dict[str, int] = {}
        self._usedFields: list[tuple[int, str]] = []

    ##
    #  Class Methods
    ##

    def doConvert(self) -> None:
        """Convert the list of text tokens into a Markdown document."""
        if self._extended:
            mTags = EXT_MD
            cSkip = nwUnicode.U_MMSP
        else:
            mTags = STD_MD
            cSkip = ""

        lines = []
        for tType, _, tText, tFormat, tStyle in self._blocks:
            if tType == BlockTyp.TEXT:
                tTemp = self._formatText(tText, tFormat, mTags).replace("\n", "  \n")
                lines.append(f"{tTemp}\n\n")

            elif tType in (BlockTyp.TITLE, BlockTyp.PART):
                tHead = tText.replace("\n", " - ")
                lines.append(f"{tHead}\n")
                lines.append("=" * len(tHead) + "\n\n")

            elif tType == BlockTyp.HEAD1:
                tHead = tText.replace("\n", " - ")
                lines.append(f"# {tHead}\n\n")

            elif tType == BlockTyp.HEAD2:
                tHead = tText.replace("\n", " - ")
                lines.append(f"## {tHead}\n\n")

            elif tType == BlockTyp.HEAD3:
                tHead = tText.replace("\n", " - ")
                lines.append(f"### {tHead}\n\n")

            elif tType == BlockTyp.HEAD4:
                tHead = tText.replace("\n", " - ")
                lines.append(f"#### {tHead}\n\n")

            elif tType == BlockTyp.SEP:
                lines.append(f"{tText}\n\n")

            elif tType == BlockTyp.HRULE:
                lines.append("----\n\n")

            elif tType == BlockTyp.SKIP:
                lines.append(f"{cSkip}\n\n")

            elif tType in COMMENT_BLOCKS:
                lines.append(f"{self._formatText(tText, tFormat, mTags)}\n\n")

            elif tType == BlockTyp.KEYWORD:
                end = "  \n" if tStyle & BlockFmt.Z_BTM else "\n\n"
                lines.append(f"{self._formatText(tText, tFormat, mTags)}{end}")

            else:  # pragma: no cover
                pass

        self._pages.append("".join(lines))

    def closeDocument(self) -> None:
        """Run close document tasks."""
        # Replace fields if there are stats available
        if self._usedFields and self._counts:
            pages = len(self._pages)
            for doc, field in self._usedFields:
                if doc >= 0 and doc < pages and (value := self._counts.get(field)) is not None:
                    self._pages[doc] = self._pages[doc].replace(f"{{{{{field}}}}}", self._formatInt(value))

        # Add footnotes
        if self._usedNotes:
            tags = EXT_MD if self._extended else STD_MD
            footnotes = self._localLookup("Footnotes")

            lines = []
            lines.append(f"### {footnotes}\n\n")
            for key, index in self._usedNotes.items():
                if content := self._footnotes.get(key):  # pragma: no branch
                    marker = f"{index}. "
                    text = self._formatText(content[0], content[1], tags)
                    lines.append(f"{marker}{text}\n")
            lines.append("\n")
            self._pages.append("".join(lines))

    def saveDocument(self, path: Path) -> None:
        """Save the data to a plain text file."""
        with open(path, mode="w", encoding="utf-8") as outFile:
            outFile.write("".join(self._pages))
        logger.info("Wrote file: %s", path)

    def replaceTabs(self, nSpaces: int = 8, spaceChar: str = " ") -> None:
        """Replace tabs with spaces."""
        spaces = spaceChar * nSpaces
        self._pages = [p.replace("\t", spaces) for p in self._pages]

    ##
    #  Internal Functions
    ##

    def _formatText(self, text: str, tFmt: T_Formats, tags: dict[TextFmt, str]) -> str:
        """Apply formatting tags to text."""
        temp = text
        for pos, fmt, data in reversed(tFmt):
            md = ""
            if fmt == TextFmt.FNOTE:
                if data in self._footnotes:
                    index = len(self._usedNotes) + 1
                    self._usedNotes[data] = index
                    md = f"[{index}]"
                else:
                    md = "[ERR]"
            elif fmt == TextFmt.FIELD:
                if field := data.partition(":")[2]:  # pragma: no branch
                    self._usedFields.append((len(self._pages), field))
                    md = f"{{{{{field}}}}}"
            else:
                md = tags.get(fmt, "")
            temp = f"{temp[:pos]}{md}{temp[pos:]}"
        return temp
