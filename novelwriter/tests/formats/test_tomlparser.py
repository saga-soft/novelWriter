"""
novelWriter - TOML Config Parser Tests
======================================

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

from pathlib import Path

import pytest

from novelwriter.enum import nwItemClass
from novelwriter.formats.tomlparser import NTomlParser, T_TomlConfig, T_TomlObject

from tests.helpers import writeFile


@pytest.mark.base
def testTomlParser_NTomlParser(fncPath):
    """Test the NTomlParser class."""
    conf = fncPath / "test.toml"
    writeFile(
        conf,
        (
            "[main]\n"
            'stropt = "value"\n'
            "intopt1 = 42\n"
            'intopt2 = "42.43"\n'
            "boolopt1 = true\n"
            "boolopt2 = false\n"
            "boolopt3 = 1\n"
            "boolopt4 = 0\n"
            'boolopt5 = "true"\n'
            'list1 = ["a", "b", "c"]\n'
            "list2 = [17, 18, 19]\n"
            "float1 = 4.2\n"
            'enum1 = "NOVEL"\n'
            f'path1 = "{fncPath.as_posix()}"\n'
        ),
    )

    parser = NTomlParser()
    parser.read(conf)

    # Readers
    # =======

    # Read String
    assert parser.getStr("main", "stropt", "stuff") == "value"
    assert parser.getStr("main", "intopt1", "stuff") == "stuff"

    assert parser.getStr("nope", "stropt", "stuff") == "stuff"
    assert parser.getStr("main", "blabla", "stuff") == "stuff"

    # Read Boolean
    assert parser.getBool("main", "boolopt1", None) is True  # type: ignore
    assert parser.getBool("main", "boolopt2", None) is False  # type: ignore
    assert parser.getBool("main", "boolopt3", None) is True  # type: ignore
    assert parser.getBool("main", "boolopt4", None) is False  # type: ignore
    assert parser.getBool("main", "boolopt5", None) is True  # type: ignore
    assert parser.getBool("main", "intopt1", None) is None  # type: ignore

    assert parser.getBool("nope", "boolopt1", None) is None  # type: ignore
    assert parser.getBool("main", "blabla", None) is None  # type: ignore

    # Read Integer
    assert parser.getInt("main", "intopt1", 13) == 42
    assert parser.getInt("main", "intopt2", 13) == 13
    assert parser.getInt("main", "stropt", 13) == 13

    assert parser.getInt("nope", "intopt1", 13) == 13
    assert parser.getInt("main", "blabla", 13) == 13

    # Read Float
    assert parser.getFloat("main", "intopt1", 13.0) == 42.0
    assert parser.getFloat("main", "float1", 13.0) == 4.2
    assert parser.getFloat("main", "stropt", 13.0) == 13.0

    assert parser.getFloat("nope", "intopt1", 13.0) == 13.0
    assert parser.getFloat("main", "blabla", 13.0) == 13.0

    # Read Path
    assert parser.getPath("main", "path1", Path.home()) == fncPath

    # Read String List
    assert parser.getStrList("main", "list1", []) == []
    assert parser.getStrList("main", "list1", ["x"]) == ["a"]
    assert parser.getStrList("main", "list1", ["x", "y"]) == ["a", "b"]
    assert parser.getStrList("main", "list1", ["x", "y", "z"]) == ["a", "b", "c"]
    assert parser.getStrList("main", "list1", ["x", "y", "z", "w"]) == ["a", "b", "c", "w"]

    assert parser.getStrList("main", "stropt", ["x"]) == ["x"]

    assert parser.getStrList("nope", "list1", ["x"]) == ["x"]
    assert parser.getStrList("main", "blabla", ["x"]) == ["x"]

    # Read Integer List
    assert parser.getIntList("main", "list2", []) == []
    assert parser.getIntList("main", "list2", [1]) == [17]
    assert parser.getIntList("main", "list2", [1, 2]) == [17, 18]
    assert parser.getIntList("main", "list2", [1, 2, 3]) == [17, 18, 19]
    assert parser.getIntList("main", "list2", [1, 2, 3, 4]) == [17, 18, 19, 4]

    assert parser.getIntList("main", "stropt", [1]) == [1]

    assert parser.getIntList("nope", "list2", [1]) == [1]
    assert parser.getIntList("main", "blabla", [1]) == [1]

    # Read Enum
    assert parser.getEnum("main", "enum1", nwItemClass.NO_CLASS) == nwItemClass.NOVEL
    assert parser.getEnum("main", "blabla", nwItemClass.NO_CLASS) == nwItemClass.NO_CLASS


@pytest.mark.base
def testTomlParser_Flat(fncPath):
    """Test reading and writing a flat, section-less structure using
    a parser constructed with flat=True.
    """
    data: T_TomlObject = {"name": "Document Name", "hash": "abc123"}

    parser = NTomlParser(flat=True)
    text = parser.writeString(data)
    assert text == 'name = "Document Name"\nhash = "abc123"\n'

    path = fncPath / "flat.toml"
    parser.write(path, data)
    assert text == path.read_text(encoding="utf-8")

    reader = NTomlParser(flat=True)
    reader.readString(text)
    assert reader.getStr(None, "name", "") == "Document Name"
    assert reader.getStr(None, "hash", "") == "abc123"
    assert reader.getStr(None, "nope", "") == ""

    # An empty dict produces an empty string
    assert parser.writeString({}) == ""

    # Sections aren't a concept in this mode: a section in the source
    # asking for one via a non-None section also finds nothing
    assert reader.getStr("Meta", "name", "") == ""


@pytest.mark.base
def testTomlParser_NTomlParserInvalid(fncPath, caplog):
    """Test that NTomlParser logs and drops entries nested deeper than
    the supported structure for each mode, for both write and read.
    """
    # Read: a nested table within a section is dropped, but the rest
    # of the section is kept
    path = fncPath / "invalid_read.toml"
    writeFile(path, '[Main]\nfont = "Sans Serif"\n\n[Main.sub]\nbad = "nope"\n')
    reader = NTomlParser()
    reader.read(path)
    assert "Invalid config entry 'Main.sub'" in caplog.text
    assert reader.getStr("Main", "font", "") == "Sans Serif"
    caplog.clear()

    # Write: a non-dict section entry is skipped and logged
    path2 = fncPath / "invalid_write.toml"
    parser = NTomlParser()
    parser.write(path2, {"Main": {"font": "Sans Serif"}, "bad": "not a section"})  # type: ignore
    assert "Invalid config section 'bad'" in caplog.text
    caplog.clear()

    reader2 = NTomlParser()
    reader2.read(path2)
    assert reader2.getStr("Main", "font", "") == "Sans Serif"

    # Read (flat mode): a table isn't a supported value and is dropped
    path3 = fncPath / "invalid_flat.toml"
    writeFile(path3, 'font = "Sans Serif"\n\n[Main]\nbad = "nope"\n')
    reader3 = NTomlParser(flat=True)
    reader3.read(path3)
    assert "Invalid config entry 'Main', sections are not supported in flat mode" in caplog.text
    assert reader3.getStr(None, "font", "") == "Sans Serif"


@pytest.mark.base
def testTomlParser_ReadWriteString(fncPath):
    """Test the readString and writeString methods, and that they
    produce output identical to the file-based read and write.
    """
    data: T_TomlConfig = {
        "main": {
            "stropt": "value",
            "intopt1": 42,
            "boolopt1": True,
            "list1": ["a", "b", "c"],
            "float1": 4.2,
            "enum1": nwItemClass.NOVEL,
        },
    }

    parser = NTomlParser()
    text = parser.writeString(data)

    path = fncPath / "string.toml"
    parser.write(path, data)
    assert text == path.read_text(encoding="utf-8")

    reader = NTomlParser()
    reader.readString(text)
    assert reader.getStr("main", "stropt", "") == "value"
    assert reader.getInt("main", "intopt1", 0) == 42
    assert reader.getBool("main", "boolopt1", False) is True
    assert reader.getStrList("main", "list1", ["", "", ""]) == ["a", "b", "c"]
    assert reader.getFloat("main", "float1", 0.0) == 4.2
    assert reader.getEnum("main", "enum1", nwItemClass.NO_CLASS) == nwItemClass.NOVEL

    # An empty dict produces an empty string, not just section boilerplate
    assert parser.writeString({}) == ""


@pytest.mark.base
def testTomlParser_ReadWriteStringInvalid(caplog):
    """Test that readString and writeString log and drop entries
    nested deeper than the supported structure, mirroring the
    file-based test but through strings.
    """
    parser = NTomlParser()
    text = parser.writeString({"Main": {"font": "Sans Serif"}, "bad": "not a section"})  # type: ignore
    assert "Invalid config section 'bad'" in caplog.text
    caplog.clear()

    reader = NTomlParser()
    reader.readString(text)
    assert reader.getStr("Main", "font", "") == "Sans Serif"

    reader2 = NTomlParser()
    reader2.readString('[Main]\nfont = "Sans Serif"\n\n[Main.sub]\nbad = "nope"\n')
    assert "Invalid config entry 'Main.sub'" in caplog.text
    assert reader2.getStr("Main", "font", "") == "Sans Serif"

    # A bare top-level key is invalid outside of flat mode
    reader3 = NTomlParser()
    reader3.readString('bad = "not a section"\n\n[Main]\nfont = "Sans Serif"\n')
    assert "Invalid config section 'bad'" in caplog.text
    assert reader3.getStr("Main", "font", "") == "Sans Serif"
