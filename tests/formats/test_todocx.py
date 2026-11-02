"""
novelWriter - DocX Format Tests
===============================

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

import xml.etree.ElementTree as ET
import zipfile

from pathlib import Path

import pytest

from novelwriter.common import xmlIndent
from novelwriter.constants import nwHeadFmt, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt, nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp
from novelwriter.formats.todocx import OOXML_SCM, DocXParagraph, ToDocX, _mkTag, _wTag
from novelwriter.manuscript.buildsettings import BuildSettings
from novelwriter.manuscript.docbuild import DocumentBuilder

from tests.helpers import DOCX_IGNORE, TstPaths, cmpFiles, xmlToText
from tests.mocked import MockGuiMain


@pytest.mark.core
def testToDocX_NovelHeadingStyles(mockGUI: MockGuiMain):
    """Test formatting of novel headings."""
    project = NWProject()
    doc = ToDocX(project)
    doc._isNovel = True
    doc.initDocument()

    # Title
    # =====

    xTest = ET.Element(_wTag("body"))
    doc._text = "#! Hello World"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Title" /><w:jc w:val="center" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Plain Partition
    doc._text = "# Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Title" /><w:pageBreakBefore /><w:jc w:val="center" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Formatted Partition
    doc._text = "# Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.setPartitionFormat(f"Part{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Title" /><w:pageBreakBefore /><w:jc w:val="center" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Part</w:t><w:br /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Plain Chapter
    doc._text = "## Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading1" /><w:pageBreakBefore /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Formatted Chapter
    doc._text = "## Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.setChapterFormat(f"Chapter {nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading1" /><w:pageBreakBefore /></w:pPr>'
        "<w:r><w:rPr /><w:t>Chapter 2</w:t><w:br /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Plain Scene
    doc._text = "### Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading2" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Formatted Scene
    doc._text = "### Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.setSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading2" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Scene 2</w:t><w:br /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Section
    doc._text = "#### Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading3" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )


@pytest.mark.core
def testToDocX_NotesHeadingStyles(mockGUI: MockGuiMain):
    """Test formatting of notes headings."""
    project = NWProject()
    doc = ToDocX(project)
    doc._isNovel = False
    doc.initDocument()

    # Title
    xTest = ET.Element(_wTag("body"))
    doc._text = "#! Hello World"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Title" /><w:jc w:val="center" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Heading 1
    doc._text = "# Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading1" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Heading 2
    doc._text = "## Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading2" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Heading 3
    doc._text = "### Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading3" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Heading 4
    doc._text = "#### Hello World"
    xTest = ET.Element(_wTag("body"))
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Heading4" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )


@pytest.mark.core
def testToDocX_ParagraphStyles(mockGUI: MockGuiMain):
    """Test formatting of paragraphs."""
    project = NWProject()
    doc = ToDocX(project)
    doc.setCommentType(nwComment.PLAIN, True)
    doc.setCommentType(nwComment.SYNOPSIS, True)
    doc.setCommentType(nwComment.SHORT, True)
    doc.setKeywords(True)
    doc.initDocument()

    # Normal Text
    xTest = ET.Element(_wTag("body"))
    doc._text = "Hello World"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr><w:r><w:rPr />'
        "<w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Separator
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.SEP, "", "* * *", [], BlockFmt.NONE)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Separator" /></w:pPr><w:r><w:rPr /><w:t>* * *</w:t></w:r></w:p></w:body>'
    )

    # Horizontal Rule
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.HRULE, "", "", [], BlockFmt.NONE)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" />'
        '<w:pBdr><w:bottom w:val="single" w:color="646464" w:sz="6" w:space="1" /></w:pBdr>'
        '<w:ind w:left="2400" w:right="2400" /></w:pPr></w:p></w:body>'
    )

    # Empty Paragraph
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.SKIP, "", "* * *", [], BlockFmt.NONE)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == ('<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr></w:p></w:body>')

    # Synopsis
    xTest = ET.Element(_wTag("body"))
    doc._text = "%Synopsis: Hello World\n\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="MetaText" /></w:pPr>'
        '<w:r><w:rPr><w:b /><w:color w:val="813709" /></w:rPr><w:t>Synopsis:</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="813709" /></w:rPr><w:t>Hello World</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Short
    xTest = ET.Element(_wTag("body"))
    doc._text = "%Short: Hello World\n\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="MetaText" /></w:pPr>'
        '<w:r><w:rPr><w:b /><w:color w:val="813709" /></w:rPr><w:t>Short Description:</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="813709" /></w:rPr><w:t>Hello World</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Comment
    xTest = ET.Element(_wTag("body"))
    doc._text = "% Hello World\n\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="MetaText" /></w:pPr>'
        '<w:r><w:rPr><w:b /><w:color w:val="646464" /></w:rPr><w:t>Comment:</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="646464" /></w:rPr><w:t>Hello World</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Tags and References (Single)
    xTest = ET.Element(_wTag("body"))
    doc._text = "@tag: Stuff"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="MetaText" /></w:pPr>'
        '<w:r><w:rPr><w:b /><w:color w:val="f5871f" /></w:rPr><w:t>Tag:</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="4271ae" /></w:rPr><w:t>Stuff</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Tags and References (Multiple)
    xTest = ET.Element(_wTag("body"))
    doc._text = "@char: Jane, John"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="MetaText" /></w:pPr>'
        '<w:r><w:rPr><w:b /><w:color w:val="f5871f" /></w:rPr><w:t>Characters:</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="4271ae" /></w:rPr><w:t>Jane</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve">, </w:t></w:r>'
        '<w:r><w:rPr><w:color w:val="4271ae" /></w:rPr><w:t>John</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Tags and References (Invalid)
    xTest = ET.Element(_wTag("body"))
    doc._text = "@stuff: Stuff"
    doc._pars = []
    doc.tokenizeText()
    doc.doConvert()
    assert doc._pars == []


@pytest.mark.core
def testToDocX_Links(mockGUI: MockGuiMain):
    """Test formatting of links."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    # Register 2 links
    rd1 = doc._appendExternalRel("http://example.com")
    rd2 = doc._appendExternalRel("https://example.com")
    assert rd1 == "rId1"
    assert rd2 == "rId2"

    # Link 1
    xTest = ET.Element(_wTag("body"))
    doc._text = "Foo http://example.com bar"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Foo </w:t></w:r>'
        '<w:hyperlink r:id="rId1"><w:r><w:rPr><w:rStyle w:val="InternetLink" /></w:rPr>'
        "<w:t>http://example.com</w:t></w:r></w:hyperlink>"
        '<w:r><w:rPr /><w:t xml:space="preserve"> bar</w:t></w:r></w:p></w:body>'
    )

    # Link 2
    xTest = ET.Element(_wTag("body"))
    doc._text = "Foo https://example.com bar"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Foo </w:t></w:r>'
        '<w:hyperlink r:id="rId2"><w:r><w:rPr><w:rStyle w:val="InternetLink" /></w:rPr>'
        "<w:t>https://example.com</w:t></w:r></w:hyperlink>"
        '<w:r><w:rPr /><w:t xml:space="preserve"> bar</w:t></w:r></w:p></w:body>'
    )


