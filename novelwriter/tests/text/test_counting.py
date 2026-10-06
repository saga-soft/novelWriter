"""
novelWriter - Text Counter Tests
================================

This file is a part of novelWriter
Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors

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

from novelwriter.text.counting import bodyTextCounter, preProcessText, standardCounter


@pytest.mark.core
def testTextCounting_preProcessText():
    """Test the text preprocessor for counters."""
    # Not Text
    assert preProcessText(None) == []  # type: ignore

    # No Text
    assert preProcessText("") == []

    text = (
        "#! Title\n"
        "##! Prologue\n"
        "# Heading One\n"
        "## Heading Two\n"
        "### Heading Three\n"
        "#### Heading Four\n\n"
        "@tag: value\n\n"
        "% A comment.\n\n"
        "A [b]paragraph[/b].\n\n"
        "[vspace:3]\n\n"
        "[New Page]\n\n"
        "[footnote:abcd]\n\n"
        "[br]\n\n"
        "Dashes\u2013and even longer\u2014dashes.\n\n"
    )

    # Process Text, w/Headers
    assert preProcessText(text) == [
        "#! Title",
        "##! Prologue",
        "# Heading One",
        "## Heading Two",
        "### Heading Three",
        "#### Heading Four",
        "",
        "",
        "",
        "A paragraph.",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Dashes and even longer dashes.",
        "",
    ]

    # Process Text, wo/Headers
    assert preProcessText(text, keepHeaders=False) == [
        "",
        "",
        "",
        "A paragraph.",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "Dashes and even longer dashes.",
        "",
    ]


@pytest.mark.core
def testTextCounting_standardCounter():
    """Test the standard counter."""
    # Non-Text
    assert standardCounter(None) == (0, 0, 0)  # type: ignore
    assert standardCounter(1234) == (0, 0, 0)  # type: ignore

    # Test Corner Cases, Bug #1816
    assert standardCounter("> ") == (0, 0, 0)
    assert standardCounter(" <") == (0, 0, 0)

    # General Text
    cC, wC, pC = standardCounter(
        "#! Title\n\n"
        "##! Prologue\n\n"
        "# Heading One\n"
        "## Heading Two\n"
        "### Heading Three\n"
        "###! Heading Four\n"
        "#### Heading Five\n\n"
        "@tag: value\n\n"
        "% A comment that should not be counted.\n\n"
        "The first paragraph.\n\n"
        "The second paragraph.\n\n\n"
        "The third paragraph.\n\n"
        "Dashes\u2013and even longer\u2014dashes."
    )
    assert cC == 163
    assert wC == 26
    assert pC == 4

    # Text Alignment
    cC, wC, pC = standardCounter("# Title\n\nLeft aligned<<\n\nLeft aligned <<\n\nRight indent<\n\nRight indent <\n\n")
    assert cC == 53
    assert wC == 9
    assert pC == 4

    cC, wC, pC = standardCounter("# Title\n\n>>Right aligned\n\n>> Right aligned\n\n>Left indent\n\n> Left indent\n\n")
    assert cC == 53
    assert wC == 9
    assert pC == 4

    cC, wC, pC = standardCounter(
        "# Title\n\n>>Centre aligned<<\n\n>> Centre aligned <<\n\n>Double indent<\n\n> Double indent <\n\n"
    )
    assert cC == 59
    assert wC == 9
    assert pC == 4

    # Formatting Codes, Upper Case (Old Implementation)
    cC, wC, pC = standardCounter(
        "Some text\n\n"
        "[NEWPAGE]\n\n"
        "more text\n\n"
        "[NEW PAGE]\n\n"
        "even more text\n\n"
        "[VSPACE]\n\n"
        "and some final text\n\n"
        "[VSPACE:4]\n\n"
        "THE END\n\n"
    )
    assert cC == 58
    assert wC == 13
    assert pC == 5

    # Formatting Codes, Lower Case (Current Implementation)
    cC, wC, pC = standardCounter(
        "Some text\n\n"
        "[newpage]\n\n"
        "more text\n\n"
        "[new page]\n\n"
        "even more text\n\n"
        "[vspace]\n\n"
        "and some final text\n\n"
        "[vspace:4]\n\n"
        "THE END\n\n"
    )
    assert cC == 58
    assert wC == 13
    assert pC == 5

    # Check ShortCodes
    cC, wC, pC = standardCounter(
        "Text with [b]bold[/b] text and padded [b] bold [/b] text.\n\n"
        "Text with [b][i] nested [/i] emphasis [/b] in it.\n\n"
    )
    assert cC == 78
    assert wC == 14
    assert pC == 2


@pytest.mark.core
def testTextCounting_bodyTextCounter():
    """Test the body text counter."""
    # Not Text
    assert bodyTextCounter(None) == (0, 0, 0)  # type: ignore

    # General Text
    wC, cC, sC = bodyTextCounter(
        "#! Title\n\n"
        "##! Prologue\n\n"
        "# Heading One\n"
        "## Heading Two\n"
        "### Heading Three\n"
        "#### Heading Four\n\n"
        "@tag: value\n\n"
        "% A comment that should not be counted.\n\n"
        "The first paragraph.\n\n"
        "The second paragraph.\n\n\n"
        "The third paragraph.\n\n"
        "Dashes\u2013and even longer\u2014dashes."
    )
    assert wC == 14
    assert cC == 91
    assert sC == 81
