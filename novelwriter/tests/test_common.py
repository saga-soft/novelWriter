"""
novelWriter - Common Functions Tests
====================================

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

import time
import weakref

from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QFontDatabase, QFontInfo

from novelwriter.common import (
    appendIfSet,
    checkBool,
    checkDateNone,
    checkFloat,
    checkInt,
    checkIntTuple,
    checkPath,
    checkString,
    checkStringNone,
    checkUuid,
    compact,
    decodeMimeHandles,
    describeFont,
    elide,
    encodeMimeHandles,
    firstFloat,
    fontMatcher,
    formatFileFilter,
    formatInt,
    formatLink,
    formatPercent,
    formatTime,
    formatTimeStamp,
    formatVersion,
    fuzzyTime,
    getFileSize,
    hexToInt,
    isHandle,
    isItemClass,
    isItemLayout,
    isItemType,
    isListInstance,
    isTitleTag,
    joinLines,
    jsonCombine,
    jsonEncode,
    languageName,
    makeFileNameSafe,
    minmax,
    numberToRoman,
    openExternalPath,
    processDialogSymbols,
    processLangCode,
    qtWeakLambda,
    readTextFile,
    safeExists,
    safeIsDir,
    safeIsFile,
    safeIterDir,
    simplified,
    transferCase,
    uniqueCompact,
    utf16CharMap,
    xmlElement,
    xmlIndent,
    xmlSubElem,
    yesNo,
)

from tests.helpers import writeFile
from tests.mocked import causeOSError


@pytest.mark.base
def testCommon_checkStringNone():
    """Test the checkStringNone function."""
    assert checkStringNone("Stuff", "NotNone") == "Stuff"
    assert checkStringNone("None", "NotNone") is None
    assert checkStringNone(None, "NotNone") is None
    assert checkStringNone(1, "NotNone") == "NotNone"
    assert checkStringNone(1.0, "NotNone") == "NotNone"
    assert checkStringNone(True, "NotNone") == "NotNone"


@pytest.mark.base
def testCommon_checkString():
    """Test the checkString function. Anything that is a string should
    be returned, otherwise it returns the default.
    """
    assert checkString("None", "default") == "None"
    assert checkString("Text", "default") == "Text"
    assert checkString(None, "default") == "default"
    assert checkString(1, "default") == "default"
    assert checkString(1.0, "default") == "default"
    assert checkString(True, "default") == "default"


@pytest.mark.base
def testCommon_checkInt():
    """Test the checkInt function. Anything that can be converted to an
    integer should be returned, otherwise it returns the default.
    """
    assert checkInt(1, 3) == 1
    assert checkInt(1.0, 3) == 1
    assert checkInt(True, 3) == 1
    assert checkInt(False, 3) == 0
    assert checkInt(None, 3) == 3
    assert checkInt("1", 3) == 1
    assert checkInt("1.0", 3) == 3


@pytest.mark.base
def testCommon_checkFloat():
    """Test the checkFloat function. Anything that can be converted to an
    integer should be returned, otherwise it returns the default.
    """
    assert checkFloat(1, 3.0) == 1.0
    assert checkFloat(1.0, 3.0) == 1.0
    assert checkFloat(True, 3.0) == 1.0
    assert checkFloat(False, 3.0) == 0.0
    assert checkFloat(None, 3.0) == 3.0
    assert checkFloat("1", 3.0) == 1.0
    assert checkFloat("1.0", 3.0) == 1.0


@pytest.mark.base
def testCommon_checkBool():
    """Test the checkBool function. Any bool, string version of Python
    bool, or integer 1 or 0, are returned as bool. Otherwise, the
    default is returned.
    """
    # Bools
    assert checkBool(True, False) is True
    assert checkBool(False, True) is False

    # Valid Strings
    assert checkBool("True", False) is True
    assert checkBool("False", True) is False
    assert checkBool("true", False) is True
    assert checkBool("false", True) is False
    assert checkBool("Yes", False) is True
    assert checkBool("No", True) is False
    assert checkBool("yes", False) is True
    assert checkBool("no", True) is False
    assert checkBool("On", False) is True
    assert checkBool("Off", True) is False
    assert checkBool("on", False) is True
    assert checkBool("off", True) is False

    # Invalid Strings
    assert checkBool("Foo", False) is False
    assert checkBool("Foo", True) is True
    assert checkBool("bar", False) is False
    assert checkBool("bar", True) is True

    # Valid Integers
    assert checkBool(0, True) is False
    assert checkBool(1, False) is True

    # Invalid Integers
    assert checkBool(2, True) is True
    assert checkBool(2, False) is False

    # Other Types
    assert checkBool(None, True) is True
    assert checkBool(None, False) is False
    assert checkBool(0.0, True) is True
    assert checkBool(1.0, False) is False
    assert checkBool(2.0, True) is True
    assert checkBool(2.0, False) is False


@pytest.mark.base
def testCommon_checkUuid():
    """Test the checkUuid function."""
    testUuid = "e2be99af-f9bf-4403-857a-c3d1ac25abea"
    assert checkUuid("", None) is None  # type: ignore
    assert checkUuid("e2be99af-f9bf-4403-857a-c3d1ac25abe", None) is None  # type: ignore
    assert checkUuid("e2be99af-f9bf-qq03-857a-c3d1ac25abea", None) is None  # type: ignore
    assert checkUuid("e2be99af-f9bf-4403-857a-c3d1ac25abeaa", None) is None  # type: ignore
    assert checkUuid(testUuid, None) == testUuid  # type: ignore


@pytest.mark.base
def testCommon_checkPath():
    """Test the checkPath function."""
    assert checkPath(Path("test"), None) == Path("test")  # type: ignore
    assert checkPath("test", None) == Path("test")  # type: ignore
    assert checkPath(None, None) is None  # type: ignore
    assert checkPath("", None) is None  # type: ignore
    assert checkPath("   ", None) is None  # type: ignore


@pytest.mark.base
def testCommon_checkDateNone():
    """Test the checkDateNone function."""
    fallback = date(2020, 1, 1)
    assert checkDateNone(date(2026, 7, 20), fallback) == date(2026, 7, 20)
    assert checkDateNone("2026-07-20", fallback) == date(2026, 7, 20)
    assert checkDateNone("not-a-date", fallback) == fallback
    assert checkDateNone("", fallback) == fallback
    assert checkDateNone("   ", fallback) == fallback
    assert checkDateNone(None, fallback) == fallback
    assert checkDateNone(1234, fallback) == fallback  # type: ignore


@pytest.mark.base
def testCommon_isHandle():
    """Test the isHandle function."""
    assert isHandle("47666c91c7ccf") is True
    assert isHandle("47666C91C7CCF") is False
    assert isHandle("h7666c91c7ccf") is False
    assert isHandle("None") is False
    assert isHandle(None) is False
    assert isHandle("STUFF") is False


@pytest.mark.base
def testCommon_isTitleTag():
    """Test the isTitleTag function."""
    assert isTitleTag("T1234") is True

    assert isTitleTag("t1234") is False
    assert isTitleTag("S1234") is False
    assert isTitleTag("T123A") is False
    assert isTitleTag("T12345") is False

    assert isTitleTag("None") is False
    assert isTitleTag(None) is False
    assert isTitleTag("STUFF") is False


@pytest.mark.base
def testCommon_isItemClass():
    """Test the isItemClass function."""
    assert isItemClass("NO_CLASS") is True
    assert isItemClass("NOVEL") is True
    assert isItemClass("PLOT") is True
    assert isItemClass("CHARACTER") is True
    assert isItemClass("WORLD") is True
    assert isItemClass("TIMELINE") is True
    assert isItemClass("OBJECT") is True
    assert isItemClass("ENTITY") is True
    assert isItemClass("CUSTOM") is True
    assert isItemClass("ARCHIVE") is True
    assert isItemClass("TRASH") is True

    # Invalid
    assert isItemClass("None") is False
    assert isItemClass(None) is False
    assert isItemClass("STUFF") is False


@pytest.mark.base
def testCommon_isItemType():
    """Test the isItemType function."""
    assert isItemType("NO_TYPE") is True
    assert isItemType("ROOT") is True
    assert isItemType("FOLDER") is True
    assert isItemType("FILE") is True

    # Deprecated Type
    assert isItemType("TRASH") is False

    # Invalid
    assert isItemType("None") is False
    assert isItemType(None) is False  # type: ignore
    assert isItemType("STUFF") is False


@pytest.mark.base
def testCommon_isItemLayout():
    """Test the isItemLayout function."""
    assert isItemLayout("NO_LAYOUT") is True
    assert isItemLayout("DOCUMENT") is True
    assert isItemLayout("NOTE") is True

    # Deprecated Layouts
    assert isItemLayout("TITLE") is False
    assert isItemLayout("PAGE") is False
    assert isItemLayout("BOOK") is False
    assert isItemLayout("PARTITION") is False
    assert isItemLayout("UNNUMBERED") is False
    assert isItemLayout("CHAPTER") is False
    assert isItemLayout("SCENE") is False

    # Invalid
    assert isItemLayout("None") is False
    assert isItemLayout(None) is False  # type: ignore
    assert isItemLayout("STUFF") is False


@pytest.mark.base
def testCommon_isListInstance():
    """Test the isListInstance function."""
    # String
    assert isListInstance("stuff", str) is False
    assert isListInstance(["stuff"], str) is True

    # Int
    assert isListInstance(1, int) is False
    assert isListInstance([1], int) is True

    # Mixed
    assert isListInstance([1], str) is False
    assert isListInstance(["stuff"], int) is False


@pytest.mark.base
def testCommon_hexToInt():
    """Test the hexToInt function."""
    assert hexToInt(1) == 0
    assert hexToInt("1") == 1
    assert hexToInt("0xff") == 255
    assert hexToInt("0xffff") == 65535
    assert hexToInt("0xffffq") == 0
    assert hexToInt("0xffffq", 12) == 12


@pytest.mark.base
def testCommon_minmax():
    """Test the minmax function."""
    for i in range(-5, 15):
        assert 0 <= minmax(i, 0, 10) <= 10


@pytest.mark.base
def testCommon_checkIntTuple():
    """Test the checkIntTuple function."""
    assert checkIntTuple(0, (0, 1, 2), 3) == 0
    assert checkIntTuple(5, (0, 1, 2), 3) == 3


@pytest.mark.base
def testCommon_firstFloat():
    """Test the firstFloat function."""
    assert firstFloat(None, 1.0) == 1.0
    assert firstFloat(1.0, None) == 1.0
    assert firstFloat(None, 1) == 0.0
    assert firstFloat(None, "1.0") == 0.0


@pytest.mark.base
def testCommon_formatTimeStamp():
    """Test the formatTimeStamp function."""
    tTime = time.mktime(time.gmtime(0))
    assert formatTimeStamp(tTime, False, "%Y") == "1970"
    assert formatTimeStamp(tTime, False) == "1970-01-01 00:00:00"
    assert formatTimeStamp(tTime, True) == "1970-01-01 00.00.00"
    assert formatTimeStamp(tTime, False, 123) == "ERROR"  # type: ignore


@pytest.mark.base
def testCommon_formatTime():
    """Test the formatTime function."""
    assert formatTime("1") == "ERROR"  # type: ignore
    assert formatTime(1.0) == "ERROR"  # type: ignore
    assert formatTime(1) == "00:00:01"
    assert formatTime(59) == "00:00:59"
    assert formatTime(60) == "00:01:00"
    assert formatTime(180) == "00:03:00"
    assert formatTime(194) == "00:03:14"
    assert formatTime(3540) == "00:59:00"
    assert formatTime(3599) == "00:59:59"
    assert formatTime(3600) == "01:00:00"
    assert formatTime(11640) == "03:14:00"
    assert formatTime(11655) == "03:14:15"
    assert formatTime(86399) == "23:59:59"
    assert formatTime(86400) == "1-00:00:00"
    assert formatTime(360000) == "4-04:00:00"


@pytest.mark.base
def testCommon_formatVersion():
    """Test the formatVersion function."""
    assert formatVersion("1.2") == "1.2"
    assert formatVersion("1.2.1") == "1.2 Patch 1"
    assert formatVersion("1.2a1") == "1.2 Alpha 1"
    assert formatVersion("1.2b2") == "1.2 Beta 2"
    assert formatVersion("1.2rc3") == "1.2 RC 3"
    assert formatVersion("26.1") == "2026.1"
    assert formatVersion("26.1.1") == "2026.1 Patch 1"
    assert formatVersion("26.1a1") == "2026.1 Alpha 1"
    assert formatVersion("26.1b2") == "2026.1 Beta 2"
    assert formatVersion("26.1rc3") == "2026.1 RC 3"
    assert formatVersion("12345") == ""


@pytest.mark.base
def testCommon_formatFileFilter():
    """Test the formatFileFilter function."""
    assert formatFileFilter(["*.txt"]) == "Text files (*.txt)"
    assert formatFileFilter(["*.txt", "*"]) == "Text files (*.txt);;All files (*)"
    assert formatFileFilter([("Stuff", "*.stuff"), "*.txt", "*"]) == (
        "Stuff (*.stuff);;Text files (*.txt);;All files (*)"
    )

    # Invalid entries are skipped
    assert formatFileFilter([123, ("Too", "Many", "Items"), "*.txt"]) == "Text files (*.txt)"  # type: ignore


@pytest.mark.base
def testCommon_formatLink():
    """Test the formatLink function."""
    assert formatLink("a") == "<a href='a'>a</a>"
    assert formatLink("a", "b") == "<a href='a'>b</a>"


@pytest.mark.base
def testCommon_simplified():
    """Test the simplified function."""
    assert simplified("Hello World") == "Hello World"
    assert simplified("  Hello    World   ") == "Hello World"
    assert simplified("\tHello\n\r\tWorld") == "Hello World"

    # Whitespace-like control characters are still treated as separators
    assert simplified("Hello\x1cWorld") == "Hello World"

    # Other control characters are dropped entirely, not just left as-is
    assert simplified("Hello\x00\x07\x1bWorld") == "HelloWorld"
    assert simplified("Hello \x7f World") == "Hello World"

    # Lone surrogates are dropped too, as they can't be written to UTF-8 files
    lone = b"abc\xff".decode("utf-8", "surrogateescape")
    assert simplified(f"Hello {lone} World") == "Hello abc World"


@pytest.mark.base
def testCommon_compact():
    """Test the compact function."""
    assert compact("! ! !") == "!!!"
    assert compact("1\t2\t3") == "123"
    assert compact("1\n2\n3") == "123"
    assert compact("1\r2\r3") == "123"
    assert compact("1\u00a02\u00a03") == "123"

    # Non-whitespace control characters and lone surrogates are dropped too
    assert compact("1\x00\x07\x1b2") == "12"
    lone = b"1\xff2".decode("utf-8", "surrogateescape")
    assert compact(lone) == "12"


@pytest.mark.base
def testCommon_uniqueCompact():
    """Test the uniqueCompact function."""
    assert uniqueCompact("! ! !") == "!"
    assert uniqueCompact("1\t2\t3") == "123"
    assert uniqueCompact("1\n2\n3") == "123"
    assert uniqueCompact("1\r2\r3") == "123"
    assert uniqueCompact("1\u00a02\u00a03") == "123"
    assert uniqueCompact("3 2 1") == "123"


@pytest.mark.base
def testCommon_joinLines():
    """Test the joinLines function."""
    assert joinLines("abc") == "abc"
    assert joinLines(["abc"]) == "abc"
    assert joinLines(["a", "b", "c"]) == "abc"
    assert joinLines("abc", "\n") == "abc"
    assert joinLines(["abc"], "\n") == "abc"
    assert joinLines(["a", "b", "c"], "\n") == "a\nb\nc"


@pytest.mark.base
def testCommon_appendIfSet():
    """Test the appendIfSet function."""
    data = []
    appendIfSet(data, "")
    assert data == []
    appendIfSet(data, "a")
    assert data == ["a"]
    appendIfSet(data, "b")
    assert data == ["a", "b"]


@pytest.mark.base
def testCommon_processDialogSymbols():
    """Test the processDialogSymbols function."""
    assert processDialogSymbols("abc") == ""
    assert processDialogSymbols("\u00ab\u00ab\u00bb\u00bb") == "\u00ab\u00bb"
    assert processDialogSymbols("-\u2013\u2014\u2015") == "\u2013\u2014\u2015"


@pytest.mark.base
def testCommon_processLangCode():
    """Test the processLangCode function."""
    assert processLangCode("") == ""
    assert processLangCode(" ") == ""
    assert processLangCode("en") == "en-US"
    assert processLangCode("en_gb") == "en-GB"


@pytest.mark.base
def testCommon_languageName():
    """Test the languageName function."""
    assert languageName("en-GB") == "British English"


@pytest.mark.base
def testCommon_elide():
    """Test the elide function."""
    assert elide("Hello World!", 12) == "Hello World!"
    assert elide("Hello World!", 11) == "Hello W ..."
    assert elide("Hello World!", 10) == "Hello ..."
    assert elide("Hello World!", 9) == "Hello ..."
    assert elide("Hello World!", 8) == "Hell ..."
    assert elide("Hello World!", 7) == "Hel ..."
    assert elide("Hello World!", 6) == "He ..."
    assert elide("Hello World!", 5) == "H ..."
    assert elide("Hello World!", 4) == " ..."
    assert elide("Hello World!", 3) == " ..."
    assert elide("Hello World!", 2) == " ..."
    assert elide("Hello World!", 1) == " ..."
    assert elide("Hello World!", 0) == " ..."


@pytest.mark.base
def testCommon_yesNo():
    """Test the yesNo function."""
    # Bool
    assert yesNo(True) == "yes"
    assert yesNo(False) == "no"

    # None
    assert yesNo(None) == "no"

    # String
    assert yesNo("foo") == "yes"  # type: ignore
    assert yesNo("") == "no"  # type: ignore

    # Integer
    assert yesNo(0) == "no"
    assert yesNo(1) == "yes"
    assert yesNo(2) == "yes"

    # Float
    assert yesNo(0.0) == "no"  # type: ignore
    assert yesNo(1.0) == "yes"  # type: ignore
    assert yesNo(2.0) == "yes"  # type: ignore


@pytest.mark.base
def testCommon_formatInt():
    """Test the formatInt function."""
    # Normal Cases
    assert formatInt(1) == "1"
    assert formatInt(12) == "12"
    assert formatInt(123) == "123"
    assert formatInt(1234) == "1.23\u2009k"
    assert formatInt(12345) == "12.3\u2009k"
    assert formatInt(123456) == "123\u2009k"
    assert formatInt(1234567) == "1.23\u2009M"
    assert formatInt(12345678) == "12.3\u2009M"
    assert formatInt(123456789) == "123\u2009M"
    assert formatInt(1234567890) == "1.23\u2009G"

    # Beyond the largest supported suffix, the raw value is returned
    assert formatInt(10**22) == str(10**22)

    # Exceptions
    assert formatInt(12.3) == "ERR"  # type: ignore
    assert formatInt(None) == "ERR"  # type: ignore
    assert formatInt("42") == "ERR"  # type: ignore


@pytest.mark.base
def testCommon_formatPercent():
    """Test the formatPercent function."""
    # Plain fraction, no divisor
    assert formatPercent(0.5) == "50.0\u202f%"
    assert formatPercent(1.0) == "100.0\u202f%"
    assert formatPercent(0) == "0.0\u202f%"

    # With a divisor
    assert formatPercent(50, divisor=100) == "50.0\u202f%"
    assert formatPercent(1, divisor=3) == "33.3\u202f%"

    # Divisor of zero is ignored, value is used as-is
    assert formatPercent(0, divisor=0) == "0.0\u202f%"

    # Precision
    assert formatPercent(1, divisor=3, prec=0) == "33\u202f%"
    assert formatPercent(1, divisor=3, prec=3) == "33.333\u202f%"

    # Exceptions
    assert formatPercent(None) == "ERR"  # type: ignore
    assert formatPercent("42") == "ERR"  # type: ignore
    assert formatPercent("42", divisor=3) == "ERR"  # type: ignore


@pytest.mark.base
def testCommon_transferCase():
    """Test the transferCase function."""
    assert transferCase(1, "TaRgEt") == "TaRgEt"  # type: ignore
    assert transferCase("source", 1) == 1  # type: ignore
    assert transferCase("", "TaRgEt") == "TaRgEt"
    assert transferCase("source", "") == ""
    assert transferCase("Source", "target") == "Target"
    assert transferCase("SOURCE", "target") == "TARGET"
    assert transferCase("source", "TARGET") == "target"


@pytest.mark.base
def testCommon_fuzzyTime():
    """Test the fuzzyTime function."""
    assert fuzzyTime(-1) == "in the future"
    assert fuzzyTime(0) == "just now"
    assert fuzzyTime(29) == "just now"
    assert fuzzyTime(30) == "a minute ago"
    assert fuzzyTime(89) == "a minute ago"
    assert fuzzyTime(90) == "2 minutes ago"
    assert fuzzyTime(149) == "2 minutes ago"
    assert fuzzyTime(151) == "3 minutes ago"
    assert fuzzyTime(3299) == "55 minutes ago"
    assert fuzzyTime(3300) == "an hour ago"
    assert fuzzyTime(5399) == "an hour ago"
    assert fuzzyTime(5400) == "2 hours ago"
    assert fuzzyTime(84599) == "23 hours ago"
    assert fuzzyTime(84600) == "a day ago"
    assert fuzzyTime(129599) == "a day ago"
    assert fuzzyTime(129600) == "2 days ago"
    assert fuzzyTime(561599) == "6 days ago"
    assert fuzzyTime(561600) == "a week ago"
    assert fuzzyTime(907199) == "a week ago"
    assert fuzzyTime(907200) == "2 weeks ago"
    assert fuzzyTime(2419199) == "4 weeks ago"
    assert fuzzyTime(2419200) == "a month ago"
    assert fuzzyTime(3887999) == "a month ago"
    assert fuzzyTime(3888000) == "2 months ago"
    assert fuzzyTime(29807999) == "11 months ago"
    assert fuzzyTime(29808000) == "a year ago"
    assert fuzzyTime(47336399) == "a year ago"
    assert fuzzyTime(47336400) == "2 years ago"


@pytest.mark.core
def testCommon_numberToRoman():
    """Test conversion of integers to Roman numbers."""
    assert numberToRoman(None, False) == "NAN"  # type: ignore
    assert numberToRoman(0, False) == "OOR"
    assert numberToRoman(1, False) == "I"
    assert numberToRoman(2, False) == "II"
    assert numberToRoman(3, False) == "III"
    assert numberToRoman(4, False) == "IV"
    assert numberToRoman(5, False) == "V"
    assert numberToRoman(6, False) == "VI"
    assert numberToRoman(7, False) == "VII"
    assert numberToRoman(8, False) == "VIII"
    assert numberToRoman(9, False) == "IX"
    assert numberToRoman(10, False) == "X"
    assert numberToRoman(14, False) == "XIV"
    assert numberToRoman(42, False) == "XLII"
    assert numberToRoman(99, False) == "XCIX"
    assert numberToRoman(142, False) == "CXLII"
    assert numberToRoman(542, False) == "DXLII"
    assert numberToRoman(999, False) == "CMXCIX"
    assert numberToRoman(2010, False) == "MMX"
    assert numberToRoman(999, True) == "cmxcix"


@pytest.mark.base
def testCommon_safeIterDir(fncPath: Path):
    """Test the safeIterDir function."""
    files = [
        fncPath / "file1.txt",
        fncPath / "file2.txt",
        fncPath / "file3.txt",
    ]
    for file in files:
        file.touch()

    assert sorted(safeIterDir(fncPath, alert=True)) == files
    assert list(safeIterDir(None, alert=True)) == []  # type: ignore
    assert list(safeIterDir(None)) == []  # type: ignore


@pytest.mark.base
def testCommon_safeExists(fncPath: Path):
    """Test the safeExists function."""
    file = fncPath / "file1.txt"
    file.touch()

    assert safeExists(file, alert=True) is True
    assert safeExists(None, alert=True) is False  # type: ignore
    assert safeExists(None) is False  # type: ignore


@pytest.mark.base
def testCommon_safeIsFile(fncPath: Path):
    """Test the safeIsFile function."""
    file = fncPath / "file1.txt"
    file.touch()

    assert safeIsFile(file, alert=True) is True
    assert safeIsFile(None, alert=True) is False  # type: ignore
    assert safeIsFile(None) is False  # type: ignore


@pytest.mark.base
def testCommon_safeIsDir(fncPath: Path):
    """Test the safeIsDir function."""
    folder = fncPath / "folder1"
    folder.mkdir()

    assert safeIsDir(folder, alert=True) is True
    assert safeIsDir(None, alert=True) is False  # type: ignore
    assert safeIsDir(None) is False  # type: ignore


@pytest.mark.base
def testCommon_describeFont():
    """Test the describeFont function."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    font.setPointSize(12)
    assert describeFont(font).startswith("12 pt")
    assert describeFont(None) == "Error"  # type: ignore


