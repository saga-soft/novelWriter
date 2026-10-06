"""
novelWriter - Custom Widget: Version Info
=========================================

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

import json
import logging

from datetime import datetime
from time import sleep
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PyQt6.QtCore import QRunnable, QUrl, pyqtBoundSignal, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from novelwriter import CONFIG, SHARED, __date__, __domain__, __version__
from novelwriter.common import formatLink, formatVersion
from novelwriter.constants import nwConst

logger = logging.getLogger(__name__)

API_URL = "https://api.github.com/repos/saga-soft/novelwriter/releases/latest"


class VersionInfoWidget(QWidget):
    """Custom: version Info Label.

    A custom widget that will show a clickable area for contacting
    GitHub and pulling the latest release version info.
    """

    _dataReady = pyqtSignal(str, str)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self._dataReady.connect(self._updateReleaseInfo)

        # Label Strings
        self._trLatest = self.tr("Latest Version: {0}")
        self._trChecking = self.tr("Checking ...")
        self._trDownload = self.tr("Download from {0}")

        trVersion = self.tr("Version")
        trNotes = self.tr("Release Notes")
        trCheck = self.tr("Check Now")

        # Labels
        iPx = SHARED.theme.baseIconHeight

        self._pixDate = QLabel(self)
        self._pixDate.setPixmap(SHARED.theme.getPixmap("calendar:default", iPx, iPx))
        self._pixNotes = QLabel(self)
        self._pixNotes.setPixmap(SHARED.theme.getPixmap("link:default", iPx, iPx))

        self._lblVersion = QLabel(f"{trVersion} {formatVersion(__version__)}", self)
        self._lblDate = QLabel(CONFIG.localDate(datetime.strptime(__date__, "%Y-%m-%d")), self)
        self._lblNotes = QLabel(formatLink("#notes", trNotes), self)
        self._lblNotes.linkActivated.connect(self._processLink)

        self._lblRelease = QLabel(self._trLatest.format(formatLink("#update", trCheck)), self)
        self._lblRelease.linkActivated.connect(self._processLink)

        # Assemble
        self._info = QHBoxLayout()
        self._info.addWidget(self._lblVersion, 0)
        self._info.addSpacing(6)
        self._info.addWidget(self._pixDate, 0)
        self._info.addWidget(self._lblDate, 0)
        self._info.addSpacing(6)
        self._info.addWidget(self._pixNotes, 0)
        self._info.addWidget(self._lblNotes, 0)
        self._info.addStretch(1)
        self._info.setSpacing(2)
        self._info.setContentsMargins(0, 0, 0, 0)

        self._layout = QVBoxLayout()
        self._layout.addLayout(self._info)
        self._layout.addWidget(self._lblRelease)
        self._layout.setSpacing(8)
        self._layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self._layout)

    ##
    #  Private Slots
    ##

    @pyqtSlot(str)
    def _processLink(self, link: str) -> None:
        """Process an activated link."""
        if link == "#notes":
            QDesktopServices.openUrl(QUrl(nwConst.URL_RELEASES))
        elif link == "#website":
            QDesktopServices.openUrl(QUrl(nwConst.URL_WEB))
        elif link == "#update":
            self._lblRelease.setText(self._trLatest.format(self._trChecking))
            SHARED.runInThreadPool(_Retriever(self._dataReady))

    ##
    #  Private Slots
    ##

    @pyqtSlot(str, str)
    def _updateReleaseInfo(self, tag: str, reason: str) -> None:
        """Update the widget release info."""
        if version := formatVersion(tag.lstrip("v")):
            download = formatLink("#website", __domain__)
            self._lblRelease.setText(self._trLatest.format(f"{version} \u2013 {self._trDownload.format(download)}"))
        else:
            self._lblRelease.setText(self._trLatest.format(self.tr("Failed")))
            logger.error("Could not retrieve version info: %s", reason)


class _Retriever(QRunnable):
    def __init__(self, signal: pyqtBoundSignal) -> None:
        super().__init__()
        self._signal = signal

    @pyqtSlot()
    def run(self) -> None:
        """Poll the GitHub API in the background.
        Note: The GitHub API is rate limited at 60 requests per hour.
        """
        logger.info("Contacting: %s", API_URL)
        req = Request(API_URL)
        req.add_header("User-Agent", nwConst.USER_AGENT)
        req.add_header("Accept", "application/vnd.github.v3+json")
        sleep(0.2)
        try:
            with urlopen(req, timeout=15) as ret:
                if isinstance(raw := json.loads(ret.read().decode()), dict):
                    self._signal.emit(raw.get("tag_name", ""), "")
        except HTTPError as e:
            reason = f"{e.reason.capitalize()} (HTTP {e.code})"
            logger.error(reason)
            self._signal.emit("", reason)
        except Exception as e:
            logger.error("Failed to retrieve release info")
            self._signal.emit("", str(e))
