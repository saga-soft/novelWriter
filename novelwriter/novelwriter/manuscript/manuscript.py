"""
novelWriter - GUI Manuscript Tool
=================================

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

from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import (
    QCloseEvent,
    QColor,
    QCursor,
    QDesktopServices,
    QFont,
    QPageLayout,
    QPalette,
    QResizeEvent,
    QTextDocument,
)
from PyQt6.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextBrowser,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatInt, formatPercent, fuzzyTime
from novelwriter.constants import nwHeadFmt, nwLabels, nwStats, nwUnicode, trStats
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.modified import NFlatIconButton, NToolDialog
from novelwriter.extensions.progressbars import NProgressCircle
from novelwriter.extensions.switch import NSwitch
from novelwriter.extensions.tabwidget import NTabWidget
from novelwriter.formats.tokenizer import HeadingFormatter
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.manuscript.buildsettings import BuildCollection, BuildSettings
from novelwriter.manuscript.docbuild import DocumentBuilder
from novelwriter.manuscript.manusbuild import GuiManuscriptBuild
from novelwriter.manuscript.manussettings import GuiBuildSettings
from novelwriter.types import (
    QtAlignCenter,
    QtAlignRight,
    QtAlignTop,
    QtHeaderStretch,
    QtHeaderToContents,
    QtUserRole,
)

if TYPE_CHECKING:
    from novelwriter.guimain import GuiMain

logger = logging.getLogger(__name__)


class GuiManuscript(NToolDialog):
    """GUI Tools: Manuscript Tool.

    The dialog displays all the users build definitions, a preview panel
    for the manuscript, and can trigger the actual build dialog to build
    a document directly to disk.
    """

    D_KEY = QtUserRole

    def __init__(self, parent: GuiMain) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiManuscript")
        self.setObjectName("GuiManuscript")

        self._builds = BuildCollection(SHARED.project)
        self._buildMap: dict[str, QListWidgetItem] = {}
        self._generatingPreview = False

        self.setWindowTitle(self.tr("Manuscript Build"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize

        options = SHARED.project.options
        self.resize(
            options.getInt("GuiManuscript", "winWidth", 900),
            options.getInt("GuiManuscript", "winHeight", 600),
        )

        # Build Controls
        # ==============

        self.tbAdd = NFlatIconButton(self, iSz, "add:add")
        self.tbAdd.setToolTip(self.tr("Add New Build"))
        self.tbAdd.clicked.connect(self._createNewBuild)

        self.tbDel = NFlatIconButton(self, iSz, "remove:remove")
        self.tbDel.setToolTip(self.tr("Delete Selected Build"))
        self.tbDel.clicked.connect(self._deleteSelectedBuild)

        self.tbCopy = NFlatIconButton(self, iSz, "copy:action")
        self.tbCopy.setToolTip(self.tr("Duplicate Selected Build"))
        self.tbCopy.clicked.connect(self._copySelectedBuild)

        self.tbEdit = NFlatIconButton(self, iSz, "edit:change")
        self.tbEdit.setToolTip(self.tr("Edit Selected Build"))
        self.tbEdit.clicked.connect(self._editSelectedBuild)

        self.lblBuilds = QLabel(self.tr("Build Settings"), self)
        self.lblBuilds.setFont(SHARED.theme.guiFontB)

        self.listToolBox = QHBoxLayout()
        self.listToolBox.addWidget(self.lblBuilds)
        self.listToolBox.addStretch(1)
        self.listToolBox.addWidget(self.tbAdd)
        self.listToolBox.addWidget(self.tbDel)
        self.listToolBox.addWidget(self.tbCopy)
        self.listToolBox.addWidget(self.tbEdit)
        self.listToolBox.setSpacing(0)

        # Builds
        # ======

        self.buildList = QListWidget(self)
        self.buildList.setIconSize(iSz)
        self.buildList.doubleClicked.connect(self._editSelectedBuild)
        self.buildList.currentItemChanged.connect(self._updateBuildDetails)
        self.buildList.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.buildList.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)

        # Details Tabs
        # ============

        self.buildDetails = _DetailsWidget(self)
        self.buildDetails.setColumnWidth(options.getInt("GuiManuscript", "detailsWidth", 100))

        self.buildOutline = _OutlineWidget(self)

        self.buildStats = _StatisticsWidget(self)
        self.buildStats.setExpandedState(SHARED.project.options.getList("GuiManuscript", "statsExpanded", []))

        self.detailsTabs = NTabWidget(self)
        self.detailsTabs.addTab(self.buildDetails, self.tr("Details"))
        self.detailsTabs.addTab(self.buildOutline, self.tr("Outline"))
        self.detailsTabs.addTab(self.buildStats, self.tr("Statistics"))

        self.buildSplit = QSplitter(Qt.Orientation.Vertical, self)
        self.buildSplit.addWidget(self.buildList)
        self.buildSplit.addWidget(self.detailsTabs)
        self.buildSplit.setSizes([
            options.getInt("GuiManuscript", "listHeight", 50),
            options.getInt("GuiManuscript", "detailsHeight", 50),
        ])

        # Process Controls
        # ================

        self.btnPreview = SHARED.theme.getStandardButton(nwStandardButton.PREVIEW, self)
        self.btnPreview.clicked.connect(self._generatePreview)

        self.btnPrint = SHARED.theme.getStandardButton(nwStandardButton.PRINT, self)
        self.btnPrint.clicked.connect(self._printDocument)

        self.btnBuild = SHARED.theme.getStandardButton(nwStandardButton.BUILD, self)
        self.btnBuild.clicked.connect(self._buildManuscript)

        self.btnClose = SHARED.theme.getStandardButton(nwStandardButton.CLOSE, self)
        self.btnClose.clicked.connect(self.closeDialog)

        self.processBox = QGridLayout()
        self.processBox.addWidget(self.btnPreview, 0, 0)
        self.processBox.addWidget(self.btnPrint, 0, 1)
        self.processBox.addWidget(self.btnBuild, 1, 0)
        self.processBox.addWidget(self.btnClose, 1, 1)

        # Preview Options
        # ===============

        self.countsLabel = QLabel(self)

        self.swtNewPage = NSwitch(self, height=iPx)
        self.swtNewPage.setChecked(options.getBool("GuiManuscript", "showNewPage", True))
        self.swtNewPage.clicked.connect(self._generatePreview)

        self.lblNewPage = QLabel(self.tr("Show page breaks"), self)
        self.lblNewPage.setBuddy(self.swtNewPage)

        # Assemble GUI
        # ============

        self.docPreview = _PreviewWidget(self)

        self.docBar = QHBoxLayout()
        self.docBar.addWidget(self.countsLabel, 1, QtAlignTop)
        self.docBar.addWidget(self.lblNewPage, 0, QtAlignTop)
        self.docBar.addWidget(self.swtNewPage, 0, QtAlignTop)
        self.docBar.setContentsMargins(0, 0, 0, 0)

        self.docBox = QVBoxLayout()
        self.docBox.addWidget(self.docPreview, 1)
        self.docBox.addLayout(self.docBar, 0)
        self.docBox.setContentsMargins(0, 0, 0, 0)

        self.docWdiget = QWidget(self)
        self.docWdiget.setLayout(self.docBox)

        self.controlBox = QVBoxLayout()
        self.controlBox.addLayout(self.listToolBox, 0)
        self.controlBox.addWidget(self.buildSplit, 1)
        self.controlBox.addLayout(self.processBox, 0)
        self.controlBox.setContentsMargins(0, 0, 0, 0)

        self.optsWidget = QWidget(self)
        self.optsWidget.setLayout(self.controlBox)

        self.mainSplit = QSplitter(self)
        self.mainSplit.addWidget(self.optsWidget)
        self.mainSplit.addWidget(self.docWdiget)
        self.mainSplit.setCollapsible(0, False)
        self.mainSplit.setCollapsible(1, False)
        self.mainSplit.setStretchFactor(0, 0)
        self.mainSplit.setStretchFactor(1, 1)
        self.mainSplit.setSizes([
            options.getInt("GuiManuscript", "optsWidth", 225),
            options.getInt("GuiManuscript", "viewWidth", 675),
        ])

        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.mainSplit)

        self.setLayout(self.outerBox)
        self.setSizeGripEnabled(True)

        self.updateTheme(init=True)

        # Signals
        self.buildOutline.outlineEntryClicked.connect(self.docPreview.navigateTo)

        logger.debug("Ready: GuiManuscript")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiManuscript")

    def loadContent(self) -> None:
        """Load dialog content from project data."""
        if len(self._builds) == 0:
            build = BuildSettings()
            build.setName(self.tr("My Manuscript"))
            self._builds.setBuild(build)
            selected = build.buildID
        else:
            selected = self._builds.lastBuild

        self._updateBuildsList()
        if selected in self._buildMap:
            self.buildList.setCurrentItem(self._buildMap[selected])
            QTimer.singleShot(200, self._generatePreview)

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiManuscript, init=%s", init)

        if not init:
            self.btnPreview.refreshTheme()
            self.btnPrint.refreshTheme()
            self.btnBuild.refreshTheme()
            self.btnClose.refreshTheme()

        self.detailsTabs.refreshTheme()

        self.buildDetails.updateTheme()
        self.buildOutline.updateTheme()
        self.docPreview.updateTheme()

        for obj in SHARED.mainGui.children():
            if isinstance(obj, GuiBuildSettings):
                obj.updateTheme()

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the user closing the window so we can save GUI
        settings. We also check that we don't have a build settings
        dialog open.
        """
        self._saveSettings()
        for obj in SHARED.mainGui.children():
            # Make sure we don't have any settings windows open
            if isinstance(obj, GuiBuildSettings) and obj.isVisible():
                obj.close()
        event.accept()
        self.softDelete()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _createNewBuild(self) -> None:
        """Open the build settings dialog for a new build."""
        build = BuildSettings()
        build.setName(self.tr("My Manuscript"))
        self._openSettingsDialog(build)

    @pyqtSlot()
    def _editSelectedBuild(self) -> None:
        """Edit the currently selected build settings entry."""
        if build := self._getSelectedBuild():
            self._openSettingsDialog(build)

    @pyqtSlot()
    def _copySelectedBuild(self) -> None:
        """Copy the currently selected build settings entry."""
        if build := self._getSelectedBuild():
            new = BuildSettings.duplicate(build)
            self._builds.setBuild(new)
            self._updateBuildsList()
            if item := self._buildMap.get(new.buildID):  # pragma: no branch
                item.setSelected(True)

    @pyqtSlot("QListWidgetItem*", "QListWidgetItem*")
    def _updateBuildDetails(self, current: QListWidgetItem, previous: QListWidgetItem) -> None:
        """Process change of build selection to update the details."""
        if current and (build := self._builds.getBuild(current.data(self.D_KEY))):
            self.buildDetails.updateInfo(build)

    @pyqtSlot()
    def _deleteSelectedBuild(self) -> None:
        """Delete the currently selected build settings entry."""
        if (build := self._getSelectedBuild()) and SHARED.question(self.tr("Delete build '{0}'?").format(build.name)):
            if dialog := self._findSettingsDialog(build.buildID):
                dialog.close()
            self._builds.removeBuild(build.buildID)
            self._updateBuildsList()

    @pyqtSlot(BuildSettings, bool)
    def _processNewSettings(self, build: BuildSettings, refreshPreview: bool) -> None:
        """Process new build settings from the settings dialog."""
        self._builds.setBuild(build)
        self._updateBuildItem(build)
        if refreshPreview:
            self.buildList.setCurrentItem(self._buildMap[build.buildID])
            self._generatePreview()
        elif (item := self.buildList.currentItem()) and item.data(self.D_KEY) == build.buildID:
            self._updateBuildDetails(item, item)

    @pyqtSlot()
    def _generatePreview(self) -> None:
        """Run the document builder on the current build settings for
        the preview widget.
        """
        # Re-entrancy guard
        if self._generatingPreview or not (build := self._getSelectedBuild()):
            return

        self._generatingPreview = True
        self.btnPreview.setEnabled(False)
        try:
            start = time()
            showNewPage = self.swtNewPage.isChecked()

            # Make sure editor content is saved before we start
            SHARED.saveEditor()

            docBuild = DocumentBuilder(SHARED.project, build)
            docBuild.queueAll()

            self.docPreview.beginNewBuild(len(docBuild))
            for step, _ in docBuild.iterBuildPreview(showNewPage):
                self.docPreview.buildStep(step + 1)
                QApplication.processEvents()

            buildObj = docBuild.lastBuild
            assert isinstance(buildObj, ToQTextDocument)

            font = QFont()
            font.fromString(build.getStr("format.textFont"))
            withDialog = build.getBool("format.showDialogue")

            self.docPreview.setTextFont(font)
            self.docPreview.setContent(buildObj.document)
            self.docPreview.setBuildName(build.name)

            self.buildOutline.updateOutline(buildObj.textOutline)
            self.buildStats.updateStats(buildObj.textStats, withDialog)
            self._updateCountsLabel(buildObj.textStats, withDialog)

            logger.debug("Build completed in %.3f ms", 1000 * (time() - start))
        finally:
            self.btnPreview.setEnabled(True)
            self._generatingPreview = False

        return

    @pyqtSlot()
    def _buildManuscript(self) -> None:
        """Open the build dialog and build the manuscript."""
        if build := self._getSelectedBuild():
            dialog = GuiManuscriptBuild(self, build)
            dialog.exec()

            # After the build is done, save build settings changes
            if build.changed:
                self._builds.setBuild(build)

    @pyqtSlot()
    def _printDocument(self) -> None:
        """Open the print preview dialog."""
        preview = QPrintPreviewDialog(self)
        preview.paintRequested.connect(self.docPreview.printPreview)
        preview.exec()

    ##
    #  Internal Functions
    ##

    def _getSelectedBuild(self) -> BuildSettings | None:
        """Get the currently selected build. If none are selected,
        automatically select the first one.
        """
        items = self.buildList.selectedItems()
        item = items[0] if items else self.buildList.item(0)
        if item:
            build = self._builds.getBuild(item.data(self.D_KEY))
            if isinstance(build, BuildSettings):
                return build
        return None

    def _saveSettings(self) -> None:
        """Save the user GUI settings."""
        buildOrder = [item.data(self.D_KEY) for i in range(self.buildList.count()) if (item := self.buildList.item(i))]

        current = self.buildList.currentItem()
        lastBuild = current.data(self.D_KEY) if isinstance(current, QListWidgetItem) else ""

        self._builds.setBuildsState(lastBuild, buildOrder)

        mainSplit = self.mainSplit.sizes()
        buildSplit = self.buildSplit.sizes()
        detailsWidth = self.buildDetails.getColumnWidth()
        detailsExpanded = self.buildDetails.getExpandedState()
        statsExpanded = self.buildStats.getExpandedState()
        showNewPage = self.swtNewPage.isChecked()

        logger.debug("Saving State: GuiManuscript")
        pOptions = SHARED.project.options
        pOptions.setValue("GuiManuscript", "winWidth", self.width())
        pOptions.setValue("GuiManuscript", "winHeight", self.height())
        pOptions.setValue("GuiManuscript", "optsWidth", mainSplit[0])
        pOptions.setValue("GuiManuscript", "viewWidth", mainSplit[1])
        pOptions.setValue("GuiManuscript", "listHeight", buildSplit[0])
        pOptions.setValue("GuiManuscript", "detailsHeight", buildSplit[1])
        pOptions.setValue("GuiManuscript", "detailsWidth", detailsWidth)
        pOptions.setValue("GuiManuscript", "detailsExpanded", detailsExpanded)
        pOptions.setValue("GuiManuscript", "statsExpanded", statsExpanded)
        pOptions.setValue("GuiManuscript", "showNewPage", showNewPage)
        pOptions.saveSettings()

    def _openSettingsDialog(self, build: BuildSettings) -> None:
        """Open the build settings dialog."""
        if dialog := self._findSettingsDialog(build.buildID):
            dialog.activateDialog()
            return

        dialog = GuiBuildSettings(SHARED.mainGui, build)
        dialog.activateDialog()
        dialog.loadContent()
        dialog.newSettingsReady.connect(self._processNewSettings)

        return

    def _updateBuildsList(self) -> None:
        """Update the list of available builds."""
        self.buildList.clear()
        self._buildMap.clear()
        for key, name in self._builds.builds():
            bItem = QListWidgetItem()
            bItem.setText(name)
            bItem.setIcon(SHARED.theme.getIcon("build_settings:action"))
            bItem.setData(self.D_KEY, key)
            self.buildList.addItem(bItem)
            self._buildMap[key] = bItem

    def _updateBuildItem(self, build: BuildSettings) -> None:
        """Update the entry of a specific build item."""
        if item := self._buildMap.get(build.buildID):
            item.setText(build.name)
        else:  # Probably a new item
            self._updateBuildsList()

    def _findSettingsDialog(self, buildID: str) -> GuiBuildSettings | None:
        """Return an open build settings dialog for a given build, if
        one exists.
        """
        for obj in SHARED.mainGui.children():
            if isinstance(obj, GuiBuildSettings) and obj.buildID == buildID:
                return obj
        return None

    def _updateCountsLabel(self, data: dict[str, int], withDialog: bool) -> None:
        """Update the counts label with the given stats."""
        words = data.get(nwStats.WORDS, 0)
        chars = data.get(nwStats.CHARS, 0)
        text = [
            f"{trStats(nwLabels.STATS_NAME[nwStats.WORDS])}: {formatInt(words)}",
            f"{trStats(nwLabels.STATS_NAME[nwStats.CHARS])}: {formatInt(chars)}",
        ]
        if withDialog:
            textChars = data.get(nwStats.CHARS_TEXT, 0)
            dialogChars = data.get(nwStats.CHARS_DIALOG, 0)
            dialogRatio = formatPercent(dialogChars, divisor=textChars)
            text.append(f"{trStats(nwLabels.STATS_NAME[nwStats.DIALOG_RATIO])}: {dialogRatio}")

        self.countsLabel.setText("\u2003".join(text))


