"""
novelWriter - Index Tests
=========================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

from shutil import copyfile

import pytest

from novelwriter import SHARED
from novelwriter.constants import nwFiles
from novelwriter.core.index import Index, TagsIndex
from novelwriter.core.item import ProjectItem
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment, nwItemClass, nwItemLayout, nwNovelExtra
from novelwriter.models.novelmodel import NovelModel

from tests.helpers import C, buildTestProject, cmpFiles
from tests.mocked import causeException


@pytest.mark.core
def testIndex_LoadSave(qtbot, monkeypatch, prjLipsum, nwGUI, tstPaths):
    """Test core functionality of scanning, saving, loading and checking
    the index cache file.
    """
    projFile = prjLipsum / "meta" / nwFiles.INDEX_FILE
    testFile = tstPaths.outDir / "coreIndex_LoadSave_tagsIndex.json"
    compFile = tstPaths.refDir / "coreIndex_LoadSave_tagsIndex.json"

    project = NWProject()
    assert project.openProject(prjLipsum)

    index = Index(project)
    assert repr(index) == "<Index project='Lorem Ipsum'>"

    # Check Novel Model
    model = index.getNovelModel("b3643d0f92e32")
    assert isinstance(model, NovelModel)
    assert model.columns == 3

    # A non-novel root, or an invalid handle, has no novel model
    assert index.getNovelModel("67a8707f2f249") is None
    assert index.getNovelModel("0000000000000") is None

    index.setNovelModelExtraColumn(nwNovelExtra.POV)
    index.refreshNovelModel("b3643d0f92e32")
    model = index.getNovelModel("b3643d0f92e32")
    assert isinstance(model, NovelModel)
    assert model.columns == 4

    # Refreshing with no handle or an unknown handle does nothing
    index.refreshNovelModel(None)
    index.refreshNovelModel("0000000000000")

    # Re-index
    notIndexable = {
        "b3643d0f92e32": False,  # Novel ROOT
        "45e6b01ca35c1": False,  # Chapter One FOLDER
        "6bd935d2490cd": False,  # Chapter Two FOLDER
        "67a8707f2f249": False,  # Character ROOT
        "6c6afb1247750": False,  # Plot ROOT
        "60bdf227455cc": False,  # World ROOT
        "1ace7ab1a0fc6": False,  # Trash ROOT
    }
    for tItem in project.tree:
        index.reIndexHandle(tItem.itemHandle)
        assert (tItem.itemHandle in index._itemIndex) is notIndexable.get(tItem.itemHandle, True)

    # No folder for saving
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert index.saveIndex() is False

    # Make the save fail
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeException)
        assert index.saveIndex() is False

    # Make the save pass
    assert index.saveIndex() is True

    # A full save also records the index revision on the project, which
    # is normally done by NWProject.saveProject before it calls saveIndex
    project.data.setIndexRevision(index.indexRevision)

    # Take a copy of the index
    tagIndex = str(index._tagsIndex.packData())
    itemsIndex = str(index._itemIndex.packData())

    # Update item class
    bHandle = "4c4f28287af27"
    bItem = project.tree[bHandle]
    assert bItem is not None

    tagsBod = index._tagsIndex["Bod"]
    assert tagsBod is not None
    assert tagsBod["handle"] == bHandle
    assert tagsBod["class"] == "CHARACTER"

    bItem.setClass(nwItemClass.CUSTOM)
    index.refreshHandle(bHandle)
    assert tagsBod is not None
    assert tagsBod["handle"] == bHandle
    assert tagsBod["class"] == "CUSTOM"

    # Update item class to inactive
    bItem.setClass(nwItemClass.TRASH)
    index.refreshHandle(bHandle)
    assert "Bod" not in index._tagsIndex
    bItem.setClass(nwItemClass.CHARACTER)
    index.reIndexHandle(bHandle)

    # Refreshing a handle that isn't in the project tree does nothing
    index.refreshHandle("0000000000000")

    # Delete a handle
    assert index._tagsIndex["Bod"] is not None
    assert index._itemIndex[bHandle] is not None
    index.deleteHandle(bHandle)
    assert index._tagsIndex["Bod"] is None
    assert index._itemIndex[bHandle] is None

    # Clear the index
    index.clear()
    assert index._tagsIndex._tags == {}
    assert index._itemIndex._items == {}

    # No folder for loading
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert index.loadIndex() is False

    # Make the load fail
    with monkeypatch.context() as mp:
        mp.setattr(json, "load", causeException)
        assert index.loadIndex() is False
        assert index.indexRebuild is True

    # Make the load pass
    assert index.loadIndex() is True
    assert index.indexRebuild is False
    assert index.indexUpgrade is False

    assert str(index._tagsIndex.packData()) == tagIndex
    assert str(index._itemIndex.packData()) == itemsIndex

    # Rebuild index
    index.clear()
    index.rebuild()

    assert str(index._tagsIndex.packData()) == tagIndex
    assert str(index._itemIndex.packData()) == itemsIndex

    # Check File
    copyfile(projFile, testFile)
    assert cmpFiles(testFile, compFile, ignLines=[3, 4, 5])

    # Write an empty index file and load it
    projFile.write_text("{}", encoding="utf-8")
    assert index.loadIndex() is False
    assert index.indexRebuild is True

    # Write an index file that passes loading, but is still empty
    projFile.write_text('{"novelWriter.tagsIndex": {}, "novelWriter.itemIndex": {}}', encoding="utf-8")
    assert index.loadIndex() is True
    assert index.indexRebuild is False

    # Check that the index is re-populated
    assert "04468803b92e1" in index._itemIndex
    assert "2426c6f0ca922" in index._itemIndex
    assert "441420a886d82" in index._itemIndex
    assert "47666c91c7ccf" in index._itemIndex
    assert "4c4f28287af27" in index._itemIndex
    assert "846352075de7d" in index._itemIndex
    assert "88243afbe5ed8" in index._itemIndex
    assert "88d59a277361b" in index._itemIndex
    assert "8c58a65414c23" in index._itemIndex
    assert "db7e733775d4d" in index._itemIndex
    assert "eb103bc70c90c" in index._itemIndex
    assert "f8c0562e50f1b" in index._itemIndex
    assert "f96ec11c6a3da" in index._itemIndex
    assert "fb609cd8319dc" in index._itemIndex
    assert "7a992350f3eb6" in index._itemIndex

    # Close Project
    SHARED._project = project  # Otherwise the signal is not emitted
    with qtbot.waitSignal(SHARED.indexCleared, timeout=1000):
        # Regression test for issue #1718
        project.closeProject()


@pytest.mark.core
def testIndex_ScanThis(mockGUI):
    """Test the tag scanner function scanThis."""
    project = NWProject()
    index = project.index

    isValid, bits, pos = index.scanThis("tag: this, and this")
    assert isValid is False

    isValid, bits, pos = index.scanThis("@")
    assert isValid is False

    isValid, bits, pos = index.scanThis("@:")
    assert isValid is False

    isValid, bits, pos = index.scanThis(" @a: b")
    assert isValid is False

    isValid, bits, pos = index.scanThis("@a:")
    assert isValid is True
    assert bits == ["@a"]
    assert pos == [0]

    isValid, bits, pos = index.scanThis("@a:b")
    assert isValid is True
    assert bits == ["@a", "b"]
    assert pos == [0, 3]

    isValid, bits, pos = index.scanThis("@a:b,c,d")
    assert isValid is True
    assert bits == ["@a", "b", "c", "d"]
    assert pos == [0, 3, 5, 7]

    isValid, bits, pos = index.scanThis("@a : b , c , d")
    assert isValid is True
    assert bits == ["@a", "b", "c", "d"]
    assert pos == [0, 5, 9, 13]

    isValid, bits, pos = index.scanThis("@tag: this, and this")
    assert isValid is True
    assert bits == ["@tag", "this", "and this"]
    assert pos == [0, 6, 12]

    isValid, bits, pos = index.scanThis("@tag: this,, and this")
    assert isValid is True
    assert bits == ["@tag", "this", "", "and this"]
    assert pos == [0, 6, 11, 13]

    isValid, bits, pos = index.scanThis("@tag: this, , and this")
    assert isValid is True
    assert bits == ["@tag", "this", "", "and this"]
    assert pos == [0, 6, 12, 14]

    project.closeProject()


@pytest.mark.core
def testIndex_CheckThese(nwGUI, fncPath, mockRnd):
    """Test the tag checker function checkThese."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    index = project.index
    index.clear()

    nHandle = project.newFile("Hello", C.hNovelRoot)
    cHandle = project.newFile("Jane", C.hCharRoot)
    wHandle = project.newFile("Earth", C.hWorldRoot)
    assert isinstance(nHandle, str)
    assert isinstance(cHandle, str)
    assert isinstance(wHandle, str)

    nItem = project.tree[nHandle]
    cItem = project.tree[cHandle]
    wItem = project.tree[wHandle]
    assert isinstance(nItem, ProjectItem)
    assert isinstance(cItem, ProjectItem)
    assert isinstance(wItem, ProjectItem)

    assert index.indexChangedSince(0) is False

    assert index.scanText(cHandle, ("# Jane Smith\n@tag: Jane\n@tag:\n@:\n"))
    assert index.scanText(wHandle, ("# Earth\n@tag: Earth\n"))
    assert index.scanText(
        nHandle,
        (
            "# Hello World!\n@pov: Jane\n@location: Earth\n@invalid: John\n"  # Checks for issue #688
        ),
    )
    assert index._tagsIndex.tagHandle("Earth") == wHandle
    assert index._tagsIndex.tagHeading("Earth") == "T0001"
    assert index._tagsIndex.tagClass("Earth") == "WORLD"

    assert index._tagsIndex.tagHandle("Jane") == cHandle
    assert index._tagsIndex.tagHeading("Jane") == "T0001"
    assert index._tagsIndex.tagClass("Jane") == "CHARACTER"

    assert index.getItemHeading(nHandle, "T0001").title == "Hello World!"  # type: ignore

    assert index.indexChangedSince(0) is True

    assert cItem.mainHeading == "H1"
    assert nItem.mainHeading == "H1"

    # Zero Items
    assert index.checkThese([], cHandle) == []

    # One Item
    assert index.checkThese(["@tag"], cHandle) == [True]
    assert index.checkThese(["@who"], cHandle) == [False]

    # Two Items
    assert index.checkThese(["@tag", "Jane"], cHandle) == [True, True]
    assert index.checkThese(["@tag", "John"], cHandle) == [True, True]
    assert index.checkThese(["@tag", "Jane"], nHandle) == [True, False]
    assert index.checkThese(["@tag", "John"], nHandle) == [True, True]
    assert index.checkThese(["@pov", "John"], nHandle) == [True, False]
    assert index.checkThese(["@pov", "Jane"], nHandle) == [True, True]
    assert index.checkThese(["@mention", "Jane"], nHandle) == [True, True]
    assert index.checkThese(["@ pov", "Jane"], nHandle) == [False, False]
    assert index.checkThese(["@what", "Jane"], nHandle) == [False, False]

    # Two w/Class Check
    assert index.checkThese(["@pov", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@focus", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@char", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@plot", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@time", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@location", "Earth"], nHandle) == [True, True]
    assert index.checkThese(["@object", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@entity", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@custom", "Earth"], nHandle) == [True, False]
    assert index.checkThese(["@mention", "Earth"], nHandle) == [True, True]

    # Three Items
    assert index.checkThese(["@tag", "Jane", "John"], cHandle) == [True, True, False]
    assert index.checkThese(["@who", "Jane", "John"], cHandle) == [False, False, False]
    assert index.checkThese(["@pov", "Jane", "John"], nHandle) == [True, True, False]
    assert index.checkThese(["@pov", "Jane", "Earth"], nHandle) == [True, True, False]
    assert index.checkThese(["@mention", "Jane", "Earth"], nHandle) == [True, True, True]
    assert index.checkThese(["@mention", "Jane", "Stuff"], nHandle) == [True, True, False]

    # Parse a Checked Value
    assert index.parseValue("Jane | Jane Smith") == ("Jane", "Jane Smith")
    assert index.parseValue("Jane  |  Jane Smith") == ("Jane", "Jane Smith")

    # Duplicates with Display Name
    assert index.checkThese(["@tag", "Jane | Jane Doe"], cHandle) == [True, True]
    assert index.checkThese(["@tag", "Jane | Jane Smith"], nHandle) == [True, False]

    project.closeProject()


@pytest.mark.core
def testIndex_ScanText(monkeypatch, nwGUI, fncPath, mockRnd):
    """Check the index text scanner."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    index = project.index

    # Some items for fail to scan tests
    dHandle = project.newFolder("Folder", C.hNovelRoot)
    xHandle = project.newFile("No Layout", C.hNovelRoot)
    xIndex = project.tree.model.indexFromHandle(xHandle)
    assert isinstance(dHandle, str)
    assert isinstance(xHandle, str)

    xItem = project.tree[xHandle]
    assert isinstance(xItem, ProjectItem)
    xItem.setLayout(nwItemLayout.NO_LAYOUT)

    # Check invalid data
    assert index.scanText(None, "Hello World!") is False  # type: ignore
    assert index.scanText(dHandle, "Hello World!") is False
    assert index.scanText(xHandle, "Hello World!") is False

    xItem.setLayout(nwItemLayout.DOCUMENT)
    xItem.setParent(None)
    assert index.scanText(xHandle, "Hello World!") is False

    # Create the trash folder
    tNode = project.tree.trash
    assert tNode is not None
    tIndex = project.tree.model.indexFromNode(tNode)
    tHandle = tNode.item.itemHandle
    assert project.tree[tHandle] is not None

    project.tree.model.multiMove([xIndex], tIndex)
    assert xItem.itemRoot == tHandle
    assert xItem.itemClass == nwItemClass.TRASH
    assert index.scanText(xHandle, "## Hello World!") is True
    assert xItem.mainHeading == "H2"

    # Create the archive root
    aHandle = project.newRoot(nwItemClass.ARCHIVE)
    aIndex = project.tree.model.indexFromHandle(aHandle)
    assert project.tree[aHandle] is not None

    project.tree.model.multiMove([xIndex], aIndex)
    assert index.scanText(xHandle, "### Hello World!") is True
    assert xItem.mainHeading == "H3"

    # Non-heading lines are skipped, and an invalid (H0) heading is ignored
    assert index.scanText(xHandle, "Just some text\n#####\n#### Hello World!") is True
    assert xItem.mainHeading == "H4"

    # A page with no valid heading at all leaves the main heading unchanged
    assert index.scanText(xHandle, "Just some text\n#####\n") is True
    assert xItem.mainHeading == "H4"

    # Make some usable items
    tHandle = project.newFile("Title", C.hNovelRoot)
    pHandle = project.newFile("Page", C.hNovelRoot)
    nHandle = project.newFile("Hello", C.hNovelRoot)
    cHandle = project.newFile("Jane", C.hCharRoot)
    sHandle = project.newFile("Scene", C.hNovelRoot)
    assert isinstance(tHandle, str)
    assert isinstance(pHandle, str)
    assert isinstance(nHandle, str)
    assert isinstance(cHandle, str)
    assert isinstance(sHandle, str)

    # Text Indexing
    # =============

    # Index correct text
    assert index.scanText(cHandle, ("# Jane Smith\n@tag: Jane\n"))
    assert index.scanText(
        nHandle,
        (
            "# Hello World!\n"
            "@pov: Jane\n"
            "@char: Jane\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really.[footnote:key]\n\n"
            "%Footnote.key: Footnote text.\n\n"
        ),
    )
    assert index._tagsIndex.tagHandle("Jane") == cHandle
    assert index._tagsIndex.tagHeading("Jane") == "T0001"
    assert index._tagsIndex.tagClass("Jane") == "CHARACTER"
    assert index.getItemHeading(nHandle, "T0001").title == "Hello World!"  # type: ignore
    assert index._itemIndex[nHandle].noteKeys("footnotes") == {"key"}  # type: ignore

    # A keyword line before any heading has been set is ignored
    assert index.scanText(pHandle, "@char: Jane\n# Page\n")

    # Title Indexing
    # ==============

    # Document File
    assert index.scanText(
        nHandle,
        (
            "# Title One\n\n"
            "% synopsis: Synopsis One.\n\n"
            "Paragraph One.\n\n"
            "## Title Two\n\n"
            "% synopsis: Synopsis Two.\n\n"
            "Paragraph Two.\n\n"
            "### Title Three\n\n"
            "% synopsis: Synopsis Three.\n\n"
            "Paragraph Three.\n\n"
            "#### Title Four\n\n"
            "% synopsis: Synopsis Four.\n\n"
            "Paragraph Four.\n\n"
            "##### Title Five\n\n"  # Not interpreted as a title, the hashes are counted as a word
            "Paragraph Five.\n\n"
        ),
    )
    assert index._itemIndex[nHandle]["T0001"].references == {}  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].references == {}  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].references == {}  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].references == {}  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].level == "H1"  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].level == "H2"  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].level == "H3"  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].level == "H4"  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].line == 1  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].line == 7  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].line == 13  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].line == 19  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].title == "Title One"  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].title == "Title Two"  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].title == "Title Three"  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].title == "Title Four"  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].charCount == 23  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].charCount == 23  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].charCount == 27  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].charCount == 56  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].wordCount == 4  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].wordCount == 4  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].wordCount == 4  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].wordCount == 9  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].paraCount == 1  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].paraCount == 1  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].paraCount == 1  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].paraCount == 3  # type: ignore

    assert index._itemIndex[nHandle]["T0001"].synopsis == "Synopsis One."  # type: ignore
    assert index._itemIndex[nHandle]["T0002"].synopsis == "Synopsis Two."  # type: ignore
    assert index._itemIndex[nHandle]["T0003"].synopsis == "Synopsis Three."  # type: ignore
    assert index._itemIndex[nHandle]["T0004"].synopsis == "Synopsis Four."  # type: ignore

    # Note File
    assert index.scanText(cHandle, ("# Title One\n\n@tag: One\n\n% synopsis: Synopsis One.\n\nParagraph One.\n\n"))
    assert index._itemIndex[cHandle]["T0001"].references == {}  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].level == "H1"  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].line == 1  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].title == "Title One"  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].charCount == 23  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].wordCount == 4  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].paraCount == 1  # type: ignore
    assert index._itemIndex[cHandle]["T0001"].synopsis == "Synopsis One."  # type: ignore

    # Valid and Invalid References
    assert index.scanText(
        sHandle,
        (
            "# Title One\n\n"
            "@pov: One\n\n"  # Valid
            "@char: Two\n\n"  # Invalid tag
            "@:\n\n"  # Invalid line
            "% synopsis: Synopsis One.\n\n"
            "Paragraph One.\n\n"
        ),
    )
    assert index._itemIndex[sHandle]["T0001"].references == {  # type: ignore
        "one": {"@pov"},
        "two": {"@char"},
    }

    # Special Titles
    # ==============

    assert index.scanText(tHandle, ("#! My Project\n\n>> By Jane Doe <<\n\n"))
    assert index._itemIndex[cHandle]["T0001"].references == {}  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].level == "H1"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].line == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].title == "My Project"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].charCount == 21  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].wordCount == 5  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].paraCount == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].synopsis == ""  # type: ignore

    assert index.scanText(tHandle, ("##! Prologue\n\nIn the beginning there was time ...\n\n"))
    assert index._itemIndex[cHandle]["T0001"].references == {}  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].level == "H2"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].line == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].title == "Prologue"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].charCount == 43  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].wordCount == 8  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].paraCount == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].synopsis == ""  # type: ignore

    assert index.scanText(tHandle, ("###! Hard Scene\n\nWe're no longer following Jane, but John!\n\n"))
    assert index._itemIndex[cHandle]["T0001"].references == {}  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].level == "H3"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].line == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].title == "Hard Scene"  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].charCount == 51  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].wordCount == 9  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].paraCount == 1  # type: ignore
    assert index._itemIndex[tHandle]["T0001"].synopsis == ""  # type: ignore

    # Page wo/Title
    # =============

    project.tree[pHandle]._layout = nwItemLayout.DOCUMENT  # type: ignore
    assert index.scanText(pHandle, ("This is a page with some text on it.\n\n"))
    assert index._itemIndex[pHandle]["T0000"].references == {}  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].level == "H0"  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].line == 0  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].title == ""  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].charCount == 36  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].wordCount == 9  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].paraCount == 1  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].synopsis == ""  # type: ignore

    project.tree[pHandle]._layout = nwItemLayout.NOTE  # type: ignore
    assert index.scanText(pHandle, ("This is a page with some text on it.\n\n"))
    assert index._itemIndex[pHandle]["T0000"].references == {}  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].level == "H0"  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].line == 0  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].title == ""  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].charCount == 36  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].wordCount == 9  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].paraCount == 1  # type: ignore
    assert index._itemIndex[pHandle]["T0000"].synopsis == ""  # type: ignore

    project.closeProject()


@pytest.mark.core
def testIndex_ChangedRefsSignal(qtbot, nwGUI, fncPath, mockRnd):
    """Check that scanning emits updated backreference handles."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    index = project.index

    # The SharedData signal proxy only emits for the active project
    SHARED._project = project

    nHandle = project.newFile("Hello", C.hNovelRoot)
    cHandle = project.newFile("Jane", C.hCharRoot)
    wHandle = project.newFile("Earth", C.hWorldRoot)
    assert isinstance(nHandle, str)
    assert isinstance(cHandle, str)
    assert isinstance(wHandle, str)

    assert index.scanText(cHandle, "# Jane Smith\n@tag: Jane\n")
    assert index.scanText(wHandle, "# Earth\n@tag: Earth\n")

    with qtbot.waitSignal(SHARED.indexChangedRefs, timeout=1000) as blocker:
        assert index.scanText(nHandle, "# Hello\n@char: Jane\n@location: Earth\n")
    assert blocker.args == [[cHandle, wHandle]]

    with qtbot.waitSignal(SHARED.indexChangedRefs, timeout=1000) as blocker:
        assert index.scanText(nHandle, "# Hello\n@char: Jane\n")
    assert blocker.args == [[cHandle, wHandle]]

    project.closeProject()


@pytest.mark.core
def testIndex_CommentKeys(monkeypatch, nwGUI, fncPath, mockRnd):
    """Check the index comment key generator."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    index = project.index

    nKeys = 1000

    # Generate footnote keys
    keys = set()
    for _ in range(nKeys):
        key = index.newCommentKey(C.hSceneDoc, nwComment.FOOTNOTE)
        assert key not in keys
        assert key != "err"
        keys.add(key)
    assert len(keys) == nKeys

    # Generate comment keys
    keys = set()
    for _ in range(nKeys):
        key = index.newCommentKey(C.hSceneDoc, nwComment.COMMENT)
        assert key not in keys
        keys.add(key)
    assert len(keys) == nKeys

    # Induce collision
    with monkeypatch.context() as mp:
        mp.setattr("random.choices", lambda *a, **k: "aaaa")
        assert index.newCommentKey(C.hSceneDoc, nwComment.FOOTNOTE) == "faaaa"
        assert index.newCommentKey(C.hSceneDoc, nwComment.FOOTNOTE) == "err"

    # Check invalid comment style
    assert index.newCommentKey(C.hSceneDoc, None) == "err"  # type: ignore


@pytest.mark.core
def testIndex_ExtractData(nwGUI, fncPath, mockRnd):
    """Check the index data extraction functions."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    index = project.index
    index.reIndexHandle(C.hNovelRoot)
    index.reIndexHandle(C.hPlotRoot)
    index.reIndexHandle(C.hCharRoot)
    index.reIndexHandle(C.hWorldRoot)
    index.reIndexHandle(C.hTitlePage)
    index.reIndexHandle(C.hChapterDir)
    index.reIndexHandle(C.hChapterDoc)
    index.reIndexHandle(C.hSceneDoc)

    nHandle = project.newFile("Hello", C.hNovelRoot)
    cHandle = project.newFile("Jane", C.hCharRoot)
    dHandle = project.newFile("John", C.hCharRoot)
    assert isinstance(nHandle, str)
    assert isinstance(cHandle, str)
    assert isinstance(dHandle, str)

    assert index.getItemHeading("", "") is None
    assert index.getItemHeading(C.hNovelRoot, "") is None

    assert index.scanText(cHandle, ("# Jane Smith\n@tag: Jane\n"))
    assert index.scanText(dHandle, ("# John Smith\n@tag: John\n"))
    assert index.scanText(
        nHandle,
        (
            "# Hello World!\n"
            "@tag: Scene\n"
            "@pov: Jane\n"
            "@char: Jane, John\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really.\n"
        ),
    )

    # The novel file should have the correct counts
    cC, wC, pC = index.getCounts(nHandle)
    assert cC == 62  # Characters in text and title only
    assert wC == 12  # Words in text and title only
    assert pC == 2  # Paragraphs in text only

    # Check that excluded files can be skipped
    project.tree[nHandle].setActive(False)  # type: ignore

    # getReferenceForHeader
    # =====================
    assert index.getReferenceForHeader(nHandle, 1, "@pov") == ["Jane"]
    assert index.getReferenceForHeader(nHandle, 1, "@char") == ["Jane", "John"]
    assert index.getReferenceForHeader(nHandle, 1, "@focus") == []
    assert index.getReferenceForHeader("00000", 1, "@focus") == []

    # getBackReferenceList
    # ====================

    # None handle should return an empty dict
    assert index.getBackReferenceList(None) == {}  # type: ignore

    # The Title Page file should have no references as it has no tag
    assert index.getBackReferenceList(C.hTitlePage) == {}

    # The character file should have a record of the reference from the novel file
    refs = index.getBackReferenceList(cHandle)
    assert refs[nHandle][0] == "T0001"

    # getTagSource
    # ============

    assert index.getTagSource("Jane") == (cHandle, "T0001")
    assert index.getTagSource("John") == (dHandle, "T0001")
    assert index.getTagSource("Hans") == (None, "T0000")

    # getDocumentTags
    # ===============
    assert index.getDocumentTags(cHandle) == ["jane"]
    assert index.getDocumentTags(None) == []

    # getKeyWordTags
    # ==============
    assert index.getKeyWordTags("@mention") == {"Jane", "John", "Scene"}
    assert index.getKeyWordTags("@char") == {"Jane", "John"}
    assert index.getKeyWordTags("@plot") == set()
    assert index.getKeyWordTags("@tag") == set()

    # getTagsData
    # ===========
    assert list(index.getTagsData()) == [
        (
            "jane",
            "Jane",
            "CHARACTER",
            index.getItemData(cHandle),
            index.getItemHeading(cHandle, "T0001"),
        ),
        (
            "john",
            "John",
            "CHARACTER",
            index.getItemData(dHandle),
            index.getItemHeading(dHandle, "T0001"),
        ),
    ]

    # getItemHeading
    # ==============
    assert list(index.iterItemHeadings(cHandle)) == [("T0001", index.getItemHeading(cHandle, "T0001"))]
    assert list(index.iterItemHeadings(dHandle)) == [("T0001", index.getItemHeading(dHandle, "T0001"))]
    assert list(index.iterItemHeadings(C.hInvalid)) == []

    # getSingleTag
    # ============
    assert index.getSingleTag("jane") == (
        "Jane",
        "CHARACTER",
        index.getItemData(cHandle),
        index.getItemHeading(cHandle, "T0001"),
    )
    assert index.getSingleTag("foobar") == ("", "", None, None)

    # getCounts
    # =========
    # For whole text and sections

    # Invalid handle or title should return 0s
    assert index.getCounts("stuff") == (0, 0, 0)
    assert index.getCounts(nHandle, "stuff") == (0, 0, 0)

    # Get section counts for a novel file
    assert index.scanText(
        nHandle,
        (
            "# Hello World!\n"
            "@pov: Jane\n"
            "@char: Jane\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really.\n\n"
            "# Hello World!\n"
            "@pov: Jane\n"
            "@char: Jane\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really. She's still awesome though.\n"
        ),
    )

    # Whole document
    cC, wC, pC = index.getCounts(nHandle)
    assert cC == 152
    assert wC == 28
    assert pC == 4

    # First part
    cC, wC, pC = index.getCounts(nHandle, "T0001")
    assert cC == 62
    assert wC == 12
    assert pC == 2

    # Second part
    cC, wC, pC = index.getCounts(nHandle, "T0002")
    assert cC == 90
    assert wC == 16
    assert pC == 2

    # Get section counts for a note file
    assert index.scanText(
        cHandle,
        (
            "# Hello World!\n"
            "@pov: Jane\n"
            "@char: Jane\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really.\n\n"
            "# Hello World!\n"
            "@pov: Jane\n"
            "@char: Jane\n\n"
            "% this is a comment\n\n"
            "This is a story about Jane Smith.\n\n"
            "Well, not really. She's still awesome though.\n"
        ),
    )
    # Whole document
    cC, wC, pC = index.getCounts(cHandle)
    assert cC == 152
    assert wC == 28
    assert pC == 4

    # First part
    cC, wC, pC = index.getCounts(cHandle, "T0001")
    assert cC == 62
    assert wC == 12
    assert pC == 2

    # Second part
    cC, wC, pC = index.getCounts(cHandle, "T0002")
    assert cC == 90
    assert wC == 16
    assert pC == 2

    # Novel Stats
    # ===========

    hHandle = project.newFile("Chapter", C.hNovelRoot)
    sHandle = project.newFile("Scene One", C.hNovelRoot)
    tHandle = project.newFile("Scene Two", C.hNovelRoot)

    assert project.tree[hHandle].itemLayout == nwItemLayout.DOCUMENT  # type: ignore
    assert project.tree[sHandle].itemLayout == nwItemLayout.DOCUMENT  # type: ignore
    assert project.tree[tHandle].itemLayout == nwItemLayout.DOCUMENT  # type: ignore

    assert index.scanText(hHandle, "## Chapter One\n\n")  # type: ignore
    assert index.scanText(sHandle, "### Scene One\n\n")  # type: ignore
    assert index.scanText(tHandle, "### Scene Two\n\n")  # type: ignore

    assert [(h, t) for h, t, _ in index._itemIndex.iterNovelStructure(activeOnly=False)] == [
        (C.hTitlePage, "T0001"),
        (C.hChapterDoc, "T0001"),
        (C.hSceneDoc, "T0001"),
        (nHandle, "T0001"),
        (nHandle, "T0002"),
        (hHandle, "T0001"),
        (sHandle, "T0001"),
        (tHandle, "T0001"),
    ]

    assert [(h, t) for h, t, _ in index._itemIndex.iterNovelStructure(activeOnly=True)] == [
        (C.hTitlePage, "T0001"),
        (C.hChapterDoc, "T0001"),
        (C.hSceneDoc, "T0001"),
        (hHandle, "T0001"),
        (sHandle, "T0001"),
        (tHandle, "T0001"),
    ]

    # Add a fake handle to the tree and check that it's ignored
    project.tree._items["0000000000000"] = None  # type: ignore
    project.tree._nodes["0000000000000"] = None  # type: ignore
    assert [(h, t) for h, t, _ in index._itemIndex.iterNovelStructure(activeOnly=False)] == [
        (C.hTitlePage, "T0001"),
        (C.hChapterDoc, "T0001"),
        (C.hSceneDoc, "T0001"),
        (nHandle, "T0001"),
        (nHandle, "T0002"),
        (hHandle, "T0001"),
        (sHandle, "T0001"),
        (tHandle, "T0001"),
    ]
    del project.tree._items["0000000000000"]
    del project.tree._nodes["0000000000000"]

    # Extract stats
    assert index.getNovelWordCount(activeOnly=False) == 43
    assert index.getNovelWordCount(activeOnly=True) == 15
    assert index.getNovelWordCount(rootHandle=C.hNovelRoot, activeOnly=False) == 43
    assert index.getNovelWordCount(rootHandle=C.hNovelRoot, activeOnly=True) == 15
    assert index.getNovelWordCount(rootHandle=C.hWorldRoot, activeOnly=False) == 0
    assert index.getNovelWordCount(rootHandle=C.hWorldRoot, activeOnly=True) == 0
    assert index.getNovelTitleCounts(activeOnly=False) == [0, 3, 2, 3, 0]
    assert index.getNovelTitleCounts(activeOnly=True) == [0, 1, 2, 3, 0]

    # Table of Contents
    assert index.getTableOfContents(C.hNovelRoot, 0, activeOnly=True) == []
    assert index.getTableOfContents(C.hNovelRoot, 1, activeOnly=True) == [
        (f"{C.hTitlePage}:T0001", 1, "New Novel", 15),
    ]
    assert index.getTableOfContents(C.hNovelRoot, 2, activeOnly=True) == [
        (f"{C.hTitlePage}:T0001", 1, "New Novel", 5),
        (f"{C.hChapterDoc}:T0001", 2, "New Chapter", 4),
        (f"{hHandle}:T0001", 2, "Chapter One", 6),
    ]
    assert index.getTableOfContents(C.hNovelRoot, 3, activeOnly=True) == [
        (f"{C.hTitlePage}:T0001", 1, "New Novel", 5),
        (f"{C.hChapterDoc}:T0001", 2, "New Chapter", 2),
        (f"{C.hSceneDoc}:T0001", 3, "New Scene", 2),
        (f"{hHandle}:T0001", 2, "Chapter One", 2),
        (f"{sHandle}:T0001", 3, "Scene One", 2),
        (f"{tHandle}:T0001", 3, "Scene Two", 2),
    ]

    assert index.getTableOfContents(C.hNovelRoot, 0, activeOnly=False) == []
    assert index.getTableOfContents(C.hNovelRoot, 1, activeOnly=False) == [
        (f"{C.hTitlePage}:T0001", 1, "New Novel", 9),
        (f"{nHandle}:T0001", 1, "Hello World!", 12),
        (f"{nHandle}:T0002", 1, "Hello World!", 22),
    ]

    assert index.saveIndex() is True
    assert project.saveProject() is True
    project.closeProject()


@pytest.mark.core
def testTagsIndex_Main():
    """Check the TagsIndex class."""
    tagsIndex = TagsIndex()
    assert tagsIndex._tags == {}

    # Expected data
    content = {
        "tag1": {
            "name": "Tag1",
            "display": "Tag 1",
            "handle": "0000000000001",
            "heading": "T0001",
            "class": nwItemClass.NOVEL.name,
        },
        "tag2": {
            "name": "Tag2",
            "display": "Tag 2",
            "handle": "0000000000002",
            "heading": "T0002",
            "class": nwItemClass.CHARACTER.name,
        },
        "tag3": {
            "name": "Tag3",
            "display": "Tag 3",
            "handle": "0000000000003",
            "heading": "T0003",
            "class": nwItemClass.PLOT.name,
        },
    }

    # Add data
    tagsIndex.add("Tag1", "Tag 1", "0000000000001", "T0001", "NOVEL")
    tagsIndex.add("Tag2", "Tag 2", "0000000000002", "T0002", "CHARACTER")
    tagsIndex.add("Tag3", "Tag 3", "0000000000003", "T0003", "PLOT")
    assert tagsIndex._tags == content

    # The per-class name cache is kept in sync with the added tags, as
    # is the "*" bucket holding the set of all tag names regardless
    # of class, used when filterTagNames is called with None
    assert tagsIndex.filterTagNames(nwItemClass.NOVEL.name) == {"Tag1"}
    assert tagsIndex.filterTagNames(nwItemClass.CHARACTER.name) == {"Tag2"}
    assert tagsIndex.filterTagNames(nwItemClass.PLOT.name) == {"Tag3"}
    assert tagsIndex.filterTagNames(nwItemClass.WORLD.name) == set()
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}

    # Re-adding a tag under a different class moves it in the cache
    # rather than leaving a stale entry behind in the old class, and
    # it stays a single entry in the all-tags bucket
    tagsIndex.add("Tag1", "Tag 1", "0000000000001", "T0001", "CHARACTER")
    assert tagsIndex.filterTagNames(nwItemClass.NOVEL.name) == set()
    assert tagsIndex.filterTagNames(nwItemClass.CHARACTER.name) == {"Tag1", "Tag2"}
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}
    tagsIndex.add("Tag1", "Tag 1", "0000000000001", "T0001", "NOVEL")
    assert tagsIndex.filterTagNames(nwItemClass.NOVEL.name) == {"Tag1"}
    assert tagsIndex.filterTagNames(nwItemClass.CHARACTER.name) == {"Tag2"}
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}

    # Get items
    assert tagsIndex["Tag1"] == content["tag1"]
    assert tagsIndex["Tag2"] == content["tag2"]
    assert tagsIndex["Tag3"] == content["tag3"]
    assert tagsIndex["Tag4"] is None

    # Contains
    assert "Tag1" in tagsIndex
    assert "Tag2" in tagsIndex
    assert "Tag3" in tagsIndex
    assert "Tag4" not in tagsIndex

    # Read back names
    assert tagsIndex.tagName("Tag1") == "Tag1"
    assert tagsIndex.tagName("Tag2") == "Tag2"
    assert tagsIndex.tagName("Tag3") == "Tag3"
    assert tagsIndex.tagName("Tag4") == ""

    # Read back display names
    assert tagsIndex.tagDisplay("Tag1") == "Tag 1"
    assert tagsIndex.tagDisplay("Tag2") == "Tag 2"
    assert tagsIndex.tagDisplay("Tag3") == "Tag 3"
    assert tagsIndex.tagDisplay("Tag4") == ""

    # Read back handles
    assert tagsIndex.tagHandle("Tag1") == "0000000000001"
    assert tagsIndex.tagHandle("Tag2") == "0000000000002"
    assert tagsIndex.tagHandle("Tag3") == "0000000000003"
    assert tagsIndex.tagHandle("Tag4") is None

    # Read back headings
    assert tagsIndex.tagHeading("Tag1") == "T0001"
    assert tagsIndex.tagHeading("Tag2") == "T0002"
    assert tagsIndex.tagHeading("Tag3") == "T0003"
    assert tagsIndex.tagHeading("Tag4") == "T0000"

    # Read back classes
    assert tagsIndex.tagClass("Tag1") == nwItemClass.NOVEL.name
    assert tagsIndex.tagClass("Tag2") == nwItemClass.CHARACTER.name
    assert tagsIndex.tagClass("Tag3") == nwItemClass.PLOT.name
    assert tagsIndex.tagClass("Tag4") is None

    # Change class of item. This must not touch the all-tags bucket,
    # since the tag itself isn't being added or removed
    tagsIndex.updateClass("0000000000003", nwItemClass.WORLD.name)
    assert tagsIndex.tagClass("Tag3") == nwItemClass.WORLD.name
    assert tagsIndex.filterTagNames(nwItemClass.PLOT.name) == set()
    assert tagsIndex.filterTagNames(nwItemClass.WORLD.name) == {"Tag3"}
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}
    tagsIndex.updateClass("0000000000003", nwItemClass.PLOT.name)
    assert tagsIndex.tagClass("Tag3") == nwItemClass.PLOT.name
    assert tagsIndex.filterTagNames(nwItemClass.WORLD.name) == set()
    assert tagsIndex.filterTagNames(nwItemClass.PLOT.name) == {"Tag3"}
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}

    # Calling updateClass with the class the item already has is a no-op
    tagsIndex.updateClass("0000000000003", nwItemClass.PLOT.name)
    assert tagsIndex.filterTagNames(nwItemClass.PLOT.name) == {"Tag3"}

    # Calling updateClass with a handle that isn't in the index does nothing
    tagsIndex.updateClass("0000000000099", nwItemClass.WORLD.name)
    assert tagsIndex.filterTagNames(nwItemClass.WORLD.name) == set()

    # Pack Data
    assert tagsIndex.packData() == content

    # Delete the second key and a non-existent key. Deleting must also
    # drop the tag from the all-tags bucket, unlike a reclassification
    del tagsIndex["Tag2"]
    del tagsIndex["Tag4"]
    assert "Tag1" in tagsIndex
    assert "Tag2" not in tagsIndex
    assert "Tag3" in tagsIndex
    assert "Tag4" not in tagsIndex
    assert tagsIndex.filterTagNames(nwItemClass.CHARACTER.name) == set()
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag3"}

    # Clear and reload
    tagsIndex.clear()
    assert tagsIndex._tags == {}
    assert tagsIndex._cache == {}
    assert tagsIndex.packData() == {}
    assert tagsIndex.filterTagNames(nwItemClass.NOVEL.name) == set()
    assert tagsIndex.filterTagNames(None) == set()

    tagsIndex.unpackData(content)
    assert tagsIndex._tags == content
    assert tagsIndex.packData() == content
    assert tagsIndex.filterTagNames(nwItemClass.NOVEL.name) == {"Tag1"}
    assert tagsIndex.filterTagNames(nwItemClass.CHARACTER.name) == {"Tag2"}
    assert tagsIndex.filterTagNames(nwItemClass.PLOT.name) == {"Tag3"}
    assert tagsIndex.filterTagNames(None) == {"Tag1", "Tag2", "Tag3"}

    # Unpack Errors
    # =============
    tagsIndex.clear()

    # Invalid data type
    with pytest.raises(ValueError, match="tagsIndex is not a dict"):
        tagsIndex.unpackData([])  # type: ignore

    # Invalid key
    with pytest.raises(ValueError, match="tagsIndex key must be a string"):
        tagsIndex.unpackData({
            1234: {
                "name": "Tag1",
                "display": "Tag1",
                "handle": "0000000000001",
                "heading": "T0001",
                "class": "NOVEL",
            }
        })

    # Invalid entry
    with pytest.raises(ValueError, match="tagsIndex entry is not a dict"):
        tagsIndex.unpackData({"tag1": None})

    # Invalid name
    with pytest.raises(ValueError, match="tagsIndex name is not a string"):
        tagsIndex.unpackData({
            "tag1": {
                "name": 1234,
                "display": "Tag1",
                "handle": "0000000000001",
                "heading": "T0001",
                "class": "NOVEL",
            }
        })

    # Invalid display
    with pytest.raises(ValueError, match="tagsIndex display is not a string"):
        tagsIndex.unpackData({
            "tag1": {
                "name": "Tag1",
                "display": 1234,
                "handle": "0000000000001",
                "heading": "T0001",
                "class": "NOVEL",
            }
        })

    # Invalid handle
    with pytest.raises(ValueError, match="tagsIndex handle must be a handle"):
        tagsIndex.unpackData({
            "tag1": {
                "name": "Tag1",
                "display": "Tag1",
                "handle": "blablabla",
                "heading": "T0001",
                "class": "NOVEL",
            }
        })

    # Invalid heading
    with pytest.raises(ValueError, match="tagsIndex heading must be a title tag"):
        tagsIndex.unpackData({
            "tag1": {
                "name": "Tag1",
                "display": "Tag1",
                "handle": "0000000000001",
                "heading": "stuff",
                "class": "NOVEL",
            }
        })

    # Invalid class
    with pytest.raises(ValueError, match="tagsIndex handle must be an nwItemClass"):
        tagsIndex.unpackData({
            "tag1": {
                "name": "Tag1",
                "display": "Tag1",
                "handle": "0000000000001",
                "heading": "T0001",
                "class": "STUFF",
            }
        })