@pytest.mark.base
def testCommon_fontMatcher(monkeypatch):
    """Test the fontMatcher function."""
    # Nonsense font is just returned
    nonsense = QFont("nonesense", 10)
    assert fontMatcher(nonsense) is nonsense

    # Style is reset
    nonsense.setStyleName("blabla")
    assert nonsense.styleName() == "blabla"
    assert fontMatcher(nonsense).styleName() == ""

    # General font
    if len(QFontDatabase.families()) > 1:
        fontOne = QFont(QFontDatabase.families()[0])
        fontTwo = QFont(QFontDatabase.families()[1])
        check = QFont(fontOne)
        check.setFamily(fontTwo.family())
        with monkeypatch.context() as mp:
            mp.setattr(QFontInfo, "family", lambda *a: "nonesense")
            assert fontMatcher(check).family() == fontTwo.family()


@pytest.mark.base
def testCommon_encodeDecodeMimeHandles(monkeypatch):
    """Test the encodeMimeHandles and decodeMimeHandles functions."""
    handles = ["0123456789abc", "123456789abcd", "23456789abcde"]
    mimeData = QMimeData()
    encodeMimeHandles(mimeData, handles)
    assert decodeMimeHandles(mimeData) == handles


@pytest.mark.base
def testCommon_utf16CharMap(monkeypatch):
    """Test the utf16CharMap function."""
    assert utf16CharMap("abc") == [0, 1, 2, 3]
    assert utf16CharMap("a\u2014b\u2014c") == [0, 1, 2, 3, 4, 5]
    assert utf16CharMap("a\U0001f605b\U0001f605c") == [0, 1, 3, 4, 6, 7]


