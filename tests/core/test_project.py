"""
novelWriter - NWProject Tests
=============================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

from datetime import datetime
from shutil import copyfile
from zipfile import ZipFile

import pytest

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject, NWProjectState
from novelwriter.core.projectxml import ProjectXMLReader, ProjectXMLWriter, XMLReadState
from novelwriter.enum import nwItemClass
from novelwriter.shared import _GuiAlert

from tests.helpers import XML_IGNORE, C, buildTestProject, cmpFiles
from tests.mocked import causeOSError


@pytest.mark.core
def testNWProject_NewRoot(fncPath, tstPaths, mockGUI, mockRnd):
    """Check that new root folders can be added to the project."""
    projFile = fncPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "coreProject_NewRoot_nwProject.nwx"
    compFile = tstPaths.refDir / "coreProject_NewRoot_nwProject.nwx"

    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    assert project.newRoot(nwItemClass.NOVEL) == "0000000000010"
    assert project.newRoot(nwItemClass.PLOT) == "0000000000011"
    assert project.newRoot(nwItemClass.CHARACTER) == "0000000000012"
    assert project.newRoot(nwItemClass.WORLD) == "0000000000013"
    assert project.newRoot(nwItemClass.TIMELINE) == "0000000000014"
    assert project.newRoot(nwItemClass.OBJECT) == "0000000000015"
    assert project.newRoot(nwItemClass.CUSTOM) == "0000000000016"
    assert project.newRoot(nwItemClass.CUSTOM) == "0000000000017"

    assert project.projChanged is True
    assert project.saveProject() is True
    project.closeProject()

    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)
    assert project.projChanged is False

    # Delete the new items
    assert project.removeItem("0000000000010") is True
    assert project.removeItem("0000000000011") is True
    assert project.removeItem("0000000000012") is True
    assert project.removeItem("0000000000013") is True
    assert project.removeItem("0000000000014") is True
    assert project.removeItem("0000000000015") is True
    assert project.removeItem("0000000000016") is True
    assert project.removeItem("0000000000017") is True

    assert "0000000000010" not in project.tree
    assert "0000000000011" not in project.tree
    assert "0000000000012" not in project.tree
    assert "0000000000013" not in project.tree
    assert "0000000000014" not in project.tree
    assert "0000000000015" not in project.tree
    assert "0000000000016" not in project.tree
    assert "0000000000017" not in project.tree


@pytest.mark.core
def testNWProject_NewFileFolder(monkeypatch, fncPath, tstPaths, mockGUI, mockRnd):
    """Check that new files can be added to the project."""
    projFile = fncPath / "nwProject.nwx"
    testFile = tstPaths.outDir / "coreProject_NewFileFolder_nwProject.nwx"
    compFile = tstPaths.refDir / "coreProject_NewFileFolder_nwProject.nwx"

    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    aHandle = "0000000000010"
    bHandle = "0000000000011"
    cHandle = "0000000000012"
    dHandle = "0000000000013"
    eHandle = "0000000000014"
    xHandle = "1234567890abc"

    # Invalid call
    assert project.newFolder("New Folder", xHandle) is None
    assert project.newFile("New File", xHandle) is None

    # Add files properly
    assert project.newFolder("Stuff", C.hNovelRoot) == aHandle
    assert project.newFile("Hello", aHandle) == bHandle
    assert project.newFile("Jane", C.hCharRoot) == cHandle
    assert project.newFile("John", C.hCharRoot) == dHandle
    assert project.newFile("Mike", C.hCharRoot) == eHandle

    assert aHandle in project.tree
    assert bHandle in project.tree
    assert cHandle in project.tree
    assert dHandle in project.tree
    assert eHandle in project.tree

    # Write to file, failed
    assert project.writeNewFile("blabla", 1, True) is False  # Not a handle
    assert project.writeNewFile(aHandle, 1, True) is False  # Not a file
    assert project.writeNewFile(C.hTitlePage, 1, True) is False  # Already has content

    # Write to file, success
    assert project.writeNewFile(bHandle, 2, True) is True
    assert project.storage.getDocument(bHandle).readDocument() == "## Hello\n\n"

    # Write to file with additional text, success
    assert project.writeNewFile(cHandle, 1, False, "Hi Jane\n\n") is True
    assert project.storage.getDocument(cHandle).readDocument() == ("# Jane\n\nHi Jane\n\n")

    # Copy file content, invalid target
    assert project.copyFileContent(xHandle, cHandle) is False  # Unknown handle
    assert project.copyFileContent(aHandle, cHandle) is False  # Target is a folder

    # Copy file content, invalid source
    assert project.copyFileContent(dHandle, xHandle) is False  # Unknown handle
    assert project.copyFileContent(dHandle, aHandle) is False  # Source is a folder

    # Copy file content, target not empty
    assert project.copyFileContent(bHandle, cHandle) is False

    # Copy file content, success
    assert project.copyFileContent(dHandle, cHandle) is True

    cText = project.storage.getDocument(cHandle).readDocument()
    dText = project.storage.getDocument(dHandle).readDocument()

    assert dText == cText

    # Copy file content, and update title
    assert project.copyFileContent(eHandle, cHandle, "Lars") is True
    assert project.storage.getDocument(eHandle).readDocument() == "# Lars\n\nHi Jane\n\n"

    # Save, close and check
    assert project.projChanged is True
    assert project.saveProject() is True

    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignStart=XML_IGNORE)
    assert project.projChanged is False

    # Delete new file, but block access
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.unlink", causeOSError)
        assert project.removeItem(bHandle) is False
        assert bHandle in project.tree

    # Delete new files and folders
    assert (fncPath / "content" / f"{dHandle}.md").exists()
    assert (fncPath / "content" / f"{cHandle}.md").exists()
    assert (fncPath / "content" / f"{bHandle}.md").exists()

    assert project.removeItem(dHandle) is True
    assert project.removeItem(cHandle) is True
    assert project.removeItem(bHandle) is True
    assert project.removeItem(aHandle) is True

    assert not (fncPath / "content" / f"{dHandle}.md").exists()
    assert not (fncPath / "content" / f"{cHandle}.md").exists()
    assert not (fncPath / "content" / f"{bHandle}.md").exists()

    assert aHandle not in project.tree
    assert bHandle not in project.tree
    assert cHandle not in project.tree
    assert dHandle not in project.tree

    project.closeProject()


@pytest.mark.core
def testNWProject_CreateNewNote(monkeypatch, fncPath, mockGUI, mockRnd):
    """Check that new notes can be created for a given tag."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # A NO_CLASS item class does nothing
    project.createNewNote("jane", nwItemClass.NO_CLASS)
    assert project.tree.findRoot(nwItemClass.CHARACTER) == C.hCharRoot
    assert list(project.tree.subTree(C.hCharRoot)) == []

    # A valid class creates the root folder and the note file
    project.createNewNote("jane", nwItemClass.CHARACTER)
    noteHandles = project.tree.subTree(C.hCharRoot)
    assert len(noteHandles) == 1
    assert project.tree[noteHandles[0]].itemName == "Jane"  # type: ignore
    assert project.storage.getDocument(noteHandles[0]).readDocument() == "# Jane\n\n@tag: jane\n\n"

    # A class with no existing root folder creates a new one
    assert project.tree.findRoot(nwItemClass.OBJECT) is None
    project.createNewNote("gun", nwItemClass.OBJECT)
    objRoot = project.tree.findRoot(nwItemClass.OBJECT)
    assert objRoot is not None
    assert len(project.tree.subTree(objRoot)) == 1

    # If the note file cannot be created, nothing else happens
    with monkeypatch.context() as mp:
        mp.setattr(NWProject, "newFile", lambda *a, **k: None)
        project.createNewNote("mike", nwItemClass.OBJECT)
    assert len(project.tree.subTree(objRoot)) == 1

    project.closeProject()


