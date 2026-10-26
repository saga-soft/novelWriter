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

from abc import ABC, abstractmethod
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Any

from novelwriter import CONFIG
from novelwriter.common import languageName
from novelwriter.constants import nwFiles
from novelwriter.error import logException

if TYPE_CHECKING:
    from collections.abc import Iterator

    from novelwriter.core.project import NWProject

logger = logging.getLogger(__name__)

MAX_CACHE_SIZE = 100_000


class SpellChecker(ABC):
    """Core: Spell Checking Base Class."""

    __slots__ = ("_cache", "_language", "_lock", "_project", "_requested", "_userDict")

    def __init__(self, project: NWProject) -> None:
        self._project = project
        self._userDict = UserDictionary(project)
        self._cache: dict[str, bool] = {}
        self._lock = Lock()
        self._language = None
        self._requested = None
        logger.debug("Ready: SpellChecker")

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        logger.debug("Delete: SpellChecker")

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
        If that fails, lookups accept all words so that they don't
        crash.

        Note: The whole swap is locked so that a worker thread never
        sees a partially loaded dictionary.
        """
        with self._lock:
            self._language = None
            self._requested = language or None
            self._cache.clear()

            try:
                loaded = self._loadLanguage(language)
            except Exception:
                logger.error("Failed to load spell checking for language '%s'", language)
                loaded = False

            if loaded:
                self._language = language

            self._userDict.load()
            for word in self._userDict:
                try:
                    self._addSessionWord(word)
                except Exception:
                    logger.error("Failed to add word to spell checking session")
                    break

    ##
    #  Methods
    ##

    def checkWord(self, word: str) -> bool:
        """Check the spelling of a word.

        Note:
        * The results are cached, since the same words tend to be
          checked over and over again.
        * The backend call is locked as the library is not guaranteed
          thread safe, but cache hits are lock-free.

        """
        if (result := self._cache.get(word)) is None:
            with self._lock:
                try:
                    result = bool(self._checkWord(word))
                except Exception:
                    result = True
            if len(self._cache) >= MAX_CACHE_SIZE:
                self._cache.clear()
            self._cache[word] = result
        return result

    def suggestWords(self, word: str) -> list[str]:
        """Ask the backend for suggestions."""
        with self._lock:
            try:
                return self._suggestWords(word)
            except Exception:
                return []

    def addWord(self, word: str, save: bool = True) -> None:
        """Add a word to the project dictionary."""
        if word := word.strip():
            with self._lock:
                try:
                    self._addSessionWord(word)
                except Exception:
                    return
            self._cache[word] = True
            if save and self._userDict.add(word):
                self._userDict.save()
        return

    def listDictionaries(self) -> list[tuple[str, str]]:
        """List available dictionaries."""
        lang = []
        with self._lock:
            try:
                lang = [(x, f"{languageName(x)} [{x}]") for x in set(self._listLanguages())]
            except Exception:
                logger.error("Failed to list languages for spell checking")
        return sorted(lang, key=lambda x: x[1])

    def describeDict(self) -> tuple[str, str]:
        """Describe the currently loaded dictionary."""
        try:
            tag, name = self._describeDict()
        except Exception:
            logger.error("Failed to extract information about the dictionary")
            logException()
            tag = ""
            name = ""
        return tag, name

    ##
    #  Backend Hooks
    ##

    @abstractmethod
    def _loadLanguage(self, language: str | None) -> bool:
        """Load a language dictionary, and return True on success."""

    @abstractmethod
    def _checkWord(self, word: str) -> bool:
        """Return True if the word is spelled correctly."""

    @abstractmethod
    def _suggestWords(self, word: str) -> list[str]:
        """Return spelling suggestions for a word."""

    @abstractmethod
    def _addSessionWord(self, word: str) -> None:
        """Accept a word for the rest of the session."""

    @abstractmethod
    def _listLanguages(self) -> list[str]:
        """Return the tags of all available languages."""

    @abstractmethod
    def _describeDict(self) -> tuple[str, str]:
        """Return the tag and provider name of the loaded dictionary."""


class SpellEnchant(SpellChecker):
    """Core: Enchant Spell Checking Wrapper.

    This is a wrapper class for Enchant to keep the API consistent
    between spell check tools.
    """

    __slots__ = ("_broker", "_enchant")

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._enchant = FakeEnchant()
        self._broker = None

    def _loadLanguage(self, language: str | None) -> bool:
        """Load an Enchant dictionary, or fall back to a mock one.

        Note: Enchant will allow loading an empty string as a tag, but
        this will fail later on. See issue #1096.
        """
        self._enchant = FakeEnchant()
        self._broker = None

        import enchant

        if language and enchant.dict_exists(language):
            self._broker = enchant.Broker()
            if (spell := self._broker.request_dict(language)) is not None:
                self._enchant = spell
                logger.debug("Enchant spell checking for language '%s' loaded", language)
                return True

        logger.warning("Enchant found no dictionary for language '%s'", language)
        return False

    def _checkWord(self, word: str) -> bool:
        """Forward check to pyenchant."""
        return self._enchant.check(word)

    def _suggestWords(self, word: str) -> list[str]:
        """Ask pyenchant for suggestions."""
        return self._enchant.suggest(word)

    def _addSessionWord(self, word: str) -> None:
        """Add a word to the pyenchant session."""
        self._enchant.add_to_session(word)

    def _listLanguages(self) -> list[str]:
        """List the languages known to pyenchant."""
        import enchant

        return [x for x, _ in enchant.list_dicts()]

    def _describeDict(self) -> tuple[str, str]:
        """Describe the loaded pyenchant dictionary."""
        return self._enchant.tag, self._enchant.provider.name  # type: ignore


class SpellApple(SpellChecker):
    """Core: macOS Spell Checking Wrapper.

    This is a wrapper class for the system NSSpellChecker. Words added
    by the user are ignored in a spell document owned by this instance.
    """

    __slots__ = ("_checker", "_document")

    def __init__(self, project: NWProject) -> None:
        super().__init__(project)
        self._checker: Any = None
        self._document = 0

    def __del__(self) -> None:  # pragma: no cover
        """Class destructor."""
        self._closeDocument()
        super().__del__()

    def _loadLanguage(self, language: str | None) -> bool:
        """Select a system language, and open a new spell document."""
        from AppKit import NSSpellChecker  # type: ignore

        self._closeDocument()
        self._checker = NSSpellChecker.sharedSpellChecker()
        self._checker.setAutomaticallyIdentifiesLanguages_(False)
        self._document = NSSpellChecker.uniqueSpellDocumentTag()

        if language and self._checker.setLanguage_(language):
            logger.debug("Apple spell checking for language '%s' loaded", language)
            return True

        logger.warning("Apple spell checking found no language '%s'", language)
        return False

    def _checkWord(self, word: str) -> bool:
        """Forward check to NSSpellChecker."""
        from Foundation import NSNotFound  # type: ignore

        if self._language is None:
            return True
        result, _ = self._checker.checkSpellingOfString_startingAt_language_wrap_inSpellDocumentWithTag_wordCount_(
            word, 0, self._language, False, self._document, None
        )
        return result.location == NSNotFound

    def _suggestWords(self, word: str) -> list[str]:
        """Ask NSSpellChecker for suggestions."""
        from Foundation import NSMakeRange  # type: ignore

        if self._language is None:
            return []
        guesses = self._checker.guessesForWordRange_inString_language_inSpellDocumentWithTag_(
            NSMakeRange(0, len(word)), word, self._language, self._document
        )
        return [str(x) for x in guesses or []]

    def _addSessionWord(self, word: str) -> None:
        """Ignore a word in the spell document."""
        if self._checker is not None:
            self._checker.ignoreWord_inSpellDocumentWithTag_(word, self._document)

    def _listLanguages(self) -> list[str]:
        """List the languages known to NSSpellChecker."""
        from AppKit import NSSpellChecker  # type: ignore

        return [str(x) for x in NSSpellChecker.sharedSpellChecker().availableLanguages()]

    def _describeDict(self) -> tuple[str, str]:
        """Describe the selected NSSpellChecker language."""
        if self._language is None:
            return "", ""
        return self._language, "AppleSpell"

    def _closeDocument(self) -> None:
        """Close the spell document holding the session words."""
        if self._checker is not None and self._document:
            self._checker.closeSpellDocumentWithTag_(self._document)
        self._document = 0


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
                with open(wordList, mode="w", encoding="utf-8", newline=CONFIG.lineEnding) as fObj:
                    data = {"novelWriter.userDict": list(self._words)}
                    json.dump(data, fObj, indent=2)
            except Exception:
                logger.error("Failed to save user dictionary")
                logException()
