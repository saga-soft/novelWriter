"""
novelWriter - Core Tools Tests
==============================

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

import shutil
import uuid

from pathlib import Path
from shutil import copyfile
from zipfile import ZipFile

import pytest

from novelwriter import CONFIG
from novelwriter.constants import nwFiles, nwItemClass
from novelwriter.core.coretools import DocDuplicator, DocMerger, DocSplitter, ProjectBuilder
from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt
from novelwriter.manuscript.buildsettings import BuildSettings
from novelwriter.manuscript.docbuild import DocumentBuilder

from tests.helpers import NWD_IGNORE, XML_IGNORE, C, buildTestProject, cmpFiles
from tests.mocked import causeOSError


@pytest.mark.core
def testCoreTools_DocMerger(monkeypatch, mockGUI, fncPath, tstPaths, mockRnd, ipsumText):
    """Test the DocMerger utility."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Create Files to Merge
    # =====================

    hChapter1 = project.newFile("Chapter 1", C.hNovelRoot)
    assert hChapter1 is not None

    hSceneOne11 = project.newFile("Scene 1.1", hChapter1)
    hSceneOne12 = project.newFile("Scene 1.2", hChapter1)
    hSceneOne13 = project.newFile("Scene 1.3", hChapter1)
    assert hSceneOne11 is not None
    assert hSceneOne12 is not None
    assert hSceneOne13 is not None

    docText1 = "\n\n".join(ipsumText[0:2]) + "\n\n"
    docText2 = "\n\n".join(ipsumText[1:3]) + "\n\n"
    docText3 = "\n\n".join(ipsumText[2:4]) + "\n\n"
    docText4 = "\n\n".join(ipsumText[3:5]) + "\n\n"

    project.writeNewFile(hChapter1, 2, True, docText1)
    project.writeNewFile(hSceneOne11, 3, True, docText2)
    project.writeNewFile(hSceneOne12, 3, True, docText3)
    project.writeNewFile(hSceneOne13, 3, True, docText4)

    # Basic Checks
    # ============

    docMerger = DocMerger(project)
    assert docMerger.targetHandle is None

    # No writing without a target set
    assert docMerger.writeTargetDoc() is False
    assert docMerger.targetHandle is None

    # Cannot append invalid handle
    docMerger.appendText(C.hInvalid, True, "Merge")
    assert docMerger._text == []

    # Cannot create new target from invalid handle
    docMerger.newTargetDoc(C.hInvalid, "Test")
    assert docMerger.targetHandle is None

    # Merge to New
    # ============

    saveFile = fncPath / "content" / "0000000000014.md"
    testFile = tstPaths.outDir / "coreDocTools_DocMerger_0000000000014.md"
    compFile = tstPaths.refDir / "coreDocTools_DocMerger_0000000000014.md"

    docMerger.newTargetDoc(hChapter1, "All of Chapter 1")
    assert docMerger.targetHandle == "0000000000014"

    docMerger.appendText(hChapter1, True, "Merge")
    assert len(docMerger._text) == 1
    docMerger.appendText(hSceneOne11, True, "Merge")
    assert len(docMerger._text) == 2
    docMerger.appendText(hSceneOne12, True, "Merge")
    assert len(docMerger._text) == 3
    docMerger.appendText(hSceneOne13, True, "Merge")
    assert len(docMerger._text) == 4

    # Block writing and check error handling
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert docMerger.writeTargetDoc() is False
        assert not saveFile.exists()
        assert docMerger.getError() != ""

    # Write properly, and compare
    assert docMerger.writeTargetDoc() is True
    copyfile(saveFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    # Merge into Existing
    # ===================

    saveFile = fncPath / "content" / "0000000000010.md"
    testFile = tstPaths.outDir / "coreDocTools_DocMerger_0000000000010.md"
    compFile = tstPaths.refDir / "coreDocTools_DocMerger_0000000000010.md"

    docMerger.setTargetDoc(hChapter1)

    docMerger.appendText(hSceneOne11, True, "Merge")
    assert len(docMerger._text) == 1
    docMerger.appendText(hSceneOne12, True, "Merge")
    assert len(docMerger._text) == 2
    docMerger.appendText(hSceneOne13, True, "Merge")
    assert len(docMerger._text) == 3

    assert docMerger.writeTargetDoc() is True
    copyfile(saveFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=NWD_IGNORE)

    # Appending without a comment header
    countBefore = len(docMerger._text)
    docMerger.appendText(hSceneOne13, False, "Merge")
    assert len(docMerger._text) == countBefore + 1
    assert not docMerger._text[-1].startswith("%")

    # Just for debugging
    docMerger.writeTargetDoc()


@pytest.mark.core
def testCoreTools_DocSplitter(monkeypatch, mockGUI, fncPath, mockRnd, ipsumText):
    """Test the DocSplitter utility."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Create File to Split
    # ====================

    hSplitDoc = project.newFile("Split Doc", C.hNovelRoot)

    docData = [
        "# Part One",
        ipsumText[0],
        "## Chapter One",
        ipsumText[1],
        "### Scene One",
        ipsumText[2],
        "#### Section One",
        ipsumText[3],
        "#### Section Two",
        ipsumText[4],
        "### Scene Two",
        ipsumText[0],
        "## Chapter Two",
        ipsumText[1],
        "### Scene Three",
        ipsumText[2],
        "### Scene Four",
        ipsumText[3],
        "### Scene Five",
        ipsumText[4],
    ]
    splitData = [
        (0, 1, "Part One"),
        (4, 2, "Chapter One"),
        (8, 3, "Scene One"),
        (12, 4, "Section One"),
        (16, 4, "Section Two"),
        (20, 3, "Scene Two"),
        (24, 2, "Chapter Two"),
        (28, 3, "Scene Three"),
        (32, 3, "Scene Four"),
        (36, 3, "Scene Five"),
    ]

    docText = "\n\n".join(docData)
    docRaw = docText.splitlines()
    assert project.storage.getDocument(hSplitDoc).writeDocument(docText) is True
    project.tree[hSplitDoc].setStatus(C.sFinished)  # type: ignore
    project.tree[hSplitDoc].setImport(C.iMain)  # type: ignore

    docSplitter = DocSplitter(project, hSplitDoc)  # type: ignore
    assert docSplitter._srcItem.isFileType()  # type: ignore
    assert docSplitter.getError() == ""

    # Run the split algorithm
    docSplitter.splitDocument(splitData, docRaw)  # type: ignore
    for i, (lineNo, hLevel, hLabel) in enumerate(splitData):
        assert docSplitter._rawData[i] == (docRaw[lineNo : lineNo + 4], hLevel, hLabel)
    assert project.tree.subTree(C.hNovelRoot) == [
        "000000000000c",
        "000000000000d",
        "000000000000e",
        "000000000000f",
        "0000000000010",
    ]

    # Test flat split into same parent
    docSplitter.setParentItem(C.hNovelRoot)
    assert docSplitter._inFolder is False
    assert docSplitter._parHandle is not None

    # Cause write error on all chunks
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert not any(docSplitter.writeDocuments(False))
        assert docSplitter.getError() == "OSError: Mock OSError"
    assert project.tree.subTree(C.hNovelRoot) == [
        "000000000000c",
        "000000000000d",
        "000000000000e",
        "000000000000f",
        "0000000000010",
        "0000000000011",
        "0000000000012",
        "0000000000013",
        "0000000000014",
        "0000000000015",
        "0000000000016",
        "0000000000017",
        "0000000000018",
        "0000000000019",
        "000000000001a",
    ]

    # Generate as flat structure in root folder
    resStatus = list(docSplitter.writeDocuments(False))
    resDocHandle = project.tree.subTree(C.hNovelRoot)

    assert all(resStatus)
    assert resDocHandle == [
        "000000000000c",
        "000000000000d",
        "000000000000e",
        "000000000000f",
        "0000000000010",
        "0000000000011",
        "0000000000012",
        "0000000000013",
        "0000000000014",
        "0000000000015",
        "0000000000016",
        "0000000000017",
        "0000000000018",
        "0000000000019",
        "000000000001a",
        "000000000001b",
        "000000000001c",
        "000000000001d",
        "000000000001e",
        "000000000001f",
        "0000000000020",
        "0000000000021",
        "0000000000022",
        "0000000000023",
        "0000000000024",
    ]

    # Generate as hierarchy in new folder
    docSplitter.newParentFolder(C.hNovelRoot, "Split Folder")
    assert docSplitter._inFolder is True
    assert docSplitter._parHandle is not None

    resStatus = list(docSplitter.writeDocuments(True))
    resDocHandle = project.tree.subTree(docSplitter._parHandle)

    assert all(resStatus)
    assert resDocHandle == [
        "0000000000026",  # Part One
        "0000000000027",  # Chapter One
        "0000000000028",  # Scene One
        "0000000000029",  # Section One
        "000000000002a",  # Section Two
        "000000000002b",  # Scene Two
        "000000000002c",  # Chapter Two
        "000000000002d",  # Scene Three
        "000000000002e",  # Scene Four
        "000000000002f",  # Scene Five
    ]

    # Check that status and importance has been preserved
    for rHandle in resDocHandle:
        assert project.tree[rHandle].itemStatus == C.sFinished  # type: ignore
        assert project.tree[rHandle].itemImport == C.iMain  # type: ignore

    # An invalid parent handle results in no new item being created
    docSplitter.newParentFolder(C.hInvalid, "Bad Folder")
    assert docSplitter._parHandle is None

    # An invalid parent handle deeper in the hierarchy results in no documents written
    docSplitter.setParentItem(C.hInvalid)
    assert list(docSplitter.writeDocuments(True)) == []

    # Check handling of improper initialisation
    docSplitter = DocSplitter(project, C.hInvalid)
    assert docSplitter._srcHandle is None
    assert docSplitter._srcItem is None
    assert docSplitter.newParentFolder(C.hNovelRoot, "Split Folder") is None
    assert list(docSplitter.writeDocuments(False)) == []

    project.saveProject()


@pytest.mark.core
def testCoreTools_DocDuplicator(monkeypatch, mockGUI, fncPath, tstPaths, mockRnd):
    """Test the DocDuplicator utility."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    dup = DocDuplicator(project)

    ttText = "#! New Novel\n\n>> By Jane Doe <<\n"
    chText = "## New Chapter\n\n"
    scText = "### New Scene\n\n"

    # Check document content
    assert project.storage.getDocument(C.hTitlePage).readDocument() == ttText
    assert project.storage.getDocument(C.hChapterDoc).readDocument() == chText
    assert project.storage.getDocument(C.hSceneDoc).readDocument() == scText

    # Nothing to do
    assert list(dup.duplicate([])) == []

    # Single Document
    # ===============

    # A new copy is created
    assert list(dup.duplicate([C.hSceneDoc])) == [
        "0000000000010"  # The Scene
    ]
    assert list(project.tree._items.keys()) == [
        C.hNovelRoot,
        C.hPlotRoot,
        C.hCharRoot,
        C.hWorldRoot,
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
        "0000000000010",
    ]

    # With the same content
    assert project.storage.getDocument("0000000000010").readDocument() == scText

    # They should have the same parent
    assert project.tree["0000000000010"].itemParent == C.hChapterDir  # type: ignore

    # Folder w/Two Files
    # ==================

    # The folder is copied, with two docs
    assert list(dup.duplicate([C.hChapterDir, C.hChapterDoc, C.hSceneDoc])) == [
        "0000000000011",  # The Folder
        "0000000000012",  # The Chapter
        "0000000000013",  # The Scene
    ]
    assert list(project.tree._items.keys()) == [
        C.hNovelRoot,
        C.hPlotRoot,
        C.hCharRoot,
        C.hWorldRoot,
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
        "0000000000010",
        "0000000000011",
        "0000000000012",
        "0000000000013",
    ]

    # With the same content
    assert project.storage.getDocument("0000000000012").readDocument() == chText
    assert project.storage.getDocument("0000000000013").readDocument() == scText

    # The chapter dirs should have the same parent
    assert project.tree["0000000000011"].itemParent == C.hNovelRoot  # type: ignore

    # The new files should have the new folder as parent
    assert project.tree["0000000000012"].itemParent == "0000000000011"  # type: ignore
    assert project.tree["0000000000013"].itemParent == "0000000000011"  # type: ignore

    # Full Root Folder
    # ================

    # The root is copied, with three docs and a folder
    assert list(dup.duplicate([C.hNovelRoot, C.hTitlePage, C.hChapterDir, C.hChapterDoc, C.hSceneDoc])) == [
        "0000000000014",  # The Root
        "0000000000015",  # The Title Page
        "0000000000016",  # The Folder
        "0000000000017",  # The Chapter
        "0000000000018",  # The Scene
    ]
    assert list(project.tree._items.keys()) == [
        C.hNovelRoot,
        C.hPlotRoot,
        C.hCharRoot,
        C.hWorldRoot,
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
        "0000000000010",
        "0000000000011",
        "0000000000012",
        "0000000000013",
        "0000000000014",
        "0000000000015",
        "0000000000016",
        "0000000000017",
        "0000000000018",
    ]

    # With the same content
    assert project.storage.getDocument("0000000000015").readDocument() == ttText
    assert project.storage.getDocument("0000000000017").readDocument() == chText
    assert project.storage.getDocument("0000000000018").readDocument() == scText

    # The root folder should have no parent
    assert project.tree["0000000000014"].itemParent is None  # type: ignore

    # The folder and files should have the new root
    assert project.tree["0000000000015"].itemRoot == "0000000000014"  # type: ignore
    assert project.tree["0000000000016"].itemRoot == "0000000000014"  # type: ignore
    assert project.tree["0000000000017"].itemRoot == "0000000000014"  # type: ignore
    assert project.tree["0000000000018"].itemRoot == "0000000000014"  # type: ignore

    # And they should have new parents
    assert project.tree["0000000000015"].itemParent == "0000000000014"  # type: ignore
    assert project.tree["0000000000016"].itemParent == "0000000000014"  # type: ignore
    assert project.tree["0000000000017"].itemParent == "0000000000016"  # type: ignore
    assert project.tree["0000000000018"].itemParent == "0000000000016"  # type: ignore

    # Exceptions
    # ==========

    # Handle invalid items
    assert list(dup.duplicate([C.hInvalid])) == []

    # Also stop early if invalid items are encountered
    assert list(dup.duplicate([C.hInvalid, C.hSceneDoc])) == []

    # Don't overwrite existing files
    content = project.storage.contentPath
    assert isinstance(content, Path)
    (content / "0000000000019.md").touch()
    assert (content / "0000000000019.md").exists()
    assert list(dup.duplicate([C.hChapterDoc, C.hSceneDoc])) == ["0000000000019", "000000000001a"]

    # Save and Close
    project.saveProject()

    projFile = fncPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "coreTools_DocDuplicator_nwProject.nwx"
    compFile = tstPaths.refDir / "coreTools_DocDuplicator_nwProject.nwx"

    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)

    # If duplicating an item fails, later items are still processed
    with monkeypatch.context() as mp:
        original = type(project.tree).duplicate
        state = {"count": 0}

        def flaky(self, handle, pHandle, after):
            state["count"] += 1
            return None if state["count"] == 1 else original(self, handle, pHandle, after)

        mp.setattr(type(project.tree), "duplicate", flaky)
        before = set(project.tree._items.keys())
        result = list(dup.duplicate([C.hChapterDoc, C.hSceneDoc]))
        assert len(result) == 1
        assert result[0] not in before


