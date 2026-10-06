"""
novelWriter - App Splash Screen Tests
=====================================

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

import logging

import pytest

from PyQt6.QtGui import QPainter, QPixmap

from novelwriter.splash import NSplashScreen


@pytest.mark.gui
def testSplash_Main(caplog, monkeypatch):
    """Check the splash screen's initial state, status updates, and painting."""
    monkeypatch.setattr("novelwriter.splash.sleep", lambda *a: None)
    splash = NSplashScreen()
    assert splash._text == ""
    assert splash.font().pointSizeF() == 12.0

    caplog.set_level(logging.INFO)

    # A non-empty message is logged
    splash.showStatus("Starting novelWriter ...")
    assert splash._text == "Starting novelWriter ..."
    assert "Starting novelWriter ..." in caplog.text

    # An empty message is not logged
    caplog.clear()
    splash.showStatus("")
    assert splash._text == ""
    assert caplog.text == ""

    # The status text is painted onto the splash screen
    splash._text = "Loading ..."
    pixmap = QPixmap(500, 300)
    painter = QPainter(pixmap)
    splash.drawContents(painter)
    painter.end()
