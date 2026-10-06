"""
novelWriter - Manuscript Build Dialog Tests
===========================================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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

import pytest

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QFileDialog, QListWidgetItem, QPushButton

from novelwriter import SHARED
from novelwriter.constants import nwLabels
from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt
from novelwriter.manuscript.buildsettings import BuildSettings
from novelwriter.manuscript.manusbuild import GuiManuscriptBuild
from novelwriter.shared import _GuiAlert

from tests.helpers import C, buildTestProject


@pytest.mark.gui
def testGuiManuscriptBuild_Main(monkeypatch, qtbot, nwGUI, fncPath, projPath, mockRnd):
    """Test the GuiManuscriptBuild dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    build = BuildSettings()
    build.setLastBuildPath(fncPath)

    manus = GuiManuscriptBuild(nwGUI, build)
    manus.show()

    # Check initial values
    assert manus.buildPath.text() == str(fncPath)
    assert manus.buildName.text() == "New Project - "
    assert manus.listContent.count() == 3  # All novel docs

    # Reset build name to default
    build.setName("Test Build")
    manus.btnReset.click()
    assert manus.buildName.text() == "New Project - Test Build"

    # Change path
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a: str(projPath))
        manus.btnBrowse.click()
        assert manus.buildPath.text() == str(projPath)

    # Builds
    # ======

    # Reset values
    manus.buildPath.setText(str(fncPath))
    manus.buildName.setText("TestBuild")

    # Helper function
    def selectFormat(fmt):
        for i in range(manus.listFormats.count()):
            item = manus.listFormats.item(i)
            assert isinstance(item, QListWidgetItem)
            if item.data(manus.D_KEY) == fmt:
                manus.listFormats.setCurrentItem(item)
                return
        raise ValueError("No such key in format list")

    # Build documents
    lastFmt = None
    for fmt in nwBuildFmt:
        selectFormat(fmt)
        assert manus._getSelectedFormat() == fmt
        manus.btnBuild.click()
        assert (fncPath / "TestBuild").with_suffix(nwLabels.BUILD_EXT[fmt]).exists()
        lastFmt = fmt

    manus._dialogButtonClicked(manus.btnClose)
    manus.deleteLater()

    assert build.lastBuildName == "TestBuild"
    assert build.lastFormat == lastFmt
    assert build.lastBuildPath == fncPath


@pytest.mark.gui
def testGuiManuscriptBuild_ErrorHandling(monkeypatch, qtbot, nwGUI, fncPath, projPath, mockRnd):
    """Test error handling in the GuiManuscriptBuild dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    build = BuildSettings()
    build.setName("Test Build")
    build.setLastBuildPath(fncPath)
    build.setLastBuildName("TestBuild")
    build.setLastFormat(nwBuildFmt.ODT)

    manus = GuiManuscriptBuild(nwGUI, build)
    manus.show()

    def selectFormat(fmt):
        for i in range(manus.listFormats.count()):
            item = manus.listFormats.item(i)
            assert isinstance(item, QListWidgetItem)
            if item.data(manus.D_KEY) == fmt:
                manus.listFormats.setCurrentItem(item)
                return
        raise ValueError("No such key in format list")

    # Name, path and format should be remembered
    assert manus.buildPath.text() == str(fncPath)
    assert manus.buildName.text() == "TestBuild"
    assert manus._getSelectedFormat() == nwBuildFmt.ODT

    # Check handling of no selected build
    manus.listFormats.clearSelection()
    assert manus._getSelectedFormat() is None
    assert manus._runBuild() is False

    # Check ODT build with no name set, which should just reset it
    selectFormat(nwBuildFmt.ODT)
    manus.buildName.clear()
    assert manus._runBuild() is True
    assert manus.buildName.text() == "New Project - Test Build"
    assert (fncPath / "New Project - Test Build.odt").exists()

    # But invalid path should fail
    manus.buildPath.setText(str(fncPath / "blabla"))
    assert manus._runBuild() is False

    # Blocking overwrite should also fail
    (fncPath / "TestBuild.odt").touch()
    manus.buildPath.setText(str(fncPath))
    manus.buildName.setText("TestBuild")
    with monkeypatch.context() as mp:
        mp.setattr(_GuiAlert, "finalState", False)
        assert manus._runBuild() is False

    # Test that the open button works
    lastUrl = ""

    def mockOpenUrl(url: QUrl) -> None:
        nonlocal lastUrl
        lastUrl = url.toString()

    with monkeypatch.context() as mp:
        mp.setattr(QDesktopServices, "openUrl", mockOpenUrl)
        manus.btnOpen.click()
        assert lastUrl.startswith("file://")

    # Finish
    manus._dialogButtonClicked(manus.btnClose)
    manus.deleteLater()


@pytest.mark.gui
def testGuiManuscriptBuild_EdgeCases(monkeypatch, qtbot, nwGUI, fncPath, projPath, mockRnd):
    """Test edge cases in the GuiManuscriptBuild dialog."""
    buildTestProject(NWProject(), projPath)
    nwGUI.openProject(projPath)
    build = BuildSettings()
    build.setLastBuildPath(fncPath)

    # Edge Cases
    # ==========

    # No format matches the last used format: nothing is preselected
    with monkeypatch.context() as mp:
        mp.setattr(type(build), "lastFormat", property(lambda self: None))
        manus = GuiManuscriptBuild(nwGUI, build)
        assert manus._getSelectedFormat() is None
        manus.deleteLater()

    manus = GuiManuscriptBuild(nwGUI, build)
    manus.show()

    # A button that isn't part of the dialog is ignored
    manus._dialogButtonClicked(QPushButton())

    # Cancelling the folder browse dialog leaves the path unchanged
    pathBefore = manus.buildPath.text()
    with monkeypatch.context() as mp:
        mp.setattr(QFileDialog, "getExistingDirectory", lambda *a: "")
        manus._doSelectPath()
        assert manus.buildPath.text() == pathBefore

    # A note file is filtered out of the content list by default
    SHARED.project.newFile("A Note", C.hCharRoot)
    manus._populateContentList()
    assert manus.listContent.count() == 3

    # An item whose root can't be looked up is still listed, just
    # without a proper root name
    with monkeypatch.context() as mp:
        mp.setattr(type(SHARED.project.tree), "__getitem__", lambda self, handle: None)
        manus._populateContentList()
        assert manus.listContent.count() == 3
        firstItem = manus.listContent.item(0)
        assert firstItem is not None
        assert firstItem.text().startswith("??????: ")

    manus._dialogButtonClicked(manus.btnClose)
    manus.deleteLater()
