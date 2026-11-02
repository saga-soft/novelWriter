"""
novelWriter - GUI Document Header
=================================

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

from enum import Enum
from time import time

from PyQt6.QtCore import QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QPalette
from PyQt6.QtWidgets import QHBoxLayout, QMenu, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import elide, qtAddAction
from novelwriter.enum import nwDocMode, nwState
from novelwriter.extensions.configlayout import NPathColorLabel
from novelwriter.extensions.modified import NFlatIconButton
from novelwriter.types import QtAlignCenterTop, QtAlignMiddle

logger = logging.getLogger(__name__)


class GuiDocHeaderBase(QWidget):
    """The Embedded Document Header Base Class.

    Holds the title, outline and close elements shared by the editor
    and viewer headers.
    """

    closeDocumentRequest = pyqtSignal()
    requestProjectItemSelected = pyqtSignal(str, bool)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._docHandle: str | None = None
        self._state = nwState.NORMAL

        iSz = SHARED.theme.baseIconSize
        fPx = SHARED.theme.fontPixelSize

        # Main Widget Settings
        self.setAutoFillBackground(True)

        # Title Label
        self.itemTitle = NPathColorLabel("", self)
        self.itemTitle.setMargin(0)
        self.itemTitle.setContentsMargins(0, 0, 0, 0)
        self.itemTitle.setAutoFillBackground(True)
        self.itemTitle.setAlignment(QtAlignCenterTop)
        self.itemTitle.setFixedHeight(fPx)
        self.itemTitle.linkActivated.connect(self._processLabelLink)

        # Outline
        self.outlineMenu = QMenu(self)

        self.outlineButton = NFlatIconButton(self, iSz, "list:action")
        self.outlineButton.setVisible(False)
        self.outlineButton.setToolTip(self.tr("Outline"))
        self.outlineButton.setMenu(self.outlineMenu)

        # Close
        self.closeButton = NFlatIconButton(self, iSz, "close:reject")
        self.closeButton.setVisible(False)
        self.closeButton.setToolTip(self.tr("Close"))
        self.closeButton.clicked.connect(self._closeDocument)

        # Layout
        self.outerBox = QHBoxLayout()
        self.outerBox.setContentsMargins(4, 4, 4, 4)
        self.outerBox.setSpacing(0)

    ##
    #  Setters
    ##

    def setHandle(self, tHandle: str) -> None:
        """Set the document title from the handle, or alternatively, set
        the whole document path within the project.
        """
        self._docHandle = tHandle
        if CONFIG.showFullPath:
            self.itemTitle.setText(SHARED.project.tree.itemPath(tHandle, withName=True))
        elif item := SHARED.project.tree[tHandle]:
            self.itemTitle.setText([(item.itemHandle, item.itemName)])

    ##
    #  Methods
    ##

    def clearHeader(self) -> None:
        """Clear the header."""
        self._docHandle = None
        self.itemTitle.setText("")
        self.outlineMenu.clear()
        self.outlineButton.setVisible(False)
        self.closeButton.setVisible(False)

    def heightHint(self) -> int:
        """Return the height to reserve for the header."""
        return 0 if self.isHidden() else self.sizeHint().height()

    def updateFont(self) -> None:
        """Update the font settings."""
        self.setFont(SHARED.theme.guiFont)
        self.itemTitle.setFont(SHARED.theme.guiFontSmall)

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        if not init:
            self.outlineButton.refreshTheme()
            self.closeButton.refreshTheme()
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
        self.itemTitle.setTextColors(
            color=palette.windowText().color(),
            faded=SHARED.theme.fadedText,
            error=SHARED.theme.errorText,
        )

    def changeFocusState(self, state: bool) -> None:
        """Toggle focus state."""
        self._state = nwState.NORMAL if state else nwState.INACTIVE
        self.itemTitle.setColorState(self._state)

    def flashError(self) -> None:
        """Flash a red colour for the header for a moment."""
        self.itemTitle.setColorState(nwState.ERROR)
        QTimer.singleShot(250, self._resetColourState)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _closeDocument(self) -> None:
        """Clear the header and forward the close request."""
        self.clearHeader()
        self.closeDocumentRequest.emit()

    @pyqtSlot()
    def _resetColourState(self) -> None:
        """Reset the colour state of the header title."""
        self.itemTitle.setColorState(self._state)

    @pyqtSlot(str)
    def _processLabelLink(self, link: str) -> None:
        """Process an activated link in the label."""
        if link.startswith("#"):
            self.requestProjectItemSelected.emit(link.lstrip("#"), True)

    ##
    #  Internal Functions
    ##

    def _retainSizeWhenHidden(self, widget: QWidget) -> None:
        """Make a widget keep its layout space when hidden."""
        policy = widget.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        widget.setSizePolicy(policy)


class GuiDocEditHeader(GuiDocHeaderBase):
    """The Embedded Document Header.

    Only used by DocEditor, and is at a fixed position in the
    QTextEdit's viewport.
    """

    gotoLineRequest = pyqtSignal(int)
    toggleFocusModeRequest = pyqtSignal()
    toggleSearchRequest = pyqtSignal()
    toggleToolBarRequest = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        logger.debug("Create: GuiDocEditHeader")

        self._docOutline: dict[int, str] = {}

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        # Keep as spacer in focus mode
        self._retainSizeWhenHidden(self.itemTitle)

        self.outlineMenu.triggered.connect(self._gotoBlock)

        # Buttons
        self.tbButton = NFlatIconButton(self, iSz, "fmt_toolbar:action")
        self.tbButton.setVisible(False)
        self.tbButton.setToolTip(self.tr("Toggle Tool Bar"))
        self.tbButton.clicked.connect(self.toggleToolBarRequest)

        self.searchButton = NFlatIconButton(self, iSz, "search:action")
        self.searchButton.setVisible(False)
        self.searchButton.setToolTip(self.tr("Search"))
        self.searchButton.clicked.connect(self.toggleSearchRequest)

        self.minmaxButton = NFlatIconButton(self, iSz, "maximise:action")
        self.minmaxButton.setVisible(False)
        self.minmaxButton.setToolTip(self.tr("Toggle Focus Mode"))
        self.minmaxButton.clicked.connect(self.toggleFocusModeRequest)

        # Keep the header height stable when no document is open
        self._retainSizeWhenHidden(self.minmaxButton)

        # Assemble
        self.outerBox.addWidget(self.tbButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.outlineButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.searchButton, 0, QtAlignMiddle)
        self.outerBox.addSpacing(4)
        self.outerBox.addWidget(self.itemTitle, 1, QtAlignMiddle)
        self.outerBox.addSpacing(4)
        self.outerBox.addSpacing(iPx)
        self.outerBox.addWidget(self.minmaxButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.closeButton, 0, QtAlignMiddle)

        self.setLayout(self.outerBox)

        # Other Signals
        SHARED.focusModeChanged.connect(self._focusModeChanged)

        self.updateFont()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiDocEditHeader")

    ##
    #  Setters
    ##

    def setHandle(self, tHandle: str) -> None:
        """Set the document title and show the buttons."""
        super().setHandle(tHandle)
        self.tbButton.setVisible(True)
        self.minmaxButton.setVisible(True)
        self.setFocusMode(SHARED.focusMode)

    def setFocusMode(self, focusMode: bool) -> None:
        """Update the header when in Focus Mode."""
        isShown = not (focusMode and CONFIG.cleanFocusHeader)
        self.outlineButton.setVisible(isShown)
        self.searchButton.setVisible(isShown)
        self.itemTitle.setVisible(isShown)
        self.closeButton.setVisible(isShown)

    ##
    #  Methods
    ##

    def clearHeader(self) -> None:
        """Clear the header."""
        super().clearHeader()
        self._docOutline = {}
        self.tbButton.setVisible(False)
        self.searchButton.setVisible(False)
        self.minmaxButton.setVisible(False)

    def setOutline(self, data: dict[int, str]) -> None:
        """Set the document outline dataset."""
        if data != self._docOutline:
            tStart = time()
            self.outlineMenu.clear()
            for number, text in data.items():
                qtAddAction(self.outlineMenu, elide(text, 50), data=number)
            self._docOutline = data
            logger.debug("Document outline updated in %.3f ms", 1000 * (time() - tStart))

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocEditHeader")
        if not init:
            self.tbButton.refreshTheme()
            self.searchButton.refreshTheme()
            self.minmaxButton.refreshTheme()
        super().updateTheme(init=init)

    ##
    #  Private Slots
    ##

    @pyqtSlot(QAction)
    def _gotoBlock(self, action: QAction) -> None:
        """Move cursor to a specific heading."""
        if isinstance(blockNumber := action.data(), int):
            self.gotoLineRequest.emit(blockNumber + 1)

    @pyqtSlot(bool)
    def _focusModeChanged(self, focusMode: bool) -> None:
        """Update minimise/maximise icon of the Focus Mode button."""
        self.minmaxButton.setThemeIcon("minimise:action" if focusMode else "maximise:action")


class GuiDocViewHeader(GuiDocHeaderBase):
    """The Embedded Document Header.

    Only used by DocViewer, and is at a fixed position in the
    QTextBrowser's viewport.
    """

    navBackwardRequest = pyqtSignal()
    navForwardRequest = pyqtSignal()
    navigateRequest = pyqtSignal(str)
    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    reloadDocumentRequest = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        logger.debug("Create: GuiDocViewHeader")

        self._docOutline: dict[str, tuple[str, int]] = {}

        iSz = SHARED.theme.baseIconSize

        self.outlineMenu.triggered.connect(self._gotoHeader)

        # Buttons
        self.backButton = NFlatIconButton(self, iSz, "chevron_left:action")
        self.backButton.setVisible(False)
        self.backButton.setToolTip(self.tr("Go Backward"))
        self.backButton.clicked.connect(self.navBackwardRequest)

        self.forwardButton = NFlatIconButton(self, iSz, "chevron_right:action")
        self.forwardButton.setVisible(False)
        self.forwardButton.setToolTip(self.tr("Go Forward"))
        self.forwardButton.clicked.connect(self.navForwardRequest)

        self.editButton = NFlatIconButton(self, iSz, "edit:change")
        self.editButton.setVisible(False)
        self.editButton.setToolTip(self.tr("Open in Editor"))
        self.editButton.clicked.connect(self._editDocument)

        self.refreshButton = NFlatIconButton(self, iSz, "refresh:change")
        self.refreshButton.setVisible(False)
        self.refreshButton.setToolTip(self.tr("Reload"))
        self.refreshButton.clicked.connect(self.reloadDocumentRequest)

        # Keep the header height stable when no document is open
        self._retainSizeWhenHidden(self.closeButton)

        # Assemble
        self.outerBox.addWidget(self.outlineButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.backButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.forwardButton, 0, QtAlignMiddle)
        self.outerBox.addSpacing(4)
        self.outerBox.addWidget(self.itemTitle, 1, QtAlignMiddle)
        self.outerBox.addSpacing(4)
        self.outerBox.addWidget(self.editButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.refreshButton, 0, QtAlignMiddle)
        self.outerBox.addWidget(self.closeButton, 0, QtAlignMiddle)

        self.setLayout(self.outerBox)

        self.updateFont()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiDocViewHeader")

    ##
    #  Setters
    ##

    def setHandle(self, tHandle: str) -> None:
        """Set the document title and show the buttons."""
        super().setHandle(tHandle)
        self.backButton.setVisible(True)
        self.forwardButton.setVisible(True)
        self.outlineButton.setVisible(True)
        self.editButton.setVisible(True)
        self.refreshButton.setVisible(True)
        self.closeButton.setVisible(True)

    ##
    #  Methods
    ##

    def clearHeader(self) -> None:
        """Clear the header."""
        super().clearHeader()
        self._docOutline = {}
        self.backButton.setVisible(False)
        self.forwardButton.setVisible(False)
        self.editButton.setVisible(False)
        self.refreshButton.setVisible(False)

    def setOutline(self, data: dict[str, tuple[str, int]]) -> None:
        """Set the document outline dataset."""
        tHandle = self._docHandle
        if data != self._docOutline and tHandle:
            self.outlineMenu.clear()
            entries = []
            minLevel = 5
            for title, (text, level) in data.items():
                if title != "T0000":
                    entries.append((title, text, level))
                    minLevel = min(minLevel, level)
            for title, text, level in entries[:30]:
                indent = "    " * (level - minLevel)
                qtAddAction(self.outlineMenu, f"{indent}{elide(text, 50)}", data=f"#{tHandle}:{title}")
            self._docOutline = data

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocViewHeader")
        if not init:
            self.backButton.refreshTheme()
            self.forwardButton.refreshTheme()
            self.editButton.refreshTheme()
            self.refreshButton.refreshTheme()
        super().updateTheme(init=init)

    def updateNavButtons(self, firstIdx: int, lastIdx: int, currIdx: int) -> None:
        """Enable and disable nav buttons based on index in history."""
        self.backButton.setEnabled(currIdx > firstIdx)
        self.forwardButton.setEnabled(currIdx < lastIdx)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _editDocument(self) -> None:
        """Request the document to be opened in the editor."""
        if tHandle := self._docHandle:
            self.openDocumentRequest.emit(tHandle, nwDocMode.EDIT, "", True)

    @pyqtSlot(QAction)
    def _gotoHeader(self, action: QAction) -> None:
        """Navigate to a specific heading."""
        if isinstance(data := action.data(), str):
            self.navigateRequest.emit(data)
