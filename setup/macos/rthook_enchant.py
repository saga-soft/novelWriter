"""
novelWriter - Enchant Runtime Hook
==================================

This file is a part of novelWriter
Copyright (C) 2026 Veronica Berglyd Olsen and novelWriter contributors

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

Points pyenchant at the libenchant bundled in the app. The AppleSpell
provider is found relative to the library path.
"""  # noqa

from __future__ import annotations

import os
import sys

os.environ["PYENCHANT_LIBRARY_PATH"] = os.path.join(sys._MEIPASS, "enchant", "lib", "libenchant-2.2.dylib")  # noqa: SLF001
