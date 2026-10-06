"""
novelWriter - Index Data Tests
==============================

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

import pytest

from novelwriter import CONFIG
from novelwriter.core.index import IndexCache, TagsIndex
from novelwriter.core.indexdata import IndexHeading, IndexNode
from novelwriter.core.item import ProjectItem
from novelwriter.core.project import NWProject
from novelwriter.enum import nwComment


@pytest.mark.core
def testIndexData_IndexNode(mockGUI):
    """Test the IndexNode class."""
    handle = "0123456789abc"
    project = NWProject()
    item = ProjectItem(project, handle)
    cache = IndexCache(TagsIndex())

    # Defaults
    node = IndexNode(cache, handle, item)
    assert node.handle == handle
    assert node.item is item
    assert str(node) == f"<IndexNode handle='{handle}'>"
    assert repr(node) == f"<IndexNode handle='{handle}'>"
    assert len(node) == 1
    assert "T0000" in node  # Placeholder heading

    # Add a heading
    head1 = IndexHeading(cache, node.nextHeading(), line=1, level="H1", title="Heading 1")
    head2 = IndexHeading(cache, node.nextHeading(), line=10, level="H2", title="Heading 2")
    node.addHeading(head1)
    node.addHeading(head2)
    assert len(node) == 2
    assert "T0000" not in node  # Placeholder heading should be gone
    assert "T0001" in node
    assert "T0002" in node
    assert node["T0001"] is head1
    assert node["T0002"] is head2
    assert node.headings() == ["T0001", "T0002"]
    assert dict(node.items()) == {"T0001": head1, "T0002": head2}

    # Next heading should be T0003
    assert node.nextHeading() == "T0003"

    # Set counts
    node.setHeadingCounts("T0001", 42, 13, 3)
    node.setHeadingCounts("T0002", 84, 26, 6)
    assert head1.charCount == 42
    assert head1.wordCount == 13
    assert head1.paraCount == 3
    assert head2.charCount == 84
    assert head2.wordCount == 26
    assert head2.paraCount == 6

    # Set synopsis
    node.setHeadingComment("T0001", nwComment.SYNOPSIS, "", "The first")
    node.setHeadingComment("T0002", nwComment.SYNOPSIS, "", "The second")
    assert head1.synopsis == "The first"
    assert head2.synopsis == "The second"

    # Set cache
    node.setHeadingTag("T0001", "part1")
    node.setHeadingTag("T0002", "part2")
    assert head1.tag == "part1"
    assert head2.tag == "part2"
    assert node.allTags() == ["part1", "part2"]

    # Add references
    node.addHeadingRef("T0001", ["jane"], "@pov")
    node.addHeadingRef("T0001", ["jane", "john"], "@char")
    node.addHeadingRef("T0002", ["earth", "space"], "@location")
    assert head1.references["jane"] == {"@char", "@pov"}
    assert head1.references["john"] == {"@char"}
    assert head2.references["earth"] == {"@location"}
    assert head2.references["space"] == {"@location"}

    # Unknown headings are silently ignored
    node.setHeadingCounts("T9999", 1, 1, 1)
    node.setHeadingComment("T9999", nwComment.SYNOPSIS, "", "Ignored")
    node.setHeadingTag("T9999", "ignored")
    node.addHeadingRef("T9999", ["jane"], "@pov")

    # Add note keys
    assert node.noteKeys("footnotes") == set()
    node.addNoteKey("footnotes", "key1")
    node.addNoteKey("footnotes", "key2")
    assert node.noteKeys("footnotes") == {"key1", "key2"}


@pytest.mark.core
def testIndexData_IndexNodePackUnpack(mockGUI):
    """Test the pack and unpack methods of the IndexNode class."""
    handle = "0123456789abc"
    project = NWProject()
    item = ProjectItem(project, handle)
    cache = IndexCache(TagsIndex())
    node = IndexNode(cache, handle, item)

    # Add some headings and notes
    head1 = IndexHeading(cache, node.nextHeading(), line=1, level="H1", title="Heading 1")
    head2 = IndexHeading(cache, node.nextHeading(), line=10, level="H2", title="Heading 2")
    node.addHeading(head1)
    node.addHeading(head2)
    node.setHeadingCounts("T0001", 42, 13, 3)
    node.setHeadingCounts("T0002", 84, 26, 6)
    node.addNoteKey("footnotes", "key1")
    node.addNoteKey("footnotes", "key2")

    # Check packing
    data = node.packData()
    assert data["T0001"] == {
        "meta": {
            "level": "H1",
            "title": "Heading 1",
            "mod": False,
            "line": 1,
            "tag": "",
            "counts": (42, 13, 3),
        }
    }
    assert data["T0002"] == {
        "meta": {
            "level": "H2",
            "title": "Heading 2",
            "mod": False,
            "line": 10,
            "tag": "",
            "counts": (84, 26, 6),
        }
    }
    assert set(data["document"]["footnotes"]) == {"key1", "key2"}

    # Create a new node
    new = IndexNode(cache, handle, item)

    # Unpack heading one
    data = {
        "T0001": {
            "meta": {
                "level": "H1",
                "title": "Heading 1",
                "mod": False,
                "line": 1,
                "tag": "",
                "counts": (42, 13, 3),
            }
        }
    }
    new.unpackData(data)
    data = new.packData()
    assert data["T0001"] == {
        "meta": {
            "level": "H1",
            "title": "Heading 1",
            "mod": False,
            "line": 1,
            "tag": "",
            "counts": (42, 13, 3),
        }
    }

    # Unpack invalid key
    data = {"stuff": "whatever"}
    with pytest.raises(KeyError, match="Index node contains an invalid key"):
        new.unpackData(data)

    # Unpack invalid document keys
    data = {"document": {"whatever": []}}
    with pytest.raises(ValueError, match="The notes style is invalid"):
        new.unpackData(data)

    # Unpack invalid document values
    data = {"document": {"footnotes": [1, 2, 3]}}
    with pytest.raises(ValueError, match="The notes keys must be a list of strings"):
        new.unpackData(data)

    # Unpack valid keys
    data = {"document": {"footnotes": ["key1", "key2"]}}
    new.unpackData(data)
    assert set(new.packData()["document"]["footnotes"]) == {"key1", "key2"}


@pytest.mark.core
def testIndexData_IndexHeading():
    """Test the IndexHeading class."""
    # Defaults
    cache = IndexCache(TagsIndex())
    head = IndexHeading(cache, "T0001")
    assert str(head) == "<IndexHeading key='T0001'>"
    assert repr(head) == "<IndexHeading key='T0001'>"
    assert head.key == "T0001"
    assert head.line == 0
    assert head.level == "H0"
    assert head.title == ""
    assert head.charCount == 0
    assert head.wordCount == 0
    assert head.paraCount == 0
    assert head.mainCount == 0
    assert head.synopsis == ""
    assert head.tag == ""
    assert head.references == {}

    # Set Level
    head.setLevel("Stuff")  # Invalid
    assert head.level == "H0"
    head.setLevel("H1")  # Valid
    assert head.level == "H1"

    # Set Line
    head.setLine(-1)  # Invalid
    assert head.line == 0
    head.setLine(42)  # Valid
    assert head.line == 42

    # Set Counts
    head.setCounts([1, 2])  # Invalid, must be three values
    assert head.charCount == 0
    assert head.wordCount == 0
    assert head.paraCount == 0
    head.setCounts([42, 4, 2])  # Valid
    assert head.charCount == 42
    assert head.wordCount == 4
    assert head.paraCount == 2

    # Check Main Count
    assert head.mainCount == 4
    CONFIG.useCharCount = True
    assert head.mainCount == 42

    # Set Summary
    head.setComment(nwComment.SYNOPSIS.name, "", "In the beginning ...")
    assert head.synopsis == "In the beginning ..."

    # Set Story Structure Comment
    head.setComment(nwComment.STORY.name, "crisis", "It exploded!")
    assert head.comments == {
        "summary": "In the beginning ...",
        "story.crisis": "It exploded!",
    }

    # Set Note Comment
    head.setComment(nwComment.NOTE.name, "consitency", "Only explode once")
    assert head.comments == {
        "summary": "In the beginning ...",
        "story.crisis": "It exploded!",
        "note.consitency": "Only explode once",
    }

    # Set Tag
    head.setTag("Stuff")
    assert head.tag == "stuff"  # Case insensitive

    # Add References
    head.addReference("Stuff", "@stuff")  # Invalid type
    assert head.references == {}
    head.addReference("Stuff", "@object")  # Valid type
    assert head.references == {"stuff": {"@object"}}

    # Pack Data
    assert head.packData() == {
        "meta": {"level": "H1", "title": "", "mod": False, "line": 42, "tag": "stuff", "counts": (42, 4, 2)},
        "refs": {"stuff": "@object"},
        "summary": "In the beginning ...",
        "story.crisis": "It exploded!",
        "note.consitency": "Only explode once",
    }

    # Append Synopsis
    head.setComment(nwComment.SYNOPSIS.name, "", "How it started ...")
    assert head.synopsis == "In the beginning ...\n\nHow it started ..."

    # Unpack KeyError
    with pytest.raises(KeyError, match="Unknown key in heading entry"):
        head.unpackData({"stuff": "more stuff"})

    # Unpack Comments
    head.unpackData({"summary": "How it started ..."})
    assert head.synopsis == "How it started ..."  # This resets the comments dictionary


@pytest.mark.core
def testIndexHeading_References():
    """Test the IndexHeading references handling."""
    cache = IndexCache(TagsIndex())
    head = IndexHeading(cache, "T0001")

    # Add some references
    head.setTag("Scene")
    head.addReference("Jane", "@pov")
    head.addReference("Jane", "@char")
    head.addReference("John", "@char")
    head.addReference("Main", "@plot")
    head.addReference("Gun", "@object")

    # With no tagsIndex name set, these should be empty
    assert head.getReferences() == {
        "@entity": [],
        "@plot": [],
        "@object": [],
        "@story": [],
        "@tag": [],
        "@focus": [],
        "@custom": [],
        "@time": [],
        "@pov": [],
        "@mention": [],
        "@char": [],
        "@location": [],
    }
    assert head.getReferencesByKeyword("@tag") == []

    # Set names
    cache.tags.add("Scene", "Scene", "0000000000000", "T00001", "NOVEL")
    cache.tags.add("Jane", "Jane", "0000000000000", "T00001", "CHARACTER")
    cache.tags.add("John", "John", "0000000000000", "T00001", "CHARACTER")
    cache.tags.add("Main", "Main", "0000000000000", "T00001", "PLOT")
    cache.tags.add("Gun", "Gun", "0000000000000", "T00001", "OBJECT")

    # Now they should be populated
    assert head.getReferences() == {
        "@entity": [],
        "@plot": ["Main"],
        "@object": ["Gun"],
        "@story": [],
        "@tag": ["Scene"],
        "@focus": [],
        "@custom": [],
        "@time": [],
        "@pov": ["Jane"],
        "@mention": [],
        "@char": ["Jane", "John"],
        "@location": [],
    }

    # Check them individually
    assert head.getReferencesByKeyword("@entity") == []
    assert head.getReferencesByKeyword("@plot") == ["Main"]
    assert head.getReferencesByKeyword("@object") == ["Gun"]
    assert head.getReferencesByKeyword("@story") == []
    assert head.getReferencesByKeyword("@tag") == ["Scene"]
    assert head.getReferencesByKeyword("@focus") == []
    assert head.getReferencesByKeyword("@custom") == []
    assert head.getReferencesByKeyword("@time") == []
    assert head.getReferencesByKeyword("@pov") == ["Jane"]
    assert head.getReferencesByKeyword("@mention") == []
    assert head.getReferencesByKeyword("@char") == ["Jane", "John"]
    assert head.getReferencesByKeyword("@location") == []


@pytest.mark.core
def testIndexHeading_UnpackMeta():
    """Test IndexHeading class meta unpacking."""
    cache = IndexCache(TagsIndex())

    # Valid
    data = {
        "meta": {
            "level": "H1",
            "title": "So it Begins",
            "mod": True,
            "line": 1,
            "tag": "begins",
            "counts": [95, 18, 1],
        }
    }
    head = IndexHeading(cache, "T0001")
    head.unpackData(data)
    assert head.level == "H1"
    assert head.title == "So it Begins"
    assert head.modified is True
    assert head.line == 1
    assert head.tag == "begins"
    assert head.charCount == 95
    assert head.wordCount == 18
    assert head.paraCount == 1

    # Invalid
    data = {"meta": {"level": "H9", "title": None, "mod": None, "line": None, "tag": None, "counts": [42]}}
    head = IndexHeading(cache, "T0001")
    head.unpackData(data)
    assert head.level == "H0"
    assert head.title == "None"
    assert head.modified is False
    assert head.line == 0
    assert head.tag == "None"
    assert head.charCount == 0
    assert head.wordCount == 0
    assert head.paraCount == 0

    # Empty
    data = {"meta": {}}
    head = IndexHeading(cache, "T0001")
    with pytest.raises(KeyError, match="Heading meta is missing keys"):
        head.unpackData(data)


@pytest.mark.core
def testIndexHeading_UnpackRefs():
    """Test IndexHeading class refs unpacking."""
    cache = IndexCache(TagsIndex())

    # Valid
    data = {"refs": {"jane": "@char,@pov", "john": "@char", "earth": "@location", "space": "@mention,@location"}}
    head = IndexHeading(cache, "T0001")
    head.unpackData(data)
    assert head.references["jane"] == {"@char", "@pov"}
    assert head.references["john"] == {"@char"}
    assert head.references["earth"] == {"@location"}
    assert head.references["space"] == {"@location", "@mention"}

    # Invalid key
    data = {"refs": {0: "@char,@pov"}}
    head = IndexHeading(cache, "T0001")
    with pytest.raises(ValueError, match="Heading reference key must be a string"):
        head.unpackData(data)

    # Invalid value
    data = {"refs": {"jane": None}}
    head = IndexHeading(cache, "T0001")
    with pytest.raises(ValueError, match="Heading reference value must be a string"):
        head.unpackData(data)

    # Invalid keyword
    data = {"refs": {"jane": "@char,@pov,@stuff"}}
    head = IndexHeading(cache, "T0001")
    with pytest.raises(ValueError, match="Heading reference contains an invalid keyword"):
        head.unpackData(data)
