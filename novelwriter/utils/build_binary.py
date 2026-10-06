"""
novelWriter - Binary Dist Tools
===============================

This file is a part of novelWriter
Copyright (C) 2025 Veronica Berglyd Olsen and novelWriter contributors

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

import argparse


def runPyinstaller() -> None:
    """Run the pyinstaller."""
    import PyInstaller.__main__  # type: ignore

    build = ["novelWriter.py", "--clean", "--windowed", "--onedir", "--noconfirm"]
    build += ["--name", "novelwriter"]
    build += ["--workpath", "build_bin"]
    build += ["--distpath", "dist_bin"]
    build += ["--hidden-import", "pyenchant"]
    build += ["--add-data", "novelwriter/assets:assets"]
    PyInstaller.__main__.run(build)


def main(args: argparse.Namespace) -> None:
    """Entry point function."""
    runPyinstaller()
