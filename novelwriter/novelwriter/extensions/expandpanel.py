"""
novelWriter - Custom Widget: Expandable Panel
=============================================

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

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QPalette
from PyQt6.QtWidgets import QWIDGETSIZE_MAX, QHBoxLayout, QLayout, QSplitter, QSplitterHandle, QVBoxLayout, QWidget

from novelwriter import SHARED
from novelwriter.extensions.modified import NClickableLabel, NFlatIconButton, NSplitterHandle


class NExpandablePanel(QWidget):
    """Custom Widget: Expandable Panel.

    A panel that can be expanded or collapsed by clicking on its header.
    The header contains a title and an optional icon, and the content
    area can contain any widget.
    """

    expandedStateChanged = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ep_expanded = True
        self._ep_widget = QWidget(self)

        self._ep_toggle = NFlatIconButton(self, SHARED.theme.baseIconSize, "toggle-unfold:default", padding=0)
        self._ep_toggle.setChecked(self._ep_expanded)
        self._ep_toggle.toggled.connect(self._toggleExpanded)

        self._ep_label = NClickableLabel("Unnamed", self)
        self._ep_label.setFont(SHARED.theme.guiFontB)
        self._ep_label.mouseClicked.connect(self._ep_toggle.click)

        self._ep_headerBox = QWidget(self)
        self._ep_headerBox.setContentsMargins(0, 2, 0, 2)

        self._ep_header = QHBoxLayout()
        self._ep_header.setContentsMargins(0, 0, 0, 0)
        self._ep_header.addWidget(self._ep_toggle)
        self._ep_header.addWidget(self._ep_label)
        self._ep_header.setSpacing(2)
        self._ep_headerBox.setLayout(self._ep_header)

        self._ep_layout = QVBoxLayout()
        self._ep_layout.setContentsMargins(0, 0, 0, 0)
        self._ep_layout.addWidget(self._ep_headerBox)
        self._ep_layout.addWidget(self._ep_widget)
        self._ep_layout.setSpacing(0)

        self.setLayout(self._ep_layout)

    ##
    #  Setters
    ##

    def setTitle(self, title: str) -> None:
        """Set the title of the panel."""
        self._ep_label.setText(title)

    def setExpanded(self, expanded: bool) -> None:
        """Set the expanded state of the panel."""
        self._ep_toggle.setChecked(expanded)

    def setContentLayout(self, layout: QLayout) -> None:
        """Set the content layout of the panel."""
        self._ep_widget.setLayout(layout)

    def setHeaderBackgroundRole(self, role: QPalette.ColorRole) -> None:
        """Set the background role of the header."""
        self._ep_headerBox.setBackgroundRole(role)
        self._ep_headerBox.setAutoFillBackground(True)

    ##
    #  Methods
    ##

    def isExpanded(self) -> bool:
        """Return the expanded state of the panel."""
        return self._ep_expanded

    def updateTheme(self) -> None:
        """Update the theme of the panel."""
        self._ep_toggle.refreshTheme()

    ##
    #  Private Slots
    ##

    @pyqtSlot(bool)
    def _toggleExpanded(self, state: bool) -> None:
        """Toggle the expanded state of the panel."""
        if self._ep_expanded != state:
            self._ep_expanded = state
            self._ep_widget.setVisible(state)
            if state:
                self.setMaximumHeight(QWIDGETSIZE_MAX)
            else:
                self.setMaximumHeight(self.minimumSizeHint().height())
            self.expandedStateChanged.emit(state)


class NExpandablePanelGroup(QSplitter):
    """Custom Widget: Expandable Panel Group.

    A vertical stack of widgets and expandable panels. Expandable
    panels are locked to their header-only size while collapsed, and
    freely resizable while expanded. The size a panel had before it was
    collapsed is tracked internally, and restored when expanded again.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(Qt.Orientation.Vertical, parent)
        self.setChildrenCollapsible(False)
        self.setHandleWidth(4)
        self._expandedSizes: dict[NExpandablePanel, int] = {}

    ##
    #  Methods
    ##

    def createHandle(self) -> QSplitterHandle:
        """Return a custom splitter handle that only lights up on hover."""
        return NSplitterHandle(self.orientation(), self)

    def addWidget(self, widget: QWidget) -> None:
        """Add a widget or expandable panel to the group."""
        super().addWidget(widget)
        if isinstance(widget, NExpandablePanel):
            self._expandedSizes[widget] = widget.sizeHint().height()
            widget.expandedStateChanged.connect(self._panelToggled)
            widget.setHeaderBackgroundRole(QPalette.ColorRole.AlternateBase)
            if not widget.isExpanded():
                self._collapse(widget)
        self._updateHandles()

    def setPanelSizes(self, sizes: list[int]) -> None:
        """Set the sizes of the widgets in the group. For a collapsed
        panel, the size given is instead remembered as the size to
        restore once the panel is expanded again, and the panel itself
        is kept locked to its header size.
        """
        applied = list(sizes)
        for i, size in enumerate(sizes):
            widget = self.widget(i)
            if isinstance(widget, NExpandablePanel):
                if size > 0:
                    self._expandedSizes[widget] = size
                if not widget.isExpanded():
                    applied[i] = 0
        self.setSizes(applied)

    def panelSizes(self) -> list[int]:
        """Return the sizes of the widgets in the group, substituting the
        tracked expanded size for any panel that is currently collapsed.
        """
        sizes = self.sizes()
        for i in range(self.count()):
            widget = self.widget(i)
            if isinstance(widget, NExpandablePanel) and not widget.isExpanded():
                sizes[i] = self._expandedSizes.get(widget, sizes[i])
        return sizes

    ##
    #  Private Slots
    ##

    @pyqtSlot(bool)
    def _panelToggled(self, state: bool) -> None:
        """Collapse or expand a panel when its state changes."""
        panel = self.sender()
        if isinstance(panel, NExpandablePanel):  # pragma: no branch
            if state:
                self._expand(panel)
            else:
                self._collapse(panel)

    ##
    #  Internal Functions
    ##

    def _collapse(self, panel: NExpandablePanel) -> None:
        """Lock a panel to its header size, and remember its size."""
        index = self.indexOf(panel)
        sizes = self.sizes()
        if sizes[index] > 0:
            self._expandedSizes[panel] = sizes[index]
        sizes[index] = 0
        self.setSizes(sizes)
        self._updateHandles()

    def _expand(self, panel: NExpandablePanel) -> None:
        """Restore a panel to its last known expanded size."""
        index = self.indexOf(panel)
        sizes = self.sizes()
        sizes[index] = self._expandedSizes.get(panel, panel.sizeHint().height())
        self.setSizes(sizes)
        self._updateHandles()

    def _updateHandles(self) -> None:
        """Disable handles next to a panel that cannot be resized because
        it is collapsed, since dragging them would have no effect.
        """
        for i in range(1, self.count()):
            before = self.widget(i - 1)
            after = self.widget(i)
            locked = any(isinstance(w, NExpandablePanel) and not w.isExpanded() for w in (before, after))
            if isinstance(handle := self.handle(i), NSplitterHandle):  # pragma: no branch
                handle.setResizable(not locked)