@pytest.mark.core
def testCoreTools_ProjectBuilderWrapper(monkeypatch, caplog, fncPath, mockGUI):
    """Test the wrapper function of the project builder."""
    builder = ProjectBuilder()

    # Setting no data should fail
    assert builder.buildProject({}) is False

    # Wrong type should also fail
    assert builder.buildProject("stuff") is False  # type: ignore

    # Folder not writable
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.mkdir", causeOSError)
        assert builder.buildProject({"path": fncPath}) is False
        assert "An error occurred" in caplog.text

    # Try again with a proper path
    assert builder.buildProject({"path": fncPath}) is True
    assert builder.projPath == fncPath

    # Creating the project once more should fail
    caplog.clear()
    assert builder.buildProject({"path": fncPath}) is False
    assert "The target folder is not empty." in caplog.text


@pytest.mark.core
def testCoreTools_ProjectBuilderA(monkeypatch, fncPath, tstPaths, mockGUI, mockRnd):
    """Create a new project from a project dictionary, with chapters."""
    monkeypatch.setattr("uuid.uuid4", lambda *a: uuid.UUID("d0f3fe10-c6e6-4310-8bfd-181eb4224eed"))

    data = {
        "name": "Test Project A",
        "author": "Jane Doe",
        "language": -1,
        "path": fncPath,
        "sample": False,
        "template": None,
        "chapters": 3,
        "scenes": 3,
        "roots": [
            nwItemClass.PLOT,
            nwItemClass.CHARACTER,
            nwItemClass.WORLD,
        ],
        "notes": True,
    }

    builder = ProjectBuilder()
    assert builder.buildProject(data) is True

    projFile = fncPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "coreTools_ProjectBuilderA_nwProject.nwx"
    compFile = tstPaths.refDir / "coreTools_ProjectBuilderA_nwProject.nwx"

    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)

    # Check Content
    project = NWProject()
    project.openProject(fncPath)

    build = BuildSettings()

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    testFile = tstPaths.outDir / "coreTools_ProjectBuilderA_Project.md"
    compFile = tstPaths.refDir / "coreTools_ProjectBuilderA_Project.md"

    assert list(docBuild.iterBuildDocument(testFile, nwBuildFmt.EXT_MD))
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)


