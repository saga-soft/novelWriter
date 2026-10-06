"""
novelWriter - Text Tokenizer Tests
==================================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtGui import QFont

from novelwriter import CONFIG
from novelwriter.constants import nwHeadFmt, nwStyles
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment
from novelwriter.formats.shared import BlockFmt, BlockTyp, TextFmt, stripEscape
from novelwriter.formats.tokenizer import COMMENT_STYLE, HeadingFormatter, Tokenizer
from novelwriter.formats.tomarkdown import ToMarkdown

from tests.helpers import C, buildTestProject

TMH = "0123456789abc"
TM1 = f"{TMH}:T0001"
TM2 = f"{TMH}:T0002"


class BareTokenizer(Tokenizer):
    def doConvert(self):
        super().doConvert()  # type: ignore (deliberate check)

    def closeDocument(self):
        super().closeDocument()  # type: ignore (deliberate check)

    def saveDocument(self, path) -> None:
        super().saveDocument(path)  # type: ignore (deliberate check)


@pytest.mark.core
def testTokenizer_Abstracts(mockGUI, tstPaths):
    """Test all the abstract methods of the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)

    with pytest.raises(NotImplementedError):
        tokens.doConvert()

    with pytest.raises(NotImplementedError):
        tokens.closeDocument()

    with pytest.raises(NotImplementedError):
        tokens.saveDocument(tstPaths)


@pytest.mark.core
def testTokenizer_Setters(mockGUI):
    """Test all the setters for the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)

    # Verify defaults
    assert tokens._fmtPart == nwHeadFmt.TITLE
    assert tokens._fmtChapter == nwHeadFmt.TITLE
    assert tokens._fmtUnNum == nwHeadFmt.TITLE
    assert tokens._fmtScene == nwHeadFmt.TITLE
    assert tokens._fmtHScene == nwHeadFmt.TITLE
    assert tokens._fmtSection == nwHeadFmt.TITLE
    assert tokens._textFont == QFont("Serif", 11)
    assert tokens._lineHeight == 1.15
    assert tokens._blockIndent == 4.0
    assert tokens._doJustify is False
    assert tokens._marginTitle == nwStyles.T_MARGIN["H0"]
    assert tokens._marginHead1 == nwStyles.T_MARGIN["H1"]
    assert tokens._marginHead2 == nwStyles.T_MARGIN["H2"]
    assert tokens._marginHead3 == nwStyles.T_MARGIN["H3"]
    assert tokens._marginHead4 == nwStyles.T_MARGIN["H4"]
    assert tokens._marginSep == nwStyles.T_MARGIN["SP"]
    assert tokens._marginText == nwStyles.T_MARGIN["TT"]
    assert tokens._marginMeta == nwStyles.T_MARGIN["MT"]
    assert tokens._sizeTitle == nwStyles.H_SIZES[0]
    assert tokens._sizeHead1 == nwStyles.H_SIZES[1]
    assert tokens._sizeHead2 == nwStyles.H_SIZES[2]
    assert tokens._sizeHead3 == nwStyles.H_SIZES[3]
    assert tokens._sizeHead4 == nwStyles.H_SIZES[4]
    assert tokens._hidePart is False
    assert tokens._hideChapter is False
    assert tokens._hideUnNum is False
    assert tokens._hideScene is False
    assert tokens._hideHScene is False
    assert tokens._hideSection is False
    assert tokens._linkHeadings is False
    assert tokens._doBodyText is True
    assert tokens._doComments == {nwComment.FOOTNOTE}
    assert tokens._doKeywords is False

    # Set new values
    tokens.setPartitionFormat(f"T: {nwHeadFmt.TITLE}", True)
    tokens.setChapterFormat(f"C: {nwHeadFmt.TITLE}", True)
    tokens.setUnNumberedFormat(f"U: {nwHeadFmt.TITLE}", True)
    tokens.setSceneFormat(f"S: {nwHeadFmt.TITLE}", True)
    tokens.setHardSceneFormat(f"H: {nwHeadFmt.TITLE}", True)
    tokens.setSectionFormat(f"X: {nwHeadFmt.TITLE}", True)
    tokens.setTextFont(QFont("Monospace", 10))
    tokens.setLineHeight(2.0)
    tokens.setBlockIndent(6.0)
    tokens.setJustify(True, False)
    tokens.setTitleProperties(2.0, 2.0, 8.0)
    tokens.setHead1Properties(2.0, 2.0, 7.0)
    tokens.setHead2Properties(2.0, 2.0, 6.0)
    tokens.setHead3Properties(2.0, 2.0, 5.0)
    tokens.setHead4Properties(2.0, 2.0, 4.0)
    tokens.setTextProperties(2.0, 2.0)
    tokens.setMetaProperties(2.0, 2.0)
    tokens.setSeparatorProperties(2.0, 2.0)
    tokens.setLinkHeadings(True)
    tokens.setBodyText(False)
    tokens.setCommentType(nwComment.PLAIN, True)
    tokens.setCommentType(nwComment.SHORT, True)
    tokens.setCommentType(nwComment.SYNOPSIS, True)
    tokens.setKeywords(True)

    # Check new values
    assert tokens._fmtPart == f"T: {nwHeadFmt.TITLE}"
    assert tokens._fmtChapter == f"C: {nwHeadFmt.TITLE}"
    assert tokens._fmtUnNum == f"U: {nwHeadFmt.TITLE}"
    assert tokens._fmtScene == f"S: {nwHeadFmt.TITLE}"
    assert tokens._fmtHScene == f"H: {nwHeadFmt.TITLE}"
    assert tokens._fmtSection == f"X: {nwHeadFmt.TITLE}"
    assert tokens._textFont == QFont("Monospace", 10)
    assert tokens._lineHeight == 2.0
    assert tokens._blockIndent == 6.0
    assert tokens._doJustify is True
    assert tokens._marginTitle == (2.0, 2.0)
    assert tokens._marginHead1 == (2.0, 2.0)
    assert tokens._marginHead2 == (2.0, 2.0)
    assert tokens._marginHead3 == (2.0, 2.0)
    assert tokens._marginHead4 == (2.0, 2.0)
    assert tokens._marginText == (2.0, 2.0)
    assert tokens._marginMeta == (2.0, 2.0)
    assert tokens._marginSep == (2.0, 2.0)
    assert tokens._sizeTitle == 8.0
    assert tokens._sizeHead1 == 7.0
    assert tokens._sizeHead2 == 6.0
    assert tokens._sizeHead3 == 5.0
    assert tokens._sizeHead4 == 4.0
    assert tokens._hidePart is True
    assert tokens._hideChapter is True
    assert tokens._hideUnNum is True
    assert tokens._hideScene is True
    assert tokens._hideHScene is True
    assert tokens._hideSection is True
    assert tokens._linkHeadings is True
    assert tokens._doBodyText is False
    assert tokens._doComments == {
        nwComment.FOOTNOTE,
        nwComment.PLAIN,
        nwComment.SYNOPSIS,
        nwComment.SHORT,
    }
    assert tokens._doKeywords is True

    # Properties
    assert tokens.textStats == {}
    assert tokens.errData == []

    # Check Limits
    tokens.setLineHeight(0.0)
    assert tokens._lineHeight == 0.5
    tokens.setLineHeight(10.0)
    assert tokens._lineHeight == 5.0

    tokens.setBlockIndent(-6.0)
    assert tokens._blockIndent == 0.0
    tokens.setBlockIndent(60.0)
    assert tokens._blockIndent == 10.0


@pytest.mark.core
def testTokenizer_TextOps(monkeypatch, mockGUI, mockRnd, fncPath):
    """Test handling files and text in the Tokenizer class."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    project.data.setLanguage("en")
    project._loadProjectLocalisation()

    tokens = BareTokenizer(project)
    tokens._keepRaw = True

    # Set some content to work with
    docText = (
        "### Scene Six\n\n"
        "This is text with _italic text_, some **bold text**, some ~~deleted text~~, "
        "and some **_mixed text_** and **some _nested_ text**.\n\n"
        "#### Replace\n\n"
        "Also, replace <A> and <B>.\n\n"
    )
    docTextR = docText.replace("<A>", "this").replace("<B>", "that")

    nDoc = project.storage.getDocument(C.hSceneDoc)
    assert nDoc.writeDocument(docText)

    project.data.setAutoReplace({"A": "this", "B": "that"})

    assert project.saveProject()

    # Root Heading
    assert len(tokens._blocks) == 0
    tokens.addRootHeading("stuff")
    tokens.addRootHeading(C.hSceneDoc)
    assert len(tokens._blocks) == 0

    # First Page
    tokens.addRootHeading(C.hPlotRoot)
    assert tokens._raw[-1] == "#! Notes: Plot\n\n"
    assert tokens._blocks[-1] == (
        BlockTyp.TITLE,
        "0000000000009:T0001",
        "Notes: Plot",
        [],
        BlockFmt.CENTRE,
    )

    # Not First Page
    tokens.addRootHeading(C.hPlotRoot)
    assert tokens._raw[-1] == "#! Notes: Plot\n\n"
    assert tokens._blocks[-1] == (
        BlockTyp.TITLE,
        "0000000000009:T0001",
        "Notes: Plot",
        [],
        BlockFmt.CENTRE | BlockFmt.PBB,
    )

    # A novel-like root has no "Notes:" prefix on the title
    tokens.addRootHeading(C.hNovelRoot)
    assert tokens._raw[-1] == "#! Novel\n\n"
    assert tokens._blocks[-1] == (
        BlockTyp.TITLE,
        "0000000000008:T0001",
        "Novel",
        [],
        BlockFmt.CENTRE | BlockFmt.PBB,
    )

    # Set Text
    tokens.setText("stuff")
    assert tokens._text == ""

    tokens.setText(C.hSceneDoc)
    assert tokens._text == docText

    tokens.setText(C.hSceneDoc, docText)
    assert tokens._text == docText

    assert tokens._isNovel is True

    # Pre Processing
    tokens.doPreProcessing()
    assert tokens._text == docTextR


@pytest.mark.core
def testTokenizer_StripEscape():
    """Test the stripEscape helper function."""
    text1 = "This is text with escapes: \\** \\~~ \\__"
    text2 = "This is text with escapes: ** ~~ __"
    assert stripEscape(text1) == "This is text with escapes: ** ~~ __"
    assert stripEscape(text2) == "This is text with escapes: ** ~~ __"


