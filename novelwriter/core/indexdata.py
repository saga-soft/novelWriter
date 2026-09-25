"""
novelWriter - Project Index Data
================================

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

from typing import TYPE_CHECKING, Literal

from novelwriter import CONFIG
from novelwriter.common import checkInt, compact, isListInstance, isTitleTag
from novelwriter.constants import nwKeyWords, nwStyles

if TYPE_CHECKING:
    from collections.abc import ItemsView, Sequence

    from novelwriter.core.index import IndexCache
    from novelwriter.core.item import ProjectItem
    from novelwriter.enum import nwComment

logger = logging.getLogger(__name__)

T_NoteTypes = Literal["footnotes", "comments"]
T_IndexHeadRefs = dict[str, list[str]]

TT_NONE = "T0000"  # Default title key
NOTE_TYPES: list[T_NoteTypes] = ["footnotes", "comments"]


class IndexNode:
    """Core: Single Index Item Node Class.

    This object represents the index data of a project item.
    It holds a record of all the headings in the text, and the meta data
    associated with each heading. It also holds a pointer to the project
    item. The main heading level of the item is also held here since it
    must be reset each time the item is re-indexed.
    """

    __slots__ = ("_cache", "_count", "_handle", "_headings", "_item", "_notes")

    def __init__(self, cache: IndexCache, tHandle: str, nwItem: ProjectItem) -> None:
        self._cache = cache
        self._handle = tHandle
        self._item = nwItem
        self._headings: dict[str, IndexHeading] = {TT_NONE: IndexHeading(self._cache, TT_NONE)}
        self._notes: dict[str, set[str]] = {}
        self._count = 0

    def __repr__(self) -> str:
        """Return a string representation of the index node."""
        return f"<IndexNode handle='{self._handle}'>"

    def __len__(self) -> int:
        """Return the number of headings in the index node."""
        return len(self._headings)

    def __getitem__(self, sTitle: str) -> IndexHeading | None:
        """Return the IndexHeading for the given title."""
        return self._headings.get(sTitle, None)

    def __contains__(self, sTitle: str) -> bool:
        """Return True if the given title is in the index node."""
        return sTitle in self._headings

    ##
    # Properties
    ##

    @property
    def handle(self) -> str:
        """Return the item handle of the index item."""
        return self._handle

    @property
    def item(self) -> ProjectItem:
        """Return the project item of the index item."""
        return self._item

    ##
    #  Setters
    ##

    def addHeading(self, tHeading: IndexHeading) -> None:
        """Add a heading to the item. Also remove the placeholder entry
        if it exists.
        """
        if TT_NONE in self._headings:
            self._headings.pop(TT_NONE)
        self._headings[tHeading.key] = tHeading

    def setHeadingCounts(self, sTitle: str, cCount: int, wCount: int, pCount: int) -> None:
        """Set the character, word and paragraph count of a heading."""
        if sTitle in self._headings:
            self._headings[sTitle].setCounts([cCount, wCount, pCount])

    def setHeadingComment(self, sTitle: str, comment: nwComment, key: str, text: str) -> None:
        """Set the comment text of a heading."""
        if sTitle in self._headings:
            self._headings[sTitle].setComment(comment.name, key, text)

    def setHeadingTag(self, sTitle: str, tag: str) -> None:
        """Set the tag of a heading."""
        if sTitle in self._headings:
            self._headings[sTitle].setTag(tag)

    def addHeadingRef(self, sTitle: str, tags: list[str], keyword: str) -> None:
        """Add a reference key and all its types to a heading."""
        if sTitle in self._headings:
            for tag in tags:
                self._headings[sTitle].addReference(tag, keyword)

    def addNoteKey(self, style: T_NoteTypes, key: str) -> None:
        """Add a note key to the index."""
        if style not in self._notes:
            self._notes[style] = set()
        self._notes[style].add(key)

    ##
    #  Data Methods
    ##

    def items(self) -> ItemsView[str, IndexHeading]:
        """Return IndexHeading items."""
        return self._headings.items()

    def headings(self) -> list[str]:
        """Return heading keys in sorted order."""
        return sorted(self._headings.keys())

    def allTags(self) -> list[str]:
        """Return a list of all tags in the current item."""
        return [h.tag for h in self._headings.values() if h.tag]

    def nextHeading(self) -> str:
        """Return the next heading key to be used."""
        self._count += 1
        return f"T{self._count:04d}"

    def noteKeys(self, style: T_NoteTypes) -> set[str]:
        """Return a set of all note keys."""
        return self._notes.get(style, set())

    ##
    #  Pack/Unpack
    ##

    def packData(self) -> dict:
        """Pack the indexed item's data into a dictionary."""
        data = {}
        for sTitle, hItem in self._headings.items():
            data[sTitle] = hItem.packData()
        if self._notes:
            data["document"] = {style: list(keys) for style, keys in self._notes.items()}
        return data

    def unpackData(self, data: dict) -> None:
        """Unpack an item entry from the data."""
        for key, entry in data.items():
            if isTitleTag(key):
                heading = IndexHeading(self._cache, key)
                heading.unpackData(entry)
                self.addHeading(heading)
            elif key == "document":
                for style, keys in entry.items():
                    if style not in NOTE_TYPES:
                        raise ValueError("The notes style is invalid")
                    if not isListInstance(keys, str):
                        raise ValueError("The notes keys must be a list of strings")
                    self._notes[style] = set(keys)
            else:
                raise KeyError("Index node contains an invalid key")


