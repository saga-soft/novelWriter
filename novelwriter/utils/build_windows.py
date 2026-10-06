"""
novelWriter - Windows Build
===========================

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
import compileall
import shutil
import sys
import urllib.request
import zipfile

from pathlib import Path

from utils.common import (
    ROOT_DIR,
    SETUP_DIR,
    copySourceCode,
    extractReqs,
    extractVersion,
    log,
    readFile,
    removeRedundantQt,
    systemCall,
    updateMetaFile,
    writeFile,
)


def prepareCode(outDir: Path) -> None:
    """Set up folders and copy code."""
    log("[b]Copying and compiling novelWriter source ...[e]")
    log("")

    copySourceCode(outDir)
    updateMetaFile(outDir / "novelwriter" / "assets" / "meta.toml", buildFormat="windows-setup", installSource="github")

    files = [
        ROOT_DIR / "CREDITS.md",
        ROOT_DIR / "LICENSE.md",
        SETUP_DIR / "iss_license.txt",
        SETUP_DIR / "windows" / "novelWriter.ico",
        SETUP_DIR / "windows" / "novelWriter.exe",
    ]
    for item in files:
        shutil.copyfile(item, outDir / item.name)
        log(f"[cg]Copied:[e] {item} > {outDir / item.name}")

    compileall.compile_dir(outDir / "novelwriter")

    log("[cg]Done[e]")
    log("")


def embedPython(bldDir: Path, outDir: Path) -> None:
    """Embed Python library."""
    log("[b]Adding Python embeddable ...[e]")

    pyVers = ".".join(str(v) for v in sys.version_info[:3])
    zipFile = f"python-{pyVers}-embed-amd64.zip"
    pyZip = bldDir / zipFile
    if not pyZip.is_file():
        pyUrl = f"https://www.python.org/ftp/python/{pyVers}/{zipFile}"
        log(f"Downloading: {pyUrl}")
        urllib.request.urlretrieve(pyUrl, pyZip)

    log("[b]Extracting ...[e]")
    with zipfile.ZipFile(pyZip, "r") as inFile:
        inFile.extractall(outDir)

    log("[cg]Done[e]")
    log("")


def installRequirements(libDir: Path) -> None:
    """Install dependencies."""
    log("[b]Install dependencies ...[e]")
    systemCall([sys.executable, "-m", "pip", "install", *extractReqs(["app"]), "--target", libDir])
    log("[cg]Done[e]")
    log("")


def main(args: argparse.Namespace) -> None:
    """Set up a package with embedded Python and dependencies for
    Windows installation.
    """
    log("")
    log("[b]Build Standalone Windows Package[e]")
    log("[b]================================[e]")
    log("")

    numVers, _, _ = extractVersion()
    log(f"Version: {numVers}")

    bldDir = ROOT_DIR / "dist"
    outDir = bldDir / "novelWriter"
    libDir = outDir / "lib"
    if outDir.exists():
        shutil.rmtree(outDir)

    bldDir.mkdir(exist_ok=True)
    outDir.mkdir()
    libDir.mkdir()

    prepareCode(outDir)
    embedPython(bldDir, outDir)
    installRequirements(libDir)
    removeRedundantQt(libDir)

    log("[b]Copy redistributable to root ...[e]")
    shutil.copyfile(libDir / "PyQt6" / "Qt6" / "bin" / "msvcp140.dll", outDir / "msvcp140.dll")

    log("[b]Updating starting script ...[e]")
    writeFile(
        outDir / "novelWriter.pyw",
        (
            "import os\n"
            "import sys\n"
            "\n"
            "os.curdir = os.path.abspath(os.path.dirname(__file__))\n"
            'sys.path.insert(0, os.path.join(os.curdir, "lib"))\n'
            "\n"
            'if __name__ == "__main__":\n'
            "    import novelwriter\n"
            "    novelwriter.main(sys.argv[1:])\n"
        ),
    )
    log("[cg]Done[e]")
    log("")

    log("[b]Running Inno Setup[e]")
    log("[b]##################[e]")
    log("")

    # Read the iss template
    issData = readFile(SETUP_DIR / "win_setup_embed.iss")
    issData = issData.replace(r"%%version%%", numVers)
    issData = issData.replace(r"%%dist%%", str(bldDir))
    writeFile(ROOT_DIR / "setup.iss", issData)
    log("")

    systemCall(["iscc", "setup.iss"])

    log("")
    log("[cg]Done[e]")
    log("")