@pytest.mark.core
def testToDocX_ParagraphFormatting(mockGUI: MockGuiMain):
    """Test formatting of paragraphs."""
    project = NWProject()
    doc = ToDocX(project)
    doc.setCommentType(nwComment.PLAIN, True)
    doc.setCommentType(nwComment.SYNOPSIS, True)
    doc.setKeywords(True)
    doc.initDocument()

    # Left Align
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.LEFT)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:jc w:val="left" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Right Align
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.RIGHT)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:jc w:val="right" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Center Align
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.CENTRE)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:jc w:val="center" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Justify
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.JUSTIFY)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:jc w:val="both" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Page Break Before
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.PBB)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:pageBreakBefore /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r>"
        "</w:p></w:body>"
    )

    # Page Break After
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.PBA)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r>"
        '<w:r><w:br w:type="page" /></w:r>'
        "</w:p></w:body>"
    )

    # Zero Margins
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.Z_TOP | BlockFmt.Z_BTM)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" />'
        '<w:spacing w:before="0" w:after="0" w:line="252" w:lineRule="auto" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # Indent
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.IND_L | BlockFmt.IND_R)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" />'
        '<w:ind w:left="880" w:right="880" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # First Line Indent
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.IND_T)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" />'
        '<w:ind w:firstLine="308" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )


@pytest.mark.core
def testToDocX_TextFormatting(mockGUI: MockGuiMain):
    """Test formatting of text."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    # Markdown
    xTest = ET.Element(_wTag("body"))
    doc._text = "Text **bold**, _italic_, ~~strike~~."
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Text </w:t></w:r>'
        "<w:r><w:rPr><w:b /></w:rPr><w:t>bold</w:t></w:r>"
        '<w:r><w:rPr /><w:t xml:space="preserve">, </w:t></w:r>'
        "<w:r><w:rPr><w:i /></w:rPr><w:t>italic</w:t></w:r>"
        '<w:r><w:rPr /><w:t xml:space="preserve">, </w:t></w:r>'
        "<w:r><w:rPr><w:strike /></w:rPr><w:t>strike</w:t></w:r>"
        "<w:r><w:rPr /><w:t>.</w:t></w:r>"
        "</w:p></w:body>"
    )

    # Nested Shortcode Text, Emphasis
    xTest = ET.Element(_wTag("body"))
    doc._text = "Some [s]nested [b]bold[/b] [u]and[/u] [i]italics[/i] text[/s] text."
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Some </w:t></w:r>'
        '<w:r><w:rPr><w:strike /></w:rPr><w:t xml:space="preserve">nested </w:t></w:r>'
        "<w:r><w:rPr><w:b /><w:strike /></w:rPr><w:t>bold</w:t></w:r>"
        '<w:r><w:rPr><w:strike /></w:rPr><w:t xml:space="preserve"> </w:t></w:r>'
        '<w:r><w:rPr><w:u w:val="single" /><w:strike /></w:rPr><w:t>and</w:t></w:r>'
        '<w:r><w:rPr><w:strike /></w:rPr><w:t xml:space="preserve"> </w:t></w:r>'
        "<w:r><w:rPr><w:i /><w:strike /></w:rPr><w:t>italics</w:t></w:r>"
        '<w:r><w:rPr><w:strike /></w:rPr><w:t xml:space="preserve"> text</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> text.</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Shortcode Text, Super/Subscript
    xTest = ET.Element(_wTag("body"))
    doc._text = "Some super[sup]script[/sup] and sub[sub]script[/sub] text."
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Some super</w:t></w:r>"
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr><w:t>script</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> and sub</w:t></w:r>'
        '<w:r><w:rPr><w:vertAlign w:val="subscript" /></w:rPr><w:t>script</w:t></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve"> text.</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Shortcode Text, Underline/Highlight
    xTest = ET.Element(_wTag("body"))
    doc._text = "Some [u]underlined and [m]highlighted[/m][/u] text."
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Some </w:t></w:r>'
        '<w:r><w:rPr><w:u w:val="single" /></w:rPr>'
        '<w:t xml:space="preserve">underlined and </w:t></w:r>'
        '<w:r><w:rPr><w:u w:val="single" /><w:shd w:fill="ffffa6" w:val="clear" /></w:rPr>'
        "<w:t>highlighted</w:t></w:r>"
        '<w:r><w:rPr /><w:t xml:space="preserve"> text.</w:t></w:r>'
        "</w:p></w:body>"
    )

    # Hard Break
    xTest = ET.Element(_wTag("body"))
    doc._text = "Some text.\nNext line\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Some text.</w:t><w:br /><w:t>Next line</w:t></w:r>"
        "</w:p></w:body>"
    )

    # Tab
    xTest = ET.Element(_wTag("body"))
    doc._text = "\tItem 1\tItem 2\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:tab /><w:t>Item 1</w:t><w:tab /><w:t>Item 2</w:t></w:r>"
        "</w:p></w:body>"
    )

    # Tab in Format
    xTest = ET.Element(_wTag("body"))
    doc._text = "Some **bold\ttext**"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Some </w:t></w:r>'
        "<w:r><w:rPr><w:b /></w:rPr><w:t>bold</w:t><w:tab /><w:t>text</w:t></w:r>"
        "</w:p></w:body>"
    )


@pytest.mark.core
def testToDocX_Footnotes(mockGUI: MockGuiMain):
    """Test formatting of footnotes."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    # Text
    xTest = ET.Element(_wTag("body"))
    doc._text = (
        "Text with one[footnote:fa], **two**[footnote:fd], "
        "or three[footnote:fb] footnotes.[footnote:fe]\n\n"
        "%footnote.fa: Footnote text A.[footnote:fc]\n\n"
        "%footnote.fc: This footnote is skipped.\n\n"
        "%footnote.fd: Another footnote.\n\n"
        "%footnote.fe: Again?\n\n"
    )
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Text with one</w:t></w:r>"
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr>'
        '<w:footnoteReference w:id="1" /></w:r>'
        '<w:r><w:rPr /><w:t xml:space="preserve">, </w:t></w:r>'
        "<w:r><w:rPr><w:b /></w:rPr><w:t>two</w:t></w:r>"
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr>'
        '<w:footnoteReference w:id="2" /></w:r>'
        "<w:r><w:rPr /><w:t>, or three</w:t></w:r>"
        '<w:r><w:rPr /><w:t xml:space="preserve"> footnotes.</w:t></w:r>'
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr>'
        '<w:footnoteReference w:id="3" /></w:r>'
        "</w:p></w:body>"
    )

    # Footnotes
    doc._footnotesXml()
    assert xmlToText(doc._files["footnotes.xml"].xml) == (
        "<w:footnotes>"
        '<w:footnote w:id="1"><w:p><w:pPr><w:pStyle w:val="FootnoteText" /></w:pPr>'
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr><w:footnoteRef /></w:r>'
        "<w:r><w:rPr /><w:t>Footnote text A.</w:t></w:r></w:p></w:footnote>"
        '<w:footnote w:id="2"><w:p><w:pPr><w:pStyle w:val="FootnoteText" /></w:pPr>'
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr><w:footnoteRef /></w:r>'
        "<w:r><w:rPr /><w:t>Another footnote.</w:t></w:r></w:p></w:footnote>"
        '<w:footnote w:id="3"><w:p><w:pPr><w:pStyle w:val="FootnoteText" /></w:pPr>'
        '<w:r><w:rPr><w:vertAlign w:val="superscript" /></w:rPr><w:footnoteRef /></w:r>'
        "<w:r><w:rPr /><w:t>Again?</w:t></w:r></w:p></w:footnote>"
        "</w:footnotes>"
    )