@pytest.mark.core
def testCoreTools_ProjectBuilderB(monkeypatch, fncPath, tstPaths, mockGUI, mockRnd):
    """Create a new project from a project dictionary, without chapters."""
    monkeypatch.setattr("uuid.uuid4", lambda *a: uuid.UUID("d0f3fe10-c6e6-4310-8bfd-181eb4224eed"))

    data = {
        "name": "Test Project B",
        "author": "Jane Doe",
        "language": -1,
        "path": fncPath,
        "sample": False,
        "template": None,
        "chapters": 0,
        "scenes": 6,
        "roots": [
            nwItemClass.PLOT,
            nwItemClass.CHARACTER,
            nwItemClass.WORLD,
        ],
        "notes": True,
    }

    builder = ProjectBuilder()
    assert builder.buildProject(data) is True

    projFile = fncPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "coreTools_ProjectBuilderB_nwProject.nwx"
    compFile = tstPaths.refDir / "coreTools_ProjectBuilderB_nwProject.nwx"

    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)

    # Check Content
    project = NWProject()
    project.openProject(fncPath)

    build = BuildSettings()

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    testFile = tstPaths.outDir / "coreTools_ProjectBuilderB_Project.md"
    compFile = tstPaths.refDir / "coreTools_ProjectBuilderB_Project.md"

    assert list(docBuild.iterBuildDocument(testFile, nwBuildFmt.EXT_MD))
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)


