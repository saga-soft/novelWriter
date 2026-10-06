"""
novelWriter - Manuscript Build Settings Tests
=============================================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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
import shutil
import uuid

from pathlib import Path

import pytest

from novelwriter import CONFIG
from novelwriter.constants import nwFiles, nwHeadFmt
from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt, nwItemClass
from novelwriter.manuscript.buildsettings import BuildCollection, BuildSettings, FilterMode

from tests.helpers import C, buildTestProject
from tests.mocked import causeOSError


def isUUID(value):
    """Check if a value is a valid UUID object."""
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False


@pytest.mark.core
def testBuildSettings_ClassAttributes(fncPath: Path):
    """Test the BuildSettings class attributes."""
    build = BuildSettings()
    assert build.changed is False

    # Name is always converted to string
    build.setName(None)  # type: ignore
    assert build.name == "None"

    build.setName("Test Build")
    assert build.name == "Test Build"

    # Only valid UUIDs are accepted, anything else generates a new UUID
    build.setBuildID("5cf45d24-f496-42c9-8733-529a9e52a62b")
    assert build.buildID == "5cf45d24-f496-42c9-8733-529a9e52a62b"

    build.setBuildID(None)  # type: ignore
    assert build.buildID != "5cf45d24-f496-42c9-8733-529a9e52a62b"
    assert isUUID(build.buildID)

    build.setBuildID("qcf45d24-f496-42c9-8733-529a9e52a62b")
    assert build.buildID != "qcf45d24-f496-42c9-8733-529a9e52a62b"
    assert isUUID(build.buildID)

    # Setting the same UUID again does nothing
    sameID = build.buildID
    build.setBuildID(sameID)
    assert build.buildID == sameID

    # Order is only set if the value is an integer
    build.setOrder(3)
    assert build.order == 3
    build.setOrder("not an int")  # type: ignore
    assert build.order == 3

    # Allow root only accepts True or False
    build.setAllowRoot(C.hCharRoot, None)  # type: ignore
    assert build.changed is False

    # Last path must be valid, if not it defaults to $HOME
    build.setLastBuildPath("/path/to/nowhere")
    assert build.lastBuildPath == CONFIG.homePath()

    build.setLastBuildPath(None)
    assert build.lastBuildPath == CONFIG.homePath()

    (fncPath / "test.txt").write_text("foobar")
    build.setLastBuildPath(fncPath / "test.txt")  # Can't be a file
    assert build.lastBuildPath == CONFIG.homePath()

    build.setLastBuildPath(fncPath)
    assert build.lastBuildPath == fncPath

    build.setLastBuildPath(str(fncPath))  # String paths are also ok
    assert build.lastBuildPath == fncPath

    # Last path no longer exists -> fallback to $HOME
    testDir = fncPath / "test_dir"
    testDir.mkdir()
    build.setLastBuildPath(testDir)
    assert build.lastBuildPath == testDir
    testDir.rmdir()
    assert build.lastBuildPath == CONFIG.homePath()

    # Last build name
    build.setLastBuildName(None)  # type: ignore
    assert build.lastBuildName == "None"

    build.setLastBuildName("\tBuild Name    ")
    assert build.lastBuildName == "Build Name"

    # Last build format
    build.setLastFormat(None)  # type: ignore
    assert build.lastFormat == nwBuildFmt.ODT  # Default value

    build.setLastFormat(nwBuildFmt.FODT)
    assert build.lastFormat == nwBuildFmt.FODT

    # Changes are recorded
    assert build.changed is True
    build.resetChangedState()
    assert build.changed is False

    # Set some sensible values
    build.setName("Test Build")
    build.setBuildID("5cf45d24-f496-42c9-8733-529a9e52a62b")
    build.setLastBuildPath(fncPath)
    build.setLastBuildName("Build Name")
    build.setLastFormat(nwBuildFmt.HTML)

    # Pack the values
    data = build.pack()
    assert data["name"] == "Test Build"
    assert data["uuid"] == "5cf45d24-f496-42c9-8733-529a9e52a62b"
    assert data["path"] == str(fncPath)
    assert data["build"] == "Build Name"
    assert data["format"] == nwBuildFmt.HTML.name

    # Unpack into new object
    another = BuildSettings()
    another.unpack(data)
    more = another.pack()
    assert more["name"] == "Test Build"
    assert more["uuid"] == "5cf45d24-f496-42c9-8733-529a9e52a62b"
    assert more["path"] == str(fncPath)
    assert more["build"] == "Build Name"
    assert more["format"] == nwBuildFmt.HTML.name

    # Malformed data is ignored
    malformed = BuildSettings()
    malformed.unpack({
        "content": {
            "included": "not a list",
            "excluded": None,
            "skipRoot": 123,
        },
        "settings": ["not", "a", "dict"],
    })
    assert malformed._included == set()
    assert malformed._excluded == set()
    assert malformed._skipRoot == set()


@pytest.mark.core
def testBuildSettings_BuildValues():
    """Test BuildSettings get/set of build values."""
    build = BuildSettings()

    strSetting = "headings.fmtPart"
    intSetting = "doc.pageCountOffset"
    boolSetting = "filter.includeNovel"
    floatSetting = "format.lineHeight"

    # Invalid setting
    build.setValue("foo", "bar")
    assert build.getStr("foo") == "None"

    # Value must be correct type
    build.setValue(strSetting, 15)
    assert build.getStr(strSetting) == nwHeadFmt.TITLE
    build.setValue(intSetting, 15.0)
    assert build.getInt(intSetting) == 0
    build.setValue(floatSetting, 15)
    assert build.getFloat(floatSetting) == 1.15
    build.setValue(boolSetting, "string")
    assert build.getBool(boolSetting) is True

    # Check string values
    build.setValue(strSetting, "foobar")
    assert build.getStr(strSetting) == "foobar"
    assert build.getInt(strSetting) == 0
    assert build.getBool(strSetting) is True
    assert build.getFloat(strSetting) == 0.0

    # Check int values
    build.setValue(intSetting, 42)
    assert build.getStr(intSetting) == "42"
    assert build.getInt(intSetting) == 42
    assert build.getBool(intSetting) is True
    assert build.getFloat(intSetting) == 42.0

    # Check bool values
    build.setValue(boolSetting, True)
    assert build.getStr(boolSetting) == "True"
    assert build.getInt(boolSetting) == 1
    assert build.getBool(boolSetting) is True
    assert build.getFloat(boolSetting) == 1.0

    # Check float values
    build.setValue(floatSetting, 2.5)
    assert build.getStr(floatSetting) == "2.5"
    assert build.getInt(floatSetting) == 2
    assert build.getBool(floatSetting) is True
    assert build.getFloat(floatSetting) == 2.5

    # Check labels
    assert build.getLabel(strSetting) == "Partition format"
    assert BuildSettings.getLabel(strSetting) == "Partition format"

    # Pack the values
    data = build.pack()
    assert data["settings"][strSetting] == "foobar"
    assert data["settings"][intSetting] == 42
    assert data["settings"][boolSetting] is True
    assert data["settings"][floatSetting] == 2.5

    # Unpack into new object
    another = BuildSettings()
    another.unpack(data)
    more = another.pack()
    assert more["settings"][strSetting] == "foobar"
    assert more["settings"][intSetting] == 42
    assert more["settings"][boolSetting] is True
    assert more["settings"][floatSetting] == 2.5

    # Invalid keys and values in the settings dict are skipped
    skipped = BuildSettings()
    skipped.unpack({"settings": {123: "value", strSetting: object()}})
    assert skipped.getStr(strSetting) == nwHeadFmt.TITLE


@pytest.mark.core
def testBuildSettings_Filters(mockGUI, fncPath: Path, mockRnd):
    """Test filters for project items."""
    project = NWProject()
    buildTestProject(project, fncPath)
    build = BuildSettings()

    # Add some more items
    hArchRoot = project.newRoot(nwItemClass.ARCHIVE)
    hPlotDoc = project.newFile("Main Plot", C.hPlotRoot)
    hCharDoc = project.newFile("Jane Doe", C.hCharRoot)

    # With no changes
    assert build.isRootAllowed(C.hNovelRoot) is True
    assert build.isRootAllowed(C.hPlotRoot) is True
    assert build.isRootAllowed(C.hCharRoot) is True
    assert build.isRootAllowed(C.hWorldRoot) is True

    assert build.buildItemFilter(project, withRoots=False) == {
        C.hNovelRoot: (False, FilterMode.SKIPPED),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.FILTERED),
        hCharDoc: (False, FilterMode.FILTERED),
    }

    # Enable notes and roots
    build.setValue("filter.includeNotes", True)
    assert build.buildItemFilter(project, withRoots=True) == {
        C.hNovelRoot: (True, FilterMode.ROOT),
        C.hPlotRoot: (True, FilterMode.ROOT),
        C.hCharRoot: (True, FilterMode.ROOT),
        C.hWorldRoot: (False, FilterMode.SKIPPED),  # World folder is empty
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (True, FilterMode.FILTERED),
        hCharDoc: (True, FilterMode.FILTERED),
    }

    # Skip plot and char roots
    build.setValue("filter.includeNotes", True)
    build.setAllowRoot(C.hPlotRoot, False)
    build.setAllowRoot(C.hCharRoot, False)
    assert build.isRootAllowed(C.hNovelRoot) is True
    assert build.isRootAllowed(C.hPlotRoot) is False
    assert build.isRootAllowed(C.hCharRoot) is False
    assert build.isRootAllowed(C.hWorldRoot) is True
    assert build.buildItemFilter(project, withRoots=True) == {
        C.hNovelRoot: (True, FilterMode.ROOT),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.SKIPPED),  # Now also skipped since in plot
        hCharDoc: (False, FilterMode.SKIPPED),  # Now also skipped since in char
    }

    # Enable char root again, but exclude char doc and scene doc
    build.setValue("filter.includeNotes", True)
    build.setAllowRoot(C.hPlotRoot, False)
    build.setAllowRoot(C.hCharRoot, True)
    build.setExcluded(C.hSceneDoc)
    build.setExcluded(hCharDoc)  # type: ignore
    assert build.isRootAllowed(C.hNovelRoot) is True
    assert build.isRootAllowed(C.hPlotRoot) is False
    assert build.isRootAllowed(C.hCharRoot) is True
    assert build.isRootAllowed(C.hWorldRoot) is True
    assert build.buildItemFilter(project, withRoots=True) == {
        C.hNovelRoot: (True, FilterMode.ROOT),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        C.hCharRoot: (False, FilterMode.SKIPPED),  # Is skipped anyway since doc is skipped
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (False, FilterMode.EXCLUDED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.EXCLUDED),
    }

    # Disable notes, but include char doc
    build.setValue("filter.includeNotes", False)
    build.setAllowRoot(C.hPlotRoot, False)
    build.setAllowRoot(C.hCharRoot, True)
    build.setExcluded(C.hSceneDoc)
    build.setIncluded(hCharDoc)  # type: ignore
    assert build.isRootAllowed(C.hNovelRoot) is True
    assert build.isRootAllowed(C.hPlotRoot) is False
    assert build.isRootAllowed(C.hCharRoot) is True
    assert build.isRootAllowed(C.hWorldRoot) is True
    assert build.buildItemFilter(project, withRoots=True) == {
        C.hNovelRoot: (True, FilterMode.ROOT),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        C.hCharRoot: (True, FilterMode.ROOT),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (False, FilterMode.EXCLUDED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.SKIPPED),
        hCharDoc: (True, FilterMode.INCLUDED),
    }

    # Set everything back to filtered
    build.setValue("filter.includeNotes", False)
    build.setAllowRoot(C.hPlotRoot, False)
    build.setAllowRoot(C.hCharRoot, True)
    build.setFiltered(C.hSceneDoc)
    build.setFiltered(hCharDoc)  # type: ignore
    assert build.isRootAllowed(C.hNovelRoot) is True
    assert build.isRootAllowed(C.hPlotRoot) is False
    assert build.isRootAllowed(C.hCharRoot) is True
    assert build.isRootAllowed(C.hWorldRoot) is True
    assert build.buildItemFilter(project, withRoots=True) == {
        C.hNovelRoot: (True, FilterMode.ROOT),
        C.hPlotRoot: (False, FilterMode.SKIPPED),
        C.hCharRoot: (False, FilterMode.SKIPPED),
        C.hWorldRoot: (False, FilterMode.SKIPPED),
        C.hTitlePage: (True, FilterMode.FILTERED),
        C.hChapterDir: (False, FilterMode.SKIPPED),
        C.hChapterDoc: (True, FilterMode.FILTERED),
        C.hSceneDoc: (True, FilterMode.FILTERED),
        hArchRoot: (False, FilterMode.SKIPPED),
        hPlotDoc: (False, FilterMode.SKIPPED),
        hCharDoc: (False, FilterMode.FILTERED),
    }

    # No valid project provided
    assert build.buildItemFilter(None) == {}  # type: ignore


@pytest.mark.core
def testBuildSettings_Collection(monkeypatch, mockGUI, fncPath: Path, mockRnd):
    """Test the collections class for builds."""
    project = NWProject()
    buildTestProject(project, fncPath)
    buildsFile = project.storage.getMetaFile(nwFiles.BUILDS_FILE)
    assert isinstance(buildsFile, Path)

    # No initial builds in a fresh project
    builds = BuildCollection(project)
    assert len(builds) == 0
    assert not buildsFile.exists()
    assert builds.lastBuild == ""
    assert builds.defaultBuild == ""

    # Create a default build
    buildOne = BuildSettings()
    buildOne.setName("Build One")
    buildIDOne = buildOne.buildID

    # Check that invalid type is handled
    builds.setBuild(None)  # type: ignore
    assert len(builds) == 0
    assert not buildsFile.exists()
    assert builds.getBuild(buildIDOne) is None

    # Add the build
    builds.setBuild(buildOne)
    assert len(builds) == 1
    assert buildsFile.exists()
    assert builds.getBuild(buildIDOne).buildID == buildIDOne  # type: ignore

    # Create another build
    buildTwo = BuildSettings()
    buildTwo.setName("Build Two")
    buildIDTwo = buildTwo.buildID

    # Check that we can extract info about the builds
    builds.setBuild(buildTwo)
    assert len(builds) == 2
    assert buildsFile.exists()
    assert builds.getBuild(buildIDTwo).buildID == buildIDTwo  # type: ignore
    assert list(builds.builds()) == [
        (buildIDOne, "Build One"),
        (buildIDTwo, "Build Two"),
    ]

    # Check the file content
    data = json.loads(buildsFile.read_text(encoding="utf-8"))
    assert list(data["novelWriter.builds"].keys()) == ["lastBuild", "defaultBuild", buildIDOne, buildIDTwo]

    # Remove a build
    builds.removeBuild(buildIDOne)
    assert builds.getBuild(buildIDOne) is None
    assert list(builds.builds()) == [
        (buildIDTwo, "Build Two"),
    ]

    # Check the file content
    data = json.loads(buildsFile.read_text(encoding="utf-8"))
    assert list(data["novelWriter.builds"].keys()) == ["lastBuild", "defaultBuild", buildIDTwo]
    builds.setBuild(buildOne)
    assert list(builds.builds()) == [
        (buildIDTwo, "Build Two"),
        (buildIDOne, "Build One"),
    ]
    builds.setBuildsState(buildIDOne, [buildIDTwo, buildIDOne, "not-a-real-id"])
    builds.setDefaultBuild(buildIDTwo)

    # Setting the same default build again does nothing new
    builds.setDefaultBuild(buildIDTwo)

    # Check errors: No valid path
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert builds._loadCollection() is False
        assert builds._saveCollection() is False

    # Check errors: I/O error
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert builds._loadCollection() is False
        assert builds._saveCollection() is False

    # Check errors: Can't parse json file
    shutil.copy(buildsFile, buildsFile.with_suffix(".bak"))
    buildsFile.write_text("foobar")
    assert builds._loadCollection() is False

    # Check errors: Valid json file, but list instead of object
    buildsFile.write_text("[]")
    assert builds._loadCollection() is False

    # Check errors: Valid json object, but no builds entry
    buildsFile.write_text("{}")
    assert builds._loadCollection() is False
    buildsFile.unlink()
    shutil.copy(buildsFile.with_suffix(".bak"), buildsFile)

    # Load builds file into new object
    another = BuildCollection(project)
    assert list(another.builds()) == [
        (buildIDTwo, "Build Two"),
        (buildIDOne, "Build One"),
    ]
    assert another.lastBuild == buildIDOne
    assert another.defaultBuild == buildIDTwo

    # Entries that aren't objects are skipped
    data = json.loads(buildsFile.read_text(encoding="utf-8"))
    data["novelWriter.builds"]["garbage"] = "not a build entry"
    buildsFile.write_text(json.dumps(data), encoding="utf-8")

    garbageLoaded = BuildCollection(project)
    assert list(garbageLoaded.builds()) == [
        (buildIDTwo, "Build Two"),
        (buildIDOne, "Build One"),
    ]


@pytest.mark.core
def testBuildSettings_Duplicate(monkeypatch, mockGUI, fncPath: Path, mockRnd):
    """Test duplicating builds."""
    project = NWProject()
    buildTestProject(project, fncPath)
    buildsFile = project.storage.getMetaFile(nwFiles.BUILDS_FILE)
    assert isinstance(buildsFile, Path)

    # No initial builds in a fresh project
    builds = BuildCollection(project)
    assert len(builds) == 0
    assert not buildsFile.exists()
    assert builds.lastBuild == ""
    assert builds.defaultBuild == ""

    # Create a default build
    buildOne = BuildSettings()
    buildOne.setName("Test Build")
    buildOne.setValue("headings.fmtScene", nwHeadFmt.TITLE)
    buildOne.setValue("headings.fmtAltScene", nwHeadFmt.TITLE)
    buildOne.setValue("headings.fmtSection", nwHeadFmt.TITLE)

    # Copy it
    buildTwo = BuildSettings().duplicate(buildOne)
    assert buildTwo.name == "Test Build 2"

    # Raw data
    dataOne = buildOne.pack()
    dataTwo = buildTwo.pack()

    # Name and UUID should be different
    assert dataOne["name"] != dataTwo["name"]
    assert dataOne["uuid"] != dataTwo["uuid"]

    # The rest should be equal
    assert dataOne["path"] == dataTwo["path"]
    assert dataOne["build"] == dataTwo["build"]
    assert dataOne["format"] == dataTwo["format"]
    assert dataOne["settings"] == dataTwo["settings"]
    assert dataOne["content"] == dataTwo["content"]
