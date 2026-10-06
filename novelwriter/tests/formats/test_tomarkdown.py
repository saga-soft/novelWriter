"""
novelWriter - Markdown Format Tests
===================================

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

import pytest

from novelwriter.constants import nwHeadFmt
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp
from novelwriter.formats.tomarkdown import ToMarkdown


@pytest.mark.core
def testToMarkdown_ConvertNovelHeaders(mockGUI):
    """Test header formats in the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)

    md._isNovel = True
    md._isFirst = True

    # Partition
    md._text = "# Title\n"
    md.setPartitionFormat(f"Part{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Part - Title\n============\n\n"

    # Chapter
    md._text = "## Title\n"
    md.setChapterFormat(f"Chapter {nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "# Chapter 1 - Title\n\n"

    # Scene
    md._text = "### Title\n"
    md.setSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "## Scene 1 - Title\n\n"

    # Section
    md._text = "#### Section Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "### Section Title\n\n"

    # Title
    md._text = "#! Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Title\n=====\n\n"

    # Unnumbered
    md._text = "##! Prologue\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "# Prologue\n\n"

    # Alt Scene
    md._text = "###! Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "## Title\n\n"


@pytest.mark.core
def testToMarkdown_ConvertNotesHeaders(mockGUI):
    """Test header formats in the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)

    md._isNovel = False
    md._isFirst = True

    # Heading 1
    md._text = "# Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "# Title\n\n"

    # Heading 2
    md._text = "## Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "## Title\n\n"

    # Heading 3
    md._text = "### Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "### Title\n\n"

    # Heading 4
    md._text = "#### Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "#### Title\n\n"

    # Title
    md._text = "#! Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Title\n=====\n\n"

    # Alt Heading 2
    md._text = "##! Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "## Title\n\n"

    # Alt Heading 3
    md._text = "###! Title\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "### Title\n\n"


@pytest.mark.core
def testToMarkdown_ConvertParagraphs(mockGUI):
    """Test paragraph formats in the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)

    md._isNovel = True
    md._isFirst = True

    # Text for Extended Markdown
    md._extended = True
    md._text = "Some **nested bold and _italic_ and ~~strikethrough~~ text** here\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("Some **nested bold and _italic_ and ~~strikethrough~~ text** here\n\n")

    # Text for Standard Markdown
    md._extended = False
    md._text = "Some **nested bold and _italic_ and ~~strikethrough~~ text** here\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("Some **nested bold and _italic_ and strikethrough text** here\n\n")

    # Shortcodes for Extended Markdown
    md._extended = True
    md._text = (
        "Some [b]bold[/b], [i]italic[/i], [s]strike[/s], [u]underline[/u], [m]mark[/m], "
        "super[sup]script[/sup], sub[sub]script[/sub] here\n"
    )
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "Some **bold**, _italic_, ~~strike~~, underline, ==mark==, super^script^, sub~script~ here\n\n"
    )

    # Shortcodes for Standard Markdown
    md._extended = False
    md._text = (
        "Some [b]bold[/b], [i]italic[/i], [s]strike[/s], [u]underline[/u], [m]mark[/m], "
        "super[sup]script[/sup], sub[sub]script[/sub] here\n"
    )
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("Some **bold**, _italic_, strike, underline, mark, superscript, subscript here\n\n")

    # Text w/Hard Break
    md._text = "Line one\nLine two\nLine three\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Line one  \nLine two  \nLine three\n\n"

    # Text wo/Hard Break
    md._text = "Line one\nLine two\nLine three\n"
    md.setKeepLineBreaks(False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Line one Line two Line three\n\n"

    # Synopsis, Short
    md._text = "%synopsis: The synopsis ...\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ""

    md.setCommentType(nwComment.SYNOPSIS, True)
    md._text = "%synopsis: The synopsis ...\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "**Synopsis:** The synopsis ...\n\n"

    md.setCommentType(nwComment.SHORT, True)
    md._text = "%short: A description ...\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "**Short Description:** A description ...\n\n"

    # Comment
    md._text = "% A comment ...\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ""

    md.setCommentType(nwComment.PLAIN, True)
    md._text = "% A comment ...\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "**Comment:** A comment ...\n\n"

    # Keywords
    md._text = "@char: Bod, Jane\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ""

    md.setKeywords(True)
    md._text = "@char: Bod, Jane\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "**Characters:** Bod, Jane\n\n"

    # Multiple Keywords
    md.setKeywords(True)
    md._text = "## Chapter\n\n@pov: Bod\n@plot: Main\n@location: Europe\n\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("# Chapter\n\n**Point of View:** Bod  \n**Plot:** Main  \n**Locations:** Europe\n\n")

    # Footnotes
    md._text = "Text with one[footnote:fa] or two[footnote:fb] footnotes.\n\n%footnote.fa: Footnote text A.\n\n"
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == "Text with one[1] or two[ERR] footnotes.\n\n"

    md.closeDocument()
    assert md._pages[-2] == ("Text with one[1] or two[ERR] footnotes.\n\n")
    assert md._pages[-1] == ("### Footnotes\n\n1. Footnote text A.\n\n")


@pytest.mark.core
def testToMarkdown_Fields(mockGUI):
    """Test field substitution in the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)
    md.initDocument()

    # A known field is substituted, an unknown one is left untouched
    md._text = "Word Count: [field:allWords], Unknown: [field:unknownField]\n"
    md.tokenizeText()
    md.doConvert()
    md.countStats()
    md.closeDocument()
    assert md._pages[-1] == "Word Count: 4, Unknown: {{unknownField}}\n\n"


@pytest.mark.core
def testToMarkdown_ConvertDirect(mockGUI):
    """Test the converter directly using the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)
    md._isNovel = True

    # Special Titles
    # ==============

    # Title
    md._blocks = [
        (BlockTyp.TITLE, "", "A Title", [], BlockFmt.PBB | BlockFmt.CENTRE),
    ]
    md.doConvert()
    assert md._pages[-1] == "A Title\n=======\n\n"

    # Separators
    # ==========

    # Separator
    md._blocks = [
        (BlockTyp.SEP, "", "* * *", [], BlockFmt.CENTRE),
    ]
    md.doConvert()
    assert md._pages[-1] == "* * *\n\n"

    # Horizontal Rule
    md._blocks = [
        (BlockTyp.HRULE, "", "", [], BlockFmt.CENTRE),
    ]
    md.doConvert()
    assert md._pages[-1] == "----\n\n"

    # Skip
    md._blocks = [
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]
    md.doConvert()
    assert md._pages[-1] == "\n\n"


