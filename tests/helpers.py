"""
novelWriter - Test Suite Helpers
================================

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

import difflib
import gc
import weakref
import xml.etree.ElementTree as ET

from collections.abc import Callable, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QWidget

from novelwriter import logger

if TYPE_CHECKING:
    from novelwriter.core.project import NWProject

XML_IGNORE = ("<novelWriterXML ", "<project ", "<dailyTarget ")
ODT_IGNORE = ("<meta:generator", "<meta:creation-date", "<dc:date", "<meta:editing")
EPUB_IGNORE = ('<meta property="dcterms:date">', '<meta property="dcterms:modified">', "<dc:date>")
NWD_IGNORE = ("createdDate =", "updatedDate =")
DOCX_IGNORE = ("<dcterms:created", "<dcterms:modified", "<ns0:Application")
MOCK_TIME = datetime(2019, 5, 10, 18, 52, 0).timestamp()


class C:
    # Import and status items from test project when random generator is mocked
    sNew = "s000000"
    sNote = "s000001"
    sDraft = "s000002"
    sFinished = "s000003"

    iNew = "i000004"
    iMinor = "i000005"
    iMajor = "i000006"
    iMain = "i000007"

    # Handles from test project when random generator is mocked
    hInvalid = "0000000000000"
    hNovelRoot = "0000000000008"
    hPlotRoot = "0000000000009"
    hTrashRoot = "0000000000010"
    hCharRoot = "000000000000a"
    hWorldRoot = "000000000000b"
    hTitlePage = "000000000000c"
    hChapterDir = "000000000000d"
    hChapterDoc = "000000000000e"
    hSceneDoc = "000000000000f"


def cmpFiles(
    fromFile: Path,
    toFile: Path,
    ignLines: Sequence[int] | None = None,
    ignStart: Sequence[str] | None = None,
) -> bool:
    """Compare two files, with optional line ignore by line number, or
    by matching the start of a line, ignoring leading whitespace.
    """
    ignLines = ignLines or []
    ignStart = tuple(ignStart or [])

    def loadLines(path: Path) -> list[str] | None:
        """Load a file and return its lines, stripping ignored lines."""
        try:
            lines = path.read_text(encoding="utf-8").strip().splitlines()
        except Exception as exc:
            print(str(exc))
            return None
        return [
            line
            for num, line in enumerate(lines, start=1)
            if not (num in ignLines or line.lstrip().startswith(ignStart))
        ]

    def colourDiffLine(line: str) -> str:
        """Add bright ANSI colours to a line of a unified diff."""
        if line.startswith(("+++", "---")):
            return f"\033[1m{line}\033[0m"
        elif line.startswith("+"):
            return f"\033[92m{line}\033[0m"
        elif line.startswith("-"):
            return f"\033[91m{line}\033[0m"
        elif line.startswith("@@"):
            return f"\033[96m{line}\033[0m"
        return line

    fromText = loadLines(fromFile)
    toText = loadLines(toFile)
    if fromText is None or toText is None:
        return False

    if fromText == toText:
        return True

    diff = difflib.unified_diff(fromText, toText, fromfile=str(fromFile), tofile=str(toFile), lineterm="")
    print("\n".join(colourDiffLine(line) for line in diff))

    return False


def xmlToText(xElem):
    """Get the text content of an XML element."""
    text = ET.tostring(xElem, encoding="utf-8", xml_declaration=False).decode()
    bits = text.partition(">")
    node = bits[0].partition(" ")
    rest = " ".join(x for x in node[2].split() if not x.startswith("xmlns")).replace("/", " /")
    return f"{node[0]}{rest}{bits[1]}{bits[2]}"


def readFile(file: Path):
    """Return the content of a file as a string."""
    return file.read_text(encoding="utf-8")


def writeFile(file: Path, data: str):
    """Write the contents of a string to a file."""
    file.write_text(data, encoding="utf-8")


def clearLogHandlers():
    """Clear all log handlers."""
    for handler in logger.handlers:
        logger.removeHandler(handler)


def buildTestProject(project: NWProject, path: Path) -> None:
    """Build a standard test project in path using the given project
    object.
    """
    from novelwriter.enum import nwItemClass

    project.storage.createNewProject(path)
    project.setDefaultStatusImport()

    project.data.setUuid("d0f3fe10-c6e6-4310-8bfd-181eb4224eed")
    project.data.setName("New Project")
    project.data.setAuthor("Jane Doe")

    # Creating a minimal project with a few root folders and a
    # single chapter folder with a single file.
    nrHandle = project.newRoot(nwItemClass.NOVEL)
    project.newRoot(nwItemClass.PLOT)
    project.newRoot(nwItemClass.CHARACTER)
    project.newRoot(nwItemClass.WORLD)

    tdHandle = project.newFile("Title Page", nrHandle)
    cfHandle = project.newFolder("New Folder", nrHandle) or ""
    cdHandle = project.newFile("New Chapter", cfHandle)
    sdHandle = project.newFile("New Scene", cfHandle)

    aDoc = project.storage.getDocument(tdHandle)
    aDoc.writeDocument("#! New Novel\n\n>> By Jane Doe <<\n")
    project.index.reIndexHandle(tdHandle)

    aDoc = project.storage.getDocument(cdHandle)
    aDoc.writeDocument("## {0}\n\n".format(project.tr("New Chapter")))
    project.index.reIndexHandle(cdHandle)

    aDoc = project.storage.getDocument(sdHandle)
    aDoc.writeDocument("### {0}\n\n".format(project.tr("New Scene")))
    project.index.reIndexHandle(sdHandle)

    project.session.startSession()
    project.setProjectChanged(True)
    project.saveProject()
    project._valid = True
    project._tree._ready = True


def checkDialogFreedOnClose(qtbot, factory: Callable[[], QDialog]) -> None:
    """Check that a dialog is freed by reference count alone when it is
    closed. This guards against PyQt6 reference loops where a closure
    connected to a signal captures the dialog that owns the sender, in
    which case the dialog lingers until the cyclic garbage collector
    runs. The dialog must be created by the factory so that the check
    holds the only reference to it.
    """
    dialog = factory()
    dialog.show()
    qtbot.wait(20)
    ref = weakref.ref(dialog)
    gc.disable()
    try:
        dialog.close()
        qtbot.wait(20)
        del dialog
        assert ref() is None, "Dialog was not freed by reference count on close"
    finally:
        gc.enable()


def checkWidgetFreedOnRelease(factory: Callable[[], QWidget]) -> None:
    """Check that a transient widget, like a context menu, is freed by
    reference count alone when its parent is cleared and the last
    reference is dropped. The widget must be created by the factory so
    that the check holds the only reference to it.
    """
    widget = factory()
    ref = weakref.ref(widget)
    gc.disable()
    try:
        widget.setParent(None)  # type: ignore
        del widget
        assert ref() is None, "Widget was not freed by reference count on release"
    finally:
        gc.enable()


class SimpleDialog(QDialog):
    def __init__(self, widget: QWidget | None = None) -> None:
        super().__init__()
        self._widget = widget
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        self.setLayout(layout)
        if widget:
            layout.addWidget(widget)

    @property
    def widget(self) -> QWidget | None:
        return self._widget

    def addWidget(self, widget: QWidget) -> None:
        self._widget = widget
        layout = self.layout()
        assert layout is not None
        layout.addWidget(widget)
