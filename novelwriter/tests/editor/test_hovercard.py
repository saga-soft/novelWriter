"""
novelWriter - Hover Card Tests
==============================

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

from PyQt6.QtCore import QEvent, QPoint, QPointF
from PyQt6.QtGui import QEnterEvent
from PyQt6.QtWidgets import QWidget

from novelwriter import SHARED
from novelwriter.core.indexdata import TT_NONE
from novelwriter.core.project import NWProject
from novelwriter.editor.hovercard import GuiDocHoverCard
from novelwriter.enum import nwDocMode

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiDocHoverCard_Widget(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """Test the hover card's widget mechanics: theming, caching, and
    the show/hide/mouse-enter grace period. A real project is needed
    since setTag() looks up SHARED.project.index even for tags that
    turn out not to exist.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    parent = QWidget()
    qtbot.addWidget(parent)
    card = GuiDocHoverCard(parent)
    qtbot.addWidget(card)

    assert card.isHidden() is True

    # The cache has the theme's colours baked into its HTML, so it
    # must be cleared whenever the theme is refreshed
    card._cache["stale"] = "<p>Stale</p>"
    card._tag = "stale"

    # The view/edit button icons must also be refreshed, or they stay
    # stuck on the colours of the theme active when the card was built
    viewCalls = []
    editCalls = []
    monkeypatch.setattr(card._viewBtn, "refreshTheme", lambda: viewCalls.append(1))
    monkeypatch.setattr(card._editBtn, "refreshTheme", lambda: editCalls.append(1))

    card.updateTheme()
    assert card._cache == {}
    assert card._tag == ""
    assert viewCalls == [1]
    assert editCalls == [1]

    # An empty tag never resolves to any content
    assert card.setTag("") is False
    assert card._label.text() == ""

    # A cache miss for an unresolvable tag builds and stores empty text
    assert card.setTag("ghost") is False
    assert card._cache == {"ghost": ""}

    # A pre-populated cache entry is used as-is, without being rebuilt,
    # even though "cached" does not exist in the project index
    card._cache["cached"] = "<p>Cached</p>"
    assert card.setTag("cached") is True
    assert card._label.text() == "<p>Cached</p>"

    # Setting the same tag again is a no-op that leaves the label alone
    card._cache["cached"] = "<p>Changed</p>"
    assert card.setTag("cached") is True
    assert card._label.text() == "<p>Cached</p>"

    card.clearCache()
    assert card._cache == {}
    assert card._tag == ""

    # Tags are matched case-insensitively, mirroring the index, so a
    # differently-cased hover reuses the same lower-cased cache entry
    card._cache["mixed"] = "<p>Mixed</p>"
    assert card.setTag("Mixed") is True
    assert card._tag == "mixed"
    assert card._label.text() == "<p>Mixed</p>"

    # pruneCache() drops cached entries by their (already lower-cased)
    # tag key, and resets the current tag so the next setTag() rebuilds
    # it rather than treating it as a no-op
    card._cache = {"jane": "<p>Jane</p>", "solo": "<p>Solo</p>"}
    card._tag = "jane"
    card.pruneCache(["jane"])
    assert card._cache == {"solo": "<p>Solo</p>"}
    assert card._tag == ""

    # A prune that removes nothing still resets the current tag
    card._tag = "solo"
    card.pruneCache([])
    assert card._cache == {"solo": "<p>Solo</p>"}
    assert card._tag == ""

    # Showing the card unhides it, and builds a non-empty clip mask
    # from the same rounded path used to hand-paint its background and
    # border, which also exercises paintEvent()
    with qtbot.waitExposed(card):
        card.showAt(QPoint(50, 50), 400, 800)
    assert not card.mask().isEmpty()
    card.repaint()

    # A scheduled hide is cancelled if the mouse enters the card first,
    # mirroring the grace period used when leaving the editor/viewer
    card.scheduleHide()
    assert card._hideTimer.isActive() is True
    card.enterEvent(QEnterEvent(QPointF(), QPointF(), QPointF()))
    assert card._hideTimer.isActive() is False

    # Leaving the card outright hides it immediately
    card.leaveEvent(QEvent(QEvent.Type.Leave))
    assert card.isVisible() is False

    # showAt() itself also cancels any pending scheduled hide
    card.showAt(QPoint(60, 60), 400, 800)
    card.scheduleHide()
    assert card._hideTimer.isActive() is True
    card.showAt(QPoint(70, 70), 400, 800)
    assert card._hideTimer.isActive() is False


