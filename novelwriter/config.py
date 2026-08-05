"""
novelWriter - Config Class
==========================

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

import json
import logging
import sys

from pathlib import Path
from time import time
from typing import TYPE_CHECKING, Final

from PyQt6.QtCore import (
    PYQT_VERSION,
    PYQT_VERSION_STR,
    QT_VERSION,
    QT_VERSION_STR,
    QDate,
    QDateTime,
    QLibraryInfo,
    QLocale,
    QRect,
    QStandardPaths,
    QSysInfo,
    QTranslator,
)
from PyQt6.QtGui import QFont, QFontDatabase, QFontMetrics
from PyQt6.QtWidgets import QApplication

from novelwriter.common import (
    checkInt,
    checkPath,
    compact,
    describeFont,
    fontMatcher,
    formatTimeStamp,
    joinLines,
    languageName,
    processDialogSymbols,
    safeExists,
    safeIsDir,
    simplified,
    uniqueCompact,
)
from novelwriter.constants import nwFiles, nwQuotes, nwUnicode, trStats
from novelwriter.enum import nwTheme
from novelwriter.error import formatException, logException
from novelwriter.formats.configparser import NConfigParser
from novelwriter.formats.tomlparser import NTomlParser

if TYPE_CHECKING:
    from datetime import datetime

    from novelwriter.core.projectdata import ProjectData
    from novelwriter.formats.tomlparser import T_TomlConfig
    from novelwriter.splash import NSplashScreen

logger = logging.getLogger(__name__)

DEF_GUI_DARK = "default_dark"
DEF_GUI_LIGHT = "default_light"
DEF_ICONS = "material_rounded_normal"
DEF_TREECOL = "theme"


class Config:
    """User Config.

    The main user config. The state of the config is stored in the
    novelwriter.conf file between sessions. Most of the settings can be
    modified by the user in the Preferences dialog, but some just record
    various states of the GUI.
    """

    __slots__ = (
        "_appPath",
        "_appRoot",
        "_backPath",
        "_backupPath",
        "_confPath",
        "_dLocale",
        "_dShortDate",
        "_dShortDateTime",
        "_dataPath",
        "_errData",
        "_hasError",
        "_homePath",
        "_lastAuthor",
        "_manuals",
        "_nwLangPath",
        "_qLocale",
        "_qtLangPath",
        "_qtTrans",
        "_recentPaths",
        "_recentProjects",
        "_splash",
        "allowOpenDial",
        "altDialogClose",
        "altDialogOpen",
        "appHandle",
        "appName",
        "askBeforeBackup",
        "askBeforeExit",
        "autoSaveDoc",
        "autoSaveProj",
        "autoScroll",
        "autoScrollPos",
        "autoSelect",
        "backupInterval",
        "backupOnClose",
        "countUnit",
        "cursorWidth",
        "darkTheme",
        "dialogLine",
        "dialogStyle",
        "doJustify",
        "doReplace",
        "doReplaceDQuote",
        "doReplaceDash",
        "doReplaceDots",
        "doReplaceSQuote",
        "dottedModCodes",
        "emphLabels",
        "fmtApostrophe",
        "fmtDQuoteClose",
        "fmtDQuoteOpen",
        "fmtPadAfter",
        "fmtPadBefore",
        "fmtPadThin",
        "fmtSQuoteClose",
        "fmtSQuoteOpen",
        "focusWidth",
        "fontWinSize",
        "guiFont",
        "guiLocale",
        "hasEnchant",
        "hideFocusFooter",
        "hideHScroll",
        "hideVScroll",
        "highlightEmph",
        "hostName",
        "iconColDocs",
        "iconColTree",
        "iconTheme",
        "incNotesWCount",
        "isDebug",
        "kernelVer",
        "lastNotes",
        "lightTheme",
        "lineHeight",
        "lineHighlight",
        "mainPanePos",
        "mainWinSize",
        "memInfo",
        "moveMainWin",
        "narratorBreak",
        "narratorDialog",
        "nativeFont",
        "osDarwin",
        "osLinux",
        "osType",
        "osUnknown",
        "osWindows",
        "prefsWinSize",
        "scaleHeadings",
        "scrollPastEnd",
        "searchAuto",
        "searchCase",
        "searchLoop",
        "searchMatchCap",
        "searchNextFile",
        "searchPanePos",
        "searchProjAuto",
        "searchProjCase",
        "searchProjRegEx",
        "searchProjWord",
        "searchRegEx",
        "searchWord",
        "showDetailsPanel",
        "showEditToolBar",
        "showFullPath",
        "showLineEndings",
        "showMultiSpaces",
        "showSessionTime",
        "showTabsNSpaces",
        "showViewerPanel",
        "singleStarBold",
        "spellLanguage",
        "stopWhenIdle",
        "tabWidth",
        "textFont",
        "textMargin",
        "textWidth",
        "themeMode",
        "useCharCount",
        "userIdleTime",
        "verPyQtString",
        "verPyQtValue",
        "verPyString",
        "verQtString",
        "verQtValue",
        "viewComments",
        "viewNotes",
        "viewPanePos",
        "viewSynopsis",
        "vimMode",
        "welcomeWinSize",
    )

    LANG_NW = 1
    LANG_PROJ = 2

    def __init__(self) -> None:

        # Initialisation
        # ==============

        self._splash = None

        # Set Application Variables
        self.appName = "novelWriter"
        self.appHandle = "novelwriter"

        # Set Paths
        confRoot = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.ConfigLocation))
        dataRoot = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))

        self._confPath = confRoot.absolute() / self.appHandle  # The user config location
        self._dataPath = dataRoot.absolute() / self.appHandle  # The user data location
        self._homePath = Path.home().absolute()  # The user's home directory
        self._backPath = self._homePath / "Backups"

        self._appPath = Path(__file__).parent.absolute()
        self._appRoot = self._appPath.parent
        if getattr(sys, "frozen", False):  # pragma: no cover
            # novelWriter is packaged as an exe
            self._appPath = Path(__file__).parent.parent.absolute()
            self._appRoot = self._appPath

        # Runtime Settings and Variables
        self._hasError = False  # True if the config class encountered an error
        self._errData = []  # List of error messages

        # Localisation
        # Note that these paths must be strings
        self._nwLangPath = self._appPath / "assets" / "i18n"
        self._qtLangPath = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)

        hasLocale = safeExists(self._nwLangPath / f"nw_{QLocale.system().name()}.qm")
        self._qLocale = QLocale.system() if hasLocale else QLocale("en_GB")
        self._dLocale = QLocale.system()
        self._dShortDate = self._dLocale.dateFormat(QLocale.FormatType.ShortFormat)
        self._dShortDateTime = self._dLocale.dateTimeFormat(QLocale.FormatType.ShortFormat)
        self._qtTrans = {}

        # PDF Manual
        self._manuals: dict[str, Path] = {}
        try:
            if (assets := self._appPath / "assets").is_dir():
                for item in assets.iterdir():
                    if item.is_file() and item.stem.startswith("manual") and item.suffix == ".pdf":
                        self._manuals[item.stem] = item
        except Exception:
            logException()

        # User Settings
        # =============

        self._recentProjects = RecentProjects(self)
        self._recentPaths = RecentPaths(self)
        self._lastAuthor = ""

        # General GUI Settings
        self.guiLocale = self._qLocale.name()
        self.lightTheme = DEF_GUI_LIGHT  # Light GUI theme
        self.darkTheme = DEF_GUI_DARK  # Dark GUI theme
        self.themeMode = nwTheme.AUTO  # Colour theme mode
        self.guiFont = QFont()  # Main GUI font
        self.hideVScroll = False  # Hide vertical scroll bars on main widgets
        self.hideHScroll = False  # Hide horizontal scroll bars on main widgets
        self.lastNotes = "0x0"  # The latest release notes that have been shown
        self.nativeFont = True  # Use native font dialog
        self.useCharCount = False  # Use character count as primary count
        self.countUnit = "words"  # Primary count unit
        self.vimMode = False  # Enable Vim mode

        # Icons
        self.iconTheme = DEF_ICONS  # Icons theme
        self.iconColTree = DEF_TREECOL  # Project tree icon colours
        self.iconColDocs = False  # Keep theme colours on documents

        # Size Settings
        self.mainWinSize = [1200, 650]  # Last size of the main GUI window
        self.welcomeWinSize = [800, 550]  # Last size of the welcome window
        self.prefsWinSize = [700, 615]  # Last size of the Preferences dialog
        self.fontWinSize = [700, 550]  # Last size of the Font dialog
        self.mainPanePos = [300, 800]  # Last position of the main window splitter
        self.viewPanePos = [500, 150]  # Last position of the document viewer splitter
        self.searchPanePos = [150, 500]  # Last position of the project search splitter
        self.moveMainWin = True  # Move main window to the screen middle on startup

        # Project Settings
        self.autoSaveProj = 60  # Interval for auto-saving project, in seconds
        self.autoSaveDoc = 30  # Interval for auto-saving document, in seconds
        self.emphLabels = False  # Add emphasis to H1 and H2 item labels
        self.backupOnClose = True  # Flag for running automatic backups
        self.backupInterval = "session"  # Backup interval
        self.askBeforeBackup = True  # Flag for asking before running automatic backup
        self.askBeforeExit = True  # Flag for asking before exiting the app

        # Text Editor Settings
        self.textFont = QFont()  # Editor font
        self.textWidth = 700  # Editor text width
        self.textMargin = 40  # Editor/viewer text margin
        self.tabWidth = 40  # Editor tabulator width
        self.lineHeight = 1.0  # Editor line height
        self.cursorWidth = 1  # Editor cursor width
        self.lineHighlight = False  # Highlight current line in editor

        self.focusWidth = 800  # Focus Mode text width
        self.hideFocusFooter = False  # Hide document footer in Focus Mode
        self.showFullPath = True  # Show full document path in editor header
        self.autoSelect = True  # Auto-select word when applying format with no selection

        self.doJustify = False  # Justify text
        self.showTabsNSpaces = False  # Show tabs and spaces in editor
        self.showLineEndings = False  # Show line endings in editor
        self.showMultiSpaces = False  # Highlight multiple spaces in the text
        self.scaleHeadings = True  # Use a larger size for headings
        self.singleStarBold = False  # Allow single asterisk bold

        self.doReplace = True  # Enable auto-replace as you type
        self.doReplaceSQuote = True  # Smart single quotes
        self.doReplaceDQuote = True  # Smart double quotes
        self.doReplaceDash = True  # Replace multiple hyphens with dashes
        self.doReplaceDots = True  # Replace three dots with ellipsis

        self.autoScroll = True  # Typewriter-like scrolling
        self.autoScrollPos = 30  # Start point for typewriter-like scrolling
        self.scrollPastEnd = True  # Scroll past end of document, and centre cursor

        self.dialogStyle = 2  # Quote type to use for dialogue
        self.allowOpenDial = True  # Allow open-ended dialogue quotes
        self.dialogLine = ""  # Symbol to use for dialogue line
        self.narratorBreak = ""  # Symbol to use for narrator break
        self.narratorDialog = ""  # Symbol for alternating between dialogue and narrator
        self.altDialogOpen = ""  # Alternative dialog symbol, open
        self.altDialogClose = ""  # Alternative dialog symbol, close
        self.highlightEmph = True  # Add colour to text emphasis
        self.dottedModCodes = False  # Add dotted lines under codes and modifiers

        self.stopWhenIdle = True  # Stop the status bar clock when the user is idle
        self.userIdleTime = 300  # Time of inactivity to consider user idle
        self.incNotesWCount = True  # The status bar word count includes notes

        # User-Selected Symbol Settings
        self.fmtApostrophe = nwUnicode.U_RSQUO
        self.fmtSQuoteOpen = nwUnicode.U_LSQUO
        self.fmtSQuoteClose = nwUnicode.U_RSQUO
        self.fmtDQuoteOpen = nwUnicode.U_LDQUO
        self.fmtDQuoteClose = nwUnicode.U_RDQUO
        self.fmtPadBefore = ""
        self.fmtPadAfter = ""
        self.fmtPadThin = False

        # User Paths
        self._backupPath = self._backPath  # Backup path to use, can be none

        # Spell Checking Settings
        self.spellLanguage = "en"

        # State
        self.showDetailsPanel = True  # The panel for the item details is visible
        self.showViewerPanel = True  # The panel for the viewer is visible
        self.showEditToolBar = False  # The document editor toolbar visibility
        self.showSessionTime = True  # Show the session time in the status bar
        self.viewComments = True  # Comments are shown in the viewer
        self.viewSynopsis = True  # Synopsis is shown in the viewer
        self.viewNotes = True  # Notes are shown in the viewer

        # Search Box States
        self.searchAuto = False
        self.searchCase = False
        self.searchWord = False
        self.searchRegEx = False
        self.searchLoop = False
        self.searchNextFile = False
        self.searchMatchCap = False
        self.searchProjAuto = False
        self.searchProjCase = False
        self.searchProjWord = False
        self.searchProjRegEx = False

        # System and App Information
        # ==========================

        # Check Qt Versions
        self.verQtString = QT_VERSION_STR
        self.verQtValue = QT_VERSION
        self.verPyQtString = PYQT_VERSION_STR
        self.verPyQtValue = PYQT_VERSION

        # Check Python Version
        self.verPyString = sys.version.split()[0]

        # Check OS Type
        self.osType = sys.platform
        self.osLinux = False
        self.osWindows = False
        self.osDarwin = False
        self.osUnknown = False
        if self.osType.startswith("linux"):
            self.osLinux = True
        elif self.osType.startswith("darwin"):
            self.osDarwin = True
        elif self.osType.startswith("win32") or self.osType.startswith("cygwin"):
            self.osWindows = True
        else:
            self.osUnknown = True

        # Other System Info
        self.hostName = QSysInfo.machineHostName()
        self.kernelVer = QSysInfo.kernelVersion()
        self.isDebug = False  # True if running in debug mode
        self.memInfo = False  # True if displaying mem info in status bar

        # Packages
        self.hasEnchant = False  # The pyenchant package

    ##
    #  Properties
    ##

    @property
    def hasError(self) -> bool:
        """Return True if the config class encountered an error."""
        return self._hasError

    @property
    def pdfDocs(self) -> Path | None:
        """Return the local manual PDF file, if any exist."""
        return self._manuals.get(f"manual_{self.locale.bcp47Name()}", self._manuals.get("manual"))

    @property
    def nwLangPath(self) -> Path:
        """Return the path to the novelWriter language files."""
        return self._nwLangPath

    @property
    def locale(self) -> QLocale:
        """Return the current GUI locale."""
        return self._dLocale

    @property
    def recentProjects(self) -> RecentProjects:
        """Return the recent projects list."""
        return self._recentProjects

    @property
    def lastAuthor(self) -> str:
        """Return the last author name used."""
        return self._lastAuthor

    ##
    #  Getters
    ##

    def getTextWidth(self, focusMode: bool = False) -> int:
        """Get the text with for the correct editor mode."""
        if focusMode:
            return max(self.focusWidth, 200)
        else:
            return max(self.textWidth, 200)

    ##
    #  Setters
    ##

    def setLastAuthor(self, value: str) -> None:
        """Set tle last used author name."""
        self._lastAuthor = simplified(value)

    def setMainWinSize(self, geometry: QRect) -> None:
        """Set the size of the main window, but only if the change is
        larger than 5 pixels. The OS window manager will sometimes
        adjust it a bit, and we don't want the main window to shrink or
        grow each time the app is opened.
        """
        width = geometry.width()
        height = geometry.height()
        if abs(self.mainWinSize[0] - width) > 5:
            self.mainWinSize[0] = width
        if abs(self.mainWinSize[1] - height) > 5:
            self.mainWinSize[1] = height

    def setWelcomeWinSize(self, geometry: QRect) -> None:
        """Set the size of the Preferences dialog window."""
        self.welcomeWinSize = [geometry.width(), geometry.height()]

    def setPreferencesWinSize(self, geometry: QRect) -> None:
        """Set the size of the Preferences dialog window."""
        self.prefsWinSize = [geometry.width(), geometry.height()]

    def setFontWinSize(self, geometry: QRect) -> None:
        """Set the size of the Font dialog window."""
        self.fontWinSize = [geometry.width(), geometry.height()]

    def setLastPath(self, key: str, path: str | Path) -> None:
        """Set the last used path. Only the folder is saved, so if the
        path is not a folder, the parent of the path is used instead.
        """
        if isinstance(path, str | Path):
            path = checkPath(path, self._homePath)
            if not safeIsDir(path):
                path = path.parent
            if safeIsDir(path):
                self._recentPaths.setPath(key, path)

    def setBackupPath(self, path: Path | str) -> None:
        """Set the current backup path."""
        self._backupPath = checkPath(path, self._backPath)

    def setGuiFont(self, value: QFont | str | None) -> None:
        """Update the GUI's font style from settings."""
        if isinstance(value, QFont):
            self.guiFont = fontMatcher(value)
        elif value and isinstance(value, str):
            font = QFont()
            if self.checkMinQtVersion(0x060B00):  # Qt 6.11+
                font.fromString(value)
            else:  # pragma: no cover
                font.fromString(",".join(value.split(",")[:16]))
            self.guiFont = fontMatcher(font)
        else:
            font = QFont()
            if self.osWindows and "Arial" in QFontDatabase.families():
                # On Windows we default to Arial if possible
                font.setFamily("Arial")
                font.setPointSize(10)
            else:
                font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
            self.guiFont = fontMatcher(font)
            logger.debug("Main font set to: %s", describeFont(font))
        QApplication.setFont(self.guiFont)

    def setTextFont(self, value: QFont | str | None) -> None:
        """Set the text font if it exists. If it doesn't, or is None,
        set to default font.
        """
        if isinstance(value, QFont):
            self.textFont = fontMatcher(value)
        elif value and isinstance(value, str):
            font = QFont()
            if self.checkMinQtVersion(0x060B00):  # Qt 6.11+
                font.fromString(value)
            else:  # pragma: no cover
                font.fromString(",".join(value.split(",")[:16]))
            self.textFont = fontMatcher(font)
        else:
            fontFam = QFontDatabase.families()
            if self.osWindows and "Arial" in fontFam:
                font = QFont()
                font.setFamily("Arial")
                font.setPointSize(12)
            elif self.osDarwin and "Helvetica" in fontFam:
                font = QFont()
                font.setFamily("Helvetica")
                font.setPointSize(12)
            else:
                font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
            self.textFont = fontMatcher(font)
            logger.debug("Text font set to: %s", describeFont(self.textFont))

    def setPrimaryCount(self, useCharCount: bool) -> None:
        """Set the primary count unit. This also updates the unit label."""
        self.useCharCount = useCharCount
        self.countUnit = trStats("Characters" if useCharCount else "Words").lower()

    ##
    #  Methods
    ##

    def homePath(self) -> Path:
        """Return the user's home folder."""
        return self._homePath

    def dataPath(self, target: str | None = None) -> Path:
        """Return a path in the data folder."""
        if isinstance(target, str):
            return self._dataPath / target
        return self._dataPath

    def assetPath(self, target: str | None = None) -> Path:
        """Return a path in the assets folder."""
        if isinstance(target, str):
            return self._appPath / "assets" / target
        return self._appPath / "assets"

    def lastPath(self, key: str) -> Path:
        """Return the last path used by the user, if it exists."""
        if (path := self._recentPaths.getPath(key)) and safeIsDir(asPath := Path(path)):
            return asPath
        return self._homePath

    def backupPath(self) -> Path:
        """Return the backup path."""
        if isinstance(self._backupPath, Path) and safeIsDir(self._backupPath):
            return self._backupPath
        return self._backPath

    def errorText(self) -> str:
        """Compile and return error messages from the initialisation of
        the Config class, and clear the error buffer.
        """
        message = joinLines(self._errData, "<br>")
        self._hasError = False
        self._errData = []
        return message

    def checkMinQtVersion(self, version: int) -> bool:
        """Check if a minimum Qt version is satisfied."""
        return self.verPyQtValue >= version and self.verQtValue >= version

    def localDate(self, value: datetime) -> str:
        """Return a localised date format."""
        # Explicitly convert the date first, see bug #2325
        return self._dLocale.toString(QDate(value.year, value.month, value.day), self._dShortDate)

    def localDateTime(self, value: datetime) -> str:
        """Return a localised datetime format."""
        # Explicitly convert the datetime first, see bug #2325
        return self._dLocale.toString(
            QDateTime(value.year, value.month, value.day, value.hour, value.minute, value.second),
            self._dShortDateTime,
        )

    def listLanguages(self, lngSet: int) -> list[tuple[str, str]]:
        """List localisation files in the i18n folder. The default GUI
        language is British English (en_GB).
        """
        if lngSet == self.LANG_NW:
            fPre = "nw_"
            fExt = ".qm"
            langList = {"en_GB": languageName("en_GB")}
        elif lngSet == self.LANG_PROJ:
            fPre = "project_"
            fExt = ".json"
            langList = {"en_GB": languageName("en_GB")}
        else:
            return []

        try:
            for qmFile in self._nwLangPath.iterdir():
                qmName = qmFile.name
                if not (qmFile.is_file() and qmName.startswith(fPre) and qmName.endswith(fExt)):
                    continue

                qmLang = qmName[len(fPre) : -len(fExt)]
                qmName = languageName(qmLang)
                if qmLang and qmName and qmLang != "en_GB":
                    langList[qmLang] = qmName
        except Exception as exc:
            logger.error("Failed to load additional language files", exc_info=exc)

        return sorted(langList.items(), key=lambda x: x[0])

    def splashMessage(self, message: str) -> None:
        """Send a message to the splash screen."""
        if self._splash:
            self._splash.showStatus(message)

    ##
    #  Config Actions
    ##

    def initConfig(self, confPath: str | Path | None = None, dataPath: str | Path | None = None) -> None:
        """Initialise the config class. The manual setting of confPath
        and dataPath is mainly intended for the test suite.
        """
        logger.debug("Initialising Config ...")
        if isinstance(confPath, str | Path):
            logger.info("Setting alternative config path: %s", confPath)
            self._confPath = Path(confPath)
        if isinstance(dataPath, str | Path):
            logger.info("Setting alternative data path: %s", dataPath)
            self._dataPath = Path(dataPath)

        logger.debug("Config Path: %s", self._confPath)
        logger.debug("Data Path: %s", self._dataPath)
        logger.debug("App Root: %s", self._appRoot)
        logger.debug("App Path: %s", self._appPath)
        logger.debug("PDF Manual: %s", self.pdfDocs)

        # If the config and data folders don't exist, create them
        # This assumes that the os config and data folders exist
        # Also create the themes and icons folders if possible
        try:
            self._confPath.mkdir(exist_ok=True)
            self._dataPath.mkdir(exist_ok=True)
            if self._dataPath.is_dir():
                (self._dataPath / "cache").mkdir(exist_ok=True)
                (self._dataPath / "icons").mkdir(exist_ok=True)
                (self._dataPath / "themes").mkdir(exist_ok=True)
        except Exception:
            logException()

        self._recentPaths.loadCache()
        self._recentProjects.loadCache()
        self._checkOptionalPackages()

        logger.debug("Config instance initialised")

    def initLocalisation(self, nwApp: QApplication) -> None:
        """Initialise the localisation of the GUI."""
        self.splashMessage("Loading localisation ...")

        self._qLocale = QLocale(self.guiLocale)
        QLocale.setDefault(self._qLocale)
        self._qtTrans = {}

        hasLocale = safeExists(self._nwLangPath / f"nw_{self._qLocale.name()}.qm")
        self._dLocale = self._qLocale if hasLocale else QLocale.system()
        self._dShortDate = self._dLocale.dateFormat(QLocale.FormatType.ShortFormat)
        self._dShortDateTime = self._dLocale.dateTimeFormat(QLocale.FormatType.ShortFormat)

        langList = [
            (self._qtLangPath, "qtbase"),  # Qt
            (str(self._nwLangPath), "nw"),  # novelWriter
        ]
        for lngPath, lngBase in langList:
            for lngCode in self._qLocale.uiLanguages():
                qTrans = QTranslator()
                lngFile = "{0}_{1}".format(lngBase, lngCode.replace("-", "_"))
                if lngFile not in self._qtTrans and qTrans.load(lngFile, lngPath):
                    logger.debug("Loaded: %s.qm", lngFile)
                    nwApp.installTranslator(qTrans)
                    self._qtTrans[lngFile] = qTrans

        # Refresh translated values
        self.setPrimaryCount(self.useCharCount)

    def loadConfig(self, splash: NSplashScreen | None = None) -> bool:
        """Load preferences from file and replace default settings."""
        self._splash = splash
        self.splashMessage("Loading user configuration ...")

        logger.debug("Loading config file")
        convertOld = False

        if safeExists(path := self._confPath / nwFiles.CONF_FILE):
            confPath = path
            parser = NTomlParser()
        elif safeExists(path := self._confPath / nwFiles.CONF_FILE_OLD):
            confPath = path
            parser = NConfigParser()
            convertOld = True
        else:
            # Initial file, so we just create one from defaults
            self.setGuiFont(None)
            self.setTextFont(None)
            self.saveConfig()
            return True

        try:
            parser.read(confPath)
        except Exception as exc:
            logger.error("Could not load config file")
            logException()
            self._hasError = True
            self._errData.append("Could not load config file")
            self._errData.append(formatException(exc))
            return False

        # Main
        sec = "Main"
        self.setGuiFont(parser.getStr(sec, "font", ""))
        self.lightTheme = parser.getStr(sec, "lightTheme", self.lightTheme)
        self.darkTheme = parser.getStr(sec, "darkTheme", self.darkTheme)
        self.themeMode = parser.getEnum(sec, "themeMode", self.themeMode)
        self.iconTheme = parser.getStr(sec, "icons", self.iconTheme)
        self.iconColTree = parser.getStr(sec, "iconColTree", self.iconColTree)
        self.iconColDocs = parser.getBool(sec, "iconColDocs", self.iconColDocs)
        self.guiLocale = parser.getStr(sec, "localisation", self.guiLocale)
        self.hideVScroll = parser.getBool(sec, "hideVScroll", self.hideVScroll)
        self.hideHScroll = parser.getBool(sec, "hideHScroll", self.hideHScroll)
        self.lastNotes = parser.getStr(sec, "lastNotes", self.lastNotes)
        self.nativeFont = parser.getBool(sec, "nativeFont", self.nativeFont)
        self.useCharCount = parser.getBool(sec, "useCharCount", self.useCharCount)
        self.vimMode = parser.getBool(sec, "vimMode", self.vimMode)

        # Sizes
        sec = "Sizes"
        self.mainWinSize = parser.getIntList(sec, "mainWindow", self.mainWinSize)
        self.welcomeWinSize = parser.getIntList(sec, "welcome", self.welcomeWinSize)
        self.prefsWinSize = parser.getIntList(sec, "preferences", self.prefsWinSize)
        self.fontWinSize = parser.getIntList(sec, "fontSelect", self.fontWinSize)
        self.mainPanePos = parser.getIntList(sec, "mainPane", self.mainPanePos)
        self.viewPanePos = parser.getIntList(sec, "viewPane", self.viewPanePos)
        self.searchPanePos = parser.getIntList(sec, "searchPane", self.searchPanePos)
        self.moveMainWin = parser.getBool(sec, "moveMainWin", self.moveMainWin)

        # Project
        sec = "Project"
        self.autoSaveProj = parser.getInt(sec, "autoSaveProject", self.autoSaveProj)
        self.autoSaveDoc = parser.getInt(sec, "autoSaveDoc", self.autoSaveDoc)
        self.emphLabels = parser.getBool(sec, "emphLabels", self.emphLabels)
        self._backupPath = parser.getPath(sec, "backupPath", self._backupPath)
        self.backupOnClose = parser.getBool(sec, "backupOnClose", self.backupOnClose)
        self.backupInterval = parser.getStr(sec, "backupInterval", self.backupInterval)
        self.askBeforeBackup = parser.getBool(sec, "askBeforeBackup", self.askBeforeBackup)
        self.askBeforeExit = parser.getBool(sec, "askBeforeExit", self.askBeforeExit)
        self._lastAuthor = simplified(parser.getStr(sec, "lastAuthor", self._lastAuthor))

        # Editor
        sec = "Editor"
        self.setTextFont(parser.getStr(sec, "textFont", ""))
        self.textWidth = parser.getInt(sec, "width", self.textWidth)
        self.textMargin = parser.getInt(sec, "margin", self.textMargin)
        self.tabWidth = parser.getInt(sec, "tabWidth", self.tabWidth)
        self.lineHeight = parser.getFloat(sec, "lineHeight", self.lineHeight)
        self.cursorWidth = parser.getInt(sec, "cursorWidth", self.cursorWidth)
        self.lineHighlight = parser.getBool(sec, "lineHighlight", self.lineHighlight)
        self.focusWidth = parser.getInt(sec, "focusWidth", self.focusWidth)
        self.hideFocusFooter = parser.getBool(sec, "hideFocusFooter", self.hideFocusFooter)
        self.doJustify = parser.getBool(sec, "justify", self.doJustify)
        self.autoSelect = parser.getBool(sec, "autoSelect", self.autoSelect)
        self.doReplace = parser.getBool(sec, "autoReplace", self.doReplace)
        self.doReplaceSQuote = parser.getBool(sec, "repSQuotes", self.doReplaceSQuote)
        self.doReplaceDQuote = parser.getBool(sec, "repDQuotes", self.doReplaceDQuote)
        self.doReplaceDash = parser.getBool(sec, "repDash", self.doReplaceDash)
        self.doReplaceDots = parser.getBool(sec, "repDots", self.doReplaceDots)
        self.autoScroll = parser.getBool(sec, "autoScroll", self.autoScroll)
        self.autoScrollPos = parser.getInt(sec, "autoScrollPos", self.autoScrollPos)
        self.scrollPastEnd = parser.getBool(sec, "scrollPastEnd", self.scrollPastEnd)
        self.fmtSQuoteOpen = compact(parser.getStr(sec, "fmtSQuoteOpen", self.fmtSQuoteOpen))
        self.fmtSQuoteClose = compact(parser.getStr(sec, "fmtSQuoteClose", self.fmtSQuoteClose))
        self.fmtDQuoteOpen = compact(parser.getStr(sec, "fmtDQuoteOpen", self.fmtDQuoteOpen))
        self.fmtDQuoteClose = compact(parser.getStr(sec, "fmtDQuoteClose", self.fmtDQuoteClose))
        self.fmtPadBefore = uniqueCompact(parser.getStr(sec, "fmtPadBefore", self.fmtPadBefore))
        self.fmtPadAfter = uniqueCompact(parser.getStr(sec, "fmtPadAfter", self.fmtPadAfter))
        self.fmtPadThin = parser.getBool(sec, "fmtPadThin", self.fmtPadThin)
        self.spellLanguage = parser.getStr(sec, "spellCheck", self.spellLanguage)
        self.showTabsNSpaces = parser.getBool(sec, "showTabsNSpaces", self.showTabsNSpaces)
        self.showLineEndings = parser.getBool(sec, "showLineEndings", self.showLineEndings)
        self.showMultiSpaces = parser.getBool(sec, "showMultiSpaces", self.showMultiSpaces)
        self.scaleHeadings = parser.getBool(sec, "scaleHeadings", self.scaleHeadings)
        self.singleStarBold = parser.getBool(sec, "singleStarBold", self.singleStarBold)
        self.incNotesWCount = parser.getBool(sec, "incNotesWCount", self.incNotesWCount)
        self.showFullPath = parser.getBool(sec, "showFullPath", self.showFullPath)
        self.dialogStyle = parser.getInt(sec, "dialogStyle", self.dialogStyle)
        self.allowOpenDial = parser.getBool(sec, "allowOpenDial", self.allowOpenDial)
        dialogLine = parser.getStr(sec, "dialogLine", self.dialogLine)
        narratorBreak = parser.getStr(sec, "narratorBreak", self.narratorBreak)
        narratorDialog = parser.getStr(sec, "narratorDialog", self.narratorDialog)
        self.altDialogOpen = compact(parser.getStr(sec, "altDialogOpen", self.altDialogOpen))
        self.altDialogClose = compact(parser.getStr(sec, "altDialogClose", self.altDialogClose))
        self.highlightEmph = parser.getBool(sec, "highlightEmph", self.highlightEmph)
        self.dottedModCodes = parser.getBool(sec, "dottedModCodes", self.dottedModCodes)
        self.stopWhenIdle = parser.getBool(sec, "stopWhenIdle", self.stopWhenIdle)
        self.userIdleTime = parser.getInt(sec, "userIdleTime", self.userIdleTime)

        # State
        sec = "State"
        self.showDetailsPanel = parser.getBool(sec, "showDetailsPanel", self.showDetailsPanel)
        self.showViewerPanel = parser.getBool(sec, "showViewerPanel", self.showViewerPanel)
        self.showEditToolBar = parser.getBool(sec, "showEditToolBar", self.showEditToolBar)
        self.showSessionTime = parser.getBool(sec, "showSessionTime", self.showSessionTime)
        self.viewComments = parser.getBool(sec, "viewComments", self.viewComments)
        self.viewSynopsis = parser.getBool(sec, "viewSynopsis", self.viewSynopsis)
        self.viewNotes = parser.getBool(sec, "viewNotes", self.viewNotes)
        self.searchAuto = parser.getBool(sec, "searchAuto", self.searchAuto)
        self.searchCase = parser.getBool(sec, "searchCase", self.searchCase)
        self.searchWord = parser.getBool(sec, "searchWord", self.searchWord)
        self.searchRegEx = parser.getBool(sec, "searchRegEx", self.searchRegEx)
        self.searchLoop = parser.getBool(sec, "searchLoop", self.searchLoop)
        self.searchNextFile = parser.getBool(sec, "searchNextFile", self.searchNextFile)
        self.searchMatchCap = parser.getBool(sec, "searchMatchCap", self.searchMatchCap)
        self.searchProjAuto = parser.getBool(sec, "searchProjAuto", self.searchProjAuto)
        self.searchProjCase = parser.getBool(sec, "searchProjCase", self.searchProjCase)
        self.searchProjWord = parser.getBool(sec, "searchProjWord", self.searchProjWord)
        self.searchProjRegEx = parser.getBool(sec, "searchProjRegEx", self.searchProjRegEx)

        # Check Values
        # ============

        self._prepareFont(self.guiFont, "main")
        self._prepareFont(self.textFont, "document")

        # If we're using straight quotes, disable auto-replace
        if self.fmtSQuoteOpen == self.fmtSQuoteClose == "'" and self.doReplaceSQuote:
            logger.info("Using straight single quotes, so disabling auto-replace")
            self.doReplaceSQuote = False

        if self.fmtDQuoteOpen == self.fmtDQuoteClose == '"' and self.doReplaceDQuote:
            logger.info("Using straight double quotes, so disabling auto-replace")
            self.doReplaceDQuote = False

        self.dialogLine = processDialogSymbols(dialogLine)
        self.narratorBreak = narratorBreak if narratorBreak in nwQuotes.DASHES else ""
        self.narratorDialog = narratorDialog if narratorDialog in nwQuotes.DASHES else ""

        if convertOld:
            logger.info("Old config file detected, converting to new format")
            self.saveConfig()

        return True

    def saveConfig(self) -> bool:
        """Save the current preferences to file."""
        logger.debug("Saving config file")

        config: T_TomlConfig = {}

        config["Meta"] = {
            "timeStamp": formatTimeStamp(time()),
        }

        config["Main"] = {
            "font": self.guiFont,
            "lightTheme": self.lightTheme,
            "darkTheme": self.darkTheme,
            "themeMode": self.themeMode,
            "icons": self.iconTheme,
            "iconColTree": self.iconColTree,
            "iconColDocs": self.iconColDocs,
            "localisation": self.guiLocale,
            "hideVScroll": self.hideVScroll,
            "hideHScroll": self.hideHScroll,
            "lastNotes": self.lastNotes,
            "nativeFont": self.nativeFont,
            "useCharCount": self.useCharCount,
            "vimMode": self.vimMode,
        }

        config["Sizes"] = {
            "mainWindow": self.mainWinSize,
            "welcome": self.welcomeWinSize,
            "preferences": self.prefsWinSize,
            "fontSelect": self.fontWinSize,
            "mainPane": self.mainPanePos,
            "viewPane": self.viewPanePos,
            "searchPane": self.searchPanePos,
            "moveMainWin": self.moveMainWin,
        }

        config["Project"] = {
            "autoSaveProject": self.autoSaveProj,
            "autoSaveDoc": self.autoSaveDoc,
            "emphLabels": self.emphLabels,
            "backupPath": self._backupPath,
            "backupOnClose": self.backupOnClose,
            "backupInterval": self.backupInterval,
            "askBeforeBackup": self.askBeforeBackup,
            "askBeforeExit": self.askBeforeExit,
            "lastAuthor": self._lastAuthor,
        }

        config["Editor"] = {
            "textFont": self.textFont,
            "width": self.textWidth,
            "margin": self.textMargin,
            "tabWidth": self.tabWidth,
            "lineHeight": self.lineHeight,
            "cursorWidth": self.cursorWidth,
            "lineHighlight": self.lineHighlight,
            "focusWidth": self.focusWidth,
            "hideFocusFooter": self.hideFocusFooter,
            "justify": self.doJustify,
            "autoSelect": self.autoSelect,
            "autoReplace": self.doReplace,
            "repSQuotes": self.doReplaceSQuote,
            "repDQuotes": self.doReplaceDQuote,
            "repDash": self.doReplaceDash,
            "repDots": self.doReplaceDots,
            "autoScroll": self.autoScroll,
            "autoScrollPos": self.autoScrollPos,
            "scrollPastEnd": self.scrollPastEnd,
            "fmtSQuoteOpen": self.fmtSQuoteOpen,
            "fmtSQuoteClose": self.fmtSQuoteClose,
            "fmtDQuoteOpen": self.fmtDQuoteOpen,
            "fmtDQuoteClose": self.fmtDQuoteClose,
            "fmtPadBefore": self.fmtPadBefore,
            "fmtPadAfter": self.fmtPadAfter,
            "fmtPadThin": self.fmtPadThin,
            "spellCheck": self.spellLanguage,
            "showTabsNSpaces": self.showTabsNSpaces,
            "showLineEndings": self.showLineEndings,
            "showMultiSpaces": self.showMultiSpaces,
            "scaleHeadings": self.scaleHeadings,
            "singleStarBold": self.singleStarBold,
            "incNotesWCount": self.incNotesWCount,
            "showFullPath": self.showFullPath,
            "dialogStyle": self.dialogStyle,
            "allowOpenDial": self.allowOpenDial,
            "dialogLine": self.dialogLine,
            "narratorBreak": self.narratorBreak,
            "narratorDialog": self.narratorDialog,
            "altDialogOpen": self.altDialogOpen,
            "altDialogClose": self.altDialogClose,
            "highlightEmph": self.highlightEmph,
            "dottedModCodes": self.dottedModCodes,
            "stopWhenIdle": self.stopWhenIdle,
            "userIdleTime": self.userIdleTime,
        }

        config["State"] = {
            "showDetailsPanel": self.showDetailsPanel,
            "showViewerPanel": self.showViewerPanel,
            "showEditToolBar": self.showEditToolBar,
            "showSessionTime": self.showSessionTime,
            "viewComments": self.viewComments,
            "viewSynopsis": self.viewSynopsis,
            "viewNotes": self.viewNotes,
            "searchAuto": self.searchAuto,
            "searchCase": self.searchCase,
            "searchWord": self.searchWord,
            "searchRegEx": self.searchRegEx,
            "searchLoop": self.searchLoop,
            "searchNextFile": self.searchNextFile,
            "searchMatchCap": self.searchMatchCap,
            "searchProjAuto": self.searchProjAuto,
            "searchProjCase": self.searchProjCase,
            "searchProjWord": self.searchProjWord,
            "searchProjRegEx": self.searchProjRegEx,
        }

        # Write config file
        cnfPath = self._confPath / nwFiles.CONF_FILE
        try:
            parser = NTomlParser()
            parser.write(cnfPath, config)
        except Exception as exc:
            logger.error("Could not save config file")
            logException()
            self._hasError = True
            self._errData.append("Could not save config file")
            self._errData.append(formatException(exc))
            return False

        return True

    def finishStartup(self) -> None:
        """Call after startup is complete."""
        self._splash = None

    ##
    #  Internal Functions
    ##

    def _packList(self, data: list) -> str:
        """Pack a list of items into a comma-separated string for saving
        to the config file.
        """
        return ", ".join(str(inVal) for inVal in data)

    def _checkOptionalPackages(self) -> None:
        """Check optional packages used by some features."""
        try:
            import enchant  # noqa: F401
        except ImportError:
            self.hasEnchant = False
            logger.debug("Checking package 'pyenchant': Missing")
        else:
            self.hasEnchant = True
            logger.debug("Checking package 'pyenchant': OK")

    def _prepareFont(self, font: QFont, kind: str) -> None:
        """Check Unicode availability in font. This also initialises any
        alternative character used for missing glyphs. See #2315.
        """
        self.splashMessage(f"Initialising {kind} font: {font.family()}")
        metrics = QFontMetrics(font)
        for char in nwUnicode.UI_SYMBOLS:
            if not metrics.inFont(char):  # type: ignore
                logger.warning("No glyph U+%04x in font", ord(char))  # pragma: no cover