@pytest.mark.base
def testCommon_jsonEncode():
    """Test the jsonEncode function."""
    # Wrong type
    assert jsonEncode(None) == "[]"  # type: ignore

    # Correct types
    assert jsonEncode([1, 2]) == "[\n  1,\n  2\n]"
    assert jsonEncode((1, 2)) == "[\n  1,\n  2\n]"
    assert jsonEncode({1: 2}) == '{\n  "1": 2\n}'

    tstDict = {
        "null": None,
        "one": 1,
        "two": "2",
        "three": 3.0,
        "four": False,
        "five": (1, 2),
        "six": {"a": 1, "b": 2},
        "seven": [],
        "eight": {},
    }

    # Complex Structure
    assert jsonEncode(tstDict) == (
        "{\n"
        '  "null": null,\n'
        '  "one": 1,\n'
        '  "two": "2",\n'
        '  "three": 3.0,\n'
        '  "four": false,\n'
        '  "five": [\n'
        "    1,\n"
        "    2\n"
        "  ],\n"
        '  "six": {\n'
        '    "a": 1,\n'
        '    "b": 2\n'
        "  },\n"
        '  "seven": [],\n'
        '  "eight": {}\n'
        "}"
    )

    # Additional Indent
    assert jsonEncode(tstDict, n=2) == (
        "{\n"
        '      "null": null,\n'
        '      "one": 1,\n'
        '      "two": "2",\n'
        '      "three": 3.0,\n'
        '      "four": false,\n'
        '      "five": [\n'
        "        1,\n"
        "        2\n"
        "      ],\n"
        '      "six": {\n'
        '        "a": 1,\n'
        '        "b": 2\n'
        "      },\n"
        '      "seven": [],\n'
        '      "eight": {}\n'
        "    }"
    )

    # Max Indent
    assert jsonEncode(tstDict, n=0, nmax=1) == (
        "{\n"
        '  "null": null,\n'
        '  "one": 1,\n'
        '  "two": "2",\n'
        '  "three": 3.0,\n'
        '  "four": false,\n'
        '  "five": [1, 2],\n'
        '  "six": {"a": 1, "b": 2},\n'
        '  "seven": [],\n'
        '  "eight": {}\n'
        "}"
    )


