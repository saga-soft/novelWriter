"""
novelWriter - GUI Project Tree
==============================

This file is a part of novelWriter
Copyright (C) 2018 Veronica Berglyd Olsen and novelWriter contributors

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

from contextlib import suppress
from enum import Enum

from PyQt6.QtCore import QModelIndex, QPoint, Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QMouseEvent, QPainter, QPalette, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QStyleOptionViewItem,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import elide, qtAddAction, qtAddMenu, qtLambda, qtWeakLambda
from novelwriter.constants import nwLabels, nwStyles, nwUnicode, trConst
from novelwriter.core.coretools import DocDuplicator, DocMerger, DocSplitter
from novelwriter.core.item import ProjectItem
from novelwriter.dialogs.docmerge import GuiDocMerge
from novelwriter.dialogs.docsplit import GuiDocSplit
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.dialogs.projectsettings import GuiProjectSettings
from novelwriter.enum import nwChange, nwDocMode, nwItemClass, nwItemLayout, nwItemType
from novelwriter.extensions.modified import NFlatIconButton
from novelwriter.models.itemmodel import ProjectModel, ProjectNode
from novelwriter.types import (
    QtHeaderFixed,
    QtHeaderStretch,
    QtHeaderToContents,
    QtModShift,
    QtMouseLeft,
    QtMouseMiddle,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSizeExpanding,
    QtWidgetShortcut,
)

logger = logging.getLogger(__name__)


class GuiProjectView(QWidget):
    """GUI: Project View.

    This is a wrapper class holding all the elements of the project
    tree. The core object is the project tree itself. Most methods
    available are mapped through to the project tree class.
    """

    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    projectSettingsRequest = pyqtSignal(int)
    selectedItemChanged = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        # Build GUI
        self.projTree = GuiProjectTree(self)
        self.projBar = GuiProjectToolBar(self)
        self.projBar.setEnabled(False)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.projBar, 0)
        self.outerBox.addWidget(self.projTree, 1)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)

        # Keyboard Shortcuts
        self.keyMoveUp = QShortcut(self.projTree)
        self.keyMoveUp.setKey("Ctrl+Up")
        self.keyMoveUp.setContext(QtWidgetShortcut)
        self.keyMoveUp.activated.connect(self.projTree.moveItemUp)

        self.keyMoveDn = QShortcut(self.projTree)
        self.keyMoveDn.setKey("Ctrl+Down")
        self.keyMoveDn.setContext(QtWidgetShortcut)
        self.keyMoveDn.activated.connect(self.projTree.moveItemDown)

        self.keyGoPrev = QShortcut(self.projTree)
        self.keyGoPrev.setKey("Alt+Up")
        self.keyGoPrev.setContext(QtWidgetShortcut)
        self.keyGoPrev.activated.connect(self.projTree.goToSiblingUp)

        self.keyGoNext = QShortcut(self.projTree)
        self.keyGoNext.setKey("Alt+Down")
        self.keyGoNext.setContext(QtWidgetShortcut)
        self.keyGoNext.activated.connect(self.projTree.goToSiblingDown)

        self.keyGoUp = QShortcut(self.projTree)
        self.keyGoUp.setKey("Alt+Left")
        self.keyGoUp.setContext(QtWidgetShortcut)
        self.keyGoUp.activated.connect(self.projTree.goToParent)

        self.keyGoDown = QShortcut(self.projTree)
        self.keyGoDown.setKey("Alt+Right")
        self.keyGoDown.setContext(QtWidgetShortcut)
        self.keyGoDown.activated.connect(self.projTree.goToFirstChild)

        self.keyContext = QShortcut(self.projTree)
        self.keyContext.setKey("Ctrl+.")
        self.keyContext.setContext(QtWidgetShortcut)
        self.keyContext.activated.connect(self.projTree.openContextMenu)

        self.keyOpenItem = QShortcut(self.projTree)
        self.keyOpenItem.setKeys(["Return", "Enter", "Shift+Return", "Shift+Enter"])
        self.keyOpenItem.setContext(QtWidgetShortcut)
        self.keyOpenItem.activated.connect(self.projTree.openSelectedItem)

        # Signals
        self.selectedItemChanged.connect(self.projBar.treeSelectionChanged)
        self.projBar.newDocumentFromTemplate.connect(self.createFileFromTemplate)

        # Function Mappings
        self.getSelectedHandle = self.projTree.getSelectedHandle

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiProjectView")
        self.projBar.updateTheme()

    def initViewport(self) -> None:
        """Initialise viewport settings."""
        self.projTree.initViewport()

    def closeProjectTasks(self) -> None:
        """Clear project-related GUI content."""
        self.projBar.clearContent()
        self.projBar.setEnabled(False)
        self.projTree.clearTree()

    def openProjectTasks(self) -> None:
        """Run open project tasks."""
        self.projTree.loadModel()
        self.projBar.buildTemplatesMenu()
        self.projBar.buildQuickLinksMenu()
        self.projBar.setEnabled(True)

    def setTreeFocus(self) -> None:
        """Forward the set focus call to the tree widget."""
        self.projTree.setFocus()

    def treeHasFocus(self) -> bool:
        """Check if the project tree has focus."""
        return self.projTree.hasFocus()

    def connectMenuActions(self, rename: QAction, delete: QAction, trash: QAction) -> None:
        """Connect main menu actions passed to the project tree."""
        self.projTree.addAction(rename)
        self.projTree.addAction(delete)
        self.projTree.addAction(trash)
        rename.triggered.connect(self.renameTreeItem)
        delete.triggered.connect(self.projTree.processDeleteRequest)
        trash.triggered.connect(self.projTree.emptyTrash)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    @pyqtSlot(str, str)
    def renameTreeItem(self, tHandle: str | None = None, name: str = "") -> None:
        """External request to rename an item or the currently selected
        item. This is triggered by the global menu or keyboard shortcut.
        """
        if tHandle is None:
            tHandle = self.projTree.getSelectedHandle()
        if nwItem := SHARED.project.tree[tHandle]:
            newLabel, dlgOk = GuiEditLabel.getLabel(self, text=name or nwItem.itemName)
            if dlgOk:
                nwItem.setName(newLabel)
                nwItem.notifyToRefresh()

    @pyqtSlot(str, bool)
    def setSelectedHandle(self, tHandle: str, doScroll: bool = False) -> None:
        """Select an item and optionally scroll it into view."""
        self.projTree.setSelectedHandle(tHandle, doScroll=doScroll)

    @pyqtSlot(str)
    def setActiveHandle(self, tHandle: str | None) -> None:
        """Highlight the active handle."""
        self.projTree.setActiveHandle(tHandle)

    @pyqtSlot(str, Enum)
    def onProjectItemChanged(self, tHandle: str, change: nwChange) -> None:
        """Refresh other content when project item changed."""
        self.projBar.processTemplateDocuments(tHandle)

    @pyqtSlot(str)
    def createFileFromTemplate(self, tHandle: str) -> None:
        """Create a new document from a template."""
        logger.debug("Template selected: '%s'", tHandle)
        self.projTree.newTreeItem(nwItemType.FILE, copyDoc=tHandle)

    @pyqtSlot(str, Enum)
    def updateRootItem(self, tHandle: str, change: nwChange) -> None:
        """Process root item changes."""
        self.projBar.buildQuickLinksMenu()


class GuiProjectToolBar(QWidget):
    """GUI> Project View ToolBar."""

    newDocumentFromTemplate = pyqtSignal(str)

    def __init__(self, projView: GuiProjectView) -> None:
        super().__init__(parent=projView)

        logger.debug("Create: GuiProjectToolBar")

        self.projView = projView
        self.projTree = projView.projTree

        iSz = SHARED.theme.baseIconSize

        self.setContentsMargins(0, 0, 0, 0)
        self.setBackgroundRole(QPalette.ColorRole.Base)
        self.setAutoFillBackground(True)

        # Widget Label
        self.viewLabel = QLabel(self.tr("Project Content"), self)
        self.viewLabel.setFont(SHARED.theme.guiFontB)
        self.viewLabel.setContentsMargins(0, 0, 0, 0)
        self.viewLabel.setSizePolicy(QtSizeExpanding, QtSizeExpanding)
        self.projTree.setAccessibleName(self.viewLabel.text())

        # Quick Links
        self.mQuick = QMenu(self)
        self.mQuick.triggered.connect(self._onQuickLinkSelected)

        self.tbQuick = NFlatIconButton(self, iSz, "bookmarks:action")
        self.tbQuick.setToolTip("{0} [Ctrl+L]".format(self.tr("Quick Links")))
        self.tbQuick.setShortcut("Ctrl+L")
        self.tbQuick.setMenu(self.mQuick)

        # Move Buttons
        self.tbMoveU = NFlatIconButton(self, iSz, "chevron_up:action")
        self.tbMoveU.setToolTip("{0} [Ctrl+Up]".format(self.tr("Move Up")))
        self.tbMoveU.clicked.connect(self.projTree.moveItemUp)

        self.tbMoveD = NFlatIconButton(self, iSz, "chevron_down:action")
        self.tbMoveD.setToolTip("{0} [Ctrl+Down]".format(self.tr("Move Down")))
        self.tbMoveD.clicked.connect(self.projTree.moveItemDown)

        # Add Item Menu
        self.mAdd = QMenu(self)

        self.aAddScene = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["doc_h3"]))
        self.aAddScene.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FILE, hLevel=3, isNote=False))

        self.aAddChap = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["doc_h2"]))
        self.aAddChap.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FILE, hLevel=2, isNote=False))

        self.aAddPart = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["doc_h1"]))
        self.aAddPart.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FILE, hLevel=1, isNote=False))

        self.aAddEmpty = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["document"]))
        self.aAddEmpty.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FILE, hLevel=0, isNote=False))

        self.aAddNote = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["note"]))
        self.aAddNote.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FILE, hLevel=1, isNote=True))

        self.aAddFolder = qtAddAction(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["folder"]))
        self.aAddFolder.triggered.connect(qtLambda(self.projTree.newTreeItem, nwItemType.FOLDER))

        self.mTemplates = _UpdatableMenu(self.mAdd)
        self.mTemplates.setActionsVisible(False)
        self.mTemplates.menuItemTriggered.connect(self._forwardTemplateTriggered)
        self.mAdd.addMenu(self.mTemplates)

        self.mAddRoot = qtAddMenu(self.mAdd, trConst(nwLabels.ITEM_DESCRIPTION["root"]))
        self.mAddRoot.triggered.connect(self._onAddRootSelected)
        self._buildRootMenu()

        self.tbAdd = NFlatIconButton(self, iSz, "add:add")
        self.tbAdd.setToolTip("{0} [Ctrl+N]".format(self.tr("Add Item")))
        self.tbAdd.setShortcut("Ctrl+N")
        self.tbAdd.setMenu(self.mAdd)

        # More Options Menu
        self.mMore = QMenu(self)

        self.aExpand = qtAddAction(self.mMore, self.tr("Expand All"))
        self.aExpand.triggered.connect(self.projTree.expandAll)

        self.aCollapse = qtAddAction(self.mMore, self.tr("Collapse All"))
        self.aCollapse.triggered.connect(self.projTree.collapseAll)

        self.aEmptyTrash = qtAddAction(self.mMore, self.tr("Empty Trash"))
        self.aEmptyTrash.triggered.connect(self.projTree.emptyTrash)

        self.tbMore = NFlatIconButton(self, iSz, "more_vertical:default")
        self.tbMore.setToolTip(self.tr("More Options"))
        self.tbMore.setMenu(self.mMore)

        # Assemble
        self.outerBox = QHBoxLayout()
        self.outerBox.addWidget(self.viewLabel)
        self.outerBox.addWidget(self.tbQuick)
        self.outerBox.addWidget(self.tbMoveU)
        self.outerBox.addWidget(self.tbMoveD)
        self.outerBox.addWidget(self.tbAdd)
        self.outerBox.addWidget(self.tbMore)
        self.outerBox.setContentsMargins(4, 2, 0, 2)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)
        self.updateTheme(init=True)

        logger.debug("Ready: GuiProjectToolBar")

    ##
    #  Methods
    ##

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiProjectToolBar")

        if not init:
            self.tbQuick.refreshTheme()
            self.tbMoveU.refreshTheme()
            self.tbMoveD.refreshTheme()
            self.tbAdd.refreshTheme()
            self.tbMore.refreshTheme()

        self.aAddScene.setIcon(SHARED.theme.getIcon("prj_scene:scene"))
        self.aAddChap.setIcon(SHARED.theme.getIcon("prj_chapter:chapter"))
        self.aAddPart.setIcon(SHARED.theme.getIcon("prj_title:title"))
        self.aAddEmpty.setIcon(SHARED.theme.getIcon("prj_document:file"))
        self.aAddNote.setIcon(SHARED.theme.getIcon("prj_note:note"))
        self.aAddFolder.setIcon(SHARED.theme.getIcon("prj_folder:folder"))

        self.buildTemplatesMenu()
        self.buildQuickLinksMenu()
        self._buildRootMenu()

    def clearContent(self) -> None:
        """Clear dynamic content on the tool bar."""
        self.mQuick.clear()
        self.mTemplates.clearMenu()

    def buildQuickLinksMenu(self) -> None:
        """Build the quick link menu."""
        logger.debug("Rebuilding quick links menu")
        self.mQuick.clear()
        for tHandle, nwItem in SHARED.project.tree.iterRoots(None):
            qtAddAction(
                self.mQuick,
                elide(nwItem.itemName, 50),
                icon=SHARED.theme.getIcon(nwLabels.CLASS_ICON[nwItem.itemClass]),
                data=tHandle,
            )

    def buildTemplatesMenu(self) -> None:
        """Build the templates menu."""
        for tHandle, _ in SHARED.project.tree.iterRoots(nwItemClass.TEMPLATE):
            for dHandle in SHARED.project.tree.subTree(tHandle):
                self.processTemplateDocuments(dHandle)

    def processTemplateDocuments(self, tHandle: str) -> None:
        """Process change in tree items to update menu content."""
        if item := SHARED.project.tree[tHandle]:
            if item.isTemplateFile() and item.isActive:
                self.mTemplates.addUpdate(tHandle, item.itemName, item.getMainIcon())
            elif tHandle in self.mTemplates:
                self.mTemplates.remove(tHandle)

    ##
    #  Public Slots
    ##

    @pyqtSlot(str)
    def treeSelectionChanged(self, tHandle: str) -> None:
        """Toggle the visibility of the new item entries for novel
        documents. They should only be visible if novel documents can
        actually be added.
        """
        nwItem = SHARED.project.tree[tHandle]
        allowDoc = isinstance(nwItem, ProjectItem) and nwItem.documentAllowed()
        self.aAddScene.setVisible(allowDoc)
        self.aAddChap.setVisible(allowDoc)
        self.aAddPart.setVisible(allowDoc)
        self.aAddEmpty.setVisible(allowDoc)

    ##
    #  Private Slots
    ##

    @pyqtSlot(QAction)
    def _onQuickLinkSelected(self, action: QAction) -> None:
        """Select a quick link item."""
        if isinstance(tHandle := action.data(), str):  # pragma: no branch
            self.projView.setSelectedHandle(tHandle, doScroll=True)

    @pyqtSlot(QAction)
    def _onAddRootSelected(self, action: QAction) -> None:
        """Add a new root item."""
        if isinstance(itemClass := action.data(), nwItemClass):  # pragma: no branch
            self.projTree.newTreeItem(nwItemType.ROOT, itemClass=itemClass)

    @pyqtSlot(str)
    def _forwardTemplateTriggered(self, tHandle: str) -> None:
        """Forward the template menu's selected item handle."""
        self.newDocumentFromTemplate.emit(tHandle)

    ##
    #  Internal Functions
    ##

    def _buildRootMenu(self) -> None:
        """Build the rood folder menu."""

        def addClass(itemClass: nwItemClass) -> None:
            qtAddAction(
                self.mAddRoot,
                trConst(nwLabels.CLASS_NAME[itemClass]),
                icon=SHARED.theme.getIcon(nwLabels.CLASS_ICON[itemClass]),
                data=itemClass,
            )

        self.mAddRoot.clear()
        addClass(nwItemClass.NOVEL)
        self.mAddRoot.addSeparator()
        addClass(nwItemClass.PLOT)
        addClass(nwItemClass.CHARACTER)
        addClass(nwItemClass.WORLD)
        addClass(nwItemClass.TIMELINE)
        addClass(nwItemClass.OBJECT)
        addClass(nwItemClass.ENTITY)
        addClass(nwItemClass.CUSTOM)
        self.mAddRoot.addSeparator()
        addClass(nwItemClass.ARCHIVE)
        addClass(nwItemClass.TEMPLATE)


