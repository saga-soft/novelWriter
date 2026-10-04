"""
novelWriter - AppImage Build
============================

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
import datetime
import os
import shutil
import sys

from pathlib import Path

from utils.common import (
    ROOT_DIR,
    SETUP_DIR,
    appdataXml,
    copyPackageFiles,
    copySourceCode,
    extractVersion,
    freshFolder,
    log,
    makeCheckSum,
    removeRedundantQt,
    systemCall,
    toUpload,
    updateMetaFile,
    writeFile,
)


def appImage(args: argparse.Namespace) -> None:
    """Build an AppImage."""
    try:
        import python_appimage  # noqa: F401 # type: ignore
    except ImportError:
        log(
            "[cr]ERROR:[e] Package 'python-appimage' is missing on this system.\n"
            "       Please run 'pip install --user python-appimage' to install it.\n"
        )
        sys.exit(1)

    if sys.platform != "linux":
        log("[cr]ERROR:[e] Command 'build-appimage' can only be used on Linux")
        sys.exit(1)

    log("")
    log("[b]Build AppImage[e]")
    log("[b]" + "=" * 120 + "[e]")

    mLinux = args.linux
    mArch = args.arch
    pyVer = args.python

    # Version Info
    pkgVers, _, relDate = extractVersion()
    relDate = datetime.datetime.strptime(relDate, "%Y-%m-%d")

    # Set Up Folder
    bldDir = ROOT_DIR / "dist_appimage"
    bldPkg = f"novelwriter-{pkgVers}-{mArch}"
    bldImg = f"{bldPkg}.AppImage"
    outDir = bldDir / bldPkg
    imgDir = bldDir / "appimage"
    appDir = bldDir / f"novelWriter-{mArch}"

    bldDir.mkdir(exist_ok=True)
    freshFolder(outDir)
    freshFolder(imgDir)
    freshFolder(appDir)

    # Remove old AppImages
    if images := bldDir.glob("*.AppImage"):
        log("[b]Removing old AppImages[e]")
        for image in images:
            image.unlink()

    # Copy novelWriter Source
    log("[b]Copying novelWriter source ...[e]")
    copySourceCode(outDir)
    updateMetaFile(outDir / "novelwriter" / "assets" / "meta.toml", buildFormat="appimage", installSource="github")

    log("[b]Copying or generating additional files ...[e]")
    copyPackageFiles(outDir)

    # Write Metadata
    writeFile(imgDir / "novelwriter.appdata.xml", appdataXml())
    writeFile(imgDir / "requirements.txt", str(outDir))
    writeFile(
        imgDir / "entrypoint.sh",
        (
            # f"export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${{APPDIR}}/usr/lib/{mArch}-linux-gnu/\n"
            '{{ python-executable }} -sE ${APPDIR}/opt/python{{ python-version }}/bin/novelwriter "$@"'
        ),
    )

    shutil.copyfile(SETUP_DIR / "data" / "novelwriter.desktop", imgDir / "novelwriter.desktop")
    log("[cg]Copied:[e] novelwriter.desktop")

    shutil.copyfile(SETUP_DIR / "icons" / "novelwriter.png", imgDir / "novelwriter.png")
    log("[cg]Copied:[e] novelwriter.png")

    # Build AppDir
    systemCall(
        [
            sys.executable,
            "-m",
            "python_appimage",
            "build",
            "app",
            "--no-packaging",
            "-l",
            f"{mLinux}_{mArch}",
            "-p",
            pyVer,
            "appimage",
        ],
        cwd=bldDir,
    )

    # Copy Libraries
    libPath = Path(f"/usr/lib/{mArch}-linux-gnu")
    siteDir = appDir / "opt" / f"python{pyVer}" / "lib" / f"python{pyVer}" / "site-packages"
    qt6Lib = siteDir / "PyQt6" / "Qt6" / "lib"
    shutil.copyfile(libPath / "libxcb-cursor.so.0", qt6Lib / "libxcb-cursor.so.0")

    # Remove Redundant
    removeRedundantQt(siteDir)

    # Build Image
    appToolExec = os.environ.get("APPIMAGE_TOOL_EXEC", "appimagetool")
    env = os.environ.copy()
    env["ARCH"] = mArch
    systemCall(
        [
            appToolExec,
            "--no-appstream",
            "--updateinformation",
            f"gh-releases-zsync|saga-soft|novelwriter|latest|novelwriter-*-{mArch}.AppImage.zsync",
            str(appDir),
            bldImg,
        ],
        cwd=bldDir,
        env=env,
    )

    updFile = bldDir / f"{bldImg}.zsync"
    bldFile = bldDir / bldImg
    shaFile = makeCheckSum(bldFile.name, cwd=bldDir)

    toUpload(bldFile)
    toUpload(updFile)
    toUpload(shaFile)