@pytest.mark.core
def testCoreTools_ProjectBuilderNoScenesAndRoots(monkeypatch, fncPath, mockGUI, mockRnd):
    """Create a new project with chapters but no scenes, and check handling
    of invalid root entries and disabled notes.
    """
    monkeypatch.setattr("uuid.uuid4", lambda *a: uuid.UUID("d0f3fe10-c6e6-4310-8bfd-181eb4224eed"))

    data = {
        "name": "Test Project C",
        "author": "Jane Doe",
        "language": -1,
        "path": fncPath,
        "sample": False,
        "template": None,
        "chapters": 2,
        "scenes": 0,
        "roots": [
            nwItemClass.PLOT,
            "not_a_valid_root",
        ],
        "notes": False,
    }

    builder = ProjectBuilder()
    assert builder.buildProject(data) is True

    project = NWProject()
    project.openProject(fncPath)

    # Chapters were created, but no scenes underneath them
    novelRoot = project.tree.findRoot(nwItemClass.NOVEL)
    assert novelRoot is not None
    for cHandle in project.tree.subTree(novelRoot):
        assert project.tree[cHandle].isFileType()  # type: ignore

    # The valid root was created, but no notes since "notes" is False
    plotRoot = project.tree.findRoot(nwItemClass.PLOT)
    assert plotRoot is not None
    assert project.tree.subTree(plotRoot) == []

    # The invalid root entry was ignored (only Novel, Plot, Archive, and Trash exist)
    assert project.tree.rootClasses() == {nwItemClass.NOVEL, nwItemClass.PLOT, nwItemClass.ARCHIVE, nwItemClass.TRASH}


