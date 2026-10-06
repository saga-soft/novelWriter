"""
novelWriter - Test Suite Configuration
======================================

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
import shutil
import sys
import warnings

from pathlib import Path

import pytest

from PyQt6.QtCore import QAbstractAnimation, QLocale, QThreadPool
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

sys.path.insert(1, str(Path(__file__).parent.parent.absolute()))

from novelwriter import CONFIG, SHARED
from novelwriter.config import DEF_GUI_DARK, DEF_GUI_LIGHT
from novelwriter.enum import nwTheme

from tests.mocked import MockGuiMain

_TST_ROOT = Path(__file__).parent
_SRC_ROOT = _TST_ROOT.parent
_TMP_ROOT = _TST_ROOT / "_temp"
_TMP_CONF = _TMP_ROOT / "conf"


##
#  Helper Functions
##


def resetConfigVars():
    """Reset the CONFIG object and set various values for testing to
    prevent interfering with local OS.
    """
    CONFIG.setBackupPath(_TMP_ROOT)
    CONFIG.setGuiFont(None)
    CONFIG.setTextFont(None)
    CONFIG.backupOnClose = False
    CONFIG._homePath = _TMP_ROOT
    CONFIG._dLocale = QLocale("en_GB")
    CONFIG._manuals = {"manual": _TMP_ROOT / "manual.pdf"}
    CONFIG.guiLocale = "en_GB"
    CONFIG.darkTheme = DEF_GUI_DARK
    CONFIG.lightTheme = DEF_GUI_LIGHT
    CONFIG.themeMode = nwTheme.LIGHT

    # Enable a few settings to ensure better coverage
    CONFIG.emphLabels = True
    CONFIG.lineHighlight = True


##
#  Auto Fixtures
##


@pytest.fixture(scope="session", autouse=True)
def sessionFixture():
    """A default session wide fixture to set up the test environment."""
    logging.root.setLevel(logging.INFO)
    if _TMP_ROOT.exists():
        shutil.rmtree(_TMP_ROOT)
    _TMP_ROOT.mkdir()
    _TMP_CONF.mkdir()
    (_TMP_ROOT / "manual.pdf").touch()
    (_SRC_ROOT / "novelwriter" / "assets" / "manual.pdf").touch()
    (_SRC_ROOT / "novelwriter" / "assets" / "manual_fr.pdf").touch()


@pytest.fixture(autouse=True)
def functionFixture(qtbot):
    """A default function fixture that:
    * Ensures that the main Qt thread is always available
    * Resets the config object for each function and redirect its
      storage paths to temporary test folders.
    """
    if _TMP_CONF.exists():
        shutil.rmtree(_TMP_CONF)
    _TMP_CONF.mkdir()

    CONFIG.__init__()
    CONFIG.initConfig(confPath=_TMP_CONF, dataPath=_TMP_CONF)
    resetConfigVars()
    logging.getLogger("novelwriter").setLevel(logging.INFO)


##
#  Core Test Folders
##


@pytest.fixture(scope="session")
def tstPaths():
    """Return an object that can provide the various paths needed for
    running tests.
    """

    class _Store:
        testDir = _TST_ROOT
        filesDir = _TST_ROOT / "_files"
        refDir = _TST_ROOT / "_reference"
        outDir = _TMP_ROOT / "results"
        tmpDir = _TMP_ROOT
        cnfDir = _TMP_CONF

    store = _Store()
    store.outDir.mkdir(exist_ok=True)

    return store


@pytest.fixture
def fncPath():
    """A temporary folder for a single test function."""
    fncPath = _TMP_ROOT / "function"
    if fncPath.is_dir():
        shutil.rmtree(fncPath)
    fncPath.mkdir(exist_ok=True)
    return fncPath


@pytest.fixture
def projPath(fncPath):
    """A temp folder for a single test function + project folder."""
    prjDir = fncPath / "project"
    if prjDir.exists():
        shutil.rmtree(prjDir)
    prjDir.mkdir(exist_ok=True)
    return prjDir


##
#  novelWriter Objects
##


@pytest.fixture
def mockGUI(qtbot, monkeypatch):
    """Create a mock instance of novelWriter's main GUI class."""
    from novelwriter.gui.theme import GuiTheme
    from novelwriter.shared import _GuiAlert

    monkeypatch.setattr(QMessageBox, "exec", lambda *a: None)
    monkeypatch.setattr(_GuiAlert, "exec", lambda *a: None)
    monkeypatch.setattr(_GuiAlert, "finalState", True)
    gui = MockGuiMain()
    theme = GuiTheme()
    monkeypatch.setattr(SHARED, "_gui", gui)
    monkeypatch.setattr(SHARED, "_theme", theme)

    qtbot.addWidget(gui)

    return gui


