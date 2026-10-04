"""
novelWriter - GUI Story View
============================

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

import csv
import logging

from enum import Enum
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QComboBox, QCompleter, QFileDialog, QHBoxLayout, QVBoxLayout, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatFileFilter
from novelwriter.constants import nwKeyWords, nwLabels, nwStats, trConst, trStats
from novelwriter.enum import nwItemClass
from novelwriter.extensions.configlayout import NColorLabel
from novelwriter.extensions.modified import NComboBox, NIconButton, NPushButton
from novelwriter.extensions.novelselector import NovelSelector
from novelwriter.extensions.tabwidget import NTabWidget
from novelwriter.story.outline import GuiStoryOutlineView
from novelwriter.story.storysettings import OutlineViewSettings, StoryViewCollection, StoryViewSettings
from novelwriter.story.storyviewbase import GuiStorySettingsBase, GuiStoryViewBase

if TYPE_CHECKING:
    from collections.abc import Iterable

    from novelwriter.enum import nwChange

logger = logging.getLogger(__name__)

VIEW_CLASSES: dict[type[StoryViewSettings], type[GuiStoryViewBase]] = {
    OutlineViewSettings: GuiStoryOutlineView,
}


class GuiStoryView(QWidget):
    """GUI: Project Story View."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        logger.debug("Create: GuiStoryView")

        self._views: StoryViewCollection | None = None
        self._stale: set[str] = set()
        self._highlight: set[str] = set()
        self._tagsRevision = -1

        icnSize = SHARED.theme.baseIconSize

        # Story View
        self.titleLabel = NColorLabel(
            self.tr("Story View"),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.HEADER_SCALE,
            bold=True,
        )

        self.novelValue = NovelSelector(self)
        self.novelValue.setIncludeAll(True)
        self.novelValue.setMinimumWidth(200)
        self.novelValue.novelSelectionChanged.connect(self._novelValueChanged)

        self.exportData = NIconButton(self, icnSize, "export:action")
        self.exportData.setToolTip(self.tr("Export the story view data"))
        self.exportData.clicked.connect(self._exportData)

        # Manage Views
        self.manageLabel = NColorLabel(
            self.tr("Manage Views"),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.NORMAL_SCALE,
            bold=True,
        )

        # Tabs
        self.tabMain = NTabWidget(self)
        self.tabMain.setMovable(True)
        self.tabMain.currentChanged.connect(self._currentViewChanged)

        self.addView = NIconButton(self, icnSize, "add:add")
        self.addView.setToolTip(self.tr("Add a new view"))
        self.addView.clicked.connect(self._addNewView)

        self.delView = NIconButton(self, icnSize, "remove:remove")
        self.delView.setToolTip(self.tr("Delete current view"))
        self.delView.clicked.connect(self._deleteCurrentView)

        self.copyView = NIconButton(self, icnSize, "copy:action")
        self.copyView.setToolTip(self.tr("Duplicate current view"))
        self.copyView.clicked.connect(self._copyCurrentView)

        self.editView = NIconButton(self, icnSize, "edit:change")
        self.editView.setToolTip(self.tr("Edit current view"))
        self.editView.clicked.connect(self._editCurrentView)

        self.refreshView = NPushButton(self, self.tr("Refresh"), icnSize, "refresh:change")
        self.refreshView.setToolTip(self.tr("Refresh current view"))
        self.refreshView.clicked.connect(self._refreshRequested)

        # Highlight
        self.highlightLabel = NColorLabel(
            self.tr("Highlight Reference"),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.NORMAL_SCALE,
            bold=True,
        )

        self.highlightValue = NComboBox(self)
        self.highlightValue.setEditable(True)
        self.highlightValue.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.highlightValue.setMinCharsWidth(22)
        self.highlightValue.setIconSize(icnSize)
        self.highlightValue.currentIndexChanged.connect(self._highlightChanged)

        if view := self.highlightValue.view():  # pragma: no branch
            view.setIconSize(icnSize)

        if completer := self.highlightValue.completer():  # pragma: no branch
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            if popup := completer.popup():  # pragma: no branch
                popup.setIconSize(icnSize)

        if lineEdit := self.highlightValue.lineEdit():  # pragma: no branch
            lineEdit.setClearButtonEnabled(True)
            lineEdit.textChanged.connect(self._highlightTextChanged)
            lineEdit.editingFinished.connect(self._highlightEditingFinished)

        # Assemble
        self.topBox = QHBoxLayout()
        self.topBox.addWidget(self.titleLabel)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.novelValue)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.exportData)
        self.topBox.addSpacing(32)
        self.topBox.addWidget(self.manageLabel)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.addView)
        self.topBox.addWidget(self.delView)
        self.topBox.addWidget(self.copyView)
        self.topBox.addWidget(self.editView)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.refreshView)
        self.topBox.addSpacing(32)
        self.topBox.addWidget(self.highlightLabel)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.highlightValue)
        self.topBox.addStretch(1)
        self.topBox.setContentsMargins(4, 4, 0, 0)
        self.topBox.setSpacing(4)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.topBox)
        self.outerBox.addWidget(self.tabMain)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(8)

        self.setLayout(self.outerBox)
        self._setProjectControls(False)

        logger.debug("Ready: GuiStoryView")

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        self.titleLabel.setTextColors(color=SHARED.theme.helpText)
        self.manageLabel.setTextColors(color=SHARED.theme.helpText)
        self.highlightLabel.setTextColors(color=SHARED.theme.helpText)
        self.novelValue.updateTheme()
        self.refreshView.refreshTheme()
        self.exportData.refreshTheme()
        self.addView.refreshTheme()
        self.delView.refreshTheme()
        self.copyView.refreshTheme()
        self.editView.refreshTheme()
        self.tabMain.refreshTheme()
        if self._views is not None:
            self._refreshTagList(force=True)
        for view in self._iterViews():
            view.updateTheme()
        for dialog in self._iterSettingsDialogs():
            dialog.updateTheme()

    def initSettings(self) -> None:
        """Apply changes to the preferences."""
        for view in self._iterViews():
            view.initSettings()

    def openProjectTasks(self) -> None:
        """Run open project tasks. The views are loaded in viewStory."""
        self.novelValue.refreshNovelList()
        self.novelValue.setHandle(SHARED.project.data.getLastHandle("story"))
        self._setProjectControls(True)

    def closeProjectTasks(self) -> None:
        """Run closing project tasks."""
        if self._views is not None:
            for widget in self._iterViews():
                widget.saveViewState()
            current = self.tabMain.currentWidget()
            lastView = current.settings.viewID if isinstance(current, GuiStoryViewBase) else ""
            highlight = next(iter(self._highlight), "")
            self._views.setStoryViewsState(lastView, highlight, [v.settings.viewID for v in self._iterViews()])
        while self.tabMain.count() > 0:
            self._removeTab(0)

        # Tabs are removed first so that saving from a dialog rebuilds nothing
        self._closeSettingsDialogs()
        self._views = None
        self._stale.clear()
        self._highlight = set()
        self._tagsRevision = -1

        self.highlightValue.blockSignals(True)
        self.highlightValue.clear()
        self.highlightValue.blockSignals(False)

        # Clearing must not emit a change, as it would reset the last handle
        self.novelValue.blockSignals(True)
        self.novelValue.clear()
        self.novelValue.blockSignals(False)
        self._setProjectControls(False)

    def viewStory(self) -> None:
        """Load the views if needed, and refresh the current view."""
        if self._views is None and SHARED.hasProject:
            self._loadViews()
        self._refreshCurrentView()

    ##
    #  Public Slots
    ##

    @pyqtSlot()
    def indexHasAppeared(self) -> None:
        """Refresh the current view when the index is loaded or rebuilt."""
        self._refreshCurrentView()

    @pyqtSlot(str, Enum)
    def updateRootItem(self, tHandle: str, change: nwChange) -> None:
        """Refresh the novel selector when a root folder changes."""
        self.novelValue.refreshNovelList()

    ##
    #  Private Slots
    ##

    @pyqtSlot(str)
    def _novelValueChanged(self, tHandle: str) -> None:
        """Rebuild the current view for the newly selected novel folder."""
        SHARED.project.data.setLastHandle(tHandle or None, "story")
        self._refreshCurrentView()

    @pyqtSlot()
    def _refreshRequested(self) -> None:
        """Force a rebuild of the current view."""
        self._refreshCurrentView(force=True)

    @pyqtSlot(int)
    def _currentViewChanged(self, index: int) -> None:
        """Refresh the view that was switched to."""
        self._refreshCurrentView()

    @pyqtSlot(int)
    def _highlightChanged(self, index: int) -> None:
        """Highlight the selected reference in all views."""
        tag = self.highlightValue.itemData(index)
        self._highlight = {tag} if tag else set()
        for view in self._iterViews():
            view.setHighlight(self._highlight)

    @pyqtSlot(str)
    def _highlightTextChanged(self, text: str) -> None:
        """Clear the highlight when the text is cleared."""
        if not text and self.highlightValue.currentIndex() > 0:
            self.highlightValue.setCurrentIndex(0)

    @pyqtSlot()
    def _highlightEditingFinished(self) -> None:
        """Revert text that does not match a reference."""
        combo = self.highlightValue
        if combo.findText(combo.currentText()) < 0:
            combo.setEditText(combo.itemText(combo.currentIndex()))

    @pyqtSlot()
    def _addNewView(self) -> None:
        """Add a new outline view."""
        self._addView(OutlineViewSettings())

    @pyqtSlot()
    def _copyCurrentView(self) -> None:
        """Duplicate the current view."""
        if isinstance(current := self.tabMain.currentWidget(), GuiStoryViewBase):
            self._addView(StoryViewSettings.duplicate(current.settings))

    @pyqtSlot()
    def _deleteCurrentView(self) -> None:
        """Delete the current view."""
        if (
            self._views is not None
            and isinstance(current := self.tabMain.currentWidget(), GuiStoryViewBase)
            and SHARED.question(self.tr("Delete view '{0}'?").format(current.settings.name))
        ):
            self._closeSettingsDialogs(current.settings.viewID)
            self._views.removeStoryView(current.settings.viewID)
            self._stale.discard(current.settings.viewID)
            self._removeTab(self.tabMain.currentIndex())

    @pyqtSlot()
    def _editCurrentView(self) -> None:
        """Open or activate the settings dialog for the current view."""
        if isinstance(current := self.tabMain.currentWidget(), GuiStoryViewBase) and (
            dialogClass := current.settingsDialog()
        ):
            viewID = current.settings.viewID
            for dialog in self._iterSettingsDialogs():
                if dialog.viewID == viewID:
                    dialog.activateDialog()
                    return
            current.saveViewState()
            dialog = dialogClass(SHARED.mainGui, current.settings)
            dialog.newSettingsReady.connect(self._applyViewSettings)
            dialog.activateDialog()

    @pyqtSlot(StoryViewSettings)
    def _applyViewSettings(self, settings: StoryViewSettings) -> None:
        """Save new settings from a settings dialog."""
        if self._views is not None and (view := self._views.getStoryView(settings.viewID)):
            rebuild = settings.changed
            view.updateSettings(settings)
            self._views.setStoryView(view)
            for widget in self._iterViews():
                if widget.settings is view:
                    self.tabMain.setTabText(self.tabMain.indexOf(widget), view.name)
            if rebuild:
                self._stale.add(view.viewID)
                self._refreshCurrentView()

    @pyqtSlot()
    def _exportData(self) -> None:
        """Export the story outline data as a CSV file."""
        name = CONFIG.lastPath("outline") / f"{SHARED.project.data.fileSafeName}.csv"
        if path := QFileDialog.getSaveFileName(
            self, self.tr("Save Outline As"), str(name), formatFileFilter(["*.csv", "*"])
        )[0]:
            CONFIG.setLastPath("outline", path)
            logger.info("Writing CSV file: %s", path)
            with open(path, mode="w", newline="", encoding="utf-8") as csvFile:
                writer = csv.writer(csvFile, dialect="excel", quoting=csv.QUOTE_ALL)
                writer.writerows(self._dumpNovelData(self.novelValue.handle))

    ##
    #  Internal Functions
    ##

    def _loadViews(self) -> None:
        """Load the views collection and populate the tabs."""
        views = StoryViewCollection(SHARED.project)
        if len(views) == 0:
            views.setStoryView(OutlineViewSettings())
        self._views = views
        self._highlight = {views.highlight} if views.highlight else set()

        # The current view is refreshed by the caller, not on tab change
        self.tabMain.blockSignals(True)
        for view in views.storyViews():
            index = self._addTab(view)
            if view.viewID == views.lastView:
                self.tabMain.setCurrentIndex(index)
        self.tabMain.blockSignals(False)

    def _addView(self, view: StoryViewSettings) -> None:
        """Add a new view to the collection, and switch to it."""
        if self._views is not None:
            view.setOrder(max((v.order for v in self._views.storyViews()), default=-1) + 1)
            self._views.setStoryView(view)
            if (index := self._addTab(view)) >= 0:  # pragma: no branch
                self.tabMain.setCurrentIndex(index)

    def _addTab(self, view: StoryViewSettings) -> int:
        """Add a tab for a view, and return its index."""
        if viewClass := VIEW_CLASSES.get(type(view)):
            widget = viewClass(self, view)
            widget.setHighlight(self._highlight)
            return self.tabMain.addTab(widget, view.name)
        return -1

    def _removeTab(self, index: int) -> None:
        """Remove a tab and release its widget."""
        if widget := self.tabMain.widget(index):  # pragma: no branch
            self.tabMain.removeTab(index)
            widget.setParent(None)

    def _setProjectControls(self, enabled: bool) -> None:
        """Enable or disable the controls that need an open project."""
        self.exportData.setEnabled(enabled)
        self.addView.setEnabled(enabled)
        self.delView.setEnabled(enabled)
        self.copyView.setEnabled(enabled)
        self.editView.setEnabled(enabled)
        self.refreshView.setEnabled(enabled)
        self.highlightValue.setEnabled(enabled)
        if not enabled:
            self.novelValue.setEnabled(False)

    def _closeSettingsDialogs(self, viewID: str | None = None) -> None:
        """Close all settings dialogs, or discard the one for a view."""
        for dialog in self._iterSettingsDialogs():
            if viewID is None:
                dialog.close()
            elif dialog.viewID == viewID:
                dialog.discardAndClose()

    def _iterSettingsDialogs(self) -> Iterable[GuiStorySettingsBase]:
        """Iterate over the open view settings dialogs."""
        for obj in SHARED.mainGui.children():
            if isinstance(obj, GuiStorySettingsBase):
                yield obj

    def _iterViews(self) -> Iterable[GuiStoryViewBase]:
        """Iterate over the view widgets in tab order."""
        for i in range(self.tabMain.count()):
            if isinstance(view := self.tabMain.widget(i), GuiStoryViewBase):  # pragma: no branch
                yield view

    def _refreshCurrentView(self, force: bool = False) -> None:
        """Refresh the current view, if loaded and visible."""
        if (
            self._views is not None
            and self.isVisible()
            and isinstance(current := self.tabMain.currentWidget(), GuiStoryViewBase)
        ):
            viewID = current.settings.viewID
            current.refresh(self.novelValue.handle, force=force or viewID in self._stale)
            self._stale.discard(viewID)
            self._refreshTagList()

    def _refreshTagList(self, force: bool = False) -> None:
        """Rebuild the highlight list if the index has changed."""
        index = SHARED.project.index
        if force or index.indexRevision != self._tagsRevision:
            self._tagsRevision = index.indexRevision
            current = next(iter(self._highlight), "")
            combo = self.highlightValue
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("", "")
            iPx = SHARED.theme.baseIconHeight
            for tag, name, tClass, _, _ in sorted(index.getTagsData(), key=lambda x: x[1].lower()):
                iClass = nwItemClass.__members__.get(tClass, nwItemClass.NO_CLASS)
                combo.addItem(SHARED.theme.getIcon(nwLabels.CLASS_ICON[iClass], iPx, iPx), name, tag)
            combo.setCurrentData(current, "")
            combo.blockSignals(False)
            if combo.currentData() != current:
                self._highlightChanged(combo.currentIndex())

    def _dumpNovelData(self, rootHandle: str | None) -> list[list[str | int]]:
        """Dump all novel data into a table."""
        project = SHARED.project
        index = project.index
        sLabel = project.localLookup("Story Structure")
        nLabel = project.localLookup("Note")
        sKeys = sorted(index.getStoryKeys())
        nKeys = sorted(index.getNoteKeys())
        sMatch = [f"story.{k}" for k in sKeys]
        nMatch = [f"note.{k}" for k in nKeys]
        sHeaders = [f"{sLabel} ({k})" for k in sKeys]
        nHeaders = [f"{nLabel} ({k})" for k in nKeys]

        data: list[list[str | int]] = [
            [
                "H",
                self.tr("Title"),
                self.tr("Document"),
                self.tr("Line"),
                self.tr("Status"),
                trStats(nwLabels.STATS_NAME[nwStats.CHARS]),
                trStats(nwLabels.STATS_NAME[nwStats.WORDS]),
                trStats(nwLabels.STATS_NAME[nwStats.PARAGRAPHS]),
                *(trConst(nwLabels.KEY_NAME[k]) for k in nwKeyWords.CAN_LOOKUP),
                self.tr("Synopsis"),
                *sHeaders,
                *nHeaders,
            ]
        ]

        for tHandle, _, hItem in index.iterNovelStructure(rHandle=rootHandle, activeOnly=True):
            if hItem.level != "H0" and (nwItem := project.tree[tHandle]):
                refs = hItem.getReferences()
                comments = hItem.comments
                data.append([
                    hItem.level,
                    hItem.title,
                    nwItem.itemName,
                    hItem.line,
                    nwItem.getImportStatus()[0],
                    hItem.charCount,
                    hItem.wordCount,
                    hItem.paraCount,
                    *(", ".join(refs[k]) for k in nwKeyWords.CAN_LOOKUP),
                    hItem.synopsis,
                    *(comments.get(k, "") for k in sMatch),
                    *(comments.get(k, "") for k in nMatch),
                ])

        return data
