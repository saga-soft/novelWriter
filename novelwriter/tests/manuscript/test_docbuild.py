"""
novelWriter - Manuscript Builder Tests
======================================

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
import zipfile

from pathlib import Path
from shutil import copyfile

import pytest

from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt, nwItemClass
from novelwriter.formats.tohtml import ToHtml
from novelwriter.formats.tomarkdown import ToMarkdown
from novelwriter.formats.toodt import ToOdt
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.formats.toraw import ToRaw
from novelwriter.manuscript.buildsettings import BuildSettings
from novelwriter.manuscript.docbuild import DocumentBuilder

from tests.helpers import ODT_IGNORE, C, buildTestProject, cmpFiles
from tests.mocked import causeException, causeOSError

BUILD_CONF = {
    "name": "Test Build",
    "uuid": "f8796eee-e234-4e8a-8355-b2709177e53c",
    "settings": {
        "filter.includeNovel": True,
        "filter.includeNotes": True,
        "filter.includeInactive": True,
        "headings.fmtPart": "Part: {Title}",
        "headings.fmtChapter": "Chapter: {Title}",
        "headings.fmtUnnumbered": "{Title}",
        "headings.fmtScene": "Scene: {Title}",
        "headings.fmtSection": "Section: {Title}",
        "headings.hideScene": False,
        "headings.hideSection": False,
        "text.includeBodyText": True,
        "text.includeSynopsis": True,
        "text.includeComments": True,
        "text.includeKeywords": True,
        "text.addNoteHeadings": True,
        "format.buildLang": "en_GB",
        "format.textFont": "Arial,12",
        "format.lineHeight": 1.5,
        "format.justifyText": True,
        "format.stripUnicode": False,
        "format.replaceTabs": True,
        "format.firstLineIndent": True,
        "format.colorHeadings": True,
        "html.addStyles": True,
    },
    "content": {
        "included": [],
        "excluded": [],
        "skipRoot": [],
    },
}


@pytest.mark.core
def testDocumentBuilder_OpenDocument(monkeypatch, mockGUI, prjLipsum, fncPath, tstPaths):
    """Test building an open document manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild._outline = True
    docBuild.queueAll()

    assert docBuild._outline is True

    assert len(docBuild) == 19

    # Check FODT Build
    # ================

    docFile = fncPath / "Lorem Ipsum.fodt"
    tstFile = tstPaths.outDir / "mBuildDocBuild_OpenDocument_Lorem_Ipsum.fodt"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_OpenDocument_Lorem_Ipsum.fodt"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.FODT):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile, ignStart=ODT_IGNORE)

    # Check ODT Build
    # ===============

    docFile = fncPath / "Lorem Ipsum.odt"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.ODT):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    assert docFile.is_file()
    assert zipfile.is_zipfile(docFile)

    # Check Error Handling
    # ====================

    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)

        docFile = fncPath / "Lorem Ipsum Err.fodt"
        for _ in docBuild.iterBuildDocument(docFile, nwBuildFmt.FODT):
            pass

        assert docBuild.error == "OSError: Mock OSError"
        assert not docFile.is_file()

    # Check Build Issues
    # ==================

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.formats.toodt.ToOdt.doConvert", causeException)
        assert len(docBuild) == 19

        count = 0
        error = []
        docFile = fncPath / "Lorem Ipsum Err.fodt"
        for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.FODT):
            count += 1 if success else 0
            if not success and docBuild.error:
                error.append(docBuild.error)

        assert count == 1
        assert error == [
            "Build: Failed to build '7a992350f3eb6'",
            "Build: Failed to build '8c58a65414c23'",
            "Build: Failed to build '88d59a277361b'",
            "Build: Failed to build 'db7e733775d4d'",
            "Build: Failed to build 'fb609cd8319dc'",
            "Build: Failed to build '88243afbe5ed8'",
            "Build: Failed to build 'f96ec11c6a3da'",
            "Build: Failed to build '846352075de7d'",
            "Build: Failed to build '441420a886d82'",
            "Build: Failed to build 'eb103bc70c90c'",
            "Build: Failed to build 'f8c0562e50f1b'",
            "Build: Failed to build '47666c91c7ccf'",
            "Build: Failed to build '67a8707f2f249'",
            "Build: Failed to build '4c4f28287af27'",
            "Build: Failed to build '6c6afb1247750'",
            "Build: Failed to build '2426c6f0ca922'",
            "Build: Failed to build '60bdf227455cc'",
            "Build: Failed to build '04468803b92e1'",
        ]


