"""
novelWriter - Project Item Tests
================================

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

import copy

import pytest

from PyQt6.QtGui import QIcon

from novelwriter import CONFIG
from novelwriter.core.item import ProjectItem
from novelwriter.core.project import NWProject
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType

from tests.helpers import C, buildTestProject


@pytest.mark.core
def testProjectItem_Setters(mockGUI, mockRnd, fncPath):
    """Test all the simple setters for the ProjectItem class."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    item = ProjectItem(project, "0000000000000")
    assert item.itemHandle == "0000000000000"

    statusKeys = ["s000000", "s000001", "s000002", "s000003"]
    importKeys = ["i000004", "i000005", "i000006", "i000007"]

    # Name
    item.setName("A Name")
    assert item.itemName == "A Name"
    item.setName("\t A Name   ")
    assert item.itemName == "A Name"
    item.setName("\t A\t\u2009\u202f\u2002\u2003\u2028\u2029Name   ")
    assert item.itemName == "A Name"
    item.setName(123)
    assert item.itemName == ""

    # Parent
    item.setParent(None)
    assert item.itemParent is None
    item.setParent(123)
    assert item.itemParent is None
    item.setParent("0123456789abcdef")
    assert item.itemParent is None
    item.setParent("0123456789abg")
    assert item.itemParent is None
    item.setParent("0123456789abc")
    assert item.itemParent == "0123456789abc"

    # Root
    item.setRoot(None)
    assert item.itemRoot is None
    item.setRoot(123)
    assert item.itemRoot is None
    item.setRoot("0123456789abcdef")
    assert item.itemRoot is None
    item.setRoot("0123456789abg")
    assert item.itemRoot is None
    item.setRoot("0123456789abc")
    assert item.itemRoot == "0123456789abc"

    # Order
    item.setOrder(None)
    assert item.itemOrder == 0
    item.setOrder("1")
    assert item.itemOrder == 1
    item.setOrder(1)
    assert item.itemOrder == 1

    # Importance
    item._class = nwItemClass.CHARACTER
    item.setImport("Word")
    assert item.itemImport == importKeys[0]  # Default
    for key in importKeys:
        item.setImport(key)
        assert item.itemImport == key

    # Status
    item._class = nwItemClass.NOVEL
    item.setStatus("Word")
    assert item.itemStatus == statusKeys[0]  # Default
    for key in statusKeys:
        item.setStatus(key)
        assert item.itemStatus == key

    # Status/Importance Wrapper
    item._class = nwItemClass.CHARACTER
    for key in importKeys:
        item.setImport(key)
        assert item.itemImport == key
        assert item.itemStatus == statusKeys[3]  # Should not change

    item._class = nwItemClass.NOVEL
    for key in statusKeys:
        item.setStatus(key)
        assert item.itemImport == importKeys[3]  # Should not change
        assert item.itemStatus == key

    # Expanded
    item.setExpanded(8)
    assert item.isExpanded is False
    item.setExpanded(None)
    assert item.isExpanded is False
    item.setExpanded("None")
    assert item.isExpanded is False
    item.setExpanded("What?")
    assert item.isExpanded is False
    item.setExpanded("True")
    assert item.isExpanded is False
    item.setExpanded(True)
    assert item.isExpanded is True

    # Active
    item.setActive(8)
    assert item.isActive is False
    item.setActive(None)
    assert item.isActive is False
    item.setActive("None")
    assert item.isActive is False
    item.setActive("What?")
    assert item.isActive is False
    item.setActive("True")
    assert item.isActive is False
    item.setActive(True)
    assert item.isActive is True

    # CharCount
    item.setCharCount(None)
    assert item.charCount == 0
    item.setCharCount("1")
    assert item.charCount == 0
    item.setCharCount(1)
    assert item.charCount == 1

    # WordCount
    item.setWordCount(None)
    assert item.wordCount == 0
    item.setWordCount("1")
    assert item.wordCount == 0
    item.setWordCount(1)
    assert item.wordCount == 1

    # ParaCount
    item.setParaCount(None)
    assert item.paraCount == 0
    item.setParaCount("1")
    assert item.paraCount == 0
    item.setParaCount(1)
    assert item.paraCount == 1

    # MainCount
    item.setWordCount(123)
    item.setCharCount(1234)
    CONFIG.useCharCount = False
    assert item.mainCount == 123
    CONFIG.useCharCount = True
    assert item.mainCount == 1234
    CONFIG.useCharCount = False

    # InitCount
    item._wordInit = 12
    item._charInit = 34
    CONFIG.useCharCount = False
    assert item.initCount == 12
    CONFIG.useCharCount = True
    assert item.initCount == 34
    CONFIG.useCharCount = False

    # CursorPos
    item.setCursorPos(None)
    assert item.cursorPos == 0
    item.setCursorPos("1")
    assert item.cursorPos == 0
    item.setCursorPos(1)
    assert item.cursorPos == 1


