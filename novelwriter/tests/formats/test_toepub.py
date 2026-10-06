"""
novelWriter - EPub Format Tests
===============================

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

import zipfile

from shutil import copyfile

import pytest

from novelwriter.constants import nwHeadFmt, nwUnicode
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp
from novelwriter.formats.toepub import EPubType, ToEPub, _mkTag

from tests.helpers import EPUB_IGNORE, cmpFiles


@pytest.mark.core
def testFmtToEPub_MkTag():
    """Test the tag maker function."""
    assert _mkTag("dc", "text") == "{http://purl.org/dc/elements/1.1/}text"
    assert _mkTag("xml", "text") == "{http://www.w3.org/XML/1998/namespace}text"
    assert _mkTag("blabla", "text") == "text"


@pytest.mark.core
def testToEPub_ConvertNovelHeaders(mockGUI):
    """Test header formats in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()

    epub._isNovel = True
    epub._isFirst = True

    # Partition
    epub._text = "# Title\n"
    epub.setPartitionFormat(f"Part{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.PART
    assert epub._sections[-1].title == "Part<br />Title"

    # Chapter
    epub._text = "## Title\n"
    epub.setChapterFormat(f"Chapter {nwHeadFmt.CH_NUM}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.CHAPTER
    assert epub._sections[-1].title == "Chapter 1<br />Title"

    # Scene
    epub._text = "### Title\n"
    epub.setSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h2>Scene 1<br />Title</h2>"

    # Section
    epub._text = "#### Title\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h3>Title</h3>"

    # Title
    epub._text = "#! Title\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.PART
    assert epub._sections[-1].title == "Title"

    # Unnumbered
    epub._text = "##! Prologue\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.CHAPTER
    assert epub._sections[-1].title == "Prologue"

    # Alt Scene
    epub._text = "###! Title\n"
    epub.setHardSceneFormat(f"Scene {nwHeadFmt.SC_ABS}{nwHeadFmt.BR}{nwHeadFmt.TITLE}")
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h2>Scene 1<br />Title</h2>"


@pytest.mark.core
def testToEPub_ConvertNotesHeaders(mockGUI):
    """Test note header formats in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()

    epub._isNovel = False
    epub._isFirst = True

    # Heading 1
    epub._text = "# Heading One\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h1>Heading One</h1>"

    # Heading 2
    epub._text = "## Heading Two\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h2>Heading Two</h2>"

    # Heading 3
    epub._text = "### Heading Three\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h3>Heading Three</h3>"

    # Heading 4
    epub._text = "#### Heading Four\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h4>Heading Four</h4>"

    # Title
    epub._text = "#! Heading One\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h1 style='text-align: center; page-break-before: always;'>Heading One</h1>"

    # Alt Heading 2
    epub._text = "##! Heading Two\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h2>Heading Two</h2>"

    # Alt Heading 3
    epub._text = "###! Heading Three\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h3>Heading Three</h3>"


@pytest.mark.core
def testToEPub_ConvertParagraphs(mockGUI):
    """Test paragraph formats in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()
    epub._isNovel = True
    epub._isFirst = True

    # Text
    epub._text = "Some **nested bold and _italic_ and ~~strikethrough~~ text** here\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p>Some <strong>nested bold and <em>italic</em> and <del>strikethrough</del> text</strong> here</p>"
    )

    # Shortcodes
    epub._text = (
        "Some [b]bold[/b], [i]italic[/i], [s]strike[/s], [u]underline[/u], [m]mark[/m], "
        "super[sup]script[/sup], sub[sub]script[/sub] here\n"
    )
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p>Some <strong>bold</strong>, <em>italic</em>, <del>strike</del>, "
        "<span style='text-decoration: underline;'>underline</span>, <mark>mark</mark>, "
        "super<sup>script</sup>, sub<sub>script</sub> here</p>"
    )

    # Text w/Hard Break
    epub._text = "Line one\nLine two\nLine three\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p>Line one<br />Line two<br />Line three</p>"

    # Synopsis, Short, and plain comments
    nText = len(epub._sections[-1].text)

    epub._text = "%synopsis: The synopsis ...\n"
    epub.tokenizeText()
    epub.doConvert()
    assert len(epub._sections[-1].text) == nText

    epub.setCommentType(nwComment.SYNOPSIS, True)
    epub._text = "%synopsis: The synopsis ...\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='comment'>"
        "<strong><span style='color: #813709'>Synopsis:</span></strong> "
        "<span style='color: #813709'>The synopsis ...</span>"
        "</p>\n"
    )

    epub.setCommentType(nwComment.SHORT, True)
    epub._text = "%short: A short description ...\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='comment'>"
        "<strong><span style='color: #813709'>Short Description:</span></strong> "
        "<span style='color: #813709'>A short description ...</span>"
        "</p>\n"
    )

    epub._text = "% A comment ...\n"
    epub.tokenizeText()
    epub.doConvert()
    assert len(epub._sections[-1].text) == nText + 2

    epub.setCommentType(nwComment.PLAIN, True)
    epub._text = "% A comment ...\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='comment'>"
        "<strong><span style='color: #646464'>Comment:</span></strong> "
        "<span style='color: #646464'>A comment ...</span>"
        "</p>\n"
    )


