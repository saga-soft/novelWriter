#!/usr/bin/env python3
"""
novelWriter - Packaging Utils
=============================

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

import argparse
import shutil
import sys

import utils.assets
import utils.build_appimage
import utils.build_debian
import utils.build_flatpak
import utils.build_macos
import utils.build_pypi
import utils.build_windows
import utils.docs
import utils.icon_themes

from utils.common import ROOT_DIR, extractReqs, extractVersion, isStableVersion

OS_LINUX = sys.platform.startswith("linux")
OS_DARWIN = sys.platform.startswith("darwin")
OS_WIN = sys.platform.startswith("win32")


def printVersion(args: argparse.Namespace) -> None:
    """Print the novelWriter version and exit."""
    print(extractVersion(beQuiet=True)[0], end=None)


def printChannel(args: argparse.Namespace) -> None:
    """Print 'stable' or 'pre' depending on the release channel, and exit."""
    print("stable" if isStableVersion() else "pre", end=None)


def cleanBuildDirs(args: argparse.Namespace) -> None:
    """Recursively delete the 'build' and 'dist' folders."""
    print("")
    print("Cleaning up build environment ...")
    print("")

    folders = [
        ROOT_DIR / ".flatpak-builder",
        ROOT_DIR / "build_macos",
        ROOT_DIR / "build",
        ROOT_DIR / "dist_appimage",
        ROOT_DIR / "dist_macos",
        ROOT_DIR / "dist_deb",
        ROOT_DIR / "dist_doc",
        ROOT_DIR / "dist_flathub",
        ROOT_DIR / "dist_flatpak",
        ROOT_DIR / "dist_pypi",
        ROOT_DIR / "dist",
        ROOT_DIR / "novelWriter.egg-info",
    ]

    for folder in folders:
        if folder.is_dir():
            try:
                shutil.rmtree(folder)
                print(f"Deleted: {folder}")
            except OSError:
                print(f"Failed:  {folder}")
        else:
            print(f"Missing: {folder}")

    print("")


def genReqFiles(args: argparse.Namespace) -> None:
    """Generate requirements.txt file from pyproject.toml."""
    select = [s.strip().lower() for s in args.groups] if args.groups else ["app"]
    (ROOT_DIR / "requirements.txt").write_text("\n".join(extractReqs(select)), encoding="utf-8")


if __name__ == "__main__":
    """Parse command line options and run the commands."""
    parser = argparse.ArgumentParser(
        usage="pkgutils.py [command] [--flags]",
        description=(
            "This tool provides setup and build commands for installing or distributing "
            "novelWriter as a package on Linux, Mac and Windows, as well as developer tools "
            "for internationalisation."
        ),
    )
    parsers = parser.add_subparsers()

    # Version
    cmdVersion = parsers.add_parser("version", help="Print the novelWriter version.")
    cmdVersion.set_defaults(func=printVersion)

    # Release Channel
    cmdChannel = parsers.add_parser("channel", help="Print 'stable' or 'pre' depending on the release channel.")
    cmdChannel.set_defaults(func=printChannel)

    # Additional Builds
    # =================

    # Build Icons
    styles = ", ".join(["all", "default", "optional", "free", "non_free", *utils.icon_themes.ICON_SOURCES.keys()])
    cmdIcons = parsers.add_parser("icons", help="Build icon theme files from upstream sources.")
    cmdIcons.add_argument("style", help=f"What icon style to build: {styles}")
    cmdIcons.add_argument("--work-dir", help="Working directory.", default="build_icons")
    cmdIcons.set_defaults(func=utils.icon_themes.main)

    # Import Translations
    cmdImportTS = parsers.add_parser("qtlimport", help="Import updated i18n files from a Crowdin zip file.")
    cmdImportTS.add_argument("file", help="Path to zip file from Crowdin")
    cmdImportTS.set_defaults(func=utils.assets.importI18nUpdates)

    # Update i18n Sources
    cmdUpdateTS = parsers.add_parser(
        "qtlupdate",
        help=(
            "Update translation files for internationalisation. "
            "The files to be updated must be provided as arguments. "
            "New files can be created by giving a 'nw_<lang>.ts' file name "
            "where <lang> is a valid language code."
        ),
    )
    cmdUpdateTS.add_argument("files", nargs="+")
    cmdUpdateTS.set_defaults(func=utils.assets.updateTranslationSources)

    # Build i18n Files
    cmdBuildQM = parsers.add_parser("qtlrelease", help="Build the language files for internationalisation.")
    cmdBuildQM.set_defaults(func=utils.assets.buildTranslationAssets)

    # Update Docs i18n Sources
    cmdUpdateDocsPo = parsers.add_parser(
        "docs-lupdate",
        help=(
            "Update translation files for internationalisation of the docs. "
            "The langauges to be updated can be added as arguments, "
            "or set to all to update all existing translations."
        ),
    )
    cmdUpdateDocsPo.add_argument("lang", nargs="+")
    cmdUpdateDocsPo.set_defaults(func=utils.docs.updateDocsTranslationSources)

    # Build PDF Docs
    cmdBuildPdfDocs = parsers.add_parser("docs-pdf", help="Build the PDF manual files.")
    cmdBuildPdfDocs.add_argument("lang", nargs="+")
    cmdBuildPdfDocs.set_defaults(func=utils.docs.buildPdfDocAssets)

    # Build HTML Docs
    cmdBuildHtmlDocs = parsers.add_parser("docs-html", help="Build the HTML docs.")
    cmdBuildHtmlDocs.add_argument("lang", nargs="+", help="Language codes to generate docs for.")
    cmdBuildHtmlDocs.set_defaults(func=utils.docs.buildHtmlDocs)

    # Build Sample
    cmdBuildSample = parsers.add_parser("sample", help="Build the sample project zip file and add it to assets.")
    cmdBuildSample.set_defaults(func=utils.assets.buildSampleZip)

    # Clean Assets
    cmdCleanAssets = parsers.add_parser("clean-assets", help="Delete assets built by docs-pdf, sample and qtlrelease.")
    cmdCleanAssets.set_defaults(func=utils.assets.cleanBuiltAssets)

    # Build Assets
    cmdBuildAssets = parsers.add_parser(
        "build-assets", help="Build all assets. Includes docs-pdf, sample and qtlrelease."
    )
    cmdBuildAssets.set_defaults(func=utils.assets.buildAllAssets)

    # Python Packaging
    # ================

    # Build Debian Package
    distros = ", ".join(utils.build_debian.DISTRO_TARGETS.keys())
    cmdBuildDeb = parsers.add_parser(
        "build-deb", help="Build .deb packages for publishing. Add --sign to sign package."
    )
    cmdBuildDeb.add_argument("distro", help=f"Release to build for: {distros}.")
    cmdBuildDeb.add_argument("--sign", action="store_true", help="Sign the package.")
    cmdBuildDeb.add_argument("--build", type=int, help="Set build number, appended to the distro suffix.")
    cmdBuildDeb.add_argument("--install-source", help="Override the install source in meta.toml.")
    cmdBuildDeb.set_defaults(func=utils.build_debian.debian)

    # Print Debian Build Dependencies
    cmdDebDepends = parsers.add_parser("build-deb-depends", help="Print the apt package dependencies.")
    cmdDebDepends.add_argument("distro", help=f"Release to build for: {distros}.")
    cmdDebDepends.set_defaults(func=utils.build_debian.printDebDepends)

    # Build Ubuntu Packages for Launchpad
    cmdBuildUbuntu = parsers.add_parser(
        "build-ubuntu", help="Build source packages for Launchpad. Add --sign to sign package."
    )
    cmdBuildUbuntu.add_argument("--sign", action="store_true", help="Sign the package.")
    cmdBuildUbuntu.add_argument("--build", type=int, help="Set build number.")
    cmdBuildUbuntu.set_defaults(func=utils.build_debian.launchpad)

    # Build AppImage
    # See https://github.com/pypa/manylinux
    # See https://python-appimage.readthedocs.io/en/latest/#available-python-appimages
    cmdBuildAppImage = parsers.add_parser("build-appimage", help="Build an AppImage.")
    cmdBuildAppImage.add_argument("linux", help="Manylinux version, e.g. manylinux_2_28")
    cmdBuildAppImage.add_argument("arch", help="Architecture, e.g. x86_64")
    cmdBuildAppImage.add_argument("python", help="Python version, e.g. 3.13")
    cmdBuildAppImage.set_defaults(func=utils.build_appimage.appImage)

    # Build Flatpak
    cmdBuildFlatpak = parsers.add_parser("build-flatpak", help="Build a Flatpak image for direct download.")
    cmdBuildFlatpak.set_defaults(func=utils.build_flatpak.flatpak)

    # Build Flathub Submission Files
    cmdBuildFlathub = parsers.add_parser(
        "build-flathub", help="Generate the manifest and support files for a Flathub submission."
    )
    cmdBuildFlathub.add_argument("path", nargs="?", help="Path to copy the generated files into.")
    cmdBuildFlathub.set_defaults(func=utils.build_flatpak.flathub)

    # Build PyPI Packages
    cmdBuildPypi = parsers.add_parser("build-pypi", help="Build sdist and wheel packages for PyPI.")
    cmdBuildPypi.set_defaults(func=utils.build_pypi.pypi)

    # Build Windows Inno Setup Installer
    cmdBuildSetupExe = parsers.add_parser(
        "build-win-exe", help="Build a setup.exe file with Python embedded for Windows."
    )
    cmdBuildSetupExe.set_defaults(func=utils.build_windows.main)

    # Build MacOS App Bundle
    cmdBuildMac = parsers.add_parser(
        "build-mac", help="Build a macOS application bundle. Add --identity to sign with a Developer ID."
    )
    cmdBuildMac.add_argument("--identity", help="Codesign identity. Defaults to ad-hoc signing.")
    cmdBuildMac.set_defaults(func=utils.build_macos.main)

    # Build Clean
    cmdBuildClean = parsers.add_parser("build-clean", help="Recursively delete all build folders.")
    cmdBuildClean.set_defaults(func=cleanBuildDirs)

    # Generate Requirement File
    cmdGenReq = parsers.add_parser("gen-req", help="Generate a requirements.txt file for pip.")
    cmdGenReq.add_argument(
        "groups",
        nargs="*",
        help=(
            "Groups to generate for, or 'all' to generate for all groups. "
            "Use 'app' to generate for just the core application. "
            "Defaults to 'app' if none are specified."
        ),
    )
    cmdGenReq.set_defaults(func=genReqFiles)

    args = parser.parse_args()
    args.func(args)
