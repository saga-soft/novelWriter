"""
novelWriter - Config Tests
==========================

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

import datetime
import json
import sys

from pathlib import Path
from shutil import copyfile

import pytest

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QFontDatabase

from novelwriter import CONFIG
from novelwriter.config import Config, RecentPaths, RecentProjects
from novelwriter.constants import nwFiles
from novelwriter.core.project import NWProject
from novelwriter.enum import nwTheme

from tests.helpers import cmpFiles, writeFile
from tests.mocked import MockApp, causeOSError


@pytest.mark.base
def testConfig_Constructor(monkeypatch):
    """Test config constructor."""
    # Linux
    with monkeypatch.context() as mp:
        mp.setattr("sys.platform", "linux")
        conf = Config()
        assert conf.osLinux is True
        assert conf.osDarwin is False
        assert conf.osWindows is False
        assert conf.osUnknown is False

    # MacOS
    with monkeypatch.context() as mp:
        mp.setattr("sys.platform", "darwin")
        conf = Config()
        assert conf.osLinux is False
        assert conf.osDarwin is True
        assert conf.osWindows is False
        assert conf.osUnknown is False

    # Windows
    with monkeypatch.context() as mp:
        mp.setattr("sys.platform", "win32")
        conf = Config()
        assert conf.osLinux is False
        assert conf.osDarwin is False
        assert conf.osWindows is True
        assert conf.osUnknown is False

    # Cygwin
    with monkeypatch.context() as mp:
        mp.setattr("sys.platform", "cygwin")
        conf = Config()
        assert conf.osLinux is False
        assert conf.osDarwin is False
        assert conf.osWindows is True
        assert conf.osUnknown is False

    # Other
    with monkeypatch.context() as mp:
        mp.setattr("sys.platform", "some_other_os")
        conf = Config()
        assert conf.osLinux is False
        assert conf.osDarwin is False
        assert conf.osWindows is False
        assert conf.osUnknown is True


@pytest.mark.base
def testConfig_InitLoadSave(monkeypatch, fncPath, tstPaths):
    """Test config initialisation."""
    conf = Config()

    confFile = fncPath / nwFiles.CONF_FILE
    testFile = tstPaths.outDir / "config_novelwriter.toml"
    compFile = tstPaths.refDir / "config_novelwriter.toml"

    # Make sure we don't have any old conf file
    if confFile.is_file():
        confFile.unlink()

    # Running init + load against a new path should write a new config file
    conf.initConfig(confPath=fncPath, dataPath=fncPath)
    assert conf._confPath == fncPath
    assert conf._dataPath == fncPath
    conf.loadConfig()
    assert confFile.exists()

    # Check that we have a default file
    copyfile(confFile, testFile)
    ignore = (
        "timeStamp",
        "font",
        "localisation",
        "lastNotes",
        "textFont",
        "backupPath",
    )
    assert cmpFiles(testFile, compFile, ignStart=ignore)
    conf.errorText()  # This clears the error cache

    # Block saving the file
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert conf.saveConfig() is False
        assert conf.hasError is True
        assert conf.errorText().startswith("Could not save config file")

    # Block loading the file
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert conf.loadConfig() is False
        assert conf.hasError is True
        assert conf.errorText().startswith("Could not load config file")

    # Change a few settings, save, reset, and reload
    conf.lightTheme = "foo"
    conf.darkTheme = "bar"
    assert conf.saveConfig() is True

    newConf = Config()
    newConf.initConfig(confPath=fncPath, dataPath=fncPath)
    newConf.loadConfig()
    assert newConf.lightTheme == "foo"
    assert newConf.darkTheme == "bar"

    # If the data path doesn't materialise as a folder, sub-folders are skipped
    with monkeypatch.context() as mp:
        freshDataPath = fncPath / "freshdata"
        origIsDir = Path.is_dir
        mp.setattr(Path, "is_dir", lambda self: False if self == freshDataPath else origIsDir(self))
        conf.initConfig(confPath=fncPath, dataPath=freshDataPath)
        assert not (freshDataPath / "cache").exists()

    # Test Correcting Quote Settings
    conf.fmtDQuoteOpen = '"'
    conf.fmtDQuoteClose = '"'
    conf.fmtSQuoteOpen = "'"
    conf.fmtSQuoteClose = "'"
    conf.doReplaceDQuote = True
    conf.doReplaceSQuote = True
    assert conf.saveConfig() is True

    assert newConf.loadConfig() is True
    assert newConf.doReplaceDQuote is False
    assert newConf.doReplaceSQuote is False


@pytest.mark.base
def testConfig_Localisation(fncPath, tstPaths):
    """Test localisation."""
    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)

    # Localisation
    # ============

    i18nDir = fncPath / "i18n"
    i18nDir.mkdir()
    conf._nwLangPath = i18nDir

    copyfile(tstPaths.filesDir / "nw_en_GB.qm", i18nDir / "nw_en_GB.qm")
    writeFile(i18nDir / "nw_en_GB.ts", "")
    writeFile(i18nDir / "nw_abcd.qm", "")

    tstApp = MockApp()
    conf.initLocalisation(tstApp)  # type: ignore

    # Check Lists
    languages = conf.listLanguages(conf.LANG_NW)
    assert languages == [("en_GB", "British English")]
    languages = conf.listLanguages(conf.LANG_PROJ)
    assert languages == [("en_GB", "British English")]
    languages = conf.listLanguages(None)  # type: ignore
    assert languages == []

    # Add Language
    copyfile(tstPaths.filesDir / "nw_en_GB.qm", i18nDir / "nw_fr.qm")
    writeFile(i18nDir / "nw_fr.ts", "")

    languages = conf.listLanguages(conf.LANG_NW)
    assert languages == [("en_GB", "British English"), ("fr", "Français")]

    # Date Formats
    # Checks for bug #2325
    ts = datetime.datetime.fromtimestamp(1746370775)
    CONFIG._dShortDate = "dd/MM/yyyy"
    CONFIG._dShortDateTime = "dd/MM/yyyy HH:mm"
    assert CONFIG.localDate(ts) == ts.strftime("%d/%m/%Y")
    assert CONFIG.localDateTime(ts) == ts.strftime("%d/%m/%Y %H:%M")


@pytest.mark.base
def testConfig_Methods(fncPath):
    """Check class methods."""
    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)

    # Home Path
    assert conf.homePath() == Path.home().absolute()

    # Data Path
    assert conf.dataPath() == fncPath
    assert conf.dataPath("stuff") == fncPath / "stuff"

    # Assets Path
    appPath = conf._appPath
    assert conf.assetPath() == appPath / "assets"
    assert conf.assetPath("stuff") == appPath / "assets" / "stuff"

    # Last Path
    assert conf.lastPath("project") == Path.home().absolute()

    tmpStuff = fncPath / "stuff"
    tmpStuff.mkdir()
    conf.setLastPath("project", tmpStuff)
    assert conf.lastPath("project") == tmpStuff

    fileStuff = tmpStuff / "more_stuff.txt"
    fileStuff.write_text("Stuff")
    conf.setLastPath("project", fileStuff)
    assert conf.lastPath("project") == tmpStuff

    fileStuff.unlink()
    tmpStuff.rmdir()
    assert conf.lastPath("project") == Path.home().absolute()

    # Invalid type does nothing
    conf.setLastPath("project", None)  # type: ignore
    assert conf.lastPath("project") == Path.home().absolute()

    # A path where neither it nor its parent exist does nothing
    conf.setLastPath("project", fncPath / "missing" / "deeper" / "file.txt")
    assert conf.lastPath("project") == Path.home().absolute()

    # Backup Path
    assert conf.backupPath() == conf._backPath
    conf.setBackupPath(fncPath)
    assert conf.backupPath() == fncPath

    # Recent Projects
    assert isinstance(conf.recentProjects, RecentProjects)

    # Last Author
    assert CONFIG.lastAuthor == ""
    CONFIG.setLastAuthor(" Jane    Doe  ")
    assert CONFIG.lastAuthor == "Jane Doe"


@pytest.mark.base
def testConfig_Fonts(monkeypatch, fncPath):
    """Check the OS-specific default font selection."""
    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)

    with monkeypatch.context() as mp:
        mp.setattr(conf, "osWindows", True)
        mp.setattr(QFontDatabase, "families", lambda *a: ["Arial"])
        conf.setGuiFont(None)
        assert conf.guiFont.family() == "Arial"

        conf.setTextFont(None)
        assert conf.textFont.family() == "Arial"

    with monkeypatch.context() as mp:
        mp.setattr(conf, "osDarwin", True)
        mp.setattr(QFontDatabase, "families", lambda *a: ["Helvetica"])
        conf.setTextFont(None)
        assert conf.textFont.family() == "Helvetica"


@pytest.mark.base
def testConfig_SettersGetters(fncPath):
    """Set various sizes and positions."""
    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)

    # Setter + Getter Combos
    # ======================

    # Window Size
    conf.setMainWinSize(QRect(0, 0, 1205, 655))
    assert conf.mainWinSize == [1200, 650]

    conf.setMainWinSize(QRect(0, 0, 70, 70))
    assert conf.mainWinSize == [70, 70]

    conf.setMainWinSize(QRect(0, 0, 1200, 650))

    # Welcome Window Size
    conf.setWelcomeWinSize(QRect(0, 0, 70, 70))
    assert conf.welcomeWinSize == [70, 70]

    conf.setWelcomeWinSize(QRect(0, 0, 800, 500))

    # Preferences Size
    conf.setPreferencesWinSize(QRect(0, 0, 70, 70))
    assert conf.prefsWinSize == [70, 70]

    conf.setPreferencesWinSize(QRect(0, 0, 700, 615))

    # Font Dialog Size
    conf.setFontWinSize(QRect(0, 0, 70, 70))
    assert conf.fontWinSize == [70, 70]

    conf.setFontWinSize(QRect(0, 0, 700, 550))

    # Getters Only
    # ============

    assert conf.getTextWidth(False) == 700
    assert conf.getTextWidth(True) == 800


@pytest.mark.base
def testConfig_Internal(monkeypatch, fncPath):
    """Check internal functions."""
    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)

    # Function _packList
    assert conf._packList(["A", 1, 2.0, None, False]) == "A, 1, 2.0, None, False"

    # Function _checkOptionalPackages
    # (Assumes enchant package exists and is importable)
    conf._checkOptionalPackages()
    assert conf.hasEnchant is True

    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "enchant", None)
        conf._checkOptionalPackages()
        assert conf.hasEnchant is False


@pytest.mark.base
def testConfig_RecentCache(monkeypatch, tstPaths, nwGUI):
    """Test recent cache file."""
    cacheFile = tstPaths.cnfDir / nwFiles.RECENT_FILE
    recent = RecentProjects(CONFIG)

    # Load when there is no file should pass, but load nothing
    assert not cacheFile.exists()
    assert recent.loadCache() is True
    assert recent.listEntries() == []

    # Add a couple of values
    pathOne = tstPaths.cnfDir / "projPathOne" / nwFiles.PROJ_FILE
    pathTwo = tstPaths.cnfDir / "projPathTwo" / nwFiles.PROJ_FILE

    prjOne = NWProject()
    prjTwo = NWProject()

    prjOne.data.setUuid(None)
    prjTwo.data.setUuid(None)
    prjOne.data.setName("Proj One")
    prjTwo.data.setName("Proj Two")
    prjOne.data.setCurrCounts(100, 0)
    prjTwo.data.setCurrCounts(200, 0)

    recent.update(pathOne, prjOne.data, 1600002000)
    recent.update(pathTwo, prjTwo.data, 1600005600)
    assert recent.listEntries() == [
        (str(pathOne), "Proj One", 100, 1600002000),
        (str(pathTwo), "Proj Two", 200, 1600005600),
    ]
    assert cacheFile.exists()
    cacheFile.unlink()
    assert not cacheFile.exists()

    # Fail to Save
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert recent.saveCache() is False
        assert not cacheFile.exists()

    # Save Proper
    assert recent.saveCache() is True
    assert cacheFile.exists()

    # Fail to Load
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert recent.loadCache() is False
        assert recent.listEntries() == []

    # Load Proper
    assert recent.loadCache() is True
    assert recent.listEntries() == [
        (str(pathOne), "Proj One", 100, 1600002000),
        (str(pathTwo), "Proj Two", 200, 1600005600),
    ]

    # Pass Invalid
    recent.update(None, None, 0)  # type: ignore
    recent.update(None, None, 0)  # type: ignore
    assert recent.listEntries() == [
        (str(pathOne), "Proj One", 100, 1600002000),
        (str(pathTwo), "Proj Two", 200, 1600005600),
    ]

    # Remove Non-Existent Entry
    recent.remove("stuff")
    assert recent.listEntries() == [
        (str(pathOne), "Proj One", 100, 1600002000),
        (str(pathTwo), "Proj Two", 200, 1600005600),
    ]

    # Remove Second Entry
    recent.remove(pathTwo)
    assert recent.listEntries() == [
        (str(pathOne), "Proj One", 100, 1600002000),
    ]

    # Entries missing a path or a title are skipped
    cacheFile.write_text(
        json.dumps({
            "": {"uuid": "abc", "title": "No Path", "words": 1, "chars": 1, "time": 1},
            str(pathTwo): {"uuid": "abc", "title": "", "words": 1, "chars": 1, "time": 1},
        }),
        encoding="utf-8",
    )
    assert recent.loadCache() is True
    assert recent.listEntries() == []

    # Entries without a UUID are not mapped
    recent._setEntry("", str(pathOne), "No UUID", 10, 0, 0)
    assert recent._map.get("") is None


@pytest.mark.base
def testConfig_RecentPaths(monkeypatch, tstPaths):
    """Test recent paths file."""
    cacheFile = tstPaths.cnfDir / nwFiles.RECENT_PATH
    recent = RecentPaths(CONFIG)

    # Load when there is no file should pass, but load nothing
    assert not cacheFile.exists()
    assert recent.loadCache() is True
    assert recent._data == {}

    # Set valid paths
    recent.setPath("default", tstPaths.cnfDir / "default")
    recent.setPath("project", tstPaths.cnfDir / "project")
    recent.setPath("import", tstPaths.cnfDir / "import")
    recent.setPath("story", tstPaths.cnfDir / "story")
    recent.setPath("stats", tstPaths.cnfDir / "stats")

    # Set invalid path
    recent.setPath("foobar", tstPaths.cnfDir / "foobar")

    # Check valid paths
    assert recent.getPath("default") == str(tstPaths.cnfDir / "default")
    assert recent.getPath("project") == str(tstPaths.cnfDir / "project")
    assert recent.getPath("import") == str(tstPaths.cnfDir / "import")
    assert recent.getPath("story") == str(tstPaths.cnfDir / "story")
    assert recent.getPath("stats") == str(tstPaths.cnfDir / "stats")

    # Check invalid path
    assert recent.getPath("foobar") is None

    # Check file
    expected = {
        "default": str(tstPaths.cnfDir / "default"),
        "project": str(tstPaths.cnfDir / "project"),
        "import": str(tstPaths.cnfDir / "import"),
        "story": str(tstPaths.cnfDir / "story"),
        "stats": str(tstPaths.cnfDir / "stats"),
    }

    assert cacheFile.exists()
    assert json.loads(cacheFile.read_text()) == expected

    # Clear and reload
    recent._data = {}
    recent.loadCache()
    assert recent._data == expected

    # A non-dict cache file is ignored
    cacheFile.write_text(json.dumps(["not", "a", "dict"]), encoding="utf-8")
    recent._data = {}
    assert recent.loadCache() is True
    assert recent._data == {}

    # Invalid keys and non-string values are skipped
    cacheFile.write_text(
        json.dumps({
            "default": str(tstPaths.cnfDir / "default"),
            "foobar": str(tstPaths.cnfDir / "foobar"),
            "project": 1234,
        }),
        encoding="utf-8",
    )
    recent._data = {}
    assert recent.loadCache() is True
    assert recent._data == {"default": str(tstPaths.cnfDir / "default")}

    # Check error handling
    with monkeypatch.context() as mp:
        mp.setattr("builtins.open", causeOSError)
        assert recent.saveCache() is False
        assert recent.loadCache() is False


@pytest.mark.base
def testConfig_IOError(monkeypatch):
    """Test handling of I/O errors when using pathlib."""
    with monkeypatch.context() as mp:
        mp.setattr(Path, "iterdir", causeOSError)
        config = Config()  # Loading manuals will fail if not handled
        assert config.listLanguages(config.LANG_NW) == [("en_GB", "British English")]

    # No assets folder found
    with monkeypatch.context() as mp:
        origIsDir = Path.is_dir
        mp.setattr(Path, "is_dir", lambda self: False if self.name == "assets" else origIsDir(self))
        config = Config()
        assert config._manuals == {}

    with monkeypatch.context() as mp:
        config = Config()
        mp.setattr(Path, "is_dir", causeOSError)
        config.initConfig()


@pytest.mark.base
def testConfig_ConvertOldConfig(fncPath, tstPaths):
    """Test that an old ini-format config file is converted to the new
    TOML format when loaded.
    """
    oldFile = fncPath / nwFiles.CONF_FILE_OLD
    newFile = fncPath / nwFiles.CONF_FILE
    copyfile(tstPaths.filesDir / "old_novelwriter.conf", oldFile)

    assert oldFile.is_file()
    assert not newFile.exists()

    conf = Config()
    conf.initConfig(confPath=fncPath, dataPath=fncPath)
    assert conf.loadConfig() is True

    # The old file should have triggered a conversion to the new format
    assert newFile.exists()

    # A selection of values should have been picked up from the old file
    assert conf.lightTheme == "default_light"
    assert conf.darkTheme == "default_dark"
    assert conf.themeMode == nwTheme.AUTO
    assert conf.mainWinSize == [1200, 650]
    assert conf.fontWinSize == [700, 550]
    assert conf.autoSaveProj == 60
    assert conf.autoSaveDoc == 30
    assert conf.backupInterval == "session"
    assert conf.textWidth == 700
    assert conf.tabWidth == 40
    assert conf.dialogStyle == 2
    assert conf.spellLanguage == "en"
    assert conf.userIdleTime == 300
    assert conf.showSessionTime is True
    assert conf.searchRegEx is False

    # Loading the newly converted file should produce the same values
    newConf = Config()
    newConf.initConfig(confPath=fncPath, dataPath=fncPath)
    assert newConf.loadConfig() is True
    assert newConf.mainWinSize == conf.mainWinSize
    assert newConf.dialogStyle == conf.dialogStyle
    assert newConf.spellLanguage == conf.spellLanguage