@pytest.mark.core
def testToEPub_ConvertMeta(mockGUI):
    """Test meta data formats in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()
    epub._isNovel = True
    epub._isFirst = True

    # Keywords Disabled
    epub.setKeywords(False)
    nText = len(epub._sections[-1].text)
    epub._text = "@char: Bod, Jane\n"
    epub.tokenizeText()
    epub.doConvert()
    assert len(epub._sections[-1].text) == nText

    # Keywords Enabled
    epub.setKeywords(True)
    epub._text = "@char: Bod, Jane\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='meta meta-char'><strong><span style='color: #f5871f'>"
        "Characters:</span></strong> "
        "<span style='color: #4271ae'>Bod</span>, "
        "<span style='color: #4271ae'>Jane</span></p>\n"
    )

    # Tags w/Colour
    epub.setStyles(True)
    epub._text = "@tag: Bod\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='meta meta-tag'><strong><span style='color: #f5871f'>Tag:</span></strong> "
        "<span style='color: #4271ae'>Bod</span></p>\n"
    )

    epub._text = "@tag: Bod | Nobody Owens\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p class='meta meta-tag'><strong><span style='color: #f5871f'>Tag:</span></strong> "
        "<span style='color: #4271ae'>Bod</span> | "
        "<span style='color: #4271ae'>Nobody Owens</span></p>\n"
    )

    # Tags wo/Colour
    epub.setStyles(False)
    epub._text = "@tag: Bod\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p class='meta meta-tag'><strong>Tag:</strong> Bod</p>\n"

    epub._text = "@tag: Bod | Nobody Owens\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p class='meta meta-tag'><strong>Tag:</strong> Bod | Nobody Owens</p>\n"

    # Multiple Keywords w/Colour
    epub.setStyles(True)
    epub._isFirst = False
    epub.setKeywords(True)
    epub._text = "## Chapter\n\n@pov: Bod\n@plot: Main\n@location: Europe\n\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].title == "Chapter"
    assert epub._sections[-1].text[-3:] == [
        (
            "<p class='meta meta-pov' style='margin-bottom: 0;'><strong><span style='color: #f5871f'>"
            "Point of View:</span></strong> <span style='color: #4271ae'>Bod</span></p>\n"
        ),
        (
            "<p class='meta meta-plot' style='margin-bottom: 0; margin-top: 0;'><strong><span style='color: #f5871f'>"
            "Plot:</span></strong> <span style='color: #4271ae'>Main</span></p>\n"
        ),
        (
            "<p class='meta meta-location' style='margin-top: 0;'><strong><span style='color: #f5871f'>"
            "Locations:</span></strong> <span style='color: #4271ae'>Europe</span></p>\n"
        ),
    ]

    # Multiple Keywords wo/Colour
    epub.setStyles(False)
    epub._isFirst = False
    epub.setKeywords(True)
    epub._text = "## Chapter\n\n@pov: Bod\n@plot: Main\n@location: Europe\n\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].title == "Chapter"
    assert epub._sections[-1].text[-3:] == [
        "<p class='meta meta-pov' style='margin-bottom: 0;'><strong>Point of View:</strong> Bod</p>\n",
        "<p class='meta meta-plot' style='margin-bottom: 0; margin-top: 0;'><strong>Plot:</strong> Main</p>\n",
        "<p class='meta meta-location' style='margin-top: 0;'><strong>Locations:</strong> Europe</p>\n",
    ]


@pytest.mark.core
def testToEPub_Alignment(mockGUI):
    """Test paragraph alignment in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()

    # Left
    epub._text = "This is text <<\nspanning multiple\nlines"
    epub.tokenizeText()
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1] == "<p style='text-align: left;'>This is text<br />spanning multiple<br />lines</p>"
    )

    # Right
    epub._text = ">> This is text\nspanning multiple\nlines"
    epub.tokenizeText()
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1]
        == "<p style='text-align: right;'>This is text<br />spanning multiple<br />lines</p>"
    )

    # Centre
    epub._text = ">> This is text <<\nspanning multiple\nlines"
    epub.tokenizeText()
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1]
        == "<p style='text-align: center;'>This is text<br />spanning multiple<br />lines</p>"
    )

    # Left before Right
    epub._text = ">> This is text\nspanning multiple <<\nlines"
    epub.tokenizeText()
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1] == "<p style='text-align: left;'>This is text<br />spanning multiple<br />lines</p>"
    )

    # Right before Centre
    epub._text = ">> This is text <<\n>> spanning multiple\nlines"
    epub.tokenizeText()
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1]
        == "<p style='text-align: right;'>This is text<br />spanning multiple<br />lines</p>"
    )