class _DetailsWidget(QWidget):
    """The details of the selected build settings."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._initExpanded = True
        self._build = None

        # Tree Widget
        self.listView = QTreeWidget(self)
        self.listView.setHeaderLabels([self.tr("Setting"), self.tr("Value")])
        self.listView.setIndentation(SHARED.theme.baseIconHeight)
        self.listView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.listView.setFrameStyle(QFrame.Shape.NoFrame)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.listView)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.outerBox)

    ##
    #  Getters
    ##

    def getColumnWidth(self) -> int:
        """Get the width of the first column."""
        return self.listView.columnWidth(0)

    def getExpandedState(self) -> list[bool]:
        """Get the expanded state of each top level item."""
        state = []
        for i in range(self.listView.topLevelItemCount()):
            item = self.listView.topLevelItem(i)
            if isinstance(item, QTreeWidgetItem):  # pragma: no branch
                state.append(item.isExpanded())
        return state

    ##
    #  Setters
    ##

    def setColumnWidth(self, value: int) -> None:
        """Set the width of the first column."""
        self.listView.setColumnWidth(0, value)

    def setExpandedState(self, state: list[bool]) -> None:
        """Set the expanded state of each top level item."""
        count = len(state)
        for i in range(self.listView.topLevelItemCount()):
            item = self.listView.topLevelItem(i)
            if isinstance(item, QTreeWidgetItem):  # pragma: no branch
                item.setExpanded((state[i] if i < count else True) and item.childCount() > 0)

    ##
    #  Methods
    ##

    def updateInfo(self, build: BuildSettings) -> None:
        """Load the build settings info into the table."""
        if self._initExpanded:
            previous = SHARED.project.options.getList("GuiManuscript", "detailsExpanded", [])
            expanded = [bool(s) for s in previous]
            self._initExpanded = False
        else:
            expanded = self.getExpandedState()

        self.listView.clear()

        on = SHARED.theme.getIcon("bullet-on:action")
        off = SHARED.theme.getIcon("bullet-off:action")

        # Name
        item = QTreeWidgetItem()
        item.setText(0, self.tr("Name"))
        item.setText(1, build.name)
        self.listView.addTopLevelItem(item)

        # Selection
        item = QTreeWidgetItem()
        item.setText(0, self.tr("Selection"))
        item.setText(1, "")
        self.listView.addTopLevelItem(item)
        for tHandle, nwItem in SHARED.project.tree.iterRoots(None):
            if not nwItem.isInactiveClass():
                sub = QTreeWidgetItem()
                sub.setText(0, nwItem.itemName)
                sub.setIcon(1, on if build.isRootAllowed(tHandle) else off)
                item.addChild(sub)

        # Headings
        hFmt = HeadingFormatter(SHARED.project, 7, 5, 23)
        title = self.tr("Title")
        hidden = self.tr("Hidden")

        item = QTreeWidgetItem()
        item.setText(0, build.getLabel("headings"))
        item.setText(1, "")
        self.listView.addTopLevelItem(item)
        for hFormat, hHide in [
            ("headings.fmtPart", "headings.hidePart"),
            ("headings.fmtChapter", "headings.hideChapter"),
            ("headings.fmtUnnumbered", "headings.hideUnnumbered"),
            ("headings.fmtScene", "headings.hideScene"),
            ("headings.fmtAltScene", "headings.hideAltScene"),
            ("headings.fmtSection", "headings.hideSection"),
        ]:
            sub = QTreeWidgetItem()
            sub.setText(0, build.getLabel(hFormat))
            if build.getBool(hHide):
                sub.setText(1, f"[{hidden}]")
            else:
                preview = build.getStr(hFormat).replace(nwHeadFmt.BR, nwUnicode.U_LBREAK)
                sub.setText(1, hFmt.apply(preview, title, 0))
            item.addChild(sub)

        # Text Content
        item = QTreeWidgetItem()
        item.setText(0, build.getLabel("text.grpContent"))
        item.setText(1, "")
        self.listView.addTopLevelItem(item)
        for key in [
            "text.includeBodyText",
            "text.includeSynopsis",
            "text.includeComments",
            "text.includeStory",
            "text.includeNotes",
            "text.includeKeywords",
        ]:
            sub = QTreeWidgetItem()
            sub.setText(0, build.getLabel(key))
            sub.setIcon(1, on if build.getBool(key) else off)
            item.addChild(sub)

        self._build = build

        # Restore expanded state
        self.setExpandedState(expanded)

    def updateTheme(self) -> None:
        """Update theme elements."""
        if self._build:
            logger.debug("Theme Update: _DetailsWidget")
            self.updateInfo(self._build)


class _OutlineWidget(QWidget):
    """The outline of the manuscript."""

    D_LINE = QtUserRole

    outlineEntryClicked = pyqtSignal(str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._outline = {}

        # Tree Widget
        self.listView = QTreeWidget(self)
        self.listView.setHeaderHidden(True)
        self.listView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.listView.setFrameStyle(QFrame.Shape.NoFrame)
        self.listView.itemClicked.connect(self._onItemClick)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.listView)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.outerBox)

    def updateOutline(self, data: dict[str, str], *, force: bool = False) -> None:
        """Update the outline."""
        if isinstance(data, dict) and (data != self._outline or force):
            self.listView.clear()

            tFont = SHARED.theme.guiFontB
            hFont = SHARED.theme.guiFontBU
            tBrush = SHARED.theme.accentText

            indent = False
            if root := self.listView.invisibleRootItem():  # pragma: no branch
                parent = root
                for anchor, entry in data.items():
                    prefix, _, text = entry.partition("|")
                    if prefix in ("TT", "PT", "CH", "SC", "H1", "H2"):
                        item = QTreeWidgetItem([text])
                        item.setData(0, self.D_LINE, anchor)
                        if prefix == "TT":
                            item.setFont(0, tFont)
                            item.setForeground(0, tBrush)
                            root.addChild(item)
                            parent = root
                        elif prefix == "PT":
                            item.setFont(0, hFont)
                            root.addChild(item)
                            parent = root
                        elif prefix in ("CH", "H1"):
                            root.addChild(item)
                            parent = item
                        elif prefix in ("SC", "H2"):  # pragma: no branch
                            parent.addChild(item)
                            indent = True

            self.listView.setIndentation(SHARED.theme.baseIconHeight if indent else 4)
            self._outline = data

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _OutlineWidget")
        self.updateOutline(self._outline, force=True)

    ##
    #  Private Slots
    ##

    def _onItemClick(self, item: QTreeWidgetItem) -> None:
        """Process tree item click."""
        self.outlineEntryClicked.emit(str(item.data(0, self.D_LINE)))


class _StatisticsWidget(QWidget):
    """The statistics of the manuscript."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._initExpanded = True

        # Tree Widget
        self.listView = QTreeWidget(self)
        self.listView.setHeaderLabels([self.tr("Count"), self.tr("Value")])
        self.listView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.listView.setIndentation(SHARED.theme.baseIconHeight)
        self.listView.setFrameStyle(QFrame.Shape.NoFrame)

        # Entries
        self.cTitles = QTreeWidgetItem(self.listView, [trStats(nwLabels.STATS_NAME[nwStats.TITLES]), ""])
        self.cParagraphs = QTreeWidgetItem(self.listView, [trStats(nwLabels.STATS_NAME[nwStats.PARAGRAPHS]), ""])
        self.cDialog = QTreeWidgetItem(self.listView, [trStats(nwLabels.STATS_NAME[nwStats.DIALOG_RATIO]), ""])
        self.cWords = QTreeWidgetItem(self.listView, [trStats(nwLabels.STATS_NAME[nwStats.WORDS]), ""])
        self.cChars = QTreeWidgetItem(self.listView, [trStats(nwLabels.STATS_NAME[nwStats.CHARS]), ""])

        self.cTextWords = QTreeWidgetItem(self.cWords, [trStats(nwLabels.STATS_NAME[nwStats.WORDS_TEXT]), ""])
        self.cTitlesWords = QTreeWidgetItem(self.cWords, [trStats(nwLabels.STATS_NAME[nwStats.WORDS_TITLE]), ""])

        self.cWChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.WCHARS_ALL]), ""])
        self.cTextChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.CHARS_TEXT]), ""])
        self.cTextWChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.WCHARS_TEXT]), ""])
        self.cDialogChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.CHARS_DIALOG]), ""])
        self.cTitlesChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.CHARS_TITLE]), ""])
        self.cTitleWChars = QTreeWidgetItem(self.cChars, [trStats(nwLabels.STATS_NAME[nwStats.WCHARS_TITLE]), ""])

        self.cTitles.setTextAlignment(1, QtAlignRight)
        self.cParagraphs.setTextAlignment(1, QtAlignRight)
        self.cDialog.setTextAlignment(1, QtAlignRight)
        self.cWords.setTextAlignment(1, QtAlignRight)
        self.cChars.setTextAlignment(1, QtAlignRight)
        self.cTextWords.setTextAlignment(1, QtAlignRight)
        self.cTitlesWords.setTextAlignment(1, QtAlignRight)
        self.cTextChars.setTextAlignment(1, QtAlignRight)
        self.cTitlesChars.setTextAlignment(1, QtAlignRight)
        self.cDialogChars.setTextAlignment(1, QtAlignRight)
        self.cWChars.setTextAlignment(1, QtAlignRight)
        self.cTextWChars.setTextAlignment(1, QtAlignRight)
        self.cTitleWChars.setTextAlignment(1, QtAlignRight)

        # Assemble
        self.outerBox = QVBoxLayout()
        self.outerBox.addWidget(self.listView)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.outerBox)

    ##
    #  Getters
    ##

    def getExpandedState(self) -> list[bool]:
        """Get the expanded state of each top level item."""
        state = []
        for i in range(self.listView.topLevelItemCount()):
            item = self.listView.topLevelItem(i)
            if isinstance(item, QTreeWidgetItem):  # pragma: no branch
                state.append(item.isExpanded())
        return state

    ##
    #  Setters
    ##

    def setExpandedState(self, state: list[bool]) -> None:
        """Set the expanded state of each top level item."""
        count = len(state)
        for i in range(self.listView.topLevelItemCount()):
            item = self.listView.topLevelItem(i)
            if isinstance(item, QTreeWidgetItem):  # pragma: no branch
                item.setExpanded((state[i] if i < count else True) and item.childCount() > 0)

    ##
    #  Methods
    ##

    def updateStats(self, data: dict[str, int], withDialog: bool) -> None:
        """Update the stats values from a Tokenizer stats dict."""
        titles = data.get(nwStats.TITLES, 0)
        paragraphs = data.get(nwStats.PARAGRAPHS, 0)
        words = data.get(nwStats.WORDS, 0)
        chars = data.get(nwStats.CHARS, 0)

        textWords = data.get(nwStats.WORDS_TEXT, 0)
        titleWords = data.get(nwStats.WORDS_TITLE, 0)

        wChars = data.get(nwStats.WCHARS_ALL, 0)
        textWChars = data.get(nwStats.WCHARS_TEXT, 0)
        textChars = data.get(nwStats.CHARS_TEXT, 0)
        dialogChars = data.get(nwStats.CHARS_DIALOG, 0)
        titleChars = data.get(nwStats.CHARS_TITLE, 0)
        titleWChars = data.get(nwStats.WCHARS_TITLE, 0)

        self.cTitles.setText(1, f"{titles:n}")
        self.cParagraphs.setText(1, f"{paragraphs:n}")
        self.cDialog.setText(1, formatPercent(dialogChars, divisor=textChars) if withDialog else "\u2014")
        self.cWords.setText(1, f"{words:n}")
        self.cChars.setText(1, f"{chars:n}")

        self.cTextWords.setText(1, f"{textWords:n}")
        self.cTitlesWords.setText(1, f"{titleWords:n}")

        self.cWChars.setText(1, f"{wChars:n}")
        self.cTextWChars.setText(1, f"{textWChars:n}")
        self.cTextChars.setText(1, f"{textChars:n}")
        self.cDialogChars.setText(1, f"{dialogChars:n}" if withDialog else "\u2014")
        self.cTitlesChars.setText(1, f"{titleChars:n}")
        self.cTitleWChars.setText(1, f"{titleWChars:n}")

        if header := self.listView.header():  # pragma: no branch
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QtHeaderStretch)
            header.setSectionResizeMode(1, QtHeaderToContents)