@pytest.mark.core
def testNWProject_Open(monkeypatch, caplog, mockGUI, fncPath, mockRnd):
    """Test opening a project."""
    project = NWProject()
    mockRnd.reset()
    # buildTestProject(project, fncPath)

    # Unknown project file
    fooBar = fncPath / "foobar.txt"
    fooBar.touch()
    caplog.clear()
    assert project.openProject(fooBar) is False
    assert "Not a known project file format." in caplog.text
    assert project.isValid is False
    assert project.lockStatus is None

    # No project file
    caplog.clear()
    assert project.openProject(fncPath) is False
    assert "Project file not found." in caplog.text
    fooBar.unlink()

    # Fail to open project location
    projFile = fncPath / nwFiles.PROJ_FILE
    metaFile = fncPath / "meta"
    projFile.touch()
    metaFile.touch()
    caplog.clear()
    assert project.openProject(fncPath) is False
    assert "Failed to open project." in caplog.text
    metaFile.unlink()
    projFile.unlink()

    # Create test project
    buildTestProject(project, fncPath)

    # Open successfully
    assert project.openProject(fncPath) is True

    # Open again should fail on lock file
    assert project.openProject(fncPath) is False
    assert project.state == NWProjectState.LOCKED
    assert project.isValid is True
    assert project.lockStatus is not None

    # Force re-open
    assert project.openProject(fncPath, clearLock=True) is True
    assert project.state == NWProjectState.READY
    assert project.isValid is True
    assert project.lockStatus is None

    # Fail getting xml reader
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getXmlReader", lambda *a: None)
        assert project.openProject(fncPath, clearLock=True) is False

    # Not a novelwriter XML file
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "read", lambda *a: False)
        mp.setattr(ProjectXMLReader, "state", property(lambda *a: XMLReadState.NOT_NWX_FILE))
        assert project.openProject(fncPath, clearLock=True) is False
        assert "Project file does not appear" in SHARED.lastAlert[0]

    # Unknown project file version
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "read", lambda *a: False)
        mp.setattr(ProjectXMLReader, "state", property(lambda *a: XMLReadState.UNKNOWN_VERSION))
        assert project.openProject(fncPath, clearLock=True) is False
        assert "Unknown or unsupported novelWriter project file" in SHARED.lastAlert[0]

    # Other parse error
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "read", lambda *a: False)
        mp.setattr(ProjectXMLReader, "state", property(lambda *a: XMLReadState.CANNOT_PARSE))
        assert project.openProject(fncPath, clearLock=True) is False
        assert "Failed to parse project xml" in SHARED.lastAlert[0]

    # Won't convert legacy file
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "state", property(lambda *a: XMLReadState.WAS_LEGACY))
        mp.setattr(_GuiAlert, "finalState", False)
        assert project.openProject(fncPath, clearLock=True) is False
        assert "The file format of your project is about to be" in SHARED.lastAlert[0]

    # Also won't convert old document files, even if the xml itself isn't flagged as legacy
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.hasBreakingChanges", lambda *a: True)
        mp.setattr(_GuiAlert, "finalState", False)
        assert project.openProject(fncPath, clearLock=True) is False
        assert "The file format of your project is about to be" in SHARED.lastAlert[0]

    # Won't open project from newer version
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "hexVersion", property(lambda *a: 0x99999999))
        mp.setattr(_GuiAlert, "finalState", False)
        assert project.openProject(fncPath, clearLock=True) is False
        assert "This project was saved by a newer version" in SHARED.lastAlert[0]

    # Will open a newer version project if the user accepts
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "hexVersion", property(lambda *a: 0x99999999))
        assert project.openProject(fncPath, clearLock=True) is True

    # If the storage path is unavailable, recent projects are not updated
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.storagePath", property(lambda *a: None))
        assert project.openProject(fncPath, clearLock=True) is True

    # Fail checking items should still pass
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.ProjectTree.checkConsistency", lambda *a: (1, 0))
        assert project.openProject(fncPath, clearLock=True) is True

    # Trigger an index rebuild
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLReader, "state", property(lambda *a: XMLReadState.WAS_LEGACY))
        mp.setattr("novelwriter.core.index.Index.loadIndex", lambda *a: True)
        project.index._indexRevision = 0
        assert project.openProject(fncPath, clearLock=True) is True
        assert "The file format of your project is about to be" in SHARED.lastAlert[0]
        assert project.index._indexRevision == 4

    project.closeProject()


