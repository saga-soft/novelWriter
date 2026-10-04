"""
novelWriter - Project Tree Tests
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

import random

from copy import deepcopy
from pathlib import Path

import pytest

from novelwriter.constants import nwFiles
from novelwriter.core.item import ProjectItem
from novelwriter.core.project import NWProject
from novelwriter.core.tree import ProjectTree
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType

from tests.helpers import C, buildTestProject
from tests.mocked import causeOSError


def assertTreeModelConsistency(tree: ProjectTree) -> None:
    """Assert map and model consistency for the loaded tree."""
    modelNodes = tree.model.root.allChildren()
    modelHandles = {node.item.itemHandle for node in modelNodes}

    assert len(modelHandles) == len(modelNodes)
    assert set(tree._nodes.keys()) == modelHandles
    assert set(tree._items.keys()) == modelHandles

    for node in modelNodes:
        handle = node.item.itemHandle
        assert tree._nodes[handle] is node
        assert tree._items[handle] is node.item

        parent = node.parent()
        assert parent is not None
        assert parent.child(node.row()) is node

        if parent is tree.model.root:
            assert node.item.itemParent is None
            assert node.item.itemRoot == handle
        else:
            pHandle = parent.item.itemHandle
            assert node.item.itemParent == pHandle
            assert node.item.itemRoot == parent.item.itemRoot


@pytest.fixture
def mockItems(mockGUI, mockRnd, fncPath):
    """Create a list of mock items."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    return project.tree.pack()


@pytest.mark.core
def testProjectTree_Populate(monkeypatch, mockGUI, mockItems):
    """Test populating the project tree."""
    project = NWProject()
    tree = ProjectTree(project)

    # Check that tree is empty
    assert bool(tree) is False
    assert len(tree) == 0

    # Trash should be added on request
    assert tree.trash is not None
    assert tree.nodes[tree.trash.item.itemHandle].item.itemName == "Trash"
    assert bool(tree) is True
    assert len(tree) == 1
    tree.clear()

    # Load Items
    tree.unpack(mockItems)
    assert len(tree) == 9
    assert tree.trash is not None
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]
    assert tree.allDocs() == [C.hTitlePage, C.hChapterDoc, C.hSceneDoc]
    assertTreeModelConsistency(tree)

    # Pack the data again
    assert [n["name"] for n in tree.pack()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]

    # Inject a node in the map, but not in the tree (inconsistent tree)
    # This should be ignored
    tree._nodes["123456789abc"] = tree.model.root
    with pytest.raises(AssertionError):
        assertTreeModelConsistency(tree)
    assert [n["name"] for n in tree.pack()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]

    # Clear, and populate in reverse order
    tree.clear()
    assert bool(tree) is False
    assert len(tree) == 0
    tree.unpack(list(reversed(mockItems)))
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Locations",
        "Characters",
        "Plot",
        "Novel",
        "New Folder",
        "New Scene",
        "New Chapter",
        "Title Page",
        "Trash",
    ]
    assertTreeModelConsistency(tree)

    # Clear, and populate with one item being its own parent
    tree.clear()
    assert bool(tree) is False
    assert len(tree) == 0
    modItems = deepcopy(mockItems)
    assert modItems[1]["name"] == "Title Page"
    modItems[1]["itemAttr"]["parent"] = modItems[1]["itemAttr"]["handle"]
    tree.unpack(mockItems)
    assert len(tree) == 9
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]
    assertTreeModelConsistency(tree)

    # Clear, and populate with one item that has an invalid handle
    tree.clear()
    assert bool(tree) is False
    assert len(tree) == 0
    badItems = deepcopy(mockItems)
    badItems[1]["itemAttr"]["handle"] = "not-a-handle"
    tree.unpack(badItems)
    assert len(tree) == 8  # One less than the full set
    assertTreeModelConsistency(tree)

    # Clear, and populate with an item whose parent handle doesn't exist anywhere
    tree.clear()
    assert bool(tree) is False
    assert len(tree) == 0
    orphanItems = deepcopy(mockItems)
    orphanItems[1]["itemAttr"]["parent"] = "9999999999999"
    tree.unpack(orphanItems)
    assert len(tree) == 8  # Title Page could not be added
    assertTreeModelConsistency(tree)

    # Clear, and populate with a non-root item that has no parent
    tree.clear()
    assert bool(tree) is False
    assert len(tree) == 0
    noParentItems = deepcopy(mockItems)
    noParentItems[1]["itemAttr"]["parent"] = None
    tree.unpack(noParentItems)
    assert len(tree) == 8  # Title Page could not be added
    assertTreeModelConsistency(tree)

    # Clear and populate reversed with max depth limit very low
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.MAX_DEPTH", 1)
        tree.clear()
        assert bool(tree) is False
        assert len(tree) == 0
        tree.unpack(list(reversed(mockItems)))
        assert [n.item.itemName for n in tree.model.root.allChildren()] == [
            "Locations",
            "Characters",
            "Plot",
            "Novel",
            "Trash",
        ]
        assertTreeModelConsistency(tree)


