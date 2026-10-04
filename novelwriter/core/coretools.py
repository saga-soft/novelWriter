"""
novelWriter - Project Document Tools
====================================

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
import shutil

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile, is_zipfile

from PyQt6.QtCore import QCoreApplication

from novelwriter import CONFIG, SHARED
from novelwriter.common import isHandle, minmax, safeExists, safeIsFile, simplified
from novelwriter.constants import nwFiles, nwItemClass, nwStats
from novelwriter.core.project import NWProject
from novelwriter.core.storage import ProjectStorageCreate

if TYPE_CHECKING:
    from collections.abc import Iterable


logger = logging.getLogger(__name__)


class DocMerger:
    """Tool: Merge Documents.

    Document tool for merging a set of documents into a single new
    document. The parameters are defined by the user using the
    GuiDocMerge dialog.
    """

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._error = ""
        self._target = None
        self._text = []

    @property
    def targetHandle(self) -> str | None:
        """Get the handle of the target document."""
        if self._target:
            return self._target.itemHandle
        return None

    ##
    #  Methods
    ##

    def getError(self) -> str:
        """Return any collected errors."""
        return self._error

    def setTargetDoc(self, tHandle: str) -> None:
        """Set the target document for the merging. Calling this
        function resets the class.
        """
        self._target = self._project.tree[tHandle]
        self._text = []

    def newTargetDoc(self, sHandle: str, label: str) -> None:
        """Create a brand new target document based on a source handle
        and a new doc label. Calling this function resets the class.
        """
        sItem = self._project.tree[sHandle]
        if sItem and sItem.itemParent:
            tHandle = self._project.newFile(label, sItem.itemParent)
            if nwItem := self._project.tree[tHandle]:  # pragma: no branch
                nwItem.setLayout(sItem.itemLayout)
                nwItem.setStatus(sItem.itemStatus)
                nwItem.setImport(sItem.itemImport)
                nwItem.notifyToRefresh()
                self._target = nwItem
                self._text = []

    def appendText(self, sHandle: str, addComment: bool, cmtPrefix: str) -> None:
        """Append text from an existing document to the text buffer."""
        if item := self._project.tree[sHandle]:
            text = self._project.storage.getDocumentText(sHandle).rstrip("\n")
            if addComment:
                info = item.describeMe()
                status, _ = item.getImportStatus()
                text = f"% {cmtPrefix} {info}: {item.itemName} [{status}]\n\n{text}"
            self._text.append(text)

    def writeTargetDoc(self) -> bool:
        """Write the accumulated text into the designated target
        document, appending any existing text.
        """
        if self._target:
            outDoc = self._project.storage.getDocument(self._target.itemHandle)
            if text := (outDoc.readDocument() or "").rstrip("\n"):
                self._text.insert(0, text)

            status = outDoc.writeDocument("\n\n".join(self._text) + "\n\n")
            if not status:
                self._error = outDoc.error

            self._project.index.reIndexHandle(self._target.itemHandle)
            self._target.notifyToRefresh()

            return status

        return False


class DocSplitter:
    """Document tool for splitting a document into a set of new
    documents. The parameters are defined by the user using the
    GuiDocSplit dialog.
    """

    def __init__(self, project: NWProject, sHandle: str) -> None:

        self._project = project

        self._error = ""
        self._parHandle = None
        self._srcHandle = None
        self._srcItem = None

        self._inFolder = False
        self._rawData = []

        srcItem = self._project.tree[sHandle]
        if srcItem is not None and srcItem.isFileType():
            self._srcHandle = sHandle
            self._srcItem = srcItem

    def __len__(self) -> int:
        """Return the number of raw data entries."""
        return len(self._rawData)

    ##
    #  Methods
    ##

    def getError(self) -> str:
        """Return any collected errors."""
        return self._error

    def setParentItem(self, pHandle: str) -> None:
        """Set the item that will be the top level parent item for the
        new documents.
        """
        self._parHandle = pHandle
        self._inFolder = False

    def newParentFolder(self, pHandle: str, folderLabel: str) -> None:
        """Create a new folder that will be the top level parent item
        for the new documents.
        """
        if self._srcItem:
            nHandle = self._project.newFolder(folderLabel, pHandle)
            if nwItem := self._project.tree[nHandle]:
                nwItem.setStatus(self._srcItem.itemStatus)
                nwItem.setImport(self._srcItem.itemImport)
                nwItem.notifyToRefresh()
            self._parHandle = nHandle
            self._inFolder = True

    def splitDocument(self, splitData: list, splitText: list[str]) -> None:
        """Loop through the split data record and perform the split job
        on a list of text lines.
        """
        self._rawData = []
        buffer = splitText.copy()
        for lineNo, hLevel, hLabel in reversed(splitData):
            chunk = buffer[lineNo:]
            buffer = buffer[:lineNo]
            self._rawData.insert(0, (chunk, hLevel, hLabel))

    def writeDocuments(self, docHierarchy: bool) -> Iterable[bool]:
        """Write each document in the buffer and yield if successful."""
        if self._srcHandle and self._srcItem and self._parHandle:
            pHandle = self._parHandle
            hHandle = [self._parHandle, None, None, None, None]
            pLevel = 0
            for docText, hLevel, docLabel in self._rawData:
                hLevel = minmax(hLevel, 1, 4)
                if pLevel == 0:
                    pLevel = hLevel

                if docHierarchy:
                    if hLevel == 1:
                        pHandle = self._parHandle
                    elif hLevel == 2:
                        pHandle = hHandle[1] or hHandle[0]
                    elif hLevel == 3:
                        pHandle = hHandle[2] or hHandle[1] or hHandle[0]
                    elif hLevel == 4:
                        pHandle = hHandle[3] or hHandle[2] or hHandle[1] or hHandle[0]
                    else:  # pragma: no cover
                        pass

                if (dHandle := self._project.newFile(docLabel, pHandle)) and (nwItem := self._project.tree[dHandle]):
                    hHandle[hLevel] = dHandle
                    nwItem.setStatus(self._srcItem.itemStatus)
                    nwItem.setImport(self._srcItem.itemImport)

                    outDoc = self._project.storage.getDocument(dHandle)
                    status = outDoc.writeDocument("\n".join(docText))
                    if not status:
                        self._error = outDoc.error

                    self._project.index.reIndexHandle(dHandle)
                    nwItem.notifyToRefresh()

                    yield status

                    hHandle[hLevel] = dHandle
                    pLevel = hLevel
        return


class DocDuplicator:
    """A class that will duplicate all documents and folders starting
    from a given handle.
    """

    def __init__(self, project: NWProject) -> None:
        self._project = project

    ##
    #  Methods
    ##

    def duplicate(self, items: list[str]) -> list[str]:
        """Run through a list of items, duplicate them, and copy the
        text content if they are documents.
        """
        result = []
        after = True
        if items:
            hMap: dict[str, str | None] = dict.fromkeys(items)
            SHARED.initMainProgress(len(items))
            for tHandle in items:
                SHARED.incMainProgress()
                if oldItem := self._project.tree[tHandle]:
                    pHandle = hMap.get(oldItem.itemParent or "") or oldItem.itemParent
                    if newItem := self._project.tree.duplicate(tHandle, pHandle, after):
                        hMap[tHandle] = newItem.itemHandle
                        if newItem.isFileType():
                            self._project.copyFileContent(newItem.itemHandle, tHandle)
                        newItem.notifyToRefresh()
                        result.append(newItem.itemHandle)
                    after = False
                else:
                    break
            SHARED.clearMainProgress()
        return result


class ProjectBuilder:
    """A class to build a new project from a set of user-defined
    parameter provided by the New Project Wizard.
    """

    def __init__(self) -> None:
        self._path = None
        self.tr = partial(QCoreApplication.translate, "ProjectBuilder")

    @property
    def projPath(self) -> Path | None:
        """The path of the newly created project."""
        return self._path

    ##
    #  Methods
    ##

    def buildProject(self, data: dict) -> bool:
        """Build or copy a project from a data dictionary."""
        if isinstance(data, dict):
            path = data.get("path") or None
            if author := data.get("author"):
                CONFIG.setLastAuthor(author)
            if isinstance(path, str | Path):
                self._path = Path(path).resolve()
                if data.get("sample"):
                    return self._extractSampleProject(self._path, data)
                elif data.get("template"):
                    return self._copyProject(self._path, data)
                else:
                    return self._buildAndPopulate(self._path, data)
            SHARED.error("A project path is required.")
        return False

    ##
    #  Internal Functions
    ##

    def _buildAndPopulate(self, path: Path, data: dict) -> bool:
        """Build a blank project from a data dictionary."""
        project = NWProject()
        status = project.storage.createNewProject(path)
        if status == ProjectStorageCreate.NOT_EMPTY:
            SHARED.error(self.tr("The target folder is not empty. Please choose another folder."))
            return False
        elif status == ProjectStorageCreate.OS_ERROR:
            SHARED.error(
                self.tr("An error occurred while trying to create the project."),
                exc=project.storage.exc,
            )
            return False

        self._path = project.storage.storagePath

        trName = self.tr("New Project")
        trAuthor = self.tr("Author Name")
        trTitlePage = self.tr("Title Page")

        # Settings
        project.data.setUuid(None)
        project.data.setName(data.get("name", trName))
        project.data.setAuthor(data.get("author", trAuthor))
        project.data.setLanguage(CONFIG.guiLocale)
        project.setDefaultStatusImport()
        project.session.startSession()

        # Add Root Folders
        hNovelRoot = project.newRoot(nwItemClass.NOVEL)
        hTitlePage = project.newFile(trTitlePage, hNovelRoot)

        # Generate Title Page
        aDoc = project.storage.getDocument(hTitlePage)
        aDoc.writeDocument(
            (
                "{author}[br]\n"
                "{address} 1[br]\n"
                "{address} 2 <<\n"
                "\n"
                "[vspace:5]\n"
                "\n"
                "#! {title}\n"
                "\n"
                ">> **{by} {author}** <<\n"
                "\n"
                ">> {count}: [field:{field}] <<\n"
            ).format(
                author=project.data.author or trAuthor,
                address=self.tr("Address Line"),
                title=project.data.name or trName,
                by=self.tr("By"),
                count=self.tr("Word Count"),
                field=nwStats.WORDS_TEXT,
            )
        )

        # Create chapters and scenes
        numChapters = data.get("chapters", 0)
        numScenes = data.get("scenes", 0)

        trChSynop = self.tr("Summary of the chapter.")
        trScSynop = self.tr("Summary of the scene.")
        trNoteDesc = self.tr("A short description.")

        # Create chapters
        if numChapters > 0:
            for ch in range(numChapters):
                chTitle = self.tr("Chapter {0}").format(f"{ch + 1:d}")
                cHandle = project.newFile(chTitle, hNovelRoot)
                aDoc = project.storage.getDocument(cHandle)
                aDoc.writeDocument(f"## {chTitle}\n\n%Synopsis: {trChSynop}\n\n")

                # Create chapter scenes
                if numScenes > 0 and cHandle:
                    for sc in range(numScenes):
                        scTitle = self.tr("Scene {0}").format(f"{ch + 1:d}.{sc + 1:d}")
                        sHandle = project.newFile(scTitle, cHandle)
                        aDoc = project.storage.getDocument(sHandle)
                        aDoc.writeDocument(f"### {scTitle}\n\n%Synopsis: {trScSynop}\n\n")

        # Create scenes (no chapters)
        elif numScenes > 0:
            for sc in range(numScenes):
                scTitle = self.tr("Scene {0}").format(f"{sc + 1:d}")
                sHandle = project.newFile(scTitle, hNovelRoot)
                aDoc = project.storage.getDocument(sHandle)
                aDoc.writeDocument(f"### {scTitle}\n\n%Synopsis: {trScSynop}\n\n")

        # Create notes folders
        noteTitles = {
            nwItemClass.PLOT: self.tr("Main Plot"),
            nwItemClass.CHARACTER: self.tr("Protagonist"),
            nwItemClass.WORLD: self.tr("Main Location"),
        }

        addNotes = data.get("notes", False)
        for newRoot in data.get("roots", []):
            if isinstance(newRoot, nwItemClass):
                rHandle = project.newRoot(newRoot)
                if addNotes:
                    aHandle = project.newFile(noteTitles[newRoot], rHandle)
                    ntTag = simplified(noteTitles[newRoot]).replace(" ", "")
                    aDoc = project.storage.getDocument(aHandle)
                    aDoc.writeDocument(f"# {noteTitles[newRoot]}\n\n@tag: {ntTag}\n\n%Short: {trNoteDesc}\n\n")

        # Also add the archive and trash folders
        project.newRoot(nwItemClass.ARCHIVE)
        _ = project.tree.trash  # Triggers the creation of Trash

        project.index.rebuild()
        project.saveProject()
        project.closeProject()

        return True

    def _copyProject(self, path: Path, data: dict) -> bool:
        """Copy an existing project content, but not the meta data, and
        update new settings.
        """
        source = data.get("template")
        if not (
            isinstance(source, Path) and safeIsFile(source) and (source.name == nwFiles.PROJ_FILE or is_zipfile(source))
        ):
            logger.error("Could not access source project: %s", source)
            return False

        logger.info("Copying project: %s", source)
        if safeExists(path):
            SHARED.error(self.tr("The target folder already exists. Please choose another folder."))
            return False

        # Begin copying
        srcPath = source.parent
        dstPath = path.resolve()
        srcCont = srcPath / "content"
        dstCont = dstPath / "content"
        try:
            dstPath.mkdir(exist_ok=True)
            dstCont.mkdir(exist_ok=True)
            if is_zipfile(source):
                with ZipFile(source) as zipObj:
                    for member in zipObj.namelist():
                        if member == nwFiles.PROJ_FILE or (member.startswith("content") and member.endswith(".md")):
                            zipObj.extract(member, dstPath)
            else:
                shutil.copy2(srcPath / nwFiles.PROJ_FILE, dstPath)
                for item in srcCont.iterdir():
                    if item.is_file() and item.suffix == ".md" and isHandle(item.stem):
                        shutil.copy2(item, dstCont)
        except Exception as exc:
            SHARED.error(self.tr("Could not copy project files."), exc=exc)
            return False

        # Open the copied project and update settings
        self._resetProject(dstPath, data)

        return True

    def _extractSampleProject(self, path: Path, data: dict) -> bool:
        """Make a copy of the sample project by extracting the
        sample.zip file to the new path.
        """
        if safeExists(path):
            SHARED.error(self.tr("The target folder already exists. Please choose another folder."))
            return False

        if safeIsFile(sample := CONFIG.assetPath("sample.zip")):
            try:
                shutil.unpack_archive(sample, path)
                self._resetProject(path, data)
            except Exception as exc:
                SHARED.error(self.tr("Failed to create a new example project."), exc=exc)
                return False
        else:
            SHARED.error(
                self.tr(
                    "Failed to create a new example project. "
                    "Could not find the necessary files. "
                    "They seem to be missing from this installation."
                )
            )
            return False

        return True

    def _resetProject(self, path: Path, data: dict) -> None:
        """Open a project and reset/update its settings."""
        project = NWProject()
        project.openProject(path)
        isSample = project.data.uuid == "e2be99af-f9bf-4403-857a-c3d1ac25abea"

        # Project Data
        project.data.setUuid("")  # Creates a fresh uuid
        if name := data.get("name", ""):
            project.data.setName(name)
        if author := data.get("author", ""):
            project.data.setAuthor(author)
        if isSample:
            project.data.setLastHandle("974e400180a99", "editor")
            project.data.setLastHandle("53b69b83cdafc", "viewer")

        # Reset Items
        for item in project.tree:
            item.setCursorPos(0)
            item.setExpanded(True)

        # Settings
        project.data.setSpellCheck(True)
        project.data.setSpellLang(None)
        project.data.setDoBackup(True)
        project.data.setSaveCount(0)
        project.data.setAutoCount(0)
        project.data.setEditTime(0)

        project.index.rebuild()
        project.saveProject()
        project.closeProject()
