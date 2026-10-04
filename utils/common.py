"""
novelWriter - Common Utils
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

import getpass
import json
import os
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).parent.parent
SETUP_DIR = ROOT_DIR / "setup"

MIN_QT_VERS = "6.4"
MIN_PY_VERSION = "3.11"
LOCAL_TZ = ZoneInfo("Europe/Oslo")

META_TEMPLATE = """
[Build]
timestamp = "{build_timestamp}"
type = "{build_type}"
format = "{build_format}"
install_source = "{install_source}"
"""

# ANSI Colour Codes
ANSI_COLOURS = {
    "[e]": "\033[0m",  # Reset
    "[b]": "\033[1m",  # Bold
    "[ck]": "\033[90m",  # Bright black
    "[cr]": "\033[91m",  # Bright red
    "[cg]": "\033[92m",  # Bright green
    "[cy]": "\033[93m",  # Bright yellow
    "[cb]": "\033[94m",  # Bright blue
    "[cm]": "\033[95m",  # Bright magenta
    "[cc]": "\033[96m",  # Bright cyan
    "[cw]": "\033[97m",  # Bright white
}

NO_COLOR = bool(os.environ.get("NO_COLOR"))  # Non-empty value forces colour off
SUPPORTS_COLOUR = sys.stdout.isatty() and not NO_COLOR


def log(message: str | Path | Exception = "") -> None:
    """Print a message to the terminal, translating ANSI colour codes."""
    if isinstance(message, Exception):
        message = f"[cr]{message.__class__.__name__}:[e] {message!s}"
    else:
        message = str(message)

    if message:
        for code, ansi in ANSI_COLOURS.items():
            message = message.replace(code, ansi if SUPPORTS_COLOUR else "")

    print(message, flush=True)


def isStableVersion() -> bool:
    """Return True if the version is a stable release."""
    _, hexVers, _ = extractVersion(beQuiet=True)
    return hexVers[-2] == "f"


def updateMetaFile(metaFile: Path, buildFormat: str, installSource: str) -> None:
    """Write the meta.toml file with build information to a build folder,
    ahead of packaging. Must not be used to overwrite the checked-in
    placeholder file in the source tree.
    """
    metaFile.write_text(
        META_TEMPLATE.format(
            build_timestamp=datetime.now(tz=LOCAL_TZ).isoformat(timespec="seconds"),
            build_type="stable" if isStableVersion() else "testing",
            build_format=buildFormat.lower(),
            install_source=installSource.lower(),
        ),
        encoding="utf-8",
    )
    log(f"[cg]Wrote:[e] {metaFile.relative_to(ROOT_DIR)}")


def readEnvFile() -> dict[str, str]:
    """Read a simple KEY=VALUE .env file from the project root into a dict."""
    envFile = ROOT_DIR / ".env"
    values = {}
    if envFile.is_file():
        for line in envFile.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def getEnvValue(key: str, prompt: str) -> str:
    """Resolve a value from the environment, the .env file, or a masked prompt."""
    if value := os.environ.get(key) or readEnvFile().get(key):
        return value
    return getpass.getpass(f"{prompt}: ").strip()


def apiRequest(url: str, token: str, data: dict | None = None) -> dict:
    """Make an authenticated GET or POST request against a JSON API."""
    body = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(url, data=body, method="POST" if body else "GET")
    request.add_header("Authorization", f"Bearer {token}")
    request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API error {exc.code}: {detail}") from exc


def extractReqs(groups: list[str]) -> list[str]:
    """Extract dependency groups from pyproject.toml."""
    data = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    reqs = []
    if "app" in groups or "all" in groups:
        reqs += data["project"]["dependencies"]
    for group in data["dependency-groups"]:
        if group in groups or "all" in groups:
            reqs += [d for d in data["dependency-groups"][group] if isinstance(d, str)]
    return reqs


def extractVersion(beQuiet: bool = False) -> tuple[str, str, str]:
    """Extract the novelWriter version number without having to import
    anything else from the main package.
    """

    def getValue(text: str) -> str:
        bits = text.partition("=")
        return bits[2].strip().strip('"')

    numVers = "0"
    hexVers = "0x0"
    relDate = "Unknown"
    initFile = ROOT_DIR / "novelwriter" / "__init__.py"
    try:
        for aLine in initFile.read_text(encoding="utf-8").splitlines():
            if aLine.startswith("__version__"):
                numVers = getValue(aLine)
            if aLine.startswith("__hexversion__"):
                hexVers = getValue(aLine)
            if aLine.startswith("__date__"):
                relDate = getValue(aLine)
    except Exception as exc:
        log(f"[cr]Could not read file:[e] {initFile}")
        log(exc)

    if not beQuiet:
        log(f"novelWriter version: {numVers} ({hexVers}) at {relDate}")

    return numVers, hexVers, relDate


def stripVersion(version: str) -> str:
    """Strip the pre-release part from a version number."""
    if "a" in version:
        return version.partition("a")[0]
    elif "b" in version:
        return version.partition("b")[0]
    elif "rc" in version:
        return version.partition("rc")[0]
    else:
        return version


def splitVersion(version: str) -> tuple[int, int, int]:
    """Split a version number into its major, minor and patch parts."""
    major, minor, patch = 0, 0, 0
    try:
        parts = stripVersion(version).split(".")
        if len(parts) > 0:
            major = int(parts[0])
        if len(parts) > 1:
            minor = int(parts[1])
        if len(parts) > 2:
            patch = int(parts[2])
    except Exception as exc:
        log(f"[cr]Could not split version:[e] {version}")
        log(exc)
    return major, minor, patch


def formatVersion(value: str) -> str:
    """Format a version number into a more human readable form."""
    major, _, version = value.partition(".")
    prefix = "20" if int(major) >= 20 else ""
    if "." in version:
        version = version.replace(".", " Patch ")
    elif "a" in version:
        version = version.replace("a", " Alpha ")
    elif "b" in version:
        version = version.replace("b", " Beta ")
    elif "rc" in version:
        version = version.replace("rc", " RC ")
    return f"{prefix}{major}.{version}" if major and version else ""


def copySourceCode(dst: Path) -> None:
    """Copy the novelwriter source tree to path."""
    src = ROOT_DIR / "novelwriter"
    for item in src.glob("**/*"):
        relSrc = item.relative_to(ROOT_DIR)
        if item.suffix in (".pyc", ".pyo"):
            log(f"[cy]Ignored:[e] {relSrc}")
            continue
        if item.parent.is_dir() and item.parent.name != "__pycache__":
            dstDir = dst / relSrc.parent
            if not dstDir.exists():
                dstDir.mkdir(parents=True)
                log(f"[cg]Created:[e] {dstDir.relative_to(ROOT_DIR)}")
        if item.is_file():
            shutil.copyfile(item, dst / relSrc)
            log(f"[cg]Copied:[e] {relSrc}")


def copyTestCode(dst: Path) -> None:
    """Copy the novelwriter test suite to path."""
    src = ROOT_DIR / "tests"
    skipDirs = {"__pycache__", ".pytest_cache", "_temp", "temp"}
    for item in src.glob("**/*"):
        relSrc = item.relative_to(ROOT_DIR)
        if skipDirs & set(relSrc.parts):
            continue
        if item.suffix in (".pyc", ".pyo"):
            log(f"[cy]Ignored:[e] {relSrc}")
            continue
        if item.parent.is_dir() and item.parent.name not in skipDirs:
            dstDir = dst / relSrc.parent
            if not dstDir.exists():
                dstDir.mkdir(parents=True)
                log(f"[cg]Created:[e] {dstDir.relative_to(ROOT_DIR)}")
        if item.is_file():
            shutil.copyfile(item, dst / relSrc)
            log(f"[cg]Copied:[e] {relSrc}")


def copyPackageFiles(dst: Path, oldLicense: bool = False) -> None:
    """Copy files needed for packaging."""
    copyFiles = [
        ROOT_DIR / "LICENSE.md",
        SETUP_DIR / "LICENSE-Apache-2.0.txt",
        ROOT_DIR / "CREDITS.md",
        ROOT_DIR / "pyproject.toml",
    ]
    for copyFile in copyFiles:
        shutil.copyfile(copyFile, dst / copyFile.name)
        log(f"[cg]Copied:[e] {copyFile}")

    text = readFile(ROOT_DIR / "pyproject.toml")
    text = text.replace("setup/description_pypi.md", "data/description_short.txt")
    if oldLicense:
        new = []
        for line in text.splitlines():
            if line.startswith("license = "):
                line = 'license = {text = "GPL-3.0-or-later AND Apache-2.0 AND CC-BY-4.0"}'
            if line.startswith("license-files = "):
                continue
            new.append(line)
        text = "\n".join(new)
    writeFile(dst / "pyproject.toml", text)


def toUpload(srcPath: str | Path, dstName: str | None = None) -> None:
    """Copy a file produced by one of the build functions to the upload
    directory. The file can optionally be given a new name.
    """
    uplDir = Path("dist_upload")
    uplDir.mkdir(exist_ok=True)
    srcPath = Path(srcPath)
    shutil.copyfile(srcPath, uplDir / (dstName or srcPath.name))


def makeCheckSum(sumFile: str, cwd: Path | None = None) -> str:
    """Create a SHA256 checksum file."""
    try:
        if cwd is None:
            shaFile = f"{sumFile}.sha256"
        else:
            shaFile = cwd / f"{sumFile}.sha256"
        with open(shaFile, mode="w", encoding="utf-8") as fOut:
            subprocess.call(["shasum", "-a", "256", sumFile], stdout=fOut, cwd=cwd)
        log(f"[cg]SHA256 Sum:[e] {shaFile}")
    except Exception as exc:
        log("[cr]Could not generate sha256 file[e]")
        log(exc)
        return ""

    return str(shaFile)


def checkAssetsExist() -> bool:
    """Check that the necessary assets exist ahead of a build."""
    hasSample = False
    hasManual = False
    hasQmData = False

    sampleZip = ROOT_DIR / "novelwriter" / "assets" / "sample.zip"
    if sampleZip.is_file():
        log(f"[cg]Found:[e] {sampleZip}")
        hasSample = True

    pdfManual = ROOT_DIR / "novelwriter" / "assets" / "manual.pdf"
    if pdfManual.is_file():
        log(f"[cg]Found:[e] {pdfManual}")
        hasManual = True

    i18nAssets = ROOT_DIR / "novelwriter" / "assets" / "i18n"
    if len(list(i18nAssets.glob("*.qm"))) > 0:
        log(f"[cg]Found:[e] {i18nAssets}/*.qm")
        hasQmData = True

    return hasSample and hasManual and hasQmData


def appdataXml() -> str:
    """Generate the appdata XML content."""
    raw = readFile(SETUP_DIR / "description_short.txt")
    desc = " ".join(raw.strip().splitlines()).strip()
    return readFile(SETUP_DIR / "novelwriter.appdata.xml").format(description=desc)


def readFile(file: Path) -> str:
    """Read an entire file and return as a string."""
    return file.read_text(encoding="utf-8")


def writeFile(file: Path, text: str) -> int:
    """Write string to file."""
    result = file.write_text(text, encoding="utf-8")
    log(f"[cg]Wrote:[e] {file.relative_to(ROOT_DIR)}")
    return result


def freshFolder(path: Path) -> None:
    """Make sure a folder exists and is empty."""
    if path.exists():
        log(f"[cy]Removing:[e] {path}")
        shutil.rmtree(path)
    path.mkdir()


def systemCall(cmd: list, cwd: Path | str | None = None, env: dict | None = None) -> int:
    """Make a system call using subprocess."""
    if isinstance(cwd, Path):
        cwd = str(cwd)
    try:
        code = subprocess.call([str(c) for c in cmd], cwd=cwd, env=env)
    except Exception as exc:
        log(exc)
        sys.exit(1)
    return code


def removeRedundantQt(qtBase: Path) -> None:
    """Delete Qt files that are not needed."""

    def unlinkIfFound(file: Path) -> None:
        if file.is_file():
            file.unlink()
            log(f"[cy]Deleted:[e] {file.relative_to(ROOT_DIR)}")

    def deleteFolder(folder: Path) -> None:
        if folder.is_dir():
            shutil.rmtree(folder)
            log(f"[cy]Deleted:[e] {folder.relative_to(ROOT_DIR)}")

    def unlinkIfPrefix(folder: Path, prefix: tuple[str, ...]) -> None:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.name.startswith(prefix):
                    if item.is_file():
                        unlinkIfFound(item)
                    elif item.is_dir():
                        deleteFolder(item)

    log("[b]Deleting redundant files ...[e]")

    pyQt6Dir = qtBase / "PyQt6"
    bindDir = qtBase / "PyQt6" / "bindings"
    qt6Dir = qtBase / "PyQt6" / "Qt6"
    binDir = qtBase / "PyQt6" / "Qt6" / "bin"
    libDir = qtBase / "PyQt6" / "Qt6" / "lib"
    plugDir = qtBase / "PyQt6" / "Qt6" / "plugins"
    qmDir = qtBase / "PyQt6" / "Qt6" / "translations"
    dictDir = qtBase / "enchant" / "data" / "mingw64" / "share" / "enchant" / "hunspell"

    # Prune Dictionaries
    if dictDir.exists():
        for item in dictDir.iterdir():
            if not item.name.startswith(("en_GB", "en_US")):
                unlinkIfFound(item)

    # Prune Translations
    for item in qmDir.iterdir():
        if not item.name.startswith("qtbase"):
            unlinkIfFound(item)

    # Delete Modules
    modules = [
        "Qt6Qml",
        "Qt6Quick",
        "Qt6Bluetooth",
        "Qt6Nfc",
        "Qt6Sensors",
        "Qt6SerialPort",
        "Qt6Test",
    ]
    modules.extend([x.replace("Qt6", "Qt") for x in modules])
    modules.extend([f"lib{x}" for x in modules])
    modules = tuple(modules)

    unlinkIfPrefix(pyQt6Dir, modules)
    unlinkIfPrefix(bindDir, modules)
    unlinkIfPrefix(binDir, modules)
    unlinkIfPrefix(libDir, modules)

    # Other Files
    deleteFolder(qt6Dir / "qml")
    deleteFolder(plugDir / "qmlls")
    deleteFolder(plugDir / "qmllint")


def extractBuildInfo(tool: str) -> dict[str, str]:
    """Extract the build information from pyproject.toml."""
    data = tomllib.loads((ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["novelwriter"]["build"][tool]