@pytest.mark.core
def testProjectTree_ManipulateTree(monkeypatch, mockGUI, mockItems):
    """Check create, add, remove and duplicate items."""
    project = NWProject()
    tree = ProjectTree(project)
    tree.unpack(mockItems)
    assertTreeModelConsistency(tree)
    assert len(tree) == 9
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]

    # Create Root
    oHandle = tree.create("Objects", None, nwItemType.ROOT, nwItemClass.OBJECT, pos=4)
    assert oHandle is not None
    assert oHandle in tree

    # Create Folder
    fHandle = tree.create("Foo", oHandle, nwItemType.FOLDER, pos=0)
    assert fHandle is not None
    assert fHandle in tree

    # Create File
    bHandle = tree.create("Bar", fHandle, nwItemType.FILE, pos=0)
    assert bHandle is not None
    assert bHandle in tree

    # Check Tree
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Trash",
    ]

    # Cannot add a folder or file with no parent
    assert tree.create("Foo", None, nwItemType.FOLDER, pos=0) is None
    assert tree.create("Bar", None, nwItemType.FILE, pos=0) is None
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Trash",
    ]

    # Duplicate Bar -> Baz
    baz = tree.duplicate(bHandle, fHandle, True)
    assert baz is not None
    baz.setName("Baz")
    zHandle = baz.itemHandle
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Baz",
        "Trash",
    ]

    # Duplicate non-existent
    assert tree.duplicate("bob", fHandle, True) is None
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Baz",
        "Trash",
    ]

    # Duplicate with an invalid parent
    assert tree.duplicate(bHandle, "not-a-parent", True) is None
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Baz",
        "Trash",
    ]

    # Remove Baz
    assert tree.remove(zHandle) is True
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Trash",
    ]
    assert len(tree._items) == len(tree.model.root.allChildren())
    assert len(tree._items) == len(tree._nodes)
    assertTreeModelConsistency(tree)

    # Remove non-existing
    assert tree.remove("bob") is False

    # Remove where the model refuses to remove the child
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.models.itemmodel.ProjectModel.removeChild", lambda *a: False)
        assert tree.remove(bHandle) is False

    # Add item with non-existing parent
    item = ProjectItem(project, tree._makeHandle())
    item.setParent(tree._makeHandle())
    assert tree.add(item) is False
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Trash",
    ]

    # Add item with non parent, that isn't a root
    item = ProjectItem(project, tree._makeHandle())
    item.setType(nwItemType.FOLDER)
    assert tree.add(item) is False
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Objects",
        "Foo",
        "Bar",
        "Trash",
    ]

    # Remove a subtree and ensure descendants are purged from maps
    assert tree.remove(C.hChapterDir) is True
    assert C.hChapterDir not in tree._items
    assert C.hChapterDoc not in tree._items
    assert C.hSceneDoc not in tree._items
    assert C.hChapterDir not in tree._nodes
    assert C.hChapterDoc not in tree._nodes
    assert C.hSceneDoc not in tree._nodes
    assertTreeModelConsistency(tree)