class IndexHeading:
    """Core: Single Index Heading Class.

    This object represents a section of text in a project item
    associated with a single (valid) heading. It holds a separate record
    of all references made under the heading.
    """

    __slots__ = ("_cache", "_comments", "_counts", "_key", "_level", "_line", "_refs", "_tag", "_title")

    def __init__(self, cache: IndexCache, key: str, line: int = 0, level: str = "H0", title: str = "") -> None:
        self._cache = cache
        self._key = key
        self._line = line
        self._level = level
        self._title = title
        self._counts: tuple[int, int, int] = (0, 0, 0)
        self._tag = ""
        self._refs: dict[str, set[str]] = {}
        self._comments: dict[str, str] = {}

    def __repr__(self) -> str:
        """Return a string representation of the index heading."""
        return f"<IndexHeading key='{self._key}'>"

    ##
    #  Properties
    ##

    @property
    def key(self) -> str:
        return self._key

    @property
    def line(self) -> int:
        return self._line

    @property
    def level(self) -> str:
        return self._level

    @property
    def title(self) -> str:
        return self._title

    @property
    def mainCount(self) -> int:
        return self._counts[0 if CONFIG.useCharCount else 1]

    @property
    def charCount(self) -> int:
        return self._counts[0]

    @property
    def wordCount(self) -> int:
        return self._counts[1]

    @property
    def paraCount(self) -> int:
        return self._counts[2]

    @property
    def synopsis(self) -> str:
        return self._comments.get("summary", "")

    @property
    def comments(self) -> dict[str, str]:
        return self._comments

    @property
    def tag(self) -> str:
        return self._tag

    @property
    def references(self) -> dict[str, set[str]]:
        return self._refs

    ##
    #  Setters
    ##

    def setLevel(self, level: str) -> None:
        """Set the level of the heading if it's a valid value."""
        if level in nwStyles.H_VALID:
            self._level = level

    def setLine(self, line: int) -> None:
        """Set the line number of a heading."""
        self._line = max(0, checkInt(line, 0))

    def setCounts(self, counts: Sequence[int]) -> None:
        """Set the character, word and paragraph count. Make sure the
        value is an integer and is not smaller than 0.
        """
        if len(counts) == 3:
            self._counts = (
                max(0, checkInt(counts[0], 0)),
                max(0, checkInt(counts[1], 0)),
                max(0, checkInt(counts[2], 0)),
            )

    def setComment(self, comment: str, key: str, text: str) -> None:
        """Set the text for a comment and make sure it is a string."""
        match comment.lower():
            case "short" | "synopsis" | "summary":
                self._appendCommentText("summary", text)
            case "story" if key:
                self._cache.story.add(key)
                self._appendCommentText(f"story.{key}", text)
            case "note" if key:
                self._cache.note.add(key)
                self._appendCommentText(f"note.{key}", text)

    def setTag(self, tag: str) -> None:
        """Set the tag for references, and make sure it is a string."""
        self._tag = str(tag).lower()

    def addReference(self, tag: str, keyword: str) -> None:
        """Add a record of a reference tag, and what keyword types it is
        associated with.
        """
        if keyword in nwKeyWords.VALID_KEYS:
            tag = tag.lower()
            if tag not in self._refs:
                self._refs[tag] = set()
            self._refs[tag].add(keyword)

    ##
    #  Getters
    ##

    def getReferences(self) -> T_IndexHeadRefs:
        """Extract all tags and references for this heading."""
        refs = {x: [] for x in nwKeyWords.VALID_KEYS}
        for tag, types in self._refs.items():
            for keyword in types:
                if keyword in refs and (name := self._cache.tags.tagName(tag)):
                    refs[keyword].append(name)
            if name := self._cache.tags.tagName(self._tag):
                refs[nwKeyWords.TAG_KEY] = [name]
        return refs

    def getReferencesByKeyword(self, keyword: str) -> list[str]:
        """Extract all references for this heading."""
        refs = []
        if keyword == nwKeyWords.TAG_KEY:
            if name := self._cache.tags.tagName(self._tag):
                refs.append(name)
        else:
            for tag, types in self._refs.items():
                if keyword in types and (name := self._cache.tags.tagName(tag)):
                    refs.append(name)
        return refs

    ##
    #  Data Methods
    ##

    def packData(self) -> dict:
        """Pack the values into a dictionary for saving to cache."""
        data = {}
        data["meta"] = {
            "level": self._level,
            "title": self._title,
            "line": self._line,
            "tag": self._tag,
            "counts": self._counts,
        }
        if self._refs:
            data["refs"] = {k: ",".join(sorted(v)) for k, v in self._refs.items()}
        if self._comments:
            data.update(self._comments)
        return data

    def unpackData(self, data: dict) -> None:
        """Unpack a heading entry from a dictionary."""
        self._comments = {}  # These are accumulative and should be reset here
        for key, entry in data.items():
            if key == "meta":
                self.setLevel(entry.get("level", "H0"))
                self._title = str(entry.get("title", ""))
                self._tag = str(entry.get("tag", ""))
                self.setLine(entry.get("line", 0))
                self.setCounts(entry.get("counts", [0, 0, 0]))
            elif key == "refs":
                for tag, value in entry.items():
                    if not isinstance(tag, str):
                        raise ValueError("Heading reference key must be a string")
                    if not isinstance(value, str):
                        raise ValueError("Heading reference value must be a string")
                    for keyword in value.split(","):
                        if keyword in nwKeyWords.VALID_KEYS:
                            self.addReference(tag, keyword)
                        else:
                            raise ValueError("Heading reference contains an invalid keyword")
            elif key == "summary" or key.startswith(("story", "note")):
                comment, _, kind = str(key).partition(".")
                self.setComment(comment, compact(kind), str(entry))
            else:
                raise KeyError("Unknown key in heading entry")

    ##
    #  Internal Functions
    ##

    def _appendCommentText(self, key: str, text: str) -> None:
        """Append text to a comment."""
        if current := self._comments.get(key):
            text = f"{current:s}\n\n{text:s}"
        self._comments[key] = str(text)
