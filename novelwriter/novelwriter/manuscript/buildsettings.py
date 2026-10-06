"""
novelWriter - Build Settings
============================

This file is a part of novelWriter
Copyright (C) 2023 Veronica Berglyd Olsen and novelWriter contributors

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
import uuid

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QT_TRANSLATE_NOOP, QCoreApplication

from novelwriter import CONFIG
from novelwriter.common import checkUuid, isHandle, jsonEncode, safeExists, safeIsDir
from novelwriter.constants import nwFiles, nwHeadFmt, nwStyles
from novelwriter.core.project import NWProject
from novelwriter.enum import nwBuildFmt
from novelwriter.error import logException

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = logging.getLogger(__name__)

T_BuildValue = str | int | float | bool

# The Settings Template
# =====================
# Each entry contains a tuple on the form: (type, default)

# fmt: off
SETTINGS_TEMPLATE: dict[str, tuple[type, T_BuildValue]] = {
    "filter.includeNovel":     (bool, True),
    "filter.includeNotes":     (bool, False),
    "filter.includeInactive":  (bool, False),
    "headings.fmtPart":        (str, nwHeadFmt.TITLE),
    "headings.fmtChapter":     (str, nwHeadFmt.TITLE),
    "headings.fmtUnnumbered":  (str, nwHeadFmt.TITLE),
    "headings.fmtScene":       (str, "* * *"),
    "headings.fmtAltScene":    (str, ""),
    "headings.fmtSection":     (str, ""),
    "headings.hidePart":       (bool, False),
    "headings.hideChapter":    (bool, False),
    "headings.hideUnnumbered": (bool, False),
    "headings.hideScene":      (bool, False),
    "headings.hideAltScene":   (bool, False),
    "headings.hideSection":    (bool, True),
    "headings.centerTitle":    (bool, True),
    "headings.centerPart":     (bool, True),
    "headings.centerChapter":  (bool, False),
    "headings.centerScene":    (bool, False),
    "headings.breakTitle":     (bool, False),
    "headings.breakPart":      (bool, True),
    "headings.breakChapter":   (bool, True),
    "headings.breakScene":     (bool, False),
    "text.includeBodyText":    (bool, True),
    "text.includeSynopsis":    (bool, False),
    "text.includeComments":    (bool, False),
    "text.includeStory":       (bool, False),
    "text.includeNotes":       (bool, False),
    "text.includeKeywords":    (bool, False),
    "text.ignoredKeywords":    (str, ""),
    "text.addNoteHeadings":    (bool, True),
    "format.textFont":         (str, CONFIG.textFont.toString()),
    "format.lineHeight":       (float, 1.15),
    "format.justifyText":      (bool, False),
    "format.justifyOnBreak":   (bool, True),
    "format.stripUnicode":     (bool, False),
    "format.replaceTabs":      (bool, False),
    "format.keepBreaks":       (bool, True),
    "format.showDialogue":     (bool, False),
    "format.colorHeadings":    (bool, True),
    "format.boldHeadings":     (bool, True),
    "format.upperHeadings":    (bool, False),
    "format.firstLineIndent":  (bool, False),
    "format.firstIndentWidth": (float, 1.4),
    "format.indentFirstPar":   (bool, False),
    "format.titleSize":        (float, nwStyles.H_SIZES[0]),
    "format.h1Size":           (float, nwStyles.H_SIZES[1]),
    "format.h2Size":           (float, nwStyles.H_SIZES[2]),
    "format.h3Size":           (float, nwStyles.H_SIZES[3]),
    "format.h4Size":           (float, nwStyles.H_SIZES[4]),
    "format.titleMarginT":     (float, nwStyles.T_MARGIN["H0"][0]),
    "format.titleMarginB":     (float, nwStyles.T_MARGIN["H0"][1]),
    "format.h1MarginT":        (float, nwStyles.T_MARGIN["H1"][0]),
    "format.h1MarginB":        (float, nwStyles.T_MARGIN["H1"][1]),
    "format.h2MarginT":        (float, nwStyles.T_MARGIN["H2"][0]),
    "format.h2MarginB":        (float, nwStyles.T_MARGIN["H2"][1]),
    "format.h3MarginT":        (float, nwStyles.T_MARGIN["H3"][0]),
    "format.h3MarginB":        (float, nwStyles.T_MARGIN["H3"][1]),
    "format.h4MarginT":        (float, nwStyles.T_MARGIN["H4"][0]),
    "format.h4MarginB":        (float, nwStyles.T_MARGIN["H4"][1]),
    "format.textMarginT":      (float, nwStyles.T_MARGIN["TT"][0]),
    "format.textMarginB":      (float, nwStyles.T_MARGIN["TT"][1]),
    "format.sepMarginT":       (float, nwStyles.T_MARGIN["SP"][0]),
    "format.sepMarginB":       (float, nwStyles.T_MARGIN["SP"][1]),
    "format.lineForMargin":    (bool, False),
    "format.pageUnit":         (str, "cm"),
    "format.pageSize":         (str, "A4"),
    "format.pageWidth":        (float, 21.0),
    "format.pageHeight":       (float, 29.7),
    "format.topMargin":        (float, 2.0),
    "format.bottomMargin":     (float, 2.0),
    "format.leftMargin":       (float, 2.0),
    "format.rightMargin":      (float, 2.0),
    "doc.pageHeader":          (str, nwHeadFmt.DOC_AUTO),
    "doc.pageCountOffset":     (int, 0),
    "doc.metaLanguage":        (str, ""),
    "html.addStyles":          (bool, True),
    "html.preserveTabs":       (bool, False),
}

SETTINGS_LABELS = {
    "headings":                QT_TRANSLATE_NOOP("Builds", "Headings"),
    "headings.fmtPart":        QT_TRANSLATE_NOOP("Builds", "Partition format"),
    "headings.fmtChapter":     QT_TRANSLATE_NOOP("Builds", "Chapter format"),
    "headings.fmtUnnumbered":  QT_TRANSLATE_NOOP("Builds", "Unnumbered format"),
    "headings.fmtScene":       QT_TRANSLATE_NOOP("Builds", "Scene format"),
    "headings.fmtAltScene":    QT_TRANSLATE_NOOP("Builds", "Alt. Scene format"),
    "headings.fmtSection":     QT_TRANSLATE_NOOP("Builds", "Section format"),
    "headings.styleTitle":     QT_TRANSLATE_NOOP("Builds", "Title styling"),
    "headings.stylePart":      QT_TRANSLATE_NOOP("Builds", "Partition styling"),
    "headings.styleChapter":   QT_TRANSLATE_NOOP("Builds", "Chapter styling"),
    "headings.styleScene":     QT_TRANSLATE_NOOP("Builds", "Scene styling"),

    "text.grpContent":         QT_TRANSLATE_NOOP("Builds", "Text Content"),
    "text.includeBodyText":    QT_TRANSLATE_NOOP("Builds", "Include body text"),
    "text.includeSynopsis":    QT_TRANSLATE_NOOP("Builds", "Include synopsis"),
    "text.includeComments":    QT_TRANSLATE_NOOP("Builds", "Include comments"),
    "text.includeStory":       QT_TRANSLATE_NOOP("Builds", "Include story structure"),
    "text.includeNotes":       QT_TRANSLATE_NOOP("Builds", "Include manuscript notes"),
    "text.includeKeywords":    QT_TRANSLATE_NOOP("Builds", "Include tags and references"),
    "text.ignoredKeywords":    QT_TRANSLATE_NOOP("Builds", "Ignore these keys"),
    "text.addNoteHeadings":    QT_TRANSLATE_NOOP("Builds", "Add titles for note root folders"),

    "format.grpFormat":        QT_TRANSLATE_NOOP("Builds", "Text Format"),
    "format.textFont":         QT_TRANSLATE_NOOP("Builds", "Text font"),
    "format.lineHeight":       QT_TRANSLATE_NOOP("Builds", "Line height"),
    "format.justifyText":      QT_TRANSLATE_NOOP("Builds", "Justify text margins"),
    "format.justifyOnBreak":   QT_TRANSLATE_NOOP("Builds", "Justify text on manual line breaks"),
    "format.stripUnicode":     QT_TRANSLATE_NOOP("Builds", "Replace Unicode characters"),
    "format.replaceTabs":      QT_TRANSLATE_NOOP("Builds", "Replace tabs with spaces"),
    "format.keepBreaks":       QT_TRANSLATE_NOOP("Builds", "Preserve hard line breaks"),
    "format.showDialogue":     QT_TRANSLATE_NOOP("Builds", "Apply dialogue highlighting"),

    "format.grpHeadings":      QT_TRANSLATE_NOOP("Builds", "Heading Format"),
    "format.colorHeadings":    QT_TRANSLATE_NOOP("Builds", "Add colours to headings"),
    "format.boldHeadings":     QT_TRANSLATE_NOOP("Builds", "Bold headings"),
    "format.upperHeadings":    QT_TRANSLATE_NOOP("Builds", "Uppercase headings"),

    "format.grpParIndent":     QT_TRANSLATE_NOOP("Builds", "First Line Indent"),
    "format.firstLineIndent":  QT_TRANSLATE_NOOP("Builds", "Enable indent"),
    "format.firstIndentWidth": QT_TRANSLATE_NOOP("Builds", "Indent width"),
    "format.indentFirstPar":   QT_TRANSLATE_NOOP("Builds", "Indent first paragraph"),

    "format.grpMargins":       QT_TRANSLATE_NOOP("Builds", "Size & Margins"),
    "format.titleMargin":      QT_TRANSLATE_NOOP("Builds", "Title and Partition"),
    "format.h1Margin":         QT_TRANSLATE_NOOP("Builds", "Heading 1 and Chapter"),
    "format.h2Margin":         QT_TRANSLATE_NOOP("Builds", "Heading 2 and Scene"),
    "format.h3Margin":         QT_TRANSLATE_NOOP("Builds", "Heading 3 and Section"),
    "format.h4Margin":         QT_TRANSLATE_NOOP("Builds", "Heading 4"),
    "format.textMargin":       QT_TRANSLATE_NOOP("Builds", "Text paragraph"),
    "format.sepMargin":        QT_TRANSLATE_NOOP("Builds", "Scene separator"),
    "format.lineForMargin":    QT_TRANSLATE_NOOP("Builds", "Add empty lines instead of margins"),

    "format.grpPage":          QT_TRANSLATE_NOOP("Builds", "Page Layout"),
    "format.pageUnit":         QT_TRANSLATE_NOOP("Builds", "Unit"),
    "format.pageSize":         QT_TRANSLATE_NOOP("Builds", "Page size"),
    "format.pageMargins":      QT_TRANSLATE_NOOP("Builds", "Page margins"),

    "doc":                     QT_TRANSLATE_NOOP("Builds", "Document Style"),
    "doc.pageHeader":          QT_TRANSLATE_NOOP("Builds", "Page header"),
    "doc.pageCountOffset":     QT_TRANSLATE_NOOP("Builds", "Page counter offset"),
    "doc.metaLanguage":        QT_TRANSLATE_NOOP("Builds", "Override document language"),

    "html":                    QT_TRANSLATE_NOOP("Builds", "HTML Options"),
    "html.addStyles":          QT_TRANSLATE_NOOP("Builds", "Add CSS styles"),
    "html.preserveTabs":       QT_TRANSLATE_NOOP("Builds", "Preserve tab characters"),
}
# fmt: on

RENAMED = {
    "odt.pageHeader": "doc.pageHeader",
    "odt.pageCountOffset": "doc.pageCountOffset",
    "doc.colorHeadings": "format.colorHeadings",
    "doc.boldHeadings": "format.boldHeadings",
}


class FilterMode(Enum):
    """The decision reason for an item in a filtered project."""

    UNKNOWN = 0
    FILTERED = 1
    INCLUDED = 2
    EXCLUDED = 3
    SKIPPED = 4
    ROOT = 5


class BuildSettings:
    """Manuscript: Build Settings Class.

    This class manages the build settings for a Manuscript build job.
    The settings can be packed/unpacked to/from a dictionary for JSON.
    """

    __slots__ = (
        "_build",
        "_changed",
        "_excluded",
        "_format",
        "_included",
        "_name",
        "_order",
        "_path",
        "_settings",
        "_skipRoot",
        "_uuid",
    )

    def __init__(self) -> None:
        self._name = ""
        self._uuid = str(uuid.uuid4())
        self._path = CONFIG.homePath()
        self._build = ""
        self._order = 0
        self._format = nwBuildFmt.ODT
        self._skipRoot = set()
        self._excluded = set()
        self._included = set()
        self._settings = {k: v[1] for k, v in SETTINGS_TEMPLATE.items()}
        self._changed = False

    @classmethod
    def fromDict(cls, data: dict) -> BuildSettings:
        """Create a build settings object from a dict."""
        new = cls()
        new.unpack(data)
        return new

    ##
    #  Properties
    ##

    @property
    def name(self) -> str:
        """Return the build name."""
        return self._name

    @property
    def buildID(self) -> str:
        """Return the build ID as a UUID."""
        return self._uuid

    @property
    def order(self) -> int:
        """Return the build order."""
        return self._order

    @property
    def lastBuildPath(self) -> Path:
        """The last used build path."""
        if safeIsDir(self._path):
            return self._path
        return CONFIG.homePath()

    @property
    def lastBuildName(self) -> str:
        """The last used build name."""
        return self._build

    @property
    def lastFormat(self) -> nwBuildFmt:
        """The last used build format."""
        return self._format

    @property
    def changed(self) -> bool:
        """The changed status of the build."""
        return self._changed

    ##
    #  Getters
    ##

    @staticmethod
    def getLabel(key: str) -> str:
        """Extract the GUI label for a specific setting."""
        return QCoreApplication.translate("Builds", SETTINGS_LABELS.get(key, "ERROR"))

    def getStr(self, key: str) -> str:
        """Type safe value access for strings."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return str(value)

    def getBool(self, key: str) -> bool:
        """Type safe value access for bools."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return bool(value)

    def getInt(self, key: str) -> int:
        """Type safe value access for integers."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return int(value) if isinstance(value, int | float) else 0

    def getFloat(self, key: str) -> float:
        """Type safe value access for floats."""
        value = self._settings.get(key, SETTINGS_TEMPLATE.get(key, (None, None))[1])
        return float(value) if isinstance(value, int | float) else 0.0

    ##
    #  Setters
    ##

    def setName(self, name: str) -> None:
        """Set the build setting display name."""
        self._name = str(name)

    def setBuildID(self, value: str | uuid.UUID) -> None:
        """Set a UUID build ID."""
        value = checkUuid(value, "")
        if not value:
            self._uuid = str(uuid.uuid4())
        elif value != self._uuid:
            self._uuid = value

    def setOrder(self, value: int) -> None:
        """Set the build order."""
        if isinstance(value, int):
            self._order = value

    def setLastBuildPath(self, path: Path | str | None) -> None:
        """Set the last used build path."""
        if isinstance(path, str):
            path = Path(path)
        if isinstance(path, Path) and safeIsDir(path):
            self._path = path
        else:
            self._path = CONFIG.homePath()
        self._changed = True

    def setLastBuildName(self, name: str) -> None:
        """Set the last used build name."""
        self._build = str(name).strip()
        self._changed = True

    def setLastFormat(self, value: nwBuildFmt) -> None:
        """Set the last used build format."""
        if isinstance(value, nwBuildFmt):
            self._format = value
            self._changed = True

    def setFiltered(self, tHandle: str) -> None:
        """Set an item as filtered."""
        self._excluded.discard(tHandle)
        self._included.discard(tHandle)
        self._changed = True

    def setIncluded(self, tHandle: str) -> None:
        """Set an item as explicitly included."""
        self._excluded.discard(tHandle)
        self._included.add(tHandle)
        self._changed = True

    def setExcluded(self, tHandle: str) -> None:
        """Set an item as explicitly excluded."""
        self._excluded.add(tHandle)
        self._included.discard(tHandle)
        self._changed = True

    def setAllowRoot(self, tHandle: str, state: bool) -> None:
        """Set a specific root folder as allowed or not."""
        if state is True:
            self._skipRoot.discard(tHandle)
            self._changed = True
        elif state is False:
            self._skipRoot.add(tHandle)
            self._changed = True

    def setValue(self, key: str, value: T_BuildValue) -> None:
        """Set a specific value for a build setting."""
        if (d := SETTINGS_TEMPLATE.get(key)) and len(d) == 2 and isinstance(value, d[0]):
            self._changed |= value != self._settings[key]
            self._settings[key] = value

    ##
    #  Methods
    ##

    def isRootAllowed(self, tHandle: str) -> bool:
        """Check if a root handle is allowed in the build."""
        return tHandle not in self._skipRoot

    def buildItemFilter(self, project: NWProject, withRoots: bool = False) -> dict[str, tuple[bool, FilterMode]]:
        """Return a dictionary of item handles with filter decisions
        applied.
        """
        result: dict[str, tuple[bool, FilterMode]] = {}
        if not isinstance(project, NWProject):
            return result

        incNovel = bool(self.getBool("filter.includeNovel"))
        incNotes = bool(self.getBool("filter.includeNotes"))
        incInactive = bool(self.getBool("filter.includeInactive"))

        postponed = []

        def allowRoot(rHandle: str | None) -> None:
            if rHandle in postponed and rHandle in result and rHandle is not None:
                result[rHandle] = (True, FilterMode.ROOT)
                postponed.remove(rHandle)

        for item in project.tree:
            tHandle = item.itemHandle
            if item.isInactiveClass() or (item.itemRoot in self._skipRoot):
                result[tHandle] = (False, FilterMode.SKIPPED)
                continue
            if withRoots and item.isRootType():
                result[tHandle] = (False, FilterMode.SKIPPED)
                postponed.append(tHandle)
                continue
            if not item.isFileType():
                result[tHandle] = (False, FilterMode.SKIPPED)
                continue
            if tHandle in self._included:
                result[tHandle] = (True, FilterMode.INCLUDED)
                allowRoot(item.itemRoot)
                continue
            if tHandle in self._excluded:
                result[tHandle] = (False, FilterMode.EXCLUDED)
                continue

            isNote = item.isNoteLayout()
            isNovel = item.isDocumentLayout()
            isActive = item.isActive

            byActive = isActive or (not isActive and incInactive)
            byLayout = (isNote and incNotes) or (isNovel and incNovel)

            isAllowed = byActive and byLayout

            result[tHandle] = (isAllowed, FilterMode.FILTERED)
            if isAllowed:
                allowRoot(item.itemRoot)

        return result

    def resetChangedState(self) -> None:
        """Reset the changed status of the settings object. This must be
        called when the changes have been safely saved or passed on.
        """
        self._changed = False

    def pack(self) -> dict:
        """Pack all content into a JSON compatible dictionary."""
        logger.debug("Collecting build setting for '%s'", self._name)
        return {
            "name": self._name,
            "uuid": self._uuid,
            "path": str(self._path),
            "build": self._build,
            "order": self._order,
            "format": self._format.name,
            "settings": self._settings.copy(),
            "content": {
                "included": list(self._included),
                "excluded": list(self._excluded),
                "skipRoot": list(self._skipRoot),
            },
        }

    def unpack(self, data: dict) -> None:
        """Unpack a dictionary and populate the class."""
        content = data.get("content", {})
        settings = data.get("settings", {})
        included = content.get("included", [])
        excluded = content.get("excluded", [])
        skipRoot = content.get("skipRoot", [])

        self.setName(data.get("name", ""))
        self.setBuildID(data.get("uuid", ""))
        self.setOrder(data.get("order", 0))
        self.setLastBuildPath(data.get("path"))
        self.setLastBuildName(data.get("build", ""))

        buildFmt = str(data.get("format", ""))
        if buildFmt in nwBuildFmt.__members__:
            self.setLastFormat(nwBuildFmt[buildFmt])

        if isinstance(included, list):
            self._included = {h for h in included if isHandle(h)}
        if isinstance(excluded, list):
            self._excluded = {h for h in excluded if isHandle(h)}
        if isinstance(skipRoot, list):
            self._skipRoot = {h for h in skipRoot if isHandle(h)}

        self._settings = {k: v[1] for k, v in SETTINGS_TEMPLATE.items()}
        if isinstance(settings, dict):
            for key, value in settings.items():
                if isinstance(key, str) and isinstance(value, T_BuildValue):
                    self.setValue(RENAMED.get(key, key), value)

        self._changed = False

    @classmethod
    def duplicate(cls, source: BuildSettings) -> BuildSettings:
        """Make a copy of another build."""
        new = cls()
        new.unpack(source.pack())
        new._uuid = str(uuid.uuid4())
        new._name = f"{source.name} 2"
        return new


