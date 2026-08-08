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
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QSplitter, QStackedWidget, QVBoxLayout, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatFileFilter
from novelwriter.constants import nwKeyWords, nwLabels, nwStats, trConst, trStats
from novelwriter.extensions.configlayout import NColorLabel
from novelwriter.extensions.modified import NIconButton
from novelwriter.extensions.novelselector import NovelSelector
from novelwriter.story.storypanel import GuiStoryPanel

if TYPE_CHECKING:
    from novelwriter.enum import nwChange

logger = logging.getLogger(__name__)


class GuiStoryView(QWidget):
    """GUI: Project Story View."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)

        self.storyPanel = GuiStoryPanel(self)
        self.contentStack = QStackedWidget(self)

        btnSize = 1.4 * SHARED.theme.baseIconSize

        # Top Bar
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

        self.refreshView = NIconButton(self, btnSize, "refresh:change")
        self.refreshView.setToolTip(self.tr("Refresh the story view"))
        self.refreshView.clicked.connect(self._refreshRequested)

        self.exportData = NIconButton(self, btnSize, "export:action")
        self.exportData.setToolTip(self.tr("Export the story view data"))
        self.exportData.clicked.connect(self._exportData)

        # Main Splitter
        self.splitMain = QSplitter(Qt.Orientation.Horizontal)
        self.splitMain.setContentsMargins(0, 0, 0, 0)
        self.splitMain.addWidget(self.storyPanel)
        self.splitMain.addWidget(self.contentStack)
        self.splitMain.setOpaqueResize(False)
        self.splitMain.setHandleWidth(4)
        self.splitMain.setSizes([max(s, 100) for s in CONFIG.storyPanePos])
        self.splitMain.setCollapsible(0, False)
        self.splitMain.setCollapsible(1, False)
        self.splitMain.setStretchFactor(0, 0)
        self.splitMain.setStretchFactor(1, 1)
        self.splitMain.splitterMoved.connect(self._saveSplitterSizes)

        # Assemble
        self.topBox = QHBoxLayout()
        self.topBox.addWidget(self.titleLabel)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.novelValue)
        self.topBox.addSpacing(8)
        self.topBox.addWidget(self.refreshView)
        self.topBox.addWidget(self.exportData)
        self.topBox.addStretch(1)
        self.topBox.setContentsMargins(4, 4, 0, 0)
        self.topBox.setSpacing(4)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.topBox)
        self.outerBox.addWidget(self.splitMain)
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(8)

        self.setLayout(self.outerBox)

        self.showContent(self.storyPanel.outlineContent)

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""
        self.storyPanel.updateTheme()

    def openProjectTasks(self) -> None:
        """Run open project tasks.

        The outline itself is not built here. It is built lazily the
        first time the user switches to the story view, see viewStory.
        """
        options = SHARED.project.options
        outline = self.storyPanel.outlineContent
        outline.restoreColumnWidths(options.getList("GuiStoryOutline", "colWidths", []))
        self.novelValue.refreshNovelList()
        self.novelValue.setHandle(SHARED.project.data.getLastHandle("story"))

    def closeProjectTasks(self) -> None:
        """Run closing project tasks."""
        options = SHARED.project.options
        outline = self.storyPanel.outlineContent
        options.setValue("GuiStoryOutline", "colWidths", outline.saveColumnWidths())
        SHARED.project.data.setLastHandle(self.novelValue.handle, "story")
        outline.clear()

    def viewStory(self) -> None:
        """Build or refresh the outline when the story view is shown."""
        self.storyPanel.outlineContent.refresh(self.novelValue.handle)

    def showContent(self, widget: QWidget) -> None:
        """Add a widget to the content stack, if needed, and show it.

        This is the switchboard a foldable panel's "generate" action
        will call to lazily add and activate its content widget.
        """
        if self.contentStack.indexOf(widget) == -1:
            self.contentStack.addWidget(widget)
        self.contentStack.setCurrentWidget(widget)

    ##
    #  Public Slots
    ##

    @pyqtSlot(str, Enum)
    def updateRootItem(self, tHandle: str, change: nwChange) -> None:
        """Refresh the novel selector when a root folder changes."""
        self.novelValue.refreshNovelList()

    ##
    #  Private Slots
    ##

    @pyqtSlot(int, int)
    def _saveSplitterSizes(self, pos: int, index: int) -> None:
        """Save the splitter sizes when moved by the user."""
        CONFIG.storyPanePos = self.splitMain.sizes()

    @pyqtSlot(str)
    def _novelValueChanged(self, tHandle: str) -> None:
        """Rebuild the outline for the newly selected novel folder."""
        self.storyPanel.outlineContent.refresh(tHandle or None)

    @pyqtSlot()
    def _refreshRequested(self) -> None:
        """Force a rebuild of the outline for the selected novel folder."""
        self.storyPanel.outlineContent.refresh(self.novelValue.handle, force=True)

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
                trConst(nwLabels.KEY_NAME[nwKeyWords.POV_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.FOCUS_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.CHAR_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.PLOT_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.TIME_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.WORLD_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.OBJECT_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.ENTITY_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.CUSTOM_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.STORY_KEY]),
                trConst(nwLabels.KEY_NAME[nwKeyWords.MENTION_KEY]),
                self.tr("Synopsis"),
                *sHeaders,
                *nHeaders,
            ]
        ]

        for tHandle, _sTitle, hItem in index.iterNovelStructure(rHandle=rootHandle, activeOnly=True):
            if hItem.level != "H0" and (nwItem := project.tree[tHandle]):
                refs = hItem.getReferences()
                comments = dict(hItem.comments.items())
                story = [comments.get(k, "") for k in sMatch]
                notes = [comments.get(k, "") for k in nMatch]
                data.append([
                    hItem.level,
                    hItem.title,
                    nwItem.itemName,
                    hItem.line,
                    nwItem.getImportStatus()[0],
                    hItem.charCount,
                    hItem.wordCount,
                    hItem.paraCount,
                    ", ".join(refs[nwKeyWords.POV_KEY]),
                    ", ".join(refs[nwKeyWords.FOCUS_KEY]),
                    ", ".join(refs[nwKeyWords.CHAR_KEY]),
                    ", ".join(refs[nwKeyWords.PLOT_KEY]),
                    ", ".join(refs[nwKeyWords.TIME_KEY]),
                    ", ".join(refs[nwKeyWords.WORLD_KEY]),
                    ", ".join(refs[nwKeyWords.OBJECT_KEY]),
                    ", ".join(refs[nwKeyWords.ENTITY_KEY]),
                    ", ".join(refs[nwKeyWords.CUSTOM_KEY]),
                    ", ".join(refs[nwKeyWords.STORY_KEY]),
                    ", ".join(refs[nwKeyWords.MENTION_KEY]),
                    hItem.synopsis,
                    *story,
                    *notes,
                ])

        return data