@pytest.mark.core
def testNWProject_OpenConvertsOldDocuments(monkeypatch, mockGUI, fncPath, mockRnd):
    """Test that an old .nwd document file is only converted to .md
    once the user accepts the upgrade prompt.
    """
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    project.closeProject()

    contentPath = fncPath / "content"
    nwdFile = contentPath / f"{C.hSceneDoc}.nwd"
    mdFile = contentPath / f"{C.hSceneDoc}.md"
    mdFile.unlink()
    nwdFile.write_text("### New Scene\n\n", encoding="utf-8")

    # Declining the prompt leaves the file untouched
    project = NWProject()
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert project.openProject(fncPath) is False
    assert nwdFile.exists()
    assert not mdFile.exists()

    # Accepting converts the file and the project opens normally
    project = NWProject()
    assert project.openProject(fncPath, clearLock=True) is True
    assert not nwdFile.exists()
    assert mdFile.exists()
    assert C.hSceneDoc in project.tree

    project.closeProject()


@pytest.mark.core
def testNWProject_Save(monkeypatch, mockGUI, mockRnd, fncPath):
    """Test saving a project."""
    project = NWProject()

    # Nothing to save
    assert project.saveProject() is False

    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Fail getting xml writer
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getXmlWriter", lambda *a: None)
        assert project.saveProject() is False

    # Fail writing
    with monkeypatch.context() as mp:
        mp.setattr(ProjectXMLWriter, "write", lambda *a: False)
        assert project.saveProject() is False

    # Save with and without autosave
    assert project.saveProject(autoSave=False) is True
    assert project.saveProject(autoSave=True) is True

    # If the storage path is unavailable, recent projects are not updated
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.storagePath", property(lambda *a: None))
        assert project.saveProject() is True

    project.closeProject()