@pytest.mark.core
def testCoreTools_ProjectBuilderCopyPlain(monkeypatch, caplog, mockGUI, prjLipsum, fncPath):
    """Create a new project copied from existing project."""
    srcPath = prjLipsum / nwFiles.PROJ_FILE
    dstPath = fncPath / "lipsum"
    data = {
        "name": "Test Project",
        "author": "Jane Doe",
        "path": dstPath,
        "template": srcPath,
    }

    builder = ProjectBuilder()

    # No path set
    assert builder.buildProject({"template": srcPath}) is False

    # No project at path
    assert builder.buildProject({"path": fncPath, "template": fncPath}) is False

    # Cannot copy to existing folder
    assert builder.buildProject({"path": fncPath, "template": srcPath}) is False

    # Valid data, but copy fails
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.mkdir", lambda *a, **k: causeOSError)
        assert builder.buildProject(data) is False
        assert "Could not copy project files." in caplog.text
        dstPath.unlink(missing_ok=True)  # The failed mkdir leaves an empty file

    # Add a stray file that should not be copied
    strayFile = prjLipsum / "content" / "not-a-handle.txt"
    strayFile.write_text("stray")

    # Copy project properly
    assert builder.buildProject(data) is True
    assert not (dstPath / "content" / "not-a-handle.txt").exists()

    # Check Copy
    # ==========

    srcProject = NWProject()
    srcProject.openProject(srcPath)

    dstProject = NWProject()
    dstProject.openProject(dstPath)

    # UUID should be different
    assert srcProject.data.uuid != dstProject.data.uuid

    # Name should be different
    assert srcProject.data.name == "Lorem Ipsum"
    assert dstProject.data.name == "Test Project"

    # Author should be different
    assert srcProject.data.author == "lipsum.com"
    assert dstProject.data.author == "Jane Doe"

    # Language should be the same
    assert srcProject.data.language == "en_GB"
    assert dstProject.data.language == "en_GB"

    # Counts should be more or less zeroed
    assert dstProject.data.saveCount < 5
    assert dstProject.data.autoCount < 5
    assert dstProject.data.editTime < 10


