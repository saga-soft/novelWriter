"""
novelWriter - GUI Project Search
================================

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

from enum import Enum
from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QModelIndex, QRect, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QCursor, QKeyEvent, QPainter, QPalette, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QToolBar,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import minmax
from novelwriter.constants import nwLabels, trConst
from novelwriter.core.projectsearch import DocSearch
from novelwriter.enum import nwChange, nwDocMode
from novelwriter.extensions.expandpanel import NExpandablePanel, NExpandablePanelGroup
from novelwriter.extensions.modified import NFlatIconButton
from novelwriter.extensions.switchbox import NSwitchBox
from novelwriter.models.searchmodel import SearchNode, SearchResultModel
from novelwriter.text.autoreplace import LineEditAutoReplace
from novelwriter.types import (
    QtAlignMiddle,
    QtDisplayRole,
    QtElideRight,
    QtHeaderStretch,
    QtHeaderToContents,
    QtHexArgb,
    QtKeyDown,
    QtKeyUp,
    QtModShift,
    QtSelected,
    QtUserRole,
    QtWidgetShortcut,
)

if TYPE_CHECKING:
    from novelwriter.core.item import ProjectItem
    from novelwriter.core.projectsearch import T_SearchResults

logger = logging.getLogger(__name__)

RESULT_FLAGS = int(Qt.TextFlag.TextSingleLine) | int(QtAlignMiddle)


class GuiProjectSearch(QWidget):
    """GUI: Project Search Panel."""

    selectedItemChanged = pyqtSignal(str)
    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    openDocumentSelectRequest = pyqtSignal(str, int, int, bool)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiProjectSearch")

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        self._search = DocSearch()
        self._model = SearchResultModel()
        self._blocked = False
        self._activeSearch = False

        self.setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRole(QPalette.ColorRole.Base)
        self.setAutoFillBackground(True)

        self.autoReplace = LineEditAutoReplace()

        # Header
        self.viewLabel = QLabel(self.tr("Project Search"), self)
        self.viewLabel.setFont(SHARED.theme.guiFontB)
        self.viewLabel.setContentsMargins(4, 4, 0, 2)

        # Options
        self.searchOpt = QToolBar(self)
        self.searchOpt.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.searchOpt.setIconSize(iSz)
        self.searchOpt.setContentsMargins(0, 0, 0, 0)

        self.tbAuto = NFlatIconButton(self, iSz, "search_auto:tool")
        self.tbAuto.setToolTip(self.tr("Auto-Replace Symbols"))
        self.tbAuto.setCheckable(True)
        self.tbAuto.setChecked(CONFIG.searchProjAuto)
        self.tbAuto.clicked.connect(self._toggleAuto)
        self.searchOpt.addWidget(self.tbAuto)

        self.tbCase = NFlatIconButton(self, iSz, "search_case:tool")
        self.tbCase.setToolTip(self.tr("Case Sensitive"))
        self.tbCase.setCheckable(True)
        self.tbCase.setChecked(CONFIG.searchProjCase)
        self.tbCase.clicked.connect(self._toggleCase)
        self.searchOpt.addWidget(self.tbCase)

        self.tbWord = NFlatIconButton(self, iSz, "search_word:tool")
        self.tbWord.setToolTip(self.tr("Whole Words Only"))
        self.tbWord.setCheckable(True)
        self.tbWord.setChecked(CONFIG.searchProjWord)
        self.tbWord.clicked.connect(self._toggleWord)
        self.searchOpt.addWidget(self.tbWord)

        self.tbRegEx = NFlatIconButton(self, iSz, "search_regex:tool")
        self.tbRegEx.setToolTip(self.tr("RegEx Mode"))
        self.tbRegEx.setCheckable(True)
        self.tbRegEx.setChecked(CONFIG.searchProjRegEx)
        self.tbRegEx.clicked.connect(self._toggleRegEx)
        self.searchOpt.addWidget(self.tbRegEx)

        # Search Box
        self.searchAction = QAction("", self)
        self.searchAction.setIcon(SHARED.theme.getIcon("search:apply"))
        self.searchAction.triggered.connect(self._processSearch)

        self.searchText = QLineEdit(self)
        self.searchText.setPlaceholderText(self.tr("Search for"))
        self.searchText.addAction(self.searchAction, QLineEdit.ActionPosition.TrailingPosition)
        self.searchText.returnPressed.connect(self._processSearch)
        self.searchText.textEdited.connect(self._editSearchText)

        # Search Filters
        self.searchFilters = _SearchFilters(self)
        self.searchFilters.setExpanded(False)

        # Search Result
        self.searchResult = QTreeView(self)
        self.searchResult.setModel(self._model)
        self.searchResult.setHeaderHidden(True)
        self.searchResult.setIconSize(iSz)
        self.searchResult.setIndentation(iPx)
        self.searchResult.setFrameStyle(QFrame.Shape.NoFrame)
        self.searchResult.setUniformRowHeights(True)
        self.searchResult.setAllColumnsShowFocus(True)
        self.searchResult.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.searchResult.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.searchResult.doubleClicked.connect(self._searchResultDoubleClicked)
        self.searchResult.setAccessibleName(self.viewLabel.text())

        self._matchDelegate = _SearchResultDelegate(self.searchResult)
        self.searchResult.setItemDelegateForColumn(SearchNode.C_NAME, self._matchDelegate)

        if header := self.searchResult.header():  # pragma: no branch
            header.setStretchLastSection(False)
            header.setSectionResizeMode(SearchNode.C_NAME, QtHeaderStretch)
            header.setSectionResizeMode(SearchNode.C_COUNT, QtHeaderToContents)

        if selModel := self.searchResult.selectionModel():  # pragma: no branch
            selModel.currentChanged.connect(self._searchResultSelected)

        # Keyboard Shortcuts
        self.keyOpenResult = QShortcut(self.searchResult)
        self.keyOpenResult.setKeys(["Return", "Enter", "Shift+Return", "Shift+Enter"])
        self.keyOpenResult.setContext(QtWidgetShortcut)
        self.keyOpenResult.activated.connect(self._openSelectedResult)

        # Assemble
        self.headerBox = QHBoxLayout()
        self.headerBox.addWidget(self.viewLabel, 1)
        self.headerBox.addWidget(self.searchOpt, 0, QtAlignMiddle)
        self.headerBox.setContentsMargins(0, 0, 0, 0)
        self.headerBox.setSpacing(0)

        self.searchSplit = NExpandablePanelGroup(self)
        self.searchSplit.addWidget(self.searchFilters)
        self.searchSplit.addWidget(self.searchResult)
        self.searchSplit.setStretchFactor(0, 0)
        self.searchSplit.setStretchFactor(1, 1)
        self.searchSplit.setPanelSizes(list(CONFIG.searchPanePos))

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.headerBox, 0)
        self.outerBox.addWidget(self.searchText, 0)
        self.outerBox.addWidget(self.searchSplit, 1)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(2)

        self.setLayout(self.outerBox)
        self.initSettings()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiProjectSearch")

    @property
    def searchObject(self) -> DocSearch:
        """Return the search object."""
        return self._search

    def splitSizes(self) -> list[int]:
        """Get the sizes of the splitter widget in its expanded state."""
        return self.searchSplit.panelSizes()

    def initSettings(self) -> None:
        """Initialise the settings."""
        self.tbAuto.setChecked(CONFIG.searchAuto if CONFIG.doReplace else False)
        self.tbAuto.setEnabled(CONFIG.doReplace)

    ##
    #  Methods
    ##

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiProjectSearch")

        palette = QApplication.palette()
        colBase = palette.base().color().name(QtHexArgb)
        colFocus = palette.highlight().color().name(QtHexArgb)

        self.searchText.setStyleSheet(
            f"QLineEdit {{border: 1px solid {colBase}; padding: 2px;}} "
            f"QLineEdit:focus {{border: 1px solid {colFocus};}} "
        )

        self.searchAction.setIcon(SHARED.theme.getIcon("search:apply"))
        self._model.updateTheme()
        self._matchDelegate.updateTheme()
        self.searchFilters.updateTheme()
        if viewport := self.searchResult.viewport():  # pragma: no branch
            viewport.update()

        if not init:
            self.tbAuto.refreshTheme()
            self.tbCase.refreshTheme()
            self.tbWord.refreshTheme()
            self.tbRegEx.refreshTheme()

    def beginSearch(self, text: str = "") -> None:
        """Focus the search box and select its text, if any."""
        self.searchText.setFocus()
        self.searchText.selectAll()
        if text:
            self.searchText.setText(text.partition("\n")[0])
            self.searchText.selectAll()

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        self.searchFilters.openProjectTasks()
        self.searchFilters.setExpanded(False)

    def closeProjectTasks(self) -> None:
        """Run close project tasks."""
        self.searchFilters.closeProjectTasks()
        self.searchFilters.setExpanded(False)
        self.searchText.clear()
        self._model.clear()
        self._activeSearch = False

    def refreshCurrentSearch(self) -> None:
        """Refresh the search if there is one."""
        if self._activeSearch:
            self._processSearch()

    ##
    #  Events
    ##

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Process key press events. This handles up and down arrow key
        presses to jump between search text box and result tree.
        """
        if event.key() == QtKeyDown and self.searchText.hasFocus() and (first := self._model.index(0, 0)).isValid():
            self.searchResult.setCurrentIndex(first)
            self.searchResult.setFocus()
        elif (
            event.key() == QtKeyUp
            and self.searchResult.hasFocus()
            and (first := self._model.index(0, 0)).isValid()
            and self.searchResult.currentIndex() == first
        ):
            self.searchResult.clearSelection()
            self.searchText.setFocus()
        else:
            super().keyPressEvent(event)

    ##
    #  Public Slots
    ##

    @pyqtSlot(str, nwChange)
    def updateRootItem(self, tHandle: str, change: nwChange) -> None:
        """Forward root item changes to the search filters."""
        self.searchFilters.updateRootItem(tHandle, change)

    @pyqtSlot(str, float)
    def textChanged(self, tHandle: str, timeStamp: float) -> None:
        """Update search result for a specific document."""
        if (entry := self._model.entry(tHandle)) and timeStamp > entry[1] and (nwItem := SHARED.project.tree[tHandle]):
            start = time()
            results, capped = self._search.searchText(SHARED.mainGui.docEditor.getText())
            self._addResult(nwItem, results, capped)
            logger.debug("Updated search for '%s' in %.3f ms", tHandle, 1000 * (time() - start))

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _openSelectedResult(self) -> None:
        """Open the currently selected search result."""
        if result := self._model.result(self.searchResult.currentIndex()):
            handle, start, length = result
            if QApplication.keyboardModifiers() == QtModShift:
                self.openDocumentRequest.emit(handle, nwDocMode.VIEW, "", True)
            else:
                self.openDocumentSelectRequest.emit(handle, start, length, False)

    @pyqtSlot()
    def _processSearch(self) -> None:
        """Perform a search. This function is re-entrant. See #2924."""
        if not self._blocked:
            self._blocked = True
            try:
                QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
                start = time()
                SHARED.saveEditor()
                searchText = self.searchText.text()

                self._model.clear()
                self._activeSearch = bool(searchText)
                if searchText:
                    self._search.setUserRegEx(self.tbRegEx.isChecked())
                    self._search.setCaseSensitive(self.tbCase.isChecked())
                    self._search.setWholeWords(self.tbWord.isChecked())
                    handles = []
                    for item, results, capped in self._search.iterSearch(SHARED.project, searchText):
                        if results:
                            self._model.setResult(item, results, capped)
                            handles.append(item.itemHandle)

                    # Run separately to avoid re-layout
                    for handle in handles:
                        self._expandResult(handle)

                logger.debug("Search took %.3f ms", 1000 * (time() - start))
                QApplication.restoreOverrideCursor()

            finally:
                self._blocked = False

    @pyqtSlot(QModelIndex, QModelIndex)
    def _searchResultSelected(self, current: QModelIndex, previous: QModelIndex) -> None:
        """Process search result selection."""
        if result := self._model.result(current):
            self.selectedItemChanged.emit(result[0])
        elif handle := self._model.handle(current):
            self.selectedItemChanged.emit(handle)

    @pyqtSlot(QModelIndex)
    def _searchResultDoubleClicked(self, index: QModelIndex) -> None:
        """Process search result double click."""
        if result := self._model.result(index):
            handle, start, length = result
            self.openDocumentSelectRequest.emit(handle, start, length, True)

    @pyqtSlot(str)
    def _editSearchText(self, text: str) -> None:
        """Update the search results when the search text changes."""
        if CONFIG.searchProjAuto:
            self.autoReplace(self.searchText)

    @pyqtSlot(bool)
    def _toggleAuto(self, state: bool) -> None:
        """Enable/disable auto-replace symbols mode."""
        CONFIG.searchProjAuto = state

    @pyqtSlot(bool)
    def _toggleCase(self, state: bool) -> None:
        """Enable/disable case sensitive mode."""
        CONFIG.searchProjCase = state
        self.refreshCurrentSearch()

    @pyqtSlot(bool)
    def _toggleWord(self, state: bool) -> None:
        """Enable/disable whole word search mode."""
        CONFIG.searchProjWord = state
        self.refreshCurrentSearch()

    @pyqtSlot(bool)
    def _toggleRegEx(self, state: bool) -> None:
        """Enable/disable regular expression search mode."""
        CONFIG.searchProjRegEx = state
        self.refreshCurrentSearch()

    ##
    #  Internal Functions
    ##

    def _addResult(self, nwItem: ProjectItem, results: T_SearchResults, capped: bool) -> None:
        """Add or update a document's results, and update the view."""
        if results:
            self._model.setResult(nwItem, results, capped)
            self._expandResult(nwItem.itemHandle)
            QApplication.processEvents()

    def _expandResult(self, handle: str) -> None:
        """Span and expand a document's rows in the result tree."""
        parent = self._model.indexFromHandle(handle)
        for row in range(self._model.rowCount(parent)):
            self.searchResult.setFirstColumnSpanned(row, parent, True)
        self.searchResult.setExpanded(parent, True)


