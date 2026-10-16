"""
novelWriter - MacOS Build
=========================

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
"""  # noqa

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys

from pathlib import Path

from utils.common import (
    ROOT_DIR,
    SETUP_DIR,
    checkAssetsExist,
    extractVersion,
    freshFolder,
    log,
    stripVersion,
    systemCall,
    updateMetaFile,
)


def enchantPrefix() -> Path:
    """Locate the Homebrew enchant installation."""
    prefix = Path("")
    if brew := shutil.which("brew"):
        result = subprocess.run([brew, "--prefix", "enchant"], capture_output=True, text=True, check=False)
        if result.returncode == 0:
            prefix = Path(result.stdout.strip())
    required = [
        prefix / "lib" / "libenchant-2.2.dylib",
        prefix / "lib" / "enchant-2" / "enchant_applespell.so",
    ]
    if not all(f.is_file() for f in required):
        log("[cr]ERROR:[e] Homebrew package 'enchant' is missing. Run 'brew install enchant'.")
        sys.exit(1)
    return prefix


def main(args: argparse.Namespace) -> None:
    """Build a macOS application bundle with PyInstaller."""
    try:
        import PyInstaller.__main__  # type: ignore
    except ImportError:
        log("[cr]ERROR:[e] Package 'pyinstaller' is missing. Run 'uv sync --group build'.")
        sys.exit(1)

    if sys.platform != "darwin":
        log("[cr]ERROR:[e] Command 'build-mac' can only be used on macOS")
        sys.exit(1)

    log("")
    log("[b]Build MacOS App Bundle[e]")
    log("[b]======================[e]")
    log("")

    if not checkAssetsExist():
        log("[cr]ERROR:[e] Missing assets, run 'pkgutils.py build-assets' first")
        sys.exit(1)

    numVers = stripVersion(extractVersion()[0])
    bldDir = ROOT_DIR / "build_macos"
    outDir = ROOT_DIR / "dist_macos"
    assetDir = bldDir / "assets"
    freshFolder(bldDir)
    freshFolder(outDir)

    shutil.copytree(ROOT_DIR / "novelwriter" / "assets", assetDir)
    updateMetaFile(assetDir / "meta.toml", buildFormat="macos-app", installSource="github")
    iconSet = SETUP_DIR / "macos" / "novelwriter.iconset"
    systemCall(["iconutil", "-c", "icns", iconSet, "-o", bldDir / "novelwriter.icns"])

    os.environ["NW_VERSION"] = numVers
    os.environ["NW_BUILD_DIR"] = str(bldDir)
    os.environ["NW_ENCHANT_PREFIX"] = str(enchantPrefix())
    os.environ["NW_MIN_MACOS"] = f"{platform.mac_ver()[0].partition('.')[0]}.0"
    os.environ["NW_CODESIGN_IDENTITY"] = args.identity or ""

    PyInstaller.__main__.run([
        str(SETUP_DIR / "macos" / "novelWriter.spec"),
        "--clean",
        "--noconfirm",
        "--workpath",
        str(bldDir / "pyinstaller"),
        "--distpath",
        str(outDir),
    ])
    shutil.rmtree(outDir / "novelWriter")
