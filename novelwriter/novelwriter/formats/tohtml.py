"""
novelWriter - HTML Text Converter
=================================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

import json
import logging

from time import time
from typing import TYPE_CHECKING

from novelwriter.common import formatTimeStamp
from novelwriter.constants import nwHtmlUnicode
from novelwriter.formats.shared import BlockFmt, BlockTyp, T_Formats, TextFmt, stripEscape
from novelwriter.formats.tokenizer import COMMENT_BLOCKS, Tokenizer
from novelwriter.types import FONT_STYLE, FONT_WEIGHTS, QtHexRgb

if TYPE_CHECKING:
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

# Each opener tag, with the id of its corresponding closer and tag format
HTML_OPENER: dict[int, tuple[int, str]] = {
    TextFmt.B_B: (TextFmt.B_E, "<strong>"),
    TextFmt.I_B: (TextFmt.I_E, "<em>"),
    TextFmt.D_B: (TextFmt.D_E, "<del>"),
    TextFmt.U_B: (TextFmt.U_E, "<span style='text-decoration: underline;'>"),
    TextFmt.M_B: (TextFmt.M_E, "<mark>"),
    TextFmt.SUP_B: (TextFmt.SUP_E, "<sup>"),
    TextFmt.SUB_B: (TextFmt.SUB_E, "<sub>"),
    TextFmt.COL_B: (TextFmt.COL_E, "<span style='color: {0}'>"),
    TextFmt.ANM_B: (TextFmt.ANM_E, "<a name='{0}'>"),
    TextFmt.ARF_B: (TextFmt.ARF_E, "<a href='{0}'>"),
    TextFmt.HRF_B: (TextFmt.HRF_E, "<a href='{0}'>"),
}

# Each closer tag, with the id of its corresponding opener and tag format
HTML_CLOSER: dict[int, tuple[int, str]] = {
    TextFmt.B_E: (TextFmt.B_B, "</strong>"),
    TextFmt.I_E: (TextFmt.I_B, "</em>"),
    TextFmt.D_E: (TextFmt.D_B, "</del>"),
    TextFmt.U_E: (TextFmt.U_B, "</span>"),
    TextFmt.M_E: (TextFmt.M_B, "</mark>"),
    TextFmt.SUP_E: (TextFmt.SUP_B, "</sup>"),
    TextFmt.SUB_E: (TextFmt.SUB_B, "</sub>"),
    TextFmt.COL_E: (TextFmt.COL_B, "</span>"),
    TextFmt.ANM_E: (TextFmt.ANM_B, "</a>"),
    TextFmt.ARF_E: (TextFmt.ARF_B, "</a>"),
    TextFmt.HRF_E: (TextFmt.HRF_B, "</a>"),
}

# Empty HTML tag record
HTML_NONE = (0, "")


class ToHtml(Tokenizer):
    """Core: HTML Document Writer.

    Extend the Tokenizer class to write HTML output.
    """

    __slots__ = ("_brTag", "_cssStyles", "_trMap", "_usedFields", "_usedNotes")

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._trMap = {}
        self._cssStyles = True
        self._usedNotes: dict[str, int] = {}
        self._usedFields: list[tuple[int, str]] = []
        self._brTag = "<br>"
        self.setReplaceUnicode(False)

    ##
    #  Setters
    ##

    def setStyles(self, cssStyles: bool) -> None:
        """Enable or disable CSS styling. Some elements may still have
        class tags.
        """
        self._cssStyles = cssStyles

    def setReplaceUnicode(self, doReplace: bool) -> None:
        """Set the translation map to either minimal or full unicode for
        html entities replacement.
        """
        # Control characters must always be replaced
        # Angle brackets are replaced later as they are also used in
        # formatting codes
        self._trMap = str.maketrans({"&": "&amp;"})
        if doReplace:
            # Extend to all relevant Unicode characters
            self._trMap.update(str.maketrans(nwHtmlUnicode.U_TO_H))

    ##
    #  Class Methods
    ##

    def doPreProcessing(self) -> None:
        """Extend the auto-replace to also properly encode some unicode
        characters into their respective HTML entities.
        """
        super().doPreProcessing()
        self._text = self._text.translate(self._trMap)

    def doConvert(self) -> None:
        """Convert the list of text tokens into an HTML document."""
        lines = []
        for tType, tMeta, tText, tFmt, tStyle in self._blocks:
            tText, tFmt = self._processHtmlEntities(tText, tFmt)
            hStyle = self._genInlineStyles(tStyle)

            aNm = ""
            if self._linkHeadings and tMeta:
                aNm = f"<a name='{tMeta}'></a>"

            # Process Text Type
            if tType == BlockTyp.TEXT:
                lines.append(f"<p{hStyle}>{self._formatText(tText, tFmt)}</p>\n")

            elif tType in (BlockTyp.TITLE, BlockTyp.PART):
                tHead = tText.replace("\n", self._brTag)
                lines.append(f"<p class='title'{hStyle}>{aNm}{tHead}</p>\n")

            elif tType == BlockTyp.HEAD1:
                tHead = tText.replace("\n", self._brTag)
                lines.append(f"<h1{hStyle}>{aNm}{tHead}</h1>\n")

            elif tType == BlockTyp.HEAD2:
                tHead = tText.replace("\n", self._brTag)
                lines.append(f"<h2{hStyle}>{aNm}{tHead}</h2>\n")

            elif tType == BlockTyp.HEAD3:
                tHead = tText.replace("\n", self._brTag)
                lines.append(f"<h3{hStyle}>{aNm}{tHead}</h3>\n")

            elif tType == BlockTyp.HEAD4:
                tHead = tText.replace("\n", self._brTag)
                lines.append(f"<h4{hStyle}>{aNm}{tHead}</h4>\n")

            elif tType == BlockTyp.SEP:
                lines.append(f"<p class='sep'{hStyle}>{tText}</p>\n")

            elif tType == BlockTyp.HRULE:
                lines.append(f"<hr{hStyle}>\n")

            elif tType == BlockTyp.SKIP:
                lines.append(f"<p{hStyle}>&nbsp;</p>\n")

            elif tType in COMMENT_BLOCKS:
                lines.append(f"<p class='comment'{hStyle}>{self._formatText(tText, tFmt)}</p>\n")

            elif tType == BlockTyp.KEYWORD:
                tClass = f"meta meta-{tMeta}"
                lines.append(f"<p class='{tClass}'{hStyle}>{self._formatText(tText, tFmt)}</p>\n")

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
            footnotes = self._localLookup("Footnotes")

            lines = []
            lines.append(f"<h3>{footnotes}</h3>\n")
            lines.append("<ol>\n")
            for key, index in self._usedNotes.items():
                if content := self._footnotes.get(key):  # pragma: no branch
                    text = self._formatText(*content)
                    lines.append(f"<li id='footnote_{index}'><p>{text}</p></li>\n")
            lines.append("</ol>\n")

            self._pages.append("".join(lines))

    def saveDocument(self, path: Path) -> None:
        """Save the data to an HTML file."""
        if path.suffix.lower() == ".json":
            ts = time()
            data = {
                "meta": {
                    "projectName": self._project.data.name,
                    "novelAuthor": self._project.data.author,
                    "buildTime": int(ts),
                    "buildTimeStr": formatTimeStamp(ts),
                },
                "text": {
                    "css": self._generateStyleSheet(),
                    "html": [t.replace("\t", "&#09;").rstrip().split("\n") for t in self._pages],
                },
            }
            with open(path, mode="w", encoding="utf-8") as fObj:
                json.dump(data, fObj, indent=2)

        else:
            html = []
            html.append("<!DOCTYPE html>")
            html.append(f"<html lang='{self._dLocale.bcp47Name()}'>")
            html.append("<head>")
            html.append(f"<title>{self._project.data.name:s}</title>")
            html.append("<meta charset='utf-8'>")
            if self._cssStyles:
                html.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
                html.append("<style>")
                html.extend(self._generateStyleSheet())
                html.append("</style>")
            html.append("</head>")
            html.append("<body>")
            html.append(("".join(self._pages)).replace("\t", "&#09;").rstrip())
            html.append("</body>")
            html.append("</html>\n")

            with open(path, mode="w", encoding="utf-8") as fObj:
                fObj.write("\n".join(html))

        logger.info("Wrote file: %s", path)

    def replaceTabs(self, nSpaces: int = 8, spaceChar: str = "&nbsp;") -> None:
        """Replace tabs with spaces in the html."""
        tabSpace = spaceChar * nSpaces
        pages = [aLine.replace("\t", tabSpace) for aLine in self._pages]
        self._pages = pages

    ##
    #  Internal Functions
    ##

    def _generateStyleSheet(self) -> list[str]:
        """Generate a stylesheet for the current settings."""
        if not self._cssStyles:
            return []

        tColor = self._theme.text.name(QtHexRgb)
        lColor = self._theme.head.name(QtHexRgb)
        mColor = self._theme.highlight.name(QtHexRgb)
        cColor = self._theme.comment.name(QtHexRgb)
        hColor = lColor if self._colorHeads else tColor

        mtH0 = self._marginTitle[0]
        mbH0 = self._marginTitle[1]
        mtH1 = self._marginHead1[0]
        mbH1 = self._marginHead1[1]
        mtH2 = self._marginHead2[0]
        mbH2 = self._marginHead2[1]
        mtH3 = self._marginHead3[0]
        mbH3 = self._marginHead3[1]
        mtH4 = self._marginHead4[0]
        mbH4 = self._marginHead4[1]
        mtTT = self._marginText[0]
        mbTT = self._marginText[1]
        mtSP = self._marginSep[0]
        mbSP = self._marginSep[1]

        fSz0 = self._sizeTitle
        fSz1 = self._sizeHead1
        fSz2 = self._sizeHead2
        fSz3 = self._sizeHead3
        fSz4 = self._sizeHead4

        font = self._textFont
        fFam = font.family()
        fSz = font.pointSize()
        fW = FONT_WEIGHTS.get(font.weight(), 400)
        hW = FONT_WEIGHTS.get(700 if self._boldHeads else 400, 400)
        fS = FONT_STYLE.get(font.style(), "normal")

        lHeight = round(100 * self._lineHeight)

        return self._cssBuilder({
            "body": {
                "color": tColor,
                "font-family": f"'{fFam}'",
                "font-size": f"{fSz}pt",
                "font-weight": fW,
                "font-style": fS,
            },
            "p": {
                "text-align": self._defaultAlign,
                "line-height": f"{lHeight}%",
                "margin-top": f"{mtTT:.2f}em",
                "margin-bottom": f"{mbTT:.2f}em",
            },
            "a": {
                "color": lColor,
            },
            "mark": {
                "background": mColor,
            },
            "hr": {
                "width": "50%",
                "color": cColor,
                "margin": f"{mtSP:.2f}em auto {mbSP:.2f}em auto",
            },
            "h1, h2, h3, h4": {
                "color": hColor,
                "page-break-after": "avoid",
            },
            "h1": {
                "font-size": f"{fSz1:.2f}em",
                "font-weight": f"{hW}",
                "margin-top": f"{mtH1:.2f}em",
                "margin-bottom": f"{mbH1:.2f}em",
            },
            "h2": {
                "font-size": f"{fSz2:.2f}em",
                "font-weight": f"{hW}",
                "margin-top": f"{mtH2:.2f}em",
                "margin-bottom": f"{mbH2:.2f}em",
            },
            "h3": {
                "font-size": f"{fSz3:.2f}em",
                "font-weight": f"{hW}",
                "margin-top": f"{mtH3:.2f}em",
                "margin-bottom": f"{mbH3:.2f}em",
            },
            "h4": {
                "font-size": f"{fSz4:.2f}em",
                "font-weight": f"{hW}",
                "margin-top": f"{mtH4:.2f}em",
                "margin-bottom": f"{mbH4:.2f}em",
            },
            ".title": {
                "font-size": f"{fSz0:.2f}em",
                "font-weight": f"{hW}",
                "margin-top": f"{mtH0:.2f}em",
                "margin-bottom": f"{mbH0:.2f}em",
            },
            ".sep": {
                "text-align": "center",
                "margin-top": f"{mtSP:.2f}em",
                "margin-bottom": f"{mbSP:.2f}em",
            },
        })

    def _genFootnoteReferences(self, key: str) -> str:
        """Generate footnote references in the text."""
        index = len(self._usedNotes) + 1
        self._usedNotes[key] = index
        return f"<sup><a href='#footnote_{index}'>{index}</a></sup>"

    ##
    #  Protected Functions (Shared with EPub)
    ##

    def _genInlineStyles(self, tStyle: BlockFmt) -> str:
        """Generate inline styles for a block of text."""
        aStyle = []
        if tStyle & BlockFmt.LEFT:
            aStyle.append("text-align: left;")
        elif tStyle & BlockFmt.RIGHT:
            aStyle.append("text-align: right;")
        elif tStyle & BlockFmt.CENTRE:
            aStyle.append("text-align: center;")
        elif tStyle & BlockFmt.JUSTIFY:
            aStyle.append("text-align: justify;")

        if tStyle & BlockFmt.PBB:
            aStyle.append("page-break-before: always;")
        if tStyle & BlockFmt.PBA:
            aStyle.append("page-break-after: always;")

        if tStyle & BlockFmt.Z_BTM:
            aStyle.append("margin-bottom: 0;")
        if tStyle & BlockFmt.Z_TOP:
            aStyle.append("margin-top: 0;")

        if tStyle & BlockFmt.IND_L:
            aStyle.append(f"margin-left: {self._blockIndent:.2f}em;")
        if tStyle & BlockFmt.IND_R:
            aStyle.append(f"margin-right: {self._blockIndent:.2f}em;")
        if tStyle & BlockFmt.IND_T:
            aStyle.append(f"text-indent: {self._firstWidth:.2f}em;")

        hStyle = ""
        if aStyle:
            stVals = " ".join(aStyle)
            hStyle = f" style='{stVals}'"

        return hStyle

    def _formatText(self, text: str, tFmt: T_Formats) -> str:
        """Apply formatting tags to text."""
        temp = text

        # Build a list of all html tags that need to be inserted in the text.
        # This is done in the forward direction, and a tag is only opened if it
        # isn't already open, and only closed if it has previously been opened.
        tags: list[tuple[int, str]] = []
        state = dict.fromkeys(HTML_OPENER, False)
        plain = not self._cssStyles
        for pos, fmt, data in tFmt:
            if plain and fmt in (TextFmt.COL_B, TextFmt.COL_E):
                # We ignore colour tags if CSS is off
                continue
            if m := HTML_OPENER.get(fmt):
                if not state.get(fmt, True):
                    if fmt == TextFmt.COL_B and (color := self._classes.get(data)):
                        tags.append((pos, m[1].format(color.name(QtHexRgb))))
                    elif fmt in (TextFmt.ANM_B, TextFmt.ARF_B, TextFmt.HRF_B):
                        tags.append((pos, m[1].format(data or "#")))
                    else:
                        tags.append((pos, m[1]))
                    state[fmt] = True
            elif m := HTML_CLOSER.get(fmt):
                if state.get(m[0], False):
                    tags.append((pos, m[1]))
                    state[m[0]] = False
            elif fmt == TextFmt.FNOTE:
                if data in self._footnotes:
                    tags.append((pos, self._genFootnoteReferences(data)))
                else:
                    tags.append((pos, "<sup>ERR</sup>"))
            elif fmt == TextFmt.FIELD and (field := data.partition(":")[2]):
                self._usedFields.append((len(self._pages), field))
                tags.append((pos, f"{{{{{field}}}}}"))

        # Check all format types and close any tag that is still open. This
        # ensures that unclosed tags don't spill over to the next paragraph.
        end = len(text)
        for opener, active in state.items():
            if active:
                closer = HTML_OPENER.get(opener, HTML_NONE)[0]
                tags.append((end, HTML_CLOSER.get(closer, HTML_NONE)[1]))

        # Insert all tags at their correct position, starting from the back.
        # The reverse order ensures that the positions are not shifted while we
        # insert tags.
        for pos, tag in reversed(tags):
            temp = f"{temp[:pos]}{tag}{temp[pos:]}"

        # Replace all line breaks with proper HTML break tags
        temp = temp.replace("\n", self._brTag)

        return stripEscape(temp)

    def _processHtmlEntities(self, text: str, fmt: T_Formats) -> tuple[str, T_Formats]:
        """Replace < and > with HTML entities."""
        # Replace < and > with HTML entities
        if fmt:
            # If we have formatting, we must recompute the locations
            temp = []
            i = 0
            for c in text:
                if c == "<":
                    temp.append("&lt;")
                    fmt = [(p + 3 if p > i else p, f, k) for p, f, k in fmt]
                    i += 4
                elif c == ">":
                    temp.append("&gt;")
                    fmt = [(p + 3 if p > i else p, f, k) for p, f, k in fmt]
                    i += 4
                else:
                    temp.append(c)
                    i += 1
            text = "".join(temp)
        else:
            # If we don't have formatting, we can do a plain replace
            text = text.replace("<", "&lt;").replace(">", "&gt;")

        return text, fmt

    def _cssBuilder(self, styles: dict[str, dict[str, str | int]], compact: bool = True) -> list[str]:
        """Build a CSS style string from a dictionary of style properties."""
        blocks = []
        for selector, values in styles.items():
            br = "" if compact else "\n"
            ind = "" if compact else "  "
            sep = "; " if compact else ";\n"
            content = sep.join(f"{ind}{k}: {v}" for k, v in values.items())
            blocks.append(f"{selector} {{{br}{content.rstrip(' ')}{br}}}")
        return blocks