@pytest.fixture
def mockGUIwithTheme(mockGUI):
    """Create a mock instance of novelWriter's main GUI class with the
    theme instance initialised.
    """
    SHARED.theme.initThemes()
    return mockGUI


@pytest.fixture
def nwGUI(qtbot, monkeypatch, functionFixture):
    """Create an instance of the novelWriter GUI."""
    from novelwriter.gui.theme import GuiTheme
    from novelwriter.guimain import GuiMain
    from novelwriter.shared import _GuiAlert

    monkeypatch.setattr(QMessageBox, "exec", lambda *a: None)
    monkeypatch.setattr(_GuiAlert, "exec", lambda *a: None)
    monkeypatch.setattr(_GuiAlert, "finalState", True)

    CONFIG.loadConfig()
    SHARED.initTheme(GuiTheme())
    nwGUI = GuiMain()
    qtbot.addWidget(nwGUI, before_close_func=_checkNoLeftoverState)
    resetConfigVars()
    nwGUI.docEditor.initEditor()

    nwGUI.show()
    qtbot.wait(20)

    yield nwGUI

    # Let any in-flight background jobs (word counter, text checker)
    # finish and deliver their queued signals before the widget tree
    # below them is closed and scheduled for deletion
    if globalPool := QThreadPool.globalInstance():
        globalPool.waitForDone(7000)
        globalPool.clear()

    nwGUI.close()


##
#  Python Objects
##


@pytest.fixture
def mockRnd(monkeypatch):
    """Create a mock random number generator that just counts upwards
    from 0. This one will generate status/importance flags and handles
    in a predictable sequence.
    """

    class MockRnd:
        def __init__(self):
            self.reset()

        def _rnd(self, n):
            yield from range(n)

        def reset(self):
            gen = self._rnd(1000)
            monkeypatch.setattr("random.getrandbits", lambda *a: next(gen))

    return MockRnd()


##
#  Temp Project Folders
##


@pytest.fixture
def prjLipsum():
    """A medium sized novelWriter example project with a lot of Lorem
    Ipsum text.
    """
    src = _TST_ROOT / "_lipsum"
    dst = _TMP_ROOT / "lipsum"
    if dst.exists():
        shutil.rmtree(dst)

    shutil.copytree(src, dst)

    # Delete all generated files
    (dst / "nwProject.bak").unlink(missing_ok=True)
    (dst / "ToC.txt").unlink(missing_ok=True)
    if (meta := dst / "meta").is_dir():
        shutil.rmtree(meta)

    yield dst

    if dst.exists():
        shutil.rmtree(dst)


