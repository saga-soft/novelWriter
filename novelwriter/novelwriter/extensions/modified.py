"""
novelWriter - Custom Widget: Modified Widgets
=============================================

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

import logging

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, QModelIndex, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QKeySequence, QPainter, QPaintEvent, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFontDialog,
    QLabel,
    QPushButton,
    QSpinBox,
    QSplitter,
    QSplitterHandle,
    QStyleOptionToolButton,
    QToolButton,
    QTreeView,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.enum import nwStandardButton
from novelwriter.types import (
    QtAlignCenter,
    QtAlignLeftMiddle,
    QtIconDisabled,
    QtIconNormal,
    QtIconOff,
    QtIconOn,
    QtMouseLeft,
    QtMouseMiddle,
    QtMouseOver,
    QtRoleAccept,
    QtRoleReject,
    QtToolButtonTextIcon,
)

if TYPE_CHECKING:
    from enum import Enum

    from PyQt6.QtGui import QFont, QKeyEvent, QMouseEvent, QWheelEvent

    from novelwriter.guimain import GuiMain

logger = logging.getLogger(__name__)


class NDialog(QDialog):
    """Custom: Modified QDialog."""

    def softDelete(self) -> None:
        """Since calling deleteLater is sometimes not safe from Python,
        as the C++ object can be deleted before the Python process is
        done with the object, we instead set the dialog's parent to None
        so that it gets garbage collected when it runs out of scope.
        """
        self.setParent(None)

    @pyqtSlot()
    def closeDialog(self) -> None:
        """Close the dialog."""
        self.setResult(0)
        self.close()


class NToolDialog(NDialog):
    """Custom: Modified QDialog for Tools."""

    def __init__(self, parent: GuiMain) -> None:
        super().__init__(parent=parent)
        self.setModal(False)
        if CONFIG.osDarwin:  # pragma: no cover
            self.setWindowFlag(Qt.WindowType.Tool)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Close on escape via closeEvent, which QDialog.reject bypasses."""
        if event.matches(QKeySequence.StandardKey.Cancel):
            self.close()
        else:
            super().keyPressEvent(event)

    def activateDialog(self) -> None:
        """Activate dialog on various operating systems."""
        self.show()
        if CONFIG.osWindows:  # pragma: no cover
            self.activateWindow()
        self.raise_()
        QApplication.processEvents()


class NNonBlockingDialog(NDialog):
    """Custom: Modified Non-Blocking QDialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setModal(True)

    def activateDialog(self) -> None:
        """Activate dialog on various operating systems."""
        self.show()
        if CONFIG.osWindows:  # pragma: no cover
            self.activateWindow()
        self.raise_()
        QApplication.processEvents()


class NFontDialog(QFontDialog):
    """Custom: Modified Font Dialog.

    An overload of the Qt font dialog that remembers its previous size.
    """

    def __init__(self, initial: QFont, parent: QWidget) -> None:
        super().__init__(initial, parent)

        # Look for the button box and replace the buttons
        if dlgBox := self.findChild(QDialogButtonBox):  # pragma: no branch
            self.btnOk = SHARED.theme.getStandardButton(nwStandardButton.OK, self)
            self.btnOk.clicked.connect(self.accept)

            self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
            self.btnCancel.clicked.connect(self.reject)

            dlgBox.clear()
            dlgBox.addButton(self.btnOk, QtRoleAccept)
            dlgBox.addButton(self.btnCancel, QtRoleReject)

        logger.debug("Ready: NFontDialog")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: NFontDialog")

    @staticmethod
    def selectFont(font: QFont, parent: QWidget, title: str, native: bool) -> tuple[QFont, bool]:
        """Open the dialog and select a font."""
        if native:
            if CONFIG.osDarwin:
                # The macOS font panel has no accept button, so closing it
                # must count as accepting the current font.
                # Also we can't use `QFontDialog.getFont(..)` because it
                # always returns the previously selected font without an accept action
                dialog = QFontDialog(font, parent)
                dialog.setWindowTitle(title)
                dialog.exec()
                return dialog.currentFont(), True

            # If we're using the native dialog, let Qt handle it
            font, result = QFontDialog.getFont(font, parent, title)
            return font, bool(result)

        # Execute the custom dialog
        dialog = NFontDialog(font, parent)
        dialog.setOption(QFontDialog.FontDialogOption.DontUseNativeDialog, True)
        dialog.setWindowTitle(title)
        dialog.resize(*CONFIG.fontWinSize)

        dialog.exec()
        CONFIG.setFontWinSize(dialog.geometry())

        font = dialog.selectedFont()
        status = dialog.result() == 1
        dialog.setParent(None)

        return font, status


class NTreeView(QTreeView):
    """Custom: Modified QTreeView.

    The main purpose is to provide the middleClicked signal that matches
    clicked and doubleCLicked.
    """

    middleClicked = pyqtSignal(QModelIndex)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Emit a signal on mouse middle click."""
        if event and event.button() == QtMouseMiddle and (index := self.indexAt(event.pos())).isValid():
            self.middleClicked.emit(index)
        return super().mousePressEvent(event)


