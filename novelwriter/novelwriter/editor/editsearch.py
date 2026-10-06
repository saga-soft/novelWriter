"""
novelWriter - GUI Editor Search
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

from PyQt6.QtCore import QEvent, QObject, QRegularExpression, pyqtSlot
from PyQt6.QtGui import QKeyEvent, QPalette
from PyQt6.QtWidgets import QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit

from novelwriter import CONFIG, SHARED
from novelwriter.constants import nwConst
from novelwriter.extensions.modified import NFlatIconButton
from novelwriter.text.autoreplace import LineEditAutoReplace
from novelwriter.types import QtKeyEscape, QtModShift

if TYPE_CHECKING:
    from novelwriter.editor.editor import GuiDocEditor

logger = logging.getLogger(__name__)


class GuiDocEditSearch(QFrame):
    """The Embedded Document Search/Replace Feature.

    Only used by DocEditor, and is at a fixed position in the
    QTextEdit's viewport.
    """

    def __init__(self, docEditor: GuiDocEditor) -> None:
        super().__init__(parent=docEditor)

        logger.debug("Create: GuiDocEditSearch")

        self.docEditor = docEditor

        iSz = SHARED.theme.baseIconSize

        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Plain)

        self.mainBox = QGridLayout(self)
        self.setLayout(self.mainBox)

        # Text Boxes
        # ==========

        self.autoReplace = LineEditAutoReplace()

        self.searchBox = QLineEdit(self)
        self.searchBox.setPlaceholderText(self.tr("Search for"))
        self.searchBox.returnPressed.connect(self._doSearch)
        self.searchBox.textEdited.connect(self._editSearchText)
        self.searchBox.installEventFilter(self)

        self.replaceBox = QLineEdit(self)
        self.replaceBox.setPlaceholderText(self.tr("Replace with"))
        self.replaceBox.returnPressed.connect(self._doReplace)
        self.replaceBox.textEdited.connect(self._editReplaceText)
        self.replaceBox.installEventFilter(self)

        self.resultLabel = QLabel("?/?", self)

        self.tbAuto = NFlatIconButton(self, iSz, "search_auto:tool")
        self.tbAuto.setToolTip(self.tr("Auto-Replace Symbols"))
        self.tbAuto.setCheckable(True)
        self.tbAuto.clicked.connect(self._doToggleAuto)
        self.setAutoReplaceEnabled(CONFIG.doReplace)

        self.tbCase = NFlatIconButton(self, iSz, "search_case:tool")
        self.tbCase.setToolTip(self.tr("Case Sensitive"))
        self.tbCase.setCheckable(True)
        self.tbCase.setChecked(CONFIG.searchCase)
        self.tbCase.clicked.connect(self._doToggleCase)

        self.tbWord = NFlatIconButton(self, iSz, "search_word:tool")
        self.tbWord.setToolTip(self.tr("Whole Words Only"))
        self.tbWord.setCheckable(True)
        self.tbWord.setChecked(CONFIG.searchWord)
        self.tbWord.clicked.connect(self._doToggleWord)

        self.tbRegEx = NFlatIconButton(self, iSz, "search_regex:tool")
        self.tbRegEx.setToolTip(self.tr("RegEx Mode"))
        self.tbRegEx.setCheckable(True)
        self.tbRegEx.setChecked(CONFIG.searchRegEx)
        self.tbRegEx.clicked.connect(self._doToggleRegEx)

        self.tbLoop = NFlatIconButton(self, iSz, "search_loop:tool")
        self.tbLoop.setToolTip(self.tr("Loop Search"))
        self.tbLoop.setCheckable(True)
        self.tbLoop.setChecked(CONFIG.searchLoop)
        self.tbLoop.clicked.connect(self._doToggleLoop)

        self.tbProject = NFlatIconButton(self, iSz, "search_project:tool")
        self.tbProject.setToolTip(self.tr("Search Next File"))
        self.tbProject.setCheckable(True)
        self.tbProject.setChecked(CONFIG.searchNextFile)
        self.tbProject.clicked.connect(self._doToggleProject)

        self.tbMatchCap = NFlatIconButton(self, iSz, "search_preserve:tool")
        self.tbMatchCap.setToolTip(self.tr("Preserve Case"))
        self.tbMatchCap.setCheckable(True)
        self.tbMatchCap.setChecked(CONFIG.searchMatchCap)
        self.tbMatchCap.clicked.connect(self._doToggleMatchCap)

        self.tbCancel = NFlatIconButton(self, iSz, "search_cancel:tool")
        self.tbCancel.setToolTip(self.tr("Close Search"))
        self.tbCancel.clicked.connect(self.closeSearch)

        # Buttons
        # =======

        self.showReplace = NFlatIconButton(self, iSz, "toggle-unfold:default")
        self.showReplace.toggled.connect(self._doToggleReplace)

        self.searchButton = NFlatIconButton(self, iSz, "search:action")
        self.searchButton.setToolTip(self.tr("Find in current document"))
        self.searchButton.clicked.connect(self._doSearch)

        self.replaceButton = NFlatIconButton(self, iSz, "search_replace:apply")
        self.replaceButton.setToolTip(self.tr("Find and replace in current document"))
        self.replaceButton.clicked.connect(self._doReplace)

        # Assemble
        # ========

        self.searchOpt = QHBoxLayout()
        self.searchOpt.addWidget(self.tbAuto)
        self.searchOpt.addWidget(self.tbCase)
        self.searchOpt.addWidget(self.tbWord)
        self.searchOpt.addWidget(self.tbRegEx)
        self.searchOpt.addWidget(self.tbLoop)
        self.searchOpt.addWidget(self.tbProject)
        self.searchOpt.addWidget(self.tbMatchCap)
        self.searchOpt.addStretch(1)
        self.searchOpt.addWidget(self.tbCancel)
        self.searchOpt.setContentsMargins(0, 0, 0, 0)

        self.mainBox.addLayout(self.searchOpt, 0, 1, 1, 3)
        self.mainBox.addWidget(self.showReplace, 1, 0, 1, 1)
        self.mainBox.addWidget(self.searchBox, 1, 1, 1, 1)
        self.mainBox.addWidget(self.searchButton, 1, 2, 1, 1)
        self.mainBox.addWidget(self.resultLabel, 1, 3, 1, 1)
        self.mainBox.addWidget(self.replaceBox, 2, 1, 1, 1)
        self.mainBox.addWidget(self.replaceButton, 2, 2, 1, 1)

        self.mainBox.setColumnStretch(0, 0)
        self.mainBox.setColumnStretch(1, 0)
        self.mainBox.setColumnStretch(2, 1)
        self.mainBox.setColumnStretch(3, 0)
        self.mainBox.setSpacing(2)
        self.mainBox.setContentsMargins(6, 6, 6, 6)

        self.searchBox.setFixedWidth(200)
        self.replaceBox.setFixedWidth(200)
        self.replaceBox.setVisible(False)
        self.replaceButton.setVisible(False)
        self.adjustSize()

        self.updateFont()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiDocEditSearch")

    ##
    #  Properties
    ##

    @property
    def searchText(self) -> str:
        """Return the current search text."""
        return self.searchBox.text()

    @property
    def replaceText(self) -> str:
        """Return the current replace text."""
        return self.replaceBox.text()

    ##
    #  Getters
    ##

    def getSearchObject(self) -> str | QRegularExpression:
        """Return the current search text either as text or as a regular
        expression object.
        """
        text = self.searchBox.text()
        if CONFIG.searchRegEx:
            rxOpt = QRegularExpression.PatternOption.UseUnicodePropertiesOption
            if not CONFIG.searchCase:
                rxOpt |= QRegularExpression.PatternOption.CaseInsensitiveOption
            regEx = QRegularExpression(text, rxOpt)
            self._alertSearchValid(regEx.isValid())
            return regEx
        return text

    ##
    #  Setters
    ##

    def setSearchText(self, text: str | None) -> None:
        """Open the search bar and set the search text to the text
        provided, if any.
        """
        if not self.isVisible():
            self.setVisible(True)
        if text is not None:
            self.searchBox.setText(text)
        self.searchBox.setFocus()
        self.searchBox.selectAll()
        if CONFIG.searchRegEx:
            self._alertSearchValid(True)

    def setReplaceText(self, text: str) -> None:
        """Set the replace text."""
        self.showReplace.setChecked(True)
        self.replaceBox.setFocus()
        self.replaceBox.setText(text)

    def setResultCount(self, currRes: int | None, resCount: int | None) -> None:
        """Set the count values for the current search."""
        lim = nwConst.MAX_SEARCH_RESULT
        numCount = f"{lim:n}+" if (resCount or 0) > lim else f"{resCount:n}"
        sCurrRes = "?" if currRes is None else str(currRes)
        sResCount = "?" if resCount is None else numCount
        widthRef = "0" * max(2 * len(sResCount) + 1, 5)
        minWidth = SHARED.theme.getTextWidth(widthRef, SHARED.theme.guiFontSmall)
        self.resultLabel.setText(f"{sCurrRes}/{sResCount}")
        self.resultLabel.setMinimumWidth(minWidth)
        self.adjustSize()
        self.docEditor.updateDocMargins()

    def setAutoReplaceEnabled(self, state: bool) -> None:
        """Enable/disable auto-replace mode."""
        self.tbAuto.setChecked(CONFIG.searchAuto if state else False)
        self.tbAuto.setEnabled(state)

    ##
    #  Methods
    ##

    def updateFont(self) -> None:
        """Update the font settings."""
        self.setFont(SHARED.theme.guiFont)
        self.searchBox.setFont(SHARED.theme.guiFontSmall)
        self.replaceBox.setFont(SHARED.theme.guiFontSmall)
        self.resultLabel.setFont(SHARED.theme.guiFontSmall)
        self.resultLabel.setMinimumWidth(SHARED.theme.getTextWidth("?/?", SHARED.theme.guiFontSmall))

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocEditSearch")

        palette = QApplication.palette()
        self.setPalette(palette)
        self.searchBox.setPalette(palette)
        self.replaceBox.setPalette(palette)

        # Set icons
        if not init:
            self.tbAuto.refreshTheme()
            self.tbCase.refreshTheme()
            self.tbWord.refreshTheme()
            self.tbRegEx.refreshTheme()
            self.tbLoop.refreshTheme()
            self.tbProject.refreshTheme()
            self.tbMatchCap.refreshTheme()
            self.tbCancel.refreshTheme()
            self.searchButton.refreshTheme()
            self.replaceButton.refreshTheme()
            self.showReplace.refreshTheme()

    def cycleFocus(self) -> bool:
        """Cycle focus on tab key press. This just alternates focus
        between the two input boxes, if the replace box is visible.
        """
        if self.searchBox.hasFocus():
            self.replaceBox.setFocus()
            return True
        elif self.replaceBox.hasFocus():
            self.searchBox.setFocus()
            return True
        return False

    def anyFocus(self) -> bool:
        """Return True if any of the input boxes have focus."""
        return self.hasFocus() or self.isAncestorOf(QApplication.focusWidget())

    ##
    #  Events and Overloads
    ##

    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        """Close the search box on Escape while either input box has
        focus. GuiDocEditor.keyPressEvent handles Escape for the
        editor itself, but doesn't see key events sent directly to
        these child line edits.
        """
        if (
            event is not None
            and event.type() == QEvent.Type.KeyPress
            and isinstance(event, QKeyEvent)
            and event.key() == QtKeyEscape
        ):
            self.closeSearch()
            return True
        return super().eventFilter(obj, event)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def closeSearch(self) -> None:
        """Close the search box."""
        self.showReplace.setChecked(False)
        self.setVisible(False)
        self.docEditor.clearSearchSelections()
        self.docEditor.updateDocMargins()
        self.docEditor.setFocus()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _doSearch(self) -> None:
        """Call the search action function for the document editor."""
        self.docEditor.findNext(goBack=(QApplication.keyboardModifiers() == QtModShift))

    @pyqtSlot()
    def _doReplace(self) -> None:
        """Call the replace action function for the document editor."""
        self.docEditor.replaceNext()

    @pyqtSlot(str)
    def _editSearchText(self, text: str) -> None:
        """Update the search results when the search text changes."""
        if CONFIG.doReplace and CONFIG.searchAuto:
            self.autoReplace(self.searchBox)

    @pyqtSlot(str)
    def _editReplaceText(self, text: str) -> None:
        """Update the replace box when the text changes."""
        if CONFIG.doReplace and CONFIG.searchAuto:
            self.autoReplace(self.replaceBox)

    @pyqtSlot(bool)
    def _doToggleReplace(self, state: bool) -> None:
        """Toggle the show/hide of the replace box."""
        self.replaceBox.setVisible(state)
        self.replaceButton.setVisible(state)
        self.adjustSize()
        self.docEditor.updateDocMargins()

    @pyqtSlot(bool)
    def _doToggleAuto(self, state: bool) -> None:
        """Enable/disable auto-replace mode."""
        CONFIG.searchAuto = state

    @pyqtSlot(bool)
    def _doToggleCase(self, state: bool) -> None:
        """Enable/disable case sensitive mode."""
        CONFIG.searchCase = state

    @pyqtSlot(bool)
    def _doToggleWord(self, state: bool) -> None:
        """Enable/disable whole word search mode."""
        CONFIG.searchWord = state

    @pyqtSlot(bool)
    def _doToggleRegEx(self, state: bool) -> None:
        """Enable/disable regular expression search mode."""
        CONFIG.searchRegEx = state

    @pyqtSlot(bool)
    def _doToggleLoop(self, state: bool) -> None:
        """Enable/disable looping the search."""
        CONFIG.searchLoop = state

    @pyqtSlot(bool)
    def _doToggleProject(self, state: bool) -> None:
        """Enable/disable continuing search in next project file."""
        CONFIG.searchNextFile = state

    @pyqtSlot(bool)
    def _doToggleMatchCap(self, state: bool) -> None:
        """Enable/disable preserving capitalisation when replacing."""
        CONFIG.searchMatchCap = state

    ##
    #  Internal Functions
    ##

    def _alertSearchValid(self, isValid: bool) -> None:
        """Highlight the search box to indicate the search string is or
        isn't valid. Take the colour from the replace box.
        """
        palette = self.replaceBox.palette()
        palette.setColor(QPalette.ColorRole.Text, palette.text().color() if isValid else SHARED.theme.errorText)
        self.searchBox.setPalette(palette)
