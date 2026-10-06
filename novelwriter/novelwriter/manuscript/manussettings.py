"""
novelWriter - GUI Build Settings
================================

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QFont, QIcon, QSyntaxHighlighter, QTextCharFormat, QTextDocument
from PyQt6.QtWidgets import (
    QAbstractButton,
    QAbstractItemView,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import describeFont, fontMatcher, languageName, processLangCode, qtAddAction, qtLambda
from novelwriter.constants import nwHeadFmt, nwKeyWords, nwLabels, nwStyles, nwUnicode, trConst
from novelwriter.enum import nwStandardButton, nwToolButton
from novelwriter.extensions.configlayout import NColorLabel, NFixedPage, NScrollableForm, NScrollablePage
from novelwriter.extensions.modified import NComboBox, NDoubleSpinBox, NIconButton, NSpinBox, NToolDialog
from novelwriter.extensions.pagedsidebar import NPagedSideBar
from novelwriter.extensions.switch import NSwitch
from novelwriter.extensions.switchbox import NSwitchBox
from novelwriter.manuscript.buildsettings import BuildSettings, FilterMode
from novelwriter.text.autoreplace import TextAutoReplace
from novelwriter.types import (
    QtAlignCenter,
    QtAlignLeft,
    QtAlignRightMiddle,
    QtHeaderFixed,
    QtHeaderStretch,
    QtRoleAccept,
    QtRoleApply,
    QtRoleDestruct,
    QtSelectDocument,
    QtUserRole,
)

if TYPE_CHECKING:
    from novelwriter.guimain import GuiMain

logger = logging.getLogger(__name__)


class GuiBuildSettings(NToolDialog):
    """GUI Tools: Manuscript Build Settings Dialog.

    The main tool for configuring manuscript builds. It's a GUI tool for
    editing JSON build definitions, wrapped as a BuildSettings object.
    """

    OPT_FILTERS = 1
    OPT_HEADINGS = 2
    OPT_FORMATTING = 10

    newSettingsReady = pyqtSignal(BuildSettings, bool)

    def __init__(self, parent: GuiMain, build: BuildSettings) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiBuildSettings")
        self.setObjectName("GuiBuildSettings")

        # Make a copy of the build object
        self._build = BuildSettings.fromDict(build.pack())

        self.setWindowTitle(self.tr("Manuscript Build Settings"))
        self.setMinimumSize(700, 400)

        iPx = SHARED.theme.baseIconHeight
        options = SHARED.project.options
        self.resize(
            options.getInt("GuiBuildSettings", "winWidth", 750),
            options.getInt("GuiBuildSettings", "winHeight", 550),
        )

        # Title
        self.titleLabel = NColorLabel(
            self.tr("Manuscript Build Settings"),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.HEADER_SCALE,
            indent=4,
        )

        # Settings Name
        self.lblBuildName = QLabel(self.tr("Name"), self)
        self.editBuildName = QLineEdit(self)

        # SideBar
        self.sidebar = NPagedSideBar(self)
        self.sidebar.setLabelColor(SHARED.theme.helpText)
        self.sidebar.setAccessibleName(self.titleLabel.text())

        self.sidebar.addLabel(self.tr("General"))
        self.sidebar.addButton(self.tr("Selection"), self.OPT_FILTERS)
        self.sidebar.addButton(self.tr("Headings"), self.OPT_HEADINGS)
        self.sidebar.addLabel(self.tr("Formatting"))

        self.sidebar.buttonClicked.connect(self._stackPageSelected)

        # Content
        self.optTabSelect = _FilterTab(self, self._build)
        self.optTabHeadings = _HeadingsTab(self, self._build)
        self.optTabFormatting = _FormattingTab(self, self._build, self.sidebar)

        self.toolStack = QStackedWidget(self)
        self.toolStack.addWidget(self.optTabSelect)
        self.toolStack.addWidget(self.optTabHeadings)
        self.toolStack.addWidget(self.optTabFormatting)

        # Preview
        self.swtAutoPreview = NSwitch(self, height=iPx)
        self.swtAutoPreview.setChecked(options.getBool("GuiBuildSettings", "autoPreview", True))

        self.lblAutoPreview = QLabel(self.tr("Auto-update preview"), self)
        self.lblAutoPreview.setBuddy(self.swtAutoPreview)

        # Buttons
        self.btnApply = SHARED.theme.getStandardButton(nwStandardButton.APPLY, self)
        self.btnSave = SHARED.theme.getStandardButton(nwStandardButton.SAVE, self)
        self.btnClose = SHARED.theme.getStandardButton(nwStandardButton.CLOSE, self)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnApply, QtRoleApply)
        self.btnBox.addButton(self.btnSave, QtRoleAccept)
        self.btnBox.addButton(self.btnClose, QtRoleDestruct)
        self.btnBox.clicked.connect(self._dialogButtonClicked)

        # Assemble
        self.topBox = QHBoxLayout()
        self.topBox.addWidget(self.titleLabel)
        self.topBox.addStretch(1)
        self.topBox.addWidget(self.lblBuildName)
        self.topBox.addWidget(self.editBuildName, 1)

        self.mainBox = QHBoxLayout()
        self.mainBox.addWidget(self.sidebar)
        self.mainBox.addWidget(self.toolStack)
        self.mainBox.setContentsMargins(0, 0, 0, 0)

        self.bottomBox = QHBoxLayout()
        self.bottomBox.addWidget(self.lblAutoPreview, 0)
        self.bottomBox.addWidget(self.swtAutoPreview, 0)
        self.bottomBox.addSpacing(8)
        self.bottomBox.addWidget(self.btnBox, 1)
        self.bottomBox.setContentsMargins(0, 0, 0, 0)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.topBox)
        self.outerBox.addLayout(self.mainBox)
        self.outerBox.addLayout(self.bottomBox)
        self.outerBox.setSpacing(12)

        self.setLayout(self.outerBox)
        self.updateTheme(init=True)

        # Set Default Tab
        self.sidebar.setSelected(self.OPT_FILTERS)

        logger.debug("Ready: GuiBuildSettings")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiBuildSettings")

    def loadContent(self) -> None:
        """Populate the child widgets."""
        self.editBuildName.setText(self._build.name)
        self.optTabSelect.loadContent()
        self.optTabHeadings.loadContent()
        self.optTabFormatting.loadContent()

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiBuildSettings, init=%s", init)

        if not init:
            self.btnApply.refreshTheme()
            self.btnSave.refreshTheme()
            self.btnClose.refreshTheme()

            self.optTabSelect.updateTheme()
            self.optTabHeadings.updateTheme()
            self.optTabFormatting.updateTheme()

        self.titleLabel.setTextColors(color=SHARED.theme.helpText)
        self.sidebar.setLabelColor(SHARED.theme.helpText)

    ##
    #  Properties
    ##

    @property
    def buildID(self) -> str:
        """The build ID of the build of the dialog."""
        return self._build.buildID

    ##
    #  Events
    ##

    def closeEvent(self, event: QEvent) -> None:
        """Capture the user closing the window so we can save
        settings.
        """
        logger.debug("Closing: GuiBuildSettings")
        self._applyChanges()
        self._askToSaveBuild()
        self._saveSettings()
        event.accept()
        self.softDelete()

    ##
    #  Private Slots
    ##

    @pyqtSlot(int)
    def _stackPageSelected(self, pageId: int) -> None:
        """Process a user request to switch page."""
        if pageId == self.OPT_FILTERS:
            self.toolStack.setCurrentWidget(self.optTabSelect)
        elif pageId == self.OPT_HEADINGS:
            self.toolStack.setCurrentWidget(self.optTabHeadings)
        elif pageId >= self.OPT_FORMATTING:
            self.toolStack.setCurrentWidget(self.optTabFormatting)
            self.optTabFormatting.scrollToSection(pageId)
        else:  # pragma: no cover
            pass

    @pyqtSlot("QAbstractButton*")
    def _dialogButtonClicked(self, button: QAbstractButton) -> None:
        """Handle button clicks from the dialog button box."""
        if button == self.btnApply:
            self._applyChanges()
            self._emitBuildData()
        elif button == self.btnSave:
            self._applyChanges()
            self._emitBuildData()
            self.close()
        elif button == self.btnClose:
            self._build.resetChangedState()
            self.close()
        else:  # pragma: no cover
            pass

    ##
    #  Internal Functions
    ##

    def _askToSaveBuild(self) -> None:
        """Check if there are unsaved changes, and if there are, ask
        whether the user wants to save them.
        """
        if self._build.changed:
            if SHARED.question(self.tr("Do you want to save your changes to '{0}'?").format(self._build.name)):
                self._emitBuildData()
            self._build.resetChangedState()

    def _saveSettings(self) -> None:
        """Save the various user settings."""
        treeWidth, filterWidth = self.optTabSelect.mainSplitSizes()
        logger.debug("Saving State: GuiBuildSettings")
        options = SHARED.project.options
        options.setValue("GuiBuildSettings", "winWidth", self.width())
        options.setValue("GuiBuildSettings", "winHeight", self.height())
        options.setValue("GuiBuildSettings", "treeWidth", treeWidth)
        options.setValue("GuiBuildSettings", "filterWidth", filterWidth)
        options.setValue("GuiBuildSettings", "autoPreview", self.swtAutoPreview.isChecked())
        options.saveSettings()

    def _applyChanges(self) -> None:
        """Apply all settings changes to the build object."""
        self._build.setName(self.editBuildName.text())
        self.optTabHeadings.saveContent()
        self.optTabFormatting.saveContent()

    def _emitBuildData(self) -> None:
        """Assemble the build data and emit the signal."""
        self.newSettingsReady.emit(self._build, self.swtAutoPreview.isChecked())
        self._build.resetChangedState()


class _FilterTab(NFixedPage):
    C_DATA = 0
    C_NAME = 0
    C_ACTIVE = 1
    C_STATUS = 2

    D_HANDLE = QtUserRole
    D_FILE = QtUserRole + 1

    F_NONE = 0
    F_FILTERED = 1
    F_INCLUDED = 2
    F_EXCLUDED = 3

    def __init__(self, parent: QWidget, build: BuildSettings) -> None:
        super().__init__(parent=parent)

        self._treeMap: dict[str, QTreeWidgetItem] = {}
        self._build = build

        self._statusFlags: dict[int, QIcon] = {
            self.F_NONE: QIcon(),
            self.F_FILTERED: SHARED.theme.getIcon("filter:option"),
            self.F_INCLUDED: SHARED.theme.getIcon("pin:action"),
            self.F_EXCLUDED: SHARED.theme.getIcon("exclude:reject"),
        }

        self._trIncluded = self.tr("Included in manuscript")
        self._trExcluded = self.tr("Excluded from manuscript")

        # Project Tree
        # ============

        iSz = SHARED.theme.baseIconSize
        iPx = SHARED.theme.baseIconHeight

        # Tree Widget
        self.optTree = QTreeWidget(self)
        self.optTree.setIconSize(iSz)
        self.optTree.setUniformRowHeights(True)
        self.optTree.setAllColumnsShowFocus(True)
        self.optTree.setHeaderHidden(True)
        self.optTree.setIndentation(iPx)
        self.optTree.setColumnCount(3)

        if header := self.optTree.header():  # pragma: no branch
            header.setStretchLastSection(False)
            header.setMinimumSectionSize(iPx + 6)  # See Issue #1551
            header.setSectionResizeMode(self.C_NAME, QtHeaderStretch)
            header.setSectionResizeMode(self.C_ACTIVE, QtHeaderFixed)
            header.setSectionResizeMode(self.C_STATUS, QtHeaderFixed)
            header.resizeSection(self.C_ACTIVE, iPx + 6)
            header.resizeSection(self.C_STATUS, iPx + 6)

        self.optTree.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.optTree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.optTree.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Filters
        # =======

        self.includedButton = NIconButton(self, iSz)
        self.includedButton.setToolTip(self.tr("Always included"))
        self.includedButton.clicked.connect(qtLambda(self._setSelectedMode, self.F_INCLUDED))

        self.excludedButton = NIconButton(self, iSz)
        self.excludedButton.setToolTip(self.tr("Always excluded"))
        self.excludedButton.clicked.connect(qtLambda(self._setSelectedMode, self.F_EXCLUDED))

        self.resetButton = NIconButton(self, iSz)
        self.resetButton.setToolTip(self.tr("Reset to default"))
        self.resetButton.clicked.connect(qtLambda(self._setSelectedMode, self.F_FILTERED))

        self.modeBox = QHBoxLayout()
        self.modeBox.addWidget(QLabel(self.tr("Mark selection as"), self))
        self.modeBox.addStretch(1)
        self.modeBox.addWidget(self.includedButton)
        self.modeBox.addWidget(self.excludedButton)
        self.modeBox.addWidget(self.resetButton)
        self.modeBox.setSpacing(4)

        # Filer Options
        self.filterOpt = NSwitchBox(self, iPx)
        self.filterOpt.switchToggled.connect(self._applyFilterSwitch)
        self.filterOpt.setFrameStyle(QFrame.Shape.NoFrame)

        # Assemble GUI
        # ============

        pOptions = SHARED.project.options

        self.selectionBox = QVBoxLayout()
        self.selectionBox.addWidget(self.optTree)
        self.selectionBox.addLayout(self.modeBox)
        self.selectionBox.setContentsMargins(0, 0, 0, 0)

        self.selectionWidget = QWidget(self)
        self.selectionWidget.setLayout(self.selectionBox)

        self.mainSplit = QSplitter(self)
        self.mainSplit.addWidget(self.selectionWidget)
        self.mainSplit.addWidget(self.filterOpt)
        self.mainSplit.setCollapsible(0, False)
        self.mainSplit.setCollapsible(1, False)
        self.mainSplit.setStretchFactor(0, 1)
        self.mainSplit.setStretchFactor(1, 0)
        self.mainSplit.setSizes([
            pOptions.getInt("GuiBuildSettings", "treeWidth", 300),
            pOptions.getInt("GuiBuildSettings", "filterWidth", 300),
        ])

        self.updateTheme(init=True)
        self.setCentralWidget(self.mainSplit)

    def loadContent(self) -> None:
        """Populate the widgets."""
        self._populateTree()
        self._populateFilters()

    def mainSplitSizes(self) -> tuple[int, int]:
        """Extract the sizes of the main splitter."""
        sizes = self.mainSplit.sizes()
        m, n = (sizes[0], sizes[1]) if len(sizes) >= 2 else (0, 0)
        return m, n

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _FilterTab, init=%s", init)

        if not init:
            self._statusFlags[self.F_FILTERED] = SHARED.theme.getIcon("filter:option")
            self._statusFlags[self.F_INCLUDED] = SHARED.theme.getIcon("pin:action")
            self._statusFlags[self.F_EXCLUDED] = SHARED.theme.getIcon("exclude:reject")
            self.loadContent()

        self.includedButton.setIcon(self._statusFlags[self.F_INCLUDED])
        self.excludedButton.setIcon(self._statusFlags[self.F_EXCLUDED])
        self.resetButton.setThemeIcon("revert:reset")

    ##
    #  Slots
    ##

    @pyqtSlot(str, bool)
    def _applyFilterSwitch(self, key: str, state: bool) -> None:
        """Apply filter switch and update the settings."""
        if key.startswith("doc:"):
            self._build.setValue(key[4:], state)
            self._setTreeItemMode()
        elif key.startswith("root:"):
            self._build.setAllowRoot(key[5:], state)
            self._populateTree()
        else:  # pragma: no cover
            pass

    ##
    #  Internal Functions
    ##

    def _populateTree(self) -> None:
        """Build the tree of project items."""
        logger.debug("Building project tree")
        self._treeMap = {}
        self.optTree.clear()
        for nwItem in SHARED.project.tree:
            tHandle = nwItem.itemHandle
            pHandle = nwItem.itemParent
            rHandle = nwItem.itemRoot

            if tHandle is None or rHandle is None:
                continue

            isFile = nwItem.isFileType()
            if nwItem.isInactiveClass() or not self._build.isRootAllowed(rHandle):
                continue

            trItem = QTreeWidgetItem()
            trItem.setIcon(self.C_NAME, nwItem.getMainIcon())
            trItem.setText(self.C_NAME, nwItem.itemName)
            trItem.setData(self.C_DATA, self.D_HANDLE, tHandle)
            trItem.setData(self.C_DATA, self.D_FILE, isFile)
            trItem.setIcon(self.C_ACTIVE, nwItem.getActiveStatus()[1])
            trItem.setTextAlignment(self.C_NAME, QtAlignLeft)

            if pHandle is None and nwItem.isRootType():
                self.optTree.addTopLevelItem(trItem)
            elif pHandle in self._treeMap:
                self._treeMap[pHandle].addChild(trItem)
            else:
                logger.debug("Skipping item '%s'", tHandle)
                continue

            self._treeMap[tHandle] = trItem
            trItem.setExpanded(True)

        self._setTreeItemMode()

    def _populateFilters(self) -> None:
        """Populate the filter options switches."""
        self.filterOpt.clear()
        self.filterOpt.addLabel(trConst(nwLabels.FILTER_GROUPS["documents"]))
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["novel"]),
            "doc:filter.includeNovel",
            icon="prj_scene:scene",
            default=self._build.getBool("filter.includeNovel"),
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["notes"]),
            "doc:filter.includeNotes",
            icon="prj_note:note",
            default=self._build.getBool("filter.includeNotes"),
        )
        self.filterOpt.addItem(
            trConst(nwLabels.FILTER_TYPES["inactive"]),
            "doc:filter.includeInactive",
            icon="unchecked:reject",
            default=self._build.getBool("filter.includeInactive"),
        )

        self.filterOpt.addSeparator()

        # Root Classes
        self.filterOpt.addLabel(self.tr("Select Root Folders"))
        for tHandle, nwItem in SHARED.project.tree.iterRoots(None):
            if not nwItem.isInactiveClass():
                self.filterOpt.addItem(
                    nwItem.itemName,
                    f"root:{tHandle}",
                    icon=nwItem.getMainIconStyle(),
                    default=self._build.isRootAllowed(tHandle),
                )

    def _setSelectedMode(self, mode: int) -> None:
        """Set the mode for the selected items."""
        items = self.optTree.selectedItems()
        if len(items) == 1 and isinstance(items[0], QTreeWidgetItem):
            items = self._scanChildren(items[0], [])

        for item in items:
            if isinstance(item, QTreeWidgetItem):  # pragma: no branch
                tHandle = item.data(self.C_DATA, self.D_HANDLE)
                isFile = item.data(self.C_DATA, self.D_FILE)
                if isFile:
                    if mode == self.F_FILTERED:
                        self._build.setFiltered(tHandle)
                    elif mode == self.F_INCLUDED:
                        self._build.setIncluded(tHandle)
                    elif mode == self.F_EXCLUDED:
                        self._build.setExcluded(tHandle)
                    else:  # pragma: no cover
                        pass

        self._setTreeItemMode()

    def _setTreeItemMode(self) -> None:
        """Update the filtered mode icon on all items."""
        filtered = self._build.buildItemFilter(SHARED.project)
        for tHandle, item in self._treeMap.items():
            allow, mode = filtered.get(tHandle, (False, FilterMode.UNKNOWN))
            if mode == FilterMode.INCLUDED:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_INCLUDED])
                item.setToolTip(self.C_STATUS, self._trIncluded)
            elif mode == FilterMode.EXCLUDED:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_EXCLUDED])
                item.setToolTip(self.C_STATUS, self._trExcluded)
            elif mode == FilterMode.FILTERED and allow:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_FILTERED])
                item.setToolTip(self.C_STATUS, self._trIncluded)
            else:
                item.setIcon(self.C_STATUS, self._statusFlags[self.F_NONE])

    def _scanChildren(self, item: QTreeWidgetItem | None, items: list) -> list[QTreeWidgetItem]:
        """Recursively return all items in a tree starting at a given
        QTreeWidgetItem.
        """
        if isinstance(item, QTreeWidgetItem):  # pragma: no branch
            items.append(item)
            for i in range(item.childCount()):
                self._scanChildren(item.child(i), items)
        return items


class _HeadingsTab(NScrollablePage):
    EDIT_TITLE = 1
    EDIT_CHAPTER = 2
    EDIT_UNNUM = 3
    EDIT_SCENE = 4
    EDIT_HSCENE = 5
    EDIT_SECTION = 6

    def __init__(self, parent: QWidget, build: BuildSettings) -> None:
        super().__init__(parent=parent)

        self._build = build
        self._editing = 0

        iPx = SHARED.theme.baseIconHeight
        trHide = self.tr("Hide")

        # Format Boxes
        # ============
        self.formatBox = QGridLayout()
        self.formatBox.setHorizontalSpacing(6)

        # Title Heading
        self.lblPart = QLabel(self._build.getLabel("headings.fmtPart"), self)
        self.fmtPart = QLineEdit("", self)
        self.fmtPart.setReadOnly(True)
        self.btnPart = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnPart.clicked.connect(qtLambda(self._editHeading, self.EDIT_TITLE))
        self.swtPart = NSwitch(self, height=iPx)
        self.hdePart = QLabel(trHide, self)
        self.hdePart.setIndent(6)
        self.hdePart.setBuddy(self.swtPart)

        self.formatBox.addWidget(self.lblPart, 0, 0)
        self.formatBox.addWidget(self.fmtPart, 0, 1)
        self.formatBox.addWidget(self.btnPart, 0, 2)
        self.formatBox.addWidget(self.hdePart, 0, 3)
        self.formatBox.addWidget(self.swtPart, 0, 4)

        # Chapter Heading
        self.lblChapter = QLabel(self._build.getLabel("headings.fmtChapter"), self)
        self.fmtChapter = QLineEdit("", self)
        self.fmtChapter.setReadOnly(True)
        self.btnChapter = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnChapter.clicked.connect(qtLambda(self._editHeading, self.EDIT_CHAPTER))
        self.swtChapter = NSwitch(self, height=iPx)
        self.hdeChapter = QLabel(trHide, self)
        self.hdeChapter.setIndent(6)
        self.hdeChapter.setBuddy(self.swtChapter)

        self.formatBox.addWidget(self.lblChapter, 1, 0)
        self.formatBox.addWidget(self.fmtChapter, 1, 1)
        self.formatBox.addWidget(self.btnChapter, 1, 2)
        self.formatBox.addWidget(self.hdeChapter, 1, 3)
        self.formatBox.addWidget(self.swtChapter, 1, 4)

        # Unnumbered Chapter Heading
        self.lblUnnumbered = QLabel(self._build.getLabel("headings.fmtUnnumbered"), self)
        self.fmtUnnumbered = QLineEdit("", self)
        self.fmtUnnumbered.setReadOnly(True)
        self.btnUnnumbered = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnUnnumbered.clicked.connect(qtLambda(self._editHeading, self.EDIT_UNNUM))
        self.swtUnnumbered = NSwitch(self, height=iPx)
        self.hdeUnnumbered = QLabel(trHide, self)
        self.hdeUnnumbered.setIndent(6)
        self.hdeUnnumbered.setBuddy(self.swtUnnumbered)

        self.formatBox.addWidget(self.lblUnnumbered, 2, 0)
        self.formatBox.addWidget(self.fmtUnnumbered, 2, 1)
        self.formatBox.addWidget(self.btnUnnumbered, 2, 2)
        self.formatBox.addWidget(self.hdeUnnumbered, 2, 3)
        self.formatBox.addWidget(self.swtUnnumbered, 2, 4)

        # Scene Heading
        self.lblScene = QLabel(self._build.getLabel("headings.fmtScene"), self)
        self.fmtScene = QLineEdit("", self)
        self.fmtScene.setReadOnly(True)
        self.btnScene = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnScene.clicked.connect(qtLambda(self._editHeading, self.EDIT_SCENE))
        self.swtScene = NSwitch(self, height=iPx)
        self.hdeScene = QLabel(trHide, self)
        self.hdeScene.setIndent(6)
        self.hdeScene.setBuddy(self.swtScene)

        self.formatBox.addWidget(self.lblScene, 3, 0)
        self.formatBox.addWidget(self.fmtScene, 3, 1)
        self.formatBox.addWidget(self.btnScene, 3, 2)
        self.formatBox.addWidget(self.hdeScene, 3, 3)
        self.formatBox.addWidget(self.swtScene, 3, 4)

        # Alt Scene Heading
        self.lblAScene = QLabel(self._build.getLabel("headings.fmtAltScene"), self)
        self.fmtAScene = QLineEdit("", self)
        self.fmtAScene.setReadOnly(True)
        self.btnAScene = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnAScene.clicked.connect(qtLambda(self._editHeading, self.EDIT_HSCENE))
        self.swtAScene = NSwitch(self, height=iPx)
        self.hdeAScene = QLabel(trHide, self)
        self.hdeAScene.setIndent(6)
        self.hdeAScene.setBuddy(self.swtAScene)

        self.formatBox.addWidget(self.lblAScene, 4, 0)
        self.formatBox.addWidget(self.fmtAScene, 4, 1)
        self.formatBox.addWidget(self.btnAScene, 4, 2)
        self.formatBox.addWidget(self.hdeAScene, 4, 3)
        self.formatBox.addWidget(self.swtAScene, 4, 4)

        # Section Heading
        self.lblSection = QLabel(self._build.getLabel("headings.fmtSection"), self)
        self.fmtSection = QLineEdit("", self)
        self.fmtSection.setReadOnly(True)
        self.btnSection = SHARED.theme.getIconButton(nwToolButton.EDIT, self)
        self.btnSection.clicked.connect(qtLambda(self._editHeading, self.EDIT_SECTION))
        self.swtSection = NSwitch(self, height=iPx)
        self.hdeSection = QLabel(trHide, self)
        self.hdeSection.setIndent(6)
        self.hdeSection.setBuddy(self.swtSection)

        self.formatBox.addWidget(self.lblSection, 5, 0)
        self.formatBox.addWidget(self.fmtSection, 5, 1)
        self.formatBox.addWidget(self.btnSection, 5, 2)
        self.formatBox.addWidget(self.hdeSection, 5, 3)
        self.formatBox.addWidget(self.swtSection, 5, 4)

        # Edit Form
        # =========

        self.lblEditForm = QLabel(self.tr("Editing: {0}").format(self.tr("None")), self)

        self.editTextBox = QPlainTextEdit(self)
        self.editTextBox.setFixedHeight(5 * iPx)
        self.editTextBox.setEnabled(False)

        self.formSyntax = _HeadingSyntaxHighlighter(self.editTextBox.document())

        self._autoReplace = TextAutoReplace()
        if document := self.editTextBox.document():  # pragma: no branch
            document.contentsChange.connect(self._editTextBoxChanged)

        self.mInsert = QMenu(self)
        self.aInsTitle = qtAddAction(self.mInsert, self.tr("Title"))
        self.aInsChNum = qtAddAction(self.mInsert, self.tr("Chapter Number"))
        self.aInsChWord = qtAddAction(self.mInsert, self.tr("Chapter Number (Word)"))
        self.aInsChRomU = qtAddAction(self.mInsert, self.tr("Chapter Number (Upper Case Roman)"))
        self.aInsChRomL = qtAddAction(self.mInsert, self.tr("Chapter Number (Lower Case Roman)"))
        self.aInsScNum = qtAddAction(self.mInsert, self.tr("Scene Number (In Chapter)"))
        self.aInsScAbs = qtAddAction(self.mInsert, self.tr("Scene Number (Absolute)"))
        self.aInsCharPOV = qtAddAction(self.mInsert, self.tr("Point of View Character"))
        self.aInsCharFocus = qtAddAction(self.mInsert, self.tr("Focus Character"))
        self.aInsHRule = qtAddAction(self.mInsert, self.tr("Horizontal Rule"))

        self.aInsTitle.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.TITLE))
        self.aInsChNum.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CH_NUM))
        self.aInsChWord.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CH_WORD))
        self.aInsChRomU.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CH_ROMU))
        self.aInsChRomL.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CH_ROML))
        self.aInsScNum.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.SC_NUM))
        self.aInsScAbs.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.SC_ABS))
        self.aInsCharPOV.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CHAR_POV))
        self.aInsCharFocus.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.CHAR_FOCUS))
        self.aInsHRule.triggered.connect(qtLambda(self._insertIntoForm, nwHeadFmt.HRULE, True))

        self.btnInsert = QPushButton(self.tr("Insert"), self)
        self.btnInsert.setMenu(self.mInsert)

        self.btnApply = QPushButton(self.tr("Apply"), self)
        self.btnApply.clicked.connect(self._saveFormat)

        self.formButtonBox = QHBoxLayout()
        self.formButtonBox.addStretch(1)
        self.formButtonBox.addWidget(self.btnInsert)
        self.formButtonBox.addWidget(self.btnApply)

        self.editFormBox = QVBoxLayout()
        self.editFormBox.addWidget(self.lblEditForm)
        self.editFormBox.addWidget(self.editTextBox)
        self.editFormBox.addLayout(self.formButtonBox)

        # Layout Matrix
        # =============
        trCentre = self.tr("Centre")
        trBreak = self.tr("Page Break")

        self.layoutMatrix = QGridLayout()
        self.layoutMatrix.setVerticalSpacing(12)
        self.layoutMatrix.setHorizontalSpacing(12)

        self.layoutMatrix.addWidget(QLabel(trCentre, self), 0, 1)
        self.layoutMatrix.addWidget(QLabel(trBreak, self), 0, 2)

        # Title Layout
        trLabel = self._build.getLabel("headings.styleTitle")
        self.lblTitle = QLabel(trLabel, self)
        self.centerTitle = NSwitch(self, height=iPx)
        self.centerTitle.setAccessibleName(f"{trLabel}: {trCentre}")
        self.breakTitle = NSwitch(self, height=iPx)
        self.breakTitle.setAccessibleName(f"{trLabel}: {trBreak}")

        self.layoutMatrix.addWidget(self.lblTitle, 1, 0)
        self.layoutMatrix.addWidget(self.centerTitle, 1, 1, QtAlignCenter)
        self.layoutMatrix.addWidget(self.breakTitle, 1, 2, QtAlignCenter)

        # Partition Layout
        trLabel = self._build.getLabel("headings.stylePart")
        self.lblPart = QLabel(trLabel, self)
        self.centerPart = NSwitch(self, height=iPx)
        self.centerPart.setAccessibleName(f"{trLabel}: {trCentre}")
        self.breakPart = NSwitch(self, height=iPx)
        self.breakPart.setAccessibleName(f"{trLabel}: {trBreak}")

        self.layoutMatrix.addWidget(self.lblPart, 2, 0)
        self.layoutMatrix.addWidget(self.centerPart, 2, 1, QtAlignCenter)
        self.layoutMatrix.addWidget(self.breakPart, 2, 2, QtAlignCenter)

        # Chapter Layout
        trLabel = self._build.getLabel("headings.styleChapter")
        self.lblChapter = QLabel(trLabel, self)
        self.centerChapter = NSwitch(self, height=iPx)
        self.centerChapter.setAccessibleName(f"{trLabel}: {trCentre}")
        self.breakChapter = NSwitch(self, height=iPx)
        self.breakChapter.setAccessibleName(f"{trLabel}: {trBreak}")

        self.layoutMatrix.addWidget(self.lblChapter, 3, 0)
        self.layoutMatrix.addWidget(self.centerChapter, 3, 1, QtAlignCenter)
        self.layoutMatrix.addWidget(self.breakChapter, 3, 2, QtAlignCenter)

        # Scene Layout
        trLabel = self._build.getLabel("headings.styleScene")
        self.lblScene = QLabel(trLabel, self)
        self.centerScene = NSwitch(self, height=iPx)
        self.centerScene.setAccessibleName(f"{trLabel}: {trCentre}")
        self.breakScene = NSwitch(self, height=iPx)
        self.breakScene.setAccessibleName(f"{trLabel}: {trBreak}")

        self.layoutMatrix.addWidget(self.lblScene, 4, 0)
        self.layoutMatrix.addWidget(self.centerScene, 4, 1, QtAlignCenter)
        self.layoutMatrix.addWidget(self.breakScene, 4, 2, QtAlignCenter)

        self.layoutMatrix.setColumnStretch(3, 1)

        # Assemble
        # ========

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.formatBox)
        self.outerBox.addSpacing(16)
        self.outerBox.addLayout(self.editFormBox)
        self.outerBox.addSpacing(16)
        self.outerBox.addLayout(self.layoutMatrix)
        self.outerBox.addStretch(1)

        self.updateTheme(onInit=True)
        self.setCentralLayout(self.outerBox)

    def updateTheme(self, onInit: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _HeadingsTab")

        if not onInit:
            self.btnPart.refreshTheme()
            self.btnChapter.refreshTheme()
            self.btnUnnumbered.refreshTheme()
            self.btnScene.refreshTheme()
            self.btnAScene.refreshTheme()
            self.btnSection.refreshTheme()

        self.formSyntax.initHighlighter()
        self.formSyntax.rehighlight()

    def loadContent(self) -> None:
        """Populate the widgets."""

        def fmtBreak(text: str) -> str:
            return text.replace(nwHeadFmt.BR, nwUnicode.U_LBREAK)

        self.fmtPart.setText(fmtBreak(self._build.getStr("headings.fmtPart")))
        self.fmtChapter.setText(fmtBreak(self._build.getStr("headings.fmtChapter")))
        self.fmtUnnumbered.setText(fmtBreak(self._build.getStr("headings.fmtUnnumbered")))
        self.fmtScene.setText(fmtBreak(self._build.getStr("headings.fmtScene")))
        self.fmtAScene.setText(fmtBreak(self._build.getStr("headings.fmtAltScene")))
        self.fmtSection.setText(fmtBreak(self._build.getStr("headings.fmtSection")))

        self.swtPart.setChecked(self._build.getBool("headings.hidePart"))
        self.swtChapter.setChecked(self._build.getBool("headings.hideChapter"))
        self.swtUnnumbered.setChecked(self._build.getBool("headings.hideUnnumbered"))
        self.swtScene.setChecked(self._build.getBool("headings.hideScene"))
        self.swtAScene.setChecked(self._build.getBool("headings.hideAltScene"))
        self.swtSection.setChecked(self._build.getBool("headings.hideSection"))

        self.centerTitle.setChecked(self._build.getBool("headings.centerTitle"))
        self.centerPart.setChecked(self._build.getBool("headings.centerPart"))
        self.centerChapter.setChecked(self._build.getBool("headings.centerChapter"))
        self.centerScene.setChecked(self._build.getBool("headings.centerScene"))

        self.breakTitle.setChecked(self._build.getBool("headings.breakTitle"))
        self.breakPart.setChecked(self._build.getBool("headings.breakPart"))
        self.breakChapter.setChecked(self._build.getBool("headings.breakChapter"))
        self.breakScene.setChecked(self._build.getBool("headings.breakScene"))

    def saveContent(self) -> None:
        """Save choices back into build object."""
        self._build.setValue("headings.hidePart", self.swtPart.isChecked())
        self._build.setValue("headings.hideChapter", self.swtChapter.isChecked())
        self._build.setValue("headings.hideUnnumbered", self.swtUnnumbered.isChecked())
        self._build.setValue("headings.hideScene", self.swtScene.isChecked())
        self._build.setValue("headings.hideAltScene", self.swtAScene.isChecked())
        self._build.setValue("headings.hideSection", self.swtSection.isChecked())

        self._build.setValue("headings.centerTitle", self.centerTitle.isChecked())
        self._build.setValue("headings.centerPart", self.centerPart.isChecked())
        self._build.setValue("headings.centerChapter", self.centerChapter.isChecked())
        self._build.setValue("headings.centerScene", self.centerScene.isChecked())

        self._build.setValue("headings.breakTitle", self.breakTitle.isChecked())
        self._build.setValue("headings.breakPart", self.breakPart.isChecked())
        self._build.setValue("headings.breakChapter", self.breakChapter.isChecked())
        self._build.setValue("headings.breakScene", self.breakScene.isChecked())

    ##
    #  Internal Functions
    ##

    def _insertIntoForm(self, text: str, replace: bool = False) -> None:
        """Insert formatting text from the dropdown menu."""
        if self._editing > 0:
            cursor = self.editTextBox.textCursor()
            if replace:
                cursor.select(QtSelectDocument)
                cursor.removeSelectedText()
            cursor.insertText(text)
            self.editTextBox.setFocus()

    def _editHeading(self, heading: int) -> None:
        """Populate the form with a specific heading format."""
        self._editing = heading
        self.editTextBox.setEnabled(True)
        if heading == self.EDIT_TITLE:
            text = self.fmtPart.text()
            label = self._build.getLabel("headings.fmtPart")
        elif heading == self.EDIT_CHAPTER:
            text = self.fmtChapter.text()
            label = self._build.getLabel("headings.fmtChapter")
        elif heading == self.EDIT_UNNUM:
            text = self.fmtUnnumbered.text()
            label = self._build.getLabel("headings.fmtUnnumbered")
        elif heading == self.EDIT_SCENE:
            text = self.fmtScene.text()
            label = self._build.getLabel("headings.fmtScene")
        elif heading == self.EDIT_HSCENE:
            text = self.fmtAScene.text()
            label = self._build.getLabel("headings.fmtAltScene")
        elif heading == self.EDIT_SECTION:
            text = self.fmtSection.text()
            label = self._build.getLabel("headings.fmtSection")
        else:
            self._editing = 0
            self.editTextBox.setEnabled(False)
            text = ""
            label = self.tr("None")

        self.editTextBox.setPlainText(text.replace(nwUnicode.U_LBREAK, "\n"))
        self.lblEditForm.setText(self.tr("Editing: {0}").format(label))

    ##
    #  Private Slots
    ##

    @pyqtSlot(int, int, int)
    def _editTextBoxChanged(self, pos: int, removed: int, added: int) -> None:
        """Apply auto-replace as the user types in the edit box."""
        if CONFIG.doReplace and added == 1:
            cursor = self.editTextBox.textCursor()
            self._autoReplace(cursor.block().text(), cursor)

    @pyqtSlot()
    def _saveFormat(self) -> None:
        """Save the format from the edit text box."""
        heading = self._editing
        text = self.editTextBox.toPlainText().strip().replace("\n", nwUnicode.U_LBREAK)
        value = text.replace(nwUnicode.U_LBREAK, nwHeadFmt.BR)
        if heading == self.EDIT_TITLE:
            self.fmtPart.setText(text)
            self._build.setValue("headings.fmtPart", value)
        elif heading == self.EDIT_CHAPTER:
            self.fmtChapter.setText(text)
            self._build.setValue("headings.fmtChapter", value)
        elif heading == self.EDIT_UNNUM:
            self.fmtUnnumbered.setText(text)
            self._build.setValue("headings.fmtUnnumbered", value)
        elif heading == self.EDIT_SCENE:
            self.fmtScene.setText(text)
            self._build.setValue("headings.fmtScene", value)
        elif heading == self.EDIT_HSCENE:
            self.fmtAScene.setText(text)
            self._build.setValue("headings.fmtAltScene", value)
        elif heading == self.EDIT_SECTION:
            self.fmtSection.setText(text)
            self._build.setValue("headings.fmtSection", value)
        else:
            return

        self._editHeading(0)
        self.editTextBox.clear()

        return


class _HeadingSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document: QTextDocument | None) -> None:
        super().__init__(document)
        self._fmtSymbol = QTextCharFormat()
        self._fmtFormat = QTextCharFormat()
        self.initHighlighter()

    def initHighlighter(self) -> None:
        """Update theme elements."""
        syntax = SHARED.theme.syntaxTheme
        self._fmtSymbol.setForeground(syntax.head)
        self._fmtFormat.setForeground(syntax.emph)

    def highlightBlock(self, text: str) -> None:
        """Add syntax highlighting to the text block."""
        if text == nwHeadFmt.HRULE:
            # Special case for horizontal rule, which is a single symbol
            self.setFormat(0, len(text), self._fmtSymbol)
        else:
            for heading in nwHeadFmt.PAGE_HEADERS:
                if (chars := len(heading)) > 0:  # pragma: no branch
                    offset = 0
                    while (pos := text.find(heading, offset)) >= 0:
                        offset = pos + chars
                        self.setFormat(pos, chars, self._fmtSymbol)
                        self.setFormat(pos + 1, chars - 2, self._fmtFormat)
                        if (ddots := heading.find(":")) > 0:
                            self.setFormat(pos + ddots, 1, self._fmtSymbol)


class _FormattingTab(NScrollableForm):
    def __init__(self, parent: QWidget, build: BuildSettings, sidebar: NPagedSideBar) -> None:
        super().__init__(parent=parent)

        self._build = build
        self._sidebar = sidebar

        self.setHelpTextStyle(SHARED.theme.helpText)
        self.buildForm()
        self.updateTheme(onInit=True)

    def buildForm(self) -> None:
        """Build the formatting form."""
        section = 10

        iSp = 6
        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        # Text Content
        # ============

        title = self._build.getLabel("text.grpContent")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        # Text Inclusion
        self.incBodyText = NSwitch(self, height=iPx)
        self.incSynopsis = NSwitch(self, height=iPx)
        self.incComments = NSwitch(self, height=iPx)
        self.incStory = NSwitch(self, height=iPx)
        self.incNotes = NSwitch(self, height=iPx)
        self.incKeywords = NSwitch(self, height=iPx)

        self.addRow(self._build.getLabel("text.includeBodyText"), self.incBodyText)
        self.addRow(self._build.getLabel("text.includeSynopsis"), self.incSynopsis)
        self.addRow(self._build.getLabel("text.includeComments"), self.incComments)
        self.addRow(self._build.getLabel("text.includeStory"), self.incStory)
        self.addRow(self._build.getLabel("text.includeNotes"), self.incNotes)
        self.addRow(self._build.getLabel("text.includeKeywords"), self.incKeywords)

        # Ignored Keywords
        self.ignoredKeywords = QLineEdit(self)

        self.mnKeywords = QMenu(self)
        self.mnKeywords.triggered.connect(self._ignoredKeywordSelected)
        for keyword in nwKeyWords.VALID_KEYS:
            qtAddAction(self.mnKeywords, trConst(nwLabels.KEY_NAME[keyword]), data=keyword)

        self.ignoredKeywordsButton = NIconButton(self, iSz, "add:add")
        self.ignoredKeywordsButton.setToolTip(self.tr("Select Keyword"))
        self.ignoredKeywordsButton.setMenu(self.mnKeywords)
        self.addRow(
            self._build.getLabel("text.ignoredKeywords"),
            self.ignoredKeywords,
            button=self.ignoredKeywordsButton,
            stretch=(1, 1),
        )

        # Note Headings
        self.addNoteHead = NSwitch(self, height=iPx)
        self.addRow(self._build.getLabel("text.addNoteHeadings"), self.addNoteHead)

        # Text Format
        # ===========

        title = self._build.getLabel("format.grpFormat")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        # Text Font
        self.textFont = QLineEdit(self)
        self.textFont.setReadOnly(True)
        self.btnTextFont = SHARED.theme.getIconButton(nwToolButton.FONT, self)
        self.btnTextFont.clicked.connect(self._selectFont)
        self.addRow(
            self._build.getLabel("format.textFont"),
            self.textFont,
            button=self.btnTextFont,
            stretch=(1, 1),
        )

        # Line Height
        self.lineHeight = NDoubleSpinBox(self, minVal=0.75, maxVal=3.0, step=0.05, prec=2)
        self.lineHeight.setFixedNumbersWidth(4)
        self.addRow(self._build.getLabel("format.lineHeight"), self.lineHeight, unit="em")

        # Text Options
        self.justifyText = NSwitch(self, height=iPx)
        self.justifyOnBreak = NSwitch(self, height=iPx)
        self.stripUnicode = NSwitch(self, height=iPx)
        self.replaceTabs = NSwitch(self, height=iPx)
        self.keepBreaks = NSwitch(self, height=iPx)
        self.showDialogue = NSwitch(self, height=iPx)

        self.addRow(self._build.getLabel("format.justifyText"), self.justifyText)
        self.addRow(self._build.getLabel("format.justifyOnBreak"), self.justifyOnBreak)
        self.addRow(self._build.getLabel("format.stripUnicode"), self.stripUnicode)
        self.addRow(self._build.getLabel("format.replaceTabs"), self.replaceTabs)
        self.addRow(self._build.getLabel("format.keepBreaks"), self.keepBreaks)
        self.addRow(self._build.getLabel("format.showDialogue"), self.showDialogue)

        # Heading Format
        # ==============

        title = self._build.getLabel("format.grpHeadings")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        self.colorHeadings = NSwitch(self, height=iPx)
        self.boldHeadings = NSwitch(self, height=iPx)
        self.upperHeadings = NSwitch(self, height=iPx)

        self.addRow(self._build.getLabel("format.colorHeadings"), self.colorHeadings)
        self.addRow(self._build.getLabel("format.boldHeadings"), self.boldHeadings)
        self.addRow(self._build.getLabel("format.upperHeadings"), self.upperHeadings)

        # First Line Indent
        # =================

        title = self._build.getLabel("format.grpParIndent")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        self.firstIndent = NSwitch(self, height=iPx)
        self.indentFirstPar = NSwitch(self, height=iPx)

        self.indentWidth = NDoubleSpinBox(self, minVal=0.1, maxVal=9.9, step=0.1, prec=1)
        self.indentWidth.setFixedNumbersWidth(4)

        self.addRow(self._build.getLabel("format.firstLineIndent"), self.firstIndent)
        self.addRow(self._build.getLabel("format.firstIndentWidth"), self.indentWidth, unit="em")
        self.addRow(self._build.getLabel("format.indentFirstPar"), self.indentFirstPar)

        # Size & Margins
        # ==============

        title = self._build.getLabel("format.grpMargins")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        # Title
        self.titleSize = NDoubleSpinBox(self, minVal=0.8, maxVal=10.0, step=0.05)
        self.titleSize.setFixedNumbersWidth(4)
        self.titleMarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.titleMarginT.setFixedNumbersWidth(4)
        self.titleMarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.titleMarginB.setFixedNumbersWidth(4)
        self.btnTitleProps = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnTitleProps.clicked.connect(self._resetTitleProps)

        self.pixH0S = QLabel(self)
        self.pixH0T = QLabel(self)
        self.pixH0B = QLabel(self)

        self.addRow(
            self._build.getLabel("format.titleMargin"),
            [
                self.pixH0S,
                self.titleSize,
                iSp,
                self.pixH0T,
                self.titleMarginT,
                iSp,
                self.pixH0B,
                self.titleMarginB,
            ],
            button=self.btnTitleProps,
        )

        # Heading 1
        self.h1Size = NDoubleSpinBox(self, minVal=0.8, maxVal=10.0, step=0.05)
        self.h1Size.setFixedNumbersWidth(4)
        self.h1MarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h1MarginT.setFixedNumbersWidth(4)
        self.h1MarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h1MarginB.setFixedNumbersWidth(4)
        self.btnH1Props = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnH1Props.clicked.connect(self._resetH1Props)

        self.pixH1S = QLabel(self)
        self.pixH1T = QLabel(self)
        self.pixH1B = QLabel(self)

        self.addRow(
            self._build.getLabel("format.h1Margin"),
            [
                self.pixH1S,
                self.h1Size,
                iSp,
                self.pixH1T,
                self.h1MarginT,
                iSp,
                self.pixH1B,
                self.h1MarginB,
            ],
            button=self.btnH1Props,
        )

        # Heading 2
        self.h2Size = NDoubleSpinBox(self, minVal=0.8, maxVal=10.0, step=0.05)
        self.h2Size.setFixedNumbersWidth(4)
        self.h2MarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h2MarginT.setFixedNumbersWidth(4)
        self.h2MarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h2MarginB.setFixedNumbersWidth(4)
        self.btnH2Props = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnH2Props.clicked.connect(self._resetH2Props)

        self.pixH2S = QLabel(self)
        self.pixH2T = QLabel(self)
        self.pixH2B = QLabel(self)

        self.addRow(
            self._build.getLabel("format.h2Margin"),
            [
                self.pixH2S,
                self.h2Size,
                iSp,
                self.pixH2T,
                self.h2MarginT,
                iSp,
                self.pixH2B,
                self.h2MarginB,
            ],
            button=self.btnH2Props,
        )

        # Heading 3
        self.h3Size = NDoubleSpinBox(self, minVal=0.8, maxVal=10.0, step=0.05)
        self.h3Size.setFixedNumbersWidth(4)
        self.h3MarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h3MarginT.setFixedNumbersWidth(4)
        self.h3MarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h3MarginB.setFixedNumbersWidth(4)
        self.btnH3Props = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnH3Props.clicked.connect(self._resetH3Props)

        self.pixH3S = QLabel(self)
        self.pixH3T = QLabel(self)
        self.pixH3B = QLabel(self)

        self.addRow(
            self._build.getLabel("format.h3Margin"),
            [
                self.pixH3S,
                self.h3Size,
                iSp,
                self.pixH3T,
                self.h3MarginT,
                iSp,
                self.pixH3B,
                self.h3MarginB,
            ],
            button=self.btnH3Props,
        )

        # Heading 4
        self.h4Size = NDoubleSpinBox(self, minVal=0.8, maxVal=10.0, step=0.05)
        self.h4Size.setFixedNumbersWidth(4)
        self.h4MarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h4MarginT.setFixedNumbersWidth(4)
        self.h4MarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.h4MarginB.setFixedNumbersWidth(4)
        self.btnH4Props = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnH4Props.clicked.connect(self._resetH4Props)

        self.pixH4S = QLabel(self)
        self.pixH4T = QLabel(self)
        self.pixH4B = QLabel(self)

        self.addRow(
            self._build.getLabel("format.h4Margin"),
            [
                self.pixH4S,
                self.h4Size,
                iSp,
                self.pixH4T,
                self.h4MarginT,
                iSp,
                self.pixH4B,
                self.h4MarginB,
            ],
            button=self.btnH4Props,
        )

        # Text
        self.textMarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.textMarginT.setFixedNumbersWidth(4)
        self.textMarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.textMarginB.setFixedNumbersWidth(4)
        self.btnTextProps = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnTextProps.clicked.connect(self._resetTextProps)

        self.pixTTT = QLabel(self)
        self.pixTTB = QLabel(self)

        self.addRow(
            self._build.getLabel("format.textMargin"),
            [self.pixTTT, self.textMarginT, iSp, self.pixTTB, self.textMarginB],
            button=self.btnTextProps,
        )

        # Separator
        self.sepMarginT = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.sepMarginT.setFixedNumbersWidth(4)
        self.sepMarginB = NDoubleSpinBox(self, minVal=0.0, maxVal=10.0, step=0.1)
        self.sepMarginB.setFixedNumbersWidth(4)
        self.btnSepProps = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnSepProps.clicked.connect(self._resetSepProps)

        self.pixSPT = QLabel(self)
        self.pixSPB = QLabel(self)

        self.addRow(
            self._build.getLabel("format.sepMargin"),
            [self.pixSPT, self.sepMarginT, iSp, self.pixSPB, self.sepMarginB],
            button=self.btnSepProps,
        )

        # Empty Lines
        self.lineForMargin = NSwitch(self, height=iPx)
        self.lineForMargin.clicked.connect(self._updateTextMarginState)

        self.addRow(self._build.getLabel("format.lineForMargin"), self.lineForMargin)

        # Page Layout
        # ===========

        title = self._build.getLabel("format.grpPage")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        # Unit
        self.pageUnit = NComboBox(self)
        for key, name in nwLabels.PAGE_UNIT_NAME.items():
            self.pageUnit.addItem(trConst(name), key)

        self.addRow(self._build.getLabel("format.pageUnit"), self.pageUnit)

        # Page Size
        self.pageSize = NComboBox(self)
        for key, name in nwLabels.PAPER_NAME.items():
            self.pageSize.addItem(trConst(name), key)

        self.pageWidth = NDoubleSpinBox(self, minVal=1.0, maxVal=500.0)
        self.pageWidth.setFixedNumbersWidth(5)
        self.pageWidth.valueChanged.connect(self._pageSizeValueChanged)

        self.pageHeight = NDoubleSpinBox(self, minVal=1.0, maxVal=500.0)
        self.pageHeight.setFixedNumbersWidth(5)
        self.pageHeight.valueChanged.connect(self._pageSizeValueChanged)

        self.pixPSH = QLabel(self)
        self.pixPSW = QLabel(self)

        self.addRow(
            self._build.getLabel("format.pageSize"),
            [self.pageSize, iSp, self.pixPSW, self.pageWidth, iSp, self.pixPSH, self.pageHeight],
        )

        # Page Margins
        self.topMargin = NDoubleSpinBox(self)
        self.topMargin.setFixedNumbersWidth(5)

        self.bottomMargin = NDoubleSpinBox(self)
        self.bottomMargin.setFixedNumbersWidth(5)

        self.leftMargin = NDoubleSpinBox(self)
        self.leftMargin.setFixedNumbersWidth(5)

        self.rightMargin = NDoubleSpinBox(self)
        self.rightMargin.setFixedNumbersWidth(5)

        self.pixPMT = QLabel(self)
        self.pixPMB = QLabel(self)
        self.pixPML = QLabel(self)
        self.pixPMR = QLabel(self)

        self.addRow(
            self._build.getLabel("format.pageMargins"),
            [self.pixPMT, self.topMargin, iSp, self.pixPMB, self.bottomMargin],
        )
        self.addRow(
            "",
            [self.pixPML, self.leftMargin, iSp, self.pixPMR, self.rightMargin],
        )

        # Document Style
        # ==============

        title = self._build.getLabel("doc")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        # Header
        self.pageHeader = QLineEdit(self)
        self.pageHeader.setMinimumWidth(200)
        self.btnPageHeader = SHARED.theme.getIconButton(nwToolButton.REVERT, self)
        self.btnPageHeader.clicked.connect(self._resetPageHeader)
        self.addRow(
            self._build.getLabel("doc.pageHeader"),
            self.pageHeader,
            button=self.btnPageHeader,
            stretch=(1, 1),
        )

        self.pageCountOffset = NSpinBox(self, minVal=0, maxVal=999)
        self.pageCountOffset.setFixedNumbersWidth(4)
        self.addRow(self._build.getLabel("doc.pageCountOffset"), self.pageCountOffset)

        # Meta Language
        self.lblMetaLanguage = QLabel(self)
        self.lblMetaLanguage.setAlignment(QtAlignRightMiddle)
        self.lblMetaLanguage.setFixedWidth(200)

        self.metaLanguage = QLineEdit(self)
        self.metaLanguage.setAlignment(QtAlignCenter)
        self.metaLanguage.setFixedWidth(80)
        self.metaLanguage.textChanged.connect(self._refreshMetaLang)

        self.addRow(self._build.getLabel("doc.metaLanguage"), [self.lblMetaLanguage, 8, self.metaLanguage])

        # HTML Document
        # =============

        title = self._build.getLabel("html")
        section += 1
        self._sidebar.addButton(title, section)
        self.addGroupLabel(title, section)

        self.htmlAddStyles = NSwitch(self, height=iPx)
        self.addRow(self._build.getLabel("html.addStyles"), self.htmlAddStyles)

        self.htmlPreserveTabs = NSwitch(self, height=iPx)
        self.addRow(self._build.getLabel("html.preserveTabs"), self.htmlPreserveTabs)

        # Finalise
        self.finalise()

    def updateTheme(self, onInit: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _FormattingTab")

        if not onInit:
            self.ignoredKeywordsButton.refreshTheme()
            self.btnTextFont.refreshTheme()
            self.btnPageHeader.refreshTheme()
            self.btnTitleProps.refreshTheme()
            self.btnH1Props.refreshTheme()
            self.btnH2Props.refreshTheme()
            self.btnH3Props.refreshTheme()
            self.btnH4Props.refreshTheme()
            self.btnTextProps.refreshTheme()
            self.btnSepProps.refreshTheme()

        iPx = SHARED.theme.baseIconHeight

        fSize = SHARED.theme.getPixmap("fmt_size", iPx, iPx)
        self.pixH0S.setPixmap(fSize)
        self.pixH1S.setPixmap(fSize)
        self.pixH2S.setPixmap(fSize)
        self.pixH3S.setPixmap(fSize)
        self.pixH4S.setPixmap(fSize)

        tMargin = SHARED.theme.getPixmap("margin_top", iPx, iPx)
        bMargin = SHARED.theme.getPixmap("margin_bottom", iPx, iPx)
        self.pixH0T.setPixmap(tMargin)
        self.pixH0B.setPixmap(bMargin)
        self.pixH1T.setPixmap(tMargin)
        self.pixH1B.setPixmap(bMargin)
        self.pixH2T.setPixmap(tMargin)
        self.pixH2B.setPixmap(bMargin)
        self.pixH3T.setPixmap(tMargin)
        self.pixH3B.setPixmap(bMargin)
        self.pixH4T.setPixmap(tMargin)
        self.pixH4B.setPixmap(bMargin)
        self.pixTTT.setPixmap(tMargin)
        self.pixTTB.setPixmap(bMargin)
        self.pixSPT.setPixmap(tMargin)
        self.pixSPB.setPixmap(bMargin)
        self.pixPMT.setPixmap(tMargin)
        self.pixPMB.setPixmap(bMargin)

        self.pixPSH.setPixmap(SHARED.theme.getPixmap("fit_height", iPx, iPx))
        self.pixPSW.setPixmap(SHARED.theme.getPixmap("fit_width", iPx, iPx))
        self.pixPML.setPixmap(SHARED.theme.getPixmap("margin_left", iPx, iPx))
        self.pixPMR.setPixmap(SHARED.theme.getPixmap("margin_right", iPx, iPx))

        self.pageSize.updateStyle()
        self.pageUnit.updateStyle()

    def loadContent(self) -> None:
        """Populate the widgets."""
        # Text Content
        # ============

        self.incBodyText.setChecked(self._build.getBool("text.includeBodyText"))
        self.incSynopsis.setChecked(self._build.getBool("text.includeSynopsis"))
        self.incComments.setChecked(self._build.getBool("text.includeComments"))
        self.incStory.setChecked(self._build.getBool("text.includeStory"))
        self.incNotes.setChecked(self._build.getBool("text.includeNotes"))
        self.incKeywords.setChecked(self._build.getBool("text.includeKeywords"))
        self.ignoredKeywords.setText(self._build.getStr("text.ignoredKeywords"))
        self.addNoteHead.setChecked(self._build.getBool("text.addNoteHeadings"))
        self._updateIgnoredKeywords()

        # Text Format
        # ===========

        font = QFont()
        font.fromString(self._build.getStr("format.textFont"))
        self._textFont = fontMatcher(font)

        self.textFont.setText(describeFont(self._textFont))
        self.textFont.setCursorPosition(0)

        self.lineHeight.setValue(self._build.getFloat("format.lineHeight"))
        self.justifyText.setChecked(self._build.getBool("format.justifyText"))
        self.justifyOnBreak.setChecked(self._build.getBool("format.justifyOnBreak"))
        self.stripUnicode.setChecked(self._build.getBool("format.stripUnicode"))
        self.replaceTabs.setChecked(self._build.getBool("format.replaceTabs"))
        self.keepBreaks.setChecked(self._build.getBool("format.keepBreaks"))
        self.showDialogue.setChecked(self._build.getBool("format.showDialogue"))

        # Heading Format
        # ==============

        self.colorHeadings.setChecked(self._build.getBool("format.colorHeadings"))
        self.boldHeadings.setChecked(self._build.getBool("format.boldHeadings"))
        self.upperHeadings.setChecked(self._build.getBool("format.upperHeadings"))

        # First Line Indent
        # =================

        self.firstIndent.setChecked(self._build.getBool("format.firstLineIndent"))
        self.indentWidth.setValue(self._build.getFloat("format.firstIndentWidth"))
        self.indentFirstPar.setChecked(self._build.getBool("format.indentFirstPar"))

        # Text Margins
        # ============

        self.titleSize.setValue(self._build.getFloat("format.titleSize"))
        self.h1Size.setValue(self._build.getFloat("format.h1Size"))
        self.h2Size.setValue(self._build.getFloat("format.h2Size"))
        self.h3Size.setValue(self._build.getFloat("format.h3Size"))
        self.h4Size.setValue(self._build.getFloat("format.h4Size"))

        self.titleMarginT.setValue(self._build.getFloat("format.titleMarginT"))
        self.titleMarginB.setValue(self._build.getFloat("format.titleMarginB"))
        self.h1MarginT.setValue(self._build.getFloat("format.h1MarginT"))
        self.h1MarginB.setValue(self._build.getFloat("format.h1MarginB"))
        self.h2MarginT.setValue(self._build.getFloat("format.h2MarginT"))
        self.h2MarginB.setValue(self._build.getFloat("format.h2MarginB"))
        self.h3MarginT.setValue(self._build.getFloat("format.h3MarginT"))
        self.h3MarginB.setValue(self._build.getFloat("format.h3MarginB"))
        self.h4MarginT.setValue(self._build.getFloat("format.h4MarginT"))
        self.h4MarginB.setValue(self._build.getFloat("format.h4MarginB"))
        self.textMarginT.setValue(self._build.getFloat("format.textMarginT"))
        self.textMarginB.setValue(self._build.getFloat("format.textMarginB"))
        self.sepMarginT.setValue(self._build.getFloat("format.sepMarginT"))
        self.sepMarginB.setValue(self._build.getFloat("format.sepMarginB"))
        self.lineForMargin.setChecked(self._build.getBool("format.lineForMargin"))

        self._updateTextMarginState()

        # Page Layout
        # ===========

        pageUnit = self._build.getStr("format.pageUnit")
        index = self.pageUnit.findData(pageUnit)
        if index >= 0:
            self.pageUnit.setCurrentIndex(index)
            self._unitScale = nwLabels.PAGE_UNIT_SCALE.get(pageUnit, 1.0)
            self._changeUnit(index)

        self.pageWidth.setValue(self._build.getFloat("format.pageWidth"))
        self.pageHeight.setValue(self._build.getFloat("format.pageHeight"))
        self.topMargin.setValue(self._build.getFloat("format.topMargin"))
        self.bottomMargin.setValue(self._build.getFloat("format.bottomMargin"))
        self.leftMargin.setValue(self._build.getFloat("format.leftMargin"))
        self.rightMargin.setValue(self._build.getFloat("format.rightMargin"))

        pageSize = self._build.getStr("format.pageSize")
        index = self.pageSize.findData(pageSize)
        if index >= 0:
            self.pageSize.setCurrentIndex(index)
            self._changePageSize(index)

        self.pageUnit.currentIndexChanged.connect(self._changeUnit)
        self.pageSize.currentIndexChanged.connect(self._changePageSize)

        # Document
        # ========

        self.metaLanguage.setText(processLangCode(self._build.getStr("doc.metaLanguage")))
        self.pageHeader.setText(self._build.getStr("doc.pageHeader"))
        self.pageCountOffset.setValue(self._build.getInt("doc.pageCountOffset"))
        self.pageHeader.setCursorPosition(0)

        # HTML Document
        # =============

        self.htmlAddStyles.setChecked(self._build.getBool("html.addStyles"))
        self.htmlPreserveTabs.setChecked(self._build.getBool("html.preserveTabs"))

    def saveContent(self) -> None:
        """Save choices back into build object."""
        # Text Content
        self._updateIgnoredKeywords()
        self._build.setValue("text.includeBodyText", self.incBodyText.isChecked())
        self._build.setValue("text.includeSynopsis", self.incSynopsis.isChecked())
        self._build.setValue("text.includeComments", self.incComments.isChecked())
        self._build.setValue("text.includeStory", self.incStory.isChecked())
        self._build.setValue("text.includeNotes", self.incNotes.isChecked())
        self._build.setValue("text.includeKeywords", self.incKeywords.isChecked())
        self._build.setValue("text.ignoredKeywords", self.ignoredKeywords.text())
        self._build.setValue("text.addNoteHeadings", self.addNoteHead.isChecked())

        # Text Format
        self._build.setValue("format.textFont", self._textFont.toString())
        self._build.setValue("format.lineHeight", self.lineHeight.value())

        self._build.setValue("format.justifyText", self.justifyText.isChecked())
        self._build.setValue("format.justifyOnBreak", self.justifyOnBreak.isChecked())
        self._build.setValue("format.stripUnicode", self.stripUnicode.isChecked())
        self._build.setValue("format.replaceTabs", self.replaceTabs.isChecked())
        self._build.setValue("format.keepBreaks", self.keepBreaks.isChecked())
        self._build.setValue("format.showDialogue", self.showDialogue.isChecked())

        # Heading Format
        self._build.setValue("format.colorHeadings", self.colorHeadings.isChecked())
        self._build.setValue("format.boldHeadings", self.boldHeadings.isChecked())
        self._build.setValue("format.upperHeadings", self.upperHeadings.isChecked())

        # First Line Indent
        self._build.setValue("format.firstLineIndent", self.firstIndent.isChecked())
        self._build.setValue("format.firstIndentWidth", self.indentWidth.value())
        self._build.setValue("format.indentFirstPar", self.indentFirstPar.isChecked())

        # Text Margins
        self._build.setValue("format.titleSize", self.titleSize.value())
        self._build.setValue("format.h1Size", self.h1Size.value())
        self._build.setValue("format.h2Size", self.h2Size.value())
        self._build.setValue("format.h3Size", self.h3Size.value())
        self._build.setValue("format.h4Size", self.h4Size.value())

        self._build.setValue("format.titleMarginT", self.titleMarginT.value())
        self._build.setValue("format.titleMarginB", self.titleMarginB.value())
        self._build.setValue("format.h1MarginT", self.h1MarginT.value())
        self._build.setValue("format.h1MarginB", self.h1MarginB.value())
        self._build.setValue("format.h2MarginT", self.h2MarginT.value())
        self._build.setValue("format.h2MarginB", self.h2MarginB.value())
        self._build.setValue("format.h3MarginT", self.h3MarginT.value())
        self._build.setValue("format.h3MarginB", self.h3MarginB.value())
        self._build.setValue("format.h4MarginT", self.h4MarginT.value())
        self._build.setValue("format.h4MarginB", self.h4MarginB.value())
        self._build.setValue("format.textMarginT", self.textMarginT.value())
        self._build.setValue("format.textMarginB", self.textMarginB.value())
        self._build.setValue("format.sepMarginT", self.sepMarginT.value())
        self._build.setValue("format.sepMarginB", self.sepMarginB.value())
        self._build.setValue("format.lineForMargin", self.lineForMargin.isChecked())

        # Page Layout
        self._build.setValue("format.pageUnit", str(self.pageUnit.currentData()))
        self._build.setValue("format.pageSize", str(self.pageSize.currentData()))
        self._build.setValue("format.pageWidth", self.pageWidth.value())
        self._build.setValue("format.pageHeight", self.pageHeight.value())
        self._build.setValue("format.topMargin", self.topMargin.value())
        self._build.setValue("format.bottomMargin", self.bottomMargin.value())
        self._build.setValue("format.leftMargin", self.leftMargin.value())
        self._build.setValue("format.rightMargin", self.rightMargin.value())

        # Documents
        metaLanguage = processLangCode(self.metaLanguage.text())

        self._build.setValue("doc.metaLanguage", metaLanguage)
        self._build.setValue("doc.pageHeader", self.pageHeader.text())
        self._build.setValue("doc.pageCountOffset", self.pageCountOffset.value())

        self.metaLanguage.setText(metaLanguage)

        # HTML Document
        self._build.setValue("html.addStyles", self.htmlAddStyles.isChecked())
        self._build.setValue("html.preserveTabs", self.htmlPreserveTabs.isChecked())

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _selectFont(self) -> None:
        """Open the QFontDialog and set a font for the font style."""
        font, status = SHARED.getFont(self._textFont, CONFIG.nativeFont)
        if status:
            self._textFont = fontMatcher(font)
            self.textFont.setText(describeFont(self._textFont))
            self.textFont.setCursorPosition(0)

    @pyqtSlot(int)
    def _changeUnit(self, index: int) -> None:
        """Process current unit change to recalculate sizes."""
        newUnit = self.pageUnit.itemData(index)
        newScale = nwLabels.PAGE_UNIT_SCALE.get(newUnit, 1.0)
        reScale = self._unitScale / newScale

        pageWidth = self.pageWidth.value() * reScale
        pageHeight = self.pageHeight.value() * reScale
        topMargin = self.topMargin.value() * reScale
        bottomMargin = self.bottomMargin.value() * reScale
        leftMargin = self.leftMargin.value() * reScale
        rightMargin = self.rightMargin.value() * reScale

        isMM = newUnit == "mm"
        nDec = 1 if isMM else 2
        nStep = 1.0 if isMM else 0.1
        pMax = 500.0 if isMM else 50.0
        pMin = 10.0 if isMM else 1.0
        mMax = 150.0 if isMM else 15.0

        self.pageWidth.blockSignals(True)
        self.pageWidth.setDecimals(nDec)
        self.pageWidth.setSingleStep(nStep)
        self.pageWidth.setMaximum(pMax)
        self.pageWidth.setMinimum(pMin)
        self.pageWidth.setValue(pageWidth)
        self.pageWidth.blockSignals(False)

        self.pageHeight.blockSignals(True)
        self.pageHeight.setDecimals(nDec)
        self.pageHeight.setSingleStep(nStep)
        self.pageHeight.setMaximum(pMax)
        self.pageHeight.setMinimum(pMin)
        self.pageHeight.setValue(pageHeight)
        self.pageHeight.blockSignals(False)

        self.topMargin.setDecimals(nDec)
        self.topMargin.setSingleStep(nStep)
        self.topMargin.setMaximum(mMax)
        self.topMargin.setValue(topMargin)

        self.bottomMargin.setDecimals(nDec)
        self.bottomMargin.setSingleStep(nStep)
        self.bottomMargin.setMaximum(mMax)
        self.bottomMargin.setValue(bottomMargin)

        self.leftMargin.setDecimals(nDec)
        self.leftMargin.setSingleStep(nStep)
        self.leftMargin.setMaximum(mMax)
        self.leftMargin.setValue(leftMargin)

        self.rightMargin.setDecimals(nDec)
        self.rightMargin.setSingleStep(nStep)
        self.rightMargin.setMaximum(mMax)
        self.rightMargin.setValue(rightMargin)

        self._unitScale = newScale
        self._changePageSize(self.pageSize.currentIndex())

    @pyqtSlot(int)
    def _changePageSize(self, index: int) -> None:
        """Process page size change."""
        w, h = nwLabels.PAPER_SIZE[self.pageSize.itemData(index)] if index >= 0 else (-1.0, -1.0)
        if w > 0.0 and h > 0.0:
            self.pageWidth.blockSignals(True)
            self.pageWidth.setValue(w / self._unitScale)
            self.pageWidth.blockSignals(False)
            self.pageHeight.blockSignals(True)
            self.pageHeight.setValue(h / self._unitScale)
            self.pageHeight.blockSignals(False)

    @pyqtSlot()
    def _pageSizeValueChanged(self) -> None:
        """Process that the user has changed the page size spin boxes,
        so we flip the page size box to Custom.
        """
        if (index := self.pageSize.findData("Custom")) >= 0:  # pragma: no branch
            self.pageSize.setCurrentIndex(index)

    @pyqtSlot()
    def _resetPageHeader(self) -> None:
        """Reset the document header format to default."""
        self.pageHeader.setText(nwHeadFmt.DOC_AUTO)
        self.pageHeader.setCursorPosition(0)

    @pyqtSlot()
    def _resetTitleProps(self) -> None:
        """Reset the title size and margins to default."""
        self.titleSize.setValue(nwStyles.H_SIZES[0])
        self.titleMarginT.setValue(nwStyles.T_MARGIN["H0"][0])
        self.titleMarginB.setValue(nwStyles.T_MARGIN["H0"][1])

    @pyqtSlot()
    def _resetH1Props(self) -> None:
        """Reset the H1 size and margins to default."""
        self.h1Size.setValue(nwStyles.H_SIZES[1])
        self.h1MarginT.setValue(nwStyles.T_MARGIN["H1"][0])
        self.h1MarginB.setValue(nwStyles.T_MARGIN["H1"][1])

    @pyqtSlot()
    def _resetH2Props(self) -> None:
        """Reset the H2 size and margins to default."""
        self.h2Size.setValue(nwStyles.H_SIZES[2])
        self.h2MarginT.setValue(nwStyles.T_MARGIN["H2"][0])
        self.h2MarginB.setValue(nwStyles.T_MARGIN["H2"][1])

    @pyqtSlot()
    def _resetH3Props(self) -> None:
        """Reset the H3 size and margins to default."""
        self.h3Size.setValue(nwStyles.H_SIZES[3])
        self.h3MarginT.setValue(nwStyles.T_MARGIN["H3"][0])
        self.h3MarginB.setValue(nwStyles.T_MARGIN["H3"][1])

    @pyqtSlot()
    def _resetH4Props(self) -> None:
        """Reset the H4 size and margins to default."""
        self.h4Size.setValue(nwStyles.H_SIZES[4])
        self.h4MarginT.setValue(nwStyles.T_MARGIN["H4"][0])
        self.h4MarginB.setValue(nwStyles.T_MARGIN["H4"][1])

    @pyqtSlot()
    def _resetTextProps(self) -> None:
        """Reset the text size and margins to default."""
        self.textMarginT.setValue(nwStyles.T_MARGIN["TT"][0])
        self.textMarginB.setValue(nwStyles.T_MARGIN["TT"][1])

    @pyqtSlot()
    def _resetSepProps(self) -> None:
        """Reset the separator size and margins to default."""
        self.sepMarginT.setValue(nwStyles.T_MARGIN["SP"][0])
        self.sepMarginB.setValue(nwStyles.T_MARGIN["SP"][1])

    @pyqtSlot()
    def _refreshMetaLang(self) -> None:
        """Update the meta language helper info."""
        code = self.metaLanguage.text().strip()
        self.lblMetaLanguage.setText(languageName(code))

    @pyqtSlot()
    def _updateTextMarginState(self) -> None:
        """Update the enabled state of text margin settings."""
        enabled = not self.lineForMargin.isChecked()
        self.titleMarginT.setEnabled(enabled)
        self.titleMarginB.setEnabled(enabled)
        self.h1MarginT.setEnabled(enabled)
        self.h1MarginB.setEnabled(enabled)
        self.h2MarginT.setEnabled(enabled)
        self.h2MarginB.setEnabled(enabled)
        self.h3MarginT.setEnabled(enabled)
        self.h3MarginB.setEnabled(enabled)
        self.h4MarginT.setEnabled(enabled)
        self.h4MarginB.setEnabled(enabled)
        self.textMarginT.setEnabled(enabled)
        self.textMarginB.setEnabled(enabled)
        self.sepMarginT.setEnabled(enabled)
        self.sepMarginB.setEnabled(enabled)

    @pyqtSlot(QAction)
    def _ignoredKeywordSelected(self, action: QAction) -> None:
        """Process the user selecting an ignored keyword from the menu."""
        if isinstance(keyword := action.data(), str):
            self._updateIgnoredKeywords(keyword)

    ##
    #  Internal Functions
    ##

    def _updateIgnoredKeywords(self, keyword: str | None = None) -> None:
        """Update the ignored keywords list."""
        current = [x.lower().strip() for x in self.ignoredKeywords.text().split(",")]
        if keyword:
            current.append(keyword)
        verified = {x for x in current if x in nwKeyWords.VALID_KEYS}
        self.ignoredKeywords.setText(", ".join(verified))
