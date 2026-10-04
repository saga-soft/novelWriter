"""
novelWriter - GUI Syntax Highlighter
====================================

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

import logging
import re

from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QSyntaxHighlighter, QTextCharFormat, QTextDocument

from novelwriter import CONFIG, SHARED
from novelwriter.common import checkInt, utf16CharMap
from novelwriter.constants import nwUnicode
from novelwriter.editor.textblock import T_TextMetaList, TextBlockData
from novelwriter.enum import nwComment
from novelwriter.text.formats import processComment
from novelwriter.text.patterns import REGEX_PATTERNS, DialogParser
from novelwriter.types import QtFontBold, QtTextUserProperty

if TYPE_CHECKING:
    from novelwriter.editor.editordocument import GuiTextDocument

logger = logging.getLogger(__name__)


BLOCK_NONE = 0
BLOCK_TEXT = 1
BLOCK_META = 2
BLOCK_TITLE = 4

MAX_BLOCK_LENGTH = 20000


class GuiDocHighlighter(QSyntaxHighlighter):
    """GUI: Editor Syntax Highlighter."""

    __slots__ = (
        "_cmnRules",
        "_dialogParser",
        "_hStyles",
        "_isInactive",
        "_isNovel",
        "_minRules",
        "_tHandle",
        "_txtRules",
    )

    def __init__(self, document: QTextDocument) -> None:
        super().__init__(document)

        logger.debug("Create: GuiDocHighlighter")

        self._tHandle = None
        self._isNovel = False
        self._isInactive = False

        self._hStyles: dict[str, QTextCharFormat] = {}
        self._minRules: list[tuple[re.Pattern, dict[int, QTextCharFormat]]] = []
        self._txtRules: list[tuple[re.Pattern, dict[int, QTextCharFormat]]] = []
        self._cmnRules: list[tuple[re.Pattern, dict[int, QTextCharFormat]]] = []

        self._dialogParser = DialogParser()

        self.initHighlighter()

        logger.debug("Ready: GuiDocHighlighter")

    def initHighlighter(self) -> None:
        """Initialise the syntax highlighter, setting all the colour
        rules and building the RegExes.
        """
        logger.debug("Setting up highlighting rules")
        syntax = SHARED.theme.syntaxTheme

        colEmph = syntax.emph if CONFIG.highlightEmph else None
        fmtCodes = "dot" if CONFIG.dottedModCodes else ""

        # Map to Qt's fixed relative font sizes for heading
        h1Size = 4 if CONFIG.scaleHeadings else None
        h2Size = 3 if CONFIG.scaleHeadings else None
        h3Size = 2 if CONFIG.scaleHeadings else None
        h4Size = 1 if CONFIG.scaleHeadings else None

        # Create Character Formats
        self._addCharFormat("text", syntax.text)
        self._addCharFormat("header1", syntax.head, "b", h1Size)
        self._addCharFormat("header2", syntax.head, "b", h2Size)
        self._addCharFormat("header3", syntax.head, "b", h3Size)
        self._addCharFormat("header4", syntax.head, "b", h4Size)
        self._addCharFormat("head1h", syntax.headH, "b", h1Size)
        self._addCharFormat("head2h", syntax.headH, "b", h2Size)
        self._addCharFormat("head3h", syntax.headH, "b", h3Size)
        self._addCharFormat("head4h", syntax.headH, "b", h4Size)
        self._addCharFormat("bold", colEmph, "b")
        self._addCharFormat("italic", colEmph, "i")
        self._addCharFormat("strike", syntax.hidden, "s")
        self._addCharFormat("mark", syntax.mark, "bg")
        self._addCharFormat("nobreak", syntax.space, "bg")
        self._addCharFormat("altdialog", syntax.dialA)
        self._addCharFormat("dialog", syntax.dialN)
        self._addCharFormat("replace", syntax.repTag, fmtCodes)
        self._addCharFormat("hidden", syntax.hidden)
        self._addCharFormat("markup", syntax.hidden)
        self._addCharFormat("link", syntax.link, "u")
        self._addCharFormat("note", syntax.note)
        self._addCharFormat("code", syntax.code, fmtCodes)
        self._addCharFormat("keyword", syntax.key)
        self._addCharFormat("tag", syntax.tag, "u")
        self._addCharFormat("modifier", syntax.mod, fmtCodes)
        self._addCharFormat("value", syntax.val, fmtCodes)
        self._addCharFormat("optional", syntax.opt)
        self._addCharFormat("invalid", None, "err")

        self._txtRules.clear()
        self._cmnRules.clear()

        self._dialogParser.initParser()

        # Non-Breaking Spaces
        rxRule = re.compile(f"[{nwUnicode.U_NBSP}{nwUnicode.U_THNBSP}]+")
        hlRule = {
            0: self._hStyles["nobreak"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Alt Dialogue
        if rxRule := REGEX_PATTERNS.altDialogStyle:
            hlRule = {
                0: self._hStyles["altdialog"],
            }
            self._txtRules.append((rxRule, hlRule))

        # Markdown Italic
        rxRule = REGEX_PATTERNS.markdownItalic
        hlRule = {
            1: self._hStyles["markup"],
            2: self._hStyles["italic"],
            3: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Markdown Bold
        rxRule = REGEX_PATTERNS.markdownBold
        hlRule = {
            1: self._hStyles["markup"],
            2: self._hStyles["bold"],
            3: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Markdown Strikethrough
        rxRule = REGEX_PATTERNS.markdownStrike
        hlRule = {
            1: self._hStyles["markup"],
            2: self._hStyles["strike"],
            3: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Markdown Highlight
        rxRule = REGEX_PATTERNS.markdownMark
        hlRule = {
            1: self._hStyles["markup"],
            2: self._hStyles["mark"],
            3: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Markdown Link
        rxRule = REGEX_PATTERNS.markdownLink
        hlRule = {
            1: self._hStyles["markup"],
            2: self._hStyles["value"],
            3: self._hStyles["markup"],
            4: self._hStyles["link"],
            5: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Shortcodes
        rxRule = REGEX_PATTERNS.shortcodePlain
        hlRule = {
            1: self._hStyles["code"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Shortcodes w/Value
        rxRule = REGEX_PATTERNS.shortcodeValue
        hlRule = {
            1: self._hStyles["code"],
            2: self._hStyles["value"],
            3: self._hStyles["code"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # URLs
        rxRule = REGEX_PATTERNS.url
        hlRule = {
            0: self._hStyles["link"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

        # Alignment Tags
        rxRule = re.compile(r"(^>{1,2}|<{1,2}$)")
        hlRule = {
            1: self._hStyles["markup"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))

        # Auto-Replace Tags
        rxRule = re.compile(r"<(\S+?)>")
        hlRule = {
            0: self._hStyles["replace"],
        }
        self._minRules.append((rxRule, hlRule))
        self._txtRules.append((rxRule, hlRule))
        self._cmnRules.append((rxRule, hlRule))

    ##
    #  Setters
    ##

    def setHandle(self, tHandle: str) -> None:
        """Set the handle of the currently highlighted document."""
        self._tHandle = tHandle
        self._isNovel = False
        self._isInactive = False
        if item := SHARED.project.tree[tHandle]:
            self._isNovel = item.isDocumentLayout()
            self._isInactive = item.isInactiveClass()
        logger.debug("Syntax highlighter enabled for item '%s'", tHandle)

    ##
    #  Methods
    ##

    def rehighlight(self) -> None:
        """Mark the document layout busy before a full rehighlight."""
        doc: GuiTextDocument = self.document()  # type: ignore[assignment]
        if hasattr(doc, "markLayoutBusy"):
            doc.markLayoutBusy()
        super().rehighlight()

    def rehighlightByType(self, cType: int) -> None:
        """Loop through all blocks and re-highlight those of a given
        content type.
        """
        if document := self.document():  # pragma: no branch
            tStart = time()
            block = document.begin()
            while block.isValid():
                if block.userState() & cType > 0:
                    self.rehighlightBlock(block)
                block = block.next()
            logger.debug("Document highlighted in %.3f ms", (1000 * (time() - tStart)))

    ##
    #  Highlight Block
    ##

    def highlightBlock(self, text: str) -> None:
        """Highlight a single block. Prefer to check first character for
        all formats that are defined by their initial characters. This
        is significantly faster than running the regex checks used for
        text paragraphs.
        """
        self.setCurrentBlockState(BLOCK_NONE)
        if self._tHandle is None or not text:
            self._clearBlockData()
            return

        origLen = len(text)
        blockLen = self.currentBlock().length()
        if origLen > MAX_BLOCK_LENGTH:
            text = text[:MAX_BLOCK_LENGTH]

        utf16Map = None
        if blockLen > origLen + 1:
            # If the lengths are different, the line contains 4 byte
            # Unicode characters, and we must use a map between Python
            # string indices and the UTF-16 indices used by Qt, where a
            # 4 byte character occupies two slots. See #2449.
            utf16Map = utf16CharMap(text)

        offset = 0
        rules = None
        if text.startswith("@"):  # Keywords and commands
            self.setCurrentBlockState(BLOCK_META)
            index = SHARED.project.index
            isValid, bits, loc = index.scanThis(text)
            isGood = index.checkThese(bits, self._tHandle)
            meta: T_TextMetaList = []
            if isValid:
                for n, bit in enumerate(bits):
                    pos = utf16Map[loc[n]] if utf16Map else loc[n]
                    length = utf16Map[loc[n] + len(bit)] - pos if utf16Map else len(bit)
                    if n == 0 and isGood[n]:
                        self.setFormat(pos, length, self._hStyles["keyword"])
                    elif isGood[n] and not self._isInactive:
                        a, b = index.parseValue(bit)
                        aLen = utf16Map[loc[n] + len(a)] - pos if utf16Map else len(a)
                        self.setFormat(pos, aLen, self._hStyles["tag"])
                        meta.append((pos, pos + aLen, a, "tag"))
                        if b:
                            bLen = utf16Map[loc[n] + len(b)] - pos if utf16Map else len(b)
                            self.setFormat(pos + length - bLen, bLen, self._hStyles["optional"])
                    elif not self._isInactive:
                        self.setFormat(pos, length, self._hStyles["invalid"])

            # We never want to run the spell checker on keyword/values,
            # so we clear the cached check text and force a return here,
            # but the tag positions are kept for the hover card
            data = self.currentBlockUserData()
            if not isinstance(data, TextBlockData):
                data = TextBlockData()
                self.setCurrentBlockUserData(data)
            data.clear()
            data.setMetaData(meta)
            return

        elif text.startswith(("# ", "#! ", "## ", "##! ", "### ", "###! ", "#### ")):
            self.setCurrentBlockState(BLOCK_TITLE)

            if text.startswith("# "):  # Heading 1
                self.setFormat(0, 1, self._hStyles["head1h"])
                self.setFormat(1, blockLen, self._hStyles["header1"])

            elif text.startswith("## "):  # Heading 2
                self.setFormat(0, 2, self._hStyles["head2h"])
                self.setFormat(2, blockLen, self._hStyles["header2"])

            elif text.startswith("### "):  # Heading 3
                self.setFormat(0, 3, self._hStyles["head3h"])
                self.setFormat(3, blockLen, self._hStyles["header3"])

            elif text.startswith("#### "):  # Heading 4
                self.setFormat(0, 4, self._hStyles["head4h"])
                self.setFormat(4, blockLen, self._hStyles["header4"])

            elif text.startswith("#! "):  # Title
                self.setFormat(0, 2, self._hStyles["head1h"])
                self.setFormat(2, blockLen, self._hStyles["header1"])

            elif text.startswith("##! "):  # Unnumbered
                self.setFormat(0, 3, self._hStyles["head2h"])
                self.setFormat(3, blockLen, self._hStyles["header2"])

            elif text.startswith("###! "):  # Alternative Scene
                self.setFormat(0, 4, self._hStyles["head3h"])
                self.setFormat(4, blockLen, self._hStyles["header3"])

            else:  # pragma: no cover
                pass

        elif text.startswith("%"):  # Comments
            self.setCurrentBlockState(BLOCK_TEXT)
            rules = self._cmnRules

            style, mod, _, dot, pos = processComment(text)
            offset = pos
            if utf16Map:
                dot = utf16Map[dot]
                pos = utf16Map[pos]
            length = blockLen - pos
            if style == nwComment.PLAIN:
                self.setFormat(0, length, self._hStyles["hidden"])
            elif style == nwComment.IGNORE:
                self.setFormat(0, length, self._hStyles["strike"])
                self._clearBlockData()
                return  # No more processing for these
            elif mod:
                self.setFormat(0, dot, self._hStyles["modifier"])
                self.setFormat(dot, pos - dot, self._hStyles["value"])
                self.setFormat(pos, length, self._hStyles["note"])
            else:
                self.setFormat(0, pos, self._hStyles["modifier"])
                self.setFormat(pos, length, self._hStyles["note"])

        elif text.startswith("["):  # Special Command
            self.setCurrentBlockState(BLOCK_TEXT)
            rules = self._txtRules if self._isNovel else self._minRules

            check = text.rstrip().lower()
            if check in ("[newpage]", "[new page]", "[vspace]"):
                self.setFormat(0, blockLen, self._hStyles["code"])
                self._clearBlockData()
                return
            elif check.startswith("[vspace:") and check.endswith("]"):
                value = checkInt(check[8:-1], 0)
                style = "value" if value > 0 else "invalid"
                self.setFormat(0, 8, self._hStyles["code"])
                self.setFormat(8, blockLen - 10, self._hStyles[style])
                self.setFormat(blockLen - 2, blockLen, self._hStyles["code"])
                self._clearBlockData()
                return

        else:  # Text Paragraph
            self.setCurrentBlockState(BLOCK_TEXT)
            rules = self._txtRules if self._isNovel else self._minRules
            if self._isNovel and self._dialogParser.enabled:
                if utf16Map:
                    for pos, end in self._dialogParser(text):
                        pos = utf16Map[pos]
                        end = utf16Map[end]
                        self.setFormat(pos, end - pos, self._hStyles["dialog"])
                else:
                    for pos, end in self._dialogParser(text):
                        self.setFormat(pos, end - pos, self._hStyles["dialog"])

        if rules:
            if utf16Map:
                for rX, hRule in rules:
                    for res in re.finditer(rX, text[offset:]):
                        for x, hFmt in hRule.items():
                            pos = res.start(x) + offset
                            end = res.end(x) + offset
                            for x in range(pos, end):
                                m = utf16Map[x]
                                cFmt = self.format(m)
                                if not cFmt.property(QtTextUserProperty):
                                    cFmt.merge(hFmt)
                                    self.setFormat(m, utf16Map[x + 1] - m, cFmt)
            else:
                for rX, hRule in rules:
                    for res in re.finditer(rX, text[offset:]):
                        for x, hFmt in hRule.items():
                            pos = res.start(x) + offset
                            end = res.end(x) + offset
                            for x in range(pos, end):
                                cFmt = self.format(x)
                                if not cFmt.property(QtTextUserProperty):
                                    cFmt.merge(hFmt)
                                    self.setFormat(x, 1, cFmt)

        data = self.currentBlockUserData()
        if not isinstance(data, TextBlockData):
            data = TextBlockData()
            self.setCurrentBlockUserData(data)

        data.processText(text, offset, utf16Map)

        return

    ##
    #  Internal Functions
    ##

    def _clearBlockData(self) -> None:
        """Clear the cached user data of the current block."""
        if isinstance(data := self.currentBlockUserData(), TextBlockData):
            data.clear()

    def _addCharFormat(
        self,
        name: str,
        color: QColor | None = None,
        style: str | None = None,
        size: int | None = None,
    ) -> None:
        """Generate a highlighter character format."""
        charFormat = QTextCharFormat()
        blockMerge = name == "markup"
        charFormat.setProperty(QtTextUserProperty, blockMerge)

        if style:
            styles = style.split(",")
            if "b" in styles:
                charFormat.setFontWeight(QtFontBold)
            if "i" in styles:
                charFormat.setFontItalic(True)
            if "u" in styles:
                charFormat.setFontUnderline(True)
            if "s" in styles:
                charFormat.setFontStrikeOut(True)
            if "dot" in styles:
                charFormat.setUnderlineStyle(QTextCharFormat.UnderlineStyle.DotLine)
            if "err" in styles:
                charFormat.setUnderlineColor(SHARED.theme.syntaxTheme.error)
                charFormat.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)
            if "bg" in styles and color is not None:
                charFormat.setBackground(QBrush(color, Qt.BrushStyle.SolidPattern))
                color = None

        if color:
            charFormat.setForeground(color)

        if size is not None:
            charFormat.setProperty(QTextCharFormat.Property.FontSizeAdjustment, size)

        self._hStyles[name] = charFormat
