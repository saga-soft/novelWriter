"""
novelWriter - Theme and Icons Classes
=====================================

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
import tomllib

from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING, Any, Final

from PyQt6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication, QSize, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QFontMetrics,
    QGuiApplication,
    QIcon,
    QPainter,
    QPainterPath,
    QPalette,
    QPixmap,
)
from PyQt6.QtWidgets import QApplication, QToolTip, QWidget

from novelwriter import CONFIG
from novelwriter.common import checkInt, minmax, safeIsFile
from novelwriter.config import DEF_GUI_DARK, DEF_GUI_LIGHT, DEF_ICONS, DEF_TREECOL
from novelwriter.constants import nwLabels
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType, nwStandardButton, nwTheme, nwToolButton
from novelwriter.error import logException
from novelwriter.extensions.modified import NFlatIconButton, NIconButton, NPushButton
from novelwriter.types import (
    QtBlack,
    QtColActive,
    QtColDisabled,
    QtColInactive,
    QtFontSemiBold,
    QtIconNormal,
    QtIconOff,
    QtIconOn,
    QtPaintAntiAlias,
    QtTransparent,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

STANDARD_BUTTONS = {
    nwStandardButton.OK: (QT_TRANSLATE_NOOP("Button", "OK"), "btn_ok:action"),
    nwStandardButton.CANCEL: (QT_TRANSLATE_NOOP("Button", "Cancel"), "btn_cancel:reject"),
    nwStandardButton.YES: (QT_TRANSLATE_NOOP("Button", "&Yes"), "btn_yes:accept"),
    nwStandardButton.NO: (QT_TRANSLATE_NOOP("Button", "&No"), "btn_no:reject"),
    nwStandardButton.OPEN: (QT_TRANSLATE_NOOP("Button", "Open"), "btn_open:action"),
    nwStandardButton.CLOSE: (QT_TRANSLATE_NOOP("Button", "Close"), "btn_close:destroy"),
    nwStandardButton.SAVE: (QT_TRANSLATE_NOOP("Button", "Save"), "btn_save:action"),
    nwStandardButton.BROWSE: (QT_TRANSLATE_NOOP("Button", "Browse"), "btn_browse:system"),
    nwStandardButton.LIST: (QT_TRANSLATE_NOOP("Button", "List"), "btn_list:action"),
    nwStandardButton.NEW: (QT_TRANSLATE_NOOP("Button", "New"), "btn_new:apply"),
    nwStandardButton.CREATE: (QT_TRANSLATE_NOOP("Button", "Create"), "btn_create:create"),
    nwStandardButton.RESET: (QT_TRANSLATE_NOOP("Button", "Reset"), "btn_reset:reset"),
    nwStandardButton.INSERT: (QT_TRANSLATE_NOOP("Button", "Insert"), "btn_insert:action"),
    nwStandardButton.APPLY: (QT_TRANSLATE_NOOP("Button", "Apply"), "btn_apply:apply"),
    nwStandardButton.BUILD: (QT_TRANSLATE_NOOP("Button", "Build"), "btn_build:action"),
    nwStandardButton.PRINT: (QT_TRANSLATE_NOOP("Button", "Print"), "btn_print:action"),
    nwStandardButton.PREVIEW: (QT_TRANSLATE_NOOP("Button", "Preview"), "btn_preview:action"),
}

TOOL_BUTTONS = {
    nwToolButton.ADD: (QT_TRANSLATE_NOOP("Button", "Add"), "add:add"),
    nwToolButton.REMOVE: (QT_TRANSLATE_NOOP("Button", "Remove"), "remove:remove"),
    nwToolButton.MOVE_UP: (QT_TRANSLATE_NOOP("Button", "Move Up"), "chevron_up:action"),
    nwToolButton.MOVE_DOWN: (QT_TRANSLATE_NOOP("Button", "Move Down"), "chevron_down:action"),
    nwToolButton.IMPORT: (QT_TRANSLATE_NOOP("Button", "Import"), "import:apply"),
    nwToolButton.EXPORT: (QT_TRANSLATE_NOOP("Button", "Export"), "export:action"),
    nwToolButton.BROWSE: (QT_TRANSLATE_NOOP("Button", "Browse"), "browse:system"),
    nwToolButton.EDIT: (QT_TRANSLATE_NOOP("Button", "Edit"), "edit:change"),
    nwToolButton.REVERT: (QT_TRANSLATE_NOOP("Button", "Revert"), "revert:reset"),
    nwToolButton.FONT: (QT_TRANSLATE_NOOP("Button", "Select Font"), "font:tool"),
}


@dataclass
class ThemeEntry:
    """Theme data."""

    name: str
    dark: bool
    path: Path


class ThemeMeta:
    """Theme meta data."""

    name: str = ""
    mode: str = ""
    author: str = ""
    credit: str = ""
    url: str = ""


class IconsMeta:
    """Icon theme meta data."""

    name: str = ""
    author: str = ""
    license: str = ""


class SyntaxColors:
    """Colours for the syntax highlighter."""

    back: QColor = QColor(255, 255, 255)
    text: QColor = QColor(0, 0, 0)
    line: QColor = QColor(0, 0, 0)
    link: QColor = QColor(0, 0, 0)
    head: QColor = QColor(0, 0, 0)
    headH: QColor = QColor(0, 0, 0)
    emph: QColor = QColor(0, 0, 0)
    space: QColor = QColor(0, 0, 0)
    dialN: QColor = QColor(0, 0, 0)
    dialA: QColor = QColor(0, 0, 0)
    hidden: QColor = QColor(0, 0, 0)
    note: QColor = QColor(0, 0, 0)
    code: QColor = QColor(0, 0, 0)
    key: QColor = QColor(0, 0, 0)
    tag: QColor = QColor(0, 0, 0)
    val: QColor = QColor(0, 0, 0)
    opt: QColor = QColor(0, 0, 0)
    spell: QColor = QColor(0, 0, 0)
    error: QColor = QColor(0, 0, 0)
    repTag: QColor = QColor(0, 0, 0)
    mod: QColor = QColor(0, 0, 0)
    mark: QColor = QColor(255, 255, 255, 128)


class GuiTheme:
    """Gui Theme Class.

    Handles the look and feel of novelWriter.
    """

    __slots__ = (
        "_allThemes",
        "_currentTheme",
        "_darkThemes",
        "_guiPalette",
        "_lightThemes",
        "_meta",
        "_qColors",
        "_svgColors",
        "_syntaxList",
        "accentCol",
        "accentText",
        "activeBase",
        "activeButton",
        "baseButtonHeight",
        "baseIconHeight",
        "baseIconSize",
        "errorText",
        "fadedText",
        "fontPixelSize",
        "fontPixelSizeLarge",
        "fontPointSize",
        "getDecoration",
        "getFlatButton",
        "getHeaderDecoration",
        "getHeaderDecorationNarrow",
        "getIcon",
        "getIconButton",
        "getItemIcon",
        "getItemIconStyle",
        "getPixmap",
        "getStandardButton",
        "getToggleIcon",
        "guiFont",
        "guiFontB",
        "guiFontBU",
        "guiFontFixed",
        "guiFontLarge",
        "guiFontLargeB",
        "guiFontSmall",
        "guiFontSmallB",
        "helpText",
        "iconCache",
        "isDarkTheme",
        "pushButtonIconSize",
        "searchCol",
        "sidebarIconSize",
        "syntaxTheme",
        "textNHeight",
        "textNWidth",
        "toolButtonIconSize",
    )

    def __init__(self) -> None:

        # Theme Objects
        self.iconCache = GuiIcons(self)
        self.syntaxTheme = SyntaxColors()
        self.isDarkTheme = False

        # Special Colours
        self.helpText = QColor(0, 0, 0)
        self.fadedText = QColor(0, 0, 0)
        self.errorText = QColor(255, 0, 0)
        self.accentText = QColor(0, 0, 255)
        self.accentCol = QColor(255, 0, 255)  # Needed until we move to Qt 6.6
        self.activeButton = QColor(0, 0, 255)
        self.activeBase = QColor(225, 225, 225)
        self.searchCol = QColor(255, 196, 0, 96)

        # Theme Data
        self._meta = ThemeMeta()
        self._currentTheme = ""
        self._guiPalette = QPalette()
        self._allThemes: dict[str, ThemeEntry] = {}
        self._svgColors: dict[str, bytes] = {}
        self._qColors: dict[str, QColor] = {}

        # Icon Functions
        self.getIcon = self.iconCache.getIcon
        self.getPixmap = self.iconCache.getPixmap
        self.getItemIcon = self.iconCache.getItemIcon
        self.getToggleIcon = self.iconCache.getToggleIcon
        self.getDecoration = self.iconCache.getDecoration
        self.getIconButton = self.iconCache.getIconButton
        self.getFlatButton = self.iconCache.getFlatButton
        self.getItemIconStyle = self.iconCache.getItemIconStyle
        self.getStandardButton = self.iconCache.getStandardButton
        self.getHeaderDecoration = self.iconCache.getHeaderDecoration
        self.getHeaderDecorationNarrow = self.iconCache.getHeaderDecorationNarrow

        # Fonts
        sSmaller = 10.0 / 11.0
        sMedium = 12.0 / 11.0
        sLarger = 13.0 / 11.0
        sLarge = 15.0 / 11.0
        sXLarge = 19.0 / 11.0

        self.guiFont = QApplication.font()
        self.guiFontB = QApplication.font()
        self.guiFontB.setWeight(QtFontSemiBold)
        self.guiFontBU = QApplication.font()
        self.guiFontBU.setWeight(QtFontSemiBold)
        self.guiFontBU.setUnderline(True)

        self.guiFontSmall = QApplication.font()
        self.guiFontSmall.setPointSizeF(sSmaller * self.guiFont.pointSizeF())
        self.guiFontSmallB = QApplication.font()
        self.guiFontSmallB.setWeight(QtFontSemiBold)
        self.guiFontSmallB.setPointSizeF(sSmaller * self.guiFont.pointSizeF())

        self.guiFontLarge = QApplication.font()
        self.guiFontLarge.setPointSizeF(sLarger * self.guiFont.pointSizeF())
        self.guiFontLargeB = QApplication.font()
        self.guiFontLargeB.setWeight(QtFontSemiBold)
        self.guiFontLargeB.setPointSizeF(sLarger * self.guiFont.pointSizeF())

        qMetric = QFontMetrics(self.guiFont)
        fHeight = qMetric.height()
        fAscent = qMetric.ascent()

        self.fontPointSize = self.guiFont.pointSizeF()
        self.fontPixelSize = fHeight
        self.fontPixelSizeLarge = round(sLarger * fHeight)
        self.baseIconHeight = fAscent
        self.baseButtonHeight = round(sLarge * fAscent)

        self.baseIconSize = QSize(fAscent, fAscent)
        self.sidebarIconSize = QSize(round(sXLarge * fAscent), round(sXLarge * fAscent))
        self.toolButtonIconSize = QSize(round(sSmaller * fAscent), round(sSmaller * fAscent))
        self.pushButtonIconSize = QSize(round(sMedium * fAscent), round(sMedium * fAscent))

        self.textNHeight = qMetric.boundingRect("N").height()
        self.textNWidth = qMetric.boundingRect("N").width()

        # Monospace Font
        self.guiFontFixed = QFont()
        self.guiFontFixed.setPointSizeF(sSmaller * self.fontPointSize)
        self.guiFontFixed.setFamily(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont).family())

        logger.debug("GUI Font Family: %s", self.guiFont.family())
        logger.debug("GUI Font Point Size: %.2f pt", self.fontPointSize)
        logger.debug("GUI Font Pixel Size: %d px", self.fontPixelSize)
        logger.debug("GUI Base Icon Height: %d px", self.baseIconHeight)
        logger.debug("GUI Base Button Height: %d px", self.baseButtonHeight)
        logger.debug("GUI Sidebar Icon Height: %s px", self.sidebarIconSize.height())
        logger.debug("GUI ToolButton Icon Height: %s px", self.toolButtonIconSize.height())
        logger.debug("GUI PushButton Icon Height: %s px", self.pushButtonIconSize.height())
        logger.debug("Text 'N' Height: %d px", self.textNHeight)
        logger.debug("Text 'N' Width: %d px", self.textNWidth)

    ##
    #  Properties
    ##

    @property
    def colourThemes(self) -> dict[str, ThemeEntry]:
        """Return a dictionary of all themes."""
        return self._allThemes

    @property
    def themeInfo(self) -> ThemeMeta:
        """Return the metadata for the current theme."""
        return self._meta

    ##
    #  Getters
    ##

    def getTextWidth(self, text: str, font: QFont | None = None) -> int:
        """Return the width needed to contain a given piece of text in
        pixels.
        """
        if isinstance(font, QFont):
            qMetrics = QFontMetrics(font)
        else:
            qMetrics = QFontMetrics(self.guiFont)
        return ceil(qMetrics.boundingRect(text).width())

    def getBaseColor(self, name: str) -> QColor:
        """Return a base color."""
        return QColor(self._qColors.get(name) or QtBlack)

    def getRawBaseColor(self, name: str) -> bytes:
        """Return a base color."""
        if color := self._svgColors.get(name):
            return color
        logger.warning("No colour named '%s'", name)
        return self._svgColors.get("default", b"#000000")

    def getStructureColor(self, hLevel: int) -> QColor:
        """Return a structure color."""
        match hLevel:
            case 1:
                name = "title"
            case 2:
                name = "chapter"
            case 3:
                name = "scene"
            case _:
                name = "file"
        return QColor(self._qColors.get(name) or QtTransparent)

    ##
    #  Theme Methods
    ##

    def initThemes(self) -> None:
        """Initialise themes."""
        CONFIG.splashMessage("Scanning for colour themes ...")
        themes: list[Path] = []
        _listContent(themes, CONFIG.assetPath("themes"), ".toml")
        _listContent(themes, CONFIG.dataPath("themes"), ".toml")
        self._scanThemes(themes)

        self.iconCache.initIcons()
        self.loadTheme()

    def isDesktopDarkMode(self, schemeHint: Any | None = None) -> bool:
        """Check if the desktop is in dark mode."""
        if CONFIG.checkMinQtVersion(0x060500):
            # Qt.ColorScheme was added in Qt 6.5
            if schemeHint is not None:
                return schemeHint == Qt.ColorScheme.Dark
            elif styleHints := QGuiApplication.styleHints():
                return styleHints.colorScheme() == Qt.ColorScheme.Dark

        palette = QPalette()
        text = palette.windowText().color()
        window = palette.window().color()
        return text.lightnessF() > window.lightnessF()

    def loadTheme(self, *, schemeHint: Any | None = None, force: bool = False) -> bool:
        """Load the currently specified GUI theme. The boolean return
        can be used to determine if the GUI needs refreshing.
        """
        match CONFIG.themeMode:
            case nwTheme.LIGHT:
                darkMode = False
            case nwTheme.DARK:
                darkMode = True
            case _:
                darkMode = self.isDesktopDarkMode(schemeHint=schemeHint)

        theme = CONFIG.darkTheme if darkMode else CONFIG.lightTheme
        if theme not in self._allThemes:
            logger.error("Could not find theme '%s'", theme)
            if darkMode:
                theme = DEF_GUI_DARK
                CONFIG.darkTheme = DEF_GUI_DARK
            else:
                theme = DEF_GUI_LIGHT
                CONFIG.lightTheme = DEF_GUI_LIGHT

        if theme == self._currentTheme and not force:
            logger.info("Theme '%s' is already loaded", theme)
            return False

        entry = self._allThemes.get(theme)
        if not entry:
            logger.error("Could not load GUI theme")
            return False

        CONFIG.splashMessage(f"Loading colour theme: {entry.name}")
        logger.info("Loading GUI theme '%s'", theme)
        try:
            with open(entry.path, mode="rb") as fileObj:
                data = tomllib.load(fileObj)
        except Exception:
            logger.error("Could not read file: %s", entry.path)
            logException()
            return False

        # Reset Palette
        self._resetTheme()

        # Main
        meta = ThemeMeta()
        if section := data.get("Main"):
            meta.name = section.get("name", "")
            meta.mode = section.get("mode", "light")
            meta.author = section.get("author", "")
            meta.credit = section.get("credit", "")
            meta.url = section.get("url", "")

        self._meta = meta

        # Base
        if section := data.get("Base"):
            self._setBaseColor("base", self._readColor(section, "base"))
            self._setBaseColor("default", self._readColor(section, "default"))
            self._setBaseColor("faded", self._readColor(section, "faded"))
            self._setBaseColor("red", self._readColor(section, "red"))
            self._setBaseColor("orange", self._readColor(section, "orange"))
            self._setBaseColor("yellow", self._readColor(section, "yellow"))
            self._setBaseColor("green", self._readColor(section, "green"))
            self._setBaseColor("cyan", self._readColor(section, "cyan"))
            self._setBaseColor("blue", self._readColor(section, "blue"))
            self._setBaseColor("purple", self._readColor(section, "purple"))

        # Project
        if section := data.get("Project"):
            self._setBaseColor("root", self._readColor(section, "root"))
            self._setBaseColor("folder", self._readColor(section, "folder"))
            self._setBaseColor("file", self._readColor(section, "file"))
            self._setBaseColor("title", self._readColor(section, "title"))
            self._setBaseColor("chapter", self._readColor(section, "chapter"))
            self._setBaseColor("scene", self._readColor(section, "scene"))
            self._setBaseColor("note", self._readColor(section, "note"))
            self._setBaseColor("active", self._readColor(section, "active"))
            self._setBaseColor("inactive", self._readColor(section, "inactive"))
            self._setBaseColor("disabled", self._readColor(section, "disabled"))

        # Icon
        if section := data.get("Icon"):
            self._setBaseColor("tool", self._readColor(section, "tool"))
            self._setBaseColor("sidebar", self._readColor(section, "sidebar"))
            self._setBaseColor("accept", self._readColor(section, "accept"))
            self._setBaseColor("reject", self._readColor(section, "reject"))
            self._setBaseColor("action", self._readColor(section, "action"))
            self._setBaseColor("option", self._readColor(section, "option"))
            self._setBaseColor("apply", self._readColor(section, "apply"))
            self._setBaseColor("create", self._readColor(section, "create"))
            self._setBaseColor("destroy", self._readColor(section, "destroy"))
            self._setBaseColor("reset", self._readColor(section, "reset"))
            self._setBaseColor("add", self._readColor(section, "add"))
            self._setBaseColor("change", self._readColor(section, "change"))
            self._setBaseColor("remove", self._readColor(section, "remove"))
            self._setBaseColor("shortcode", self._readColor(section, "shortcode"))
            self._setBaseColor("markdown", self._readColor(section, "markdown"))
            self._setBaseColor("system", self._readColor(section, "system"))
            self._setBaseColor("info", self._readColor(section, "info"))
            self._setBaseColor("warning", self._readColor(section, "warning"))
            self._setBaseColor("error", self._readColor(section, "error"))

        # Palette
        if section := data.get("Palette"):
            self._setPalette(section, "window", QPalette.ColorRole.Window)
            self._setPalette(section, "windowText", QPalette.ColorRole.WindowText)
            self._setPalette(section, "base", QPalette.ColorRole.Base)
            self._setPalette(section, "alternateBase", QPalette.ColorRole.AlternateBase)
            self._setPalette(section, "text", QPalette.ColorRole.Text)
            self._setPalette(section, "tooltipBase", QPalette.ColorRole.ToolTipBase)
            self._setPalette(section, "tooltipText", QPalette.ColorRole.ToolTipText)
            self._setPalette(section, "button", QPalette.ColorRole.Button)
            self._setPalette(section, "buttonText", QPalette.ColorRole.ButtonText)
            self._setPalette(section, "brightText", QPalette.ColorRole.BrightText)
            self._setPalette(section, "highlight", QPalette.ColorRole.Highlight)
            self._setPalette(section, "highlightedText", QPalette.ColorRole.HighlightedText)
            self._setPalette(section, "link", QPalette.ColorRole.Link)
            self._setPalette(section, "linkVisited", QPalette.ColorRole.LinkVisited)
            self.accentCol = self._readColor(section, "accent")  # Special handling 'til Qt 6.6

        # GUI
        if section := data.get("GUI"):
            self.helpText = self._readColor(section, "helpText")
            self.fadedText = self._readColor(section, "fadedText")
            self.errorText = self._readColor(section, "errorText")
            self.accentText = self._readColor(section, "accentText")
            self.activeButton = self._readColor(section, "activeButton")
            self.activeBase = self._readColor(section, "activeBase")
            self.searchCol = self._readColor(section, "searchMatch")

        # Syntax
        self.syntaxTheme = SyntaxColors()
        if section := data.get("Syntax"):
            self.syntaxTheme.back = self._readColor(section, "background")
            self.syntaxTheme.text = self._readColor(section, "text")
            self.syntaxTheme.line = self._readColor(section, "line")
            self.syntaxTheme.link = self._readColor(section, "link")
            self.syntaxTheme.head = self._readColor(section, "headerText")
            self.syntaxTheme.headH = self._readColor(section, "headerTag")
            self.syntaxTheme.emph = self._readColor(section, "emphasis")
            self.syntaxTheme.space = self._readColor(section, "whitespace")
            self.syntaxTheme.dialN = self._readColor(section, "dialog")
            self.syntaxTheme.dialA = self._readColor(section, "altDialog")
            self.syntaxTheme.hidden = self._readColor(section, "hidden")
            self.syntaxTheme.note = self._readColor(section, "note")
            self.syntaxTheme.code = self._readColor(section, "shortcode")
            self.syntaxTheme.key = self._readColor(section, "keyword")
            self.syntaxTheme.tag = self._readColor(section, "tag")
            self.syntaxTheme.val = self._readColor(section, "value")
            self.syntaxTheme.opt = self._readColor(section, "optional")
            self.syntaxTheme.spell = self._readColor(section, "spellCheckLine")
            self.syntaxTheme.error = self._readColor(section, "errorLine")
            self.syntaxTheme.repTag = self._readColor(section, "replaceTag")
            self.syntaxTheme.mod = self._readColor(section, "modifier")
            self.syntaxTheme.mark = self._readColor(section, "textHighlight")

        # Update Dependant Colours
        # Based on: https://github.com/qt/qtbase/blob/dev/src/gui/kernel/qplatformtheme.cpp
        text = self._guiPalette.text().color()
        window = self._guiPalette.window().color()
        highlight = self._guiPalette.highlight().color()

        if window.lightnessF() < 0.15:
            # If window is too dark, we need a lighter ref colour for shades
            ref = QColor.fromHslF(window.hueF(), window.saturationF(), 0.15, window.alphaF())
        else:
            ref = window

        light = ref.lighter(150)
        mid = ref.darker(130)
        midLight = mid.lighter(110)
        dark = ref.darker(150)
        shadow = dark.darker(135)
        darkOff = dark.darker(150)
        shadowOff = ref.darker(150)

        grey = QColor(120, 120, 120) if darkMode else QColor(140, 140, 140)
        dimmed = QColor(130, 130, 130) if darkMode else QColor(190, 190, 190)

        placeholder = QColor(text)
        placeholder.setAlpha(128)

        self._guiPalette.setBrush(QPalette.ColorRole.Light, light)
        self._guiPalette.setBrush(QPalette.ColorRole.Mid, mid)
        self._guiPalette.setBrush(QPalette.ColorRole.Midlight, midLight)
        self._guiPalette.setBrush(QPalette.ColorRole.Dark, dark)
        self._guiPalette.setBrush(QPalette.ColorRole.Shadow, shadow)

        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Text, dimmed)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.WindowText, dimmed)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.ButtonText, dimmed)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Base, window)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Dark, darkOff)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Shadow, shadowOff)

        self._guiPalette.setBrush(QPalette.ColorRole.PlaceholderText, placeholder)

        self._guiPalette.setBrush(QtColActive, QPalette.ColorRole.Highlight, highlight)
        self._guiPalette.setBrush(QtColInactive, QPalette.ColorRole.Highlight, highlight)
        self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Highlight, grey)

        if CONFIG.checkMinQtVersion(0x060600):
            self._guiPalette.setBrush(QtColActive, QPalette.ColorRole.Accent, self.accentCol)
            self._guiPalette.setBrush(QtColInactive, QPalette.ColorRole.Accent, self.accentCol)
            self._guiPalette.setBrush(QtColDisabled, QPalette.ColorRole.Accent, grey)

        # Set project override colours
        if (override := CONFIG.iconColTree) != DEF_TREECOL:
            color = self._qColors.get(override, QtBlack)
            self._setBaseColor("root", color)
            self._setBaseColor("folder", color)
            if not CONFIG.iconColDocs:
                self._setBaseColor("file", color)
                self._setBaseColor("title", color)
                self._setBaseColor("chapter", color)
                self._setBaseColor("scene", color)
                self._setBaseColor("note", color)

        self.isDarkTheme = darkMode
        self._currentTheme = theme

        # Load icons after the theme is parsed
        self.iconCache.loadTheme(CONFIG.iconTheme)

        # Finalise
        QApplication.setPalette(self._guiPalette)
        QToolTip.setPalette(self._guiPalette)  # Fixes an issue with desktop overrides on Linux, see #2871

        return True

    def parseColor(self, value: str, default: QColor = QtBlack) -> QColor:
        """Parse a string as a colour value."""
        if value in self._qColors:
            # Named colour
            return self._qColors[value]
        elif value.startswith("#") and len(value) == 7:
            # Assume #RRGGBB
            return QColor.fromString(value)
        elif value.startswith("#") and len(value) == 9:
            # Assume #RRGGBBAA and convert to #AARRGGBB
            return QColor.fromString(f"#{value[7:9]}{value[1:7]}")
        elif ":" in value:
            # Colour name and lighter, darker or alpha
            name, _, adjust = value.partition(":")
            color = QColor(self._qColors.get(name.strip(), default))
            if adjust.startswith("L"):
                color = color.lighter(minmax(checkInt(adjust[1:], 100), 0, 10000))
            elif adjust.startswith("D"):
                color = color.darker(minmax(checkInt(adjust[1:], 100), 0, 10000))
            else:
                color.setAlpha(minmax(checkInt(adjust, 255), 0, 255))
            return color
        elif "," in value:
            # Integer red, green, blue, alpha
            data = value.split(",")
            result = [0, 0, 0, 255]
            for i in range(min(len(data), 4)):
                result[i] = minmax(checkInt(data[i].strip(), result[i]), 0, 255)
            return QColor(*result)
        return default

    def generateColorRange(self, start: str, end: str, mid: str | None = None, steps: int = 10) -> list[QColor]:
        """Generate a range of colours between start and end, optionally passing through mid."""
        result: list[QColor] = []
        scale = max(steps - 1, 1)
        colS = self.parseColor(start)
        colE = self.parseColor(end)
        colM = self.parseColor(mid) if mid is not None else None

        if colM is None:
            for i in range(steps):
                t = i / scale
                r = round(colS.red() + (colE.red() - colS.red()) * t)
                g = round(colS.green() + (colE.green() - colS.green()) * t)
                b = round(colS.blue() + (colE.blue() - colS.blue()) * t)
                a = round(colS.alpha() + (colE.alpha() - colS.alpha()) * t)
                result.append(QColor(r, g, b, a))
        else:
            for i in range(steps):
                t = i / scale
                if t < 0.5:
                    t *= 2
                    r = round(colS.red() + (colM.red() - colS.red()) * t)
                    g = round(colS.green() + (colM.green() - colS.green()) * t)
                    b = round(colS.blue() + (colM.blue() - colS.blue()) * t)
                    a = round(colS.alpha() + (colM.alpha() - colS.alpha()) * t)
                else:
                    t = (t - 0.5) * 2
                    r = round(colM.red() + (colE.red() - colM.red()) * t)
                    g = round(colM.green() + (colE.green() - colM.green()) * t)
                    b = round(colM.blue() + (colE.blue() - colM.blue()) * t)
                    a = round(colM.alpha() + (colE.alpha() - colM.alpha()) * t)
                result.append(QColor(r, g, b, a))
        return result

    ##
    #  Internal Functions
    ##

    def _setBaseColor(self, key: str, color: QColor) -> None:
        """Set the colour for a named colour."""
        self._qColors[key] = QColor(color)
        self._svgColors[key] = color.name(QColor.NameFormat.HexRgb).encode("utf-8")

    def _resetTheme(self) -> None:
        """Reset GUI colours to default values."""
        palette = QPalette()
        isDark = self.isDesktopDarkMode()

        # Reset GUI Palette
        base = palette.color(QPalette.ColorRole.Base)
        altBase = palette.color(QPalette.ColorRole.AlternateBase)
        default = palette.color(QPalette.ColorRole.Text)
        faded = QColor(128, 128, 128)
        dimmed = QColor(130, 130, 130) if isDark else QColor(190, 190, 190)
        red = QColor(242, 119, 122) if isDark else QColor(240, 40, 41)
        orange = QColor(249, 145, 57) if isDark else QColor(245, 135, 31)
        yellow = QColor(255, 204, 102) if isDark else QColor(234, 183, 0)
        green = QColor(153, 204, 153) if isDark else QColor(113, 140, 0)
        cyan = QColor(102, 204, 204) if isDark else QColor(62, 153, 159)
        blue = QColor(102, 153, 204) if isDark else QColor(66, 113, 174)
        purple = QColor(204, 153, 204) if isDark else QColor(137, 89, 168)

        # Text Colours
        self.helpText = dimmed
        self.fadedText = faded
        self.errorText = red
        self.accentText = blue

        # Accent Colours
        self.accentCol = purple
        self.activeButton = blue
        self.activeBase = altBase
        self.searchCol = QColor(orange)
        self.searchCol.setAlpha(96)

        self._guiPalette = palette

        # Reset Base Colours and Icons
        self.iconCache.clear()
        self._svgColors = {}
        self._qColors = {}

        # Base
        self._setBaseColor("base", base)
        self._setBaseColor("default", default)
        self._setBaseColor("faded", faded)
        self._setBaseColor("red", red)
        self._setBaseColor("orange", orange)
        self._setBaseColor("yellow", yellow)
        self._setBaseColor("green", green)
        self._setBaseColor("cyan", cyan)
        self._setBaseColor("blue", blue)
        self._setBaseColor("purple", purple)

        # Project
        self._setBaseColor("root", blue)
        self._setBaseColor("folder", yellow)
        self._setBaseColor("file", default)
        self._setBaseColor("title", green)
        self._setBaseColor("chapter", red)
        self._setBaseColor("scene", blue)
        self._setBaseColor("note", yellow)
        self._setBaseColor("active", green)
        self._setBaseColor("inactive", red)
        self._setBaseColor("disabled", faded)

        # Icon
        self._setBaseColor("tool", default)
        self._setBaseColor("sidebar", default)
        self._setBaseColor("accept", green)
        self._setBaseColor("reject", red)
        self._setBaseColor("action", blue)
        self._setBaseColor("option", orange)
        self._setBaseColor("apply", green)
        self._setBaseColor("create", yellow)
        self._setBaseColor("destroy", faded)
        self._setBaseColor("reset", green)
        self._setBaseColor("add", green)
        self._setBaseColor("change", green)
        self._setBaseColor("remove", red)
        self._setBaseColor("shortcode", default)
        self._setBaseColor("markdown", orange)
        self._setBaseColor("system", yellow)
        self._setBaseColor("info", blue)
        self._setBaseColor("warning", orange)
        self._setBaseColor("error", red)

    def _readColor(self, section: dict[str, Any], name: str) -> QColor:
        """Parse a colour value from a config string."""
        return self.parseColor(str(section.get(name, "default")))

    def _setPalette(self, section: dict[str, Any], name: str, value: QPalette.ColorRole) -> None:
        """Set a palette colour value from a config string."""
        self._guiPalette.setBrush(value, self._readColor(section, name))

    def _scanThemes(self, files: list[Path]) -> None:
        """Scan the GUI themes folder and list all themes."""
        data: dict[str, tuple[str, str, bool, Path]] = {}
        keys = []
        for file in files:
            try:
                with open(file, mode="rb") as fileObj:
                    section = tomllib.load(fileObj).get("Main", {})
                name = section.get("name", "")
                mode = section.get("mode", "").lower()
                if name and mode in ("light", "dark"):
                    key = file.stem
                    prefix = "*" if key.startswith("default") else ""
                    lookup = f"{prefix}{name} {key}"
                    keys.append(lookup)
                    data[lookup] = (file.stem, name, mode == "dark", file)
            except Exception:
                logger.error("Could not read file: %s", file)
                logException()

        self._allThemes = {}
        for lookup in sorted(keys):
            key, name, dark, item = data[lookup]
            logger.debug("Checking theme config '%s'", key)
            self._allThemes[key] = ThemeEntry(name, dark, item)


class GuiIcons:
    """The icon class manages the content of the assets/icons folder,
    and provides a simple interface for requesting icons.

    Icons are generated from SVG on first request, and then cached for
    further requests. If the icon is not defined, a placeholder icon is
    returned instead.
    """

    __slots__ = (
        "_allThemes",
        "_headerDec",
        "_headerDecNarrow",
        "_meta",
        "_noIcon",
        "_qIcons",
        "_svgData",
        "_theme",
    )

    TOGGLE_ICON_KEYS: Final[dict[str, tuple[str, str]]] = {
        "toggle-bullet": ("bullet-on", "bullet-off"),
        "toggle-unfold": ("unfold-show", "unfold-hide"),
    }
    IMAGE_MAP: Final[dict[str, tuple[str, str]]] = {
        "welcome": ("welcome.webp", "welcome.webp"),
        "nw-text": ("novelwriter-text-light.svg", "novelwriter-text-dark.svg"),
    }

    def __init__(self, mainTheme: GuiTheme) -> None:

        self._theme = mainTheme
        self._meta = IconsMeta()

        # Storage
        self._allThemes: dict[str, ThemeEntry] = {}
        self._svgData: dict[str, bytes] = {}
        self._qIcons: dict[str, QIcon] = {}
        self._headerDec: list[QPixmap] = []
        self._headerDecNarrow: list[QPixmap] = []

        # None Icon
        self._noIcon = QIcon(str(CONFIG.assetPath("icons") / "none.svg"))

    def clear(self) -> None:
        """Clear the icon cache."""
        self._svgData = {}
        self._qIcons = {}
        self._headerDec = []
        self._headerDecNarrow = []
        self._meta = ThemeMeta()

    ##
    #  Properties
    ##

    @property
    def iconThemes(self) -> dict[str, ThemeEntry]:
        """Return a dictionary of all icon themes."""
        return self._allThemes

    ##
    #  Actions
    ##

    def initIcons(self) -> None:
        """Initialise icons."""
        CONFIG.splashMessage("Scanning for icon themes ...")
        icons: list[Path] = []
        _listContent(icons, CONFIG.assetPath("icons"), ".icons")
        _listContent(icons, CONFIG.dataPath("icons"), ".icons")
        self._scanThemes(icons)

    def loadTheme(self, theme: str) -> None:
        """Update the theme map. This is more of an init, since many of
        the GUI icons cannot really be replaced without writing specific
        update functions for the classes where they're used.
        """
        if theme not in self._allThemes:
            logger.error("Could not find icon theme '%s'", theme)
            theme = DEF_ICONS
            CONFIG.iconTheme = theme

        entry = self._allThemes.get(theme)
        if not entry:
            logger.error("Could not load icon theme")
            return

        CONFIG.splashMessage(f"Loading icon theme: {entry.name}")
        logger.info("Loading icon theme '%s'", theme)
        try:
            meta = IconsMeta()
            with open(entry.path, mode="r", encoding="utf-8") as icons:
                for icon in icons:
                    bits = icon.partition("=")
                    key = bits[0].strip()
                    value = bits[2].strip()
                    if key and value:
                        if key.startswith("icon:"):
                            self._svgData[key[5:]] = value.encode("utf-8")
                        elif key == "meta:name":
                            meta.name = value
                        elif key == "meta:author":
                            meta.author = value
                        elif key == "meta:license":
                            meta.license = value
            self._meta = meta
        except Exception:
            logger.error("Could not read file: %s", entry.path)
            logException()
            return

        # Populate generated icons cache
        CONFIG.splashMessage("Generating additional icons ...")
        self.getHeaderDecoration(0)
        self.getHeaderDecorationNarrow(0)

        return

    ##
    #  Access Functions
    ##

    def getIcon(self, name: str, width: int = 24, height: int = 24) -> QIcon:
        """Return an icon from the icon buffer, or load it."""
        color = "default"
        if ":" in name:
            name, _, color = name.partition(":")
        variant = f"{name}-{color}" if color else name
        if (key := f"{variant}-{width}x{height}") in self._qIcons:
            return self._qIcons[key]
        else:
            icon = self._loadIcon(name, color, width, height)
            self._qIcons[key] = icon
            logger.debug("Icon: %s", key)
            return icon

    def getToggleIcon(self, name: str, width: int, height: int) -> QIcon:
        """Return a toggle icon from the icon buffer, or load it."""
        key, _, color = name.partition(":")
        if key in self.TOGGLE_ICON_KEYS:
            pix0 = self.getPixmap(f"{self.TOGGLE_ICON_KEYS[key][0]}:{color}", width, height)
            pix1 = self.getPixmap(f"{self.TOGGLE_ICON_KEYS[key][1]}:{color}", width, height)
            icon = QIcon()
            icon.addPixmap(pix0, QtIconNormal, QtIconOn)
            icon.addPixmap(pix1, QtIconNormal, QtIconOff)
            return icon
        return self._noIcon

    def getItemIcon(self, tType: nwItemType, tClass: nwItemClass, tLayout: nwItemLayout, hLevel: str = "H0") -> QIcon:
        """Get the correct icon for a project item based on type, class
        and heading level.
        """
        if name := self.getItemIconStyle(tType, tClass, tLayout, hLevel):
            return self.getIcon(name)
        return self._noIcon

    def getItemIconStyle(
        self,
        tType: nwItemType,
        tClass: nwItemClass,
        tLayout: nwItemLayout,
        hLevel: str = "H0",
    ) -> str:
        """Get the correct icon styles for a project item based on type,
        class and heading level.
        """
        name = ""
        if tType == nwItemType.ROOT:
            name = nwLabels.CLASS_ICON[tClass]
        elif tType == nwItemType.FOLDER:
            name = "prj_folder:folder"
        elif tType == nwItemType.FILE:
            if tLayout == nwItemLayout.DOCUMENT:
                if hLevel == "H1":
                    name = "prj_title:title"
                elif hLevel == "H2":
                    name = "prj_chapter:chapter"
                elif hLevel == "H3":
                    name = "prj_scene:scene"
                else:
                    name = "prj_document:file"
            elif tLayout == nwItemLayout.NOTE:
                name = "prj_note:note"

        return name

    def getPixmap(self, name: str, width: int, height: int) -> QPixmap:
        """Return an icon from the icon buffer as a QPixmap. If it
        doesn't exist, return an empty QPixmap.
        """
        return self.getIcon(name, width, height).pixmap(width, height, QtIconNormal)

    def getStandardButton(self, button: nwStandardButton, parent: QWidget) -> NPushButton:
        """Return a standard button with icon and text."""
        text, icon = STANDARD_BUTTONS.get(button, ("", ""))
        return NPushButton(
            parent,
            QCoreApplication.translate("Button", text),
            self._theme.pushButtonIconSize,
            icon,
        )

    def getIconButton(self, button: nwToolButton, parent: QWidget) -> NIconButton:
        """Return a tool button with icon."""
        toolTip, icon = TOOL_BUTTONS.get(button, ("", ""))
        toolButton = NIconButton(parent, self._theme.baseIconSize, icon)
        toolButton.setToolTip(QCoreApplication.translate("Button", toolTip))
        return toolButton

    def getFlatButton(self, button: nwToolButton, parent: QWidget) -> NFlatIconButton:
        """Return a tool button with icon."""
        toolTip, icon = TOOL_BUTTONS.get(button, ("", ""))
        toolButton = NFlatIconButton(parent, self._theme.baseIconSize, icon)
        toolButton.setToolTip(QCoreApplication.translate("Button", toolTip))
        return toolButton

    def getDecoration(self, name: str, w: int | None = None, h: int | None = None) -> QPixmap:
        """Load graphical decoration element based on the decoration
        map or the icon map. This function always returns a QPixmap.
        """
        if name in self.IMAGE_MAP:
            idx = int(self._theme.isDarkTheme)
            imgPath = CONFIG.assetPath("images") / self.IMAGE_MAP[name][idx]
        else:
            logger.error("Decoration with name '%s' does not exist", name)
            return QPixmap()

        if not safeIsFile(imgPath):
            logger.error("Asset not found: %s", imgPath)
            return QPixmap()

        pixmap = QPixmap(str(imgPath))
        tMode = Qt.TransformationMode.SmoothTransformation
        if w is not None and h is not None:
            return pixmap.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, tMode)
        elif w is None and h is not None:
            return pixmap.scaledToHeight(h, tMode)
        elif w is not None and h is None:
            return pixmap.scaledToWidth(w, tMode)

        return pixmap

    def getHeaderDecoration(self, hLevel: int) -> QPixmap:
        """Get the decoration for a specific heading level."""
        if not self._headerDec:
            iPx = self._theme.baseIconHeight
            self._headerDec = [
                self._generateDecoration("file", iPx, 0),
                self._generateDecoration("title", iPx, 0),
                self._generateDecoration("chapter", iPx, 1),
                self._generateDecoration("scene", iPx, 2),
                self._generateDecoration("file", iPx, 3),
            ]
        return self._headerDec[minmax(hLevel, 0, 4)]

    def getHeaderDecorationNarrow(self, hLevel: int) -> QPixmap:
        """Get the narrow decoration for a specific heading level."""
        if not self._headerDecNarrow:
            iPx = self._theme.baseIconHeight
            self._headerDecNarrow = [
                self._generateDecoration("file", iPx, 0),
                self._generateDecoration("title", iPx, 0),
                self._generateDecoration("chapter", iPx, 0),
                self._generateDecoration("scene", iPx, 0),
                self._generateDecoration("file", iPx, 0),
                self._generateDecoration("note", iPx, 0),
            ]
        return self._headerDecNarrow[minmax(hLevel, 0, 5)]

    ##
    #  Internal Functions
    ##

    def _loadIcon(self, name: str, color: str | None = None, w: int = 24, h: int = 24) -> QIcon:
        """Load an icon from the assets themes folder. This function is
        guaranteed to return a QIcon.
        """
        # If we just want the app icons, return right away
        if name == "novelwriter":
            return QIcon(str(CONFIG.assetPath("icons") / "novelwriter.svg"))
        elif name == "proj_nwx":
            return QIcon(str(CONFIG.assetPath("icons") / "x-novelwriter-project.svg"))

        if svg := self._svgData.get(name, b""):
            if fill := self._theme.getRawBaseColor(color or "default"):  # pragma: no branch
                svg = svg.replace(b"#000000", fill)
            pixmap = QPixmap(w, h)
            pixmap.fill(QtTransparent)
            pixmap.loadFromData(svg, "svg")
            return QIcon(pixmap)

        # If we didn't find one, give up and return an empty icon
        logger.warning("Did not load an icon for '%s'", name)

        return self._noIcon

    def _generateDecoration(self, color: str, height: int, indent: int = 0) -> QPixmap:
        """Generate a decoration pixmap for novel headers."""
        pixmap = QPixmap(48 * indent + 12, 48)
        pixmap.fill(QtTransparent)

        path = QPainterPath()
        path.addRoundedRect(48.0 * indent, 2.0, 12.0, 44.0, 4.0, 4.0)

        painter = QPainter(pixmap)
        painter.setRenderHint(QtPaintAntiAlias)
        if fill := self._theme.getRawBaseColor(color or "default"):  # pragma: no branch
            painter.fillPath(path, QColor(fill.decode(encoding="utf-8")))
        painter.end()

        tMode = Qt.TransformationMode.SmoothTransformation
        return pixmap.scaledToHeight(height, tMode)

    def _scanThemes(self, entries: list[Path]) -> None:
        """Scan the GUI themes folder and list all themes."""
        data: dict[str, tuple[str, str, Path]] = {}
        keys = []
        for entry in entries:
            try:
                with open(entry, mode="r", encoding="utf-8") as fo:
                    for line in fo:
                        key, _, value = line.partition("=")
                        if key.strip() == "meta:name":
                            if name := value.strip():
                                lookup = entry.stem
                                keys.append(lookup)
                                data[lookup] = (lookup, name, entry)
                            break
            except Exception:
                logger.error("Could not read file: %s", entry)
                logException()

        self._allThemes = {}
        for lookup in sorted(keys):
            key, name, item = data[lookup]
            logger.debug("Checking icon theme '%s'", key)
            self._allThemes[key] = ThemeEntry(name, False, item)


# Module Functions
# ================


def _listContent(data: list[Path], path: Path, extension: str) -> None:
    """List files of a specific type and extend the list."""
    try:
        if path.is_dir():
            data.extend(n for n in path.iterdir() if n.is_file() and n.suffix == extension)
    except Exception:
        logException()