@pytest.mark.core
def testProjectItem_DailyProgress(mockGUI, mockRnd, fncPath):
    """Test the dailyProgress getter. It must report word or character
    based counts depending on the project's target count mode, and
    report zero for items not eligible for the project goal.
    """
    project = NWProject()
    buildTestProject(project, fncPath)
    item = ProjectItem(project, "0000000000000")
    item._dailyTarget = True
    item._root = C.hNovelRoot
    item.setWordCount(120)
    item.setCharCount(600)
    item._wordInit = 100
    item._charInit = 500

    # In word count mode, the total and session change are word based
    project.data.setProjectTarget(0, None, False)
    assert item.dailyProgress() == (120, 20)

    # In character count mode, the same item reports character counts
    project.data.setProjectTarget(0, None, True)
    assert item.dailyProgress() == (600, 100)

    # Items not eligible for the daily target report zero regardless of mode
    item._dailyTarget = False
    assert item.dailyProgress() == (0, 0)
    item._dailyTarget = True

    # Items in a skipped root also report zero
    project.data.setTargetSkipRoots([C.hNovelRoot])
    assert item.dailyProgress() == (0, 0)


@pytest.mark.core
def testProjectItem_Methods(mockGUI, mockRnd, fncPath):
    """Test the simple methods of the ProjectItem class."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    item = ProjectItem(project, "0000000000000")

    # Describe Me
    # ===========

    assert item.describeMe() == "None"

    item.setType("ROOT")
    assert item.describeMe() == "Root Folder"
    assert item.isRootType() is True

    item.setType("FOLDER")
    assert item.describeMe() == "Folder"
    assert item.isFolderType() is True

    item.setType("FILE")
    item.setLayout("DOCUMENT")
    assert item.isFileType() is True
    assert item.isDocumentLayout() is True

    item.setMainHeading("HH")
    assert item.mainHeading == "H0"
    assert item.describeMe() == "Novel Document"

    item.setMainHeading("H0")
    assert item.mainHeading == "H0"
    assert item.describeMe() == "Novel Document"

    item.setMainHeading("H1")
    assert item.mainHeading == "H1"
    assert item.describeMe() == "Novel Title Page"

    item.setMainHeading("H2")
    assert item.mainHeading == "H2"
    assert item.describeMe() == "Novel Chapter"

    item.setMainHeading("H3")
    assert item.mainHeading == "H3"
    assert item.describeMe() == "Novel Scene"

    item.setMainHeading("H4")
    assert item.mainHeading == "H4"
    assert item.describeMe() == "Novel Section"

    item.setMainHeading("H5")
    assert item.mainHeading == "H4"
    assert item.describeMe() == "Novel Section"

    item.setLayout("NOTE")
    assert item.isNoteLayout() is True
    assert item.describeMe() == "Project Note"

    item.setLayout("NO_LAYOUT")
    assert item.describeMe() == "None"

    # Status + Icon
    # =============

    item.setType("FILE")
    item.setStatus(C.sNote)
    item.setImport(C.iMinor)

    item.setClass("NOVEL")
    stT, stI = item.getImportStatus()
    assert stT == "Note"
    assert isinstance(stI, QIcon)

    item.setClass("CHARACTER")
    stT, stI = item.getImportStatus()
    assert stT == "Minor"
    assert isinstance(stI, QIcon)

    # Representation
    # ==============

    item.setName("New Item")
    item.setParent("1111111111111")
    assert repr(item) == "<ProjectItem handle=0000000000000, parent=1111111111111, name='New Item'>"

    # Truthiness
    # ==========

    # Is True if the handle evaluates to True
    assert bool(ProjectItem(project, "0000000000000")) is True
    assert bool(ProjectItem(project, "")) is False

    # Copy an Item
    # ============

    scData = {
        "name": "New Scene",
        "itemAttr": {
            "handle": "000000000000f",
            "parent": "000000000000d",
            "root": "0000000000008",
            "order": "1",
            "type": "FILE",
            "class": "NOVEL",
            "layout": "DOCUMENT",
        },
        "metaAttr": {
            "expanded": "no",
            "heading": "H3",
            "charCount": "9",
            "wordCount": "2",
            "paraCount": "0",
            "cursorPos": "0",
        },
        "nameAttr": {"status": "s000000", "import": "i000004", "active": "yes"},
    }

    # Get the scene item
    scItem = project.tree[C.hSceneDoc]
    assert isinstance(scItem, ProjectItem)

    # Duplicate and update the expected content with a new handle
    cpHandle = project.tree._makeHandle()
    cpData = copy.deepcopy(scData)
    cpData["itemAttr"]["handle"] = cpHandle

    # Duplicate the scene item
    cpItem = ProjectItem.duplicate(scItem, cpHandle)
    assert isinstance(cpItem, ProjectItem)
    assert scItem is not cpItem

    # They should both point to the same project instance
    assert scItem._project is cpItem._project

    # They should contain the same data, except for the handle
    assert scItem.pack() == scData
    assert cpItem.pack() == cpData

    # Delete the original, and check that the copy remains
    del scItem
    assert cpItem.pack() == cpData


@pytest.mark.core
def testProjectItem_Duplicate(mockGUI, mockRnd, fncPath):
    """Test that duplicating an item copies every attribute of the
    source item, except the handle, which must be unique and is
    therefore provided separately. This loops over the class' declared
    __slots__ rather than naming each attribute, so the test also
    catches a new attribute being added to the class without a
    matching update to ProjectItem.duplicate.
    """
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Give every slot a distinct sentinel value, except the handle and
    # the project reference, which are excluded from the duplicate
    # copy loop below and are checked separately
    source = ProjectItem(project, "000000000000f")
    for i, slot in enumerate(ProjectItem.__slots__):
        if slot not in ("_handle", "_project"):
            setattr(source, slot, f"sentinel-{i}")

    duplicate = ProjectItem.duplicate(source, "0000000000010")

    # The duplicate is a distinct instance with a new, unique handle
    assert duplicate is not source
    assert duplicate.itemHandle == "0000000000010"
    assert duplicate.itemHandle != source.itemHandle

    # But it points to the same project instance as the source
    assert duplicate._project is source._project

    # Every other declared attribute must be copied from the source as-is
    for slot in ProjectItem.__slots__:
        if slot in ("_handle", "_project"):
            continue
        assert getattr(duplicate, slot) == getattr(source, slot), f"Attribute '{slot}' was not duplicated"


@pytest.mark.core
def testProjectItem_TypeSetter(mockGUI):
    """Test the setter for all the nwItemType values for the ProjectItem
    class.
    """
    project = NWProject()
    item = ProjectItem(project, "0000000000000")

    # Type
    item.setType(None)
    assert item.itemType == nwItemType.NO_TYPE
    item.setType("NONSENSE")
    assert item.itemType == nwItemType.NO_TYPE
    item.setType("NO_TYPE")
    assert item.itemType == nwItemType.NO_TYPE
    item.setType("ROOT")
    assert item.itemType == nwItemType.ROOT
    item.setType("FOLDER")
    assert item.itemType == nwItemType.FOLDER
    item.setType("FILE")
    assert item.itemType == nwItemType.FILE

    # Alternative
    item.setType(nwItemType.ROOT)
    assert item.itemType == nwItemType.ROOT


@pytest.mark.core
def testProjectItem_ClassSetter(mockGUI):
    """Test the setter for all the nwItemClass values for the
    ProjectItem class.
    """
    project = NWProject()
    item = ProjectItem(project, "0000000000000")
    item.setType(nwItemType.FILE)

    # Class
    item.setClass(None)
    assert item.itemClass == nwItemClass.NO_CLASS
    item.setClass("NONSENSE")
    assert item.itemClass == nwItemClass.NO_CLASS

    item.setClass("NO_CLASS")
    assert item.itemClass == nwItemClass.NO_CLASS
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is True
    assert item.isSearchableClass() is False
    assert item.isTemplateFile() is False

    item.setClass("NOVEL")
    assert item.itemClass == nwItemClass.NOVEL
    assert item.isNovelLike() is True
    assert item.documentAllowed() is True
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("PLOT")
    assert item.itemClass == nwItemClass.PLOT
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("CHARACTER")
    assert item.itemClass == nwItemClass.CHARACTER
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("WORLD")
    assert item.itemClass == nwItemClass.WORLD
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("TIMELINE")
    assert item.itemClass == nwItemClass.TIMELINE
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("OBJECT")
    assert item.itemClass == nwItemClass.OBJECT
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("ENTITY")
    assert item.itemClass == nwItemClass.ENTITY
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("CUSTOM")
    assert item.itemClass == nwItemClass.CUSTOM
    assert item.isNovelLike() is False
    assert item.documentAllowed() is False
    assert item.isInactiveClass() is False
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("ARCHIVE")
    assert item.itemClass == nwItemClass.ARCHIVE
    assert item.isNovelLike() is True
    assert item.documentAllowed() is True
    assert item.isInactiveClass() is True
    assert item.isSearchableClass() is True
    assert item.isTemplateFile() is False

    item.setClass("TEMPLATE")
    assert item.itemClass == nwItemClass.TEMPLATE
    assert item.isNovelLike() is True
    assert item.documentAllowed() is True
    assert item.isInactiveClass() is True
    assert item.isSearchableClass() is False
    assert item.isTemplateFile() is True

    item.setClass("TRASH")
    assert item.itemClass == nwItemClass.TRASH
    assert item.isNovelLike() is False
    assert item.documentAllowed() is True
    assert item.isInactiveClass() is True
    assert item.isSearchableClass() is False
    assert item.isTemplateFile() is False

    # Alternative
    item.setClass(nwItemClass.NOVEL)
    assert item.itemClass == nwItemClass.NOVEL


@pytest.mark.core
def testProjectItem_LayoutSetter(mockGUI):
    """Test the setter for all the nwItemLayout values for the
    ProjectItem class.
    """
    project = NWProject()
    item = ProjectItem(project, "0000000000000")

    # Faulty Layouts
    item.setLayout(None)
    assert item.itemLayout == nwItemLayout.NO_LAYOUT
    item.setLayout("NONSENSE")
    assert item.itemLayout == nwItemLayout.NO_LAYOUT

    # Current Layouts
    item.setLayout("NO_LAYOUT")
    assert item.itemLayout == nwItemLayout.NO_LAYOUT
    item.setLayout("DOCUMENT")
    assert item.itemLayout == nwItemLayout.DOCUMENT
    item.setLayout("NOTE")
    assert item.itemLayout == nwItemLayout.NOTE

    # Alternative
    item.setLayout(nwItemLayout.NOTE)
    assert item.itemLayout == nwItemLayout.NOTE


@pytest.mark.core
def testProjectItem_ClassDefaults(mockGUI):
    """Test the setter for the default values for the ProjectItem class."""
    project = NWProject()
    item = ProjectItem(project, "0000000000000")

    # Root items should not have their class updated
    item.setParent(None)
    item.setClass(nwItemClass.NO_CLASS)
    assert item.itemClass == nwItemClass.NO_CLASS

    item.setClassDefaults(nwItemClass.NOVEL)
    assert item.itemClass == nwItemClass.NO_CLASS

    # Non-root items should have their class updated
    item.setParent("0123456789abc")
    item.setClass(nwItemClass.NO_CLASS)
    assert item.itemClass == nwItemClass.NO_CLASS

    item.setClassDefaults(nwItemClass.NOVEL)
    assert item.itemClass == nwItemClass.NOVEL

    # Non-layout items should have their layout set based on class
    item.setParent("0123456789abc")
    item.setClass(nwItemClass.NO_CLASS)
    item.setLayout(nwItemLayout.NO_LAYOUT)
    assert item.itemLayout == nwItemLayout.NO_LAYOUT

    item.setClassDefaults(nwItemClass.NOVEL)
    assert item.itemLayout == nwItemLayout.DOCUMENT

    item.setParent("0123456789abc")
    item.setClass(nwItemClass.NO_CLASS)
    item.setLayout(nwItemLayout.NO_LAYOUT)
    assert item.itemLayout == nwItemLayout.NO_LAYOUT

    item.setClassDefaults(nwItemClass.PLOT)
    assert item.itemLayout == nwItemLayout.NOTE

    # If documents are not allowed in that class, the layout should be changed
    item.setParent("0123456789abc")
    item.setClass(nwItemClass.NO_CLASS)
    item.setLayout(nwItemLayout.DOCUMENT)
    assert item.itemLayout == nwItemLayout.DOCUMENT

    item.setClassDefaults(nwItemClass.PLOT)
    assert item.itemLayout == nwItemLayout.NOTE

    # In all cases, status and importance should no longer be None
    assert item.itemStatus is not None
    assert item.itemImport is not None


@pytest.mark.core
def testProjectItem_PackUnpack(mockGUI, caplog, mockRnd):
    """Test packing and unpacking entries for the ProjectItem class."""
    project = NWProject()
    project.data.itemStatus.add(None, "New", "#646464", "SQUARE", 0)
    project.data.itemImport.add(None, "New", "#646464", "SQUARE", 0)

    # Invalid
    item = ProjectItem(project, "0000000000000")
    assert item.unpack({}) is False

    # File
    item = ProjectItem(project, "")
    assert (
        item.unpack({
            "name": "A File",
            "itemAttr": {
                "handle": "0000000000003",
                "parent": "0000000000002",
                "root": "0000000000001",
                "order": 1,
                "type": "FILE",
                "class": "NOVEL",
                "layout": "DOCUMENT",
            },
            "metaAttr": {
                "expanded": True,
                "heading": "H1",
                "charCount": 100,
                "wordCount": 20,
                "paraCount": 2,
                "cursorPos": 50,
            },
            "nameAttr": {
                "status": None,
                "import": None,
                "active": False,
            },
        })
        is True
    )

    assert item.itemName == "A File"
    assert item.itemHandle == "0000000000003"
    assert item.itemParent == "0000000000002"
    assert item.itemRoot == "0000000000001"
    assert item.itemOrder == 1
    assert item.itemType == nwItemType.FILE
    assert item.itemClass == nwItemClass.NOVEL
    assert item.itemLayout == nwItemLayout.DOCUMENT
    assert item.itemStatus == "s000000"
    assert item.itemImport == "i000001"
    assert item.isActive is False
    assert item.isExpanded is True
    assert item.mainHeading == "H1"
    assert item.charCount == 100
    assert item.wordCount == 20
    assert item.paraCount == 2
    assert item.cursorPos == 50

    assert item.pack() == {
        "name": "A File",
        "itemAttr": {
            "handle": "0000000000003",
            "parent": "0000000000002",
            "root": "0000000000001",
            "order": "1",
            "type": "FILE",
            "class": "NOVEL",
            "layout": "DOCUMENT",
        },
        "metaAttr": {
            "expanded": "yes",
            "heading": "H1",
            "charCount": "100",
            "wordCount": "20",
            "paraCount": "2",
            "cursorPos": "50",
        },
        "nameAttr": {
            "status": "s000000",
            "import": "i000001",
            "active": "no",
        },
    }

    # Folder
    item = ProjectItem(project, "")
    assert (
        item.unpack({
            "name": "A Folder",
            "itemAttr": {
                "handle": "0000000000003",
                "parent": "0000000000002",
                "root": "0000000000001",
                "order": 1,
                "type": "FOLDER",
                "class": "NOVEL",
                "layout": "DOCUMENT",
            },
            "metaAttr": {
                "expanded": True,
                "heading": "H1",
                "charCount": 100,
                "wordCount": 20,
                "paraCount": 2,
                "cursorPos": 50,
            },
            "nameAttr": {
                "status": "",
                "import": "",
                "active": True,
            },
        })
        is True
    )

    assert item.itemName == "A Folder"
    assert item.itemHandle == "0000000000003"
    assert item.itemParent == "0000000000002"
    assert item.itemRoot == "0000000000001"
    assert item.itemOrder == 1
    assert item.itemType == nwItemType.FOLDER
    assert item.itemClass == nwItemClass.NOVEL
    assert item.itemLayout == nwItemLayout.NO_LAYOUT
    assert item.itemStatus == "s000000"
    assert item.itemImport == "i000001"
    assert item.isActive is False
    assert item.isExpanded is True
    assert item.mainHeading == "H0"
    assert item.charCount == 0
    assert item.wordCount == 0
    assert item.paraCount == 0
    assert item.cursorPos == 0

    assert item.pack() == {
        "name": "A Folder",
        "itemAttr": {
            "handle": "0000000000003",
            "parent": "0000000000002",
            "root": "0000000000001",
            "order": "1",
            "type": "FOLDER",
            "class": "NOVEL",
        },
        "metaAttr": {
            "expanded": "yes",
        },
        "nameAttr": {
            "status": "s000000",
            "import": "i000001",
        },
    }

    # Root
    item = ProjectItem(project, "")
    assert (
        item.unpack({
            "name": "A Novel",
            "itemAttr": {
                "handle": "0000000000003",
                "parent": "0000000000002",
                "root": "0000000000001",
                "order": 1,
                "type": "ROOT",
                "class": "NOVEL",
                "layout": "DOCUMENT",
            },
            "metaAttr": {
                "expanded": True,
                "heading": "H1",
                "charCount": 100,
                "wordCount": 20,
                "paraCount": 2,
                "cursorPos": 50,
            },
            "nameAttr": {
                "status": None,
                "import": None,
                "active": True,
            },
        })
        is True
    )

    assert item.itemName == "A Novel"
    assert item.itemHandle == "0000000000003"
    assert item.itemParent is None
    assert item.itemRoot == "0000000000003"
    assert item.itemOrder == 1
    assert item.itemType == nwItemType.ROOT
    assert item.itemClass == nwItemClass.NOVEL
    assert item.itemLayout == nwItemLayout.NO_LAYOUT
    assert item.itemStatus == "s000000"
    assert item.itemImport == "i000001"
    assert item.isActive is False
    assert item.isExpanded is True
    assert item.mainHeading == "H0"
    assert item.charCount == 0
    assert item.wordCount == 0
    assert item.paraCount == 0
    assert item.cursorPos == 0

    assert item.pack() == {
        "name": "A Novel",
        "itemAttr": {
            "handle": "0000000000003",
            "parent": "None",
            "root": "0000000000003",
            "order": "1",
            "type": "ROOT",
            "class": "NOVEL",
        },
        "metaAttr": {
            "expanded": "yes",
        },
        "nameAttr": {
            "status": "s000000",
            "import": "i000001",
        },
    }
