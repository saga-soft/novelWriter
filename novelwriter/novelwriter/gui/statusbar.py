"""
novelWriter - GUI Main Window Status Bar
========================================

This file is a part of novelWriter
Copyright (C) 2019 Veronica Berglyd Olsen and novelWriter contributors

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

from datetime import datetime
from time import time
from typing import TYPE_CHECKING

from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QLabel, QStatusBar, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import formatPercent, formatTime, languageName
from novelwriter.constants import nwConst, nwLabels, nwStats, trStats
from novelwriter.extensions.modified import NClickableLabel, NFlatIconButton
from novelwriter.extensions.progressbars import NColorRangeProgress
from novelwriter.extensions.statusled import StatusLED

if TYPE_CHECKING:
    from novelwriter.types import T_MsgSeverity

logger = logging.getLogger(__name__)


class GuiMainStatus(QStatusBar):
    """GUI: Main Window Status Bar."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiMainStatus")

        self._refTime = -1.0
        self._userIdle = False
        self._debugInfo = False

        iPx = SHARED.theme.baseIconHeight
        iSz = SHARED.theme.baseIconSize
        pPx = SHARED.theme.getTextWidth("0" * 16)

        self.messageBox = _MessageWidget(self)
        self.insertWidget(0, self.messageBox)

        # Permanent Widgets
        # =================

        # The Daily Progress Bar
        self.dayReset = NFlatIconButton(self, iSz, "revert:reset")
        self.dayReset.setToolTip(self.tr("Reset Daily Progress"))
        self.dayReset.setVisible(False)
        self.dayReset.clicked.connect(self._resetDailyProgress)
        self.addPermanentWidget(self.dayReset)

        self.dayProg = NColorRangeProgress(self, pPx, iPx + 4, 1)
        self.dayProg.setValue(0)
        self.dayProg.setMaximum(1)
        self.dayProg.setVisible(False)
        self.dayProg.setBarRangeColors(start="red", mid="yellow", end="green")
        self.addPermanentWidget(self.dayProg)

        # The Project Progress Bar
        self.projProg = NColorRangeProgress(self, pPx, iPx + 4, 1)
        self.projProg.setValue(0)
        self.projProg.setMaximum(1)
        self.projProg.setVisible(False)
        self.projProg.setBarColor("blue")
        self.addPermanentWidget(self.projProg)

        # The Spell Checker Language
        self.langIcon = QLabel("", self)
        self.langText = QLabel(self.tr("None"), self)
        self.langIcon.setContentsMargins(0, 0, 0, 0)
        self.langText.setContentsMargins(0, 0, 8, 0)
        self.addPermanentWidget(self.langIcon)
        self.addPermanentWidget(self.langText)

        # The Editor Status
        self.docIcon = StatusLED(iPx, iPx, self)
        self.docText = QLabel(self.tr("Editor"), self)
        self.docIcon.setContentsMargins(0, 0, 0, 0)
        self.docText.setContentsMargins(0, 0, 8, 0)
        self.addPermanentWidget(self.docIcon)
        self.addPermanentWidget(self.docText)

        # The Project Status
        self.projIcon = StatusLED(iPx, iPx, self)
        self.projText = QLabel(self.tr("Project"), self)
        self.projIcon.setContentsMargins(0, 0, 0, 0)
        self.projText.setContentsMargins(0, 0, 8, 0)
        self.addPermanentWidget(self.projIcon)
        self.addPermanentWidget(self.projText)

        # The Project and Session Stats
        self.statsIcon = QLabel(self)
        self.statsText = QLabel("", self)
        self.statsIcon.setContentsMargins(0, 0, 0, 0)
        self.statsText.setContentsMargins(0, 0, 8, 0)
        self.addPermanentWidget(self.statsIcon)
        self.addPermanentWidget(self.statsText)

        # The Session Clock
        # Set the minimum width so the label doesn't rescale every second
        self.timeIcon = NClickableLabel(self)
        self.timeIcon.mouseClicked.connect(self._onClickTimerLabel)

        self.timeText = NClickableLabel("", self)
        self.timeText.setToolTip(self.tr("Session Time"))
        self.timeText.setMinimumWidth(SHARED.theme.getTextWidth("00:00:00:"))
        self.timeIcon.setContentsMargins(0, 0, 0, 0)
        self.timeText.setContentsMargins(0, 0, 0, 0)
        self.timeText.setVisible(CONFIG.showSessionTime)
        self.timeText.mouseClicked.connect(self._onClickTimerLabel)
        self.addPermanentWidget(self.timeIcon)
        self.addPermanentWidget(self.timeText)

        # Other Settings
        self.setSizeGripEnabled(True)

        logger.debug("Ready: GuiMainStatus")

        self.initSettings()
        self.initProjectSettings()
        self.updateTheme()
        self.clearStatus()

    def initSettings(self) -> None:
        """Apply user settings."""
        if CONFIG.useCharCount:
            self._trStatsCount = trStats(nwLabels.STATS_DISPLAY[nwStats.CHARS])
            self._trStatsTip = self.tr("Total character count (session change)")
        else:
            self._trStatsCount = trStats(nwLabels.STATS_DISPLAY[nwStats.WORDS])
            self._trStatsTip = self.tr("Total word count (session change)")

    def initProjectSettings(self) -> None:
        """Apply project settings."""
        data = SHARED.project.data
        self.updateGoals(data.targetLastCount, data.dailyProgress)

    def clearStatus(self) -> None:
        """Reset all widgets on the status bar to default values."""
        self.dayReset.setVisible(False)
        self.dayProg.setVisible(False)
        self.projProg.setVisible(False)
        self.updateGoals(0, 0)

        self.setRefTime(-1.0)
        self.setLanguage(*SHARED.spelling.describeDict())
        self.setProjectStats(0, 0)
        self.setProjectStatus(None)
        self.setDocumentStatus(None)
        self.updateTime()

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiMainStatus")

        iPx = SHARED.theme.baseIconHeight
        self.langIcon.setPixmap(SHARED.theme.getPixmap("language", iPx, iPx))
        self.statsIcon.setPixmap(SHARED.theme.getPixmap("stats", iPx, iPx))
        self.timePixmap = SHARED.theme.getPixmap("timer", iPx, iPx)
        self.idlePixmap = SHARED.theme.getPixmap("timer_off", iPx, iPx)
        self.timeIcon.setPixmap(self.timePixmap)

        colNone = SHARED.theme.getBaseColor("default")
        colSaved = SHARED.theme.getBaseColor("green")
        colUnsaved = SHARED.theme.getBaseColor("red")
        self.docIcon.setColors(colNone, colSaved, colUnsaved)
        self.projIcon.setColors(colNone, colSaved, colUnsaved)

        self.dayReset.refreshTheme()
        self.dayProg.refreshTheme()
        self.projProg.refreshTheme()

    ##
    #  Setters
    ##

    def setRefTime(self, refTime: float) -> None:
        """Set the reference time for the status bar clock."""
        self._refTime = refTime

    def setProjectStatus(self, state: bool | None) -> None:
        """Set the project status colour icon."""
        self.projIcon.setState(state)

    def setDocumentStatus(self, state: bool | None) -> None:
        """Set the document status colour icon."""
        self.docIcon.setState(state)

    def setUserIdle(self, idle: bool) -> None:
        """Change the idle status icon."""
        if not CONFIG.stopWhenIdle:
            idle = False
        if self._userIdle != idle:
            if idle:
                self.timeIcon.setPixmap(self.idlePixmap)
            else:
                self.timeIcon.setPixmap(self.timePixmap)
            self._userIdle = idle

    def setProjectStats(self, pWC: int, sWC: int) -> None:
        """Update the current project statistics."""
        self.statsText.setText(self._trStatsCount.format(f"{pWC:n}", f"{sWC:+n}"))
        self.statsText.setToolTip(self._trStatsTip)

    def updateGoals(self, pProg: int, sProg: int) -> None:
        """Update the current project and session goals."""
        data = SHARED.project.data

        if (dailyTarget := data.getEffectiveDailyGoal()) > 0:
            self.dayReset.setVisible(True)
            self.dayProg.setVisible(True)
            self.dayProg.setMaximum(dailyTarget)
            self.dayProg.setValue(min(sProg, dailyTarget))
            self.dayProg.setCentreText(formatPercent(sProg, divisor=dailyTarget, prec=1))
            self.dayProg.setToolTip(self.tr("Daily Progress: {0}/{1}").format(f"{sProg:n}", f"{dailyTarget:n}"))
        else:
            self.dayReset.setVisible(False)
            self.dayProg.setVisible(False)

        if (projTarget := data.targetCount) > 0:
            self.projProg.setVisible(True)
            self.projProg.setMaximum(projTarget)
            self.projProg.setValue(min(pProg, projTarget))
            self.projProg.setCentreText(formatPercent(pProg, divisor=projTarget, prec=1))
            self.projProg.setToolTip(self.tr("Project Progress: {0}/{1}").format(f"{pProg:n}", f"{projTarget:n}"))
        else:
            self.projProg.setVisible(False)

    def updateTime(self, idleTime: float = 0.0) -> None:
        """Update the session clock."""
        if self._refTime < 0.0:
            self.timeText.setText("00:00:00")
        else:
            if CONFIG.stopWhenIdle:
                sessTime = round(time() - self._refTime - idleTime)
            else:
                sessTime = round(time() - self._refTime)
            self.timeText.setText(formatTime(sessTime))

    ##
    #  Public Slots
    ##

    @pyqtSlot(str, str)
    def setStatusMessage(self, message: str, severity: T_MsgSeverity = "info") -> None:
        """Set the status bar message to display."""
        self.messageBox.setMessage(message, severity, nwConst.STATUS_MSG_TIMEOUT)

    @pyqtSlot(str, str)
    def setLanguage(self, language: str, provider: str) -> None:
        """Set the language code for the spell checker."""
        if language == "None":
            self.langText.setText(self.tr("None"))
            self.langText.setToolTip("")
        else:
            self.langText.setText(languageName(language))
            self.langText.setToolTip(f"{language} ({provider})" if provider else language)

    @pyqtSlot(bool)
    def updateProjectStatus(self, status: bool) -> None:
        """Update the project status."""
        self.setProjectStatus(not status)

    @pyqtSlot(bool)
    def updateDocumentStatus(self, status: bool) -> None:
        """Update the document status."""
        self.setDocumentStatus(not status)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _onClickTimerLabel(self) -> None:
        """Process mouse click on timer label."""
        state = not CONFIG.showSessionTime
        self.timeText.setVisible(state)
        CONFIG.showSessionTime = state

    @pyqtSlot()
    def _resetDailyProgress(self) -> None:
        """Ask for confirmation and reset the daily progress counter."""
        if SHARED.question(self.tr("Do you want to reset the daily progress count?")):
            SHARED.project.data.resetDailyProgress()
            self.initProjectSettings()

    ##
    #  Debug
    ##

    def memInfo(self) -> None:  # pragma: no cover
        """Display memory info on the status bar. This is used to
        investigate memory usage and Qt widgets that get left in memory.
        Enabled by the --meminfo command line flag.

        By default, this tracks memory usage diff after launch. To track
        full memory usage, set environment variable PYTHONTRACEMALLOC=1
        before starting novelWriter.
        """
        import gc
        import tracemalloc

        count = len(QApplication.allWidgets())
        if not self._debugInfo:
            if tracemalloc.is_tracing():
                self._traceMallocRef = "Total"
            else:
                self._traceMallocRef = "Relative"
                tracemalloc.start()
            self._debugInfo = True

        current, peak = tracemalloc.get_traced_memory()
        young, old0, old1 = gc.get_count()
        stamp = datetime.now().strftime("%H:%M:%S")
        message = (
            f"Widgets: {count} \u2013 "
            f"{self._traceMallocRef} Memory: {current / 1024:,.2f} kiB \u2013 "
            f"Peak: {peak / 1024:,.2f} kiB \u2013 "
            f"GC: {young}/{old0}/{old1}"
        )
        if garbage := len(gc.garbage):
            # Objects the collector could not free, should normally stay at 0
            message += f" \u2013 Uncollectable: {garbage}"
        self.showMessage(f"Debug [{stamp}] {message}", 6000)
        logger.debug("[MEMINFO] %s", message)


class _MessageWidget(QWidget):
    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._icon = QLabel(self)
        self._text = QLabel(self)

        self._layout = QHBoxLayout()
        self._layout.addWidget(self._icon)
        self._layout.addWidget(self._text)
        self._layout.setSpacing(4)
        self._layout.setContentsMargins(4, 0, 0, 0)
        self.setLayout(self._layout)

    def setMessage(self, message: str, severity: str, timeout: int) -> None:
        """Set a status bar message with a timeout."""
        iSz = SHARED.theme.baseIconHeight
        icon = severity.replace("warning", "warn")
        self._icon.setPixmap(SHARED.theme.getPixmap(f"alert_{icon}:{severity}", iSz, iSz))
        self._text.setText(message)
        QTimer.singleShot(timeout, self.clearMessage)

    @pyqtSlot()
    def clearMessage(self) -> None:
        """Clear the current status bar message and icon."""
        self._icon.clear()
        self._text.clear()