@pytest.mark.base
def testCommon_jsonCombine():
    """Test the jsonCombine function."""
    assert jsonCombine({"a": "[1, 2]", "b": "[3, 4]"}) == ('{\n  "a": [1, 2],\n  "b": [3, 4]\n}\n')


@pytest.mark.base
def testCommon_xmlIndent():
    """Test the xmlIndent function."""
    xRoot = ET.fromstring("<xml><group><item>foo</item></group></xml>")
    xmlIndent(ET.ElementTree(xRoot))
    assert ET.tostring(xRoot) == (b"<xml>\n  <group>\n    <item>foo</item>\n  </group>\n</xml>\n")

    # If we send nonsense, nothing is done
    data = "foobar"
    xmlIndent(data)  # type: ignore
    assert data == "foobar"

    # An element with no children has no child indentation applied
    xEmpty = ET.fromstring("<xml />")
    xmlIndent(xEmpty)
    assert ET.tostring(xEmpty) == b"<xml />\n"


@pytest.mark.base
def testCommon_xmlElement():
    """Test the xmlElement function."""
    assert ET.tostring(xmlElement("node", None, attrib={"a": "b"})) == b'<node a="b" />'
    assert ET.tostring(xmlElement("node", "text", attrib={"a": "b"})) == b'<node a="b">text</node>'
    assert ET.tostring(xmlElement("node", "text", tail="foo", attrib={"a": "b"})) == b'<node a="b">text</node>foo'
    assert ET.tostring(xmlElement("node", 42, attrib={"a": "b"})) == b'<node a="b">42</node>'
    assert ET.tostring(xmlElement("node", 3.14, attrib={"a": "b"})) == b'<node a="b">3.14</node>'
    assert ET.tostring(xmlElement("node", True, attrib={"a": "b"})) == b'<node a="b">true</node>'


