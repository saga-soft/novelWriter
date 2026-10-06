"""
novelWriter - QTextDocument to Text Converter Tests
===================================================

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

import pytest

from PyQt6.QtGui import QFont, QTextCharFormat, QTextCursor, QTextDocument

from novelwriter import CONFIG
from novelwriter.core.project import NWProject
from novelwriter.formats.fromqdoc import FromQTextDocument
from novelwriter.formats.tohtml import ToHtml
from novelwriter.formats.toqdoc import ToQTextDocument


@pytest.mark.core
def testFromQTextDocument_General():
    """Test a single document that touches most of the features
    supported by the converter: headings, both regular and beyond
    H4, clean-edge and nested emphasis, a soft line break, a
    mid-word format that falls back to a shortcode, superscript and
    subscript, and both right and centre alignment.
    """
    html = (
        "<h1>Chapter One</h1>"
        "<p>Some <b>bold</b>, <i>italic</i>, <s>strike</s>, <u>underline</u> and "
        "<b><i>bold italic</i></b> text.</p>"
        "<h5>A Minor Note</h5>"
        "<p>Line one<br>Line two.</p>"
        "<p>Mixed<b>bo</b>ld and water<sup>2</sup>O with H<sub>2</sub>O.</p>"
        '<p style="text-align:right">Signed, the Author.</p>'
        '<p style="text-align:center">The End</p>'
    )
    document = QTextDocument()
    document.setHtml(html)

    converter = FromQTextDocument(document)
    result = converter.convertText()

    assert result == (
        "# Chapter One\n"
        "\n"
        "Some **bold**, _italic_, ~~strike~~, [u]underline[/u] and **_bold italic_** text.\n"
        "\n"
        "**A Minor Note**\n"
        "\n"
        "Line one\nLine two.\n"
        "\n"
        "Mixed[b]bo[/b]ld and water[sup]2[/sup]O with H[sub]2[/sub]O.\n"
        "\n"
        ">> Signed, the Author.\n"
        "\n"
        ">> The End <<\n"
    )

    # With soft breaks collapsed to a space instead of kept as a line break
    converter.setPreserveSoftBreak(False)
    result = converter.convertText()
    assert "Line one Line two.\n" in result
    assert "Line one\nLine two.\n" not in result

    # An empty paragraph contributes no text, just the blank separator
    document = QTextDocument()
    document.setHtml("<p>First</p><p><br></p><p>Second</p>")
    result = FromQTextDocument(document).convertText()
    assert result == "First\n\n\nSecond\n"


@pytest.mark.core
def testFromQTextDocument_MergeSplitFragments():
    """Test that adjacent Qt fragments with identical Markdown-relevant
    formatting are merged before being wrapped. See issue #2978.
    """
    document = QTextDocument()
    cursor = QTextCursor(document)

    boldAnchor = QTextCharFormat()
    boldAnchor.setFontWeight(QFont.Weight.Bold)
    boldAnchor.setAnchor(True)
    boldAnchor.setAnchorNames(["motivation"])
    cursor.insertText("M", boldAnchor)

    bold = QTextCharFormat()
    bold.setFontWeight(QFont.Weight.Bold)
    cursor.insertText("otivation", bold)

    # Sanity check that the document really does hold two fragments
    # here, i.e. that this test exercises the merge and is not
    # trivially true because Qt already coalesced them.
    it = document.begin().begin()
    fragments = []
    while not it.atEnd():
        fragments.append(it.fragment().text())
        it += 1
    assert fragments == ["M", "otivation"]

    result = FromQTextDocument(document).convertText().strip()
    assert result == "**Motivation**"


@pytest.mark.core
def testFromQTextDocument_MarkdownVsShortcode(mockGUI):
    """Test the edge cases that decide whether a format is written
    as Markdown or as a novelWriter shortcode: Markdown is only used
    when the formatted run sits on two clean word edges. Also checks
    that the single asterisk bold setting only affects the Markdown
    form, not the shortcode fallback.
    """
    project = NWProject()

    def convert(html: str) -> str:
        """Convert an HTML fragment via FromQTextDocument."""
        document = QTextDocument()
        document.setHtml(html)
        return FromQTextDocument(document).convertText().strip()

    def revert(text: str) -> str:
        """Convert a novelWriter text fragment back to HTML via
        ToQTextDocument.
        """
        html = ToHtml(project)
        html._text = text
        html.tokenizeText()
        html.doConvert()
        return "\n".join(html._pages)

    # Clean word edges convert to Markdown
    text = "A **bold** word."
    assert convert("<p>A <b>bold</b> word.</p>") == text
    assert revert(text) == "<p>A <strong>bold</strong> word.</p>\n"

    text = "**Bold** start."
    assert convert("<p><b>Bold</b> start.</p>") == text
    assert revert(text) == "<p><strong>Bold</strong> start.</p>\n"

    text = "This is **bold**"
    assert convert("<p>This is <b>bold</b></p>") == text
    assert revert(text) == "<p>This is <strong>bold</strong></p>\n"

    text = "Wait **(bold)** now."
    assert convert("<p>Wait <b>(bold)</b> now.</p>") == text
    assert revert(text) == "<p>Wait <strong>(bold)</strong> now.</p>\n"

    text = "Some **bold** text."
    assert convert("<p>Some <b> bold </b> text.</p>") == text
    assert revert(text) == "<p>Some <strong>bold</strong> text.</p>\n"

    # Dirty word edges fall back to shortcodes
    text = "Mid[b]dle[/b]man."
    assert convert("<p>Mid<b>dle</b>man.</p>") == text
    assert revert(text) == "<p>Mid<strong>dle</strong>man.</p>\n"

    text = "Bold[b]ly[/b] stated."
    assert convert("<p>Bold<b>ly</b> stated.</p>") == text
    assert revert(text) == "<p>Bold<strong>ly</strong> stated.</p>\n"

    text = "Very [b]bold[/b]ly stated."
    assert convert("<p>Very <b>bold</b>ly stated.</p>") == text
    assert revert(text) == "<p>Very <strong>bold</strong>ly stated.</p>\n"

    # Formats with no Markdown equivalent always use shortcodes
    text = "Some [u]underlined[/u] word."
    assert convert("<p>Some <u>underlined</u> word.</p>") == text
    assert revert(text) == "<p>Some <span style='text-decoration: underline;'>underlined</span> word.</p>\n"

    text = "E=mc[sup]2[/sup] and H[sub]2[/sub]O."
    assert convert("<p>E=mc<sup>2</sup> and H<sub>2</sub>O.</p>") == text
    assert revert(text) == "<p>E=mc<sup>2</sup> and H<sub>2</sub>O.</p>\n"

    # Nested formats on a clean edge nest their Markdown tags. Italic
    # is always innermost: its "_" delimiter is a word character, so
    # "**"/"~~" placed next to it fails novelWriter's own parser and
    # is left as literal text, regardless of the source HTML's own
    # nesting order.
    assert convert("<p>Some <b><i><s>combo</s></i></b> text.</p>") == "Some **~~_combo_~~** text."
    assert convert("<p>Some <s><i><b>combo</b></i></s> text.</p>") == "Some **~~_combo_~~** text."

    # A formatted fragment with no visible text contributes nothing
    assert convert("<p>A<b> </b>B</p>") == "A B"

    # Single asterisk bold only changes the Markdown form
    CONFIG.singleStarBold = True

    text = "A *bold* word."
    assert convert("<p>A <b>bold</b> word.</p>") == text
    assert revert(text) == "<p>A <strong>bold</strong> word.</p>\n"

    text = "Mid[b]dle[/b]man."
    assert convert("<p>Mid<b>dle</b>man.</p>") == text
    assert revert(text) == "<p>Mid<strong>dle</strong>man.</p>\n"


@pytest.mark.core
def testFromQTextDocument_MarkdownNestingRoundTrip(mockGUI):
    """Test that every non-empty combination of bold, italic and
    strike survives a full round trip: HTML to FromQTextDocument to
    novelWriter text to the real tokenizer (ToQTextDocument) to the
    resulting character format.
    """
    project = NWProject()

    def styleRoundTrip(html: str) -> dict[str, bool]:
        """Convert an HTML fragment to novelWriter text, parse that text
        back through the real tokenizer, and return which of bold, italic
        and strike survived on the resulting fragment. This is the actual
        parser the generated Markdown has to survive, not just a regex
        sanity check.
        """
        document = QTextDocument()
        document.setHtml(html)
        text = FromQTextDocument(document).convertText()

        toDoc = ToQTextDocument(project)
        toDoc.initDocument()
        toDoc._text = text
        toDoc.tokenizeText()
        toDoc.doConvert()

        cFmt = toDoc.document.begin().begin().fragment().charFormat()
        return {
            "bold": cFmt.fontWeight() >= QFont.Weight.Bold,
            "italic": cFmt.fontItalic(),
            "strike": cFmt.fontStrikeOut(),
        }

    assert styleRoundTrip("<p><b>combo</b></p>") == {"bold": True, "italic": False, "strike": False}
    assert styleRoundTrip("<p><i>combo</i></p>") == {"bold": False, "italic": True, "strike": False}
    assert styleRoundTrip("<p><s>combo</s></p>") == {"bold": False, "italic": False, "strike": True}
    assert styleRoundTrip("<p><b><i>combo</i></b></p>") == {"bold": True, "italic": True, "strike": False}
    assert styleRoundTrip("<p><b><s>combo</s></b></p>") == {"bold": True, "italic": False, "strike": True}
    assert styleRoundTrip("<p><i><s>combo</s></i></p>") == {"bold": False, "italic": True, "strike": True}
    assert styleRoundTrip("<p><b><i><s>combo</s></i></b></p>") == {"bold": True, "italic": True, "strike": True}
    assert styleRoundTrip("<p><s><i><b>combo</b></i></s></p>") == {"bold": True, "italic": True, "strike": True}


@pytest.mark.core
def testFromQTextDocument_DocumentRoundTrip(mockGUI):
    """Test a round trip of novelWriter text through ToQTextDocument
    and back again through FromQTextDocument.
    """
    project = NWProject()
    toDoc = ToQTextDocument(project)
    toDoc.initDocument()

    text = (
        "# Heading One\n"
        "\n"
        "## Heading Two\n"
        "\n"
        "Some **bold** and _italic_ and ~~strike~~ text.\n"
        "\n"
        "Some [u]underline[/u] and [sup]super[/sup] and [sub]sub[/sub] text.\n"
        "\n"
        ">> Right aligned text.\n"
        "\n"
        ">> Centered text. <<\n"
    )

    toDoc._text = text
    toDoc.tokenizeText()
    toDoc.doConvert()

    result = FromQTextDocument(toDoc.document).convertText()

    assert result == text