@pytest.mark.core
def testProjectTree_PickParent(mockGUI, mockItems):
    """Check the parent item picker."""
    project = NWProject()
    tree = ProjectTree(project)
    assert len(tree) == 0

    # Case 1: Root and Folder
    # =======================

    hNovelRoot = tree.create("Novel", None, nwItemType.ROOT, nwItemClass.NOVEL)
    nNovelRoot = tree.nodes[hNovelRoot]

    # Add a folder
    sHandle, sPos = tree.pickParent(nNovelRoot, 0, False)
    assert sHandle == hNovelRoot
    assert sPos == 0
    hNovelFolder = tree.create("Folder", sHandle, nwItemType.FOLDER, pos=sPos)
    assert hNovelFolder is not None
    nNovelFolder = tree.nodes[hNovelFolder]
    assert nNovelFolder.item.itemClass == nwItemClass.NOVEL

    # Add a partition
    sHandle, sPos = tree.pickParent(nNovelRoot, 1, False)
    assert sHandle == hNovelRoot
    assert sPos == 1
    hPartOne = tree.create("Part One", sHandle, nwItemType.FILE, pos=sPos)
    assert hPartOne is not None
    nPartOne = tree.nodes[hPartOne]
    assert nPartOne.item.itemClass == nwItemClass.NOVEL
    nPartOne.item.setMainHeading("H1")

    # Folders behave identical to root
    sHandle, sPos = tree.pickParent(nNovelFolder, 0, False)
    assert sHandle == hNovelFolder
    assert sPos == 0

    # Case 2: Documents of Same Level
    # ===============================

    # Add a chapter under Part One
    hChapterOne = tree.create("Chapter One", hPartOne, nwItemType.FILE)
    assert hChapterOne is not None
    nChapterOne = tree.nodes[hChapterOne]
    assert nChapterOne.item.itemParent == hPartOne
    nChapterOne.item.setMainHeading("H2")

    # Add a chapter next to Chapter One -> Sibling (default behaviour)
    sHandle, sPos = tree.pickParent(nChapterOne, 2, False)
    assert sHandle == hPartOne
    assert sPos == 1
    hChapterTwo = tree.create("Chapter Two", sHandle, nwItemType.FILE, pos=sPos)
    assert hChapterTwo is not None
    nChapterTwo = tree.nodes[hChapterTwo]
    assert nChapterTwo.item.itemClass == nwItemClass.NOVEL
    nChapterTwo.item.setMainHeading("H2")

    # Add a new part next to Chapter Two -> Sibling to parent (second if condition)
    sHandle, sPos = tree.pickParent(nChapterTwo, 1, False)
    assert sHandle == hNovelRoot
    assert sPos == 2

    # Add a scene under Chapter Two
    hSceneOne = tree.create("Scene One", hChapterOne, nwItemType.FILE)
    assert hSceneOne is not None
    nSceneOne = tree.nodes[hSceneOne]
    assert nSceneOne.item.itemParent == hChapterOne
    nSceneOne.item.setMainHeading("H3")

    # Adding a part next to the scene should also jump a level up
    sHandle, sPos = tree.pickParent(nSceneOne, 1, False)
    assert sHandle == hPartOne
    assert sPos == 1

    # Case 3: Documents of Deeper Level
    # =================================

    # Add chapter directly to Part One with existing chapters -> Added as child (third if)
    sHandle, sPos = tree.pickParent(nPartOne, 2, False)
    assert sHandle == hPartOne
    assert sPos == 2

    # But adding a new part becomes a sibling
    sHandle, sPos = tree.pickParent(nPartOne, 1, False)
    assert sHandle == hNovelRoot
    assert sPos == 2

    # Add a page without a heading
    hPage = tree.create("Page", hNovelRoot, nwItemType.FILE)
    assert hPage is not None
    nPage = tree.nodes[hPage]
    assert nPage.item.itemParent == hNovelRoot
    nPage.item.setMainHeading("H0")

    # Add a scene below the page
    hSceneTwo = tree.create("Scene Two", hPage, nwItemType.FILE)
    assert hSceneTwo is not None
    nSceneTwo = tree.nodes[hSceneTwo]
    assert nSceneTwo.item.itemParent == hPage
    nSceneTwo.item.setMainHeading("H3")

    # A page without a heading should not add anything as a child
    sHandle, sPos = tree.pickParent(nPage, 3, False)
    assert sHandle == hNovelRoot
    assert sPos == 3

    # Case 4: Notes
    # =============

    hCharRoot = tree.create("Characters", None, nwItemType.ROOT, nwItemClass.CHARACTER)
    nCharRoot = tree.nodes[hCharRoot]

    # Add a note at root level
    hNoteOne = tree.create("Note One", hCharRoot, nwItemType.FILE)
    assert hNoteOne is not None
    nNoteOne = tree.nodes[hNoteOne]
    assert nNoteOne.item.itemClass == nwItemClass.CHARACTER
    nNoteOne.item.setMainHeading("H1")
    assert nCharRoot.childCount() == 1

    # Adding a new note is a sibling
    sHandle, sPos = tree.pickParent(nNoteOne, 1, True)
    assert sHandle == hCharRoot
    assert sPos == 1

    # Add a child note to Note One
    hNoteTwo = tree.create("Note Two", hNoteOne, nwItemType.FILE)
    assert hNoteTwo is not None
    nNoteTwo = tree.nodes[hNoteTwo]
    assert nNoteTwo.item.itemClass == nwItemClass.CHARACTER
    nNoteTwo.item.setMainHeading("H1")
    assert nNoteOne.childCount() == 1

    # Adding a new note now is a child
    sHandle, sPos = tree.pickParent(nNoteOne, 1, True)
    assert sHandle == hNoteOne
    assert sPos == 1


