"""
novelWriter - OptionState Tests
===============================

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

import pytest

from novelwriter.constants import nwFiles
from novelwriter.core.options import OptionState
from novelwriter.core.project import NWProject
from novelwriter.enum import nwNovelExtra

from tests.mocked import causeOSError


@pytest.mark.core
def testOptionState_LoadSave(monkeypatch, mockGUI, fncPath):
    """Test loading and saving from the OptionState class."""
    project = NWProject()
    options = OptionState(project)

    metaDir = fncPath / "meta"
    metaDir.mkdir()

    # Write a test file
    optFile = metaDir / nwFiles.OPTS_FILE
    optFile.write_text(
        json.dumps({
            "novelWriter.guiOptions": {
                "GuiProjectSettings": {
                    "winWidth": 570,
                    "winHeight": 375,
                    "replaceColW": 130,
                    "statusColW": 130,
                    "importColW": 130,
                    "mockItem": None,
                },
                "MockGroup": {
                    "mockItem": None,
                },
            },
        }),
        encoding="utf-8",
    )

    # Load and save with no path set
    project.storage._runtimePath = None
    assert options.loadSettings() is False
    assert options.saveSettings() is False

    # Set path
    project.storage._runtimePath = fncPath
    project.storage._ready = True
    assert project.storage.getMetaFile(nwFiles.OPTS_FILE) == optFile

    # Cause open() to fail
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert options.loadSettings() is False
        assert options.saveSettings() is False

    # Load proper
    assert options.loadSettings()

    # Check that unwanted items have been removed
    assert options._state == {
        "GuiProjectSettings": {
            "winWidth": 570,
            "winHeight": 375,
            "replaceColW": 130,
            "statusColW": 130,
            "importColW": 130,
        },
    }

    # Save proper
    assert options.saveSettings()

    # Load again to check we get the values back
    assert options.loadSettings()
    assert options._state == {
        "GuiProjectSettings": {
            "winWidth": 570,
            "winHeight": 375,
            "replaceColW": 130,
            "statusColW": 130,
            "importColW": 130,
        },
    }


@pytest.mark.core
def testOptionState_SetGet(mockGUI):
    """Test setting and getting values from the OptionState class."""
    project = NWProject()
    options = OptionState(project)

    nwColHidden = nwNovelExtra.HIDDEN

    # Set invalid values
    assert options.setValue("MockGroup", "mockItem", None) is False
    assert options.setValue("GuiProjectSettings", "mockItem", None) is False

    # Set valid value
    assert options.setValue("GuiProjectSettings", "winWidth", 100) is True

    # Set some values of different types
    assert options.setValue("GuiManuscript", "winWidth", 100) is True
    assert options.setValue("GuiManuscript", "winHeight", 12.34) is True
    assert options.setValue("GuiManuscript", "detailsExpanded", True) is True
    assert options.setValue("GuiNovelView", "lastCol", nwColHidden) is True

    # Generic get, doesn't check type
    assert options.getValue("GuiManuscript", "winWidth", None) == 100
    assert options.getValue("GuiManuscript", "winHeight", None) == 12.34
    assert options.getValue("GuiManuscript", "detailsExpanded", None) is True
    assert options.getValue("GuiManuscript", "mockItem", None) is None

    # Get type-specific
    assert options.getString("GuiManuscript", "winWidth", None) is None  # type: ignore
    assert options.getString("GuiManuscript", "mockItem", None) is None  # type: ignore
    assert options.getInt("GuiManuscript", "winWidth", None) == 100  # type: ignore
    assert options.getInt("GuiManuscript", "textFont", None) is None  # type: ignore
    assert options.getInt("GuiManuscript", "mockItem", None) is None  # type: ignore
    assert options.getFloat("GuiManuscript", "winWidth", None) == 100.0  # type: ignore
    assert options.getFloat("GuiManuscript", "mockItem", None) is None  # type: ignore
    assert options.getBool("GuiManuscript", "detailsExpanded", None) is True  # type: ignore
    assert options.getBool("GuiManuscript", "mockItem", None) is None  # type: ignore
    assert options.getEnum("GuiNovelView", "lastCol", nwNovelExtra, nwColHidden) == nwColHidden

    # Get list
    assert options.setValue("GuiManuscript", "statsExpanded", [True, False]) is True
    assert options.getList("GuiManuscript", "statsExpanded", []) == [True, False]
    assert options.setValue("GuiManuscript", "detailsExpanded", "notAList") is True
    assert options.getList("GuiManuscript", "detailsExpanded", []) == []
    assert options.getList("GuiManuscript", "mockItem", []) == []

    # Get dict
    assert options.setValue("GuiProjectSearch", "searchFilters", {"a": True, "b": False}) is True
    assert options.getDict("GuiProjectSearch", "searchFilters", {}) == {"a": True, "b": False}
    assert options.setValue("GuiProjectSearch", "searchFilters", "notADict") is True
    assert options.getDict("GuiProjectSearch", "searchFilters", {}) == {}
    assert options.getDict("GuiProjectSearch", "mockItem", {}) == {}

    # Get enum, invalid value
    assert options.setValue("GuiNovelView", "lastCol", "invalidValue") is True
    assert options.getEnum("GuiNovelView", "lastCol", nwNovelExtra, nwColHidden) == nwColHidden

    # Get from non-existent groups
    assert options.getValue("SomeGroup", "mockItem", None) is None
    assert options.getList("SomeGroup", "mockItem", []) == []
    assert options.getDict("SomeGroup", "mockItem", {}) == {}
    assert options.getString("SomeGroup", "mockItem", None) is None  # type: ignore
    assert options.getInt("SomeGroup", "mockItem", None) is None  # type: ignore
    assert options.getFloat("SomeGroup", "mockItem", None) is None  # type: ignore
    assert options.getBool("SomeGroup", "mockItem", None) is None  # type: ignore
    assert options.getEnum("SomeGroup", "mockItem", nwNovelExtra, None) is None  # type: ignore
