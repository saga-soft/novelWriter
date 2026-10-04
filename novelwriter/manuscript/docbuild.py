"""
novelWriter - Manuscript Document Builder
=========================================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtGui import QFont

from novelwriter import CONFIG
from novelwriter.constants import nwLabels
from novelwriter.core.item import ProjectItem
from novelwriter.enum import nwBuildFmt, nwComment
from novelwriter.error import formatException, logException
from novelwriter.formats.todocx import ToDocX
from novelwriter.formats.toepub import ToEPub
from novelwriter.formats.tohtml import ToHtml
from novelwriter.formats.tomarkdown import ToMarkdown
from novelwriter.formats.toodt import ToOdt
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.formats.toraw import ToRaw

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from novelwriter.core.project import NWProject
    from novelwriter.formats.tokenizer import Tokenizer
    from novelwriter.manuscript.buildsettings import BuildSettings

logger = logging.getLogger(__name__)


class DocumentBuilder:
    """Manuscript: Manuscript Document Build Class.

    This is the core tool that assembles a project and outputs a
    manuscript, based on a build definition object (BuildSettings).
    """

    __slots__ = (
        "_build",
        "_cache",
        "_count",
        "_error",
        "_outline",
        "_project",
        "_queue",
    )

    def __init__(self, project: NWProject, build: BuildSettings) -> None:
        self._project = project
        self._build = build
        self._queue = []
        self._error = None
        self._cache = None
        self._count = False
        self._outline = False

    ##
    #  Properties
    ##

    @property
    def error(self) -> str | None:
        """Return the last error, if any."""
        return self._error

    @property
    def lastBuild(self) -> Tokenizer | None:
        """Return the build object of the last build process, if any.
        This is useful for accessing build details and data after the
        build job is completed.
        """
        return self._cache

    ##
    #  Special Methods
    ##

    def __len__(self) -> int:
        """Return the length of the build queue."""
        return len(self._queue)

    ##
    #  Methods
    ##

    def addDocument(self, tHandle: str) -> None:
        """Add a document to the build queue manually."""
        self._queue.append(tHandle)

    def queueAll(self) -> None:
        """Queue all document as defined by the build settings."""
        self._queue = []
        withRoots = self._build.getBool("text.addNoteHeadings")
        filtered = self._build.buildItemFilter(self._project, withRoots=withRoots)
        for item in self._project.tree:
            if filtered.get(item.itemHandle, (False, 0))[0]:
                self._queue.append(item.itemHandle)

    def iterBuildPreview(self, newPage: bool) -> Iterable[tuple[int, bool]]:
        """Build a preview QTextDocument."""
        makeObj = ToQTextDocument(self._project)
        filtered = self._setupBuild(makeObj)
        makeObj.initDocument()
        makeObj.setShowNewPage(newPage)
        self._outline = True
        yield from self._iterBuild(makeObj, filtered)
        makeObj.closeDocument()
        self._error = None
        self._cache = makeObj
        return

    def iterBuildDocument(self, path: Path, bFormat: nwBuildFmt) -> Iterable[tuple[int, bool]]:
        """Select a builder based on format."""
        self._error = None
        self._cache = None

        if bFormat in (nwBuildFmt.J_HTML, nwBuildFmt.J_NWD):
            # Ensure that JSON output has the correct extension
            path = path.with_suffix(".json")

        if bFormat in (nwBuildFmt.ODT, nwBuildFmt.FODT):
            makeObj = ToOdt(self._project, bFormat == nwBuildFmt.FODT)
            filtered = self._setupBuild(makeObj)
            makeObj.initDocument()
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()

        elif bFormat in (nwBuildFmt.HTML, nwBuildFmt.J_HTML):
            makeObj = ToHtml(self._project)
            filtered = self._setupBuild(makeObj)
            makeObj.initDocument()
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()
            if not self._build.getBool("html.preserveTabs"):
                makeObj.replaceTabs()

        elif bFormat in (nwBuildFmt.STD_MD, nwBuildFmt.EXT_MD):
            makeObj = ToMarkdown(self._project, bFormat == nwBuildFmt.EXT_MD)
            filtered = self._setupBuild(makeObj)
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()
            if self._build.getBool("format.replaceTabs"):
                makeObj.replaceTabs(nSpaces=4, spaceChar=" ")

        elif bFormat in (nwBuildFmt.NWD, nwBuildFmt.J_NWD):
            makeObj = ToRaw(self._project)
            filtered = self._setupBuild(makeObj)
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()
            if self._build.getBool("format.replaceTabs"):
                makeObj.replaceTabs(nSpaces=4, spaceChar=" ")

        elif bFormat == nwBuildFmt.DOCX:
            makeObj = ToDocX(self._project)
            filtered = self._setupBuild(makeObj)
            makeObj.initDocument()
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()

        elif bFormat == nwBuildFmt.EPUB:
            makeObj = ToEPub(self._project)
            filtered = self._setupBuild(makeObj)
            makeObj.initDocument()
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()

        elif bFormat == nwBuildFmt.PDF:
            makeObj = ToQTextDocument(self._project, pdf=True)
            makeObj.setAnchorsEnabled(False)
            filtered = self._setupBuild(makeObj)
            makeObj.initDocument()
            yield from self._iterBuild(makeObj, filtered)
            makeObj.closeDocument()

        else:
            logger.error("Unsupported document format")
            return

        self._error = None
        self._cache = makeObj

        try:
            makeObj.saveDocument(path)
        except Exception as exc:
            logException()
            self._error = formatException(exc)

        return

    ##
    #  Internal Functions
    ##

    def _iterBuild(self, makeObj: Tokenizer, filtered: dict) -> Iterable[tuple[int, bool]]:
        """Iterate over buildable documents."""
        self._count = True
        for i, tHandle in enumerate(self._queue):
            self._error = None
            if filtered.get(tHandle, (False, 0))[0]:
                yield i, self._doBuild(makeObj, tHandle)
            else:
                yield i, False
        return

    def _setupBuild(self, bldObj: Tokenizer) -> dict:
        """Configure the build object."""
        # Get Settings
        textFont = QFont(CONFIG.textFont)
        textFont.fromString(self._build.getStr("format.textFont"))

        bldObj.setTextFont(textFont)
        bldObj.setLanguage(self._build.getStr("doc.metaLanguage") or self._project.data.language)

        bldObj.setPartitionFormat(
            self._build.getStr("headings.fmtPart"),
            self._build.getBool("headings.hidePart"),
        )
        bldObj.setChapterFormat(
            self._build.getStr("headings.fmtChapter"),
            self._build.getBool("headings.hideChapter"),
        )
        bldObj.setUnNumberedFormat(
            self._build.getStr("headings.fmtUnnumbered"),
            self._build.getBool("headings.hideUnnumbered"),
        )
        bldObj.setSceneFormat(
            self._build.getStr("headings.fmtScene"),
            self._build.getBool("headings.hideScene"),
        )
        bldObj.setHardSceneFormat(
            self._build.getStr("headings.fmtAltScene"),
            self._build.getBool("headings.hideAltScene"),
        )
        bldObj.setSectionFormat(
            self._build.getStr("headings.fmtSection"),
            self._build.getBool("headings.hideSection"),
        )
        bldObj.setTitleStyle(
            self._build.getBool("headings.centerTitle"),
            self._build.getBool("headings.breakTitle"),
        )
        bldObj.setPartitionStyle(
            self._build.getBool("headings.centerPart"),
            self._build.getBool("headings.breakPart"),
        )
        bldObj.setChapterStyle(
            self._build.getBool("headings.centerChapter"),
            self._build.getBool("headings.breakChapter"),
        )
        bldObj.setSceneStyle(
            self._build.getBool("headings.centerScene"),
            self._build.getBool("headings.breakScene"),
        )

        bldObj.setJustify(
            self._build.getBool("format.justifyText"),
            self._build.getBool("format.justifyOnBreak"),
        )
        bldObj.setLineHeight(self._build.getFloat("format.lineHeight"))
        bldObj.setKeepLineBreaks(self._build.getBool("format.keepBreaks"))
        bldObj.setDialogHighlight(self._build.getBool("format.showDialogue"))
        bldObj.setFirstLineIndent(
            self._build.getBool("format.firstLineIndent"),
            self._build.getFloat("format.firstIndentWidth"),
            self._build.getBool("format.indentFirstPar"),
        )
        bldObj.setHeadingStyles(
            self._build.getBool("format.colorHeadings"),
            self._build.getBool("format.boldHeadings"),
            self._build.getBool("format.upperHeadings"),
        )

        bldObj.setTitleProperties(
            self._build.getFloat("format.titleMarginT"),
            self._build.getFloat("format.titleMarginB"),
            self._build.getFloat("format.titleSize"),
        )
        bldObj.setHead1Properties(
            self._build.getFloat("format.h1MarginT"),
            self._build.getFloat("format.h1MarginB"),
            self._build.getFloat("format.h1Size"),
        )
        bldObj.setHead2Properties(
            self._build.getFloat("format.h2MarginT"),
            self._build.getFloat("format.h2MarginB"),
            self._build.getFloat("format.h2Size"),
        )
        bldObj.setHead3Properties(
            self._build.getFloat("format.h3MarginT"),
            self._build.getFloat("format.h3MarginB"),
            self._build.getFloat("format.h3Size"),
        )
        bldObj.setHead4Properties(
            self._build.getFloat("format.h4MarginT"),
            self._build.getFloat("format.h4MarginB"),
            self._build.getFloat("format.h4Size"),
        )
        bldObj.setTextProperties(
            self._build.getFloat("format.textMarginT"),
            self._build.getFloat("format.textMarginB"),
        )
        bldObj.setSeparatorProperties(
            self._build.getFloat("format.sepMarginT"),
            self._build.getFloat("format.sepMarginB"),
        )

        bldObj.setBodyText(self._build.getBool("text.includeBodyText"))
        bldObj.setKeywords(self._build.getBool("text.includeKeywords"))
        bldObj.setIgnoredKeywords(self._build.getStr("text.ignoredKeywords"))
        bldObj.setCommentType(nwComment.PLAIN, self._build.getBool("text.includeComments"))
        bldObj.setCommentType(nwComment.SYNOPSIS, self._build.getBool("text.includeSynopsis"))
        bldObj.setCommentType(nwComment.SHORT, self._build.getBool("text.includeSynopsis"))
        bldObj.setCommentType(nwComment.STORY, self._build.getBool("text.includeStory"))
        bldObj.setCommentType(nwComment.NOTE, self._build.getBool("text.includeNotes"))

        if isinstance(bldObj, ToHtml):
            bldObj.setStyles(self._build.getBool("html.addStyles"))
            bldObj.setReplaceUnicode(self._build.getBool("format.stripUnicode"))

        if isinstance(bldObj, ToOdt | ToDocX):
            bldObj.setHeaderFormat(
                self._build.getStr("doc.pageHeader"),
                self._build.getInt("doc.pageCountOffset"),
            )

        if isinstance(bldObj, ToOdt | ToDocX | ToQTextDocument):
            scale = nwLabels.UNIT_SCALE.get(self._build.getStr("format.pageUnit"), 1.0)
            pW, pH = nwLabels.PAPER_SIZE.get(self._build.getStr("format.pageSize"), (-1.0, -1.0))
            bldObj.setPageLayout(
                pW if pW > 0.0 else scale * self._build.getFloat("format.pageWidth"),
                pH if pH > 0.0 else scale * self._build.getFloat("format.pageHeight"),
                scale * self._build.getFloat("format.topMargin"),
                scale * self._build.getFloat("format.bottomMargin"),
                scale * self._build.getFloat("format.leftMargin"),
                scale * self._build.getFloat("format.rightMargin"),
            )
            bldObj.setLineForMargin(self._build.getBool("format.lineForMargin"))

        return self._build.buildItemFilter(self._project, withRoots=self._build.getBool("text.addNoteHeadings"))

    def _doBuild(self, bldObj: Tokenizer, tHandle: str, convert: bool = True) -> bool:
        """Build a single document and add it to the build object."""
        tItem = self._project.tree[tHandle]
        if isinstance(tItem, ProjectItem):
            try:
                if tItem.isRootType():
                    if tItem.isNovelLike():
                        bldObj.setBreakNext()
                    else:
                        bldObj.addRootHeading(tHandle)
                        if convert:
                            bldObj.doConvert()
                        if self._count:
                            bldObj.countStats()
                        if self._outline:
                            bldObj.buildOutline()
                elif tItem.isFileType():
                    bldObj.setText(tHandle)
                    bldObj.doPreProcessing()
                    bldObj.tokenizeText()
                    if self._count:
                        bldObj.countStats()
                    if self._outline:
                        bldObj.buildOutline()
                    if convert:
                        bldObj.doConvert()

            except Exception:
                self._error = f"Build: Failed to build '{tHandle}'"
                logger.error(self._error)
                return False

        return True