@pytest.mark.core
def testToMarkdown_Save(mockGUI, fncPath):
    """Test the save method of the ToMarkdown class."""
    project = NWProject()
    md = ToMarkdown(project, False)
    md._isNovel = True

    # Build Project
    # =============

    docText = [
        "# My Novel\n\n**By Jane Doh**\n",
        "## Chapter 1\n\nThe text of chapter one.\n",
        "### Scene 1\n\nThe text of scene one.\n",
        "#### A Section\n\nMore text in scene one.\n",
        "## Chapter 2\n\nThe text of chapter two.\n",
        "### Scene 2\n\nThe text of scene two.\n",
        "#### A Section\n\n\tMore text in scene two.\n",
    ]
    resText = [
        "My Novel\n========\n\n**By Jane Doh**\n\n",
        "# Chapter 1\n\nThe text of chapter one.\n\n",
        "## Scene 1\n\nThe text of scene one.\n\n",
        "### A Section\n\nMore text in scene one.\n\n",
        "# Chapter 2\n\nThe text of chapter two.\n\n",
        "## Scene 2\n\nThe text of scene two.\n\n",
        "### A Section\n\n\tMore text in scene two.\n\n",
    ]

    for i in range(len(docText)):
        md._text = docText[i]
        md.doPreProcessing()
        md.tokenizeText()
        md.doConvert()

    assert md._pages == resText
    assert sum(len(x) for x in md._pages) == len("".join(resText))

    md.replaceTabs(nSpaces=4, spaceChar=" ")
    resText[6] = "### A Section\n\n    More text in scene two.\n\n"
    assert md._pages == resText

    # Check File
    # ==========

    saveFile = fncPath / "outFile.md"
    md.saveDocument(saveFile)
    assert saveFile.read_text(encoding="utf-8") == "".join(resText)
