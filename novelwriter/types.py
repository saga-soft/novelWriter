"""
novelWriter - Types and Flags
=============================

This file is a part of novelWriter
Copyright (C) 2024 Veronica Berglyd Olsen and novelWriter contributors

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

from typing import Literal

from PyQt6.QtCore import QAbstractAnimation, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QKeySequence,
    QPainter,
    QPalette,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QHeaderView, QSizePolicy, QStyle

# Custom Types

T_MsgSeverity = Literal["info", "warning", "error"]

# Alignment Flags

QtAlignAbsolute = Qt.AlignmentFlag.AlignAbsolute
QtAlignCenter = Qt.AlignmentFlag.AlignCenter
QtAlignHCenter = Qt.AlignmentFlag.AlignHCenter
QtAlignCenterTop = Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
QtAlignJustify = Qt.AlignmentFlag.AlignJustify
QtAlignLeft = Qt.AlignmentFlag.AlignLeft
QtAlignLeftBase = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBaseline
QtAlignLeftMiddle = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
QtAlignLeftTop = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
QtAlignMiddle = Qt.AlignmentFlag.AlignVCenter
QtAlignRight = Qt.AlignmentFlag.AlignRight
QtAlignRightBase = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBaseline
QtAlignRightMiddle = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
QtAlignRightTop = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
QtAlignTop = Qt.AlignmentFlag.AlignTop

QtVAlignNormal = QTextCharFormat.VerticalAlignment.AlignNormal
QtVAlignSub = QTextCharFormat.VerticalAlignment.AlignSubScript
QtVAlignSuper = QTextCharFormat.VerticalAlignment.AlignSuperScript

# Text Formats

QtPageBreakBefore = QTextFormat.PageBreakFlag.PageBreak_AlwaysBefore
QtPageBreakAfter = QTextFormat.PageBreakFlag.PageBreak_AlwaysAfter
QtPageBreakAuto = QTextFormat.PageBreakFlag.PageBreak_Auto

QtTextUserProperty = QTextFormat.Property.UserProperty

QtPropLineHeight = 1  # QTextBlockFormat.LineHeightTypes.ProportionalHeight

QtElideLeft = Qt.TextElideMode.ElideLeft
QtElideRight = Qt.TextElideMode.ElideRight

# Painter Types

QtTransparent = QColor(0, 0, 0, 0)
QtBlack = QColor(0, 0, 0)
QtWhite = QColor(255, 255, 255)
QtNoBrush = Qt.BrushStyle.NoBrush
QtNoPen = Qt.PenStyle.NoPen
QtRoundCap = Qt.PenCapStyle.RoundCap
QtSolidLine = Qt.PenStyle.SolidLine
QtPaintAntiAlias = QPainter.RenderHint.Antialiasing
QtMouseOver = QStyle.StateFlag.State_MouseOver
QtSelected = QStyle.StateFlag.State_Selected

QAnimDeleteWhenStopped = QAbstractAnimation.DeletionPolicy.DeleteWhenStopped

# Colour Types

QtHexRgb = QColor.NameFormat.HexRgb
QtHexArgb = QColor.NameFormat.HexArgb

QtColActive = QPalette.ColorGroup.Active
QtColInactive = QPalette.ColorGroup.Inactive
QtColDisabled = QPalette.ColorGroup.Disabled

# Styles

QtToolButtonTextIcon = Qt.ToolButtonStyle.ToolButtonTextBesideIcon
QtToolButtonIconOnly = Qt.ToolButtonStyle.ToolButtonIconOnly

# Model Item Data

QtAccessibleTextRole = Qt.ItemDataRole.AccessibleTextRole
QtDecorationRole = Qt.ItemDataRole.DecorationRole
QtDisplayRole = Qt.ItemDataRole.DisplayRole
QtFontRole = Qt.ItemDataRole.FontRole
QtForegroundRole = Qt.ItemDataRole.ForegroundRole
QtTextAlignmentRole = Qt.ItemDataRole.TextAlignmentRole
QtToolTipRole = Qt.ItemDataRole.ToolTipRole
QtUserRole = Qt.ItemDataRole.UserRole

# Keyboard and Mouse Buttons

QtKeyReturn = Qt.Key.Key_Return
QtKeyEnter = Qt.Key.Key_Enter
QtKeyLeft = Qt.Key.Key_Left
QtKeyRight = Qt.Key.Key_Right
QtKeyUp = Qt.Key.Key_Up
QtKeyDown = Qt.Key.Key_Down
QtKeyPageUp = Qt.Key.Key_PageUp
QtKeyPageDown = Qt.Key.Key_PageDown
QtKeyTab = Qt.Key.Key_Tab
QtKeyEscape = Qt.Key.Key_Escape
QtKeyBackspace = Qt.Key.Key_Backspace

QtModCtrl = Qt.KeyboardModifier.ControlModifier
QtModNone = Qt.KeyboardModifier.NoModifier
QtModShift = Qt.KeyboardModifier.ShiftModifier

QKeyRedo = QKeySequence.StandardKey.Redo
QKeyUndo = QKeySequence.StandardKey.Undo
QKeySelectAll = QKeySequence.StandardKey.SelectAll

QtMouseLeft = Qt.MouseButton.LeftButton
QtMouseMiddle = Qt.MouseButton.MiddleButton

QtWidgetShortcut = Qt.ShortcutContext.WidgetShortcut

# Dialog Button Box Types

QtAccepted = QDialog.DialogCode.Accepted
QtRejected = QDialog.DialogCode.Rejected

QtRoleAccept = QDialogButtonBox.ButtonRole.AcceptRole
QtRoleAction = QDialogButtonBox.ButtonRole.ActionRole
QtRoleApply = QDialogButtonBox.ButtonRole.ApplyRole
QtRoleDestruct = QDialogButtonBox.ButtonRole.DestructiveRole
QtRoleReject = QDialogButtonBox.ButtonRole.RejectRole
QtRoleReset = QDialogButtonBox.ButtonRole.ResetRole

# Cursor Types

QtKeepAnchor = QTextCursor.MoveMode.KeepAnchor
QtMoveAnchor = QTextCursor.MoveMode.MoveAnchor

QtMoveLeft = QTextCursor.MoveOperation.Left
QtMoveRight = QTextCursor.MoveOperation.Right
QtMoveUp = QTextCursor.MoveOperation.Up
QtMoveDown = QTextCursor.MoveOperation.Down
QtMoveEndOfLine = QTextCursor.MoveOperation.EndOfLine
QtMoveStartOfLine = QTextCursor.MoveOperation.StartOfLine
QtMoveEnd = QTextCursor.MoveOperation.End
QtMoveStart = QTextCursor.MoveOperation.Start
QtMoveNextWord = QTextCursor.MoveOperation.NextWord
QtMovePreviousWord = QTextCursor.MoveOperation.PreviousWord
QtMoveEndOfWord = QTextCursor.MoveOperation.EndOfWord
QtMoveNextChar = QTextCursor.MoveOperation.NextCharacter

QtSelectWord = QTextCursor.SelectionType.WordUnderCursor
QtSelectLine = QTextCursor.SelectionType.LineUnderCursor
QtSelectBlock = QTextCursor.SelectionType.BlockUnderCursor
QtSelectDocument = QTextCursor.SelectionType.Document

QtImCursorRectangle = Qt.InputMethodQuery.ImCursorRectangle
QtImCurrentSelection = Qt.InputMethodQuery.ImCurrentSelection

# Size Policy

QtSizeExpanding = QSizePolicy.Policy.Expanding
QtSizeFixed = QSizePolicy.Policy.Fixed
QtSizeIgnored = QSizePolicy.Policy.Ignored
QtSizeMinimum = QSizePolicy.Policy.Minimum
QtSizeMinimumExpanding = QSizePolicy.Policy.MinimumExpanding

# Resize Mode

QtHeaderStretch = QHeaderView.ResizeMode.Stretch
QtHeaderToContents = QHeaderView.ResizeMode.ResizeToContents
QtHeaderFixed = QHeaderView.ResizeMode.Fixed
QtHeaderInteractive = QHeaderView.ResizeMode.Interactive

# Scroll Bar Policy

QtScrollAlwaysOn = Qt.ScrollBarPolicy.ScrollBarAlwaysOn
QtScrollAlwaysOff = Qt.ScrollBarPolicy.ScrollBarAlwaysOff
QtScrollAsNeeded = Qt.ScrollBarPolicy.ScrollBarAsNeeded

# Icon Modes

QtIconNormal = QIcon.Mode.Normal
QtIconDisabled = QIcon.Mode.Disabled
QtIconOn = QIcon.State.On
QtIconOff = QIcon.State.Off

# Font Weight

QtFontNormal = QFont.Weight.Normal
QtFontSemiBold = QFont.Weight.DemiBold
QtFontBold = QFont.Weight.Bold

# Maps

FONT_WEIGHTS: dict[int, int] = {
    QFont.Weight.Thin: 100,
    QFont.Weight.ExtraLight: 200,
    QFont.Weight.Light: 300,
    QFont.Weight.Normal: 400,
    QFont.Weight.Medium: 500,
    QFont.Weight.DemiBold: 600,
    QFont.Weight.Bold: 700,
    QFont.Weight.ExtraBold: 800,
    QFont.Weight.Black: 900,
}

FONT_STYLE: dict[QFont.Style, str] = {
    QFont.Style.StyleNormal: "normal",
    QFont.Style.StyleItalic: "italic",
    QFont.Style.StyleOblique: "oblique",
}