@pytest.mark.core
def testCoreTools_ProjectBuilderCopyZipped(monkeypatch, caplog, mockGUI, fncPath, mockRnd):
    """Create a new project copied from existing zipped project."""
    # Create a project
    origPath = fncPath / "original"
    srcProject = NWProject()
    buildTestProject(srcProject, origPath)

    # Zip it
    shutil.make_archive(str(fncPath / "original"), "zip", origPath)

    # Make fake zip file
    fakeZip = fncPath / "broken.zip"
    fakeZip.write_bytes(b"stuff")

    # Set up the builder
    srcPath = fncPath / "original.zip"
    dstPath = fncPath / "copy"
    data = {
        "name": "Test Project",
        "author": "Jane Doe",
        "language": "en_US",
        "path": dstPath,
        "template": srcPath,
    }

    builder = ProjectBuilder()

    # No path set
    assert builder.buildProject({"template": srcPath}) is False

    # No project at path
    assert builder.buildProject({"path": fncPath, "template": fncPath}) is False

    # Cannot copy to existing folder
    assert builder.buildProject({"path": fncPath, "template": srcPath}) is False

    # Cannot copy to existing folder
    caplog.clear()
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.coretools.is_zipfile", lambda *a: True)
        assert builder.buildProject({"path": dstPath, "template": fakeZip}) is False
        assert "Could not copy project files." in caplog.text
        shutil.rmtree(dstPath, ignore_errors=True)

    # Copy project properly
    assert builder.buildProject(data) is True

    # Check Copy
    # ==========

    dstProject = NWProject()
    dstProject.openProject(dstPath)

    # UUID should be different
    assert srcProject.data.uuid != dstProject.data.uuid

    # Name should be different
    assert srcProject.data.name == "New Project"
    assert dstProject.data.name == "Test Project"

    # Author should be different
    assert srcProject.data.author == "Jane Doe"
    assert dstProject.data.author == "Jane Doe"

    # Language should be the same
    assert srcProject.data.language is None
    assert dstProject.data.language is None

    # Counts should be more or less zeroed
    assert dstProject.data.saveCount < 5
    assert dstProject.data.autoCount < 5
    assert dstProject.data.editTime < 10


