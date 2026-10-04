"""
novelWriter - GUI Story View Base
=================================

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

from typing import TYPE_CHECKING

from PyQt6.QtCore import QEvent, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QAbstractButton,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from novelwriter import SHARED
from novelwriter.common import simplified
from novelwriter.enum import nwStandardButton
from novelwriter.extensions.configlayout import NColorLabel, NScrollableForm
from novelwriter.extensions.modified import NToolDialog
from novelwriter.extensions.pagedsidebar import NPagedSideBar
from novelwriter.story.storysettings import StoryViewSettings
from novelwriter.types import QtRoleAccept, QtRoleDestruct

if TYPE_CHECKING:
    from novelwriter.guimain import GuiMain

logger = logging.getLogger(__name__)


class GuiStoryViewBase(QWidget):
    """GUI: Story View Base Class.

    The base class for the views on the Story View tabs. Subclasses add
    their content to the outer layout and implement refresh.
    """

    def __init__(self, parent: QWidget, settings: StoryViewSettings) -> None:
        super().__init__(parent)

        self._settings = settings

        self.outerBox = QVBoxLayout()
        self.outerBox.setContentsMargins(0, 0, 0, 0)
        self.outerBox.setSpacing(0)

        self.setLayout(self.outerBox)

    ##
    #  Properties
    ##

    @property
    def settings(self) -> StoryViewSettings:
        """Return the view settings object."""
        return self._settings

    ##
    #  Methods
    ##

    def updateTheme(self) -> None:
        """Update theme elements."""

    def initSettings(self) -> None:
        """Apply changes to the preferences."""

    def refresh(self, rootHandle: str | None, force: bool = False) -> None:
        """Refresh the view content."""

    def saveViewState(self) -> None:
        """Save the view state to the settings object."""

    def setHighlight(self, tags: set[str]) -> None:
        """Set the reference tag keys to highlight."""

    def settingsDialog(self) -> type[GuiStorySettingsBase] | None:
        """Return the settings dialog class of the view, if any."""
        return None


class GuiStorySettingsBase(NToolDialog):
    """GUI: Story View Settings Dialog Base.

    Subclasses build the settings form with section identifiers from
    FORM_SECTION and up, and can add pages with identifiers below it.
    """

    FORM_SECTION = 10

    newSettingsReady = pyqtSignal(StoryViewSettings)

    def __init__(self, parent: GuiMain, settings: StoryViewSettings) -> None:
        super().__init__(parent)

        logger.debug("Create: GuiStorySettings")
        self.setObjectName("GuiStorySettings")

        self._settings = settings.copy()
        self._savedName = settings.name
        self._discard = False
        self._pages: dict[int, QWidget] = {}
        self._before: list[tuple[int, str]] = []
        self._after: list[tuple[int, str]] = []
        self._beforeLabel = ""
        self._afterLabel = ""

        options = SHARED.project.options
        self.setMinimumSize(600, 400)
        self.resize(
            options.getInt("GuiStorySettings", "winWidth", 650),
            options.getInt("GuiStorySettings", "winHeight", 550),
        )

        # Title
        self.titleLabel = NColorLabel(
            "Title",
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.HEADER_SCALE,
            indent=4,
        )

        # Settings Name
        self.nameLabel = QLabel(self.tr("Name"), self)
        self.viewName = QLineEdit(self)
        self.viewName.setText(self._settings.name)

        # SideBar
        self.sidebar = NPagedSideBar(self)
        self.sidebar.setLabelColor(SHARED.theme.helpText)

        # Settings Form
        self.form = NScrollableForm(self)
        self.sidebar.buttonClicked.connect(self._stackPageSelected)

        # Content
        self.toolStack = QStackedWidget(self)

        # Buttons
        self.btnSave = SHARED.theme.getStandardButton(nwStandardButton.SAVE, self)
        self.btnClose = SHARED.theme.getStandardButton(nwStandardButton.CLOSE, self)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnSave, QtRoleAccept)
        self.btnBox.addButton(self.btnClose, QtRoleDestruct)
        self.btnBox.clicked.connect(self._dialogButtonClicked)

        # Assemble
        self.topBox = QHBoxLayout()
        self.topBox.addWidget(self.titleLabel)
        self.topBox.addStretch(1)
        self.topBox.addWidget(self.nameLabel)
        self.topBox.addWidget(self.viewName, 1)

        self.mainBox = QHBoxLayout()
        self.mainBox.addWidget(self.sidebar)
        self.mainBox.addWidget(self.toolStack)
        self.mainBox.setContentsMargins(0, 0, 0, 0)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.topBox)
        self.outerBox.addLayout(self.mainBox)
        self.outerBox.addWidget(self.btnBox)
        self.outerBox.setSpacing(12)

        self.setLayout(self.outerBox)
        self._buildContent()
        self.loadSettings()
        self.updateTheme(init=True)

        logger.debug("Ready: GuiStorySettings")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiStorySettings")

    def updateTheme(self, *, init: bool = False) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiStorySettings")

        if not init:
            self.btnSave.refreshTheme()
            self.btnClose.refreshTheme()

        self.titleLabel.setTextColors(color=SHARED.theme.helpText)
        self.sidebar.setLabelColor(SHARED.theme.helpText)

    def discardAndClose(self) -> None:
        """Close the dialog without saving or asking to save changes."""
        self._discard = True
        self.close()

    ##
    #  Properties
    ##

    @property
    def viewID(self) -> str:
        """Return the view ID of the settings being edited."""
        return self._settings.viewID

    ##
    #  Setters
    ##

    def setTitle(self, title: str) -> None:
        """Set the dialog title."""
        self.setWindowTitle(title)
        self.titleLabel.setText(title)
        self.sidebar.setAccessibleName(title)

    ##
    #  Methods
    ##

    def addPage(self, page: QWidget, title: str, pageId: int, after: bool = False) -> None:
        """Add a page before or after the settings form."""
        self._pages[pageId] = page
        if after:
            self._after.append((pageId, title))
        else:
            self._before.append((pageId, title))

    def setPageLabel(self, label: str, after: bool = False) -> None:
        """Set a sidebar label above the pages before or after the form."""
        if after:
            self._afterLabel = label
        else:
            self._beforeLabel = label

    ##
    #  Overload
    ##

    def buildPages(self) -> None:
        """Overload this to add pages with addPage."""

    def buildForm(self) -> None:
        """Overload this to build the form."""

    def loadSettings(self) -> None:
        """Overload this to load settings."""

    def saveSettings(self) -> None:
        """Overload this to save settings."""

    ##
    #  Events
    ##

    def closeEvent(self, event: QEvent) -> None:
        """Apply changes and ask to save them when closing."""
        logger.debug("Closing: GuiStorySettings")
        if not self._discard:
            self._applyChanges()
            self._askToSave()
        self._saveWindowState()
        event.accept()
        self.softDelete()

    ##
    #  Private Slots
    ##

    @pyqtSlot("QAbstractButton*")
    def _dialogButtonClicked(self, button: QAbstractButton) -> None:
        """Handle button clicks from the dialog button box."""
        if button == self.btnSave:
            self._applyChanges()
            self._emitSettings()
            self.close()
        elif button == self.btnClose:
            self.close()
        else:  # pragma: no cover
            pass

    @pyqtSlot(int)
    def _stackPageSelected(self, pageId: int) -> None:
        """Switch to the page, or scroll to the form section."""
        if page := self._pages.get(pageId):
            self.toolStack.setCurrentWidget(page)
        else:
            self.toolStack.setCurrentWidget(self.form)
            self.form.scrollToSection(pageId)

    ##
    #  Internal Functions
    ##

    def _buildContent(self) -> None:
        """Build the pages and the form, in sidebar order."""
        self.buildPages()
        if self._before and self._beforeLabel:
            self.sidebar.addLabel(self._beforeLabel)
        for pageId, title in self._before:
            self.sidebar.addButton(title, pageId)
            self.toolStack.addWidget(self._pages[pageId])
        self.buildForm()
        self.toolStack.addWidget(self.form)
        if self._after and self._afterLabel:
            self.sidebar.addLabel(self._afterLabel)
        for pageId, title in self._after:
            self.sidebar.addButton(title, pageId)
            self.toolStack.addWidget(self._pages[pageId])
        if self._before:
            self.sidebar.setSelected(self._before[0][0])

    def _askToSave(self) -> None:
        """Ask to save unsaved changes, if any."""
        if self._settings.changed:
            if SHARED.question(self.tr("Do you want to save your changes to '{0}'?").format(self._settings.name)):
                self._emitSettings()
            self._settings.resetChangedState()
        elif self._settings.name != self._savedName:
            # A rename does not need a rebuild, so save it without asking
            self._emitSettings()

    def _saveWindowState(self) -> None:
        """Save the dialog window size."""
        logger.debug("Saving State: GuiStorySettings")
        options = SHARED.project.options
        options.setValue("GuiStorySettings", "winWidth", self.width())
        options.setValue("GuiStorySettings", "winHeight", self.height())
        options.saveSettings()

    def _applyChanges(self) -> None:
        """Apply the name and the form values to the settings."""
        self._settings.setName(simplified(self.viewName.text()) or self._settings.defaultName)
        self.saveSettings()

    def _emitSettings(self) -> None:
        """Emit the settings and reset the changed state."""
        self._savedName = self._settings.name
        self.newSettingsReady.emit(self._settings)
        self._settings.resetChangedState()