class _PreviewWidget(QTextBrowser):
    """The manuscript preview widget."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        self._docTime = 0
        self._buildName = ""
        self._scrollPos = 0

        # Document Setup
        dPalette = self.palette()
        dPalette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        dPalette.setColor(QPalette.ColorRole.Text, QColor(0, 0, 0))
        self.setPalette(dPalette)

        self.setMinimumWidth(40 * SHARED.theme.textNWidth)
        self.setTabStopDistance(CONFIG.tabWidth)
        self.setOpenExternalLinks(False)
        self.setOpenLinks(False)

        if document := self.document():  # pragma: no branch
            document.setDocumentMargin(CONFIG.textMargin)

        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)

        # Signals
        self.anchorClicked.connect(self._linkClicked)

        # Document Age
        aFont = self.font()
        aFont.setPointSizeF(0.9 * SHARED.theme.fontPointSize)

        self.ageLabel = QLabel("", self)
        self.ageLabel.setIndent(0)
        self.ageLabel.setFont(aFont)
        self.ageLabel.setAutoFillBackground(True)
        self.ageLabel.setAlignment(QtAlignCenter)
        self.ageLabel.setFixedHeight(int(2.1 * SHARED.theme.fontPixelSize))

        # Progress
        self.buildProgress = NProgressCircle(self, 160, 16)
        self.buildProgress.setVisible(False)
        self.buildProgress.setMaximum(1)
        self.buildProgress.setValue(0)
        self.buildProgress.setColors(
            back=QColor(255, 255, 255, 224), track=QColor(196, 196, 196, 128), text=QColor(0, 0, 0)
        )

        self._updateDocMargins()
        self._updateBuildAge()

        self.updateTheme()
        self.setTextFont(CONFIG.textFont)

        # Age Timer
        self.ageTimer = QTimer(self)
        self.ageTimer.setInterval(10000)
        self.ageTimer.timeout.connect(self._updateBuildAge)
        self.ageTimer.start()

    ##
    #  Setters
    ##

    def setBuildName(self, name: str) -> None:
        """Set the build name for the document label."""
        self._buildName = name
        self._updateBuildAge()

    def setTextFont(self, font: QFont) -> None:
        """Set the text font properties and then reset for sub-widgets.
        This needs special attention since there appears to be a bug in
        Qt 5.15.3. See issues #1862 and #1875.
        """
        self.setFont(font)
        self.buildProgress.setFont(SHARED.theme.guiFont)
        self.ageLabel.setFont(SHARED.theme.guiFontSmall)

    ##
    #  Methods
    ##

    def beginNewBuild(self, length: int) -> None:
        """Clear the document and show the progress bar."""
        self.buildProgress.setMaximum(length)
        self.buildProgress.setValue(0)
        self.buildProgress.setCentreText(None)
        self.buildProgress.setVisible(True)
        if vBar := self.verticalScrollBar():  # pragma: no branch
            self._scrollPos = vBar.value()
        self.setPlaceholderText("")
        self.clear()

    def buildStep(self, value: int) -> None:
        """Update the progress bar value."""
        self.buildProgress.setValue(value)
        QApplication.processEvents()

    def setContent(self, document: QTextDocument) -> None:
        """Set the content of the preview widget."""
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        self.buildProgress.setCentreText(self.tr("Processing ..."))
        QApplication.processEvents()

        document.setDocumentMargin(CONFIG.textMargin)
        self.setDocument(document)
        self.setTabStopDistance(CONFIG.tabWidth)

        self._docTime = int(time())
        self._updateBuildAge()

        self.buildProgress.setCentreText(self.tr("Done"))
        QApplication.restoreOverrideCursor()
        QTimer.singleShot(300, self._postUpdate)

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: _PreviewWidget")

        palette = QApplication.palette()
        palette.setColor(QPalette.ColorRole.Window, palette.toolTipBase().color())
        palette.setColor(QPalette.ColorRole.WindowText, palette.toolTipText().color())
        self.ageLabel.setPalette(palette)

    ##
    #  Events
    ##

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Capture resize and update the document margins."""
        super().resizeEvent(event)
        self._updateDocMargins()

    ##
    #  Public Slots
    ##

    @pyqtSlot("QPrinter*")
    def printPreview(self, printer: QPrinter) -> None:
        """Connect the print preview painter to the document viewer."""
        if document := self.document():  # pragma: no branch
            QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

            # Disable font hinting for the print job, see issues #2637 and #2640
            origFont = document.defaultFont()
            noHint = QFont(origFont)
            noHint.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
            document.setDefaultFont(noHint)

            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            document.print(printer)
            document.setDefaultFont(origFont)

            QApplication.restoreOverrideCursor()

    @pyqtSlot(str)
    def navigateTo(self, anchor: str) -> None:
        """Go to a specific #link in the document."""
        logger.debug("Moving to anchor '#%s'", anchor)
        self.setSource(QUrl(f"#{anchor}"))

    ##
    #  Private Slots
    ##

    @pyqtSlot("QUrl")
    def _linkClicked(self, url: QUrl) -> None:
        """Process a clicked link in the document."""
        if link := url.url():
            logger.debug("Clicked link: '%s'", link)
            if link.startswith("#"):
                self.navigateTo(link.lstrip("#"))
            elif link.startswith("http"):
                QDesktopServices.openUrl(QUrl(url))

    @pyqtSlot()
    def _updateBuildAge(self) -> None:
        """Update the build time and the fuzzy age."""
        if self._buildName and self._docTime > 0:
            self.ageLabel.setText(
                "<b>{0}</b><br>{1}: {2}".format(
                    self._buildName,
                    self.tr("Built"),
                    fuzzyTime(int(time()) - self._docTime),
                )
            )
        else:
            self.ageLabel.setText("<b>{0}</b>".format(self.tr("No Preview")))

    @pyqtSlot()
    def _postUpdate(self) -> None:
        """Run tasks after content update."""
        self.buildProgress.setVisible(False)
        if vBar := self.verticalScrollBar():  # pragma: no branch
            vBar.setValue(self._scrollPos)

    ##
    #  Internal Functions
    ##

    def _updateDocMargins(self) -> None:
        """Automatically adjust the header to fill the top of the
        document within the viewport.
        """
        vBar = self.verticalScrollBar()
        tB = self.frameWidth()
        vW = self.width() - 2 * tB - (vBar.width() if vBar else 0)
        vH = self.height() - 2 * tB
        tH = self.ageLabel.height()
        pS = self.buildProgress.width()
        self.ageLabel.setGeometry(tB, tB, vW, tH)
        self.setViewportMargins(0, tH, 0, 0)
        self.buildProgress.move((vW - pS) // 2, (vH - pS) // 2)