@pytest.mark.gui
def testGuiDocHoverCard_TagContent(qtbot, nwGUI, projPath, mockRnd):
    """Test that setTag() assembles the correct HTML for a tag's name,
    display alias, title and synopsis, and that the View/Edit buttons
    resolve the current tag and re-emit openDocumentRequest.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)

    cHandle = SHARED.project.newFile("People", C.hCharRoot)
    assert cHandle is not None
    assert nwGUI.openDocument(cHandle) is True
    nwGUI.docEditor.replaceText(
        "# Jane Doe\n\n@tag: Jane | Janey\n\n%Synopsis: A short synopsis.\n\n"
        "# Solo Person\n\n@tag: Solo\n\n"
        "# Multi Person\n\n@tag: Multi\n\n%Synopsis: First part.\n\n%Synopsis: Second part.\n\n"
    )
    nwGUI.saveDocument()

    parent = QWidget()
    qtbot.addWidget(parent)
    card = GuiDocHoverCard(parent)
    qtbot.addWidget(card)

    # Name and display differ, and the tag has both a title and a
    # synopsis: one paragraph for each of the three parts
    assert card.setTag("Jane") is True
    text = card._label.text()
    assert text.count("<p>") == 3
    assert "Jane" in text
    assert "Janey" in text
    assert "Jane Doe" in text
    assert "A short synopsis." in text

    # Name and display are the same, and there is a title but no
    # synopsis: only two paragraphs
    assert card.setTag("Solo") is True
    text = card._label.text()
    assert text.count("<p>") == 2
    assert "Solo Person" in text
    assert "A short synopsis." not in text

    # A synopsis with two paragraphs, separated by a blank line, is
    # rendered as two separate <p> blocks rather than one run-on block
    assert card.setTag("Multi") is True
    text = card._label.text()
    assert text.count("<p>") == 4
    assert "First part." in text
    assert "Second part." in text

    # An unknown tag never resolves to any content
    assert card.setTag("DoesNotExist") is False
    assert card._label.text() == ""

    # The index treats tags as case-insensitive, so a differently-cased
    # hover still resolves the same tag and its cached HTML
    card.clearCache()
    assert card.setTag("JANE") is True
    text = card._label.text()
    assert "Jane Doe" in text
    assert list(card._cache) == ["jane"]

    # The View/Edit buttons resolve the current tag via the index and
    # re-emit openDocumentRequest with the matching mode
    card.setTag("Jane")
    tHandle, sTitle = SHARED.project.index.getTagSource("Jane")
    assert tHandle is not None

    with qtbot.waitSignal(card.openDocumentRequest, timeout=1000) as blocker:
        card._onViewClicked()
    assert blocker.args == [tHandle, nwDocMode.VIEW, sTitle, True]

    with qtbot.waitSignal(card.openDocumentRequest, timeout=1000) as blocker:
        card._onEditClicked()
    assert blocker.args == [tHandle, nwDocMode.EDIT, sTitle, True]

    # An unresolved tag emits nothing when the buttons are clicked
    card.setTag("DoesNotExist")
    with qtbot.assertNotEmitted(card.openDocumentRequest, wait=200):
        card._onViewClicked()
        card._onEditClicked()


@pytest.mark.gui
def testGuiDocHoverCard_NoHeadingTitle(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """A tag defined under the dummy T0000 heading must not show a
    title. The real indexer never actually produces this combination
    for a tag definition, since an '@' line before any heading is not
    indexed at all, so the heading key is substituted directly on an
    otherwise normally-indexed tag to exercise the guard.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    cHandle = SHARED.project.newFile("People", C.hCharRoot)
    assert cHandle is not None
    assert nwGUI.openDocument(cHandle) is True
    nwGUI.docEditor.replaceText("# Jane Doe\n\n@tag: Jane\n\n")
    nwGUI.saveDocument()

    _, _, _, hItem = SHARED.project.index.getSingleTag("Jane")
    assert hItem is not None
    assert hItem.title == "Jane Doe"
    monkeypatch.setattr(hItem, "_key", TT_NONE)

    parent = QWidget()
    qtbot.addWidget(parent)
    card = GuiDocHoverCard(parent)
    qtbot.addWidget(card)

    assert card.setTag("Jane") is True
    text = card._label.text()
    assert text.count("<p>") == 1
    assert "Jane Doe" not in text


@pytest.mark.gui
def testGuiDocHoverCard_NoHeadingItem(monkeypatch, qtbot, nwGUI, projPath, mockRnd):
    """A tag whose heading cannot be resolved at all, despite having a
    valid name and item, must fall back to just the name paragraph.
    getSingleTag() cannot actually return this shape for a tag with a
    name, since a resolved heading is one of its own preconditions, so
    it is patched directly to exercise the guard.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    cHandle = SHARED.project.newFile("People", C.hCharRoot)
    assert cHandle is not None
    assert nwGUI.openDocument(cHandle) is True
    nwGUI.docEditor.replaceText("# Jane Doe\n\n@tag: Jane\n\n")
    nwGUI.saveDocument()

    name, tClass, iItem, hItem = SHARED.project.index.getSingleTag("Jane")
    assert hItem is not None
    indexClass = type(SHARED.project.index)
    monkeypatch.setattr(indexClass, "getSingleTag", lambda *a: (name, tClass, iItem, None))

    parent = QWidget()
    qtbot.addWidget(parent)
    card = GuiDocHoverCard(parent)
    qtbot.addWidget(card)

    assert card.setTag("Jane") is True
    text = card._label.text()
    assert text.count("<p>") == 1
    assert "Jane Doe" not in text