@pytest.mark.core
def testToDocX_Lists(mockGUI: MockGuiMain):
    """Test formatting of lists."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    # Text
    xTest = ET.Element(_wTag("body"))
    doc._text = "Text\n* One\n* Two\nmore\n* Three\n\n* Four\n\nText\n"
    doc.tokenizeText()
    doc.doConvert()
    for par in doc._pars:
        par.toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Text</w:t></w:r></w:p>"
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph" />'
        '<w:numPr><w:ilvl w:val="0" /><w:numId w:val="1" /></w:numPr>'
        '<w:spacing w:before="132" w:after="0" w:line="252" w:lineRule="auto" /></w:pPr>'
        "<w:r><w:rPr /><w:t>One</w:t></w:r></w:p>"
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph" />'
        '<w:numPr><w:ilvl w:val="0" /><w:numId w:val="1" /></w:numPr>'
        '<w:spacing w:before="0" w:after="0" w:line="252" w:lineRule="auto" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Two</w:t><w:br /><w:t>more</w:t></w:r></w:p>"
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph" />'
        '<w:numPr><w:ilvl w:val="0" /><w:numId w:val="1" /></w:numPr>'
        '<w:spacing w:before="0" w:after="132" w:line="252" w:lineRule="auto" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Three</w:t></w:r></w:p>"
        '<w:p><w:pPr><w:pStyle w:val="ListParagraph" />'
        '<w:numPr><w:ilvl w:val="0" /><w:numId w:val="2" /></w:numPr></w:pPr>'
        "<w:r><w:rPr /><w:t>Four</w:t></w:r></w:p>"
        '<w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Text</w:t></w:r></w:p></w:body>"
    )

    # Ordered List
    xTest = ET.Element(_wTag("body"))
    doc._text = "#. Five\n#. Six\n"
    doc.tokenizeText()
    doc.doConvert()
    for par in doc._pars[-2:]:
        par.toXml(xTest)
    assert [x.get(_wTag("val")) for x in xTest.iter(_wTag("numId"))] == ["3", "3"]
    assert doc._numLists == [False, False, True]

    # Numbering
    doc.closeDocument()
    xRoot = doc._files["numbering.xml"].xml
    assert doc._rels["numbering.xml"].relType.endswith("/numbering")

    xAbst = xRoot.findall(_wTag("abstractNum"))
    assert [x.get(_wTag("abstractNumId")) for x in xAbst] == ["0", "1"]
    for xA, numFmt, lvlText, hanging in [
        (xAbst[0], "bullet", [nwUnicode.U_BULL, nwUnicode.U_BULL], "220"),
        (xAbst[1], "decimal", ["%1.", "%9."], "330"),
    ]:
        xLvls = xA.findall(_wTag("lvl"))
        assert len(xLvls) == 9
        for xLvl, left, text in [(xLvls[0], "440", lvlText[0]), (xLvls[8], "3960", lvlText[1])]:
            assert [(x.tag, x.get(_wTag("val"))) for x in xLvl[:4]] == [
                (_wTag("start"), "1"),
                (_wTag("numFmt"), numFmt),
                (_wTag("lvlText"), text),
                (_wTag("lvlJc"), "left"),
            ]
            xInd = xLvl.find(f"{_wTag('pPr')}/{_wTag('ind')}")
            assert xInd is not None
            assert xInd.get(_wTag("left")) == left
            assert xInd.get(_wTag("hanging")) == hanging

    # Ordered lists restart their numbering
    xNums = xRoot.findall(_wTag("num"))
    assert [x.get(_wTag("numId")) for x in xNums] == ["1", "2", "3"]
    assert [x[0].get(_wTag("val")) for x in xNums] == ["0", "0", "1"]
    assert [len(x) for x in xNums] == [1, 1, 2]
    xOvr = xNums[2][1]
    assert xOvr.tag == _wTag("lvlOverride")
    assert xOvr.get(_wTag("ilvl")) == "0"
    assert xOvr[0].tag == _wTag("startOverride")
    assert xOvr[0].get(_wTag("val")) == "1"


@pytest.mark.core
def testToDocX_Fields(mockGUI: MockGuiMain):
    """Test formatting of footnotes."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    # Field Builder
    xNode = doc._generateField("a:b", 0x00)
    assert isinstance(xNode, ET.Element)
    assert xmlToText(xNode) == "<w:r><w:rPr /><w:t>0</w:t></w:r>"
    assert doc._usedFields == [(xNode.find(_wTag("t")), "b")]

    assert doc._generateField("a", 0x00) is None

    # Full Processing
    doc._text = "Word Count: [field:allWords]\nCharacter Count: [field:allChars]\nChicken Count: [field:allChickens]\n"
    doc.tokenizeText()
    doc.doConvert()
    doc.countStats()
    doc._documentXml(None, None, None)
    assert xmlToText(doc._files["document.xml"].xml) == (
        '<w:document><w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        '<w:r><w:rPr /><w:t xml:space="preserve">Word Count: </w:t></w:r>'
        "<w:r><w:rPr /><w:t>6</w:t></w:r>"
        '<w:r><w:rPr /><w:br /><w:t xml:space="preserve">Character Count: </w:t></w:r>'
        "<w:r><w:rPr /><w:t>46</w:t></w:r>"
        '<w:r><w:rPr /><w:br /><w:t xml:space="preserve">Chicken Count: </w:t></w:r>'
        "<w:r><w:rPr /><w:t>0</w:t></w:r>"
        "</w:p><w:sectPr>"
        '<w:footnotePr><w:numFmt w:val="decimal" /></w:footnotePr>'
        '<w:pgSz w:w="11905" w:h="16837" w:orient="portrait" />'
        '<w:pgMar w:top="1133" w:right="1133" w:bottom="1133" w:left="1133" '
        'w:header="748" w:footer="0" w:gutter="0" />'
        '<w:pgNumType w:start="1" w:fmt="decimal" /><w:titlePg />'
        "</w:sectPr></w:body></w:document>"
    )


