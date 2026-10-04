"""
novelWriter - Debian Build
==========================

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
import email.utils
import shutil
import sys

from dataclasses import dataclass
from datetime import date, datetime

from utils.common import (
    MIN_PY_VERSION,
    MIN_QT_VERS,
    ROOT_DIR,
    SETUP_DIR,
    checkAssetsExist,
    copyPackageFiles,
    copySourceCode,
    copyTestCode,
    extractVersion,
    log,
    makeCheckSum,
    systemCall,
    toUpload,
    updateMetaFile,
    writeFile,
)

SIGN_KEY = "D6A9F6B8F227CF7C6F6D1EE84DBBE4B734B0BD08"

# Single source of truth for what's needed to build and test the package
BUILD_DEPENDS = [
    "dh-python",
    "pybuild-plugin-pyproject",
    "python3-build",
    "python3-setuptools",
    "python3-all",
    "debhelper (>= 9)",
]
TEST_DEPENDS = [
    "python3-pytest (>= 6.0)",
    "python3-pytestqt",
    "python3-pytest-timeout",
]

DEB_CONTROL = f"""
Source: novelwriter
Maintainer: Veronica Berglyd Olsen <code@vkbo.net>
Section: text
Priority: optional
Build-Depends:
  %build-dependencies%,
  %dependencies%,
  %test-dependencies%
Standards-Version: 4.5.1
Homepage: https://novelwriter.io
X-Python3-Version: >= {MIN_PY_VERSION}

Package: novelwriter
Architecture: all
Depends:
  ${{misc:Depends}},
  ${{python3:Depends}},
  %dependencies%
