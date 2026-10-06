"""
novelWriter - App Init Tests
============================

This file is a part of novelWriter
Copyright (C) 2020 Veronica Berglyd Olsen and novelWriter contributors

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

import ctypes
import logging
import sys

from types import ModuleType
from unittest.mock import Mock

import pytest

from PyQt6.QtWidgets import QApplication

from novelwriter import BLUE, CONFIG, END, FILE, LINE, LVLC, LVLP, TEXT, TIME, WHITE, _createApp, logger, main
from novelwriter.splash import NSplashScreen

from tests.helpers import clearLogHandlers


@pytest.mark.base
def testInit_Launch(caplog, monkeypatch, fncPath):
    """Check launching the main GUI."""
    monkeypatch.setattr(NSplashScreen, "show", lambda *a: None)
    monkeypatch.setattr(NSplashScreen, "finish", lambda *a: None)
    monkeypatch.setattr("novelwriter.splash.sleep", lambda *a: None)
    monkeypatch.setattr("novelwriter._createApp", lambda *a: Mock())
    monkeypatch.setattr("novelwriter.guimain.GuiMain", Mock())
    monkeypatch.setattr(sys, "exit", Mock())

    # Default Launch
    main([f"--config={fncPath}", f"--data={fncPath}"])
    assert CONFIG._confPath == fncPath
    assert CONFIG._dataPath == fncPath

    # Darwin Launch Error Handling
    with monkeypatch.context() as mp:
        mp.setattr(sys, "platform", "darwin")
        mp.setitem(sys.modules, "Foundation", None)
        main([f"--config={fncPath}", f"--data={fncPath}"])

    # Darwin Launch, Success
    with monkeypatch.context() as mp:
        bundleInfo = {}
        mockBundle = Mock()
        mockBundle.localizedInfoDictionary = Mock(return_value=None)
        mockBundle.infoDictionary = Mock(return_value=bundleInfo)
        mockNSBundle = Mock()
        mockNSBundle.mainBundle = Mock(return_value=mockBundle)
        mockFoundation = ModuleType("Foundation")
        mockFoundation.NSBundle = mockNSBundle  # type: ignore
        mp.setattr(sys, "platform", "darwin")
        mp.setitem(sys.modules, "Foundation", mockFoundation)
        main([f"--config={fncPath}", f"--data={fncPath}"])
        assert bundleInfo["CFBundleName"] == "novelWriter"

    # Windows Launch Error Handling
    with monkeypatch.context() as mp:
        mp.setattr(sys, "platform", "win32")
        mp.setitem(sys.modules, "ctypes", None)
        main([f"--config={fncPath}", f"--data={fncPath}"])

    # Windows Launch, Success
    with monkeypatch.context() as mp:
        mp.setattr(sys, "platform", "win32")
        mp.setattr(ctypes, "windll", Mock(), raising=False)
        main([f"--config={fncPath}", f"--data={fncPath}"])

    # Other Platform
    with monkeypatch.context() as mp:
        mp.setattr(sys, "platform", "freebsd")
        main([f"--config={fncPath}", f"--data={fncPath}"])


@pytest.mark.base
def testInit_CreateApp(caplog, monkeypatch, fncPath):
    """Check creating the Qt app."""
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.__init__", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.setApplicationName", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.setApplicationVersion", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.setWindowIcon", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.setOrganizationDomain", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.exec", lambda *a: 0)

    app = _createApp()
    assert isinstance(app, QApplication)


@pytest.mark.base
def testInit_Options(monkeypatch, fncPath):
    """Test command line options for logging level."""
    monkeypatch.setattr(NSplashScreen, "show", lambda *a: None)
    monkeypatch.setattr(NSplashScreen, "finish", lambda *a: None)
    monkeypatch.setattr("novelwriter.splash.sleep", lambda *a: None)

    gui = Mock()
    app = Mock()
    app.exec = Mock(return_value=0)

    monkeypatch.setattr("novelwriter._createApp", lambda *a: app)
    monkeypatch.setattr("novelwriter.guimain.GuiMain", lambda *a: gui)
    monkeypatch.setattr(sys, "argv", ["novelWriter.py", f"--config={fncPath}", f"--data={fncPath}"])

    # Defaults wo/Args
    gui.reset_mock()
    with pytest.raises(SystemExit) as ex:
        main()
    assert ex.value.code == 0
    assert logger.getEffectiveLevel() == logging.WARNING
    gui.postLaunchTasks.assert_called_once()
    gui.postLaunchTasks.assert_called_with(None)

    # Defaults
    with pytest.raises(SystemExit) as ex:
        main([f"--config={fncPath}", f"--data={fncPath}", "--meminfo"])
    assert ex.value.code == 0
    assert CONFIG.memInfo is True

    def getFormat() -> str:
        formatter = logger.handlers[0].formatter
        assert formatter is not None
        fmt = formatter._fmt
        assert fmt is not None
        return fmt

    # Log Levels w/Color
    clearLogHandlers()
    with pytest.raises(SystemExit) as ex:
        main(["--info", "--color", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0
    assert logger.getEffectiveLevel() == logging.INFO
    assert getFormat() == f"{LVLC}  {TEXT}"

    clearLogHandlers()
    with pytest.raises(SystemExit) as ex:
        main(["--debug", "--color", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert getFormat() == f"{TIME}  {BLUE}{FILE}{END}:{WHITE}{LINE}{END}  {LVLC}  {TEXT}"

    # Log Levels wo/Color
    clearLogHandlers()
    with pytest.raises(SystemExit) as ex:
        main(["--info", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0
    assert logger.getEffectiveLevel() == logging.INFO
    assert getFormat() == f"{LVLP}  {TEXT}"

    clearLogHandlers()
    with pytest.raises(SystemExit) as ex:
        main(["--debug", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert getFormat() == f"{TIME}  {FILE}:{LINE}  {LVLP}  {TEXT}"

    # Help and Version
    with pytest.raises(SystemExit) as ex:
        main(["--help", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0

    with pytest.raises(SystemExit) as ex:
        main(["--version", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 0

    # Invalid options
    with pytest.raises(SystemExit) as ex:
        main(["--invalid", f"--config={fncPath}", f"--data={fncPath}"])
    assert ex.value.code == 2

    # Project Path
    gui.reset_mock()
    with pytest.raises(SystemExit) as ex:
        main([f"--config={fncPath}", f"--data={fncPath}", "sample/"])
    assert ex.value.code == 0
    gui.postLaunchTasks.assert_called_once()
    gui.postLaunchTasks.assert_called_with("sample/")


@pytest.mark.base
def testInit_Imports(caplog, monkeypatch, fncPath):
    """Check import error handling."""
    monkeypatch.setattr("novelwriter._createApp", lambda *a: Mock())
    monkeypatch.setattr("novelwriter.guimain.GuiMain", lambda *a: Mock())

    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.__init__", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QApplication.exec", lambda *a: 0)
    monkeypatch.setattr("PyQt6.QtWidgets.QErrorMessage.__init__", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QErrorMessage.resize", lambda *a: None)
    monkeypatch.setattr("PyQt6.QtWidgets.QErrorMessage.showMessage", lambda *a: None)
    monkeypatch.setattr("sys.hexversion", 0x0)
    monkeypatch.setattr("novelwriter.CONFIG.verQtValue", 0x050000)
    monkeypatch.setattr("novelwriter.CONFIG.verPyQtValue", 0x050000)

    with pytest.raises(SystemExit) as ex:
        main([f"--config={fncPath}", f"--data={fncPath}"])

    assert ex.value.code & 4 == 4  # Python version not satisfied  # type: ignore
    assert ex.value.code & 8 == 8  # Qt version not satisfied  # type: ignore
    assert ex.value.code & 16 == 16  # PyQt version not satisfied  # type: ignore

    assert "At least Python" in caplog.messages[0]
    assert "At least Qt6" in caplog.messages[1]
    assert "At least PyQt6" in caplog.messages[2]
