"""
novelWriter - Modified Widgets Tests
====================================

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

from unittest.mock import Mock

import pytest

from PyQt6.QtCore import QEvent, QPoint, QPointF, QSize, Qt
from PyQt6.QtGui import QCloseEvent, QFont, QKeyEvent, QMouseEvent, QStandardItem, QStandardItemModel, QWheelEvent
from PyQt6.QtWidgets import QFontDialog, QSplitter, QWidget
from pytestqt.qtbot import QtBot

from novelwriter import CONFIG
from novelwriter.extensions.modified import (
    NClickableLabel,
    NComboBox,
    NDialog,
    NDoubleSpinBox,
    NFlatIconButton,
    NFlatIconTextButton,
    NFontDialog,
    NHRadioGroup,
    NIconButton,
    NNonBlockingDialog,
    NRadioButton,
    NSpinBox,
    NSplitterHandle,
    NToolDialog,
    NTreeView,
)
from novelwriter.guimain import GuiMain
from novelwriter.types import (
    QtIconNormal,
    QtIconOff,
    QtIconOn,
    QtKeyEscape,
    QtModNone,
    QtMouseLeft,
    QtMouseMiddle,
    QtRejected,
)

from tests.helpers import SimpleDialog
from tests.mocked import MockGuiMain


class MockWheelEvent(QWheelEvent):
    """Mock wheel event that records being ignored."""

    def __init__(self):
        super().__init__(
            QPointF(0, 0),
            QPointF(0, 0),
            QPoint(0, 0),
            QPoint(0, 0),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.ScrollUpdate,
            False,
        )
        self.ignored = False

    def ignore(self):
        """Ignore the event and record it."""
        super().ignore()
        self.ignored = True


@pytest.mark.gui
def testNDialog_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the NDialog class."""
    widget = QWidget()
    dialog = NDialog(widget)
    assert dialog.parent() is widget

    dialog.softDelete()
    assert dialog.parent() is None

    with qtbot.waitSignal(dialog.rejected, timeout=1000):
        dialog.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, QtKeyEscape, QtModNone))
        assert dialog.result() == QtRejected


@pytest.mark.gui
def testNToolDialog_Main(qtbot: QtBot, nwGUI: GuiMain):
    """Test the NToolDialog class."""
    dialog = NToolDialog(nwGUI)
    qtbot.addWidget(dialog)
    dialog.activateDialog()
    dialog.close()

    # Escape closes the dialog without a closeEvent override
    dialog.activateDialog()
    qtbot.keyClick(dialog, QtKeyEscape)
    assert dialog.isHidden()

    # Other keys are passed on
    dialog.activateDialog()
    qtbot.keyClick(dialog, Qt.Key.Key_A)
    assert dialog.isVisible()
    dialog.close()

    # Escape closes the dialog via a closeEvent override
    closed = False

    def closeEvent(event: QCloseEvent) -> None:
        nonlocal closed
        closed = True
        event.accept()

    dialog = NToolDialog(nwGUI)
    qtbot.addWidget(dialog)
    dialog.closeEvent = closeEvent  # type: ignore
    dialog.activateDialog()
    qtbot.keyClick(dialog, QtKeyEscape)
    assert dialog.isHidden()
    assert closed is True


@pytest.mark.gui
def testNNonBlockingDialog_Main(qtbot: QtBot):
    """Test the NNonBlockingDialog class."""
    dialog = NNonBlockingDialog()
    qtbot.addWidget(dialog)
    dialog.activateDialog()
    dialog.close()


