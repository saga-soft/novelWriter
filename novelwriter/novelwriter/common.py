"""
novelWriter - Common Functions
==============================

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

import json
import logging
import unicodedata
import uuid
import weakref
import xml.etree.ElementTree as ET

from datetime import date, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, TypeGuard, TypeVar
from urllib.parse import urljoin
from urllib.request import pathname2url

from PyQt6.QtCore import QCoreApplication, QLocale, QMimeData, QUrl
from PyQt6.QtGui import QAction, QDesktopServices, QFont, QFontDatabase, QFontInfo, QIcon
from PyQt6.QtWidgets import QMenu, QMenuBar, QWidget

from novelwriter.constants import nwConst, nwLabels, nwQuotes, nwUnicode, trConst
from novelwriter.enum import nwItemClass, nwItemLayout, nwItemType
from novelwriter.error import logException

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from types import MethodType

logger = logging.getLogger(__name__)

_Type = TypeVar("_Type")


##
#  Checker Functions
##


def checkStringNone(value: Any, default: str | None) -> str | None:
    """Check if a variable is a string or a None."""
    if value is None or value == "None":
        return None
    if isinstance(value, str):
        return str(value)
    return default


def checkString(value: Any, default: str) -> str:
    """Check if a variable is a string."""
    if isinstance(value, str):
        return str(value)
    return default


def checkInt(value: Any, default: int) -> int:
    """Check if a variable is an integer."""
    try:
        return int(value)
    except Exception:
        return default


def checkFloat(value: Any, default: float) -> float:
    """Check if a variable is a float."""
    try:
        return float(value)
    except Exception:
        return default


def checkBool(value: Any, default: bool) -> bool:
    """Check if a variable is a boolean."""
    if isinstance(value, bool):
        return value
    elif isinstance(value, str):
        check = value.lower()
        if check in ("true", "yes", "on"):
            return True
        elif check in ("false", "no", "off"):
            return False
        else:
            return default
    elif isinstance(value, int):
        if value == 1:
            return True
        elif value == 0:
            return False
        else:
            return default
    return default


def checkUuid(value: Any, default: str) -> str:
    """Try to process a value as an UUID, or return a default."""
    try:
        return str(uuid.UUID(value))
    except Exception:
        return default


def checkPath(value: Any, default: Path) -> Path:
    """Check if a value is a valid path."""
    if isinstance(value, Path):
        return value
    elif isinstance(value, str) and value.strip():
        return Path(value)
    return default


def checkDateNone(value: Any, default: date | None) -> date | None:
    """Check if a value is a valid date."""
    if isinstance(value, date):
        return value
    elif isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value)
        except Exception:
            return default
    return default


##
#  Validator Functions
##


def isHandle(value: Any) -> TypeGuard[str]:
    """Check if a string is a valid novelWriter handle.
    Note: This is case sensitive. Must be lower case.
    """
    if not isinstance(value, str):
        return False
    if len(value) != 13:
        return False
    return all(c in "0123456789abcdef" for c in value)


def isTitleTag(value: Any) -> TypeGuard[str]:
    """Check if a string is a valid title tag string."""
    if not isinstance(value, str):
        return False
    if len(value) != 5:
        return False
    if not value.startswith("T"):
        return False
    return all(c in "0123456789" for c in value[1:])


def isItemClass(value: Any) -> TypeGuard[str]:
    """Check if a string is a valid nwItemClass identifier."""
    return isinstance(value, str) and value in nwItemClass.__members__


def isItemType(value: Any) -> TypeGuard[str]:
    """Check if a string is a valid nwItemType identifier."""
    return isinstance(value, str) and value in nwItemType.__members__


def isItemLayout(value: Any) -> TypeGuard[str]:
    """Check if a string is a valid nwItemLayout identifier."""
    return isinstance(value, str) and value in nwItemLayout.__members__


def isListInstance(data: Any, check: type[_Type]) -> TypeGuard[list[_Type]]:
    """Check that all items of a list is of a given type."""
    return isinstance(data, list) and all(isinstance(item, check) for item in data)


def hexToInt(value: Any, default: int = 0) -> int:
    """Convert a hex string to an integer."""
    if isinstance(value, str):
        try:
            return int(value, 16)
        except Exception:
            return default
    return default


def minmax(value: int, minVal: int, maxVal: int) -> int:
    """Check that an value is between min and max value (inclusive)."""
    return min(maxVal, max(minVal, value))


def checkIntTuple(value: int, valid: tuple | list | set, default: int) -> int:
    """Check that an int is an element of a tuple. If it isn't, return
    the default value.
    """
    if isinstance(value, int) and value in valid:
        return value
    return default


def firstFloat(*args: Any) -> float:
    """Return the first value that is a float."""
    for arg in args:
        if isinstance(arg, float):
            return arg
    return 0.0


##
#  Formatting Functions
##


def formatInt(value: int) -> str:
    """Format an integer with k, M, G etc."""
    if not isinstance(value, int):
        return "ERR"

    fVal = float(value)
    if fVal > 1000.0:
        for pF in ["k", "M", "G", "T", "P", "E"]:
            fVal /= 1000.0
            if fVal < 1000.0:
                if fVal < 10.0:
                    return f"{fVal:4.2f}{nwUnicode.U_THSP}{pF}"
                elif fVal < 100.0:
                    return f"{fVal:4.1f}{nwUnicode.U_THSP}{pF}"
                else:
                    return f"{fVal:3.0f}{nwUnicode.U_THSP}{pF}"

    return str(value)


def formatPercent(value: float | int, *, divisor: float | int | None = None, prec: int = 1) -> str:
    """Format a number and optionally a divisor as a percentage."""
    if not isinstance(value, (float, int)):
        return "ERR"
    if isinstance(divisor, (float, int)) and divisor != 0:
        value = value / divisor
    fmt = f"{{0:.{prec}f}}\u202f%"
    return fmt.format(value * 100.0)


def formatTimeStamp(value: float, fileSafe: bool = False, fmt: str | None = None) -> str:
    """Take a number (on the format returned by time.time()) and convert
    it to a timestamp string.
    """
    try:
        result = datetime.fromtimestamp(value).strftime(nwConst.FMT_TSTAMP if fmt is None else fmt)
        return result.replace(":", ".") if fileSafe else result
    except Exception:
        return "ERROR"


def formatTime(t: int) -> str:
    """Format a time in seconds in HH:MM:SS format or d-HH:MM:SS format
    if a full day or longer.
    """
    if isinstance(t, int):
        if t >= 86400:
            return f"{t // 86400:d}-{t % 86400 // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"
        else:
            return f"{t // 3600:02d}:{t % 3600 // 60:02d}:{t % 60:02d}"
    return "ERROR"


def formatVersion(value: str) -> str:
    """Format a version number into a more human readable form."""
    major, _, version = value.partition(".")
    prefix = "20" if checkInt(major, 0) >= 20 else ""
    if "." in version:
        version = version.replace(".", " Patch ")
    elif "a" in version:
        version = version.replace("a", " Alpha ")
    elif "b" in version:
        version = version.replace("b", " Beta ")
    elif "rc" in version:
        version = version.replace("rc", " RC ")
    return f"{prefix}{major}.{version}" if major and version else ""


def formatFileFilter(extensions: list[str | tuple[str, str]]) -> str:
    """Format a list of extensions, or extension + label pairs into a
    QFileDialog extensions filter.
    """
    result = []
    for ext in extensions:
        if isinstance(ext, str):
            result.append(f"{trConst(nwLabels.FILE_FILTERS.get(ext, 'ERR'))} ({ext})")
        elif isinstance(ext, tuple) and len(ext) == 2:
            result.append(f"{ext[0]} ({ext[1]})")
    return ";;".join(result)


def formatLink(link: str, text: str = "") -> str:
    """Format a HTML link for use in labels."""
    return f"<a href='{link}'>{text or link}</a>"


##
#  String Functions
##


def _stripUnsafe(text: str) -> str:
    """Drop non-whitespace control characters and lone surrogates from
    a string.
    """
    return "".join(c for c in str(text) if c.isspace() or unicodedata.category(c) not in ("Cc", "Cs"))


def simplified(text: str) -> str:
    """Take a string and strip leading and trailing whitespaces, and
    replace all occurrences of (multiple) whitespaces with a 0x20
    space.
    """
    return " ".join(_stripUnsafe(text).split())


def compact(text: str) -> str:
    """Compact a string by removing spaces."""
    return "".join(_stripUnsafe(text).split())


def uniqueCompact(text: str) -> str:
    """Return a unique, compact and sorted string."""
    return "".join(sorted(set(compact(text))))


def joinLines(value: str | list[str], sep: str = "") -> str:
    """Join a list of strings with a separator."""
    if isinstance(value, list):
        return sep.join(str(x) for x in value)
    return str(value)


def appendIfSet(data: list[_Type], value: _Type) -> None:
    """Append value to list if value is set (truthy)."""
    if value:
        data.append(value)


def processDialogSymbols(symbols: str) -> str:
    """Process dialogue line symbols."""
    result = ""
    for c in uniqueCompact(symbols):
        if c in nwQuotes.ALLOWED:
            result += c
    return result


def processLangCode(code: str) -> str:
    """Validate a language code."""
    code = code.strip()
    return QLocale(code).name().replace("_", "-") if code else ""


def languageName(code: str) -> str:
    """Return the local name of a language."""
    return QLocale(code).nativeLanguageName().title()


def elide(text: str, length: int) -> str:
    """Elide a piece of text to a maximum length."""
    if len(text) > (cut := max(4, length)):
        return f"{text[: cut - 4].rstrip()} ..."
    return text


def yesNo(value: int | bool | None) -> Literal["yes", "no"]:
    """Convert a boolean evaluated variable to a yes or no."""
    return "yes" if value else "no"


def transferCase(source: str, target: str) -> str:
    """Transfers the case of the source word to the target word. This
    will consider all upper or lower, and first char capitalisation.
    """
    result = target

    if not isinstance(source, str) or not isinstance(target, str):
        return result
    if len(target) < 1 or len(source) < 1:
        return result

    if source.istitle():
        result = target.title()

    if source.isupper():
        result = target.upper()
    elif source.islower():
        result = target.lower()

    return result


def fuzzyTime(seconds: int) -> str:
    """Convert a time difference in seconds into a fuzzy time string."""
    if seconds < 0:
        return QCoreApplication.translate("Common", "in the future")
    elif seconds < 30:
        return QCoreApplication.translate("Common", "just now")
    elif seconds < 90:
        return QCoreApplication.translate("Common", "a minute ago")
    elif seconds < 3300:  # 55 minutes
        return QCoreApplication.translate("Common", "{0} minutes ago").format(round(seconds / 60))
    elif seconds < 5400:  # 90 minutes
        return QCoreApplication.translate("Common", "an hour ago")
    elif seconds < 84600:  # 23.5 hours
        return QCoreApplication.translate("Common", "{0} hours ago").format(round(seconds / 3600))
    elif seconds < 129600:  # 1.5 days
        return QCoreApplication.translate("Common", "a day ago")
    elif seconds < 561600:  # 6.5 days
        return QCoreApplication.translate("Common", "{0} days ago").format(round(seconds / 86400))
    elif seconds < 907200:  # 10.5 days
        return QCoreApplication.translate("Common", "a week ago")
    elif seconds < 2419200:  # 28 days
        return QCoreApplication.translate("Common", "{0} weeks ago").format(round(seconds / 604800))
    elif seconds < 3888000:  # 45 days
        return QCoreApplication.translate("Common", "a month ago")
    elif seconds < 29808000:  # 345 days
        return QCoreApplication.translate("Common", "{0} months ago").format(round(seconds / 2592000))
    elif seconds < 47336400:  # 1.5 years
        return QCoreApplication.translate("Common", "a year ago")
    else:
        return QCoreApplication.translate("Common", "{0} years ago").format(round(seconds / 31557600))


def numberToRoman(value: int, toLower: bool = False) -> str:
    """Convert an integer to a Roman number."""
    if not isinstance(value, int):
        return "NAN"
    if value < 1 or value > 4999:
        return "OOR"

    lookup = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ]

    roman = ""
    for divisor, symbol in lookup:
        n = value // divisor
        roman += n * symbol
        value -= n * divisor
        if value <= 0:
            break
    else:  # pragma: no cover
        pass

    return roman.lower() if toLower else roman


##
#  Safe I/O Wrappers
##


def safeIterDir(path: Path, *, alert: bool = False) -> Generator[Path, None, None]:
    """Call Path.iterdir() with exception handling."""
    try:
        yield from path.iterdir()
    except Exception as exc:
        logException()
        if alert:
            from novelwriter import SHARED

            SHARED.newStatusMessage(exc, "warning")


def safeExists(path: Path, *, alert: bool = False) -> bool:
    """Call Path.exists() with exception handling."""
    try:
        return path.exists()
    except Exception as exc:
        logException()
        if alert:
            from novelwriter import SHARED

            SHARED.newStatusMessage(exc, "warning")
        return False


def safeIsFile(path: Path, *, alert: bool = False) -> bool:
    """Call Path.is_file() with exception handling."""
    try:
        return path.is_file()
    except Exception as exc:
        logException()
        if alert:
            from novelwriter import SHARED

            SHARED.newStatusMessage(exc, "warning")
        return False


def safeIsDir(path: Path, *, alert: bool = False) -> bool:
    """Call Path.is_dir() with exception handling."""
    try:
        return path.is_dir()
    except Exception as exc:
        logException()
        if alert:
            from novelwriter import SHARED

            SHARED.newStatusMessage(exc, "warning")
        return False


##
#  Qt Helpers
##


def describeFont(font: QFont) -> str:
    """Describe a font in a way that can be displayed on the GUI."""
    if isinstance(font, QFont):
        info = QFontInfo(font)
        family = info.family()
        styles = [v for v in info.styleName().split() if v not in family]
        return " ".join([f"{info.pointSize()} pt", family, *styles])
    return "Error"


def fontMatcher(font: QFont) -> QFont:
    """Make sure the font is the correct family, if possible. This
    ensures that Qt doesn't re-use another font under the hood. The
    default Qt font matching algorithm doesn't handle well changing
    application fonts at runtime.
    """
    font.setStyleName(None)  # Make sure no font style name is set from config, see #2502
    info = QFontInfo(font)
    if (famRequest := font.family()) != (famActual := info.family()):
        logger.warning("Font mismatch: Requested '%s', but got '%s'", famRequest, famActual)
        if famRequest in QFontDatabase.families():
            styleRequest, sizeRequest = font.styleName(), font.pointSize()
            logger.info("Lookup: %s, %s, %d pt", famRequest, styleRequest, sizeRequest)
            temp = QFontDatabase.font(famRequest, styleRequest, sizeRequest)
            temp.setPointSize(sizeRequest)  # Make sure it isn't changed
            famFound, styleFound, sizeFound = temp.family(), temp.styleName(), temp.pointSize()
            if famFound == famRequest:
                logger.info("Found: %s, %s, %d pt", famFound, styleFound, sizeFound)
                return temp
        logger.warning("Could not find a font match in the font database")
        logger.warning("If you just changed font, you may need to restart the application")
    return font


def qtLambda(func: Callable, *args: Any, **kwargs: Any) -> Callable:
    """A replacement for Python lambdas that works for Qt slots."""  # noqa: D401

    def wrapper(*a_: Any) -> None:
        func(*args, **kwargs)

    return wrapper


def qtWeakLambda(method: MethodType, *args: Any, **kwargs: Any) -> Callable:
    """A qtLambda that only holds a weak reference to the bound method.
    Use this instead of qtLambda when the slot is a method of the object
    that also owns the signal, as the strong reference in qtLambda would
    otherwise keep the object alive until the cyclic garbage collector
    runs.
    """  # noqa: D401
    ref = weakref.WeakMethod(method)

    def wrapper(*a_: Any) -> None:
        if func := ref():
            func(*args, **kwargs)

    return wrapper


def qtAddAction(parent: QWidget, label: str, *, icon: QIcon | None = None, data: Any | None = None) -> QAction:
    """Add action to a widget and always return the action."""
    action = QAction(label, parent)
    if icon is not None:
        action.setIcon(icon)
    if data is not None:
        action.setData(data)
    parent.addAction(action)
    return action


def qtAddMenu(parent: QMenuBar | QMenu, label: str) -> QMenu:
    """Add a menu to a menu and always return the menu."""
    menu = QMenu(label, parent)
    parent.addMenu(menu)
    return menu


def encodeMimeHandles(mimeData: QMimeData, handles: list[str]) -> None:
    """Encode handles into a mime data object."""
    mimeData.setData(nwConst.MIME_HANDLE, b"|".join(h.encode() for h in handles))


def decodeMimeHandles(mimeData: QMimeData) -> list[str]:
    """Decode and split a mime data object with handles."""
    return mimeData.data(nwConst.MIME_HANDLE).data().decode().split("|")


def utf16CharMap(text: str) -> list[int]:
    """Compute mapping from Python string index to QString index.
    Python strings are always one character per position in either
    ASCII, UCS-2 or UCS-4. QStrings are in UTF-16, so wide characters
    use 2 indices, and thus create an offset.
    """
    utf16Map = list(range(len(text) + 1))
    offset = 0
    for i, c in enumerate(text, 1):
        if ord(c) > 0xFFFF:
            offset += 1
        utf16Map[i] = i + offset
    return utf16Map


##
#  Encoder Functions
##


def jsonEncode(data: dict | list | tuple, n: int = 0, nmax: int = 0) -> str:
    """Encode a dictionary, list or tuple as a json object or array, and
    indent from level n up to a max level nmax if nmax is larger than 0.
    """
    if not isinstance(data, dict | list | tuple):
        return "[]"

    buffer = []
    indent = ""

    for chunk in json.JSONEncoder().iterencode(data):
        if chunk == "":  # pragma: no cover
            # Just a precaution
            continue

        first = chunk[0]
        if chunk in ("{}", "[]"):
            buffer.append(chunk)

        elif first in ("{", "["):
            n += 1
            indent = "\n" + "  " * n
            if n > nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(chunk[0] + indent + chunk[1:])

        elif first in ("}", "]"):
            n -= 1
            indent = "\n" + "  " * n
            if n >= nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(indent + chunk)

        elif first == ",":
            if n > nmax > 0:
                buffer.append(chunk)
            else:
                buffer.append(chunk[0] + indent + chunk[1:].lstrip())

        else:
            buffer.append(chunk)

    return "".join(buffer)


def jsonCombine(data: dict[str, str]) -> str:
    """Combine multiple already packed JSON strings."""
    payload = ",\n".join(f'  "{k}": {v}' for k, v in data.items())
    return f"{{\n{payload}\n}}\n"


##
#  XML Helpers
##


def xmlIndent(xml: ET.Element | ET.ElementTree) -> None:
    """A modified version of the XML indent function in the standard
    library. It behaves more closely to how the one from lxml does.
    """  # noqa: D401
    tree = xml.getroot() if isinstance(xml, ET.ElementTree) else xml
    if not isinstance(tree, ET.Element):
        return

    indentations = ["\n"]

    def indentChildren(elem: ET.Element, level: int) -> None:
        chLevel = level + 1
        try:
            chIndent = indentations[chLevel]
        except IndexError:
            chIndent = indentations[level] + "  "
            indentations.append(chIndent)

        if elem.text is None:
            elem.text = chIndent

        last = None
        for child in elem:
            if len(child):
                indentChildren(child, chLevel)
            if child.tail is None:
                child.tail = chIndent
                last = child

        # Dedent the last child
        if last is not None:
            last.tail = indentations[level]

    if len(tree):
        indentChildren(tree, 0)
    tree.tail = "\n"

    return


def xmlElement(
    tag: str,
    text: str | int | float | bool | None = None,
    *,
    attrib: dict | None = None,
    tail: str | None = None,
) -> ET.Element:
    """A custom implementation of Element with more arguments."""  # noqa: D401
    xSub = ET.Element(tag, attrib=attrib or {})
    if text is not None:
        if isinstance(text, bool):
            xSub.text = str(text).lower()
        else:
            xSub.text = str(text)
    if tail is not None:
        xSub.tail = tail
    return xSub


def xmlSubElem(
    parent: ET.Element,
    tag: str,
    text: str | int | float | bool | None = None,
    *,
    attrib: dict | None = None,
    tail: str | None = None,
) -> ET.Element:
    """A custom implementation of SubElement with more arguments."""  # noqa: D401
    xSub = ET.SubElement(parent, tag, attrib=attrib or {})
    if text is not None:
        if isinstance(text, bool):
            xSub.text = str(text).lower()
        else:
            xSub.text = str(text)
    if tail is not None:
        xSub.tail = tail
    return xSub


##
#  File and File System Functions
##


def readTextFile(path: str | Path) -> str:
    """Read the content of a text file in a robust manner."""
    path = Path(path)
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        logger.error("Could not read file: %s", path)
        logException()
        return ""


def makeFileNameSafe(text: str) -> str:
    """Return a filename-safe string.

    See: https://unicode.org/reports/tr15/#Norm_Forms
    """
    text = unicodedata.normalize("NFKC", text).strip()
    return "".join(c for c in text if c.isprintable() and c not in r'\/:*?"<>|')


def getFileSize(path: Path) -> int:
    """Return the size of a file."""
    try:
        return path.stat().st_size
    except Exception:
        return -1


def openExternalPath(path: Path) -> bool:
    """Open a path by passing it to the desktop environment."""
    if Path(path).exists():
        QDesktopServices.openUrl(QUrl(urljoin("file:", pathname2url(str(path)))))
        return True
    return False
