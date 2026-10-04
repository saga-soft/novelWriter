"""
novelWriter - GUI Text Document Tests
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

import pytest

from novelwriter.constants import nwConst
from novelwriter.core.project import NWProject
from novelwriter.editor.highlighter import BLOCK_TITLE

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiTextDocument_LayoutBusy(qtbot, nwGUI, projPath, ipsumText, mockRnd):
    """Test that only a document over the size limit enters the busy
    state, and that it settles again once the layout catches up.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    qDoc = nwGUI.docEditor._qDocument

    # A small document never becomes busy
    qDoc.setPlainText("A short document")
    assert qDoc.characterCount() <= nwConst.BIG_DOC_LIMIT
    with qtbot.assertNotEmitted(qDoc.layoutSettled, wait=300):
        qDoc.markLayoutBusy()
    assert qDoc.isLayoutBusy() is False

    # A document over the limit becomes busy, then settles again
    unit = "\n\n".join(ipsumText)
    reps = nwConst.BIG_DOC_LIMIT // len(unit) + 2
    qDoc.setPlainText("\n\n".join([unit] * reps))
    assert qDoc.characterCount() > nwConst.BIG_DOC_LIMIT
    assert qDoc.isLayoutBusy() is False  # Not marked busy yet

    qDoc.markLayoutBusy()
    assert qDoc.isLayoutBusy() is True

    with qtbot.waitSignal(qDoc.layoutSettled, timeout=5000):
        pass

    assert qDoc.isLayoutBusy() is False


@pytest.mark.gui
def testGuiTextDocument_BigDocOperations(qtbot, monkeypatch, nwGUI, projPath, ipsumText, mockRnd):
    """Test that setTextContent, setLineHeight, and setBottomMargin
    all respect the layout busy state on a document over the size limit.
    """
    monkeypatch.setattr(nwConst, "BIG_DOC_LIMIT", 10)
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    qDoc = nwGUI.docEditor._qDocument

    qDoc.setTextContent(ipsumText[0], C.hSceneDoc)
    assert qDoc.isLayoutBusy() is True

    rootFrame = qDoc.rootFrame()
    assert rootFrame is not None
    before = rootFrame.frameFormat().bottomMargin()

    # The bottom margin is guarded while busy ...
    qDoc.setBottomMargin(before + 42)
    assert rootFrame.frameFormat().bottomMargin() == before

    with qtbot.waitSignal(qDoc.layoutSettled, timeout=5000):
        pass
    assert qDoc.isLayoutBusy() is False

    # ... but not once settled
    qDoc.setBottomMargin(before + 42)
    assert rootFrame.frameFormat().bottomMargin() != before

    # Changing the line height re-marks the layout busy
    qDoc.setLineHeight(1.5)
    assert qDoc.isLayoutBusy() is True

    with qtbot.waitSignal(qDoc.layoutSettled, timeout=5000):
        pass
    assert qDoc.isLayoutBusy() is False


@pytest.mark.gui
def testGuiTextDocument_IterBlockByType(qtbot, nwGUI, projPath, mockRnd):
    """Test that iterBlockByType stops at maxCount instead of
    continuing to scan the rest of the document.
    """
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    assert nwGUI.openDocument(C.hSceneDoc) is True
    qDoc = nwGUI.docEditor._qDocument

    qDoc.setPlainText("\n\n".join(f"### Heading {i}" for i in range(5)))

    # There are more matching blocks than the cap below
    allTitles = list(qDoc.iterBlockByType(BLOCK_TITLE, maxCount=1000))
    assert [b.text() for b in allTitles] == [f"### Heading {i}" for i in range(5)]

    # A smaller maxCount stops early instead of yielding the rest
    capped = list(qDoc.iterBlockByType(BLOCK_TITLE, maxCount=2))
    assert [b.text() for b in capped] == ["### Heading 0", "### Heading 1"]