@pytest.mark.core
def testDocumentBuilder_HTML(monkeypatch, mockGUI, prjLipsum, fncPath, tstPaths):
    """Test building an HTML manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    assert len(docBuild) == 19

    # Check HTML5 Build
    # =================

    docFile = fncPath / "Lorem Ipsum.htm"
    tstFile = tstPaths.outDir / "mBuildDocBuild_HTML5_Lorem_Ipsum.htm"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_HTML5_Lorem_Ipsum.htm"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.HTML):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile)

    # Check HTML5 JSON Build
    # ======================

    docFile = fncPath / "Lorem Ipsum.json"
    tstFile = tstPaths.outDir / "mBuildDocBuild_HTML5_Lorem_Ipsum.json"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_HTML5_Lorem_Ipsum.json"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.J_HTML):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile, ignLines=[5, 6])

    # Check Error Handling
    # ====================

    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)

        docFile = fncPath / "Lorem Ipsum Err.htm"
        for _ in docBuild.iterBuildDocument(docFile, nwBuildFmt.HTML):
            pass

        assert docBuild.error == "OSError: Mock OSError"
        assert not docFile.is_file()

    # Preserve Tabs
    # =============

    build.setValue("html.preserveTabs", True)
    docFile = fncPath / "Lorem Ipsum Tabs.htm"
    assert all(success for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.HTML))
    assert docFile.is_file()


@pytest.mark.core
def testDocumentBuilder_Markdown(monkeypatch, mockGUI, prjLipsum, fncPath, tstPaths):
    """Test building an Markdown manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    assert len(docBuild) == 19

    # Check Standard Markdown Build
    # =============================

    docFile = fncPath / "Lorem Ipsum Standard.md"
    tstFile = tstPaths.outDir / "mBuildDocBuild_Standard_Markdown_Lorem_Ipsum.md"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_Standard_Markdown_Lorem_Ipsum.md"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.STD_MD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile)

    # Check Extended Markdown Build
    # =============================

    docFile = fncPath / "Lorem Ipsum Standard.md"
    tstFile = tstPaths.outDir / "mBuildDocBuild_Extended_Markdown_Lorem_Ipsum.md"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_Extended_Markdown_Lorem_Ipsum.md"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.EXT_MD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile)

    # Check Error Handling
    # ====================

    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)

        docFile = fncPath / "Lorem Ipsum Err.md"
        for _ in docBuild.iterBuildDocument(docFile, nwBuildFmt.STD_MD):
            pass

        assert docBuild.error == "OSError: Mock OSError"
        assert not docFile.is_file()


@pytest.mark.core
def testDocumentBuilder_DocX(mockGUI, prjLipsum, fncPath):
    """Test building a Word manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    assert len(docBuild) == 19

    # Check Build
    # ===========

    docFile = fncPath / "Lorem Ipsum.docx"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.DOCX):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    assert docFile.is_file()
    assert zipfile.is_zipfile(docFile)


@pytest.mark.core
def testDocumentBuilder_PDF(mockGUI, prjLipsum, fncPath):
    """Test building a PDF manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    assert len(docBuild) == 19

    # Check Build
    # ===========

    docFile = fncPath / "Lorem Ipsum.pdf"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.PDF):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    assert docFile.is_file()


