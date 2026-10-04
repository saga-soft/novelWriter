"""
novelWriter - GUI Document Viewer
=================================

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

from enum import Enum

from PyQt6.QtCore import QEvent, QPoint, Qt, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import (
    QCursor,
    QDesktopServices,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QMouseEvent,
    QPalette,
    QResizeEvent,
    QTextCursor,
)
from PyQt6.QtWidgets import QApplication, QFrame, QMenu, QTextBrowser, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import decodeMimeHandles, fontMatcher, qtAddAction, qtLambda
from novelwriter.constants import nwConst, nwStyles, nwUnicode
from novelwriter.editor.footer import GuiDocViewFooter
from novelwriter.editor.header import GuiDocViewHeader
from novelwriter.editor.history import GuiDocViewHistory
from novelwriter.editor.hovercard import GuiDocHoverCard
from novelwriter.enum import nwChange, nwComment, nwDocAction, nwDocMode, nwItemType
from novelwriter.error import logException
from novelwriter.extensions.eventfilters import WheelEventFilter
from novelwriter.formats.shared import TextDocumentTheme
from novelwriter.formats.toqdoc import ToQTextDocument
from novelwriter.types import (
    QtKeepAnchor,
    QtMoveAnchor,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSelectBlock,
    QtSelectDocument,
    QtSelectWord,
)

logger = logging.getLogger(__name__)


class GuiDocViewer(QTextBrowser):
    """GUI: Document Viewer."""

    closeDocumentRequest = pyqtSignal()
    documentLoaded = pyqtSignal(str)
    loadDocumentTagRequest = pyqtSignal(str, Enum)
    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    reloadDocumentRequest = pyqtSignal()
    requestProjectItemSelected = pyqtSignal(str, bool)
    togglePanelVisibility = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocViewer")

        # Internal Variables
        self._docHandle = None
        self._docTheme = TextDocumentTheme()

        # Settings
        self.setMinimumWidth(300)
        self.setAutoFillBackground(True)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFrameStyle(QFrame.Shape.NoFrame)

        # Document Header and Footer
        self.docHeader = GuiDocViewHeader(self)
        self.docFooter = GuiDocViewFooter(self)
        self.docHistory = GuiDocViewHistory(self)
        self.stickyRef = False

        # Signals
        self.anchorClicked.connect(self._linkClicked)

        # Set Up Reference Tag Hover Card
        self._hoverCard = GuiDocHoverCard(self)
        self._hoverCard.openDocumentRequest.connect(self.openDocumentRequest)
        self._hoverPos = QPoint()
        self._timerHover = QTimer(self)
        self._timerHover.timeout.connect(self._showHoverCard)
        self._timerHover.setSingleShot(True)
        self._timerHover.setInterval(250)

        if viewport := self.viewport():  # pragma: no branch
            viewport.setMouseTracking(True)

        # Install Event Filter for Mouse Wheel
        self.wheelEventFilter = WheelEventFilter(self)
        self.installEventFilter(self.wheelEventFilter)

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._openContextMenu)

        # Function Mapping
        self.changeFocusState = self.docHeader.changeFocusState

        self.initViewer()

        logger.debug("Ready: GuiDocViewer")

    ##
    #  Properties
    ##

    @property
    def docHandle(self) -> str | None:
        """Return the handle of the currently open document."""
        return self._docHandle

    @property
    def scrollPosition(self) -> int:
        """Return the scrollbar position."""
        if (vBar := self.verticalScrollBar()) and vBar.isVisible():
            return vBar.value()
        return 0

    ##
    #  Methods
    ##

    def clearViewer(self) -> None:
        """Clear the content of the document and reset key variables."""
        self.clear()
        self.setSearchPaths([""])
        self._docHandle = None
        self.docHeader.clearHeader()
        self._timerHover.stop()
        self._hoverCard.hide()
        self._hoverCard.clearCache()

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocViewer")
        self.docHeader.updateTheme()
        self.docFooter.updateTheme()

    def initViewer(self) -> None:
        """Set editor settings from main config."""
        # Set the font. See issues #1862 and #1875.
        self.setFont(CONFIG.textFont)
        self.docHeader.updateFont()
        self.docFooter.updateFont()

        # Set the widget colours to match syntax theme
        syntax = SHARED.theme.syntaxTheme

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, syntax.back)
        palette.setColor(QPalette.ColorRole.Base, syntax.back)
        palette.setColor(QPalette.ColorRole.Text, syntax.text)
        self.setPalette(palette)

        if viewport := self.viewport():  # pragma: no branch
            palette = viewport.palette()
            palette.setColor(QPalette.ColorRole.Base, syntax.back)
            palette.setColor(QPalette.ColorRole.Text, syntax.text)
            viewport.setPalette(palette)
            self.docHeader.matchColors()
            self.docFooter.matchColors()

        # Update theme colours
        self._docTheme.text = syntax.text
        self._docTheme.highlight = syntax.mark
        self._docTheme.head = syntax.head
        self._docTheme.link = syntax.link
        self._docTheme.comment = syntax.hidden
        self._docTheme.note = syntax.note
        self._docTheme.code = syntax.code
        self._docTheme.modifier = syntax.mod
        self._docTheme.keyword = syntax.key
        self._docTheme.tag = syntax.tag
        self._docTheme.optional = syntax.opt
        self._docTheme.dialog = syntax.dialN
        self._docTheme.altdialog = syntax.dialA

        self._hoverCard.updateTheme()

        # Set default text margins
        if document := self.document():  # pragma: no branch
            document.setDocumentMargin(0)

        self.initViewport()

        # Refresh the tab stops
        self.setTabStopDistance(CONFIG.tabWidth)

        # If we have a document open, we should reload it in case the font changed
        self.reloadText()

    def initViewport(self) -> None:
        """Initialise the settings of the viewer viewport."""
        # Scrolling
        if CONFIG.hideVScroll:
            self.setVerticalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setVerticalScrollBarPolicy(QtScrollAsNeeded)

        if CONFIG.hideHScroll:
            self.setHorizontalScrollBarPolicy(QtScrollAlwaysOff)
        else:
            self.setHorizontalScrollBarPolicy(QtScrollAsNeeded)

        self.updateDocMargins()

    def initSettings(self) -> None:
        """Initialise non-expensive settings."""
        if self._docHandle:
            self.docHeader.setHandle(self._docHandle)

    def loadText(self, tHandle: str, updateHistory: bool = True) -> bool:
        """Load text into the viewer from an item handle."""
        self._timerHover.stop()
        self._hoverCard.hide()
        if not SHARED.project.tree.checkType(tHandle, nwItemType.FILE):
            logger.warning("Item not found")
            self.documentLoaded.emit("")
            return False

        logger.debug("Generating preview for item '%s'", tHandle)
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))

        vBar = self.verticalScrollBar()
        sPos = vBar.value() if vBar else 0

        qDoc = ToQTextDocument(SHARED.project)
        qDoc.setJustify(CONFIG.doJustify, False)
        qDoc.setDialogHighlight(True)
        qDoc.setTextFont(CONFIG.textFont)
        qDoc.setFixedHeadings(True)
        qDoc.setLineHeight(CONFIG.lineHeight)
        qDoc.setTheme(self._docTheme)
        qDoc.initDocument()
        qDoc.setKeywords(True)
        qDoc.setCommentType(nwComment.PLAIN, CONFIG.viewComments)
        qDoc.setCommentType(nwComment.SYNOPSIS, CONFIG.viewSynopsis)
        qDoc.setCommentType(nwComment.SHORT, CONFIG.viewSynopsis)
        qDoc.setCommentType(nwComment.STORY, CONFIG.viewNotes)
        qDoc.setCommentType(nwComment.NOTE, CONFIG.viewNotes)

        # Be extra careful here to prevent crashes when first opening a
        # project as a crash here leaves no way of recovering.
        # See issue #298
        try:
            qDoc.setText(tHandle)
            qDoc.doPreProcessing()
            qDoc.tokenizeText()
            qDoc.doConvert()
            qDoc.closeDocument()
        except Exception:
            logger.error("Failed to generate preview for document with handle '%s'", tHandle)
            logException()
            self.setText(self.tr("An error occurred while generating the preview."))
            QApplication.restoreOverrideCursor()
            return False

        # Must be before setDocument
        if updateHistory:
            self.docHistory.append(tHandle)

        self.setDocumentTitle(tHandle)
        self.setDocument(qDoc.document)
        self.setTabStopDistance(CONFIG.tabWidth)

        if self._docHandle == tHandle and vBar:
            # This is a refresh, so we set the scrollbar back to where it was
            vBar.setValue(sPos)

        self._docHandle = tHandle
        SHARED.project.data.setLastHandle(tHandle, "viewer")
        self.docHeader.setHandle(tHandle)
        self.docHeader.setOutline({
            sTitle: (hItem.title, nwStyles.H_LEVEL.get(hItem.level, 0))
            for sTitle, hItem in SHARED.project.index.iterItemHeadings(tHandle)
        })
        self.updateDocMargins()

        QApplication.restoreOverrideCursor()
        self.documentLoaded.emit(tHandle)

        return True

    def reloadText(self) -> None:
        """Reload the text in the current document."""
        if self._docHandle:
            self.loadText(self._docHandle, updateHistory=False)

    def docAction(self, action: nwDocAction) -> bool:
        """Process document actions on the current document."""
        logger.debug("Requesting action: '%s'", action.name)
        if self._docHandle is None:
            logger.error("No document open")
            return False
        if action in (nwDocAction.CUT, nwDocAction.COPY):
            self.copy()
        elif action == nwDocAction.SEL_ALL:
            self._makeSelection(QtSelectDocument)
        elif action == nwDocAction.SEL_PARA:
            self._makeSelection(QtSelectBlock)
        elif action == nwDocAction.ZOOM_IN:
            self.zoomIn()
        elif action == nwDocAction.ZOOM_OUT:
            self.zoomOut()
        elif action == nwDocAction.ZOOM_RESET:
            self.zoomReset()
        else:
            logger.debug("Unknown or unsupported document action '%s'", action)
            return False
        return True

    def anyFocus(self) -> bool:
        """Check if any widget or child widget has focus."""
        return self.hasFocus() or self.isAncestorOf(QApplication.focusWidget())

    def clearNavHistory(self) -> None:
        """Clear the navigation history."""
        self.docHistory.clear()

    def updateDocMargins(self) -> None:
        """Automatically adjust the margins so the text is centred."""
        wW = self.width()
        wH = self.height()
        cM = CONFIG.textMargin

        vBar = self.verticalScrollBar()
        sW = vBar.width() if vBar and vBar.isVisible() else 0

        hBar = self.horizontalScrollBar()
        sH = hBar.height() if hBar and hBar.isVisible() else 0

        tM = cM
        if CONFIG.textWidth > 0:
            tW = CONFIG.getTextWidth()
            tM = max((wW - sW - tW) // 2, cM)

        tB = self.frameWidth()
        tW = wW - 2 * tB - sW
        tH = self.docHeader.height()
        fH = self.docFooter.height()
        fY = wH - fH - tB - sH

        self.docHeader.setGeometry(tB, tB, tW, tH)
        self.docFooter.setGeometry(tB, fY, tW, fH)
        self.setViewportMargins(tM, max(cM, tH), tM, max(cM, fH))

    ##
    #  Setters
    ##

    def setScrollPosition(self, pos: int) -> None:
        """Set the scrollbar position."""
        if (vBar := self.verticalScrollBar()) and vBar.isVisible():
            vBar.setValue(pos)

    ##
    #  Public Slots
    ##

    @pyqtSlot(str, Enum)
    def onProjectItemChanged(self, tHandle: str, change: nwChange) -> None:
        """Update the header title bar if needed."""
        if tHandle == self._docHandle and change == nwChange.UPDATE:
            self.docHeader.setHandle(tHandle)
            self.updateDocMargins()

    @pyqtSlot(str)
    def navigateTo(self, anchor: str) -> None:
        """Go to a specific #link in the document."""
        if isinstance(anchor, str) and anchor.startswith("#"):
            logger.debug("Moving to anchor '%s'", anchor)
            self.setSource(QUrl(anchor))

    @pyqtSlot()
    def zoomReset(self) -> None:
        """Reset the editor's font size to the user's configured size."""
        if document := self.document():  # pragma: no branch
            font = fontMatcher(CONFIG.textFont)
            self.setFont(font)
            document.setDefaultFont(font)

    @pyqtSlot(list, list)
    def updateChangedTags(self, updated: list[str], deleted: list[str]) -> None:
        """Tags have changed, so just in case we rehighlight them."""
        if updated or deleted:
            self._hoverCard.pruneCache(updated + deleted)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def navBackward(self) -> None:
        """Navigate backwards in the document view history."""
        self.docHistory.backward()

    @pyqtSlot()
    def navForward(self) -> None:
        """Navigate forwards in the document view history."""
        self.docHistory.forward()

    @pyqtSlot("QUrl")
    def _linkClicked(self, url: QUrl) -> None:
        """Process a clicked link in the document."""
        if link := url.url():
            logger.debug("Clicked link: '%s'", link)
            if (bits := link.partition("_")) and bits[0] == "#tag" and bits[2]:
                self.loadDocumentTagRequest.emit(bits[2], nwDocMode.VIEW)
            elif link.startswith("#"):
                self.navigateTo(link)
            elif link.startswith(("http", "file")):
                QDesktopServices.openUrl(QUrl(url))

    @pyqtSlot()
    def _showHoverCard(self) -> None:
        """Show the reference tag hover card if the position last
        recorded by mouseMoveEvent is still over a tag anchor once the
        hover delay has elapsed.
        """
        href = self.anchorAt(self._hoverPos)
        tag = href[5:] if href.startswith("#tag_") else ""
        if tag and self._hoverCard.setTag(tag) and (viewport := self.viewport()):
            rect = self.cursorRect(self.cursorForPosition(self._hoverPos))
            pos = QPoint(self._hoverPos.x(), rect.bottom() + 4)
            self._hoverCard.showAt(viewport.mapToGlobal(pos), viewport.width(), viewport.height())
        else:
            self._hoverCard.scheduleHide()

    @pyqtSlot("QPoint")
    def _openContextMenu(self, point: QPoint) -> None:
        """Open context menu at location."""
        userCursor = self.textCursor()
        userSelection = userCursor.hasSelection()

        ctxMenu = QMenu(self)

        if userSelection:
            action = qtAddAction(ctxMenu, self.tr("Copy"))
            action.triggered.connect(qtLambda(self.docAction, nwDocAction.COPY))
            ctxMenu.addSeparator()

        action = qtAddAction(ctxMenu, self.tr("Select All"))
        action.triggered.connect(qtLambda(self.docAction, nwDocAction.SEL_ALL))

        action = qtAddAction(ctxMenu, self.tr("Select Word"))
        action.triggered.connect(qtLambda(self._makePosSelection, QtSelectWord, point))

        action = qtAddAction(ctxMenu, self.tr("Select Paragraph"))
        action.triggered.connect(qtLambda(self._makePosSelection, QtSelectBlock, point))

        # Open the context menu
        if viewport := self.viewport():  # pragma: no branch
            ctxMenu.exec(viewport.mapToGlobal(point))

        ctxMenu.setParent(None)

    ##
    #  Events
    ##

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Update document margins when widget is resized."""
        self.updateDocMargins()
        super().resizeEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Track mouse movement to trigger the reference tag hover
        card. Unlike the editor, anchorAt() is a proper hit test
        against the rendered link, so no extra care is needed to
        reject hovers past the end of a line.
        """
        pos = event.pos()
        if self.anchorAt(pos).startswith("#tag_"):
            self._hoverPos = pos
            self._timerHover.start()
        else:
            self._timerHover.stop()
            self._hoverCard.scheduleHide()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Request that the hover card be hidden when the mouse leaves
        the viewer. The hide is delayed rather than immediate, so the
        mouse has time to move onto the card itself, which cancels it.
        """
        self._timerHover.stop()
        self._hoverCard.scheduleHide()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Capture mouse click events on the document."""
        if event.button() == Qt.MouseButton.BackButton:
            self.navBackward()
        elif event.button() == Qt.MouseButton.ForwardButton:
            self.navForward()
        else:
            super().mouseReleaseEvent(event)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Overload drag enter event to handle dragged items."""
        if (data := event.mimeData()) and data.hasFormat(nwConst.MIME_HANDLE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """Overload drag move event to handle dragged items."""
        if (data := event.mimeData()) and data.hasFormat(nwConst.MIME_HANDLE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Overload drop event to handle dragged items."""
        if (data := event.mimeData()) and data.hasFormat(nwConst.MIME_HANDLE):
            if (handles := decodeMimeHandles(data)) and SHARED.project.tree.checkType(handles[0], nwItemType.FILE):
                self.openDocumentRequest.emit(handles[0], nwDocMode.VIEW, "", True)
        else:
            super().dropEvent(event)

    ##
    #  Internal Functions
    ##

    def _makeSelection(self, selType: QTextCursor.SelectionType) -> None:
        """Handle selection of text based on a selection mode."""
        cursor = self.textCursor()
        cursor.clearSelection()
        cursor.select(selType)

        if selType == QtSelectBlock:
            # This selection mode also selects the preceding paragraph
            # separator, which we want to avoid.
            posS = cursor.selectionStart()
            posE = cursor.selectionEnd()
            selTxt = cursor.selectedText()
            if selTxt.startswith(nwUnicode.U_PSEP):
                cursor.setPosition(posS + 1, QtMoveAnchor)
                cursor.setPosition(posE, QtKeepAnchor)

        self.setTextCursor(cursor)

    def _makePosSelection(self, selType: QTextCursor.SelectionType, pos: QPoint) -> None:
        """Handle text selection at a given location."""
        self.setTextCursor(self.cursorForPosition(pos))
        self._makeSelection(selType)