@pytest.mark.core
def testTokenizer_HeaderFormat(mockGUI):
    """Test the tokenization of header formats in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    # Title
    # =====

    # Story File
    tokens._isNovel = True
    tokens._isFirst = True
    tokens._text = "#! Novel Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TITLE, TM1, "Novel Title", [], BlockFmt.CENTRE),
    ]

    # Note File
    tokens._isNovel = False
    tokens._isFirst = True
    tokens._text = "#! Note Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TITLE, TM1, "Note Title", [], BlockFmt.CENTRE),
    ]

    # Header 1
    # ========

    # Story File
    tokens._isNovel = True
    tokens._isFirst = True
    tokens._text = "# Novel Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Novel Title", [], BlockFmt.CENTRE),
    ]

    # Note File
    tokens._isNovel = False
    tokens._isFirst = True
    tokens._text = "# Note Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Note Title", [], BlockFmt.NONE),
    ]

    # Header 2
    # ========

    # Story File
    tokens._isNovel = True
    tokens._text = "## Chapter One\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Chapter One", [], BlockFmt.PBB),
    ]

    # Note File
    tokens._isNovel = False
    tokens._text = "## Heading 2\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "Heading 2", [], BlockFmt.NONE),
    ]

    # Header 3
    # ========

    # Story File
    tokens._isNovel = True
    tokens._text = "### Scene One\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "Scene One", [], BlockFmt.NONE),
    ]

    # Note File
    tokens._isNovel = False
    tokens._text = "### Heading 3\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD3, TM1, "Heading 3", [], BlockFmt.NONE),
    ]

    # Header 4
    # ========

    # Story File
    tokens._isNovel = True
    tokens._text = "#### A Section\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD3, TM1, "A Section", [], BlockFmt.NONE),
    ]

    # Note File
    tokens._isNovel = False
    tokens._text = "#### Heading 4\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD4, TM1, "Heading 4", [], BlockFmt.NONE),
    ]

    # Title
    # =====

    # Story File
    tokens._isNovel = True
    tokens._isFirst = False
    tokens._text = "#! Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TITLE, TM1, "Title", [], BlockFmt.PBB | BlockFmt.CENTRE),
    ]

    # Note File
    tokens._isNovel = False
    tokens._isFirst = False
    tokens._text = "#! Title\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TITLE, TM1, "Title", [], BlockFmt.PBB | BlockFmt.CENTRE),
    ]

    # Unnumbered
    # ==========

    # Story File
    tokens._isNovel = True
    tokens._text = "##! Prologue\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Prologue", [], BlockFmt.PBB),
    ]

    # Note File
    tokens._isNovel = False
    tokens._text = "##! Prologue\n"

    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "Prologue", [], BlockFmt.NONE),
    ]


@pytest.mark.core
def testTokenizer_HeaderStyleNone(mockGUI):
    """Test header styling disabled."""
    project = NWProject()
    tokens = BareTokenizer(project)

    def processStyle(text: str, first: bool) -> BlockFmt:
        tokens._text = text
        tokens._isFirst = first
        tokens.tokenizeText()
        return tokens._blocks[0][4]

    tokens.setTitleStyle(False, False)
    tokens.setPartitionStyle(False, False)
    tokens.setChapterStyle(False, False)
    tokens.setSceneStyle(False, False)

    assert tokens._titleStyle == BlockFmt.NONE
    assert tokens._partStyle == BlockFmt.NONE
    assert tokens._chapterStyle == BlockFmt.NONE
    assert tokens._sceneStyle == BlockFmt.NONE

    # Novel Docs
    tokens._isNovel = True

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE

    # Note Docs
    tokens._isNovel = False

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE


@pytest.mark.core
def testTokenizer_HeaderStyleCenter(mockGUI):
    """Test header styling centred."""
    project = NWProject()
    tokens = BareTokenizer(project)

    def processStyle(text: str, first: bool) -> BlockFmt:
        tokens._text = text
        tokens._isFirst = first
        tokens.tokenizeText()
        return tokens._blocks[0][4]

    tokens.setTitleStyle(True, False)
    tokens.setPartitionStyle(True, False)
    tokens.setChapterStyle(True, False)
    tokens.setSceneStyle(True, False)

    assert tokens._titleStyle == BlockFmt.CENTRE
    assert tokens._partStyle == BlockFmt.CENTRE
    assert tokens._chapterStyle == BlockFmt.CENTRE
    assert tokens._sceneStyle == BlockFmt.CENTRE

    # Novel Docs
    tokens._isNovel = True

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.CENTRE
    assert processStyle("## Chapter\n", False) == BlockFmt.CENTRE
    assert processStyle("### Scene\n", False) == BlockFmt.CENTRE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", False) == BlockFmt.CENTRE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.CENTRE
    assert processStyle("## Chapter\n", True) == BlockFmt.CENTRE
    assert processStyle("### Scene\n", True) == BlockFmt.CENTRE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", True) == BlockFmt.CENTRE

    # Note Docs
    tokens._isNovel = False

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE


@pytest.mark.core
def testTokenizer_HeaderStylePageBreak(mockGUI):
    """Test header styling page break."""
    project = NWProject()
    tokens = BareTokenizer(project)

    def processStyle(text: str, first: bool) -> BlockFmt:
        tokens._text = text
        tokens._isFirst = first
        tokens.tokenizeText()
        return tokens._blocks[0][4]

    tokens.setTitleStyle(False, True)
    tokens.setPartitionStyle(False, True)
    tokens.setChapterStyle(False, True)
    tokens.setSceneStyle(False, True)

    assert tokens._titleStyle == BlockFmt.PBB
    assert tokens._partStyle == BlockFmt.PBB
    assert tokens._chapterStyle == BlockFmt.PBB
    assert tokens._sceneStyle == BlockFmt.PBB

    # Novel Docs
    tokens._isNovel = True

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.PBB
    assert processStyle("## Chapter\n", False) == BlockFmt.PBB
    assert processStyle("### Scene\n", False) == BlockFmt.PBB
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.PBB
    assert processStyle("##! Prologue\n", False) == BlockFmt.PBB

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE

    # Note Docs
    tokens._isNovel = False

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.PBB
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE


@pytest.mark.core
def testTokenizer_HeaderStylePageBreakCenter(mockGUI):
    """Test header styling page break and centred."""
    project = NWProject()
    tokens = BareTokenizer(project)

    def processStyle(text: str, first: bool) -> BlockFmt:
        tokens._text = text
        tokens._isFirst = first
        tokens.tokenizeText()
        return tokens._blocks[0][4]

    tokens.setTitleStyle(True, True)
    tokens.setPartitionStyle(True, True)
    tokens.setChapterStyle(True, True)
    tokens.setSceneStyle(True, True)

    assert tokens._titleStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._partStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._chapterStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._sceneStyle == BlockFmt.CENTRE | BlockFmt.PBB

    # Novel Docs
    tokens._isNovel = True

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("## Chapter\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("### Scene\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("##! Prologue\n", False) == BlockFmt.CENTRE | BlockFmt.PBB

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.CENTRE
    assert processStyle("## Chapter\n", True) == BlockFmt.CENTRE
    assert processStyle("### Scene\n", True) == BlockFmt.CENTRE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", True) == BlockFmt.CENTRE

    # Note Docs
    tokens._isNovel = False

    # First Document is False
    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # First Document is True
    assert processStyle("# Title\n", True) == BlockFmt.NONE
    assert processStyle("## Chapter\n", True) == BlockFmt.NONE
    assert processStyle("### Scene\n", True) == BlockFmt.NONE
    assert processStyle("#### Section\n", True) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", True) == BlockFmt.CENTRE
    assert processStyle("##! Prologue\n", True) == BlockFmt.NONE


@pytest.mark.core
def testTokenizer_HeaderStyleSeparation(mockGUI):
    """Test header styling separation."""
    project = NWProject()
    tokens = BareTokenizer(project)

    def processStyle(text: str, first: bool) -> BlockFmt:
        tokens._text = text
        tokens._isFirst = first
        tokens.tokenizeText()
        return tokens._blocks[0][4]

    tokens._isNovel = True

    # Title Styles
    tokens.setTitleStyle(True, True)
    tokens.setPartitionStyle(False, False)
    tokens.setChapterStyle(False, False)
    tokens.setSceneStyle(False, False)

    assert tokens._titleStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._partStyle == BlockFmt.NONE
    assert tokens._chapterStyle == BlockFmt.NONE
    assert tokens._sceneStyle == BlockFmt.NONE

    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # Partition Styles
    tokens.setTitleStyle(False, False)
    tokens.setPartitionStyle(True, True)
    tokens.setChapterStyle(False, False)
    tokens.setSceneStyle(False, False)

    assert tokens._titleStyle == BlockFmt.NONE
    assert tokens._partStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._chapterStyle == BlockFmt.NONE
    assert tokens._sceneStyle == BlockFmt.NONE

    assert processStyle("# Title\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE

    # Chapter Styles
    tokens.setTitleStyle(False, False)
    tokens.setPartitionStyle(False, False)
    tokens.setChapterStyle(True, True)
    tokens.setSceneStyle(False, False)

    assert tokens._titleStyle == BlockFmt.NONE
    assert tokens._partStyle == BlockFmt.NONE
    assert tokens._chapterStyle == BlockFmt.CENTRE | BlockFmt.PBB
    assert tokens._sceneStyle == BlockFmt.NONE

    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("### Scene\n", False) == BlockFmt.NONE
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", False) == BlockFmt.CENTRE | BlockFmt.PBB

    # Scene Styles
    tokens.setTitleStyle(False, False)
    tokens.setPartitionStyle(False, False)
    tokens.setChapterStyle(False, False)
    tokens.setSceneStyle(True, True)

    assert tokens._titleStyle == BlockFmt.NONE
    assert tokens._partStyle == BlockFmt.NONE
    assert tokens._chapterStyle == BlockFmt.NONE
    assert tokens._sceneStyle == BlockFmt.CENTRE | BlockFmt.PBB

    assert processStyle("# Title\n", False) == BlockFmt.NONE
    assert processStyle("## Chapter\n", False) == BlockFmt.NONE
    assert processStyle("### Scene\n", False) == BlockFmt.CENTRE | BlockFmt.PBB
    assert processStyle("#### Section\n", False) == BlockFmt.NONE
    assert processStyle("#! My Novel\n", False) == BlockFmt.NONE
    assert processStyle("##! Prologue\n", False) == BlockFmt.NONE


@pytest.mark.core
def testTokenizer_HeaderStyleHorizontalRule(mockGUI):
    """Test header style processing with static horizontal rule format."""
    project = NWProject()
    tokens = BareTokenizer(project)

    tokens._isNovel = True
    tokens._handle = TMH

    # Scene rule as static four hyphens emits a centred HRULE block
    tokens.setSceneFormat(nwHeadFmt.HRULE, False)
    tokens._noSep = False
    tokens._text = "### Scene One\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HRULE, TM1, "", [], BlockFmt.NONE),
    ]

    # Immediately after chapter, scene separators and HRULE are suppressed
    tokens.setSceneFormat(nwHeadFmt.HRULE, False)
    tokens._noSep = True
    tokens._text = "### Scene Two\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    # Mixed format is not allowed and treated as a normal header
    tokens.setSceneFormat(f"{nwHeadFmt.HRULE}{nwHeadFmt.BR}{nwHeadFmt.TITLE}", False)
    tokens._noSep = False
    tokens._text = "### Scene Three\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, f"{nwHeadFmt.HRULE}\nScene Three", [], BlockFmt.NONE),
    ]

    # The same static four hyphens rule applies to hard scenes
    tokens.setHardSceneFormat(nwHeadFmt.HRULE, False)
    tokens._noSep = False
    tokens._text = "###! Scene Four\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HRULE, TM1, "", [], BlockFmt.NONE),
    ]

    # Sections still treat static four hyphens as a centred HRULE block
    tokens.setSectionFormat(nwHeadFmt.HRULE, False)
    tokens._noSep = True
    tokens._text = "#### Section\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HRULE, TM1, "", [], BlockFmt.NONE),
    ]


@pytest.mark.core
def testTokenizer_MetaFormat(mockGUI):
    """Test the tokenization of meta formats in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    # Ignore Text
    tokens._text = "%~ Some text\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    # Comment
    tokens.setCommentType(nwComment.PLAIN, False)
    tokens._text = "% A comment\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    tokens.setCommentType(nwComment.PLAIN, True)
    tokens._text = "% A comment\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.COMMENT,
            "",
            "Comment: A comment",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "comment"),
                (8, TextFmt.COL_E, ""),
                (8, TextFmt.B_E, ""),
                (9, TextFmt.COL_B, "comment"),
                (18, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    # Synopsis
    tokens.setCommentType(nwComment.SYNOPSIS, False)
    tokens._text = "%synopsis: The synopsis\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    tokens.setCommentType(nwComment.SYNOPSIS, True)
    tokens._text = "% synopsis: The synopsis\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.SUMMARY,
            "",
            "Synopsis: The synopsis",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "modifier"),
                (9, TextFmt.COL_E, ""),
                (9, TextFmt.B_E, ""),
                (10, TextFmt.COL_B, "note"),
                (22, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    # Short
    tokens.setCommentType(nwComment.SHORT, False)
    tokens._text = "% short: A short description\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    tokens.setCommentType(nwComment.SHORT, True)
    tokens._text = "% short: A short description\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.SUMMARY,
            "",
            "Short Description: A short description",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "modifier"),
                (18, TextFmt.COL_E, ""),
                (18, TextFmt.B_E, ""),
                (19, TextFmt.COL_B, "note"),
                (38, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    # Story Comments
    tokens.setCommentType(nwComment.STORY, False)
    tokens.setCommentType(nwComment.NOTE, False)
    tokens._text = (
        "%Story.Stuff: Stuff happens\n"
        "%Note.More: That stuff that happened\n"
        "%Note.Other: That other stuff that happened\n"
    )
    tokens.tokenizeText()
    assert tokens._blocks == []

    tokens.setCommentType(nwComment.STORY, True)
    tokens.setCommentType(nwComment.NOTE, True)
    tokens._text = (
        "%Story.Stuff: Stuff happens\n"
        "%Note.More: That stuff that happened\n"
        "%Note.Other: That other stuff that happened\n"
    )
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.NOTE,
            "",
            "Story Structure (Stuff): Stuff happens",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "modifier"),
                (24, TextFmt.COL_E, ""),
                (24, TextFmt.B_E, ""),
                (25, TextFmt.COL_B, "note"),
                (38, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_BTM,
        ),
        (
            BlockTyp.NOTE,
            "",
            "Note (More): That stuff that happened",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "modifier"),
                (12, TextFmt.COL_E, ""),
                (12, TextFmt.B_E, ""),
                (13, TextFmt.COL_B, "note"),
                (37, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_TOP | BlockFmt.Z_BTM,
        ),
        (
            BlockTyp.NOTE,
            "",
            "Note (Other): That other stuff that happened",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "modifier"),
                (13, TextFmt.COL_E, ""),
                (13, TextFmt.B_E, ""),
                (14, TextFmt.COL_B, "note"),
                (44, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_TOP,
        ),
    ]

    # Keyword
    tokens.setKeywords(False)
    tokens._text = "@char: Bod\n"
    tokens.tokenizeText()
    assert tokens._blocks == []

    tokens.setKeywords(True)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.KEYWORD,
            "char",
            "Characters: Bod",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "keyword"),
                (11, TextFmt.COL_E, ""),
                (11, TextFmt.B_E, ""),
                (12, TextFmt.COL_B, "tag"),
                (12, TextFmt.ARF_B, "#tag_bod"),
                (15, TextFmt.ARF_E, ""),
                (15, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    tokens._text = "@pov: Bod\n@plot: Main\n@location: Europe\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.KEYWORD,
            "pov",
            "Point of View: Bod",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "keyword"),
                (14, TextFmt.COL_E, ""),
                (14, TextFmt.B_E, ""),
                (15, TextFmt.COL_B, "tag"),
                (15, TextFmt.ARF_B, "#tag_bod"),
                (18, TextFmt.ARF_E, ""),
                (18, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_BTM,
        ),
        (
            BlockTyp.KEYWORD,
            "plot",
            "Plot: Main",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "keyword"),
                (5, TextFmt.COL_E, ""),
                (5, TextFmt.B_E, ""),
                (6, TextFmt.COL_B, "tag"),
                (6, TextFmt.ARF_B, "#tag_main"),
                (10, TextFmt.ARF_E, ""),
                (10, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_TOP | BlockFmt.Z_BTM,
        ),
        (
            BlockTyp.KEYWORD,
            "location",
            "Locations: Europe",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "keyword"),
                (10, TextFmt.COL_E, ""),
                (10, TextFmt.B_E, ""),
                (11, TextFmt.COL_B, "tag"),
                (11, TextFmt.ARF_B, "#tag_europe"),
                (17, TextFmt.ARF_E, ""),
                (17, TextFmt.COL_E, ""),
            ],
            BlockFmt.Z_TOP,
        ),
    ]

    # Ignored keywords
    tokens._text = "@pov: Bod\n@plot: Main\n@location: Europe\n"
    tokens.setIgnoredKeywords("@plot, @location")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.KEYWORD,
            "pov",
            "Point of View: Bod",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "keyword"),
                (14, TextFmt.COL_E, ""),
                (14, TextFmt.B_E, ""),
                (15, TextFmt.COL_B, "tag"),
                (15, TextFmt.ARF_B, "#tag_bod"),
                (18, TextFmt.ARF_E, ""),
                (18, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]


