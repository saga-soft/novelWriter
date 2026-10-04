"""
novelWriter - INI Config Parser Tests
=====================================

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
from novelwriter.formats.configparser import NConfigParser

from tests.helpers import writeFile


@pytest.mark.base
def testConfigParser_NConfigParser(fncPath):
    """Test the NConfigParser subclass."""
    conf = fncPath / "test.cfg"
    writeFile(
        conf,
        (
            "[main]\n"
            "stropt = value\n"
            "intopt1 = 42\n"
            "intopt2 = 42.43\n"
            "boolopt1 = true\n"
            "boolopt2 = TRUE\n"
            "boolopt3 = 1\n"
            "boolopt4 = 0\n"
            "list1 = a, b, c\n"
            "list2 = 17, 18, 19\n"
            "float1 = 4.2\n"
            "enum1 = NOVEL\n"
            f"path1 = {fncPath}\n"
        ),
    )

    parser = NConfigParser()
    parser.read(conf)

    # Readers
    # =======

    # Read String
    assert parser.getStr("main", "stropt", "stuff") == "value"
    assert parser.getStr("main", "boolopt1", "stuff") == "true"
    assert parser.getStr("main", "intopt1", "stuff") == "42"

    assert parser.getStr("nope", "stropt", "stuff") == "stuff"
    assert parser.getStr("main", "blabla", "stuff") == "stuff"

    # Read Boolean
    assert parser.getBool("main", "boolopt1", None) is True  # type: ignore
    assert parser.getBool("main", "boolopt2", None) is True  # type: ignore
    assert parser.getBool("main", "boolopt3", None) is True  # type: ignore
    assert parser.getBool("main", "boolopt4", None) is False  # type: ignore
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

    assert parser.getStrList("main", "stropt", ["x"]) == ["value"]
    assert parser.getStrList("main", "intopt1", ["x"]) == ["42"]

    assert parser.getStrList("nope", "list1", ["x"]) == ["x"]
    assert parser.getStrList("main", "blabla", ["x"]) == ["x"]

    # Read Integer List
    assert parser.getIntList("main", "list2", []) == []
    assert parser.getIntList("main", "list2", [1]) == [17]
    assert parser.getIntList("main", "list2", [1, 2]) == [17, 18]
    assert parser.getIntList("main", "list2", [1, 2, 3]) == [17, 18, 19]
    assert parser.getIntList("main", "list2", [1, 2, 3, 4]) == [17, 18, 19, 4]

    assert parser.getIntList("main", "stropt", [1]) == [1]
    assert parser.getIntList("main", "boolopt1", [1]) == [1]

    assert parser.getIntList("nope", "list2", [1]) == [1]
    assert parser.getIntList("main", "blabla", [1]) == [1]

    # Read Enum
    assert parser.getEnum("main", "enum1", nwItemClass.NO_CLASS) == nwItemClass.NOVEL
    assert parser.getEnum("main", "blabla", nwItemClass.NO_CLASS) == nwItemClass.NO_CLASS