@pytest.mark.core
def testProjectTree_ItemMethods(monkeypatch, mockGUI, mockItems):
    """Check the item methods of the tree."""
    project = NWProject()
    tree = ProjectTree(project)
    tree.unpack(mockItems)
    assert len(tree) == 9
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]

    # Check Type
    assert tree.checkType(C.hNovelRoot, nwItemType.ROOT) is True
    assert tree.checkType(C.hNovelRoot, nwItemType.FOLDER) is False
    assert tree.checkType(C.hNovelRoot, nwItemType.FILE) is False

    assert tree.checkType(C.hChapterDir, nwItemType.ROOT) is False
    assert tree.checkType(C.hChapterDir, nwItemType.FOLDER) is True
    assert tree.checkType(C.hChapterDir, nwItemType.FILE) is False

    assert tree.checkType(C.hChapterDoc, nwItemType.ROOT) is False
    assert tree.checkType(C.hChapterDoc, nwItemType.FOLDER) is False
    assert tree.checkType(C.hChapterDoc, nwItemType.FILE) is True

    assert tree.checkType(C.hInvalid, nwItemType.ROOT) is False
    assert tree.checkType(C.hInvalid, nwItemType.FOLDER) is False
    assert tree.checkType(C.hInvalid, nwItemType.FILE) is False

    # Item Path
    assert tree.itemPath(C.hSceneDoc, withName=True) == [
        ("000000000000f", "New Scene"),
        ("000000000000d", "New Folder"),
        ("0000000000008", "Novel"),
    ]
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.MAX_DEPTH", 1)
        assert tree.itemPath(C.hSceneDoc, withName=True) == [
            ("000000000000f", "New Scene"),
        ]

    # An unknown handle returns an empty path
    assert tree.itemPath(C.hInvalid, withName=True) == []

    # Sub Tree
    assert tree.subTree(C.hInvalid) == []
    assert tree.subTree(C.hNovelRoot) == [
        C.hTitlePage,
        C.hChapterDir,
        C.hChapterDoc,
        C.hSceneDoc,
    ]

    # Root Classes
    classes = tree.rootClasses()
    assert len(classes) == 5
    assert nwItemClass.NOVEL in classes
    assert nwItemClass.PLOT in classes
    assert nwItemClass.CHARACTER in classes
    assert nwItemClass.WORLD in classes
    assert nwItemClass.TIMELINE not in classes
    assert nwItemClass.OBJECT not in classes
    assert nwItemClass.ENTITY not in classes
    assert nwItemClass.CUSTOM not in classes
    assert nwItemClass.ARCHIVE not in classes
    assert nwItemClass.TEMPLATE not in classes
    assert nwItemClass.TRASH in classes

    # Iter Roots
    assert list(tree.iterRoots(nwItemClass.NOVEL)) == [(C.hNovelRoot, tree[C.hNovelRoot])]
    assert list(tree.iterRoots(nwItemClass.PLOT)) == [(C.hPlotRoot, tree[C.hPlotRoot])]
    assert list(tree.iterRoots(nwItemClass.CHARACTER)) == [(C.hCharRoot, tree[C.hCharRoot])]
    assert list(tree.iterRoots(nwItemClass.WORLD)) == [(C.hWorldRoot, tree[C.hWorldRoot])]
    assert list(tree.iterRoots(nwItemClass.OBJECT)) == []

    # Find Root
    assert tree.findRoot(nwItemClass.NOVEL) == C.hNovelRoot
    assert tree.findRoot(nwItemClass.PLOT) == C.hPlotRoot
    assert tree.findRoot(nwItemClass.CHARACTER) == C.hCharRoot
    assert tree.findRoot(nwItemClass.WORLD) == C.hWorldRoot
    assert tree.findRoot(nwItemClass.OBJECT) is None