@pytest.mark.base
def testCommon_xmlSubElem():
    """Test the xmlSubElem function."""
    assert ET.tostring(xmlSubElem(ET.Element("r"), "node", None, attrib={"a": "b"})) == b'<node a="b" />'
    assert ET.tostring(xmlSubElem(ET.Element("r"), "node", "text", attrib={"a": "b"})) == b'<node a="b">text</node>'
    assert (
        ET.tostring(xmlSubElem(ET.Element("r"), "node", "text", tail="foo", attrib={"a": "b"}))
        == b'<node a="b">text</node>foo'
    )
    assert ET.tostring(xmlSubElem(ET.Element("r"), "node", 42, attrib={"a": "b"})) == b'<node a="b">42</node>'
    assert ET.tostring(xmlSubElem(ET.Element("r"), "node", 3.14, attrib={"a": "b"})) == b'<node a="b">3.14</node>'
    assert ET.tostring(xmlSubElem(ET.Element("r"), "node", True, attrib={"a": "b"})) == b'<node a="b">true</node>'


@pytest.mark.base
def testCommon_readTextFile(monkeypatch, fncPath, ipsumText):
    """Test the readTextFile function."""
    testText = "\n\n".join(ipsumText) + "\n"
    testFile = fncPath / "ipsum.txt"
    writeFile(testFile, testText)

    assert readTextFile(fncPath / "not_a_file.txt") == ""
    assert readTextFile(testFile) == testText

    with monkeypatch.context() as mp:
        mp.setattr("pathlib.Path.read_text", causeOSError)
        assert readTextFile(testFile) == ""


