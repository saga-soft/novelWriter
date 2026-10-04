"""
novelWriter - Project Document
==============================

This file is a part of novelWriter
Copyright (C) 2018 Veronica Berglyd Olsen and novelWriter contributors

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

import hashlib
import logging
import os

from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, TextIO

from novelwriter.common import formatTimeStamp, isHandle, safeExists, safeIsFile
from novelwriter.enum import nwItemClass, nwItemLayout
from novelwriter.error import formatException, logException
from novelwriter.formats.tomlparser import NTomlParser

if TYPE_CHECKING:
    from novelwriter.core.item import ProjectItem
    from novelwriter.core.project import NWProject
    from novelwriter.formats.tomlparser import T_TomlObject

logger = logging.getLogger(__name__)

MAX_META_LINES = 20


@dataclass
class DocumentMeta:
    """A dataclass representing the meta data of a document."""

    name: str = ""
    parent: str | None = None
    handle: str | None = None
    itemClass: nwItemClass = nwItemClass.NOVEL
    itemLayout: nwItemLayout = nwItemLayout.NOTE
    textHash: str = ""
    createdDate: str = "Unknown"
    updatedDate: str = "Unknown"


class ProjectDocument:
    """Core: Project Document Class.

    A Class wrapping a single novelWriter document file. It represents
    a project item of nwItemType FILE. The file is not guaranteed to
    exist, even if the item does. In the case it doesn't exist, reading
    it returns a None rather than an empty or non-empty string.
    """

    def __init__(self, project: NWProject, tHandle: str | None) -> None:

        self._project = project

        self._item = None  # The currently open item
        self._handle = None  # The handle of the currently open item
        self._fileLoc = None  # The file location of the currently open item
        self._meta = DocumentMeta()  # The meta data of the currently open item
        self._error = ""  # The latest encountered IO error

        self._lastHash = ""  # The last known SHA hash
        self._lastStat = None  # The (mtime_ns, size) of the file at last read/write
        self._hashError = False  # Hash mismatch on last write attempt

        if isHandle(tHandle):
            self._handle = tHandle

        if self._handle is not None:
            self._item = self._project.tree[tHandle]

    def __repr__(self) -> str:
        """Return a string representation of the document."""
        return f"<ProjectDocument handle={self._handle}>"

    def __bool__(self) -> bool:
        """Return True if the document has a valid handle and item."""
        return self._handle is not None and self._item is not None

    ##
    #  Properties
    ##

    @property
    def hashError(self) -> bool:
        """Check if the file hash has changed outside of novelWriter."""
        return self._hashError

    @property
    def fileLocation(self) -> str:
        """Return the file location of the current document."""
        return str(self._fileLoc)

    @property
    def meta(self) -> DocumentMeta:
        """Return the meta data of the current document."""
        return self._meta

    @property
    def error(self) -> str:
        """Return the last recorded error."""
        return self._error

    @property
    def createdDate(self) -> str:
        """Return the document creation date."""
        return self._meta.createdDate

    @property
    def updatedDate(self) -> str:
        """Return the document creation date."""
        return self._meta.updatedDate

    @property
    def nwItem(self) -> ProjectItem | None:
        """Return a pointer to the currently open ProjectItem."""
        return self._item

    ##
    #  Static Methods
    ##

    @staticmethod
    def quickReadText(content: Path, tHandle: str) -> str:
        """Return the text of a document in a fast and efficient way."""
        try:
            if (path := content / f"{tHandle}.md").is_file():
                with open(path, mode="r", encoding="utf-8") as inFile:
                    _, text = ProjectDocument._splitHeader(inFile)
                    return text
        except Exception:
            logger.error("Cannot read document with handle '%s'", tHandle)
            logException()
        return ""

    ##
    #  Methods
    ##

    def fileExists(self) -> bool:
        """Check if the document file exists."""
        if self._handle is None:
            return False

        contentPath = self._project.storage.contentPath
        if not isinstance(contentPath, Path):
            logger.error("No content path set")
            return False

        return safeIsFile(contentPath / f"{self._handle}.md")

    def readDocument(self, isOrphan: bool = False) -> str | None:
        """Read the document specified by the handle set in the
        constructor, capturing potential file system errors and parse
        meta data. If the document doesn't exist on disk, return an
        empty string. If something went wrong, return None.
        """
        self._error = ""
        if not isinstance(self._handle, str):
            logger.error("No document handle set")
            return None

        if self._item is None and not isOrphan:
            logger.error("Unknown novelWriter document")
            return None

        contentPath = self._project.storage.contentPath
        if not isinstance(contentPath, Path):
            logger.error("No content path set")
            return None

        docFile = f"{self._handle}.md"
        logger.debug("Opening document: %s", docFile)

        docPath = contentPath / docFile
        self._fileLoc = docPath

        text = ""
        self._meta = DocumentMeta()
        self._lastHash = ""
        self._lastStat = None

        if safeExists(docPath):
            try:
                with open(docPath, mode="r", encoding="utf-8") as inFile:
                    metaLines, text = self._splitHeader(inFile)
                    if metaLines:
                        parser = NTomlParser(flat=True)
                        parser.readString("".join(metaLines))
                        self._applyMeta(parser)

                    # Record the file's stat so future saves can check for
                    # external changes without a full re-read and hash
                    stat = os.fstat(inFile.fileno())
                    self._lastStat = (stat.st_mtime_ns, stat.st_size)

            except Exception as exc:
                self._error = formatException(exc)
                return None

        else:
            # The document file does not exist, so we assume it's a new
            # document and return an empty text string.
            logger.debug("The requested document does not exist")

        self._lastHash = hashlib.sha1(text.encode()).hexdigest()

        return text

    def writeDocument(self, text: str, forceWrite: bool = False) -> bool:
        """Write the document specified by the handle attribute. Handle
        any IO errors in the process  Returns True if successful, False
        if not.
        """
        self._error = ""
        if not isinstance(self._handle, str):
            logger.error("No document handle set")
            return False

        contentPath = self._project.storage.contentPath
        if not isinstance(contentPath, Path):
            logger.error("No content path set")
            return False

        docFile = f"{self._handle}.md"
        logger.debug("Saving document: %s", docFile)

        docPath = contentPath / docFile
        docTemp = docPath.with_suffix(".tmp")

        # Check if the document has changed on disk
        prevHash = self._lastHash
        if prevHash:
            try:
                stat = docPath.stat()
                statSig = (stat.st_mtime_ns, stat.st_size)
            except OSError:
                statSig = None

            if statSig != self._lastStat:
                # Verify by checking the hash
                self.readDocument()
                if self._lastHash != prevHash and not forceWrite:
                    logger.error("File has been altered on disk since opened")
                    self._hashError = True
                    return False

        if text and not text.endswith("\n"):
            text += "\n"

        currTime = formatTimeStamp(time())
        writeHash = hashlib.sha1(text.encode(encoding="utf-8")).hexdigest()
        createdDate = self._meta.createdDate
        updatedDate = self._meta.updatedDate
        if writeHash != self._lastHash:
            updatedDate = currTime
        if not safeIsFile(docPath):
            createdDate = currTime
            updatedDate = currTime

        # DocMeta Header
        docMeta = ""
        if self._item:
            meta: T_TomlObject = {
                "name": self._item.itemName,
                "parent": self._item.itemParent or "",
                "handle": self._item.itemHandle or "",
                "class": self._item.itemClass.name,
                "layout": self._item.itemLayout.name,
                "textHash": writeHash,
                "createdDate": createdDate,
                "updatedDate": updatedDate,
            }
            toml = NTomlParser(flat=True).writeString(meta).strip()
            docMeta = f"+++\n{toml}\n+++\n"

        try:
            with open(docTemp, mode="w", encoding="utf-8") as outFile:
                outFile.write(docMeta)
                outFile.write(text)
        except Exception as exc:
            self._error = formatException(exc)
            return False

        # If we're here, the file was successfully saved, so we can
        # replace the temp file with the actual file
        try:
            docTemp.replace(docPath)
        except OSError as exc:
            self._error = formatException(exc)
            return False

        self._lastHash = writeHash
        self._meta.textHash = writeHash
        self._meta.createdDate = createdDate
        self._meta.updatedDate = updatedDate
        try:
            stat = docPath.stat()
            self._lastStat = (stat.st_mtime_ns, stat.st_size)
        except OSError:
            self._lastStat = None
        self._hashError = False

        return True

    def deleteDocument(self) -> bool:
        """Permanently delete a document source file and related files
        from the project data folder.
        """
        self._error = ""
        if not isinstance(self._handle, str):
            logger.error("No document handle set")
            return False

        contentPath = self._project.storage.contentPath
        if not isinstance(contentPath, Path):
            logger.error("No content path set")
            return False

        docPath = contentPath / f"{self._handle}.md"
        docTemp = docPath.with_suffix(".tmp")

        try:
            docPath.unlink(missing_ok=True)
            docTemp.unlink(missing_ok=True)
        except Exception as exc:
            self._error = formatException(exc)
            return False

        return True

    ##
    #  Internal Functions
    ##

    def _applyMeta(self, parser: NTomlParser) -> None:
        """Populate the document meta data from a parsed TOML header."""
        parent = parser.getStr(None, "parent", "")
        handle = parser.getStr(None, "handle", "")

        self._meta = DocumentMeta(
            name=parser.getStr(None, "name", ""),
            parent=parent if isHandle(parent) else None,
            handle=handle if isHandle(handle) else None,
            itemClass=parser.getEnum(None, "class", nwItemClass.NOVEL),
            itemLayout=parser.getEnum(None, "layout", nwItemLayout.NOTE),
            textHash=parser.getStr(None, "textHash", ""),
            createdDate=parser.getStr(None, "createdDate", "Unknown"),
            updatedDate=parser.getStr(None, "updatedDate", "Unknown"),
        )

    @staticmethod
    def _splitHeader(stream: TextIO) -> tuple[list[str], str]:
        """Split an open document file into TOML header and text."""
        first = stream.readline()
        if first.strip() == "+++":
            meta = []
            for _ in range(MAX_META_LINES):
                line = stream.readline()
                if not line:
                    break
                if line.strip() == "+++":
                    return meta, stream.read()
                meta.append(line)
            stream.seek(0)
            return [], stream.read()
        return [], first + stream.read()
