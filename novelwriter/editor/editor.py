"""
novelWriter - GUI Document Editor
=================================

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

import bisect
import logging

from enum import Enum, IntFlag
from time import time

from PyQt6 import sip
from PyQt6.QtCore import (
    QEvent,
    QMimeData,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    QUrl,
    QVariant,
    pyqtSignal,
    pyqtSlot,
)
from PyQt6.QtGui import (
    QCursor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QInputMethodEvent,
    QKeyEvent,
    QMouseEvent,
    QPalette,
    QResizeEvent,
    QShortcut,
    QTextBlock,
    QTextCharFormat,
    QTextCursor,
    QTextDocument,
    QTextFormat,
    QTextOption,
    QWheelEvent,
)
from PyQt6.QtWidgets import QApplication, QFrame, QMenu, QTextEdit, QWidget

from novelwriter import CONFIG, SHARED
from novelwriter.common import (
    decodeMimeHandles,
    fontMatcher,
    minmax,
    qtAddAction,
    qtAddMenu,
    qtLambda,
    qtWeakLambda,
    transferCase,
)
from novelwriter.constants import nwConst, nwKeyWords, nwShortcode, nwStyles, nwUnicode
from novelwriter.core.document import ProjectDocument
from novelwriter.dialogs.editlabel import GuiEditLabel
from novelwriter.dialogs.editlink import GuiEditLink
from novelwriter.editor.completer import CommandCompleter
from novelwriter.editor.editordocument import GuiTextDocument
from novelwriter.editor.editsearch import GuiDocEditSearch
from novelwriter.editor.edittoolbar import GuiDocToolBar
from novelwriter.editor.footer import GuiDocEditFooter
from novelwriter.editor.header import GuiDocEditHeader
from novelwriter.editor.highlighter import BLOCK_META, BLOCK_TITLE
from novelwriter.editor.hovercard import GuiDocHoverCard
from novelwriter.editor.runnables import T_TextCheckPayload, TextCheckDispatcher, WordCounterDispatcher
from novelwriter.editor.textblock import T_TextCheckList, TextBlockData
from novelwriter.enum import (
    nwChange,
    nwComment,
    nwDocAction,
    nwDocInsert,
    nwDocMode,
    nwItemClass,
    nwItemType,
    nwVimMode,
)
from novelwriter.extensions.eventfilters import WheelEventFilter
from novelwriter.formats.fromqdoc import FromQTextDocument
from novelwriter.text.autoreplace import TextAutoReplace
from novelwriter.text.formats import processHeading
from novelwriter.text.patterns import REGEX_PATTERNS
from novelwriter.tools.lipsum import GuiLipsum
from novelwriter.types import (
    QAnimDeleteWhenStopped,
    QKeyRedo,
    QKeySelectAll,
    QKeyUndo,
    QtAlignJustify,
    QtImCurrentSelection,
    QtImCursorRectangle,
    QtKeepAnchor,
    QtKeyDown,
    QtKeyEnter,
    QtKeyEscape,
    QtKeyLeft,
    QtKeyPageDown,
    QtKeyPageUp,
    QtKeyReturn,
    QtKeyRight,
    QtKeyUp,
    QtModCtrl,
    QtModNone,
    QtModShift,
    QtMoveAnchor,
    QtMoveDown,
    QtMoveEnd,
    QtMoveEndOfLine,
    QtMoveEndOfWord,
    QtMoveLeft,
    QtMoveNextChar,
    QtMoveNextWord,
    QtMovePreviousWord,
    QtMoveRight,
    QtMoveStart,
    QtMoveStartOfLine,
    QtMoveUp,
    QtScrollAlwaysOff,
    QtScrollAsNeeded,
    QtSelectBlock,
    QtSelectDocument,
    QtSelectLine,
    QtSelectWord,
    QtTransparent,
    QtWidgetShortcut,
)

logger = logging.getLogger(__name__)

T_TextCheckBlock = tuple[QTextBlock, TextBlockData, int]
T_TextCheckJob = tuple[int, list[T_TextCheckBlock]]
T_Selections = list[QTextEdit.ExtraSelection]
T_SelCache = dict[int, tuple[T_TextCheckList, T_Selections]]

MOVE_KEYS = (QtKeyLeft, QtKeyRight, QtKeyUp, QtKeyDown, QtKeyPageUp, QtKeyPageDown)
ENTER_KEYS = (QtKeyReturn, QtKeyEnter)


class _SelectAction(Enum):
    NO_DECISION = 0
    KEEP_SELECTION = 1
    KEEP_POSITION = 2
    MOVE_AFTER = 3


class _TagAction(IntFlag):
    NONE = 0b00
    FOLLOW = 0b01
    CREATE = 0b10


class GuiDocEditor(QTextEdit):
    """Gui Widget: Main Document Editor."""

    __slots__ = (
        "_autoReplace",
        "_checkDispatcher",
        "_checkJob",
        "_checkJobId",
        "_checkPassPos",
        "_completer",
        "_dirtyBlocks",
        "_doReplace",
        "_docChanged",
        "_docCounter",
        "_docHandle",
        "_followTagEdit",
        "_followTagView",
        "_formatErrFormat",
        "_formatSelections",
        "_hoverCard",
        "_hoverPos",
        "_keyContext",
        "_lastActive",
        "_lastDocTask",
        "_lastEdit",
        "_lastFind",
        "_lineColor",
        "_nextLine",
        "_nwDocument",
        "_nwItem",
        "_prevLine",
        "_qDocument",
        "_queuePos",
        "_searchFormat",
        "_searchSelections",
        "_selCacheFormat",
        "_selCacheSpell",
        "_selCounter",
        "_selection",
        "_spellErrFormat",
        "_spellPassNotify",
        "_spellSelections",
        "_suppressed",
        "_timerCheck",
        "_timerDoc",
        "_timerHover",
        "_timerSel",
        "_timerTextCheck",
        "_trActions",
        "_trAddWord",
        "_trCopy",
        "_trCreateNote",
        "_trCut",
        "_trEditTag",
        "_trIgnoreWord",
        "_trMoveText",
        "_trNoSuggest",
        "_trOpenURL",
        "_trPaste",
        "_trSelectAll",
        "_trSelectPara",
        "_trSelectWord",
        "_trSetName",
        "_trSpellSuggest",
        "_trSplitDoc",
        "_trViewTag",
        "_vim",
        "_vpMargin",
        "_zoomIn",
        "_zoomOut",
        "_zoomReset",
        "changeFocusState",
        "closeSearch",
        "docFooter",
        "docHeader",
        "docSearch",
        "docToolBar",
        "searchVisible",
        "wheelEventFilter",
    )

    SEP_TABLE = str.maketrans({
        nwUnicode.U_LSEP: "\n",  # Line Separator
        nwUnicode.U_PSEP: "\n",  # Paragraph Separator
    })

    closeEditorRequest = pyqtSignal()
    docTextChanged = pyqtSignal(str, float)
    editedStatusChanged = pyqtSignal(bool)
    itemHandleChanged = pyqtSignal(str)
    loadDocumentTagRequest = pyqtSignal(str, Enum)
    openDocumentRequest = pyqtSignal(str, Enum, str, bool)
    requestNewNoteCreation = pyqtSignal(str, nwItemClass)
    requestNextDocument = pyqtSignal(str, bool, bool)
    requestProjectItemRenamed = pyqtSignal(str, str)
    requestProjectItemSelected = pyqtSignal(str, bool)
    spellCheckStateChanged = pyqtSignal(bool)
    toggleFocusModeRequest = pyqtSignal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent=parent)

        logger.debug("Create: GuiDocEditor")

        # Class Variables
        self._nwDocument = None
        self._nwItem = None

        self._docChanged = False  # Flag for changed status of document
        self._docHandle = None  # The handle of the open document
        self._vpMargin = 0  # The editor viewport margin, set during init

        # Document Variables
        self._lastEdit = 0.0  # Timestamp of last edit
        self._lastActive = 0.0  # Timestamp of last activity
        self._lastDocTask = -1.0  # Timestamp of last edit processed by _runDocumentTasks
        self._lastFind = None  # Position of the last found search word
        self._doReplace = False  # Switch to temporarily disable auto-replace
        self._lineColor = QtTransparent
        self._selection = QTextEdit.ExtraSelection()

        # Search Variables
        self._searchFormat = QTextCharFormat()
        self._searchSelections: T_Selections = []

        # Spell and Format Check Variables
        self._spellErrFormat = QTextCharFormat()
        self._formatErrFormat = QTextCharFormat()
        self._spellSelections: T_Selections = []
        self._formatSelections: T_Selections = []
        self._selCacheSpell: T_SelCache = {}
        self._selCacheFormat: T_SelCache = {}
        self._dirtyBlocks: dict[int, QTextBlock] = {}
        self._suppressed = False
        self._checkPassPos: int | None = None
        self._spellPassNotify = False
        self._checkJob: T_TextCheckJob | None = None
        self._checkJobId = 0
        self._checkDispatcher = TextCheckDispatcher(self, self._textCheckResults)

        # Context Menu Translation
        self._trSetName = self.tr("Set as Document Name")
        self._trOpenURL = self.tr("Open URL")
        self._trViewTag = self.tr("View Tag Source")
        self._trEditTag = self.tr("Edit Tag Source")
        self._trCreateNote = self.tr("Create Note for Tag")
        self._trCut = self.tr("Cut")
        self._trCopy = self.tr("Copy")
        self._trPaste = self.tr("Paste")
        self._trSelectAll = self.tr("Select All")
        self._trSelectWord = self.tr("Select Word")
        self._trSelectPara = self.tr("Select Paragraph")
        self._trMoveText = self.tr("Move Text to New Document")
        self._trSplitDoc = self.tr("Split Document at Cursor")
        self._trActions = self.tr("More Actions")
        self._trSpellSuggest = self.tr("Spelling Suggestion(s)")
        self._trNoSuggest = self.tr("No Suggestions")
        self._trIgnoreWord = self.tr("Ignore Word")
        self._trAddWord = self.tr("Add Word to Dictionary")

        # Auto-Replace
        self._autoReplace = TextAutoReplace()

        # Completer
        self._completer = CommandCompleter(self)
        self._completer.insertText.connect(self._insertCompletion)

        # Create Custom Document
        self._qDocument = GuiTextDocument(self)
        self.setDocument(self._qDocument)

        # Connect Editor and Document Signals
        self._queuePos = None  # Queue cursor position for large documents
        self._qDocument.contentsChange.connect(self._docChange)
        self._qDocument.layoutSettled.connect(self._onLayoutSettled)
        self.selectionChanged.connect(self._updateSelectedStatus)
        self.cursorPositionChanged.connect(self._cursorMoved)

        # Document Title
        self.docHeader = GuiDocEditHeader(self)
        self.docFooter = GuiDocEditFooter(self)
        self.docSearch = GuiDocEditSearch(self)
        self.docToolBar = GuiDocToolBar(self)

        # Connect Widget Signals
        self.docHeader.closeDocumentRequest.connect(self._closeCurrentDocument)
        self.docHeader.toggleToolBarRequest.connect(self._toggleToolBarVisibility)
        self.docToolBar.requestDocAction.connect(self.docAction)

        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._openContextMenu)

        # Editor Settings
        self.setMinimumWidth(300)
        self.setAutoFillBackground(True)
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setAcceptDrops(True)
        self.setAcceptRichText(False)

        # Custom Shortcuts
        self._keyContext = QShortcut(self)
        self._keyContext.setKey("Ctrl+.")
        self._keyContext.setContext(QtWidgetShortcut)
        self._keyContext.activated.connect(self._openContextFromCursor)

        self._followTagView = QShortcut(self)
        self._followTagView.setKeys(["Ctrl+Return", "Ctrl+Enter"])
        self._followTagView.setContext(QtWidgetShortcut)
        self._followTagView.activated.connect(qtWeakLambda(self._processTag))

        self._followTagEdit = QShortcut(self)
        self._followTagEdit.setKeys(["Ctrl+Shift+Return", "Ctrl+Shift+Enter"])
        self._followTagEdit.setContext(QtWidgetShortcut)
        self._followTagEdit.activated.connect(qtWeakLambda(self._processTag, edit=True))

        self._pastePlainText = QShortcut(self)
        self._pastePlainText.setKeys(["Ctrl+Shift+V"])
        self._pastePlainText.setContext(QtWidgetShortcut)
        self._pastePlainText.activated.connect(self._pasteAsPlainText)

        self._prevLine = QShortcut(self)
        self._prevLine.setKey("Ctrl+Up")
        self._prevLine.setContext(QtWidgetShortcut)
        self._prevLine.activated.connect(qtWeakLambda(self._skipToParagraph, -1))

        self._nextLine = QShortcut(self)
        self._nextLine.setKey("Ctrl+Down")
        self._nextLine.setContext(QtWidgetShortcut)
        self._nextLine.activated.connect(qtWeakLambda(self._skipToParagraph, 1))

        # Set Up Document Word Counter
        self._timerDoc = QTimer(self)
        self._timerDoc.timeout.connect(self._runDocumentTasks)
        self._timerDoc.setSingleShot(True)
        self._timerDoc.setInterval(5000)
        self._docCounter = WordCounterDispatcher(self, self._updateDocCounts)

        # Set Up Selection Word Counter
        self._timerSel = QTimer(self)
        self._timerSel.timeout.connect(self._runSelCounter)
        self._timerSel.setSingleShot(True)
        self._timerSel.setInterval(500)
        self._selCounter = WordCounterDispatcher(self, self._updateSelCounts)

        # Set Up Spell Underline Refresh
        self._timerCheck = QTimer(self)
        self._timerCheck.timeout.connect(self._updateCheckSelections)
        self._timerCheck.setSingleShot(True)
        self._timerCheck.setInterval(0)

        if vBar := self.verticalScrollBar():  # pragma: no branch
            vBar.valueChanged.connect(qtWeakLambda(self._restartCheckTimer))

        # Set Up Spell Check Debounce
        self._timerTextCheck = QTimer(self)
        self._timerTextCheck.timeout.connect(self._dispatchTextCheck)
        self._timerTextCheck.setSingleShot(True)
        self._timerTextCheck.setInterval(300)

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

        # Function Mapping
        self.closeSearch = self.docSearch.closeSearch
        self.searchVisible = self.docSearch.isVisible
        self.changeFocusState = self.docHeader.changeFocusState

        # Vim State for vimMode
        self._vim = VimState()

        # Finalise
        self.updateSyntaxColors()
        self.initEditor()

        logger.debug("Ready: GuiDocEditor")

    ##
    #  Properties
    ##

    @property
    def docChanged(self) -> bool:
        """Return the changed status of the document."""
        return self._docChanged

    @property
    def docHandle(self) -> str | None:
        """Return the handle of the currently open document."""
        return self._docHandle

    @property
    def lastActive(self) -> float:
        """Return the last active timestamp for the user."""
        return self._lastActive

    @property
    def isEmpty(self) -> bool:
        """Check if the current document is empty."""
        return self._qDocument.isEmpty()

    ##
    #  Methods
    ##

    def clearEditor(self) -> None:
        """Clear the current document and reset all document-related
        flags and counters.
        """
        self._nwDocument = None
        self.setReadOnly(True)
        self.clear()
        self._timerDoc.stop()
        self._timerSel.stop()
        self._queuePos = None

        self._docHandle = None
        self._lastEdit = 0.0
        self._lastActive = 0.0
        self._lastDocTask = -1.0
        self._lastFind = None
        self._doReplace = False

        self.setDocumentChanged(False)
        self.docHeader.clearHeader()
        self.docFooter.setHandle(self._docHandle)
        self.docToolBar.setVisible(False)

        self._timerCheck.stop()
        self._timerTextCheck.stop()
        self._timerHover.stop()
        self._hoverCard.hide()
        self._hoverCard.clearCache()
        self._checkPassPos = None
        self._spellPassNotify = False
        self._checkJob = None
        self._dirtyBlocks.clear()
        self._spellSelections.clear()
        self._formatSelections.clear()
        self._selCacheSpell.clear()
        self._selCacheFormat.clear()
        self._searchSelections.clear()
        self.setExtraSelections([])

        self.itemHandleChanged.emit("")

    def updateTheme(self) -> None:
        """Update theme elements."""
        logger.debug("Theme Update: GuiDocEditor")

        self.docSearch.updateTheme()
        self.docHeader.updateTheme()
        self.docFooter.updateTheme()
        self.docToolBar.updateTheme()

    def updateSyntaxColors(self) -> None:
        """Update the syntax highlighting theme."""
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
        self._hoverCard.updateTheme()

        self._lineColor = syntax.line
        self._selection.format.setBackground(self._lineColor)
        self._selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)

        self._spellErrFormat = QTextCharFormat()
        self._spellErrFormat.setUnderlineColor(syntax.spell)
        self._spellErrFormat.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SpellCheckUnderline)

        self._formatErrFormat = QTextCharFormat()
        self._formatErrFormat.setUnderlineColor(syntax.error)
        self._formatErrFormat.setUnderlineStyle(QTextCharFormat.UnderlineStyle.SingleUnderline)

        self._searchFormat = QTextCharFormat()
        self._searchFormat.setBackground(SHARED.theme.searchCol)

        for selection in self._searchSelections:
            selection.format = self._searchFormat
        for _, selections in self._selCacheSpell.values():
            for selection in selections:
                selection.format = self._spellErrFormat
        for _, selections in self._selCacheFormat.values():
            for selection in selections:
                selection.format = self._formatErrFormat
        self._applyExtraSelections()

    def initEditor(self) -> None:
        """Initialise or re-initialise the editor with the user's
        settings. This function is both called when the editor is
        created, and when the user changes the main editor preferences.
        """
        self.docFooter.initSettings()

        # Reload spell check and dictionaries
        SHARED.updateSpellCheckLanguage()

        # Set the font. See issues #1862 and #1875.
        font = fontMatcher(CONFIG.textFont)
        self.setFont(font)
        self._qDocument.setDefaultFont(font)
        self.docHeader.updateFont()
        self.docFooter.updateFont()
        self.docSearch.updateFont()

        # Update highlighter settings
        self._qDocument.syntaxHighlighter.initHighlighter()

        # Update the viewport
        self.initViewport()

        # Also set the document text options for the document text flow
        options = QTextOption()
        if CONFIG.doJustify:
            options.setAlignment(QtAlignJustify)
        if CONFIG.showTabsNSpaces:
            options.setFlags(options.flags() | QTextOption.Flag.ShowTabsAndSpaces)
        if CONFIG.showLineEndings:
            options.setFlags(options.flags() | QTextOption.Flag.ShowLineAndParagraphSeparators)
        self._qDocument.setDefaultTextOption(options)

        # Refresh sizes
        self.setTabStopDistance(CONFIG.tabWidth)
        self.setCursorWidth(CONFIG.cursorWidth)
        self._spellSelections.clear()
        self._formatSelections.clear()
        self._selCacheSpell.clear()
        self._selCacheFormat.clear()
        self.setExtraSelections([])
        self._cursorMoved()

        # If we have a document open, we should refresh it in case the
        # font changed, otherwise we just clear the editor entirely,
        # which makes it read only.
        if self._docHandle:
            self._qDocument.markLayoutBusy()
            self.setReadOnly(self._qDocument.isLayoutBusy())
            self._qDocument.setLineHeight(CONFIG.lineHeight)
            self._qDocument.syntaxHighlighter.rehighlight()
            self._qDocument.markContentsDirty(0, self._qDocument.characterCount())
            if not self._qDocument.isLayoutBusy():
                self._beginCheckPass()
            self.docHeader.setHandle(self._docHandle)
            # Restart the settle countdown one last time
            self._qDocument.markLayoutBusy()
        else:
            self.clearEditor()

        # Refresh Vim Mode
        self.setVimMode(nwVimMode.NORMAL)

    def initViewport(self) -> None:
        """Initialise the settings of the editor viewport."""
        # Set default text margins
        # Due to cursor visibility, a part of the margin must be
        # allocated to the document itself. See issue #1112.
        self._qDocument.setDocumentMargin(4)
        self._vpMargin = max(CONFIG.textMargin - 4, 0)
        self.setViewportMargins(self._vpMargin, self._vpMargin, self._vpMargin, self._vpMargin)

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

    def initSettings(self, updateVimMode: bool = False) -> None:
        """Initialise non-expensive settings."""
        if self._docHandle:
            self.docHeader.setHandle(self._docHandle)
            self.docSearch.setAutoReplaceEnabled(CONFIG.doReplace)
        if updateVimMode:
            self.setVimMode(nwVimMode.NORMAL)

    def loadText(self, tHandle: str, tLine: int | None = None) -> bool:
        """Load text from a document into the editor. If we have an I/O
        error, we must handle this and clear the editor so that we don't
        risk overwriting the file if it exists. This can for instance
        happen if the file contains binary elements or an encoding that
        novelWriter does not support. If loading is successful, or the
        document is new (empty string), we set up the editor for editing
        the file.
        """
        self._nwDocument = SHARED.project.storage.getDocument(tHandle)
        self._nwItem = self._nwDocument.nwItem
        if not (self._nwItem and self._nwItem.itemType == nwItemType.FILE):
            logger.debug("Requested item '%s' is not a document", tHandle)
            self.clearEditor()
            return False

        if (text := self._nwDocument.readDocument()) is None:
            # There was an I/O error
            self.clearEditor()
            return False

        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        self._docHandle = tHandle

        self._allowAutoReplace(False)
        self._qDocument.setTextContent(text, tHandle)
        self._allowAutoReplace(True)
        if not self._qDocument.isLayoutBusy():
            self._beginCheckPass()

        self._lastEdit = time()
        self._lastActive = time()
        self._runDocumentTasks()

        self.updateDocMargins()

        if isinstance(tLine, int):
            self.setCursorLine(tLine)
        else:
            self.moveCursorAfterLoad(self._nwItem.cursorPos)

        if self._queuePos is None:
            # Covers tLine being 0 or an invalid line, which setCursorLine
            # silently no-ops on, and would otherwise skip clearing read-only.
            self.setReadOnly(False)

        self.docHeader.setHandle(tHandle)
        self.docFooter.setHandle(tHandle)

        # This is a hack to fix invisible cursor on an empty document
        if self._qDocument.characterCount() <= 1:
            self.setPlainText("\n")
            self.setPlainText("")
            self.setCursorPosition(0)

        self.setDocumentChanged(False)
        self._qDocument.clearUndoRedoStacks()
        self.docToolBar.setVisible(CONFIG.showEditToolBar)

        # Process State Changes
        SHARED.project.data.setLastHandle(tHandle, "editor")
        self.itemHandleChanged.emit(tHandle)

        # Finalise
        QApplication.restoreOverrideCursor()
        SHARED.newStatusMessage(self.tr("Opened Document: {0}").format(self._nwItem.itemName))

        return True

    def replaceText(self, text: str) -> None:
        """Replace the text of the current document with the provided
        text. This also clears undo history.
        """
        QApplication.setOverrideCursor(QCursor(Qt.CursorShape.WaitCursor))
        self.setPlainText(text)
        self._qDocument.setLineHeight(CONFIG.lineHeight)
        self.updateDocMargins()
        self.setDocumentChanged(True)
        QApplication.restoreOverrideCursor()

    def saveText(self) -> bool:
        """Save the text currently in the editor to the ProjectDocument
        object, and update the ProjectItem meta data.
        """
        if self._nwItem is None or self._nwDocument is None:
            logger.error("Cannot save text as no document is open")
            return False

        tHandle = self._nwItem.itemHandle
        if self._docHandle != tHandle:
            logger.error("Editor handle '%s' and item handle '%s' do not match", self._docHandle, tHandle)
            return False

        text = self.getText()
        if not self._nwDocument.writeDocument(text):
            saveOk = False
            if self._nwDocument.hashError and SHARED.question(
                self.tr(
                    "This document has been changed outside of novelWriter "
                    "while it was open. Overwrite the file on disk?"
                )
            ):
                saveOk = self._nwDocument.writeDocument(text, forceWrite=True)

            if not saveOk:
                SHARED.error(self.tr("Could not save document."), info=self._nwDocument.error)
                return False

        self.setDocumentChanged(False)
        self.docTextChanged.emit(self._docHandle, self._lastEdit)
        SHARED.project.index.scanText(tHandle, text)

        SHARED.newStatusMessage(self.tr("Saved Document: {0}").format(self._nwItem.itemName))

        return True

    def cursorIsVisible(self) -> bool:
        """Check if the cursor is visible in the editor."""
        viewport = self.viewport()
        height = viewport.height() if viewport else 0
        return self.cursorRect().top() > 0 and self.cursorRect().bottom() < height

    def ensureCursorVisible(self, *, centre: bool) -> None:
        """Ensure cursor is visible, and optionally centre it."""
        if (viewport := self.viewport()) and (vBar := self.verticalScrollBar()):  # pragma: no branch
            cT = self.cursorRect().top()
            cB = self.cursorRect().bottom()
            vH = viewport.height()
            if centre:
                cY = (cT + cB) // 2
                vBar.setValue(vBar.value() + cY - vH // 2)
            elif cT < 0:
                vBar.setValue(vBar.value() + cT - 1)
            elif cB > vH:
                vBar.setValue(vBar.value() + (cB - vH) + 1)

    def updateDocMargins(self) -> None:
        """Automatically adjust the margins so the text is centred if
        we have a text width set or we're in Focus Mode. Otherwise, just
        ensure the margins are set correctly.
        """
        wW = self.width()
        wH = self.height()

        vBar = self.verticalScrollBar()
        sW = vBar.width() if vBar and vBar.isVisible() else 0

        hBar = self.horizontalScrollBar()
        sH = hBar.height() if hBar and hBar.isVisible() else 0

        tM = self._vpMargin
        if CONFIG.textWidth > 0 or SHARED.focusMode:
            tW = CONFIG.getTextWidth(SHARED.focusMode)
            tM = max((wW - sW - tW) // 2, self._vpMargin)

        tB = self.frameWidth()
        tW = wW - 2 * tB - sW
        tH = self.docHeader.height()
        fH = self.docFooter.height()
        fY = wH - fH - tB - sH
        self.docHeader.setGeometry(tB, tB, tW, tH)
        self.docFooter.setGeometry(tB, fY, tW, fH)
        self.docToolBar.move(0, tH)

        rH = 0
        if self.docSearch.isVisible():
            rH = self.docSearch.height()
            rW = self.docSearch.width()
            rL = wW - sW - rW - 2 * tB
            self.docSearch.move(rL, 2 * tB)

        uM = max(self._vpMargin, tH, rH)
        lM = max(self._vpMargin, fH)
        self.setViewportMargins(tM, uM, tM, lM)

        self._qDocument.setBottomMargin(max(wH - 2 * tB - uM - lM - sH, 0) if CONFIG.scrollPastEnd else 0)

    ##
    #  Getters
    ##

    def getText(self) -> str:
        """Get the text content of the current document. This method uses
        QTextDocument->toRawText instead of toPlainText. The former preserves
        non-breaking spaces, the latter does not. We still want to get rid of
        paragraph and line separators though.

        See: https://doc.qt.io/qt-6/qtextdocument.html#toPlainText
        """
        return self._qDocument.toRawText().translate(self.SEP_TABLE)

    def getSelectedText(self) -> str:
        """Get currently selected text."""
        if (cursor := self.textCursor()).hasSelection():
            return cursor.selectedText().translate(self.SEP_TABLE)
        return ""

    def getCursorPosition(self) -> int:
        """Find the cursor position in the document. If the editor has a
        selection, return the position of the end of the selection.
        """
        return self.textCursor().selectionEnd()

    ##
    #  Setters
    ##

    def setVimMode(self, mode: nwVimMode) -> None:
        """Change the vim mode."""
        if CONFIG.vimMode:
            if mode == nwVimMode.NORMAL:
                cursor = self.textCursor()
                cursor.clearSelection()
                self.setTextCursor(cursor)
            self._vim.setMode(mode)
            self.docFooter.updateVimModeStatusBar(mode)
        else:
            self.docFooter.updateVimModeStatusBar(None)

    def setDocumentChanged(self, state: bool) -> None:
        """Keep track of the document changed variable, and emit the
        document change signal.
        """
        if self._docChanged != state:
            logger.debug("Document changed status is '%s'", state)
            self._docChanged = state
            self.editedStatusChanged.emit(self._docChanged)

    def setCursorPosition(self, position: int) -> None:
        """Move the cursor to a given position in the document."""
        if (chars := self._qDocument.characterCount()) > 1 and isinstance(position, int):
            cursor = self.textCursor()
            cursor.setPosition(minmax(position, 0, chars - 1))
            self.setTextCursor(cursor)
            self.ensureCursorVisible(centre=True)

    def saveCursorPosition(self) -> None:
        """Save the cursor position to the current project item."""
        if self._nwItem is not None:
            cursPos = self.getCursorPosition()
            self._nwItem.setCursorPos(cursPos)

    def setCursorLine(self, line: int | None) -> None:
        """Move the cursor to a given line in the document."""
        if isinstance(line, int) and line != 0:
            line = self._qDocument.blockCount() + line if line < 0 else line - 1
            if (block := self._qDocument.findBlockByNumber(line)).isValid():
                self.moveCursorAfterLoad(block.position())
                logger.debug("Cursor moved to line %d", line + 1)

    def moveCursorAfterLoad(self, position: int) -> None:
        """Move the cursor to a position, queuing the move until the
        document layout is ready.
        """
        self._qDocument.markLayoutBusy()
        if position > 0 and self._qDocument.isLayoutBusy():
            self.setReadOnly(True)  # Just for safety
            self._queuePos = position
        else:
            self.setReadOnly(False)
            self.setCursorPosition(position)

    def setCursorSelection(self, start: int, length: int) -> None:
        """Make a text selection."""
        if start >= 0 and length > 0:
            cursor = self.textCursor()
            cursor.setPosition(start, QtMoveAnchor)
            cursor.setPosition(start + length, QtKeepAnchor)
            self.setTextCursor(cursor)
            self.ensureCursorVisible(centre=False)

    ##
    #  Spell Checking
    ##

    def toggleSpellCheck(self, state: bool | None) -> None:
        """Toggle spell checking.

        This is the main spell check setting function, and this one
        should call all other setSpellCheck functions in other classes.
        If the spell check state is not defined (None), then toggle the
        current status saved in this class.
        """
        if state is None:
            state = not SHARED.project.data.spellCheck

        if SHARED.spelling.spellLanguage is None:
            state = False

        if state and not CONFIG.hasEnchant:
            SHARED.info(self.tr("Spell checking requires the package PyEnchant. It does not appear to be installed."))
            state = False

        SHARED.project.data.setSpellCheck(state)
        self.spellCheckStateChanged.emit(state)
        self.spellCheckDocument()

        logger.debug("Spell check is set to '%s'", state)

    def spellCheckDocument(self) -> None:
        """Spell check the entire document, and update the status of the
        currently loaded text.
        """
        logger.debug("Running spell checker")
        self._spellPassNotify = SHARED.project.data.spellCheck
        if not self._qDocument.isLayoutBusy():
            self._beginCheckPass()

    ##
    #  General Class Methods
    ##

    def docAction(self, action: nwDocAction) -> bool:
        """Perform an action on the current document based on an action
        flag. This is just a single entry point wrapper function to
        ensure all the feature functions get the correct information
        passed to it without having to consider the internal logic of
        this class when calling these actions from other classes.
        """
        if self._docHandle is None:
            logger.error("No document open")
            return False

        if not isinstance(action, nwDocAction):
            logger.error("Not a document action")
            return False

        logger.debug("Requesting action: %s", action.name)

        cursor = self.textCursor()
        noFormat = (
            (block := cursor.block()).isValid()
            and (text := block.text())
            and text.startswith(("@", "# ", "## ", "### ", "#### ", "#! ", "##! ", "###! "))
        )

        self._allowAutoReplace(False)
        if action == nwDocAction.UNDO:
            self.undo()
        elif action == nwDocAction.REDO:
            self.redo()
        elif action == nwDocAction.CUT:
            self.cut()
        elif action == nwDocAction.COPY:
            self.copy()
        elif action == nwDocAction.PASTE:
            self.paste()
        elif action == nwDocAction.MD_ITALIC and not noFormat:
            self._toggleFormat(1, "_")
        elif action == nwDocAction.MD_BOLD and not noFormat:
            self._toggleFormat(1 if CONFIG.singleStarBold else 2, "*")
        elif action == nwDocAction.MD_STRIKE and not noFormat:
            self._toggleFormat(2, "~")
        elif action == nwDocAction.MD_MARK and not noFormat:
            self._toggleFormat(2, "=")
        elif action == nwDocAction.MD_LINK and not noFormat:
            self._formatLink()
        elif action == nwDocAction.S_QUOTE:
            self._wrapSelection(CONFIG.fmtSQuoteOpen, CONFIG.fmtSQuoteClose)
        elif action == nwDocAction.D_QUOTE:
            self._wrapSelection(CONFIG.fmtDQuoteOpen, CONFIG.fmtDQuoteClose)
        elif action == nwDocAction.SEL_ALL:
            self._makeSelection(QtSelectDocument)
        elif action == nwDocAction.SEL_PARA:
            self._makeSelection(QtSelectBlock)
        elif action == nwDocAction.BLOCK_H1:
            self._formatBlock(nwDocAction.BLOCK_H1)
        elif action == nwDocAction.BLOCK_H2:
            self._formatBlock(nwDocAction.BLOCK_H2)
        elif action == nwDocAction.BLOCK_H3:
            self._formatBlock(nwDocAction.BLOCK_H3)
        elif action == nwDocAction.BLOCK_H4:
            self._formatBlock(nwDocAction.BLOCK_H4)
        elif action == nwDocAction.BLOCK_COM:
            self._iterFormatBlocks(nwDocAction.BLOCK_COM)
        elif action == nwDocAction.BLOCK_IGN:
            self._iterFormatBlocks(nwDocAction.BLOCK_IGN)
        elif action == nwDocAction.BLOCK_TXT:
            self._iterFormatBlocks(nwDocAction.BLOCK_TXT)
        elif action == nwDocAction.BLOCK_TTL:
            self._formatBlock(nwDocAction.BLOCK_TTL)
        elif action == nwDocAction.BLOCK_UNN:
            self._formatBlock(nwDocAction.BLOCK_UNN)
        elif action == nwDocAction.BLOCK_HSC:
            self._formatBlock(nwDocAction.BLOCK_HSC)
        elif action == nwDocAction.REPL_SNG:
            self._replaceQuotes("'", CONFIG.fmtSQuoteOpen, CONFIG.fmtSQuoteClose)
        elif action == nwDocAction.REPL_DBL:
            self._replaceQuotes('"', CONFIG.fmtDQuoteOpen, CONFIG.fmtDQuoteClose)
        elif action == nwDocAction.RM_BREAKS:
            self._removeInParLineBreaks()
        elif action == nwDocAction.ALIGN_L and not noFormat:
            self._formatBlock(nwDocAction.ALIGN_L)
        elif action == nwDocAction.ALIGN_C and not noFormat:
            self._formatBlock(nwDocAction.ALIGN_C)
        elif action == nwDocAction.ALIGN_R and not noFormat:
            self._formatBlock(nwDocAction.ALIGN_R)
        elif action == nwDocAction.INDENT_L and not noFormat:
            self._formatBlock(nwDocAction.INDENT_L)
        elif action == nwDocAction.INDENT_R and not noFormat:
            self._formatBlock(nwDocAction.INDENT_R)
        elif action == nwDocAction.SC_ITALIC and not noFormat:
            self._wrapSelection(nwShortcode.ITALIC_O, nwShortcode.ITALIC_C)
        elif action == nwDocAction.SC_BOLD and not noFormat:
            self._wrapSelection(nwShortcode.BOLD_O, nwShortcode.BOLD_C)
        elif action == nwDocAction.SC_STRIKE and not noFormat:
            self._wrapSelection(nwShortcode.STRIKE_O, nwShortcode.STRIKE_C)
        elif action == nwDocAction.SC_ULINE and not noFormat:
            self._wrapSelection(nwShortcode.ULINE_O, nwShortcode.ULINE_C)
        elif action == nwDocAction.SC_MARK and not noFormat:
            self._wrapSelection(nwShortcode.MARK_O, nwShortcode.MARK_C)
        elif action == nwDocAction.SC_SUP and not noFormat:
            self._wrapSelection(nwShortcode.SUP_O, nwShortcode.SUP_C)
        elif action == nwDocAction.SC_SUB and not noFormat:
            self._wrapSelection(nwShortcode.SUB_O, nwShortcode.SUB_C)
        elif action == nwDocAction.MOVE_TEXT:
            self._moveTextToNewDocument()
        elif action == nwDocAction.ZOOM_IN:
            self.zoomIn()
        elif action == nwDocAction.ZOOM_OUT:
            self.zoomOut()
        elif action == nwDocAction.ZOOM_RESET:
            self.zoomReset()
        else:
            if noFormat:
                logger.warning("Action '%s' not alowed on current block", action)
                self.docHeader.flashError()
                SHARED.newStatusMessage(self.tr("Cannot apply requested format on this line"))
            else:
                logger.error("Unknown action '%s' requested", action)
            self._allowAutoReplace(True)
            return False

        self._allowAutoReplace(True)
        self._lastActive = time()

        return True

    def anyFocus(self) -> bool:
        """Check if any widget or child widget has focus."""
        return self.hasFocus() or self.isAncestorOf(QApplication.focusWidget())

    def revealLocation(self) -> None:
        """Tell the user where on the file system the file in the editor
        is saved.
        """
        if isinstance(self._nwDocument, ProjectDocument):
            SHARED.info(
                [
                    self.tr("Document Details"),
                    "\u2013" * 40,
                    self.tr("Created: {0}").format(self._nwDocument.createdDate),
                    self.tr("Updated: {0}").format(self._nwDocument.updatedDate),
                ],
                details=self.tr("File Location: {0}").format(self._nwDocument.fileLocation),
                log=False,
            )

    def insertText(self, insert: str | nwDocInsert) -> None:
        """Insert a specific type of text at the cursor position."""
        if self._docHandle is None:
            logger.error("No document open")
            return

        text = ""
        block = False
        after = False

        if isinstance(insert, str):
            text = insert
        elif isinstance(insert, nwDocInsert):
            if insert == nwDocInsert.QUOTE_LS:
                text = CONFIG.fmtSQuoteOpen
            elif insert == nwDocInsert.QUOTE_RS:
                text = CONFIG.fmtSQuoteClose
            elif insert == nwDocInsert.QUOTE_LD:
                text = CONFIG.fmtDQuoteOpen
            elif insert == nwDocInsert.QUOTE_RD:
                text = CONFIG.fmtDQuoteClose
            elif insert == nwDocInsert.SYNOPSIS:
                text = "%Synopsis: "
                block = True
                after = True
            elif insert == nwDocInsert.SHORT:
                text = "%Short: "
                block = True
                after = True
            elif insert == nwDocInsert.NEW_PAGE:
                text = "[newpage]"
                block = True
                after = False
            elif insert == nwDocInsert.VSPACE_S:
                text = "[vspace]"
                block = True
                after = False
            elif insert == nwDocInsert.VSPACE_M:
                text = "[vspace:2]"
                block = True
                after = False
            elif insert == nwDocInsert.LIPSUM:
                text = GuiLipsum.getLipsum(self)
                block = True
                after = False
            elif insert == nwDocInsert.FOOTNOTE:
                self._insertCommentStructure(nwComment.FOOTNOTE)
            elif insert == nwDocInsert.LINE_BRK:
                text = nwShortcode.BREAK

        if text:
            if block:
                self.insertNewBlock(text, defaultAfter=after)
            else:
                cursor = self.textCursor()
                cursor.beginEditBlock()
                cursor.insertText(text)
                cursor.endEditBlock()

        return

    def insertNewBlock(self, text: str, defaultAfter: bool = True) -> bool:
        """Insert a piece of text on a blank line."""
        cursor = self.textCursor()
        block = cursor.block()
        if not block.isValid():
            logger.error("Not a valid text block")
            return False

        sPos = block.position()
        sLen = block.length()

        cursor.beginEditBlock()

        if sLen > 1 and defaultAfter:
            cursor.setPosition(sPos + sLen - 1)
            cursor.insertText("\n")
        else:
            cursor.setPosition(sPos)

        cursor.insertText(text)

        if sLen > 1 and not defaultAfter:
            cursor.insertText("\n")

        cursor.endEditBlock()

        self.setTextCursor(cursor)

        return True

    ##
    #  Events and Overloads
    ##

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Intercept key press events.
        We need to intercept a few key sequences:
          * The return and enter keys redirect here even if the search
            box has focus. Since we need these keys to continue search,
            we block any further interaction here while it has focus.
          * The undo/redo/select all sequences bypass the docAction
            pathway from the menu, so we redirect them back from here.
          * We also handle automatic scrolling here.
        """
        self._lastActive = time()
        key = event.key()

        if self._completer.handleKeyPress(event, key):
            return

        if key == QtKeyEscape:
            if self.searchVisible():
                self.closeSearch()
            elif CONFIG.vimMode:
                self.setVimMode(nwVimMode.NORMAL)
            elif SHARED.focusMode:
                SHARED.setFocusMode(False)
            event.ignore()
            return

        if CONFIG.vimMode and self._vim.mode != nwVimMode.INSERT:
            if self._handleVimNormalModeModeSwitching(event):
                return

            if self._vim.mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
                self._handleVimVisualMode(event)
            else:
                self._handleVimNormalMode(event)

            return

        if self.docSearch.anyFocus() and key in ENTER_KEYS:
            return
        elif event == QKeyRedo:
            self.docAction(nwDocAction.REDO)
            return
        elif event == QKeyUndo:
            self.docAction(nwDocAction.UNDO)
            return
        elif event == QKeySelectAll:
            self.docAction(nwDocAction.SEL_ALL)
            return

        if CONFIG.autoScroll:
            cPos = self.cursorRect().topLeft().y()
            self._dispatchKeyPress(event)
            nPos = self.cursorRect().topLeft().y()
            kMod = event.modifiers()
            okMod = kMod in (QtModNone, QtModShift)
            okKey = key not in MOVE_KEYS
            if nPos != cPos and okMod and okKey and (viewport := self.viewport()):
                mPos = CONFIG.autoScrollPos * 0.01 * viewport.height()
                if cPos > mPos and (vBar := self.verticalScrollBar()):
                    cMov = nPos - cPos
                    anim = QPropertyAnimation(vBar, b"value", self)
                    anim.setDuration(120)
                    anim.setStartValue(vBar.value())
                    anim.setEndValue(vBar.value() + cMov)
                    anim.start(QAnimDeleteWhenStopped)
        else:
            self._dispatchKeyPress(event)

        return

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
                self.openDocumentRequest.emit(handles[0], nwDocMode.EDIT, "", True)
        else:
            super().dropEvent(event)

    def focusNextPrevChild(self, _next: bool) -> bool:
        """Capture the focus request from the tab key on the text
        editor. If the editor has focus, we do not change focus and
        allow the editor to insert a tab. If the search bar has focus,
        we forward the call to the search object.
        """
        if self.hasFocus() or ((popup := self._completer.popup()) and popup.isVisible()):
            # QWidget.event() consults this before keyPressEvent() ever
            # runs, so while the completer popup is open, Tab must stay
            # with the editor even if hasFocus() is momentarily wrong
            # (observed on macOS after the popup, a separate top-level
            # window, is shown).
            return False
        elif self.docSearch.isVisible():
            return self.docSearch.cycleFocus()
        return True

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """If the mouse button is released and the control key is
        pressed, check if we're clicking on a tag, and trigger the
        follow tag function.
        """
        if event.modifiers() & QtModCtrl == QtModCtrl:
            cursor = self.cursorForPosition(event.pos())
            mData, mType = self._qDocument.metaDataAtPos(cursor.position())
            if mData and mType == "url":
                SHARED.openWebsite(mData)
            else:
                self._processTag(cursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Track mouse movement to trigger the reference tag hover card.
        The hover check itself is debounced by a timer, and is only
        started at all if the block under the cursor holds any meta
        data, so idle moves over plain text stay cheap.
        """
        pos = event.pos()
        data = self.cursorForPosition(pos).block().userData()
        if isinstance(data, TextBlockData) and data.metaData:
            self._hoverPos = pos
            self._timerHover.start()
        else:
            self._timerHover.stop()
            self._hoverCard.scheduleHide()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Request that the hover card be hidden when the mouse leaves
        the editor. The hide is delayed rather than immediate, so the
        mouse has time to move onto the card itself, which cancels it.
        """
        self._timerHover.stop()
        self._hoverCard.scheduleHide()
        super().leaveEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Zoom the editor font with Ctrl+Scroll wheel."""
        self._hideHoverCard()
        if event.modifiers() & QtModCtrl == QtModCtrl:
            delta = event.angleDelta().y() // 120
            if delta > 0:
                self.zoomIn(delta)
            elif delta < 0:
                self.zoomOut(-delta)
            event.accept()
            return
        super().wheelEvent(event)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """If the text editor is resized, we must make sure the document
        has its margins adjusted according to user preferences.
        """
        self.updateDocMargins()
        self._timerCheck.start()
        super().resizeEvent(event)

    def inputMethodEvent(self, event: QInputMethodEvent) -> None:
        """Handle text being input from CJK input methods."""
        super().inputMethodEvent(event)
        if event.commitString():  # pragma: no branch
            # See issues #2267 and #2517
            self.ensureCursorVisible(centre=False)
            # cursorRect() is still stale immediately after the commit,
            # so positioning the popup must wait for the next event
            # loop iteration
            QTimer.singleShot(0, self._completerToCursor)

    def inputMethodQuery(self, query: Qt.InputMethodQuery) -> QRect | QVariant:
        """Adjust completion windows for CJK input methods to consider
        the viewport margins.
        """
        if query == QtImCursorRectangle:
            # See issues #2267 and #2517
            vM = self.viewportMargins()
            rect = self.cursorRect()
            rect.translate(vM.left(), vM.top())
            return rect
        elif query == QtImCurrentSelection:
            # See issue #2622
            ac = sip.enableautoconversion(QVariant, False)  # type: ignore
            variant = super().inputMethodQuery(query)
            sip.enableautoconversion(QVariant, ac)  # type: ignore
            return variant
        return super().inputMethodQuery(query)

    def createMimeDataFromSelection(self) -> QMimeData:
        """Overload mime data creation for copy/cut so that only plain
        text is put on the clipboard, and not also HTML.
        """
        data = QMimeData()
        data.setText(self.getSelectedText())
        return data

    def insertFromMimeData(self, source: QMimeData | None) -> None:
        """Overload mime data insertion in the document."""
        if not source:
            # Blocks empty inserts, see #2598
            return

        document = None
        if source.hasHtml():
            logger.debug("Converting rich text paste")
            document = QTextDocument()
            document.setHtml(source.html())
        elif source.hasFormat(nwConst.MIME_MARKDOWN):
            logger.debug("Converting Markdown paste")
            data = source.data(nwConst.MIME_MARKDOWN).data().decode("utf-8", errors="replace")
            document = QTextDocument()
            document.setMarkdown(data)

        if document is not None:
            text = FromQTextDocument(document).convertText().strip("\n")
        elif urls := source.urls():
            text = "\n".join(url.toString(QUrl.ComponentFormattingOption.FullyEncoded) for url in urls)
        elif source.hasText():
            text = source.text()
        else:
            return

        self._insertPlainText(text)

    ##
    #  Public Slots
    ##

    @pyqtSlot(str, Enum)
    def onProjectItemChanged(self, tHandle: str, change: nwChange) -> None:
        """Process project item change. Called when an item label is
        changed to check if the document title bar needs updating.
        """
        if tHandle == self._docHandle and change == nwChange.UPDATE:
            self.docHeader.setHandle(tHandle)
            self.docFooter.updateInfo()
            self.updateDocMargins()

    @pyqtSlot(str)
    def insertKeyWord(self, keyword: str) -> bool:
        """Insert a keyword in the text editor, at the cursor position.
        If the insert line is not blank, a new line is started.
        """
        if keyword not in nwKeyWords.VALID_KEYS:
            logger.error("Invalid keyword '%s'", keyword)
            return False
        logger.debug("Inserting keyword '%s'", keyword)
        return self.insertNewBlock(f"{keyword}: ")

    @pyqtSlot()
    def toggleSearch(self) -> None:
        """Toggle the visibility of the search box."""
        if self.searchVisible():
            self.closeSearch()
        else:
            self.beginSearch()

    @pyqtSlot(list, list)
    def updateChangedTags(self, updated: list[str], deleted: list[str]) -> None:
        """Tags have changed, so just in case we rehighlight them."""
        if updated or deleted:
            self._qDocument.syntaxHighlighter.rehighlightByType(BLOCK_META)
            self._hoverCard.pruneCache(updated + deleted)

    @pyqtSlot(str, str)
    def processSpellCheckChange(self, language: str, provider: str) -> None:
        """Process a change in the spell check language or provider."""
        self.spellCheckDocument()

    @pyqtSlot()
    def zoomReset(self) -> None:
        """Reset the editor's font size to the user's configured size."""
        font = fontMatcher(CONFIG.textFont)
        self.setFont(font)
        self._qDocument.setDefaultFont(font)

    ##
    #  Private Slots
    ##

    @pyqtSlot()
    def _pasteAsPlainText(self) -> None:
        """Paste the clipboard's plain text content."""
        if clipboard := QApplication.clipboard():  # pragma: no branch
            self._insertPlainText(clipboard.text())

    @pyqtSlot(int, int, int)
    def _docChange(self, pos: int, removed: int, added: int) -> None:
        """Triggered by QTextDocument->contentsChanged. This also
        triggers the syntax highlighter.
        """
        self._lastEdit = time()
        self._lastFind = None

        if not self._docChanged:
            self.setDocumentChanged(removed != 0 or added != 0)

        if not self._timerDoc.isActive():
            self._timerDoc.start()

        if SHARED.project.data.spellCheck or CONFIG.showMultiSpaces:
            # Flag the affected blocks for the debounced spell/format check
            block = self._qDocument.findBlock(pos)
            while block.isValid() and block.position() <= pos + added:
                self._dirtyBlocks[block.blockNumber()] = block
                block = block.next()
            self._timerTextCheck.start()
            self._timerCheck.start()

        if (block := self._qDocument.findBlock(pos)).isValid():
            text = block.text()

            if text and text[0] in "@%" and added + removed == 1:
                # Only run on single character changes, or it will trigger
                # at unwanted times when other changes are made to the document
                cursor = self.textCursor()
                bPos = cursor.positionInBlock()
                if bPos > 0:
                    if text[0] == "@":
                        show = self._completer.updateMetaText(text, bPos)
                    else:
                        show = self._completer.updateCommentText(text, bPos)
                    if show:
                        # cursorRect() is still stale at this point, as the
                        # block's text layout hasn't caught up with this
                        # edit yet, so positioning the popup must wait for
                        # the next event loop iteration
                        QTimer.singleShot(0, self._showCompleter)
                    elif popup := self._completer.popup():  # pragma: no branch
                        # Otherwise, make sure a popup from an earlier
                        # keystroke that no longer has any matches is
                        # not left open with stale content
                        popup.hide()

            if self._doReplace and added == 1:
                cursor = self.textCursor()
                if self._autoReplace(text, cursor):
                    self._qDocument.syntaxHighlighter.rehighlightBlock(cursor.block())

    @pyqtSlot()
    def _onLayoutSettled(self) -> None:
        """Restore full interactivity once a busy-marked full-document
        operation (see GuiTextDocument.markLayoutBusy) has settled, and
        apply any cursor position that was queued while it was busy.
        Read-only is unconditionally cleared here: every call site that
        marks the document busy only does so while a document is open
        and meant to end up editable.
        """
        if self._queuePos is not None:
            position = self._queuePos
            self._queuePos = None
            self.setCursorPosition(position)
        self.setReadOnly(False)
        self.updateDocMargins()
        self._beginCheckPass()

    @pyqtSlot()
    def _cursorMoved(self) -> None:
        """Triggered when the cursor moved in the editor."""
        self._hideHoverCard()
        self.docFooter.updateLineCount(self.textCursor())
        if self._suppressed:
            # An underline was suppressed at the previous cursor
            # position, so the underlines must be refreshed
            self._timerCheck.start()
        if CONFIG.lineHighlight:
            self._selection.cursor = self.textCursor()
            self._selection.cursor.clearSelection()
            self._applyExtraSelections()

    @pyqtSlot()
    def _showHoverCard(self) -> None:
        """Show the reference tag hover card if the position last
        recorded by mouseMoveEvent is still over a tag once the hover
        delay has elapsed. Past the end of a line, cursorForPosition
        clamps to the nearest character, so the resolved cursor's own
        rect is checked against the actual mouse position to reject
        hovers over the empty space beyond the text.
        """
        cursor = self.cursorForPosition(self._hoverPos)
        rect = self.cursorRect(cursor)
        onText = abs(self._hoverPos.x() - rect.x()) <= self.fontMetrics().averageCharWidth()
        mData, mType = self._qDocument.metaDataAtPos(cursor.position()) if onText else ("", "")
        if mData and mType == "tag" and self._hoverCard.setTag(mData) and (viewport := self.viewport()):
            pos = QPoint(self._hoverPos.x(), rect.bottom() + 4)
            self._hoverCard.showAt(viewport.mapToGlobal(pos), viewport.width(), viewport.height())
        else:
            self._hoverCard.scheduleHide()

    @pyqtSlot()
    def _restartCheckTimer(self) -> None:
        """Restart the debounced spell/format marker refresh timer."""
        self._timerCheck.start()

    @pyqtSlot()
    def _updateCheckSelections(self) -> None:
        """Rebuild the spell and format error markers for all visible
        blocks. The extra selections for a block are cached here, keyed
        by its TextBlockData identity, and only rebuilt when that
        block's own error list has changed, so an edit to one block
        doesn't force every other visible block's markers to be
        reconstructed. The cache is owned solely by this widget so its
        lifetime is tied to plain Python reference counting rather than
        Qt's block/document teardown order. A trailing space under the
        cursor is not flagged, since it is a natural, transient state
        while the line is still being typed. See issue discussion #1347.
        """
        checkSpell = SHARED.project.data.spellCheck
        checkFormat = CONFIG.showMultiSpaces

        spellSelections = []
        formatSelections = []
        suppressed = False
        if (checkSpell or checkFormat) and (viewport := self.viewport()):
            cPos = self.textCursor().position()
            last = self.cursorForPosition(viewport.rect().bottomLeft()).blockNumber()
            block = self.cursorForPosition(viewport.rect().topLeft()).block()
            while block.isValid() and block.blockNumber() <= last:
                if isinstance(data := block.userData(), TextBlockData):
                    key = id(data)
                    position = block.position()

                    if checkSpell:
                        cached = self._selCacheSpell.get(key)
                        if cached is None or cached[0] != data.spellErrors:
                            cached = (
                                data.spellErrors,
                                self._buildSelections(block, self._spellErrFormat, data.spellErrors),
                            )
                            self._selCacheSpell[key] = cached
                        for (start, end, _), selection in zip(data.spellErrors, cached[1], strict=True):
                            if position + start < cPos <= position + end:
                                # Don't underline the word under the cursor
                                suppressed = True
                                continue
                            spellSelections.append(selection)

                    if checkFormat:
                        cached = self._selCacheFormat.get(key)
                        if cached is None or cached[0] != data.formatErrors:
                            cached = (
                                data.formatErrors,
                                self._buildSelections(block, self._formatErrFormat, data.formatErrors),
                            )
                            self._selCacheFormat[key] = cached
                        for (start, end, kind), selection in zip(data.formatErrors, cached[1], strict=True):
                            if kind == "trail" and position + start < cPos <= position + end:
                                # Not yet a real trailing space, still being typed
                                suppressed = True
                                continue
                            formatSelections.append(selection)

                block = block.next()

        self._suppressed = suppressed
        self._spellSelections = spellSelections
        self._formatSelections = formatSelections
        self._applyExtraSelections()

    def _buildSelections(self, block: QTextBlock, fmt: QTextCharFormat, errors: T_TextCheckList) -> T_Selections:
        """Build a list of extra selections from a block's cached error
        positions. The returned QTextCursor objects track the document
        automatically, so they stay valid even as edits elsewhere shift
        the block's absolute position.
        """
        position = block.position()
        selections = []
        for start, end, _ in errors:
            cursor = QTextCursor(self._qDocument)
            cursor.setPosition(position + start)
            cursor.setPosition(position + end, QtKeepAnchor)
            selection = QTextEdit.ExtraSelection()
            selection.format = fmt
            selection.cursor = cursor
            selections.append(selection)
        return selections

    @pyqtSlot()
    def _dispatchTextCheck(self) -> None:
        """Send the next batch of text blocks to the text check worker.
        Modified blocks are prioritised, then the blocks queued for the
        background document pass, resolved by character position since
        the document can be edited between dispatches.
        """
        if self._checkJob is not None:
            # There is already a job running
            return

        job: list[T_TextCheckBlock] = []
        payload: T_TextCheckPayload = []
        while self._dirtyBlocks and len(job) < nwConst.CHECK_PASS_CHUNK:
            _, block = self._dirtyBlocks.popitem()
            if block.isValid() and isinstance(data := block.userData(), TextBlockData):  # pragma: no branch
                payload.append((len(job), *data.checkData()))
                job.append((block, data, data.revision))

        if self._checkPassPos is not None:
            block = self._qDocument.findBlock(self._checkPassPos)
            while block.isValid() and len(job) < nwConst.CHECK_PASS_CHUNK:
                if isinstance(data := block.userData(), TextBlockData):
                    payload.append((len(job), *data.checkData()))
                    job.append((block, data, data.revision))
                block = block.next()
            self._checkPassPos = block.position() if block.isValid() else None
            if self._checkPassPos is None:
                logger.debug("Text check background pass complete")

        if job:
            self._checkJobId += 1
            self._checkJob = (self._checkJobId, job)
            self._checkDispatcher.dispatch(
                self._checkJobId,
                payload,
                checkSpell=SHARED.project.data.spellCheck,
                checkFormat=CONFIG.showMultiSpaces,
            )
        elif self._spellPassNotify:
            self._spellPassNotify = False
            SHARED.newStatusMessage(self.tr("Spell check complete"))

    @pyqtSlot(int, list)
    def _textCheckResults(self, jobId: int, results: list[tuple[int, T_TextCheckList, T_TextCheckList]]) -> None:
        """Process the results from the spell/format check worker.
        Results are discarded if the job was cancelled, or per block if
        the block was modified or removed while the worker was running.
        """
        if self._checkJob and self._checkJob[0] == jobId:
            job = self._checkJob[1]
            self._checkJob = None
            for index, spellErrors, formatErrors in results:
                block, data, revision = job[index]
                if block.isValid() and block.userData() is data and data.revision == revision:
                    data.setSpellErrors(spellErrors)
                    data.setFormatErrors(formatErrors)
            self._timerCheck.start()
            self._dispatchTextCheck()

    @pyqtSlot(int, int, str)
    def _insertCompletion(self, pos: int, length: int, text: str) -> None:
        """Insert choice from the completer popup."""
        cursor = self.textCursor()
        if (block := cursor.block()).isValid():  # pragma: no branch
            check = pos + block.position()
            cursor.setPosition(check, QtMoveAnchor)
            cursor.setPosition(check + length, QtKeepAnchor)
            cursor.insertText(text)
            if popup := self._completer.popup():  # pragma: no branch
                popup.hide()

    @pyqtSlot()
    def _openContextFromCursor(self) -> None:
        """Open the spell check context menu at the cursor."""
        self._openContextMenu(self.cursorRect().center())

    @pyqtSlot("QPoint")
    def _openContextMenu(self, pos: QPoint) -> None:
        """Open the editor context menu at a given coordinate."""
        pCursor = self.cursorForPosition(pos)
        pBlock = pCursor.block()
        hasSelection = self.textCursor().hasSelection()

        ctxMenu = QMenu(self)
        ctxMenu.setObjectName("ContextMenu")
        if pBlock.userState() == BLOCK_TITLE:
            action = qtAddAction(ctxMenu, self._trSetName)
            action.triggered.connect(qtLambda(self._emitRenameItem, pBlock))

        # URL
        mData, mType = self._qDocument.metaDataAtPos(pCursor.position())
        if mData and mType == "url":
            action = qtAddAction(ctxMenu, self._trOpenURL)
            action.triggered.connect(qtLambda(SHARED.openWebsite, mData))
            ctxMenu.addSeparator()

        # Follow
        status = self._processTag(cursor=pCursor, follow=False)
        if status & _TagAction.FOLLOW:
            action = qtAddAction(ctxMenu, self._trViewTag)
            action.triggered.connect(qtLambda(self._processTag, cursor=pCursor, follow=True, edit=False))
            action = qtAddAction(ctxMenu, self._trEditTag)
            action.triggered.connect(qtLambda(self._processTag, cursor=pCursor, follow=True, edit=True))
            ctxMenu.addSeparator()
        elif status & _TagAction.CREATE:
            action = qtAddAction(ctxMenu, self._trCreateNote)
            action.triggered.connect(qtLambda(self._processTag, cursor=pCursor, create=True))
            ctxMenu.addSeparator()

        # Cut, Copy and Paste
        if hasSelection:
            action = qtAddAction(ctxMenu, self._trCut)
            action.triggered.connect(qtLambda(self.docAction, nwDocAction.CUT))
            action = qtAddAction(ctxMenu, self._trCopy)
            action.triggered.connect(qtLambda(self.docAction, nwDocAction.COPY))

        action = qtAddAction(ctxMenu, self._trPaste)
        action.triggered.connect(qtLambda(self.docAction, nwDocAction.PASTE))
        ctxMenu.addSeparator()

        # Selections
        action = qtAddAction(ctxMenu, self._trSelectAll)
        action.triggered.connect(qtLambda(self.docAction, nwDocAction.SEL_ALL))
        action = qtAddAction(ctxMenu, self._trSelectWord)
        action.triggered.connect(qtLambda(self._makePosSelection, QtSelectWord, pos))
        action = qtAddAction(ctxMenu, self._trSelectPara)
        action.triggered.connect(qtLambda(self._makePosSelection, QtSelectBlock, pos))

        # Actions
        mTools = qtAddMenu(ctxMenu, self._trActions)
        action = qtAddAction(mTools, self._trMoveText if hasSelection else self._trSplitDoc)
        action.triggered.connect(self._moveTextToNewDocument)

        # Spell Checking
        if SHARED.project.data.spellCheck:
            word, sPos, ePos, suggest = self._qDocument.spellErrorAtPos(pCursor.position())
            if word and sPos >= 0:
                logger.debug("Word '%s' is misspelled", word)
                wBlock = pCursor.block()
                wPos = wBlock.position()
                wCursor = self.textCursor()
                wCursor.setPosition(wPos + sPos)
                wCursor.setPosition(wPos + ePos, QtKeepAnchor)
                if suggest:
                    ctxMenu.addSeparator()
                    qtAddAction(ctxMenu, self._trSpellSuggest)
                    for option in suggest[:15]:
                        action = qtAddAction(ctxMenu, f"{nwUnicode.U_ENDASH} {option}")
                        action.triggered.connect(qtLambda(self._correctWord, wCursor, option))
                else:
                    qtAddAction(ctxMenu, f"{nwUnicode.U_ENDASH} {self._trNoSuggest}")

                ctxMenu.addSeparator()
                action = qtAddAction(ctxMenu, self._trIgnoreWord)
                action.triggered.connect(qtLambda(self._addWord, word, wBlock, False))
                action = qtAddAction(ctxMenu, self._trAddWord)
                action.triggered.connect(qtLambda(self._addWord, word, wBlock, True))

        # Execute the context menu
        if viewport := self.viewport():  # pragma: no branch
            ctxMenu.exec(viewport.mapToGlobal(pos))

        ctxMenu.setParent(None)

    @pyqtSlot()
    def _runDocumentTasks(self) -> None:
        """Run timer document tasks."""
        if self._docHandle and self._lastEdit > self._lastDocTask:
            logger.debug("Running document tasks")
            self._lastDocTask = self._lastEdit
            if not self._docCounter.busy:
                self._docCounter.count(self.getText())

            self.docHeader.setOutline({
                block.blockNumber(): block.text() for block in self._qDocument.iterBlockByType(BLOCK_TITLE, maxCount=30)
            })

            if self._docChanged:
                self.docTextChanged.emit(self._docHandle, self._lastEdit)

    @pyqtSlot()
    def _moveTextToNewDocument(self) -> None:
        """Process request to move text to new document."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.movePosition(QtMoveEnd, QtKeepAnchor)
            self.setTextCursor(cursor)

        if (
            cursor.hasSelection()
            and (text := self.getSelectedText().strip())  # This handles proper line breaks
            and (item := self._nwItem)
            and (parent := item.itemParent)
        ):
            heading, title = processHeading(text.partition("\n")[0])
            label, dlgOk = GuiEditLabel.getLabel(
                self,
                text=title or f"{item.itemName} (1)",
                info=self.tr("Create a new document from selected text?"),
            )
            if dlgOk and (
                tHandle := SHARED.project.newFile(label, parent, SHARED.project.tree.subTreePos(item.itemHandle) + 1)
            ):
                hasHeading = heading != "H0"
                hLevel = nwStyles.H_LEVEL.get(heading if hasHeading else item.mainHeading, 3)
                if SHARED.project.writeNewFile(
                    tHandle, hLevel, item.isDocumentLayout(), text, addHeading=not hasHeading
                ):
                    SHARED.project.index.reIndexHandle(tHandle)
                    SHARED.project.tree.refreshItems([tHandle])
                    cursor.removeSelectedText()

    @pyqtSlot(int, int, int)
    def _updateDocCounts(self, cCount: int, wCount: int, pCount: int) -> None:
        """Process the word counter's finished signal."""
        if self._docHandle and self._nwItem:
            logger.debug("Updating word count")
            mCount = cCount if CONFIG.useCharCount else wCount
            needsRefresh = mCount != self._nwItem.mainCount
            self._nwItem.setCharCount(cCount)
            self._nwItem.setWordCount(wCount)
            self._nwItem.setParaCount(pCount)
            if needsRefresh:
                self._nwItem.notifyToRefresh()
                if not self.textCursor().hasSelection():
                    # Selection counter should take precedence (#2155)
                    self.docFooter.updateMainCount(mCount, False)

    @pyqtSlot()
    def _updateSelectedStatus(self) -> None:
        """Process user change in text selection. Forward this
        information to the footer, and start the selection word counter.
        """
        if self.textCursor().hasSelection():
            if not self._timerSel.isActive():
                self._timerSel.start()
        else:
            self._timerSel.stop()
            self.docFooter.updateMainCount(0, False)

    @pyqtSlot()
    def _runSelCounter(self) -> None:
        """Update the selection word count."""
        if self._docHandle and not self._selCounter.busy and (text := self.getSelectedText()):
            self._selCounter.count(text)

    @pyqtSlot(int, int, int)
    def _updateSelCounts(self, cCount: int, wCount: int, pCount: int) -> None:
        """Update the counts on the counter's finished signal."""
        if self._docHandle and self._nwItem:
            logger.debug("Updating selection count")
            self.docFooter.updateMainCount(cCount if CONFIG.useCharCount else wCount, True)
            self._timerSel.stop()

    @pyqtSlot()
    def _closeCurrentDocument(self) -> None:
        """Close the document. Forwarded to the main Gui."""
        self.closeEditorRequest.emit()
        self.docToolBar.setVisible(False)

    @pyqtSlot()
    def _toggleToolBarVisibility(self) -> None:
        """Toggle the visibility of the tool bar."""
        state = not self.docToolBar.isVisible()
        self.docToolBar.setVisible(state)
        CONFIG.showEditToolBar = state

    ##
    #  Search & Replace
    ##

    def beginSearch(self) -> None:
        """Set the selected text as the search text."""
        self.docSearch.setSearchText(self.getSelectedText() or None)
        resS, _ = self.findAllOccurences()
        self.docSearch.setResultCount(None, len(resS))

    def beginReplace(self) -> None:
        """Initialise the search box and reset the replace text box."""
        self.beginSearch()
        self.docSearch.setReplaceText("")
        self.updateDocMargins()

    def findNext(self, goBack: bool = False) -> None:
        """Search for the next or previous occurrence of the search bar
        text in the document. Wrap around if not found and loop is
        enabled, or continue to next file if next file is enabled.
        """
        if not self.anyFocus():
            logger.debug("Editor does not have focus")
            return

        if not self.docSearch.isVisible():
            self.beginSearch()
            return

        prevFocus = QApplication.focusWidget() or self
        resS, resE = self.findAllOccurences()
        if len(resS) == 0 and self._docHandle:
            self.docSearch.setResultCount(0, 0)
            self._lastFind = None
            if CONFIG.searchNextFile:
                self.openNextFindDocument(prevFocus, goBack)
            return

        cursor = self.textCursor()
        resIdx = bisect.bisect_left(resS, cursor.position())

        doLoop = CONFIG.searchLoop
        maxIdx = len(resS) - 1

        if goBack:
            resIdx -= 2

        if (resIdx < 0 and goBack) or (resIdx > maxIdx and not goBack):
            if self._docHandle and CONFIG.searchNextFile:
                self.openNextFindDocument(prevFocus, goBack)
                return
            elif goBack:
                resIdx = maxIdx if doLoop else 0
            else:
                resIdx = 0 if doLoop else maxIdx

            resIdx = max(0, min(resIdx, maxIdx))

        self.selectFindSelection(resS, resE, resIdx)

        return

    def openNextFindDocument(self, prevFocus: QWidget, goBack: bool) -> None:
        """Open the adjacent document and select its edge-most match."""
        if self._docHandle:
            self.requestNextDocument.emit(self._docHandle, CONFIG.searchLoop, goBack)
            self.beginSearch()
            prevFocus.setFocus()

            resS, resE = self.findAllOccurences()
            if len(resS) == 0:
                return

            self.selectFindSelection(resS, resE, len(resS) - 1 if goBack else 0)

    def selectFindSelection(self, resS: list[int], resE: list[int], resIdx: int) -> None:
        """Select one search result and update the search state."""
        cursor = self.textCursor()
        cursor.setPosition(resS[resIdx], QtMoveAnchor)
        cursor.setPosition(resE[resIdx], QtKeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible(centre=False)

        self.docSearch.setResultCount(resIdx + 1, len(resS))
        self._lastFind = (resS[resIdx], resE[resIdx])

    def findAllOccurences(self) -> tuple[list[int], list[int]]:
        """Create a list of all search results of the current search
        text in the document.
        """
        resS = []
        resE = []
        cursor = self.textCursor()
        hasSelection = cursor.hasSelection()
        if hasSelection:
            origA = cursor.selectionStart()
            origB = cursor.selectionEnd()
        else:
            origA = cursor.position()
            origB = cursor.position()

        findOpt = QTextDocument.FindFlag(0)
        if CONFIG.searchCase:
            findOpt |= QTextDocument.FindFlag.FindCaseSensitively
        if CONFIG.searchWord:
            findOpt |= QTextDocument.FindFlag.FindWholeWords

        searchFor = self.docSearch.getSearchObject()
        cursor.setPosition(0)
        self.setTextCursor(cursor)

        # Search up to a maximum of MAX_SEARCH_RESULT, and make sure
        # certain special searches like a regex search for .* don't loop
        # infinitely
        while self.find(searchFor, findOpt) and len(resE) <= nwConst.MAX_SEARCH_RESULT:
            cursor = self.textCursor()
            if cursor.hasSelection():
                resS.append(cursor.selectionStart())
                resE.append(cursor.selectionEnd())
            else:
                logger.warning("The search returned an empty result")
                break

        if hasSelection:
            cursor.setPosition(origA, QtMoveAnchor)
            cursor.setPosition(origB, QtKeepAnchor)
        else:
            cursor.setPosition(origA)

        self.setTextCursor(cursor)
        self.highlightSearchSelections(resS, resE)

        return resS, resE

    def replaceNext(self) -> None:
        """Search for the next occurrence of the search bar text in the
        document and replace it with the replace text. Call search next
        automatically when done.
        """
        if not self.anyFocus():
            logger.debug("Editor does not have focus")
            return

        if not self.docSearch.isVisible():
            # The search tool is not active, so we activate it.
            self.beginSearch()
            return

        cursor = self.textCursor()
        if not cursor.hasSelection():
            # We have no text selected at all, so just make this a
            # regular find next call.
            self.findNext()
            return

        if self._lastFind is None and cursor.hasSelection():
            # If we have a selection but no search, it may have been the
            # text we triggered the search with, in which case we search
            # again from the beginning of that selection to make sure we
            # have a valid result.
            sPos = cursor.selectionStart()
            cursor.clearSelection()
            cursor.setPosition(sPos)
            self.setTextCursor(cursor)
            self.findNext()
            cursor = self.textCursor()

        if self._lastFind is None:
            # In case the above didn't find a result, we give up here.
            return

        searchFor = self.docSearch.searchText
        replWith = self.docSearch.replaceText

        if CONFIG.searchMatchCap:
            replWith = transferCase(cursor.selectedText(), replWith)

        # Make sure the selected text was selected by an actual find
        # call, and not the user.
        if self._lastFind == (cursor.selectionStart(), cursor.selectionEnd()):
            cursor.beginEditBlock()
            cursor.removeSelectedText()
            cursor.insertText(replWith)
            cursor.endEditBlock()
            cursor.setPosition(cursor.selectionEnd())
            self.setTextCursor(cursor)
            logger.debug(
                "Replaced occurrence of '%s' with '%s' on line %d",
                searchFor,
                replWith,
                cursor.blockNumber() + 1,
            )

        self.findNext()

        return

    def clearSearchSelections(self) -> None:
        """Clear the highlight of all search results in the document."""
        self.highlightSearchSelections([], [])

    def highlightSearchSelections(self, resS: list[int], resE: list[int]) -> None:
        """Highlight all search results in the document."""
        selections = []
        for start, end in zip(resS, resE, strict=True):
            cursor = QTextCursor(self._qDocument)
            cursor.setPosition(start)
            cursor.setPosition(end, QtKeepAnchor)
            selection = QTextEdit.ExtraSelection()
            selection.format = self._searchFormat
            selection.cursor = cursor
            selections.append(selection)
        self._searchSelections = selections
        self._applyExtraSelections()

    ##
    #  Internal Functions : Text Manipulation
    ##

    def _toggleFormat(self, fLen: int, fChar: str) -> None:
        """Toggle the formatting of a specific type for a piece of text.
        If more than one block is selected, the formatting is applied to
        the first block.
        """
        cursor = self.textCursor()
        posO = cursor.position()
        if cursor.hasSelection():
            select = _SelectAction.KEEP_SELECTION
        else:
            cursor = self._autoSelect()
            if cursor.hasSelection() and posO == cursor.selectionEnd():
                select = _SelectAction.MOVE_AFTER
            else:
                select = _SelectAction.KEEP_POSITION

        posS = cursor.selectionStart()
        posE = cursor.selectionEnd()
        if posS == posE and self._qDocument.characterAt(posO - 1) == fChar:
            logger.warning("Format repetition, cancelling action")
            cursor.clearSelection()
            cursor.setPosition(posO)
            self.setTextCursor(cursor)
            return

        blockS = self._qDocument.findBlock(posS)
        blockE = self._qDocument.findBlock(posE)
        if blockS != blockE:
            posE = blockS.position() + blockS.length() - 1
            cursor.clearSelection()
            cursor.setPosition(posS, QtMoveAnchor)
            cursor.setPosition(posE, QtKeepAnchor)
            self.setTextCursor(cursor)

        numB = 0
        for n in range(fLen):
            if self._qDocument.characterAt(posS - n - 1) == fChar:
                numB += 1
            else:
                break

        numA = 0
        for n in range(fLen):
            if self._qDocument.characterAt(posE + n) == fChar:
                numA += 1
            else:
                break

        if fLen == min(numA, numB):
            cursor.beginEditBlock()
            cursor.setPosition(posS)
            for _ in range(fLen):
                cursor.deletePreviousChar()
            cursor.setPosition(posE)
            for _ in range(fLen):
                cursor.deletePreviousChar()
            cursor.endEditBlock()

            if select != _SelectAction.KEEP_SELECTION:
                cursor.clearSelection()
                cursor.setPosition(posO - fLen)
                self.setTextCursor(cursor)

        else:
            self._wrapSelection(fChar * fLen, pos=posO, select=select)

        return

    def _wrapSelection(
        self,
        before: str,
        after: str | None = None,
        pos: int | None = None,
        select: _SelectAction = _SelectAction.NO_DECISION,
    ) -> None:
        """Wrap the selected text in whatever is in tBefore and tAfter.
        If there is no selection, the autoSelect setting decides the
        action. AutoSelect will select the word under the cursor before
        wrapping it. If this feature is disabled, nothing is done.
        """
        if after is None:
            after = before

        cursor = self.textCursor()
        posO = pos if isinstance(pos, int) else cursor.position()
        if select == _SelectAction.NO_DECISION:
            if cursor.hasSelection():
                select = _SelectAction.KEEP_SELECTION
            else:
                cursor = self._autoSelect()
                if cursor.hasSelection() and posO == cursor.selectionEnd():
                    select = _SelectAction.MOVE_AFTER
                else:
                    select = _SelectAction.KEEP_POSITION

        posS = cursor.selectionStart()
        posE = cursor.selectionEnd()

        blockS = self._qDocument.findBlock(posS)
        blockE = self._qDocument.findBlock(posE)
        if blockS != blockE:
            posE = blockS.position() + blockS.length() - 1

        cursor.clearSelection()
        cursor.beginEditBlock()
        cursor.setPosition(posE)
        cursor.insertText(after)
        cursor.setPosition(posS)
        cursor.insertText(before)
        cursor.endEditBlock()

        if select == _SelectAction.MOVE_AFTER:
            cursor.setPosition(posE + len(before + after))
        elif select == _SelectAction.KEEP_SELECTION:
            cursor.setPosition(posS + len(before), QtMoveAnchor)
            cursor.setPosition(posE + len(before), QtKeepAnchor)
        elif select == _SelectAction.KEEP_POSITION:
            cursor.setPosition(posO + len(before))
        else:  # pragma: no cover
            pass

        self.setTextCursor(cursor)

    def _replaceQuotes(self, sQuote: str, oQuote: str, cQuote: str) -> None:
        """Replace all straight quotes in the selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            SHARED.error(self.tr("Please select some text before calling replace quotes."))
            return

        posS = cursor.selectionStart()
        posE = cursor.selectionEnd()
        closeCheck = (" ", "\n", nwUnicode.U_LSEP, nwUnicode.U_PSEP)

        self._allowAutoReplace(False)
        for posC in range(posS, posE + 1):
            cursor.setPosition(posC)
            cursor.movePosition(QtMoveLeft, QtKeepAnchor, 2)
            selText = cursor.selectedText()

            nS = len(selText)
            if nS == 2:
                pC = selText[0]
                cC = selText[1]
            elif nS == 1:
                pC = " "
                cC = selText[0]
            else:  # pragma: no cover
                continue

            if cC != sQuote:
                continue

            cursor.clearSelection()
            cursor.setPosition(posC)
            if pC in closeCheck:
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveLeft, QtKeepAnchor, 1)
                cursor.insertText(oQuote)
                cursor.endEditBlock()
            else:
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveLeft, QtKeepAnchor, 1)
                cursor.insertText(cQuote)
                cursor.endEditBlock()

        self._allowAutoReplace(True)

        return

    def _processBlockFormat(self, action: nwDocAction, text: str, toggle: bool = True) -> tuple[nwDocAction, str, int]:
        """Process the formatting of a single text block."""
        # Remove existing format first, if any
        if text.startswith("@"):
            logger.error("Cannot apply block format to keyword/value line")
            return nwDocAction.NO_ACTION, "", 0
        elif text.startswith("%~"):
            temp = text[2:].lstrip()
            offset = len(text) - len(temp)
            if toggle and action == nwDocAction.BLOCK_IGN:
                action = nwDocAction.BLOCK_TXT
        elif text.startswith("%"):
            temp = text[1:].lstrip()
            offset = len(text) - len(temp)
            if toggle and action == nwDocAction.BLOCK_COM:
                action = nwDocAction.BLOCK_TXT
        elif text.startswith("# "):
            temp = text[2:]
            offset = 2
        elif text.startswith("## "):
            temp = text[3:]
            offset = 3
        elif text.startswith("### "):
            temp = text[4:]
            offset = 4
        elif text.startswith("#### "):
            temp = text[5:]
            offset = 5
        elif text.startswith("#! "):
            temp = text[3:]
            offset = 3
        elif text.startswith("##! "):
            temp = text[4:]
            offset = 4
        elif text.startswith("###! "):
            temp = text[5:]
            offset = 5
        elif text.startswith(">> "):
            temp = text[3:]
            offset = 3
        elif (text.startswith("> ") and action != nwDocAction.INDENT_R) or text.startswith(">>"):
            temp = text[2:]
            offset = 2
        elif text.startswith(">") and action != nwDocAction.INDENT_R:
            temp = text[1:]
            offset = 1
        else:
            temp = text
            offset = 0

        # Also remove formatting tags at the end
        if text.endswith(" <<"):
            temp = temp[:-3]
        elif (text.endswith(" <") and action != nwDocAction.INDENT_L) or text.endswith("<<"):
            temp = temp[:-2]
        elif text.endswith("<") and action != nwDocAction.INDENT_L:
            temp = temp[:-1]

        # Apply new format
        if action == nwDocAction.BLOCK_COM:
            text = f"% {temp}"
            offset -= 2
        elif action == nwDocAction.BLOCK_IGN:
            text = f"%~ {temp}"
            offset -= 3
        elif action == nwDocAction.BLOCK_H1:
            text = f"# {temp}"
            offset -= 2
        elif action == nwDocAction.BLOCK_H2:
            text = f"## {temp}"
            offset -= 3
        elif action == nwDocAction.BLOCK_H3:
            text = f"### {temp}"
            offset -= 4
        elif action == nwDocAction.BLOCK_H4:
            text = f"#### {temp}"
            offset -= 5
        elif action == nwDocAction.BLOCK_TTL:
            text = f"#! {temp}"
            offset -= 3
        elif action == nwDocAction.BLOCK_UNN:
            text = f"##! {temp}"
            offset -= 4
        elif action == nwDocAction.BLOCK_HSC:
            text = f"###! {temp}"
            offset -= 5
        elif action == nwDocAction.ALIGN_L:
            text = f"{temp} <<"
        elif action == nwDocAction.ALIGN_C:
            text = f">> {temp} <<"
            offset -= 3
        elif action == nwDocAction.ALIGN_R:
            text = f">> {temp}"
            offset -= 3
        elif action == nwDocAction.INDENT_L:
            text = f"> {temp}"
            offset -= 2
        elif action == nwDocAction.INDENT_R:
            text = f"{temp} <"
        elif action == nwDocAction.BLOCK_TXT:
            text = temp
        else:
            logger.error("Unknown or unsupported block format requested: '%s'", action)
            return nwDocAction.NO_ACTION, "", 0

        return action, text, offset

    def _formatBlock(self, action: nwDocAction) -> bool:
        """Change the block format of the block under the cursor."""
        cursor = self.textCursor()
        block = cursor.block()
        if not block.isValid():
            logger.debug("Invalid block selected for action '%s'", action)
            return False

        action, text, offset = self._processBlockFormat(action, block.text())
        if action == nwDocAction.NO_ACTION:
            return False

        pos = cursor.position()

        cursor.beginEditBlock()
        self._makeSelection(QtSelectBlock, cursor)
        cursor.insertText(text)
        cursor.endEditBlock()

        if (move := pos - offset) >= 0:
            cursor.setPosition(move)
        self.setTextCursor(cursor)

        return True

    def _formatLink(self) -> None:
        """Format a link under the cursor, or insert a new one. An
        existing bare URL or Markdown link at the cursor is detected via
        the block's TextBlockData, and used to pre-fill the edit dialog.
        """
        cursor = self.textCursor()
        block = cursor.block()

        text = ""
        url = ""
        posS = posE = cursor.position()
        if cursor.hasSelection():
            posS = cursor.selectionStart()
            posE = cursor.selectionEnd()
            text = cursor.selectedText()

        if isinstance(data := block.userData(), TextBlockData):
            check = cursor.position() - block.position()
            for start, end, mData, mType in data.metaData:
                if mType in ("url", "link") and start <= check <= end:
                    posS = block.position() + start
                    posE = block.position() + end
                    url = mData
                    text = ""
                    if mType == "link":
                        linkCursor = QTextCursor(self._qDocument)
                        linkCursor.setPosition(posS)
                        linkCursor.setPosition(posE, QtKeepAnchor)
                        if m := REGEX_PATTERNS.markdownLink.match(linkCursor.selectedText()):  # pragma: no branch
                            text, url = m.group(2), m.group(4)
                    break

        newText, newUrl, dlgOk = GuiEditLink.getLink(self, text=text, url=url)
        if not dlgOk or not newUrl:
            return

        result = f"[{newText}]({newUrl})" if newText else newUrl

        cursor.setPosition(posS)
        cursor.setPosition(posE, QtKeepAnchor)
        cursor.beginEditBlock()
        cursor.insertText(result)
        cursor.endEditBlock()
        self.setTextCursor(cursor)

    def _iterFormatBlocks(self, action: nwDocAction) -> bool:
        """Iterate over all selected blocks and apply format. If no
        selection is made, just forward the call to the single block
        formatter function.
        """
        cursor = self.textCursor()
        blocks = self._selectedBlocks(cursor)
        if len(blocks) < 2:
            return self._formatBlock(action)

        toggle = True
        cursor.beginEditBlock()
        for block in blocks:
            blockText = block.text()
            pAction, text, _ = self._processBlockFormat(action, blockText, toggle)
            if pAction != nwDocAction.NO_ACTION and blockText.strip():
                action = pAction  # First block decides further actions
                cursor.setPosition(block.position())
                self._makeSelection(QtSelectBlock, cursor)
                cursor.insertText(text)
                toggle = False

        cursor.endEditBlock()

        return True

    def _selectedBlocks(self, cursor: QTextCursor) -> list[QTextBlock]:
        """Return a list of all blocks selected by a cursor."""
        blocks: list[QTextBlock] = []
        if cursor.hasSelection():
            block = self._qDocument.findBlock(cursor.selectionStart())
            lastNum = self._qDocument.findBlock(cursor.selectionEnd()).blockNumber()
            while block.isValid() and block.blockNumber() <= lastNum:
                blocks.append(block)
                block = block.next()
        return blocks

    def _removeInParLineBreaks(self) -> None:
        """Strip line breaks within paragraphs in the selected text."""
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtSelectDocument)

        rS = 0
        rE = self._qDocument.characterCount()
        if sBlocks := self._selectedBlocks(cursor):
            rS = sBlocks[0].position()
            rE = sBlocks[-1].position() + sBlocks[-1].length()

        # Clean up the text
        currPar = []
        cleanText = ""
        for cBlock in sBlocks:
            cText = cBlock.text()
            if cText.strip() == "":
                if currPar:
                    cleanText += " ".join(currPar) + "\n\n"
                else:
                    cleanText += "\n"
                currPar = []
            elif cText.startswith(("# ", "## ", "### ", "#### ", "@", "%")):
                cleanText += cText + "\n"
            else:
                currPar.append(cText)

        if currPar:
            cleanText += " ".join(currPar) + "\n\n"

        # Replace the text with the cleaned up text
        cursor.beginEditBlock()
        cursor.clearSelection()
        cursor.setPosition(rS)
        cursor.movePosition(QtMoveRight, QtKeepAnchor, rE - rS)
        cursor.insertText(cleanText.rstrip() + "\n")
        cursor.endEditBlock()

    def _insertCommentStructure(self, style: nwComment) -> None:
        """Insert a shortcut/comment combo."""
        if self._docHandle and style == nwComment.FOOTNOTE:
            self.saveText()  # Index must be up to date
            key = SHARED.project.index.newCommentKey(self._docHandle, style)
            code = nwShortcode.COMMENT_STYLES[nwComment.FOOTNOTE]

            cursor = self.textCursor()
            block = cursor.block()
            text = block.text().rstrip()
            if not text or text.startswith("@"):
                logger.error("Invalid footnote location")
                return

            cursor.beginEditBlock()
            cursor.insertText(code.format(key))
            cursor.setPosition(block.position() + block.length() - 1)
            cursor.insertBlock()
            cursor.insertBlock()
            cursor.insertText(f"%Footnote.{key}: ")
            cursor.endEditBlock()

            self.setTextCursor(cursor)

        return

    def _insertPlainText(self, text: str) -> None:
        """Insert plain text at the current cursor position."""
        if text:
            # Ensures line height is applied, see #2874
            logger.debug("Inserted text into document")
            cursor = self.textCursor()
            cursor.beginEditBlock()
            cursor.insertText(text)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            # Deferred to avoid re-entrancy, see #2917
            QTimer.singleShot(0, lambda: self.ensureCursorVisible(centre=False))

    ##
    #  Internal Functions : Vim Mode
    ##

    def _handleVimNormalModeModeSwitching(self, event: QKeyEvent) -> bool:
        """Handle key events for Vim mode switching in NORMAL mode."""
        if (text := event.text()) == "i":
            self.setVimMode(nwVimMode.INSERT)
        elif text == "I":
            cursor = self.textCursor()
            cursor.movePosition(QtMoveStartOfLine)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            return True
        elif text == "v":
            self.setVimMode(nwVimMode.VISUAL)
            cursor = self.textCursor()
            cursor.movePosition(QtMoveRight, QtKeepAnchor, 1)
            self.setTextCursor(cursor)
            return True
        elif text == "V":
            self.setVimMode(nwVimMode.V_LINE)
            cursor = self.textCursor()
            cursor.select(QtSelectLine)
            self.setTextCursor(cursor)
            return True
        return False  # Not a mode switching motion

    def _handleVimNormalMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode NORMAL mode motions."""
        key = event.text()
        cursor = self.textCursor()
        # -- NORMAL mode PREFIX
        if self._vim.mode == nwVimMode.NORMAL:
            if key in self._vim.PREFIX_KEYS or key in self._vim.SUFFIX_KEYS:
                self._vim.pushCommandKey(key)
            else:
                self._vim.setCommand(key)

        if (command := self._vim.command) == "dd":
            cursor.beginEditBlock()
            cursor.select(QtSelectLine)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            cursor.setPosition(cursor.selectionEnd())
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "x":
            cursor.movePosition(QtMoveRight, QtKeepAnchor, 1)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "w":
            cursor.movePosition(QtMoveNextWord)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "b":
            cursor.movePosition(QtMovePreviousWord)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "e":
            # Try to move to end of the current word
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord)

            # If we didn't move (we were already at end of a word),
            # step forward one character (if possible) and then move to the next EndOfWord.
            if cursor.position() == origPos:
                textLen = len(self.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar)
                    cursor.movePosition(QtMoveEndOfWord)

            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "dw":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "db":
            cursor.beginEditBlock()
            cursor.movePosition(QtMovePreviousWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "de":
            cursor.beginEditBlock()
            # Extend selection to end of current/next word
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            if cursor.position() == origPos:  # Already at end-of-word
                textLen = len(self.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar, QtKeepAnchor)
                    cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "d$":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveEndOfLine, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "yw":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "gg":
            cursor.movePosition(QtMoveStart)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "G":
            cursor.movePosition(QtMoveEnd)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "yy":
            cursor.select(QtSelectLine)
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "p":
            if text := self._vim.pasteFromInternal():
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveEndOfLine)
                cursor.insertText("\n" + text)
                cursor.endEditBlock()
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "P":
            if text := self._vim.pasteFromInternal():
                cursor.beginEditBlock()
                cursor.movePosition(QtMoveStartOfLine)
                cursor.insertText(text + "\n")
                cursor.endEditBlock()
                self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "o":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveEndOfLine)
            cursor.insertText("\n")
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "O":
            cursor.beginEditBlock()
            cursor.movePosition(QtMoveStartOfLine)
            cursor.insertText("\n")
            cursor.movePosition(QtMoveUp)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)

        elif command == "$":
            cursor.movePosition(QtMoveEndOfLine)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "a":
            cursor.movePosition(QtMoveRight)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            self._vim.resetCommand()

        elif command == "A":
            cursor.movePosition(QtMoveEndOfLine)
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.INSERT)
            self._vim.resetCommand()

        elif command == "u":
            self.docAction(nwDocAction.UNDO)
            self._vim.resetCommand()

        elif command == "zz":
            self.setTextCursor(cursor)
            self.ensureCursorVisible(centre=True)
            self._vim.resetCommand()

        # Single-step navigation
        elif command == "h":
            cursor.movePosition(QtMoveLeft)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "j":
            cursor.movePosition(QtMoveDown)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "k":
            cursor.movePosition(QtMoveUp)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "l":
            cursor.movePosition(QtMoveRight)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

    def _handleVimVisualMode(self, event: QKeyEvent) -> None:
        """Handle key events for Vim mode VISUAL and VLINE mode motions."""
        key = event.text()
        cursor = self.textCursor()

        # -- VISUAL mode PREFIX
        if key in self._vim.VISUAL_PREFIX_KEYS:
            self._vim.pushCommandKey(key)
        else:
            # If adding none repeating visual mode motions,
            # need to add a suffix case, see normal mode.
            self._vim.setCommand(key)

        # --- VISUAL / VISUALLINE mode ---
        if (command := self._vim.command) in ("d", "x"):
            cursor.beginEditBlock()
            self._vim.yankToInternal(cursor.selectedText())
            cursor.removeSelectedText()
            cursor.endEditBlock()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "y":
            self._vim.yankToInternal(cursor.selectedText())
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self.setVimMode(nwVimMode.NORMAL)

        elif command == "w":
            cursor.movePosition(QtMoveNextWord, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "b":
            cursor.movePosition(QtMovePreviousWord, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "e":
            origPos = cursor.position()
            cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)
            if cursor.position() == origPos:
                textLen = len(self.toPlainText())
                if origPos < textLen:
                    cursor.movePosition(QtMoveNextChar, QtKeepAnchor)
                    cursor.movePosition(QtMoveEndOfWord, QtKeepAnchor)

            self.setTextCursor(cursor)
            self._vim.resetCommand()

        elif command == "gg":
            cursor.movePosition(QtMoveStart, QtKeepAnchor)
            self.setTextCursor(cursor)
            self._vim.resetCommand()

        # Handle motions (extend selection)
        elif command == "h":
            cursor.movePosition(QtMoveLeft, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "l":
            cursor.movePosition(QtMoveRight, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "j":
            cursor.movePosition(QtMoveDown, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "k":
            cursor.movePosition(QtMoveUp, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "$":
            cursor.movePosition(QtMoveEndOfLine, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "0":
            cursor.movePosition(QtMoveStartOfLine, QtKeepAnchor)
            self.setTextCursor(cursor)

        elif command == "G":
            cursor.movePosition(QtMoveEnd, QtKeepAnchor)
            self.setTextCursor(cursor)

    ##
    #  Internal Functions
    ##

    def _dispatchKeyPress(self, event: QKeyEvent) -> None:
        """Send a key event on to the base class for regular handling,
        except for a plain Return/Enter press, which is handled
        directly instead.

        Qt's own Return handling (QWidgetTextControlPrivate::
        insertParagraphSeparator) resets the current block's format to
        a bare default and swallows the keypress whenever the cursor
        is on an empty block whose format isn't already default. That
        heuristic exists so rich-text users can hit Enter twice to
        escape a list/heading/quote, but every block here always
        carries a non-default line height, so it fires on every
        ordinary blank-line paragraph break and silently eats every
        second Return. novelWriter never uses Qt's native list/heading
        block formatting, so the heuristic serves no purpose here, and
        can be bypassed entirely by inserting the new block directly.
        """
        if event.key() in ENTER_KEYS and event.modifiers() == QtModNone:
            cursor = self.textCursor()
            cursor.insertBlock()
            self.setTextCursor(cursor)
            self.ensureCursorVisible(centre=False)
            event.accept()
        else:
            super().keyPressEvent(event)

    def _hideHoverCard(self) -> None:
        """Stop the hover timer and hide the hover card, if visible."""
        self._timerHover.stop()
        self._hoverCard.hide()

    def _applyExtraSelections(self) -> None:
        """Set the editor's extra selections from the line highlight
        and the cached spell and format error markers.
        """
        selections = []
        if CONFIG.lineHighlight:
            selections.append(self._selection)
        selections.extend(self._searchSelections)
        selections.extend(self._spellSelections)
        selections.extend(self._formatSelections)
        self.setExtraSelections(selections)

    def _beginCheckPass(self) -> None:
        """Spell and format check the visible blocks, and start a chunked
        check of the entire document on the worker thread. If neither
        check is enabled, only the markers are cleared.
        """
        checkSpell = SHARED.project.data.spellCheck
        checkFormat = CONFIG.showMultiSpaces
        self._timerTextCheck.stop()
        self._dirtyBlocks.clear()
        self._checkJob = None
        self._checkPassPos = None
        if checkSpell or checkFormat:
            if viewport := self.viewport():  # pragma: no branch
                # Check the visible blocks first so that their result
                # is available immediately
                last = self.cursorForPosition(viewport.rect().bottomLeft()).blockNumber()
                block = self.cursorForPosition(viewport.rect().topLeft()).block()
                while block.isValid() and block.blockNumber() <= last:
                    if isinstance(data := block.userData(), TextBlockData):
                        if checkSpell:
                            data.spellCheck()
                        if checkFormat:
                            data.formatCheck()
                    block = block.next()
            self._checkPassPos = 0
            logger.debug("Text check starting background pass over %d blocks", self._qDocument.blockCount())
            self._dispatchTextCheck()
        self._updateCheckSelections()

    def _showCompleter(self) -> None:
        """Show, or reposition, the completer popup at the cursor."""
        self._completer.complete(self._completerRect())

    def _completerToCursor(self) -> None:
        """Make sure the completer popup is positioned by the cursor."""
        if (popup := self._completer.popup()) and popup.isVisible():
            self._showCompleter()

    def _completerRect(self) -> QRect:
        """Build the rect QCompleter positions its popup from. It maps
        the rect through the editor widget itself, but cursorRect() is
        in viewport coordinates, so that must be translated first (see
        issues #2267 and #2517), or the popup ends up offset by the
        viewport's margins. The rect is then widened to fit the
        popup's own content, or QCompleter renders it just as wide as
        the thin cursor blinker.
        """
        vM = self.viewportMargins()
        rect = self.cursorRect()
        rect.translate(vM.left(), vM.top())
        if popup := self._completer.popup():  # pragma: no branch
            width = popup.sizeHintForColumn(0)
            if bar := popup.verticalScrollBar():  # pragma: no branch
                width += bar.sizeHint().width()
            rect.setWidth(width)
        return rect

    def _correctWord(self, cursor: QTextCursor, word: str) -> None:
        """Slot for the spell check context menu triggering the
        replacement of a word with the word from the dictionary.
        """
        pos = cursor.selectionStart()
        cursor.beginEditBlock()
        cursor.removeSelectedText()
        cursor.insertText(word)
        cursor.endEditBlock()
        cursor.setPosition(pos)
        self.setTextCursor(cursor)

    def _addWord(self, word: str, block: QTextBlock, save: bool) -> None:
        """Slot for the spell check context menu triggered when the user
        wants to add a word to the project dictionary.
        """
        logger.debug("Added '%s' to project dictionary, %s", word, "saved" if save else "unsaved")
        SHARED.spelling.addWord(word, save=save)
        if isinstance(data := block.userData(), TextBlockData):  # pragma: no branch
            data.spellCheck()
        self._updateCheckSelections()

    def _processTag(
        self,
        cursor: QTextCursor | None = None,
        *,
        follow: bool = True,
        edit: bool = False,
        create: bool = False,
    ) -> _TagAction:
        """Activated by Ctrl+Enter. Checks that we're in a block
        starting with '@'. We then find the tag under the cursor and
        check that it is not the tag itself. If all this is fine, we
        have a tag and can tell the document viewer to try and find and
        load the file where the tag is defined.
        """
        if cursor is None:
            cursor = self.textCursor()

        status = _TagAction.NONE
        block = cursor.block()
        text = block.text()
        if len(text) == 0:
            return status

        if text.startswith("@") and self._docHandle:
            isGood, tBits, tPos = SHARED.project.index.scanThis(text)
            if not isGood or not tBits or (key := tBits[0]) == nwKeyWords.TAG_KEY or key not in nwKeyWords.VALID_KEYS:
                return status

            tag = ""
            exist = False
            cPos = cursor.selectionStart() - block.position()
            tExist = SHARED.project.index.checkThese(tBits, self._docHandle)
            for sTag, sPos, sExist in zip(reversed(tBits), reversed(tPos), reversed(tExist), strict=False):
                if cPos >= sPos:
                    # The cursor is between the start of two tags
                    if cPos <= sPos + len(sTag):
                        # The cursor is inside or at the edge of the tag
                        tag = sTag
                        exist = sExist
                    break

            if not tag or tag.startswith("@"):
                # The keyword cannot be looked up, so we ignore that
                return status

            if not exist and key in nwKeyWords.CAN_CREATE:
                # Must only be set if we have a tag selected
                status |= _TagAction.CREATE

            if exist:
                status |= _TagAction.FOLLOW

            if follow and exist:
                logger.debug("Attempting to follow tag '%s'", tag)
                self.loadDocumentTagRequest.emit(tag, nwDocMode.EDIT if edit else nwDocMode.VIEW)
            elif create and not exist:
                if SHARED.question(self.tr("Do you want to create a new project note for the tag '{0}'?").format(tag)):
                    itemClass = nwKeyWords.KEY_CLASS.get(tBits[0], nwItemClass.NO_CLASS)
                    self.requestNewNoteCreation.emit(tag, itemClass)

        return status

    def _emitRenameItem(self, block: QTextBlock) -> None:
        """Emit a signal to request an item be renamed."""
        if self._docHandle:
            text = block.text().lstrip("#").lstrip("!").strip()
            self.requestProjectItemRenamed.emit(self._docHandle, text)

    def _autoSelect(self) -> QTextCursor:
        """Return a cursor which may or may not have a selection based
        on user settings and document action. The selection will be the
        word closest to the cursor consisting of alphanumerical unicode
        characters.
        """
        cursor = self.textCursor()
        if CONFIG.autoSelect and not cursor.hasSelection():
            cPos = cursor.position()
            bPos = cursor.block().position()
            bLen = cursor.block().length()
            apos = nwUnicode.U_APOS + nwUnicode.U_RSQUO

            # Scan backward
            sPos = cPos
            for i in range(cPos - bPos):
                sPos = cPos - i - 1
                cOne = str(self._qDocument.characterAt(sPos))
                cTwo = str(self._qDocument.characterAt(sPos - 1))
                if not (cOne.isalnum() or (cOne in apos and cTwo.isalnum())):
                    sPos += 1
                    break

            # Scan forward
            ePos = cPos
            for i in range(bPos + bLen - cPos):  # pragma: no branch
                # The block's trailing (non-alnum) separator character is
                # always within range, so this loop always finds a
                # boundary and breaks before running to exhaustion.
                ePos = cPos + i
                cOne = str(self._qDocument.characterAt(ePos))
                cTwo = str(self._qDocument.characterAt(ePos + 1))
                if not (cOne.isalnum() or (cOne in apos and cTwo.isalnum())):
                    break

            if ePos - sPos <= 0:
                # No selection possible
                return cursor

            cursor.clearSelection()
            cursor.setPosition(sPos, QtMoveAnchor)
            cursor.setPosition(ePos, QtKeepAnchor)

            self.setTextCursor(cursor)

        return cursor

    def _makeSelection(self, mode: QTextCursor.SelectionType, cursor: QTextCursor | None = None) -> None:
        """Select text based on selection mode."""
        if cursor is None:
            cursor = self.textCursor()
        cursor.clearSelection()
        cursor.select(mode)

        if mode == QtSelectWord:
            cursor = self._autoSelect()

        elif mode == QtSelectBlock:
            # This selection mode also selects the preceding paragraph
            # separator, which we want to avoid.
            posS = cursor.selectionStart()
            posE = cursor.selectionEnd()
            selTxt = cursor.selectedText()
            if selTxt.startswith(nwUnicode.U_PSEP):
                cursor.setPosition(posS + 1, QtMoveAnchor)
                cursor.setPosition(posE, QtKeepAnchor)

        self.setTextCursor(cursor)

    def _makePosSelection(self, mode: QTextCursor.SelectionType, pos: QPoint) -> None:
        """Select text based on selection mode, but first move cursor."""
        cursor = self.cursorForPosition(pos)
        self.setTextCursor(cursor)
        self._makeSelection(mode)

    def _allowAutoReplace(self, state: bool) -> None:
        """Enable/disable the auto-replace feature temporarily."""
        if state:
            self._doReplace = CONFIG.doReplace
        else:
            self._doReplace = False

    def _skipToParagraph(self, step: int) -> None:
        """Move cursor to next paragraph by step."""
        if step != 0:
            block = self.textCursor().block()
            while block.isValid():
                block = block.next() if step > 0 else block.previous()
                if block.isValid() and block.text().strip():
                    cursor = self.textCursor()
                    cursor.setPosition(block.position())
                    self.setTextCursor(cursor)
                    break


class VimState:
    """Minimal Vim state machine."""

    __slots__ = ("_internalClipboard", "_mode", "_normalCommand", "_visualCommand")

    PREFIX_KEYS = "dygz"
    VISUAL_PREFIX_KEYS = "g"
    SUFFIX_KEYS = "web$"

    def __init__(self) -> None:
        self._mode: nwVimMode = nwVimMode.NORMAL
        self._normalCommand = ""
        self._visualCommand = ""
        self._internalClipboard = ""
        self.setMode(nwVimMode.NORMAL)

    @property
    def mode(self) -> nwVimMode:
        """Return current vim mode."""
        return self._mode

    @property
    def command(self) -> str:
        """Return the current vim command."""
        if self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            return self._visualCommand
        else:
            return self._normalCommand

    def setMode(self, mode: nwVimMode) -> None:
        """Switch vim mode."""
        if mode != self._mode:
            logger.debug("Vim Mode changed to %s", mode.name)
            self._mode = mode
            self.resetCommand()

    def resetCommand(self) -> None:
        """Reset internal vim command."""
        self._normalCommand = ""
        self._visualCommand = ""

    def pushCommandKey(self, key: str) -> None:
        """Push key to the current command building stack."""
        if self._mode is nwVimMode.NORMAL:
            self._normalCommand += key
        elif self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            self._visualCommand += key

    def setCommand(self, key: str) -> None:
        """Set the state of the current vim command."""
        if self._mode is nwVimMode.NORMAL:
            self._normalCommand = key
        elif self._mode in (nwVimMode.VISUAL, nwVimMode.V_LINE):
            self._visualCommand = key

    def yankToInternal(self, text: str) -> None:
        """Put text into internal vim buffer."""
        self._internalClipboard = text

    def pasteFromInternal(self) -> str:
        """Paste from the internal vim clipboard."""
        return self._internalClipboard
