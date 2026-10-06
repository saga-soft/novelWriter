"""
novelWriter - Open Document Format Tests
========================================

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

import xml.etree.ElementTree as ET
import zipfile

from shutil import copyfile

import pytest

from PyQt6.QtGui import QColor

from novelwriter.common import xmlIndent
from novelwriter.constants import nwHeadFmt
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp, TextFmt
from novelwriter.formats.toodt import (
    X_ROOT_TEXT,
    ODTBorderStyle,
    ODTParagraphStyle,
    ODTTextStyle,
    ToOdt,
    XMLParagraph,
    _mkTag,
)

from tests.helpers import ODT_IGNORE, cmpFiles, xmlToText


@pytest.mark.core
def testToOdt_Init(mockGUI):
    """Test initialisation of the ODT document."""
    project = NWProject()

    # Flat Doc
    # ========

    odt = ToOdt(project, isFlat=True)
    odt.initDocument()

    # Document XML
    assert odt._dFlat.tag == _mkTag("office", "document")
    assert odt._dCont.tag == ""
    assert odt._dMeta.tag == ""
    assert odt._dStyl.tag == ""

    # Content XML
    assert odt._xMeta.tag == _mkTag("office", "meta")
    assert odt._xFont.tag == _mkTag("office", "font-face-decls")
    assert odt._xFnt2.tag == ""
    assert odt._xStyl.tag == _mkTag("office", "styles")
    assert odt._xAuto.tag == _mkTag("office", "automatic-styles")
    assert odt._xAut2.tag == ""
    assert odt._xMast.tag == _mkTag("office", "master-styles")
    assert odt._xBody.tag == _mkTag("office", "body")
    assert odt._xText.tag == _mkTag("office", "text")

    # ODT Doc
    # =======

    odt = ToOdt(project, isFlat=False)
    odt.initDocument()

    # Document XML
    assert odt._dFlat.tag == ""
    assert odt._dCont.tag == _mkTag("office", "document-content")
    assert odt._dMeta.tag == _mkTag("office", "document-meta")
    assert odt._dStyl.tag == _mkTag("office", "document-styles")

    # Content XML
    assert odt._xMeta.tag == _mkTag("office", "meta")
    assert odt._xFont.tag == _mkTag("office", "font-face-decls")
    assert odt._xFnt2.tag == _mkTag("office", "font-face-decls")
    assert odt._xStyl.tag == _mkTag("office", "styles")
    assert odt._xAuto.tag == _mkTag("office", "automatic-styles")
    assert odt._xAut2.tag == _mkTag("office", "automatic-styles")
    assert odt._xMast.tag == _mkTag("office", "master-styles")
    assert odt._xBody.tag == _mkTag("office", "body")
    assert odt._xText.tag == _mkTag("office", "text")


@pytest.mark.core
def testToOdt_TextFormatting(mockGUI):
    """Test formatting of paragraphs."""
    project = NWProject()
    odt = ToOdt(project, isFlat=True)

    odt.initDocument()
    assert xmlToText(odt._xText) == "<office:text />"

    # Paragraph Style
    # ===============
    oStyle = ODTParagraphStyle("test")

    assert odt._paraStyle("stuff", oStyle) == "Standard"
    assert odt._paraStyle("Text_20_body", oStyle) == "Text_20_body"

    # Create new para style
    oStyle.setTextAlign("center")
    assert odt._paraStyle("Text_20_body", oStyle) == "P1"

    # Return the same style on second call
    assert odt._paraStyle("Text_20_body", oStyle) == "P1"

    assert list(odt._mainPara.keys()) == [
        "Text_20_body",
        "First_20_line_20_indent",
        "Text_20_Meta",
        "Title",
        "Separator",
        "Horizontal_20_Line",
        "Heading_20_1",
        "Heading_20_2",
        "Heading_20_3",
        "Heading_20_4",
        "Header",
        "Footnote",
    ]

    key = "3cf442c88e0f5e263fdf225fa4763d6e5d7a1d78e611c24f5e9befef1b7646c9"
    assert key in odt._autoPara
    assert isinstance(odt._autoPara[key], ODTParagraphStyle)
    assert odt._autoPara[key].name == "P1"

    # Paragraph Formatting
    # ====================
    oStyle = ODTParagraphStyle("test")

    # No Text
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, "")
    assert xmlToText(xTest) == ('<office:text><text:p text:style-name="Standard" /></office:text>')

    # No Format
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, "Hello World")
    assert odt.errData == []
    assert xmlToText(xTest) == ('<office:text><text:p text:style-name="Standard">Hello World</text:p></office:text>')

    # Heading Level None
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, "Hello World", isHead=True)
    assert odt.errData == []
    assert xmlToText(xTest) == ('<office:text><text:h text:style-name="Standard">Hello World</text:h></office:text>')

    # Heading Level 1
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, "Hello World", isHead=True, oLevel="1")
    assert odt.errData == []
    assert xmlToText(xTest) == (
        '<office:text><text:h text:style-name="Standard" text:outline-level="1">Hello World</text:h></office:text>'
    )

    # Formatted Text
    text = "A bold word"
    fmt = [(2, TextFmt.B_B, ""), (6, TextFmt.B_E, "")]
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert odt.errData == []
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">A <text:span text:style-name="T1">bold</text:span> '
        "word</text:p>"
        "</office:text>"
    )

    # Incorrectly Formatted Text
    text = "A few words"
    fmt = [(2, TextFmt.B_B, ""), (5, TextFmt.B_E, ""), (7, 99999, "")]
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">A <text:span text:style-name="T1">few</text:span> '
        "words</text:p>"
        "</office:text>"
    )
    odt._errData = []

    # Unclosed format
    text = "A bold word"
    fmt = [(2, TextFmt.B_B, "")]
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert odt.errData == []
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">A '
        '<text:span text:style-name="T1">bold word</text:span></text:p>'
        "</office:text>"
    )

    # Tabs and Breaks
    text = "Hello\n\tWorld"
    fmt = []
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert odt.errData == []
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">Hello<text:line-break /><text:tab />World</text:p>'
        "</office:text>"
    )


@pytest.mark.core
def testToOdt_Fields(mockGUI):
    """Test formatting of footnotes."""
    project = NWProject()
    odt = ToOdt(project, True)
    odt.initDocument()

    # Field Builder
    xNode = odt._generateField("a:allWords", 0x00)
    assert isinstance(xNode, ET.Element)
    assert xmlToText(xNode) == (
        '<text:user-field-getstyle:data-style-name="N0" text:name="ManuscriptAllWords">0</text:user-field-get>'
    )
    # assert odt._usedFields == [(xNode.find(_wTag("t")), "b")]

    assert odt._generateField("a", 0x00) is None

    # Full Processing
    odt._text = "Word Count: [field:allWords]\nCharacter Count: [field:allChars]\nChicken Count: [field:allChickens]\n"
    odt.tokenizeText()
    odt.doConvert()
    odt.countStats()
    assert xmlToText(odt._xBody) == (
        "<office:body><office:text>"
        '<text:p text:style-name="Text_20_body">'
        'Word Count: <text:user-field-get style:data-style-name="N0" '
        'text:name="ManuscriptAllWords">0</text:user-field-get><text:line-break />'
        'Character Count: <text:user-field-get style:data-style-name="N0" '
        'text:name="ManuscriptAllChars">0</text:user-field-get><text:line-break />'
        'Chicken Count: <text:user-field-get style:data-style-name="N0" '
        'text:name="ManuscriptAllChickens">0</text:user-field-get></text:p>'
        "</office:text></office:body>"
    )


@pytest.mark.core
def testToOdt_DialogueFormatting(mockGUI):
    """Test formatting of dialogue."""
    project = NWProject()
    odt = ToOdt(project, isFlat=True)
    odt.setDialogHighlight(True)
    odt.initDocument()
    oStyle = ODTParagraphStyle("test")

    # Regular dialogue
    text = "Text with 'dialogue in it.'"
    fmt = [(10, TextFmt.COL_B, "dialog"), (27, TextFmt.COL_E, "enddialog")]
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert odt.errData == []
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">Text with '
        "<text:span text:style-name=\"T1\">'dialogue in it.'</text:span></text:p>"
        "</office:text>"
    )

    # Alternative dialogue
    text = "Text with ::dialogue in it.::"
    fmt = [(10, TextFmt.COL_B, "altdialog"), (29, TextFmt.COL_E, "endaltdialog")]
    xTest = ET.Element(_mkTag("office", "text"))
    odt._addTextPar(xTest, "Standard", oStyle, text, tFmt=fmt)
    assert odt.errData == []
    assert xmlToText(xTest) == (
        "<office:text>"
        '<text:p text:style-name="Standard">Text with '
        '<text:span text:style-name="T2">::dialogue in it.::</text:span></text:p>'
        "</office:text>"
    )


@pytest.mark.core
def testToOdt_ConvertNovelHeadings(mockGUI):
    """Test the novel heading converter of the ToOdt class."""
    project = NWProject()
    odt = ToOdt(project, isFlat=True)
    odt._isNovel = True

    # Title
    odt._isFirst = True
    odt._text = "#! Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == ('<office:text><text:p text:style-name="Title">Title</text:p></office:text>')

    # Partition
    odt._text = "# Title\n"
    odt.setPartitionFormat(f"Part{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:p text:style-name="P1">Part<text:line-break />Title</text:p></office:text>'
    )

    # Chapter
    odt._text = "## Title\n"
    odt.setChapterFormat(f"Chapter {nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="P2" text:outline-level="1">Chapter 1'
        "<text:line-break />Title</text:h>"
        "</office:text>"
    )

    # Unnumbered Chapter
    odt._text = "##! Prologue\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="P2" text:outline-level="1">Prologue</text:h></office:text>'
    )

    # Scene
    odt._text = "### Title\n"
    odt.setSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene 1'
        "<text:line-break />Title</text:h>"
        "</office:text>"
    )

    # Alt. Scene
    odt._text = "###! Title\n"
    odt.setHardSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene 2'
        "<text:line-break />Title</text:h>"
        "</office:text>"
    )

    # Section
    odt._text = "#### Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="Heading_20_3" text:outline-level="3">Title</text:h></office:text>'
    )


@pytest.mark.core
def testToOdt_ConvertNotesHeadings(mockGUI):
    """Test the notes headings converter of the ToOdt class."""
    project = NWProject()
    odt = ToOdt(project, isFlat=True)
    odt._isNovel = False

    # Heading 1
    odt._text = "# Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="Heading_20_1" text:outline-level="1">Title</text:h></office:text>'
    )

    # Heading 2
    odt._text = "## Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="Heading_20_2" text:outline-level="2">Title</text:h></office:text>'
    )

    # Heading 3
    odt._text = "### Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="Heading_20_3" text:outline-level="3">Title</text:h></office:text>'
    )

    # Heading 4
    odt._text = "#### Title\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        '<office:text><text:h text:style-name="Heading_20_4" text:outline-level="4">Title</text:h></office:text>'
    )


@pytest.mark.core
def testToOdt_ConvertParagraphs(mockGUI):
    """Test the converter of the ToOdt class."""
    project = NWProject()
    odt = ToOdt(project, isFlat=True)
    odt._isNovel = True

    def getStyle(styleName):
        for style in odt._autoPara.values():
            if style.name == styleName:
                return style
        return None

    # Nested Markdown Text
    odt._text = "Some ~~nested **bold** and _italics_ text~~ text."
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some '
        '<text:span text:style-name="T1">nested </text:span>'
        '<text:span text:style-name="T2">bold</text:span>'
        '<text:span text:style-name="T1"> and </text:span>'
        '<text:span text:style-name="T3">italics</text:span>'
        '<text:span text:style-name="T1"> text</text:span> text.</text:p>'
        "</office:text>"
    )

    # Nested Shortcode Text, Emphasis
    odt._text = "Some [s]nested [b]bold[/b] [u]and[/u] [i]italics[/i] text[/s] text."
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some '
        '<text:span text:style-name="T1">nested </text:span>'
        '<text:span text:style-name="T2">bold</text:span>'
        '<text:span text:style-name="T1"> </text:span>'
        '<text:span text:style-name="T4">and</text:span>'
        '<text:span text:style-name="T1"> </text:span>'
        '<text:span text:style-name="T3">italics</text:span>'
        '<text:span text:style-name="T1"> text</text:span> text.</text:p>'
        "</office:text>"
    )

    # Shortcode Text, Super/Subscript
    odt._text = "Some super[sup]script[/sup] and sub[sub]script[/sub] text."
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some '
        'super<text:span text:style-name="T5">script</text:span> and '
        'sub<text:span text:style-name="T6">script</text:span> text.</text:p>'
        "</office:text>"
    )

    # Shortcode Text, Underline/Highlight
    odt._text = "Some [u]underlined and [m]highlighted[/m][/u] text."
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some '
        '<text:span text:style-name="T7">underlined and </text:span>'
        '<text:span text:style-name="T8">highlighted</text:span> text.</text:p>'
        "</office:text>"
    )

    # Hard Break
    odt._text = "Some text.\nNext line\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some text.<text:line-break />Next line</text:p>'
        "</office:text>"
    )

    # Tab
    odt._text = "\tItem 1\tItem 2\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body"><text:tab />Item 1<text:tab />Item 2</text:p>'
        "</office:text>"
    )

    # Tab in Format
    odt._text = "Some **bold\ttext**"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Some <text:span text:style-name="T9">'
        "bold<text:tab />text</text:span></text:p>"
        "</office:text>"
    )

    # Multiple Spaces
    odt._text = "### Scene\n\nHello World\n\nHello  World\n\nHello   World\n\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene</text:h>'
        '<text:p text:style-name="Text_20_body">Hello World</text:p>'
        '<text:p text:style-name="Text_20_body">Hello <text:s />World</text:p>'
        '<text:p text:style-name="Text_20_body">Hello <text:s text:c="2" />World</text:p>'
        "</office:text>"
    )

    # Synopsis, Short, Comment, Keywords
    odt._text = "### Scene\n\n@pov: Jane\n\n% synopsis: So it begins\n\n% short: Then what\n\n% A plain comment\n\n"
    odt.setCommentType(nwComment.SYNOPSIS, True)
    odt.setCommentType(nwComment.SHORT, True)
    odt.setCommentType(nwComment.PLAIN, True)
    odt.setKeywords(True)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene</text:h>'
        '<text:p text:style-name="Text_20_Meta"><text:span text:style-name="T10">'
        'Point of View:</text:span> <text:span text:style-name="T11">Jane</text:span></text:p>'
        '<text:p text:style-name="Text_20_Meta"><text:span text:style-name="T12">'
        "Synopsis:</text:span> "
        '<text:span text:style-name="T13">So it begins</text:span></text:p>'
        '<text:p text:style-name="Text_20_Meta"><text:span text:style-name="T12">'
        "Short Description:</text:span> "
        '<text:span text:style-name="T13">Then what</text:span></text:p>'
        '<text:p text:style-name="Text_20_Meta"><text:span text:style-name="T14">'
        "Comment:</text:span> "
        '<text:span text:style-name="T15">A plain comment</text:span></text:p>'
        "</office:text>"
    )

    # Scene Separator
    odt._text = "### Scene One\n\nText\n\n### Scene Two\n\nText"
    odt.setSceneFormat("* * *", False)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Separator">* * *</text:p>'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        '<text:p text:style-name="Separator">* * *</text:p>'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        "</office:text>"
    )

    # Horizontal Line
    odt._text = "### Scene One\n\nText\n\n### Scene Two\n\nText"
    odt.setSceneFormat(nwHeadFmt.HRULE, False)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Horizontal_20_Line" />'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        '<text:p text:style-name="Horizontal_20_Line" />'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        "</office:text>"
    )

    # Scene Break
    odt._text = "### Scene One\n\nText\n\n### Scene Two\n\nText"
    odt.setSceneFormat("", False)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body" />'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        '<text:p text:style-name="Text_20_body" />'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        "</office:text>"
    )

    # Paragraph Styles
    odt._text = (
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: John\n"
        "@plot: Main\n\n"
        ">> Right align\n\n"
        "Left Align <<\n\n"
        ">> Centered <<\n\n"
        "> Left indent\n\n"
        "Right indent <\n\n"
    )
    odt.setSceneFormat(nwHeadFmt.TITLE, False)
    odt.setKeywords(True)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene</text:h>'
        '<text:p text:style-name="P1"><text:span text:style-name="T10">'
        'Point of View:</text:span> <text:span text:style-name="T11">Jane</text:span></text:p>'
        '<text:p text:style-name="P2"><text:span text:style-name="T10">'
        'Characters:</text:span> <text:span text:style-name="T11">John</text:span></text:p>'
        '<text:p text:style-name="Text_20_Meta"><text:span text:style-name="T10">'
        'Plot:</text:span> <text:span text:style-name="T11">Main</text:span></text:p>'
        '<text:p text:style-name="P3">Right align</text:p>'
        '<text:p text:style-name="Text_20_body">Left Align</text:p>'
        '<text:p text:style-name="P4">Centered</text:p>'
        '<text:p text:style-name="P5">Left indent</text:p>'
        '<text:p text:style-name="P6">Right indent</text:p>'
        "</office:text>"
    )
    assert getStyle("P1")._pAttr["margin-bottom"] == ["fo", "0.000cm"]  # type: ignore
    assert getStyle("P2")._pAttr["margin-bottom"] == ["fo", "0.000cm"]  # type: ignore
    assert getStyle("P2")._pAttr["margin-top"] == ["fo", "0.000cm"]  # type: ignore
    assert getStyle("P3")._pAttr["text-align"] == ["fo", "right"]  # type: ignore
    assert getStyle("P4")._pAttr["text-align"] == ["fo", "center"]  # type: ignore
    assert getStyle("P5")._pAttr["margin-left"] == ["fo", "1.693cm"]  # type: ignore
    assert getStyle("P6")._pAttr["margin-right"] == ["fo", "1.693cm"]  # type: ignore

    # Justified
    odt._text = "### Scene\n\nRegular paragraph\n\nwith\nbreak\n\nLeft Align <<\n\n"
    odt.setJustify(True, False)
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    odt.setJustify(False, False)
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="Heading_20_2" text:outline-level="2">Scene</text:h>'
        '<text:p text:style-name="P7">Regular paragraph</text:p>'
        '<text:p text:style-name="P7">with<text:line-break />break</text:p>'
        '<text:p text:style-name="Text_20_body">Left Align</text:p>'
        "</office:text>"
    )
    assert getStyle("P7")._pAttr["text-align"] == ["fo", "justify"]  # type: ignore

    # Page Breaks
    odt._text = "## Chapter One\n\nText\n\n## Chapter Two\n\nText\n\n"
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:h text:style-name="P8" text:outline-level="1">Chapter One</text:h>'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        '<text:h text:style-name="P8" text:outline-level="1">Chapter Two</text:h>'
        '<text:p text:style-name="Text_20_body">Text</text:p>'
        "</office:text>"
    )

    # Footnotes
    odt._text = (
        "Text with one[footnote:fa], **two**[footnote:fd], "
        "or three[footnote:fb] footnotes.[footnote:fe]\n\n"
        "%footnote.fa: Footnote text A.[footnote:fc]\n\n"
        "%footnote.fc: This footnote is skipped.\n\n"
        "%footnote.fd: Another footnote.\n\n"
        "%footnote.fe: Again?\n\n"
    )
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Text with one'
        '<text:note text:id="ftn1" text:note-class="footnote">'
        "<text:note-citation>1</text:note-citation>"
        "<text:note-body>"
        '<text:p text:style-name="Footnote">Footnote text A.</text:p>'
        "</text:note-body>"
        '</text:note>, <text:span text:style-name="T9">two</text:span>'
        '<text:note text:id="ftn2" text:note-class="footnote">'
        "<text:note-citation>2</text:note-citation>"
        "<text:note-body>"
        '<text:p text:style-name="Footnote">Another footnote.</text:p>'
        "</text:note-body>"
        "</text:note>, or three footnotes."
        '<text:note text:id="ftn3" text:note-class="footnote">'
        "<text:note-citation>3</text:note-citation>"
        "<text:note-body>"
        '<text:p text:style-name="Footnote">Again?</text:p>'
        "</text:note-body>"
        "</text:note></text:p>"
        "</office:text>"
    )

    # Test for issue #1412
    # ====================
    # See #1412

    odt._text = "Test text \\**_bold_** and more."
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.closeDocument()
    assert odt.errData == []
    assert xmlToText(odt._xText) == (
        "<office:text>"
        '<text:p text:style-name="Text_20_body">Test text **<text:span text:style-name="T16">'
        "bold</text:span>** and more.</text:p>"
        "</office:text>"
    )


@pytest.mark.core
def testToOdt_ConvertDirect(mockGUI):
    """Test the converter directly using the ToOdt class to reach some
    otherwise hard to reach conditions.
    """
    project = NWProject()
    doc = ToOdt(project, isFlat=True)

    doc._isNovel = True

    # Justified
    doc = ToOdt(project, isFlat=True)
    doc._blocks = [
        (BlockTyp.TEXT, "", "This is a paragraph", [], BlockFmt.JUSTIFY),
    ]
    doc.initDocument()
    doc.doConvert()
    doc.closeDocument()
    assert (
        '<style:style style:name="P1" style:family="paragraph" '
        'style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:text-align="justify" />'
        "</style:style>"
    ) in xmlToText(doc._xAuto)
    assert xmlToText(doc._xText) == (
        '<office:text><text:p text:style-name="P1">This is a paragraph</text:p></office:text>'
    )

    # Page Break After
    doc = ToOdt(project, isFlat=True)
    doc._blocks = [
        (BlockTyp.TEXT, "", "This is a paragraph", [], BlockFmt.PBA),
    ]
    doc.initDocument()
    doc.doConvert()
    doc.closeDocument()
    assert (
        '<style:style style:name="P1" style:family="paragraph" '
        'style:parent-style-name="Text_20_body">'
        '<style:paragraph-properties fo:break-after="page" />'
        "</style:style>"
    ) in xmlToText(doc._xAuto)
    assert xmlToText(doc._xText) == (
        '<office:text><text:p text:style-name="P1">This is a paragraph</text:p></office:text>'
    )


@pytest.mark.core
def testToOdt_SaveFlat(mockGUI, fncPath, tstPaths, ipsumText):
    """Test the document save functions."""
    project = NWProject()
    project.data.setAuthor("Jane Smith")
    project.data.setName("Test Project")
    project.data.setSaveCount(1234)
    project.data.setEditTime(3674096)

    odt = ToOdt(project, isFlat=True)
    odt._isNovel = True
    odt.setHeaderFormat(nwHeadFmt.DOC_AUTO, 1)
    assert odt._headerFormat == nwHeadFmt.DOC_AUTO

    odt.setPageLayout(148, 210, 20, 18, 17, 15)
    assert odt._mDocWidth == "14.800cm"
    assert odt._mDocHeight == "21.000cm"
    assert odt._mDocTop == "2.000cm"
    assert odt._mDocBtm == "1.800cm"
    assert odt._mDocLeft == "1.700cm"
    assert odt._mDocRight == "1.500cm"

    odt._text = (
        "#! My Novel\n\n"
        "**Word Count: [field:allWords]**\n"
        "[field:paragraphCount] paragrphs\n"
        "Web: http://example.com\n\n"
        "## Chapter One\n\n"
        f"{ipsumText[0]}\n\n"
        "## Chapter Two\n\n"
        f"{ipsumText[1]}[footnote:abc]\n\n"
        "%Footnote.abc: Lorem ipsum\n\n"
    )
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.countStats()
    odt.closeDocument()

    flatFile = fncPath / "document.fodt"
    testFile = tstPaths.outDir / "fmtToOdt_SaveFlat_document.fodt"
    compFile = tstPaths.refDir / "fmtToOdt_SaveFlat_document.fodt"

    odt.saveDocument(flatFile)
    assert flatFile.exists()

    copyfile(flatFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=ODT_IGNORE)


@pytest.mark.core
def testToOdt_SaveFlatWithEmptyLines(mockGUI, fncPath, tstPaths, ipsumText):
    """Test the document save functions."""
    project = NWProject()
    project.data.setAuthor("Jane Smith")
    project.data.setName("Test Project")
    project.data.setSaveCount(1234)
    project.data.setEditTime(3674096)

    odt = ToOdt(project, isFlat=True)
    odt._isNovel = True
    odt.setHeaderFormat(nwHeadFmt.DOC_AUTO, 1)
    odt.setLineForMargin(True)
    odt.setJustify(True, False)
    assert odt._headerFormat == nwHeadFmt.DOC_AUTO

    odt.setPageLayout(148, 210, 20, 18, 17, 15)
    assert odt._mDocWidth == "14.800cm"
    assert odt._mDocHeight == "21.000cm"
    assert odt._mDocTop == "2.000cm"
    assert odt._mDocBtm == "1.800cm"
    assert odt._mDocLeft == "1.700cm"
    assert odt._mDocRight == "1.500cm"

    odt._text = (
        "#! My Novel\n\n"
        "**Word Count: [field:allWords]**\n"
        "[field:paragraphCount] paragrphs\n"
        "Web: http://example.com\n\n"
        "## Chapter One\n\n"
        f"{ipsumText[0]}\n\n"
        "## Chapter Two\n\n"
        f"{ipsumText[1]}[footnote:abc]\n\n"
        "%Footnote.abc: Lorem ipsum\n\n"
    )
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.countStats()
    odt.closeDocument()

    flatFile = fncPath / "document.fodt"
    testFile = tstPaths.outDir / "fmtToOdt_SaveFlatWithEmptyLines_document.fodt"
    compFile = tstPaths.refDir / "fmtToOdt_SaveFlatWithEmptyLines_document.fodt"

    odt.saveDocument(flatFile)
    assert flatFile.exists()

    copyfile(flatFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=ODT_IGNORE)


@pytest.mark.core
def testToOdt_SaveFull(mockGUI, fncPath, tstPaths, ipsumText):
    """Test the document save functions."""
    project = NWProject()
    project.data.setAuthor("Jane Smith")
    project.data.setName("Test Project")
    project.data.setSaveCount(1234)
    project.data.setEditTime(3674096)

    odt = ToOdt(project, isFlat=False)
    odt._isNovel = True

    # Set a format without page number
    odt.setHeaderFormat(f"{nwHeadFmt.DOC_PROJECT} - {nwHeadFmt.DOC_AUTHOR}", 0)

    odt._text = (
        "#! My Novel\n\n"
        "**Word Count: [field:allWords]**\n"
        "[field:paragraphCount] paragrphs\n"
        "Web: http://example.com\n\n"
        "## Chapter One\n\n"
        f"{ipsumText[0]}\n\n"
        "## Chapter Two\n\n"
        f"{ipsumText[1]}[footnote:abc]\n\n"
        "%Footnote.abc: Lorem ipsum\n\n"
    )
    odt.tokenizeText()
    odt.initDocument()
    odt.doConvert()
    odt.countStats()
    odt.closeDocument()

    fullFile = fncPath / "document.odt"

    odt.saveDocument(fullFile)
    assert fullFile.exists()
    assert zipfile.is_zipfile(fullFile)

    maniFile = tstPaths.outDir / "fmtToOdt_SaveFull_manifest.xml"
    settFile = tstPaths.outDir / "fmtToOdt_SaveFull_settings.xml"
    contFile = tstPaths.outDir / "fmtToOdt_SaveFull_content.xml"
    metaFile = tstPaths.outDir / "fmtToOdt_SaveFull_meta.xml"
    stylFile = tstPaths.outDir / "fmtToOdt_SaveFull_styles.xml"

    maniComp = tstPaths.refDir / "fmtToOdt_SaveFull_manifest.xml"
    settComp = tstPaths.refDir / "fmtToOdt_SaveFull_settings.xml"
    contComp = tstPaths.refDir / "fmtToOdt_SaveFull_content.xml"
    metaComp = tstPaths.refDir / "fmtToOdt_SaveFull_meta.xml"
    stylComp = tstPaths.refDir / "fmtToOdt_SaveFull_styles.xml"

    extaxtTo = tstPaths.outDir / "fmtToOdt_SaveFull"

    with zipfile.ZipFile(fullFile, mode="r") as zipObj:
        zipObj.extract("META-INF/manifest.xml", extaxtTo)
        zipObj.extract("settings.xml", extaxtTo)
        zipObj.extract("content.xml", extaxtTo)
        zipObj.extract("meta.xml", extaxtTo)
        zipObj.extract("styles.xml", extaxtTo)

    maniOut = tstPaths.outDir / "fmtToOdt_SaveFull" / "META-INF" / "manifest.xml"
    settOut = tstPaths.outDir / "fmtToOdt_SaveFull" / "settings.xml"
    contOut = tstPaths.outDir / "fmtToOdt_SaveFull" / "content.xml"
    metaOut = tstPaths.outDir / "fmtToOdt_SaveFull" / "meta.xml"
    stylOut = tstPaths.outDir / "fmtToOdt_SaveFull" / "styles.xml"

    def prettifyXml(inFile, outFile):
        with open(outFile, mode="wb") as fStream:
            xml = ET.parse(inFile)
            xmlIndent(xml.getroot())
            xml.write(fStream, encoding="utf-8", xml_declaration=True)

    prettifyXml(maniOut, maniFile)
    prettifyXml(settOut, settFile)
    prettifyXml(contOut, contFile)
    prettifyXml(metaOut, metaFile)
    prettifyXml(stylOut, stylFile)

    assert cmpFiles(maniFile, maniComp)
    assert cmpFiles(settFile, settComp)
    assert cmpFiles(contFile, contComp)
    assert cmpFiles(metaFile, metaComp, ignStart=ODT_IGNORE)
    assert cmpFiles(stylFile, stylComp)


@pytest.mark.core
def testToOdt_ODTParagraphStyle():
    """Test the ODTParagraphStyle class."""
    parStyle = ODTParagraphStyle("test")

    # Set Attributes
    # ==============

    # Display, Parent, Next Style
    assert parStyle._mAttr["display-name"] == ["style", None]
    assert parStyle._mAttr["parent-style-name"] == ["style", None]
    assert parStyle._mAttr["next-style-name"] == ["style", None]

    parStyle.setDisplayName("Name")
    parStyle.setParentStyleName("Name")
    parStyle.setNextStyleName("Name")

    assert parStyle._mAttr["display-name"] == ["style", "Name"]
    assert parStyle._mAttr["parent-style-name"] == ["style", "Name"]
    assert parStyle._mAttr["next-style-name"] == ["style", "Name"]

    # Outline Level
    assert parStyle._mAttr["default-outline-level"] == ["style", None]
    parStyle.setOutlineLevel("0")
    assert parStyle._mAttr["default-outline-level"] == ["style", None]
    parStyle.setOutlineLevel("1")
    assert parStyle._mAttr["default-outline-level"] == ["style", "1"]
    parStyle.setOutlineLevel("2")
    assert parStyle._mAttr["default-outline-level"] == ["style", "2"]
    parStyle.setOutlineLevel("3")
    assert parStyle._mAttr["default-outline-level"] == ["style", "3"]
    parStyle.setOutlineLevel("4")
    assert parStyle._mAttr["default-outline-level"] == ["style", "4"]
    parStyle.setOutlineLevel("5")
    assert parStyle._mAttr["default-outline-level"] == ["style", None]

    # Class
    assert parStyle._mAttr["class"] == ["style", None]
    parStyle.setClass("stuff")
    assert parStyle._mAttr["class"] == ["style", None]
    parStyle.setClass("text")
    assert parStyle._mAttr["class"] == ["style", "text"]
    parStyle.setClass("chapter")
    assert parStyle._mAttr["class"] == ["style", "chapter"]
    parStyle.setClass("stuff")
    assert parStyle._mAttr["class"] == ["style", None]

    # Set Paragraph Style
    # ===================

    # Margins & Line Height
    assert parStyle._pAttr["margin-top"] == ["fo", None]
    assert parStyle._pAttr["margin-bottom"] == ["fo", None]
    assert parStyle._pAttr["margin-left"] == ["fo", None]
    assert parStyle._pAttr["margin-right"] == ["fo", None]
    assert parStyle._pAttr["border-left"] == ["fo", None]
    assert parStyle._pAttr["border-right"] == ["fo", None]
    assert parStyle._pAttr["border-top"] == ["fo", None]
    assert parStyle._pAttr["border-bottom"] == ["fo", None]
    assert parStyle._pAttr["text-indent"] == ["fo", None]
    assert parStyle._pAttr["line-height"] == ["fo", None]

    parStyle.setMarginTop("0.000cm")
    parStyle.setMarginBottom("0.000cm")
    parStyle.setMarginLeft("0.000cm")
    parStyle.setMarginRight("0.000cm")
    parStyle.setBorderLeft(ODTBorderStyle("none"))
    parStyle.setBorderRight(ODTBorderStyle("none"))
    parStyle.setBorderTop(ODTBorderStyle("none"))
    parStyle.setBorderBottom(ODTBorderStyle("double", 0.14, QColor(128, 128, 128)))
    parStyle.setTextIndent("0.000cm")
    parStyle.setLineHeight("1.15")

    assert parStyle._pAttr["margin-top"] == ["fo", "0.000cm"]
    assert parStyle._pAttr["margin-bottom"] == ["fo", "0.000cm"]
    assert parStyle._pAttr["margin-left"] == ["fo", "0.000cm"]
    assert parStyle._pAttr["margin-right"] == ["fo", "0.000cm"]
    assert parStyle._pAttr["border-left"] == ["fo", "none"]
    assert parStyle._pAttr["border-right"] == ["fo", "none"]
    assert parStyle._pAttr["border-top"] == ["fo", "none"]
    assert parStyle._pAttr["border-bottom"] == ["fo", "0.14pt double #808080"]
    assert parStyle._pAttr["text-indent"] == ["fo", "0.000cm"]
    assert parStyle._pAttr["line-height"] == ["fo", "1.15"]

    # Text Alignment
    assert parStyle._pAttr["text-align"] == ["fo", None]
    parStyle.setTextAlign("stuff")
    assert parStyle._pAttr["text-align"] == ["fo", None]
    parStyle.setTextAlign("start")
    assert parStyle._pAttr["text-align"] == ["fo", "start"]
    parStyle.setTextAlign("center")
    assert parStyle._pAttr["text-align"] == ["fo", "center"]
    parStyle.setTextAlign("end")
    assert parStyle._pAttr["text-align"] == ["fo", "end"]
    parStyle.setTextAlign("justify")
    assert parStyle._pAttr["text-align"] == ["fo", "justify"]
    parStyle.setTextAlign("left")
    assert parStyle._pAttr["text-align"] == ["fo", "left"]
    parStyle.setTextAlign("right")
    assert parStyle._pAttr["text-align"] == ["fo", "right"]
    parStyle.setTextAlign("stuff")
    assert parStyle._pAttr["text-align"] == ["fo", None]

    # Break Before
    assert parStyle._pAttr["break-before"] == ["fo", None]
    parStyle.setBreakBefore("stuff")
    assert parStyle._pAttr["break-before"] == ["fo", None]
    parStyle.setBreakBefore("auto")
    assert parStyle._pAttr["break-before"] == ["fo", "auto"]
    parStyle.setBreakBefore("page")
    assert parStyle._pAttr["break-before"] == ["fo", "page"]
    parStyle.setBreakBefore("even-page")
    assert parStyle._pAttr["break-before"] == ["fo", "even-page"]
    parStyle.setBreakBefore("odd-page")
    assert parStyle._pAttr["break-before"] == ["fo", "odd-page"]
    parStyle.setBreakBefore("inherit")
    assert parStyle._pAttr["break-before"] == ["fo", "inherit"]
    parStyle.setBreakBefore("stuff")
    assert parStyle._pAttr["break-before"] == ["fo", None]

    # Break After
    assert parStyle._pAttr["break-after"] == ["fo", None]
    parStyle.setBreakAfter("stuff")
    assert parStyle._pAttr["break-after"] == ["fo", None]
    parStyle.setBreakAfter("auto")
    assert parStyle._pAttr["break-after"] == ["fo", "auto"]
    parStyle.setBreakAfter("page")
    assert parStyle._pAttr["break-after"] == ["fo", "page"]
    parStyle.setBreakAfter("even-page")
    assert parStyle._pAttr["break-after"] == ["fo", "even-page"]
    parStyle.setBreakAfter("odd-page")
    assert parStyle._pAttr["break-after"] == ["fo", "odd-page"]
    parStyle.setBreakAfter("inherit")
    assert parStyle._pAttr["break-after"] == ["fo", "inherit"]
    parStyle.setBreakAfter("stuff")
    assert parStyle._pAttr["break-after"] == ["fo", None]

    # Text Attributes
    # ===============

    # Font Name, Family and Size
    assert parStyle._tAttr["font-name"] == ["style", None]
    assert parStyle._tAttr["font-family"] == ["fo", None]
    assert parStyle._tAttr["font-size"] == ["fo", None]

    parStyle.setFontName("Verdana")
    parStyle.setFontFamily("Verdana")
    parStyle.setFontSize("12pt")

    assert parStyle._tAttr["font-name"] == ["style", "Verdana"]
    assert parStyle._tAttr["font-family"] == ["fo", "Verdana"]
    assert parStyle._tAttr["font-size"] == ["fo", "12pt"]

    # Font Weight
    assert parStyle._tAttr["font-weight"] == ["fo", None]
    parStyle.setFontWeight("stuff")
    assert parStyle._tAttr["font-weight"] == ["fo", None]
    parStyle.setFontWeight("normal")
    assert parStyle._tAttr["font-weight"] == ["fo", "normal"]
    parStyle.setFontWeight("bold")
    assert parStyle._tAttr["font-weight"] == ["fo", "bold"]
    parStyle.setFontWeight("100")
    assert parStyle._tAttr["font-weight"] == ["fo", "100"]
    parStyle.setFontWeight("200")
    assert parStyle._tAttr["font-weight"] == ["fo", "200"]
    parStyle.setFontWeight("300")
    assert parStyle._tAttr["font-weight"] == ["fo", "300"]
    parStyle.setFontWeight("400")
    assert parStyle._tAttr["font-weight"] == ["fo", "400"]
    parStyle.setFontWeight("500")
    assert parStyle._tAttr["font-weight"] == ["fo", "500"]
    parStyle.setFontWeight("600")
    assert parStyle._tAttr["font-weight"] == ["fo", "600"]
    parStyle.setFontWeight("700")
    assert parStyle._tAttr["font-weight"] == ["fo", "700"]
    parStyle.setFontWeight("800")
    assert parStyle._tAttr["font-weight"] == ["fo", "800"]
    parStyle.setFontWeight("900")
    assert parStyle._tAttr["font-weight"] == ["fo", "900"]
    parStyle.setFontWeight("stuff")
    assert parStyle._tAttr["font-weight"] == ["fo", None]

    # Colour & Opacity
    assert parStyle._tAttr["color"] == ["fo", None]
    assert parStyle._tAttr["opacity"] == ["loext", None]

    parStyle.setColor(QColor(0, 0, 0, 128))

    assert parStyle._tAttr["color"] == ["fo", "#000000"]
    assert parStyle._tAttr["opacity"] == ["loext", "50%"]

    parStyle.setColor(None)

    assert parStyle._tAttr["color"] == ["fo", None]
    assert parStyle._tAttr["opacity"] == ["loext", None]

    # Pack XML
    # ========
    xStyle = ET.Element("test")
    parStyle.packXML(xStyle)
    assert xmlToText(xStyle) == (
        "<test>"
        '<style:style style:name="test" style:family="paragraph" style:display-name="Name" '
        'style:parent-style-name="Name" style:next-style-name="Name">'
        '<style:paragraph-properties fo:margin-top="0.000cm" fo:margin-bottom="0.000cm" '
        'fo:margin-left="0.000cm" fo:margin-right="0.000cm" fo:border-left="none" '
        'fo:border-right="none" fo:border-top="none" '
        'fo:border-bottom="0.14pt double #808080" fo:text-indent="0.000cm" '
        'fo:line-height="1.15" />'
        '<style:text-properties style:font-name="Verdana" fo:font-family="Verdana" '
        'fo:font-size="12pt" />'
        "</style:style>"
        "</test>"
    )

    # A style with no paragraph or text attributes set skips both
    # the paragraph-properties and text-properties elements
    blankStyle = ODTParagraphStyle("blank")
    xBlank = ET.Element("test")
    blankStyle.packXML(xBlank)
    assert xmlToText(xBlank) == ('<test><style:style style:name="blank" style:family="paragraph" /></test>')

    # Changes
    # =======

    aStyle = ODTParagraphStyle("test")
    oStyle = ODTParagraphStyle("test")
    assert aStyle.checkNew(oStyle) is False
    assert aStyle.getID() == oStyle.getID()

    aStyle.setDisplayName("Name1")
    oStyle.setDisplayName("Name2")
    assert aStyle.checkNew(oStyle) is True
    assert aStyle.getID() != oStyle.getID()

    aStyle = ODTParagraphStyle("test")
    oStyle = ODTParagraphStyle("test")
    aStyle.setMarginTop("0.000cm")
    oStyle.setMarginTop("1.000cm")
    assert aStyle.checkNew(oStyle) is True
    assert aStyle.getID() != oStyle.getID()

    aStyle = ODTParagraphStyle("test")
    oStyle = ODTParagraphStyle("test")
    aStyle.setColor(QColor(0, 0, 0))
    oStyle.setColor(QColor(42, 42, 42))
    assert aStyle.checkNew(oStyle) is True
    assert aStyle.getID() != oStyle.getID()


@pytest.mark.core
def testToOdt_ODTBorderStyle():
    """Test the ODTBorderStyle class."""
    assert str(ODTBorderStyle("none")) == "none"
    assert str(ODTBorderStyle("dashed", 0.50)) == "0.50pt dashed"
    assert str(ODTBorderStyle("solid", 0.75, QColor(100, 100, 100))) == "0.75pt solid #646464"


@pytest.mark.core
def testToOdt_ODTTextStyle():
    """Test the ODTTextStyle class."""
    txtStyle = ODTTextStyle("test")

    # Font Weight
    assert txtStyle._tAttr["font-weight"] == ["fo", None]
    txtStyle.setFontWeight("stuff")
    assert txtStyle._tAttr["font-weight"] == ["fo", None]
    txtStyle.setFontWeight("normal")
    assert txtStyle._tAttr["font-weight"] == ["fo", "normal"]
    txtStyle.setFontWeight("bold")
    assert txtStyle._tAttr["font-weight"] == ["fo", "bold"]
    txtStyle.setFontWeight("100")
    assert txtStyle._tAttr["font-weight"] == ["fo", "100"]
    txtStyle.setFontWeight("200")
    assert txtStyle._tAttr["font-weight"] == ["fo", "200"]
    txtStyle.setFontWeight("300")
    assert txtStyle._tAttr["font-weight"] == ["fo", "300"]
    txtStyle.setFontWeight("400")
    assert txtStyle._tAttr["font-weight"] == ["fo", "400"]
    txtStyle.setFontWeight("500")
    assert txtStyle._tAttr["font-weight"] == ["fo", "500"]
    txtStyle.setFontWeight("600")
    assert txtStyle._tAttr["font-weight"] == ["fo", "600"]
    txtStyle.setFontWeight("700")
    assert txtStyle._tAttr["font-weight"] == ["fo", "700"]
    txtStyle.setFontWeight("800")
    assert txtStyle._tAttr["font-weight"] == ["fo", "800"]
    txtStyle.setFontWeight("900")
    assert txtStyle._tAttr["font-weight"] == ["fo", "900"]
    txtStyle.setFontWeight("stuff")
    assert txtStyle._tAttr["font-weight"] == ["fo", None]

    # Font Style
    assert txtStyle._tAttr["font-style"] == ["fo", None]
    txtStyle.setFontStyle("stuff")
    assert txtStyle._tAttr["font-style"] == ["fo", None]
    txtStyle.setFontStyle("normal")
    assert txtStyle._tAttr["font-style"] == ["fo", "normal"]
    txtStyle.setFontStyle("italic")
    assert txtStyle._tAttr["font-style"] == ["fo", "italic"]
    txtStyle.setFontStyle("oblique")
    assert txtStyle._tAttr["font-style"] == ["fo", "oblique"]
    txtStyle.setFontStyle("stuff")
    assert txtStyle._tAttr["font-style"] == ["fo", None]

    # Text Color
    assert txtStyle._tAttr["color"] == ["fo", None]
    txtStyle.setColor("#012345")  # type: ignore
    assert txtStyle._tAttr["color"] == ["fo", None]
    txtStyle.setColor(QColor(255, 128, 0))
    assert txtStyle._tAttr["color"] == ["fo", "#ff8000"]
    txtStyle.setColor(None)
    assert txtStyle._tAttr["color"] == ["fo", None]

    # Background Color
    assert txtStyle._tAttr["background-color"] == ["fo", None]
    txtStyle.setBackgroundColor("#012345")  # type: ignore
    assert txtStyle._tAttr["background-color"] == ["fo", None]
    txtStyle.setBackgroundColor(QColor(255, 128, 0))
    assert txtStyle._tAttr["background-color"] == ["fo", "#ff8000"]
    txtStyle.setBackgroundColor(None)
    assert txtStyle._tAttr["background-color"] == ["fo", None]

    # Text Position
    assert txtStyle._tAttr["text-position"] == ["style", None]
    txtStyle.setTextPosition("stuff")
    assert txtStyle._tAttr["text-position"] == ["style", None]
    txtStyle.setTextPosition("super")
    assert txtStyle._tAttr["text-position"] == ["style", "super 58%"]
    txtStyle.setTextPosition("sub")
    assert txtStyle._tAttr["text-position"] == ["style", "sub 58%"]
    txtStyle.setTextPosition("stuff")
    assert txtStyle._tAttr["text-position"] == ["style", None]

    # Line Through Style
    assert txtStyle._tAttr["text-line-through-style"] == ["style", None]
    txtStyle.setStrikeStyle("stuff")
    assert txtStyle._tAttr["text-line-through-style"] == ["style", None]
    txtStyle.setStrikeStyle("none")
    assert txtStyle._tAttr["text-line-through-style"] == ["style", "none"]
    txtStyle.setStrikeStyle("solid")
    assert txtStyle._tAttr["text-line-through-style"] == ["style", "solid"]
    txtStyle.setStrikeStyle("stuff")
    assert txtStyle._tAttr["text-line-through-style"] == ["style", None]

    # Line Through Type
    assert txtStyle._tAttr["text-line-through-type"] == ["style", None]
    txtStyle.setStrikeType("stuff")
    assert txtStyle._tAttr["text-line-through-type"] == ["style", None]
    txtStyle.setStrikeType("none")  # Deprecated in ODF 1.3
    assert txtStyle._tAttr["text-line-through-type"] == ["style", None]
    txtStyle.setStrikeType("single")
    assert txtStyle._tAttr["text-line-through-type"] == ["style", "single"]
    txtStyle.setStrikeType("double")
    assert txtStyle._tAttr["text-line-through-type"] == ["style", "double"]
    txtStyle.setStrikeType("stuff")
    assert txtStyle._tAttr["text-line-through-type"] == ["style", None]

    # Underline Style
    assert txtStyle._tAttr["text-underline-style"] == ["style", None]
    txtStyle.setUnderlineStyle("stuff")
    assert txtStyle._tAttr["text-underline-style"] == ["style", None]
    txtStyle.setUnderlineStyle("none")
    assert txtStyle._tAttr["text-underline-style"] == ["style", "none"]
    txtStyle.setUnderlineStyle("solid")
    assert txtStyle._tAttr["text-underline-style"] == ["style", "solid"]
    txtStyle.setUnderlineStyle("stuff")
    assert txtStyle._tAttr["text-underline-style"] == ["style", None]

    # Underline Width
    assert txtStyle._tAttr["text-underline-width"] == ["style", None]
    txtStyle.setUnderlineWidth("stuff")
    assert txtStyle._tAttr["text-underline-width"] == ["style", None]
    txtStyle.setUnderlineWidth("auto")
    assert txtStyle._tAttr["text-underline-width"] == ["style", "auto"]
    txtStyle.setUnderlineWidth("stuff")
    assert txtStyle._tAttr["text-underline-width"] == ["style", None]

    # Underline Colour
    assert txtStyle._tAttr["text-underline-color"] == ["style", None]
    txtStyle.setUnderlineColor("stuff")
    assert txtStyle._tAttr["text-underline-color"] == ["style", None]
    txtStyle.setUnderlineColor("font-color")
    assert txtStyle._tAttr["text-underline-color"] == ["style", "font-color"]
    txtStyle.setUnderlineColor("stuff")
    assert txtStyle._tAttr["text-underline-color"] == ["style", None]

    # Pack XML
    # ========
    txtStyle.setFontWeight("bold")
    txtStyle.setFontStyle("italic")
    txtStyle.setTextPosition("super")
    txtStyle.setStrikeStyle("solid")
    txtStyle.setStrikeType("single")
    xStyle = ET.Element("test")
    txtStyle.packXML(xStyle)
    assert xmlToText(xStyle) == (
        '<test><style:style style:name="test" style:family="text"><style:text-properties '
        'fo:font-weight="bold" fo:font-style="italic" style:text-position="super 58%" '
        'style:text-line-through-style="solid" style:text-line-through-type="single" />'
        "</style:style></test>"
    )

    # A style with no text attributes set skips the text-properties element
    blankStyle = ODTTextStyle("blank")
    xBlank = ET.Element("test")
    blankStyle.packXML(xBlank)
    assert xmlToText(xBlank) == ('<test><style:style style:name="blank" style:family="text" /></test>')


@pytest.mark.core
def testToOdt_XMLParagraph():
    """Test XML encoding of paragraph."""
    # Stage 1 : Text
    # ==============

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    # Plain Text
    xmlPar.appendText("Hello World")
    assert xmlToText(xRoot) == ("<root><text:p>Hello World</text:p></root>")

    # Text Span
    xmlPar.appendSpan("spanned text", "T1", "")
    assert xmlToText(xRoot) == (
        '<root><text:p>Hello World<text:span text:style-name="T1">spanned text</text:span></text:p></root>'
    )

    # Tail Text
    xmlPar.appendText("more text")
    assert xmlToText(xRoot) == (
        '<root><text:p>Hello World<text:span text:style-name="T1">spanned text</text:span>more text</text:p></root>'
    )

    assert xmlPar.checkError() == (0, "")

    # Stage 2 : Line Breaks
    # =====================

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    # Plain Text w/Line Break
    xmlPar.appendText("Hello\nWorld\n!!")
    assert xmlToText(xRoot) == ("<root><text:p>Hello<text:line-break />World<text:line-break />!!</text:p></root>")

    # Text Span w/Line Break
    xmlPar.appendSpan("spanned\ntext", "T1", "")
    assert xmlToText(xRoot) == (
        "<root>"
        "<text:p>Hello<text:line-break />World<text:line-break />!!"
        '<text:span text:style-name="T1">spanned<text:line-break />text</text:span></text:p>'
        "</root>"
    )

    # Tail Text w/Line Break
    xmlPar.appendText("more\ntext")
    assert xmlToText(xRoot) == (
        "<root>"
        "<text:p>Hello<text:line-break />World<text:line-break />!!"
        '<text:span text:style-name="T1">spanned<text:line-break />text</text:span>'
        "more<text:line-break />text</text:p>"
        "</root>"
    )

    assert xmlPar.checkError() == (0, "")

    # Stage 3 : Tabs
    # ==============

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    # Plain Text w/Line Break
    xmlPar.appendText("Hello\tWorld\t!!")
    assert xmlToText(xRoot) == ("<root><text:p>Hello<text:tab />World<text:tab />!!</text:p></root>")

    # Text Span w/Line Break
    xmlPar.appendSpan("spanned\ttext", "T1", "")
    assert xmlToText(xRoot) == (
        "<root>"
        "<text:p>Hello<text:tab />World<text:tab />!!"
        '<text:span text:style-name="T1">spanned<text:tab />text</text:span></text:p>'
        "</root>"
    )

    # Tail Text w/Line Break
    xmlPar.appendText("more\ttext")
    assert xmlToText(xRoot) == (
        "<root>"
        "<text:p>Hello<text:tab />World<text:tab />!!"
        '<text:span text:style-name="T1">spanned<text:tab />text</text:span>'
        "more<text:tab />text</text:p>"
        "</root>"
    )

    # Tail Text w/Link
    xmlPar.appendSpan("Example", "T1", "http://www.example.com")
    assert xmlToText(xRoot) == (
        "<root>"
        "<text:p>Hello<text:tab />World<text:tab />!!"
        '<text:span text:style-name="T1">spanned<text:tab />text</text:span>'
        "more<text:tab />text"
        '<text:a xlink:type="simple" xlink:href="http://www.example.com" text:style-name="T1">'
        "Example</text:a></text:p>"
        "</root>"
    )

    assert xmlPar.checkError() == (0, "")

    # Stage 4 : Spaces
    # ================

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    # Plain Text w/Spaces
    xmlPar.appendText("Hello  World   !!")
    assert xmlToText(xRoot) == ('<root><text:p>Hello <text:s />World <text:s text:c="2" />!!</text:p></root>')

    # Text Span w/Spaces
    xmlPar.appendSpan("spanned    text", "T1", "")
    assert xmlToText(xRoot) == (
        "<root>"
        '<text:p>Hello <text:s />World <text:s text:c="2" />!!'
        '<text:span text:style-name="T1">spanned <text:s text:c="3" />text</text:span></text:p>'
        "</root>"
    )

    # Tail Text w/Spaces
    xmlPar.appendText("more     text")
    assert xmlToText(xRoot) == (
        "<root>"
        '<text:p>Hello <text:s />World <text:s text:c="2" />!!'
        '<text:span text:style-name="T1">spanned <text:s text:c="3" />text</text:span>'
        'more <text:s text:c="4" />text</text:p>'
        "</root>"
    )

    assert xmlPar.checkError() == (0, "")

    # Stage 5 : Lots of Spaces
    # ========================

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    # Plain Text w/Many Spaces
    xmlPar.appendText("  \t A \n  B ")
    assert xmlToText(xRoot) == (
        '<root><text:p><text:s text:c="2" /><text:tab /> A <text:line-break /> <text:s />B </text:p></root>'
    )

    # Text Span w/Many Spaces
    xmlPar.appendSpan("  C  \t  D \n E ", "T1", "")
    assert xmlToText(xRoot) == (
        "<root>"
        '<text:p><text:s text:c="2" /><text:tab /> A <text:line-break /> <text:s />B '
        '<text:span text:style-name="T1"> <text:s />C <text:s /><text:tab /> <text:s />D '
        "<text:line-break /> E </text:span></text:p>"
        "</root>"
    )

    assert xmlPar.checkError() == (0, "")

    # Check Error
    # ===========

    xRoot = ET.Element("root")
    xElem = ET.SubElement(xRoot, _mkTag("text", "p"))
    xmlPar = XMLParagraph(xElem)

    xmlPar.appendText("A")
    xmlPar._nState = 5
    xmlPar.appendText("B")
    xmlPar.appendText("\n")
    xmlPar.appendText("\t")
    xmlPar.appendText("  ")
    xmlPar.appendText("   ")

    assert xmlPar.checkError() == (8, "8 char(s) were not written: 'AB\n\t     '")

    # A node is not appended in an invalid or unsupported state
    xImg = ET.Element(_mkTag("draw", "frame"))
    xmlPar.appendNode(xImg)
    assert list(xElem) == []

    xmlPar._nState = X_ROOT_TEXT
    xmlPar.appendNode(None)
    assert list(xElem) == []


@pytest.mark.core
def testToOdt_MkTag():
    """Test the tag maker function."""
    assert _mkTag("office", "text") == "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}text"
    assert _mkTag("style", "text") == "{urn:oasis:names:tc:opendocument:xmlns:style:1.0}text"
    assert _mkTag("blabla", "text") == "text"
