"""
novelWriter - Project Search Tool
=================================

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
import re

from typing import TYPE_CHECKING

from novelwriter import SHARED
from novelwriter.constants import nwConst

if TYPE_CHECKING:
    from collections.abc import Iterable

    from novelwriter.core.item import ProjectItem
    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

T_SearchResults = list[tuple[int, int, str, int]]


class DocSearch:
    """Tool: Search Documents.

    A global document search class.
    """

    __slots__ = (
        "_docsInactive",
        "_docsNotes",
        "_docsNovel",
        "_escape",
        "_fullText",
        "_opts",
        "_regEx",
        "_skipRoots",
        "_textBody",
        "_textComments",
        "_textHeadings",
        "_textMeta",
        "_words",
    )

    def __init__(self) -> None:
        self._regEx = re.compile(r"")
        self._opts = re.IGNORECASE
        self._words = False
        self._escape = True

        # Filters
        self._docsNovel = True
        self._docsNotes = True
        self._docsInactive = True
        self._skipRoots: list[str] = []
        self._textHeadings = True
        self._textMeta = True
        self._textComments = True
        self._textBody = True
        self._fullText = True

    ##
    #  Setters
    ##

    def setCaseSensitive(self, state: bool) -> None:
        """Set the case sensitive search flag."""
        self._opts = 0 if state else re.IGNORECASE

    def setWholeWords(self, state: bool) -> None:
        """Set the whole words search flag."""
        self._words = state

    def setUserRegEx(self, state: bool) -> None:
        """Set the escape flag to the opposite state."""
        self._escape = not state

    def setDocumentFilters(self, novel: bool, notes: bool, inactive: bool) -> None:
        """Set the document type filters."""
        self._docsNovel = novel
        self._docsNotes = notes
        self._docsInactive = inactive

    def setSkipRoots(self, roots: list[str]) -> None:
        """Set the list of root handles to skip during the search."""
        self._skipRoots = roots

    def setContentFilters(self, headings: bool, meta: bool, comments: bool, body: bool) -> None:
        """Set the content type filters."""
        self._textHeadings = headings
        self._textMeta = meta
        self._textComments = comments
        self._textBody = body
        self._fullText = headings and meta and comments and body

    ##
    #  Methods
    ##

    def iterSearch(self, project: NWProject, search: str) -> Iterable[tuple[ProjectItem, T_SearchResults, bool]]:
        """Iterate through documents in a project and apply search."""
        self._regEx = re.compile(self._buildPattern(search), self._opts)
        logger.debug("Searching with pattern '%s'", self._regEx.pattern)
        storage = project.storage
        SHARED.initMainProgress(len(project.tree))
        for item in project.tree:
            SHARED.incMainProgress()
            if (
                item.isFileType()
                and item.itemRoot not in self._skipRoots
                and ((self._docsNovel and item.isDocumentLayout()) or (self._docsNotes and item.isNoteLayout()))
                and (item.isActive or (self._docsInactive and not item.isActive))
            ):
                results, capped = self.searchText(storage.getDocumentText(item.itemHandle))
                yield item, results, capped
        SHARED.clearMainProgress()
        return

    def searchText(self, text: str) -> tuple[T_SearchResults, bool]:
        """Search a piece of text for RegEx matches."""
        result = []
        prev = -1

        if not self._fullText:
            filtered = []
            for line in text.splitlines(keepends=True):
                if line.strip():
                    overwrite = 0
                    temp = line.rstrip("\n")
                    if line[0] == "#":
                        overwrite = 0 if self._textHeadings else len(temp)
                    elif line[0] == "@":
                        overwrite = 0 if self._textMeta else len(temp)
                    elif line[0] == "%":
                        overwrite = 0 if self._textComments else len(temp)
                    else:
                        overwrite = 0 if self._textBody else len(temp)
                    filtered.append((" " * overwrite) + line[overwrite:])
                else:
                    filtered.append(line)

            text = "".join(filtered)

        for res in self._regEx.finditer(text):
            pos = res.start(0)
            num = len(res.group(0))
            end = pos + num

            # Ignore zero length matches at the same position as the previous match
            if num == 0 and pos == prev:
                continue
            prev = end

            sBr = text.rfind("\n", 0, pos) + 1
            eBr = text.find("\n", end)
            eBr = eBr if eBr != -1 else len(text)

            left = max(sBr, pos - 20)
            if left > sBr and (space := text.find(" ", left, pos)) != -1:
                left = space + 1

            # Cap the context at 100 characters in total
            right = min(eBr, end + 80, left + 100)
            if right < eBr and (space := text.rfind(" ", end, right)) != -1:
                right = space

            if context := text[left:right]:
                result.append((pos, num, context, pos - left))
                if len(result) >= nwConst.MAX_SEARCH_RESULT:
                    return result, True

        return result, False

    ##
    #  Internal Functions
    ##

    def _buildPattern(self, search: str) -> str:
        """Build the search pattern string."""
        if self._escape:
            search = re.escape(search)
        if self._words:
            search = f"(?:^|\\b){search}(?:$|\\b)"
        return search