class GuiProjectTree(QTreeView):
    """GUI: Project View Tree."""

    def __init__(self, projView: GuiProjectView) -> None:
        super().__init__(parent=projView)

        logger.debug("Create: GuiProjectTree")

        self.projView = projView

        # Internal Variables
        self._actHandle = None

        # Cached Translations
        self.trActive = trConst(nwLabels.ACTIVE_NAME[True])
        self.trInactive = trConst(nwLabels.ACTIVE_NAME[False])

        # Tree Settings
        iPx = SHARED.theme.baseIconHeight

        self.setIconSize(SHARED.theme.baseIconSize)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setUniformRowHeights(True)
        self.setAllColumnsShowFocus(True)
        self.setExpandsOnDoubleClick(False)
        self.setAutoExpandDelay(1000)
        self.setHeaderHidden(True)
        self.setIndentation(iPx)

        # Allow Move by Drag & Drop
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Set selection options
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openContextMenu)

        # Connect signals
        self.doubleClicked.connect(self._onDoubleClick)
        self.collapsed.connect(self._onNodeCollapsed)
        self.expanded.connect(self._onNodeExpanded)

        # Set custom settings
        self.initViewport()

        logger.debug("Ready: GuiProjectTree")

    def initViewport(self) -> None:
        """Initialise viewport settings."""
        if CONFIG.hideVScroll:
            self.setVerticalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setVerticalScrollBarPolicy(QtScrollAsNeeded)
        if CONFIG.hideHScroll:
            self.setHorizontalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(QtScrollAsNeeded)

    ##
    #  External Methods
    ##

    def setActiveHandle(self, tHandle: str | None) -> None:
        """Set the handle to be highlighted."""
        self._actHandle = tHandle

    def getSelectedHandle(self) -> str | None:
        """Get the currently selected handle."""
        if (indexes := self.selectedIndexes()) and (node := self._getNode(indexes[0])):
            return node.item.itemHandle
        return None

    ##
    #  Module Internal Methods
    ##

    def clearTree(self) -> None:
        """Clear the tree view."""
        self.setModel(None)

    def loadModel(self) -> None:
        """Load and prepare a new project model."""
        if selectModelOld := self.selectionModel():
            with suppress(TypeError):
                selectModelOld.currentChanged.disconnect(self._onSelectionChange)
            selectModelOld.setParent(None)

        self.setModel(SHARED.project.tree.model)

        # Lock the column sizes
        iPx = SHARED.theme.baseIconHeight

        if header := self.header():  # pragma: no branch
            header.setStretchLastSection(False)
            header.setMinimumSectionSize(iPx + 6)
            header.setSectionResizeMode(ProjectNode.C_NAME, QtHeaderStretch)
            header.setSectionResizeMode(ProjectNode.C_COUNT, QtHeaderToContents)
            header.setSectionResizeMode(ProjectNode.C_ACTIVE, QtHeaderFixed)
            header.setSectionResizeMode(ProjectNode.C_STATUS, QtHeaderFixed)
            header.resizeSection(ProjectNode.C_ACTIVE, iPx + 6)
            header.resizeSection(ProjectNode.C_STATUS, iPx + 6)

        if selectModelNew := self.selectionModel():  # pragma: no branch
            selectModelNew.currentChanged.connect(self._onSelectionChange)

        self.restoreExpandedState()

    def restoreExpandedState(self) -> None:
        """Expand all nodes that were previously expanded."""
        if model := self._getModel():
            self.blockSignals(True)
            for index in model.allExpanded():
                self.setExpanded(index, True)
            self.blockSignals(False)

    def setSelectedHandle(self, tHandle: str | None, doScroll: bool = False) -> None:
        """Set a specific handle as the selected item."""
        if (model := self._getModel()) and (index := model.indexFromHandle(tHandle)).isValid():
            self.setCurrentIndex(index)
            if doScroll:
                self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
            self.projView.selectedItemChanged.emit(tHandle)

    def newTreeItem(
        self,
        itemType: nwItemType,
        itemClass: nwItemClass | None = None,
        hLevel: int = 1,
        isNote: bool = False,
        copyDoc: str | None = None,
    ) -> None:
        """Add new item to the tree, with a given itemType (and
        itemClass if Root), and attach it to the selected handle. Also
        make sure the item is added in a place it can be added, and that
        other meta data is set correctly to ensure a valid project tree.
        """
        if not SHARED.hasProject:
            logger.error("No project open")
            return

        tHandle = None
        if itemType == nwItemType.ROOT and isinstance(itemClass, nwItemClass):
            sPos = -1
            if (
                (node := self._getNode(self.currentIndex()))
                and (itemRoot := node.item.itemRoot)
                and (root := SHARED.project.tree.nodes.get(itemRoot))
            ):
                sPos = root.row() + 1

            tHandle = SHARED.project.newRoot(itemClass, sPos)
            self.restoreExpandedState()

        elif itemType in (nwItemType.FILE, nwItemType.FOLDER):
            if not ((model := self._getModel()) and (node := model.node(self.currentIndex()))):
                SHARED.error(self.tr("Did not find anywhere to add the file or folder!"))
                return

            if node.item.itemClass == nwItemClass.TRASH:
                SHARED.error(self.tr("Cannot add new files or folders to the Trash folder."))
                return

            # Set default label and determine where to put the new item
            nNote = isNote
            nLevel = hLevel
            if itemType == nwItemType.FILE:
                if copyDoc and (cItem := SHARED.project.tree[copyDoc]):
                    nNote = cItem.isNoteLayout()
                    nLevel = nwStyles.H_LEVEL.get(cItem.mainHeading, 0)
                    newLabel = cItem.itemName
                elif isNote:
                    newLabel = self.tr("New Note")
                elif hLevel == 1:
                    newLabel = self.tr("New Part")
                elif hLevel == 2:
                    newLabel = self.tr("New Chapter")
                elif hLevel == 3:
                    newLabel = self.tr("New Scene")
                else:
                    newLabel = self.tr("New Document")
            else:
                newLabel = self.tr("New Folder")
                nLevel = 0

            sHandle, sPos = SHARED.project.tree.pickParent(node, nLevel, nNote)
            if sHandle:
                newLabel, dlgOk = GuiEditLabel.getLabel(self, text=newLabel)
                if dlgOk:
                    # Add the file or folder
                    if itemType == nwItemType.FILE:
                        if tHandle := SHARED.project.newFile(newLabel, sHandle, sPos):
                            if copyDoc:
                                SHARED.project.copyFileContent(tHandle, copyDoc, newLabel)
                            elif hLevel > 0:
                                SHARED.project.writeNewFile(tHandle, hLevel, not nNote)
                            SHARED.project.index.reIndexHandle(tHandle)
                            SHARED.project.tree.refreshItems([tHandle])
                    else:
                        tHandle = SHARED.project.newFolder(newLabel, sHandle, sPos)

        # Select the new item automatically
        if tHandle:
            self.setSelectedHandle(tHandle)

        return

    def mergeDocuments(self, tHandle: str, newFile: bool) -> bool:
        """Merge an item's child documents into a single document."""
        logger.info("Request to merge items under handle '%s'", tHandle)

        if not (tItem := SHARED.project.tree[tHandle]):
            return False

        if tItem.isRootType():
            logger.error("Cannot merge root item")
            return False

        itemList = SHARED.project.tree.subTree(tHandle)
        if newFile:
            itemList.insert(0, tHandle)

        data, status = GuiDocMerge.getData(SHARED.mainGui, tHandle, itemList)
        if not status:
            logger.info("Action cancelled by user")
            return False
        if not (items := data.get("finalItems", [])):
            SHARED.info(self.tr("No documents selected for merging."))
            return False

        # Save the open document first, in case it's part of merge
        SHARED.saveEditor()

        # Create merge object, and append docs
        docMerger = DocMerger(SHARED.project)
        mLabel = self.tr("Merged")

        if newFile:
            docMerger.newTargetDoc(tHandle, f"[{mLabel}] {tItem.itemName}")
        elif tItem.isFileType():
            docMerger.setTargetDoc(tHandle)
        else:
            return False

        SHARED.initMainProgress(len(items))
        self.setEnabled(False)
        for sHandle in items:
            SHARED.incMainProgress()
            docMerger.appendText(sHandle, True, mLabel)

        self.setEnabled(True)
        SHARED.clearMainProgress()

        if not docMerger.writeTargetDoc():
            SHARED.error(self.tr("Could not write document content."), info=docMerger.getError())
            return False

        if data.get("moveToTrash", False):
            self.processDeleteRequest(data.get("finalItems", []), False)

        if mHandle := docMerger.targetHandle:
            self.projView.openDocumentRequest.emit(mHandle, nwDocMode.EDIT, "", False)
            self.projView.setSelectedHandle(mHandle, doScroll=True)

        return True

    def splitDocument(self, tHandle: str) -> bool:
        """Split a document into multiple documents."""
        logger.info("Request to split items with handle '%s'", tHandle)

        if not (tItem := SHARED.project.tree[tHandle]):
            return False

        if not tItem.isFileType() or tItem.itemParent is None:
            logger.error("Only valid document items can be split")
            return False

        data, text, status = GuiDocSplit.getData(SHARED.mainGui, tHandle)
        if not status:
            logger.info("Action cancelled by user")
            return False

        headerList = data.get("headerList", [])
        intoFolder = data.get("intoFolder", False)
        docHierarchy = data.get("docHierarchy", False)

        docSplit = DocSplitter(SHARED.project, tHandle)
        if intoFolder:
            docSplit.newParentFolder(tItem.itemParent, tItem.itemName)
        else:
            docSplit.setParentItem(tItem.itemParent)

        docSplit.splitDocument(headerList, text)
        SHARED.initMainProgress(len(docSplit))
        self.setEnabled(False)
        for writeOk in docSplit.writeDocuments(docHierarchy):
            SHARED.incMainProgress()
            if not writeOk:
                SHARED.error(self.tr("Could not write document content."), info=docSplit.getError())

        if data.get("moveToTrash", False):
            self.processDeleteRequest([tHandle], False)

        self.setEnabled(True)
        SHARED.clearMainProgress()

        return True

    def duplicateFromHandle(self, tHandle: str) -> None:
        """Duplicate the item hierarchy from a given item."""
        itemTree = [tHandle]
        itemTree.extend(SHARED.project.tree.subTree(tHandle))
        if itemTree:  # pragma: no branch
            if len(itemTree) == 1:
                question = self.tr("Do you want to duplicate this document?")
            else:
                question = self.tr("Do you want to duplicate this item and all child items?")
            if SHARED.question(question):
                self.setEnabled(False)
                docDup = DocDuplicator(SHARED.project)
                dHandles = docDup.duplicate(itemTree)
                if len(dHandles) != len(itemTree):
                    SHARED.warn(self.tr("Could not duplicate all items."))
                self.setEnabled(True)
        self.restoreExpandedState()

    ##
    #  Events and Overloads
    ##

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Overload mousePressEvent to clear selection if clicking the
        mouse in a blank area of the tree view, and to load a document
        for viewing if the user middle-clicked.
        """
        super().mousePressEvent(event)
        if event.button() == QtMouseLeft:
            if not self.indexAt(event.pos()).isValid():
                self._clearSelection()
        elif (
            event.button() == QtMouseMiddle
            and (node := self._getNode(self.indexAt(event.pos())))
            and node.item.isFileType()
        ):
            self.projView.openDocumentRequest.emit(node.item.itemHandle, nwDocMode.VIEW, "", False)

    def drawRow(self, painter: QPainter, opt: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Draw a box on the active row."""
        if (node := self._getNode(index)) and node.item.itemHandle == self._actHandle:
            painter.fillRect(opt.rect, self.palette().alternateBase())
        super().drawRow(painter, opt, index)

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def openSelectedItem(self) -> None:
        """Open the currently selected file, or view it if Shift is held."""
        if (node := self._getNode(self.currentIndex())) and node.item.isFileType():
            mode = nwDocMode.VIEW if QApplication.keyboardModifiers() == QtModShift else nwDocMode.EDIT
            self.projView.openDocumentRequest.emit(node.item.itemHandle, mode, "", False)

    @pyqtSlot()
    def moveItemUp(self) -> None:
        """Move an item up in the tree."""
        if model := self._getModel():
            model.internalMove(self.currentIndex(), -1)

    @pyqtSlot()
    def moveItemDown(self) -> None:
        """Move an item down in the tree."""
        if model := self._getModel():
            model.internalMove(self.currentIndex(), 1)

    @pyqtSlot()
    def goToSiblingUp(self) -> None:
        """Skip to the previous sibling."""
        if (
            (node := self._getNode(self.currentIndex()))
            and (parent := node.parent())
            and (move := parent.child(node.row() - 1))
            and (model := self._getModel())
        ):
            self.setCurrentIndex(model.indexFromNode(move))

    @pyqtSlot()
    def goToSiblingDown(self) -> None:
        """Skip to the next sibling."""
        if (
            (node := self._getNode(self.currentIndex()))
            and (parent := node.parent())
            and (move := parent.child(node.row() + 1))
            and (model := self._getModel())
        ):
            self.setCurrentIndex(model.indexFromNode(move))

    @pyqtSlot()
    def goToParent(self) -> None:
        """Move to parent item."""
        if (
            (model := self._getModel())
            and (node := model.node(self.currentIndex()))
            and (parent := node.parent())
            and parent is not model.root
        ):
            self.setCurrentIndex(model.indexFromNode(parent))

    @pyqtSlot()
    def goToFirstChild(self) -> None:
        """Move to first child item."""
        if (model := self._getModel()) and (node := model.node(self.currentIndex())) and (child := node.child(0)):
            self.setCurrentIndex(model.indexFromNode(child))

    @pyqtSlot(QModelIndex)
    def expandFromIndex(self, index: QModelIndex) -> None:
        """Expand all nodes from index."""
        self.expandRecursively(index)

    @pyqtSlot(QModelIndex)
    def collapseFromIndex(self, index: QModelIndex) -> None:
        """Collapse all nodes from index."""
        if (model := self._getModel()) and (node := model.node(index)):
            for child in node.allChildren():
                self.setExpanded(model.indexFromNode(child), False)

    @pyqtSlot()
    def processDeleteRequest(self, handles: list[str] | None = None, askFirst: bool = True) -> None:
        """Move selected items to Trash."""
        if handles and (model := self._getModel()):
            indices = [model.indexFromHandle(handle) for handle in handles]
        else:
            indices = self._selectedRows()

        if indices and (model := self._getModel()):
            if len(indices) == 1 and (node := model.node(indices[0])) and node.item.isRootType():
                if node.childCount() == 0:
                    SHARED.project.removeItem(node.item.itemHandle)
                else:
                    SHARED.error(self.tr("Root folders can only be deleted when they are empty."))
                return

            if model.trashSelection(indices):
                if not SHARED.question(self.tr("Permanently delete selected item(s)?")):
                    logger.info("Action cancelled by user")
                    return

                self.setEnabled(False)
                for index in indices:
                    if node := model.node(index):
                        self._deleteSubTree(node)
                self.setEnabled(True)

            elif trashNode := SHARED.project.tree.trash:
                if askFirst and not SHARED.question(self.tr("Move selected item(s) to Trash?")):
                    logger.info("Action cancelled by user")
                    return

                self.setEnabled(False)
                model.multiMove(indices, model.indexFromNode(trashNode))
                self.setEnabled(True)

        return

    @pyqtSlot()
    def emptyTrash(self) -> None:
        """Permanently delete all documents in the Trash folder. This
        function only asks for confirmation once, and calls the regular
        deleteItem function for each document in the Trash folder.
        """
        if trash := SHARED.project.tree.trash:
            if not (nodes := trash.allChildren()):
                SHARED.info(self.tr("The Trash folder is already empty."))
                return
            if not SHARED.question(self.tr("Permanently delete {0} file(s) from Trash?").format(len(nodes))):
                logger.info("Action cancelled by user")
                return
            for node in list(trash.children):
                self._deleteSubTree(node)
        return

    @pyqtSlot()
    @pyqtSlot("QPoint")
    def openContextMenu(self, point: QPoint | None = None) -> None:
        """Open a context menu in-place where the user clicked."""
        if model := self._getModel():
            if point is None:
                point = self.visualRect(self.currentIndex()).center()
            if point is not None:  # pragma: no branch
                index = self.indexAt(point)
                if (node := self._getNode(index)) and (indices := self._selectedRows()):
                    ctxMenu = _TreeContextMenu(self, model, node, indices)
                    if node is SHARED.project.tree.trash:
                        ctxMenu.buildTrashMenu()
                    elif len(indices) > 1:
                        ctxMenu.buildMultiSelectMenu()
                    else:
                        ctxMenu.buildSingleSelectMenu()
                    if viewport := self.viewport():  # pragma: no branch
                        ctxMenu.exec(viewport.mapToGlobal(point))
                    ctxMenu.setParent(None)

    ##
    #  Private Slots
    ##

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onSelectionChange(self, current: QModelIndex, previous: QModelIndex) -> None:
        """Process user changing which item is selected."""
        if node := self._getNode(current):
            self.projView.selectedItemChanged.emit(node.item.itemHandle)

    @pyqtSlot(QModelIndex)
    def _onDoubleClick(self, index: QModelIndex) -> None:
        """Capture a double-click event and either request the document
        for editing if it is a file, or expand/close the node if not.
        """
        if node := self._getNode(index):
            if node.item.isFileType():
                self.projView.openDocumentRequest.emit(node.item.itemHandle, nwDocMode.EDIT, "", True)
            else:
                self.setExpanded(index, not self.isExpanded(index))

    @pyqtSlot(QModelIndex)
    def _onNodeCollapsed(self, index: QModelIndex) -> None:
        """Capture a node collapse, and pass it to the model."""
        if node := self._getNode(index):
            node.setExpanded(False)

    @pyqtSlot(QModelIndex)
    def _onNodeExpanded(self, index: QModelIndex) -> None:
        """Capture a node expand, and pass it to the model."""
        if node := self._getNode(index):
            node.setExpanded(True)

    ##
    #  Internal Functions
    ##

    def _clearSelection(self) -> None:
        """Clear the currently selected items."""
        self.clearSelection()
        if model := self.selectionModel():
            # Selection model can be None (#2173)
            model.clearCurrentIndex()

    def _deleteSubTree(self, node: ProjectNode) -> None:
        """Permanently delete a node and its descendants."""
        for child in reversed(node.allChildren()):
            SHARED.project.removeItem(child.item.itemHandle)
        SHARED.project.removeItem(node.item.itemHandle)

    def _selectedRows(self) -> list[QModelIndex]:
        """Return all column 0 indexes."""
        return [i for i in self.selectedIndexes() if i.column() == 0]

    def _getModel(self) -> ProjectModel | None:
        """Return the model, if it exists."""
        if isinstance(model := self.model(), ProjectModel):
            return model
        return None

    def _getNode(self, index: QModelIndex) -> ProjectNode | None:
        """Return a project node corresponding to a model index."""
        if isinstance(model := self.model(), ProjectModel) and (node := model.node(index)):
            return node
        return None