@pytest.mark.base
def testCommon_makeFileNameSafe():
    """Test the makeFileNameSafe function."""
    # Trim edges
    assert makeFileNameSafe(" Name ") == "Name"

    # Normalise Unicode
    assert makeFileNameSafe("Stuff œﬁ2⁵") == "Stuff œfi25"

    # No control characters
    assert makeFileNameSafe("One\tTwo") == "OneTwo"
    assert makeFileNameSafe("One\nTwo") == "OneTwo"
    assert makeFileNameSafe("One\rTwo") == "OneTwo"

    # Invalid special characters
    assert makeFileNameSafe("One\\Two") == "OneTwo"
    assert makeFileNameSafe("One/Two") == "OneTwo"
    assert makeFileNameSafe("One:Two") == "OneTwo"
    assert makeFileNameSafe("One*Two") == "OneTwo"
    assert makeFileNameSafe("One?Two") == "OneTwo"
    assert makeFileNameSafe('One"Two') == "OneTwo"
    assert makeFileNameSafe("One<Two") == "OneTwo"
    assert makeFileNameSafe("One>Two") == "OneTwo"
    assert makeFileNameSafe("One|Two") == "OneTwo"

    # Names that are valid
    assert makeFileNameSafe("One Two") == "One Two"
    assert makeFileNameSafe("One,Two") == "One,Two"
    assert makeFileNameSafe("One-Two") == "One-Two"
    assert makeFileNameSafe("One\u2013Two") == "One\u2013Two"
    assert makeFileNameSafe("One\u2014Two") == "One\u2014Two"
    assert makeFileNameSafe("Bob's Story") == "Bob's Story"

    # Unicode
    assert makeFileNameSafe("æøå") == "æøå"
    assert makeFileNameSafe("ßÜ") == "ßÜ"