@pytest.mark.core
def testToEPub_Footnotes(mockGUI):
    """Test paragraph formats with footnotes in the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()
    epub._isNovel = True
    epub._isFirst = True

    epub._text = "Text with one[footnote:fa] or two[footnote:fb] footnotes.\n\n%footnote.fa: Footnote text A.\n\n"
    epub.tokenizeText()
    epub.doConvert()
    assert epub._sections[-1].text[-1] == (
        "<p>Text with one<sup><a epub:type='noteref' href='#fn_1' id='fns_1'>1</a></sup> "
        "or two<sup>ERR</sup> footnotes.</p>"
    )
    assert epub._sections[-1].footnotes == [
        "<aside epub:type='footnote' id='fn_1'><p><a href='#fns_1'>1.</a> Footnote text A.</p></aside>"
    ]


@pytest.mark.core
def testToEPub_CloseDocument(mockGUI, fncPath):
    """Test pruning of empty sections and field substitution on close/save."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()
    epub._isNovel = True

    # A document with no leading title or text leaves the initial front
    # matter section empty, and it should be pruned on close
    epub._text = "## Chapter One\n\n[field:allWords] words[field:unknownField]\n\n"
    epub.tokenizeText()
    epub.doConvert()
    epub.countStats()
    epub.closeDocument()
    assert len(epub._sections) == 1
    assert epub._sections[0].epubType == EPubType.CHAPTER

    # An unknown field is left untouched, since there is no matching count
    epub.saveDocument(fncPath / "closeDocument.epub")
    assert epub._sections[0].text[-1] == "<p>3 words{{unknownField}}</p>"

    # With no fields used, the substitution step is skipped entirely
    epub2 = ToEPub(project)
    epub2.initDocument()
    epub2._text = "## Chapter One\n\nSome text\n\n"
    epub2.tokenizeText()
    epub2.doConvert()
    epub2.closeDocument()
    epub2.saveDocument(fncPath / "closeDocumentNoFields.epub")
    assert epub2._sections[0].text[-1] == "<p>Some text</p>"