@pytest.mark.core
def testTokenizer_MarginFormat(mockGUI):
    """Test the tokenization of margin formats in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)

    # Alignment and Indentation
    dblIndent = BlockFmt.IND_L | BlockFmt.IND_R
    rIndAlign = BlockFmt.RIGHT | BlockFmt.IND_R
    tokens._text = (
        "Some regular text\n\n"
        "Some left-aligned text <<\n\n"
        ">> Some right-aligned text\n\n"
        ">> Some centered text <<\n\n"
        "> Left-indented block\n\n"
        "Right-indented block <\n\n"
        "> Double-indented block <\n\n"
        ">> Right-indent, right-aligned <\n\n"
    )
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "Some regular text", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Some left-aligned text", [], BlockFmt.LEFT),
        (BlockTyp.TEXT, "", "Some right-aligned text", [], BlockFmt.RIGHT),
        (BlockTyp.TEXT, "", "Some centered text", [], BlockFmt.CENTRE),
        (BlockTyp.TEXT, "", "Left-indented block", [], BlockFmt.IND_L),
        (BlockTyp.TEXT, "", "Right-indented block", [], BlockFmt.IND_R),
        (BlockTyp.TEXT, "", "Double-indented block", [], dblIndent),
        (BlockTyp.TEXT, "", "Right-indent, right-aligned", [], rIndAlign),
    ]


@pytest.mark.core
@pytest.mark.parametrize("singleBold", [True, False])
def testTokenizer_ExtractFormats(mockGUI, singleBold):
    """Test the extraction of formats in the Tokenizer class.
    This test is run twice, with single and with double asterisk support
    for bold.
    """
    CONFIG.singleStarBold = singleBold

    project = NWProject()
    tokens = BareTokenizer(project)

    # Markdown
    # ========

    # Plain bold
    text, fmt = tokens._extractFormats("Text with **bold** in it.")
    assert text == "Text with bold in it."
    assert fmt == [(10, TextFmt.B_B, ""), (14, TextFmt.B_E, "")]

    if singleBold:
        text, fmt = tokens._extractFormats("Text with *bold* in it.")
        assert text == "Text with bold in it."
        assert fmt == [(10, TextFmt.B_B, ""), (14, TextFmt.B_E, "")]
    else:
        # If single bold is off, this format is ignored
        text, fmt = tokens._extractFormats("Text with *bold* in it.")
        assert text == "Text with *bold* in it."
        assert fmt == []

    # Plain italics
    text, fmt = tokens._extractFormats("Text with _italics_ in it.")
    assert text == "Text with italics in it."
    assert fmt == [(10, TextFmt.I_B, ""), (17, TextFmt.I_E, "")]

    # Plain strikethrough
    text, fmt = tokens._extractFormats("Text with ~~strikethrough~~ in it.")
    assert text == "Text with strikethrough in it."
    assert fmt == [(10, TextFmt.D_B, ""), (23, TextFmt.D_E, "")]

    # Plain mark
    text, fmt = tokens._extractFormats("Text with ==a highlight== in it.")
    assert text == "Text with a highlight in it."
    assert fmt == [(10, TextFmt.M_B, ""), (21, TextFmt.M_E, "")]

    # Nested bold/italics
    text, fmt = tokens._extractFormats("Text with **bold and _italics_** in it.")
    assert text == "Text with bold and italics in it."
    assert fmt == [
        (10, TextFmt.B_B, ""),
        (19, TextFmt.I_B, ""),
        (26, TextFmt.I_E, ""),
        (26, TextFmt.B_E, ""),
    ]

    if singleBold:
        text, fmt = tokens._extractFormats("Text with *bold and _italics_* in it.")
        assert text == "Text with bold and italics in it."
        assert fmt == [
            (10, TextFmt.B_B, ""),
            (19, TextFmt.I_B, ""),
            (26, TextFmt.I_E, ""),
            (26, TextFmt.B_E, ""),
        ]
    else:
        # If single bold is off, only italics is recognised
        text, fmt = tokens._extractFormats("Text with *bold and _italics_* in it.")
        assert text == "Text with *bold and italics* in it."
        assert fmt == [
            (20, TextFmt.I_B, ""),
            (27, TextFmt.I_E, ""),
        ]

    # Bold with overlapping italics
    if singleBold:
        # Here bold is accepted because the second closing asterisk is itself a valid boundary
        text, fmt = tokens._extractFormats("Text with **bold and overlapping _italics**_ in it.")
        assert text == "Text with *bold and overlapping italics* in it."
        assert fmt == [
            (11, TextFmt.B_B, ""),
            (32, TextFmt.I_B, ""),
            (39, TextFmt.B_E, ""),
            (40, TextFmt.I_E, ""),
        ]
    else:
        # Here, bold is ignored because it is not on word boundary
        text, fmt = tokens._extractFormats("Text with **bold and overlapping _italics**_ in it.")
        assert text == "Text with **bold and overlapping italics** in it."
        assert fmt == [(33, TextFmt.I_B, ""), (42, TextFmt.I_E, "")]

    # Shortcodes
    # ==========

    # Plain bold
    text, fmt = tokens._extractFormats("Text with [b]bold[/b] in it.")
    assert text == "Text with bold in it."
    assert fmt == [(10, TextFmt.B_B, ""), (14, TextFmt.B_E, "")]

    # Plain italics
    text, fmt = tokens._extractFormats("Text with [i]italics[/i] in it.")
    assert text == "Text with italics in it."
    assert fmt == [(10, TextFmt.I_B, ""), (17, TextFmt.I_E, "")]

    # Plain strikethrough
    text, fmt = tokens._extractFormats("Text with [s]strikethrough[/s] in it.")
    assert text == "Text with strikethrough in it."
    assert fmt == [(10, TextFmt.D_B, ""), (23, TextFmt.D_E, "")]

    # Plain underline
    text, fmt = tokens._extractFormats("Text with [u]underline[/u] in it.")
    assert text == "Text with underline in it."
    assert fmt == [(10, TextFmt.U_B, ""), (19, TextFmt.U_E, "")]

    # Plain mark
    text, fmt = tokens._extractFormats("Text with [m]highlight[/m] in it.")
    assert text == "Text with highlight in it."
    assert fmt == [(10, TextFmt.M_B, ""), (19, TextFmt.M_E, "")]

    # Plain superscript
    text, fmt = tokens._extractFormats("Text with super[sup]script[/sup] in it.")
    assert text == "Text with superscript in it."
    assert fmt == [(15, TextFmt.SUP_B, ""), (21, TextFmt.SUP_E, "")]

    # Plain subscript
    text, fmt = tokens._extractFormats("Text with sub[sub]script[/sub] in it.")
    assert text == "Text with subscript in it."
    assert fmt == [(13, TextFmt.SUB_B, ""), (19, TextFmt.SUB_E, "")]

    # Nested bold/italics
    text, fmt = tokens._extractFormats("Text with [b]bold and [i]italics[/i][/b] in it.")
    assert text == "Text with bold and italics in it."
    assert fmt == [
        (10, TextFmt.B_B, ""),
        (19, TextFmt.I_B, ""),
        (26, TextFmt.I_E, ""),
        (26, TextFmt.B_E, ""),
    ]

    # Bold with overlapping italics
    # With shortcodes, this works
    text, fmt = tokens._extractFormats("Text with [b]bold and overlapping [i]italics[/b][/i] in it.")
    assert text == "Text with bold and overlapping italics in it."
    assert fmt == [
        (10, TextFmt.B_B, ""),
        (31, TextFmt.I_B, ""),
        (38, TextFmt.B_E, ""),
        (38, TextFmt.I_E, ""),
    ]

    # So does this
    text, fmt = tokens._extractFormats("Text with [b]bold and overlapping [i]italics[/b] in[/i] it.")
    assert text == "Text with bold and overlapping italics in it."
    assert fmt == [
        (10, TextFmt.B_B, ""),
        (31, TextFmt.I_B, ""),
        (38, TextFmt.B_E, ""),
        (41, TextFmt.I_E, ""),
    ]

    # URLs and Markdown Links
    # =======================

    # A bare URL is wrapped as a link, and left visible in the text
    text, fmt = tokens._extractFormats("Text with http://example.com in it.")
    assert text == "Text with http://example.com in it."
    assert fmt == [
        (10, TextFmt.HRF_B, "http://example.com"),
        (28, TextFmt.HRF_E, ""),
    ]

    # A Markdown-style link has its brackets stripped, and only the
    # link text is shown, wrapped as a link pointing to the URL
    text, fmt = tokens._extractFormats("Text with [a link](http://example.com) in it.")
    assert text == "Text with a link in it."
    assert fmt == [
        (10, TextFmt.STRIP, ""),
        (10, TextFmt.HRF_B, "http://example.com"),
        (16, TextFmt.STRIP, ""),
        (16, TextFmt.HRF_E, ""),
    ]

    # The URL inside a Markdown-style link must not also be picked up
    # by the plain URL match, while a separate, bare URL elsewhere in
    # the same text is still matched normally
    text, fmt = tokens._extractFormats("See [a link](http://example.com) and also http://other.com here.")
    assert text == "See a link and also http://other.com here."
    assert fmt == [
        (4, TextFmt.STRIP, ""),
        (4, TextFmt.HRF_B, "http://example.com"),
        (10, TextFmt.STRIP, ""),
        (10, TextFmt.HRF_E, ""),
        (20, TextFmt.HRF_B, "http://other.com"),
        (36, TextFmt.HRF_E, ""),
    ]


@pytest.mark.core
def testTokenizer_Paragraphs(mockGUI):
    """Test the splitting of paragraphs."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    # Collapse empty lines
    tokens._text = "First paragraph\n\n\nSecond paragraph\n\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "First paragraph", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Second paragraph", [], BlockFmt.NONE),
    ]

    # Combine multi-line paragraphs, keep breaks
    tokens._text = "This is text\nspanning multiple\nlines"
    tokens.setKeepLineBreaks(True)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "This is text\nspanning multiple\nlines", [], BlockFmt.NONE),
    ]

    # Combine multi-line paragraphs, remove breaks
    tokens._text = "This is text\nspanning multiple\nlines"
    tokens.setKeepLineBreaks(False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "This is text spanning multiple lines", [], BlockFmt.NONE),
    ]

    # Combine multi-line paragraphs, remove breaks, with formatting
    tokens._text = "This **is text**\nspanning _multiple_\nlines"
    tokens.setKeepLineBreaks(False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "This is text spanning multiple lines",
            [
                (5, TextFmt.B_B, ""),
                (12, TextFmt.B_E, ""),
                (22, TextFmt.I_B, ""),
                (30, TextFmt.I_E, ""),
            ],
            BlockFmt.NONE,
        ),
    ]

    # Make sure titles break a paragraph
    tokens._text = "# Title\nText _on_\ntwo lines.\n## Chapter\nMore **text**\n_here_.\n\n\n"
    tokens.setKeepLineBreaks(False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Title", [], BlockFmt.NONE),
        (
            BlockTyp.TEXT,
            "",
            "Text on two lines.",
            [
                (5, TextFmt.I_B, ""),
                (7, TextFmt.I_E, ""),
            ],
            BlockFmt.NONE,
        ),
        (BlockTyp.HEAD2, TM2, "Chapter", [], BlockFmt.NONE),
        (
            BlockTyp.TEXT,
            "",
            "More text here.",
            [
                (5, TextFmt.B_B, ""),
                (9, TextFmt.B_E, ""),
                (10, TextFmt.I_B, ""),
                (14, TextFmt.I_E, ""),
            ],
            BlockFmt.NONE,
        ),
    ]