class RecentProjects:
    """A record of recently opened projects."""

    def __init__(self, config: Config) -> None:
        self._conf = config
        self._data: dict[str, dict[str, str | int]] = {}
        self._map: dict[str, str] = {}

    def loadCache(self) -> bool:
        """Load the cache file for recent projects."""
        self._data = {}
        self._map = {}
        try:
            cacheFile = self._conf.dataPath(nwFiles.RECENT_FILE)
            if cacheFile.is_file():
                with open(cacheFile, mode="r", encoding="utf-8") as inFile:
                    data = json.load(inFile)
                for path, entry in data.items():
                    puuid = str(entry.get("uuid", ""))
                    title = str(entry.get("title", ""))
                    words = checkInt(entry.get("words", 0), 0)
                    chars = checkInt(entry.get("chars", 0), 0)
                    saved = checkInt(entry.get("time", 0), 0)
                    if path and title:
                        self._setEntry(puuid, path, title, words, chars, saved)
        except Exception:
            logger.error("Could not load recent project cache")
            logException()
            return False
        return True

    def saveCache(self) -> bool:
        """Save the cache dictionary of recent projects."""
        cacheFile = self._conf.dataPath(nwFiles.RECENT_FILE)
        cacheTemp = cacheFile.with_suffix(".tmp")
        try:
            with open(cacheTemp, mode="w+", encoding="utf-8") as outFile:
                json.dump(self._data, outFile, indent=2)
            cacheTemp.replace(cacheFile)
        except Exception:
            logger.error("Could not save recent project cache")
            logException()
            return False
        return True

    def listEntries(self) -> list[tuple[str, str, int, int]]:
        """List all items in the cache."""
        return [
            (str(k), str(e["title"]), checkInt(e["words"], 0), checkInt(e["time"], 0)) for k, e in self._data.items()
        ]

    def update(self, path: str | Path, data: ProjectData, saved: float | int) -> None:
        """Add or update recent cache information on a given project."""
        try:
            if (remove := self._map.get(data.uuid)) and (remove != str(path)):
                self.remove(remove)
            self._setEntry(
                data.uuid,
                str(path),
                data.name,
                sum(data.currCounts[:2]),
                sum(data.currCounts[2:]),
                int(saved),
            )
            self.saveCache()
        except Exception:
            pass

    def remove(self, path: str | Path) -> None:
        """Try to remove a path from the recent projects cache."""
        if self._data.pop(str(path), None) is not None:
            logger.debug("Removed recent: %s", path)
            self.saveCache()

    def _setEntry(self, puuid: str, path: str, title: str, words: int, chars: int, saved: int) -> None:
        """Set an entry in the recent projects record."""
        self._data[path] = {
            "uuid": puuid,
            "title": title,
            "words": words,
            "chars": chars,
            "time": saved,
        }
        if puuid:
            self._map[puuid] = path