Description: A plain text editor for planning and writing novels
"""


def runtimeDepends(target: DistroTarget) -> list[str]:
    """Return the runtime Depends for a given Debian control version."""
    depend = [
        f"python3 (>= {MIN_PY_VERSION})",
        f"python3-pyqt6 (>= {MIN_QT_VERS})",
        f"python3-pyqt6.qtsvg (>= {MIN_QT_VERS})",
        "python3-enchant (>= 2.0)",
        f"qt6-image-formats-plugins (>= {MIN_QT_VERS})",
    ]
    if target.debianVersion > 12:
        depend.append(f"qt6-svg-plugins (>= {MIN_QT_VERS})")
    return depend


@dataclass(frozen=True)
class DistroTarget:
    """A single Debian/Ubuntu distro release to build a package for."""

    family: str
    codename: str
    numVersion: str
    debianVersion: int
    suffix: str
    eol: date
    old: bool = False


DISTRO_TARGETS: dict[str, DistroTarget] = {
    "bookworm": DistroTarget("debian", "bookworm", "12", 12, "deb12u", date(2028, 6, 30), old=True),
    "trixie": DistroTarget("debian", "trixie", "13", 13, "deb13u", date(2030, 6, 30)),
    "noble": DistroTarget("ubuntu", "noble", "24.04", 12, "ubuntu24.04.", date(2029, 5, 1), old=True),
    "resolute": DistroTarget("ubuntu", "resolute", "26.04", 13, "ubuntu26.04.", date(2031, 5, 1)),
    "stonking": DistroTarget("ubuntu", "stonking", "26.10", 13, "ubuntu26.10.", date(2027, 7, 1)),
    "wilma": DistroTarget("linuxmint", "wilma", "22", 12, "mint22.", date(2029, 5, 1), old=True),
}


def aptPackages(target: DistroTarget) -> list[str]:
    """Return the plain apt package names (no version constraints) needed
    to build and test the Debian package for a given distro target.
    """
    entries = [*BUILD_DEPENDS, *runtimeDepends(target), *TEST_DEPENDS]
    return sorted({entry.split(" ", 1)[0] for entry in entries})


def makeDebianPackage(
    target: DistroTarget,
    signKey: str | None,
    buildNum: int,
    installSource: str,
) -> None:
    """Build a Debian package."""
    log("")
    log("[b]Build Debian Package[e]")
    log("[b]====================[e]")
    log(f"Target: {target.family.title()} {target.numVersion} {target.codename.title()}")
    log("")

    # Version Info
    # ============

    numVers, _, relDate = extractVersion()
    relDate = datetime.strptime(relDate, "%Y-%m-%d")
    pkgDate = email.utils.format_datetime(relDate.replace(hour=12, tzinfo=None))
    log("")

    pkgVers = numVers.replace("a", "~a").replace("b", "~b").replace("rc", "~rc")
    pkgVers = f"{pkgVers}+{target.suffix}{buildNum}"

    # Set Up Folder
    # =============

    bldDir = ROOT_DIR / "dist_deb"
    bldPkg = f"novelwriter_{pkgVers}"
    outDir = bldDir / bldPkg
    debDir = outDir / "debian"
    datDir = outDir / "data"

    bldDir.mkdir(exist_ok=True)
    if outDir.exists():
        log("[b]Removing old build files ...[e]")
        log("")
        shutil.rmtree(outDir)

    outDir.mkdir(exist_ok=False)

    # Check Additional Assets
    # =======================

    if not checkAssetsExist():
        log("[cr]ERROR:[e] Missing build assets")
        sys.exit(1)

    # Copy novelWriter Source
    # =======================

    log("[b]Copying novelWriter source ...[e]")
    log("")

    copySourceCode(outDir)
    copyTestCode(outDir)
    updateMetaFile(outDir / "novelwriter" / "assets" / "meta.toml", buildFormat="debian", installSource=installSource)

    log("")
    log("[b]Copying or generating additional files ...[e]")
    log("")

    copyPackageFiles(outDir, oldLicense=target.old)

    # Copy/Write Debian Files
    # =======================

    shutil.copytree(SETUP_DIR / "debian", debDir)
    log("[cg]Copied:[e] debian/*")

    control = DEB_CONTROL.replace("%build-dependencies%", ",\n  ".join(BUILD_DEPENDS))
    control = control.replace("%dependencies%", ",\n  ".join(runtimeDepends(target)))
    control = control.replace("%test-dependencies%", ",\n  ".join(TEST_DEPENDS))
    writeFile(debDir / "control", control)
    log("[cg]Wrote:[e]  debian/control")

    writeFile(
        debDir / "changelog",
        (
            f"novelwriter ({pkgVers}) {target.codename}; urgency=low\n\n"
            f"  * Update to version {pkgVers}\n\n"
            f" -- Veronica Berglyd Olsen <code@vkbo.net>  {pkgDate}\n"
        ),
    )
    log("[cg]Wrote:[e]  debian/changelog")

    # Copy/Write Data Files
    # =====================

    shutil.copytree(SETUP_DIR / "data", datDir)
    log("[cg]Copied:[e] data/*")

    shutil.copyfile(SETUP_DIR / "description_short.txt", outDir / "data" / "description_short.txt")
    log("[cg]Copied:[e] data/description_short.txt")

    # Build Package
    # =============

    log("")
    log("[b]Running dpkg-buildpackage ...[e]")
    log("")

    if signKey is None:
        signArgs = ["-us", "-uc"]
    else:
        signArgs = [f"-k{signKey}"]

    systemCall(["dpkg-buildpackage", *signArgs], cwd=outDir)
    shutil.copyfile(bldDir / f"{bldPkg}.tar.xz", bldDir / f"{bldPkg}.debian.tar.xz")
    toUpload(bldDir / f"{bldPkg}.debian.tar.xz")
    toUpload(bldDir / f"{bldPkg}_all.deb")
    toUpload(makeCheckSum(f"{bldPkg}.debian.tar.xz", cwd=bldDir))
    toUpload(makeCheckSum(f"{bldPkg}_all.deb", cwd=bldDir))

    log("")
    log("[cg]Done![e]")
    log("")


def printDebDepends(args: argparse.Namespace) -> None:
    """Print the apt packages needed to build and test a .deb for a given
    distro target, so CI can install them without duplicating this list.
    """
    print(" ".join(aptPackages(DISTRO_TARGETS[args.distro])), end=None)


def debian(args: argparse.Namespace) -> None:
    """Build a .deb package for a single distro target."""
    if sys.platform != "linux":
        log("[cr]ERROR:[e] Command 'build-deb' can only be used on Linux")
        sys.exit(1)

    target = DISTRO_TARGETS[args.distro]
    signKey = SIGN_KEY if args.sign else None
    bldNum = int(args.build) if args.build else 0
    installSource = args.install_source or "cloudsmith"

    if date.today() > target.eol:
        log(f"[cr]ERROR:[e] {target.family.title()} {target.codename} is EOL, not building package for it.")
        sys.exit(1)

    makeDebianPackage(target, signKey, bldNum, installSource)
