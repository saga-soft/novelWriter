"""
novelWriter - Exception Handling
================================

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

import logging
import random
import sys

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QStyle,
    QWidget,
)

if TYPE_CHECKING:
    from types import TracebackType

logger = logging.getLogger(__name__)


def logException() -> None:
    """Log the content of an exception message."""
    exType, exValue, _ = sys.exc_info()
    if exType is not None:
        logger.error(f"{exType.__name__}: {exValue!s}", stacklevel=2)  # noqa: G004


def formatException(exc: BaseException) -> str:
    """Format an exception as a string the same way the default
    exception handler does.
    """
    return f"{type(exc).__name__}: {exc!s}"


class ErrorMessage(QDialog):
    """GUI: Error Dialog."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)
        self.setObjectName("ErrorMessage")

        # Widgets
        self.msgIcon = QLabel()
        if style := QApplication.style():  # pragma: no branch
            self.msgIcon.setPixmap(style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxCritical).pixmap(64, 64))

        self.msgHead = QLabel()
        self.msgHead.setOpenExternalLinks(True)
        self.msgHead.setWordWrap(True)

        font = QFont()
        font.setPointSize(round(0.9 * self.font().pointSize()))
        font.setFamily(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family())

        self.msgBody = QPlainTextEdit()
        self.msgBody.setFont(font)
        self.msgBody.setReadOnly(True)

        self.btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.btnBox.rejected.connect(self._doClose)

        # Assemble
        self.mainBox = QGridLayout()
        self.mainBox.addWidget(self.msgIcon, 0, 0, 2, 1, Qt.AlignmentFlag.AlignTop)
        self.mainBox.addWidget(self.msgHead, 0, 1, 1, 1, Qt.AlignmentFlag.AlignTop)
        self.mainBox.addWidget(self.msgBody, 1, 1, 1, 1)
        self.mainBox.addWidget(self.btnBox, 2, 0, 1, 2)
        self.mainBox.setSpacing(16)

        # Pick a random window title from a set of error messages by
        # Hex the computer, Unseen University, Ankh-Morpork, Discworld
        # and other Discworld references
        self.setWindowTitle(
            [
                "+++ Out of Cheese Error +++",
                "+++ Divide by Cucumber Error +++",
                "+++ Please Reinstall Universe and Reboot +++",
                "+++ Error At Address 14, Treacle Mine Road +++",
                "+++ Abomination Unto Nuggan Error +++",
                "+++ Anoia Error: Cutlery Stuck in Drawer +++",
            ][random.randint(0, 5)]
        )

        self.setLayout(self.mainBox)

        self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setSizeGripEnabled(True)
        self.resize(800, 400)

    def setMessage(self, exType: type, exValue: BaseException, exTrace: TracebackType) -> None:
        """Generate a message and append session data, error info and
        error traceback.
        """
        from traceback import format_tb

        from PyQt6.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QSysInfo

        from novelwriter import CONFIG, __version__
        from novelwriter.constants import nwConst

        self.msgHead.setText(
            "<p>An unhandled error has been encountered.</p>"
            "<p>Please report this error by submitting an issue report on "
            "GitHub, providing a description, and including the error "
            "message and traceback shown below.</p>"
            f"<p>URL: <a href='{nwConst.URL_REPORT}'>{nwConst.URL_REPORT}</a></p>"
        )

        try:
            kernelVersion = QSysInfo.kernelVersion()
        except Exception:
            kernelVersion = "Unknown"

        try:
            import enchant

            enchantVersion = enchant.__version__
        except Exception:
            enchantVersion = "Unknown"

        try:
            trace = "\n".join(format_tb(exTrace))
            self.msgBody.setPlainText(
                "Environment:\n"
                f"novelWriter Version: {__version__}\n"
                f"Install Info: {CONFIG.buildFormat} ({CONFIG.installSource})\n"
                f"Host OS: {sys.platform} ({kernelVersion})\n"
                f"Python: {sys.version.split()[0]} ({sys.hexversion:#x})\n"
                f"Qt: {QT_VERSION_STR}, PyQt: {PYQT_VERSION_STR}\n"
                f"Enchant: {enchantVersion}\n\n"
                f"{exType.__name__}:\n{exValue!s}\n\n"
                f"Traceback:\n{trace}\n"
            )
        except Exception:
            self.msgBody.setPlainText("Failed to generate error report ...")

    ##
    #  Slots
    ##

    @pyqtSlot()
    def _doClose(self) -> None:
        """Close the dialog."""
        self.close()


def exceptionHandler(exType: type, exValue: BaseException, exTrace: TracebackType) -> None:
    """Catch unhandled global exceptions."""
    from traceback import print_tb

    from PyQt6.QtWidgets import QApplication

    logger.critical("%s: %s", exType.__name__, exValue)
    print_tb(exTrace)

    try:
        nwGUI = None
        for qWin in QApplication.topLevelWidgets():
            if qWin.objectName() == "GuiMain":  # pragma: no branch (this branch is flaky)
                nwGUI = qWin
                break

        if nwGUI is None:
            logger.warning("Could not find main GUI window so cannot open error dialog")
            return

        errMsg = ErrorMessage(nwGUI)
        errMsg.setMessage(exType, exValue, exTrace)
        errMsg.exec()

        try:
            # Try a controlled shutdown
            nwGUI.closeProject(isYes=True)  # type: ignore
            nwGUI.closeMain()  # type: ignore
            logger.info("Emergency shutdown successful")

        except Exception as exc:
            logger.critical("Could not close the project before exiting")
            logger.critical(formatException(exc))

        QApplication.exit(1)

    except Exception as exc:
        logger.critical(formatException(exc))

    return