@pytest.mark.core
def testTokenizer_BreakAlignIndent(mockGUI):
    """Test the splitting of paragraphs with alignment."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    for text in [
        "This is text <<\nspanning multiple\nlines",
        "This is text\nspanning multiple <<\nlines",
        "This is text\nspanning multiple\nlines <<",
    ]:
        # Preserve Breaks
        tokens.setKeepLineBreaks(True)
        tokens._text = text
        tokens.tokenizeText()
        assert tokens._blocks == [
            (BlockTyp.TEXT, "", "This is text\nspanning multiple\nlines", [], BlockFmt.LEFT),
        ]

        # Don't Preserve Breaks
        tokens.setKeepLineBreaks(False)
        tokens._text = text
        tokens.tokenizeText()
        assert tokens._blocks == [
            (BlockTyp.TEXT, "", "This is text spanning multiple lines", [], BlockFmt.LEFT),
        ]

        # With Justify
        # This should disable justify
        tokens.setKeepLineBreaks(True)
        tokens.setJustify(True, False)
        tokens._text = text
        tokens.tokenizeText()
        assert tokens._blocks == [
            (BlockTyp.TEXT, "", "This is text\nspanning multiple\nlines", [], BlockFmt.LEFT),
        ]

        # With Indent
        # This should disable indent
        tokens.setKeepLineBreaks(True)
        tokens.setFirstLineIndent(True, 1.0, False)
        tokens._text = text
        tokens.tokenizeText()
        assert tokens._blocks == [
            (BlockTyp.TEXT, "", "This is text\nspanning multiple\nlines", [], BlockFmt.LEFT),
        ]


@pytest.mark.core
def testTokenizer_BreakJustify(mockGUI):
    """Test the of processing of justify with breaks."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH
    tokens.setJustify(True, False)

    # Applied to all lines when breaks are preserved
    tokens._text = "This is text\nspanning multiple\nlines"
    tokens.setKeepLineBreaks(True)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "This is text\nspanning multiple\nlines", [], BlockFmt.JUSTIFY),
    ]

    # Turning off breaks should make no difference (see issue #2426)
    tokens._text = "This is text\nspanning multiple\nlines"
    tokens.setKeepLineBreaks(False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "This is text spanning multiple lines", [], BlockFmt.JUSTIFY),
    ]