@pytest.mark.core
def testToDocX_RightToLeft(mockGUI: MockGuiMain):
    """Test RTL documents."""
    project = NWProject()
    doc = ToDocX(project)
    doc.setLanguage(None, True)
    doc.initDocument()
    word = "متن"

    # LTR blocks are marked, and keep physical alignment and indents
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.LEFT | BlockFmt.IND_L)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /><w:bidi w:val="0" />'
        '<w:ind w:left="880" /><w:jc w:val="left" /></w:pPr>'
        "<w:r><w:rPr /><w:t>Hello World</w:t></w:r></w:p></w:body>"
    )

    # RTL blocks inherit the direction, and swap left and right, which
    # Word treats as start and end
    xTest = ET.Element(_wTag("body"))
    doc._blocks = [(BlockTyp.TEXT, "", word, [], BlockFmt.LEFT | BlockFmt.IND_L)]
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" />'
        '<w:ind w:right="880" /><w:jc w:val="right" /></w:pPr>'
        f"<w:r><w:rPr /><w:t>{word}</w:t></w:r></w:p></w:body>"
    )

    # Bold and italic also apply to complex scripts
    xTest = ET.Element(_wTag("body"))
    doc._text = f"**{word}** _{word}_"
    doc.tokenizeText()
    doc.doConvert()
    doc._pars[-1].toXml(xTest)
    assert xmlToText(xTest) == (
        '<w:body><w:p><w:pPr><w:pStyle w:val="Normal" /></w:pPr>'
        f"<w:r><w:rPr><w:b /><w:bCs /></w:rPr><w:t>{word}</w:t></w:r>"
        '<w:r><w:rPr /><w:t xml:space="preserve"> </w:t></w:r>'
        f"<w:r><w:rPr><w:i /><w:iCs /></w:rPr><w:t>{word}</w:t></w:r>"
        "</w:p></w:body>"
    )

    # Footnotes follow the same rule
    doc._text = f"{word}[footnote:a]\n\n%footnote.a: English note.\n\n"
    doc.tokenizeText()
    doc.doConvert()
    doc._footnotesXml()
    assert '<w:pStyle w:val="FootnoteText" /><w:bidi w:val="0" />' in xmlToText(doc._files["footnotes.xml"].xml)

    # The document defaults and the section are RTL, with the gutter on the right
    doc.closeDocument()
    styles = xmlToText(doc._files["styles.xml"].xml)
    assert "<w:pPrDefault><w:pPr><w:bidi /><w:spacing " in styles
    assert '<w:lang w:val="en_GB" w:bidi="en_GB" />' in styles
    assert "<w:titlePg /><w:bidi /><w:rtlGutter /></w:sectPr>" in xmlToText(doc._files["document.xml"].xml)


