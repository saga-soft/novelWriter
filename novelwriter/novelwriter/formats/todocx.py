"""
novelWriter - DocX Text Converter
=================================

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

import logging
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from typing import TYPE_CHECKING, Literal, NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

from PyQt6.QtCore import QMargins, QSize

from novelwriter import __version__
from novelwriter.common import firstFloat, xmlElement, xmlSubElem
from novelwriter.constants import nwHeadFmt, nwStyles
from novelwriter.formats.shared import BlockFmt, BlockTyp, T_Formats, TextFmt, stripEscape
from novelwriter.formats.tokenizer import COMMENT_BLOCKS, Tokenizer
from novelwriter.types import QtBlack, QtHexRgb

if TYPE_CHECKING:
    from pathlib import Path

    from PyQt6.QtGui import QColor

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

# RegEx
RX_TEXT = re.compile(r"([\n\t])")

# Types and Relationships
OOXML_SCM = "http://schemas.openxmlformats.org"
WORD_BASE = "application/vnd.openxmlformats-officedocument.wordprocessingml"
RELS_TYPE = "application/vnd.openxmlformats-package.relationships+xml"
RELS_BASE = f"{OOXML_SCM}/officeDocument/2006/relationships"

# Main XML NameSpaces
XML_NS = {
    "cp": f"{OOXML_SCM}/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
    "dcterms": "http://purl.org/dc/terms/",
    "r": RELS_BASE,
    "w": f"{OOXML_SCM}/wordprocessingml/2006/main",
    "xml": "http://www.w3.org/XML/1998/namespace",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}
for ns, uri in XML_NS.items():
    ET.register_namespace(ns, uri)


def _wTag(tag: str) -> str:
    """Assemble namespace and tag name for standard w namespace."""
    return f"{{{OOXML_SCM}/wordprocessingml/2006/main}}{tag}"


def _mkTag(ns: str, tag: str) -> str:
    """Assemble namespace and tag name."""
    if uri := XML_NS.get(ns, ""):
        return f"{{{uri}}}{tag}"
    logger.warning("Missing xml namespace '%s'", ns)
    return tag


def _docXCol(color: QColor) -> str:
    """Format a QColor as the DocX accepted value."""
    return color.name(QtHexRgb).lstrip("#")


def _wText(parent: ET.Element, text: str) -> ET.Element:
    """Create a text element and add the preserve flag if necessary."""
    attrib = {}
    if len(text) > len(text.strip()):
        attrib[_mkTag("xml", "space")] = "preserve"
    return xmlSubElem(parent, _wTag("t"), text, attrib=attrib)


def _mmToSz(value: float) -> int:
    """Convert millimetres to internal margin size units."""
    return int(value * 20.0 * 72.0 / 25.4)


# Cached
W_VAL = _wTag("val")

# Formatting Codes
X_BLD = 0x001  # Bold format
X_ITA = 0x002  # Italic format
X_DEL = 0x004  # Strikethrough format
X_UND = 0x008  # Underline format
X_MRK = 0x010  # Marked format
X_SUP = 0x020  # Superscript
X_SUB = 0x040  # Subscript
X_COL = 0x080  # Coloured text
X_HRF = 0x100  # Link

# Formatting Masks
M_BLD = ~X_BLD
M_ITA = ~X_ITA
M_DEL = ~X_DEL
M_UND = ~X_UND
M_MRK = ~X_MRK
M_SUP = ~X_SUP
M_SUB = ~X_SUB
M_COL = ~X_COL
M_HRF = ~X_HRF

# DocX Styles
S_NORM = "Normal"
S_TITLE = "Title"
S_HEAD1 = "Heading1"
S_HEAD2 = "Heading2"
S_HEAD3 = "Heading3"
S_HEAD4 = "Heading4"
S_SEP = "Separator"
S_META = "MetaText"
S_HEAD = "Header"
S_FNOTE = "FootnoteText"


class DocXXmlRel(NamedTuple):
    """DocX XML Rel Data."""

    rId: str
    relType: str
    targetMode: str | None = None


class DocXXmlFile(NamedTuple):
    """DocX XML File Data."""

    xml: ET.Element
    path: str
    contentType: str


class DocXParStyle(NamedTuple):
    """DocX XML Paragraph Style Data."""

    name: str
    styleId: str
    size: float
    basedOn: str | None = None
    nextStyle: str | None = None
    before: float | None = None
    after: float | None = None
    left: float | None = None
    line: float | None = None
    indentFirst: float | None = None
    align: str | None = None
    default: bool = False
    level: int | None = None
    color: str | None = None
    bold: bool = False


class DocXBorder(NamedTuple):
    """DocX Border Data."""

    line: Literal["single", "double", "dashed", "dotted"] = "single"
    color: QColor = QtBlack
    size: int = 6
    space: int = 1
    margin: int = 0


class ToDocX(Tokenizer):
    """Core: DocX Document Writer.

    Extend the Tokenizer class to writer DocX Document files.
    """

    __slots__ = (
        "_files",
        "_fontFamily",
        "_fontSize",
        "_headerFormat",
        "_mHorLine",
        "_pageMargins",
        "_pageOffset",
        "_pageSize",
        "_pars",
        "_rels",
        "_styles",
        "_usedFields",
        "_usedNotes",
    )

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)

        # Properties
        self._headerFormat = ""
        self._pageOffset = 0

        # Internal
        self._fontFamily = "Liberation Serif"
        self._fontSize = 12.0
        self._pageSize = QSize(_mmToSz(210.0), _mmToSz(297.0))
        self._pageMargins = QMargins(_mmToSz(20.0), _mmToSz(20.0), _mmToSz(20.0), _mmToSz(20.0))
        self._mHorLine = _mmToSz(42.5 / 20.0)

        # Data Variables
        self._pars: list[DocXParagraph] = []
        self._rels: dict[str, DocXXmlRel] = {}
        self._files: dict[str, DocXXmlFile] = {}
        self._styles: dict[str, DocXParStyle] = {}
        self._usedNotes: dict[str, int] = {}
        self._usedFields: list[tuple[ET.Element, str]] = []

    ##
    #  Setters
    ##

    def setPageLayout(self, width: float, height: float, top: float, bottom: float, left: float, right: float) -> None:
        """Set the document page size and margins in millimetres."""
        self._pageSize = QSize(_mmToSz(width), _mmToSz(height))
        self._pageMargins = QMargins(_mmToSz(left), _mmToSz(top), _mmToSz(right), _mmToSz(bottom))
        self._mHorLine = _mmToSz((width - left - right) / 80.0)

    def setHeaderFormat(self, value: str, offset: int) -> None:
        """Set the document header format."""
        self._headerFormat = value.strip()
        self._pageOffset = offset

    ##
    #  Class Methods
    ##

    def initDocument(self) -> None:
        """Initialise the DocX document structure."""
        super().initDocument()
        self._fontFamily = self._textFont.family()
        self._fontSize = self._textFont.pointSizeF()
        self._generateStyles()

    def doConvert(self) -> None:
        """Convert the list of text tokens into XML elements."""
        bIndent = self._fontSize * self._blockIndent

        for tType, _, tText, tFormat, tStyle in self._blocks:
            # Create Paragraph
            par = DocXParagraph()
            self._pars.append(par)

            # Styles
            if tStyle & BlockFmt.LEFT:
                par.setAlignment("left")
            elif tStyle & BlockFmt.RIGHT:
                par.setAlignment("right")
            elif tStyle & BlockFmt.CENTRE:
                par.setAlignment("center")
            elif tStyle & BlockFmt.JUSTIFY:
                par.setAlignment("both")

            if tStyle & BlockFmt.PBB:
                par.setPageBreakBefore(True)
            if tStyle & BlockFmt.PBA:
                par.setPageBreakAfter(True)

            if tStyle & BlockFmt.Z_BTM:
                par.setMarginBottom(0.0)
            if tStyle & BlockFmt.Z_TOP:
                par.setMarginTop(0.0)

            if tStyle & BlockFmt.IND_T:
                par.setIndentFirst(True)
            if tStyle & BlockFmt.IND_L:
                par.setMarginLeft(bIndent)
            if tStyle & BlockFmt.IND_R:
                par.setMarginRight(bIndent)

            # Process Text Types
            if tType == BlockTyp.TEXT:
                self._processFragments(par, S_NORM, tText, tFormat)

            elif tType in (BlockTyp.TITLE, BlockTyp.PART):
                self._processFragments(par, S_TITLE, tText, tFormat)

            elif tType == BlockTyp.HEAD1:
                self._processFragments(par, S_HEAD1, tText, tFormat)

            elif tType == BlockTyp.HEAD2:
                self._processFragments(par, S_HEAD2, tText, tFormat)

            elif tType == BlockTyp.HEAD3:
                self._processFragments(par, S_HEAD3, tText, tFormat)

            elif tType == BlockTyp.HEAD4:
                self._processFragments(par, S_HEAD4, tText, tFormat)

            elif tType == BlockTyp.SEP:
                self._processFragments(par, S_SEP, tText)

            elif tType == BlockTyp.HRULE:
                par.setBorder("bottom", DocXBorder(line="single", color=self._theme.comment))
                par.setMarginLeft(self._mHorLine)
                par.setMarginRight(self._mHorLine)
                self._processFragments(par, S_NORM, "")

            elif tType == BlockTyp.SKIP:
                self._processFragments(par, S_NORM, "")

            elif tType in COMMENT_BLOCKS or tType == BlockTyp.KEYWORD:
                self._processFragments(par, S_META, tText, tFormat)

            else:  # pragma: no cover
                pass

    def closeDocument(self) -> None:
        """Generate all the XML."""
        self._coreXml()
        self._appXml()
        self._stylesXml()
        self._fontTableXml()

        fId = None
        dId = None
        if self._headerFormat:
            dId = self._defaultHeaderXml()
            fId = self._firstHeaderXml()

        self._documentXml(fId, dId)
        self._settingsXml()
        if self._usedNotes:
            self._footnotesXml()

    def saveDocument(self, path: Path) -> None:
        """Save the data to a .docx file."""
        # Content Lists
        cExts: list[tuple[str, str]] = []
        cExts.append(("xml", "application/xml"))
        cExts.append(("rels", RELS_TYPE))

        cDocs: list[tuple[str, str]] = []
        cDocs.append(("/_rels/.rels", RELS_TYPE))
        cDocs.append(("/word/_rels/document.xml.rels", RELS_TYPE))

        # Relationships XML
        rRels = xmlElement("Relationships", attrib={"xmlns": f"{OOXML_SCM}/package/2006/relationships"})
        wRels = xmlElement("Relationships", attrib={"xmlns": f"{OOXML_SCM}/package/2006/relationships"})
        for name, rel in self._rels.items():
            isRoot = name in ("core.xml", "app.xml", "document.xml")
            if xml := self._files.get(name):
                target = f"{xml.path}/{name}" if isRoot else name
                cDocs.append((f"/{xml.path}/{name}", xml.contentType))
            else:
                target = name
            attrib = {"Id": rel.rId, "Type": rel.relType, "Target": target}
            if rel.targetMode:
                attrib["TargetMode"] = rel.targetMode
            xmlSubElem(rRels if isRoot else wRels, "Relationship", attrib=attrib)

        # Content Types XML
        dTypes = xmlElement("Types", attrib={"xmlns": f"{OOXML_SCM}/package/2006/content-types"})
        for name, content in cExts:
            xmlSubElem(dTypes, "Default", attrib={"Extension": name, "ContentType": content})
        for name, content in cDocs:
            xmlSubElem(dTypes, "Override", attrib={"PartName": name, "ContentType": content})

        def xmlToZip(name: str, root: ET.Element, zipObj: ZipFile) -> None:
            zipObj.writestr(name, ET.tostring(root, encoding="utf-8", xml_declaration=True))

        with ZipFile(path, mode="w", compression=ZIP_DEFLATED, compresslevel=3) as outZip:
            xmlToZip("_rels/.rels", rRels, outZip)
            xmlToZip("word/_rels/document.xml.rels", wRels, outZip)
            for name, rel in self._files.items():
                xmlToZip(f"{rel.path}/{name}", rel.xml, outZip)
            xmlToZip("[Content_Types].xml", dTypes, outZip)

    ##
    #  Internal Functions
    ##

    def _processFragments(self, par: DocXParagraph, pStyle: str, text: str, tFmt: T_Formats | None = None) -> None:
        """Apply formatting tags to text."""
        par.setStyle(self._styles.get(pStyle))
        xFmt = 0x00
        xNode = None
        fStart = 0
        fLink = ""
        fClass = ""
        for fPos, fFmt, fData in tFmt or []:
            if xNode is not None:
                par.addContent(xNode)
                xNode = None

            if temp := text[fStart:fPos]:
                par.addContent(self._textRunToXml(temp, xFmt, fClass, fLink))

            if fFmt == TextFmt.B_B:
                xFmt |= X_BLD
            elif fFmt == TextFmt.B_E:
                xFmt &= M_BLD
            elif fFmt == TextFmt.I_B:
                xFmt |= X_ITA
            elif fFmt == TextFmt.I_E:
                xFmt &= M_ITA
            elif fFmt == TextFmt.D_B:
                xFmt |= X_DEL
            elif fFmt == TextFmt.D_E:
                xFmt &= M_DEL
            elif fFmt == TextFmt.U_B:
                xFmt |= X_UND
            elif fFmt == TextFmt.U_E:
                xFmt &= M_UND
            elif fFmt == TextFmt.M_B:
                xFmt |= X_MRK
            elif fFmt == TextFmt.M_E:
                xFmt &= M_MRK
            elif fFmt == TextFmt.SUP_B:
                xFmt |= X_SUP
            elif fFmt == TextFmt.SUP_E:
                xFmt &= M_SUP
            elif fFmt == TextFmt.SUB_B:
                xFmt |= X_SUB
            elif fFmt == TextFmt.SUB_E:
                xFmt &= M_SUB
            elif fFmt == TextFmt.COL_B:
                xFmt |= X_COL
                fClass = fData
            elif fFmt == TextFmt.COL_E:
                xFmt &= M_COL
                fClass = ""
            elif fFmt == TextFmt.HRF_B:
                xFmt |= X_HRF
                fLink = fData
            elif fFmt == TextFmt.HRF_E:
                xFmt &= M_HRF
                fLink = ""
            elif fFmt == TextFmt.FNOTE:
                xNode = self._generateFootnote(fData)
            elif fFmt == TextFmt.FIELD:
                xNode = self._generateField(fData, xFmt)
            elif fFmt == TextFmt.STRIP:
                pass

            # Move pos for next pass
            fStart = fPos

        if xNode is not None:
            par.addContent(xNode)

        if temp := text[fStart:]:
            par.addContent(self._textRunToXml(temp, xFmt, fClass, fLink))

    def _textRunToXml(self, text: str | None, fmt: int, fClass: str, fLink: str) -> ET.Element:
        """Encode the text run into XML."""
        xR = xmlElement(_wTag("r"))
        rPr = xmlSubElem(xR, _wTag("rPr"))
        if fmt & X_BLD:
            xmlSubElem(rPr, _wTag("b"))
        if fmt & X_ITA:
            xmlSubElem(rPr, _wTag("i"))
        if fmt & X_UND:
            xmlSubElem(rPr, _wTag("u"), attrib={W_VAL: "single"})
        if fmt & X_MRK:
            xmlSubElem(
                rPr,
                _wTag("shd"),
                attrib={
                    _wTag("fill"): _docXCol(self._theme.highlight),
                    W_VAL: "clear",
                },
            )
        if fmt & X_DEL:
            xmlSubElem(rPr, _wTag("strike"))
        if fmt & X_SUP:
            xmlSubElem(rPr, _wTag("vertAlign"), attrib={W_VAL: "superscript"})
        if fmt & X_SUB:
            xmlSubElem(rPr, _wTag("vertAlign"), attrib={W_VAL: "subscript"})
        if fmt & X_COL and (color := self._classes.get(fClass)):
            xmlSubElem(rPr, _wTag("color"), attrib={W_VAL: _docXCol(color)})

        if isinstance(text, str):
            for segment in RX_TEXT.split(stripEscape(text)):
                if segment == "\n":
                    xmlSubElem(xR, _wTag("br"))
                elif segment == "\t":
                    xmlSubElem(xR, _wTag("tab"))
                elif segment:
                    _wText(xR, segment)

        if fmt & X_HRF and fLink:
            xmlSubElem(rPr, _wTag("rStyle"), attrib={W_VAL: "InternetLink"})
            xH = xmlElement(
                _wTag("hyperlink"),
                attrib={
                    _mkTag("r", "id"): self._appendExternalRel(fLink),
                },
            )
            xH.append(xR)
            return xH

        return xR

    ##
    #  DocX Content
    ##

    def _generateFootnote(self, key: str) -> ET.Element | None:
        """Generate a footnote XML object."""
        if key in self._footnotes:
            idx = len(self._usedNotes) + 1
            xR = xmlElement(_wTag("r"))
            rPr = xmlSubElem(xR, _wTag("rPr"))
            xmlSubElem(rPr, _wTag("vertAlign"), attrib={W_VAL: "superscript"})
            xmlSubElem(xR, _wTag("footnoteReference"), attrib={_wTag("id"): str(idx)})
            self._usedNotes[key] = idx
            return xR
        return None

    def _generateField(self, key: str, fmt: int) -> ET.Element | None:
        """Generate a data field XML object."""
        if key and (field := key.partition(":")[2]):
            xR = self._textRunToXml(None, fmt, "", "")
            xT = _wText(xR, "0")
            self._usedFields.append((xT, field))
            return xR
        return None

    def _generateStyles(self) -> None:
        """Generate usable styles."""
        styles: list[DocXParStyle] = []

        hColor = _docXCol(self._theme.head) if self._colorHeads else None
        fSz = self._fontSize

        # Add Normal Style
        styles.append(
            DocXParStyle(
                name="Normal",
                styleId=S_NORM,
                size=fSz,
                default=True,
                before=fSz * self._marginText[0],
                after=fSz * self._marginText[1],
                line=fSz * self._lineHeight,
                indentFirst=fSz * self._firstWidth,
                align=self._defaultAlign,
            )
        )

        # Add Title
        styles.append(
            DocXParStyle(
                name="Title",
                styleId=S_TITLE,
                size=fSz * self._sizeTitle,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginTitle[0],
                after=fSz * self._marginTitle[1],
                line=fSz * self._lineHeight,
                level=0,
                bold=self._boldHeads,
            )
        )

        # Add Heading 1
        styles.append(
            DocXParStyle(
                name="Heading 1",
                styleId=S_HEAD1,
                size=fSz * self._sizeHead1,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginHead1[0],
                after=fSz * self._marginHead1[1],
                line=fSz * self._lineHeight,
                level=0,
                color=hColor,
                bold=self._boldHeads,
            )
        )

        # Add Heading 2
        styles.append(
            DocXParStyle(
                name="Heading 2",
                styleId=S_HEAD2,
                size=fSz * self._sizeHead2,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginHead2[0],
                after=fSz * self._marginHead2[1],
                line=fSz * self._lineHeight,
                level=1,
                color=hColor,
                bold=self._boldHeads,
            )
        )

        # Add Heading 3
        styles.append(
            DocXParStyle(
                name="Heading 3",
                styleId=S_HEAD3,
                size=fSz * self._sizeHead3,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginHead3[0],
                after=fSz * self._marginHead3[1],
                line=fSz * self._lineHeight,
                level=1,
                color=hColor,
                bold=self._boldHeads,
            )
        )

        # Add Heading 4
        styles.append(
            DocXParStyle(
                name="Heading 4",
                styleId=S_HEAD4,
                size=fSz * self._sizeHead4,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginHead4[0],
                after=fSz * self._marginHead4[1],
                line=fSz * self._lineHeight,
                level=1,
                color=hColor,
                bold=self._boldHeads,
            )
        )

        # Add Separator
        styles.append(
            DocXParStyle(
                name="Separator",
                styleId=S_SEP,
                size=fSz,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginSep[0],
                after=fSz * self._marginSep[1],
                line=fSz * self._lineHeight,
                align="center",
            )
        )

        # Add Text Meta Style
        styles.append(
            DocXParStyle(
                name="Meta Text",
                styleId=S_META,
                size=fSz,
                basedOn=S_NORM,
                nextStyle=S_NORM,
                before=fSz * self._marginMeta[0],
                after=fSz * self._marginMeta[1],
                line=fSz * self._lineHeight,
            )
        )

        # Header
        styles.append(
            DocXParStyle(
                name="Header",
                styleId=S_HEAD,
                size=fSz,
                basedOn=S_NORM,
                align="right",
            )
        )

        # Footnote
        styles.append(
            DocXParStyle(
                name="Footnote Text",
                styleId=S_FNOTE,
                size=nwStyles.T_SMALL * fSz,
                basedOn=S_NORM,
                before=0.0,
                after=fSz * self._marginFoot[1],
                left=fSz * self._marginFoot[0],
                line=fSz * self._lineHeight,
            )
        )

        # Add to Cache
        for style in styles:
            self._styles[style.styleId] = style

    def _nextRelId(self) -> str:
        """Generate the next unique rId."""
        return f"rId{len(self._rels) + 1}"

    def _appendExternalRel(self, target: str) -> str:
        """Append external rel to the registry."""
        if rel := self._rels.get(target):
            return rel.rId
        rId = self._nextRelId()
        self._rels[target] = DocXXmlRel(rId=rId, relType=f"{RELS_BASE}/hyperlink", targetMode="External")
        return rId

    def _appXml(self) -> str:
        """Populate app.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement("Properties", attrib={"xmlns": f"{OOXML_SCM}/officeDocument/2006/extended-properties"})
        self._rels["app.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/extended-properties",
        )
        self._files["app.xml"] = DocXXmlFile(
            xml=xRoot,
            path="docProps",
            contentType="application/vnd.openxmlformats-officedocument.extended-properties+xml",
        )

        xmlSubElem(xRoot, "TotalTime", self._project.data.editTime // 60)
        xmlSubElem(xRoot, "Application", f"novelWriter/{__version__}")
        if count := self._counts.get("allWords"):
            xmlSubElem(xRoot, "Words", count)
        if count := self._counts.get("textWordChars"):
            xmlSubElem(xRoot, "Characters", count)
        if count := self._counts.get("textChars"):
            xmlSubElem(xRoot, "CharactersWithSpaces", count)
        if count := self._counts.get("paragraphCount"):
            xmlSubElem(xRoot, "Paragraphs", count)

        return rId

    def _coreXml(self) -> str:
        """Populate app.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_mkTag("cp", "coreProperties"))
        self._rels["core.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{OOXML_SCM}/package/2006/relationships/metadata/core-properties",
        )
        self._files["core.xml"] = DocXXmlFile(
            xml=xRoot,
            path="docProps",
            contentType="application/vnd.openxmlformats-package.core-properties+xml",
        )

        timeStamp = datetime.now().isoformat(sep="T", timespec="seconds")
        tsAttr = {_mkTag("xsi", "type"): "dcterms:W3CDTF"}
        xmlSubElem(xRoot, _mkTag("dcterms", "created"), timeStamp, attrib=tsAttr)
        xmlSubElem(xRoot, _mkTag("dcterms", "modified"), timeStamp, attrib=tsAttr)
        xmlSubElem(xRoot, _mkTag("dc", "creator"), self._project.data.author)
        xmlSubElem(xRoot, _mkTag("dc", "title"), self._project.data.name)
        xmlSubElem(xRoot, _mkTag("dc", "language"), self._dLocale.name())
        xmlSubElem(xRoot, _mkTag("cp", "revision"), str(self._project.data.saveCount))
        xmlSubElem(xRoot, _mkTag("cp", "lastModifiedBy"), self._project.data.author)

        return rId

    def _stylesXml(self) -> str:
        """Populate styles.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("styles"))
        self._rels["styles.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/styles",
        )
        self._files["styles.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.styles+xml",
        )

        # Default Style
        xStyl = xmlSubElem(xRoot, _wTag("docDefaults"))
        xRDef = xmlSubElem(xStyl, _wTag("rPrDefault"))
        xPDef = xmlSubElem(xStyl, _wTag("pPrDefault"))
        xRPr = xmlSubElem(xRDef, _wTag("rPr"))
        xPPr = xmlSubElem(xPDef, _wTag("pPr"))

        size = str(int(2.0 * self._fontSize))
        line = str(int(20.0 * self._lineHeight * self._fontSize))

        xmlSubElem(
            xRPr,
            _wTag("rFonts"),
            attrib={
                _wTag("ascii"): self._fontFamily,
                _wTag("hAnsi"): self._fontFamily,
                _wTag("cs"): self._fontFamily,
            },
        )
        xmlSubElem(xRPr, _wTag("sz"), attrib={W_VAL: size})
        xmlSubElem(xRPr, _wTag("szCs"), attrib={W_VAL: size})
        xmlSubElem(xRPr, _wTag("lang"), attrib={W_VAL: self._dLocale.name()})
        xmlSubElem(xPPr, _wTag("spacing"), attrib={_wTag("line"): line})

        # Paragraph Styles
        for style in self._styles.values():
            sAttr = {}
            sAttr[_wTag("type")] = "paragraph"
            sAttr[_wTag("styleId")] = style.styleId
            if style.default:
                sAttr[_wTag("default")] = "1"

            size = firstFloat(style.size, self._fontSize)

            xStyl = xmlSubElem(xRoot, _wTag("style"), attrib=sAttr)
            xmlSubElem(xStyl, _wTag("name"), attrib={W_VAL: style.name})
            if style.basedOn:
                xmlSubElem(xStyl, _wTag("basedOn"), attrib={W_VAL: style.basedOn})
            if style.nextStyle:
                xmlSubElem(xStyl, _wTag("next"), attrib={W_VAL: style.nextStyle})

            # pPr Node
            pPr = xmlSubElem(xStyl, _wTag("pPr"))
            xmlSubElem(
                pPr,
                _wTag("spacing"),
                attrib={
                    _wTag("before"): str(int(20.0 * firstFloat(style.before))),
                    _wTag("after"): str(int(20.0 * firstFloat(style.after))),
                    _wTag("line"): str(int(20.0 * firstFloat(style.line, size))),
                    _wTag("lineRule"): "auto",
                },
            )
            if style.left is not None:
                xmlSubElem(
                    pPr,
                    _wTag("ind"),
                    attrib={
                        _wTag("left"): str(int(20.0 * style.left)),
                    },
                )
            if style.align:
                xmlSubElem(pPr, _wTag("jc"), attrib={W_VAL: style.align})
            if style.level is not None:
                xmlSubElem(pPr, _wTag("outlineLvl"), attrib={W_VAL: str(style.level)})

            # rPr Node
            rPr = xmlSubElem(xStyl, _wTag("rPr"))
            if style.bold:
                xmlSubElem(rPr, _wTag("b"))
            if style.color:
                xmlSubElem(rPr, _wTag("color"), attrib={W_VAL: style.color})
            xmlSubElem(rPr, _wTag("sz"), attrib={W_VAL: str(int(2.0 * size))})
            xmlSubElem(rPr, _wTag("szCs"), attrib={W_VAL: str(int(2.0 * size))})

        # Character Style
        xStyl = xmlSubElem(
            xRoot,
            _wTag("style"),
            attrib={_wTag("type"): "character", _wTag("styleId"): "InternetLink"},
        )
        xmlSubElem(xStyl, _wTag("name"), attrib={W_VAL: "Hyperlink"})
        rPr = xmlSubElem(xStyl, _wTag("rPr"))
        xmlSubElem(rPr, _wTag("color"), attrib={W_VAL: _docXCol(self._theme.link)})
        xmlSubElem(rPr, _wTag("u"), attrib={W_VAL: "single"})

        return rId

    def _defaultHeaderXml(self) -> str:
        """Populate header1.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("hdr"))
        self._rels["header1.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/header",
        )
        self._files["header1.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.header+xml",
        )

        xP = xmlSubElem(xRoot, _wTag("p"))
        xPPr = xmlSubElem(xP, _wTag("pPr"))
        xmlSubElem(xPPr, _wTag("pStyle"), attrib={W_VAL: S_HEAD})
        xmlSubElem(xPPr, _wTag("jc"), attrib={W_VAL: "right"})
        xmlSubElem(xPPr, _wTag("rPr"))

        pre, page, post = self._headerFormat.partition(nwHeadFmt.DOC_PAGE)
        pre = pre.replace(nwHeadFmt.DOC_PROJECT, self._project.data.name)
        pre = pre.replace(nwHeadFmt.DOC_AUTHOR, self._project.data.author)
        post = post.replace(nwHeadFmt.DOC_PROJECT, self._project.data.name)
        post = post.replace(nwHeadFmt.DOC_AUTHOR, self._project.data.author)

        wFldCT = _wTag("fldCharType")
        if pre:
            xR = xmlSubElem(xP, _wTag("r"))
            _wText(xR, pre)
        if page:
            xR = xmlSubElem(xP, _wTag("r"))
            xmlSubElem(xR, _wTag("fldChar"), attrib={wFldCT: "begin"})
            xR = xmlSubElem(xP, _wTag("r"))
            xmlSubElem(xR, _wTag("instrText"), "PAGE", attrib={_mkTag("xml", "space"): "preserve"})
            xR = xmlSubElem(xP, _wTag("r"))
            xmlSubElem(xR, _wTag("fldChar"), attrib={wFldCT: "separate"})
            xR = xmlSubElem(xP, _wTag("r"))
            xmlSubElem(xR, _wTag("fldChar"), attrib={wFldCT: "end"})
        if post:
            xR = xmlSubElem(xP, _wTag("r"))
            _wText(xR, post)

        return rId

    def _firstHeaderXml(self) -> str:
        """Populate header2.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("hdr"))
        self._rels["header2.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/header",
        )
        self._files["header2.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.header+xml",
        )

        xP = xmlSubElem(xRoot, _wTag("p"))
        xPPr = xmlSubElem(xP, _wTag("pPr"))
        xmlSubElem(xPPr, _wTag("pStyle"), attrib={W_VAL: S_HEAD})
        xmlSubElem(xPPr, _wTag("jc"), attrib={W_VAL: "right"})
        xmlSubElem(xPPr, _wTag("rPr"))

        xR = xmlSubElem(xP, _wTag("r"))
        xmlSubElem(xR, _wTag("rPr"))

        return rId

    def _documentXml(self, hFirst: str | None, hDefault: str | None) -> str:
        """Populate document.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("document"))
        xBody = xmlSubElem(xRoot, _wTag("body"))
        self._rels["document.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/officeDocument",
        )
        self._files["document.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.document.main+xml",
        )

        # Map all Page Break Before to After where possible
        pars: list[DocXParagraph] = []
        for i, par in enumerate(self._pars):
            if i > 0 and par.pageBreakBefore:
                prev = self._pars[i - 1]
                par.setPageBreakBefore(False)
                prev.setPageBreakAfter(True)

            pars.append(par)

        # Replace fields if there are stats available
        if self._usedFields and self._counts:
            for xField, field in self._usedFields:
                if (value := self._counts.get(field)) is not None:
                    xField.text = self._formatInt(value)

        # Write Paragraphs
        for par in pars:
            par.toXml(xBody)

        # Write Settings
        xSect = xmlSubElem(xBody, _wTag("sectPr"))
        if hFirst and hDefault:
            xmlSubElem(
                xSect,
                _wTag("headerReference"),
                attrib={
                    _wTag("type"): "first",
                    _mkTag("r", "id"): hFirst,
                },
            )
            xmlSubElem(
                xSect,
                _wTag("headerReference"),
                attrib={
                    _wTag("type"): "default",
                    _mkTag("r", "id"): hDefault,
                },
            )

        xFn = xmlSubElem(xSect, _wTag("footnotePr"))
        xmlSubElem(
            xFn,
            _wTag("numFmt"),
            attrib={
                W_VAL: "decimal",
            },
        )

        xmlSubElem(
            xSect,
            _wTag("pgSz"),
            attrib={
                _wTag("w"): str(self._pageSize.width()),
                _wTag("h"): str(self._pageSize.height()),
                _wTag("orient"): "portrait",
            },
        )
        xmlSubElem(
            xSect,
            _wTag("pgMar"),
            attrib={
                _wTag("top"): str(self._pageMargins.top()),
                _wTag("right"): str(self._pageMargins.right()),
                _wTag("bottom"): str(self._pageMargins.bottom()),
                _wTag("left"): str(self._pageMargins.left()),
                _wTag("header"): str(self._pageMargins.top() - int(35.0 * self._fontSize)),
                _wTag("footer"): "0",
                _wTag("gutter"): "0",
            },
        )
        xmlSubElem(
            xSect,
            _wTag("pgNumType"),
            attrib={
                _wTag("start"): str(1 - self._pageOffset),
                _wTag("fmt"): "decimal",
            },
        )
        xmlSubElem(xSect, _wTag("titlePg"))

        return rId

    def _footnotesXml(self) -> str:
        """Populate footnotes.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("footnotes"))
        self._rels["footnotes.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/footnotes",
        )
        self._files["footnotes.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.footnotes+xml",
        )

        for key, idx in self._usedNotes.items():
            par = DocXParagraph()
            par.setIsFootnote(True)
            if content := self._footnotes.get(key):  # pragma: no branch
                self._processFragments(par, S_FNOTE, content[0], content[1])
            par.toXml(xmlSubElem(xRoot, _wTag("footnote"), attrib={_wTag("id"): str(idx)}))

        return rId

    def _fontTableXml(self) -> str:
        """Populate fontTable.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("fonts"))
        self._rels["fontTable.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/fontTable",
        )
        self._files["fontTable.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.fontTable+xml",
        )

        xFont = xmlSubElem(
            xRoot,
            _wTag("font"),
            attrib={
                _wTag("name"): self._textFont.family(),
            },
        )
        xmlSubElem(
            xFont,
            _wTag("pitch"),
            attrib={
                W_VAL: "fixed" if self._textFont.fixedPitch() else "variable",
            },
        )

        return rId

    def _settingsXml(self) -> str:
        """Populate settings.xml."""
        rId = self._nextRelId()
        xRoot = xmlElement(_wTag("settings"))
        self._rels["settings.xml"] = DocXXmlRel(
            rId=rId,
            relType=f"{RELS_BASE}/settings",
        )
        self._files["settings.xml"] = DocXXmlFile(
            xml=xRoot,
            path="word",
            contentType=f"{WORD_BASE}.settings+xml",
        )

        xSet = xmlSubElem(xRoot, _wTag("footnotePr"))
        xmlSubElem(xSet, _wTag("numFmt"), attrib={W_VAL: "decimal"})

        xSet = xmlSubElem(xRoot, _wTag("compat"))
        if not self._justifyOnBreak:
            xmlSubElem(xSet, _wTag("doNotExpandShiftReturn"))
        xmlSubElem(
            xSet,
            _wTag("compatSetting"),
            attrib={
                _wTag("name"): "compatibilityMode",
                _wTag("uri"): "http://schemas.microsoft.com/office/word",
                W_VAL: "12",
            },
        )

        if self._counts:
            xVars = xmlSubElem(xRoot, _wTag("docVars"))
            for key, value in self._counts.items():
                xmlSubElem(
                    xVars,
                    _wTag("docVar"),
                    attrib={
                        _wTag("name"): f"Manuscript{key[:1].upper()}{key[1:]}",
                        W_VAL: str(value),
                    },
                )

        return rId


class DocXParagraph:
    """DocX Text Paragraph.

    This class holds a single paragraph of a DocX document.
    """

    __slots__ = (
        "_borders",
        "_bottomMargin",
        "_breakAfter",
        "_breakBefore",
        "_content",
        "_footnoteRef",
        "_indentFirst",
        "_leftMargin",
        "_rightMargin",
        "_style",
        "_textAlign",
        "_topMargin",
    )

    def __init__(self) -> None:
        self._content: list[ET.Element] = []
        self._style: DocXParStyle | None = None
        self._textAlign: str | None = None
        self._topMargin: float | None = None
        self._bottomMargin: float | None = None
        self._leftMargin: float | None = None
        self._rightMargin: float | None = None
        self._indentFirst = False
        self._breakBefore = False
        self._breakAfter = False
        self._footnoteRef = False
        self._borders: dict[str, DocXBorder] = {}

    ##
    #  Properties
    ##

    @property
    def pageBreakBefore(self) -> bool:
        """Has page break before."""
        return self._breakBefore

    ##
    #  Setters
    ##

    def setStyle(self, style: DocXParStyle | None) -> None:
        """Set the paragraph style."""
        self._style = style

    def setAlignment(self, value: str) -> None:
        """Set paragraph alignment."""
        if value in ("left", "center", "right", "both"):
            self._textAlign = value

    def setMarginTop(self, value: float) -> None:
        """Set margin above in pt."""
        self._topMargin = value

    def setMarginBottom(self, value: float) -> None:
        """Set margin below in pt."""
        self._bottomMargin = value

    def setMarginLeft(self, value: float) -> None:
        """Set margin left in pt."""
        self._leftMargin = value

    def setMarginRight(self, value: float) -> None:
        """Set margin right in pt."""
        self._rightMargin = value

    def setBorder(self, position: str, value: DocXBorder) -> None:
        """Set border for a specific position."""
        self._borders[position] = value

    def setIndentFirst(self, state: bool) -> None:
        """Set first line indent."""
        self._indentFirst = state

    def setPageBreakBefore(self, state: bool) -> None:
        """Set page break before flag."""
        self._breakBefore = state

    def setPageBreakAfter(self, state: bool) -> None:
        """Set page break after flag."""
        self._breakAfter = state

    def setIsFootnote(self, state: bool) -> None:
        """Set is footnote flag."""
        self._footnoteRef = state

    ##
    #  Methods
    ##

    def addContent(self, run: ET.Element) -> None:
        """Add a run segment to the paragraph."""
        self._content.append(run)

    def toXml(self, body: ET.Element) -> None:
        """Generate the XML. Call after all content is set."""
        if style := self._style:
            xP = xmlSubElem(body, _wTag("p"))

            # Values
            indent = {}
            if self._indentFirst and style.indentFirst is not None:
                indent[_wTag("firstLine")] = str(int(20.0 * style.indentFirst))
            if self._leftMargin is not None:
                indent[_wTag("left")] = str(int(20.0 * self._leftMargin))
            if self._rightMargin is not None:
                indent[_wTag("right")] = str(int(20.0 * self._rightMargin))

            # Paragraph
            pPr = xmlSubElem(xP, _wTag("pPr"))
            xmlSubElem(pPr, _wTag("pStyle"), attrib={W_VAL: style.styleId})
            if self._topMargin is not None or self._bottomMargin is not None:
                xmlSubElem(
                    pPr,
                    _wTag("spacing"),
                    attrib={
                        _wTag("before"): str(int(20.0 * firstFloat(self._topMargin, style.before))),
                        _wTag("after"): str(int(20.0 * firstFloat(self._bottomMargin, style.after))),
                        _wTag("line"): str(int(20.0 * firstFloat(style.line, style.size))),
                        _wTag("lineRule"): "auto",
                    },
                )
            if self._borders:
                pBdr = xmlSubElem(pPr, _wTag("pBdr"))
                for position, border in self._borders.items():
                    xmlSubElem(
                        pBdr,
                        _wTag(position),
                        attrib={
                            _wTag("val"): border.line,
                            _wTag("color"): _docXCol(border.color),
                            _wTag("sz"): str(border.size),
                            _wTag("space"): str(border.space),
                        },
                    )
            if indent:
                xmlSubElem(pPr, _wTag("ind"), attrib=indent)
            if self._textAlign:
                xmlSubElem(pPr, _wTag("jc"), attrib={W_VAL: self._textAlign})

            # Text
            if self._footnoteRef:
                xR = xmlSubElem(xP, _wTag("r"))
                rPr = xmlSubElem(xR, _wTag("rPr"))
                xmlSubElem(rPr, _wTag("vertAlign"), attrib={W_VAL: "superscript"})
                xmlSubElem(xR, _wTag("footnoteRef"))
            if self._breakBefore:
                xR = xmlSubElem(xP, _wTag("r"))
                xmlSubElem(xR, _wTag("br"), attrib={_wTag("type"): "page"})
            for xR in self._content:
                xP.append(xR)
            if self._breakAfter:
                xR = xmlSubElem(xP, _wTag("r"))
                xmlSubElem(xR, _wTag("br"), attrib={_wTag("type"): "page"})
