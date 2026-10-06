"""
novelWriter - Spell Checks
==========================

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

from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

from novelwriter.common import languageName
from novelwriter.constants import nwFiles
from novelwriter.error import logException

if TYPE_CHECKING:
    from collections.abc import Iterator

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

MAX_CACHE_SIZE = 100_000


class SpellEnchant:
    """Core: Enchant Spell Checking Wrapper.

    This is a wrapper class for Enchant to keep the API consistent
    between spell check tools.
    """

    __slots__ = ("_broker", "_cache", "_enchant", "_language", "_lock", "_project", "_requested", "_userDict")

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._enchant = FakeEnchant()
        self._userDict = UserDictionary(project)
        self._cache: dict[str, bool] = {}
        self._lock = Lock()
        self._language = None
        self._requested = None
        self._broker = None
        logger.debug("Ready: SpellEnchant")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: SpellEnchant")

    ##
    #  Properties
    ##

    @property
    def spellLanguage(self) -> str | None:
        """Return the current spell check language."""
        return self._language

    @property
    def requestedLanguage(self) -> str | None:
        """Return the requested spell check language."""
        return self._requested

    ##
    #  Setters
    ##

    def setLanguage(self, language: str | None) -> None:
        """Load a dictionary for the language specified in the config.
        If that fails, we load a mock dictionary so that lookups don't
        crash.

        Note:
        * Enchant will allow loading an empty string as a tag, but this
          will fail later on. See issue #1096.
        * The whole swap is locked so that a worker thread never sees a
          partially loaded dictionary.

        """
        with self._lock:
            self._enchant = FakeEnchant()
            self._broker = None
            self._language = None
            self._requested = language or None
            self._cache.clear()

            try:
                import enchant

                if language and enchant.dict_exists(language):
                    self._broker = enchant.Broker()
                    self._enchant = self._broker.request_dict(language)
                    self._language = language
                    logger.debug("Enchant spell checking for language '%s' loaded", language)
                else:
                    logger.warning("Enchant found no dictionary for language '%s'", language)

            except Exception:
                logger.error("Failed to load enchant spell checking for language '%s'", language)

            if self._enchant is None:
                self._enchant = FakeEnchant()
            else:
                self._userDict.load()
                for word in self._userDict:
                    self._enchant.add_to_session(word)

    ##
    #  Methods
    ##

    def checkWord(self, word: str) -> bool:
        """Forward check to pyenchant.

        Note:
        * The results are cached, since the same words tend to be
          checked over and over again.
        * The enchant call is locked as the library is not guaranteed thread safe, but
          cache hits are lock-free.

        """
        if (result := self._cache.get(word)) is None:
            with self._lock:
                try:
                    result = bool(self._enchant.check(word))
                except Exception:
                    result = True
            if len(self._cache) >= MAX_CACHE_SIZE:
                self._cache.clear()
            self._cache[word] = result
        return result

    def suggestWords(self, word: str) -> list[str]:
        """Ask pyenchant for suggestions."""
        with self._lock:
            try:
                return self._enchant.suggest(word)
            except Exception:
                return []

    def addWord(self, word: str, save: bool = True) -> None:
        """Add a word to the project dictionary."""
        if word := word.strip():
            with self._lock:
                try:
                    self._enchant.add_to_session(word)
                except Exception:
                    return
            self._cache[word] = True
            if save and self._userDict.add(word):
                self._userDict.save()
        return

    def listDictionaries(self) -> list[tuple[str, str]]:
        """List available dictionaries."""
        lang = []
        try:
            import enchant

            tags = [x for x, _ in enchant.list_dicts()]
            lang = [(x, f"{languageName(x)} [{x}]") for x in set(tags)]
        except Exception:
            logger.error("Failed to list languages for enchant spell checking")
        return sorted(lang, key=lambda x: x[1])

    def describeDict(self) -> tuple[str, str]:
        """Describe the currently loaded dictionary."""
        try:
            tag = self._enchant.tag
            name = self._enchant.provider.name  # type: ignore
        except Exception:
            logger.error("Failed to extract information about the dictionary")
            logException()
            tag = ""
            name = ""
        return tag, name


class FakeEnchant:
    """Fallback for when Enchant is selected, but not installed."""

    __slots__ = ("provider", "tag")

    def __init__(self) -> None:

        class FakeProvider:
            name = ""

        self.tag = ""
        self.provider = FakeProvider()

    def check(self, word: str) -> bool:
        """Return True for all words."""
        return True

    def suggest(self, word: str) -> list[str]:
        """Return an empty suggestion list."""
        return []

    def add_to_session(self, word: str) -> None:
        """Do nothing."""
        return


class UserDictionary:
    """Core: User Word Dictionary.

    This class holds all the user's own words for spell checking
    purposes. The dictionary is per-project.
    """

    __slots__ = ("_project", "_words")

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._words = set()

    def __contains__(self, word: str) -> bool:
        """Return True if the word is in the dictionary."""
        return word in self._words

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the words in the dictionary."""
        return iter(self._words)

    def add(self, word: str) -> bool:
        """Add a word to the dictionary, and return True if it was
        added, or False if it already existed.
        """
        if word in self._words:
            return False
        self._words.add(word)
        return True

    def load(self) -> None:
        """Load the user's dictionary."""
        self._words = set()
        wordList = self._project.storage.getMetaFile(nwFiles.DICT_FILE)
        try:
            if isinstance(wordList, Path) and wordList.is_file():
                with open(wordList, mode="r", encoding="utf-8") as fObj:
                    data = json.load(fObj)
                self._words = set(data.get("novelWriter.userDict", []))
                logger.info("Loaded: %s", nwFiles.DICT_FILE)
        except Exception:
            logger.error("Failed to load user dictionary")
            logException()

    def save(self) -> None:
        """Save the user's dictionary."""
        wordList = self._project.storage.getMetaFile(nwFiles.DICT_FILE)
        if isinstance(wordList, Path):
            try:
                with open(wordList, mode="w", encoding="utf-8") as fObj:
                    data = {"novelWriter.userDict": list(self._words)}
                    json.dump(data, fObj, indent=2)
            except Exception:
                logger.error("Failed to save user dictionary")
                logException()