@pytest.mark.core
def testToDocX_MinimalClose(mockGUI: MockGuiMain):
    """Test closing a document with no header format and no counts."""
    project = NWProject()
    doc = ToDocX(project)
    doc.initDocument()

    doc._text = "## Hello World"
    doc.tokenizeText()
    doc.doConvert()

    # No header format and no stats have been computed, so the header
    # and stats-dependent branches should all be skipped without error
    doc.closeDocument()
    assert "header1.xml" not in doc._files
    assert "footnotes.xml" not in doc._files
    assert "numbering.xml" not in doc._files

    xVars = doc._files["settings.xml"].xml.find(_wTag("docVars"))
    assert xVars is None
    assert doc._files["settings.xml"].xml.find(_wTag("mirrorMargins")) is None

    # Gutter and mirrored margins
    doc.setPageLayout(210.0, 297.0, 20.0, 20.0, 20.0, 20.0, 10.0, True)
    doc.closeDocument()
    assert doc._files["settings.xml"].xml[0].tag == _wTag("mirrorMargins")

    xMar = doc._files["document.xml"].xml.find(f"{_wTag('body')}/{_wTag('sectPr')}/{_wTag('pgMar')}")
    assert xMar is not None
    assert xMar.get(_wTag("left")) == "1133"
    assert xMar.get(_wTag("gutter")) == "566"

    # A header format consisting only of the page marker has no
    # leading or trailing text
    doc.setHeaderFormat(nwHeadFmt.DOC_PAGE, "", 0)
    doc.closeDocument()
    assert xmlToText(doc._files["header1.xml"].xml) == (
        '<w:hdr><w:p><w:pPr><w:pStyle w:val="Header" /><w:jc w:val="right" />'
        "<w:rPr /></w:pPr>"
        '<w:r><w:fldChar w:fldCharType="begin" /></w:r>'
        '<w:r><w:instrText xml:space="preserve">PAGE</w:instrText></w:r>'
        '<w:r><w:fldChar w:fldCharType="separate" /></w:r>'
        '<w:r><w:fldChar w:fldCharType="end" /></w:r>'
        "</w:p></w:hdr>"
    )

    # A header format without a page marker has no page field
    doc.setHeaderFormat("Just Text", "", 0)
    doc.closeDocument()
    assert xmlToText(doc._files["header1.xml"].xml) == (
        '<w:hdr><w:p><w:pPr><w:pStyle w:val="Header" /><w:jc w:val="right" />'
        "<w:rPr /></w:pPr>"
        "<w:r><w:t>Just Text</w:t></w:r>"
        "</w:p></w:hdr>"
    )


