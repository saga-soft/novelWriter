"""
novelWriter - Project Storage Tests
===================================

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

import json
import logging

from pathlib import Path
from zipfile import ZipFile

import pytest

from novelwriter import CONFIG
from novelwriter.constants import nwFiles
from novelwriter.core.document import ProjectDocument
from novelwriter.core.project import NWProject
from novelwriter.core.projectxml import ProjectXMLReader, ProjectXMLWriter
from novelwriter.core.storage import (
    ProjectStorage,
    ProjectStorageCreate,
    ProjectStorageOpen,
    _LegacyDocuments,
    _LegacyStorage,
)
from novelwriter.enum import nwItemClass, nwItemLayout

from tests.helpers import C, buildTestProject
from tests.mocked import causeOSError


class MockProject:
    """Test class for projects."""


@pytest.mark.core
def testProjectStorage_CreateNewProject(mockGUI, fncPath):
    """Test creating a project in a folder."""
    project = NWProject()

    # Create instance
    storage = ProjectStorage(project)

    # Check defaults
    assert storage.storagePath is None
    assert storage.runtimePath is None
    assert storage.contentPath is None
    assert storage._openMode == ProjectStorage.MODE_INACTIVE
    assert storage._ready is False

    # Check closed project return values
    assert storage.isOpen() is False
    assert storage.getXmlReader() is None
    assert storage.getXmlWriter() is None
    assert bool(storage.getDocument(C.hSceneDoc)) is False
    assert storage.getMetaFile("file") is None
    assert storage.scanContent() == []
    assert storage.getDocumentText(C.hSceneDoc) == ""

    # Cannot prepare a non-empty folder
    (fncPath / "foobar.txt").touch()
    assert storage.createNewProject(fncPath) == ProjectStorageCreate.NOT_EMPTY

    # Try creating in a non-existent subfolder instead
    assert storage.createNewProject(fncPath / "project1") == ProjectStorageCreate.READY
    assert (fncPath / "project1").is_dir()
    assert (fncPath / "project1" / "meta").is_dir()
    assert (fncPath / "project1" / "content").is_dir()

    # However, the parent folder must exist
    assert storage.createNewProject(fncPath / "foobar" / "project1") == ProjectStorageCreate.OS_ERROR
    assert isinstance(storage.exc, FileNotFoundError)

    project.closeProject()


@pytest.mark.core
def testProjectStorage_InitProjectStorage(monkeypatch, mockGUI, fncPath, mockRnd):
    """Test initialising a project in a folder."""
    project = NWProject()

    # Create instance
    storage = ProjectStorage(project)

    # Check defaults
    assert storage.storagePath is None
    assert storage.runtimePath is None
    assert storage.contentPath is None
    assert storage._openMode == ProjectStorage.MODE_INACTIVE
    assert storage._ready is False

    # Check closed project return values
    assert storage.isOpen() is False
    assert storage.getXmlReader() is None
    assert storage.getXmlWriter() is None
    assert bool(storage.getDocument(C.hSceneDoc)) is False
    assert storage.getMetaFile("file") is None
    assert storage.scanContent() == []

    # Create a new project
    buildTestProject(project, fncPath)

    # Init with the wrong file
    foo = fncPath / "foobar.txt"
    foo.touch()
    assert storage.initProjectStorage(fncPath / "foobar.txt") == ProjectStorageOpen.UNKOWN
    foo.unlink()
    storage._clearLockFile()
    storage.clear()

    # Init with the user's home dir
    assert storage.initProjectStorage(Path.home()) == ProjectStorageOpen.NOT_FOUND
    storage._clearLockFile()
    storage.clear()

    # Init with the project folder is OK
    assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.READY
    assert storage.runtimePath == fncPath
    assert storage.storagePath == fncPath
    assert storage.contentPath == fncPath / "content"
    assert storage._openMode == ProjectStorage.MODE_INPLACE
    storage._clearLockFile()
    storage.clear()

    # Init with the project main file is OK
    assert storage.initProjectStorage(fncPath / nwFiles.PROJ_FILE) == ProjectStorageOpen.READY
    assert storage.runtimePath == fncPath
    assert storage.storagePath == fncPath
    assert storage.contentPath == fncPath / "content"
    assert storage._openMode == ProjectStorage.MODE_INPLACE
    storage._clearLockFile()
    storage.clear()

    # Locking does nothing before the storage is ready
    unreadyStorage = ProjectStorage(MockProject())  # type: ignore
    unreadyStorage.lockSession()

    # Open twice, where second should fail due to lockfile
    # Note that locking is only possible after a successful open
    assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.READY
    storage.lockSession()
    assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.LOCKED
    assert isinstance(storage.lockStatus, list)
    assert len(storage.lockStatus) == 4

    # But open again with clear lock file flag set is OK
    assert storage.initProjectStorage(fncPath, clearLock=True) == ProjectStorageOpen.READY
    assert storage.lockStatus is None

    # We should now have access to project resources
    assert isinstance(storage.getXmlReader(), ProjectXMLReader)
    assert isinstance(storage.getXmlWriter(), ProjectXMLWriter)
    assert isinstance(storage.getDocument(C.hSceneDoc), ProjectDocument)
    assert repr(storage.getDocument(C.hSceneDoc)) == f"<ProjectDocument handle={C.hSceneDoc}>"

    # We can directly access the content of a document
    assert storage.getDocumentText(C.hSceneDoc) == "### New Scene\n\n"

    project.closeProject()


@pytest.mark.core
def testProjectStorage_InitProjectStorage_Invalid(monkeypatch, mockGUI, fncPath):
    """Test initialising a project in an invalid folder."""
    project = NWProject()

    # Create instance
    storage = ProjectStorage(project)

    # Check defaults
    assert storage.storagePath is None
    assert storage.runtimePath is None
    assert storage.contentPath is None
    assert storage._openMode == ProjectStorage.MODE_INACTIVE
    assert storage._ready is False

    # Check closed project return values
    assert storage.isOpen() is False
    assert storage.getXmlReader() is None
    assert storage.getXmlWriter() is None
    assert bool(storage.getDocument(C.hSceneDoc)) is False
    assert storage.getMetaFile("file") is None
    assert storage.scanContent() == []

    # Populate folder with invalid files
    (fncPath / "meta").touch()  # These are now files but should be folders
    (fncPath / "content").touch()  # These are now files but should be folders

    # Try opening the folder, but there is no project file
    assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.NOT_FOUND

    # Add the project file, and we should now fail on the folders
    (fncPath / nwFiles.PROJ_FILE).touch()
    assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.FAILED

    # Remove the files blocking the folders, but make the legacy storage scan fail
    (fncPath / "meta").unlink()
    (fncPath / "content").unlink()
    with monkeypatch.context() as mp:
        mp.setattr(_LegacyStorage, "deprecatedFiles", causeOSError)
        assert storage.initProjectStorage(fncPath) == ProjectStorageOpen.FAILED

    project.closeProject()


@pytest.mark.core
def testProjectStorage_LockFile(monkeypatch, fncPath):
    """Test the project lock file."""
    monkeypatch.setattr("novelwriter.core.storage.time", lambda: 1000.0)

    storage = ProjectStorage(MockProject())  # type: ignore
    assert storage.isOpen() is False

    # Project not open, so cannot read/write lock file
    assert storage._readLockFile() is None
    assert storage._writeLockFile() is False
    assert storage._clearLockFile() is False

    # Set a path to work with
    lockFilePath = fncPath / nwFiles.PROJ_LOCK
    storage._lockFilePath = lockFilePath

    # Path is set, but there is no lockfile
    storage._readLockFile()
    assert storage.lockStatus is None

    # Write lockfile fails
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.write_text", causeOSError)
        assert storage._writeLockFile() is False
        assert not lockFilePath.exists()

    # Successful write
    assert storage._writeLockFile() is True
    assert lockFilePath.exists()
    assert lockFilePath.read_text().split(";")[3] == "1000"

    # Read lockfile fails
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.read_text", causeOSError)
        storage._readLockFile()
        assert storage.lockStatus == ["ERROR", "ERROR", "ERROR", "ERROR"]
        assert lockFilePath.exists()

    # Successful read
    storage._readLockFile()
    assert storage.lockStatus == [
        CONFIG.hostName,
        CONFIG.osType,
        CONFIG.kernelVer,
        "1000",
    ]

    # Write an invalid lockfile
    lockFilePath.write_text("a;b;c")
    storage._readLockFile()
    assert storage.lockStatus is None

    # Fail to remove lockfile
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.unlink", causeOSError)
        assert storage._clearLockFile() is False
        assert lockFilePath.exists()

    # Successful remove
    assert storage._clearLockFile() is True
    assert not lockFilePath.exists()


@pytest.mark.core
def testProjectStorage_ZipIt(monkeypatch, mockGUI, fncPath, tstPaths, mockRnd):
    """Test making a zip archive of a project."""
    zipFile = tstPaths.tmpDir / "project.zip"

    project = NWProject()
    storage = project.storage
    assert storage.zipIt(zipFile) is False

    # Make a project
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Fail to create archive
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ZipFile.write", causeOSError)
        assert storage.zipIt(zipFile) is False

    # Add a stray file that should not be included
    strayFile = fncPath / "content" / "not-a-handle.txt"
    strayFile.write_text("stray")

    # Create archive
    assert storage.zipIt(zipFile) is True

    # Check content
    with ZipFile(zipFile, mode="r") as archive:
        names = archive.namelist()
        assert nwFiles.PROJ_FILE in names
        assert f"meta/{nwFiles.OPTS_FILE}" in names
        assert f"meta/{nwFiles.INDEX_FILE}" in names
        assert f"content/{C.hTitlePage}.md" in names
        assert f"content/{C.hChapterDoc}.md" in names
        assert f"content/{C.hSceneDoc}.md" in names
        assert "content/not-a-handle.txt" not in names

    project.closeProject()


@pytest.mark.core
def testProjectStorage_LegacyDataFolder(monkeypatch, fncPath):
    """Test project file format 1.0 folder structure conversion."""
    project = MockProject()
    storage = ProjectStorage(project)  # type: ignore
    assert storage.isOpen() is False
    storage._runtimePath = fncPath
    (fncPath / nwFiles.PROJ_FILE).touch()
    storage.initProjectStorage(fncPath)
    legacy = _LegacyStorage(project)  # type: ignore

    data = []
    files = []
    for c in "0123456789abcdefX":
        dataDir = fncPath / f"data_{c}"
        dataDir.mkdir()
        data.append(dataDir)

        nwdFile = dataDir / f"00000000000{c}_main.nwd"
        bakFile = dataDir / f"00000000000{c}_main.bak"
        nwdFile.write_text("#")
        bakFile.write_text("#")
        files.append(nwdFile)
        files.append(bakFile)

    for item in files:
        assert item.exists()

    # Pollute folder 7 and 8
    (data[7] / "stuff.txt").write_text("foo")
    (data[8] / "bar").mkdir()

    # Process folders
    for i in range(9):
        legacy.legacyDataFolder(fncPath, data[i])

    # Files form 0 to 8 should now be in content
    for i in range(9):
        assert (fncPath / "content" / f"{i}00000000000{i}.nwd").exists()

    # Folders 0 to 6 should be deleted
    for i in range(7):
        assert not data[i].exists()

    # While 7 and 8 remain
    assert data[7].exists()
    assert data[8].exists()

    # So does folder X, which is invalid
    legacy.legacyDataFolder(fncPath, data[16])
    assert data[16].exists()

    # Fail cleanup of folder 9
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.rename", causeOSError)
        mp.setattr("pathlib.Path.unlink", causeOSError)
        legacy.legacyDataFolder(fncPath, data[9])
        assert data[9].exists()
        assert not (fncPath / "content" / "9000000000009.nwd").exists()

    # Run the remaining through the prepare storage call, which finds
    # the moved .nwd files, but does not convert them yet
    assert storage.initProjectStorage(fncPath, clearLock=True) == ProjectStorageOpen.READY
    assert storage.hasBreakingChanges() is True
    for c in "0123456789abcdef":
        assert (fncPath / "content" / f"{c}00000000000{c}.nwd").exists()


@pytest.mark.core
def testProjectStorage_FindOldDocuments(fncPath):
    """Test scanning the content folder for old .nwd document files."""
    project = MockProject()
    storage = ProjectStorage(project)  # type: ignore
    storage._runtimePath = fncPath
    (fncPath / nwFiles.PROJ_FILE).touch()
    storage.initProjectStorage(fncPath)
    legacy = _LegacyStorage(project)  # type: ignore

    content = fncPath / "content"
    nwdFile = content / f"{C.hSceneDoc}.nwd"
    nwdFile.write_text("### Text\n", encoding="utf-8")
    (content / f"{C.hChapterDoc}.md").write_text("### Text\n", encoding="utf-8")
    (content / "folder.nwd").mkdir()

    assert legacy.findOldDocuments(content) == [nwdFile]


@pytest.mark.core
def testProjectStorage_RunPostXMLTasks(monkeypatch, fncPath):
    """Test running the post-XML-load document conversion tasks."""
    project = MockProject()
    storage = ProjectStorage(project)  # type: ignore
    storage._runtimePath = fncPath
    (fncPath / nwFiles.PROJ_FILE).touch()
    storage.initProjectStorage(fncPath)

    # No old documents found, so there is nothing to do
    assert storage.hasBreakingChanges() is False
    assert storage.runPostXMLTasks() is True

    # Add an old-format document and re-scan for it
    content = fncPath / "content"
    nwdFile = content / f"{C.hSceneDoc}.nwd"
    nwdFile.write_text("### Text\n", encoding="utf-8")
    storage._oldDocuments = _LegacyStorage(project).findOldDocuments(content)  # type: ignore
    assert storage.hasBreakingChanges() is True

    # A successful conversion
    assert storage.runPostXMLTasks() is True
    assert not nwdFile.exists()
    assert (content / f"{C.hSceneDoc}.md").exists()

    # A failed conversion records the exception
    storage._oldDocuments = [nwdFile]
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage._LegacyDocuments.convertDocuments", causeOSError)
        assert storage.runPostXMLTasks() is False
        assert isinstance(storage.exc, OSError)


@pytest.mark.core
def testLegacyDocuments_ConvertDocuments(monkeypatch, fncPath):
    """Test conversion of old .nwd document files to .md with a TOML header."""
    project = MockProject()
    storage = ProjectStorage(project)  # type: ignore
    storage._runtimePath = fncPath
    (fncPath / nwFiles.PROJ_FILE).touch()
    storage.initProjectStorage(fncPath)
    legacy = _LegacyDocuments(project)  # type: ignore

    content = fncPath / "content"

    # A regular old-format document with a full meta header
    nwdFile = content / f"{C.hSceneDoc}.nwd"
    nwdFile.write_text(
        (
            "%%~name: Scene One\n"
            f"%%~path: {C.hChapterDir}/{C.hSceneDoc}\n"
            "%%~kind: NOVEL/DOCUMENT\n"
            "%%~hash: abc123\n"
            "%%~date: 2020-01-01 00:00:00/2020-01-02 00:00:00\n"
            "### Scene One\n\nSome text.\n"
        ),
        encoding="utf-8",
    )

    legacy.convertDocuments([nwdFile])

    assert not nwdFile.exists()
    mdFile = content / f"{C.hSceneDoc}.md"
    assert mdFile.read_text(encoding="utf-8") == (
        "+++\n"
        'name = "Scene One"\n'
        f'parent = "{C.hChapterDir}"\n'
        f'handle = "{C.hSceneDoc}"\n'
        'class = "NOVEL"\n'
        'layout = "DOCUMENT"\n'
        'textHash = "abc123"\n'
        'createdDate = "2020-01-01 00:00:00"\n'
        'updatedDate = "2020-01-02 00:00:00"\n'
        "+++\n"
        "### Scene One\n\nSome text.\n"
    )

    # A document with more than 10 meta lines never reaches the body
    # text, but is still converted
    longFile = content / f"{C.hTitlePage}.nwd"
    longFile.write_text("".join(f"%%~junk{i}: value\n" for i in range(12)), encoding="utf-8")
    legacy.convertDocuments([longFile])
    assert not longFile.exists()
    assert (content / f"{C.hTitlePage}.md").exists()

    # A path that is not a .nwd file is ignored
    txtFile = content / "not-a-doc.txt"
    txtFile.write_text("stuff", encoding="utf-8")
    legacy.convertDocuments([txtFile])
    assert txtFile.exists()

    # If conversion fails, the file is renamed to .md as a fallback so
    # it can still be opened, even with its raw, unconverted content
    badFile = content / f"{C.hChapterDoc}.nwd"
    rawText = "%%~name: Bad\n### Text\n"
    badFile.write_text(rawText, encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.write_text", causeOSError)
        legacy.convertDocuments([badFile])
    assert not badFile.exists()
    fallbackFile = content / f"{C.hChapterDoc}.md"
    assert fallbackFile.read_text(encoding="utf-8") == rawText

    # A partial output file left behind by the failed write does not
    # block the fallback from overwriting it (replace, not rename, so
    # this also works on platforms that don't allow renaming onto an
    # existing file, e.g. Windows)
    fallbackFile.unlink()
    badFile.write_text(rawText, encoding="utf-8")
    fallbackFile.write_text("partial junk", encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.write_text", causeOSError)
        legacy.convertDocuments([badFile])
    assert not badFile.exists()
    assert fallbackFile.read_text(encoding="utf-8") == rawText

    # If the fallback rename also fails, there is nothing more that can
    # be done, so the exception is left to propagate to the caller
    fallbackFile.unlink()
    badFile.write_text(rawText, encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.write_text", causeOSError)
        mp.setattr("pathlib.Path.replace", causeOSError)
        with pytest.raises(OSError, match="Mock OSError"):
            legacy.convertDocuments([badFile])
    assert badFile.exists()
    assert not fallbackFile.exists()


@pytest.mark.core
def testLegacyDocuments_ParseOldDocumentMeta(caplog):
    """Test parsing of individual old-format meta data lines."""
    caplog.set_level(logging.DEBUG, logger="novelwriter")
    legacy = _LegacyDocuments(MockProject())  # type: ignore

    # Name
    assert legacy._parseOldDocumentMeta(["%%~name: Test File\n"]) == {"name": "Test File"}

    # Name: control characters from an old, unvalidated file are cleaned,
    # as they would otherwise end up unescaped in the new TOML header
    assert legacy._parseOldDocumentMeta(["%%~name: Bad\x1bTitle\n"]) == {"name": "BadTitle"}

    # Path: valid parent and handle
    meta = legacy._parseOldDocumentMeta([f"%%~path: {C.hChapterDir}/{C.hSceneDoc}\n"])
    assert meta == {"parent": C.hChapterDir, "handle": C.hSceneDoc}

    # Path: malformed value is ignored entirely
    assert legacy._parseOldDocumentMeta(["%%~path: onlyonepart\n"]) == {}

    # Path: invalid handles are dropped individually
    assert legacy._parseOldDocumentMeta(["%%~path: notahandle/alsonot\n"]) == {}

    # Kind: valid class and layout
    meta = legacy._parseOldDocumentMeta(["%%~kind: NOVEL/DOCUMENT\n"])
    assert meta == {"class": nwItemClass.NOVEL, "layout": nwItemLayout.DOCUMENT}

    # Kind: malformed value is ignored entirely
    assert legacy._parseOldDocumentMeta(["%%~kind: onlyonepart\n"]) == {}

    # Kind: unknown class/layout names are dropped individually
    assert legacy._parseOldDocumentMeta(["%%~kind: BADCLASS/BADLAYOUT\n"]) == {}

    # Hash
    assert legacy._parseOldDocumentMeta(["%%~hash: abc123\n"]) == {"textHash": "abc123"}

    # Date: valid
    meta = legacy._parseOldDocumentMeta(["%%~date: 2020-01-01 00:00:00/2020-01-02 00:00:00\n"])
    assert meta == {"createdDate": "2020-01-01 00:00:00", "updatedDate": "2020-01-02 00:00:00"}

    # Date: malformed value is ignored entirely
    assert legacy._parseOldDocumentMeta(["%%~date: onlyonepart\n"]) == {}

    # Unknown meta lines are logged and otherwise ignored
    assert legacy._parseOldDocumentMeta(["%%~unknown: stuff\n"]) == {}
    assert "Unknown meta data" in caplog.text


@pytest.mark.core
def testProjectStorage_DeprecatedFiles(monkeypatch, fncPath):
    """Test cleanup of deprecated files."""
    project = MockProject()
    storage = ProjectStorage(project)  # type: ignore
    assert storage.isOpen() is False
    storage._runtimePath = fncPath
    (fncPath / nwFiles.PROJ_FILE).touch()
    storage.initProjectStorage(fncPath)
    legacy = _LegacyStorage(project)  # type: ignore

    # Files/Folders to be Deleted or Renamed
    # ======================================

    remove = [
        fncPath / "meta" / "tagsIndex.json",
        fncPath / "meta" / "mainOptions.json",
        fncPath / "meta" / "exportOptions.json",
        fncPath / "meta" / "outlineOptions.json",
        fncPath / "meta" / "timelineOptions.json",
        fncPath / "meta" / "docMergeOptions.json",
        fncPath / "meta" / "sessionLogOptions.json",
        fncPath / "cache" / "prevBuild.json",
        fncPath / "ToC.json",
    ]
    (fncPath / "cache").mkdir()
    for depFile in remove:
        depFile.write_text("foo")
        assert depFile.exists()

    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.unlink", causeOSError)
        legacy.deprecatedFiles(fncPath)
        for depFile in remove:
            assert depFile.exists()

    legacy.deprecatedFiles(fncPath)
    for depFile in remove:
        assert not depFile.exists()


@pytest.mark.core
def testProjectStorage_OldFormatConvert(monkeypatch, mockGUI, fncPath):
    """Test cleanup of deprecated files that needs to be converted."""
    project = NWProject()
    buildTestProject(project, fncPath)
    legacy = _LegacyStorage(project)

    # Word List
    wordListOld: Path = fncPath / "meta" / "wordlist.txt"
    wordListNew: Path = fncPath / "meta" / nwFiles.DICT_FILE

    wordListOld.write_text(("word_a\n\nword_b\nword_c\n"), encoding="utf-8")

    assert wordListOld.exists() is True
    assert wordListNew.exists() is False

    # Log File
    sessLogOld: Path = fncPath / "meta" / "sessionStats.log"
    sessLogNew: Path = fncPath / "meta" / nwFiles.SESS_FILE

    sessLogOld.write_text(
        (
            "# Offset 150\n"
            "# Start Time         End Time                Novel     Notes    Idle\n"
            "2021-02-02 02:02:02  2021-02-02 03:03:03       200       200      10\n"
            "2021-03-03 03:03:03  2021-03-03 04:04:04       300       300      20\n"
        ),
        encoding="utf-8",
    )

    assert sessLogOld.exists() is True
    assert sessLogNew.exists() is False

    # Check Failure
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        legacy.deprecatedFiles(fncPath)
        assert wordListOld.exists() is True
        assert wordListNew.exists() is False
        assert sessLogOld.exists() is True
        assert sessLogNew.exists() is False

    # Check Success
    legacy.deprecatedFiles(fncPath)
    assert wordListOld.exists() is False
    assert wordListNew.exists() is True
    assert sessLogOld.exists() is False
    assert sessLogNew.exists() is True

    # Check Word List
    data = json.loads(wordListNew.read_text(encoding="utf-8"))
    assert "word_a" in data["novelWriter.userDict"]
    assert "word_b" in data["novelWriter.userDict"]
    assert "word_c" in data["novelWriter.userDict"]

    # Check Session Log
    data = list(project.session.iterRecords())
    assert data[0] == {"type": "initial", "offset": 150}
    assert data[1] == {
        "type": "record",
        "start": "2021-02-02 02:02:02",
        "end": "2021-02-02 03:03:03",
        "novel": 200,
        "notes": 200,
        "cnovel": 0,
        "cnotes": 0,
        "idle": 10,
    }
    assert data[2] == {
        "type": "record",
        "start": "2021-03-03 03:03:03",
        "end": "2021-03-03 04:04:04",
        "novel": 300,
        "notes": 300,
        "cnovel": 0,
        "cnotes": 0,
        "idle": 20,
    }