@pytest.mark.core
def testTokenizer_TextFormat(mockGUI):
    """Test the tokenization of text formats in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    # Text
    tokens._text = "Some plain text\non two lines\n\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "Some plain text\non two lines", [], BlockFmt.NONE),
    ]

    tokens.setBodyText(False)
    tokens.tokenizeText()
    assert tokens._blocks == []
    tokens.setBodyText(True)

    # Text Emphasis
    tokens._text = "Some **bolded text** on this lines\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Some bolded text on this lines",
            [
                (5, TextFmt.B_B, ""),
                (16, TextFmt.B_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    tokens._text = "Some _italic text_ on this lines\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Some italic text on this lines",
            [
                (5, TextFmt.I_B, ""),
                (16, TextFmt.I_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    tokens._text = "Some **_bold italic text_** on this lines\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Some bold italic text on this lines",
            [
                (5, TextFmt.B_B, ""),
                (5, TextFmt.I_B, ""),
                (21, TextFmt.I_E, ""),
                (21, TextFmt.B_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    tokens._text = "Some ~~strikethrough text~~ on this lines\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Some strikethrough text on this lines",
            [
                (5, TextFmt.D_B, ""),
                (23, TextFmt.D_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    tokens._text = "Some **nested bold and _italic_ and ~~strikethrough~~ text** here\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Some nested bold and italic and strikethrough text here",
            [
                (5, TextFmt.B_B, ""),
                (21, TextFmt.I_B, ""),
                (27, TextFmt.I_E, ""),
                (32, TextFmt.D_B, ""),
                (45, TextFmt.D_E, ""),
                (50, TextFmt.B_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]


@pytest.mark.core
def testTokenizer_LineBreak(mockGUI):
    """Test processing of forced line breaks in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH
    tokens.setCommentType(nwComment.PLAIN, True)

    # They are stripped in headers
    tokens._text = "## Hello[br] World"
    tokens.tokenizeText()
    assert tokens._blocks == [(BlockTyp.HEAD2, TM1, "Hello World", [], BlockFmt.NONE)]

    # They are stripped in comments
    tokens._text = "% Hello[br] World"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.COMMENT,
            "",
            "Comment: Hello World",
            [
                (0, TextFmt.B_B, ""),
                (0, TextFmt.COL_B, "comment"),
                (8, TextFmt.COL_E, ""),
                (8, TextFmt.B_E, ""),
                (9, TextFmt.COL_B, "comment"),
                (20, TextFmt.COL_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]

    # They are used in text, with breaks enabled
    tokens.setKeepLineBreaks(True)
    tokens._text = "Hello[br]\nWorld"
    tokens.tokenizeText()
    assert tokens._blocks == [(BlockTyp.TEXT, "", "Hello\nWorld", [], BlockFmt.NONE)]

    # They are used in text, with breaks disabled
    tokens.setKeepLineBreaks(False)
    tokens._text = "Hello[br]\nWorld"
    tokens.tokenizeText()
    assert tokens._blocks == [(BlockTyp.TEXT, "", "Hello\nWorld", [], BlockFmt.NONE)]

    # Without forced breaks, they are preserved with breaks enabled
    tokens.setKeepLineBreaks(True)
    tokens._text = "Hello\nWorld"
    tokens.tokenizeText()
    assert tokens._blocks == [(BlockTyp.TEXT, "", "Hello\nWorld", [], BlockFmt.NONE)]

    # Without forced breaks, they are not preserved with breaks disabled
    tokens.setKeepLineBreaks(False)
    tokens._text = "Hello\nWorld"
    tokens.tokenizeText()
    assert tokens._blocks == [(BlockTyp.TEXT, "", "Hello World", [], BlockFmt.NONE)]


@pytest.mark.core
def testTokenizer_LineForMargin(mockGUI):
    """Test using empty lines between blocks in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH
    tokens._isNovel = True
    tokens.setLineForMargin(True)
    tokens.setChapterStyle(False, True)

    # Between paragraphs
    tokens._text = "Line one\n\nLine two"
    tokens._isFirst = True
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "Line one", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Line two", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]

    # Not between hard line breaks
    tokens._text = "Line one\nLine two"
    tokens._isFirst = True
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "Line one\nLine two", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]

    # Between heading and text
    tokens._text = "### Scene\n\nLine one"
    tokens._isFirst = True
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.HEAD2, f"{TMH}:T0001", "Scene", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Line one", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]

    # Between two chapters
    tokens._text = "## Chapter One\n\nText\n\n## Chapter Two\n\nText"
    tokens._isFirst = True
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.HEAD1, f"{TMH}:T0001", "Chapter One", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Text", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.PBB),
        (BlockTyp.HEAD1, f"{TMH}:T0002", "Chapter Two", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Text", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
    ]


@pytest.mark.core
def testTokenizer_ShortcodeValue(mockGUI):
    """Test processing of shortcodes with values."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH

    # Footnote
    tokens._text = "Hello World[footnote:abcd] to you!"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Hello World to you!",
            [
                (11, TextFmt.FNOTE, f"{TMH}:abcd"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Field
    tokens._text = "Hello World: [field:abcd] times!"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Hello World:  times!",
            [
                (13, TextFmt.FIELD, f"{TMH}:abcd"),
            ],
            BlockFmt.NONE,
        )
    ]


@pytest.mark.core
def testTokenizer_Dialogue(mockGUI):
    """Test the tokenization of dialogue in the Tokenizer class."""
    CONFIG.fmtDQuoteOpen = "\u201c"
    CONFIG.fmtDQuoteClose = "\u201d"
    CONFIG.fmtSQuoteOpen = "\u2018"
    CONFIG.fmtSQuoteClose = "\u2019"
    CONFIG.dialogStyle = 3
    CONFIG.altDialogOpen = "::"
    CONFIG.altDialogClose = "::"

    project = NWProject()
    tokens = BareTokenizer(project)
    tokens.setDialogHighlight(True)
    tokens._handle = TMH
    tokens._isNovel = True

    # Single quotes
    tokens._text = "Text with \u2018dialogue one,\u2019 and \u2018dialogue two.\u2019\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Text with \u2018dialogue one,\u2019 and \u2018dialogue two.\u2019",
            [
                (10, TextFmt.COL_B, "dialog"),
                (25, TextFmt.COL_E, "enddialog"),
                (30, TextFmt.COL_B, "dialog"),
                (45, TextFmt.COL_E, "enddialog"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Double quotes
    tokens._text = "Text with \u201cdialogue one,\u201d and \u201cdialogue two.\u201d\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Text with \u201cdialogue one,\u201d and \u201cdialogue two.\u201d",
            [
                (10, TextFmt.COL_B, "dialog"),
                (25, TextFmt.COL_E, "enddialog"),
                (30, TextFmt.COL_B, "dialog"),
                (45, TextFmt.COL_E, "enddialog"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Alt quotes
    tokens._text = "Text with ::dialogue one,:: and ::dialogue two.::\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "Text with ::dialogue one,:: and ::dialogue two.::",
            [
                (10, TextFmt.COL_B, "altdialog"),
                (27, TextFmt.COL_E, "endaltdialog"),
                (32, TextFmt.COL_B, "altdialog"),
                (49, TextFmt.COL_E, "endaltdialog"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Dialogue line
    CONFIG.dialogLine = "\u2013"
    tokens = BareTokenizer(project)
    tokens.setDialogHighlight(True)
    tokens._handle = TMH
    tokens._isNovel = True
    tokens._text = "\u2013 Dialogue line without narrator break.\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "\u2013 Dialogue line without narrator break.",
            [
                (0, TextFmt.COL_B, "dialog"),
                (39, TextFmt.COL_E, "enddialog"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Dialogue line with narrator break
    CONFIG.narratorBreak = "\u2013"
    tokens = BareTokenizer(project)
    tokens.setDialogHighlight(True)
    tokens._handle = TMH
    tokens._isNovel = True
    tokens._text = "\u2013 Dialogue with a narrator break, \u2013he said\u2013, see?\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "\u2013 Dialogue with a narrator break, \u2013he said\u2013, see?",
            [
                (0, TextFmt.COL_B, "dialog"),
                (34, TextFmt.COL_E, "enddialog"),
                (44, TextFmt.COL_B, "dialog"),
                (49, TextFmt.COL_E, "enddialog"),
            ],
            BlockFmt.NONE,
        )
    ]

    # Special Cases
    # =============

    # Dialogue + formatting on same index (Issue #2012)
    tokens._text = "[i]\u201cDialogue text.\u201d[/i]\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (
            BlockTyp.TEXT,
            "",
            "\u201cDialogue text.\u201d",
            [
                (0, TextFmt.I_B, ""),
                (0, TextFmt.COL_B, "dialog"),
                (16, TextFmt.COL_E, "enddialog"),
                (16, TextFmt.I_E, ""),
            ],
            BlockFmt.NONE,
        )
    ]


@pytest.mark.core
def testTokenizer_DialogueDisabled(monkeypatch, mockGUI):
    """The dialogue parser is disabled when no dialogue settings are
    active, even if highlighting is otherwise turned on.
    """
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "dialogStyle", 0)
        mp.setattr(CONFIG, "dialogLine", "")
        mp.setattr(CONFIG, "narratorDialog", "")
        mp.setattr(CONFIG, "altDialogOpen", "")
        mp.setattr(CONFIG, "altDialogClose", "")

        project = NWProject()
        tokens = BareTokenizer(project)
        tokens.setDialogHighlight(True)
        tokens._handle = TMH
        tokens._isNovel = True
        tokens._text = "Text with \u201cdialogue\u201d that is not highlighted.\n"
        tokens.tokenizeText()
        assert tokens._blocks == [
            (
                BlockTyp.TEXT,
                "",
                "Text with \u201cdialogue\u201d that is not highlighted.",
                [],
                BlockFmt.NONE,
            )
        ]


@pytest.mark.core
def testTokenizer_SpecialFormat(mockGUI):
    """Test the tokenization of special formats in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH
    tokens._isNovel = True

    # New Page
    # ========

    correctResp = [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.CENTRE),
        (BlockTyp.PART, TM2, "Title Two", [], BlockFmt.CENTRE | BlockFmt.PBB),
    ]

    # Command wo/Space
    tokens._isFirst = True
    tokens._text = "# Title One\n\n[newpage]\n\n# Title Two\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == correctResp

    # Command w/Space
    tokens._isFirst = True
    tokens._text = "# Title One\n\n[new page]\n\n# Title Two\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == correctResp

    # Trailing Spaces
    tokens._isFirst = True
    tokens._text = "# Title One\n\n[new page]   \t\n\n# Title Two\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == correctResp

    # Single Empty Paragraph
    # ======================

    tokens._text = "# Title One\n\n[vspace] \n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Multiple Empty Paragraphs
    # =========================

    # One Skip
    tokens._text = "# Title One\n\n[vspace:1] \n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Three Skips
    tokens._text = "# Title One\n\n[vspace:3] \n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Malformed Command, Case 1
    tokens._text = "# Title One\n\n[vspace:3xa] \n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Malformed Command, Case 2
    tokens._text = "# Title One\n\n[vspace:3.5]\n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Malformed Command, Case 3
    tokens._text = "# Title One\n\n[vspace:-1]\n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Empty Paragraph and Page Break
    # ==============================

    # Single Skip
    tokens._text = "# Title One\n\n[new page]\n\n[vspace]\n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.PBB),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]

    # Multiple Skip
    tokens._text = "# Title One\n\n[new page]\n\n[vspace:3]\n\nSome text to go here ...\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "Title One", [], BlockFmt.PBB | BlockFmt.CENTRE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.PBB),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.SKIP, "", "", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Some text to go here ...", [], BlockFmt.NONE),
    ]


@pytest.mark.core
def testTokenizer_TextIndent(mockGUI):
    """Test the handling of text indent in the Tokenizer class."""
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens.setCommentType(nwComment.SYNOPSIS, True)
    tokens._handle = TMH

    # No First Indent
    tokens.setFirstLineIndent(True, 1.0, False)

    assert tokens._noIndent is False
    assert tokens._firstIndent is True
    assert tokens._firstWidth == 1.0
    assert tokens._indentFirst is False

    # Page One
    # Two paragraphs in the same scene
    tokens._text = "# Title One\n\n### Scene One\n\nFirst paragraph.\n\nSecond paragraph.\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Title One", [], BlockFmt.NONE),
        (BlockTyp.HEAD3, TM2, "Scene One", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "First paragraph.", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Second paragraph.", [], BlockFmt.IND_T),
    ]
    assert tokens._noIndent is False

    # Page Two
    # New scene with only a synopsis
    tokens._text = "### Scene Two\n\n%Synopsis: Stuff happens.\n\n"
    tokens.tokenizeText()
    tFmt = [
        (0, TextFmt.B_B, ""),
        (0, TextFmt.COL_B, "modifier"),
        (9, TextFmt.COL_E, ""),
        (9, TextFmt.B_E, ""),
        (10, TextFmt.COL_B, "note"),
        (24, TextFmt.COL_E, ""),
    ]
    assert tokens._blocks == [
        (BlockTyp.HEAD3, TM1, "Scene Two", [], BlockFmt.NONE),
        (BlockTyp.SUMMARY, "", "Synopsis: Stuff happens.", tFmt, BlockFmt.NONE),
    ]
    assert tokens._noIndent is True

    # Page Three
    # Two paragraphs for the scene on the previous page
    tokens._text = "First paragraph.\n\nSecond paragraph.\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.TEXT, "", "First paragraph.", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "Second paragraph.", [], BlockFmt.IND_T),
    ]
    assert tokens._noIndent is False

    # First Indent
    tokens.setFirstLineIndent(True, 1.0, True)

    assert tokens._noIndent is False
    assert tokens._firstIndent is True
    assert tokens._firstWidth == 1.0
    assert tokens._indentFirst is True

    # Page Four
    # Two paragraphs in the same scene
    tokens._text = "# Title One\n\n### Scene One\n\nFirst paragraph.\n\nSecond paragraph.\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Title One", [], BlockFmt.NONE),
        (BlockTyp.HEAD3, TM2, "Scene One", [], BlockFmt.NONE),
        (BlockTyp.TEXT, "", "First paragraph.", [], BlockFmt.IND_T),
        (BlockTyp.TEXT, "", "Second paragraph.", [], BlockFmt.IND_T),
    ]
    assert tokens._noIndent is False


@pytest.mark.core
def testTokenizer_ProcessHeaders(mockGUI):
    """Test the header and page parser of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)
    tokens._isNovel = True
    tokens._handle = TMH

    # Titles
    # ======

    # H1: Title, First Page
    assert tokens._isFirst is True
    tokens._text = "# Part One\n"
    tokens.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "T: Part One", [], BlockFmt.CENTRE),
    ]

    # H1: Title, Not First Page
    assert tokens._isFirst is False
    tokens._text = "# Part One\n"
    tokens.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.PART, TM1, "T: Part One", [], BlockFmt.PBB | BlockFmt.CENTRE),
    ]

    # Chapters
    # ========

    # H2: Chapter
    tokens._text = "## Chapter One\n"
    tokens.setChapterFormat(f"C: {nwHeadFmt.TITLE}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "C: Chapter One", [], BlockFmt.PBB),
    ]

    # H2: Unnumbered Chapter
    tokens._text = "##! Prologue\n"
    tokens.setUnNumberedFormat(f"U: {nwHeadFmt.TITLE}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "U: Prologue", [], BlockFmt.PBB),
    ]

    # H2: Chapter Word Number
    tokens._text = "## Chapter\n"
    tokens.setChapterFormat(f"Chapter {nwHeadFmt.CH_WORD}")
    tokens._hFormatter._chapter = 0
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Chapter One", [], BlockFmt.PBB),
    ]

    # H2: Chapter Roman Number Upper Case
    tokens._text = "## Chapter\n"
    tokens.setChapterFormat(f"Chapter {nwHeadFmt.CH_ROMU}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Chapter II", [], BlockFmt.PBB),
    ]

    # H2: Chapter Roman Number Lower Case
    tokens._text = "## Chapter\n"
    tokens.setChapterFormat(f"Chapter {nwHeadFmt.CH_ROML}")
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD1, TM1, "Chapter iii", [], BlockFmt.PBB),
    ]

    # Scenes
    # ======

    # H3: Scene w/Title
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat(f"S: {nwHeadFmt.TITLE}", False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "S: Scene One", [], BlockFmt.NONE),
    ]

    # H3: Scene Hidden wo/Format
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat("", True)
    tokens.tokenizeText()
    assert tokens._blocks == []

    # H3: Scene wo/Format, first
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat("", False)
    tokens._noSep = True
    tokens.tokenizeText()
    assert tokens._blocks == []

    # H3: Scene wo/Format, not first
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat("", False)
    tokens._noSep = False
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SKIP, TM1, "", [], BlockFmt.NONE),
    ]

    # H3: Scene Separator, first
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat("* * *", False)
    tokens._noSep = True
    tokens.tokenizeText()
    assert tokens._blocks == []

    # H3: Scene Separator, not first
    tokens._text = "### Scene One\n"
    tokens.setSceneFormat("* * *", False)
    tokens._noSep = False
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SEP, TM1, "* * *", [], BlockFmt.CENTRE),
    ]

    # H3: Scene w/Absolute Number
    tokens._text = "### A Scene\n"
    tokens.setSceneFormat(f"Scene {nwHeadFmt.SC_ABS}", False)
    tokens._hFormatter._scene = 0
    tokens._hFormatter._absolute = 0
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "Scene 1", [], BlockFmt.NONE),
    ]

    # H3: Scene w/Chapter Number
    tokens._text = "### A Scene\n"
    tokens.setSceneFormat(f"Scene {nwHeadFmt.CH_NUM}.{nwHeadFmt.SC_NUM}", False)
    tokens._hFormatter._scene = 1
    tokens._hFormatter._absolute = 0
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD2, TM1, "Scene 3.2", [], BlockFmt.NONE),
    ]

    # Sections
    # ========

    # H4: Section Hidden wo/Format
    tokens._text = "#### A Section\n"
    tokens.setSectionFormat("", True)
    tokens.tokenizeText()
    assert tokens._blocks == []

    # H4: Section Visible wo/Format
    tokens._text = "#### A Section\n"
    tokens.setSectionFormat("", False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SKIP, TM1, "", [], BlockFmt.NONE),
    ]

    # H4: Section w/Format
    tokens._text = "#### A Section\n"
    tokens.setSectionFormat(f"X: {nwHeadFmt.TITLE}", False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.HEAD3, TM1, "X: A Section", [], BlockFmt.NONE),
    ]

    # H4: Section Separator
    tokens._text = "#### A Section\n"
    tokens.setSectionFormat("* * *", False)
    tokens.tokenizeText()
    assert tokens._blocks == [
        (BlockTyp.SEP, TM1, "* * *", [], BlockFmt.CENTRE),
    ]

    # Check the first scene detector, plain text
    tokens._noSep = True
    tokens._text = "Some text ...\n"
    tokens.tokenizeText()
    assert tokens._noSep is True

    # Check the first scene detector, text plus scene
    tokens._noSep = True
    tokens._text = "Some text ...\n\n### Scene\n\nText"
    tokens.tokenizeText()
    assert tokens._noSep is False


