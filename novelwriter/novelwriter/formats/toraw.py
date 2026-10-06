"""
novelWriter - Raw NW Text Format
================================

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

import json
import logging

from time import time
from typing import TYPE_CHECKING

from novelwriter.common import formatTimeStamp
from novelwriter.formats.tokenizer import Tokenizer

if TYPE_CHECKING:
    from pathlib import Path

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)


class ToRaw(Tokenizer):
    """Core: Raw novelWriter Text Writer.

    A class that will collect the minimally altered original source text
    and write it to either a text or JSON file.
    """

    __slots__ = ("_keepRaw", "_noTokens")

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._keepRaw = True
        self._noTokens = True

    def doConvert(self) -> None:
        """No conversion to perform."""
        return

    def closeDocument(self) -> None:
        """Nothing to close."""
        return

    def saveDocument(self, path: Path) -> None:
        """Save the raw text to a plain text file."""
        if path.suffix.lower() == ".json":
            ts = time()
            data = {
                "meta": {
                    "projectName": self._project.data.name,
                    "novelAuthor": self._project.data.author,
                    "buildTime": int(ts),
                    "buildTimeStr": formatTimeStamp(ts),
                },
                "text": {
                    "nwd": [page.rstrip("\n").split("\n") for page in self._raw],
                },
            }
            with open(path, mode="w", encoding="utf-8") as fObj:
                json.dump(data, fObj, indent=2)

        else:
            with open(path, mode="w", encoding="utf-8") as outFile:
                for nwdPage in self._raw:
                    outFile.write(nwdPage)

        logger.info("Wrote file: %s", path)

    def replaceTabs(self, nSpaces: int = 8, spaceChar: str = " ") -> None:
        """Replace tabs with spaces."""
        spaces = spaceChar * nSpaces
        self._raw = [p.replace("\t", spaces) for p in self._raw]
