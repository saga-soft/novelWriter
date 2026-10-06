"""
novelWriter - Text Formats Tests
================================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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

from novelwriter.enum import nwComment
from novelwriter.text.formats import _checkModKey, processComment, processHeading


@pytest.mark.core
def testTextFormats_checkModKey():
    """Test the _checkModKey function."""
    # Check Requirements

    # Synopsis
    assert _checkModKey("synopsis", "") is True
    assert _checkModKey("synopsis", "a") is False

    # Short
    assert _checkModKey("short", "") is True
    assert _checkModKey("short", "a") is False

    # Note
    assert _checkModKey("note", "") is True
    assert _checkModKey("note", "a") is True

    # Footnote
    assert _checkModKey("footnote", "") is False
    assert _checkModKey("footnote", "a") is True

    # Invalid
    assert _checkModKey("stuff", "") is False
    assert _checkModKey("stuff", "a") is False

    # Check Keys
    assert _checkModKey("note", "a") is True
    assert _checkModKey("note", "a1") is True
    assert _checkModKey("note", "a1.2") is False
    assert _checkModKey("note", "a1_2") is True


@pytest.mark.core
def testTextFormats_processComment():
    """Test the comment processing function."""
    # Plain
    assert processComment("%Hi") == (nwComment.PLAIN, "", "Hi", 0, 0)
    assert processComment("% Hi") == (nwComment.PLAIN, "", "Hi", 0, 0)
    assert processComment("% Hi:You") == (nwComment.PLAIN, "", "Hi:You", 0, 0)
    assert processComment("% Hi.You:There") == (nwComment.PLAIN, "", "Hi.You:There", 0, 0)

    # Ignore
    assert processComment("%~Hi") == (nwComment.IGNORE, "", "Hi", 0, 0)
    assert processComment("%~ Hi") == (nwComment.IGNORE, "", "Hi", 0, 0)

    # Invalid
    assert processComment("") == (nwComment.PLAIN, "", "", 0, 0)

    # Short : Term not allowed
    assert processComment("%short: Hi") == (nwComment.SHORT, "", "Hi", 0, 7)
    assert processComment("%short.a: Hi") == (nwComment.PLAIN, "", "short.a: Hi", 0, 0)

    # Synopsis : Term not allowed
    assert processComment("%synopsis: Hi") == (nwComment.SYNOPSIS, "", "Hi", 0, 10)
    assert processComment("%synopsis.a: Hi") == (nwComment.PLAIN, "", "synopsis.a: Hi", 0, 0)

    # Note : Term optional
    assert processComment("%note: Hi") == (nwComment.NOTE, "", "Hi", 0, 6)
    assert processComment("%note.a: Hi") == (nwComment.NOTE, "a", "Hi", 6, 8)

    # Footnote : Term required
    assert processComment("%footnote: Hi") == (nwComment.PLAIN, "", "footnote: Hi", 0, 0)
    assert processComment("%footnote.a: Hi") == (nwComment.FOOTNOTE, "a", "Hi", 10, 12)

    # Check Case
    assert processComment("%Footnote.a: Hi") == (nwComment.FOOTNOTE, "a", "Hi", 10, 12)
    assert processComment("%FOOTNOTE.A: Hi") == (nwComment.FOOTNOTE, "A", "Hi", 10, 12)
    assert processComment("%FootNote.A_a: Hi") == (nwComment.FOOTNOTE, "A_a", "Hi", 10, 14)

    # Padding without term
    assert processComment("%short: Hi") == (nwComment.SHORT, "", "Hi", 0, 7)
    assert processComment("% short: Hi") == (nwComment.SHORT, "", "Hi", 0, 8)
    assert processComment("%  short : Hi") == (nwComment.SHORT, "", "Hi", 0, 10)
    assert processComment("%   short  : Hi") == (nwComment.SHORT, "", "Hi", 0, 12)
    assert processComment("% \t  short  : Hi") == (nwComment.SHORT, "", "Hi", 0, 13)

    # Padding with term
    assert processComment("%note.term: Hi") == (nwComment.NOTE, "term", "Hi", 6, 11)
    assert processComment("% note.term: Hi") == (nwComment.NOTE, "term", "Hi", 7, 12)
    assert processComment("% note.term : Hi") == (nwComment.NOTE, "term", "Hi", 7, 13)
    assert processComment("% note. term : Hi") == (nwComment.PLAIN, "", "note. term : Hi", 0, 0)
    assert processComment("% note . term : Hi") == (nwComment.PLAIN, "", "note . term : Hi", 0, 0)


@pytest.mark.core
def testTextFormats_processHeading():
    """Test the heading processing function."""
    # Correct titles
    assert processHeading("# Title") == ("H1", "Title", False)
    assert processHeading("#! Title") == ("H1", "Title", True)
    assert processHeading("## Title") == ("H2", "Title", False)
    assert processHeading("##! Title") == ("H2", "Title", True)
    assert processHeading("### Title") == ("H3", "Title", False)
    assert processHeading("###! Title") == ("H3", "Title", True)
    assert processHeading("#### Title") == ("H4", "Title", False)

    # Stripped text
    assert processHeading("# \tTitle\t  ") == ("H1", "Title", False)

    # Incorrect titles
    assert processHeading("##### Title") == ("H0", "", False)
    assert processHeading("#Title") == ("H0", "", False)