class _SearchResultDelegate(QStyledItemDelegate):
    """GUI: Search Result Match Delegate.

    Paints the match column, highlighting the matched substring of a
    match-level row with the palette's highlight colour. Document-level
    rows have no span data and are left to the default rendering.
    """

    __slots__ = ("_rectColM", "_rectColS", "_textColP", "_textColS")

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.updateTheme()

    def updateTheme(self) -> None:
        """Refresh the cached theme colours."""
        self._textColP = QApplication.palette().text().color()
        self._textColS = QApplication.palette().highlightedText().color()
        self._rectColS = QApplication.palette().highlight().color()
        self._rectColM = SHARED.theme.searchCol

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint a search result entry, highlighting the match, if any."""
        if not isinstance(span := index.data(QtUserRole), tuple):
            super().paint(painter, option, index)
            return

        text = index.data(QtDisplayRole) or ""
        sPos, ePos = span
        rect = option.rect
        selected = bool(option.state & QtSelected)

        painter.save()
        painter.setClipRect(rect)
        painter.setFont(option.font)

        if selected:
            painter.fillRect(rect, self._rectColS)

        metrics = painter.fontMetrics()
        avail = max(0, rect.width() - 4)
        text = metrics.elidedText(text, QtElideRight, avail)
        sPos = minmax(sPos, 0, len(text))
        ePos = minmax(ePos, sPos, len(text))

        x = rect.x() + 4
        y = rect.y()
        h = rect.height()
        if ePos > sPos:
            wPos = metrics.horizontalAdvance(text[:sPos])
            wMatch = metrics.horizontalAdvance(text[sPos:ePos])
            painter.fillRect(QRect(x + wPos, y + 1, wMatch, h - 2), self._rectColM)

        painter.setPen(self._textColS if selected else self._textColP)
        painter.drawText(QRect(x, y, rect.right() - x, h), RESULT_FLAGS, text)

        painter.restore()


class _SearchFilters(NExpandablePanel):
    """GUI: Search Filters Panel."""

    def __init__(self, parent: GuiProjectSearch) -> None:
        super().__init__(parent=parent)

        self._parent = parent
        self._search = parent.searchObject

        self.setTitle(self.tr("Filters"))

        iPx = SHARED.theme.baseIconHeight

        self.filterOpt = NSwitchBox(self, baseSize=iPx)
        self.filterOpt.setMinimumHeight(4 * iPx)
        self.filterOpt.switchToggled.connect(self._buildFilterToggled)

        self.settingsBox = QVBoxLayout()
        self.settingsBox.addWidget(self.filterOpt, 0)
        self.settingsBox.setContentsMargins(0, 0, 0, 0)

        self.setContentLayout(self.settingsBox)

    ##
    #  Methods
    ##

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        self._buildFilterOptions()
        self.filterOpt.setSwitchState(SHARED.project.options.getDict("GuiProjectSearch", "searchFilters", {}))

    def closeProjectTasks(self) -> None:
        """Run close project tasks."""
        SHARED.project.options.setValue("GuiProjectSearch", "searchFilters", self.filterOpt.getSwitchState())
        self.filterOpt.clear()

    def updateTheme(self) -> None:
        """Update theme elements."""
        super().updateTheme()
        self.filterOpt.updateTheme()

    def updateRootItem(self, tHandle: str, change: nwChange) -> None:
        """Update the root folder filters when there was a change."""
        match change:
            case nwChange.CREATE | nwChange.UPDATE:
                if nwItem := SHARED.project.tree[tHandle]:
                    self._processRootFilterEntry(nwItem)
            case nwChange.DELETE:
                self.filterOpt.removeItem(f"root:{tHandle}")
            case _:  # pragma: no cover
                pass

    ##
    #  Private Slots
    ##

    @pyqtSlot(str, bool)
    def _buildFilterToggled(self, identifier: str, state: bool) -> None:
        """Handle a filter option being toggled."""
        logger.debug("Filter toggled: %s = %s", identifier, state)

        switches = self.filterOpt.getSwitchState()

        self._search.setDocumentFilters(
            novel=switches.get("docs:includeNovel", True),
            notes=switches.get("docs:includeNotes", True),
            inactive=switches.get("docs:includeInactive", True),
        )
        self._search.setContentFilters(
            headings=switches.get("text:includeHeadings", True),
            meta=switches.get("text:includeMeta", True),
            comments=switches.get("text:includeComments", True),
            body=switches.get("text:includeBody", True),
        )
        self._search.setSkipRoots([
            rIdentifier.partition(":")[2]
            for rIdentifier, rState in switches.items()
            if rIdentifier.startswith("root:") and not rState
        ])

        self._parent.refreshCurrentSearch()

    ##
    #  Internal Functions
    ##

    def _buildFilterOptions(self) -> None:
        """Build the filter options list."""
        expanded = self.isExpanded()
        self.setExpanded(False)
        self.filterOpt.clear()

        # Text Content
        self.filterOpt.addLabel(trConst(nwLabels.FILTER_GROUPS["content"]))
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["headings"]),
            "text:includeHeadings",
            icon="filter:option",
            default=True,
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["meta"]),
            "text:includeMeta",
            icon="filter:option",
            default=True,
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["comments"]),
            "text:includeComments",
            icon="filter:option",
            default=True,
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["text"]),
            "text:includeBody",
            icon="filter:option",
            default=True,
        )
        self.filterOpt.addSeparator()

        # Document Types
        self.filterOpt.addLabel(trConst(nwLabels.FILTER_GROUPS["documents"]))
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["novel"]),
            "docs:includeNovel",
            icon="prj_scene:scene",
            default=True,
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["notes"]),
            "docs:includeNotes",
            icon="prj_note:note",
            default=True,
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["inactive"]),
            "docs:includeInactive",
            icon="unchecked:reject",
            default=True,
        )
        self.filterOpt.addSeparator()

        # Root Folders
        self.filterOpt.addLabel(self.tr("Root Folders"))
        for _, nwItem in SHARED.project.tree.iterRoots(None):
            self._processRootFilterEntry(nwItem)

        self.setExpanded(expanded)

    def _processRootFilterEntry(self, nwItem: ProjectItem) -> None:
        """Append or update a root filter option."""
        if nwItem.isSearchableClass():
            self.filterOpt.addItem(
                nwItem.itemName,
                f"root:{nwItem.itemHandle}",
                icon=nwItem.getMainIconStyle(),
                default=not nwItem.isInactiveClass(),
            )