@pytest.mark.core
def testToDocX_DoublePages(mockGUI: MockGuiMain):
    """Test odd page sections and even page headers."""
    project = NWProject()
    doc = ToDocX(project)
    doc.setPageLayout(210.0, 297.0, 20.0, 20.0, 20.0, 20.0, 10.0, True)
    doc.setHeaderFormat("Odd", "Even", 1)
    doc.initDocument()
    doc._blocks = [
        (BlockTyp.TEXT, "", "Title page", [], BlockFmt.NONE),
        (BlockTyp.HEAD1, "", "Chapter One", [], BlockFmt.HBB),
        (BlockTyp.TEXT, "", "Text", [], BlockFmt.PBB),
        (BlockTyp.HEAD1, "", "Chapter Two", [], BlockFmt.PBB | BlockFmt.HBB),
    ]
    doc.doConvert()
    doc.closeDocument()

    xBody = doc._files["document.xml"].xml.find(_wTag("body"))
    assert xBody is not None
    page = (
        '<w:pgSz w:w="11905" w:h="16837" w:orient="portrait" />'
        '<w:pgMar w:top="1133" w:right="1133" w:bottom="1133" w:left="1133" '
        'w:header="748" w:footer="0" w:gutter="566" />'
    )
    notes = '<w:footnotePr><w:numFmt w:val="decimal" /></w:footnotePr>'
    heads = '<w:headerReference w:type="default" r:id="rId5" /><w:headerReference w:type="even" r:id="rId7" />'
    oddSection = f'<w:sectPr>{heads}{notes}<w:type w:val="oddPage" />{page}<w:pgNumType w:fmt="decimal" /></w:sectPr>'

    # The first section ends before the first odd page break, and
    # the following sections start on odd pages and continue numbering
    assert [xmlToText(x) for x in xBody] == [
        (
            '<w:p><w:pPr><w:pStyle w:val="Normal" />'
            f'<w:sectPr><w:headerReference w:type="first" r:id="rId6" />{heads}{notes}{page}'
            '<w:pgNumType w:start="0" w:fmt="decimal" /><w:titlePg /></w:sectPr>'
            "</w:pPr><w:r><w:rPr /><w:t>Title page</w:t></w:r></w:p>"
        ),
        '<w:p><w:pPr><w:pStyle w:val="Heading1" /></w:pPr><w:r><w:rPr /><w:t>Chapter One</w:t></w:r></w:p>',
        (
            f'<w:p><w:pPr><w:pStyle w:val="Normal" /><w:pageBreakBefore />{oddSection}'
            "</w:pPr><w:r><w:rPr /><w:t>Text</w:t></w:r></w:p>"
        ),
        '<w:p><w:pPr><w:pStyle w:val="Heading1" /></w:pPr><w:r><w:rPr /><w:t>Chapter Two</w:t></w:r></w:p>',
        oddSection,
    ]

    # The even page header is mirrored
    assert xmlToText(doc._files["header3.xml"].xml) == (
        '<w:hdr><w:p><w:pPr><w:pStyle w:val="Header" /><w:jc w:val="left" /><w:rPr /></w:pPr>'
        "<w:r><w:t>Even</w:t></w:r></w:p></w:hdr>"
    )

    # Even and odd headers are enabled
    xSett = doc._files["settings.xml"].xml
    assert xSett[0].tag == _wTag("mirrorMargins")
    assert xSett[1].tag == _wTag("defaultTabStop")
    assert xSett[2].tag == _wTag("evenAndOddHeaders")

    # Single pages have no even page header
    doc.setPageLayout(210.0, 297.0, 20.0, 20.0, 20.0, 20.0, 10.0, False)
    doc._files = {}
    doc.closeDocument()
    assert "header3.xml" not in doc._files
    assert doc._files["settings.xml"].xml.find(_wTag("evenAndOddHeaders")) is None


