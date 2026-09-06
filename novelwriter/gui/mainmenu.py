"""
novelWriter - GUI Main Menu
===========================

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

import logging

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenuBar

from novelwriter import CONFIG, SHARED
from novelwriter.common import openExternalPath, qtAddAction, qtAddMenu, qtLambda, qtWeakLambda
from novelwriter.constants import (
    nwConst,
    nwKeyWords,
    nwLabels,
    nwShortcode,
    nwStats,
    nwStyles,
    nwUnicode,
    trConst,
    trStats,
)
from novelwriter.enum import nwDocAction, nwDocInsert, nwFocus, nwView
from novelwriter.extensions.eventfilters import StatusTipFilter
from novelwriter.types import QtWidgetShortcut

if TYPE_CHECKING:
    from novelwriter.guimain import GuiMain

logger = logging.getLogger(__name__)


class GuiMainMenu(QMenuBar):
    """The GUI main menu. All menu actions are defined here with the
    main menu as the owner. Each widget that need them elsewhere need to
    add them from this class.
    """

    requestDocAction = pyqtSignal(nwDocAction)
    requestDocInsert = pyqtSignal(nwDocInsert)
    requestDocInsertText = pyqtSignal(str)
    requestDocKeyWordInsert = pyqtSignal(str)
    requestFocusChange = pyqtSignal(nwFocus)
    requestViewChange = pyqtSignal(nwView)

    def __init__(self, mainGui: GuiMain) -> None:
        super().__init__(parent=mainGui)

        logger.debug("Create: GuiMainMenu")

        self.mainGui = mainGui

        # Build Menu
        self._buildProjectMenu()
        self._buildDocumentMenu()
        self._buildEditMenu()
        self._buildViewMenu()
        self._buildInsertMenu()
        self._buildFormatMenu()
        self._buildSearchMenu()
        self._buildToolsMenu()
        self._buildHelpMenu()

        self.installEventFilter(StatusTipFilter(mainGui))

        logger.debug("Ready: GuiMainMenu")

    ##
    #  Public Slots
    ##

    @pyqtSlot(bool)
    def setSpellCheckState(self, state: bool) -> None:
        """Forward spell check check state to its action."""
        self.aSpellCheck.setChecked(state)

    @pyqtSlot()
    def setSelectedProjectSpellCheckLanguage(self) -> None:
        """Set the selected spell check language in the menu to match
        the project's setting.
        """
        for action in self.mSelectLanguage.actions():
            action.setChecked(action.data() == (SHARED.project.data.spellLang or "None"))

    @pyqtSlot()
    def updateSpellCheckLanguages(self) -> None:
        """Update the list of available spell check languages."""
        self.mSelectLanguage.clear()
        languages = SHARED.spelling.listDictionaries()
        languages.insert(0, ("None", self.tr("Default")))
        for tag, language in languages:
            aSpell = QAction(self.mSelectLanguage)
            aSpell.setText(language)
            aSpell.setCheckable(True)
            aSpell.setData(tag)
            aSpell.triggered.connect(qtWeakLambda(self._changeSpelling, tag))
            self.mSelectLanguage.addAction(aSpell)
        self.setSelectedProjectSpellCheckLanguage()

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _toggleSpellCheck(self) -> None:
        """Toggle spell checking. The active status of the spell check
        flag is handled by the document editor class, so we make no
        decision, just pass a None to the function and let it decide.
        """
        self.mainGui.docEditor.toggleSpellCheck(None)

    @pyqtSlot()
    def _openUserManualFile(self) -> None:
        """Open the documentation in PDF format."""
        if isinstance(CONFIG.pdfDocs, Path):
            openExternalPath(CONFIG.pdfDocs)

    @pyqtSlot(str)
    def _changeSpelling(self, language: str) -> None:
        """Change the spell check language."""
        SHARED.project.data.setSpellLang(language)
        SHARED.updateSpellCheckLanguage()
        self.setSelectedProjectSpellCheckLanguage()

    @pyqtSlot(nwDocAction)
    def _emitDocAction(self, action: nwDocAction) -> None:
        """Forward a document action request."""
        self.requestDocAction.emit(action)

    @pyqtSlot(nwDocInsert)
    def _emitDocInsert(self, insert: nwDocInsert) -> None:
        """Forward a document insert request."""
        self.requestDocInsert.emit(insert)

    @pyqtSlot(str)
    def _emitDocInsertText(self, text: str) -> None:
        """Forward a document text insert request."""
        self.requestDocInsertText.emit(text)

    @pyqtSlot(str)
    def _emitDocKeyWordInsert(self, key: str) -> None:
        """Forward a document keyword insert request."""
        self.requestDocKeyWordInsert.emit(key)

    @pyqtSlot(nwFocus)
    def _emitFocusChange(self, focus: nwFocus) -> None:
        """Forward a focus change request."""
        self.requestFocusChange.emit(focus)

    @pyqtSlot(nwView)
    def _emitViewChange(self, view: nwView) -> None:
        """Forward a view change request."""
        self.requestViewChange.emit(view)

    ##
    #  Internal Functions
    ##

    def _buildProjectMenu(self) -> None:
        """Assemble the Project menu."""
        # Project
        self.projMenu = qtAddMenu(self, self.tr("&Project"))

        # Project > Create or Open Project
        self.aOpenProject = qtAddAction(self.projMenu, self.tr("Create or Open Project"))
        self.aOpenProject.setShortcut("Ctrl+Shift+O")
        self.aOpenProject.triggered.connect(self.mainGui.showWelcomeDialog)

        # Project > Save Project
        self.aSaveProject = qtAddAction(self.projMenu, self.tr("Save Project"))
        self.aSaveProject.setShortcut("Ctrl+Shift+S")
        self.aSaveProject.triggered.connect(qtWeakLambda(self.mainGui.saveProject))
        self.mainGui.addAction(self.aSaveProject)

        # Project > Close Project
        self.aCloseProject = qtAddAction(self.projMenu, self.tr("Close Project"))
        self.aCloseProject.setShortcut("Ctrl+Shift+W")
        self.aCloseProject.triggered.connect(qtWeakLambda(self.mainGui.closeProject, False))

        # Project > Separator
        self.projMenu.addSeparator()

        # Project > Project Settings
        self.aProjectSettings = qtAddAction(self.projMenu, self.tr("Project Settings"))
        self.aProjectSettings.setShortcut("Ctrl+Shift+,")
        self.aProjectSettings.triggered.connect(self.mainGui.showProjectSettingsDialog)

        # Project > Novel Details
        self.aNovelDetails = qtAddAction(self.projMenu, self.tr("Novel Details"))
        self.aNovelDetails.setShortcut("Shift+F6")
        self.aNovelDetails.triggered.connect(self.mainGui.showNovelDetailsDialog)

        # Project > Separator
        self.projMenu.addSeparator()

        # Project > Edit
        self.aRenameItem = qtAddAction(self.projMenu, self.tr("Rename Item"))
        self.aRenameItem.setShortcut("F2")

        # Project > Delete
        self.aDeleteItem = qtAddAction(self.projMenu, self.tr("Delete Item"))
        self.aDeleteItem.setShortcut("Del")
        self.aDeleteItem.setShortcutContext(QtWidgetShortcut)

        # Project > Empty Trash
        self.aEmptyTrash = qtAddAction(self.projMenu, self.tr("Empty Trash"))

        self.mainGui.projView.connectMenuActions(self.aRenameItem, self.aDeleteItem, self.aEmptyTrash)

        # Project > Separator
        self.projMenu.addSeparator()

        # Project > Exit
        self.aExitNW = qtAddAction(self.projMenu, self.tr("Exit"))
        self.aExitNW.setShortcut("Ctrl+Q")
        self.aExitNW.setMenuRole(QAction.MenuRole.QuitRole)
        self.aExitNW.triggered.connect(qtWeakLambda(self.mainGui.closeMain))
        self.mainGui.addAction(self.aExitNW)

    def _buildDocumentMenu(self) -> None:
        """Assemble the Document menu."""
        # Document
        self.docuMenu = qtAddMenu(self, self.tr("&Document"))

        # Document > Open
        self.aOpenDoc = qtAddAction(self.docuMenu, self.tr("Open Document"))
        self.aOpenDoc.setShortcut("Ctrl+O")
        self.aOpenDoc.triggered.connect(self.mainGui.openSelectedItem)

        # Document > Save
        self.aSaveDoc = qtAddAction(self.docuMenu, self.tr("Save Document"))
        self.aSaveDoc.setShortcut("Ctrl+S")
        self.aSaveDoc.triggered.connect(self.mainGui.forceSaveDocument)
        self.mainGui.addAction(self.aSaveDoc)

        # Document > Close
        self.aCloseDoc = qtAddAction(self.docuMenu, self.tr("Close Document"))
        self.aCloseDoc.setShortcut("Ctrl+W")
        self.aCloseDoc.triggered.connect(self.mainGui.closeDocEditor)
        self.mainGui.addAction(self.aCloseDoc)

        # Document > Separator
        self.docuMenu.addSeparator()

        # Document > Preview
        self.aViewDoc = qtAddAction(self.docuMenu, self.tr("View Document"))
        self.aViewDoc.setShortcut("Ctrl+R")
        self.aViewDoc.triggered.connect(qtWeakLambda(self.mainGui.viewDocument, None))

        # Document > Close Preview
        self.aCloseView = qtAddAction(self.docuMenu, self.tr("Close Document View"))
        self.aCloseView.setShortcut("Ctrl+Shift+R")
        self.aCloseView.triggered.connect(self.mainGui.closeDocViewer)

        # Document > Separator
        self.docuMenu.addSeparator()

        # Document > Show File Details
        self.aFileDetails = qtAddAction(self.docuMenu, self.tr("Show File Details"))
        self.aFileDetails.triggered.connect(qtWeakLambda(self.mainGui.docEditor.revealLocation))

        # Document > Import From File
        self.aImportFile = qtAddAction(self.docuMenu, self.tr("Import Text from File"))
        self.aImportFile.triggered.connect(qtWeakLambda(self.mainGui.importDocument))

        # Document > Move Text
        self.aMoveText = qtAddAction(self.docuMenu, self.tr("Move Text to New Document"))
        self.aMoveText.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.MOVE_TEXT))

    def _buildEditMenu(self) -> None:
        """Assemble the Edit menu."""
        # Edit
        self.editMenu = qtAddMenu(self, self.tr("&Edit"))

        # Edit > Undo
        self.aEditUndo = qtAddAction(self.editMenu, self.tr("Undo"))
        self.aEditUndo.setShortcut("Ctrl+Z")
        self.aEditUndo.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.UNDO))
        self.mainGui.addAction(self.aEditUndo)

        # Edit > Redo
        self.aEditRedo = qtAddAction(self.editMenu, self.tr("Redo"))
        self.aEditRedo.setShortcut("Ctrl+Y")
        self.aEditRedo.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.REDO))
        self.mainGui.addAction(self.aEditRedo)

        # Edit > Separator
        self.editMenu.addSeparator()

        # Edit > Cut
        self.aEditCut = qtAddAction(self.editMenu, self.tr("Cut"))
        self.aEditCut.setShortcut("Ctrl+X")
        self.aEditCut.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.CUT))
        self.mainGui.addAction(self.aEditCut)

        # Edit > Copy
        self.aEditCopy = qtAddAction(self.editMenu, self.tr("Copy"))
        self.aEditCopy.setShortcut("Ctrl+C")
        self.aEditCopy.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.COPY))
        self.mainGui.addAction(self.aEditCopy)

        # Edit > Paste
        self.aEditPaste = qtAddAction(self.editMenu, self.tr("Paste"))
        self.aEditPaste.setShortcut("Ctrl+V")
        self.aEditPaste.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.PASTE))
        self.mainGui.addAction(self.aEditPaste)

        # Edit > Separator
        self.editMenu.addSeparator()

        # Edit > Select All
        self.aSelectAll = qtAddAction(self.editMenu, self.tr("Select All"))
        self.aSelectAll.setShortcut("Ctrl+A")
        self.aSelectAll.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SEL_ALL))
        self.mainGui.addAction(self.aSelectAll)

        # Edit > Select Paragraph
        self.aSelectPar = qtAddAction(self.editMenu, self.tr("Select Paragraph"))
        self.aSelectPar.setShortcut("Ctrl+Shift+A")
        self.aSelectPar.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SEL_PARA))
        self.mainGui.addAction(self.aSelectPar)

    def _buildViewMenu(self) -> None:
        """Assemble the View menu."""
        # View
        self.viewMenu = qtAddMenu(self, self.tr("&View"))

        # View > TreeView
        self.aFocusTree = qtAddAction(self.viewMenu, self.tr("Go to Tree View"))
        self.aFocusTree.setShortcut("Ctrl+T")
        self.aFocusTree.triggered.connect(qtWeakLambda(self._emitFocusChange, nwFocus.TREE))
        self.mainGui.addAction(self.aFocusTree)

        # View > Document Editor
        self.aFocusDocument = qtAddAction(self.viewMenu, self.tr("Go to Document"))
        self.aFocusDocument.setShortcut("Ctrl+E")
        self.aFocusDocument.triggered.connect(qtWeakLambda(self._emitFocusChange, nwFocus.DOCUMENT))

        # View > Story View
        self.aFocusStory = qtAddAction(self.viewMenu, self.tr("Go to Story View"))
        self.aFocusStory.setShortcut("Ctrl+Shift+T")
        self.aFocusStory.triggered.connect(qtWeakLambda(self._emitFocusChange, nwFocus.STORY))
        self.mainGui.addAction(self.aFocusStory)

        # View > Separator
        self.viewMenu.addSeparator()

        # View > Go Backward
        self.aViewPrev = qtAddAction(self.viewMenu, self.tr("Navigate Backward"))
        self.aViewPrev.setShortcut("Alt+Left")
        self.aViewPrev.setShortcutContext(QtWidgetShortcut)
        self.aViewPrev.triggered.connect(self.mainGui.docViewer.navBackward)
        self.mainGui.docViewer.addAction(self.aViewPrev)

        # View > Go Forward
        self.aViewNext = qtAddAction(self.viewMenu, self.tr("Navigate Forward"))
        self.aViewNext.setShortcut("Alt+Right")
        self.aViewNext.setShortcutContext(QtWidgetShortcut)
        self.aViewNext.triggered.connect(self.mainGui.docViewer.navForward)
        self.mainGui.docViewer.addAction(self.aViewNext)

        # View > Separator
        self.viewMenu.addSeparator()

        # View > Focus Mode
        self.aFocusMode = qtAddAction(self.viewMenu, self.tr("Focus Mode"))
        self.aFocusMode.setShortcut("F8")
        self.aFocusMode.triggered.connect(self.mainGui.toggleFocusMode)
        self.mainGui.addAction(self.aFocusMode)

        # View > Toggle Full Screen
        self.aFullScreen = qtAddAction(self.viewMenu, self.tr("Full Screen Mode"))
        self.aFullScreen.setShortcut("F11")
        self.aFullScreen.triggered.connect(self.mainGui.toggleFullScreenMode)
        self.mainGui.addAction(self.aFullScreen)

        # View > Separator
        self.viewMenu.addSeparator()

        # View > Zoom In
        self.aZoomIn = qtAddAction(self.viewMenu, self.tr("Zoom In"))
        self.aZoomIn.setShortcuts(["Ctrl++", "Ctrl+="])
        self.aZoomIn.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ZOOM_IN))
        self.mainGui.addAction(self.aZoomIn)

        # View > Zoom Out
        self.aZoomOut = qtAddAction(self.viewMenu, self.tr("Zoom Out"))
        self.aZoomOut.setShortcuts(["Ctrl+-", "Ctrl+_"])
        self.aZoomOut.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ZOOM_OUT))
        self.mainGui.addAction(self.aZoomOut)

        # View > Reset Zoom
        self.aZoomReset = qtAddAction(self.viewMenu, self.tr("Reset Zoom"))
        self.aZoomReset.setShortcut("Ctrl+0")
        self.aZoomReset.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ZOOM_RESET))
        self.mainGui.addAction(self.aZoomReset)

    def _buildInsertMenu(self) -> None:
        """Assemble the Insert menu."""
        # Insert
        self.insMenu = qtAddMenu(self, self.tr("&Insert"))

        # Insert > Dashes and Dots
        self.mInsDashes = qtAddMenu(self.insMenu, self.tr("Dashes"))

        # Insert > Short Dash
        self.aInsENDash = qtAddAction(self.mInsDashes, self.tr("Short Dash"))
        self.aInsENDash.setShortcut("Ctrl+K, -")
        self.aInsENDash.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_ENDASH))
        self.mainGui.addAction(self.aInsENDash)

        # Insert > Long Dash
        self.aInsEMDash = qtAddAction(self.mInsDashes, self.tr("Long Dash"))
        self.aInsEMDash.setShortcut("Ctrl+K, _")
        self.aInsEMDash.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_EMDASH))
        self.mainGui.addAction(self.aInsEMDash)

        # Insert > Long Dash
        self.aInsHorBar = qtAddAction(self.mInsDashes, self.tr("Horizontal Bar"))
        self.aInsHorBar.setShortcut("Ctrl+K, Ctrl+_")
        self.aInsHorBar.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_HBAR))
        self.mainGui.addAction(self.aInsHorBar)

        # Insert > Figure Dash
        self.aInsFigDash = qtAddAction(self.mInsDashes, self.tr("Figure Dash"))
        self.aInsFigDash.setShortcut("Ctrl+K, ~")
        self.aInsFigDash.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_FGDASH))
        self.mainGui.addAction(self.aInsFigDash)

        # Insert > Quote Marks
        self.mInsQuotes = qtAddMenu(self.insMenu, self.tr("Quote Marks"))

        # Insert > Left Single Quote
        self.aInsQuoteLS = qtAddAction(self.mInsQuotes, self.tr("Left Single Quote"))
        self.aInsQuoteLS.setShortcut("Ctrl+K, 1")
        self.aInsQuoteLS.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.QUOTE_LS))
        self.mainGui.addAction(self.aInsQuoteLS)

        # Insert > Right Single Quote
        self.aInsQuoteRS = qtAddAction(self.mInsQuotes, self.tr("Right Single Quote"))
        self.aInsQuoteRS.setShortcut("Ctrl+K, 2")
        self.aInsQuoteRS.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.QUOTE_RS))
        self.mainGui.addAction(self.aInsQuoteRS)

        # Insert > Left Double Quote
        self.aInsQuoteLD = qtAddAction(self.mInsQuotes, self.tr("Left Double Quote"))
        self.aInsQuoteLD.setShortcut("Ctrl+K, 3")
        self.aInsQuoteLD.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.QUOTE_LD))
        self.mainGui.addAction(self.aInsQuoteLD)

        # Insert > Right Double Quote
        self.aInsQuoteRD = qtAddAction(self.mInsQuotes, self.tr("Right Double Quote"))
        self.aInsQuoteRD.setShortcut("Ctrl+K, 4")
        self.aInsQuoteRD.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.QUOTE_RD))
        self.mainGui.addAction(self.aInsQuoteRD)

        # Insert > Alternative Apostrophe
        self.aInsMSApos = qtAddAction(self.mInsQuotes, self.tr("Alternative Apostrophe"))
        self.aInsMSApos.setShortcut("Ctrl+K, '")
        self.aInsMSApos.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_MAPOS))
        self.mainGui.addAction(self.aInsMSApos)

        # Insert > Symbols
        self.mInsPunct = qtAddMenu(self.insMenu, self.tr("General Punctuation"))

        # Insert > Ellipsis
        self.aInsEllipsis = qtAddAction(self.mInsPunct, self.tr("Ellipsis"))
        self.aInsEllipsis.setShortcut("Ctrl+K, .")
        self.aInsEllipsis.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_HELLIP))
        self.mainGui.addAction(self.aInsEllipsis)

        # Insert > Prime
        self.aInsPrime = qtAddAction(self.mInsPunct, self.tr("Prime"))
        self.aInsPrime.setShortcut("Ctrl+K, Ctrl+'")
        self.aInsPrime.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_PRIME))
        self.mainGui.addAction(self.aInsPrime)

        # Insert > Double Prime
        self.aInsDPrime = qtAddAction(self.mInsPunct, self.tr("Double Prime"))
        self.aInsDPrime.setShortcut('Ctrl+K, Ctrl+"')
        self.aInsDPrime.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_DPRIME))
        self.mainGui.addAction(self.aInsDPrime)

        # Insert > White Spaces
        self.mInsSpace = qtAddMenu(self.insMenu, self.tr("White Spaces"))

        # Insert > Non-Breaking Space
        self.aInsNBSpace = qtAddAction(self.mInsSpace, self.tr("Non-Breaking Space"))
        self.aInsNBSpace.setShortcut("Ctrl+K, Space")
        self.aInsNBSpace.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_NBSP))
        self.mainGui.addAction(self.aInsNBSpace)

        # Insert > Thin Space
        self.aInsThinSpace = qtAddAction(self.mInsSpace, self.tr("Thin Space"))
        self.aInsThinSpace.setShortcut("Ctrl+K, Shift+Space")
        self.aInsThinSpace.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_THSP))
        self.mainGui.addAction(self.aInsThinSpace)

        # Insert > Thin Non-Breaking Space
        self.aInsThinNBSpace = qtAddAction(self.mInsSpace, self.tr("Thin Non-Breaking Space"))
        self.aInsThinNBSpace.setShortcut("Ctrl+K, Ctrl+Space")
        self.aInsThinNBSpace.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_THNBSP))
        self.mainGui.addAction(self.aInsThinNBSpace)

        # Insert > Symbols
        self.mInsSymbol = qtAddMenu(self.insMenu, self.tr("Other Symbols"))

        # Insert > List Bullet
        self.aInsBullet = qtAddAction(self.mInsSymbol, self.tr("List Bullet"))
        self.aInsBullet.setShortcut("Ctrl+K, *")
        self.aInsBullet.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_BULL))
        self.mainGui.addAction(self.aInsBullet)

        # Insert > Hyphen Bullet
        self.aInsHyBull = qtAddAction(self.mInsSymbol, self.tr("Hyphen Bullet"))
        self.aInsHyBull.setShortcut("Ctrl+K, Ctrl+-")
        self.aInsHyBull.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_HYBULL))
        self.mainGui.addAction(self.aInsHyBull)

        # Insert > Flower Mark
        self.aInsFlower = qtAddAction(self.mInsSymbol, self.tr("Flower Mark"))
        self.aInsFlower.setShortcut("Ctrl+K, Ctrl+*")
        self.aInsFlower.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_FLOWER))
        self.mainGui.addAction(self.aInsFlower)

        # Insert > Per Mille
        self.aInsPerMille = qtAddAction(self.mInsSymbol, self.tr("Per Mille"))
        self.aInsPerMille.setShortcut("Ctrl+K, %")
        self.aInsPerMille.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_PERMIL))
        self.mainGui.addAction(self.aInsPerMille)

        # Insert > Degree Symbol
        self.aInsDegree = qtAddAction(self.mInsSymbol, self.tr("Degree Symbol"))
        self.aInsDegree.setShortcut("Ctrl+K, Ctrl+O")
        self.aInsDegree.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_DEGREE))
        self.mainGui.addAction(self.aInsDegree)

        # Insert > Minus Sign
        self.aInsMinus = qtAddAction(self.mInsSymbol, self.tr("Minus Sign"))
        self.aInsMinus.setShortcut("Ctrl+K, Ctrl+M")
        self.aInsMinus.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_MINUS))
        self.mainGui.addAction(self.aInsMinus)

        # Insert > Times Sign
        self.aInsTimes = qtAddAction(self.mInsSymbol, self.tr("Times Sign"))
        self.aInsTimes.setShortcut("Ctrl+K, Ctrl+X")
        self.aInsTimes.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_TIMES))
        self.mainGui.addAction(self.aInsTimes)

        # Insert > Division
        self.aInsDivide = qtAddAction(self.mInsSymbol, self.tr("Division Sign"))
        self.aInsDivide.setShortcut("Ctrl+K, Ctrl+D")
        self.aInsDivide.triggered.connect(qtWeakLambda(self._emitDocInsertText, nwUnicode.U_DIVIDE))
        self.mainGui.addAction(self.aInsDivide)

        # Insert > Tags and References
        self.mInsKeywords = qtAddMenu(self.insMenu, self.tr("Tags and References"))
        for key in nwKeyWords.ALL_KEYS:
            action = qtAddAction(self.mInsKeywords, trConst(nwLabels.KEY_NAME[key]))
            action.setShortcut(nwLabels.KEY_SHORTCUT[key])
            action.triggered.connect(qtWeakLambda(self._emitDocKeyWordInsert, key))
            self.mainGui.addAction(action)

        # Insert > Special Comments
        self.mInsComments = qtAddMenu(self.insMenu, self.tr("Special Comments"))

        # Insert > Synopsis Comment
        self.aInsSynopsis = qtAddAction(self.mInsComments, self.tr("Synopsis Comment"))
        self.aInsSynopsis.setShortcut("Ctrl+K, S")
        self.aInsSynopsis.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.SYNOPSIS))
        self.mainGui.addAction(self.aInsSynopsis)

        # Insert > Short Description Comment
        self.aInsShort = qtAddAction(self.mInsComments, self.tr("Short Description Comment"))
        self.aInsShort.setShortcut("Ctrl+K, H")
        self.aInsShort.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.SHORT))
        self.mainGui.addAction(self.aInsShort)

        # Insert > Word/Character Count
        self.mInsField = qtAddMenu(self.insMenu, self.tr("Word/Character Count"))
        for field in nwStats.ALL_FIELDS:
            value = nwShortcode.FIELD_VALUE.format(field)
            action = qtAddAction(self.mInsField, trStats(nwLabels.STATS_NAME[field]))
            action.triggered.connect(qtWeakLambda(self._emitDocInsertText, value))

        # Insert > Breaks and Vertical Space
        self.mInsBreaks = qtAddMenu(self.insMenu, self.tr("Breaks and Vertical Space"))

        # Insert > New Page
        self.aInsNewPage = qtAddAction(self.mInsBreaks, self.tr("Page Break"))
        self.aInsNewPage.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.NEW_PAGE))

        # Insert > Forced Line Break
        self.aInsLineBreak = qtAddAction(self.mInsBreaks, self.tr("Forced Line Break"))
        self.aInsLineBreak.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.LINE_BRK))

        # Insert > Vertical Space (Single)
        self.aInsVSpaceS = qtAddAction(self.mInsBreaks, self.tr("Vertical Space (Single)"))
        self.aInsVSpaceS.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.VSPACE_S))

        # Insert > Vertical Space (Multi)
        self.aInsVSpaceM = qtAddAction(self.mInsBreaks, self.tr("Vertical Space (Multi)"))
        self.aInsVSpaceM.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.VSPACE_M))

        # Insert > Placeholder Text
        self.aLipsumText = qtAddAction(self.insMenu, self.tr("Placeholder Text"))
        self.aLipsumText.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.LIPSUM))

        # Insert > Footnote
        self.aFootnote = qtAddAction(self.insMenu, self.tr("Footnote"))
        self.aFootnote.triggered.connect(qtWeakLambda(self._emitDocInsert, nwDocInsert.FOOTNOTE))

    def _buildFormatMenu(self) -> None:
        """Assemble the Format menu."""
        # Format
        self.fmtMenu = qtAddMenu(self, self.tr("&Format"))

        # Format > Bold
        self.aFmtBold = qtAddAction(self.fmtMenu, self.tr("Bold"))
        self.aFmtBold.setShortcut("Ctrl+B")
        self.aFmtBold.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.MD_BOLD))
        self.mainGui.addAction(self.aFmtBold)

        # Format > Italic
        self.aFmtItalic = qtAddAction(self.fmtMenu, self.tr("Italic"))
        self.aFmtItalic.setShortcut("Ctrl+I")
        self.aFmtItalic.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.MD_ITALIC))
        self.mainGui.addAction(self.aFmtItalic)

        # Format > Strikethrough
        self.aFmtStrike = qtAddAction(self.fmtMenu, self.tr("Strikethrough"))
        self.aFmtStrike.setShortcut("Ctrl+D")
        self.aFmtStrike.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.MD_STRIKE))
        self.mainGui.addAction(self.aFmtStrike)

        # Format > Highlight
        self.aFmtMark = qtAddAction(self.fmtMenu, self.tr("Highlight"))
        self.aFmtMark.setShortcut("Ctrl+M")
        self.aFmtMark.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.MD_MARK))
        self.mainGui.addAction(self.aFmtStrike)

        # Edit > Separator
        self.fmtMenu.addSeparator()

        # Format > Double Quotes
        self.aFmtDQuote = qtAddAction(self.fmtMenu, self.tr("Wrap Double Quotes"))
        self.aFmtDQuote.setShortcut('Ctrl+"')
        self.aFmtDQuote.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.D_QUOTE))
        self.mainGui.addAction(self.aFmtDQuote)

        # Format > Single Quotes
        self.aFmtSQuote = qtAddAction(self.fmtMenu, self.tr("Wrap Single Quotes"))
        self.aFmtSQuote.setShortcut("Ctrl+'")
        self.aFmtSQuote.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.S_QUOTE))
        self.mainGui.addAction(self.aFmtSQuote)

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Shortcodes
        self.mShortcodes = qtAddMenu(self.fmtMenu, self.tr("More Formats ..."))

        # Shortcode Bold
        self.aScBold = qtAddAction(self.mShortcodes, self.tr("Bold (Shortcode)"))
        self.aScBold.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_BOLD))

        # Shortcode Italic
        self.aScItalic = qtAddAction(self.mShortcodes, self.tr("Italics (Shortcode)"))
        self.aScItalic.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_ITALIC))

        # Shortcode Strikethrough
        self.aScStrike = qtAddAction(self.mShortcodes, self.tr("Strikethrough (Shortcode)"))
        self.aScStrike.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_STRIKE))

        # Shortcode Underline
        self.aScULine = qtAddAction(self.mShortcodes, self.tr("Underline"))
        self.aScULine.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_ULINE))

        # Shortcode Mark
        self.aScMark = qtAddAction(self.mShortcodes, self.tr("Highlight"))
        self.aScMark.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_MARK))

        # Shortcode Superscript
        self.aScSuper = qtAddAction(self.mShortcodes, self.tr("Superscript"))
        self.aScSuper.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_SUP))

        # Shortcode Subscript
        self.aScSub = qtAddAction(self.mShortcodes, self.tr("Subscript"))
        self.aScSub.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.SC_SUB))

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Heading 1 (Partition)
        self.aFmtHead1 = qtAddAction(self.fmtMenu, trConst(nwStyles.T_LABEL["H1"]))
        self.aFmtHead1.setShortcut("Ctrl+1")
        self.aFmtHead1.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_H1))
        self.mainGui.addAction(self.aFmtHead1)

        # Format > Heading 2 (Chapter)
        self.aFmtHead2 = qtAddAction(self.fmtMenu, trConst(nwStyles.T_LABEL["H2"]))
        self.aFmtHead2.setShortcut("Ctrl+2")
        self.aFmtHead2.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_H2))
        self.mainGui.addAction(self.aFmtHead2)

        # Format > Heading 3 (Scene)
        self.aFmtHead3 = qtAddAction(self.fmtMenu, trConst(nwStyles.T_LABEL["H3"]))
        self.aFmtHead3.setShortcut("Ctrl+3")
        self.aFmtHead3.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_H3))
        self.mainGui.addAction(self.aFmtHead3)

        # Format > Heading 4 (Section)
        self.aFmtHead4 = qtAddAction(self.fmtMenu, trConst(nwStyles.T_LABEL["H4"]))
        self.aFmtHead4.setShortcut("Ctrl+4")
        self.aFmtHead4.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_H4))
        self.mainGui.addAction(self.aFmtHead4)

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Novel Title
        self.aFmtTitle = qtAddAction(self.fmtMenu, self.tr("Novel Title"))
        self.aFmtTitle.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_TTL))

        # Format > Unnumbered Chapter
        self.aFmtUnNum = qtAddAction(self.fmtMenu, self.tr("Unnumbered Chapter"))
        self.aFmtUnNum.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_UNN))

        # Format > Alternative Scene
        self.aFmtHardSc = qtAddAction(self.fmtMenu, self.tr("Alternative Scene"))
        self.aFmtHardSc.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_HSC))

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Align Left
        self.aFmtAlignLeft = qtAddAction(self.fmtMenu, self.tr("Align Left"))
        self.aFmtAlignLeft.setShortcut("Ctrl+5")
        self.aFmtAlignLeft.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ALIGN_L))
        self.mainGui.addAction(self.aFmtAlignLeft)

        # Format > Align Centre
        self.aFmtAlignCentre = qtAddAction(self.fmtMenu, self.tr("Align Centre"))
        self.aFmtAlignCentre.setShortcut("Ctrl+6")
        self.aFmtAlignCentre.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ALIGN_C))
        self.mainGui.addAction(self.aFmtAlignCentre)

        # Format > Align Right
        self.aFmtAlignRight = qtAddAction(self.fmtMenu, self.tr("Align Right"))
        self.aFmtAlignRight.setShortcut("Ctrl+7")
        self.aFmtAlignRight.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.ALIGN_R))
        self.mainGui.addAction(self.aFmtAlignRight)

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Indent Left
        self.aFmtIndentLeft = qtAddAction(self.fmtMenu, self.tr("Indent Left"))
        self.aFmtIndentLeft.setShortcut("Ctrl+8")
        self.aFmtIndentLeft.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.INDENT_L))
        self.mainGui.addAction(self.aFmtIndentLeft)

        # Format > Indent Right
        self.aFmtIndentRight = qtAddAction(self.fmtMenu, self.tr("Indent Right"))
        self.aFmtIndentRight.setShortcut("Ctrl+9")
        self.aFmtIndentRight.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.INDENT_R))
        self.mainGui.addAction(self.aFmtIndentRight)

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Comment
        self.aFmtComment = qtAddAction(self.fmtMenu, self.tr("Toggle Comment"))
        self.aFmtComment.setShortcut("Ctrl+/")
        self.aFmtComment.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_COM))
        self.mainGui.addAction(self.aFmtComment)

        # Format > Ignore Text
        self.aFmtIgnore = qtAddAction(self.fmtMenu, self.tr("Toggle Ignore Text"))
        self.aFmtIgnore.setShortcut("Ctrl+Shift+D")
        self.aFmtIgnore.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_IGN))

        # Format > Remove Block Format
        self.aFmtNoFormat = qtAddAction(self.fmtMenu, self.tr("Remove Block Format"))
        self.aFmtNoFormat.setShortcut("Ctrl+Shift+/")
        self.aFmtNoFormat.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.BLOCK_TXT))
        self.mainGui.addAction(self.aFmtNoFormat)

        # Format > Separator
        self.fmtMenu.addSeparator()

        # Format > Replace Straight Single Quotes
        self.aFmtReplSng = qtAddAction(self.fmtMenu, self.tr("Replace Straight Single Quotes"))
        self.aFmtReplSng.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.REPL_SNG))

        # Format > Replace Straight Double Quotes
        self.aFmtReplDbl = qtAddAction(self.fmtMenu, self.tr("Replace Straight Double Quotes"))
        self.aFmtReplDbl.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.REPL_DBL))

        # Format > Remove In-Paragraph Breaks
        self.aFmtRmBreaks = qtAddAction(self.fmtMenu, self.tr("Remove In-Paragraph Breaks"))
        self.aFmtRmBreaks.triggered.connect(qtWeakLambda(self._emitDocAction, nwDocAction.RM_BREAKS))

    def _buildSearchMenu(self) -> None:
        """Assemble the Search menu."""
        # Search
        self.srcMenu = qtAddMenu(self, self.tr("&Search"))

        # Search > Find
        self.aFind = qtAddAction(self.srcMenu, self.tr("Find"))
        self.aFind.setShortcut("Ctrl+F")
        self.aFind.triggered.connect(qtWeakLambda(self.mainGui.docEditor.beginSearch))
        self.mainGui.addAction(self.aFind)

        # Search > Replace
        self.aReplace = qtAddAction(self.srcMenu, self.tr("Replace"))
        self.aReplace.setShortcut("Ctrl+=" if CONFIG.osDarwin else "Ctrl+H")
        self.aReplace.triggered.connect(qtWeakLambda(self.mainGui.docEditor.beginReplace))
        self.mainGui.addAction(self.aReplace)

        # Search > Find Next
        self.aFindNext = qtAddAction(self.srcMenu, self.tr("Find Next"))
        self.aFindNext.setShortcuts(["Ctrl+G", "F3"] if CONFIG.osDarwin else ["F3", "Ctrl+G"])
        self.aFindNext.triggered.connect(qtWeakLambda(self.mainGui.docEditor.findNext))
        self.mainGui.addAction(self.aFindNext)

        # Search > Find Prev
        self.aFindPrev = qtAddAction(self.srcMenu, self.tr("Find Previous"))
        self.aFindPrev.setShortcuts(["Ctrl+Shift+G", "Shift+F3"] if CONFIG.osDarwin else ["Shift+F3", "Ctrl+Shift+G"])
        self.aFindPrev.triggered.connect(qtWeakLambda(self.mainGui.docEditor.findNext, goBack=True))
        self.mainGui.addAction(self.aFindPrev)

        # Search > Replace Next
        self.aReplaceNext = qtAddAction(self.srcMenu, self.tr("Replace Next"))
        self.aReplaceNext.setShortcut("Ctrl+Shift+1")
        self.aReplaceNext.triggered.connect(qtWeakLambda(self.mainGui.docEditor.replaceNext))
        self.mainGui.addAction(self.aReplaceNext)

        # Search > Separator
        self.srcMenu.addSeparator()

        # Search > Find in Project
        self.aFindProj = qtAddAction(self.srcMenu, self.tr("Find in Project"))
        self.aFindProj.setShortcut("Ctrl+Shift+F")
        self.aFindProj.triggered.connect(qtWeakLambda(self._emitViewChange, nwView.SEARCH))

    def _buildToolsMenu(self) -> None:
        """Assemble the Tools menu."""
        # Tools
        self.toolsMenu = qtAddMenu(self, self.tr("&Tools"))

        # Tools > Check Spelling
        self.aSpellCheck = qtAddAction(self.toolsMenu, self.tr("Check Spelling"))
        self.aSpellCheck.setCheckable(True)
        self.aSpellCheck.setChecked(SHARED.project.data.spellCheck)
        self.aSpellCheck.triggered.connect(self._toggleSpellCheck)  # triggered, not toggled!
        self.aSpellCheck.setShortcut("Ctrl+F7")
        self.mainGui.addAction(self.aSpellCheck)

        self.mSelectLanguage = qtAddMenu(self.toolsMenu, self.tr("Spell Check Language"))
        self.updateSpellCheckLanguages()

        # Tools > Re-Run Spell Check
        self.aReRunSpell = qtAddAction(self.toolsMenu, self.tr("Re-Run Spell Check"))
        self.aReRunSpell.setShortcut("F7")
        self.aReRunSpell.triggered.connect(qtWeakLambda(self.mainGui.docEditor.spellCheckDocument))
        self.mainGui.addAction(self.aReRunSpell)

        # Tools > Project Word List
        self.aEditWordList = qtAddAction(self.toolsMenu, self.tr("Project Word List"))
        self.aEditWordList.triggered.connect(self.mainGui.showProjectWordListDialog)

        # Tools > Add Dictionaries
        if CONFIG.osWindows or CONFIG.isDebug:
            self.aAddDicts = qtAddAction(self.toolsMenu, self.tr("Add Dictionaries"))
            self.aAddDicts.triggered.connect(self.mainGui.showDictionariesDialog)

        # Tools > Separator
        self.toolsMenu.addSeparator()

        # Tools > Rebuild Index
        self.aRebuildIndex = qtAddAction(self.toolsMenu, self.tr("Rebuild Index"))
        self.aRebuildIndex.setShortcut("F9")
        self.aRebuildIndex.triggered.connect(qtWeakLambda(self.mainGui.rebuildIndex))

        # Tools > Separator
        self.toolsMenu.addSeparator()

        # Tools > Backup Project
        self.aBackupProject = qtAddAction(self.toolsMenu, self.tr("Backup Project"))
        self.aBackupProject.triggered.connect(qtLambda(SHARED.project.backupProject, True))

        # Tools > Manuscript Build
        self.aBuildManuscript = qtAddAction(self.toolsMenu, self.tr("Manuscript Build"))
        self.aBuildManuscript.setShortcut("F5")
        self.aBuildManuscript.triggered.connect(self.mainGui.showBuildManuscriptDialog)

        # Tools > Writing Statistics
        self.aWritingStats = qtAddAction(self.toolsMenu, self.tr("Writing Statistics"))
        self.aWritingStats.setShortcut("F6")
        self.aWritingStats.triggered.connect(self.mainGui.showWritingStatsDialog)

        # Tools > Preferences
        self.aPreferences = qtAddAction(self.toolsMenu, self.tr("Preferences"))
        self.aPreferences.setShortcut("Ctrl+,")
        self.aPreferences.setMenuRole(QAction.MenuRole.PreferencesRole)
        self.aPreferences.triggered.connect(self.mainGui.showPreferencesDialog)
        self.mainGui.addAction(self.aPreferences)

    def _buildHelpMenu(self) -> None:
        """Assemble the Help menu."""
        # Help
        self.helpMenu = qtAddMenu(self, self.tr("&Help"))

        # Help > About
        self.aAboutNW = qtAddAction(self.helpMenu, self.tr("About novelWriter"))
        self.aAboutNW.setMenuRole(QAction.MenuRole.AboutRole)
        self.aAboutNW.triggered.connect(self.mainGui.showAboutNWDialog)

        # Help > About Qt
        self.aAboutQt = qtAddAction(self.helpMenu, self.tr("About Qt"))
        self.aAboutQt.setMenuRole(QAction.MenuRole.AboutQtRole)
        self.aAboutQt.triggered.connect(self.mainGui.showAboutQtDialog)

        # Help > Separator
        self.helpMenu.addSeparator()

        # Help > User Manual (Online)
        self.aHelpDocs = qtAddAction(self.helpMenu, self.tr("User Manual (Online)"))
        self.aHelpDocs.setShortcut("F1")
        self.aHelpDocs.triggered.connect(qtLambda(SHARED.openWebsite, nwConst.URL_DOCS))
        self.mainGui.addAction(self.aHelpDocs)

        # Help > User Manual (PDF)
        if isinstance(CONFIG.pdfDocs, Path):
            self.aPdfDocs = qtAddAction(self.helpMenu, self.tr("User Manual (PDF)"))
            self.aPdfDocs.setShortcut("Shift+F1")
            self.aPdfDocs.triggered.connect(self._openUserManualFile)
            self.mainGui.addAction(self.aPdfDocs)

        # Help > Separator
        self.helpMenu.addSeparator()

        # Document > Report an Issue
        self.aIssue = qtAddAction(self.helpMenu, self.tr("Report an Issue (GitHub)"))
        self.aIssue.triggered.connect(qtLambda(SHARED.openWebsite, nwConst.URL_REPORT))

        # Document > Ask a Question
        self.aQuestion = qtAddAction(self.helpMenu, self.tr("Ask a Question (GitHub)"))
        self.aQuestion.triggered.connect(qtLambda(SHARED.openWebsite, nwConst.URL_HELP))

        # Document > Main Website
        self.aWebsite = qtAddAction(self.helpMenu, self.tr("The novelWriter Website"))
        self.aWebsite.triggered.connect(qtLambda(SHARED.openWebsite, nwConst.URL_WEB))
