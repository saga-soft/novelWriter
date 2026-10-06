"""
novelWriter - QTextDocument Converter
=====================================

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QMarginsF, QSizeF
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPageLayout,
    QPageSize,
    QTextBlockFormat,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFrameFormat,
    QTextLength,
    QTextTableCellFormat,
    QTextTableFormat,
)
from PyQt6.QtPrintSupport import QPrinter

from novelwriter import __version__
from novelwriter.constants import nwUnicode
from novelwriter.formats.shared import BlockFmt, BlockTyp, T_Formats, TextFmt, stripEscape
from novelwriter.formats.tokenizer import HEADING_BLOCKS, META_BLOCKS, Tokenizer
from novelwriter.types import (
    QtAlignAbsolute,
    QtAlignCenter,
    QtAlignJustify,
    QtAlignLeft,
    QtAlignRight,
    QtFontBold,
    QtFontNormal,
    QtKeepAnchor,
    QtMoveAnchor,
    QtMoveEnd,
    QtPageBreakAfter,
    QtPageBreakAuto,
    QtPageBreakBefore,
    QtPropLineHeight,
    QtTransparent,
    QtVAlignNormal,
    QtVAlignSub,
    QtVAlignSuper,
)

if TYPE_CHECKING:
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

T_TextStyle = tuple[QTextBlockFormat, QTextCharFormat]


def newBlock(cursor: QTextCursor, bFmt: QTextBlockFormat) -> None:
    """Insert a new block if not at the beginning of the document."""
    if cursor.position() > 0:
        cursor.insertBlock(bFmt)
    else:
        cursor.setBlockFormat(bFmt)


class ToQTextDocument(Tokenizer):
    """Core: QTextDocument Writer.

    Extend the Tokenizer class to generate a QTextDocument output. This
    is intended for usage in the document viewer and build tool preview.
    """

    __slots__ = (
        "_blockFmt",
        "_charFmt",
        "_dItalic",
        "_dStrike",
        "_dUnderline",
        "_dWeight",
        "_document",
        "_fHead",
        "_fixedHeadings",
        "_hWeight",
        "_iHead",
        "_init",
        "_mHead",
        "_mIndent",
        "_mMeta",
        "_mSep",
        "_mText",
        "_newPage",
        "_pageMargins",
        "_pageSize",
        "_printer",
        "_sHead",
        "_tIndent",
        "_usedFields",
        "_usedNotes",
    )

    def __init__(self, project: NWProject, pdf: bool = False) -> None:
        super().__init__(project)
        self._document = QTextDocument()
        self._document.setUndoRedoEnabled(False)
        self._document.setDocumentMargin(0.0)

        self._printer = None
        if pdf:
            self._printer = QPrinter(QPrinter.PrinterMode.PrinterResolution)
            self._printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            self._printer.setDocName(project.data.name)
            self._printer.setCreator(f"novelWriter/{__version__}")

        self._usedNotes: dict[str, int] = {}
        self._usedFields: list[tuple[int, str]] = []

        self._init = False
        self._newPage = False

        self._hWeight = QtFontBold
        self._dWeight = QtFontNormal
        self._dItalic = False
        self._dStrike = False
        self._dUnderline = False

        self._pageSize = QPageSize(QPageSize.PageSizeId.A4)
        self._pageMargins = QMarginsF(20.0, 20.0, 20.0, 20.0)
        self._fixedHeadings = False

        self._mHead: dict[BlockTyp, tuple[float, float]] = {}
        self._sHead: dict[BlockTyp, float] = {}
        self._fHead: dict[BlockTyp, int] = {}
        self._iHead: dict[BlockTyp, int] = {}
        self._mText: tuple[float, float] = (1.0, 1.0)
        self._mMeta: tuple[float, float] = (1.0, 1.0)
        self._mSep: tuple[float, float] = (1.0, 1.0)
        self._mIndent = 1.0
        self._tIndent = 1.0
        self._blockFmt = QTextBlockFormat()
        self._charFmt = QTextCharFormat()

    ##
    #  Properties
    ##

    @property
    def document(self) -> QTextDocument:
        """Return the document."""
        return self._document

    ##
    #  Setters
    ##

    def setPageLayout(self, width: float, height: float, top: float, bottom: float, left: float, right: float) -> None:
        """Set the document page size and margins in millimetres."""
        self._pageSize = QPageSize(QSizeF(width, height), QPageSize.Unit.Millimeter)
        self._pageMargins = QMarginsF(left, top, right, bottom)

    def setShowNewPage(self, state: bool) -> None:
        """Add markers for page breaks."""
        self._newPage = state

    def setFixedHeadings(self, state: bool) -> None:
        """Use fixed heading sizes rather than scaling with the text font."""
        self._fixedHeadings = state

    ##
    #  Class Methods
    ##

    def initDocument(self) -> None:
        """Initialise all computed values of the document."""
        super().initDocument()

        self._document.setUndoRedoEnabled(False)
        self._document.blockSignals(True)
        self._document.clear()

        # Set Up PDF Printing
        # The hinting preference solves an issue with kerning on Windows, and
        # setting the paint device ensures the document is rendered at print
        # resolution. See issues #2100 and #2637.
        dpi = 96.0
        if self._printer:
            dpi = 72.0
            self._printer.setPageSize(self._pageSize)
            self._printer.setPageMargins(self._pageMargins, QPageLayout.Unit.Millimeter)
            self._textFont.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            self._document.setPageSize(self._printer.pageRect(QPrinter.Unit.DevicePixel).size())
            if layout := self._document.documentLayout():  # pragma: no branch
                layout.setPaintDevice(self._printer)

        self._document.setDefaultFont(self._textFont)

        # Default Styles
        self._dWeight = self._textFont.weight()
        self._dItalic = self._textFont.italic()
        self._dStrike = self._textFont.strikeOut()
        self._dUnderline = self._textFont.underline()

        # Header Weight
        self._hWeight = QtFontBold if self._boldHeads else self._dWeight

        # Scaled Sizes
        fPt = self._textFont.pointSizeF()
        fPx = fPt * 96.0 / 72.0  # 1 em in pixels
        mPx = fPx * dpi / 96.0

        self._mHead = {
            BlockTyp.TITLE: (fPx * self._marginTitle[0], fPx * self._marginTitle[1]),
            BlockTyp.PART: (fPx * self._marginTitle[0], fPx * self._marginTitle[1]),
            BlockTyp.HEAD1: (fPx * self._marginHead1[0], fPx * self._marginHead1[1]),
            BlockTyp.HEAD2: (fPx * self._marginHead2[0], fPx * self._marginHead2[1]),
            BlockTyp.HEAD3: (fPx * self._marginHead3[0], fPx * self._marginHead3[1]),
            BlockTyp.HEAD4: (fPx * self._marginHead4[0], fPx * self._marginHead4[1]),
        }

        self._sHead = {
            BlockTyp.TITLE: fPt * self._sizeTitle,
            BlockTyp.PART: fPt * self._sizeTitle,
            BlockTyp.HEAD1: fPt * self._sizeHead1,
            BlockTyp.HEAD2: fPt * self._sizeHead2,
            BlockTyp.HEAD3: fPt * self._sizeHead3,
            BlockTyp.HEAD4: fPt * self._sizeHead4,
        }
        self._fHead = {
            BlockTyp.TITLE: 4,
            BlockTyp.PART: 4,
            BlockTyp.HEAD1: 4,
            BlockTyp.HEAD2: 3,
            BlockTyp.HEAD3: 2,
            BlockTyp.HEAD4: 1,
        }
        self._iHead = {
            BlockTyp.TITLE: 0,
            BlockTyp.PART: 1,
            BlockTyp.HEAD1: 1,
            BlockTyp.HEAD2: 2,
            BlockTyp.HEAD3: 3,
            BlockTyp.HEAD4: 4,
        }

        self._mText = (fPx * self._marginText[0], fPx * self._marginText[1])
        self._mMeta = (fPx * self._marginMeta[0], fPx * self._marginMeta[1])
        self._mSep = (fPx * self._marginSep[0], fPx * self._marginSep[1])

        self._mIndent = mPx * 2.0
        self._tIndent = mPx * self._firstWidth

        # Text Formats
        self._blockFmt.setTopMargin(self._mText[0])
        self._blockFmt.setBottomMargin(self._mText[1])
        self._blockFmt.setAlignment(QtAlignAbsolute)
        self._blockFmt.setLineHeight(100.0 * self._lineHeight, QtPropLineHeight)

        self._charFmt.setBackground(QtTransparent)
        self._charFmt.setForeground(self._theme.text)

        self._init = True

    def doConvert(self) -> None:
        """Write text tokens into the document."""
        if not self._init:
            return

        self._document.blockSignals(self._printer is None)
        cursor = QTextCursor(self._document)
        cursor.movePosition(QtMoveEnd)

        for tType, tMeta, tText, tFormat, tStyle in self._blocks:
            bFmt = QTextBlockFormat(self._blockFmt)
            if tType in META_BLOCKS:
                bFmt.setTopMargin(self._mMeta[0])
                bFmt.setBottomMargin(self._mMeta[1])
            elif tType == BlockTyp.SEP:
                bFmt.setTopMargin(self._mSep[0])
                bFmt.setBottomMargin(self._mSep[1])

            if tStyle & BlockFmt.LEFT:
                bFmt.setAlignment(QtAlignLeft)
            elif tStyle & BlockFmt.RIGHT:
                bFmt.setAlignment(QtAlignRight)
            elif tStyle & BlockFmt.CENTRE:
                bFmt.setAlignment(QtAlignCenter)
            elif tStyle & BlockFmt.JUSTIFY:
                bFmt.setAlignment(QtAlignJustify)

            if tStyle & BlockFmt.PBB:
                self._insertNewPageMarker(cursor)
                bFmt.setPageBreakPolicy(QtPageBreakBefore)
            if tStyle & BlockFmt.PBA:
                bFmt.setPageBreakPolicy(QtPageBreakAfter)

            if tStyle & BlockFmt.Z_BTM:
                bFmt.setBottomMargin(0.0)
            if tStyle & BlockFmt.Z_TOP:
                bFmt.setTopMargin(0.0)

            if tStyle & BlockFmt.IND_L:
                bFmt.setLeftMargin(self._mIndent)
            if tStyle & BlockFmt.IND_R:
                bFmt.setRightMargin(self._mIndent)
            if tStyle & BlockFmt.IND_T:
                bFmt.setTextIndent(self._tIndent)

            if tType == BlockTyp.TEXT:
                newBlock(cursor, bFmt)
                self._insertFragments(tText, tFormat, cursor, self._charFmt)

            elif tType in HEADING_BLOCKS:
                bFmt, cFmt = self._genHeadStyle(tType, tMeta, bFmt)
                for tPart in tText.split("\n"):
                    newBlock(cursor, bFmt)
                    cursor.insertText(tPart, cFmt)
                    bFmt.setPageBreakPolicy(QtPageBreakAuto)

            elif tType in META_BLOCKS:
                newBlock(cursor, bFmt)
                self._insertFragments(tText, tFormat, cursor, self._charFmt)

            elif tType == BlockTyp.SEP:
                newBlock(cursor, bFmt)
                cursor.insertText(tText, self._charFmt)

            elif tType == BlockTyp.HRULE:
                self._insertHorizontalRule(cursor)

            elif tType == BlockTyp.SKIP:
                newBlock(cursor, bFmt)
                cursor.insertText(nwUnicode.U_NBSP, self._charFmt)

            else:  # pragma: no cover
                pass

            if tStyle & BlockFmt.PBA:
                self._insertNewPageMarker(cursor)

        self._document.blockSignals(False)

        return

    def saveDocument(self, path: Path) -> None:
        """Save the document as a PDF file."""
        if self._printer:  # pragma: no branch
            logger.info("Writing PDF ...")
            self._printer.setOutputFileName(str(path))
            self._document.print(self._printer)
            logger.info("Wrote %d pages at %d DPI", self._document.pageCount(), self._printer.resolution())

    def closeDocument(self) -> None:
        """Run close document tasks."""
        self._document.blockSignals(True)

        # Replace fields if there are stats available
        if self._usedFields and self._counts:
            cursor = QTextCursor(self._document)
            for pos, field in reversed(self._usedFields):
                if (value := self._counts.get(field)) is not None:
                    cursor.setPosition(pos, QtMoveAnchor)
                    cursor.setPosition(pos + 1, QtKeepAnchor)
                    cursor.insertText(self._formatInt(value))

        # Add footnotes
        if self._usedNotes:
            cursor = QTextCursor(self._document)
            cursor.movePosition(QtMoveEnd)

            bFmt, cFmt = self._genHeadStyle(BlockTyp.HEAD4, "", self._blockFmt)
            newBlock(cursor, bFmt)
            cursor.insertText(self._localLookup("Footnotes"), cFmt)

            for key, index in self._usedNotes.items():
                if content := self._footnotes.get(key):  # pragma: no branch
                    cFmt = QTextCharFormat(self._charFmt)
                    cFmt.setForeground(self._theme.code)
                    cFmt.setAnchor(True)
                    cFmt.setAnchorNames([f"footnote_{index}"])
                    newBlock(cursor, self._blockFmt)
                    cursor.insertText(f"{index}. ", cFmt)
                    self._insertFragments(*content, cursor, self._charFmt)

        self._document.blockSignals(False)

    ##
    #  Internal Functions
    ##

    def _insertFragments(self, text: str, tFmt: T_Formats, cursor: QTextCursor, dFmt: QTextCharFormat) -> None:
        """Apply formatting tags to text."""
        cFmt = QTextCharFormat(dFmt)
        temp = text.replace("\n", nwUnicode.U_LSEP)
        start = 0
        primary: QColor | None = None
        for pos, fmt, data in tFmt:
            # Insert buffer with previous format
            cursor.insertText(stripEscape(temp[start:pos]), cFmt)

            # Construct next format
            if fmt == TextFmt.B_B:
                cFmt.setFontWeight(QtFontBold)
            elif fmt == TextFmt.B_E:
                cFmt.setFontWeight(self._dWeight)
            elif fmt == TextFmt.I_B:
                cFmt.setFontItalic(True)
            elif fmt == TextFmt.I_E:
                cFmt.setFontItalic(self._dItalic)
            elif fmt == TextFmt.D_B:
                cFmt.setFontStrikeOut(True)
            elif fmt == TextFmt.D_E:
                cFmt.setFontStrikeOut(self._dStrike)
            elif fmt == TextFmt.U_B:
                cFmt.setFontUnderline(True)
            elif fmt == TextFmt.U_E:
                cFmt.setFontUnderline(self._dUnderline)
            elif fmt == TextFmt.M_B:
                cFmt.setBackground(self._theme.highlight)
            elif fmt == TextFmt.M_E:
                cFmt.setBackground(QtTransparent)
            elif fmt == TextFmt.SUP_B:
                cFmt.setVerticalAlignment(QtVAlignSuper)
            elif fmt == TextFmt.SUP_E:
                cFmt.setVerticalAlignment(QtVAlignNormal)
            elif fmt == TextFmt.SUB_B:
                cFmt.setVerticalAlignment(QtVAlignSub)
            elif fmt == TextFmt.SUB_E:
                cFmt.setVerticalAlignment(QtVAlignNormal)
            elif fmt == TextFmt.COL_B:
                if color := self._classes.get(data):  # pragma: no branch
                    cFmt.setForeground(color)
                    primary = color
            elif fmt == TextFmt.COL_E:
                cFmt.setForeground(self._theme.text)
                primary = None
            elif fmt == TextFmt.ANM_B:
                cFmt.setAnchor(True)
                cFmt.setAnchorNames([data])
            elif fmt == TextFmt.ANM_E:
                cFmt.setAnchor(False)
            elif fmt == TextFmt.ARF_B:
                cFmt.setFontUnderline(True)
                cFmt.setAnchor(True)
                cFmt.setAnchorHref(data)
            elif fmt == TextFmt.ARF_E:
                cFmt.setFontUnderline(False)
                cFmt.setAnchor(False)
                cFmt.setAnchorHref("")
            elif fmt == TextFmt.HRF_B:
                cFmt.setForeground(self._theme.link)
                cFmt.setFontUnderline(True)
                cFmt.setAnchor(True)
                cFmt.setAnchorHref(data)
            elif fmt == TextFmt.HRF_E:
                cFmt.setForeground(primary or self._theme.text)
                cFmt.setFontUnderline(self._dUnderline)
                cFmt.setAnchor(False)
                cFmt.setAnchorHref("")
            elif fmt == TextFmt.FNOTE:
                xFmt = QTextCharFormat(self._charFmt)
                xFmt.setForeground(self._theme.code)
                xFmt.setVerticalAlignment(QtVAlignSuper)
                if data in self._footnotes:
                    index = len(self._usedNotes) + 1
                    self._usedNotes[data] = index
                    xFmt.setAnchor(True)
                    xFmt.setAnchorHref(f"#footnote_{index}")
                    xFmt.setFontUnderline(True)
                    cursor.insertText(f"[{index}]", xFmt)
                else:
                    cursor.insertText("[ERR]", cFmt)
            elif fmt == TextFmt.FIELD and (field := data.partition(":")[2]):
                self._usedFields.append((cursor.position(), field))
                cursor.insertText("0", cFmt)

            # Move pos for next pass
            start = pos

        # Insert whatever is left in the buffer
        cursor.insertText(stripEscape(temp[start:]), cFmt)

    def _insertNewPageMarker(self, cursor: QTextCursor) -> None:
        """Insert a new page marker as a dashed line."""
        if self._newPage:
            tFmt = QTextTableFormat()
            tFmt.setBorder(0.0)
            tFmt.setBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_None)
            tFmt.setCellPadding(0.0)
            tFmt.setCellSpacing(0.0)
            tFmt.setTopMargin(self._mSep[0])
            tFmt.setBottomMargin(self._mSep[1])
            tFmt.setWidth(QTextLength(QTextLength.Type.PercentageLength, 100.0))

            cFmt = QTextTableCellFormat()
            cFmt.setBottomBorder(1.0)
            cFmt.setBottomBorderStyle(QTextFrameFormat.BorderStyle.BorderStyle_Dashed)
            cFmt.setBottomBorderBrush(QBrush(self._theme.text))

            if table := cursor.insertTable(1, 1, tFmt):  # pragma: no branch
                table.cellAt(0, 0).setFormat(cFmt)
            if root := self._document.rootFrame():  # pragma: no branch
                cursor.swap(root.lastCursorPosition())

    def _insertHorizontalRule(self, cursor: QTextCursor) -> None:
        """Insert a horizontal rule marker."""
        bFmt = QTextBlockFormat(self._blockFmt)
        bFmt.setAlignment(QtAlignCenter)
        bFmt.setTopMargin(self._mSep[0])
        bFmt.setBottomMargin(self._mSep[1])
        bFmt.setLineHeight(100.0, QtPropLineHeight)
        bFmt.setProperty(
            QTextBlockFormat.Property.BlockTrailingHorizontalRulerWidth,
            QTextLength(QTextLength.Type.PercentageLength, 50.0),
        )
        bFmt.setProperty(QTextBlockFormat.Property.BackgroundBrush, QBrush(self._theme.text))

        newBlock(cursor, bFmt)

    def _genHeadStyle(self, hType: BlockTyp, hKey: str, rFmt: QTextBlockFormat) -> T_TextStyle:
        """Generate a heading style set."""
        mTop, mBottom = self._mHead.get(hType, (0.0, 0.0))

        bFmt = QTextBlockFormat(rFmt)
        bFmt.setTopMargin(mTop)
        bFmt.setBottomMargin(mBottom)
        bFmt.setHeadingLevel(self._iHead.get(hType, 0))

        hCol = self._colorHeads and hType != BlockTyp.TITLE
        cFmt = QTextCharFormat(self._charFmt)
        cFmt.setForeground(self._theme.head if hCol else self._theme.text)
        cFmt.setFontWeight(self._hWeight)
        if self._fixedHeadings:
            cFmt.setProperty(QTextCharFormat.Property.FontSizeAdjustment, self._fHead.get(hType, 0))
        else:
            cFmt.setFontPointSize(self._sHead.get(hType, 1.0))
        if hKey and self._useAnchors:
            cFmt.setAnchorNames([hKey])
            cFmt.setAnchor(True)

        return bFmt, cFmt