@pytest.mark.core
def testToDocX_ParagraphEdgeCases():
    """Test edge cases of the DocXParagraph class."""
    par = DocXParagraph()

    # An invalid alignment value is ignored
    par.setAlignment("diagonal")  # type: ignore
    assert par._textAlign is None

    # A paragraph without a style produces no XML
    xTest = ET.Element(_wTag("body"))
    par.toXml(xTest)
    assert len(xTest) == 0


@pytest.mark.core
def testToDocX_SaveDocument(mockGUI: MockGuiMain, prjLipsum: Path, fncPath: Path, tstPaths: TstPaths):
    """Test document output."""
    project = NWProject()
    project.openProject(prjLipsum)

    pageHeader = f"Page {nwHeadFmt.DOC_PAGE} - {nwHeadFmt.DOC_PROJECT} ({nwHeadFmt.DOC_AUTHOR})"

    build = BuildSettings()
    build.setValue("filter.includeNovel", True)
    build.setValue("filter.includeNotes", True)
    build.setValue("filter.includeInactive", False)
    build.setValue("text.includeSynopsis", True)
    build.setValue("text.includeComments", True)
    build.setValue("text.includeKeywords", True)
    build.setValue("format.textFont", "Source Sans Pro,12")
    build.setValue("format.firstLineIndent", True)
    build.setValue("format.justifyOnBreak", False)
    build.setValue("doc.pageHeader", pageHeader)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    docPath = fncPath / "document.docx"
    assert list(docBuild.iterBuildDocument(docPath, nwBuildFmt.DOCX)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
        (8, True),
        (9, True),
        (10, True),
        (11, True),
        (12, True),
        (13, True),
        (14, True),
        (15, True),
        (16, True),
        (17, True),
    ]

    assert docPath.exists()
    assert zipfile.is_zipfile(docPath)

    with zipfile.ZipFile(docPath, mode="r") as zipObj:
        zipObj.extractall(fncPath / "extract")

    def prettifyXml(inFile: Path, outFile: Path) -> None:
        with open(outFile, mode="wb") as fStream:
            xml = ET.parse(inFile)
            xmlIndent(xml)  # type: ignore
            xml.write(fStream, encoding="utf-8", xml_declaration=True)

    expected = [
        fncPath / "extract" / "[Content_Types].xml",
        fncPath / "extract" / "_rels" / ".rels",
        fncPath / "extract" / "docProps" / "app.xml",
        fncPath / "extract" / "docProps" / "core.xml",
        fncPath / "extract" / "word" / "_rels" / "document.xml.rels",
        fncPath / "extract" / "word" / "document.xml",
        fncPath / "extract" / "word" / "footnotes.xml",
        fncPath / "extract" / "word" / "header1.xml",
        fncPath / "extract" / "word" / "header2.xml",
        fncPath / "extract" / "word" / "settings.xml",
        fncPath / "extract" / "word" / "styles.xml",
        fncPath / "extract" / "word" / "fontTable.xml",
    ]

    outDir = tstPaths.outDir / "fmtToDocX_SaveDocument"
    outDir.mkdir()
    for file in expected:
        assert file.is_file()
        name = file.name.replace("[", "").replace("]", "").lstrip(".")
        outFile = outDir / name
        refFile = tstPaths.refDir / f"fmtToDocX_SaveDocument_{name}"
        prettifyXml(file, outFile)
        assert cmpFiles(outFile, refFile, ignStart=DOCX_IGNORE)


@pytest.mark.core
def testToDocX_MkTag():
    """Test the tag maker function."""
    assert _mkTag("r", "id") == f"{{{OOXML_SCM}/officeDocument/2006/relationships}}id"
    assert _mkTag("w", "t") == f"{{{OOXML_SCM}/wordprocessingml/2006/main}}t"
    assert _mkTag("q", "t") == "t"
