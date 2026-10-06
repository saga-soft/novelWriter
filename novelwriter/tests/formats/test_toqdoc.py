"""
novelWriter - QTextDocument Format Tests
========================================

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

import pytest

from PyQt6.QtGui import QTextBlock, QTextCharFormat, QTextCursor, QTextFormat, QTextLength

from novelwriter import CONFIG
from novelwriter.constants import nwHeadFmt, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp, TextDocumentTheme
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.types import (
    QtAlignAbsolute,
    QtAlignCenter,
    QtAlignJustify,
    QtAlignLeft,
    QtAlignRight,
    QtFontBold,
    QtMoveEnd,
    QtPageBreakAfter,
    QtPageBreakAuto,
    QtPageBreakBefore,
    QtTransparent,
    QtVAlignNormal,
    QtVAlignSub,
    QtVAlignSuper,
)

THEME = TextDocumentTheme()


def charFmtInBlock(block: QTextBlock, pos: int) -> QTextCharFormat:
    """Get the character format at a given place in a block."""
    cursor = QTextCursor(block)
    cursor.setPosition(block.position() + pos)
    return cursor.charFormat()


@pytest.mark.core
def testToQTextDocument_ConvertHeaders(mockGUI):
    """Test header formats in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True

    # Add a line break in chapter header format, see #2415
    doc.setChapterFormat(f"{nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")

    # Populate
    doc._text = "#! Title\n# Partition\n## Chapter\n### Scene\n#### Section\n"
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 6

    # Title
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Title"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakAuto  # Expected on first title
    assert bFmt.topMargin() == doc._mHead[BlockTyp.TITLE][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.TITLE][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.TITLE]
    assert cFmt.foreground().color() == THEME.text

    # Partition
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Partition"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mHead[BlockTyp.PART][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.PART][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.PART]
    assert cFmt.foreground().color() == THEME.head

    # Chapter, Line 1
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "1"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakBefore
    assert bFmt.topMargin() == doc._mHead[BlockTyp.HEAD1][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.HEAD1][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.HEAD1]
    assert cFmt.foreground().color() == THEME.head

    # Chapter, Line 2
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "Chapter"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakAuto  # Important! See #2415
    assert bFmt.topMargin() == doc._mHead[BlockTyp.HEAD1][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.HEAD1][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.HEAD1]
    assert cFmt.foreground().color() == THEME.head

    # Scene
    block = doc.document.findBlockByNumber(4)
    assert block.text() == "Scene"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakAuto
    assert bFmt.topMargin() == doc._mHead[BlockTyp.HEAD2][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.HEAD2][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.HEAD2]
    assert cFmt.foreground().color() == THEME.head

    # Section
    block = doc.document.findBlockByNumber(5)
    assert block.text() == "Section"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakAuto
    assert bFmt.topMargin() == doc._mHead[BlockTyp.HEAD3][0]
    assert bFmt.bottomMargin() == doc._mHead[BlockTyp.HEAD3][1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == QtFontBold
    assert cFmt.fontPointSize() == doc._sHead[BlockTyp.HEAD3]
    assert cFmt.foreground().color() == THEME.head


@pytest.mark.core
def testToQTextDocument_SeparatorSkip(mockGUI):
    """Test separator and skip in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True
    doc._text = "#! Title\n## Chapter\n### Scene 1\nText 1\n### Scene 2\nText 2\n#### Section\nText 3\n"
    doc.setSceneFormat("* * *", False)
    doc.setSectionFormat("", False)
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 7

    # 0: Title
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Title"

    # 1: Chapter
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Chapter"

    # Hidden: Scene 1

    # 2: Text 1
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "Text 1"

    # 3: Scene 2
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "* * *"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mSep[0]
    assert bFmt.bottomMargin() == doc._mSep[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.text

    # 4: Text 2
    block = doc.document.findBlockByNumber(4)
    assert block.text() == "Text 2"

    # 5: Section
    block = doc.document.findBlockByNumber(5)
    assert block.text() == nwUnicode.U_NBSP
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mText[0]
    assert bFmt.bottomMargin() == doc._mText[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.text

    # 6: Text 3
    block = doc.document.findBlockByNumber(6)
    assert block.text() == "Text 3"


@pytest.mark.core
def testToQTextDocument_HorizontalRule(mockGUI):
    """Test horizontal rule helper in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True
    doc._text = "#! Title\n## Chapter\n### Scene 1\nText 1\n### Scene 2\nText 2\n#### Section\nText 3\n"
    doc.setSceneFormat(nwHeadFmt.HRULE, False)
    doc.setSectionFormat("", False)
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 7

    cursor = QTextCursor(doc.document)
    cursor.movePosition(QtMoveEnd)
    doc._insertHorizontalRule(cursor)

    block = doc.document.findBlockByNumber(3)
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignCenter
    assert bFmt.hasProperty(QTextFormat.Property.BlockTrailingHorizontalRulerWidth)

    width = bFmt.lengthProperty(QTextFormat.Property.BlockTrailingHorizontalRulerWidth)
    assert width.type() == QTextLength.Type.PercentageLength
    assert width.rawValue() == pytest.approx(50.0)


@pytest.mark.core
def testToQTextDocument_NovelMeta(mockGUI):
    """Test novel meta formats in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True
    doc.setCommentType(nwComment.PLAIN, True)
    doc.setCommentType(nwComment.SYNOPSIS, True)
    doc.setKeywords(True)
    doc._text = (
        "### Scene\n\n@pov: Jane\n@char: John, Bob\n\n%Synopsis: Stuff that happened\n\n% A regular comment\n\nText\n\n"
    )
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 6

    # 0: Scene
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Scene"

    # 1: Jane
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Point of View: Jane"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mMeta[0]
    assert bFmt.bottomMargin() == 0.0
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.keyword
    cFmt = charFmtInBlock(block, 16)
    assert cFmt.foreground().color() == THEME.tag

    # 2: John, Bob
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "Characters: John, Bob"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == 0.0
    assert bFmt.bottomMargin() == doc._mMeta[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.keyword
    cFmt = charFmtInBlock(block, 13)
    assert cFmt.foreground().color() == THEME.tag

    # 3: Synopsis
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "Synopsis: Stuff that happened"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mText[0]
    assert bFmt.bottomMargin() == doc._mText[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.modifier
    cFmt = charFmtInBlock(block, 11)
    assert cFmt.foreground().color() == THEME.note

    # 4: Comment
    block = doc.document.findBlockByNumber(4)
    assert block.text() == "Comment: A regular comment"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mText[0]
    assert bFmt.bottomMargin() == doc._mText[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.comment
    cFmt = charFmtInBlock(block, 10)
    assert cFmt.foreground().color() == THEME.comment

    # 5: Text
    block = doc.document.findBlockByNumber(5)
    assert block.text() == "Text"


@pytest.mark.core
def testToQTextDocument_NoteMeta(mockGUI):
    """Test note meta formats in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = False
    doc._isFirst = True
    doc.setCommentType(nwComment.PLAIN, True)
    doc.setCommentType(nwComment.SHORT, True)
    doc.setKeywords(True)
    doc._text = "# Jane Smith\n\n@tag: Jane | Jane Smith\n%Short: All about Jane\n\nText\n\n"
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 4

    # 0: Title
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Jane Smith"

    # 1: Tag
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Tag: Jane | Jane Smith"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mMeta[0]
    assert bFmt.bottomMargin() == doc._mMeta[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.keyword
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.foreground().color() == THEME.tag
    cFmt = charFmtInBlock(block, 11)
    assert cFmt.foreground().color() == THEME.text
    cFmt = charFmtInBlock(block, 13)
    assert cFmt.foreground().color() == THEME.optional

    # 2: Short
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "Short Description: All about Jane"
    bFmt = block.blockFormat()
    assert bFmt.topMargin() == doc._mText[0]
    assert bFmt.bottomMargin() == doc._mText[1]
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground().color() == THEME.modifier
    cFmt = charFmtInBlock(block, 20)
    assert cFmt.foreground().color() == THEME.note

    # 3: Text
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "Text"


@pytest.mark.core
def testToQTextDocument_TextBlockFormats(mockGUI):
    """Test text block formats in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.setFirstLineIndent(True, 2.0, False)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True

    # Alignment & Indent
    # ==================
    doc.document.clear()

    doc._text = (
        "### Scene\n\n"
        "Left <<\n\n"
        ">> Center <<\n\n"
        ">> Right\n\n"
        "> Left Indent\n\n"
        "Right Indent <\n\n"
        "> Double Indent <\n\n"
        "Text Indent\n\n"
    )
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 8

    # 0: Scene
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Scene"

    # 1: Left
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Left"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignLeft

    # 2: Center
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "Center"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignCenter

    # 3: Right
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "Right"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignRight

    # 4: Left Indent
    block = doc.document.findBlockByNumber(4)
    assert block.text() == "Left Indent"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignAbsolute
    assert bFmt.leftMargin() == doc._mIndent
    assert bFmt.rightMargin() == 0.0

    # 5: Right Indent
    block = doc.document.findBlockByNumber(5)
    assert block.text() == "Right Indent"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignAbsolute
    assert bFmt.leftMargin() == 0.0
    assert bFmt.rightMargin() == doc._mIndent

    # 6: Double Indent
    block = doc.document.findBlockByNumber(6)
    assert block.text() == "Double Indent"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignAbsolute
    assert bFmt.leftMargin() == doc._mIndent
    assert bFmt.rightMargin() == doc._mIndent

    # 7: Text Indent
    block = doc.document.findBlockByNumber(7)
    assert block.text() == "Text Indent"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignAbsolute
    assert bFmt.textIndent() == doc._tIndent
    assert bFmt.leftMargin() == 0.0
    assert bFmt.rightMargin() == 0.0

    # Unreachable
    # ===========
    # Some formatting markers are currently not reachable
    doc.document.clear()

    doc._blocks = [
        (BlockTyp.TEXT, "", "This is justified", [], BlockFmt.JUSTIFY),
        (BlockTyp.TEXT, "", "This has a page break", [], BlockFmt.PBA),
    ]
    doc.doConvert()
    assert doc.document.blockCount() == 2

    # 0: Justify
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "This is justified"
    bFmt = block.blockFormat()
    assert bFmt.alignment() == QtAlignJustify

    # 1: Page Break After
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "This has a page break"
    bFmt = block.blockFormat()
    assert bFmt.pageBreakPolicy() == QtPageBreakAfter


@pytest.mark.core
def testToQTextDocument_TextCharFormats(mockGUI):
    """Test text char formats in the ToQTextDocument class."""
    CONFIG.fmtDQuoteOpen = nwUnicode.U_LDQUO
    CONFIG.fmtDQuoteClose = nwUnicode.U_RDQUO
    CONFIG.altDialogOpen = "|<"
    CONFIG.altDialogClose = ">|"

    project = NWProject()
    doc = ToQTextDocument(project)

    # Convert before init
    doc._text = "Blabla"
    doc.setDialogHighlight(True)
    doc.doConvert()
    doc.tokenizeText()
    assert doc.document.toPlainText() == ""

    # Init
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True

    doc._text = (
        "### Scene\n\n"
        "With [b]bold[/b] text\n\n"
        "With [i]italic[/i] text\n\n"
        "With [s]deleted[/s] text\n\n"
        "With [u]underlined[/u] text\n\n"
        "With [m]highlighted[/m] text\n\n"
        "With super[sup]script[/sup] text\n\n"
        "With sub[sub]script[/sub] text\n\n"
        "With \u201cdialog\u201d text\n\n"
        "With |<alternative dialog>| text\n\n"
        "With http://example.com text\n\n"
    )
    doc.tokenizeText()
    doc.doConvert()
    assert doc.document.blockCount() == 11

    # 0: Scene
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Scene"

    # 1: Bold
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "With bold text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontWeight() == doc._dWeight
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.fontWeight() == QtFontBold
    cFmt = charFmtInBlock(block, 10)
    assert cFmt.fontWeight() == doc._dWeight

    # 2: Italic
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "With italic text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontItalic() is False
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.fontItalic() is True
    cFmt = charFmtInBlock(block, 12)
    assert cFmt.fontItalic() is False

    # 3: Deleted
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "With deleted text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontStrikeOut() is False
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.fontStrikeOut() is True
    cFmt = charFmtInBlock(block, 13)
    assert cFmt.fontStrikeOut() is False

    # 4: Underlined
    block = doc.document.findBlockByNumber(4)
    assert block.text() == "With underlined text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.fontUnderline() is False
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.fontUnderline() is True
    cFmt = charFmtInBlock(block, 16)
    assert cFmt.fontUnderline() is False

    # 5: Highlighted
    block = doc.document.findBlockByNumber(5)
    assert block.text() == "With highlighted text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.background() == QtTransparent
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.background() == THEME.highlight
    cFmt = charFmtInBlock(block, 17)
    assert cFmt.background() == QtTransparent

    # 6: Superscript
    block = doc.document.findBlockByNumber(6)
    assert block.text() == "With superscript text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.verticalAlignment() == QtVAlignNormal
    cFmt = charFmtInBlock(block, 11)
    assert cFmt.verticalAlignment() == QtVAlignSuper
    cFmt = charFmtInBlock(block, 17)
    assert cFmt.verticalAlignment() == QtVAlignNormal

    # 7: Subscript
    block = doc.document.findBlockByNumber(7)
    assert block.text() == "With subscript text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.verticalAlignment() == QtVAlignNormal
    cFmt = charFmtInBlock(block, 9)
    assert cFmt.verticalAlignment() == QtVAlignSub
    cFmt = charFmtInBlock(block, 15)
    assert cFmt.verticalAlignment() == QtVAlignNormal

    # 8: Dialogue
    block = doc.document.findBlockByNumber(8)
    assert block.text() == "With \u201cdialog\u201d text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground() == THEME.text
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.foreground() == THEME.dialog
    cFmt = charFmtInBlock(block, 14)
    assert cFmt.foreground() == THEME.text

    # 9: Alt. Dialogue
    block = doc.document.findBlockByNumber(9)
    assert block.text() == "With |<alternative dialog>| text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground() == THEME.text
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.foreground() == THEME.altdialog
    cFmt = charFmtInBlock(block, 28)
    assert cFmt.foreground() == THEME.text

    # 10: Url
    block = doc.document.findBlockByNumber(10)
    assert block.text() == "With http://example.com text"
    cFmt = charFmtInBlock(block, 1)
    assert cFmt.foreground() == THEME.text
    cFmt = charFmtInBlock(block, 6)
    assert cFmt.foreground() == THEME.link
    assert cFmt.isAnchor() is True
    assert cFmt.anchorHref() == "http://example.com"
    cFmt = charFmtInBlock(block, 24)
    assert cFmt.foreground() == THEME.text


@pytest.mark.core
def testToQTextDocument_Footnotes(mockGUI):
    """Test footnotes in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._isNovel = True
    doc._isFirst = True

    doc._text = (
        "### Scene\n\n"
        "Text with valid[footnote:fn1] and invalid[footnote:fn2] footnotes.\n\n"
        "%Footnote.fn1: Here's the first note.[footnote:fn3]\n\n"
        "%Footnote.fn3: This nested footnote is skipped.\n\n"
    )
    doc.tokenizeText()
    doc.doConvert()
    doc.closeDocument()
    assert doc.document.blockCount() == 4

    # 0: Scene
    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Scene"

    # 1: Text
    block = doc.document.findBlockByNumber(1)
    assert block.text() == "Text with valid[1] and invalid[ERR] footnotes."

    # 2: Footnotes
    block = doc.document.findBlockByNumber(2)
    assert block.text() == "Footnotes"

    # 3: Footnote 1, with the nested footnote reference stripped
    block = doc.document.findBlockByNumber(3)
    assert block.text() == "1. Here's the first note."


@pytest.mark.core
def testToQTextDocument_Fields(mockGUI):
    """Test field substitution in the ToQTextDocument class."""
    project = NWProject()
    doc = ToQTextDocument(project)
    doc.initDocument()

    doc._text = "Word Count: [field:allWords], Unknown: [field:unknownField]\n"
    doc.tokenizeText()
    doc.doConvert()
    doc.countStats()
    doc.closeDocument()

    block = doc.document.findBlockByNumber(0)
    assert block.text() == "Word Count: 4, Unknown: 0"
