"""
novelWriter - GUI Editor Footer
===============================

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

import logging

from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QPalette, QPixmap, QTextCursor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import qtWeakLambda
from novelwriter.constants import nwLabels, nwStats, trLabel, trStats
from novelwriter.enum import nwStdLabel, nwVimMode
from novelwriter.extensions.modified import NFlatIconButton, NFlatIconTextButton
from novelwriter.types import QtAlignLeftTop, QtBlack

if TYPE_CHECKING:
    from novelwriter.editor.viewer import GuiDocViewer

logger = logging.getLogger(__name__)


class GuiDocEditFooter(QWidget):
    """The Embedded Document Footer.

    Only used by DocEditor, and is at a fixed position in the
    QTextEdit's viewport.
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocEditFooter")

        self._tItem = None
        self._docHandle = None

        iPx = round(0.9 * SHARED.theme.baseIconHeight)
        fPx = int(0.9 * SHARED.theme.fontPixelSize)

        # Cached Translations
        self.initSettings()
        self._trLineCount = self.tr("Line: {0} ({1})")
        self._trSelectCount = self.tr("Selected: {0}")

        self._lineNo = -1
        self._linePc = -1

        # Main Widget Settings
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)

        # Status
        self.statusIcon = QLabel("", self)
        self.statusIcon.setFixedHeight(iPx)
        self.statusIcon.setAlignment(QtAlignLeftTop)

        self.statusText = QLabel("", self)
        self.statusText.setAutoFillBackground(True)
        self.statusText.setFixedHeight(fPx)
        self.statusText.setAlignment(QtAlignLeftTop)

        # Lines
        self.linesIcon = QLabel("", self)
        self.linesIcon.setFixedHeight(iPx)
        self.linesIcon.setAlignment(QtAlignLeftTop)

        self.linesText = QLabel("", self)
        self.linesText.setAutoFillBackground(True)
        self.linesText.setFixedHeight(fPx)
        self.linesText.setAlignment(QtAlignLeftTop)

        # Words
        self.wordsIcon = QLabel("", self)
        self.wordsIcon.setFixedHeight(iPx)
        self.wordsIcon.setAlignment(QtAlignLeftTop)

        self.wordsText = QLabel("", self)
        self.wordsText.setAutoFillBackground(True)
        self.wordsText.setFixedHeight(fPx)
        self.wordsText.setAlignment(QtAlignLeftTop)

        # Vim mode status bar
        self.vimStatus = QLabel("", self)
        self.vimStatus.setAutoFillBackground(True)
        self.vimStatus.setFixedHeight(fPx)
        self.vimStatus.setAlignment(QtAlignLeftTop)
        self._vimMode: nwVimMode | None = None
        self._vimColor = SHARED.theme.getBaseColor("base")
        self._vimModes = {}

        # Assemble Layout
        self.outerBox = QHBoxLayout()
        self.outerBox.setSpacing(4)
        self.outerBox.addWidget(self.statusIcon)
        self.outerBox.addWidget(self.statusText)
        self.outerBox.addStretch(1)
        self.outerBox.addSpacing(6)
        self.outerBox.addWidget(self.vimStatus)
        self.outerBox.addSpacing(6)
        self.outerBox.addWidget(self.linesIcon)
        self.outerBox.addWidget(self.linesText)
        self.outerBox.addSpacing(6)
        self.outerBox.addWidget(self.wordsIcon)
        self.outerBox.addWidget(self.wordsText)
        self.outerBox.setContentsMargins(8, 8, 8, 8)

        self.setLayout(self.outerBox)

        # Fix Margins and Size
        # This is needed for high DPI systems. See issue #499.
        self.setContentsMargins(0, 0, 0, 0)
        self.setMinimumHeight(fPx + 16)

        # Fix the Colours
        self.updateFont()
        self.updateTheme()

        # Initialise Info
        self.updateMainCount(0, False)

        logger.debug("Ready: GuiDocEditFooter")

    ##
    #  Methods
    ##

    def initSettings(self) -> None:
        """Apply user settings."""
        self._trMainCount = trStats(nwLabels.STATS_DISPLAY[nwStats.CHARS if CONFIG.useCharCount else nwStats.WORDS])

    def updateFont(self) -> None:
        """Update the font settings."""
        self.setFont(SHARED.theme.guiFont)
        self.statusText.setFont(SHARED.theme.guiFontSmall)
        self.linesText.setFont(SHARED.theme.guiFontSmall)
        self.wordsText.setFont(SHARED.theme.guiFontSmall)
        self.vimStatus.setFont(SHARED.theme.guiFontSmall)

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocEditFooter")

        iPx = round(0.9 * SHARED.theme.baseIconHeight)
        self.linesIcon.setPixmap(SHARED.theme.getPixmap("lines", iPx, iPx))
        self.wordsIcon.setPixmap(SHARED.theme.getPixmap("stats", iPx, iPx))
        self.matchColors()
        self._vimColor = SHARED.theme.getBaseColor("base")
        self._vimModes = {
            nwVimMode.NORMAL: (self.tr("NORMAL"), SHARED.theme.getBaseColor("green")),
            nwVimMode.INSERT: (self.tr("INSERT"), SHARED.theme.getBaseColor("blue")),
            nwVimMode.VISUAL: (self.tr("VISUAL"), SHARED.theme.getBaseColor("orange")),
            nwVimMode.V_LINE: (self.tr("V-LINE"), SHARED.theme.getBaseColor("orange")),
        }

    def matchColors(self) -> None:
        """Update the colours of the widget to match those of the syntax
        theme rather than the main GUI.
        """
        syntax = SHARED.theme.syntaxTheme

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, syntax.back)
        palette.setColor(QPalette.ColorRole.WindowText, syntax.text)
        palette.setColor(QPalette.ColorRole.Text, syntax.text)

        self.setPalette(palette)
        self.statusText.setPalette(palette)
        self.linesText.setPalette(palette)
        self.wordsText.setPalette(palette)

    def setHandle(self, tHandle: str | None) -> None:
        """Set the handle that will populate the footer's data."""
        self._docHandle = tHandle
        if self._docHandle is None:
            logger.debug("No handle set, so clearing the editor footer")
            self._tItem = None
        else:
            self._tItem = SHARED.project.tree[self._docHandle]

        self.updateInfo()
        self.updateMainCount(0, False)

    def updateInfo(self) -> None:
        """Update the content of text labels."""
        if self._tItem is None:
            sIcon = QPixmap()
            sText = ""
        else:
            iPx = round(0.9 * SHARED.theme.baseIconHeight)
            status, icon = self._tItem.getImportStatus()
            sIcon = icon.pixmap(iPx, iPx)
            sText = f"{status} / {self._tItem.describeMe()}"

        self.statusIcon.setPixmap(sIcon)
        self.statusText.setText(sText)

    def updateLineCount(self, cursor: QTextCursor) -> None:
        """Update the line and document position counter."""
        if document := cursor.document():  # pragma: no branch
            lineNo = cursor.blockNumber() + 1
            linePc = 100 * (cursor.position() + 1) // max(document.characterCount(), 1)
            if lineNo != self._lineNo or linePc != self._linePc:
                self.linesText.setText(self._trLineCount.format(f"{lineNo:n}", f"{linePc:d}\u202f%"))
                self._lineNo = lineNo
                self._linePc = linePc

    def updateMainCount(self, count: int, selection: bool) -> None:
        """Update main counter information."""
        if selection and count:
            text = self._trSelectCount.format(f"{count:n}")
        elif self._tItem:
            count = self._tItem.mainCount
            diff = count - self._tItem.initCount
            text = self._trMainCount.format(f"{count:n}", f"{diff:+n}")
        else:
            text = self._trMainCount.format("0", "+0")
        self.wordsText.setText(text)

    def updateVimModeStatusBar(self, mode: nwVimMode | None) -> None:
        """Update the vim Mode status information."""
        if mode is None:
            self.vimStatus.setText("")
            self.vimStatus.setVisible(False)
            self._vimMode = None
        elif mode != self._vimMode:
            text, color = self._vimModes.get(mode, ("", QtBlack))
            palette = self.vimStatus.palette()
            palette.setColor(QPalette.ColorRole.WindowText, self._vimColor)
            palette.setColor(QPalette.ColorRole.Window, color)
            self.vimStatus.setText(f"  {text}  ")
            self.vimStatus.setPalette(palette)
            self.vimStatus.setVisible(True)
            self._vimMode = mode