@pytest.mark.core
def testToEPub_ConvertDirect(mockGUI):
    """Test the converter directly using the ToEPub class."""
    project = NWProject()
    epub = ToEPub(project)
    epub.initDocument()

    epub._isNovel = True

    # Frontmatter title
    epub._blocks = [
        (BlockTyp.TITLE, "", "A Title", [], BlockFmt.PBB | BlockFmt.CENTRE),
    ]
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.FRONTMATTER
    assert epub._sections[-1].text[-1] == "<h1 style='text-align: center; page-break-before: always;'>A Title</h1>"

    # Part starts new section with title
    epub._blocks = [
        (BlockTyp.PART, "", "A Part", [], BlockFmt.CENTRE),
    ]
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.PART
    assert epub._sections[-1].title == "A Part"

    # Chapter starts new section with title
    epub._blocks = [
        (BlockTyp.HEAD1, "", "Chapter One", [], BlockFmt.PBB),
    ]
    epub.doConvert()
    assert epub._sections[-1].epubType == EPubType.CHAPTER
    assert epub._sections[-1].title == "Chapter One"

    # Headings
    epub._blocks = [
        (BlockTyp.HEAD2, "", "Scene One", [], BlockFmt.NONE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h2>Scene One</h2>"

    epub._blocks = [
        (BlockTyp.HEAD3, "", "Section One", [], BlockFmt.NONE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h3>Section One</h3>"

    epub._blocks = [
        (BlockTyp.HEAD4, "", "Subsection One", [], BlockFmt.NONE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<h4>Subsection One</h4>"

    # Separator, rule and skip
    epub._blocks = [
        (BlockTyp.SEP, "", "* * *", [], BlockFmt.CENTRE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p class='sep'>* * *</p>"

    epub._blocks = [
        (BlockTyp.HRULE, "", "", [], BlockFmt.CENTRE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<hr style='text-align: center;'/>"

    epub._blocks = [
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == f"<p>{nwUnicode.U_NBSP}</p>"

    # Alignment
    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.LEFT),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='text-align: left;'>Some text ...</p>"

    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.RIGHT),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='text-align: right;'>Some text ...</p>"

    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.CENTRE),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='text-align: center;'>Some text ...</p>"

    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.JUSTIFY),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='text-align: justify;'>Some text ...</p>"

    # Page break
    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.PBB | BlockFmt.PBA),
    ]
    epub.doConvert()
    assert (
        epub._sections[-1].text[-1]
        == "<p style='page-break-before: always; page-break-after: always;'>Some text ...</p>"
    )

    # Indent
    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.IND_L),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='margin-left: 4.00em;'>Some text ...</p>"

    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.IND_R),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='margin-right: 4.00em;'>Some text ...</p>"

    epub._blocks = [
        (BlockTyp.TEXT, "", "Some text ...", [], BlockFmt.IND_T),
    ]
    epub.doConvert()
    assert epub._sections[-1].text[-1] == "<p style='text-indent: 1.40em;'>Some text ...</p>"


@pytest.mark.core
def testToEPub_Save(mockGUI, fncPath, tstPaths, ipsumText):
    """Test the save method of the ToEPub class."""
    project = NWProject()
    project.data.setAuthor("Jane Smith")

    epub = ToEPub(project)
    epub.initDocument()
    epub._isNovel = True

    epub._text = (
        "#! My Novel\n\n"
        "**Word Count: [field:allWords]**\n"
        "[field:paragraphCount] paragraphs\n"
        "Web: http://example.com\n\n"
        "## Chapter One\n\n"
        f"{ipsumText[0]}\n\n"
        "## Chapter Two\n\n"
        f"{ipsumText[1]}[footnote:abc]\n\n"
        "%Footnote.abc: Lorem ipsum\n\n"
    )
    epub.tokenizeText()
    epub.initDocument()
    epub.doConvert()
    epub.countStats()
    epub.closeDocument()

    saveFile = fncPath / "outFile.epub"
    epub.saveDocument(saveFile)
    assert saveFile.exists()
    assert zipfile.is_zipfile(saveFile)

    extaxtTo = tstPaths.outDir / "fmtToEPub_SaveFull"
    with zipfile.ZipFile(saveFile, mode="r") as zipObj:
        assert sorted(zipObj.namelist()) == [
            "META-INF/container.xml",
            "OEBPS/nav.xhtml",
            "OEBPS/package.opf",
            "OEBPS/styles/stylesheet.css",
            "OEBPS/toc.ncx",
            "OEBPS/xhtml/chapter1.xhtml",
            "OEBPS/xhtml/chapter2.xhtml",
            "OEBPS/xhtml/frontmatter1.xhtml",
            "mimetype",
        ]
        for file in zipObj.namelist():
            zipObj.extract(file, extaxtTo)

    navOut = extaxtTo / "OEBPS" / "nav.xhtml"
    opfOut = extaxtTo / "OEBPS" / "package.opf"
    cssOut = extaxtTo / "OEBPS" / "styles" / "stylesheet.css"
    tocOut = extaxtTo / "OEBPS" / "toc.ncx"
    ch1Out = extaxtTo / "OEBPS" / "xhtml" / "chapter1.xhtml"
    ch2Out = extaxtTo / "OEBPS" / "xhtml" / "chapter2.xhtml"
    fm1Out = extaxtTo / "OEBPS" / "xhtml" / "frontmatter1.xhtml"

    navFile = tstPaths.outDir / "fmtToEPub_Save_nav.xhtml"
    opfFile = tstPaths.outDir / "fmtToEPub_Save_package.opf"
    cssFile = tstPaths.outDir / "fmtToEPub_Save_stylesheet.css"
    tocFile = tstPaths.outDir / "fmtToEPub_Save_toc.ncx"
    ch1File = tstPaths.outDir / "fmtToEPub_Save_chapter1.xhtml"
    ch2File = tstPaths.outDir / "fmtToEPub_Save_chapter2.xhtml"
    fm1File = tstPaths.outDir / "fmtToEPub_Save_frontmatter1.xhtml"

    navComp = tstPaths.refDir / "fmtToEPub_Save_nav.xhtml"
    opfComp = tstPaths.refDir / "fmtToEPub_Save_package.opf"
    cssComp = tstPaths.refDir / "fmtToEPub_Save_stylesheet.css"
    tocComp = tstPaths.refDir / "fmtToEPub_Save_toc.ncx"
    ch1Comp = tstPaths.refDir / "fmtToEPub_Save_chapter1.xhtml"
    ch2Comp = tstPaths.refDir / "fmtToEPub_Save_chapter2.xhtml"
    fm1Comp = tstPaths.refDir / "fmtToEPub_Save_frontmatter1.xhtml"

    copyfile(navOut, navFile)
    copyfile(opfOut, opfFile)
    copyfile(cssOut, cssFile)
    copyfile(tocOut, tocFile)
    copyfile(ch1Out, ch1File)
    copyfile(ch2Out, ch2File)
    copyfile(fm1Out, fm1File)

    assert cmpFiles(navFile, navComp)
    assert cmpFiles(opfFile, opfComp, ignStart=EPUB_IGNORE)
    assert cmpFiles(cssFile, cssComp)
    assert cmpFiles(tocFile, tocComp)
    assert cmpFiles(ch1File, ch1Comp)
    assert cmpFiles(ch2File, ch2Comp)
    assert cmpFiles(fm1File, fm1Comp)