@pytest.mark.core
def testTokenizer_FormatComment(mockGUI):
    """Test note and comment formatting."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)

    # Comment, No Formatting
    style = COMMENT_STYLE[nwComment.PLAIN]
    assert tokens._formatComment(style, "", "Hello world!") == (
        "Comment: Hello world!",
        [
            (0, TextFmt.B_B, ""),
            (0, TextFmt.COL_B, "comment"),
            (8, TextFmt.COL_E, ""),
            (8, TextFmt.B_E, ""),
            (9, TextFmt.COL_B, "comment"),
            (21, TextFmt.COL_E, ""),
        ],
    )

    # Synopsis, No Formatting
    style = COMMENT_STYLE[nwComment.SYNOPSIS]
    assert tokens._formatComment(style, "", "Hello world!") == (
        "Synopsis: Hello world!",
        [
            (0, TextFmt.B_B, ""),
            (0, TextFmt.COL_B, "modifier"),
            (9, TextFmt.COL_E, ""),
            (9, TextFmt.B_E, ""),
            (10, TextFmt.COL_B, "note"),
            (22, TextFmt.COL_E, ""),
        ],
    )


@pytest.mark.core
def testTokenizer_FormatMeta(mockGUI):
    """Test meta formatting."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)

    assert tokens._formatMeta("@tag: Jane | Jane Smith") == (
        "@tag",
        "Tag: Jane | Jane Smith",
        [
            (0, TextFmt.B_B, ""),
            (0, TextFmt.COL_B, "keyword"),
            (4, TextFmt.COL_E, ""),
            (4, TextFmt.B_E, ""),
            (5, TextFmt.COL_B, "tag"),
            (5, TextFmt.ANM_B, "tag_jane"),
            (9, TextFmt.ANM_E, ""),
            (9, TextFmt.COL_E, ""),
            (12, TextFmt.COL_B, "optional"),
            (22, TextFmt.COL_E, ""),
        ],
    )

    assert tokens._formatMeta("@char: Jane, John") == (
        "@char",
        "Characters: Jane, John",
        [
            (0, TextFmt.B_B, ""),
            (0, TextFmt.COL_B, "keyword"),
            (11, TextFmt.COL_E, ""),
            (11, TextFmt.B_E, ""),
            (12, TextFmt.COL_B, "tag"),
            (12, TextFmt.ARF_B, "#tag_jane"),
            (16, TextFmt.ARF_E, ""),
            (16, TextFmt.COL_E, ""),
            (18, TextFmt.COL_B, "tag"),
            (18, TextFmt.ARF_B, "#tag_john"),
            (22, TextFmt.ARF_E, ""),
            (22, TextFmt.COL_E, ""),
        ],
    )

    # A keyword with no values only produces the label
    assert tokens._formatMeta("@char:") == (
        "@char",
        "Characters: ",
        [
            (0, TextFmt.B_B, ""),
            (0, TextFmt.COL_B, "keyword"),
            (11, TextFmt.COL_E, ""),
            (11, TextFmt.B_E, ""),
        ],
    )


