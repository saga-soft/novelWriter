"""
novelWriter - GUI Preferences
=============================

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

from typing import NamedTuple

from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent, QKeySequence
from PyQt6.QtWidgets import (
    QCompleter,
    QDialogButtonBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QMenu,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from novelwriter import CONFIG, SHARED
from novelwriter.common import compact, describeFont, processDialogSymbols, qtAddAction, uniqueCompact
from novelwriter.config import DEF_GUI_DARK, DEF_GUI_LIGHT, DEF_ICONS, DEF_TREECOL
from novelwriter.constants import nwLabels, nwQuotes, nwUnicode, trConst, trUnit
from novelwriter.dialogs.quotes import GuiQuoteSelect
from novelwriter.enum import nwStandardButton, nwStdUnit, nwToolButton
from novelwriter.extensions.configlayout import NColorLabel, NScrollableForm
from novelwriter.extensions.modified import NComboBox, NDialog, NDoubleSpinBox, NIconButton, NSpinBox
from novelwriter.extensions.pagedsidebar import NPagedSideBar
from novelwriter.extensions.switch import NSwitch
from novelwriter.types import QtAlignCenter, QtRoleAccept, QtRoleReject

logger = logging.getLogger(__name__)


class GuiNeedsUpdate(NamedTuple):
    """The update flags after settings have been processed."""

    restart: bool
    tree: bool
    theme: bool
    syntax: bool
    spelling: bool
    vim: bool
    editor: bool
    viewer: bool
    viewport: bool


class GuiPreferences(NDialog):
    """GUI: Preferences Dialog."""

    newPreferencesReady = pyqtSignal(GuiNeedsUpdate)

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiPreferences")
        self.setObjectName("GuiPreferences")
        self.setWindowTitle(self.tr("Preferences"))
        self.setMinimumSize(600, 500)
        self.resize(*CONFIG.prefsWinSize)

        # Title
        self.titleLabel = NColorLabel(
            self.tr("Preferences"),
            self,
            color=SHARED.theme.helpText,
            scale=NColorLabel.HEADER_SCALE,
            indent=4,
        )

        # Search Box
        self.searchAction = QAction(SHARED.theme.getIcon("search:apply"), "")
        self.searchAction.triggered.connect(self._gotoSearch)

        self.searchText = QLineEdit(self)
        self.searchText.setPlaceholderText(self.tr("Search"))
        self.searchText.setMinimumWidth(200)
        self.searchText.addAction(self.searchAction, QLineEdit.ActionPosition.TrailingPosition)

        # SideBar
        self.sidebar = NPagedSideBar(self)
        self.sidebar.setLabelColor(SHARED.theme.helpText)
        self.sidebar.setAccessibleName(self.titleLabel.text())
        self.sidebar.buttonClicked.connect(self._sidebarClicked)

        # Form
        self.mainForm = NScrollableForm(self)
        self.mainForm.setHelpTextStyle(SHARED.theme.helpText)

        # Buttons
        self.btnSave = SHARED.theme.getStandardButton(nwStandardButton.SAVE, self)
        self.btnSave.clicked.connect(self._doSave)

        self.btnCancel = SHARED.theme.getStandardButton(nwStandardButton.CANCEL, self)
        self.btnCancel.clicked.connect(self.closeDialog)

        self.btnBox = QDialogButtonBox(self)
        self.btnBox.addButton(self.btnSave, QtRoleAccept)
        self.btnBox.addButton(self.btnCancel, QtRoleReject)

        # Assemble
        self.searchBox = QHBoxLayout()
        self.searchBox.addWidget(self.titleLabel)
        self.searchBox.addStretch(1)
        self.searchBox.addWidget(self.searchText, 1)

        self.mainBox = QHBoxLayout()
        self.mainBox.addWidget(self.sidebar)
        self.mainBox.addWidget(self.mainForm)
        self.mainBox.setContentsMargins(0, 0, 0, 0)

        self.outerBox = QVBoxLayout()
        self.outerBox.addLayout(self.searchBox)
        self.outerBox.addLayout(self.mainBox)
        self.outerBox.addWidget(self.btnBox)
        self.outerBox.setSpacing(8)

        self.setLayout(self.outerBox)
        self.setSizeGripEnabled(True)

        # Build Form
        self.buildForm()

        # Populate Search
        self.searchCompleter = QCompleter(self.mainForm.labels, self)
        self.searchCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.searchCompleter.setFilterMode(Qt.MatchFlag.MatchContains)
        self.searchCompleter.activated.connect(self._gotoSearch)

        self.searchText.setCompleter(self.searchCompleter)

        logger.debug("Ready: GuiPreferences")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: GuiPreferences")

    def buildForm(self) -> None:
        """Build the settings form."""
        section = 0
        iSz = SHARED.theme.baseIconSize
        boxFixed = 6 * SHARED.theme.textNWidth

        # Temporary Variables
        self._guiFont = CONFIG.guiFont
        self._textFont = CONFIG.textFont

        trPx = trUnit(nwStdUnit.PIXELS)
        trSec = trUnit(nwStdUnit.SECONDS)
        trMin = trUnit(nwStdUnit.MINUTES)

        # Label
        self.sidebar.addLabel(self.tr("General"))

        # Appearance
        # ==========

        title = self.tr("Appearance")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Display Language
        self.guiLocale = NComboBox(self)
        self.guiLocale.setMinimumWidth(200)
        for lang, name in CONFIG.listLanguages(CONFIG.LANG_NW):
            self.guiLocale.addItem(name, lang)
        self.guiLocale.setCurrentData(CONFIG.guiLocale, "en_GB")

        self.mainForm.addRow(
            self.tr("Display language"),
            self.guiLocale,
            self.tr("Requires restart to take effect."),
            stretch=(3, 2),
        )

        # Colour Theme
        self.lightTheme = NComboBox(self)
        self.lightTheme.setMinimumWidth(200)
        self.darkTheme = NComboBox(self)
        self.darkTheme.setMinimumWidth(200)
        for key, theme in SHARED.theme.colourThemes.items():
            if theme.dark:
                self.darkTheme.addItem(theme.name, key)
            else:
                self.lightTheme.addItem(theme.name, key)

        self.lightTheme.setCurrentData(CONFIG.lightTheme, DEF_GUI_LIGHT)
        self.darkTheme.setCurrentData(CONFIG.darkTheme, DEF_GUI_DARK)

        self.mainForm.addRow(
            self.tr("Light colour theme"),
            self.lightTheme,
            self.tr("You can change theme mode from the sidebar."),
            stretch=(3, 2),
        )
        self.mainForm.addRow(
            self.tr("Dark colour theme"),
            self.darkTheme,
            self.tr("You can change theme mode from the sidebar."),
            stretch=(3, 2),
        )

        # Icon Theme
        self.iconTheme = NComboBox(self)
        self.iconTheme.setMinimumWidth(200)
        for key, theme in SHARED.theme.iconCache.iconThemes.items():
            self.iconTheme.addItem(theme.name, key)

        self.iconTheme.setCurrentData(CONFIG.iconTheme, DEF_ICONS)

        self.mainForm.addRow(
            self.tr("Icon theme"),
            self.iconTheme,
            self.tr("User interface icon theme."),
            stretch=(3, 2),
        )

        # Application Font Family
        self.guiFont = QLineEdit(self)
        self.guiFont.setReadOnly(True)
        self.guiFont.setMinimumWidth(162)
        self.guiFont.setText(describeFont(self._guiFont))
        self.guiFont.setCursorPosition(0)
        self.guiFontButton = SHARED.theme.getIconButton(nwToolButton.FONT, self)
        self.guiFontButton.clicked.connect(self._selectGuiFont)
        self.mainForm.addRow(
            self.tr("Application font"),
            self.guiFont,
            self.tr("Requires restart to take effect."),
            stretch=(3, 2),
            button=self.guiFontButton,
        )

        # Vertical Scrollbars
        self.hideVScroll = NSwitch(self)
        self.hideVScroll.setChecked(CONFIG.hideVScroll)
        self.mainForm.addRow(
            self.tr("Hide vertical scroll bars in main windows"),
            self.hideVScroll,
            self.tr("Scrolling available with mouse wheel and keys only."),
        )

        # Horizontal Scrollbars
        self.hideHScroll = NSwitch(self)
        self.hideHScroll.setChecked(CONFIG.hideHScroll)
        self.mainForm.addRow(
            self.tr("Hide horizontal scroll bars in main windows"),
            self.hideHScroll,
            self.tr("Scrolling available with mouse wheel and keys only."),
        )

        # Native Font Dialog
        self.nativeFont = NSwitch(self)
        self.nativeFont.setChecked(CONFIG.nativeFont)
        self.mainForm.addRow(
            self.tr("Use the system's font selection dialog"),
            self.nativeFont,
            self.tr("Turn off to use the Qt font dialog, which may have more options."),
        )

        # Use Character Count
        self.useCharCount = NSwitch(self)
        self.useCharCount.setChecked(CONFIG.useCharCount)
        self.mainForm.addRow(
            self.tr("Prefer character count over word count"),
            self.useCharCount,
            self.tr("Display character count instead where available."),
        )

        # Document Style
        # ==============

        title = self.tr("Document Style")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Document Font Family
        self.textFont = QLineEdit(self)
        self.textFont.setReadOnly(True)
        self.textFont.setMinimumWidth(162)
        self.textFont.setText(describeFont(CONFIG.textFont))
        self.textFont.setCursorPosition(0)
        self.textFontButton = SHARED.theme.getIconButton(nwToolButton.FONT, self)
        self.textFontButton.clicked.connect(self._selectTextFont)
        self.mainForm.addRow(
            self.tr("Document font"),
            self.textFont,
            self.tr("Applies to both document editor and viewer."),
            stretch=(3, 2),
            button=self.textFontButton,
        )

        # Document Path
        self.showFullPath = NSwitch(self)
        self.showFullPath.setChecked(CONFIG.showFullPath)
        self.mainForm.addRow(
            self.tr("Show full path in document header"),
            self.showFullPath,
            self.tr("Add the parent folder names to the header."),
        )

        # Include Notes in Word Count
        self.incNotesWCount = NSwitch(self)
        self.incNotesWCount.setChecked(CONFIG.incNotesWCount)
        self.mainForm.addRow(
            self.tr("Include project notes in status bar word count"),
            self.incNotesWCount,
        )

        # Project View
        # ============

        title = self.tr("Project View")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Tree Icon Colours
        self.iconColTree = NComboBox(self)
        self.iconColTree.setMinimumWidth(200)
        self.iconColTree.addItem(self.tr("Theme Colours"), DEF_TREECOL)
        for key, label in nwLabels.THEME_COLORS.items():
            self.iconColTree.addItem(trConst(label), key)
        self.iconColTree.setCurrentData(CONFIG.iconColTree, DEF_TREECOL)

        self.mainForm.addRow(
            self.tr("Project tree icon colours"),
            self.iconColTree,
            self.tr("Override colours for project icons."),
            stretch=(3, 2),
        )

        # Keep Theme Colours on Documents
        self.iconColDocs = NSwitch(self)
        self.iconColDocs.setChecked(CONFIG.iconColDocs)
        self.mainForm.addRow(
            self.tr("Keep theme colours on documents"),
            self.iconColDocs,
            self.tr("Only override icon colours for folders."),
        )

        # Emphasise Labels
        self.emphLabels = NSwitch(self)
        self.emphLabels.setChecked(CONFIG.emphLabels)
        self.mainForm.addRow(
            self.tr("Emphasise partition and chapter labels"),
            self.emphLabels,
            self.tr("Makes them stand out in the project tree."),
        )

        # Behaviour
        # =========

        title = self.tr("Behaviour")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Document Save Timer
        self.autoSaveDoc = NSpinBox(self, minVal=5, maxVal=600)
        self.autoSaveDoc.setFixedNumbersWidth(3)
        self.autoSaveDoc.setValue(CONFIG.autoSaveDoc)
        self.mainForm.addRow(
            self.tr("Save document interval"),
            self.autoSaveDoc,
            self.tr("How often the document is automatically saved."),
            unit=trSec,
        )

        # Project Save Timer
        self.autoSaveProj = NSpinBox(self, minVal=5, maxVal=600)
        self.autoSaveProj.setFixedNumbersWidth(3)
        self.autoSaveProj.setValue(CONFIG.autoSaveProj)
        self.mainForm.addRow(
            self.tr("Save project interval"),
            self.autoSaveProj,
            self.tr("How often the project is automatically saved."),
            unit=trSec,
        )

        # Ask before exiting novelWriter
        self.askBeforeExit = NSwitch(self)
        self.askBeforeExit.setChecked(CONFIG.askBeforeExit)
        self.mainForm.addRow(
            self.tr("Ask before exiting novelWriter"),
            self.askBeforeExit,
            self.tr("Only applies when a project is open."),
        )

        # Centre main window on startup
        self.moveMainWin = NSwitch(self)
        self.moveMainWin.setChecked(CONFIG.moveMainWin)
        self.mainForm.addRow(
            self.tr("Centre window on startup"),
            self.moveMainWin,
            self.tr("Applies to main window and welcome dialog."),
        )

        # Project Backup
        # ==============

        title = self.tr("Project Backup")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Backup Path
        self.backupPath = CONFIG.backupPath()
        self.backupGetPath = QPushButton(SHARED.theme.getIcon("browse:system"), self.tr("Browse"), self)
        self.backupGetPath.setIconSize(iSz)
        self.backupGetPath.clicked.connect(self._backupFolder)
        self.mainForm.addRow(
            self.tr("Backup storage location"),
            self.backupGetPath,
            self.tr("Path: {0}").format(self.backupPath),
            editable="backupPath",
        )

        # Backup Interval
        self.backupInterval = NComboBox(self)
        for key, label in nwLabels.BACKUP_INTERVAL.items():
            self.backupInterval.addItem(trConst(label), key)
        self.backupInterval.setCurrentData(CONFIG.backupInterval, "session")
        self.mainForm.addRow(
            self.tr("Backup frequency"),
            self.backupInterval,
            self.tr("Keeps one backup for each time period."),
        )

        # Run When Closing
        self.backupOnClose = NSwitch(self)
        self.backupOnClose.setChecked(CONFIG.backupOnClose)
        self.backupOnClose.toggled.connect(self._toggledBackupOnClose)
        self.mainForm.addRow(
            self.tr("Run backup when the project is closed"),
            self.backupOnClose,
            self.tr("Can be overridden for individual projects in Project Settings."),
        )

        # Ask Before Backup
        # Only enabled when "Run when closing" is checked
        self.askBeforeBackup = NSwitch(self)
        self.askBeforeBackup.setChecked(CONFIG.askBeforeBackup)
        self.askBeforeBackup.setEnabled(CONFIG.backupOnClose)
        self.mainForm.addRow(
            self.tr("Ask before running backup"),
            self.askBeforeBackup,
            self.tr("If off, backups will run in the background."),
        )

        # Session Timer
        # =============

        title = self.tr("Session Timer")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Pause When Idle
        self.stopWhenIdle = NSwitch(self)
        self.stopWhenIdle.setChecked(CONFIG.stopWhenIdle)
        self.mainForm.addRow(
            self.tr("Pause the session timer when not writing"),
            self.stopWhenIdle,
            self.tr("Also pauses when the application window does not have focus."),
        )

        # Inactive Time for Idle
        self.userIdleTime = NDoubleSpinBox(self, minVal=0.5, maxVal=600.0, step=0.5, prec=1)
        self.userIdleTime.setFixedNumbersWidth(5)
        self.userIdleTime.setValue(CONFIG.userIdleTime / 60.0)
        self.mainForm.addRow(
            self.tr("Editor inactive time before pausing timer"),
            self.userIdleTime,
            self.tr("User activity includes typing and changing the content."),
            unit=trMin,
        )

        # Label
        self.sidebar.addLabel(self.tr("Writing"))

        # Text Flow
        # =========

        title = self.tr("Text Flow")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Max Text Width in Normal Mode
        self.textWidth = NSpinBox(self, minVal=0, maxVal=10000, step=10)
        self.textWidth.setFixedNumbersWidth(5)
        self.textWidth.setValue(CONFIG.textWidth)
        self.mainForm.addRow(
            self.tr('Maximum text width in "Normal Mode"'),
            self.textWidth,
            self.tr("Set to 0 to disable this feature."),
            unit=trPx,
        )

        # Max Text Width in Focus Mode
        self.focusWidth = NSpinBox(self, minVal=200, maxVal=10000, step=10)
        self.focusWidth.setFixedNumbersWidth(5)
        self.focusWidth.setValue(CONFIG.focusWidth)
        self.mainForm.addRow(
            self.tr('Maximum text width in "Focus Mode"'),
            self.focusWidth,
            self.tr("The maximum width cannot be disabled."),
            unit=trPx,
        )

        # Focus Mode Footer
        self.hideFocusFooter = NSwitch(self)
        self.hideFocusFooter.setChecked(CONFIG.hideFocusFooter)
        self.mainForm.addRow(
            self.tr('Hide document footer in "Focus Mode"'),
            self.hideFocusFooter,
            self.tr("Hide the information bar in the document editor."),
        )

        # Justify Text
        self.doJustify = NSwitch(self)
        self.doJustify.setChecked(CONFIG.doJustify)
        self.mainForm.addRow(
            self.tr("Justify the text margins"),
            self.doJustify,
            self.tr("Applies to both document editor and viewer."),
        )

        # Document Margins
        self.textMargin = NSpinBox(self, minVal=0, maxVal=900)
        self.textMargin.setFixedNumbersWidth(3)
        self.textMargin.setValue(CONFIG.textMargin)
        self.mainForm.addRow(
            self.tr("Minimum text margin"),
            self.textMargin,
            self.tr("Applies to both document editor and viewer."),
            unit=trPx,
        )

        # Tab Width
        self.tabWidth = NSpinBox(self, minVal=0, maxVal=200)
        self.tabWidth.setFixedNumbersWidth(3)
        self.tabWidth.setValue(CONFIG.tabWidth)
        self.mainForm.addRow(
            self.tr("Tab width"),
            self.tabWidth,
            self.tr("The width of a tab key press in the editor and viewer."),
            unit=trPx,
        )

        # Line Height
        self.lineHeight = NDoubleSpinBox(self, minVal=0.5, maxVal=3.0, step=0.05, prec=2)
        self.lineHeight.setValue(CONFIG.lineHeight)
        self.lineHeight.setFixedNumbersWidth(4)
        self.mainForm.addRow(
            self.tr("Line height"),
            self.lineHeight,
            self.tr("The relative line height in the editor and viewer."),
            unit=self.tr("em"),
        )

        # Text Editing
        # ============

        title = self.tr("Text Editing")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Spell Checking
        self.spellLanguage = NComboBox(self)
        self.spellLanguage.setMinimumWidth(200)

        if CONFIG.hasEnchant:
            for tag, language in SHARED.spelling.listDictionaries():
                self.spellLanguage.addItem(language, tag)
        else:
            self.spellLanguage.addItem(nwUnicode.U_EMDASH, "")
            self.spellLanguage.setEnabled(False)

        if (idx := self.spellLanguage.findData(CONFIG.spellLanguage)) != -1:
            self.spellLanguage.setCurrentIndex(idx)

        self.mainForm.addRow(
            self.tr("Spell check language"),
            self.spellLanguage,
            self.tr("Available languages are determined by your system."),
            stretch=(3, 2),
        )

        # Auto-Select Word Under Cursor
        self.autoSelect = NSwitch(self)
        self.autoSelect.setChecked(CONFIG.autoSelect)
        self.mainForm.addRow(
            self.tr("Auto-select word under cursor"),
            self.autoSelect,
            self.tr("Apply formatting to word under cursor if no selection is made."),
        )

        # Cursor Width
        self.cursorWidth = NSpinBox(self, minVal=1, maxVal=20)
        self.cursorWidth.setFixedNumbersWidth(2)
        self.cursorWidth.setValue(CONFIG.cursorWidth)
        self.mainForm.addRow(
            self.tr("Cursor width"),
            self.cursorWidth,
            self.tr("The width of the text cursor of the editor."),
            unit=trPx,
        )

        # Scale Headings
        self.scaleHeadings = NSwitch(self)
        self.scaleHeadings.setChecked(CONFIG.scaleHeadings)
        self.mainForm.addRow(
            self.tr("Use a larger font size for headings"),
            self.scaleHeadings,
            self.tr("Turning this off only affects the editor."),
        )

        # Single Asterisk Bold
        self.singleStarBold = NSwitch(self)
        self.singleStarBold.setChecked(CONFIG.singleStarBold)
        self.mainForm.addRow(
            self.tr("Prefer single asterisk bold"),
            self.singleStarBold,
            self.tr("This does not turn off double asterisks for bold."),
        )

        # Highlight Current Line
        self.lineHighlight = NSwitch(self)
        self.lineHighlight.setChecked(CONFIG.lineHighlight)
        self.mainForm.addRow(
            self.tr("Highlight current line"),
            self.lineHighlight,
        )

        # Show Tabs and Spaces
        self.showTabsNSpaces = NSwitch(self)
        self.showTabsNSpaces.setChecked(CONFIG.showTabsNSpaces)
        self.mainForm.addRow(
            self.tr("Show tabs and spaces"),
            self.showTabsNSpaces,
        )

        # Show Line Endings
        self.showLineEndings = NSwitch(self)
        self.showLineEndings.setChecked(CONFIG.showLineEndings)
        self.mainForm.addRow(
            self.tr("Show line endings"),
            self.showLineEndings,
        )

        # Editor Scrolling
        # ================

        title = self.tr("Editor Scrolling")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Scroll Past End
        self.scrollPastEnd = NSwitch(self)
        self.scrollPastEnd.setChecked(CONFIG.scrollPastEnd)
        self.mainForm.addRow(
            self.tr("Scroll past the end of the document"),
            self.scrollPastEnd,
            self.tr("Also centres the cursor when scrolling."),
        )

        # Typewriter Scrolling
        self.autoScroll = NSwitch(self)
        self.autoScroll.setChecked(CONFIG.autoScroll)
        self.mainForm.addRow(
            self.tr("Typewriter style scrolling when you type"),
            self.autoScroll,
            self.tr("Keeps the cursor at a fixed vertical position."),
        )

        # Typewriter Position
        self.autoScrollPos = NSpinBox(self, minVal=10, maxVal=90)
        self.autoScrollPos.setFixedNumbersWidth(2)
        self.autoScrollPos.setValue(int(CONFIG.autoScrollPos))
        self.mainForm.addRow(
            self.tr("Minimum position for Typewriter scrolling"),
            self.autoScrollPos,
            self.tr("Percentage of the editor height from the top."),
            unit="%",
        )

        # Text Highlighting
        # =================

        title = self.tr("Text Highlighting")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Dialogue Quotes
        self.dialogStyle = NComboBox(self)
        self.dialogStyle.addItem(self.tr("None"), 0)
        self.dialogStyle.addItem(self.tr("Single Quotes"), 1)
        self.dialogStyle.addItem(self.tr("Double Quotes"), 2)
        self.dialogStyle.addItem(self.tr("Both"), 3)
        self.dialogStyle.setCurrentData(CONFIG.dialogStyle, 2)
        self.mainForm.addRow(
            self.tr("Highlight dialogue"),
            self.dialogStyle,
            self.tr("Applies to the selected quote styles."),
        )

        # Open-Ended Dialogue
        self.allowOpenDial = NSwitch(self)
        self.allowOpenDial.setChecked(CONFIG.allowOpenDial)
        self.mainForm.addRow(
            self.tr("Allow open-ended dialogue"),
            self.allowOpenDial,
            self.tr("Highlight dialogue line with no closing quote."),
        )

        # Alternative Dialogue
        self.altDialogOpen = QLineEdit(self)
        self.altDialogOpen.setMaxLength(4)
        self.altDialogOpen.setFixedWidth(boxFixed)
        self.altDialogOpen.setAlignment(QtAlignCenter)
        self.altDialogOpen.setText(CONFIG.altDialogOpen)

        self.altDialogClose = QLineEdit(self)
        self.altDialogClose.setMaxLength(4)
        self.altDialogClose.setFixedWidth(boxFixed)
        self.altDialogClose.setAlignment(QtAlignCenter)
        self.altDialogClose.setText(CONFIG.altDialogClose)

        self.mainForm.addRow(
            self.tr("Alternative dialogue symbols"),
            [self.altDialogOpen, self.altDialogClose],
            self.tr("Custom highlighting of dialogue text."),
        )

        # Dialogue Line
        self.mnLineSymbols = QMenu(self)
        for symbol in nwQuotes.ALLOWED:
            label = trConst(nwQuotes.SYMBOLS.get(symbol, nwQuotes.DASHES.get(symbol, "None")))
            qtAddAction(self.mnLineSymbols, f"[ {symbol} ] {label}", data=symbol)

        self.mnLineSymbols.triggered.connect(self._insertDialogLineSymbol)

        self.dialogLine = QLineEdit(self)
        self.dialogLine.setMinimumWidth(100)
        self.dialogLine.setAlignment(QtAlignCenter)
        self.dialogLine.setText(" ".join(CONFIG.dialogLine))

        self.dialogLineButton = NIconButton(self, iSz, "add:add")
        self.dialogLineButton.setToolTip(self.tr("Select Symbol"))
        self.dialogLineButton.setMenu(self.mnLineSymbols)

        self.mainForm.addRow(
            self.tr("Dialogue line symbols"),
            self.dialogLine,
            self.tr("Lines starting with any of these symbols are dialogue."),
            button=self.dialogLineButton,
        )

        # Narrator Break
        self.narratorBreak = NComboBox(self)
        self.narratorDialog = NComboBox(self)
        for key, value in nwQuotes.DASHES.items():
            label = trConst(value)
            self.narratorBreak.addItem(label, key)
            self.narratorDialog.addItem(label, key)

        self.narratorBreak.setCurrentData(CONFIG.narratorBreak, "")
        self.narratorDialog.setCurrentData(CONFIG.narratorDialog, "")

        self.mainForm.addRow(
            self.tr("Narrator break symbol"),
            self.narratorBreak,
            self.tr("Symbol to indicate a narrator break in dialogue."),
        )
        self.mainForm.addRow(
            self.tr("Alternating dialogue/narration symbol"),
            self.narratorDialog,
            self.tr("Alternates dialogue highlighting within any paragraph."),
        )

        # Emphasis
        self.highlightEmph = NSwitch(self)
        self.highlightEmph.setChecked(CONFIG.highlightEmph)
        self.mainForm.addRow(
            self.tr("Add highlight colour to emphasised text"),
            self.highlightEmph,
            self.tr("Applies to the document editor only."),
        )

        # Dotted Codes and Modifiers
        self.dottedModCodes = NSwitch(self)
        self.dottedModCodes.setChecked(CONFIG.dottedModCodes)
        self.mainForm.addRow(
            self.tr("Add dotted lines under codes and modifiers"),
            self.dottedModCodes,
            self.tr("Applies to the document editor only."),
        )

        # Additional Spaces
        self.showMultiSpaces = NSwitch(self)
        self.showMultiSpaces.setChecked(CONFIG.showMultiSpaces)
        self.mainForm.addRow(
            self.tr("Highlight multiple spaces between words"),
            self.showMultiSpaces,
            self.tr("Applies to the document editor only."),
        )

        # Text Automation
        # ===============

        title = self.tr("Text Automation")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Auto-Replace as You Type Main Switch
        self.doReplace = NSwitch(self)
        self.doReplace.setChecked(CONFIG.doReplace)
        self.doReplace.toggled.connect(self._toggleAutoReplaceMain)
        self.mainForm.addRow(
            self.tr("Auto-replace text as you type"),
            self.doReplace,
            self.tr("Allow the editor to replace symbols as you type."),
        )

        # Auto-Replace Single Quotes
        self.doReplaceSQuote = NSwitch(self)
        self.doReplaceSQuote.setChecked(CONFIG.doReplaceSQuote)
        self.doReplaceSQuote.setEnabled(CONFIG.doReplace)
        self.mainForm.addRow(
            self.tr("Auto-replace single quotes"),
            self.doReplaceSQuote,
            self.tr("Try to guess which is an opening or a closing quote."),
        )

        # Auto-Replace Double Quotes
        self.doReplaceDQuote = NSwitch(self)
        self.doReplaceDQuote.setChecked(CONFIG.doReplaceDQuote)
        self.doReplaceDQuote.setEnabled(CONFIG.doReplace)
        self.mainForm.addRow(
            self.tr("Auto-replace double quotes"),
            self.doReplaceDQuote,
            self.tr("Try to guess which is an opening or a closing quote."),
        )

        # Auto-Replace Hyphens
        self.doReplaceDash = NSwitch(self)
        self.doReplaceDash.setChecked(CONFIG.doReplaceDash)
        self.doReplaceDash.setEnabled(CONFIG.doReplace)
        self.mainForm.addRow(
            self.tr("Auto-replace dashes"),
            self.doReplaceDash,
            self.tr("Double and triple hyphens become short and long dashes."),
        )

        # Auto-Replace Dots
        self.doReplaceDots = NSwitch(self)
        self.doReplaceDots.setChecked(CONFIG.doReplaceDots)
        self.doReplaceDots.setEnabled(CONFIG.doReplace)
        self.mainForm.addRow(
            self.tr("Auto-replace dots"),
            self.doReplaceDots,
            self.tr("Three consecutive dots become ellipsis."),
        )

        # Pad Before
        self.fmtPadBefore = QLineEdit(self)
        self.fmtPadBefore.setMaxLength(32)
        self.fmtPadBefore.setMinimumWidth(150)
        self.fmtPadBefore.setText(CONFIG.fmtPadBefore)
        self.mainForm.addRow(
            self.tr("Insert non-breaking space before"),
            self.fmtPadBefore,
            self.tr("Automatically add space before any of these symbols."),
            stretch=(2, 1),
        )

        # Pad After
        self.fmtPadAfter = QLineEdit(self)
        self.fmtPadAfter.setMaxLength(32)
        self.fmtPadAfter.setMinimumWidth(150)
        self.fmtPadAfter.setText(CONFIG.fmtPadAfter)
        self.mainForm.addRow(
            self.tr("Insert non-breaking space after"),
            self.fmtPadAfter,
            self.tr("Automatically add space after any of these symbols."),
            stretch=(2, 1),
        )

        # Use Thin Space
        self.fmtPadThin = NSwitch(self)
        self.fmtPadThin.setChecked(CONFIG.fmtPadThin)
        self.fmtPadThin.setEnabled(CONFIG.doReplace)
        self.mainForm.addRow(
            self.tr("Use thin space instead"),
            self.fmtPadThin,
            self.tr("Inserts a thin space instead of a regular space."),
        )

        # Quotation Style
        # ===============

        title = self.tr("Quotation Style")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Single Quote Style
        self.fmtSQuoteOpen = QLineEdit(self)
        self.fmtSQuoteOpen.setMaxLength(1)
        self.fmtSQuoteOpen.setReadOnly(True)
        self.fmtSQuoteOpen.setFixedWidth(boxFixed)
        self.fmtSQuoteOpen.setAlignment(QtAlignCenter)
        self.fmtSQuoteOpen.setText(CONFIG.fmtSQuoteOpen)
        self.btnSQuoteOpen = NIconButton(self, iSz, "quote:tool")
        self.btnSQuoteOpen.setToolTip(self.tr("Select Symbol"))
        self.btnSQuoteOpen.clicked.connect(self._changeSingleQuoteOpen)
        self.mainForm.addRow(
            self.tr("Single quote open style"),
            self.fmtSQuoteOpen,
            self.tr("The symbol to use for a leading single quote."),
            button=self.btnSQuoteOpen,
        )

        self.fmtSQuoteClose = QLineEdit(self)
        self.fmtSQuoteClose.setMaxLength(1)
        self.fmtSQuoteClose.setReadOnly(True)
        self.fmtSQuoteClose.setFixedWidth(boxFixed)
        self.fmtSQuoteClose.setAlignment(QtAlignCenter)
        self.fmtSQuoteClose.setText(CONFIG.fmtSQuoteClose)
        self.btnSQuoteClose = NIconButton(self, iSz, "quote:tool")
        self.btnSQuoteClose.setToolTip(self.tr("Select Symbol"))
        self.btnSQuoteClose.clicked.connect(self._changeSingleQuoteClose)
        self.mainForm.addRow(
            self.tr("Single quote close style"),
            self.fmtSQuoteClose,
            self.tr("The symbol to use for a trailing single quote."),
            button=self.btnSQuoteClose,
        )

        # Double Quote Style
        self.fmtDQuoteOpen = QLineEdit(self)
        self.fmtDQuoteOpen.setMaxLength(1)
        self.fmtDQuoteOpen.setReadOnly(True)
        self.fmtDQuoteOpen.setFixedWidth(boxFixed)
        self.fmtDQuoteOpen.setAlignment(QtAlignCenter)
        self.fmtDQuoteOpen.setText(CONFIG.fmtDQuoteOpen)
        self.btnDQuoteOpen = NIconButton(self, iSz, "quote:tool")
        self.btnDQuoteOpen.setToolTip(self.tr("Select Symbol"))
        self.btnDQuoteOpen.clicked.connect(self._changeDoubleQuoteOpen)
        self.mainForm.addRow(
            self.tr("Double quote open style"),
            self.fmtDQuoteOpen,
            self.tr("The symbol to use for a leading double quote."),
            button=self.btnDQuoteOpen,
        )

        self.fmtDQuoteClose = QLineEdit(self)
        self.fmtDQuoteClose.setMaxLength(1)
        self.fmtDQuoteClose.setReadOnly(True)
        self.fmtDQuoteClose.setFixedWidth(boxFixed)
        self.fmtDQuoteClose.setAlignment(QtAlignCenter)
        self.fmtDQuoteClose.setText(CONFIG.fmtDQuoteClose)
        self.btnDQuoteClose = NIconButton(self, iSz, "quote:tool")
        self.btnDQuoteClose.setToolTip(self.tr("Select Symbol"))
        self.btnDQuoteClose.clicked.connect(self._changeDoubleQuoteClose)
        self.mainForm.addRow(
            self.tr("Double quote close style"),
            self.fmtDQuoteClose,
            self.tr("The symbol to use for a trailing double quote."),
            button=self.btnDQuoteClose,
        )

        # Features
        # ========

        title = self.tr("Features")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Enable Vim Mode
        self.vimMode = NSwitch(self)
        self.vimMode.setChecked(CONFIG.vimMode)
        self.mainForm.addRow(
            self.tr("Enable Vim mode"),
            self.vimMode,
            self.tr("Switch the editor to use Vim editor commands."),
        )

        # AI Assistant
        # ============

        title = self.tr("AI Assistant")
        section += 1
        self.sidebar.addButton(title, section)
        self.mainForm.addGroupLabel(title, section)

        # Enable AI
        self.aiEnabled = NSwitch(self)
        self.aiEnabled.setChecked(CONFIG.aiEnabled)
        self.mainForm.addRow(
            self.tr("Enable AI Assistant"),
            self.aiEnabled,
            self.tr("Turn on the AI sidebar."),
        )

        # AI Provider
        self.aiProvider = NComboBox(self)
        self.aiProvider.addItems(["Local / Llama.cpp", "OpenAI", "Anthropic", "Google Gemini"])
        self.aiProvider.setCurrentText(CONFIG.aiProvider)
        self.mainForm.addRow(
            self.tr("AI Provider"),
            self.aiProvider,
            self.tr("Select the AI service provider."),
        )

        # API Keys (only shown for respective providers)
        self.aiApiKeyLocal = QLineEdit(self)
        self.aiApiKeyLocal.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyLocal.setPlaceholderText(self.tr("Local API Key (sk-...)"))
        self.aiApiKeyLocal.hide()
        if getattr(CONFIG, "aiApiKeyLocal", ""):
            self.aiApiKeyLocal.setText(CONFIG.aiApiKeyLocal)
        self.mainForm.addRow(self.tr("Local API Key"), self.aiApiKeyLocal, self.tr("Your API key for local providers."))

        self.aiApiKeyOpenAI = QLineEdit(self)
        self.aiApiKeyOpenAI.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyOpenAI.setPlaceholderText(self.tr("OpenAI API Key (sk-...)"))
        self.aiApiKeyOpenAI.hide()
        if getattr(CONFIG, "aiApiKeyOpenAI", ""):
            self.aiApiKeyOpenAI.setText(CONFIG.aiApiKeyOpenAI)
        self.mainForm.addRow(self.tr("OpenAI API Key"), self.aiApiKeyOpenAI, self.tr("Your API key for OpenAI."))

        self.aiApiKeyAnthropic = QLineEdit(self)
        self.aiApiKeyAnthropic.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyAnthropic.setPlaceholderText(self.tr("Anthropic API Key (sk-ant-...)"))
        self.aiApiKeyAnthropic.hide()
        if getattr(CONFIG, "aiApiKeyAnthropic", ""):
            self.aiApiKeyAnthropic.setText(CONFIG.aiApiKeyAnthropic)
        self.mainForm.addRow(
            self.tr("Anthropic API Key"), self.aiApiKeyAnthropic, self.tr("Your API key for Anthropic.")
        )

        self.aiApiKeyGemini = QLineEdit(self)
        self.aiApiKeyGemini.setEchoMode(QLineEdit.EchoMode.Password)
        self.aiApiKeyGemini.setPlaceholderText(self.tr("Gemini API Key (AIza...)"))
        self.aiApiKeyGemini.hide()
        if getattr(CONFIG, "aiApiKeyGemini", ""):
            self.aiApiKeyGemini.setText(CONFIG.aiApiKeyGemini)
        self.mainForm.addRow(self.tr("Gemini API Key"), self.aiApiKeyGemini, self.tr("Your API key for Google Gemini."))

        # Engine Path
        self.aiEndpoint = QLineEdit(self)
        self.aiEndpoint.setText(CONFIG.aiEndpoint)
        self.mainForm.addRow(
            self.tr("AI Server Endpoint"),
            self.aiEndpoint,
            self.tr("Endpoint URL (e.g. http://127.0.0.1:8080)"),
        )

        # Toggle API Key visibility based on provider.
        # Note: the initial visibility pass is deferred until after
        # self.mainForm.finalise() below, since the form layout (needed
        # for labelForField) does not exist yet during buildForm().
        self.aiProvider.currentTextChanged.connect(self._toggle_api_fields)

        # Model Selection
        modelLayout = QHBoxLayout()
        self.aiModelCombo = NComboBox(self)
        self.aiModelCombo.setMinimumWidth(200)
        self.aiModelCombo.setEditable(True)
        self.aiModelCombo.addItem(CONFIG.aiModel)
        self.aiModelCombo.setCurrentText(CONFIG.aiModel)

        self.refreshModelsBtn = QPushButton("Refresh", self)
        self.refreshModelsBtn.clicked.connect(self._refreshAiModels)

        modelLayout.addWidget(self.aiModelCombo, 1)
        modelLayout.addWidget(self.refreshModelsBtn)

        modelWidget = QWidget(self)
        modelWidget.setLayout(modelLayout)
        modelLayout.setContentsMargins(0, 0, 0, 0)

        self.mainForm.addRow(
            self.tr("Model"),
            modelWidget,
            self.tr("Query the endpoint and select a model."),
        )

        # Context Size
        self.aiContextSize = NSpinBox(self)
        self.aiContextSize.setRange(512, 128000)
        self.aiContextSize.setSingleStep(1024)
        self.aiContextSize.setValue(CONFIG.aiContextSize)
        self.mainForm.addRow(
            self.tr("Context Size"),
            self.aiContextSize,
            self.tr("Context window size (-c parameter)."),
        )

        # Temperature
        self.aiTemperature = NDoubleSpinBox(self)
        self.aiTemperature.setRange(0.0, 2.0)
        self.aiTemperature.setSingleStep(0.1)
        self.aiTemperature.setValue(CONFIG.aiTemperature)
        self.mainForm.addRow(
            self.tr("Temperature"),
            self.aiTemperature,
            self.tr("Higher values make output more random."),
        )

        # Thinking
        self.aiThinkingCombo = NComboBox(self)
        self.aiThinkingCombo.addItems(["Off", "low", "med", "high", "xhigh"])
        self.aiThinkingCombo.setCurrentText(getattr(CONFIG, "aiThinking", "Off"))
        self.mainForm.addRow(
            self.tr("Thinking Variable"),
            self.aiThinkingCombo,
            self.tr("Thinking/reasoning effort for supported models."),
        )

        # Co-author
        self.aiPromptCoAuthor = QTextEdit(self)
        self.aiPromptCoAuthor.setFixedHeight(60)
        self.aiPromptCoAuthor.setPlainText(CONFIG.aiPromptCoAuthor)
        self.mainForm.addRow(
            self.tr("Co-author Role"), self.aiPromptCoAuthor, self.tr("Prompt for the Co-author specialization.")
        )

        # Editor
        self.aiPromptEditor = QTextEdit(self)
        self.aiPromptEditor.setFixedHeight(60)
        self.aiPromptEditor.setPlainText(CONFIG.aiPromptEditor)
        self.mainForm.addRow(
            self.tr("Editor Role"), self.aiPromptEditor, self.tr("Prompt for the Editor specialization.")
        )

        # Publisher
        self.aiPromptPublisher = QTextEdit(self)
        self.aiPromptPublisher.setFixedHeight(60)
        self.aiPromptPublisher.setPlainText(CONFIG.aiPromptPublisher)
        self.mainForm.addRow(
            self.tr("Publisher Role"), self.aiPromptPublisher, self.tr("Prompt for the Publisher specialization.")
        )

        # Reader
        self.aiPromptReader = QTextEdit(self)
        self.aiPromptReader.setFixedHeight(60)
        self.aiPromptReader.setPlainText(CONFIG.aiPromptReader)
        self.mainForm.addRow(
            self.tr("Reader Role"), self.aiPromptReader, self.tr("Prompt for the Reader specialization.")
        )

        self.mainForm.finalise()
        self._toggle_api_fields()
        self.sidebar.setSelected(1)

    ##
    #  Events
    ##

    def closeEvent(self, event: QCloseEvent) -> None:
        """Capture the close event and perform cleanup."""
        logger.debug("Close: GuiPreferences")
        self._saveWindowSize()
        event.accept()
        self.softDelete()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Overload keyPressEvent and only accept escape. The main
        purpose here is to prevent Enter/Return from closing the dialog
        as it is used for the search box.
        """
        if event.matches(QKeySequence.StandardKey.Cancel):
            self.close()
        event.ignore()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _refreshAiModels(self) -> None:
        """Fetch the model list using the hardcoded base URLs for each provider.

        The endpoint field is only used for Local / Llama.cpp.
        """
        import requests

        provider = self.aiProvider.currentText()
        if provider == "OpenAI":
            api_key = self.aiApiKeyOpenAI.text().strip()
        elif provider == "Anthropic":
            api_key = self.aiApiKeyAnthropic.text().strip()
        elif provider == "Google Gemini":
            api_key = self.aiApiKeyGemini.text().strip()
        else:
            api_key = ""

        if provider == "Local / Llama.cpp":
            endpoint = self.aiEndpoint.text().strip().rstrip("/")
            if not endpoint:
                return
            url = f"{endpoint}/models" if endpoint.endswith("/v1") else f"{endpoint}/v1/models"
            headers = {}
        elif provider == "OpenAI":
            if not api_key:
                return
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
        elif provider == "Anthropic":
            if not api_key:
                return
            url = "https://api.anthropic.com/v1/models"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            }
        elif provider == "Google Gemini":
            if not api_key:
                return
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            headers = {}
        else:
            return

        try:
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            if provider == "Google Gemini":
                # Gemini returns {"models": [{"name": "models/xxx", ...}]}
                names = []
                for m in data.get("models", []):
                    name = m.get("name", "")
                    if not name.startswith("models/"):
                        continue
                    # Only list models that can generate content
                    if "generateContent" not in m.get("supportedGenerationMethods", []):
                        continue
                    names.append(name[len("models/") :])
            else:
                names = [m.get("id", "") for m in data.get("data", [])]

            self.aiModelCombo.blockSignals(True)
            current = CONFIG.aiModel
            self.aiModelCombo.clear()
            for name in names:
                self.aiModelCombo.addItem(name)
            idx = self.aiModelCombo.findText(current)
            if idx >= 0:
                self.aiModelCombo.setCurrentIndex(idx)
            elif names:
                self.aiModelCombo.setCurrentIndex(0)
            else:
                self.aiModelCombo.addItem(current)
            self.aiModelCombo.blockSignals(False)
        except Exception as e:
            logger.error(f"Failed to fetch models: {e}")

    @pyqtSlot()
    def _toggle_api_fields(self) -> None:
        """Show/hide provider-specific fields based on the selected provider.

        The endpoint, context size, and temperature are local-only options;
        cloud providers use hardcoded base URLs and their own defaults.
        """
        provider = self.aiProvider.currentText()
        is_local = provider == "Local / Llama.cpp"

        def set_row_visible(widget, visible: bool) -> None:
            widget.setVisible(visible)
            from PyQt6.QtWidgets import QLabel

            for label in self.mainForm.findChildren(QLabel):
                if label.buddy() == widget:
                    label.setVisible(visible)

        # Show the correct API key field
        set_row_visible(self.aiApiKeyLocal, is_local)
        set_row_visible(self.aiApiKeyOpenAI, provider == "OpenAI")
        set_row_visible(self.aiApiKeyAnthropic, provider == "Anthropic")
        set_row_visible(self.aiApiKeyGemini, provider == "Google Gemini")

        # Endpoint, context size, and temperature apply to Local only
        set_row_visible(self.aiEndpoint, is_local)
        set_row_visible(self.aiContextSize, is_local)
        set_row_visible(self.aiTemperature, is_local)
        set_row_visible(self.aiThinkingCombo, is_local)

    @pyqtSlot(int)
    def _sidebarClicked(self, section: int) -> None:
        """Process a user request to switch page."""
        self.mainForm.scrollToSection(section)

    @pyqtSlot()
    def _gotoSearch(self) -> None:
        """Go to the setting indicated by the search text."""
        self.mainForm.scrollToLabel(self.searchText.text().strip())

    @pyqtSlot()
    def _selectGuiFont(self) -> None:
        """Open the QFontDialog and set a font for the font style."""
        font, status = SHARED.getFont(self._guiFont, self.nativeFont.isChecked())
        if status:
            self.guiFont.setText(describeFont(font))
            self.guiFont.setCursorPosition(0)
            self._guiFont = font

    @pyqtSlot()
    def _selectTextFont(self) -> None:
        """Open the QFontDialog and set a font for the font style."""
        font, status = SHARED.getFont(self._textFont, self.nativeFont.isChecked())
        if status:
            self.textFont.setText(describeFont(font))
            self.textFont.setCursorPosition(0)
            self._textFont = font

    @pyqtSlot()
    def _backupFolder(self) -> None:
        """Open a dialog to select the backup folder."""
        if path := QFileDialog.getExistingDirectory(
            self,
            self.tr("Backup Directory"),
            str(self.backupPath) or "",
            options=QFileDialog.Option.ShowDirsOnly,
        ):
            self.backupPath = path
            self.mainForm.setHelpText("backupPath", self.tr("Path: {0}").format(path))

    @pyqtSlot(bool)
    def _toggledBackupOnClose(self, state: bool) -> None:
        """Toggle switch that depends on the backup on close switch."""
        self.askBeforeBackup.setEnabled(state)

    @pyqtSlot(QAction)
    def _insertDialogLineSymbol(self, action: QAction) -> None:
        """Insert a symbol in the dialogue line box."""
        current = self.dialogLine.text()
        values = processDialogSymbols(f"{current} {action.data()}")
        self.dialogLine.setText(" ".join(values))

    @pyqtSlot(bool)
    def _toggleAutoReplaceMain(self, state: bool) -> None:
        """Toggle switches controlled by the auto replace switch."""
        self.doReplaceSQuote.setEnabled(state)
        self.doReplaceDQuote.setEnabled(state)
        self.doReplaceDash.setEnabled(state)
        self.doReplaceDots.setEnabled(state)
        self.fmtPadThin.setEnabled(state)

    @pyqtSlot()
    def _changeSingleQuoteOpen(self) -> None:
        """Change single quote open style."""
        quote, status = GuiQuoteSelect.getQuote(self, current=self.fmtSQuoteOpen.text())
        if status:
            self.fmtSQuoteOpen.setText(quote)

    @pyqtSlot()
    def _changeSingleQuoteClose(self) -> None:
        """Change single quote close style."""
        quote, status = GuiQuoteSelect.getQuote(self, current=self.fmtSQuoteClose.text())
        if status:
            self.fmtSQuoteClose.setText(quote)

    @pyqtSlot()
    def _changeDoubleQuoteOpen(self) -> None:
        """Change double quote open style."""
        quote, status = GuiQuoteSelect.getQuote(self, current=self.fmtDQuoteOpen.text())
        if status:
            self.fmtDQuoteOpen.setText(quote)

    @pyqtSlot()
    def _changeDoubleQuoteClose(self) -> None:
        """Change double quote close style."""
        quote, status = GuiQuoteSelect.getQuote(self, current=self.fmtDQuoteClose.text())
        if status:
            self.fmtDQuoteClose.setText(quote)

    ##
    #  Internal Functions
    ##

    def _saveWindowSize(self) -> None:
        """Save the dialog window size."""
        CONFIG.setPreferencesWinSize(self.geometry())

    def _doSave(self) -> None:
        """Save the values set in the form."""
        updateTheme = False
        needsRestart = False
        updateSyntax = False
        updateSpelling = False
        updateVimMode = False
        refreshTree = False
        initEditor = False
        initViewer = False
        initViewport = False

        # Appearance
        guiLocale = self.guiLocale.currentData()
        lightTheme = self.lightTheme.currentData()
        darkTheme = self.darkTheme.currentData()
        iconTheme = self.iconTheme.currentData()
        hideVScroll = self.hideVScroll.isChecked()
        hideHScroll = self.hideHScroll.isChecked()
        useCharCount = self.useCharCount.isChecked()

        updateTheme |= CONFIG.lightTheme != lightTheme
        updateTheme |= CONFIG.darkTheme != darkTheme
        updateTheme |= CONFIG.iconTheme != iconTheme
        needsRestart |= CONFIG.guiLocale != guiLocale
        needsRestart |= CONFIG.guiFont != self._guiFont
        refreshTree |= CONFIG.useCharCount != useCharCount
        updateSyntax |= CONFIG.lightTheme != lightTheme
        updateSyntax |= CONFIG.darkTheme != darkTheme
        initViewport |= CONFIG.hideVScroll != hideVScroll
        initViewport |= CONFIG.hideHScroll != hideHScroll

        CONFIG.guiLocale = guiLocale
        CONFIG.lightTheme = lightTheme
        CONFIG.darkTheme = darkTheme
        CONFIG.iconTheme = iconTheme
        CONFIG.hideVScroll = hideVScroll
        CONFIG.hideHScroll = hideHScroll
        CONFIG.nativeFont = self.nativeFont.isChecked()
        CONFIG.setGuiFont(self._guiFont)
        CONFIG.setPrimaryCount(useCharCount)

        # Document Style
        textFont = self._textFont

        initEditor |= CONFIG.textFont != textFont
        initViewer |= CONFIG.textFont != textFont

        CONFIG.showFullPath = self.showFullPath.isChecked()
        CONFIG.incNotesWCount = self.incNotesWCount.isChecked()
        CONFIG.setTextFont(textFont)

        # Project View
        iconColTree = self.iconColTree.currentData()
        iconColDocs = self.iconColDocs.isChecked()
        emphLabels = self.emphLabels.isChecked()

        updateTheme |= CONFIG.iconColTree != iconColTree
        updateTheme |= CONFIG.iconColDocs != iconColDocs
        refreshTree |= CONFIG.emphLabels != emphLabels

        CONFIG.iconColTree = iconColTree
        CONFIG.iconColDocs = iconColDocs
        CONFIG.emphLabels = emphLabels

        # Behaviour
        CONFIG.autoSaveDoc = self.autoSaveDoc.value()
        CONFIG.autoSaveProj = self.autoSaveProj.value()
        CONFIG.askBeforeExit = self.askBeforeExit.isChecked()
        CONFIG.moveMainWin = self.moveMainWin.isChecked()

        # Project Backup
        CONFIG.setBackupPath(self.backupPath)
        CONFIG.backupInterval = self.backupInterval.currentData()
        CONFIG.backupOnClose = self.backupOnClose.isChecked()
        CONFIG.askBeforeBackup = self.askBeforeBackup.isChecked()

        # Session Timer
        CONFIG.stopWhenIdle = self.stopWhenIdle.isChecked()
        CONFIG.userIdleTime = round(self.userIdleTime.value() * 60)

        # Text Flow
        textWidth = self.textWidth.value()
        focusWidth = self.focusWidth.value()
        doJustify = self.doJustify.isChecked()
        textMargin = self.textMargin.value()
        tabWidth = self.tabWidth.value()
        lineHeight = self.lineHeight.value()

        initEditor |= CONFIG.doJustify != doJustify
        initEditor |= CONFIG.tabWidth != tabWidth
        initEditor |= CONFIG.lineHeight != lineHeight
        initViewer |= CONFIG.doJustify != doJustify
        initViewer |= CONFIG.tabWidth != tabWidth
        initViewer |= CONFIG.lineHeight != lineHeight
        initViewport |= CONFIG.textWidth != textWidth
        initViewport |= CONFIG.focusWidth != focusWidth
        initViewport |= CONFIG.textMargin != textMargin

        CONFIG.textWidth = textWidth
        CONFIG.focusWidth = focusWidth
        CONFIG.hideFocusFooter = self.hideFocusFooter.isChecked()
        CONFIG.doJustify = doJustify
        CONFIG.textMargin = textMargin
        CONFIG.tabWidth = tabWidth
        CONFIG.lineHeight = lineHeight

        # Text Editing
        spellLanguage = self.spellLanguage.currentData()
        cursorWidth = self.cursorWidth.value()
        scaleHeadings = self.scaleHeadings.isChecked()
        singleStarBold = self.singleStarBold.isChecked()
        lineHighlight = self.lineHighlight.isChecked()
        showTabsNSpaces = self.showTabsNSpaces.isChecked()
        showLineEndings = self.showLineEndings.isChecked()

        updateSyntax |= CONFIG.scaleHeadings != scaleHeadings
        updateSyntax |= CONFIG.singleStarBold != singleStarBold
        updateSyntax |= CONFIG.lineHighlight != lineHighlight
        initEditor |= CONFIG.cursorWidth != cursorWidth
        initEditor |= CONFIG.showTabsNSpaces != showTabsNSpaces
        initEditor |= CONFIG.showLineEndings != showLineEndings
        updateSpelling |= CONFIG.spellLanguage != spellLanguage

        CONFIG.spellLanguage = spellLanguage
        CONFIG.autoSelect = self.autoSelect.isChecked()
        CONFIG.cursorWidth = cursorWidth
        CONFIG.scaleHeadings = scaleHeadings
        CONFIG.singleStarBold = singleStarBold
        CONFIG.lineHighlight = lineHighlight
        CONFIG.showTabsNSpaces = showTabsNSpaces
        CONFIG.showLineEndings = showLineEndings

        # Editor Scrolling
        scrollPastEnd = self.scrollPastEnd.isChecked()

        initViewport |= CONFIG.scrollPastEnd != scrollPastEnd

        CONFIG.autoScroll = self.autoScroll.isChecked()  # Read on every keyPressEvent
        CONFIG.autoScrollPos = self.autoScrollPos.value()  # Read on every keyPressEvent
        CONFIG.scrollPastEnd = scrollPastEnd

        # Text Highlighting
        dialogueStyle = self.dialogStyle.currentData()
        allowOpenDial = self.allowOpenDial.isChecked()
        dialogueLine = processDialogSymbols(self.dialogLine.text())
        narratorBreak = self.narratorBreak.currentData()
        narratorDialog = self.narratorDialog.currentData()
        altDialogOpen = compact(self.altDialogOpen.text())
        altDialogClose = compact(self.altDialogClose.text())
        highlightEmph = self.highlightEmph.isChecked()
        dottedModCodes = self.dottedModCodes.isChecked()
        showMultiSpaces = self.showMultiSpaces.isChecked()

        updateSyntax |= CONFIG.dialogStyle != dialogueStyle
        updateSyntax |= CONFIG.allowOpenDial != allowOpenDial
        updateSyntax |= CONFIG.dialogLine != dialogueLine
        updateSyntax |= CONFIG.narratorBreak != narratorBreak
        updateSyntax |= CONFIG.narratorDialog != narratorDialog
        updateSyntax |= CONFIG.altDialogOpen != altDialogOpen
        updateSyntax |= CONFIG.altDialogClose != altDialogClose
        updateSyntax |= CONFIG.highlightEmph != highlightEmph
        updateSyntax |= CONFIG.dottedModCodes != dottedModCodes
        initEditor |= CONFIG.showMultiSpaces != showMultiSpaces

        CONFIG.dialogStyle = dialogueStyle
        CONFIG.allowOpenDial = allowOpenDial
        CONFIG.dialogLine = dialogueLine
        CONFIG.narratorBreak = narratorBreak
        CONFIG.narratorDialog = narratorDialog
        CONFIG.altDialogOpen = altDialogOpen
        CONFIG.altDialogClose = altDialogClose
        CONFIG.highlightEmph = highlightEmph
        CONFIG.dottedModCodes = dottedModCodes
        CONFIG.showMultiSpaces = showMultiSpaces

        # Text Automation
        CONFIG.doReplace = self.doReplace.isChecked()
        CONFIG.doReplaceSQuote = self.doReplaceSQuote.isChecked()
        CONFIG.doReplaceDQuote = self.doReplaceDQuote.isChecked()
        CONFIG.doReplaceDash = self.doReplaceDash.isChecked()
        CONFIG.doReplaceDots = self.doReplaceDots.isChecked()
        CONFIG.fmtPadBefore = uniqueCompact(self.fmtPadBefore.text())
        CONFIG.fmtPadAfter = uniqueCompact(self.fmtPadAfter.text())
        CONFIG.fmtPadThin = self.fmtPadThin.isChecked()

        # Quotation Style
        CONFIG.fmtSQuoteOpen = self.fmtSQuoteOpen.text()
        CONFIG.fmtSQuoteClose = self.fmtSQuoteClose.text()
        CONFIG.fmtDQuoteOpen = self.fmtDQuoteOpen.text()
        CONFIG.fmtDQuoteClose = self.fmtDQuoteClose.text()

        # Features
        vimMode = self.vimMode.isChecked()
        if vimMode and not CONFIG.vimMode:
            vimMode = SHARED.question([
                self.tr("Are you sure you want to enable Vim mode?"),
                self.tr("This changes how the editor accepts input."),
            ])
        self.vimMode.setChecked(vimMode)

        updateVimMode |= CONFIG.vimMode != vimMode

        CONFIG.vimMode = vimMode
        CONFIG.aiEnabled = self.aiEnabled.isChecked()
        CONFIG.aiProvider = self.aiProvider.currentText()
        CONFIG.aiApiKeyLocal = self.aiApiKeyLocal.text()
        CONFIG.aiApiKeyOpenAI = self.aiApiKeyOpenAI.text()
        CONFIG.aiApiKeyAnthropic = self.aiApiKeyAnthropic.text()
        CONFIG.aiApiKeyGemini = self.aiApiKeyGemini.text()
        CONFIG.aiEndpoint = self.aiEndpoint.text()
        CONFIG.aiModel = self.aiModelCombo.currentText()
        CONFIG.aiContextSize = self.aiContextSize.value()
        CONFIG.aiTemperature = self.aiTemperature.value()
        CONFIG.aiThinking = self.aiThinkingCombo.currentText()
        CONFIG.aiPromptCoAuthor = self.aiPromptCoAuthor.toPlainText().strip()
        CONFIG.aiPromptEditor = self.aiPromptEditor.toPlainText().strip()
        CONFIG.aiPromptPublisher = self.aiPromptPublisher.toPlainText().strip()
        CONFIG.aiPromptReader = self.aiPromptReader.toPlainText().strip()

        # Finalise
        CONFIG.saveConfig()
        self.newPreferencesReady.emit(
            GuiNeedsUpdate(
                restart=needsRestart,
                tree=refreshTree,
                theme=updateTheme,
                syntax=updateSyntax,
                spelling=updateSpelling,
                vim=updateVimMode,
                editor=initEditor,
                viewer=initViewer,
                viewport=initViewport,
            )
        )

        self.close()