@pytest.mark.core
def testItemIndex_Main(nwGUI, fncPath, mockRnd):
    """Check the ItemIndex class."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    project.index.clear()

    nHandle = C.hTitlePage
    cHandle = C.hChapterDoc
    sHandle = C.hSceneDoc

    assert project.index.saveIndex() is True
    itemIndex = project.index._itemIndex

    # The index should be empty
    assert nHandle not in itemIndex
    assert cHandle not in itemIndex
    assert sHandle not in itemIndex

    # Add Items
    # =========
    assert cHandle not in itemIndex

    # Add the novel chapter file
    itemIndex.add(cHandle, project.tree[cHandle])  # type: ignore
    assert cHandle in itemIndex
    assert itemIndex[cHandle].item == project.tree[cHandle]  # type: ignore
    assert itemIndex.allItemTags(cHandle) == []
    assert list(itemIndex.iterItemHeaders(cHandle))[0][0] == "T0000"

    # Add a heading to the item, which should replace the T000000 heading
    assert itemIndex.addItemHeading(cHandle, 1, "H2", "Chapter One") == "T0001"
    assert list(itemIndex.iterItemHeaders(cHandle))[0][0] == "T0001"

    # Add a heading to an invalid item
    assert itemIndex.addItemHeading(C.hInvalid, 1, "H1", "Stuff") == "T0000"

    # Set the remaining data values
    itemIndex.setHeadingCounts(cHandle, "T0001", 60, 10, 2)
    itemIndex.setHeadingComment(cHandle, "T0001", nwComment.SYNOPSIS, "", "In the beginning ...")
    itemIndex.setHeadingTag(cHandle, "T0001", "One")
    itemIndex.addHeadingRef(cHandle, "T0001", ["Jane"], "@pov")
    itemIndex.addHeadingRef(cHandle, "T0001", ["Jane"], "@focus")
    itemIndex.addHeadingRef(cHandle, "T0001", ["Jane", "John"], "@char")
    idxData = itemIndex.packData()

    assert idxData[cHandle]["T0001"]["meta"] == {
        "level": "H2",
        "line": 1,
        "title": "Chapter One",
        "tag": "one",
        "counts": (60, 10, 2),
    }
    assert "@pov" in idxData[cHandle]["T0001"]["refs"]["jane"]
    assert "@focus" in idxData[cHandle]["T0001"]["refs"]["jane"]
    assert "@char" in idxData[cHandle]["T0001"]["refs"]["jane"]
    assert "@char" in idxData[cHandle]["T0001"]["refs"]["john"]
    assert idxData[cHandle]["T0001"]["summary"] == "In the beginning ..."

    # Add the other two files
    itemIndex.add(nHandle, project.tree[nHandle])  # type: ignore
    itemIndex.add(sHandle, project.tree[sHandle])  # type: ignore
    itemIndex.addItemHeading(nHandle, 1, "H1", "Novel")
    itemIndex.addItemHeading(sHandle, 1, "H3", "Scene One")

    # Check Item and Heading Direct Access
    # ====================================

    # Check repr strings
    assert repr(itemIndex[nHandle]) == f"<IndexNode handle='{nHandle}'>"
    assert repr(itemIndex[nHandle]["T0001"]) == "<IndexHeading key='T0001'>"  # type: ignore

    # Check content of a single item
    assert "T0001" in itemIndex[nHandle]  # type: ignore
    assert itemIndex[cHandle].allTags() == ["one"]  # type: ignore

    # Check the content of a single heading
    assert itemIndex[cHandle]["T0001"].key == "T0001"  # type: ignore
    assert itemIndex[cHandle]["T0001"].level == "H2"  # type: ignore
    assert itemIndex[cHandle]["T0001"].line == 1  # type: ignore
    assert itemIndex[cHandle]["T0001"].title == "Chapter One"  # type: ignore
    assert itemIndex[cHandle]["T0001"].tag == "one"  # type: ignore
    assert itemIndex[cHandle]["T0001"].charCount == 60  # type: ignore
    assert itemIndex[cHandle]["T0001"].wordCount == 10  # type: ignore
    assert itemIndex[cHandle]["T0001"].paraCount == 2  # type: ignore
    assert itemIndex[cHandle]["T0001"].synopsis == "In the beginning ..."  # type: ignore
    assert "jane" in itemIndex[cHandle]["T0001"].references  # type: ignore
    assert "john" in itemIndex[cHandle]["T0001"].references  # type: ignore

    # Check heading level setter
    itemIndex[cHandle]["T0001"].setLevel("H3")  # Change it  # type: ignore
    assert itemIndex[cHandle]["T0001"].level == "H3"  # type: ignore
    itemIndex[cHandle]["T0001"].setLevel("H2")  # Set it back  # type: ignore
    assert itemIndex[cHandle]["T0001"].level == "H2"  # type: ignore
    itemIndex[cHandle]["T0001"].setLevel("H5")  # Invalid level  # type: ignore
    assert itemIndex[cHandle]["T0001"].level == "H2"  # type: ignore

    # Data Extraction
    # ===============

    # Get headers
    allHeads = list(itemIndex.iterAllHeaders())
    assert allHeads[0][0] == cHandle
    assert allHeads[1][0] == nHandle
    assert allHeads[2][0] == sHandle
    assert allHeads[0][1] == "T0001"
    assert allHeads[1][1] == "T0001"
    assert allHeads[2][1] == "T0001"

    # Ask for stuff that doesn't exist
    assert itemIndex.allItemTags("blablabla") == []

    # Novel Structure
    # ===============

    # Add a second novel
    mHandle = project.newRoot(nwItemClass.NOVEL)
    uHandle = project.newFile("Title Page", mHandle)
    assert uHandle is not None
    itemIndex.add(uHandle, project.tree[uHandle])  # type: ignore
    itemIndex.addItemHeading(uHandle, "T0001", "H1", "Novel 2")  # type: ignore
    assert uHandle in itemIndex

    # Structure of all novels
    nStruct = list(itemIndex.iterNovelStructure())
    assert len(nStruct) == 4
    assert nStruct[0][0] == nHandle
    assert nStruct[1][0] == cHandle
    assert nStruct[2][0] == sHandle
    assert nStruct[3][0] == uHandle

    # Novel structure with root handle set
    nStruct = list(itemIndex.iterNovelStructure(rHandle=C.hNovelRoot))
    assert len(nStruct) == 3
    assert nStruct[0][0] == nHandle
    assert nStruct[1][0] == cHandle
    assert nStruct[2][0] == sHandle

    nStruct = list(itemIndex.iterNovelStructure(rHandle=mHandle))
    assert len(nStruct) == 1
    assert nStruct[0][0] == uHandle

    # Inject garbage into tree
    project.tree._items["stuff"] = None  # type: ignore
    project.tree._nodes["stuff"] = None  # type: ignore
    nStruct = list(itemIndex.iterNovelStructure())
    assert len(nStruct) == 4
    assert nStruct[0][0] == nHandle
    assert nStruct[1][0] == cHandle
    assert nStruct[2][0] == sHandle
    assert nStruct[3][0] == uHandle

    # Skip excluded
    project.tree[sHandle].setActive(False)  # type: ignore
    nStruct = list(itemIndex.iterNovelStructure(activeOnly=True))
    assert len(nStruct) == 3
    assert nStruct[0][0] == nHandle
    assert nStruct[1][0] == cHandle
    assert nStruct[2][0] == uHandle

    # Delete new item
    del itemIndex[uHandle]  # type: ignore
    assert uHandle not in itemIndex

    # Unpack Error Handling
    # =====================

    # Pack/unpack should restore state
    content = itemIndex.packData()
    itemIndex.clear()
    itemIndex.unpackData(content)
    assert itemIndex.packData() == content
    itemIndex.clear()

    # Generating a note key fails for an invalid style or handle
    assert itemIndex.genNewNoteKey(cHandle, "invalid_style") == "err"  # type: ignore
    assert itemIndex.genNewNoteKey(C.hInvalid, "footnotes") == "err"

    # Entries for handles no longer in the project tree are dropped
    staleHandle = "0000000000099"
    assert project.tree[staleHandle] is None
    withStale = dict(content)
    withStale[staleHandle] = next(iter(content.values()))
    itemIndex.unpackData(withStale)
    assert staleHandle not in itemIndex
    assert itemIndex.packData() == content
    itemIndex.clear()

    # Data must be dictionary
    with pytest.raises(ValueError, match="itemIndex is not a dict"):
        itemIndex.unpackData("stuff")  # type: ignore

    # Keys must be valid handles
    with pytest.raises(ValueError, match="itemIndex keys must be handles"):
        itemIndex.unpackData({"stuff": "more stuff"})