class NComboBox(QComboBox):
    """Custom: Modified QComboBox.

    The main purpose is to provide a combo box that doesn't scroll when
    the mousewheel is active on it while scrolling through a scrollable
    window of many widgets.
    """

    def __init__(self, parent: QWidget | None = None, maxItems: int = 15) -> None:
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMaxVisibleItems(maxItems)
        self.updateStyle()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Only capture the mouse wheel if the widget has focus."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def setCurrentData(self, data: str | int | Enum, default: str | int | Enum) -> None:
        """Set the current index from data, with a fallback."""
        idx = self.findData(data)
        self.setCurrentIndex(self.findData(default) if idx < 0 else idx)

    def updateStyle(self) -> None:
        """Update the style sheet."""
        # The style sheet disables Fusion style pop-up mode on some
        # platforms and allows for scrolling of long lists of items
        self.setStyleSheet("QComboBox {combobox-popup: 0;}")

    def setMinCharsWidth(self, count: int) -> None:
        """Set a fixed with for a certain amount of characters."""
        self.setMinimumWidth(count * SHARED.theme.textNWidth + 25)


class NSpinBox(QSpinBox):
    """Custom: Modified QSpinBox.

    The main purpose is to provide a spin box that doesn't scroll when
    the mousewheel is active on it while scrolling through a scrollable
    window of many widgets.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        minVal: int = 0,
        maxVal: int = 15,
        step: int = 1,
    ) -> None:
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimum(minVal)
        self.setMaximum(maxVal)
        self.setSingleStep(step)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Only capture the mouse wheel if the widget has focus."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def setFixedNumbersWidth(self, count: int) -> None:
        """Set a fixed with for a certain amount of numbers."""
        self.setFixedWidth(count * SHARED.theme.textNWidth + 24)


class NDoubleSpinBox(QDoubleSpinBox):
    """Custom: Modified QDoubleSpinBox.

    The main purpose is to provide a float spin box that doesn't scroll
    when the mousewheel is active on it while scrolling through a
    scrollable window of many widgets.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        minVal: float = 0.0,
        maxVal: float = 15.0,
        step: float = 0.1,
        prec: int = 2,
    ) -> None:
        super().__init__(parent=parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimum(minVal)
        self.setMaximum(maxVal)
        self.setSingleStep(step)
        self.setDecimals(prec)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Only capture the mouse wheel if the widget has focus."""
        if self.hasFocus():
            super().wheelEvent(event)
        else:
            event.ignore()

    def setFixedNumbersWidth(self, count: int) -> None:
        """Set a fixed with for a certain amount of numbers."""
        self.setFixedWidth(count * SHARED.theme.textNWidth + 24)


class NPushButton(QPushButton):
    """Custom: Modified QPushButton.

    A quicker way to create a push button using the app theme.
    """

    def __init__(
        self,
        parent: QWidget,
        text: str,
        iconSize: QSize,
        icon: str | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self._icon = icon
        self.setText(text)
        self.setIconSize(iconSize)
        self.refreshTheme()

    def setText(self, text: str) -> None:
        """Overload the text setter to add padding."""
        return super().setText(f" {text}")

    def refreshTheme(self) -> None:
        """Update the theme icon."""
        if self._icon:
            self.setIcon(SHARED.theme.getIcon(self._icon))


class NIconButton(QToolButton):
    """Custom: Icon Push Button.

    A tool button that looks like an icon-only push button.
    """

    __slots__ = ("_icon",)

    def __init__(self, parent: QWidget, iconSize: QSize, icon: str | None = None) -> None:
        super().__init__(parent=parent)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setIconSize(iconSize)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._icon = icon
        if icon:  # pragma: no branch
            self.setThemeIcon(icon)

    def setThemeIcon(self, icon: str) -> None:
        """Set an icon from the current theme."""
        self._icon = icon
        self.setIcon(SHARED.theme.getIcon(icon))

    def refreshTheme(self) -> None:
        """Refresh the icon for theme updates."""
        if self._icon:  # pragma: no branch
            self.setIcon(SHARED.theme.getIcon(self._icon))

    def sizeHint(self) -> QSize:
        """Pad the size hint to a square the height of a standard QPushButton."""
        height = round(self.fontMetrics().height() * 1.5)
        return QSize(height, height)


class NFlatIconButton(QToolButton):
    """Custom: Flat Icon Tool Button.

    A flat icon-only tool button.
    """

    __slots__ = ("_icon", "_iconToggle")

    def __init__(self, parent: QWidget, iconSize: QSize, icon: str, padding: float = 0.23) -> None:
        super().__init__(parent=parent)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setIconSize(iconSize)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setFixedSize(round(iconSize.width() * (1 + 2 * padding)), round(iconSize.height() * (1 + 2 * padding)))
        self._icon = icon
        self._iconToggle = icon.startswith("toggle-")
        self.setCheckable(self._iconToggle)
        if icon:  # pragma: no branch
            self.setThemeIcon(icon)

    def setThemeIcon(self, icon: str) -> None:
        """Set an icon from the current theme."""
        self._icon = icon
        if self._iconToggle:
            self.setIcon(SHARED.theme.getToggleIcon(icon, self.iconSize().width(), self.iconSize().height()))
        else:
            self.setIcon(SHARED.theme.getIcon(icon))

    def refreshTheme(self) -> None:
        """Refresh the icon for theme updates."""
        if self._icon:  # pragma: no branch
            self.setThemeIcon(self._icon)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Paint the icon with a background colour when hovered or checked."""
        opt = QStyleOptionToolButton()
        opt.initFrom(self)

        rect = self.rect()
        painter = QPainter(self)
        if not self._iconToggle and self.isCheckable() and self.isChecked():
            painter.fillRect(rect, SHARED.theme.activeButton)
        elif opt.state & QtMouseOver == QtMouseOver:  # pragma: no cover
            painter.fillRect(rect, SHARED.theme.activeBase)

        icon = self.icon()
        if not icon.isNull():  # pragma: no branch
            size = self.iconSize()
            x = rect.x() + (rect.width() - size.width()) // 2
            y = rect.y() + (rect.height() - size.height()) // 2
            mode = QtIconNormal if self.isEnabled() else QtIconDisabled
            state = QtIconOn if self.isChecked() else QtIconOff
            icon.paint(painter, x, y, size.width(), size.height(), QtAlignCenter, mode, state)


class NFlatIconTextButton(QToolButton):
    """Custom: Modified QToolButton.

    A quicker way to create a toggle button that switches icon when
    toggled, using the app theme. For toggle buttons that only need to
    change background colour, use NIconToolButton with
    setCheckable(True) instead.
    """

    __slots__ = ("_icon", "_iconToggle")

    def __init__(self, parent: QWidget, iconSize: QSize, icon: str, text: str) -> None:
        super().__init__(parent=parent)
        self.setToolButtonStyle(QtToolButtonTextIcon)
        self.setIconSize(iconSize)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.setText(text)
        self._icon = icon
        self._iconToggle = icon.startswith("toggle-")
        self.setCheckable(self._iconToggle)
        if icon:  # pragma: no branch
            self.setThemeIcon(icon)

    def setThemeIcon(self, icon: str) -> None:
        """Set an icon from the current theme."""
        self._icon = icon
        if self._iconToggle:
            self.setIcon(SHARED.theme.getToggleIcon(icon, self.iconSize().width(), self.iconSize().height()))
        else:
            self.setIcon(SHARED.theme.getIcon(icon))

    def refreshTheme(self) -> None:
        """Refresh the icon for theme updates."""
        if self._icon:  # pragma: no branch
            self.setThemeIcon(self._icon)

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Paint the icon with a background colour when hovered or checked."""
        opt = QStyleOptionToolButton()
        opt.initFrom(self)

        rect = self.rect()
        painter = QPainter(self)
        if opt.state & QtMouseOver == QtMouseOver:  # pragma: no cover
            painter.fillRect(rect, SHARED.theme.activeBase)

        icon = self.icon()
        size = self.iconSize()
        mode = QtIconNormal if self.isEnabled() else QtIconDisabled
        state = QtIconOn if self.isChecked() else QtIconOff
        if text := self.text():  # pragma: no branch
            margin = (rect.height() - size.height()) // 2
            x = rect.x() + margin
            y = rect.y() + margin
            if not icon.isNull():  # pragma: no branch
                icon.paint(painter, x, y, size.width(), size.height(), QtAlignCenter, mode, state)
            textRect = rect.adjusted(x + size.width() + margin, 0, -margin, 0)
            painter.setPen(opt.palette.color(QPalette.ColorRole.ButtonText))
            painter.drawText(textRect, QtAlignLeftMiddle, text)


class NClickableLabel(QLabel):
    """Custom: Clickable QLabel."""

    mouseClicked = pyqtSignal()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Capture a left mouse click and emit its signal."""
        if event.button() == QtMouseLeft:
            self.mouseClicked.emit()
        return super().mousePressEvent(event)


class NClipLabel(QLabel):
    """Custom: Clipping QLabel.

    A QLabel that can be compressed narrower than its text, so long
    labels are clipped instead of forcing a horizontal scroll bar. The
    parent widget must have horizontal size policy set to expanding.
    """

    def minimumSizeHint(self) -> QSize:
        """Override the minimum size hint to allow clipping."""
        return QSize(10, super().minimumSizeHint().height())


class NSplitterHandle(QSplitterHandle):
    """Custom Widget: Highlighted Splitter Handle.

    A splitter handle that is invisible until hovered or dragged, at
    which point it lights up in the highlight colour.
    """

    def __init__(self, orientation: Qt.Orientation, parent: QSplitter) -> None:
        super().__init__(orientation, parent)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._active = False
        self._resizable = True

    def setResizable(self, resizable: bool) -> None:
        """Enable or disable the hover/drag highlight and the resize
        cursor, for use when the adjacent pane cannot actually be resized.
        """
        self._resizable = resizable
        if resizable:
            isHorizontal = self.orientation() == Qt.Orientation.Horizontal
            self.setCursor(Qt.CursorShape.SplitHCursor if isHorizontal else Qt.CursorShape.SplitVCursor)
        else:
            self._active = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def event(self, event: QEvent | None) -> bool:
        """Track hover state to trigger a repaint."""
        if event is not None and event.type() in (QEvent.Type.HoverEnter, QEvent.Type.HoverLeave):
            self._active = self._resizable and event.type() == QEvent.Type.HoverEnter
            self.update()
        return super().event(event)

    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Keep the handle highlighted while being dragged."""
        if self._resizable:
            self._active = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent | None) -> None:
        """Drop the highlight if the cursor has left the handle."""
        super().mouseReleaseEvent(event)
        self._active = self._resizable and self.underMouse()
        self.update()

    def paintEvent(self, event: QPaintEvent | None) -> None:
        """Paint the handle in the highlight colour when active."""
        if self._active:
            painter = QPainter(self)
            painter.fillRect(self.rect(), self.palette().color(QPalette.ColorRole.Highlight))