@pytest.mark.core
def testTokenizer_BuildOutline(mockGUI, ipsumText):
    """Test stats counter of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)

    # Novel
    tokens._isNovel = True
    tokens._handle = "0000000000000"
    tokens._text = (
        "#! My Novel\n\n"
        "# Part One\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
        "#### Section\n\n"
        "Text\n\n"
    )
    tokens.tokenizeText()
    tokens.buildOutline()

    # Note
    tokens._isNovel = False
    tokens._handle = "0000000000001"
    tokens._text = (
        "#! My Notes\n\n# Header 1\n\nText\n\n## Header 2\n\nText\n\n### Header 3\n\nText\n\n#### Header 4\n\nText\n\n"
    )
    tokens.tokenizeText()
    tokens.buildOutline()

    # Check Outline
    assert tokens.textOutline == {
        "0000000000000:T0001": "TT|My Novel",
        "0000000000000:T0002": "PT|Part One",
        "0000000000000:T0003": "CH|Chapter One",
        "0000000000000:T0004": "SC|Scene One",
        "0000000000000:T0005": "SC|Scene Two",
        "0000000000000:T0006": "CH|Chapter Two",
        "0000000000000:T0007": "SC|Scene Three",
        "0000000000000:T0008": "SC|Scene Four",
        "0000000000001:T0001": "TT|My Notes",
        "0000000000001:T0002": "H1|Header 1",
        "0000000000001:T0003": "H2|Header 2",
        "0000000000001:T0004": "H3|Header 3",
    }


@pytest.mark.core
def testTokenizer_CountStats(mockGUI, ipsumText):
    """Test stats counter of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)
    tokens._isNovel = True

    # Short Text
    # ==========

    # Header wo/Format
    tokens._text = "## A Chapter Title\n\n"
    tokens._counts = {}
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens._blocks[0][2] == "A Chapter Title"
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 0,
        "allWords": 3,
        "textWords": 0,
        "titleWords": 3,
        "allChars": 15,
        "textChars": 0,
        "titleChars": 15,
        "dialogChars": 0,
        "allWordChars": 13,
        "textWordChars": 0,
        "titleWordChars": 13,
    }

    # Header w/Format
    tokens._text = "## A Chapter Title\n\n"
    tokens._counts = {}
    tokens.setChapterFormat(f"C {nwHeadFmt.CH_NUM}: {nwHeadFmt.TITLE}")
    tokens._hFormatter.resetAll()
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens._blocks[0][2] == "C 1: A Chapter Title"
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 0,
        "allWords": 5,
        "textWords": 0,
        "titleWords": 5,
        "allChars": 20,
        "textChars": 0,
        "titleChars": 20,
        "dialogChars": 0,
        "allWordChars": 16,
        "textWordChars": 0,
        "titleWordChars": 16,
    }

    # Two Paragraphs
    # First break should be counted, the double breaks not.
    tokens._text = "Some text\non two lines.\n\nWith a second paragraph.\n\n"
    tokens._counts = {}
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats == {
        "titleCount": 0,
        "paragraphCount": 2,
        "allWords": 9,
        "textWords": 9,
        "titleWords": 0,
        "allChars": 47,
        "textChars": 47,
        "titleChars": 0,
        "dialogChars": 0,
        "allWordChars": 40,
        "textWordChars": 40,
        "titleWordChars": 0,
    }

    # Two Scenes w/Separator
    tokens._text = "## Chapter\n\n### Scene\n\nText\n\n### Scene\n\nText"
    tokens._counts = {}
    tokens.setChapterFormat(nwHeadFmt.TITLE)
    tokens.setSceneFormat("* * *", False)
    tokens.tokenizeText()
    tokens.countStats()
    assert [t[2] for t in tokens._blocks] == ["Chapter", "Text", "* * *", "Text"]
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 2,
        "allWords": 6,
        "textWords": 2,
        "titleWords": 1,
        "allChars": 20,
        "textChars": 8,
        "titleChars": 7,
        "dialogChars": 0,
        "allWordChars": 18,
        "textWordChars": 8,
        "titleWordChars": 7,
    }

    # Scene w/Synopsis
    # Synopsis does not count as a paragraph, and counts as "Synopsis: Stuff"
    tokens._text = "## Chapter\n\n### Scene\n\n%Synopsis: Stuff\n\nText"
    tokens._counts = {}
    tokens.setChapterFormat(nwHeadFmt.TITLE)
    tokens.setSceneFormat("* * *", False)
    tokens.setCommentType(nwComment.SYNOPSIS, True)
    tokens.tokenizeText()
    tokens.countStats()
    assert [t[2] for t in tokens._blocks] == ["Chapter", "Synopsis: Stuff", "Text"]
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 1,
        "allWords": 4,
        "textWords": 1,
        "titleWords": 1,
        "allChars": 26,
        "textChars": 4,
        "titleChars": 7,
        "dialogChars": 0,
        "allWordChars": 25,
        "textWordChars": 4,
        "titleWordChars": 7,
    }

    # Scene w/Short
    # Short does not count as a paragraph, and counts as "Short Description: Stuff"
    tokens._text = "## Chapter\n\n### Scene\n\n%Short: Stuff\n\nText"
    tokens._counts = {}
    tokens.setChapterFormat(nwHeadFmt.TITLE)
    tokens.setSceneFormat("* * *", False)
    tokens.setCommentType(nwComment.SHORT, True)
    tokens.tokenizeText()
    tokens.countStats()
    assert [t[2] for t in tokens._blocks] == ["Chapter", "Short Description: Stuff", "Text"]
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 1,
        "allWords": 5,
        "textWords": 1,
        "titleWords": 1,
        "allChars": 35,
        "textChars": 4,
        "titleChars": 7,
        "dialogChars": 0,
        "allWordChars": 33,
        "textWordChars": 4,
        "titleWordChars": 7,
    }

    # Scene w/Comment
    # Comment does not count as a paragraph, and counts as "Comment: Stuff"
    tokens._text = "## Chapter\n\n### Scene\n\n% Stuff\n\nText"
    tokens._counts = {}
    tokens.setChapterFormat(nwHeadFmt.TITLE)
    tokens.setSceneFormat("* * *", False)
    tokens.setCommentType(nwComment.PLAIN, True)
    tokens.tokenizeText()
    tokens.countStats()
    assert [t[2] for t in tokens._blocks] == ["Chapter", "Comment: Stuff", "Text"]
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 1,
        "allWords": 4,
        "textWords": 1,
        "titleWords": 1,
        "allChars": 25,
        "textChars": 4,
        "titleChars": 7,
        "dialogChars": 0,
        "allWordChars": 24,
        "textWordChars": 4,
        "titleWordChars": 7,
    }

    # Scene w/Keyword
    # Keyword does not count as a paragraph, and counts as "Point of View: Jane"
    tokens._text = "## Chapter\n\n### Scene\n\n@pov: Jane\n\nText"
    tokens._counts = {}
    tokens.setChapterFormat(nwHeadFmt.TITLE)
    tokens.setSceneFormat("* * *", False)
    tokens.setKeywords(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert [t[2] for t in tokens._blocks] == ["Chapter", "Point of View: Jane", "Text"]
    assert tokens.textStats == {
        "titleCount": 1,
        "paragraphCount": 1,
        "allWords": 6,
        "textWords": 1,
        "titleWords": 1,
        "allChars": 30,
        "textChars": 4,
        "titleChars": 7,
        "dialogChars": 0,
        "allWordChars": 27,
        "textWordChars": 4,
        "titleWordChars": 7,
    }

    # Long Text
    # =========
    tokens._text = (
        "# Act One\n\n"
        "## Chapter\n\n"
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: Jane, John\n\n"
        "%Synopsis: A scene\n\n"
        f"{ipsumText[0]}.\n\n"
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: Jane, John\n\n"
        "%Synopsis: A scene\n\n"
        f"{ipsumText[1]}.\n\n"
        "## Chapter\n\n"
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: Jane, John\n\n"
        "%Synopsis: A scene\n\n"
        f"{ipsumText[2]}.\n\n"
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: Jane, John\n\n"
        "%Synopsis: A scene\n\n"
        f"{ipsumText[3]}.\n\n"
        "## Chapter\n\n"
        "### Scene\n\n"
        "@pov: Jane\n"
        "@char: Jane, John\n\n"
        "%Synopsis: A scene\n\n"
        f"{ipsumText[4]}.\n\n"
    )
    tokens._counts = {}

    tokens.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    tokens.setChapterFormat(f"C {nwHeadFmt.CH_NUM}: {nwHeadFmt.TITLE}")
    tokens.setSceneFormat("* * *", False)
    tokens.setCommentType(nwComment.SYNOPSIS, True)
    tokens.setCommentType(nwComment.PLAIN, True)
    tokens.setKeywords(True)

    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats == {
        "titleCount": 4,
        "paragraphCount": 5,
        "allWords": 596,
        "textWords": 528,
        "titleWords": 12,
        "allChars": 3859,
        "textChars": 3513,
        "titleChars": 46,
        "dialogChars": 0,
        "allWordChars": 3289,
        "textWordChars": 2990,
        "titleWordChars": 38,
    }


@pytest.mark.core
def testTokenizer_CountStats_Dialogue(mockGUI):
    """Test the dialogue character counter of the Tokenizer class."""
    CONFIG.fmtDQuoteOpen = "\u201c"
    CONFIG.fmtDQuoteClose = "\u201d"
    CONFIG.fmtSQuoteOpen = "\u2018"
    CONFIG.fmtSQuoteClose = "\u2019"
    CONFIG.dialogStyle = 3
    CONFIG.altDialogOpen = "::"
    CONFIG.altDialogClose = "::"

    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    tokens = BareTokenizer(project)
    tokens._isNovel = True

    # Highlighting disabled: no dialogue is counted, even if present
    tokens._text = "Text with \u201cdialogue,\u201d and ::alt dialogue::, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(False)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == 0

    # Highlighting enabled: quoted dialogue is counted
    tokens._text = "Text with \u201cdialogue one\u201d and \u201cdialogue two\u201d, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("\u201cdialogue one\u201d") + len("\u201cdialogue two\u201d")

    # Highlighting enabled: alt-dialogue syntax is also counted
    tokens._text = "Text with ::alt dialogue one:: and ::alt dialogue two::, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("::alt dialogue one::") + len("::alt dialogue two::")

    # Highlighting enabled: both regular and alt dialogue are combined
    tokens._text = "Text with \u201cdialogue\u201d and ::alt dialogue::, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("\u201cdialogue\u201d") + len("::alt dialogue::")

    # Highlighting enabled: unrelated formatting markers within the same
    # paragraph should be skipped when scanning for dialogue markers
    tokens._text = "Text with \u201c**bold** dialogue\u201d, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("\u201cbold dialogue\u201d")

    # Highlighting enabled: a nested alt-dialogue marker fully contained
    # within a regular dialogue quote overlaps, and must not be double
    # counted, nor cause the overlapping regions to be dropped
    tokens._text = "Text with \u201c::dialogue::\u201d, too.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("\u201c::dialogue::\u201d")

    # Highlighting enabled: a dialogue quote and an alt-dialogue marker
    # that cross each other, rather than nest, must still be merged into
    # a single non-overlapping span
    tokens._text = "Text with \u201cdialog and ::alt\u201d dialog:: in it.\n\n"
    tokens._counts = {}
    tokens.setDialogHighlight(True)
    tokens.tokenizeText()
    tokens.countStats()
    assert tokens.textStats["dialogChars"] == len("\u201cdialog and ::alt\u201d dialog::")


@pytest.mark.core
def testTokenizer_SceneSeparators(mockGUI):
    """Test the section and scene separators of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    md = ToMarkdown(project, False)
    md._isNovel = True

    # Separator Handling, Titles
    # ==========================

    md._text = (
        "# Title One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "# Title Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
    )
    md.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    md.setChapterFormat(f"C: {nwHeadFmt.TITLE}")
    md.setSectionFormat("", True)

    # Static Separator
    md.setSceneFormat("~", False)
    md.setHardSceneFormat("* * *", False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "T: Title One\n============\n\nText\n\n~\n\nText\n\nT: Title Two\n============\n\nText\n\n* * *\n\nText\n\n"
    )

    # Scene Title Formatted
    md.setSceneFormat(f"S: {nwHeadFmt.TITLE}", False)
    md.setHardSceneFormat(f"H: {nwHeadFmt.TITLE}", False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "T: Title One\n"
        "============\n\n"
        "## S: Scene One\n\n"
        "Text\n\n"
        "## S: Scene Two\n\n"
        "Text\n\n"
        "T: Title Two\n"
        "============\n\n"
        "## S: Scene Three\n\n"
        "Text\n\n"
        "## H: Scene Four\n\n"
        "Text\n\n"
    )

    # Separator Handling, Chapters
    # ============================

    md._text = (
        "# Title One\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
    )
    md.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    md.setChapterFormat(f"C: {nwHeadFmt.TITLE}")
    md.setSectionFormat("", True)

    # Static Separator
    md.setSceneFormat("* * *", False)
    md.setHardSceneFormat("* * *", False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "T: Title One\n"
        "============\n\n"
        "# C: Chapter One\n\n"
        "Text\n\n"
        "* * *\n\n"
        "Text\n\n"
        "# C: Chapter Two\n\n"
        "Text\n\n"
        "* * *\n\n"
        "Text\n\n"
    )

    # Scene Title Formatted
    md.setSceneFormat(f"S: {nwHeadFmt.TITLE}", False)
    md.setHardSceneFormat(f"H: {nwHeadFmt.TITLE}", False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "T: Title One\n"
        "============\n\n"
        "# C: Chapter One\n\n"
        "## S: Scene One\n\n"
        "Text\n\n"
        "## S: Scene Two\n\n"
        "Text\n\n"
        "# C: Chapter Two\n\n"
        "## S: Scene Three\n\n"
        "Text\n\n"
        "## H: Scene Four\n\n"
        "Text\n\n"
    )

    # Separators with Scenes Only
    # ===========================
    # Requires a fresh builder class
    md = ToMarkdown(project, True)
    md._isNovel = True

    md._text = (
        "### Scene One\n\nText\n\n### Scene Two\n\nText\n\n### Scene Three\n\nText\n\n###! Scene Four\n\nText\n\n"
    )

    md.setSceneFormat("", False)
    md.setHardSceneFormat("* * *", False)
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("Text\n\n\u205f\n\nText\n\n\u205f\n\nText\n\n* * *\n\nText\n\n")


@pytest.mark.core
def testTokenizer_HeaderVisibility(mockGUI):
    """Test the heading visibility settings of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    md = ToMarkdown(project, False)

    md._text = (
        "#! Novel\n\n"
        "# Title One\n\n"
        "##! Prologue\n\n"
        "Text\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "#### Section Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
    )

    # Novel Files
    # ===========
    # Headers are promoted one level

    md._isNovel = True

    # Show All
    md.setPartitionFormat(nwHeadFmt.TITLE, False)
    md.setChapterFormat(nwHeadFmt.TITLE, False)
    md.setUnNumberedFormat(nwHeadFmt.TITLE, False)
    md.setSceneFormat(nwHeadFmt.TITLE, False)
    md.setHardSceneFormat(nwHeadFmt.TITLE, False)
    md.setSectionFormat(nwHeadFmt.TITLE, False)

    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "Novel\n"
        "=====\n\n"
        "Title One\n"
        "=========\n\n"
        "# Prologue\n\n"
        "Text\n\n"
        "# Chapter One\n\n"
        "## Scene One\n\n"
        "Text\n\n"
        "## Scene Two\n\n"
        "### Section Two\n\n"
        "Text\n\n"
        "# Chapter Two\n\n"
        "## Scene Three\n\n"
        "Text\n\n"
        "## Scene Four\n\n"
        "Text\n\n"
    )

    # Hide All
    md.setPartitionFormat(nwHeadFmt.TITLE, True)
    md.setChapterFormat(nwHeadFmt.TITLE, True)
    md.setUnNumberedFormat(nwHeadFmt.TITLE, True)
    md.setSceneFormat(nwHeadFmt.TITLE, True)
    md.setHardSceneFormat(nwHeadFmt.TITLE, True)
    md.setSectionFormat(nwHeadFmt.TITLE, True)

    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == ("Novel\n=====\n\nText\n\nText\n\nText\n\nText\n\nText\n\n")

    # Note Files
    # ==========
    # Headers are exported as-is

    md._isNovel = False

    # Hide All
    md.setPartitionFormat(nwHeadFmt.TITLE, True)
    md.setChapterFormat(nwHeadFmt.TITLE, True)
    md.setUnNumberedFormat(nwHeadFmt.TITLE, True)
    md.setSceneFormat(nwHeadFmt.TITLE, True)
    md.setHardSceneFormat(nwHeadFmt.TITLE, True)
    md.setSectionFormat(nwHeadFmt.TITLE, True)

    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "Novel\n"
        "=====\n\n"
        "# Title One\n\n"
        "## Prologue\n\n"
        "Text\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "#### Section Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "### Scene Four\n\n"
        "Text\n\n"
    )