@pytest.mark.core
def testNWProject_AutoSaveIndexRevision(mockGUI, mockRnd, fncPath):
    """Test that the index revision is kept current in the project file
    on every save, including autosave.
    """
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)  # Performs a full save

    savedRevision = project.index.indexRevision
    assert project.data.indexRevision == savedRevision

    # Edit a document and only autosave, so the index cache on disk is left untouched
    tHandle = next(i.itemHandle for i in project.tree if i.isFileType())
    doc = project.storage.getDocument(tHandle)
    doc.writeDocument("### More Content\n\n")
    project.index.reIndexHandle(tHandle)
    assert project.index.indexRevision > savedRevision

    assert project.saveProject(autoSave=True) is True
    autoSavedRevision = project.index.indexRevision
    assert project.data.indexRevision == autoSavedRevision
    assert autoSavedRevision > savedRevision
    project.closeProject()

    # Simulate recovering after a crash.
    # The cached index.json on disk still reflects the state as of the
    # last full save, so it must be flagged as needing a rebuild.
    recovered = NWProject()
    assert recovered.openProject(fncPath, clearLock=True) is True
    assert recovered.index.indexRevision == savedRevision
    assert recovered.data.indexRevision == autoSavedRevision
    assert recovered.index.indexRebuild is True
    recovered.closeProject()


@pytest.mark.core
def testNWProject_Methods(monkeypatch, mockGUI, fncPath, mockRnd):
    """Test other project class methods and functions."""
    project = NWProject()
    buildTestProject(project, fncPath)

    # Project Name
    project.data.setName("  A Name ")
    assert project.data.name == "A Name"

    # Project Author
    project.data.setAuthor("  Jane\tDoe ")
    assert project.data.author == "Jane Doe"

    # Spell check
    project.setProjectChanged(False)
    project.data.setSpellCheck(True)
    project.data.setSpellCheck(False)
    assert project.projChanged is True
    assert project.projOpened > 0

    # Spell language
    project.setProjectChanged(False)
    assert project.data.spellLang is None
    project.data.setSpellLang(None)
    assert project.data.spellLang is None
    project.data.setSpellLang("None")  # Should be interpreted as None
    assert project.data.spellLang is None
    project.data.setSpellLang("en_GB")
    assert project.data.spellLang == "en_GB"
    assert project.projChanged is True

    # Project Language
    project.setProjectChanged(False)
    project.data.setLanguage("en")
    project.setProjectLang(None)
    assert project.data.language is None
    project.setProjectLang("en_GB")
    assert project.data.language == "en_GB"

    # Setting the same language again does nothing
    project.setProjectChanged(False)
    project.setProjectLang("en_GB")
    assert project.projChanged is False

    # A non-bool value does not change the project changed flag
    assert project.setProjectChanged("not a bool") is False  # type: ignore

    # Language Lookup
    assert project.localLookup(1) == "One"
    assert project.localLookup(10) == "Ten"

    # Set invalid language
    project.data.setLanguage("foo")
    project._loadProjectLocalisation()
    assert project.localLookup(1) == "One"
    assert project.localLookup(10) == "Ten"

    # Block reading language data
    project.data.setLanguage("en")
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        project._loadProjectLocalisation()
        assert project.localLookup(1) == "One"
        assert project.localLookup(10) == "Ten"

    # Last edited
    project.setProjectChanged(False)
    project._data.setLastHandle("0123456789abc", "editor")
    assert project._data.getLastHandle("editor") == "0123456789abc"
    assert project.projChanged

    # Last viewed
    project.setProjectChanged(False)
    project._data.setLastHandle("0123456789abc", "viewer")
    assert project._data.getLastHandle("viewer") == "0123456789abc"
    assert project.projChanged

    # Auto Replace
    project.setProjectChanged(False)
    project.data.setAutoReplace({"A": "B", "C": "D"})
    assert project.data.autoReplace == {"A": "B", "C": "D"}
    assert project.projChanged

    # Error Report
    SHARED.appendErrorMessage("Error 1")
    SHARED.appendErrorMessage("Error 2")
    project._reportErrors("Opps!")
    assert SHARED.lastAlert == ["Opps!", "Error 1<br><br>Error 2"]


