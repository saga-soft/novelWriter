"""
novelWriter - Project Search Tests
==================================

This file is a part of novelWriter
Copyright (C) 2022 Veronica Berglyd Olsen and novelWriter contributors

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

import re

import pytest

from novelwriter.constants import nwConst
from novelwriter.core.project import NWProject
from novelwriter.core.projectsearch import DocSearch

from tests.helpers import C, buildTestProject


@pytest.mark.core
def testProjectSearch_Search(monkeypatch, mockGUI, fncPath, mockRnd, ipsumText):
    """Test the DocSearch utility."""
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\n" + "\n\n".join(ipsumText))

    search = DocSearch()

    # Defaults
    # ========

    result = [(i.itemHandle, r, c) for i, r, c in search.iterSearch(project, "Scene")]
    assert result[0] == (C.hTitlePage, [], False)
    assert result[1] == (C.hChapterDoc, [], False)
    assert result[2] == (C.hSceneDoc, [(8, 5, "### New Scene", 8)], False)

    # Patterns
    # ========

    # Escape
    assert search._buildPattern("[A-Za-z0-9_]+") == r"\[A\-Za\-z0\-9_\]\+"

    # Whole Words
    search.setWholeWords(True)
    search.setUserRegEx(True)
    assert search._buildPattern("Hi") == r"(?:^|\b)Hi(?:$|\b)"
    search.setWholeWords(False)
    search.setUserRegEx(False)

    # Test Settings
    # =============

    def pruneResult(result, index):
        temp = [(i.itemHandle, r, c) for i, r, c in result][index][1]
        return [(s, n, c[o : o + n]) for s, n, c, o in temp]

    # Defaults
    assert pruneResult(search.iterSearch(project, "Lorem"), 2) == [
        (15, 5, "Lorem"),
        (754, 5, "lorem"),
        (2056, 5, "lorem"),
        (2209, 5, "lorem"),
        (2425, 5, "lorem"),
        (2840, 5, "lorem"),
        (3399, 5, "lorem"),
    ]

    # Whole Words
    search.setWholeWords(True)
    assert pruneResult(search.iterSearch(project, "Lor"), 2) == []
    search.setWholeWords(False)
    assert pruneResult(search.iterSearch(project, "Lor"), 2) == [
        (15, 3, "Lor"),
        (29, 3, "lor"),
        (754, 3, "lor"),
        (2056, 3, "lor"),
        (2209, 3, "lor"),
        (2425, 3, "lor"),
        (2840, 3, "lor"),
        (3328, 3, "lor"),
        (3399, 3, "lor"),
    ]

    # As RegEx
    search.setWholeWords(False)
    search.setUserRegEx(True)
    assert pruneResult(search.iterSearch(project, r"Lor\b"), 2) == [
        (29, 3, "lor"),
        (3328, 3, "lor"),
    ]

    # Max Results
    with monkeypatch.context() as mp:
        mp.setattr(nwConst, "MAX_SEARCH_RESULT", 3)
        assert pruneResult(search.iterSearch(project, "Lorem"), 2) == [
            (15, 5, "Lorem"),
            (754, 5, "lorem"),
            (2056, 5, "lorem"),
        ]

    # Case Sensitive
    search.setCaseSensitive(True)
    assert pruneResult(search.iterSearch(project, "Lorem"), 2) == [(15, 5, "Lorem")]
    search.setCaseSensitive(False)

    # A match on an empty line yields no context in either direction
    search._regEx = re.compile(r"$")
    assert search.searchText("") == ([], False)


@pytest.mark.core
def testProjectSearch_SearchContext():
    """Test that the search context flows in both directions from the
    match, but is clipped at the line boundary.
    """
    search = DocSearch()

    # The context flows in both directions from the match
    search._regEx = re.compile(r"MATCH")
    text = "some words before MATCH and some words after"
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, num, context, offset = results[0]
    assert context[offset : offset + num] == "MATCH"
    assert context == text
    assert offset == 18

    # The context never crosses into the previous or next line, even
    # when the match sits right at the start of its own line
    search._regEx = re.compile(r"MATCH")
    text = "Previous line text that must never appear here\nMATCH end of line\n"
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, _, context, offset = results[0]
    assert offset == 0
    assert context == "MATCH end of line"

    # A long single line is capped at ~20 characters to the left and
    # ~80 characters to the right, both trimmed to a word boundary,
    # and never leaks into the adjacent lines
    search._regEx = re.compile(r"TARGET")
    pre = "abcde " * 10
    post = "fghij " * 20
    text = f"prevline marker should not appear\n{pre}TARGET {post}\nnextline marker should not appear"
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, num, context, offset = results[0]
    assert context[offset : offset + num] == "TARGET"
    assert "prevline" not in context
    assert "nextline" not in context
    assert offset <= 20
    assert len(context) - (offset + num) <= 80

    # When there is no space to trim to on the left, the cut lands
    # mid-word at the raw 20 character mark instead
    search._regEx = re.compile(r"MATCH")
    text = ("a" * 30) + "MATCH"
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, num, context, offset = results[0]
    assert context[offset : offset + num] == "MATCH"
    assert offset == 20

    # Likewise on the right, at the raw 80 character mark
    text = "MATCH" + ("b" * 100)
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, num, context, offset = results[0]
    assert context[offset : offset + num] == "MATCH"
    assert len(context) - (offset + num) == 80

    # A match that is itself much longer than the total context cap,
    # such as a greedy RegEx like `.*` grabbing a whole paragraph, is
    # truncated so the context never exceeds 100 characters in total
    search._regEx = re.compile(r".*")
    text = "x" * 30 + "y" * 300
    results, _ = search.searchText(text)
    assert len(results) == 1
    pos, num, context, offset = results[0]
    assert pos == 0
    assert num == 330
    assert offset == 0
    assert len(context) == 100

    # The same cap applies when there is context on the left as well
    search._regEx = re.compile(r"MATCH.*")
    text = "some words " + "MATCH" + ("z" * 300)
    results, _ = search.searchText(text)
    assert len(results) == 1
    _, num, context, offset = results[0]
    assert context[offset : offset + 5] == "MATCH"
    assert len(context) == 100


@pytest.mark.core
def testProjectSearch_DocumentFilters(mockGUI, fncPath, mockRnd):
    """Test that the document type and root folder filters exclude the
    expected documents from the project-wide search.
    """
    project = NWProject()
    mockRnd.reset()
    buildTestProject(project, fncPath)

    # Add a note under the Character root, and mark the scene document
    # as inactive, then add the search term to all three documents
    noteHandle = project.newFile("Jane", C.hCharRoot)
    assert noteHandle is not None
    project.storage.getDocument(noteHandle).writeDocument("@tag: Jane\n\nTARGET\n")
    project.tree[C.hSceneDoc].setActive(False)  # type: ignore
    project.storage.getDocument(C.hSceneDoc).writeDocument("### New Scene\n\nTARGET\n")
    project.storage.getDocument(C.hChapterDoc).writeDocument("## New Chapter\n\nTARGET\n")

    search = DocSearch()

    def handles(result):
        return [i.itemHandle for i, r, _ in result if r]

    # By default, novel documents, notes, and inactive documents are all included
    assert handles(search.iterSearch(project, "TARGET")) == [C.hChapterDoc, C.hSceneDoc, noteHandle]

    # Excluding notes removes the character note
    search.setDocumentFilters(novel=True, notes=False, inactive=True)
    assert handles(search.iterSearch(project, "TARGET")) == [C.hChapterDoc, C.hSceneDoc]

    # Excluding novel documents leaves only the note
    search.setDocumentFilters(novel=False, notes=True, inactive=True)
    assert handles(search.iterSearch(project, "TARGET")) == [noteHandle]

    # Excluding inactive documents removes the inactive scene
    search.setDocumentFilters(novel=True, notes=True, inactive=False)
    assert handles(search.iterSearch(project, "TARGET")) == [C.hChapterDoc, noteHandle]

    # Restore the document filter defaults
    search.setDocumentFilters(novel=True, notes=True, inactive=True)

    # Skipping the Character root excludes the note even though the
    # document filters above would otherwise allow it
    search.setSkipRoots([C.hCharRoot])
    assert handles(search.iterSearch(project, "TARGET")) == [C.hChapterDoc, C.hSceneDoc]

    # Clearing the skip list restores the note to the results
    search.setSkipRoots([])
    assert handles(search.iterSearch(project, "TARGET")) == [C.hChapterDoc, C.hSceneDoc, noteHandle]


@pytest.mark.core
def testProjectSearch_NoDuplicates():
    """Test that a RegEx that can produce a zero-length match right
    after a preceding match, such as `.*`, does not yield a
    near-duplicate result.
    """
    search = DocSearch()
    search._regEx = re.compile(r".*")
    text = "Hello world\nSecond line here\n"
    results, _ = search.searchText(text)
    assert [(pos, num) for pos, num, _, _ in results] == [(0, 11), (12, 16)]


@pytest.mark.core
def testProjectSearch_ContentFilters():
    """Test that the content type filters exclude matches on headings,
    meta data and comment lines as expected, and that masking those
    lines out doesn't shift the position or context of matches on the
    remaining lines.
    """
    search = DocSearch()
    search._regEx = re.compile(r"TARGET")
    text = "# Heading TARGET\n@char: TARGET\n% comment TARGET\n\nBody text TARGET here\n"

    def pruneResult(result):
        return [(pos, num, context) for pos, num, context, _ in result]

    # By default, all content types are searched
    results, capped = search.searchText(text)
    assert capped is False
    assert pruneResult(results) == [
        (10, 6, "# Heading TARGET"),
        (24, 6, "@char: TARGET"),
        (41, 6, "% comment TARGET"),
        (59, 6, "Body text TARGET here"),
    ]

    # Excluding headings removes only the heading match, and the
    # position and context of the other matches is unaffected
    search.setContentFilters(headings=False, meta=True, comments=True, body=True)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [
        (24, 6, "@char: TARGET"),
        (41, 6, "% comment TARGET"),
        (59, 6, "Body text TARGET here"),
    ]

    # Excluding meta data removes only the meta match
    search.setContentFilters(headings=True, meta=False, comments=True, body=True)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [
        (10, 6, "# Heading TARGET"),
        (41, 6, "% comment TARGET"),
        (59, 6, "Body text TARGET here"),
    ]

    # Excluding comments removes only the comment match
    search.setContentFilters(headings=True, meta=True, comments=False, body=True)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [
        (10, 6, "# Heading TARGET"),
        (24, 6, "@char: TARGET"),
        (59, 6, "Body text TARGET here"),
    ]

    # Excluding body text removes only the body match
    search.setContentFilters(headings=True, meta=True, comments=True, body=False)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [
        (10, 6, "# Heading TARGET"),
        (24, 6, "@char: TARGET"),
        (41, 6, "% comment TARGET"),
    ]

    # Excluding everything but body text leaves only the body match
    search.setContentFilters(headings=False, meta=False, comments=False, body=True)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [(59, 6, "Body text TARGET here")]

    # Excluding everything yields no matches at all
    search.setContentFilters(headings=False, meta=False, comments=False, body=False)
    results, _ = search.searchText(text)
    assert results == []

    # Restore full text search, and confirm the result is identical
    # to the initial, unfiltered search
    search.setContentFilters(headings=True, meta=True, comments=True, body=True)
    results, _ = search.searchText(text)
    assert pruneResult(results) == [
        (10, 6, "# Heading TARGET"),
        (24, 6, "@char: TARGET"),
        (41, 6, "% comment TARGET"),
        (59, 6, "Body text TARGET here"),
    ]
