"""
novelWriter - Constants
=======================

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

from typing import Final

from PyQt6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication

from novelwriter.enum import nwBuildFmt, nwComment, nwItemClass, nwItemLayout, nwStatusShape, nwTheme


def trConst(text: str) -> str:
    """Translate a constant."""
    return QCoreApplication.translate("Constant", text)


def trStats(text: str) -> str:
    """Translate a stats constants."""
    return QCoreApplication.translate("Stats", text)


class nwConst:
    """Various Constants."""

    # Date and Time Formats
    FMT_TSTAMP = "%Y-%m-%d %H:%M:%S"  # Default format
    FMT_DSTAMP = "%Y-%m-%d"  # Date only format

    # URLs
    URL_WEB = "https://novelwriter.io"
    URL_DOCS = "https://docs.novelwriter.io"
    URL_RELEASES = "https://releases.novelwriter.io"
    URL_CODE = "https://github.com/vkbo/novelWriter"
    URL_REPORT = "https://github.com/vkbo/novelWriter/issues"
    URL_HELP = "https://github.com/vkbo/novelWriter/discussions"

    # Requests
    USER_AGENT = "Mozilla/5.0 (compatible; novelWriter (Python))"

    # Mime Types
    MIME_HANDLE = "text/vnd.novelwriter.handle"
    MIME_MARKDOWN = "text/markdown"

    # Gui Settings
    STATUS_MSG_TIMEOUT = 15000  # milliseconds
    MAX_SEARCH_RESULT = 1000
    CHECK_PASS_CHUNK = 100  # Chunk size for spell and format checking
    BIG_DOC_LIMIT = 500000  # Doc size above which the initial cursor move is queued


class nwRegEx:
    """Common RegExes."""

    URL = r"\bhttps?://(?:www\.|(?!www))[\w/()@:%_\+-.~#!?&=]+\b"
    WORDS = r"\b[^\s\-\+\/–—\[\]:]+\b"  # noqa: RUF001
    BREAK = r"(?i)(?<!\\)(\[br\]\n?)"
    FMT_IT = r"(?<![\w\\])(_)(?![\s_])(.+?)(?<![\s\\])(\1)(?!\w)"
    FMT_B1 = r"(?<![\w\\])(\*{1,2})(?![\s\*])(.+?)(?<![\s\\])(\1)(?!\w)"
    FMT_B2 = r"(?<![\w\\])(\*{2})(?![\s\*])(.+?)(?<![\s\\])(\1)(?!\w)"
    FMT_ST = r"(?<![\w\\])(~{2})(?![\s~])(.+?)(?<![\s\\])(\1)(?!\w)"
    FMT_HL = r"(?<![\w\\])(={2})(?![\s=])(.+?)(?<![\s\\])(\1)(?!\w)"
    FMT_SC = r"(?i)(?<!\\)(\[(?:b|/b|i|/i|s|/s|u|/u|m|/m|sup|/sup|sub|/sub|br)\])"
    FMT_SV = r"(?i)(?<!\\)(\[(?:footnote|field):)(.+?)(?<!\\)(\])"


class nwShortcode:
    """Document ShortCodes."""

    BOLD_O = "[b]"
    BOLD_C = "[/b]"
    ITALIC_O = "[i]"
    ITALIC_C = "[/i]"
    STRIKE_O = "[s]"
    STRIKE_C = "[/s]"
    ULINE_O = "[u]"
    ULINE_C = "[/u]"
    MARK_O = "[m]"
    MARK_C = "[/m]"
    SUP_O = "[sup]"
    SUP_C = "[/sup]"
    SUB_O = "[sub]"
    SUB_C = "[/sub]"
    BREAK = "[br]"

    FOOTNOTE_B = "[footnote:"
    FIELD_B = "[field:"

    COMMENT_STYLES: Final[dict[nwComment, str]] = {
        nwComment.FOOTNOTE: "[footnote:{0}]",
        nwComment.COMMENT: "[comment:{0}]",
    }

    FIELD_VALUE = "[field:{0}]"


class nwStyles:
    """Style Settings for Headings."""

    H_VALID = ("H0", "H1", "H2", "H3", "H4")
    H_LEVEL: Final[dict[str, int]] = {"H0": 0, "H1": 1, "H2": 2, "H3": 3, "H4": 4}
    H_SIZES: Final[dict[int, float]] = {0: 2.50, 1: 2.00, 2: 1.75, 3: 1.50, 4: 1.25}

    T_NORMAL = 1.0
    T_SMALL = 0.8

    T_LABEL: Final[dict[str, str]] = {
        "H0": QT_TRANSLATE_NOOP("Constant", "Title"),
        "H1": QT_TRANSLATE_NOOP("Constant", "Heading 1 (Partition)"),
        "H2": QT_TRANSLATE_NOOP("Constant", "Heading 2 (Chapter)"),
        "H3": QT_TRANSLATE_NOOP("Constant", "Heading 3 (Scene)"),
        "H4": QT_TRANSLATE_NOOP("Constant", "Heading 4 (Section)"),
        "TT": QT_TRANSLATE_NOOP("Constant", "Text Paragraph"),
        "SP": QT_TRANSLATE_NOOP("Constant", "Scene Separator"),
    }
    T_MARGIN: Final[dict[str, tuple[float, float]]] = {
        "H0": (1.50, 0.60),  # Title margins (top, bottom)
        "H1": (1.50, 0.60),  # Heading 1 margins (top, bottom)
        "H2": (1.50, 0.60),  # Heading 2 margins (top, bottom)
        "H3": (1.20, 0.60),  # Heading 3 margins (top, bottom)
        "H4": (1.20, 0.60),  # Heading 4 margins (top, bottom)
        "TT": (0.00, 0.60),  # Text margins (top, bottom)
        "SP": (1.20, 1.20),  # Separator margins (top, bottom)
        "MT": (0.00, 0.60),  # Meta margins (top, bottom)
        "FT": (1.40, 0.40),  # Footnote margins (left, bottom)
    }


class nwFiles:
    """novelWriter Files."""

    # Config Files
    CONF_FILE = "novelwriter.toml"
    CONF_FILE_OLD = "novelwriter.conf"
    RECENT_FILE = "recentProjects.json"
    RECENT_PATH = "recentPaths.json"

    # Project Root Files
    PROJ_FILE = "nwProject.nwx"
    PROJ_LOCK = "nwProject.lock"
    TOC_TXT = "ToC.txt"

    # Project Meta Files
    BUILDS_FILE = "builds.json"
    INDEX_FILE = "index.json"
    OPTS_FILE = "options.json"
    DICT_FILE = "userdict.json"
    SESS_FILE = "sessions.jsonl"


class nwKeyWords:
    """Meta Data KeyWord Constants."""

    TAG_KEY = "@tag"
    POV_KEY = "@pov"
    FOCUS_KEY = "@focus"
    CHAR_KEY = "@char"
    PLOT_KEY = "@plot"
    TIME_KEY = "@time"
    WORLD_KEY = "@location"
    OBJECT_KEY = "@object"
    ENTITY_KEY = "@entity"
    CUSTOM_KEY = "@custom"
    STORY_KEY = "@story"
    MENTION_KEY = "@mention"

    # Note: The order here affects the order of menu entries
    ALL_KEYS: Final[list[str]] = [
        TAG_KEY,
        POV_KEY,
        FOCUS_KEY,
        CHAR_KEY,
        PLOT_KEY,
        TIME_KEY,
        WORLD_KEY,
        OBJECT_KEY,
        ENTITY_KEY,
        CUSTOM_KEY,
        STORY_KEY,
        MENTION_KEY,
    ]
    CAN_CREATE: Final[list[str]] = [
        POV_KEY,
        FOCUS_KEY,
        CHAR_KEY,
        PLOT_KEY,
        TIME_KEY,
        WORLD_KEY,
        OBJECT_KEY,
        ENTITY_KEY,
        CUSTOM_KEY,
    ]
    CAN_LOOKUP: Final[list[str]] = [
        POV_KEY,
        FOCUS_KEY,
        CHAR_KEY,
        PLOT_KEY,
        TIME_KEY,
        WORLD_KEY,
        OBJECT_KEY,
        ENTITY_KEY,
        CUSTOM_KEY,
        STORY_KEY,
        MENTION_KEY,
    ]

    # Set of Valid Keys
    VALID_KEYS: Final[set[str]] = set(ALL_KEYS)

    # Map from Keys to Item Class
    KEY_CLASS: Final[dict[str, nwItemClass]] = {
        POV_KEY: nwItemClass.CHARACTER,
        FOCUS_KEY: nwItemClass.CHARACTER,
        CHAR_KEY: nwItemClass.CHARACTER,
        PLOT_KEY: nwItemClass.PLOT,
        TIME_KEY: nwItemClass.TIMELINE,
        WORLD_KEY: nwItemClass.WORLD,
        OBJECT_KEY: nwItemClass.OBJECT,
        ENTITY_KEY: nwItemClass.ENTITY,
        CUSTOM_KEY: nwItemClass.CUSTOM,
        STORY_KEY: nwItemClass.NOVEL,
    }


class nwLists:
    """Various Lists."""

    USER_CLASSES: Final[list[nwItemClass]] = [
        nwItemClass.CHARACTER,
        nwItemClass.PLOT,
        nwItemClass.WORLD,
        nwItemClass.TIMELINE,
        nwItemClass.OBJECT,
        nwItemClass.ENTITY,
        nwItemClass.CUSTOM,
    ]


class nwStats:
    """Text Statistics."""

    CHARS = "allChars"
    CHARS_TEXT = "textChars"
    CHARS_TITLE = "titleChars"
    CHARS_DIALOG = "dialogChars"
    PARAGRAPHS = "paragraphCount"
    TITLES = "titleCount"
    WCHARS_ALL = "allWordChars"
    WCHARS_TEXT = "textWordChars"
    WCHARS_TITLE = "titleWordChars"
    WORDS = "allWords"
    WORDS_TEXT = "textWords"
    WORDS_TITLE = "titleWords"
    DIALOG_RATIO = "dialogRatio"

    # Note: The order here affects the order of menu entries
    ALL_FIELDS: Final[list[str]] = [
        WORDS,
        WORDS_TEXT,
        WORDS_TITLE,
        CHARS,
        CHARS_TEXT,
        CHARS_TITLE,
        WCHARS_ALL,
        WCHARS_TEXT,
        WCHARS_TITLE,
        PARAGRAPHS,
        TITLES,
    ]


class nwLabels:
    """Various Common GUI Labels."""

    CLASS_NAME: Final[dict[nwItemClass, str]] = {
        nwItemClass.NO_CLASS: QT_TRANSLATE_NOOP("Constant", "None"),
        nwItemClass.NOVEL: QT_TRANSLATE_NOOP("Constant", "Novel"),
        nwItemClass.PLOT: QT_TRANSLATE_NOOP("Constant", "Plot"),
        nwItemClass.CHARACTER: QT_TRANSLATE_NOOP("Constant", "Characters"),
        nwItemClass.WORLD: QT_TRANSLATE_NOOP("Constant", "Locations"),
        nwItemClass.TIMELINE: QT_TRANSLATE_NOOP("Constant", "Timeline"),
        nwItemClass.OBJECT: QT_TRANSLATE_NOOP("Constant", "Objects"),
        nwItemClass.ENTITY: QT_TRANSLATE_NOOP("Constant", "Entities"),
        nwItemClass.CUSTOM: QT_TRANSLATE_NOOP("Constant", "Custom"),
        nwItemClass.ARCHIVE: QT_TRANSLATE_NOOP("Constant", "Archive"),
        nwItemClass.TEMPLATE: QT_TRANSLATE_NOOP("Constant", "Templates"),
        nwItemClass.TRASH: QT_TRANSLATE_NOOP("Constant", "Trash"),
    }
    CLASS_ICON: Final[dict[nwItemClass, str]] = {
        nwItemClass.NO_CLASS: "cls_none:root",
        nwItemClass.NOVEL: "cls_novel:root",
        nwItemClass.PLOT: "cls_plot:root",
        nwItemClass.CHARACTER: "cls_character:root",
        nwItemClass.WORLD: "cls_world:root",
        nwItemClass.TIMELINE: "cls_timeline:root",
        nwItemClass.OBJECT: "cls_object:root",
        nwItemClass.ENTITY: "cls_entity:root",
        nwItemClass.CUSTOM: "cls_custom:root",
        nwItemClass.ARCHIVE: "cls_archive:root",
        nwItemClass.TEMPLATE: "cls_template:root",
        nwItemClass.TRASH: "cls_trash:root",
    }
    LAYOUT_NAME: Final[dict[nwItemLayout, str]] = {
        nwItemLayout.NO_LAYOUT: QT_TRANSLATE_NOOP("Constant", "None"),
        nwItemLayout.DOCUMENT: QT_TRANSLATE_NOOP("Constant", "Novel Document"),
        nwItemLayout.NOTE: QT_TRANSLATE_NOOP("Constant", "Project Note"),
    }
    ITEM_DESCRIPTION: Final[dict[str, str]] = {
        "none": QT_TRANSLATE_NOOP("Constant", "None"),
        "root": QT_TRANSLATE_NOOP("Constant", "Root Folder"),
        "folder": QT_TRANSLATE_NOOP("Constant", "Folder"),
        "document": QT_TRANSLATE_NOOP("Constant", "Novel Document"),
        "doc_h1": QT_TRANSLATE_NOOP("Constant", "Novel Title Page"),
        "doc_h2": QT_TRANSLATE_NOOP("Constant", "Novel Chapter"),
        "doc_h3": QT_TRANSLATE_NOOP("Constant", "Novel Scene"),
        "doc_h4": QT_TRANSLATE_NOOP("Constant", "Novel Section"),
        "note": QT_TRANSLATE_NOOP("Constant", "Project Note"),
    }
    ACTIVE_NAME: Final[dict[bool, str]] = {
        True: QT_TRANSLATE_NOOP("Constant", "Active"),
        False: QT_TRANSLATE_NOOP("Constant", "Inactive"),
    }
    KEY_NAME: Final[dict[str, str]] = {
        nwKeyWords.TAG_KEY: QT_TRANSLATE_NOOP("Constant", "Tag"),
        nwKeyWords.POV_KEY: QT_TRANSLATE_NOOP("Constant", "Point of View"),
        nwKeyWords.FOCUS_KEY: QT_TRANSLATE_NOOP("Constant", "Focus"),
        nwKeyWords.CHAR_KEY: QT_TRANSLATE_NOOP("Constant", "Characters"),
        nwKeyWords.PLOT_KEY: QT_TRANSLATE_NOOP("Constant", "Plot"),
        nwKeyWords.TIME_KEY: QT_TRANSLATE_NOOP("Constant", "Timeline"),
        nwKeyWords.WORLD_KEY: QT_TRANSLATE_NOOP("Constant", "Locations"),
        nwKeyWords.OBJECT_KEY: QT_TRANSLATE_NOOP("Constant", "Objects"),
        nwKeyWords.ENTITY_KEY: QT_TRANSLATE_NOOP("Constant", "Entities"),
        nwKeyWords.CUSTOM_KEY: QT_TRANSLATE_NOOP("Constant", "Custom"),
        nwKeyWords.STORY_KEY: QT_TRANSLATE_NOOP("Constant", "Story"),
        nwKeyWords.MENTION_KEY: QT_TRANSLATE_NOOP("Constant", "Mentions"),
    }
    KEY_SHORTCUT: Final[dict[str, str]] = {
        nwKeyWords.TAG_KEY: "Ctrl+K, G",
        nwKeyWords.POV_KEY: "Ctrl+K, V",
        nwKeyWords.FOCUS_KEY: "Ctrl+K, F",
        nwKeyWords.CHAR_KEY: "Ctrl+K, C",
        nwKeyWords.PLOT_KEY: "Ctrl+K, P",
        nwKeyWords.TIME_KEY: "Ctrl+K, T",
        nwKeyWords.WORLD_KEY: "Ctrl+K, L",
        nwKeyWords.OBJECT_KEY: "Ctrl+K, O",
        nwKeyWords.ENTITY_KEY: "Ctrl+K, E",
        nwKeyWords.CUSTOM_KEY: "Ctrl+K, X",
        nwKeyWords.STORY_KEY: "Ctrl+K, N",
        nwKeyWords.MENTION_KEY: "Ctrl+K, M",
    }
    STATS_NAME: Final[dict[str, str]] = {
        nwStats.CHARS: QT_TRANSLATE_NOOP("Stats", "Characters"),
        nwStats.CHARS_TEXT: QT_TRANSLATE_NOOP("Stats", "Characters in text"),
        nwStats.CHARS_TITLE: QT_TRANSLATE_NOOP("Stats", "Characters in headings"),
        nwStats.CHARS_DIALOG: QT_TRANSLATE_NOOP("Stats", "Characters in dialogue"),
        nwStats.PARAGRAPHS: QT_TRANSLATE_NOOP("Stats", "Paragraphs"),
        nwStats.TITLES: QT_TRANSLATE_NOOP("Stats", "Headings"),
        nwStats.WCHARS_ALL: QT_TRANSLATE_NOOP("Stats", "Characters, no spaces"),
        nwStats.WCHARS_TEXT: QT_TRANSLATE_NOOP("Stats", "Characters in text, no spaces"),
        nwStats.WCHARS_TITLE: QT_TRANSLATE_NOOP("Stats", "Characters in headings, no spaces"),
        nwStats.WORDS: QT_TRANSLATE_NOOP("Stats", "Words"),
        nwStats.WORDS_TEXT: QT_TRANSLATE_NOOP("Stats", "Words in text"),
        nwStats.WORDS_TITLE: QT_TRANSLATE_NOOP("Stats", "Words in headings"),
        nwStats.DIALOG_RATIO: QT_TRANSLATE_NOOP("Stats", "Dialogue"),
    }
    STATS_DISPLAY: Final[dict[str, str]] = {
        nwStats.CHARS: QT_TRANSLATE_NOOP("Stats", "Characters: {0} ({1})"),
        nwStats.WORDS: QT_TRANSLATE_NOOP("Stats", "Words: {0} ({1})"),
    }
    BUILD_FMT: Final[dict[nwBuildFmt, str]] = {
        nwBuildFmt.ODT: QT_TRANSLATE_NOOP("Constant", "Open Document (.odt)"),
        nwBuildFmt.FODT: QT_TRANSLATE_NOOP("Constant", "Flat Open Document (.fodt)"),
        nwBuildFmt.DOCX: QT_TRANSLATE_NOOP("Constant", "Microsoft Word Document (.docx)"),
        nwBuildFmt.HTML: QT_TRANSLATE_NOOP("Constant", "HTML 5 (.html)"),
        nwBuildFmt.EPUB: QT_TRANSLATE_NOOP("Constant", "Electronic Publication E-book (.epub)"),
        nwBuildFmt.NWD: QT_TRANSLATE_NOOP("Constant", "novelWriter Markup (.txt)"),
        nwBuildFmt.STD_MD: QT_TRANSLATE_NOOP("Constant", "Standard Markdown (.md)"),
        nwBuildFmt.EXT_MD: QT_TRANSLATE_NOOP("Constant", "Extended Markdown (.md)"),
        nwBuildFmt.PDF: QT_TRANSLATE_NOOP("Constant", "Portable Document Format (.pdf)"),
        nwBuildFmt.J_HTML: QT_TRANSLATE_NOOP("Constant", "JSON + HTML 5 (.json)"),
        nwBuildFmt.J_NWD: QT_TRANSLATE_NOOP("Constant", "JSON + novelWriter Markup (.json)"),
    }
    BUILD_EXT: Final[dict[nwBuildFmt, str]] = {
        nwBuildFmt.ODT: ".odt",
        nwBuildFmt.FODT: ".fodt",
        nwBuildFmt.DOCX: ".docx",
        nwBuildFmt.HTML: ".html",
        nwBuildFmt.EPUB: ".epub",
        nwBuildFmt.NWD: ".txt",
        nwBuildFmt.STD_MD: ".md",
        nwBuildFmt.EXT_MD: ".md",
        nwBuildFmt.PDF: ".pdf",
        nwBuildFmt.J_HTML: ".json",
        nwBuildFmt.J_NWD: ".json",
    }
    SHAPES_PLAIN: Final[dict[nwStatusShape, str]] = {
        nwStatusShape.SQUARE: QT_TRANSLATE_NOOP("Constant", "Square"),
        nwStatusShape.TRIANGLE: QT_TRANSLATE_NOOP("Constant", "Triangle"),
        nwStatusShape.NABLA: QT_TRANSLATE_NOOP("Constant", "Nabla"),
        nwStatusShape.DIAMOND: QT_TRANSLATE_NOOP("Constant", "Diamond"),
        nwStatusShape.PENTAGON: QT_TRANSLATE_NOOP("Constant", "Pentagon"),
        nwStatusShape.HEXAGON: QT_TRANSLATE_NOOP("Constant", "Hexagon"),
        nwStatusShape.STAR: QT_TRANSLATE_NOOP("Constant", "Star"),
        nwStatusShape.PACMAN: QT_TRANSLATE_NOOP("Constant", "Pacman"),
    }
    SHAPES_CIRCLE: Final[dict[nwStatusShape, str]] = {
        nwStatusShape.CIRCLE_Q: QT_TRANSLATE_NOOP("Constant", "1/4 Circle"),
        nwStatusShape.CIRCLE_H: QT_TRANSLATE_NOOP("Constant", "Half Circle"),
        nwStatusShape.CIRCLE_T: QT_TRANSLATE_NOOP("Constant", "3/4 Circle"),
        nwStatusShape.CIRCLE: QT_TRANSLATE_NOOP("Constant", "Full Circle"),
    }
    SHAPES_BARS: Final[dict[nwStatusShape, str]] = {
        nwStatusShape.BARS_1: QT_TRANSLATE_NOOP("Constant", "1 Bar"),
        nwStatusShape.BARS_2: QT_TRANSLATE_NOOP("Constant", "2 Bars"),
        nwStatusShape.BARS_3: QT_TRANSLATE_NOOP("Constant", "3 Bars"),
        nwStatusShape.BARS_4: QT_TRANSLATE_NOOP("Constant", "4 Bars"),
    }
    SHAPES_BLOCKS: Final[dict[nwStatusShape, str]] = {
        nwStatusShape.BLOCK_1: QT_TRANSLATE_NOOP("Constant", "1 Block"),
        nwStatusShape.BLOCK_2: QT_TRANSLATE_NOOP("Constant", "2 Blocks"),
        nwStatusShape.BLOCK_3: QT_TRANSLATE_NOOP("Constant", "3 Blocks"),
        nwStatusShape.BLOCK_4: QT_TRANSLATE_NOOP("Constant", "4 Blocks"),
    }
    FILE_FILTERS: Final[dict[str, str]] = {
        "*.txt": QT_TRANSLATE_NOOP("Constant", "Text files"),
        "*.md": QT_TRANSLATE_NOOP("Constant", "Markdown files"),
        "*.csv": QT_TRANSLATE_NOOP("Constant", "CSV files"),
        "*": QT_TRANSLATE_NOOP("Constant", "All files"),
    }
    UNIT_NAME: Final[dict[str, str]] = {
        "mm": QT_TRANSLATE_NOOP("Constant", "Millimetres"),
        "cm": QT_TRANSLATE_NOOP("Constant", "Centimetres"),
        "in": QT_TRANSLATE_NOOP("Constant", "Inches"),
    }
    UNIT_SCALE: Final[dict[str, float]] = {
        "mm": 1.0,
        "cm": 10.0,
        "in": 25.4,
    }
    PAPER_NAME: Final[dict[str, str]] = {
        "A4": QT_TRANSLATE_NOOP("Constant", "A4"),
        "A5": QT_TRANSLATE_NOOP("Constant", "A5"),
        "A6": QT_TRANSLATE_NOOP("Constant", "A6"),
        "Legal": QT_TRANSLATE_NOOP("Constant", "US Legal"),
        "Letter": QT_TRANSLATE_NOOP("Constant", "US Letter"),
        "Custom": QT_TRANSLATE_NOOP("Constant", "Custom"),
    }
    PAPER_SIZE: Final[dict[str, tuple[float, float]]] = {
        "A4": (210.0, 297.0),
        "A5": (148.0, 210.0),
        "A6": (105.0, 148.0),
        "Legal": (215.9, 355.6),
        "Letter": (215.9, 279.4),
        "Custom": (-1.0, -1.0),
    }
    THEME_COLORS: Final[dict[str, str]] = {
        "default": QT_TRANSLATE_NOOP("Constant", "Foreground Colour"),
        "base": QT_TRANSLATE_NOOP("Constant", "Background Colour"),
        "faded": QT_TRANSLATE_NOOP("Constant", "Faded Colour"),
        "red": QT_TRANSLATE_NOOP("Constant", "Red"),
        "orange": QT_TRANSLATE_NOOP("Constant", "Orange"),
        "yellow": QT_TRANSLATE_NOOP("Constant", "Yellow"),
        "green": QT_TRANSLATE_NOOP("Constant", "Green"),
        "cyan": QT_TRANSLATE_NOOP("Constant", "Cyan"),
        "blue": QT_TRANSLATE_NOOP("Constant", "Blue"),
        "purple": QT_TRANSLATE_NOOP("Constant", "Purple"),
    }
    THEME_MODE_ICON: Final[dict[nwTheme, str]] = {
        nwTheme.AUTO: "theme_auto:sidebar",
        nwTheme.LIGHT: "theme_light:sidebar",
        nwTheme.DARK: "theme_dark:sidebar",
    }
    THEME_MODE_LABEL: Final[dict[nwTheme, str]] = {
        nwTheme.AUTO: QT_TRANSLATE_NOOP("Constant", "System Theme"),
        nwTheme.LIGHT: QT_TRANSLATE_NOOP("Constant", "Light Theme"),
        nwTheme.DARK: QT_TRANSLATE_NOOP("Constant", "Dark Theme"),
    }
    BACKUP_INTERVAL: Final[dict[str, str]] = {
        "session": QT_TRANSLATE_NOOP("Constant", "Per Session"),
        "day": QT_TRANSLATE_NOOP("Constant", "Per Day"),
        "week": QT_TRANSLATE_NOOP("Constant", "Per Week"),
        "month": QT_TRANSLATE_NOOP("Constant", "Per Month"),
    }
    FILTER_GROUPS: Final[dict[str, str]] = {
        "documents": QT_TRANSLATE_NOOP("Constant", "Document Filters"),
        "content": QT_TRANSLATE_NOOP("Constant", "Content Filters"),
    }
    FILTER_TYPES: Final[dict[str, str]] = {
        "novel": QT_TRANSLATE_NOOP("Constant", "Novel documents"),
        "notes": QT_TRANSLATE_NOOP("Constant", "Project notes"),
        "inactive": QT_TRANSLATE_NOOP("Constant", "Inactive documents"),
        "headings": QT_TRANSLATE_NOOP("Constant", "Headings"),
        "text": QT_TRANSLATE_NOOP("Constant", "Body text paragraphs"),
        "meta": QT_TRANSLATE_NOOP("Constant", "Tags and references"),
        "comments": QT_TRANSLATE_NOOP("Constant", "Comments and footnotes"),
    }


class nwHeadFmt:
    """Manuscript Header Formats."""

    BR = "{BR}"
    TITLE = "{Title}"
    CH_NUM = "{Chapter}"
    CH_WORD = "{Chapter:Word}"
    CH_ROMU = "{Chapter:URoman}"
    CH_ROML = "{Chapter:LRoman}"
    SC_NUM = "{Scene}"
    SC_ABS = "{Scene:Abs}"
    CHAR_POV = "{Char:POV}"
    CHAR_FOCUS = "{Char:Focus}"
    HRULE = "----"

    PAGE_HEADERS: Final[list[str]] = [
        TITLE,
        CH_NUM,
        CH_WORD,
        CH_ROMU,
        CH_ROML,
        SC_NUM,
        SC_ABS,
        CHAR_POV,
        CHAR_FOCUS,
    ]

    # Document Page Header
    DOC_PROJECT = "{Project}"
    DOC_AUTHOR = "{Author}"
    DOC_PAGE = "{Page}"
    DOC_AUTO = "{Project} / {Author} / {Page}"


class nwQuotes:
    """Allowed quotation marks.

    Source: https://en.wikipedia.org/wiki/Quotation_mark
    """

    SYMBOLS: Final[dict[str, str]] = {
        "\u0027": QT_TRANSLATE_NOOP("Constant", "Straight single quotation mark"),
        "\u0022": QT_TRANSLATE_NOOP("Constant", "Straight double quotation mark"),
        "\u2018": QT_TRANSLATE_NOOP("Constant", "Left single quotation mark"),
        "\u2019": QT_TRANSLATE_NOOP("Constant", "Right single quotation mark"),
        "\u201a": QT_TRANSLATE_NOOP("Constant", "Single low-9 quotation mark"),
        "\u201b": QT_TRANSLATE_NOOP("Constant", "Single high-reversed-9 quotation mark"),
        "\u201c": QT_TRANSLATE_NOOP("Constant", "Left double quotation mark"),
        "\u201d": QT_TRANSLATE_NOOP("Constant", "Right double quotation mark"),
        "\u201e": QT_TRANSLATE_NOOP("Constant", "Double low-9 quotation mark"),
        "\u201f": QT_TRANSLATE_NOOP("Constant", "Double high-reversed-9 quotation mark"),
        "\u2e42": QT_TRANSLATE_NOOP("Constant", "Double low-reversed-9 quotation mark"),
        "\u2039": QT_TRANSLATE_NOOP("Constant", "Single left-pointing angle quotation mark"),
        "\u203a": QT_TRANSLATE_NOOP("Constant", "Single right-pointing angle quotation mark"),
        "\u00ab": QT_TRANSLATE_NOOP("Constant", "Double left-pointing angle quotation mark"),
        "\u00bb": QT_TRANSLATE_NOOP("Constant", "Double right-pointing angle quotation mark"),
        "\u300c": QT_TRANSLATE_NOOP("Constant", "Left corner bracket"),
        "\u300d": QT_TRANSLATE_NOOP("Constant", "Right corner bracket"),
        "\u300e": QT_TRANSLATE_NOOP("Constant", "Left white corner bracket"),
        "\u300f": QT_TRANSLATE_NOOP("Constant", "Right white corner bracket"),
    }

    DASHES: Final[dict[str, str]] = {
        "": QT_TRANSLATE_NOOP("Constant", "None"),
        "\u2013": QT_TRANSLATE_NOOP("Constant", "Short dash"),
        "\u2014": QT_TRANSLATE_NOOP("Constant", "Long dash"),
        "\u2015": QT_TRANSLATE_NOOP("Constant", "Horizontal bar"),
    }

    ALLOWED: Final[list[str]] = [
        "\u0027",
        "\u0022",
        "\u2018",
        "\u2019",
        "\u201a",
        "\u201b",
        "\u201c",
        "\u201d",
        "\u201e",
        "\u201f",
        "\u2e42",
        "\u2039",
        "\u203a",
        "\u00ab",
        "\u00bb",
        "\u300c",
        "\u300d",
        "\u300e",
        "\u300f",
        "\u2013",
        "\u2014",
        "\u2015",
    ]


class nwUnicode:
    """Supported unicode character constants and their HTML equivalents."""

    # Unicode Constants
    # =================

    # Quotation Marks
    U_QUOT = "\u0022"  # Quotation mark
    U_APOS = "\u0027"  # Apostrophe
    U_LAQUO = "\u00ab"  # Left-pointing double angle quotation mark
    U_RAQUO = "\u00bb"  # Right-pointing double angle quotation mark
    U_LSQUO = "\u2018"  # Left single quotation mark
    U_RSQUO = "\u2019"  # Right single quotation mark
    U_SBQUO = "\u201a"  # Single low-9 quotation mark
    U_SUQUO = "\u201b"  # Single high-reversed-9 quotation mark
    U_LDQUO = "\u201c"  # Left double quotation mark
    U_RDQUO = "\u201d"  # Right double quotation mark
    U_BDQUO = "\u201e"  # Double low-9 quotation mark
    U_UDQUO = "\u201f"  # Double high-reversed-9 quotation mark
    U_LSAQUO = "\u2039"  # Single left-pointing angle quotation mark
    U_RSAQUO = "\u203a"  # Single right-pointing angle quotation mark
    U_BDRQUO = "\u2e42"  # Double low-reversed-9 quotation mark
    U_LCQUO = "\u300c"  # Left corner bracket
    U_RCQUO = "\u300d"  # Right corner bracket
    U_LWCQUO = "\u300e"  # Left white corner bracket
    U_RWCQUO = "\u300f"  # Right white corner bracket

    # Punctuation
    U_FGDASH = "\u2012"  # Figure dash
    U_ENDASH = "\u2013"  # Short dash
    U_EMDASH = "\u2014"  # Long dash
    U_HBAR = "\u2015"  # Horizontal bar
    U_HELLIP = "\u2026"  # Ellipsis
    U_MAPOS = "\u02bc"  # Modifier letter single apostrophe
    U_PRIME = "\u2032"  # Prime
    U_DPRIME = "\u2033"  # Double prime

    # Spaces and Lines
    U_NBSP = "\u00a0"  # Non-breaking space
    U_THSP = "\u2009"  # Thin space
    U_THNBSP = "\u202f"  # Thin non-breaking space
    U_ENSP = "\u2002"  # Short (en) space
    U_EMSP = "\u2003"  # Long (em) space
    U_MMSP = "\u205f"  # Medium mathematical space
    U_LSEP = "\u2028"  # Line separator
    U_PSEP = "\u2029"  # Paragraph separator

    # Symbols
    U_CHECK = "\u2714"  # Heavy check mark
    U_CROSS = "\u2715"  # Heavy cross mark
    U_BULL = "\u2022"  # List bullet
    U_TRBULL = "\u2023"  # Triangle bullet
    U_HYBULL = "\u2043"  # Hyphen bullet
    U_FLOWER = "\u2055"  # Flower punctuation mark
    U_PERMIL = "\u2030"  # Per mille sign
    U_DEGREE = "\u00b0"  # Degree symbol
    U_MINUS = "\u2212"  # Minus sign
    U_TIMES = "\u00d7"  # Multiplication sign
    U_DIVIDE = "\u00f7"  # Division sign

    # Special
    U_UNKN = "\ufffd"  # Unknown character
    U_NAC1 = "\ufffe"  # Not a character
    U_NAC2 = "\uffff"  # Not a character

    # Placeholders
    U_LBREAK = "\u21b2"  # Downwards Arrow With Tip Leftwards

    # HTML Equivalents
    # ================

    # Quotes
    H_QUOT = "&quot;"
    H_APOS = "&#39;"
    H_LAQUO = "&laquo;"
    H_RAQUO = "&raquo;"
    H_LSQUO = "&lsquo;"
    H_RSQUO = "&rsquo;"
    H_SBQUO = "&sbquo;"
    H_SUQUO = "&#8219;"
    H_LDQUO = "&ldquo;"
    H_RDQUO = "&rdquo;"
    H_BDQUO = "&bdquo;"
    H_UDQUO = "&#8223;"
    H_LSAQUO = "&lsaquo;"
    H_RSAQUO = "&rsaquo;"
    H_BDRQUO = "&#11842;"
    H_LCQUO = "&#12300;"
    H_RCQUO = "&#12301;"
    H_LWCQUO = "&#12302;"
    H_RWCQUO = "&#12303;"

    # Punctuation
    H_FGDASH = "&#8210;"
    H_ENDASH = "&ndash;"
    H_EMDASH = "&mdash;"
    H_HBAR = "&#8213;"
    H_HELLIP = "&hellip;"
    H_MAPOS = "&#700;"
    H_PRIME = "&prime;"
    H_DPRIME = "&#8243;"

    # Spaces
    H_NBSP = "&nbsp;"
    H_THSP = "&thinsp;"
    H_THNBSP = "&#8239;"
    H_ENSP = "&ensp;"
    H_EMSP = "&emsp;"

    # Symbols
    H_CHECK = "&#10004;"
    H_CROSS = "&#10005;"
    H_BULL = "&bull;"
    H_TRBULL = "&#8227;"
    H_HYBULL = "&hybull;"
    H_FLOWER = "&#8277;"
    H_PERMIL = "&#8240;"
    H_DEGREE = "&deg;"
    H_MINUS = "&minus;"
    H_TIMES = "&times;"
    H_DIVIDE = "&divide;"

    # Unicode symbols expected to be used on the UI
    UI_SYMBOLS: Final[list[str]] = [
        U_QUOT,
        U_APOS,
        U_LAQUO,
        U_RAQUO,
        U_LSQUO,
        U_RSQUO,
        U_SBQUO,
        U_SUQUO,
        U_LDQUO,
        U_RDQUO,
        U_BDQUO,
        U_UDQUO,
        U_LSAQUO,
        U_RSAQUO,
        U_BDRQUO,
        U_LCQUO,
        U_RCQUO,
        U_LWCQUO,
        U_RWCQUO,
        U_FGDASH,
        U_ENDASH,
        U_EMDASH,
        U_HBAR,
        U_HELLIP,
        U_MAPOS,
        U_PRIME,
        U_DPRIME,
        U_NBSP,
        U_THSP,
        U_THNBSP,
        U_ENSP,
        U_EMSP,
        U_MMSP,
        U_CHECK,
        U_CROSS,
        U_BULL,
        U_TRBULL,
        U_HYBULL,
        U_FLOWER,
        U_PERMIL,
        U_DEGREE,
        U_MINUS,
        U_TIMES,
        U_DIVIDE,
        U_LBREAK,
    ]


class nwHtmlUnicode:
    """Unicode to HTML Map."""

    U_TO_H: Final[dict[str, str]] = {
        # Quotes
        nwUnicode.U_QUOT: nwUnicode.H_QUOT,
        nwUnicode.U_APOS: nwUnicode.H_APOS,
        nwUnicode.U_LAQUO: nwUnicode.H_LAQUO,
        nwUnicode.U_RAQUO: nwUnicode.H_RAQUO,
        nwUnicode.U_LSQUO: nwUnicode.H_LSQUO,
        nwUnicode.U_RSQUO: nwUnicode.H_RSQUO,
        nwUnicode.U_SBQUO: nwUnicode.H_SBQUO,
        nwUnicode.U_SUQUO: nwUnicode.H_SUQUO,
        nwUnicode.U_LDQUO: nwUnicode.H_LDQUO,
        nwUnicode.U_RDQUO: nwUnicode.H_RDQUO,
        nwUnicode.U_BDQUO: nwUnicode.H_BDQUO,
        nwUnicode.U_UDQUO: nwUnicode.H_UDQUO,
        nwUnicode.U_LSAQUO: nwUnicode.H_LSAQUO,
        nwUnicode.U_RSAQUO: nwUnicode.H_RSAQUO,
        nwUnicode.U_BDRQUO: nwUnicode.H_BDRQUO,
        nwUnicode.U_LCQUO: nwUnicode.H_LCQUO,
        nwUnicode.U_RCQUO: nwUnicode.H_RCQUO,
        nwUnicode.U_LWCQUO: nwUnicode.H_LWCQUO,
        nwUnicode.U_RWCQUO: nwUnicode.H_RWCQUO,
        # Punctuation
        nwUnicode.U_FGDASH: nwUnicode.H_FGDASH,
        nwUnicode.U_ENDASH: nwUnicode.H_ENDASH,
        nwUnicode.U_EMDASH: nwUnicode.H_EMDASH,
        nwUnicode.U_HBAR: nwUnicode.H_HBAR,
        nwUnicode.U_HELLIP: nwUnicode.H_HELLIP,
        nwUnicode.U_MAPOS: nwUnicode.H_MAPOS,
        nwUnicode.U_PRIME: nwUnicode.H_PRIME,
        nwUnicode.U_DPRIME: nwUnicode.H_DPRIME,
        # Spaces
        nwUnicode.U_NBSP: nwUnicode.H_NBSP,
        nwUnicode.U_THSP: nwUnicode.H_THSP,
        nwUnicode.U_THNBSP: nwUnicode.H_THNBSP,
        nwUnicode.U_ENSP: nwUnicode.H_ENSP,
        nwUnicode.U_EMSP: nwUnicode.H_EMSP,
        # Symbols
        nwUnicode.U_CHECK: nwUnicode.H_CHECK,
        nwUnicode.U_CROSS: nwUnicode.H_CROSS,
        nwUnicode.U_BULL: nwUnicode.H_BULL,
        nwUnicode.U_TRBULL: nwUnicode.H_TRBULL,
        nwUnicode.U_HYBULL: nwUnicode.H_HYBULL,
        nwUnicode.U_FLOWER: nwUnicode.H_FLOWER,
        nwUnicode.U_PERMIL: nwUnicode.H_PERMIL,
        nwUnicode.U_DEGREE: nwUnicode.H_DEGREE,
        nwUnicode.U_MINUS: nwUnicode.H_MINUS,
        nwUnicode.U_TIMES: nwUnicode.H_TIMES,
        nwUnicode.U_DIVIDE: nwUnicode.H_DIVIDE,
    }