@pytest.fixture(scope="session")
def ipsumText():
    """Return five paragraphs of Lorem Ipsum text."""
    return [
        (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nunc maximus justo non dictum co"
            "mmodo. Curabitur lacinia tempor orci vel luctus. Phasellus porta metus eu massa luctus, e"
            "get euismod risus rhoncus. Vestibulum sed arcu nisi. Maecenas pretium facilisis velit, ve"
            "l semper lacus aliquam sit amet. Vestibulum vulputate neque ligula, rhoncus blandit turpi"
            "s consequat id. Mauris sagittis vehicula imperdiet. Duis sed nunc pretium, ornare purus v"
            "el, sodales augue. Maecenas a suscipit risus. Quisque volutpat justo eleifend est ullamco"
            "rper fermentum. Donec ullamcorper et tortor a laoreet. Nam id risus nisi. Vivamus non imp"
            "erdiet erat, sit amet imperdiet felis. Mauris vitae neque et est aliquam scelerisque non "
            "non ipsum."
        ),
        (
            "Nullam laoreet lorem nec malesuada vehicula. Vivamus tempus sodales lectus sed viverra. A"
            "enean lacinia sollicitudin quam, quis tempus eros suscipit id. Duis sed rutrum nisi, ut p"
            "ulvinar magna. Nam et cursus tortor. Phasellus ac odio tellus. Nullam in iaculis ipsum. V"
            "ivamus ante sem, ultricies sed varius quis, tristique nec tellus. Nullam eu urna vitae la"
            "cus hendrerit gravida. Quisque pulvinar erat ex, id efficitur velit sodales vitae. Proin "
            "vestibulum, sapien eget mattis euismod, tortor quam viverra risus, at congue mauris torto"
            "r eu nunc. Mauris pellentesque elit leo, quis eleifend sem placerat a. Vivamus iaculis du"
            "i eget tellus volutpat, ac varius nisi facilisis."
        ),
        (
            "Nullam a nisl magna. Praesent commodo nec diam aliquet vestibulum. In sapien velit, sodal"
            "es feugiat porta ut, rhoncus a elit. Quisque egestas nisi eu eros laoreet, quis facilisis"
            " est pretium. Nullam bibendum sed tellus nec lobortis. Duis elit massa, volutpat a lacini"
            "a a, ullamcorper in dui. Suspendisse ac laoreet dui. Curabitur elementum, tortor elementu"
            "m ultricies laoreet, nunc massa vulputate augue, vitae tincidunt nunc enim eget nisl."
        ),
        (
            "Pellentesque nibh urna, volutpat et feugiat porta, rutrum sed lectus. Aliquam eget risus "
            "id orci tincidunt condimentum et sit amet purus. Curabitur tincidunt odio vel ante feugia"
            "t feugiat. Proin nunc lorem, molestie a sapien et, varius elementum nunc. Donec non ferme"
            "ntum nisl. In et massa placerat, faucibus felis eu, congue nisi. Proin sed tortor non lor"
            "em mattis cursus. Vestibulum magna neque, bibendum vel nibh et, tincidunt rhoncus nisi. D"
            "uis pulvinar mi a quam rutrum maximus. Nunc sollicitudin, urna in cursus facilisis, augue"
            " neque imperdiet metus, ac finibus lorem ante id nulla. Sed maximus eleifend justo id feu"
            "giat. Cras eget diam vel est blandit tempor nec a leo. Mauris risus est, fringilla in ali"
            "quam a, sagittis vel enim. Nullam sodales id erat placerat lobortis."
        ),
        (
            "Integer ac gravida quam. Quisque eleifend nisl nec pretium tincidunt. Quisque sollicitudi"
            "n nisi in hendrerit scelerisque. Sed ornare nisl lacus, sit amet consectetur lectus egest"
            "as et. Vivamus nec arcu lorem. Donec rhoncus, purus a porta accumsan, nunc lectus iaculis"
            " libero, et fringilla tellus augue et velit. Integer varius felis scelerisque, vulputate "
            "tellus eu, laoreet justo. Suspendisse sit amet sem vehicula, auctor odio sed, aliquet eni"
            "m. In ac tortor sed tortor fringilla elementum. Nulla non odio at magna vulputate sceleri"
            "sque. Nam elementum diam eu rutrum scelerisque. Sed fermentum, felis quis vulputate ferme"
            "ntum, libero metus sollicitudin est, in faucibus purus nulla non dolor. Ut vitae felis po"
            "rta, feugiat nunc et, bibendum neque. Nullam nec lorem nec metus ullamcorper malesuada ut"
            " a nisl. Etiam eget tristique dui. Nulla sed mi finibus, venenatis tellus non, maximus en"
            "im."
        ),
    ]


##
#  Checker Functions
##


def _checkNoLeftoverState(widget: QWidget) -> None:
    """Warn if the test left an animation still running or an extra
    top-level widget open.
    """
    running = [a for a in widget.findChildren(QAbstractAnimation) if a.state() == QAbstractAnimation.State.Running]
    if running:
        warnings.warn(f"Test left {len(running)} animation(s) still running: {running}", stacklevel=2)

    extra = [w for w in QApplication.topLevelWidgets() if w is not widget and w.isVisible()]
    if extra:
        warnings.warn(f"Test left extra top-level widget(s) open: {extra}", stacklevel=2)
