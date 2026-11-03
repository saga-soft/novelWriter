"""
novelWriter - Version Info Widget Tests
=======================================

This file is a part of novelWriter.

Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors.

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

from typing import Any
from urllib.error import HTTPError

import pytest

from PyQt6.QtCore import QObject, Qt, QUrl, pyqtBoundSignal, pyqtSignal
from PyQt6.QtWidgets import QWidget
from pytestqt.qtbot import QtBot

from novelwriter import SHARED
from novelwriter.constants import nwConst
from novelwriter.extensions.versioninfo import VersionInfoWidget, _Retriever
from novelwriter.types import QtAlignAbsolute, QtAlignLeftMiddle, QtAlignRightMiddle

from tests.helpers import SimpleDialog
from tests.mocked import MockGuiMain


class MockSignalHolder(QObject):
    """Mock object holding the data ready signal."""

    dataReady = pyqtSignal(str, str)


class MockRetriever:
    """Mock retriever that only stores the signal."""

    def __init__(self, signal: pyqtBoundSignal) -> None:
        self.signal = signal


class MockDesktopServices:
    """Mock desktop services that record the opened URL."""

    url = None

    @staticmethod
    def openUrl(url: QUrl) -> None:
        """Record the URL instead of opening it."""
        MockDesktopServices.url = url


class MockData:
    """Mock release data."""

    def decode(self, *a: Any) -> str:
        """Return a release as JSON."""
        return '{"tag_name": "v1.0"}'


class MockPayload:
    """Mock release payload."""

    def __enter__(self):
        """Enter the payload context."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the payload context."""
        return

    def read(self):
        """Return the release data."""
        return MockData()


class MockListData:
    """Mock empty release list data."""

    def decode(self, *a: Any) -> str:
        """Return an empty JSON list."""
        return "[]"


class MockListPayload:
    """Mock empty release list payload."""

    def __enter__(self):
        """Enter the payload context."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Exit the payload context."""
        return

    def read(self):
        """Return the empty list data."""
        return MockListData()


class MockHTTPError:
    """Mock payload that raises an HTTP error."""

    def __enter__(self):
        """Raise an HTTP error."""
        raise HTTPError("http://example.com", 403, "Rate limit", None, None)  # type: ignore

    def __exit__(self, *args: Any) -> None:
        """Exit the payload context."""
        return


class MockException:
    """Mock payload that raises a generic exception."""

    def __enter__(self):
        """Raise a generic exception."""
        raise Exception("Oh noes!")

    def __exit__(self, *args: Any) -> None:
        """Exit the payload context."""
        return


@pytest.mark.gui
def testVersionInfoWidget_Main(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, mockGUI: MockGuiMain):
    """Test the VersionInfoWidget class."""
    version = VersionInfoWidget(None)  # type: ignore
    dialog = SimpleDialog(version)
    dialog.show()

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.QDesktopServices", MockDesktopServices)
        version._processLink("#notes")
        assert MockDesktopServices.url == QUrl(nwConst.URL_RELEASES)

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.QDesktopServices", MockDesktopServices)
        version._processLink("#website")
        assert MockDesktopServices.url == QUrl(nwConst.URL_WEB)

    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo._Retriever", MockRetriever)
        mp.setattr(SHARED, "runInThreadPool", lambda *a: None)
        version._processLink("#update")
        assert version._lblRelease.text() == "Latest Version: Checking ..."

    # Unknown links do nothing
    version._processLink("#unknown")

    version._updateReleaseInfo("v2.0", "")
    assert version._lblRelease.text() == (
        "Latest Version: 2.0 \u2013 Download from <a href='#website'>novelwriter.io</a>"
    )

    version._updateReleaseInfo("", "")
    assert version._lblRelease.text() == "Latest Version: Failed"

    # The release label aligns with the layout direction
    assert version._lblRelease.alignment() == QtAlignAbsolute | QtAlignLeftMiddle
    rtlParent = QWidget()
    rtlParent.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    rtlVersion = VersionInfoWidget(rtlParent)
    assert rtlVersion._lblRelease.alignment() == QtAlignAbsolute | QtAlignRightMiddle

    dialog.close()
    # qtbot.stop()


@pytest.mark.gui
def testVersionInfoWidget_Retriever(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch):
    """Test the _Retriever class."""
    holder = MockSignalHolder()
    task = _Retriever(holder.dataReady)

    # Valid Data
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.urlopen", lambda *a, **k: MockPayload())
        with qtbot.waitSignal(holder.dataReady) as signal:
            task.run()
            assert signal.args == ["v1.0", ""]

    def httpErr():
        raise HTTPError("http://example.com", 403, "Rate limit")  # type: ignore

    # Non-Dict Response
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.urlopen", lambda *a, **k: MockListPayload())
        received = []
        holder.dataReady.connect(lambda tag, reason: received.append((tag, reason)))
        task.run()
        assert received == []

    # HTTP Error
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.urlopen", lambda *a, **k: MockHTTPError())
        with qtbot.waitSignal(holder.dataReady) as signal:
            task.run()
            assert signal.args == ["", "Rate limit (HTTP 403)"]

    # Other Error
    with monkeypatch.context() as mp:
        mp.setattr("novelwriter.extensions.versioninfo.urlopen", lambda *a, **k: MockException())
        with qtbot.waitSignal(holder.dataReady) as signal:
            task.run()
            assert signal.args == ["", "Oh noes!"]