@pytest.mark.core
def testTokenizer_CounterHandling(mockGUI):
    """Test the heading counter of the Tokenizer class."""
    project = NWProject()
    project.data.setLanguage("en")
    project._loadProjectLocalisation()
    md = ToMarkdown(project, False)
    md._isNovel = True

    # Counter Handling, Novel Titles
    # ==============================
    # This also checks that only numbered chapters bump the counter

    md._text = (
        "#! Novel One\n\n"
        "##! Prologue\n\n"
        "Text\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
        "#! Novel Two\n\n"
        "##! Prologue\n\n"
        "Text\n\n"
        "## Chapter One\n\n"
        "### Scene One\n\n"
        "Text\n\n"
        "### Scene Two\n\n"
        "Text\n\n"
        "## Chapter Two\n\n"
        "### Scene Three\n\n"
        "Text\n\n"
        "###! Scene Four\n\n"
        "Text\n\n"
    )
    md.setPartitionFormat(f"T: {nwHeadFmt.TITLE}")
    md.setChapterFormat(f"C {nwHeadFmt.CH_NUM}: {nwHeadFmt.TITLE}")
    md.setUnNumberedFormat(f"U: {nwHeadFmt.TITLE}")
    md.setSceneFormat(f"S {nwHeadFmt.CH_NUM}.{nwHeadFmt.SC_NUM} ({nwHeadFmt.SC_ABS}): {nwHeadFmt.TITLE}", False)
    md.setHardSceneFormat(f"H {nwHeadFmt.CH_NUM}.{nwHeadFmt.SC_NUM} ({nwHeadFmt.SC_ABS}): {nwHeadFmt.TITLE}", False)
    md.setSectionFormat("", True)

    # Two Novel Format
    md.tokenizeText()
    md.doConvert()
    assert md._pages[-1] == (
        "Novel One\n"
        "=========\n\n"
        "# U: Prologue\n\n"
        "Text\n\n"
        "# C 1: Chapter One\n\n"
        "## S 1.1 (1): Scene One\n\n"
        "Text\n\n"
        "## S 1.2 (2): Scene Two\n\n"
        "Text\n\n"
        "# C 2: Chapter Two\n\n"
        "## S 2.1 (3): Scene Three\n\n"
        "Text\n\n"
        "## H 2.2 (4): Scene Four\n\n"
        "Text\n\n"
        "Novel Two\n"
        "=========\n\n"
        "# U: Prologue\n\n"
        "Text\n\n"
        "# C 1: Chapter One\n\n"
        "## S 1.1 (1): Scene One\n\n"
        "Text\n\n"
        "## S 1.2 (2): Scene Two\n\n"
        "Text\n\n"
        "# C 2: Chapter Two\n\n"
        "## S 2.1 (3): Scene Three\n\n"
        "Text\n\n"
        "## H 2.2 (4): Scene Four\n\n"
        "Text\n\n"
    )


@pytest.mark.core
def testTokenizer_HeadingFormatter(fncPath, mockGUI, mockRnd):
    """Check the HeadingFormatter class."""
    project = NWProject()
    project.setProjectLang("en_GB")
    mockRnd.reset()
    buildTestProject(project, fncPath)

    nHandle = project.newFile("Hello", C.hNovelRoot)
    cHandle = project.newFile("Jane", C.hCharRoot)
    dHandle = project.newFile("John", C.hCharRoot)

    assert isinstance(nHandle, str)
    assert isinstance(cHandle, str)
    assert isinstance(dHandle, str)

    assert project.index.scanText(cHandle, ("# Jane Smith\n@tag: Jane | Jane Smith\n"))
    assert project.index.scanText(dHandle, ("# John Smith\n@tag: John | John Smith\n"))
    assert project.index.scanText(
        nHandle,
        (
            "## Hi Bob\n"
            "@pov: Jane\n"
            "@focus: John\n"
            "@char: Jane, John\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really.\n"
        ),
    )

    formatter = HeadingFormatter(project)
    formatter.setHandle(nHandle)

    # Counters
    # ========
    cFormat = f"Chapter {nwHeadFmt.CH_NUM}.{nwHeadFmt.SC_NUM} - Scene {nwHeadFmt.SC_ABS} - {nwHeadFmt.TITLE}"

    # Initial
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 0.0 - Scene 0 - Hi Bob"

    # First Chapter and Scene
    formatter.incChapter()
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 1.1 - Scene 1 - Hi Bob"

    # Next Scenes
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 1.2 - Scene 2 - Hi Bob"
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 1.3 - Scene 3 - Hi Bob"
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 1.4 - Scene 4 - Hi Bob"

    # Next Chapter and Scene
    formatter.incChapter()
    formatter.resetScene()
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 2.1 - Scene 5 - Hi Bob"

    # New Main Title
    formatter.resetAll()
    formatter.incChapter()
    formatter.incScene()
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 1.1 - Scene 1 - Hi Bob"

    # Special Formats
    # ===============
    formatter._chapter = 2
    formatter._scene = 3
    formatter._absolute = 8

    # Chapter Number Word
    cFormat = f"Chapter {nwHeadFmt.CH_WORD}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.TITLE}"
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter Two, Scene 3 - Hi Bob"

    # Chapter Upper Case Roman
    cFormat = f"Chapter {nwHeadFmt.CH_ROMU}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.TITLE}"
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter II, Scene 3 - Hi Bob"

    # Chapter Lower Case Roman
    cFormat = f"Chapter {nwHeadFmt.CH_ROML}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.TITLE}"
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter ii, Scene 3 - Hi Bob"

    # Chapter w/PoV Character
    cFormat = f"Chapter {nwHeadFmt.CH_NUM}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.CHAR_POV}"
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 2, Scene 3 - Jane Smith"

    # Chapter w/Focus Character
    cFormat = f"Chapter {nwHeadFmt.CH_NUM}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.CHAR_FOCUS}"
    assert formatter.apply(cFormat, "Hi Bob", 1) == "Chapter 2, Scene 3 - John Smith"

    # Chapter w/Fallback PoV
    cFormat = f"Chapter {nwHeadFmt.CH_NUM}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.CHAR_POV}"
    assert formatter.apply(cFormat, "Hi Bob", 0) == "Chapter 2, Scene 3 - Point of View"

    # Chapter w/Fallback Focus
    cFormat = f"Chapter {nwHeadFmt.CH_NUM}, Scene {nwHeadFmt.SC_NUM} - {nwHeadFmt.CHAR_FOCUS}"
    assert formatter.apply(cFormat, "Hi Bob", 0) == "Chapter 2, Scene 3 - Focus"

    # Uppercase Headings
    formatter.setUppercase(True)
    assert formatter.apply(nwHeadFmt.TITLE, "Chapter One", 0) == "CHAPTER ONE"


@pytest.mark.core
def testTokenizer_FirstPageAllEmpty(mockGUI):
    """A first page consisting only of blank lines has no non-empty
    block to strip a leading page break from.
    """
    project = NWProject()
    tokens = BareTokenizer(project)
    tokens._handle = TMH
    tokens._isFirst = True
    tokens._text = "\n\n\n"
    tokens.tokenizeText()
    assert tokens._blocks == []
    assert tokens._isFirst is False