class _UpdatableMenu(QMenu):
    menuItemTriggered = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._map: dict[str, QAction] = {}
        self.setTitle(self.tr("From Template"))
        self.triggered.connect(self._actionTriggered)

    def __contains__(self, tHandle: str) -> bool:
        """Look up a handle in the menu."""
        return tHandle in self._map

    ##
    #  Methods
    ##

    def addUpdate(self, tHandle: str, name: str, icon: QIcon) -> None:
        """Add or update a template item."""
        if tHandle in self._map:
            action = self._map[tHandle]
            action.setText(name)
            action.setIcon(icon)
        else:
            action = QAction(icon, name, self)
            action.setData(tHandle)
            self.addAction(action)
            self._map[tHandle] = action
        self.setActionsVisible(True)

    def remove(self, tHandle: str) -> None:
        """Remove a template item."""
        if action := self._map.pop(tHandle, None):
            self.removeAction(action)
            action.setParent(None)
        if not self._map:
            self.setActionsVisible(False)

    def clearMenu(self) -> None:
        """Clear all menu content."""
        self._map.clear()
        self.clear()

    def setActionsVisible(self, value: bool) -> None:
        """Set the visibility of root action."""
        if action := self.menuAction():  # pragma: no branch
            action.setVisible(value)

    ##
    #  Private Slots
    ##

    @pyqtSlot(QAction)
    def _actionTriggered(self, action: QAction) -> None:
        """Translate the menu trigger into an item trigger."""
        self.menuItemTriggered.emit(str(action.data()))


