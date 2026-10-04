"""
novelWriter - GUI Story Outline Tests
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

from PyQt6.QtCore import QModelIndex, QPoint, QPointF, Qt
from PyQt6.QtGui import QDropEvent, QPainter, QPixmap, QWheelEvent
from PyQt6.QtWidgets import QApplication, QStyleOptionViewItem

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwKeyWords
from novelwriter.enum import nwView
from novelwriter.models.outlinemodel import OutlineModel
from novelwriter.story.outline import GuiOutlineViewSettings, GuiStoryOutlineView, _OutlineDelegate
from novelwriter.story.storysettings import OutlineColumn, OutlineViewSettings
from novelwriter.types import QtModCtrl, QtModNone, QtScrollAlwaysOff, QtScrollAsNeeded

ALL_SETTINGS = (
    "outline.syntaxColors",
    "outline.showParts",
    "outline.showScenes",
    "outline.showSections",
    "outline.showProgress",
)


@pytest.mark.gui
def testStoryOutline_Settings(qtbot, nwGUI, prjLipsum):
    """Test the outline view settings and build state."""
    assert nwGUI.openProject(prjLipsum)
    root = QModelIndex()

    # Scroll bars follow the config
    CONFIG.hideVScroll = True
    CONFIG.hideHScroll = True
    settings = OutlineViewSettings()
    view = GuiStoryOutlineView(nwGUI, settings)
    tree = view.outlineContent
    model = tree._model
    assert tree.verticalScrollBarPolicy() == QtScrollAlwaysOff
    assert tree.horizontalScrollBarPolicy() == QtScrollAlwaysOff

    CONFIG.hideVScroll = False
    CONFIG.hideHScroll = False
    tree.initViewport()
    assert tree.verticalScrollBarPolicy() == QtScrollAsNeeded
    assert tree.horizontalScrollBarPolicy() == QtScrollAsNeeded

    # Preferences are applied to the viewport
    CONFIG.hideVScroll = True
    view.initSettings()
    assert tree.verticalScrollBarPolicy() == QtScrollAlwaysOff
    CONFIG.hideVScroll = False
    view.initSettings()

    # Default settings
    view.refresh(None)
    assert model.rowCount(root) == 10
    assert model.columnCount(root) == 5
    assert not any(tree.isColumnHidden(c) for c in range(5))

    # Everything enabled
    for key in ALL_SETTINGS:
        settings.setValue(key, True)
    view.refresh(None, force=True)
    assert model.rowCount(root) == 12
    assert tree._delegate._tagCol == SHARED.theme.syntaxTheme.tag
    assert tree._delegate._keyCol == SHARED.theme.syntaxTheme.key
    assert tree._delegate._noteCol == SHARED.theme.syntaxTheme.note
    assert tree._delegate._modCol == SHARED.theme.syntaxTheme.mod
    assert model.node(model.index(11, 0)).progress == "Page 16 (81.9\u202f%)"  # type: ignore

    # Progress follows the page settings
    settings.setValue("outline.countPerPage", 100)
    settings.setValue("outline.clearDoublePage", False)
    view.refresh(None, force=True)
    assert model.node(model.index(11, 0)).progress == "Page 27 (81.9\u202f%)"  # type: ignore

    # Progress is relative to the project target if it is larger
    SHARED.project.data.setProjectTarget(6012, None, False)
    view.refresh(None, force=True)
    assert model.node(model.index(11, 0)).progress == "Page 27 (41.0\u202f%)"  # type: ignore
    settings.setValue("outline.useTargetCount", False)
    view.refresh(None, force=True)
    assert model.node(model.index(11, 0)).progress == "Page 27 (81.9\u202f%)"  # type: ignore

    # Row height follows the number of lines, within limits
    delegate = tree._delegate
    hLine = delegate._fm.height()
    assert delegate._rowHeight == delegate._lineHeight + 2 * hLine
    settings.setValue("outline.rowLines", 6)
    view.refresh(None, force=True)
    assert delegate._rowHeight == delegate._lineHeight + 5 * hLine
    delegate.setRowLines(1)
    assert delegate._rowHeight == delegate._lineHeight + 2 * hLine
    delegate.setRowLines(20)
    assert delegate._rowHeight == delegate._lineHeight + 9 * hLine

    # Everything disabled leaves chapters only
    for key in ALL_SETTINGS:
        settings.setValue(key, False)
    view.refresh(None, force=True)
    assert model.rowCount(root) == 3
    assert tree._delegate._tagCol == tree._delegate._textCol
    assert tree._delegate._keyCol == tree._delegate._textCol
    assert tree._delegate._noteCol == tree._delegate._textCol
    assert tree._delegate._modCol == tree._delegate._textCol
    assert model.node(model.index(0, 0)).progress == ""  # type: ignore

    # Columns without content are hidden
    settings.setColumns([*settings.columns, OutlineColumn("empty", "Empty", ())])
    view.refresh(None, force=True)
    assert model.columnCount(root) == 6
    assert [tree.isColumnHidden(c) for c in (4, 5)] == [False, True]

    # No rebuild without a change
    model.clear()
    view.refresh(None)
    assert model.rowCount(root) == 0

    # Clearing resets the build state
    tree.clear()
    view.refresh(None)
    assert model.rowCount(root) == 3

    # Chapters can be hidden
    settings.setValue("outline.showChapters", False)
    settings.setValue("outline.showScenes", True)
    view.refresh(None, force=True)
    assert model.rowCount(root) == 5
    assert {model.node(model.index(r, 0)).level for r in range(5)} == {3}  # type: ignore


@pytest.mark.gui
def testStoryOutline_ColumnState(qtbot, nwGUI, prjLipsum):
    """Test saving and loading the column order and widths."""
    assert nwGUI.openProject(prjLipsum)
    nwGUI._changeView(nwView.STORY)
    storyView = nwGUI.storyView
    storyView.addView.click()

    view = storyView.tabMain.currentWidget()
    assert isinstance(view, GuiStoryOutlineView)
    tree = view.outlineContent
    header = tree.header()
    assert header is not None

    # The default columns are characters, plot, world and comments
    chars, plot, world, comments = (f"column:{c.cid}" for c in view.settings.columns)  # type: ignore

    # Move and resize columns, and hide one
    header.moveSection(header.visualIndex(4), 1)
    header.resizeSection(OutlineModel.C_TITLE, 300)
    header.resizeSection(4, 250)
    header.resizeSection(2, 200)
    header.resizeSection(3, 120)
    tree.setColumnHidden(3, True)

    # The state is saved when the project is closed
    assert nwGUI.closeProject(isYes=True)
    assert nwGUI.openProject(prjLipsum)
    nwGUI._changeView(nwView.STORY)

    view = storyView.tabMain.currentWidget()
    assert isinstance(view, GuiStoryOutlineView)
    tree = view.outlineContent
    header = tree.header()
    assert header is not None
    # Plot is the last visible column, so it is stretched and not saved
    assert view.settings.getState("columns") == {
        "title": 300,
        comments: 250,
        chars: 160,
        plot: 160,
        world: 160,
    }
    assert [header.logicalIndex(i) for i in range(5)] == [0, 4, 1, 2, 3]
    assert header.sectionSize(OutlineModel.C_TITLE) == 300
    assert header.sectionSize(4) == 250

    # Changing the columns keeps the state by key, and adds new columns
    # at the end
    outline = view.settings
    assert isinstance(outline, OutlineViewSettings)
    header.resizeSection(1, 180)
    outline.setColumns([OutlineColumn("new", "New", ("note.new",)), *outline.columns])
    view.refresh(None, force=True)
    assert [header.logicalIndex(i) for i in range(6)] == [0, 5, 2, 3, 4, 1]
    assert header.sectionSize(5) == 250
    assert header.sectionSize(2) == 180
    assert header.sectionSize(1) == 160

    # Title stays first, unknown keys and invalid widths are skipped, and
    # missing columns are kept after the known ones
    settings = OutlineViewSettings()
    plot = f"column:{settings.columns[1].cid}"
    comments = f"column:{settings.columns[3].cid}"
    settings.setState("columns", {plot: "wide", "unknown": 100, "title": 30, comments: 90})
    tree = GuiStoryOutlineView(nwGUI, settings).outlineContent
    tree.refresh(None)
    header = tree.header()
    assert header is not None
    assert [header.logicalIndex(i) for i in range(3)] == [0, 2, 4]
    assert header.sectionSize(OutlineModel.C_TITLE) == 260
    assert header.sectionSize(2) == 160
    assert header.sectionSize(4) == 90

    # Nothing is saved before the state is loaded on the first build
    settings = OutlineViewSettings()
    tree = GuiStoryOutlineView(nwGUI, settings).outlineContent
    tree.saveColumnState()
    assert settings.getState("columns") is None

    # A hidden column without a previous width gets the default width
    tree.refresh(None)
    tree.setColumnHidden(1, True)
    tree.saveColumnState()
    assert settings.getState("columns")[f"column:{settings.columns[0].cid}"] == 160

    # The stretched last column keeps its previous width
    settings = OutlineViewSettings()
    comments = f"column:{settings.columns[3].cid}"
    settings.setState("columns", {comments: 300})
    tree = GuiStoryOutlineView(nwGUI, settings).outlineContent
    tree.refresh(None)
    tree.saveColumnState()
    assert settings.getState("columns")[comments] == 300


@pytest.mark.gui
def testStoryOutline_WheelScroll(qtbot, nwGUI, prjLipsum):
    """Test that the mouse wheel scrolls one item per step."""
    assert nwGUI.openProject(prjLipsum)

    settings = OutlineViewSettings()
    view = GuiStoryOutlineView(nwGUI, settings)
    view.resize(800, 200)
    view.show()
    view.refresh(None)

    tree = view.outlineContent
    vBar = tree.verticalScrollBar()
    assert vBar is not None
    qtbot.waitUntil(lambda: vBar.maximum() > 3)

    def scroll(steps: int, modifiers: Qt.KeyboardModifier = QtModNone) -> int:
        vBar.setValue(0)
        tree.wheelEvent(
            QWheelEvent(
                QPointF(10.0, 10.0),
                QPointF(10.0, 10.0),
                QPoint(0, 0),
                QPoint(0, -120 * steps),
                Qt.MouseButton.NoButton,
                modifiers,
                Qt.ScrollPhase.NoScrollPhase,
                False,
            )
        )
        return vBar.value()

    # One item per step, regardless of desktop setting
    lines = QApplication.wheelScrollLines()
    QApplication.setWheelScrollLines(3)
    assert scroll(1) == 1
    assert scroll(2) == 2
    QApplication.setWheelScrollLines(1)
    assert scroll(1) == 1

    # Control scrolls a page, as before
    QApplication.setWheelScrollLines(3)
    assert scroll(1, QtModCtrl) == vBar.pageStep()
    QApplication.setWheelScrollLines(lines)


@pytest.mark.gui
def testStoryOutline_Paint(qtbot, monkeypatch, nwGUI, prjLipsum):
    """Test painting the outline rows."""
    assert nwGUI.openProject(prjLipsum)

    settings = OutlineViewSettings()
    for key in ALL_SETTINGS:
        settings.setValue(key, True)
    more = ("@entity", "@custom", "@mention", "synopsis")
    columns = [c for c in settings.columns if c.keys != ("synopsis",)]
    settings.setColumns([*columns, OutlineColumn("more", "More", more)])

    view = GuiStoryOutlineView(nwGUI, settings)
    view.resize(1600, 800)
    view.refresh(None)
    view.updateTheme()

    tree = view.outlineContent
    model = tree._model
    delegate = tree._delegate
    labels = model._labels.sKeys

    # Fill in all reference types, with some left empty
    for i, node in enumerate(model._nodes):
        node._lists = (
            {
                nwKeyWords.POV_KEY: ["Jane"],
                nwKeyWords.FOCUS_KEY: ["John"],
                nwKeyWords.CHAR_KEY: ["Jane", "John", "Jack", "Jill", "James", "Julia", "Joseph", "Joanna"],
                nwKeyWords.PLOT_KEY: ["Main"],
                nwKeyWords.TIME_KEY: ["Morning", "Afternoon", "Evening", "Night"],
                nwKeyWords.WORLD_KEY: ["Europe"],
                nwKeyWords.ENTITY_KEY: ["Company"],
                nwKeyWords.CUSTOM_KEY: ["Custom"],
                nwKeyWords.MENTION_KEY: ["Jack"],
            }
            if i % 2
            else {nwKeyWords.FOCUS_KEY: ["John"]}
        )
        refs = {k: ", ".join(v) for k, v in node._lists.items()}
        node._entries = [[(k, labels[k], refs[k]) for k in keys if k in refs] for keys in node._columns]
        node._entries[-1].append(("synopsis", "Synopsis", "Text"))
        if i % 2:
            node._progress = ""

    # Paint all rows with one selected
    tree.setCurrentIndex(model.index(3, 0))
    assert not view.grab().isNull()

    # Highlighted references
    tree.setHighlight({"jane", "jack", "main", "night", "company", "custom"})
    assert delegate._highlight == {"jane", "jack", "main", "night", "company", "custom"}
    assert not view.grab().isNull()

    # Highlights are placed after the label offset
    node = model._nodes[1]
    formats = delegate._highlightFormats(node, nwKeyWords.CHAR_KEY, 0)
    assert [(f.start, f.length) for f in formats] == [(0, 4), (12, 4)]
    formats = delegate._highlightFormats(node, nwKeyWords.CHAR_KEY, 6)
    assert [(f.start, f.length) for f in formats] == [(6, 4), (18, 4)]

    # Entries are stacked, leaving a line for each following entry, and
    # the text is limited to whole lines within the height
    calls = []
    drawLayout = _OutlineDelegate._drawLayout

    def recordLayout(self, painter, x, y, w, h, text, formats):
        used = drawLayout(self, painter, x, y, w, h, text, formats)
        calls.append((y, h, text, used, painter.pen().color(), formats[0].format))
        return used

    hLine = delegate._fm.height()
    pixmap = QPixmap(200, 200)
    painter = QPainter(pixmap)
    entries = [
        ("@location", "Locations", ", ".join(f"World{i}" for i in range(30))),
        ("note.purpose", "Note (Purpose)", "Text"),
    ]
    with monkeypatch.context() as mp:
        mp.setattr(_OutlineDelegate, "_drawLayout", recordLayout)
        delegate._paintEntries(painter, 0, 0, 150, 3 * hLine, node, entries)
        world, note = calls
        assert world[:2] == (0, 2 * hLine)
        assert world[2].startswith("Locations: World0, World1")
        assert 2 * hLine - 2 <= world[3] <= 2 * hLine + 2
        assert world[4] == delegate._tagCol
        assert world[5] == delegate._boldFormat
        assert note[:3] == (world[3], 3 * hLine - world[3], "Note (Purpose): Text")
        assert note[4] == delegate._noteCol
        assert note[5] == delegate._modFormat

    painter.end()

    # Partition rows are a single line
    option = QStyleOptionViewItem()
    part = model.index(0, 0)
    chapter = model.index(1, 0)
    assert model.node(part).level == 1  # type: ignore
    assert delegate.sizeHint(option, part).height() < delegate.sizeHint(option, chapter).height()

    # Indices from other models fall back to default painting
    pixmap = QPixmap(100, 100)
    painter = QPainter(pixmap)
    delegate.paint(painter, option, QModelIndex())
    painter.end()


@pytest.mark.gui
def testStoryOutline_ColumnsPage(qtbot, nwGUI, prjLipsum):
    """Test the outline columns settings page."""
    assert nwGUI.openProject(prjLipsum)
    index = SHARED.project.index
    heading = index.getItemHeading("fb609cd8319dc", "T0001")
    assert heading is not None
    heading.setComment("story", "Goal", "Text")
    heading.setComment("note", "Consistency", "Text")
    heading.setComment("note", "consistency", "Text")
    for key in "ABC":
        heading.setComment("note", key, "Text")

    refs = list(nwKeyWords.CAN_LOOKUP)
    notes = ["story.goal", "note.a", "note.b", "note.c", "note.consistency", "note.purpose"]

    settings = OutlineViewSettings()
    # The columns are listed in the order of the outline header, with
    # columns not in the header last
    settings.setColumns([OutlineColumn("a", "A", ()), OutlineColumn("b", "B", ()), OutlineColumn("c", "C", ())])
    settings.setState("columns", {"title": 100, "column:c": 100, "column:a": 100})
    dialog = GuiOutlineViewSettings(nwGUI, settings)
    assert [c.cid for c in dialog.columnsPage.columns()] == ["c", "a", "b"]
    dialog.discardAndClose()

    settings = OutlineViewSettings()
    settings.setColumns([OutlineColumn("a", "Comments", ("synopsis",)), OutlineColumn("b", "Other", ("note.gone",))])
    dialog = GuiOutlineViewSettings(nwGUI, settings)
    qtbot.addWidget(dialog)
    page = dialog.columnsPage
    tree = page.columnTree
    combo = page.entryValue

    def options() -> list[str]:
        return [combo.itemData(i) for i in range(combo.count())]

    def keys(n: int) -> list[str]:
        section = tree.topLevelItem(n)
        assert section is not None
        return [section.child(i).data(0, page.D_KEY) for i in range(section.childCount())]  # type: ignore

    # The columns are loaded, and used keys are not in the options
    assert tree.topLevelItemCount() == 2
    assert keys(0) == ["synopsis"]
    assert keys(1) == ["note.gone"]
    assert tree.topLevelItem(1).child(0).text(0) == "Note: gone"  # type: ignore
    assert tree.topLevelItem(1).child(0).foreground(0).color() == SHARED.theme.helpText  # type: ignore
    assert options() == [*refs, *notes]
    assert combo.itemText(0) == "Point of View"
    assert combo.itemText(11) == "Story: Goal"
    assert combo.itemText(15) == "Note: Consistency"
    assert not combo.itemIcon(0).isNull()
    assert not combo.itemIcon(11).isNull()

    # Entries are added to the selected column, but only if the text matches
    tree.setCurrentItem(tree.topLevelItem(0))
    combo.setCurrentIndex(15)
    page.addEntry.click()
    assert keys(0) == ["synopsis", "note.consistency"]
    assert "note.consistency" not in options()
    combo.setEditText("Nope")
    page.addEntry.click()
    assert keys(0) == ["synopsis", "note.consistency"]

    # A column is full at five entries
    for _ in range(4):
        combo.setCurrentIndex(0)
        page.addEntry.click()
    assert keys(0) == ["synopsis", "note.consistency", "@pov", "@focus", "@char"]
    assert tree.topLevelItem(0).child(2).foreground(0).color() != SHARED.theme.helpText  # type: ignore
    assert options()[0] == "@plot"

    # Without a selection, entries are added to the last column
    tree.setCurrentItem(None)  # type: ignore
    page.addEntry.click()
    assert keys(1) == ["note.gone", "@plot"]
    assert "@plot" not in options()

    # Removing an entry only applies to entry items
    tree.setCurrentItem(tree.topLevelItem(1))
    page.delEntry.click()
    assert keys(1) == ["note.gone", "@plot"]
    tree.setCurrentItem(tree.topLevelItem(1).child(1))  # type: ignore
    page.delEntry.click()
    assert keys(1) == ["note.gone"]
    assert options()[0] == "@plot"

    # Columns are added, renamed and removed, with empty names replaced
    page.addColumn.click()
    assert tree.topLevelItemCount() == 3
    assert tree.currentItem() is tree.topLevelItem(2)
    page.editColumn.click()
    tree.topLevelItem(2).setText(0, "  ")  # type: ignore
    assert page.columns()[2].name == "Column"
    tree.setCurrentItem(tree.topLevelItem(0).child(1))  # type: ignore
    page.delColumn.click()
    assert tree.topLevelItemCount() == 2
    assert options() == [*refs, "synopsis", *notes]

    # Without a selection, the column controls do nothing
    tree.setCurrentItem(None)  # type: ignore
    page.editColumn.click()
    page.delColumn.click()
    assert tree.topLevelItemCount() == 2

    # Adding an entry without any columns creates one
    page.setColumns([])
    combo.setCurrentIndex(0)
    page.addEntry.click()
    assert page.columns()[0].name == "Column"
    assert page.columns()[0].keys == ("@pov",)

    # Drops are only accepted into columns with room
    page.setColumns([
        OutlineColumn("a", "A", ("note.a",)),
        OutlineColumn("b", "B", ("synopsis", "story.goal", "note.b", "note.c", "note.consistency")),
    ])
    source = tree.topLevelItem(0).child(0)  # type: ignore
    full = tree.topLevelItem(1)
    assert source is not None
    assert full is not None
    tree.setCurrentItem(source)

    def drop(target: QPoint) -> QDropEvent:
        event = QDropEvent(
            QPointF(target),
            Qt.DropAction.MoveAction,
            tree.mimeData([source]),
            Qt.MouseButton.LeftButton,
            QtModNone,
        )
        event.accept()
        tree.dropEvent(event)
        return event

    assert drop(tree.visualItemRect(full).center()).isAccepted() is False
    drop(tree.visualItemRect(tree.topLevelItem(0)).center())  # type: ignore
    drop(QPoint(-10, -10))
    assert [c.keys for c in page.columns()] == [
        ("note.a",),
        ("synopsis", "story.goal", "note.b", "note.c", "note.consistency"),
    ]

    # The page is saved to the settings
    dialog._applyChanges()
    assert [c.keys for c in settings.columns] == [("synopsis",), ("note.gone",)]
    assert dialog._settings.columns == page.columns()  # type: ignore
    dialog.discardAndClose()