class RecentPaths:
    """A record of recently used file paths."""

    KEYS: Final[list[str]] = ["default", "project", "import", "story", "stats"]

    def __init__(self, config: Config) -> None:
        self._conf = config
        self._data = {}

    def setPath(self, key: str, path: Path | str) -> None:
        """Set a path for a given key, and save the cache."""
        if key in self.KEYS:
            self._data[key] = str(path)
        self.saveCache()

    def getPath(self, key: str) -> str | None:
        """Get a path for a given key, or return None."""
        return self._data.get(key)

    def loadCache(self) -> bool:
        """Load the cache file for recent paths."""
        self._data = {}
        try:
            cacheFile = self._conf.dataPath(nwFiles.RECENT_PATH)
            if cacheFile.is_file():
                with open(cacheFile, mode="r", encoding="utf-8") as inFile:
                    data = json.load(inFile)
                if isinstance(data, dict):
                    for key, path in data.items():
                        if key in self.KEYS and isinstance(path, str):
                            self._data[key] = path
        except Exception:
            logger.error("Could not load recent paths cache")
            logException()
            return False
        return True

    def saveCache(self) -> bool:
        """Save the cache dictionary of recent paths."""
        cacheFile = self._conf.dataPath(nwFiles.RECENT_PATH)
        cacheTemp = cacheFile.with_suffix(".tmp")
        try:
            with open(cacheTemp, mode="w+", encoding="utf-8") as outFile:
                json.dump(self._data, outFile, indent=2)
            cacheTemp.replace(cacheFile)
        except Exception:
            logger.error("Could not save recent paths cache")
            logException()
            return False
        return True