@pytest.mark.core
def testNWProject_Backup(monkeypatch, mockGUI, fncPath, tstPaths):
    """Test the automated backup feature of the project class. The test
    creates a backup of the Minimal test project, and then unzips the
    backup file and checks that the project XML file is identical to
    the original file.
    """
    project = NWProject()

    # No Project
    assert project.backupProject(doNotify=False) is False

    buildTestProject(project, fncPath)

    # Invalid Settings
    # ================

    # Missing project name
    CONFIG._backupPath = tstPaths.tmpDir
    project.data.setName("")
    assert project.backupProject(doNotify=False) is False

    # Valid Settings
    # ==============
    CONFIG._backupPath = tstPaths.tmpDir
    project.data.setName("Test Minimal")

    # Can't make folder
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.mkdir", causeOSError)
        assert project.backupProject(doNotify=False) is False

    # Can't write archive
    with monkeypatch.context() as mp:
        mp.setattr("zipfile.ZipFile.write", causeOSError)
        assert project.backupProject(doNotify=False) is False

    # Test correct settings
    assert project.backupProject(doNotify=True) is True

    files = sorted((tstPaths.tmpDir / "Test Minimal").iterdir())
    assert len(files) in (1, 2)  # Sometimes 2 due to clock tick

    zipFile = files[0]
    assert zipFile.name.startswith("Test Minimal")
    assert zipFile.suffix == ".zip"

    # Extract the archive
    with ZipFile(tstPaths.tmpDir / "Test Minimal" / zipFile.name, mode="r") as inZip:
        inZip.extractall(tstPaths.tmpDir / "extract")

    # Check that the main project file was restored
    assert cmpFiles(fncPath / "nwProject.nwx", tstPaths.tmpDir / "extract" / "nwProject.nwx")

    # Test intervals
    fixedTime = 1783722600.0
    fixedLocal = datetime.fromtimestamp(fixedTime)
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.project.time", lambda *a, **k: fixedTime)
        CONFIG.backupInterval = "session"
        assert project.backupProject(doNotify=False) is True
        stamp = fixedLocal.strftime("%Y-%m-%d %H.%M.%S")
        assert (tstPaths.tmpDir / "Test Minimal" / f"Test Minimal {stamp}.zip").exists()

        CONFIG.backupInterval = "day"
        assert project.backupProject(doNotify=False) is True
        stamp = fixedLocal.strftime("%Y-%m-%d")
        assert (tstPaths.tmpDir / "Test Minimal" / f"Test Minimal {stamp}.zip").exists()

        CONFIG.backupInterval = "week"
        assert project.backupProject(doNotify=False) is True
        stamp = fixedLocal.strftime("%G-W%V")
        assert (tstPaths.tmpDir / "Test Minimal" / f"Test Minimal {stamp}.zip").exists()

        CONFIG.backupInterval = "month"
        assert project.backupProject(doNotify=False) is True
        stamp = fixedLocal.strftime("%Y-%m")
        assert (tstPaths.tmpDir / "Test Minimal" / f"Test Minimal {stamp}.zip").exists()
