"""
novelWriter - Custom Widget: Config Layout
==========================================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QAbstractButton, QFrame, QHBoxLayout, QLabel, QLayout, QScrollArea, QVBoxLayout, QWidget

from novelwriter import SHARED
from novelwriter.constants import nwUnicode
from novelwriter.enum import nwState
from novelwriter.types import QtFontNormal, QtFontSemiBold, QtHexArgb, QtScrollAsNeeded

DEFAULT_SCALE = 0.9


class NFixedPage(QFrame):
    """Extension: Fixed Page Widget.

    A custom widget that holds a layout. This is just a wrapper around a
    QFrame that sets the same frame style as the other Page widgets.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFrameShape(QFrame.Shape.StyledPanel)

    def setCentralLayout(self, layout: QLayout) -> None:
        """Set a layout as the central object."""
        self.setLayout(layout)

    def setCentralWidget(self, widget: QWidget) -> None:
        """Set a layout as the central object."""
        layout = QHBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)


class NScrollablePage(QScrollArea):
    """Extension: Scrollable Page Widget.

    A custom widget that holds a layout within a scrollable area.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._widget = QWidget(self)
        self.setWidget(self._widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtScrollAsNeeded)
        self.setVerticalScrollBarPolicy(QtScrollAsNeeded)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFrameShape(QFrame.Shape.StyledPanel)

    def setCentralLayout(self, layout: QLayout) -> None:
        """Set the central layout of the scroll page."""
        self._widget.setLayout(layout)


class NScrollableForm(QScrollArea):
    """Extension: Scrollable Form Widget.

    A custom widget that creates a form within a scrollable area.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._helpCol = QColor(0, 0, 0)
        self._fontScale = DEFAULT_SCALE
        self._first = True
        self._indent = 12

        self._sections: dict[int, QLabel] = {}
        self._editableHelp: dict[str, NColorLabel] = {}
        self._editableUnit: dict[str, QLabel] = {}
        self._index: dict[str, QWidget] = {}

        self._layout = QVBoxLayout()
        self._layout.setSpacing(12)

        self._widget = QWidget(self)
        self._widget.setLayout(self._layout)

        self.setWidget(self._widget)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(QtScrollAsNeeded)
        self.setVerticalScrollBarPolicy(QtScrollAsNeeded)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setFrameShape(QFrame.Shape.StyledPanel)

    ##
    #  Properties
    ##

    @property
    def labels(self) -> list[str]:
        return list(self._index.keys())

    ##
    #  Setters
    ##

    def setHelpTextStyle(self, color: QColor, scale: float = DEFAULT_SCALE) -> None:
        """Set the text color for the help text."""
        self._helpCol = color
        self._fontScale = scale

    def setHelpText(self, key: str, text: str) -> None:
        """Set the text for the help label."""
        if qHelp := self._editableHelp.get(key):
            qHelp.setText(text)

    def setUnitText(self, key: str, text: str) -> None:
        """Set the text for the unit label."""
        if qUnit := self._editableUnit.get(key):
            qUnit.setText(text)

    def setRowIndent(self, indent: int) -> None:
        """Set the indentation of each row."""
        self._indent = max(indent, 0)

    ##
    #  Methods
    ##

    def scrollToSection(self, identifier: int) -> None:
        """Scroll to the requested section identifier."""
        if identifier in self._sections:
            yPos = self._sections[identifier].pos().y() - 8
            if vBar := self.verticalScrollBar():  # pragma: no branch
                vBar.setValue(yPos)

    def scrollToLabel(self, label: str) -> None:
        """Scroll to the requested label."""
        if label in self._index:
            yPos = self._index[label].pos().y() - 8
            if vBar := self.verticalScrollBar():  # pragma: no branch
                vBar.setValue(yPos)

    def addGroupLabel(self, label: str, identifier: int | None = None) -> None:
        """Add a text label to separate groups of settings."""
        qLabel = QLabel(label, self)
        qLabel.setFont(SHARED.theme.guiFontB)
        qLabel.setContentsMargins(0, 4, 0, 4)
        if not self._first:
            self._layout.addSpacing(20)
        self._layout.addWidget(qLabel)
        self._first = False
        if identifier is not None:
            self._sections[identifier] = qLabel

    def addRow(
        self,
        label: str | None,
        widget: QWidget | list[QWidget | int],
        helpText: str = "",
        unit: str | None = None,
        button: QWidget | None = None,
        editable: str | None = None,
        stretch: tuple[int, int] = (1, 0),
    ) -> None:
        """Add a label and a widget as a new row of the form."""
        row = QHBoxLayout()
        row.setSpacing(12)

        if isinstance(widget, list):
            wBox = QHBoxLayout()
            wBox.setContentsMargins(0, 0, 0, 0)
            for item in widget:
                if isinstance(item, QWidget):
                    wBox.addWidget(item)
                elif isinstance(item, int):
                    wBox.addSpacing(item)
            qWidget = QWidget(self)
            qWidget.setLayout(wBox)
        else:
            qWidget = widget

        qLabel = QLabel(label or "", self)
        qLabel.setIndent(self._indent)
        qLabel.setBuddy(qWidget)
        qWidget.setAccessibleName(label)

        if helpText:
            qHelp = NColorLabel(
                str(helpText),
                self,
                color=self._helpCol,
                scale=self._fontScale,
                wrap=True,
                indent=self._indent,
            )
            qHelp.setBuddy(qWidget)
            qWidget.setAccessibleDescription(helpText)
            labelBox = QVBoxLayout()
            labelBox.addWidget(qLabel, 0)
            labelBox.addWidget(qHelp, 1)
            labelBox.setSpacing(0)
            row.addLayout(labelBox, stretch[0])
            if editable:
                self._editableHelp[editable] = qHelp
        else:
            row.addWidget(qLabel, stretch[0])

        if isinstance(unit, str):
            qUnit = QLabel(unit, self)
            qUnit.setBuddy(qWidget)
            qWidget.setAccessibleDescription(f"{unit}. {qWidget.accessibleDescription()}")
            box = QHBoxLayout()
            box.addWidget(qWidget, 1)
            box.addWidget(qUnit, 0)
            row.addLayout(box, stretch[1])
            if editable:
                self._editableUnit[editable] = qUnit
        elif isinstance(button, QAbstractButton):
            box = QHBoxLayout()
            box.addWidget(qWidget, 1)
            box.addWidget(button, 0)
            row.addLayout(box, stretch[1])
        else:
            row.addWidget(qWidget, stretch[1])

        self._first = False
        self._layout.addLayout(row)
        if label:
            self._index[label.strip()] = qWidget

    def finalise(self) -> None:
        """Finalise the layout when the form is built."""
        self._layout.addSpacing(20)
        self._layout.addStretch(1)


