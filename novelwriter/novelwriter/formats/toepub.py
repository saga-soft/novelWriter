"""
novelWriter - EPUB Converter
============================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Final, NamedTuple
from zipfile import ZIP_DEFLATED, ZipFile

from novelwriter.common import xmlElement, xmlIndent, xmlSubElem
from novelwriter.constants import nwUnicode
from novelwriter.formats.shared import BlockTyp
from novelwriter.formats.tohtml import ToHtml
from novelwriter.formats.tokenizer import COMMENT_BLOCKS

if TYPE_CHECKING:
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

X_MIME = "application/epub+zip"

# Main XML NameSpaces
XML_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "xml": "http://www.w3.org/XML/1998/namespace",
}
for ns, uri in XML_NS.items():
    ET.register_namespace(ns, uri)


def _mkTag(ns: str, tag: str) -> str:
    """Assemble namespace and tag name."""
    if uri := XML_NS.get(ns, ""):
        return f"{{{uri}}}{tag}"
    logger.warning("Missing xml namespace '%s'", ns)
    return tag


class EPubType(Enum):
    """EPub Section Types."""

    COVER = 0
    FRONTMATTER = 1
    PART = 2
    CHAPTER = 3
    BACKMATTER = 4
    NOTES = 5


class ManifestEntry(NamedTuple):
    """EPub Manifest Entry."""

    id: str
    href: str
    mediaType: str
    properties: str | None = None


class ToEPub(ToHtml):
    """Core: EPub Writer.

    Extend the ToHtml class to write EPub output.
    """

    __slots__ = ("_isFront", "_nextFnIndex", "_section", "_sections")

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._section = EPubSection(EPubType.FRONTMATTER)
        self._sections = [self._section]
        self._isFront = True
        self._brTag = "<br />"
        self._nextFnIndex = 1
        self._useAnchors = False

    ##
    #  Setters
    ##

    def setReplaceUnicode(self, doReplace: bool) -> None:
        """Set translation map.

        Replace Unicode is ignored for EPub.
        """
        self._trMap = str.maketrans({"&": "&amp;"})

    ##
    #  Class Methods
    ##

    def doConvert(self) -> None:
        """Convert the list of text tokens into HTML."""
        for tType, tMeta, tText, tFmt, tStyle in self._blocks:
            tText, tFmt = self._processHtmlEntities(tText, tFmt)
            hStyle = self._genInlineStyles(tStyle)

            # Process Text Type
            if tType == BlockTyp.TEXT:
                self._section.text.append(f"<p{hStyle}>{self._formatText(tText, tFmt)}</p>")

            elif tType == BlockTyp.TITLE and self._isFront:
                tHead = tText.replace("\n", self._brTag)
                self._section.text.append(f"<h1{hStyle}>{tHead}</h1>")

            elif tType in (BlockTyp.TITLE, BlockTyp.PART):
                self._section = EPubSection(EPubType.PART if self._isNovel else EPubType.NOTES)
                self._sections.append(self._section)

                tHead = tText.replace("\n", self._brTag)
                self._section.setTitle(tHead, "H1")
                self._isFront = False

            elif tType == BlockTyp.HEAD1:
                tHead = tText.replace("\n", self._brTag)
                if self._isNovel:
                    self._section = EPubSection(EPubType.CHAPTER)
                    self._sections.append(self._section)
                    self._section.setTitle(tHead, "H1")
                    self._isFront = False
                else:
                    self._section.text.append(f"<h1{hStyle}>{tHead}</h1>")

            elif tType == BlockTyp.HEAD2:
                tHead = tText.replace("\n", self._brTag)
                self._section.text.append(f"<h2{hStyle}>{tHead}</h2>")

            elif tType == BlockTyp.HEAD3:
                tHead = tText.replace("\n", self._brTag)
                self._section.text.append(f"<h3{hStyle}>{tHead}</h3>")

            elif tType == BlockTyp.HEAD4:
                tHead = tText.replace("\n", self._brTag)
                self._section.text.append(f"<h4{hStyle}>{tHead}</h4>")

            elif tType == BlockTyp.SEP:
                self._section.text.append(f"<p class='sep'>{tText}</p>")

            elif tType == BlockTyp.HRULE:
                self._section.text.append(f"<hr{hStyle}/>")

            elif tType == BlockTyp.SKIP:
                self._section.text.append(f"<p{hStyle}>{nwUnicode.U_NBSP}</p>")

            elif tType in COMMENT_BLOCKS:
                self._section.text.append(f"<p class='comment'{hStyle}>{self._formatText(tText, tFmt)}</p>\n")

            elif tType == BlockTyp.KEYWORD:
                tClass = f"meta meta-{tMeta}"
                self._section.text.append(f"<p class='{tClass}'{hStyle}>{self._formatText(tText, tFmt)}</p>\n")

            else:  # pragma: no cover
                pass

    def closeDocument(self) -> None:
        """Run close document tasks."""
        # Generate section names and IDs, and prune empty ones
        counts = dict.fromkeys(EPubType, 0)
        sections = []
        for section in self._sections:
            if section.hasContent():
                eType = section.epubType
                counts[eType] += 1
                section.setSectionName(f"{eType.name.lower()}{counts[eType]}", len(sections) + 1)
                sections.append(section)
        self._sections = sections

    def saveDocument(self, path: Path) -> None:
        """Save the data to a .epub file."""
        # Replace fields if there are stats available
        if self._usedFields and self._counts:
            pages = len(self._sections)
            for doc, field in self._usedFields:
                if doc >= 0 and doc < pages and (value := self._counts.get(field)) is not None:
                    for i, text in enumerate(self._sections[doc].text):
                        self._sections[doc].text[i] = text.replace(f"{{{{{field}}}}}", self._formatInt(value))

        # Generate the XML files and save to a zip file
        xContainer = self._containerXml()
        xPackage = self._packageXml()
        xToc = self._tocXml()

        def xmlToZip(name: str, root: ET.Element, zipObj: ZipFile) -> None:
            xmlIndent(root)
            zipObj.writestr(name, ET.tostring(root, encoding="utf-8", xml_declaration=True))

        lang = self._dLocale.name()
        with ZipFile(path, mode="w", compression=ZIP_DEFLATED, compresslevel=3) as outZip:
            outZip.writestr("mimetype", X_MIME, compress_type=None, compresslevel=None)
            xmlToZip("META-INF/container.xml", xContainer, outZip)
            xmlToZip("OEBPS/package.opf", xPackage, outZip)
            xmlToZip("OEBPS/toc.ncx", xToc, outZip)
            outZip.writestr("OEBPS/nav.xhtml", self._generateNavPage())
            outZip.writestr("OEBPS/styles/stylesheet.css", self._generateStyleSheet())
            for section in self._sections:
                outZip.writestr(f"OEBPS/xhtml/{section.name}.xhtml", section.sectionToXHtml(lang))

    ##
    #  EPub Files
    ##

    def _containerXml(self) -> ET.Element:
        """Populate container.xml."""
        xRoot = xmlElement(
            "container",
            attrib={
                "xmlns": "urn:oasis:names:tc:opendocument:xmlns:container",
                "version": "1.0",
            },
        )
        xFiles = xmlSubElem(xRoot, "rootfiles")
        xmlSubElem(
            xFiles,
            "rootfile",
            attrib={
                "full-path": "OEBPS/package.opf",
                "media-type": "application/oebps-package+xml",
            },
        )
        return xRoot

    def _packageXml(self) -> ET.Element:
        """Populate package.opf."""
        xRoot = xmlElement(
            "package",
            attrib={
                "version": "3.0",
                _mkTag("xml", "lang"): self._dLocale.name(),
                "xmlns": "http://www.idpf.org/2007/opf",
                "unique-identifier": "uid",
            },
        )

        # Meta Data
        timeStamp = datetime.now(UTC).isoformat(sep="T", timespec="seconds")
        aPubID = {"refines": "#pub-id", "property": "identifier-type", "scheme": "xsd:string"}
        aCreator = {"refines": "#creator", "property": "role", "scheme": "marc:relators"}

        xMetaData = xmlSubElem(xRoot, "metadata")
        xmlSubElem(xMetaData, _mkTag("dc", "title"), self._project.data.name)
        xmlSubElem(xMetaData, _mkTag("dc", "creator"), self._project.data.author)
        xmlSubElem(xMetaData, _mkTag("dc", "publisher"), self._project.data.author)
        xmlSubElem(xMetaData, _mkTag("dc", "language"), self._dLocale.name())
        xmlSubElem(xMetaData, _mkTag("dc", "date"), timeStamp[:10])
        xmlSubElem(xMetaData, _mkTag("dc", "identifier"), f"urn:uuid:{self._project.data.uuid}", attrib={"id": "uid"})
        xmlSubElem(xMetaData, "meta", "uuid", attrib=aPubID)
        xmlSubElem(xMetaData, "meta", "aut", attrib=aCreator)
        xmlSubElem(xMetaData, "meta", timeStamp[:10], attrib={"property": "dcterms:date"})
        xmlSubElem(xMetaData, "meta", timeStamp, attrib={"property": "dcterms:modified"})
        xmlSubElem(xMetaData, "meta", self._project.data.author, attrib={"property": "dcterms:creator"})

        # Manifest
        manifest: list[ManifestEntry] = [
            ManifestEntry(id=section.sectionID, href=f"xhtml/{section.name}.xhtml", mediaType="application/xhtml+xml")
            for section in self._sections
        ]
        manifest.append(ManifestEntry(id="nav", href="nav.xhtml", mediaType="application/xhtml+xml", properties="nav"))
        manifest.append(ManifestEntry(id="css", href="styles/stylesheet.css", mediaType="text/css"))
        manifest.append(ManifestEntry(id="toc", href="toc.ncx", mediaType="application/x-dtbncx+xml"))

        xManifest = xmlSubElem(xRoot, "manifest")
        for entry in manifest:
            attrib = {
                "id": entry.id,
                "href": entry.href,
                "media-type": entry.mediaType,
            }
            if entry.properties:
                attrib["properties"] = entry.properties
            xmlSubElem(xManifest, "item", attrib=attrib)

        # Spine
        xSpine = xmlSubElem(xRoot, "spine", attrib={"toc": "toc"})
        for section in self._sections:
            xmlSubElem(xSpine, "itemref", attrib={"idref": section.sectionID})

        return xRoot

    def _tocXml(self) -> ET.Element:
        """Populate toc.ncx.

        See: https://en.wikipedia.org/wiki/EPUB#.ncx_file
        """
        xRoot = xmlElement(
            "ncx",
            attrib={
                "xmlns": "http://www.daisy.org/z3986/2005/ncx/",
                "version": "2005-1",
                _mkTag("xml", "lang"): self._dLocale.name(),
            },
        )

        uid = f"urn:uuid:{self._project.data.uuid}"
        xHead = xmlSubElem(xRoot, "head")
        xmlSubElem(xHead, "meta", attrib={"name": "dtb:uid", "content": uid})
        xmlSubElem(xHead, "meta", attrib={"name": "dtb:depth", "content": "1"})
        xmlSubElem(xHead, "meta", attrib={"name": "dtb:totalPageCount", "content": "0"})
        xmlSubElem(xHead, "meta", attrib={"name": "dtb:maxPageNumber", "content": "0"})

        xTitle = xmlSubElem(xRoot, "docTitle")
        xmlSubElem(xTitle, "text", self._project.data.name)
        xAuthor = xmlSubElem(xRoot, "docTitle")
        xmlSubElem(xAuthor, "text", self._project.data.author)

        xNavMap = xmlSubElem(xRoot, "navMap")
        playOrder = 0
        for section in self._sections:
            if (title := section.title) and section.epubType != EPubType.COVER:
                playOrder += 1
                xNavPoint = xmlSubElem(
                    xNavMap,
                    "navPoint",
                    attrib={
                        "class": "chapter",
                        "id": section.sectionID,
                        "playOrder": str(playOrder),
                    },
                )
                xLabel = xmlSubElem(xNavPoint, "navLabel")
                xmlSubElem(xLabel, "text", title)
                xmlSubElem(xNavPoint, "content", attrib={"src": f"xhtml/{section.name}.xhtml"})

        return xRoot

    def _generateNavPage(self) -> str:
        """Generate the content XHtml page."""
        langCode = self._dLocale.name()
        title = self._localLookup("Contents")

        xHtml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xHtml.append("<!DOCTYPE html>")
        xHtml.append(
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
            f'lang="{langCode}" xml:lang="{langCode}">'
        )
        xHtml.append("<head>")
        xHtml.append(f"<title>{title}</title>")
        xHtml.append('<meta http-equiv="default-style" content="text/html; charset=utf-8"/>')
        xHtml.append('<link rel="stylesheet" type="text/css" href="styles/stylesheet.css"/>')
        xHtml.append("</head>")
        xHtml.append("<body>")
        xHtml.append("<header>")
        xHtml.append(f'<h1 id="toc">{title}</h1>')
        xHtml.append("</header>")
        xHtml.append('<nav epub:type="toc" role="doc-toc" aria-labelledby="toc">')
        xHtml.append('<ol epub:type="list">')
        xHtml.extend(
            f'<li><a href="xhtml/{section.name}.xhtml#{section.sectionID}">{title}</a></li>'
            for section in self._sections
            if (title := section.title) and section.epubType != EPubType.COVER
        )
        xHtml.append("</ol>")
        xHtml.append("</nav>")
        xHtml.append("</body>")
        xHtml.append("</html>")
        return "\n".join(xHtml)

    def _generateStyleSheet(self) -> str:
        """Generate the book style sheet."""
        return "\n\n".join(
            self._cssBuilder(
                {
                    "a": {
                        "text-decoration": "underline",
                        "display": "inline",
                    },
                    "hr": {
                        "width": "50%",
                        "margin-left": "auto",
                        "margin-right": "auto",
                    },
                    ".sep": {
                        "text-align": "center",
                    },
                },
                compact=False,
            )
        )

    ##
    #  Internal Functions
    ##

    def _genFootnoteReferences(self, key: str) -> str:
        """Generate footnote references in the text."""
        index = self._nextFnIndex
        self._nextFnIndex += 1

        if content := self._footnotes.get(key):  # pragma: no branch
            text = self._formatText(*content)
            self._section.footnotes.append(
                f"<aside epub:type='footnote' id='fn_{index}'><p><a href='#fns_{index}'>{index}.</a> {text}</p></aside>"
            )

        return f"<sup><a epub:type='noteref' href='#fn_{index}' id='fns_{index}'>{index}</a></sup>"


class EPubSection:
    """A section of a book.

    This can be a chapter, partition, front matter, or back matter
    documents. New sections are generated each time a H1 header is
    encountered.

    See: https://www.w3.org/TR/epub-ssv/#sec-partitions
    """

    __slots__ = ("_class", "_footnotes", "_id", "_name", "_text", "_title", "_type")

    BODY_TYPE: Final[dict[EPubType, str]] = {
        EPubType.COVER: "cover",
        EPubType.FRONTMATTER: "frontmatter",
        EPubType.PART: "bodymatter",
        EPubType.CHAPTER: "bodymatter",
        EPubType.BACKMATTER: "backmatter",
        EPubType.NOTES: "bodymatter",
    }
    SECTION_TYPE: Final[dict[EPubType, tuple[str, str]]] = {
        EPubType.COVER: ("cover", ""),
        EPubType.FRONTMATTER: ("frontmatter", ""),
        EPubType.PART: ("part", " doc-part"),
        EPubType.CHAPTER: ("chapter", "doc-chapter"),
        EPubType.BACKMATTER: ("backmatter", ""),
        EPubType.NOTES: ("notes", " doc-chapter"),
    }

    def __init__(self, eType: EPubType) -> None:
        self._type = eType
        self._name = ""
        self._id = ""
        self._title = ""
        self._class = ""
        self._text: list[str] = []
        self._footnotes: list[str] = []

    @property
    def title(self) -> str:
        """Return the section title."""
        return self._title

    @property
    def text(self) -> list[str]:
        """Return the text buffer."""
        return self._text

    @property
    def footnotes(self) -> list[str]:
        """Return the footnotes buffer."""
        return self._footnotes

    @property
    def epubType(self) -> EPubType:
        """Return the epub:type of the section."""
        return self._type

    @property
    def name(self) -> str:
        """Return the name of the section."""
        return self._name

    @property
    def sectionID(self) -> str:
        """Return the section ID of the section."""
        return self._id

    ##
    #  Setters
    ##

    def setSectionName(self, name: str, sid: int) -> None:
        """Set the section name and number."""
        self._name = name
        self._id = f"sec_{sid}"

    def setTitle(self, title: str, cssClass: str) -> None:
        """Set the title. This is useful if the title isn't available
        when the section is created.
        """
        self._title = title
        self._class = cssClass

    ##
    #  Methods
    ##

    def hasContent(self) -> bool:
        """Return True if there is text."""
        return self._title != "" or len(self._text) > 0

    def sectionToXHtml(self, langCode: str) -> str:
        """Pack all content into an XHtml string."""
        eType, eRole = self.SECTION_TYPE.get(self._type, (None, None))
        sType = f' epub:type="{eType}"' if eType else ""
        sRole = f' role="{eRole}"' if eRole else ""
        hClass = f' class="{self._class}"' if self._class else ""
        xHtml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xHtml.append("<!DOCTYPE html>")
        xHtml.append(
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" '
            f'lang="{langCode}" xml:lang="{langCode}">'
        )
        xHtml.append("<head>")
        if self._title:
            xHtml.append(f"<title>{self._title}</title>")
        xHtml.append('<meta http-equiv="default-style" content="text/html; charset=utf-8"/>')
        xHtml.append('<link rel="stylesheet" type="text/css" href="../styles/stylesheet.css"/>')
        xHtml.append("</head>")
        xHtml.append(f'<body epub:type="{self.BODY_TYPE.get(self._type)}">')
        xHtml.append(f'<section{sType}{sRole} aria-labelledby="{self._id}">')
        if self._title:
            xHtml.append("<header>")
            xHtml.append(f'<h1{hClass} id="{self._id}">{self._title}</h1>')
            xHtml.append("</header>")
        xHtml.extend(self._text)
        xHtml.append("</section>")
        xHtml.extend(self._footnotes)
        xHtml.append("</body>")
        xHtml.append("</html>")
        return "\n".join(xHtml)