@pytest.mark.core
def testProjectTree_OtherMethods(qtbot, monkeypatch, mockGUI, fncPath, mockRnd):
    """Check other methods in the tree."""
    project = NWProject()
    buildTestProject(project, fncPath)
    tree = project.tree
    trash = tree.trash

    assert len(tree) == 9
    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Novel",
        "Title Page",
        "New Folder",
        "New Chapter",
        "New Scene",
        "Plot",
        "Characters",
        "Locations",
        "Trash",
    ]

    # Refresh All
    assert tree.sumCounts() == (9, 0, 40, 0, 9, 9)
    assert tree.model.root.count == 9

    # In character count mode, the session and target counts switch from
    # word counts to character counts, while the novel/notes totals,
    # which are always reported as both, are unaffected
    project.data.setProjectTarget(0, None, True)
    assert tree.sumCounts() == (9, 0, 40, 0, 40, 40)
    project.data.setProjectTarget(0, None, False)

    # Items with no layout (e.g. folders created directly) are not counted
    noLayoutHandle = tree.create("No Layout", C.hNovelRoot, nwItemType.FILE)
    assert noLayoutHandle is not None
    tree[noLayoutHandle].setLayout(nwItemLayout.NO_LAYOUT)  # type: ignore
    tree[noLayoutHandle].setWordCount(99)  # type: ignore
    assert tree.sumCounts() == (9, 0, 40, 0, 9, 9)
    tree.remove(noLayoutHandle)

    for node in tree.nodes.values():
        if node.item.isFileType():
            node.item.setWordCount(5)

    with qtbot.waitSignal(tree._model.layoutChanged):
        tree.refreshAllItems()
    assert tree.model.root.count == 15

    project.index.rebuild()
    tree.refreshAllItems()
    assert tree.model.root.count == 9

    # Refresh a specific item, and ignore an unknown handle
    tree.refreshItems([C.hTitlePage, "not-a-handle"])

    # Trash can't be created
    assert trash is not None
    assert tree._getTrashNode() is trash
    tree._trash = trash
    tree.remove(trash.item.itemHandle)
    assert tree._trash is None

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.ProjectTree.create", lambda *a, **k: None)
        tree._trash = trash
        assert tree.trash is None
        assert tree._getTrashNode() is None


