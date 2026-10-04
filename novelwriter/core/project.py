"""
novelWriter - Project Wrapper
=============================

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

import json
import logging

from enum import Enum
from functools import partial
from pathlib import Path
from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QCoreApplication

from novelwriter import CONFIG, SHARED, __hexversion__, __version__
from novelwriter.common import (
    checkStringNone,
    formatInt,
    formatTimeStamp,
    getFileSize,
    hexToInt,
    makeFileNameSafe,
    minmax,
    safeIsFile,
)
from novelwriter.constants import nwLabels, trConst
from novelwriter.core.index import Index
from novelwriter.core.options import OptionState
from novelwriter.core.projectdata import ProjectData
from novelwriter.core.projectxml import ProjectXMLReader, ProjectXMLWriter, XMLReadState
from novelwriter.core.sessions import SessionLog
from novelwriter.core.storage import ProjectStorage, ProjectStorageOpen
from novelwriter.core.tree import ProjectTree
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType
from novelwriter.error import logException

if TYPE_CHECKING:
    from novelwriter.core.status import T_StatusKind, T_UpdateEntry

logger = logging.getLogger(__name__)


class NWProjectState(Enum):
    """The state of the loaded project."""

    UNKNOWN = 0
    LOCKED = 1
    RECOVERY = 2
    READY = 3


class NWProject:
    """Core: novelWriter Project Class.

    This class is the parent class of the project, and holds instances
    of project data, the project tree, and the project index.
    """

    __slots__ = (
        "_changed",
        "_countsDirty",
        "_data",
        "_index",
        "_langData",
        "_options",
        "_session",
        "_state",
        "_storage",
        "_tree",
        "_valid",
        "tr",
    )

    def __init__(self) -> None:

        # Core Elements
        self._options = OptionState(self)  # Project-specific GUI options
        self._storage = ProjectStorage(self)  # The project storage handler
        self._data = ProjectData(self)  # The project settings
        self._tree = ProjectTree(self)  # The project tree
        self._index = Index(self)  # The project index
        self._session = SessionLog(self)  # The session record

        # Project Status
        self._langData = {}  # Localisation data
        self._changed = False  # The project has unsaved changes
        self._valid = False  # The project was successfully loaded
        self._state = NWProjectState.UNKNOWN
        self._countsDirty = False  # The word counts need to be recalculated

        # Internal Mapping
        self.tr = partial(QCoreApplication.translate, "NWProject")

        logger.debug("Ready: NWProject")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: NWProject")

    def clear(self) -> None:
        """Clear the project."""
        self._tree.clear()
        self._index.clear()

    ##
    #  Properties
    ##

    @property
    def options(self) -> OptionState:
        return self._options

    @property
    def storage(self) -> ProjectStorage:
        return self._storage

    @property
    def data(self) -> ProjectData:
        return self._data

    @property
    def tree(self) -> ProjectTree:
        return self._tree

    @property
    def index(self) -> Index:
        return self._index

    @property
    def session(self) -> SessionLog:
        return self._session

    @property
    def projOpened(self) -> float:
        return self._session.start

    @property
    def projChanged(self) -> bool:
        return self._changed

    @property
    def isValid(self) -> bool:
        """Return True if a project is loaded."""
        return self._valid

    @property
    def state(self) -> NWProjectState:
        """Return the current project state."""
        return self._state

    @property
    def lockStatus(self) -> list | None:
        """Return the project lock information."""
        return self._storage.lockStatus

    @property
    def currentTotalCount(self) -> int:
        """Return the current total word count from the tree."""
        return self._tree.model.root.count

    @property
    def countsDirty(self) -> bool:
        """Return whether the word counts need to be recalculated."""
        return self._countsDirty

    ##
    #  Item Methods
    ##

    def newRoot(self, itemClass: nwItemClass, pos: int = -1) -> str:
        """Add a new root folder to the project. If label is not set,
        use the class label.
        """
        label = trConst(nwLabels.CLASS_NAME[itemClass])
        return self._tree.create(label, None, nwItemType.ROOT, itemClass=itemClass, pos=pos)

    def newFolder(self, label: str, parent: str, pos: int = -1) -> str | None:
        """Add a new folder with a given label and parent item."""
        return self._tree.create(label, parent, nwItemType.FOLDER, pos=pos)

    def newFile(self, label: str, parent: str, pos: int = -1) -> str | None:
        """Add a new file with a given label and parent item."""
        return self._tree.create(label, parent, nwItemType.FILE, pos=pos)

    def removeItem(self, tHandle: str) -> bool:
        """Remove an item from the project. This will delete both the
        project entry and a document file if it exists.
        """
        if self._tree.checkType(tHandle, nwItemType.FILE):
            SHARED.closeDocument(tHandle)
            doc = self._storage.getDocument(tHandle)
            if not doc.deleteDocument():
                SHARED.error(self.tr("Could not delete document file."), info=doc.error)
                return False
        self._index.deleteHandle(tHandle)
        self._tree.remove(tHandle)
        return True

    def writeNewFile(
        self,
        tHandle: str,
        hLevel: int,
        isDocument: bool,
        text: str = "",
        *,
        addHeading: bool = True,
    ) -> bool:
        """Write content to a new document after it is created. This
        will not run if the file exists and is not empty.
        """
        if not ((tItem := self._tree[tHandle]) and tItem.isFileType()):
            return False

        if self._storage.getDocumentText(tHandle).strip():
            return False

        if addHeading:
            indent = "#" * minmax(hLevel, 1, 4)
            text = f"{indent} {tItem.itemName}\n\n{text}"

        if tItem.isNovelLike() and isDocument:
            tItem.setLayout(nwItemLayout.DOCUMENT)
        else:
            tItem.setLayout(nwItemLayout.NOTE)

        self._storage.getDocument(tHandle).writeDocument(text)
        self._index.scanText(tHandle, text)

        return True

    def copyFileContent(self, tHandle: str, sHandle: str, newTitle: str | None = None) -> bool:
        """Copy content to a new document after it is created. This
        will not run if the file exists and is not empty.
        """
        if not ((tItem := self._tree[tHandle]) and tItem.isFileType()):
            return False

        if not ((sItem := self._tree[sHandle]) and sItem.isFileType()):
            return False

        if self._storage.getDocumentText(tHandle).strip():
            return False

        logger.debug("Populating '%s' with text from '%s'", tHandle, sHandle)
        text = self._storage.getDocumentText(sHandle)
        if (
            newTitle
            and (lines := text.split("\n"))
            and lines
            and lines[0].startswith(("# ", "## ", "### ", "#### ", "#! ", "##! ", "###! "))
        ):
            prefix, _, _ = lines[0].partition(" ")
            lines[0] = f"{prefix} {newTitle}"
            text = "\n".join(lines)

        self._storage.getDocument(tHandle).writeDocument(text)
        sItem.setLayout(tItem.itemLayout)
        self._index.reIndexHandle(tHandle)

        return True

    def createNewNote(self, tag: str, itemClass: nwItemClass) -> None:
        """Create a new note. This function is used by the document
        editor to create note files for unknown tags.
        """
        if itemClass != nwItemClass.NO_CLASS:
            if not (rHandle := self._tree.findRoot(itemClass)):
                rHandle = self.newRoot(itemClass)
            if rHandle and (tHandle := self.newFile(tag.title(), rHandle)):
                self.writeNewFile(tHandle, 1, False, f"@tag: {tag}\n\n")
                self._tree.refreshItems([tHandle])

    ##
    #  Project Methods
    ##

    def openProject(self, projPath: str | Path, clearLock: bool = False) -> bool:
        """Open the project file provided. If it doesn't exist, assume
        it is a folder and look for the file within it. If successful,
        parse the XML of the file and populate the project variables and
        build the tree of project items.
        """
        logger.info("Opening project: %s", projPath)

        status = self._storage.initProjectStorage(projPath, clearLock)
        if status != ProjectStorageOpen.READY:
            if status == ProjectStorageOpen.UNKOWN:
                SHARED.error(
                    self.tr("Not a known project file format."),
                    info=self.tr("Path: {0}").format(str(projPath)),
                )
            elif status == ProjectStorageOpen.NOT_FOUND:
                SHARED.error(
                    self.tr("Project file not found."),
                    info=self.tr("Path: {0}").format(str(projPath)),
                )
            elif status == ProjectStorageOpen.FAILED:
                SHARED.error(
                    self.tr("Failed to open project."),
                    info=self.tr("Path: {0}").format(str(projPath)),
                    exc=self._storage.exc,
                )
            elif status == ProjectStorageOpen.LOCKED:
                self._state = NWProjectState.LOCKED
            else:  # pragma: no cover
                pass
            return False

        # Read Project XML
        # ================

        xmlReader = self._storage.getXmlReader()
        if not isinstance(xmlReader, ProjectXMLReader):
            return False

        self._data = ProjectData(self)
        projContent = []
        xmlParsed = xmlReader.read(self._data, projContent)
        appVersion = xmlReader.appVersion or self.tr("Unknown")
        if not xmlParsed:
            if xmlReader.state == XMLReadState.NOT_NWX_FILE:
                SHARED.error(self.tr("Project file does not appear to be a novelWriterXML file."))
            elif xmlReader.state == XMLReadState.UNKNOWN_VERSION:
                SHARED.error(
                    self.tr(
                        "Unknown or unsupported novelWriter project file format. "
                        "The project cannot be opened by this version of novelWriter. "
                        "The file was saved with novelWriter version {0}."
                    ).format(appVersion)
                )
            else:
                SHARED.error(self.tr("Failed to parse project xml."))
            return False

        # Check Legacy Upgrade
        # ====================

        if (xmlReader.state == XMLReadState.WAS_LEGACY or self._storage.hasBreakingChanges()) and not SHARED.question(
            self.tr(
                "The file format of your project is about to be updated. "
                "If you proceed, older versions of novelWriter will no "
                "longer be able to open this project. Continue?"
            )
        ):
            return False

        # Check novelWriter Version
        # =========================

        if xmlReader.hexVersion > hexToInt(__hexversion__) and not SHARED.question(
            self.tr(
                "This project was saved by a newer version of "
                "novelWriter, version {0}. This is version {1}. If you "
                "continue to open the project, some attributes and "
                "settings may not be preserved, but the overall project "
                "should be fine. Continue opening the project?"
            ).format(appVersion, __version__),
            warn=True,
        ):
            return False

        # Post XML Loading
        self._storage.runPostXMLTasks()

        # Extract Data
        # ============

        self._tree.unpack(projContent)
        self._options.loadSettings()
        self._loadProjectLocalisation()

        # Update recent projects
        if storePath := self._storage.storagePath:
            CONFIG.recentProjects.update(storePath, self._data, time())

        # Check the project tree consistency
        # This also handles any orphaned files found
        orphans, recovered = self._tree.checkConsistency(self.tr("Recovered"))
        if orphans > 0:
            SHARED.warn(
                self.tr("Found {0} orphaned file(s) in the project. {1} file(s) were recovered.").format(
                    orphans, recovered
                )
            )

        self._index.loadIndex()
        if xmlReader.state == XMLReadState.WAS_LEGACY:
            # Often, the index needs to be rebuilt when updating format
            self._index.rebuild()

        self.updateCounts()
        self._session.startSession()
        self.setProjectChanged(False)
        self._valid = True
        self._state = NWProjectState.READY
        self._storage.lockSession()  # Lock only after a successful open. See issue #1977.

        SHARED.newStatusMessage(self.tr("Opened Project: {0}").format(self._data.name))

        return True

    def saveProject(self, autoSave: bool = False) -> bool:
        """Save the project main XML file. The saving command itself
        uses a temporary filename, and the file is replaced afterwards
        to make sure if the save fails, we're not left with a truncated
        file.
        """
        if not self._storage.isOpen():
            SHARED.error(self.tr("There is no project open."))
            return False

        saveTime = time()

        logger.info("Saving project: %s", self._storage.storagePath)

        if autoSave:
            self._data.incAutoCount()
        else:
            self._data.incSaveCount()

        self.updateCounts()
        self.countStatus()

        xmlWriter = self._storage.getXmlWriter()
        if not isinstance(xmlWriter, ProjectXMLWriter):
            return False

        saveTime = time()
        SHARED.clearErrorCache()
        self._data.setIndexRevision(self._index.indexRevision)
        editTime = self._data.editTime + max(round(saveTime - self._session.start), 0)
        content = self._tree.pack()
        if not xmlWriter.write(self._data, content, saveTime, editTime):
            self._reportErrors(self.tr("Issues encountered when saving project:"))
            return False

        # Save other project data
        if not autoSave:
            self._options.saveSettings()
            self._index.saveIndex()

        self._storage.runPostSaveTasks(autoSave=autoSave)

        # Update recent projects
        if storagePath := self._storage.storagePath:
            CONFIG.recentProjects.update(storagePath, self._data, saveTime)

        self._reportErrors(self.tr("Issues encountered when saving project:"))

        SHARED.newStatusMessage(self.tr("Saved Project: {0}").format(self._data.name))
        self.setProjectChanged(False)

        return True

    def closeProject(self, idleTime: float = 0.0) -> None:
        """Close the project."""
        logger.info("Closing project")

        SHARED.clearErrorCache()
        self._index.clear()  # Triggers clear signal, see #1718
        self._options.saveSettings()
        self._tree.writeToCFile()
        self._session.appendSession(idleTime)
        self._storage.closeSession()
        self._reportErrors(self.tr("Issues encountered when closing project:"))

    def backupProject(self, doNotify: bool) -> bool:
        """Create a zip file of the entire project."""
        if not self._storage.isOpen():
            logger.error("No project open")
            return False

        logger.info("Backing up project")
        SHARED.newStatusMessage(self.tr("Backing up project ..."))

        if not self._data.name:
            SHARED.error(
                self.tr(
                    "Cannot backup project because no project name is set. "
                    "Please set a Project Name in Project Settings."
                )
            )
            return False

        cleanName = makeFileNameSafe(self._data.name)
        backupPath = CONFIG.backupPath()
        baseDir = backupPath / cleanName
        try:
            baseDir.mkdir(exist_ok=True, parents=True)
        except Exception as exc:
            SHARED.error(self.tr("Could not create backup folder."), exc=exc)
            return False

        match CONFIG.backupInterval:
            case "day":
                timeStamp = formatTimeStamp(time(), fileSafe=True, fmt="%Y-%m-%d")
            case "week":
                timeStamp = formatTimeStamp(time(), fileSafe=True, fmt="%G-W%V")
            case "month":
                timeStamp = formatTimeStamp(time(), fileSafe=True, fmt="%Y-%m")
            case _:  # Option "session" falls through here
                timeStamp = formatTimeStamp(time(), fileSafe=True)

        archName = baseDir / f"{cleanName} {timeStamp}.zip"
        if self._storage.zipIt(archName, compression=2):
            if doNotify:
                size = formatInt(getFileSize(archName))
                SHARED.info(
                    self.tr("Created a backup of your project of size {0}B.").format(size),
                    info=self.tr("Path: {0}").format(str(backupPath)),
                )
        else:
            SHARED.error(self.tr("Could not write backup archive."))
            return False

        SHARED.newStatusMessage(self.tr("Project backed up to '{0}'").format(str(archName)))

        return True

    ##
    #  Setters
    ##

    def setDefaultStatusImport(self) -> None:
        """Set the default status and importance values."""
        self._data.itemStatus.add(None, self.tr("New"), "faded", "STAR", 0)
        self._data.itemStatus.add(None, self.tr("Note"), "red", "TRIANGLE", 0)
        self._data.itemStatus.add(None, self.tr("Draft"), "yellow", "CIRCLE_T", 0)
        self._data.itemStatus.add(None, self.tr("Finished"), "green", "STAR", 0)
        self._data.itemImport.add(None, self.tr("New"), "purple", "SQUARE", 0)
        self._data.itemImport.add(None, self.tr("Minor"), "purple", "BLOCK_2", 0)
        self._data.itemImport.add(None, self.tr("Major"), "purple", "BLOCK_3", 0)
        self._data.itemImport.add(None, self.tr("Main"), "purple", "BLOCK_4", 0)

    def setProjectLang(self, language: str | None) -> None:
        """Set the project-specific language."""
        language = checkStringNone(language, None)
        if self._data.language != language:
            self._data.setLanguage(language)
            self._loadProjectLocalisation()
            self.setProjectChanged(True)

    def setProjectChanged(self, status: bool) -> bool:
        """Toggle the project changed flag, and propagate the
        information to the GUI statusbar.
        """
        if isinstance(status, bool):
            self._changed = status
            SHARED.setGlobalProjectState(self._changed)
        return self._changed

    ##
    #  Class Methods
    ##

    def updateCounts(self) -> None:
        """Update the total word and character count values."""
        wNovel, wNotes, cNovel, cNotes, wSession, wTarget = self._tree.sumCounts()
        self._data.setCurrCounts(wNovel=wNovel, wNotes=wNotes, cNovel=cNovel, cNotes=cNotes)
        self._data.setDailyProgress(wSession, wTarget)
        self._countsDirty = False

    def markCountsDirty(self) -> None:
        """Flag that an item's goal eligibility has changed, so the word
        counts are stale and must be recalculated.
        """
        self._countsDirty = True

    def countStatus(self) -> None:
        """Count how many times the various status flags are used in the
        project tree. The counts themselves are kept in the ItemStatus
        objects. This is essentially a refresh.
        """
        self._data.itemStatus.resetCounts()
        self._data.itemImport.resetCounts()
        for nwItem in self._tree:
            if nwItem.isNovelLike():
                self._data.itemStatus.increment(nwItem.itemStatus)
            else:
                self._data.itemImport.increment(nwItem.itemImport)

    def updateStatus(self, kind: T_StatusKind, update: T_UpdateEntry) -> None:
        """Update status or import entries."""
        if kind == "s":
            self._data.itemStatus.update(update)
            SHARED.emitStatusLabelsChanged(self, kind)
            self._tree.refreshAllItems()
        elif kind == "i":
            self._data.itemImport.update(update)
            SHARED.emitStatusLabelsChanged(self, kind)
            self._tree.refreshAllItems()
        else:  # pragma: no cover
            pass

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: NWProject")

        self._data.itemStatus.refreshIcons()
        self._data.itemImport.refreshIcons()

    def localLookup(self, word: str | int) -> str:
        """Look up a word or number in the translation map for the
        project and return it. The variable is cast to a string before
        lookup. If the word does not exist, it returns itself.
        """
        return self._langData.get(str(word), str(word))

    ##
    #  Internal Functions
    ##
    def _reportErrors(self, title: str) -> None:
        """Report any errors from the error cache."""
        if errors := SHARED.errorCache():
            SHARED.error(title, "<br><br>".join(errors))

    def _loadProjectLocalisation(self) -> bool:
        """Load the language data for the current project language."""
        if self._data.language is None or CONFIG.nwLangPath is None:
            self._langData = {}
            return False

        langFile = Path(CONFIG.nwLangPath) / f"project_{self._data.language}.json"
        if not safeIsFile(langFile):
            langFile = Path(CONFIG.nwLangPath) / "project_en_GB.json"

        try:
            with open(langFile, mode="r", encoding="utf-8") as inFile:
                self._langData = json.load(inFile)
            logger.debug("Loaded project language file: %s", langFile.name)
        except Exception:
            logger.error("Failed to load project language file")
            logException()
            return False

        return True