@pytest.mark.core
def testDocumentBuilder_NWD(mockGUI, prjLipsum, fncPath, tstPaths):
    """Test building a NWD manuscript."""
    project = NWProject()
    project.openProject(prjLipsum)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()

    assert len(docBuild) == 19

    # Check NWD Build
    # ===============

    docFile = fncPath / "Lorem Ipsum.txt"
    tstFile = tstPaths.outDir / "mBuildDocBuild_NWD_Lorem_Ipsum.txt"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_NWD_Lorem_Ipsum.txt"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.NWD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile)

    # Check NWD JSON Build
    # ====================

    docFile = fncPath / "Lorem Ipsum.json"
    tstFile = tstPaths.outDir / "mBuildDocBuild_NWD_Lorem_Ipsum.json"
    cmpFile = tstPaths.refDir / "mBuildDocBuild_NWD_Lorem_Ipsum.json"

    count = 0
    error = []
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.J_NWD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 19
    assert error == []

    copyfile(docFile, tstFile)
    assert cmpFiles(tstFile, cmpFile, ignLines=[5, 6])


@pytest.mark.core
def testDocumentBuilder_Custom(mockGUI, fncPath: Path, mockRnd):
    """Test custom builds and some error handling."""
    project = NWProject()
    buildTestProject(project, fncPath)

    build = BuildSettings()
    build.unpack(BUILD_CONF)

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()
    assert len(docBuild) == 4

    # Build a simple text doc
    count = 0
    error = []
    docFile = fncPath / "Minimal.txt"
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.NWD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 4
    assert error == []
    assert docFile.read_text(encoding="utf-8") == (
        "#! New Novel\n\n>> By Jane Doe <<\n\n## New Chapter\n\n### New Scene\n\n"
    )
    docFile.unlink()

    # Add an invalid item to the project
    nHandle = "0123456789def"
    project.tree._items[nHandle] = None  # type: ignore
    project.tree._nodes[nHandle] = None  # type: ignore

    docBuild.queueAll()
    assert len(docBuild) == 4

    docBuild.addDocument(nHandle)
    assert len(docBuild) == 5

    # Build the doc again with broken items
    count = 0
    error = []
    docFile = fncPath / "Minimal.txt"
    for _, success in docBuild.iterBuildDocument(docFile, nwBuildFmt.NWD):
        count += 1 if success else 0
        if docBuild.error:
            error.append(docBuild.error)

    assert count == 4
    assert error == []
    assert docFile.read_text(encoding="utf-8") == (
        "#! New Novel\n\n>> By Jane Doe <<\n\n## New Chapter\n\n### New Scene\n\n"
    )
    docFile.unlink()

    # Direct _doBuild Calls
    # =====================

    rawObj = ToRaw(project)

    # A handle that isn't a real tree item is a no-op success
    assert docBuild._doBuild(rawObj, nHandle) is True

    # A folder item is neither root nor file type, and is also a no-op success
    assert project.tree[C.hChapterDir].isFolderType() is True  # type: ignore
    assert docBuild._doBuild(rawObj, C.hChapterDir) is True

    # A non-novel-like root item, with counting, outline, and convert all disabled
    assert project.tree[C.hPlotRoot].itemClass == nwItemClass.PLOT  # type: ignore
    docBuild._count = False
    docBuild._outline = False
    assert docBuild._doBuild(rawObj, C.hPlotRoot, convert=False) is True

    # A file item, with counting, outline, and convert all disabled
    assert project.tree[C.hSceneDoc].isFileType() is True  # type: ignore
    assert docBuild._doBuild(rawObj, C.hSceneDoc, convert=False) is True


