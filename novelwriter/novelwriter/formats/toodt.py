"""
novelWriter - ODT Text Converter
================================

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
import xml.etree.ElementTree as ET

from datetime import datetime
from hashlib import sha256
from typing import TYPE_CHECKING, Final, Literal, NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

from PyQt6.QtGui import QColor, QFont

from novelwriter import __version__
from novelwriter.common import xmlElement, xmlIndent, xmlSubElem
from novelwriter.constants import nwHeadFmt, nwStyles
from novelwriter.formats.shared import BlockFmt, BlockTyp, TextFmt, stripEscape
from novelwriter.formats.tokenizer import COMMENT_BLOCKS, Tokenizer
from novelwriter.types import FONT_STYLE, QtHexRgb

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

# Main XML NameSpaces
XML_NS = {
    "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
    "dc": "http://purl.org/dc/elements/1.1/",
    "fo": "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0",
    "loext": "urn:org:documentfoundation:names:experimental:office:xmlns:loext:1.0",
    "manifest": "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0",
    "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    "number": "urn:oasis:names:tc:opendocument:xmlns:datastyle:1.0",
    "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
    "ooo": "http://openoffice.org/2004/office",
    "style": "urn:oasis:names:tc:opendocument:xmlns:style:1.0",
    "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    "xlink": "http://www.w3.org/1999/xlink",
}
for ns, uri in XML_NS.items():
    ET.register_namespace(ns, uri)


def _mkTag(ns: str, tag: str) -> str:
    """Assemble namespace and tag name."""
    if uri := XML_NS.get(ns, ""):
        return f"{{{uri}}}{tag}"
    logger.warning("Missing xml namespace '%s'", ns)
    return tag


def formatBool(value: bool) -> str:
    """Format a boolean value as 'true' or 'false'."""
    return "true" if value else "false"


# Mimetype and Version
X_MIME = "application/vnd.oasis.opendocument.text"
X_VERS = "1.3"

# Text Formatting Tags
TAG_BR = _mkTag("text", "line-break")
TAG_SPC = _mkTag("text", "s")
TAG_NSPC = _mkTag("text", "c")
TAG_TAB = _mkTag("text", "tab")
TAG_SPAN = _mkTag("text", "span")

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

# ODT Styles
S_TITLE = "Title"
S_HEAD1 = "Heading_20_1"
S_HEAD2 = "Heading_20_2"
S_HEAD3 = "Heading_20_3"
S_HEAD4 = "Heading_20_4"
S_SEP = "Separator"
S_HLINE = "Horizontal_20_Line"
S_FIND = "First_20_line_20_indent"
S_TEXT = "Text_20_body"
S_META = "Text_20_Meta"
S_HNF = "Header_20_and_20_Footer"
S_NUM = "N0"

# Font Data
FONT_WEIGHT_NUM = ["100", "200", "300", "400", "500", "600", "700", "800", "900"]
FONT_WEIGHT_MAP = {"400": "normal", "700": "bold"}


class ToOdt(Tokenizer):
    """Core: Open Document Writer.

    Extend the Tokenizer class to writer Open Document files. The output
    should conform to the 1.3 Extended standard.

    Test with: https://odfvalidator.org/
    """

    __slots__ = (
        "_autoPara",
        "_autoText",
        "_dCont",
        "_dCountry",
        "_dFlat",
        "_dLanguage",
        "_dMeta",
        "_dSett",
        "_dStyl",
        "_errData",
        "_fBlockIndent",
        "_fontBold",
        "_fontFamily",
        "_fontPitch",
        "_fontSize",
        "_fontStyle",
        "_fontWeight",
        "_headWeight",
        "_headerFormat",
        "_isFlat",
        "_mDocBtm",
        "_mDocHeight",
        "_mDocLeft",
        "_mDocRight",
        "_mDocTop",
        "_mDocWidth",
        "_mHorLine",
        "_mainPara",
        "_nNote",
        "_pageOffset",
        "_textFont",
        "_xAut2",
        "_xAuto",
        "_xBody",
        "_xFnt2",
        "_xFont",
        "_xMast",
        "_xMeta",
        "_xSett",
        "_xStyl",
        "_xText",
    )

    def __init__(self, project: NWProject, isFlat: bool) -> None:
        super().__init__(project)

        self._isFlat = isFlat  # Flat: .fodt, otherwise .odt

        self._dFlat = ET.Element("")  # FODT file XML root
        self._dCont = ET.Element("")  # ODT content.xml root
        self._dMeta = ET.Element("")  # ODT meta.xml root
        self._dSett = ET.Element("")  # ODT settings.xml root
        self._dStyl = ET.Element("")  # ODT styles.xml root

        self._xMeta = ET.Element("")  # Office meta root
        self._xSett = ET.Element("")  # Office settings root
        self._xFont = ET.Element("")  # Office font face declaration
        self._xFnt2 = ET.Element("")  # Office font face declaration, secondary
        self._xStyl = ET.Element("")  # Office styles root
        self._xAuto = ET.Element("")  # Office auto-styles root
        self._xAut2 = ET.Element("")  # Office auto-styles root, secondary
        self._xMast = ET.Element("")  # Office master-styles root
        self._xBody = ET.Element("")  # Office body root
        self._xText = ET.Element("")  # Office text root

        self._mainPara: dict[str, ODTParagraphStyle] = {}  # User-accessible paragraph styles
        self._autoPara: dict[str, ODTParagraphStyle] = {}  # Auto-generated paragraph styles
        self._autoText: dict[str, ODTTextStyle] = {}  # Auto-generated text styles

        # Storage
        self._nNote = 0
        self._errData = []  # List of errors encountered

        # Properties
        self._textFont = QFont("Liberation Serif", 12)
        self._headWeight = "bold"
        self._headerFormat = ""
        self._pageOffset = 0

        # Internal
        self._fontFamily = "Liberation Serif"
        self._fontSize = 12
        self._fontWeight = "normal"
        self._fontStyle = "normal"
        self._fontPitch = "variable"
        self._fontBold = "bold"
        self._fBlockIndent = "1.693cm"
        self._dLanguage = "en"
        self._dCountry = "GB"

        # Document Size and Margins
        self._mDocWidth = "21.0cm"
        self._mDocHeight = "29.7cm"
        self._mDocTop = "2.000cm"
        self._mDocBtm = "2.000cm"
        self._mDocLeft = "2.000cm"
        self._mDocRight = "2.000cm"

        # Horizontal Line Margin
        self._mHorLine = "4.250cm"  # Quarter of the text width

    ##
    #  Setters
    ##

    def setPageLayout(self, width: float, height: float, top: float, bottom: float, left: float, right: float) -> None:
        """Set the document page size and margins in millimetres."""
        self._mDocWidth = f"{width / 10.0:.3f}cm"
        self._mDocHeight = f"{height / 10.0:.3f}cm"
        self._mDocTop = f"{top / 10.0:.3f}cm"
        self._mDocBtm = f"{bottom / 10.0:.3f}cm"
        self._mDocLeft = f"{left / 10.0:.3f}cm"
        self._mDocRight = f"{right / 10.0:.3f}cm"
        self._mHorLine = f"{(width - left - right) / 40.0:.3f}cm"  # Quarter of the text width

    def setHeaderFormat(self, value: str, offset: int) -> None:
        """Set the document header format."""
        self._headerFormat = value.strip()
        self._pageOffset = offset

    ##
    #  Class Methods
    ##

    def initDocument(self) -> None:
        """Initialise a new open document XML tree."""
        super().initDocument()

        # Initialise Variables
        # ====================

        lang, _, country = self._dLocale.name().partition("_")
        self._dLanguage = lang or self._dLanguage
        self._dCountry = country or self._dCountry

        self._fontFamily = self._textFont.family()
        self._fontSize = self._textFont.pointSize()
        self._fontStyle = FONT_STYLE.get(self._textFont.style(), "normal")
        self._fontPitch = "fixed" if self._textFont.fixedPitch() else "variable"
        self._headWeight = self._fontBold if self._boldHeads else None
        self._fBlockIndent = self._emToCm(self._blockIndent)

        # Clear Errors
        self._errData = []

        # Create Roots
        # ============

        tAttr = {}
        tAttr[_mkTag("office", "version")] = X_VERS

        fAttr = {}
        fAttr[_mkTag("style", "name")] = self._fontFamily
        fAttr[_mkTag("style", "font-pitch")] = self._fontPitch

        if self._isFlat:
            # FODT File
            # =========

            tAttr[_mkTag("office", "mimetype")] = X_MIME

            tFlat = _mkTag("office", "document")
            self._dFlat = ET.Element(tFlat, attrib=tAttr)

            self._xMeta = ET.SubElement(self._dFlat, _mkTag("office", "meta"))
            self._xSett = ET.SubElement(self._dFlat, _mkTag("office", "settings"))
            self._xFont = ET.SubElement(self._dFlat, _mkTag("office", "font-face-decls"))
            self._xStyl = ET.SubElement(self._dFlat, _mkTag("office", "styles"))
            self._xAuto = ET.SubElement(self._dFlat, _mkTag("office", "automatic-styles"))
            self._xMast = ET.SubElement(self._dFlat, _mkTag("office", "master-styles"))
            self._xBody = ET.SubElement(self._dFlat, _mkTag("office", "body"))

            ET.SubElement(self._xFont, _mkTag("style", "font-face"), attrib=fAttr)

        else:
            # ODT File
            # ========

            tCont = _mkTag("office", "document-content")
            tMeta = _mkTag("office", "document-meta")
            tSett = _mkTag("office", "document-settings")
            tStyl = _mkTag("office", "document-styles")

            # content.xml
            self._dCont = ET.Element(tCont, attrib=tAttr)
            self._xFont = ET.SubElement(self._dCont, _mkTag("office", "font-face-decls"))
            self._xAuto = ET.SubElement(self._dCont, _mkTag("office", "automatic-styles"))
            self._xBody = ET.SubElement(self._dCont, _mkTag("office", "body"))

            # meta.xml
            self._dMeta = ET.Element(tMeta, attrib=tAttr)
            self._xMeta = ET.SubElement(self._dMeta, _mkTag("office", "meta"))

            # settings.xml
            self._dSett = ET.Element(tSett, attrib=tAttr)
            self._xSett = ET.SubElement(self._dSett, _mkTag("office", "settings"))

            # styles.xml
            self._dStyl = ET.Element(tStyl, attrib=tAttr)
            self._xFnt2 = ET.SubElement(self._dStyl, _mkTag("office", "font-face-decls"))
            self._xStyl = ET.SubElement(self._dStyl, _mkTag("office", "styles"))
            self._xAut2 = ET.SubElement(self._dStyl, _mkTag("office", "automatic-styles"))
            self._xMast = ET.SubElement(self._dStyl, _mkTag("office", "master-styles"))

            ET.SubElement(self._xFont, _mkTag("style", "font-face"), attrib=fAttr)
            ET.SubElement(self._xFnt2, _mkTag("style", "font-face"), attrib=fAttr)

        # Finalise
        # ========

        self._xText = ET.SubElement(self._xBody, _mkTag("office", "text"))

        timeStamp = datetime.now().isoformat(sep="T", timespec="seconds")

        # Office Meta Data
        xmlSubElem(self._xMeta, _mkTag("meta", "creation-date"), timeStamp)
        xmlSubElem(self._xMeta, _mkTag("meta", "generator"), f"novelWriter/{__version__}")
        xmlSubElem(self._xMeta, _mkTag("meta", "initial-creator"), self._project.data.author)
        xmlSubElem(self._xMeta, _mkTag("meta", "editing-cycles"), self._project.data.saveCount)

        # Format is: PnYnMnDTnHnMnS
        # https://www.w3.org/TR/2004/REC-xmlschema-2-20041028/#duration
        eT = self._project.data.editTime
        fT = f"P{eT // 86400:d}DT{eT % 86400 // 3600:d}H{eT % 3600 // 60:d}M{eT % 60:d}S"
        xmlSubElem(self._xMeta, _mkTag("meta", "editing-duration"), fT)

        # Dublin Core Meta Data
        xmlSubElem(self._xMeta, _mkTag("dc", "title"), self._project.data.name)
        xmlSubElem(self._xMeta, _mkTag("dc", "date"), timeStamp)
        xmlSubElem(self._xMeta, _mkTag("dc", "creator"), self._project.data.author)

        # Settings
        cAttr = {}
        cAttr[_mkTag("config", "name")] = ET.QName(XML_NS["ooo"], "configuration-settings")
        xCSet = xmlSubElem(self._xSett, _mkTag("config", "config-item-set"), attrib=cAttr)

        cItem = _mkTag("config", "config-item")
        cName = _mkTag("config", "name")
        cType = _mkTag("config", "type")

        cSettings = [
            ("JustifyLinesWithShrinking", "boolean", formatBool(False)),
            ("DoNotJustifyLinesWithManualBreak", "boolean", formatBool(not self._justifyOnBreak)),
        ]
        for sName, sType, sValue in cSettings:
            xmlSubElem(xCSet, cItem, sValue, attrib={cName: sName, cType: sType})

        self._pageStyles()
        self._defaultStyles()
        self._useableStyles()
        self._writeHeader()

    def doConvert(self) -> None:
        """Convert the list of text tokens into XML elements."""
        xText = self._xText
        for tType, _, tText, tFormat, tStyle in self._blocks:
            # Styles
            oStyle = ODTParagraphStyle("New")
            if tStyle & BlockFmt.LEFT:
                oStyle.setTextAlign("left")
            elif tStyle & BlockFmt.RIGHT:
                oStyle.setTextAlign("right")
            elif tStyle & BlockFmt.CENTRE:
                oStyle.setTextAlign("center")
            elif tStyle & BlockFmt.JUSTIFY:
                oStyle.setTextAlign("justify")

            if tStyle & BlockFmt.PBB:
                oStyle.setBreakBefore("page")
            if tStyle & BlockFmt.PBA:
                oStyle.setBreakAfter("page")

            if tStyle & BlockFmt.Z_BTM:
                oStyle.setMarginBottom("0.000cm")
            if tStyle & BlockFmt.Z_TOP:
                oStyle.setMarginTop("0.000cm")

            if tStyle & BlockFmt.IND_L:
                oStyle.setMarginLeft(self._fBlockIndent)
            if tStyle & BlockFmt.IND_R:
                oStyle.setMarginRight(self._fBlockIndent)

            # Process Text Types
            if tType == BlockTyp.TEXT:
                # Text indentation is processed here because there is a
                # dedicated pre-defined style for it
                if tStyle & BlockFmt.IND_T:
                    self._addTextPar(xText, S_FIND, oStyle, tText, tFmt=tFormat)
                else:
                    self._addTextPar(xText, S_TEXT, oStyle, tText, tFmt=tFormat)

            elif tType in (BlockTyp.TITLE, BlockTyp.PART):
                # Title must be text:p
                self._addTextPar(xText, S_TITLE, oStyle, tText, isHead=False)

            elif tType == BlockTyp.HEAD1:
                self._addTextPar(xText, S_HEAD1, oStyle, tText, isHead=True, oLevel="1")

            elif tType == BlockTyp.HEAD2:
                self._addTextPar(xText, S_HEAD2, oStyle, tText, isHead=True, oLevel="2")

            elif tType == BlockTyp.HEAD3:
                self._addTextPar(xText, S_HEAD3, oStyle, tText, isHead=True, oLevel="3")

            elif tType == BlockTyp.HEAD4:
                self._addTextPar(xText, S_HEAD4, oStyle, tText, isHead=True, oLevel="4")

            elif tType == BlockTyp.SEP:
                self._addTextPar(xText, S_SEP, oStyle, tText)

            elif tType == BlockTyp.HRULE:
                self._addTextPar(xText, S_HLINE, oStyle, "")

            elif tType == BlockTyp.SKIP:
                self._addTextPar(xText, S_TEXT, oStyle, "")

            elif tType in COMMENT_BLOCKS or tType == BlockTyp.KEYWORD:
                self._addTextPar(xText, S_META, oStyle, tText, tFmt=tFormat)

            else:  # pragma: no cover
                pass

    def closeDocument(self) -> None:
        """Add additional collected information to the XML."""
        for style in self._autoPara.values():
            style.packXML(self._xAuto)
        for style in self._autoText.values():
            style.packXML(self._xAuto)
        if self._counts:
            xFields = ET.Element(_mkTag("text", "user-field-decls"))
            for key, value in self._counts.items():
                ET.SubElement(
                    xFields,
                    _mkTag("text", "user-field-decl"),
                    attrib={
                        _mkTag("office", "value-type"): "float",
                        _mkTag("office", "value"): str(value),
                        _mkTag("text", "name"): f"Manuscript{key[:1].upper()}{key[1:]}",
                    },
                )
            self._xText.insert(0, xFields)

    def saveDocument(self, path: Path) -> None:
        """Save the data to an .fodt or .odt file."""
        if self._isFlat:
            with open(path, mode="wb") as fObj:
                xml = ET.ElementTree(self._dFlat)
                xmlIndent(xml)
                xml.write(fObj, encoding="utf-8", xml_declaration=True)

        else:
            mMani = _mkTag("manifest", "manifest")
            mVers = _mkTag("manifest", "version")
            mPath = _mkTag("manifest", "full-path")
            mType = _mkTag("manifest", "media-type")
            mFile = _mkTag("manifest", "file-entry")

            xMani = ET.Element(mMani, attrib={mVers: X_VERS})
            ET.SubElement(xMani, mFile, attrib={mPath: "/", mVers: X_VERS, mType: X_MIME})
            ET.SubElement(xMani, mFile, attrib={mPath: "settings.xml", mType: "text/xml"})
            ET.SubElement(xMani, mFile, attrib={mPath: "content.xml", mType: "text/xml"})
            ET.SubElement(xMani, mFile, attrib={mPath: "meta.xml", mType: "text/xml"})
            ET.SubElement(xMani, mFile, attrib={mPath: "styles.xml", mType: "text/xml"})

            def xmlToZip(name: str, root: ET.Element, zipObj: ZipFile) -> None:
                zipObj.writestr(
                    name,
                    ET.tostring(root, encoding="utf-8", xml_declaration=True),
                    compress_type=ZIP_DEFLATED,
                    compresslevel=3,
                )

            with ZipFile(path, mode="w") as outZip:
                outZip.writestr("mimetype", X_MIME, compress_type=None, compresslevel=None)
                xmlToZip("META-INF/manifest.xml", xMani, outZip)
                xmlToZip("settings.xml", self._dSett, outZip)
                xmlToZip("content.xml", self._dCont, outZip)
                xmlToZip("meta.xml", self._dMeta, outZip)
                xmlToZip("styles.xml", self._dStyl, outZip)

        logger.info("Wrote file: %s", path)

    ##
    #  Internal Functions
    ##

    def _addTextPar(
        self,
        xParent: ET.Element,
        styleName: str,
        oStyle: ODTParagraphStyle,
        tText: str,
        tFmt: Sequence[tuple[int, int, str]] | None = None,
        isHead: bool = False,
        oLevel: str | None = None,
    ) -> None:
        """Add a text paragraph to the text XML element."""
        tAttr = {_mkTag("text", "style-name"): self._paraStyle(styleName, oStyle)}
        if oLevel is not None:
            tAttr[_mkTag("text", "outline-level")] = oLevel

        pTag = "h" if isHead else "p"
        xElem = ET.SubElement(xParent, _mkTag("text", pTag), attrib=tAttr)

        # It's important to set the initial text field to empty, otherwise
        # xmlIndent will add a line break if the first subelement is a span.
        xElem.text = ""

        if not tText:
            return

        # Loop Over Fragments
        # ===================

        parProc = XMLParagraph(xElem)

        xFmt = 0x00
        tFrag = ""
        fLast = 0
        xNode = None
        fClass = ""
        fLink = ""
        for fPos, fFmt, fData in tFmt or []:
            # Add any extra nodes
            if xNode is not None:
                parProc.appendNode(xNode)
                xNode = None

            # Add the text up to the current fragment
            if tFrag := tText[fLast:fPos]:
                if xFmt == 0x00:
                    parProc.appendText(tFrag)
                else:
                    parProc.appendSpan(tFrag, self._textStyle(xFmt, fClass), fLink)

            # Calculate the change of format
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

            fLast = fPos

        if xNode is not None:
            parProc.appendNode(xNode)

        if tFrag := tText[fLast:]:
            if xFmt == 0x00:
                parProc.appendText(tFrag)
            else:
                parProc.appendSpan(tFrag, self._textStyle(xFmt, fClass), fLink)

        nErr, errMsg = parProc.checkError()
        if nErr > 0:  # pragma: no cover
            # This one should only capture bugs
            self._errData.append(errMsg)

        return

    def _paraStyle(self, mainName: str, modStyle: ODTParagraphStyle) -> str:
        """Return a name for a style object."""
        if not (refStyle := self._mainPara.get(mainName)):
            logger.error("Unknown main paragraph style '%s'", mainName)
            return "Standard"

        if not refStyle.checkNew(modStyle):
            # The style is unmodified, so we return the main style
            return mainName

        # The style is modified, so we check if there already is an
        # identical style with the same parent we can use instead
        modStyle.setParentStyleName(mainName)
        if (pID := modStyle.getID()) in self._autoPara:
            return self._autoPara[pID].name

        # If neither of the above hold, we store it as a new style
        modStyle.setName(f"P{len(self._autoPara) + 1:d}")
        self._autoPara[pID] = modStyle

        return modStyle.name

    def _textStyle(self, hFmt: int, fClass: str = "") -> str:
        """Return a text style for a given style code."""
        tKey = str(hFmt)
        color = None
        if fClass and (color := self._classes.get(fClass)):
            tKey = f"{tKey}:{fClass}"
        if tKey in self._autoText:
            return self._autoText[tKey].name

        style = ODTTextStyle(f"T{len(self._autoText) + 1:d}")
        if hFmt & X_BLD:
            style.setFontWeight(self._fontBold)
        if hFmt & X_ITA:
            style.setFontStyle("italic")
        if hFmt & X_DEL:
            style.setStrikeStyle("solid")
            style.setStrikeType("single")
        if hFmt & X_UND:
            style.setUnderlineStyle("solid")
            style.setUnderlineWidth("auto")
            style.setUnderlineColor("font-color")
        if hFmt & X_MRK:
            style.setBackgroundColor(self._theme.highlight)
        if hFmt & X_SUP:
            style.setTextPosition("super")
        if hFmt & X_SUB:
            style.setTextPosition("sub")
        if hFmt & X_COL and color:
            style.setColor(color)
        if hFmt & X_HRF:
            style.setColor(self._theme.link)
            style.setUnderlineStyle("solid")
            style.setUnderlineWidth("auto")
            style.setUnderlineColor("font-color")
        self._autoText[tKey] = style

        return style.name

    def _generateFootnote(self, key: str) -> ET.Element | None:
        """Generate a footnote XML object."""
        if content := self._footnotes.get(key):
            self._nNote += 1
            nStyle = ODTParagraphStyle("New")
            xNote = xmlElement(
                _mkTag("text", "note"),
                attrib={
                    _mkTag("text", "id"): f"ftn{self._nNote}",
                    _mkTag("text", "note-class"): "footnote",
                },
            )
            xmlSubElem(xNote, _mkTag("text", "note-citation"), self._nNote)
            xBody = xmlSubElem(xNote, _mkTag("text", "note-body"))
            self._addTextPar(xBody, "Footnote", nStyle, content[0], tFmt=content[1])
            return xNote
        return None

    def _generateField(self, key: str, fmt: int) -> ET.Element | None:
        """Generate a data field XML object."""
        if key and (field := key.partition(":")[2]):
            xField = xmlElement(
                _mkTag("text", "user-field-get"),
                "0",
                tail="",
                attrib={
                    _mkTag("style", "data-style-name"): S_NUM,
                    _mkTag("text", "name"): f"Manuscript{field[:1].upper()}{field[1:]}",
                },
            )
            if fmt == 0x00:
                return xField
            else:
                xSpan = xmlElement(
                    TAG_SPAN,
                    "",
                    tail="",
                    attrib={
                        _mkTag("text", "style-name"): self._textStyle(fmt),
                    },
                )
                xSpan.append(xField)
                return xSpan
        return None

    def _emToCm(self, value: float) -> str:
        """Convert an em value to centimetres."""
        return f"{value * self._fontSize * 2.54 / 72.0:.3f}cm"

    def _emToPt(self, scale: float) -> str:
        """Compute relative font size in points."""
        return f"{round(scale * self._fontSize):d}pt"

    ##
    #  Style Elements
    ##

    def _pageStyles(self) -> None:
        """Set the default page style."""
        xPage = ET.SubElement(
            self._xAuto if self._isFlat else self._xAut2,
            _mkTag("style", "page-layout"),
            attrib={_mkTag("style", "name"): "PM1"},
        )
        ET.SubElement(
            xPage,
            _mkTag("style", "page-layout-properties"),
            attrib={
                _mkTag("fo", "page-width"): self._mDocWidth,
                _mkTag("fo", "page-height"): self._mDocHeight,
                _mkTag("fo", "margin-top"): self._mDocTop,
                _mkTag("fo", "margin-bottom"): self._mDocBtm,
                _mkTag("fo", "margin-left"): self._mDocLeft,
                _mkTag("fo", "margin-right"): self._mDocRight,
            },
        )

        xHead = ET.SubElement(xPage, _mkTag("style", "header-style"))
        ET.SubElement(
            xHead,
            _mkTag("style", "header-footer-properties"),
            attrib={
                _mkTag("fo", "min-height"): self._emToCm(1.5),
                _mkTag("fo", "margin-left"): "0.000cm",
                _mkTag("fo", "margin-right"): "0.000cm",
                _mkTag("fo", "margin-bottom"): self._emToCm(0.5),
            },
        )

    def _defaultStyles(self) -> None:
        """Set the default styles."""
        textSize = self._emToPt(nwStyles.T_NORMAL)

        # Add Paragraph Family Style
        xStyl = ET.SubElement(
            self._xStyl,
            _mkTag("style", "default-style"),
            attrib={
                _mkTag("style", "family"): "paragraph",
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("style", "paragraph-properties"),
            attrib={
                _mkTag("style", "line-break"): "strict",
                _mkTag("style", "tab-stop-distance"): "1.251cm",
                _mkTag("style", "writing-mode"): "page",
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("style", "text-properties"),
            attrib={
                _mkTag("style", "font-name"): self._fontFamily,
                _mkTag("fo", "font-family"): self._fontFamily,
                _mkTag("fo", "font-weight"): self._fontWeight,
                _mkTag("fo", "font-style"): self._fontStyle,
                _mkTag("fo", "font-size"): textSize,
                _mkTag("fo", "language"): self._dLanguage,
                _mkTag("fo", "country"): self._dCountry,
            },
        )

        # Add Standard Paragraph Style
        xStyl = ET.SubElement(
            self._xStyl,
            _mkTag("style", "style"),
            attrib={
                _mkTag("style", "name"): "Standard",
                _mkTag("style", "family"): "paragraph",
                _mkTag("style", "class"): "text",
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("style", "text-properties"),
            attrib={
                _mkTag("style", "font-name"): self._fontFamily,
                _mkTag("fo", "font-family"): self._fontFamily,
                _mkTag("fo", "font-weight"): self._fontWeight,
                _mkTag("fo", "font-style"): self._fontStyle,
                _mkTag("fo", "font-size"): textSize,
            },
        )

        # Add Default Heading Style
        xStyl = ET.SubElement(
            self._xStyl,
            _mkTag("style", "style"),
            attrib={
                _mkTag("style", "name"): "Heading",
                _mkTag("style", "family"): "paragraph",
                _mkTag("style", "parent-style-name"): "Standard",
                _mkTag("style", "next-style-name"): S_TEXT,
                _mkTag("style", "class"): "text",
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("style", "paragraph-properties"),
            attrib={
                _mkTag("fo", "margin-top"): self._emToCm(self._marginHead4[0]),
                _mkTag("fo", "margin-bottom"): self._emToCm(self._marginHead4[1]),
                _mkTag("fo", "keep-with-next"): "always",
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("style", "text-properties"),
            attrib={
                _mkTag("style", "font-name"): self._fontFamily,
                _mkTag("fo", "font-family"): self._fontFamily,
                _mkTag("fo", "font-weight"): self._fontWeight,
                _mkTag("fo", "font-style"): self._fontStyle,
                _mkTag("fo", "font-size"): self._emToPt(self._sizeHead4),
            },
        )

        # Add Header and Footer Styles
        ET.SubElement(
            self._xStyl,
            _mkTag("style", "style"),
            attrib={
                _mkTag("style", "name"): S_HNF,
                _mkTag("style", "display-name"): "Header and Footer",
                _mkTag("style", "family"): "paragraph",
                _mkTag("style", "parent-style-name"): "Standard",
                _mkTag("style", "class"): "extra",
            },
        )

        # Numbers Style
        xStyl = ET.SubElement(
            self._xStyl,
            _mkTag("number", "number-style"),
            attrib={
                _mkTag("style", "name"): S_NUM,
            },
        )
        ET.SubElement(
            xStyl,
            _mkTag("number", "number"),
            attrib={
                _mkTag("number", "min-integer-digits"): "1",
            },
        )

    def _useableStyles(self) -> None:
        """Set the usable styles."""
        hColor = self._theme.head if self._colorHeads else None

        textSize = self._emToPt(nwStyles.T_NORMAL)
        lineHeight = f"{round(100 * self._lineHeight):d}%"

        # Add Text Body Style
        style = ODTParagraphStyle(S_TEXT)
        style.setDisplayName("Text body")
        style.setParentStyleName("Standard")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginText[0]))
        style.setMarginBottom(self._emToCm(self._marginText[1]))
        style.setLineHeight(lineHeight)
        style.setTextAlign(self._defaultAlign)
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(textSize)
        style.setFontWeight(self._fontWeight)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add First Line Indent Style
        style = ODTParagraphStyle(S_FIND)
        style.setDisplayName("First line indent")
        style.setParentStyleName(S_TEXT)
        style.setClass("text")
        style.setTextIndent(self._emToCm(self._firstWidth))
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Text Meta Style
        style = ODTParagraphStyle(S_META)
        style.setDisplayName("Text Meta")
        style.setParentStyleName("Standard")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginMeta[0]))
        style.setMarginBottom(self._emToCm(self._marginMeta[1]))
        style.setLineHeight(lineHeight)
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(textSize)
        style.setFontWeight(self._fontWeight)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Title Style
        style = ODTParagraphStyle(S_TITLE)
        style.setDisplayName("Title")
        style.setParentStyleName("Heading")
        style.setNextStyleName(S_TEXT)
        style.setClass("chapter")
        style.setMarginTop(self._emToCm(self._marginTitle[0]))
        style.setMarginBottom(self._emToCm(self._marginTitle[1]))
        style.setTextAlign("center")
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(self._emToPt(self._sizeTitle))
        style.setFontWeight(self._headWeight)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Separator Style
        style = ODTParagraphStyle(S_SEP)
        style.setDisplayName("Separator")
        style.setParentStyleName("Standard")
        style.setNextStyleName(S_TEXT)
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginSep[0]))
        style.setMarginBottom(self._emToCm(self._marginSep[1]))
        style.setLineHeight(lineHeight)
        style.setTextAlign("center")
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(textSize)
        style.setFontWeight(self._fontWeight)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Horizontal Line Style
        style = ODTParagraphStyle(S_HLINE)
        style.setDisplayName("Horizontal Line")
        style.setParentStyleName("Standard")
        style.setNextStyleName(S_TEXT)
        style.setClass("html")
        style.setMarginTop(self._emToCm(0))
        style.setMarginBottom(self._emToCm(self._marginSep[1]))
        style.setMarginLeft(self._mHorLine)
        style.setMarginRight(self._mHorLine)
        style.setBorderLeft(ODTBorderStyle("none"))
        style.setBorderRight(ODTBorderStyle("none"))
        style.setBorderTop(ODTBorderStyle("none"))
        style.setBorderBottom(ODTBorderStyle("solid", 0.75, self._theme.comment))
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Heading 1 Style
        style = ODTParagraphStyle(S_HEAD1)
        style.setDisplayName("Heading 1")
        style.setParentStyleName("Heading")
        style.setNextStyleName(S_TEXT)
        style.setOutlineLevel("1")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginHead1[0]))
        style.setMarginBottom(self._emToCm(self._marginHead1[1]))
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(self._emToPt(self._sizeHead1))
        style.setFontWeight(self._headWeight)
        style.setColor(hColor)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Heading 2 Style
        style = ODTParagraphStyle(S_HEAD2)
        style.setDisplayName("Heading 2")
        style.setParentStyleName("Heading")
        style.setNextStyleName(S_TEXT)
        style.setOutlineLevel("2")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginHead2[0]))
        style.setMarginBottom(self._emToCm(self._marginHead2[1]))
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(self._emToPt(self._sizeHead2))
        style.setFontWeight(self._headWeight)
        style.setColor(hColor)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Heading 3 Style
        style = ODTParagraphStyle(S_HEAD3)
        style.setDisplayName("Heading 3")
        style.setParentStyleName("Heading")
        style.setNextStyleName(S_TEXT)
        style.setOutlineLevel("3")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginHead3[0]))
        style.setMarginBottom(self._emToCm(self._marginHead3[1]))
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(self._emToPt(self._sizeHead3))
        style.setFontWeight(self._headWeight)
        style.setColor(hColor)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Heading 4 Style
        style = ODTParagraphStyle(S_HEAD4)
        style.setDisplayName("Heading 4")
        style.setParentStyleName("Heading")
        style.setNextStyleName(S_TEXT)
        style.setOutlineLevel("4")
        style.setClass("text")
        style.setMarginTop(self._emToCm(self._marginHead4[0]))
        style.setMarginBottom(self._emToCm(self._marginHead4[1]))
        style.setFontName(self._fontFamily)
        style.setFontFamily(self._fontFamily)
        style.setFontSize(self._emToPt(self._sizeHead4))
        style.setFontWeight(self._headWeight)
        style.setColor(hColor)
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Header Style
        style = ODTParagraphStyle("Header")
        style.setDisplayName("Header")
        style.setParentStyleName(S_HNF)
        style.setTextAlign("right")
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

        # Add Footnote Style
        style = ODTParagraphStyle("Footnote")
        style.setDisplayName("Footnote")
        style.setParentStyleName("Standard")
        style.setClass("extra")
        style.setMarginLeft(self._emToCm(self._marginFoot[0]))
        style.setMarginBottom(self._emToCm(self._marginFoot[1]))
        style.setTextIndent("-" + self._emToCm(self._marginFoot[0]))
        style.setFontSize(self._emToPt(nwStyles.T_SMALL))
        style.packXML(self._xStyl)
        self._mainPara[style.name] = style

    def _writeHeader(self) -> None:
        """Write the header elements."""
        xPage = ET.SubElement(
            self._xMast,
            _mkTag("style", "master-page"),
            attrib={
                _mkTag("style", "name"): "Standard",
                _mkTag("style", "page-layout-name"): "PM1",
            },
        )

        # Standard Page Header
        if self._headerFormat:
            pre, page, post = self._headerFormat.partition(nwHeadFmt.DOC_PAGE)

            pre = pre.replace(nwHeadFmt.DOC_PROJECT, self._project.data.name)
            pre = pre.replace(nwHeadFmt.DOC_AUTHOR, self._project.data.author)
            post = post.replace(nwHeadFmt.DOC_PROJECT, self._project.data.name)
            post = post.replace(nwHeadFmt.DOC_AUTHOR, self._project.data.author)

            xHead = ET.SubElement(xPage, _mkTag("style", "header"))
            xPar = ET.SubElement(xHead, _mkTag("text", "p"), attrib={_mkTag("text", "style-name"): "Header"})
            xPar.text = pre
            if page:
                attr = {_mkTag("text", "select-page"): "current"}
                if self._pageOffset > 0:
                    attr = {_mkTag("text", "page-adjust"): str(0 - self._pageOffset)}
                xTail = ET.SubElement(xPar, _mkTag("text", "page-number"), attrib=attr)
                xTail.text = "2"
                xTail.tail = post
            else:
                xPar.text += post

        # First Page Header
        xHead = ET.SubElement(xPage, _mkTag("style", "header-first"))
        xPar = ET.SubElement(xHead, _mkTag("text", "p"), attrib={_mkTag("text", "style-name"): "Header"})


# Auto-Style Classes
# ==================


class ODTParagraphStyle:
    """Wrapper class for the paragraph style setting used by the
    exporter. Only the used settings are exposed here to keep the class
    minimal and fast.
    """

    __slots__ = ("_mAttr", "_name", "_pAttr", "_tAttr")

    VALID_ALIGN: Final[list[str]] = ["start", "center", "end", "justify", "left", "right"]
    VALID_BREAK: Final[list[str]] = ["auto", "page", "even-page", "odd-page", "inherit"]
    VALID_LEVEL: Final[list[str]] = ["1", "2", "3", "4"]
    VALID_CLASS: Final[list[str]] = ["text", "chapter", "extra", "html"]
    VALID_WEIGHT: Final[list[str]] = ["normal", "bold", *FONT_WEIGHT_NUM]

    def __init__(self, name: str) -> None:

        self._name = name

        # Attributes
        self._mAttr = {
            "display-name": ["style", None],
            "parent-style-name": ["style", None],
            "next-style-name": ["style", None],
            "default-outline-level": ["style", None],
            "class": ["style", None],
        }

        # Paragraph Attributes
        self._pAttr = {
            "margin-top": ["fo", None],
            "margin-bottom": ["fo", None],
            "margin-left": ["fo", None],
            "margin-right": ["fo", None],
            "border-left": ["fo", None],
            "border-right": ["fo", None],
            "border-top": ["fo", None],
            "border-bottom": ["fo", None],
            "text-indent": ["fo", None],
            "line-height": ["fo", None],
            "text-align": ["fo", None],
            "break-before": ["fo", None],
            "break-after": ["fo", None],
        }

        # Text Attributes
        self._tAttr = {
            "font-name": ["style", None],
            "font-family": ["fo", None],
            "font-size": ["fo", None],
            "font-weight": ["fo", None],
            "color": ["fo", None],
            "opacity": ["loext", None],
        }

    @property
    def name(self) -> str:
        return self._name

    ##
    #  Setters
    ##

    def setName(self, name: str) -> None:
        """Set the paragraph style name."""
        self._name = name

    ##
    #  Attribute Setters
    ##

    def setDisplayName(self, value: str | None) -> None:
        """Set style display name."""
        self._mAttr["display-name"][1] = value

    def setParentStyleName(self, value: str | None) -> None:
        """Set parent style name."""
        self._mAttr["parent-style-name"][1] = value

    def setNextStyleName(self, value: str | None) -> None:
        """Set next style name."""
        self._mAttr["next-style-name"][1] = value

    def setOutlineLevel(self, value: str | None) -> None:
        """Set paragraph outline level."""
        if value in self.VALID_LEVEL:
            self._mAttr["default-outline-level"][1] = value
        else:
            self._mAttr["default-outline-level"][1] = None

    def setClass(self, value: str | None) -> None:
        """Set paragraph class."""
        if value in self.VALID_CLASS:
            self._mAttr["class"][1] = value
        else:
            self._mAttr["class"][1] = None

    ##
    #  Paragraph Setters
    ##

    def setMarginTop(self, value: str | None) -> None:
        """Set paragraph top margin."""
        self._pAttr["margin-top"][1] = value

    def setMarginBottom(self, value: str | None) -> None:
        """Set paragraph bottom margin."""
        self._pAttr["margin-bottom"][1] = value

    def setMarginLeft(self, value: str | None) -> None:
        """Set paragraph left margin."""
        self._pAttr["margin-left"][1] = value

    def setMarginRight(self, value: str | None) -> None:
        """Set paragraph right margin."""
        self._pAttr["margin-right"][1] = value

    def setBorderLeft(self, value: ODTBorderStyle | None) -> None:
        """Set paragraph left border."""
        self._pAttr["border-left"][1] = None if value is None else str(value)

    def setBorderRight(self, value: ODTBorderStyle | None) -> None:
        """Set paragraph right border."""
        self._pAttr["border-right"][1] = None if value is None else str(value)

    def setBorderTop(self, value: ODTBorderStyle | None) -> None:
        """Set paragraph top border."""
        self._pAttr["border-top"][1] = None if value is None else str(value)

    def setBorderBottom(self, value: ODTBorderStyle | None) -> None:
        """Set paragraph bottom border."""
        self._pAttr["border-bottom"][1] = None if value is None else str(value)

    def setTextIndent(self, value: str | None) -> None:
        """Set text indentation."""
        self._pAttr["text-indent"][1] = value

    def setLineHeight(self, value: str | None) -> None:
        """Set line height."""
        self._pAttr["line-height"][1] = value

    def setTextAlign(self, value: str | None) -> None:
        """Set paragraph text alignment."""
        if value in self.VALID_ALIGN:
            self._pAttr["text-align"][1] = value
        else:
            self._pAttr["text-align"][1] = None

    def setBreakBefore(self, value: str | None) -> None:
        """Set page break before policy."""
        if value in self.VALID_BREAK:
            self._pAttr["break-before"][1] = value
        else:
            self._pAttr["break-before"][1] = None

    def setBreakAfter(self, value: str | None) -> None:
        """Set page break after policy."""
        if value in self.VALID_BREAK:
            self._pAttr["break-after"][1] = value
        else:
            self._pAttr["break-after"][1] = None

    ##
    #  Text Setters
    ##

    def setFontName(self, value: str | None) -> None:
        """Set font name."""
        self._tAttr["font-name"][1] = value

    def setFontFamily(self, value: str | None) -> None:
        """Set font family."""
        self._tAttr["font-family"][1] = value

    def setFontSize(self, value: str | None) -> None:
        """Set font size."""
        self._tAttr["font-size"][1] = value

    def setFontWeight(self, value: str | None) -> None:
        """Set font weight."""
        if value in self.VALID_WEIGHT:
            self._tAttr["font-weight"][1] = value
        else:
            self._tAttr["font-weight"][1] = None

    def setColor(self, value: QColor | None) -> None:
        """Set text colour."""
        if isinstance(value, QColor):
            self._tAttr["color"][1] = value.name(QtHexRgb)
            self._tAttr["opacity"][1] = f"{int(100.0 * value.alphaF())}%"
        else:
            self._tAttr["color"][1] = None
            self._tAttr["opacity"][1] = None

    ##
    #  Methods
    ##

    def checkNew(self, style: ODTParagraphStyle) -> bool:
        """Check if there are new settings in style that differ from
        those in this object. Unset styles are ignored as they can be
        inherited from the parent style.
        """
        return (
            any(v and v != self._mAttr[m][1] for m, (_, v) in style._mAttr.items())
            or any(v and v != self._pAttr[m][1] for m, (_, v) in style._pAttr.items())
            or any(v and v != self._tAttr[m][1] for m, (_, v) in style._tAttr.items())
        )

    def getID(self) -> str:
        """Generate a unique ID from the settings."""
        return sha256(
            (f"Paragraph:Main:{self._mAttr!s}:Paragraph:Para:{self._pAttr!s}:Paragraph:Text:{self._tAttr!s}:").encode()
        ).hexdigest()

    def packXML(self, xParent: ET.Element) -> None:
        """Pack the content into an xml element."""
        attr = {
            _mkTag("style", "name"): self._name,
            _mkTag("style", "family"): "paragraph",
        }
        attr.update({_mkTag(n, m): v for m, (n, v) in self._mAttr.items() if v})
        xEntry = ET.SubElement(xParent, _mkTag("style", "style"), attrib=attr)

        if attr := {_mkTag(n, m): v for m, (n, v) in self._pAttr.items() if v}:
            ET.SubElement(xEntry, _mkTag("style", "paragraph-properties"), attrib=attr)

        if attr := {_mkTag(n, m): v for m, (n, v) in self._tAttr.items() if v}:
            ET.SubElement(xEntry, _mkTag("style", "text-properties"), attrib=attr)


class ODTBorderStyle(NamedTuple):
    """Named tuple for border styles."""

    style: Literal["none", "solid", "dashed", "dotted", "double"] = "none"
    width: float | None = None
    color: QColor | None = None

    def __str__(self) -> str:
        """Convert the border style to a string that can be used in ODT XML."""
        values = [self.style]
        if self.width is not None:
            values.insert(0, f"{self.width:.2f}pt")
        if self.color is not None:
            values.append(self.color.name(QtHexRgb))
        return " ".join(values)


class ODTTextStyle:
    """Wrapper class for the text style setting used by the exporter.
    Only the used settings are exposed here to keep the class minimal
    and fast.
    """

    __slots__ = ("_name", "_tAttr")

    VALID_WEIGHT: Final[list[str]] = ["normal", "bold", *FONT_WEIGHT_NUM]
    VALID_STYLE: Final[list[str]] = ["normal", "italic", "oblique"]
    VALID_POS: Final[list[str]] = ["super", "sub"]
    VALID_LSTYLE: Final[list[str]] = ["none", "solid"]
    VALID_LTYPE: Final[list[str]] = ["single", "double"]
    VALID_LWIDTH: Final[list[str]] = ["auto"]
    VALID_LCOL: Final[list[str]] = ["font-color"]

    def __init__(self, name: str) -> None:
        self._name = name
        self._tAttr = {
            "font-weight": ["fo", None],
            "font-style": ["fo", None],
            "color": ["fo", None],
            "background-color": ["fo", None],
            "text-position": ["style", None],
            "text-line-through-style": ["style", None],
            "text-line-through-type": ["style", None],
            "text-underline-style": ["style", None],
            "text-underline-width": ["style", None],
            "text-underline-color": ["style", None],
        }

    @property
    def name(self) -> str:
        return self._name

    ##
    #  Setters
    ##

    def setFontWeight(self, value: str | None) -> None:
        """Set text font weight."""
        if value in self.VALID_WEIGHT:
            self._tAttr["font-weight"][1] = value
        else:
            self._tAttr["font-weight"][1] = None

    def setFontStyle(self, value: str | None) -> None:
        """Set text font style."""
        if value in self.VALID_STYLE:
            self._tAttr["font-style"][1] = value
        else:
            self._tAttr["font-style"][1] = None

    def setColor(self, value: QColor | None) -> None:
        """Set text colour."""
        if isinstance(value, QColor):
            self._tAttr["color"][1] = value.name(QtHexRgb)
        else:
            self._tAttr["color"][1] = None

    def setBackgroundColor(self, value: QColor | None) -> None:
        """Set text background colour."""
        if isinstance(value, QColor):
            self._tAttr["background-color"][1] = value.name(QtHexRgb)
        else:
            self._tAttr["background-color"][1] = None

    def setTextPosition(self, value: str | None) -> None:
        """Set text vertical position."""
        if value in self.VALID_POS:
            self._tAttr["text-position"][1] = f"{value} 58%"
        else:
            self._tAttr["text-position"][1] = None

    def setStrikeStyle(self, value: str | None) -> None:
        """Set text line-trough style."""
        if value in self.VALID_LSTYLE:
            self._tAttr["text-line-through-style"][1] = value
        else:
            self._tAttr["text-line-through-style"][1] = None

    def setStrikeType(self, value: str | None) -> None:
        """Set text line-through type."""
        if value in self.VALID_LTYPE:
            self._tAttr["text-line-through-type"][1] = value
        else:
            self._tAttr["text-line-through-type"][1] = None

    def setUnderlineStyle(self, value: str | None) -> None:
        """Set text underline style."""
        if value in self.VALID_LSTYLE:
            self._tAttr["text-underline-style"][1] = value
        else:
            self._tAttr["text-underline-style"][1] = None

    def setUnderlineWidth(self, value: str | None) -> None:
        """Set text underline width."""
        if value in self.VALID_LWIDTH:
            self._tAttr["text-underline-width"][1] = value
        else:
            self._tAttr["text-underline-width"][1] = None

    def setUnderlineColor(self, value: str | None) -> None:
        """Set text underline colour."""
        if value in self.VALID_LCOL:
            self._tAttr["text-underline-color"][1] = value
        else:
            self._tAttr["text-underline-color"][1] = None

    ##
    #  Methods
    ##

    def packXML(self, xParent: ET.Element) -> None:
        """Pack the content into an xml element."""
        xEntry = ET.SubElement(
            xParent,
            _mkTag("style", "style"),
            attrib={
                _mkTag("style", "name"): self._name,
                _mkTag("style", "family"): "text",
            },
        )
        if attr := {_mkTag(n, m): v for m, (n, v) in self._tAttr.items() if v}:
            ET.SubElement(xEntry, _mkTag("style", "text-properties"), attrib=attr)


# XML Complex Element Helper Class
# ================================

X_ROOT_TEXT = 0
X_ROOT_TAIL = 1
X_SPAN_TEXT = 2
X_SPAN_SING = 3


class XMLParagraph:
    """ODT Text Paragraph.

    This is a helper class to manage the text content of a single
    XML element using mixed content tags.

    Rules:
     * The root tag can only have text set, never tail.
     * Any span must be under root, and the text in the span is set in
       one pass. The span then becomes the new base element using tail
       for further added text, permanently replacing root.
     * Any single special tags like tabs, line breaks or multi-spaces,
       should never have text set. After insertion, they become the next
       tail tag if on root level, or if in a span, only exists within
       the lifetime of the span. In this case, the span becomes the new
       tail.

    The four constants associated with this class represent the only
    allowed states the class can exist in, which dictates which XML
    object and attribute is written to,
    """

    __slots__ = ("_chrPos", "_nState", "_rawTxt", "_xRoot", "_xSing", "_xTail")

    def __init__(self, xRoot: ET.Element) -> None:

        self._xRoot = xRoot
        self._xTail = ET.Element("")
        self._xSing = ET.Element("")

        self._nState = X_ROOT_TEXT
        self._chrPos = 0
        self._rawTxt = ""
        self._xRoot.text = ""

    def appendText(self, text: str) -> None:
        """Append text to the XML element. We do this one character at
        the time in order to be able to process line breaks, tabs and
        spaces separately. Multiple spaces are concatenated into a
        single tag, and must therefore be processed separately.
        """
        text = stripEscape(text)
        nSpaces = 0
        self._rawTxt += text

        for c in text:
            if c == " ":
                nSpaces += 1
                continue
            if nSpaces > 0:
                self._processSpaces(nSpaces)
                nSpaces = 0

            if c == "\n":
                if self._nState in (X_ROOT_TEXT, X_ROOT_TAIL):
                    self._xTail = ET.SubElement(self._xRoot, TAG_BR)
                    self._xTail.tail = ""
                    self._nState = X_ROOT_TAIL
                    self._chrPos += 1
                elif self._nState in (X_SPAN_TEXT, X_SPAN_SING):
                    self._xSing = ET.SubElement(self._xTail, TAG_BR)
                    self._xSing.tail = ""
                    self._nState = X_SPAN_SING
                    self._chrPos += 1
            elif c == "\t":
                if self._nState in (X_ROOT_TEXT, X_ROOT_TAIL):
                    self._xTail = ET.SubElement(self._xRoot, TAG_TAB)
                    self._xTail.tail = ""
                    self._nState = X_ROOT_TAIL
                    self._chrPos += 1
                elif self._nState in (X_SPAN_TEXT, X_SPAN_SING):
                    self._xSing = ET.SubElement(self._xTail, TAG_TAB)
                    self._xSing.tail = ""
                    self._chrPos += 1
                    self._nState = X_SPAN_SING
            else:
                if self._nState == X_ROOT_TEXT:
                    self._xRoot.text = (self._xRoot.text or "") + c
                    self._chrPos += 1
                elif self._nState == X_ROOT_TAIL:
                    self._xTail.tail = (self._xTail.tail or "") + c
                    self._chrPos += 1
                elif self._nState == X_SPAN_TEXT:
                    self._xTail.text = (self._xTail.text or "") + c
                    self._chrPos += 1
                elif self._nState == X_SPAN_SING:
                    self._xSing.tail = (self._xSing.tail or "") + c
                    self._chrPos += 1

        if nSpaces > 0:
            # Handle trailing spaces
            self._processSpaces(nSpaces)

    def appendSpan(self, text: str, style: str, link: str) -> None:
        """Append a text span to the XML element. The span is always
        closed since we do not produce nested spans (like Libre Office).
        Therefore we return to the root element level when we're done
        processing the text of the span.
        """
        if link:
            self._xTail = ET.SubElement(
                self._xRoot,
                _mkTag("text", "a"),
                attrib={
                    _mkTag("xlink", "type"): "simple",
                    _mkTag("xlink", "href"): link,
                    _mkTag("text", "style-name"): style,
                },
            )
        else:
            self._xTail = ET.SubElement(
                self._xRoot,
                TAG_SPAN,
                attrib={
                    _mkTag("text", "style-name"): style,
                },
            )
        self._xTail.text = ""  # Defaults to None
        self._xTail.tail = ""  # Defaults to None
        self._nState = X_SPAN_TEXT
        self.appendText(text)
        self._nState = X_ROOT_TAIL

    def appendNode(self, xNode: ET.Element | None) -> None:
        """Append an XML node to the paragraph. We only check for the
        X_ROOT_TEXT and X_ROOT_TAIL states. X_SPAN_TEXT is not possible
        at all, and X_SPAN_SING only happens internally in an appendSpan
        call, returning us to an X_ROOT_TAIL state.
        """
        if xNode is not None and self._nState in (X_ROOT_TEXT, X_ROOT_TAIL):
            self._xRoot.append(xNode)
            self._xTail = xNode
            self._xTail.tail = ""
            self._nState = X_ROOT_TAIL

    def checkError(self) -> tuple[int, str]:
        """Check that the number of characters written matches the
        number of characters received.
        """
        errMsg = ""
        nMissed = len(self._rawTxt) - self._chrPos
        if nMissed != 0:
            errMsg = f"{nMissed} char(s) were not written: '{self._rawTxt}'"
        return nMissed, errMsg

    ##
    #  Internal Functions
    ##

    def _processSpaces(self, nSpaces: int) -> None:
        """Add spaces to paragraph. The first space is always written
        as-is (unless it's the first character of the paragraph). The
        second space uses the dedicated tag for spaces, and from the
        third space and on, a counter is added to the tag.

        See: http://docs.oasis-open.org/office/v1.2/os/OpenDocument-v1.2-os-part1.html
        Sections: 6.1.2, 6.1.3, and 19.763
        """
        if nSpaces > 0:  # pragma: no branch
            if self._chrPos > 0:
                if self._nState == X_ROOT_TEXT:
                    self._xRoot.text = (self._xRoot.text or "") + " "
                    self._chrPos += 1
                elif self._nState == X_ROOT_TAIL:
                    self._xTail.tail = (self._xTail.tail or "") + " "
                    self._chrPos += 1
                elif self._nState == X_SPAN_TEXT:
                    self._xTail.text = (self._xTail.text or "") + " "
                    self._chrPos += 1
                elif self._nState == X_SPAN_SING:
                    self._xSing.tail = (self._xSing.tail or "") + " "
                    self._chrPos += 1
            else:
                nSpaces += 1

        if nSpaces == 2:
            if self._nState in (X_ROOT_TEXT, X_ROOT_TAIL):
                self._xTail = ET.SubElement(self._xRoot, TAG_SPC)
                self._xTail.tail = ""
                self._nState = X_ROOT_TAIL
                self._chrPos += nSpaces - 1
            elif self._nState in (X_SPAN_TEXT, X_SPAN_SING):
                self._xSing = ET.SubElement(self._xTail, TAG_SPC)
                self._xSing.tail = ""
                self._nState = X_SPAN_SING
                self._chrPos += nSpaces - 1

        elif nSpaces > 2:
            if self._nState in (X_ROOT_TEXT, X_ROOT_TAIL):
                self._xTail = ET.SubElement(self._xRoot, TAG_SPC, attrib={TAG_NSPC: str(nSpaces - 1)})
                self._xTail.tail = ""
                self._nState = X_ROOT_TAIL
                self._chrPos += nSpaces - 1
            elif self._nState in (X_SPAN_TEXT, X_SPAN_SING):
                self._xSing = ET.SubElement(self._xTail, TAG_SPC, attrib={TAG_NSPC: str(nSpaces - 1)})
                self._xSing.tail = ""
                self._nState = X_SPAN_SING
                self._chrPos += nSpaces - 1