def testNFontDialog_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, nwGUI: GuiMain):
    """Test the NFontDialog class."""
    current = QFont()
    other = QFont()
    widget = QWidget()
    dialog = NFontDialog(current, widget)
    assert dialog.parent() is widget

    # Test native dialog
    mockNative = Mock()
    mockNative.return_value = (other, True)
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "osDarwin", False)
        mp.setattr(QFontDialog, "getFont", mockNative)
        font, result = NFontDialog.selectFont(current, widget, "Title", True)
        mockNative.assert_called_once_with(current, widget, "Title")
        assert font is other
        assert result is True

    # Test native dialog on macOS
    with monkeypatch.context() as mp:
        mp.setattr(CONFIG, "osDarwin", True)
        mp.setattr(QFontDialog, "exec", lambda *a: None)
        mp.setattr(QFontDialog, "currentFont", lambda *a: other)
        font, result = NFontDialog.selectFont(current, widget, "Title", True)
        assert font is other
        assert result is True

    # Test custom dialog
    with monkeypatch.context() as mp:
        mp.setattr(NFontDialog, "exec", lambda *a: None)
        mp.setattr(NFontDialog, "selectedFont", lambda *a: other)
        mp.setattr(NFontDialog, "result", lambda *a: 1)
        font, result = NFontDialog.selectFont(current, widget, "Title", False)
        assert font is other
        assert result is True


@pytest.mark.gui
def testNTreeView_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the NTreeView class."""
    model = QStandardItemModel(1, 1)
    model.insertRow(0, QStandardItem("Hello World"))

    widget = NTreeView()
    widget.setModel(model)
    dialog = SimpleDialog(widget)
    dialog.show()

    vPort = widget.viewport()
    item = model.item(0, 0)
    assert vPort is not None
    assert item is not None

    position = QPointF(widget.visualRect(model.createIndex(0, 0)).center())
    event = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseMiddle, QtMouseMiddle, QtModNone)
    with qtbot.waitSignal(widget.middleClicked):
        widget.mousePressEvent(event)

    # A non-middle click does not emit the signal
    leftEvent = QMouseEvent(
        QEvent.Type.MouseButtonPress, position, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, QtModNone
    )
    received = []
    widget.middleClicked.connect(lambda idx: received.append(idx))
    widget.mousePressEvent(leftEvent)
    assert received == []

    # A middle click on an invalid position does not emit the signal
    invalidPos = QPointF(-10, -10)
    invalidEvent = QMouseEvent(QEvent.Type.MouseButtonPress, invalidPos, QtMouseMiddle, QtMouseMiddle, QtModNone)
    widget.mousePressEvent(invalidEvent)
    assert received == []

    # qtbot.stop()


@pytest.mark.gui
def testNComboBox_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the NComboBox class."""
    widget = NComboBox()
    widget.addItem("Item 1", 1)
    widget.addItem("Item 2", 2)

    dialog = SimpleDialog(widget)
    dialog.show()

    with monkeypatch.context() as mp:
        mp.setattr(NComboBox, "hasFocus", lambda *a: True)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is False

    with monkeypatch.context() as mp:
        mp.setattr(NComboBox, "hasFocus", lambda *a: False)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is True

    # qtbot.stop()


@pytest.mark.gui
def testNSpinBox_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the NSpinBox class."""
    widget = NSpinBox()
    widget.setMinimum(0)
    widget.setMaximum(100)
    widget.setValue(42)

    dialog = SimpleDialog(widget)
    dialog.show()

    with monkeypatch.context() as mp:
        mp.setattr(NSpinBox, "hasFocus", lambda *a: True)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is False

    with monkeypatch.context() as mp:
        mp.setattr(NSpinBox, "hasFocus", lambda *a: False)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is True

    # qtbot.stop()


@pytest.mark.gui
def testNDoubleSpinBox_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the NDoubleSpinBox class."""
    widget = NDoubleSpinBox()
    widget.setMinimum(0.0)
    widget.setMaximum(100.0)
    widget.setValue(42.0)

    dialog = SimpleDialog(widget)
    dialog.show()

    with monkeypatch.context() as mp:
        mp.setattr(NDoubleSpinBox, "hasFocus", lambda *a: True)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is False

    with monkeypatch.context() as mp:
        mp.setattr(NDoubleSpinBox, "hasFocus", lambda *a: False)
        event = MockWheelEvent()
        widget.wheelEvent(event)
        assert event.ignored is True

    # qtbot.stop()