class GuiDocViewFooter(QWidget):
    """The Embedded Document Footer.

    Only used by DocViewer, and is at a fixed position in the
    QTextBrowser's viewport.
    """

    def __init__(self, docViewer: GuiDocViewer) -> None:
        super().__init__(parent=docViewer)

        logger.debug("Create: GuiDocViewFooter")

        self.docViewer = docViewer

        # Internal Variables
        self._docHandle = None

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        # Main Widget Settings
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)

        # Show/Hide Details
        self.showHide = NFlatIconButton(self, iSz, "panel:default")
        self.showHide.setToolTip(self.tr("Show/Hide Viewer Panel"))
        self.showHide.clicked.connect(qtWeakLambda(self._emitTogglePanelVisibility))

        # Show Comments
        self.showComments = NFlatIconTextButton(self, iSz, "toggle-bullet:action", self.tr("Comments"))
        self.showComments.setToolTip(self.tr("Show Comments"))
        self.showComments.setCheckable(True)
        self.showComments.setChecked(CONFIG.viewComments)
        self.showComments.setIconSize(iSz)
        self.showComments.toggled.connect(self._doToggleComments)

        # Show Synopsis
        self.showSynopsis = NFlatIconTextButton(self, iSz, "toggle-bullet:action", trLabel(nwStdLabel.SYNOPSIS))
        self.showSynopsis.setToolTip(self.tr("Show Synopsis Comments"))
        self.showSynopsis.setCheckable(True)
        self.showSynopsis.setChecked(CONFIG.viewSynopsis)
        self.showSynopsis.setIconSize(iSz)
        self.showSynopsis.toggled.connect(self._doToggleSynopsis)

        # Show Notes
        self.showNotes = NFlatIconTextButton(self, iSz, "toggle-bullet:action", self.tr("Notes"))
        self.showNotes.setToolTip(self.tr("Show Notes"))
        self.showNotes.setCheckable(True)
        self.showNotes.setChecked(CONFIG.viewNotes)
        self.showNotes.setIconSize(iSz)
        self.showNotes.toggled.connect(self._doToggleNotes)

        # Assemble Layout
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.showHide, 0)
        self.outerBox.addStretch(1)
        self.outerBox.addWidget(self.showComments, 0)
        self.outerBox.addWidget(self.showSynopsis, 0)
        self.outerBox.addWidget(self.showNotes, 0)
        self.outerBox.setSpacing(4)
        self.setLayout(self.outerBox)

        # Fix Margins and Size
        # This is needed for high DPI systems. See issue #499.
        self.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setContentsMargins(4, 4, 4, 4)
        self.setMinimumHeight(iPx + 8)

        self.updateFont()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiDocViewFooter")

    ##
    #  Methods
    ##

    def updateFont(self) -> None:
        """Update the font settings."""
        self.setFont(SHARED.theme.guiFont)
        self.showComments.setFont(SHARED.theme.guiFontSmall)
        self.showSynopsis.setFont(SHARED.theme.guiFontSmall)
        self.showNotes.setFont(SHARED.theme.guiFontSmall)

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocViewFooter")

        if not init:
            self.showHide.refreshTheme()
            self.showComments.refreshTheme()
            self.showSynopsis.refreshTheme()
            self.showNotes.refreshTheme()

        self.matchColors()

    def matchColors(self) -> None:
        """Update the colours of the widget to match those of the syntax
        theme rather than the main GUI.
        """
        syntax = SHARED.theme.syntaxTheme
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, syntax.back)
        palette.setColor(QPalette.ColorRole.WindowText, syntax.text)
        palette.setColor(QPalette.ColorRole.Text, syntax.text)
        self.setPalette(palette)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _emitTogglePanelVisibility(self) -> None:
        """Forward a toggle panel visibility request."""
        self.docViewer.togglePanelVisibility.emit()

    @pyqtSlot(bool)
    def _doToggleComments(self, state: bool) -> None:
        """Toggle the view comment button and reload the document."""
        CONFIG.viewComments = state
        self.docViewer.reloadText()

    @pyqtSlot(bool)
    def _doToggleSynopsis(self, state: bool) -> None:
        """Toggle the view synopsis button and reload the document."""
        CONFIG.viewSynopsis = state
        self.docViewer.reloadText()

    @pyqtSlot(bool)
    def _doToggleNotes(self, state: bool) -> None:
        """Toggle the view notes button and reload the document."""
        CONFIG.viewNotes = state
        self.docViewer.reloadText()