class NColorLabel(QLabel):
    """Extension: A Coloured Label.

    A custom widget that draws a label in a specific colour, and
    optionally at a specific size, and word wrapped.
    """

    HELP_SCALE = DEFAULT_SCALE
    NORMAL_SCALE = 1.0
    HEADER_SCALE = 1.25

    _state = None

    def __init__(
        self,
        text: str,
        parent: QWidget,
        *,
        color: QColor | None = None,
        faded: QColor | None = None,
        error: QColor | None = None,
        scale: float = HELP_SCALE,
        wrap: bool = False,
        indent: int = 0,
        bold: bool = False,
    ) -> None:
        super().__init__(text, parent=parent)

        default = self.palette().windowText().color()
        self._color = color or default
        self._faded = faded or default
        self._error = error or default

        font = self.font()
        font.setPointSizeF(scale * font.pointSizeF())
        font.setWeight(QtFontSemiBold if bold else QtFontNormal)

        self.setTextFormat(Qt.TextFormat.RichText)
        self.setFont(font)
        self.setIndent(indent)
        self.setWordWrap(wrap)
        self.setColorState(nwState.NORMAL)

    def setTextColors(
        self,
        *,
        color: QColor | None = None,
        faded: QColor | None = None,
        error: QColor | None = None,
    ) -> None:
        """Set or update the text colours."""
        self._color = color or self._color
        self._faded = faded or self._faded
        self._error = error or self._error
        self._refreshTextColor()

    def setColorState(self, state: nwState) -> None:
        """Change the colour state."""
        if self._state is not state:
            self._state = state
            self._refreshTextColor()

    def _refreshTextColor(self) -> None:
        """Refresh the colour of the text on the label."""
        palette = self.palette()
        match self._state:
            case nwState.NORMAL:
                palette.setColor(QPalette.ColorRole.WindowText, self._color)
            case nwState.INACTIVE:
                palette.setColor(QPalette.ColorRole.WindowText, self._faded)
            case nwState.ERROR:
                palette.setColor(QPalette.ColorRole.WindowText, self._error)
            case _:  # pragma: no cover
                pass
        self.setPalette(palette)


class NPathColorLabel(NColorLabel):
    """Extension: A Coloured Label for Paths."""

    _crumbs: list[tuple[str, str]] | None = None

    def setText(self, value: str | list[tuple[str, str]]) -> None:
        """Set the text or a clickable crumb-trail of links."""
        if isinstance(value, str):
            self._crumbs = None
            super().setText(value)
        else:
            self._crumbs = value
            self._refreshTextColor()

    def _refreshTextColor(self) -> None:
        """Refresh the colour of the text on the label."""
        super()._refreshTextColor()
        if self._crumbs is not None:
            color = self.palette().windowText().color().name(QtHexArgb)
            style = f"color: {color}; text-decoration: none"
            inner = f"  {nwUnicode.U_RSAQUO}  ".join(
                reversed([f"<a href='#{h}' style='{style}'>{n}</a>" for h, n in self._crumbs])
            )
            super().setText(f"<font style='color: {color}'>{inner}</font>")


class NWrappedWidgetBox(QHBoxLayout):
    """Extension: A Text-Wrapped Widget Box.

    A custom layout box where a widget is wrapped in text labels on
    either side within a layout box. The widget is inserted at the {0}
    position so that it can be used for translation strings.
    """

    def __init__(self, text: str, widget: QWidget) -> None:
        super().__init__()
        before, _, after = text.partition(r"{0}")
        if before:
            self.addWidget(QLabel(before.rstrip()))
        self.addWidget(widget)
        if after:
            self.addWidget(QLabel(after.lstrip()))