class BuildCollection:
    """Manuscript: Build Collection Class.

    This object holds all the build setting objects defined by the given
    project. The build settings are saved as a single JSON file in the
    project folder.
    """

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._lastBuild = ""
        self._defaultBuild = ""
        self._builds: dict[str, BuildSettings] = {}
        self._loadCollection()

    def __len__(self) -> int:
        """Return the number of builds."""
        return len(self._builds)

    ##
    #  Properties
    ##

    @property
    def lastBuild(self) -> str:
        """Return the last active build."""
        return self._lastBuild

    @property
    def defaultBuild(self) -> str:
        """Return the default build."""
        return self._defaultBuild

    ##
    #  Getters
    ##

    def getBuild(self, buildID: str) -> BuildSettings | None:
        """Get a specific build settings object."""
        return self._builds.get(buildID, None)

    ##
    #  Setters
    ##

    def setBuildsState(self, lastBuild: str, order: list[str]) -> None:
        """Set the last active build id."""
        for i, key in enumerate(order):
            if build := self._builds.get(key):
                build.setOrder(i)
        self._lastBuild = lastBuild
        self._saveCollection()

    def setDefaultBuild(self, buildID: str) -> None:
        """Set the default build id."""
        if buildID != self._defaultBuild:
            self._defaultBuild = buildID
            self._saveCollection()

    def setBuild(self, build: BuildSettings) -> None:
        """Set build settings data in the collection."""
        if isinstance(build, BuildSettings):
            self._builds[build.buildID] = build
            self._saveCollection()

    ##
    #  Methods
    ##

    def removeBuild(self, buildID: str) -> None:
        """Remove a build from the collection."""
        self._builds.pop(buildID, None)
        self._saveCollection()

    def builds(self) -> Iterable[tuple[str, str]]:
        """Iterate over all available builds."""
        for buildID, build in sorted(self._builds.items(), key=lambda x: x[1].order):
            yield buildID, build.name
        return

    ##
    #  Internal Functions
    ##

    def _loadCollection(self) -> bool:
        """Load build collections file."""
        buildsFile = self._project.storage.getMetaFile(nwFiles.BUILDS_FILE)
        if not isinstance(buildsFile, Path):
            return False
        if not safeExists(buildsFile):
            return True

        logger.debug("Loading builds file")
        try:
            with open(buildsFile, mode="r", encoding="utf-8") as inFile:
                data = json.load(inFile)
        except Exception:
            logger.error("Failed to load builds file")
            logException()
            return False

        if not isinstance(data, dict):
            logger.error("Builds file is not a JSON object")
            return False

        builds = data.get("novelWriter.builds", None)
        if not isinstance(builds, dict):
            logger.error("No novelWriter.builds in the builds file")
            return False

        for key, entry in builds.items():
            if key == "lastBuild":
                self._lastBuild = str(entry)
            elif key == "defaultBuild":
                self._defaultBuild = str(entry)
            elif isinstance(entry, dict):
                self._builds[key] = BuildSettings.fromDict(entry)

        return True

    def _saveCollection(self) -> bool:
        """Save build collections file."""
        buildsFile = self._project.storage.getMetaFile(nwFiles.BUILDS_FILE)
        if not isinstance(buildsFile, Path):
            return False

        logger.debug("Saving builds file")
        try:
            data: dict[str, str | dict] = {
                "lastBuild": self._lastBuild,
                "defaultBuild": self._defaultBuild,
            }
            data.update({k: b.pack() for k, b in self._builds.items()})
            with open(buildsFile, mode="w+", encoding="utf-8") as outFile:
                outFile.write(jsonEncode({"novelWriter.builds": data}, nmax=4))
        except Exception:
            logger.error("Failed to save builds file")
            logException()
            return False

        return True
