"""
novelWriter - Story View Settings Tests
=======================================

This file is a part of novelWriter
Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors

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
import uuid

from pathlib import Path

import pytest

from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject
from novelwriter.story.storysettings import OutlineColumn, OutlineViewSettings, StoryViewCollection, StoryViewSettings

from tests.helpers import buildTestProject
from tests.mocked import causeOSError

VIEW_ID = "5cf45d24-f496-42c9-8733-529a9e52a62b"


def isUUID(value):
    """Check if a value is a valid UUID object."""
    try:
        uuid.UUID(value)
        return True
    except Exception:
        return False


@pytest.mark.core
def testStoryViewSettings_ClassAttributes():
    """Test the StoryViewSettings class attributes."""
    view = OutlineViewSettings()
    assert view.changed is False
    assert isUUID(view.viewID)

    # Name is always converted to string
    view.setName(None)  # type: ignore
    assert view.name == "None"

    view.setName("Test View")
    assert view.name == "Test View"

    # Only valid UUIDs are accepted, anything else generates a new UUID
    view.setViewID(VIEW_ID)
    assert view.viewID == VIEW_ID

    view.setViewID(None)  # type: ignore
    assert view.viewID != VIEW_ID
    assert isUUID(view.viewID)

    view.setViewID("q" + VIEW_ID[1:])
    assert view.viewID != "q" + VIEW_ID[1:]
    assert isUUID(view.viewID)

    # Setting the same UUID again does nothing
    sameID = view.viewID
    view.setViewID(sameID)
    assert view.viewID == sameID

    # Order is only set if the value is an integer
    view.setOrder(3)
    assert view.order == 3
    view.setOrder("not an int")  # type: ignore
    assert view.order == 3

    # Pack the values
    view.setViewID(VIEW_ID)
    data = view.pack()
    assert data["kind"] == "outline"
    assert data["name"] == "Test View"
    assert data["uuid"] == VIEW_ID
    assert data["order"] == 3
    assert data["state"] == {}

    # Create from dict using the correct class
    another = StoryViewSettings.fromDict(data)
    assert isinstance(another, OutlineViewSettings)
    assert another.pack() == data

    # Unknown or missing kinds are rejected
    assert StoryViewSettings.fromDict({**data, "kind": "unknown"}) is None
    assert StoryViewSettings.fromDict({"name": "No Kind"}) is None

    # Copy keeps the class and all values
    copied = another.copy()
    assert isinstance(copied, OutlineViewSettings)
    assert copied is not another
    assert copied.pack() == data

    # Malformed data falls back to defaults
    malformed = OutlineViewSettings()
    malformed.unpack({"order": "3", "settings": ["not", "a", "dict"]})
    assert malformed.order == 0
    assert isUUID(malformed.viewID)
    assert malformed.getBool("outline.showScenes") is True

    # Duplicate keeps the class and settings, but not name and ID
    view.setValue("outline.showSections", True)
    copy = StoryViewSettings.duplicate(view)
    assert isinstance(copy, OutlineViewSettings)
    assert copy.name == "Test View 2"
    assert copy.viewID != view.viewID
    assert isUUID(copy.viewID)
    assert copy.order == view.order
    assert copy.pack()["settings"] == view.pack()["settings"]
    assert copy.changed is False

    # Update copies the name and settings, but not ID, order and state
    view.setState("columns", {"title": 100})
    source = OutlineViewSettings()
    source.setName("Source")
    source.setValue("outline.showSections", False)
    source.setState("columns", {"title": 200})
    view.updateSettings(source)
    assert view.name == "Source"
    assert view.viewID == VIEW_ID
    assert view.order == 3
    assert view.getBool("outline.showSections") is False
    assert view.getState("columns") == {"title": 100}


@pytest.mark.core
def testStoryViewSettings_Values():
    """Test StoryViewSettings get/set of values."""
    view = OutlineViewSettings()
    boolSetting = "outline.showSections"

    # Only the settings for the view's own kind are present
    assert StoryViewSettings().pack()["settings"] == {}
    assert view.pack()["settings"] == {
        "outline.syntaxColors": False,
        "outline.rowLines": 3,
        "outline.commentIcons": False,
        "outline.referenceIcons": False,
        "outline.showParts": True,
        "outline.showChapters": True,
        "outline.showScenes": True,
        "outline.showSections": False,
        "outline.showProgress": True,
        "outline.countPerPage": 350,
        "outline.clearDoublePage": True,
        "outline.useTargetCount": True,
    }

    # Invalid setting
    view.setValue("foo", "bar")
    assert view.getInt("foo") == 0
    assert view.changed is False

    # Value must be correct type
    view.setValue(boolSetting, "string")
    assert view.getBool(boolSetting) is False
    assert view.changed is False

    # Setting the same value does not flag a change
    view.setValue(boolSetting, False)
    assert view.changed is False

    # Check bool values
    view.setValue(boolSetting, True)
    assert view.changed is True
    assert view.getInt(boolSetting) == 1
    assert view.getBool(boolSetting) is True

    # Changes can be reset
    view.resetChangedState()
    assert view.changed is False

    # Check labels
    assert view.getLabel(boolSetting) == "Show sections"
    assert StoryViewSettings.getLabel(boolSetting) == "Show sections"

    # Unpack into new object
    another = OutlineViewSettings()
    another.unpack(view.pack())
    assert another.getBool(boolSetting) is True
    assert another.changed is False

    # Invalid keys, other kinds' keys, and invalid values are skipped
    skipped = OutlineViewSettings()
    skipped.unpack({"settings": {123: "value", "other.key": True, boolSetting: object()}})
    assert skipped.pack()["settings"] == {
        "outline.syntaxColors": False,
        "outline.rowLines": 3,
        "outline.commentIcons": False,
        "outline.referenceIcons": False,
        "outline.showParts": True,
        "outline.showChapters": True,
        "outline.showScenes": True,
        "outline.showSections": False,
        "outline.showProgress": True,
        "outline.countPerPage": 350,
        "outline.clearDoublePage": True,
        "outline.useTargetCount": True,
    }


@pytest.mark.core
def testStoryViewSettings_State():
    """Test StoryViewSettings get/set of state values."""
    view = OutlineViewSettings()
    assert view.getState("columns") is None
    assert view.stateChanged is False

    # Setting state flags a state change, but not a settings change
    view.setState("columns", {"title": 200})
    assert view.getState("columns") == {"title": 200}
    assert view.stateChanged is True
    assert view.changed is False

    view.resetChangedState()
    assert view.stateChanged is False

    # Setting the same value does not flag a change
    view.setState("columns", {"title": 200})
    assert view.stateChanged is False

    # A new key order is a change
    view.setState("columns", {"title": 200, "plot": 100})
    view.resetChangedState()
    view.setState("columns", {"plot": 100, "title": 200})
    assert list(view.getState("columns")) == ["plot", "title"]
    assert view.stateChanged is True
    view.setState("columns", {"title": 200})

    # State is packed and unpacked
    another = OutlineViewSettings()
    another.unpack(view.pack())
    assert another.getState("columns") == {"title": 200}
    assert another.stateChanged is False

    # Invalid state is replaced by an empty state
    another.unpack({"state": ["not", "a", "dict"]})
    assert another.getState("columns") is None


@pytest.mark.core
def testStoryViewSettings_Columns():
    """Test OutlineViewSettings outline columns."""
    view = OutlineViewSettings()

    # A new view has the default columns
    assert [(c.name, c.keys) for c in view.columns] == [
        ("Characters", ("@pov", "@focus", "@char")),
        ("Plot", ("@plot", "@time")),
        ("World", ("@location",)),
        ("Comments", ("synopsis",)),
    ]
    assert all(len(c.cid) == 8 for c in view.columns)

    # Keys are lower case, valid, unique and limited in number, and
    # column IDs are unique
    view.setColumns([
        OutlineColumn("a", "One", ("story.Goal", "@POV", "@tag", "synopsis.x", "note.", "short", "story", 1)),  # type: ignore
        OutlineColumn("a", "Two", ("story.goal", "note.a", "note.b", "note.c", "note.d", "note.e", "note.f")),
        OutlineColumn("", "Three", ("synopsis",)),
    ])
    one, two, three = view.columns
    assert view.changed is True
    assert one == OutlineColumn("a", "One", ("story.goal", "@pov"))
    assert two.cid not in ("", "a")
    assert two.keys == ("note.a", "note.b", "note.c", "note.d", "note.e")
    assert three.cid not in ("", "a", two.cid)
    assert three.keys == ("synopsis",)

    # Setting the same columns is not a change
    view.resetChangedState()
    view.setColumns(view.columns)
    assert view.changed is False

    # A new order is kept, but is not a change
    view.setColumns([three, one, two])
    assert view.columns == [three, one, two]
    assert view.changed is False

    # Columns are packed and unpacked
    another = OutlineViewSettings()
    another.unpack(view.pack())
    assert another.columns == view.columns
    assert another.changed is False

    # Invalid entries are skipped, and missing columns give the default
    another.unpack({"columns": ["bad", {"id": "b", "name": 1, "keys": []}, {"id": "c", "name": "C", "keys": 1}]})
    assert another.columns == []
    another.unpack({})
    assert len(another.columns) == 4

    # Updating copies the columns
    another.updateSettings(view)
    assert another.columns == view.columns


@pytest.mark.core
def testStoryViewSettings_Collection(monkeypatch, mockGUI, fncPath: Path, mockRnd):
    """Test the collections class for story views."""
    project = NWProject()
    buildTestProject(project, fncPath)
    viewsFile = project.storage.getMetaFile(nwFiles.VIEWS_FILE)
    assert isinstance(viewsFile, Path)

    # No initial views in a fresh project
    views = StoryViewCollection(project)
    assert len(views) == 0
    assert not viewsFile.exists()

    viewOne = OutlineViewSettings()
    viewOne.setName("View One")
    viewIDOne = viewOne.viewID

    # Check that invalid type is handled
    views.setStoryView(None)  # type: ignore
    assert len(views) == 0
    assert not viewsFile.exists()
    assert views.getStoryView(viewIDOne) is None

    # Add the views
    views.setStoryView(viewOne)
    assert len(views) == 1
    assert viewsFile.exists()
    assert views.getStoryView(viewIDOne) is viewOne

    viewTwo = OutlineViewSettings()
    viewTwo.setName("View Two")
    viewIDTwo = viewTwo.viewID

    views.setStoryView(viewTwo)
    assert len(views) == 2
    assert [v.viewID for v in views.storyViews()] == [viewIDOne, viewIDTwo]

    # Set the last view and reorder the views, unknown IDs are ignored
    views.setStoryViewsState(viewIDTwo, "", [viewIDTwo, viewIDOne, "not-a-real-id"])
    assert [v.viewID for v in views.storyViews()] == [viewIDTwo, viewIDOne]
    assert views.lastView == viewIDTwo
    assert views.highlight == ""

    # An unchanged state is not saved
    with monkeypatch.context() as mp:
        mp.setattr(views, "_saveCollection", lambda: pytest.fail("Unexpected save"))
        views.setStoryViewsState(viewIDTwo, "", [viewIDTwo, viewIDOne])

    # A changed highlight is saved
    views.setStoryViewsState(viewIDTwo, "bod", [viewIDTwo, viewIDOne])
    assert views.highlight == "bod"
    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    assert data["novelWriter.storyViews"]["highlight"] == "bod"

    # A changed view state is saved, and the flag reset
    viewOne.setState("columns", {"title": 200})
    views.setStoryViewsState(viewIDTwo, "bod", [viewIDTwo, viewIDOne])
    assert viewOne.stateChanged is False
    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    assert data["novelWriter.storyViews"][viewIDOne]["state"] == {"columns": {"title": 200}}

    # Check the file content
    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    assert list(data["novelWriter.storyViews"].keys()) == ["lastView", "highlight", viewIDOne, viewIDTwo]

    # Remove a view
    views.removeStoryView(viewIDOne)
    assert views.getStoryView(viewIDOne) is None
    assert [v.viewID for v in views.storyViews()] == [viewIDTwo]

    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    assert list(data["novelWriter.storyViews"].keys()) == ["lastView", "highlight", viewIDTwo]
    views.setStoryView(viewOne)

    # Load views file into new object
    another = StoryViewCollection(project)
    assert another.lastView == viewIDTwo
    assert another.highlight == "bod"
    assert [(v.viewID, v.name) for v in another.storyViews()] == [
        (viewIDTwo, "View Two"),
        (viewIDOne, "View One"),
    ]

    # Unknown kinds are preserved on save, and non-object entries are skipped
    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    unknown = {"kind": "unknown", "name": "Future View", "settings": {"unknown.value": 42}}
    data["novelWriter.storyViews"]["future"] = unknown
    data["novelWriter.storyViews"]["garbage"] = "not a view entry"
    viewsFile.write_text(json.dumps(data), encoding="utf-8")

    future = StoryViewCollection(project)
    assert len(future) == 2
    assert [v.viewID for v in future.storyViews()] == [viewIDTwo, viewIDOne]

    future.removeStoryView(viewIDOne)
    data = json.loads(viewsFile.read_text(encoding="utf-8"))
    assert data["novelWriter.storyViews"] == {
        "lastView": viewIDTwo,
        "highlight": "bod",
        "future": unknown,
        viewIDTwo: viewTwo.pack(),
    }

    # Check errors: No valid path
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.core.storage.ProjectStorage.getMetaFile", lambda *a: None)
        assert views._loadCollection() is False
        assert views._saveCollection() is False

    # Check errors: I/O error
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert views._loadCollection() is False
        assert views._saveCollection() is False

    # Check errors: Can't parse json file
    viewsFile.write_text("foobar")
    assert views._loadCollection() is False

    # Check errors: Valid json file, but list instead of object
    viewsFile.write_text("[]")
    assert views._loadCollection() is False

    # Check errors: Valid json object, but no views entry
    viewsFile.write_text("{}")
    assert views._loadCollection() is False
