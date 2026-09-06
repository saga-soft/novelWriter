"""
PyInstaller runtime hook: point pyenchant at the bundled libenchant.

The macOS DMG build bundles Homebrew's libenchant-2 dylib into
``<bundle>/lib`` and its backend plugins into ``<bundle>/lib/enchant-2``
(see .github/workflows/build-macos-dmg-pyinstaller.yaml). pyenchant would
otherwise search the host system for libenchant, which is not present on a
clean Mac, leaving the spell-check dictionary list empty (issue #2705).

This hook runs before novelWriter lazily imports ``enchant``, setting
PYENCHANT_LIBRARY_PATH so pyenchant loads the bundled library. enchant-2 is
relocatable and finds its backend plugins in the sibling ``enchant-2``
directory next to that library.
"""
import os
import sys

_base = getattr(sys, "_MEIPASS", None)
if _base:
    _lib = os.path.join(_base, "lib")
    if os.path.isdir(_lib):
        for _name in os.listdir(_lib):
            if _name.startswith("libenchant-2") and _name.endswith(".dylib"):
                os.environ.setdefault("PYENCHANT_LIBRARY_PATH", os.path.join(_lib, _name))
                break