@pytest.mark.core
def testCoreTools_ProjectBuilderSample(monkeypatch, mockGUI, fncPath, tstPaths):
    """Create a new sample project."""
    data = {
        "name": "Test Sample",
        "author": "Jane Doe",
        "path": fncPath / "project",
        "sample": True,
    }

    builder = ProjectBuilder()

    # No path set
    assert builder.buildProject({"sample": True}) is False

    # Force the lookup path for assets to our temp folder
    srcSample = CONFIG._appRoot / "sample"
    bldSample = CONFIG.assetPath("sample.zip")
    dstSample = tstPaths.tmpDir / "sample.zip"
    monkeypatch.setattr("novelwriter.config.Config.assetPath", lambda *a: tstPaths.tmpDir / "sample.zip")

    # Cannot extract when the zip does not exist
    assert builder.buildProject(data) is False

    # Create and open a defective zip file
    with open(dstSample, mode="w+", encoding="utf-8") as outFile:
        outFile.write("foo")

    assert builder.buildProject(data) is False
    dstSample.unlink()

    # Create a real zip file, and unpack it. The raw sample source isn't
    # shipped in packaged builds, only the pre-built asset, so fall back
    # to copying that instead.
    if srcSample.is_dir():
        with ZipFile(dstSample, "w") as zipObj:
            zipObj.write(srcSample / "nwProject.nwx", "nwProject.nwx")
            for docFile in (srcSample / "content").iterdir():
                zipObj.write(docFile, f"content/{docFile.name}")
    else:
        assert bldSample.is_file()
        copyfile(bldSample, dstSample)

    assert builder.buildProject(data) is True

    # Can't create to the same target again
    assert builder.buildProject(data) is False

    # Building without a name or author keeps the sample's own values
    dataNoNameAuthor = {"path": fncPath / "project2", "sample": True}
    assert builder.buildProject(dataNoNameAuthor) is True

    sampleProject = NWProject()
    sampleProject.openProject(fncPath / "project2")
    assert sampleProject.data.name != ""
    assert sampleProject.data.author != ""

    dstSample.unlink()