@pytest.mark.core
def testProjectTree_CheckConsistency(monkeypatch, caplog, mockGUI, fncPath, mockRnd):
    """Check the project tree's consistency."""
    project = NWProject()
    buildTestProject(project, fncPath)

    # By default, all is well
    caplog.clear()
    assert project.tree.checkConsistency("Recovered") == (0, 0)
    assert all(m.endswith("OK") for m in caplog.messages)

    # Create a new file with no meta data, and let the function handle it as orphaned
    xHandle = "0123456789abc"
    contentPath = project.storage.contentPath
    assert isinstance(contentPath, Path)
    assert contentPath == fncPath / "content"
    (contentPath / f"{xHandle}.md").write_text("### Stuff", encoding="utf-8")

    assert project.tree.checkConsistency("Recovered") == (1, 1)
    assert xHandle in project.tree
    itemX = project.tree[xHandle]
    assert isinstance(itemX, ProjectItem)

    # It should by default be added as a Novel file
    assert itemX.itemParent == C.hNovelRoot
    assert itemX.itemRoot == C.hNovelRoot
    assert itemX.itemClass == nwItemClass.NOVEL
    assert itemX.itemName == "[Recovered] 0123456789abc"

    # Set an unknown class in the orphaned item
    itemX.setClass(nwItemClass.OBJECT)
    itemX.setName("Stuff")
    itemX.setParent(C.hInvalid)
    project.storage.getDocument(xHandle).writeDocument("### Stuff")  # This adds meta data

    # Remove the item in the project, and re-run the consistency check
    project.tree.remove(xHandle)
    assert project.tree.checkConsistency("Recovered") == (1, 1)
    assert xHandle in project.tree
    itemX = project.tree[xHandle]
    assert isinstance(itemX, ProjectItem)

    # It should again be added as a Novel file
    assert itemX.itemParent == C.hNovelRoot
    assert itemX.itemRoot == C.hNovelRoot
    assert itemX.itemClass == nwItemClass.NOVEL
    assert itemX.itemName == "[Recovered] Stuff"

    # An orphan with valid metadata pointing to an existing parent
    # is added to that parent directly
    yHandle = "0123456789abd"
    (contentPath / f"{yHandle}.md").write_text(
        (
            "+++\n"
            'name = "Stuff"\n'
            f'parent = "{C.hNovelRoot}"\n'
            f'handle = "{yHandle}"\n'
            'class = "NOVEL"\n'
            'layout = "DOCUMENT"\n'
            'textHash = "0000000000000000000000000000000000000000"\n'
            'createdDate = "Unknown"\n'
            'updatedDate = "Unknown"\n'
            "+++\n"
            "### Stuff\n"
        ),
        encoding="utf-8",
    )
    assert project.tree.checkConsistency("Recovered") == (1, 1)
    itemY = project.tree[yHandle]
    assert isinstance(itemY, ProjectItem)
    assert itemY.itemParent == C.hNovelRoot

    # If the tree is empty, a new root folder is created
    project.tree.clear()
    assert project.tree.checkConsistency("Recovered") == (5, 5)
    assert len(project.tree) == 6
    nHandle = project.tree.findRoot(nwItemClass.NOVEL)
    assert project.tree[nHandle].itemName == "Recovered"  # type: ignore

    # If the recovered item cannot be added, it is not counted
    project.tree.remove(yHandle)
    (contentPath / f"{yHandle}.md").write_text("### Stuff", encoding="utf-8")
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.ProjectTree.add", lambda *a: False)
        assert project.tree.checkConsistency("Recovered") == (1, 0)


@pytest.mark.core
def testProjectTree_MakeHandles(mockGUI):
    """Test generating item handles."""
    random.seed(42)
    project = NWProject()
    tree = ProjectTree(project)

    handles = ["1c803a3b1799d", "bdd6406671ad1", "3eb1346685257", "23b8c392456de"]

    random.seed(42)
    tHandle = tree._makeHandle()
    assert tHandle == handles[0]
    tree._items[handles[0]] = None  # type: ignore

    # Add the next in line to the project to force duplicate
    tree._items[handles[1]] = None  # type: ignore
    tHandle = tree._makeHandle()
    assert tHandle == handles[2]
    tree._items[handles[2]] = None  # type: ignore

    # Reset the seed to force collisions, which should still end up
    # returning the next handle in the sequence
    random.seed(42)
    tHandle = tree._makeHandle()
    assert tHandle == handles[3]