@pytest.mark.base
def testCommon_getFileSize(fncPath):
    """Test the getFileSize function."""
    (fncPath / "one.txt").write_bytes(b"foobar")
    (fncPath / "two.txt").touch()

    assert getFileSize(fncPath / "nope.txt") == -1
    assert getFileSize(fncPath / "one.txt") == 6
    assert getFileSize(fncPath / "two.txt") == 0


@pytest.mark.base
def testCommon_openExternalPath(monkeypatch, tstPaths):
    """Test the openExternalPath function."""
    lastUrl = ""

    def mockOpenUrl(url: QUrl) -> None:
        nonlocal lastUrl
        lastUrl = url.toString()

    monkeypatch.setattr(QDesktopServices, "openUrl", mockOpenUrl)
    assert openExternalPath(Path("/foo/bar")) is False
    assert openExternalPath(tstPaths.tmpDir) is True
    assert lastUrl.startswith("file://")


@pytest.mark.base
def testCommon_qtWeakLambda():
    """Test the qtWeakLambda function."""

    class Counter:
        count = 0

        def add(self, step: int) -> None:
            self.count += step

    obj = Counter()
    wrapper = qtWeakLambda(obj.add, 2)

    # The wrapper calls the method, but does not keep the object alive
    wrapper()
    assert obj.count == 2

    # When the object is gone, the wrapper does nothing
    ref = weakref.ref(obj)
    del obj
    assert ref() is None
    wrapper()