@pytest.mark.gui
def testNClickableLabel_Main(qtbot: QtBot):
    """Test the NClickableLabel class."""
    widget = NClickableLabel()
    dialog = SimpleDialog(widget)
    dialog.show()

    position = QPointF(widget.rect().center())
    event = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseLeft, QtMouseLeft, QtModNone)

    with qtbot.waitSignal(widget.mouseClicked):
        widget.mousePressEvent(event)

    # A non-left click does not emit the signal
    received = []
    widget.mouseClicked.connect(lambda: received.append(True))
    rightEvent = QMouseEvent(
        QEvent.Type.MouseButtonPress, position, Qt.MouseButton.RightButton, Qt.MouseButton.RightButton, QtModNone
    )
    widget.mousePressEvent(rightEvent)
    assert received == []

    # Tooltips are used as accessible names, without the shortcut
    widget.setToolTip("Reset Zoom", "Ctrl+0")
    assert widget.toolTip() == "Reset Zoom [Ctrl+0]"
    assert widget.accessibleName() == "Reset Zoom"
    widget.setToolTip("Zoom")
    assert widget.toolTip() == "Zoom"
    assert widget.accessibleName() == "Zoom"
    widget.setToolTip(None)
    assert widget.toolTip() == ""
    assert widget.accessibleName() == ""


@pytest.mark.gui
def testNFlatButtons_Main(qtbot: QtBot, mockGUIwithTheme: MockGuiMain):
    """Test the NFlatIconButton and NFlatIconTextButton classes."""
    dialog = SimpleDialog(None)

    size = QSize(16, 16)
    button1 = NFlatIconButton(dialog, size, "add:add")
    button2 = NFlatIconTextButton(dialog, size, "bullet:action", "Text")

    assert button1.iconSize() == size
    assert button2.iconSize() == size

    assert button1.icon().isNull() is False
    assert button2.icon().isNull() is False

    dialog.addWidget(button1)
    dialog.addWidget(button2)
    dialog.show()

    # Uncheckable buttons skip the toggle style
    button1.setCheckable(True)
    assert button1.isCheckable() is True
    button1.setCheckable(False)
    assert button1.isCheckable() is False

    # Tooltips are used as accessible names, without the shortcut
    button1.setToolTip("Project Tree View", "Ctrl+T")
    assert button1.toolTip() == "Project Tree View [Ctrl+T]"
    assert button1.accessibleName() == "Project Tree View"
    button1.setToolTip("Settings")
    assert button1.toolTip() == "Settings"
    assert button1.accessibleName() == "Settings"
    button1.setToolTip(None)
    assert button1.toolTip() == ""
    assert button1.accessibleName() == ""

    button3 = NIconButton(dialog, size, "add:add")
    button3.setToolTip("Add", "Ctrl+N")
    assert button3.toolTip() == "Add [Ctrl+N]"
    assert button3.accessibleName() == "Add"

    # A toggle icon makes the text button checkable, with an on and off icon
    assert button2.isCheckable() is False
    button4 = NFlatIconTextButton(dialog, size, "toggle-bullet:action", "Toggle")
    dialog.addWidget(button4)
    assert button4.isCheckable() is True
    iconOn = button4.icon().pixmap(size, QtIconNormal, QtIconOn).toImage()
    iconOff = button4.icon().pixmap(size, QtIconNormal, QtIconOff).toImage()
    assert iconOn.isNull() is False
    assert iconOff.isNull() is False
    assert iconOn != iconOff

    # Toggling and theme refresh keep the toggle icon, and paint both states
    button4.setChecked(True)
    assert button4.isChecked() is True
    button4.grab()
    button4.refreshTheme()
    assert button4.icon().isNull() is False
    button4.setChecked(False)
    assert button4.isChecked() is False
    button4.grab()


@pytest.mark.gui
def testNRadioButton_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, mockGUI: MockGuiMain):
    """Test the NRadioButton class."""
    button = NRadioButton("Text", None)
    dialog = SimpleDialog(button)
    dialog.show()

    # Paint unchecked and checked
    assert button.isChecked() is False
    assert button.grab().isNull() is False
    button.setChecked(True)
    assert button.grab().isNull() is False

    # Disabled
    button.setEnabled(False)
    assert button.grab().isNull() is False

    # No style
    with monkeypatch.context() as mp:
        mp.setattr(button, "style", lambda: None)
        assert button.grab().isNull() is False


