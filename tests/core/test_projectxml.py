"""
novelWriter - Project XML Tests
===============================

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
import xml.etree.ElementTree as ET

from datetime import date, datetime
from shutil import copyfile

import pytest

from novelwriter import SHARED
from novelwriter.constants import nwFiles
from novelwriter.core.item import ProjectItem
from novelwriter.core.projectdata import ProjectData
from novelwriter.core.projectxml import ProjectXMLReader, ProjectXMLWriter, XMLReadState
from novelwriter.core.status import CUSTOM_COL, ItemStatus
from novelwriter.enum import nwStatusShape

from tests.helpers import cmpFiles, writeFile
from tests.mocked import causeOSError


class MockProject:
    """Fake project object."""

    data: ProjectData

    def setProjectChanged(self, *a):
        """Fake project method."""

    def markCountsDirty(self):
        """Fake project method."""


@pytest.fixture(autouse=True)
def mockVersion(monkeypatch):
    """Mock the version info to prevent diff from failing."""
    monkeypatch.setattr("novelwriter.core.projectxml.__version__", "26.2a1")
    monkeypatch.setattr("novelwriter.core.projectxml.__hexversion__", "0x260200a1")


@pytest.mark.core
def testProjectXMLReader_ReadCurrent(monkeypatch, mockGUI, tstPaths, fncPath):
    """Test reading the current XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.5.nwx"
    tstFile = tstPaths.outDir / "ProjectXML_ReadCurrent.nwx"
    xmlFile = fncPath / "nwProject-1.5.nwx"
    outFile = fncPath / "nwProject.nwx"

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    # With no valid files, the read should fail
    writeFile(xmlFile, "")
    assert xmlReader.read(data, content) is False
    assert xmlReader.state == XMLReadState.CANNOT_PARSE

    # Add a valid project file, that is not novelWriter
    writeFile(xmlFile, "<xml/>")
    assert xmlReader.read(data, content) is False
    assert xmlReader.state == XMLReadState.NOT_NWX_FILE

    # Add a valid novelWriter file without a file version
    writeFile(xmlFile, "<novelWriterXML/>")
    assert xmlReader.read(data, content) is False
    assert xmlReader.state == XMLReadState.UNKNOWN_VERSION

    # Check parsing of unknown sections
    writeFile(
        xmlFile,
        (
            "<novelWriterXML fileVersion='1.5'>"
            "  <project>"
            "    <stuff></stuff>"
            "  </project>"
            "  <settings>"
            "    <stuff></stuff>"
            "  </settings>"
            "  <content>"
            "    <item>"
            "      <stuff></stuff>"
            "    </item>"
            "    <stuff></stuff>"
            "  </content>"
            "  <stuff></stuff>"
            "</novelWriterXML>"
        ),
    )
    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.PARSED_OK

    writeFile(
        xmlFile,
        (
            "<novelWriterXML fileVersion='1.0'>"
            "  <project>"
            "    <stuff></stuff>"
            "  </project>"
            "  <settings>"
            "    <stuff></stuff>"
            "  </settings>"
            "  <content>"
            "    <item>"
            "      <stuff></stuff>"
            "    </item>"
            "    <stuff></stuff>"
            "  </content>"
            "  <stuff></stuff>"
            "</novelWriterXML>"
        ),
    )
    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY

    # A file version below current, but saved by a build at or after
    # the last breaking change, still counts as legacy
    writeFile(
        xmlFile,
        (
            "<novelWriterXML fileVersion='1.4' hexVersion='0x260200f0'>"
            "  <project>"
            "    <stuff></stuff>"
            "  </project>"
            "  <settings>"
            "    <stuff></stuff>"
            "  </settings>"
            "  <content>"
            "    <item>"
            "      <stuff></stuff>"
            "    </item>"
            "    <stuff></stuff>"
            "  </content>"
            "  <stuff></stuff>"
            "</novelWriterXML>"
        ),
    )
    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.hexVersion == 0x260200F0

    # Reset data objects
    data = ProjectData(MockProject())  # type: ignore
    content = []

    # Parse a valid, complete file
    copyfile(refFile, xmlFile)
    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.PARSED_OK
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0105
    assert xmlReader.xmlRevision == 7
    assert xmlReader.appVersion == "26.2a1"
    assert xmlReader.hexVersion == 0x260200A1

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jane Smith"
    assert data.saveCount == 2369
    assert data.autoCount == 429
    assert data.editTime == 1000

    assert data.doBackup is False
    assert data.language == "en_GB"
    assert data.spellCheck is True
    assert data.spellLang is None
    assert data.initCounts == (5561, 601, 29419, 3295)
    assert data.currCounts == (5561, 601, 29419, 3295)

    assert data.getLastHandle("editor") == "636b6aa9b697b"
    assert data.getLastHandle("viewer") == "636b6aa9b697b"
    assert data.getLastHandle("novel") == "7031beac91f75"
    assert data.getLastHandle("story") == "7031beac91f75"

    assert data.targetCount == 100000
    assert data.targetCountChars is False
    assert data.targetDeadline == date.fromisoformat("2026-08-20")
    assert data.dailyGoal == 1000
    assert data.dailyGoalAuto is False
    assert data.targetSkipRoots == {"d2d81f4831814"}
    assert data._dailyLastDate == date.today()
    assert data._dailyLastCount == 0

    assert data.itemStatus["sf12341"].name == "New"
    assert data.itemStatus["sf24ce6"].name == "Notes"
    assert data.itemStatus["sc24b8f"].name == "Started"
    assert data.itemStatus["s90e6c9"].name == "1st Draft"
    assert data.itemStatus["sd51c5b"].name == "2nd Draft"
    assert data.itemStatus["s8ae72a"].name == "3rd Draft"
    assert data.itemStatus["s78ea90"].name == "Finished"
    assert data.itemStatus["s936325"].name == "Sample"

    assert data.itemImport["ia857f0"].name == "None"
    assert data.itemImport["i4a1d39"].name == "Background"
    assert data.itemImport["icfb3a5"].name == "Minor"
    assert data.itemImport["i2d7a54"].name == "Major"
    assert data.itemImport["i56be10"].name == "Main"

    assert data.itemStatus["sf12341"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["sf24ce6"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["sc24b8f"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s90e6c9"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["sd51c5b"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s8ae72a"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s78ea90"].color.getRgb() == (58, 180, 58, 255)
    assert data.itemStatus["s936325"].color.getRgb() == (0, 0, 193, 255)

    assert data.itemImport["ia857f0"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["i4a1d39"].color.getRgb() == (220, 138, 221, 255)
    assert data.itemImport["icfb3a5"].color.getRgb() == (220, 138, 221, 255)
    assert data.itemImport["i2d7a54"].color.getRgb() == (220, 138, 221, 255)
    assert data.itemImport["i56be10"].color.getRgb() == (220, 138, 221, 255)

    assert data.itemStatus["sf12341"].theme == CUSTOM_COL
    assert data.itemStatus["sf24ce6"].theme == CUSTOM_COL
    assert data.itemStatus["sc24b8f"].theme == CUSTOM_COL
    assert data.itemStatus["s90e6c9"].theme == CUSTOM_COL
    assert data.itemStatus["sd51c5b"].theme == CUSTOM_COL
    assert data.itemStatus["s8ae72a"].theme == CUSTOM_COL
    assert data.itemStatus["s78ea90"].theme == CUSTOM_COL
    assert data.itemStatus["s936325"].theme == CUSTOM_COL

    assert data.itemImport["ia857f0"].theme == CUSTOM_COL
    assert data.itemImport["i4a1d39"].theme == CUSTOM_COL
    assert data.itemImport["icfb3a5"].theme == CUSTOM_COL
    assert data.itemImport["i2d7a54"].theme == CUSTOM_COL
    assert data.itemImport["i56be10"].theme == CUSTOM_COL

    assert data.itemStatus["sf12341"].shape == nwStatusShape.STAR
    assert data.itemStatus["sf24ce6"].shape == nwStatusShape.STAR
    assert data.itemStatus["sc24b8f"].shape == nwStatusShape.BARS_1
    assert data.itemStatus["s90e6c9"].shape == nwStatusShape.BARS_2
    assert data.itemStatus["sd51c5b"].shape == nwStatusShape.BARS_3
    assert data.itemStatus["s8ae72a"].shape == nwStatusShape.BARS_4
    assert data.itemStatus["s78ea90"].shape == nwStatusShape.STAR
    assert data.itemStatus["s936325"].shape == nwStatusShape.DIAMOND

    assert data.itemImport["ia857f0"].shape == nwStatusShape.STAR
    assert data.itemImport["i4a1d39"].shape == nwStatusShape.BLOCK_1
    assert data.itemImport["icfb3a5"].shape == nwStatusShape.BLOCK_2
    assert data.itemImport["i2d7a54"].shape == nwStatusShape.BLOCK_3
    assert data.itemImport["i56be10"].shape == nwStatusShape.BLOCK_4

    assert data.itemStatus["sf12341"].count == 7
    assert data.itemStatus["sf24ce6"].count == 2
    assert data.itemStatus["sc24b8f"].count == 2
    assert data.itemStatus["s90e6c9"].count == 5
    assert data.itemStatus["sd51c5b"].count == 2
    assert data.itemStatus["s8ae72a"].count == 0
    assert data.itemStatus["s78ea90"].count == 1
    assert data.itemStatus["s936325"].count == 7

    assert data.itemImport["ia857f0"].count == 7
    assert data.itemImport["i4a1d39"].count == 1
    assert data.itemImport["icfb3a5"].count == 1
    assert data.itemImport["i2d7a54"].count == 2
    assert data.itemImport["i56be10"].count == 1

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadCurrent.json"
    compFile = tstPaths.refDir / "projectXML_ReadCurrent.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        packedContent.append(item.pack())

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)

    # Fail saving
    SHARED.clearErrorCache()
    with monkeypatch.context() as mp:
        mp.setattr("xml.etree.ElementTree.ElementTree.write", causeOSError)
        assert xmlWriter.write(data, packedContent, timeStamp, 1000) is False
        assert SHARED.errorCache() == ["OSError: Mock OSError"]

    SHARED.clearErrorCache()
    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.replace", causeOSError)
        assert xmlWriter.write(data, packedContent, timeStamp, 1000) is False
        assert SHARED.errorCache() == ["OSError: Mock OSError"]

    # Successful save (should be run twice)
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    copyfile(outFile, tstFile)
    assert cmpFiles(tstFile, refFile)


@pytest.mark.core
def testProjectXMLReader_ReadLegacy10(tstPaths, fncPath, mockGUI, mockRnd):
    """Test reading the version 1.0 XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.0.nwx"
    xmlFile = fncPath / "nwProject-1.0.nwx"
    outFile = fncPath / "nwProject.nwx"
    copyfile(refFile, xmlFile)

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0100
    assert xmlReader.appVersion == "0.6.1"
    assert xmlReader.hexVersion == 0x000601F0

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jay Doh"  # Only last author is preserved
    assert data.saveCount == 0  # Doesn't exist in 1.0
    assert data.autoCount == 0  # Doesn't exist in 1.0
    assert data.editTime == 0  # Doesn't exist in 1.0

    assert data.doBackup is True
    assert data.language is None  # Doesn't exist in 1.0
    assert data.spellCheck is True
    assert data.spellLang is None  # Doesn't exist in 1.0
    assert data.initCounts == (0, 0, 0, 0)
    assert data.currCounts == (0, 0, 0, 0)

    assert data.getLastHandle("editor") is None  # Dropped by conversion
    assert data.getLastHandle("viewer") is None  # Dropped by conversion
    assert data.getLastHandle("novel") is None  # Doesn't exist in 1.0
    assert data.getLastHandle("story") is None  # Doesn't exist in 1.0

    assert data.targetCount == 0  # Doesn't exist in 1.0
    assert data.targetCountChars is False  # Doesn't exist in 1.0
    assert data.targetDeadline is None  # Doesn't exist in 1.0
    assert data.dailyGoal == 0  # Doesn't exist in 1.0
    assert data.dailyGoalAuto is False  # Doesn't exist in 1.0
    assert data._dailyLastDate is None  # Doesn't exist in 1.0
    assert data._dailyLastCount == 0  # Doesn't exist in 1.0

    assert data.itemStatus["s000000"].name == "New"
    assert data.itemStatus["s000001"].name == "Notes"
    assert data.itemStatus["s000002"].name == "Started"
    assert data.itemStatus["s000003"].name == "1st Draft"
    assert data.itemStatus["s000004"].name == "2nd Draft"
    assert data.itemStatus["s000005"].name == "3rd Draft"
    assert data.itemStatus["s000006"].name == "Finished"

    assert data.itemImport["i000007"].name == "None"
    assert data.itemImport["i000008"].name == "Minor"
    assert data.itemImport["i000009"].name == "Major"
    assert data.itemImport["i00000a"].name == "Main"

    assert data.itemStatus["s000000"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["s000001"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["s000002"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s000003"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000004"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000005"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000006"].color.getRgb() == (58, 180, 58, 255)

    assert data.itemImport["i000007"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["i000008"].color.getRgb() == (0, 122, 188, 255)
    assert data.itemImport["i000009"].color.getRgb() == (21, 0, 180, 255)
    assert data.itemImport["i00000a"].color.getRgb() == (117, 0, 175, 255)

    assert data.itemStatus["s000000"].theme == CUSTOM_COL
    assert data.itemStatus["s000001"].theme == CUSTOM_COL
    assert data.itemStatus["s000002"].theme == CUSTOM_COL
    assert data.itemStatus["s000003"].theme == CUSTOM_COL
    assert data.itemStatus["s000004"].theme == CUSTOM_COL
    assert data.itemStatus["s000005"].theme == CUSTOM_COL
    assert data.itemStatus["s000006"].theme == CUSTOM_COL

    assert data.itemImport["i000007"].theme == CUSTOM_COL
    assert data.itemImport["i000008"].theme == CUSTOM_COL
    assert data.itemImport["i000009"].theme == CUSTOM_COL
    assert data.itemImport["i00000a"].theme == CUSTOM_COL

    assert data.itemStatus["s000000"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000001"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000002"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000003"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000004"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000005"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000006"].shape == nwStatusShape.SQUARE

    assert data.itemImport["i000007"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000008"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000009"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i00000a"].shape == nwStatusShape.SQUARE

    assert data.itemStatus["s000000"].count == 0
    assert data.itemStatus["s000001"].count == 0
    assert data.itemStatus["s000002"].count == 0
    assert data.itemStatus["s000003"].count == 0
    assert data.itemStatus["s000004"].count == 0
    assert data.itemStatus["s000005"].count == 0
    assert data.itemStatus["s000006"].count == 0

    assert data.itemImport["i000007"].count == 0
    assert data.itemImport["i000008"].count == 0
    assert data.itemImport["i000009"].count == 0
    assert data.itemImport["i00000a"].count == 0

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadLegacy10.json"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy10.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    status = {}
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        status[item.itemHandle] = item.getImportStatus()[0]
        packedContent.append(item.pack())

    assert status == {
        "7031beac91f75": "Started",
        "53b69b83cdafc": "Started",
        "974e400180a99": "New",
        "edca4be2fcaf8": "New",
        "e7ded148d6e4a": "1st Draft",
        "6a2d6d5f4f401": "Notes",
        "636b6aa9b697b": "1st Draft",
        "bc0cbd2a407f3": "1st Draft",
        "ba8a28a246524": "Finished",
        "96b68994dfa3d": "2nd Draft",
        "88706ddc78b1b": "1st Draft",
        "ae7339df26ded": "1st Draft",
        "f6622b4617424": "None",
        "f7e2d9f330615": "None",
        "14298de4d9524": "Minor",
        "bb2c23b3c42cc": "Major",
        "15c4492bd5107": "None",
        "b3e74dbc1f584": "Main",
        "f1471bef9f2ae": "Minor",
        "5eaea4e8cdee8": "Major",
        "98acd8c76c93a": "None",
        "b8136a5a774a0": "New",
    }

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    testFile = tstPaths.outDir / "projectXML_ReadLegacy10.nwx"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy10.nwx"
    copyfile(outFile, testFile)
    assert cmpFiles(testFile, compFile)


@pytest.mark.core
def testProjectXMLReader_ReadLegacy11(tstPaths, fncPath, mockGUI, mockRnd):
    """Test reading the version 1.1 XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.1.nwx"
    xmlFile = fncPath / "nwProject-1.1.nwx"
    outFile = fncPath / "nwProject.nwx"
    copyfile(refFile, xmlFile)

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0101
    assert xmlReader.appVersion == "0.9.2"
    assert xmlReader.hexVersion == 0x000902F0

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jay Doh"  # Only last author is preserved
    assert data.saveCount == 5
    assert data.autoCount == 10
    assert data.editTime == 1000

    assert data.doBackup is True
    assert data.language is None  # Doesn't exist in 1.1
    assert data.spellCheck is True
    assert data.spellLang is None  # Doesn't exist in 1.1
    assert data.initCounts == (0, 0, 0, 0)
    assert data.currCounts == (0, 0, 0, 0)

    assert data.getLastHandle("editor") is None  # Dropped by conversion
    assert data.getLastHandle("viewer") is None  # Dropped by conversion
    assert data.getLastHandle("novel") is None  # Doesn't exist in 1.1
    assert data.getLastHandle("story") is None  # Doesn't exist in 1.1

    assert data.targetCount == 0  # Doesn't exist in 1.1
    assert data.targetCountChars is False  # Doesn't exist in 1.1
    assert data.targetDeadline is None  # Doesn't exist in 1.1
    assert data.dailyGoal == 0  # Doesn't exist in 1.1
    assert data.dailyGoalAuto is False  # Doesn't exist in 1.1
    assert data._dailyLastDate is None  # Doesn't exist in 1.1
    assert data._dailyLastCount == 0  # Doesn't exist in 1.1

    assert data.itemStatus["s000000"].name == "New"
    assert data.itemStatus["s000001"].name == "Notes"
    assert data.itemStatus["s000002"].name == "Started"
    assert data.itemStatus["s000003"].name == "1st Draft"
    assert data.itemStatus["s000004"].name == "2nd Draft"
    assert data.itemStatus["s000005"].name == "3rd Draft"
    assert data.itemStatus["s000006"].name == "Finished"

    assert data.itemImport["i000007"].name == "None"
    assert data.itemImport["i000008"].name == "Minor"
    assert data.itemImport["i000009"].name == "Major"
    assert data.itemImport["i00000a"].name == "Main"

    assert data.itemStatus["s000000"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["s000001"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["s000002"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s000003"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000004"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000005"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000006"].color.getRgb() == (58, 180, 58, 255)

    assert data.itemImport["i000007"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["i000008"].color.getRgb() == (0, 122, 188, 255)
    assert data.itemImport["i000009"].color.getRgb() == (21, 0, 180, 255)
    assert data.itemImport["i00000a"].color.getRgb() == (117, 0, 175, 255)

    assert data.itemStatus["s000000"].theme == CUSTOM_COL
    assert data.itemStatus["s000001"].theme == CUSTOM_COL
    assert data.itemStatus["s000002"].theme == CUSTOM_COL
    assert data.itemStatus["s000003"].theme == CUSTOM_COL
    assert data.itemStatus["s000004"].theme == CUSTOM_COL
    assert data.itemStatus["s000005"].theme == CUSTOM_COL
    assert data.itemStatus["s000006"].theme == CUSTOM_COL

    assert data.itemImport["i000007"].theme == CUSTOM_COL
    assert data.itemImport["i000008"].theme == CUSTOM_COL
    assert data.itemImport["i000009"].theme == CUSTOM_COL
    assert data.itemImport["i00000a"].theme == CUSTOM_COL

    assert data.itemStatus["s000000"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000001"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000002"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000003"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000004"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000005"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000006"].shape == nwStatusShape.SQUARE

    assert data.itemImport["i000007"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000008"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000009"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i00000a"].shape == nwStatusShape.SQUARE

    assert data.itemStatus["s000000"].count == 0
    assert data.itemStatus["s000001"].count == 0
    assert data.itemStatus["s000002"].count == 0
    assert data.itemStatus["s000003"].count == 0
    assert data.itemStatus["s000004"].count == 0
    assert data.itemStatus["s000005"].count == 0
    assert data.itemStatus["s000006"].count == 0

    assert data.itemImport["i000007"].count == 0
    assert data.itemImport["i000008"].count == 0
    assert data.itemImport["i000009"].count == 0
    assert data.itemImport["i00000a"].count == 0

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadLegacy11.json"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy11.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    status = {}
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        status[item.itemHandle] = item.getImportStatus()[0]
        packedContent.append(item.pack())

    assert status == {
        "7031beac91f75": "Started",
        "53b69b83cdafc": "Started",
        "974e400180a99": "New",
        "edca4be2fcaf8": "New",
        "e7ded148d6e4a": "1st Draft",
        "6a2d6d5f4f401": "Notes",
        "636b6aa9b697b": "1st Draft",
        "bc0cbd2a407f3": "1st Draft",
        "ba8a28a246524": "Finished",
        "96b68994dfa3d": "2nd Draft",
        "88706ddc78b1b": "1st Draft",
        "ae7339df26ded": "1st Draft",
        "f6622b4617424": "None",
        "f7e2d9f330615": "None",
        "14298de4d9524": "Minor",
        "bb2c23b3c42cc": "Major",
        "15c4492bd5107": "None",
        "b3e74dbc1f584": "Main",
        "f1471bef9f2ae": "Minor",
        "5eaea4e8cdee8": "Major",
        "98acd8c76c93a": "None",
        "b8136a5a774a0": "New",
    }

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    testFile = tstPaths.outDir / "projectXML_ReadLegacy11.nwx"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy11.nwx"
    copyfile(outFile, testFile)
    assert cmpFiles(testFile, compFile)


@pytest.mark.core
def testProjectXMLReader_ReadLegacy12(tstPaths, fncPath, mockGUI, mockRnd):
    """Test reading the version 1.2 XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.2.nwx"
    xmlFile = fncPath / "nwProject-1.2.nwx"
    outFile = fncPath / "nwProject.nwx"
    copyfile(refFile, xmlFile)

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0102
    assert xmlReader.appVersion == "1.4.2"
    assert xmlReader.hexVersion == 0x010402F0

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jay Doh"  # Only last author is preserved
    assert data.saveCount == 5
    assert data.autoCount == 10
    assert data.editTime == 1000

    assert data.doBackup is True
    assert data.language == "en_GB"
    assert data.spellCheck is True
    assert data.spellLang == "en_GB"
    assert data.initCounts == (840, 376, 0, 0)
    assert data.currCounts == (840, 376, 0, 0)

    assert data.getLastHandle("editor") is None  # Dropped by conversion
    assert data.getLastHandle("viewer") is None  # Dropped by conversion
    assert data.getLastHandle("novel") is None  # Doesn't exist in 1.2
    assert data.getLastHandle("story") is None  # Doesn't exist in 1.2

    assert data.targetCount == 0  # Doesn't exist in 1.2
    assert data.targetCountChars is False  # Doesn't exist in 1.2
    assert data.targetDeadline is None  # Doesn't exist in 1.2
    assert data.dailyGoal == 0  # Doesn't exist in 1.2
    assert data.dailyGoalAuto is False  # Doesn't exist in 1.2
    assert data._dailyLastDate is None  # Doesn't exist in 1.2
    assert data._dailyLastCount == 0  # Doesn't exist in 1.2

    assert data.itemStatus["s000000"].name == "New"
    assert data.itemStatus["s000001"].name == "Notes"
    assert data.itemStatus["s000002"].name == "Started"
    assert data.itemStatus["s000003"].name == "1st Draft"
    assert data.itemStatus["s000004"].name == "2nd Draft"
    assert data.itemStatus["s000005"].name == "3rd Draft"
    assert data.itemStatus["s000006"].name == "Finished"

    assert data.itemImport["i000007"].name == "None"
    assert data.itemImport["i000008"].name == "Minor"
    assert data.itemImport["i000009"].name == "Major"
    assert data.itemImport["i00000a"].name == "Main"

    assert data.itemStatus["s000000"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["s000001"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["s000002"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s000003"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000004"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000005"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000006"].color.getRgb() == (58, 180, 58, 255)

    assert data.itemImport["i000007"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["i000008"].color.getRgb() == (0, 122, 188, 255)
    assert data.itemImport["i000009"].color.getRgb() == (21, 0, 180, 255)
    assert data.itemImport["i00000a"].color.getRgb() == (117, 0, 175, 255)

    assert data.itemStatus["s000000"].theme == CUSTOM_COL
    assert data.itemStatus["s000001"].theme == CUSTOM_COL
    assert data.itemStatus["s000002"].theme == CUSTOM_COL
    assert data.itemStatus["s000003"].theme == CUSTOM_COL
    assert data.itemStatus["s000004"].theme == CUSTOM_COL
    assert data.itemStatus["s000005"].theme == CUSTOM_COL
    assert data.itemStatus["s000006"].theme == CUSTOM_COL

    assert data.itemImport["i000007"].theme == CUSTOM_COL
    assert data.itemImport["i000008"].theme == CUSTOM_COL
    assert data.itemImport["i000009"].theme == CUSTOM_COL
    assert data.itemImport["i00000a"].theme == CUSTOM_COL

    assert data.itemStatus["s000000"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000001"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000002"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000003"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000004"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000005"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000006"].shape == nwStatusShape.SQUARE

    assert data.itemImport["i000007"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000008"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000009"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i00000a"].shape == nwStatusShape.SQUARE

    assert data.itemStatus["s000000"].count == 0
    assert data.itemStatus["s000001"].count == 0
    assert data.itemStatus["s000002"].count == 0
    assert data.itemStatus["s000003"].count == 0
    assert data.itemStatus["s000004"].count == 0
    assert data.itemStatus["s000005"].count == 0
    assert data.itemStatus["s000006"].count == 0

    assert data.itemImport["i000007"].count == 0
    assert data.itemImport["i000008"].count == 0
    assert data.itemImport["i000009"].count == 0
    assert data.itemImport["i00000a"].count == 0

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadLegacy12.json"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy12.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    status = {}
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        status[item.itemHandle] = item.getImportStatus()[0]
        packedContent.append(item.pack())

    assert status == {
        "7031beac91f75": "Started",
        "53b69b83cdafc": "Started",
        "974e400180a99": "New",
        "edca4be2fcaf8": "New",
        "e7ded148d6e4a": "1st Draft",
        "6a2d6d5f4f401": "Notes",
        "636b6aa9b697b": "1st Draft",
        "bc0cbd2a407f3": "1st Draft",
        "ba8a28a246524": "New",
        "96b68994dfa3d": "2nd Draft",
        "88706ddc78b1b": "1st Draft",
        "ae7339df26ded": "1st Draft",
        "f6622b4617424": "None",
        "f7e2d9f330615": "None",
        "14298de4d9524": "Minor",
        "bb2c23b3c42cc": "Major",
        "15c4492bd5107": "None",
        "b3e74dbc1f584": "Main",
        "f1471bef9f2ae": "Minor",
        "5eaea4e8cdee8": "Major",
        "6827118336ac1": "New",  # Is now treated as novel-like
        "ae9bf3c3ea159": "New",  # Is now treated as novel-like
        "8a5deb88c0e97": "1st Draft",
        "98acd8c76c93a": "None",
        "b8136a5a774a0": "New",
    }

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    testFile = tstPaths.outDir / "projectXML_ReadLegacy12.nwx"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy12.nwx"
    copyfile(outFile, testFile)
    assert cmpFiles(testFile, compFile)


@pytest.mark.core
def testProjectXMLReader_ReadLegacy13(tstPaths, fncPath, mockGUI, mockRnd):
    """Test reading the version 1.3 XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.3.nwx"
    xmlFile = fncPath / "nwProject-1.3.nwx"
    outFile = fncPath / "nwProject.nwx"
    copyfile(refFile, xmlFile)

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0103
    assert xmlReader.appVersion == "1.6.6"
    assert xmlReader.hexVersion == 0x010606F0

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jay Doh"  # Only last author is preserved
    assert data.saveCount == 5
    assert data.autoCount == 10
    assert data.editTime == 1000

    assert data.doBackup is True
    assert data.language == "en_GB"
    assert data.spellCheck is True
    assert data.spellLang == "en_GB"
    assert data.initCounts == (830, 376, 0, 0)
    assert data.currCounts == (830, 376, 0, 0)

    assert data.getLastHandle("editor") is None  # Dropped by conversion
    assert data.getLastHandle("viewer") is None  # Dropped by conversion
    assert data.getLastHandle("novel") is None  # Doesn't exist in 1.3
    assert data.getLastHandle("story") is None  # Doesn't exist in 1.3

    assert data.targetCount == 0  # Doesn't exist in 1.3
    assert data.targetCountChars is False  # Doesn't exist in 1.3
    assert data.targetDeadline is None  # Doesn't exist in 1.3
    assert data.dailyGoal == 0  # Doesn't exist in 1.3
    assert data.dailyGoalAuto is False  # Doesn't exist in 1.3
    assert data._dailyLastDate is None  # Doesn't exist in 1.3
    assert data._dailyLastCount == 0  # Doesn't exist in 1.3

    assert data.itemStatus["s000000"].name == "New"
    assert data.itemStatus["s000001"].name == "Notes"
    assert data.itemStatus["s000002"].name == "Started"
    assert data.itemStatus["s000003"].name == "1st Draft"
    assert data.itemStatus["s000004"].name == "2nd Draft"
    assert data.itemStatus["s000005"].name == "3rd Draft"
    assert data.itemStatus["s000006"].name == "Finished"

    assert data.itemImport["i000007"].name == "None"
    assert data.itemImport["i000008"].name == "Minor"
    assert data.itemImport["i000009"].name == "Major"
    assert data.itemImport["i00000a"].name == "Main"

    assert data.itemStatus["s000000"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["s000001"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["s000002"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s000003"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000004"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000005"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s000006"].color.getRgb() == (58, 180, 58, 255)

    assert data.itemImport["i000007"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["i000008"].color.getRgb() == (0, 122, 188, 255)
    assert data.itemImport["i000009"].color.getRgb() == (21, 0, 180, 255)
    assert data.itemImport["i00000a"].color.getRgb() == (117, 0, 175, 255)

    assert data.itemStatus["s000000"].theme == CUSTOM_COL
    assert data.itemStatus["s000001"].theme == CUSTOM_COL
    assert data.itemStatus["s000002"].theme == CUSTOM_COL
    assert data.itemStatus["s000003"].theme == CUSTOM_COL
    assert data.itemStatus["s000004"].theme == CUSTOM_COL
    assert data.itemStatus["s000005"].theme == CUSTOM_COL
    assert data.itemStatus["s000006"].theme == CUSTOM_COL

    assert data.itemImport["i000007"].theme == CUSTOM_COL
    assert data.itemImport["i000008"].theme == CUSTOM_COL
    assert data.itemImport["i000009"].theme == CUSTOM_COL
    assert data.itemImport["i00000a"].theme == CUSTOM_COL

    assert data.itemStatus["s000000"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000001"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000002"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000003"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000004"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000005"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s000006"].shape == nwStatusShape.SQUARE

    assert data.itemImport["i000007"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000008"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i000009"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i00000a"].shape == nwStatusShape.SQUARE

    assert data.itemStatus["s000000"].count == 0
    assert data.itemStatus["s000001"].count == 0
    assert data.itemStatus["s000002"].count == 0
    assert data.itemStatus["s000003"].count == 0
    assert data.itemStatus["s000004"].count == 0
    assert data.itemStatus["s000005"].count == 0
    assert data.itemStatus["s000006"].count == 0

    assert data.itemImport["i000007"].count == 0
    assert data.itemImport["i000008"].count == 0
    assert data.itemImport["i000009"].count == 0
    assert data.itemImport["i00000a"].count == 0

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadLegacy13.json"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy13.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    status = {}
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        status[item.itemHandle] = item.getImportStatus()[0]
        packedContent.append(item.pack())

    assert status == {
        "7031beac91f75": "Started",
        "53b69b83cdafc": "Started",
        "974e400180a99": "New",
        "edca4be2fcaf8": "New",
        "e7ded148d6e4a": "1st Draft",
        "6a2d6d5f4f401": "Notes",
        "636b6aa9b697b": "1st Draft",
        "bc0cbd2a407f3": "1st Draft",
        "ba8a28a246524": "New",
        "96b68994dfa3d": "2nd Draft",
        "88706ddc78b1b": "1st Draft",
        "ae7339df26ded": "1st Draft",
        "f6622b4617424": "None",
        "f7e2d9f330615": "None",
        "14298de4d9524": "Minor",
        "bb2c23b3c42cc": "Major",
        "15c4492bd5107": "None",
        "b3e74dbc1f584": "Main",
        "f1471bef9f2ae": "Minor",
        "5eaea4e8cdee8": "Major",
        "6827118336ac1": "New",  # Is now treated as novel-like
        "ae9bf3c3ea159": "New",  # Is now treated as novel-like
        "8a5deb88c0e97": "1st Draft",
        "98acd8c76c93a": "None",
        "b8136a5a774a0": "New",
    }

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    testFile = tstPaths.outDir / "projectXML_ReadLegacy13.nwx"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy13.nwx"
    copyfile(outFile, testFile)
    assert cmpFiles(testFile, compFile)


@pytest.mark.core
def testProjectXMLReader_ReadLegacy14(tstPaths, fncPath, mockGUI, mockRnd):
    """Test reading the version 1.4 XML file format."""
    refFile = tstPaths.filesDir / "nwProject-1.4.nwx"
    xmlFile = fncPath / "nwProject-1.4.nwx"
    outFile = fncPath / "nwProject.nwx"
    copyfile(refFile, xmlFile)

    xmlReader = ProjectXMLReader(xmlFile)
    assert xmlReader.state == XMLReadState.NO_ACTION

    data = ProjectData(MockProject())  # type: ignore
    content = []

    assert xmlReader.read(data, content) is True
    assert xmlReader.state == XMLReadState.WAS_LEGACY
    assert xmlReader.xmlRoot == "novelWriterXML"
    assert xmlReader.xmlVersion == 0x0104
    assert xmlReader.appVersion == "2.0-rc1"
    assert xmlReader.hexVersion == 0x020000C1

    # Check loaded data
    assert data.name == "Sample Project"
    assert data.author == "Jay Doh"  # Only last author is preserved
    assert data.saveCount == 5
    assert data.autoCount == 10
    assert data.editTime == 1000

    assert data.doBackup is True
    assert data.language == "en_GB"
    assert data.spellCheck is True
    assert data.spellLang == "en_GB"
    assert data.initCounts == (954, 409, 0, 0)
    assert data.currCounts == (954, 409, 0, 0)

    assert data.getLastHandle("editor") is None  # Dropped by conversion
    assert data.getLastHandle("viewer") is None  # Dropped by conversion
    assert data.getLastHandle("novel") is None  # Doesn't exist in 1.4
    assert data.getLastHandle("story") is None  # Doesn't exist in 1.4

    assert data.targetCount == 0  # Doesn't exist in 1.4
    assert data.targetCountChars is False  # Doesn't exist in 1.4
    assert data.targetDeadline is None  # Doesn't exist in 1.4
    assert data.dailyGoal == 0  # Doesn't exist in 1.4
    assert data.dailyGoalAuto is False  # Doesn't exist in 1.4
    assert data._dailyLastDate is None  # Doesn't exist in 1.4
    assert data._dailyLastCount == 0  # Doesn't exist in 1.4

    assert data.itemStatus["sf12341"].name == "New"
    assert data.itemStatus["sf24ce6"].name == "Notes"
    assert data.itemStatus["sc24b8f"].name == "Started"
    assert data.itemStatus["s90e6c9"].name == "1st Draft"
    assert data.itemStatus["sd51c5b"].name == "2nd Draft"
    assert data.itemStatus["s8ae72a"].name == "3rd Draft"
    assert data.itemStatus["s78ea90"].name == "Finished"

    assert data.itemImport["ia857f0"].name == "None"
    assert data.itemImport["icfb3a5"].name == "Minor"
    assert data.itemImport["i2d7a54"].name == "Major"
    assert data.itemImport["i56be10"].name == "Main"

    assert data.itemStatus["sf12341"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemStatus["sf24ce6"].color.getRgb() == (200, 50, 0, 255)
    assert data.itemStatus["sc24b8f"].color.getRgb() == (182, 60, 0, 255)
    assert data.itemStatus["s90e6c9"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["sd51c5b"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s8ae72a"].color.getRgb() == (193, 129, 0, 255)
    assert data.itemStatus["s78ea90"].color.getRgb() == (58, 180, 58, 255)

    assert data.itemImport["ia857f0"].color.getRgb() == (100, 100, 100, 255)
    assert data.itemImport["icfb3a5"].color.getRgb() == (0, 122, 188, 255)
    assert data.itemImport["i2d7a54"].color.getRgb() == (21, 0, 180, 255)
    assert data.itemImport["i56be10"].color.getRgb() == (117, 0, 175, 255)

    assert data.itemStatus["sf12341"].theme == CUSTOM_COL
    assert data.itemStatus["sf24ce6"].theme == CUSTOM_COL
    assert data.itemStatus["sc24b8f"].theme == CUSTOM_COL
    assert data.itemStatus["s90e6c9"].theme == CUSTOM_COL
    assert data.itemStatus["sd51c5b"].theme == CUSTOM_COL
    assert data.itemStatus["s8ae72a"].theme == CUSTOM_COL
    assert data.itemStatus["s78ea90"].theme == CUSTOM_COL

    assert data.itemImport["ia857f0"].theme == CUSTOM_COL
    assert data.itemImport["icfb3a5"].theme == CUSTOM_COL
    assert data.itemImport["i2d7a54"].theme == CUSTOM_COL
    assert data.itemImport["i56be10"].theme == CUSTOM_COL

    assert data.itemStatus["sf12341"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["sf24ce6"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["sc24b8f"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s90e6c9"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["sd51c5b"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s8ae72a"].shape == nwStatusShape.SQUARE
    assert data.itemStatus["s78ea90"].shape == nwStatusShape.SQUARE

    assert data.itemImport["ia857f0"].shape == nwStatusShape.SQUARE
    assert data.itemImport["icfb3a5"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i2d7a54"].shape == nwStatusShape.SQUARE
    assert data.itemImport["i56be10"].shape == nwStatusShape.SQUARE

    assert data.itemStatus["sf12341"].count == 4
    assert data.itemStatus["sf24ce6"].count == 2
    assert data.itemStatus["sc24b8f"].count == 3
    assert data.itemStatus["s90e6c9"].count == 7
    assert data.itemStatus["sd51c5b"].count == 0
    assert data.itemStatus["s8ae72a"].count == 0
    assert data.itemStatus["s78ea90"].count == 1
    assert data.itemImport["ia857f0"].count == 5
    assert data.itemImport["icfb3a5"].count == 2
    assert data.itemImport["i2d7a54"].count == 2
    assert data.itemImport["i56be10"].count == 1

    # Compare content
    dumpFile = tstPaths.outDir / "projectXML_ReadLegacy14.json"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy14.json"
    with open(dumpFile, mode="w", encoding="utf-8") as dump:
        json.dump(content, dump, indent=2)
    assert cmpFiles(dumpFile, compFile)

    packedContent = []
    mockProject = MockProject()
    mockProject.data = data
    status = {}
    for entry in content:
        item = ProjectItem(mockProject, "0000000000000")  # type: ignore
        item.unpack(entry)
        status[item.itemHandle] = item.getImportStatus()[0]
        packedContent.append(item.pack())

    assert status == {
        "7031beac91f75": "Started",
        "53b69b83cdafc": "Started",
        "974e400180a99": "New",
        "edca4be2fcaf8": "1st Draft",
        "6a2d6d5f4f401": "Notes",
        "636b6aa9b697b": "1st Draft",
        "bc0cbd2a407f3": "1st Draft",
        "ba8a28a246524": "Finished",
        "96b68994dfa3d": "Notes",
        "88706ddc78b1b": "1st Draft",
        "ae7339df26ded": "1st Draft",
        "e5e47ebf63b1c": "New",
        "bacb7059e3083": "Started",
        "a520879ca0b45": "1st Draft",
        "f6622b4617424": "None",
        "f7e2d9f330615": "None",
        "14298de4d9524": "Minor",
        "bb2c23b3c42cc": "Major",
        "15c4492bd5107": "None",
        "b3e74dbc1f584": "Main",
        "f1471bef9f2ae": "Minor",
        "5eaea4e8cdee8": "Major",
        "6827118336ac1": "New",
        "ae9bf3c3ea159": "New",
        "8a5deb88c0e97": "1st Draft",
        "98acd8c76c93a": "None",
        "b8136a5a774a0": "None",
    }

    # Save the project again, which should produce an identical project xml
    timeStamp = int(datetime.fromisoformat(xmlReader.timeStamp).timestamp())
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)
    data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    assert xmlWriter.write(data, packedContent, timeStamp, 1000) is True
    testFile = tstPaths.outDir / "projectXML_ReadLegacy14.nwx"
    compFile = tstPaths.refDir / "projectXML_ReadLegacy14.nwx"
    copyfile(outFile, testFile)
    assert cmpFiles(testFile, compFile)


@pytest.mark.core
def testProjectXMLReaderWriter_ParsePackHelpers(mockGUI, fncPath):
    """Test the internal parse/pack helper functions directly."""
    xmlReader = ProjectXMLReader(fncPath / nwFiles.PROJ_FILE)
    xmlWriter = ProjectXMLWriter(fncPath / nwFiles.PROJ_FILE)

    # Non-entry elements in a status/importance list are skipped
    status = ItemStatus(ItemStatus.STATUS)
    xItem = ET.fromstring('<status><entry key="s000001" color="#ff0000">New</entry><other>Ignored</other></status>')
    xmlReader._parseStatusImport(xItem, status)
    assert len(status) == 1

    # Non-entry elements in a key/text dict are skipped
    xItem = ET.fromstring('<autoReplace><entry key="one">1</entry><other>Ignored</other></autoReplace>')
    assert xmlReader._parseDictKeyText(xItem) == {"one": "1"}

    # Empty keys are skipped when packing a dict
    xParent = ET.Element("project")
    xmlWriter._packDictKeyValue(xParent, "autoReplace", {"": "ignored", "one": "1"})
    packed = xParent.find("autoReplace")
    assert packed is not None
    assert [e.attrib["key"] for e in packed] == ["one"]


@pytest.mark.core
def testProjectXMLReaderWriter_TargetCountChars(mockGUI, fncPath):
    """Test that the project target count mode (words vs characters) is
    written to and parsed back from the XML file correctly, and that a
    file saved before the mode attribute existed defaults to words.
    """
    path = fncPath / nwFiles.PROJ_FILE
    xmlWriter = ProjectXMLWriter(path)
    xmlReader = ProjectXMLReader(path)

    # A project with the character count mode enabled is written with a
    # "characters" mode attribute, which is restored when read back
    data = ProjectData(MockProject())  # type: ignore
    data.setProjectTarget(1000, None, True)
    assert xmlWriter.write(data, [], 0.0, 0) is True
    assert 'mode="characters"' in path.read_text(encoding="utf-8")

    readBack = ProjectData(MockProject())  # type: ignore
    assert xmlReader.read(readBack, []) is True
    assert readBack.targetCountChars is True

    # A project with the word count mode is written with a "words" mode
    # attribute, which is likewise restored when read back
    data.setProjectTarget(1000, None, False)
    assert xmlWriter.write(data, [], 0.0, 0) is True
    assert 'mode="words"' in path.read_text(encoding="utf-8")

    readBack = ProjectData(MockProject())  # type: ignore
    assert xmlReader.read(readBack, []) is True
    assert readBack.targetCountChars is False

    # A settings section saved before the mode attribute was introduced
    # has no mode attribute at all, which must default to words
    xSettings = ET.fromstring('<settings><projectTarget date="None" last="0">5000</projectTarget></settings>')
    legacy = ProjectData(MockProject())  # type: ignore
    xmlReader._parseProjectSettings(xSettings, legacy)
    assert legacy.targetCount == 5000
    assert legacy.targetCountChars is False