@pytest.mark.core
def testDocumentBuilder_IterBuild(mockGUI, fncPath: Path, mockRnd):
    """Test iter build wrapper."""
    project = NWProject()
    buildTestProject(project, fncPath)
    build = BuildSettings()
    build.unpack(BUILD_CONF)

    # Add some more items
    hPlotDoc = project.newFile("Main Plot", C.hPlotRoot)
    hCharDoc = project.newFile("Jane Doe", C.hCharRoot)
    project.storage.getDocument(hPlotDoc).writeDocument("# Main Plot\n**Text**")
    project.storage.getDocument(hCharDoc).writeDocument("# Jane Doe\n~~Text~~")

    docBuild = DocumentBuilder(project, build)
    docBuild.queueAll()
    assert len(docBuild) == 8

    # ODT Format
    docFile = fncPath / "Minimal.odt"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.ODT)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToOdt)
    assert docFile.is_file()
    docFile.unlink()

    # FODT Format
    docFile = fncPath / "Minimal.fodt"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.FODT)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToOdt)
    assert docFile.read_text(encoding="utf-8").startswith("<?xml")
    docFile.unlink()

    # HTML Format
    docFile = fncPath / "Minimal.html"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.HTML)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToHtml)
    assert docFile.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")
    docFile.unlink()

    # JSON HTML Format
    docFile = fncPath / "Minimal.json"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.J_HTML)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToHtml)
    data = json.loads(docFile.read_text(encoding="utf-8"))
    assert "meta" in data
    assert "text" in data
    docFile.unlink()

    # Standard Markdown Format
    docFile = fncPath / "Minimal.md"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.STD_MD)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToMarkdown)
    assert docFile.read_text(encoding="utf-8") == (
        "New Novel\n"
        "=========\n\n"
        "By Jane Doe\n\n"
        "# Chapter: New Chapter\n\n"
        "## Scene: New Scene\n\n"
        "Notes: Plot\n"
        "===========\n\n"
        "# Main Plot\n\n"
        "**Text**\n\n"
        "Notes: Characters\n"
        "=================\n\n"
        "# Jane Doe\n\n"
        "Text\n\n"  # Standard converts strikethrough to ordinary text
    )
    docFile.unlink()

    # Extended Markdown Format
    docFile = fncPath / "Minimal.md"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.EXT_MD)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToMarkdown)
    assert docFile.read_text(encoding="utf-8") == (
        "New Novel\n"
        "=========\n\n"
        "By Jane Doe\n\n"
        "# Chapter: New Chapter\n\n"
        "## Scene: New Scene\n\n"
        "Notes: Plot\n"
        "===========\n\n"
        "# Main Plot\n\n"
        "**Text**\n\n"
        "Notes: Characters\n"
        "=================\n\n"
        "# Jane Doe\n\n"
        "~~Text~~\n\n"  # Extended allows this syntax
    )
    docFile.unlink()

    # NWD Format
    docFile = fncPath / "Minimal.txt"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.NWD)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToRaw)
    assert docFile.read_text(encoding="utf-8") == (
        "#! New Novel\n\n"
        ">> By Jane Doe <<\n\n"
        "## New Chapter\n\n"
        "### New Scene\n\n"
        "#! Notes: Plot\n\n"
        "# Main Plot\n"
        "**Text**\n\n"
        "#! Notes: Characters\n\n"
        "# Jane Doe\n"
        "~~Text~~\n\n"
    )
    docFile.unlink()

    # JSON NWD Format
    docFile = fncPath / "Minimal.json"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.J_NWD)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToRaw)
    data = json.loads(docFile.read_text(encoding="utf-8"))
    assert "meta" in data
    assert "text" in data
    docFile.unlink()

    # PDF Format
    docFile = fncPath / "Minimal.pdf"
    assert list(docBuild.iterBuildDocument(docFile, nwBuildFmt.PDF)) == [
        (0, True),
        (1, True),
        (2, True),
        (3, True),
        (4, True),
        (5, True),
        (6, True),
        (7, True),
    ]
    assert isinstance(docBuild.lastBuild, ToQTextDocument)
    assert docFile.is_file()
    docFile.unlink()

    # Invalid Format
    assert list(docBuild.iterBuildDocument(docFile, None)) == []  # type: ignore
    assert docBuild.lastBuild is None