@pytest.mark.core
def testProjectTree_DuplicateHandleGuards(mockGUI, mockItems):
    """Test duplicate handle guards in add and _addItems."""
    project = NWProject()
    tree = ProjectTree(project)
    tree.unpack(mockItems)
    assertTreeModelConsistency(tree)

    beforeNames = [n.item.itemName for n in tree.model.root.allChildren()]
    beforeItems = len(tree._items)
    beforeNodes = len(tree._nodes)

    # add() should reject duplicate handles
    dupAdd = ProjectItem(project, C.hNovelRoot)
    dupAdd.setType(nwItemType.ROOT)
    dupAdd.setClass(nwItemClass.NOVEL)
    assert tree.add(dupAdd) is False
    assert len(tree._items) == beforeItems
    assert len(tree._nodes) == beforeNodes

    # _addItems() should also skip duplicate handles
    dupUnpack = ProjectItem(project, C.hNovelRoot)
    dupUnpack.setType(nwItemType.ROOT)
    dupUnpack.setClass(nwItemClass.NOVEL)
    assert tree._addItems({C.hNovelRoot: dupUnpack}) == {}
    assert len(tree._items) == beforeItems
    assert len(tree._nodes) == beforeNodes
    assert [n.item.itemName for n in tree.model.root.allChildren()] == beforeNames
    assertTreeModelConsistency(tree)


@pytest.mark.core
def testProjectTree_RootParentIsNormalisedToTopLevel(mockGUI, mockItems):
    """Check malformed root parent references are normalised."""
    project = NWProject()
    tree = ProjectTree(project)
    tree.unpack(mockItems)
    assertTreeModelConsistency(tree)

    badRootOne = ProjectItem(project, tree._makeHandle())
    badRootOne.setName("Bad Root One")
    badRootOne.setType(nwItemType.ROOT)
    badRootOne.setClass(nwItemClass.NOVEL)
    badRootOne.setParent(C.hNovelRoot)

    assert tree.add(badRootOne) is True
    assert badRootOne.itemParent is None
    assert badRootOne.itemRoot == badRootOne.itemHandle
    assert tree.nodes[badRootOne.itemHandle].parent() is tree.model.root

    badRootTwo = ProjectItem(project, tree._makeHandle())
    badRootTwo.setName("Bad Root Two")
    badRootTwo.setType(nwItemType.ROOT)
    badRootTwo.setClass(nwItemClass.PLOT)
    badRootTwo.setParent(C.hNovelRoot)

    assert tree._addItems({badRootTwo.itemHandle: badRootTwo}) == {}
    assert badRootTwo.itemParent is None
    assert badRootTwo.itemRoot == badRootTwo.itemHandle
    assert tree.nodes[badRootTwo.itemHandle].parent() is tree.model.root
    assertTreeModelConsistency(tree)


@pytest.mark.core
def testProjectTree_UnresolvedItemsKeepLoadedTreeConsistent(monkeypatch, mockGUI, mockItems):
    """Check unresolved unpack entries do not break loaded tree consistency."""
    project = NWProject()
    tree = ProjectTree(project)

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.tree.MAX_DEPTH", 1)
        tree.unpack(list(reversed(mockItems)))

    assert [n.item.itemName for n in tree.model.root.allChildren()] == [
        "Locations",
        "Characters",
        "Plot",
        "Novel",
        "Trash",
    ]
    assertTreeModelConsistency(tree)


@pytest.mark.core
def testProjectTree_ToCFile(monkeypatch, fncPath, mockGUI, mockItems):
    """Test writing the ToC.txt file."""
    project = NWProject()
    tree = ProjectTree(project)
    tree.unpack(mockItems)

    def mockIsFile(fileName):
        """Return True for items that are files in novelWriter and
        should thus also be files in the project folder structure.
        """
        dItem = tree[fileName.name[:13]]
        assert dItem is not None
        return dItem.itemType == nwItemType.FILE

    monkeypatch.setattr("pathlib.Path.is_file", mockIsFile)
    project._storage._runtimePath = fncPath
    # (fncPath / "content").mkdir()

    # Block extraction of the path
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.contentPath", lambda *a: None)
        assert tree.writeToCFile() is False

    # Block opening the file
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert tree.writeToCFile() is False

    # Allow writing
    assert tree.writeToCFile() is True
    assert (fncPath / nwFiles.TOC_TXT).read_text() == (
        "\n"
        "Table of Contents\n"
        "=================\n"
        "\n"
        "File Name                 Class      Layout    Document Label\n"
        "-------------------------------------------------------------\n"
        "content/000000000000c.md  NOVEL      DOCUMENT  Title Page\n"
        "content/000000000000e.md  NOVEL      DOCUMENT  New Chapter\n"
        "content/000000000000f.md  NOVEL      DOCUMENT  New Scene\n"
    )
