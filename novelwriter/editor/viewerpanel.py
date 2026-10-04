"""
novelWriter - GUI Document Viewer Panel
=======================================

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

import logging

from enum import Enum
from typing import TYPE_CHECKING

from PyQt6.QtCore import QModelIndex, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QMenu,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.common import checkInt, qtAddAction
from novelwriter.constants import nwLabels, nwLists, nwStyles, trConst
from novelwriter.enum import nwChange, nwDocMode, nwItemClass
from novelwriter.extensions.modified import NFlatIconButton
from novelwriter.extensions.tabwidget import NTabWidget
from novelwriter.types import QtDecorationRole, QtHeaderFixed, QtHeaderToContents, QtUserRole

if TYPE_CHECKING:
    from novelwriter.core.indexdata import IndexHeading, IndexNode

logger = logging.getLogger(__name__)


class GuiDocViewerPanel(QWidget):
    """GUI: Document Viewer Panel.

    The panel of project meta data below the viewer.
    """

    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    loadDocumentTagRequest = pyqtSignal(str, Enum)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocViewerPanel")

        self._lastHandle = None

        iSz = SHARED.theme.baseIconSize

        self.tabBackRefs = _ViewPanelBackRefs(self)

        self.optsMenu = QMenu(self)

        self.aInactive = qtAddAction(self.optsMenu, self.tr("Hide Inactive Tags"))
        self.aInactive.setCheckable(True)
        self.aInactive.toggled.connect(self._toggleHideInactive)

        self.optsButton = NFlatIconButton(self, iSz, "more_vertical:default")
        self.optsButton.setToolTip(self.tr("Options"))
        self.optsButton.setMenu(self.optsMenu)
        self.optsButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)

        self.mainTabs = NTabWidget(self)
        self.mainTabs.addTab(self.tabBackRefs, self.tr("References"))
        self.mainTabs.setCornerWidget(self.optsButton, Qt.Corner.TopLeftCorner)

        self.kwTabs: dict[str, _ViewPanelKeyWords] = {}
        self.idTabs: dict[str, int] = {}
        for itemClass in nwLists.USER_CLASSES:
            cTab = _ViewPanelKeyWords(self, itemClass)
            tabId = self.mainTabs.addTab(cTab, trConst(nwLabels.CLASS_NAME[itemClass]))
            self.kwTabs[itemClass.name] = cTab
            self.idTabs[itemClass.name] = tabId

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.mainTabs)
        self.outerBox.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.outerBox)
        self.updateTheme(init=True)

        logger.debug("Ready: GuiDocViewerPanel")

    ##
    #  Methods
    ##

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocViewerPanel")

        self.mainTabs.refreshTheme()
        if not init:
            self.optsButton.refreshTheme()
            self.tabBackRefs.updateTheme()
            self.tabBackRefs.refreshContent(self._lastHandle)
            for tab in self.kwTabs.values():
                tab.updateTheme()
            self._loadAllTags()

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        colWidths = SHARED.project.options.getDict("GuiDocViewerPanel", "colWidths", {})
        hideInactive = SHARED.project.options.getBool("GuiDocViewerPanel", "hideInactive", False)
        self.aInactive.setChecked(hideInactive)
        if isinstance(colWidths, dict):
            for key, value in colWidths.items():
                if key in self.kwTabs and isinstance(value, list):
                    self.kwTabs[key].setColumnWidths(value)

    def closeProjectTasks(self) -> None:
        """Run close project tasks."""
        logger.debug("Saving State: GuiDocViewerPanel")
        colWidths = {k: t.getColumnWidths() for k, t in self.kwTabs.items()}
        hideInactive = self.aInactive.isChecked()
        SHARED.project.options.setValue("GuiDocViewerPanel", "colWidths", colWidths)
        SHARED.project.options.setValue("GuiDocViewerPanel", "hideInactive", hideInactive)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def indexWasCleared(self) -> None:
        """Handle event when the index has been cleared of content."""
        self.tabBackRefs.clearContent()
        for cTab in self.kwTabs.values():
            cTab.clearContent()

    @pyqtSlot()
    def indexHasAppeared(self) -> None:
        """Handle event when the index has appeared."""
        self._loadAllTags()
        self._updateTabVisibility()
        self.updateHandle(self._lastHandle)

    @pyqtSlot(str, Enum)
    def onProjectItemChanged(self, tHandle: str, change: nwChange) -> None:
        """Update meta data for project item."""
        self.tabBackRefs.refreshDocument(tHandle)
        activeOnly = self.aInactive.isChecked()
        for key in SHARED.project.index.getDocumentTags(tHandle):
            name, tClass, iItem, hItem = SHARED.project.index.getSingleTag(key)
            if tClass in self.kwTabs and iItem and hItem:
                if not activeOnly or (iItem and iItem.item.isActive):
                    self.kwTabs[tClass].addUpdateEntry(key, name, iItem, hItem)
                else:
                    self.kwTabs[tClass].removeEntry(key)
        self._updateTabVisibility()

    @pyqtSlot(str)
    def updateHandle(self, tHandle: str | None) -> None:
        """Update the document handle."""
        self._lastHandle = tHandle
        self.tabBackRefs.refreshContent(tHandle or None)

    @pyqtSlot(list, list)
    def updateChangedTags(self, updated: list[str], deleted: list[str]) -> None:
        """Forward tags changes to the lists."""
        for key in updated:
            name, tClass, iItem, hItem = SHARED.project.index.getSingleTag(key)
            if tClass in self.kwTabs and iItem and hItem:
                self.kwTabs[tClass].addUpdateEntry(key, name, iItem, hItem)
        for key in deleted:
            for cTab in self.kwTabs.values():
                if cTab.removeEntry(key):
                    break
            else:
                logger.warning("Could not remove tag '%s' from view panel", key)
        self._updateTabVisibility()

    @pyqtSlot(list)
    def updateChangedRefs(self, updated: list[str]) -> None:
        """Refresh back references when a tracked handle has changed."""
        if self._lastHandle in updated:
            self.tabBackRefs.refreshContent(self._lastHandle)

    @pyqtSlot(str)
    def updateStatusLabels(self, kind: str) -> None:
        """Update the importance labels."""
        if kind == "i":
            self._loadAllTags()

    ##
    #  Private Slots
    ##

    @pyqtSlot(bool)
    def _toggleHideInactive(self, state: bool) -> None:
        """Process toggling of active/inactive visibility."""
        logger.debug("Setting inactive items to %s", "hidden" if state else "visible")
        for cTab in self.kwTabs.values():
            cTab.clearContent()
        self._loadAllTags()
        self._updateTabVisibility()

    ##
    #  Internal Functions
    ##

    def _updateTabVisibility(self) -> None:
        """Hide class tabs with no content."""
        for tClass, cTab in self.kwTabs.items():
            self.mainTabs.setTabVisible(self.idTabs[tClass], cTab.countEntries() > 0)

    def _loadAllTags(self) -> None:
        """Load all tags into the tabs."""
        data = SHARED.project.index.getTagsData(activeOnly=self.aInactive.isChecked())
        for key, name, tClass, iItem, hItem in data:
            if tClass in self.kwTabs and iItem and hItem:
                self.kwTabs[tClass].addUpdateEntry(key, name, iItem, hItem)


class _ViewPanelBackRefs(QTreeWidget):
    C_DATA = 0
    C_DOC = 0
    C_EDIT = 1
    C_VIEW = 2
    C_TITLE = 3

    D_HANDLE = QtUserRole

    def __init__(self, parent: GuiDocViewerPanel) -> None:
        super().__init__(parent=parent)

        self._parent = parent
        self._treeMap: dict[str, QTreeWidgetItem] = {}

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        self.setHeaderLabels([self.tr("Document"), "", "", self.tr("First Heading")])
        self.setIndentation(0)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setIconSize(iSz)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        # Set Header Sizes
        if header := self.header():  # pragma: no branch
            header.setStretchLastSection(True)
            header.setMinimumSectionSize(iPx + 6)  # See Issue #1627
            header.setSectionResizeMode(self.C_DOC, QtHeaderToContents)
            header.setSectionResizeMode(self.C_EDIT, QtHeaderFixed)
            header.setSectionResizeMode(self.C_VIEW, QtHeaderFixed)
            header.setSectionResizeMode(self.C_TITLE, QtHeaderToContents)
            header.resizeSection(self.C_EDIT, iPx + 6)
            header.resizeSection(self.C_VIEW, iPx + 6)
            header.setSectionsMovable(False)

        # Cache Icons Locally
        self._editIcon = SHARED.theme.getIcon("edit:change")
        self._viewIcon = SHARED.theme.getIcon("view:action")

        # Signals
        self.clicked.connect(self._treeItemClicked)
        self.doubleClicked.connect(self._treeItemDoubleClicked)

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _ViewPanelBackRefs")

        self._editIcon = SHARED.theme.getIcon("edit:change")
        self._viewIcon = SHARED.theme.getIcon("view:action")
        for i in range(self.topLevelItemCount()):
            if item := self.topLevelItem(i):  # pragma: no branch
                item.setIcon(self.C_EDIT, self._editIcon)
                item.setIcon(self.C_VIEW, self._viewIcon)

    def clearContent(self) -> None:
        """Clear the widget."""
        self.clear()
        self._treeMap = {}

    def refreshContent(self, dHandle: str | None) -> None:
        """Update the content."""
        self.clearContent()
        if dHandle:
            refs = SHARED.project.index.getBackReferenceList(dHandle)
            for tHandle, (sTitle, hItem) in refs.items():
                self._setTreeItemValues(tHandle, sTitle, hItem)

    def refreshDocument(self, tHandle: str) -> None:
        """Refresh document meta data."""
        if iItem := SHARED.project.index.getItemData(tHandle):
            for sTitle, hItem in iItem.items():
                if f"{tHandle}:{sTitle}" in self._treeMap:
                    self._setTreeItemValues(tHandle, sTitle, hItem)

    ##
    #  Private Slots
    ##

    @pyqtSlot("QModelIndex")
    def _treeItemClicked(self, index: QModelIndex) -> None:
        """Emit document open signal on user click."""
        tHandle = index.siblingAtColumn(self.C_DATA).data(self.D_HANDLE)
        if index.column() == self.C_EDIT:
            self._parent.openDocumentRequest.emit(tHandle, nwDocMode.EDIT, "", True)
        elif index.column() == self.C_VIEW:
            self._parent.openDocumentRequest.emit(tHandle, nwDocMode.VIEW, "", True)

    @pyqtSlot("QModelIndex")
    def _treeItemDoubleClicked(self, index: QModelIndex) -> None:
        """Emit follow tag signal on user double click."""
        tHandle = index.siblingAtColumn(self.C_DATA).data(self.D_HANDLE)
        if index.column() not in (self.C_EDIT, self.C_VIEW):
            self._parent.openDocumentRequest.emit(tHandle, nwDocMode.VIEW, "", True)

    ##
    #  Internal Functions
    ##

    def _setTreeItemValues(self, tHandle: str, sTitle: str, hItem: IndexHeading) -> None:
        """Add or update a tree item."""
        if nwItem := SHARED.project.tree[tHandle]:
            iLevel = nwStyles.H_LEVEL.get(hItem.level, 0) if nwItem.isDocumentLayout() else 5
            hDec = SHARED.theme.getHeaderDecorationNarrow(iLevel)

            tKey = f"{tHandle}:{sTitle}"
            trItem = self._treeMap[tKey] if tKey in self._treeMap else QTreeWidgetItem()

            trItem.setIcon(self.C_DOC, nwItem.getMainIcon())
            trItem.setText(self.C_DOC, nwItem.itemName)
            trItem.setToolTip(self.C_DOC, nwItem.itemName)
            trItem.setIcon(self.C_EDIT, self._editIcon)
            trItem.setIcon(self.C_VIEW, self._viewIcon)
            trItem.setData(self.C_TITLE, QtDecorationRole, hDec)
            trItem.setText(self.C_TITLE, hItem.title)
            trItem.setToolTip(self.C_TITLE, hItem.title)
            trItem.setData(self.C_DATA, self.D_HANDLE, tHandle)

            if tKey not in self._treeMap:
                self.addTopLevelItem(trItem)
                self._treeMap[tKey] = trItem


class _ViewPanelKeyWords(QTreeWidget):
    C_DATA = 0
    C_NAME = 0
    C_EDIT = 1
    C_VIEW = 2
    C_IMPORT = 3
    C_DOC = 4
    C_TITLE = 5
    C_SHORT = 6

    D_TAG = QtUserRole

    def __init__(self, parent: GuiDocViewerPanel, itemClass: nwItemClass) -> None:
        super().__init__(parent=parent)

        self._parent = parent
        self._class = itemClass
        self._treeMap: dict[str, QTreeWidgetItem] = {}

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        self.setHeaderLabels([
            self.tr("Tag"),
            "",
            "",
            self.tr("Importance"),
            self.tr("Document"),
            self.tr("Heading"),
            self.tr("Short Description"),
        ])
        self.setIndentation(0)
        self.setIconSize(iSz)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setExpandsOnDoubleClick(False)
        self.setDragEnabled(False)
        self.setSortingEnabled(True)
        self.sortByColumn(self.C_NAME, Qt.SortOrder.AscendingOrder)

        # Set Header Sizes
        if header := self.header():  # pragma: no branch
            header.setStretchLastSection(True)
            header.setMinimumSectionSize(iPx + 6)  # See Issue #1627
            header.setSectionResizeMode(self.C_EDIT, QtHeaderFixed)
            header.setSectionResizeMode(self.C_VIEW, QtHeaderFixed)
            header.resizeSection(self.C_EDIT, iPx + 6)
            header.resizeSection(self.C_VIEW, iPx + 6)
            header.setSectionsMovable(False)

        # Cache Icons Locally
        self.updateTheme()

        # Signals
        self.clicked.connect(self._treeItemClicked)
        self.doubleClicked.connect(self._treeItemDoubleClicked)

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _ViewPanelKeyWords")

        self._classIcon = SHARED.theme.getIcon(nwLabels.CLASS_ICON[self._class])
        self._editIcon = SHARED.theme.getIcon("edit:change")
        self._viewIcon = SHARED.theme.getIcon("view:action")

    def countEntries(self) -> int:
        """Return the number of items in the list."""
        return self.topLevelItemCount()

    def clearContent(self) -> None:
        """Clear the list."""
        self._treeMap = {}
        self.clear()

    def addUpdateEntry(self, tag: str, name: str, iItem: IndexNode, hItem: IndexHeading) -> None:
        """Add a new entry, or update an existing one."""
        nwItem = iItem.item
        impLabel, impIcon = nwItem.getImportStatus()
        iLevel = nwStyles.H_LEVEL.get(hItem.level, 0) if nwItem.isDocumentLayout() else 5
        hDec = SHARED.theme.getHeaderDecorationNarrow(iLevel)

        # This can not use a get call to the dictionary as that would create an
        # instance of the QTreeWidgetItem, which has some weird side effects
        trItem = self._treeMap[tag] if tag in self._treeMap else QTreeWidgetItem()

        trItem.setIcon(self.C_NAME, self._classIcon)
        trItem.setText(self.C_NAME, name)
        trItem.setToolTip(self.C_NAME, name)
        trItem.setIcon(self.C_EDIT, self._editIcon)
        trItem.setIcon(self.C_VIEW, self._viewIcon)
        trItem.setIcon(self.C_IMPORT, impIcon)
        trItem.setText(self.C_IMPORT, impLabel)
        trItem.setToolTip(self.C_IMPORT, impLabel)
        trItem.setIcon(self.C_DOC, nwItem.getMainIcon())
        trItem.setText(self.C_DOC, nwItem.itemName)
        trItem.setToolTip(self.C_DOC, nwItem.itemName)
        trItem.setData(self.C_TITLE, QtDecorationRole, hDec)
        trItem.setText(self.C_TITLE, hItem.title)
        trItem.setToolTip(self.C_TITLE, hItem.title)
        trItem.setText(self.C_SHORT, hItem.synopsis)
        trItem.setToolTip(self.C_SHORT, hItem.synopsis)
        trItem.setData(self.C_DATA, self.D_TAG, tag)

        if tag not in self._treeMap:
            self.addTopLevelItem(trItem)
            self._treeMap[tag] = trItem

    def removeEntry(self, tag: str) -> bool:
        """Remove a tag from the list."""
        if tag in self._treeMap:
            self.takeTopLevelItem(self.indexOfTopLevelItem(self._treeMap[tag]))
            self._treeMap.pop(tag, None)
            return True
        return False

    def setColumnWidths(self, widths: list[int]) -> None:
        """Set the column widths."""
        if isinstance(widths, list) and len(widths) >= 4:
            self.setColumnWidth(self.C_NAME, checkInt(widths[0], 100))
            self.setColumnWidth(self.C_IMPORT, checkInt(widths[1], 100))
            self.setColumnWidth(self.C_DOC, checkInt(widths[2], 100))
            self.setColumnWidth(self.C_TITLE, checkInt(widths[3], 100))

    def getColumnWidths(self) -> list[int]:
        """Get the widths of the user-adjustable columns."""
        return [
            self.columnWidth(self.C_NAME),
            self.columnWidth(self.C_IMPORT),
            self.columnWidth(self.C_DOC),
            self.columnWidth(self.C_TITLE),
        ]

    ##
    #  Private Slots
    ##

    @pyqtSlot("QModelIndex")
    def _treeItemClicked(self, index: QModelIndex) -> None:
        """Emit follow tag signal on user click."""
        tag = index.siblingAtColumn(self.C_DATA).data(self.D_TAG)
        if index.column() == self.C_EDIT:
            self._parent.loadDocumentTagRequest.emit(tag, nwDocMode.EDIT)
        elif index.column() == self.C_VIEW:
            self._parent.loadDocumentTagRequest.emit(tag, nwDocMode.VIEW)

    @pyqtSlot("QModelIndex")
    def _treeItemDoubleClicked(self, index: QModelIndex) -> None:
        """Emit follow tag signal on user double click."""
        tag = index.siblingAtColumn(self.C_DATA).data(self.D_TAG)
        if index.column() not in (self.C_EDIT, self.C_VIEW):
            self._parent.loadDocumentTagRequest.emit(tag, nwDocMode.VIEW)