@pytest.mark.gui
def testNHRadioGroup_Main(qtbot: QtBot, mockGUI: MockGuiMain):
    """Test the NHRadioGroup class."""
    dialog = SimpleDialog(None)
    group = NHRadioGroup(dialog, "Label", {0: "None", 1: "One", 2: "Two"})
    dialog.addWidget(group)
    dialog.show()

    # The buttons are labelled, and nothing is checked initially
    buttons = group._group.buttons()
    assert [b.text() for b in buttons] == ["None", "One", "Two"]
    assert [b.accessibleName() for b in buttons] == ["Label: None", "Label: One", "Label: Two"]
    assert group.checkedId() == -1

    # Set by ID
    group.setCheckedId(2)
    assert group.checkedId() == 2

    # An unknown ID is ignored
    group.setCheckedId(9)
    assert group.checkedId() == 2

    # Clicking a button changes the checked ID
    buttons[1].click()
    assert group.checkedId() == 1

    # An empty group has nothing to check
    empty = NHRadioGroup(dialog, "Empty", {})
    empty.setCheckedId(0)
    assert empty.checkedId() == -1


@pytest.mark.gui
def testNSplitterHandle_Main(qtbot: QtBot):
    """Test the NSplitterHandle class."""
    splitter = QSplitter(Qt.Orientation.Vertical)
    handle = NSplitterHandle(Qt.Orientation.Vertical, splitter)
    dialog = SimpleDialog(splitter)
    dialog.show()
    qtbot.addWidget(dialog)
    qtbot.wait(10)

    # Starts out resizable, with the vertical split cursor, and inactive
    assert handle._resizable is True
    assert handle.cursor().shape() == Qt.CursorShape.SplitVCursor
    assert handle._active is False

    # Paint while inactive draws nothing but must not fail
    handle.repaint()

    # Hovering activates the highlight, and leaving drops it again
    handle.event(QEvent(QEvent.Type.HoverEnter))
    assert handle._active is True
    handle.event(QEvent(QEvent.Type.HoverLeave))
    assert handle._active is False

    # A mouse press keeps it highlighted while dragging, and the highlight
    # is now actually painted
    position = QPointF(handle.rect().center())
    press = QMouseEvent(QEvent.Type.MouseButtonPress, position, QtMouseLeft, QtMouseLeft, QtModNone)
    handle.mousePressEvent(press)
    assert handle._active is True
    handle.repaint()

    # On release, the highlight follows whether the cursor is still over it
    release = QMouseEvent(QEvent.Type.MouseButtonRelease, position, QtMouseLeft, QtMouseLeft, QtModNone)
    handle.mouseReleaseEvent(release)
    assert handle._active is handle.underMouse()

    # Marking it non-resizable drops any active highlight, switches to a
    # plain arrow cursor, and suppresses further hover/press highlighting
    handle.setResizable(False)
    assert handle._resizable is False
    assert handle._active is False
    assert handle.cursor().shape() == Qt.CursorShape.ArrowCursor

    handle.event(QEvent(QEvent.Type.HoverEnter))
    assert handle._active is False
    handle.mousePressEvent(press)
    assert handle._active is False

    # Marking it resizable again restores the highlight cursor
    handle.setResizable(True)
    assert handle._resizable is True
    assert handle.cursor().shape() == Qt.CursorShape.SplitVCursor

    # The horizontal orientation uses the horizontal split cursor instead
    hSplitter = QSplitter(Qt.Orientation.Horizontal)
    hHandle = NSplitterHandle(Qt.Orientation.Horizontal, hSplitter)
    assert hHandle.cursor().shape() == Qt.CursorShape.SplitHCursor
    hHandle.setResizable(False)
    hHandle.setResizable(True)
    assert hHandle.cursor().shape() == Qt.CursorShape.SplitHCursor