class _TreeContextMenu(QMenu):
    __slots__ = ("_children", "_handle", "_indices", "_item", "_model", "_node", "_tree", "_view")

    def __init__(
        self,
        projTree: GuiProjectTree,
        model: ProjectModel,
        node: ProjectNode,
        indices: list[QModelIndex],
    ) -> None:
        super().__init__(parent=projTree)
        self._tree = projTree
        self._view = projTree.projView
        self._node = node
        self._item = node.item
        self._model = model
        self._handle = node.item.itemHandle
        self._indices = indices
        self._children = node.childCount() > 0
        logger.debug("Ready: _TreeContextMenu")

    def __del__(self) -> None:  # pragma: no cover
        logger.debug("Delete: _TreeContextMenu")

    ##
    #  Methods
    ##

    def buildTrashMenu(self) -> None:
        """Build the special menu for the Trash folder."""
        action = qtAddAction(self, self.tr("Empty Trash"))
        action.triggered.connect(self._tree.emptyTrash)
        if self._children:
            self._expandCollapse()

    def buildSingleSelectMenu(self) -> None:
        """Build the single-select menu."""
        isFile = self._item.isFileType()
        isFolder = self._item.isFolderType()

        # Document Actions
        if isFile:
            self._docActions()
            self.addSeparator()

        # Create New Items
        self._itemCreation()
        self.addSeparator()

        # Edit Item Settings
        action = qtAddAction(self, self.tr("Rename"))
        action.triggered.connect(qtLambda(self._view.renameTreeItem, self._handle))
        if isFile:
            self._itemHeader()
            self._itemActive()
        self._itemStatusImport(False)

        # Transform Item
        if isFile or isFolder:
            self._itemTransform(isFile, isFolder)
        self.addSeparator()

        # Process Item
        if self._children:
            self._expandCollapse()
        action = qtAddAction(self, self.tr("Duplicate"))
        action.triggered.connect(qtLambda(self._tree.duplicateFromHandle, self._handle))
        self._deleteOrTrash()

    def buildMultiSelectMenu(self) -> None:
        """Build the multi-select menu."""
        self._itemActive()
        self._itemStatusImport(True)
        self.addSeparator()
        self._deleteOrTrash()

    ##
    #  Menu Builders
    ##

    def _docActions(self) -> None:
        """Add document actions."""
        action = qtAddAction(self, self.tr("Open Document"))
        action.triggered.connect(qtLambda(self._view.openDocumentRequest.emit, self._handle, nwDocMode.EDIT, "", True))
        action = qtAddAction(self, self.tr("View Document"))
        action.triggered.connect(qtLambda(self._view.openDocumentRequest.emit, self._handle, nwDocMode.VIEW, "", False))

    def _itemCreation(self) -> None:
        """Add create item actions."""
        menu = qtAddMenu(self, self.tr("Create New ..."))
        menu.addAction(self._view.projBar.aAddScene)
        menu.addAction(self._view.projBar.aAddChap)
        menu.addAction(self._view.projBar.aAddPart)
        menu.addAction(self._view.projBar.aAddEmpty)
        menu.addAction(self._view.projBar.aAddNote)
        menu.addAction(self._view.projBar.aAddFolder)

    def _itemHeader(self) -> None:
        """Check if there is a header that can be used for rename."""
        SHARED.saveEditor()
        if hItem := SHARED.project.index.getItemHeading(self._handle, "T0001"):
            action = qtAddAction(self, self.tr("Rename to Heading"))
            action.triggered.connect(qtLambda(self._view.renameTreeItem, self._handle, hItem.title))

    def _itemActive(self) -> None:
        """Add Active/Inactive actions."""
        if len(self._indices) > 1:
            mSub = qtAddMenu(self, self.tr("Set Active to ..."))
            aOne = qtAddAction(mSub, self._tree.trActive, icon=SHARED.theme.getIcon("checked:active"))
            aOne.triggered.connect(qtWeakLambda(self._iterItemActive, True))
            aTwo = qtAddAction(mSub, self._tree.trInactive, icon=SHARED.theme.getIcon("unchecked:inactive"))
            aTwo.triggered.connect(qtWeakLambda(self._iterItemActive, False))
        else:
            action = qtAddAction(self, self.tr("Toggle Active"))
            action.triggered.connect(self._toggleItemActive)
            if self._children > 0:
                mSub = qtAddMenu(self, self.tr("Set Children to ..."))
                aOne = qtAddAction(mSub, self._tree.trActive, icon=SHARED.theme.getIcon("checked:active"))
                aOne.triggered.connect(qtWeakLambda(self._recurseItemActive, True))
                aTwo = qtAddAction(mSub, self._tree.trInactive, icon=SHARED.theme.getIcon("unchecked:inactive"))
                aTwo.triggered.connect(qtWeakLambda(self._recurseItemActive, False))

    def _itemStatusImport(self, multi: bool) -> None:
        """Add actions for changing status or importance."""
        if self._item.isNovelLike():
            menu = qtAddMenu(self, self.tr("Set Status to ..."))
            current = self._item.itemStatus
            for key, entry in SHARED.project.data.itemStatus.iterItems():
                name = entry.name
                if not multi and current == key:
                    name += f" ({nwUnicode.U_CHECK})"
                action = qtAddAction(menu, name, icon=entry.icon)
                if multi:
                    action.triggered.connect(qtWeakLambda(self._iterSetItemStatus, key))
                else:
                    action.triggered.connect(qtWeakLambda(self._changeItemStatus, key))
            menu.addSeparator()
            action = qtAddAction(menu, self.tr("Manage Labels ..."))
            action.triggered.connect(qtLambda(self._view.projectSettingsRequest.emit, GuiProjectSettings.PAGE_STATUS))
        else:
            menu = qtAddMenu(self, self.tr("Set Importance to ..."))
            current = self._item.itemImport
            for key, entry in SHARED.project.data.itemImport.iterItems():
                name = entry.name
                if not multi and current == key:
                    name += f" ({nwUnicode.U_CHECK})"
                action = qtAddAction(menu, name, icon=entry.icon)
                if multi:
                    action.triggered.connect(qtWeakLambda(self._iterSetItemImport, key))
                else:
                    action.triggered.connect(qtWeakLambda(self._changeItemImport, key))
            menu.addSeparator()
            action = qtAddAction(menu, self.tr("Manage Labels ..."))
            action.triggered.connect(qtLambda(self._view.projectSettingsRequest.emit, GuiProjectSettings.PAGE_IMPORT))

    def _itemTransform(self, isFile: bool, isFolder: bool) -> None:
        """Add actions for the Transform menu."""
        menu = qtAddMenu(self, self.tr("Transform ..."))

        trDoc = trConst(nwLabels.LAYOUT_NAME[nwItemLayout.DOCUMENT])
        trNote = trConst(nwLabels.LAYOUT_NAME[nwItemLayout.NOTE])
        loDoc = nwItemLayout.DOCUMENT
        loNote = nwItemLayout.NOTE
        isDocFile = isFile and self._item.isDocumentLayout()
        isNoteFile = isFile and self._item.isNoteLayout()

        if isNoteFile and self._item.documentAllowed():
            action = qtAddAction(menu, self.tr("Convert to {0}").format(trDoc))
            action.triggered.connect(qtWeakLambda(self._changeItemLayout, loDoc))

        if isDocFile:
            action = qtAddAction(menu, self.tr("Convert to {0}").format(trNote))
            action.triggered.connect(qtWeakLambda(self._changeItemLayout, loNote))

        if isFolder and self._item.documentAllowed():
            action = qtAddAction(menu, self.tr("Convert to {0}").format(trDoc))
            action.triggered.connect(qtWeakLambda(self._convertFolderToFile, loDoc))

        if isFolder:
            action = qtAddAction(menu, self.tr("Convert to {0}").format(trNote))
            action.triggered.connect(qtWeakLambda(self._convertFolderToFile, loNote))

        if self._children and isFile:
            action = qtAddAction(menu, self.tr("Merge Child Items into Self"))
            action.triggered.connect(qtLambda(self._tree.mergeDocuments, self._handle, False))
            action = qtAddAction(menu, self.tr("Merge Child Items into New"))
            action.triggered.connect(qtLambda(self._tree.mergeDocuments, self._handle, True))

        if self._children and isFolder:
            action = qtAddAction(menu, self.tr("Merge Documents in Folder"))
            action.triggered.connect(qtLambda(self._tree.mergeDocuments, self._handle, True))

        if isFile:
            action = qtAddAction(menu, self.tr("Split Document by Headings"))
            action.triggered.connect(qtLambda(self._tree.splitDocument, self._handle))

    def _expandCollapse(self) -> None:
        """Add actions for expand and collapse."""
        action = qtAddAction(self, self.tr("Expand All"))
        action.triggered.connect(qtLambda(self._tree.expandFromIndex, self._indices[0]))
        action = qtAddAction(self, self.tr("Collapse All"))
        action.triggered.connect(qtLambda(self._tree.collapseFromIndex, self._indices[0]))

    def _deleteOrTrash(self) -> None:
        """Add move to Trash action."""
        if self._model.trashSelection(self._indices) or (len(self._indices) == 1 and self._item.isRootType()):
            text = self.tr("Delete Permanently")
        else:
            text = self.tr("Move to Trash")
        action = qtAddAction(self, text)
        action.triggered.connect(self._tree.processDeleteRequest)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _toggleItemActive(self) -> None:
        """Toggle the active status of an item."""
        if self._item.isFileType():
            self._item.setActive(not self._item.isActive)
            self._item.notifyToRefresh()

    ##
    #  Internal Functions
    ##

    def _iterItemActive(self, state: bool) -> None:
        """Set the active status of multiple items."""
        refresh = []
        for node in self._model.nodes(self._indices):
            if node.item.isFileType():
                node.item.setActive(state)
                refresh.append(node.item.itemHandle)
        SHARED.project.tree.refreshItems(refresh)

    def _recurseItemActive(self, state: bool) -> None:
        """Set the active status of an item and all its children."""
        refresh = []
        if self._item.isFileType():
            self._item.setActive(state)
            refresh.append(self._item.itemHandle)
        for child in self._node.allChildren():
            if child.item.isFileType():
                child.item.setActive(state)
                refresh.append(child.item.itemHandle)
        SHARED.project.tree.refreshItems(refresh)

    def _changeItemStatus(self, key: str) -> None:
        """Set a new status value of an item."""
        self._item.setStatus(key)
        self._item.notifyToRefresh()

    def _iterSetItemStatus(self, key: str) -> None:
        """Change the status value for multiple items."""
        refresh = []
        for node in self._model.nodes(self._indices):
            if node.item.isNovelLike():
                node.item.setStatus(key)
                refresh.append(node.item.itemHandle)
        SHARED.project.tree.refreshItems(refresh)

    def _changeItemImport(self, key: str) -> None:
        """Set a new importance value of an item."""
        self._item.setImport(key)
        self._item.notifyToRefresh()

    def _iterSetItemImport(self, key: str) -> None:
        """Change the status value for multiple items."""
        refresh = []
        for node in self._model.nodes(self._indices):
            if not node.item.isNovelLike():
                node.item.setImport(key)
                refresh.append(node.item.itemHandle)
        SHARED.project.tree.refreshItems(refresh)

    def _changeItemLayout(self, itemLayout: nwItemLayout) -> None:
        """Set a new item layout value of an item."""
        if itemLayout == nwItemLayout.DOCUMENT and self._item.documentAllowed():
            self._item.setLayout(nwItemLayout.DOCUMENT)
            self._item.notifyToRefresh()
            self._item.notifyNovelStructureChange()
        elif itemLayout == nwItemLayout.NOTE:
            self._item.setLayout(nwItemLayout.NOTE)
            self._item.notifyToRefresh()

    def _convertFolderToFile(self, itemLayout: nwItemLayout) -> None:
        """Convert a folder to a note or document."""
        if self._item.isFolderType():
            msgYes = SHARED.question(
                self.tr("Do you want to convert the folder to a {0}? This action cannot be reversed.").format(
                    trConst(nwLabels.LAYOUT_NAME[itemLayout])
                )
            )
            if msgYes and itemLayout == nwItemLayout.DOCUMENT and self._item.documentAllowed():
                self._item.setType(nwItemType.FILE)
                self._item.setLayout(nwItemLayout.DOCUMENT)
                self._item.notifyToRefresh()
                self._item.notifyNovelStructureChange()
            elif msgYes and itemLayout == nwItemLayout.NOTE:
                self._item.setType(nwItemType.FILE)
                self._item.setLayout(nwItemLayout.NOTE)
                self._item.notifyToRefresh()
            else:
                logger.info("Folder conversion cancelled")
