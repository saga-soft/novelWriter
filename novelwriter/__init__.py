"""
novelWriter - Init File
=======================

This file is a part of novelWriter
Copyright (C) 2018 Veronica Berglyd Olsen and novelWriter contributors

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

import gc
import getopt
import logging
import os
import sys

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QApplication, QErrorMessage

from novelwriter.config import Config
from novelwriter.error import exceptionHandler
from novelwriter.shared import SharedData
from novelwriter.splash import NSplashScreen

if TYPE_CHECKING:
    from novelwriter.guimain import GuiMain

# Package Meta
# ============

# fmt: off
__package__    = "novelwriter"
__copyright__  = "Copyright 2018-2026 Veronica Berglyd Olsen"
__license__    = "GPLv3"
__author__     = "Veronica Berglyd Olsen"
__maintainer__ = "Veronica Berglyd Olsen"
__email__      = "code@vkbo.net"
__version__    = "26.3a0"
__hexversion__ = "0x260300a0"
__date__       = "2026-07-30"
__status__     = "Stable"
__domain__     = "novelwriter.io"
# fmt: on

logger = logging.getLogger(__name__)


##
#  Main Program
##

# Globals Singletons
CONFIG = Config()
SHARED = SharedData()

# ANSI Colours
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
WHITE = "\033[97m"
END = "\033[0m"

# Log Format Components
TIME = "[{asctime:}]"
FILE = "{filename:>18}"
LINE = "{lineno:<4d}"
LVLP = "{levelname:8}"
LVLC = "{levelname:17}"
TEXT = "{message:}"

# Read Environment
FORCE_COLOR = bool(os.environ.get("FORCE_COLOR"))
NO_COLOR = bool(os.environ.get("NO_COLOR"))


def main(sysArgs: list | None = None) -> GuiMain | None:
    """Parse command line, set up logging, and launch main GUI."""
    if sysArgs is None:
        sysArgs = sys.argv[1:]

    # Valid Input Options
    shortOpt = "hvidc"
    longOpt = ["help", "version", "info", "debug", "color", "config=", "data=", "meminfo"]

    helpMsg = (
        f"novelWriter {__version__} ({__date__})\n"
        f"{__copyright__}\n"
        "\n"
        "This program is free software: you can redistribute it and/or modify\n"
        "it under the terms of the GNU General Public License as published by\n"
        "the Free Software Foundation, either version 3 of the License, or\n"
        "(at your option) any later version.\n"
        "\n"
        "This program is distributed in the hope that it will be useful,\n"
        "but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
        "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the\n"
        "GNU General Public Licence for more details.\n"
        "\n"
        "You should have received a copy of the GNU General Public License\n"
        "along with this program. If not, see <https://www.gnu.org/licenses/>.\n"
        "\n"
        "Usage:\n"
        " -h, --help     Print this message.\n"
        " -v, --version  Print program version and exit.\n"
        " -i, --info     Print additional runtime information.\n"
        " -d, --debug    Print debug output. Includes --info.\n"
        " -c, --color    Add ANSI colors to log output.\n"
        "     --meminfo  Show memory usage information in the status bar.\n"
        "     --config=  Alternative config file.\n"
        "     --data=    Alternative user data path.\n"
    )

    # Defaults
    logLevel = logging.WARNING
    fmtColor = FORCE_COLOR
    fmtLong = False
    confPath = None
    dataPath = None
    cmdOpen = None

    # Parse Options
    try:
        inOpts, inRemain = getopt.getopt(sysArgs, shortOpt, longOpt)
    except getopt.GetoptError as exc:
        print(helpMsg)
        print(f"ERROR: {exc!s}")
        sys.exit(2)

    if len(inRemain) > 0:
        cmdOpen = inRemain[0]

    for inOpt, inArg in inOpts:
        if inOpt in ("-h", "--help"):
            print(helpMsg)
            sys.exit(0)
        elif inOpt in ("-v", "--version"):
            print(f"novelWriter Version {__version__} [{__date__}]")
            sys.exit(0)
        elif inOpt in ("-i", "--info"):
            logLevel = logging.INFO
        elif inOpt in ("-d", "--debug"):
            CONFIG.isDebug = True
            fmtLong = True
            logLevel = logging.DEBUG
        elif inOpt in ("-c", "--color"):
            fmtColor = not NO_COLOR
        elif inOpt == "--meminfo":
            CONFIG.memInfo = True
        elif inOpt == "--config":
            confPath = inArg
        elif inOpt == "--data":
            dataPath = inArg
        else:  # pragma: no cover
            pass

    if fmtColor:
        # This will overwrite the default level names, and also ensure that
        # they can be converted back to integer levels
        logging.addLevelName(logging.DEBUG, f"{BLUE}DEBUG{END}")
        logging.addLevelName(logging.INFO, f"{GREEN}INFO{END}")
        logging.addLevelName(logging.WARNING, f"{YELLOW}WARNING{END}")
        logging.addLevelName(logging.ERROR, f"{RED}ERROR{END}")
        logging.addLevelName(logging.CRITICAL, f"{RED}CRITICAL{END}")

    logTxt = f"{LVLC}  {TEXT}" if fmtColor else f"{LVLP}  {TEXT}"
    logPos = f"{BLUE}{FILE}{END}:{WHITE}{LINE}{END}" if fmtColor else f"{FILE}:{LINE}"
    logFmt = f"{TIME}  {logPos}  {logTxt}" if fmtLong else logTxt

    # Setup Logging
    pkgLogger = logging.getLogger(__package__)
    pkgLogger.setLevel(logLevel)
    if len(pkgLogger.handlers) == 0:
        # Make sure we only create one logger (mostly an issue with tests)
        cHandle = logging.StreamHandler()
        cHandle.setFormatter(logging.Formatter(fmt=logFmt, style="{"))
        pkgLogger.addHandler(cHandle)

    logger.info("Starting novelWriter %s (%s) %s", __version__, __hexversion__, __date__)

    # Disable GC, running in GuiMain instead (#2927)
    gc.disable()

    # Check Packages and Versions
    errorData = []
    errorCode = 0
    if sys.hexversion < 0x030B00F0:
        errorData.append(f"At least Python 3.11 is required, found {CONFIG.verPyString}")
        errorCode |= 0x04
    if CONFIG.verQtValue < 0x060400:
        errorData.append(f"At least Qt6 version 6.4 is required, found {CONFIG.verQtString}")
        errorCode |= 0x08
    if CONFIG.verPyQtValue < 0x060400:
        errorData.append(f"At least PyQt6 version 6.4 is required, found {CONFIG.verPyQtString}")
        errorCode |= 0x10

    if errorData:
        errApp = QApplication([])
        errDlg = QErrorMessage()
        errDlg.resize(500, 300)
        errDlg.showMessage(
            (
                "<h3>A critical error was encountered</h3>"
                "<p>novelWriter cannot start due to the following issues:<p>"
                "<p>&nbsp;-&nbsp;{0}</p>"
                "<p>Shutting down ...</p>"
            ).format("<br>&nbsp;-&nbsp;".join(errorData))
        )
        for errLine in errorData:
            logger.critical(errLine)
        errApp.exec()
        sys.exit(errorCode)

    # Finish initialising config
    CONFIG.initConfig(confPath, dataPath)

    if sys.platform == "linux":
        QApplication.setDesktopFileName(CONFIG.appHandle)
    elif sys.platform == "darwin":
        try:
            from Foundation import NSBundle  # type: ignore

            bundle = NSBundle.mainBundle()
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            info["CFBundleName"] = "novelWriter"
        except Exception:
            pass  # Quietly ignore error
    elif sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("io.novelwriter.app")  # type: ignore
        except Exception:
            pass  # Quietly ignore error

    # Import GUI (after dependency checks), and launch
    from novelwriter.gui.theme import GuiTheme
    from novelwriter.guimain import GuiMain

    # Create App
    app = _createApp()

    # Connect the exception handler before making the main GUI
    sys.excepthook = exceptionHandler

    splash = NSplashScreen()
    splash.show()

    splash.showStatus("")
    splash.showStatus("Starting novelWriter ...")

    # Run Config steps that require the QApplication
    CONFIG.loadConfig(splash)
    CONFIG.initLocalisation(app)
    SHARED.initTheme(GuiTheme())

    # Launch main GUI
    nwGUI = GuiMain()
    nwGUI.showNormal()
    splash.finish(nwGUI)

    CONFIG.finishStartup()
    del splash

    nwGUI.postLaunchTasks(cmdOpen)

    code = app.exec()
    logger.info("novelWriter exited with code %d", code)
    sys.exit(code)


def _createApp() -> QApplication:
    """Create the app. This is done in a function to make it easier to
    block app creation during testing.
    """
    app = QApplication([CONFIG.appName])
    app.setStyle("Fusion")
    app.setApplicationName(CONFIG.appName)
    app.setApplicationVersion(__version__)
    app.setOrganizationDomain(__domain__)
    app.setOrganizationName(__domain__)

    return app
