"""
novelWriter - Error Handler Tests
=================================

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

import sys

from types import ModuleType

import pytest

from pytestqt.qtbot import QtBot

from novelwriter import CONFIG
from novelwriter.error import ErrorMessage, exceptionHandler, logException
from novelwriter.guimain import GuiMain

from tests.mocked import causeException


@pytest.mark.base
def testError_LogException(caplog: pytest.LogCaptureFixture):
    """Test that logging an exception outside of an except block, where
    there is no active exception, does nothing.
    """
    caplog.clear()
    logException()
    assert caplog.text == ""


@pytest.mark.base
def testError_Dialog(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, nwGUI: GuiMain):
    """Test the error dialog."""
    nwErr = ErrorMessage(nwGUI)
    qtbot.addWidget(nwErr)
    nwErr.show()

    # Invalid Error Message
    nwErr.setMessage(Exception, "Faulty Error", 123)  # type: ignore
    assert nwErr.msgBody.toPlainText() == "Failed to generate error report ..."

    # Valid Error Message
    with monkeypatch.context() as mp:
        mp.setattr("PyQt6.QtCore.QSysInfo.kernelVersion", lambda: "1.2.3")
        nwErr.setMessage(Exception, "Fine Error", None)  # type: ignore
        message = nwErr.msgBody.toPlainText()
        assert message != ""
        assert "Fine Error" in message
        assert "Exception" in message
        assert "(1.2.3)" in message
        assert "Spell Check: Unknown" not in message

    # No kernel version retrieved
    with monkeypatch.context() as mp:
        mp.setattr("PyQt6.QtCore.QSysInfo.kernelVersion", causeException)
        nwErr.setMessage(Exception, "Almost Fine Error", None)  # type: ignore
        message = nwErr.msgBody.toPlainText()
        assert message != ""
        assert "(Unknown)" in message

    # No spell check version retrieved
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "objc", None)
        mp.setitem(sys.modules, "enchant", None)
        nwErr.setMessage(Exception, "Almost Fine Error", None)  # type: ignore
        message = nwErr.msgBody.toPlainText()
        assert message != ""
        assert "Spell Check: Unknown" in message

    # Spell check versions per platform
    objc = ModuleType("objc")
    objc.__dict__["__version__"] = "1.2"
    enchant = ModuleType("enchant")
    enchant.__dict__["__version__"] = "3.4"
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "objc", objc)
        mp.setitem(sys.modules, "enchant", enchant)

        mp.setattr(CONFIG, "osDarwin", True)
        nwErr.setMessage(Exception, "Fine Error", None)  # type: ignore
        assert "Spell Check: AppleSpell (PyObjC 1.2)" in nwErr.msgBody.toPlainText()

        mp.setattr(CONFIG, "osDarwin", False)
        nwErr.setMessage(Exception, "Fine Error", None)  # type: ignore
        assert "Spell Check: Enchant 3.4" in nwErr.msgBody.toPlainText()

    nwErr._doClose()
    nwErr.close()
    nwGUI.closeMain()


@pytest.mark.base
def testError_Handler(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch, nwGUI: GuiMain):
    """Test the error handler. This test doesn't have any asserts, but
    it checks that the error handler handles potential exceptions. The
    test will fail if exceptions are not handled.
    """
    # Normal shutdown
    with monkeypatch.context() as mp:
        mp.setattr(ErrorMessage, "exec", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.exit", lambda *a: None)
        exceptionHandler(Exception, "Error Message", None)  # type: ignore

    # Should not crash when no GUI is found
    with monkeypatch.context() as mp:
        mp.setattr(ErrorMessage, "exec", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.exit", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.topLevelWidgets", list)
        exceptionHandler(Exception, "Error Message", None)  # type: ignore

    # Should handle QApplication failing
    with monkeypatch.context() as mp:
        mp.setattr(ErrorMessage, "exec", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.exit", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.topLevelWidgets", causeException)
        exceptionHandler(Exception, "Error Message", None)  # type: ignore

    # Should handle failing to close main GUI
    with monkeypatch.context() as mp:
        mp.setattr(ErrorMessage, "exec", lambda *a: None)
        mp.setattr("PyQt6.QtWidgets.QApplication.exit", lambda *a: None)
        mp.setattr("novelwriter.guimain.GuiMain.closeMain", causeException)
        exceptionHandler(Exception, "Error Message", None)  # type: ignore

    nwGUI.closeMain()
