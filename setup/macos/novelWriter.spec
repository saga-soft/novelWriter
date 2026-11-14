# -*- mode: python ; coding: utf-8 -*-

import datetime
import os

ROOT_DIR = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
BUILD_DIR = os.environ["NW_BUILD_DIR"]
VERSION = os.environ["NW_VERSION"]
MIN_MACOS = os.environ["NW_MIN_MACOS"]

DROP_FRAMEWORKS = ("QtNetwork", "QtPdf")
DROP_PREFIXES = (
    "PyQt6/Qt6/plugins/generic/",
    "PyQt6/Qt6/plugins/imageformats/libqmacheif",
    "PyQt6/Qt6/plugins/imageformats/libqmacjp2",
    "PyQt6/Qt6/plugins/imageformats/libqpdf",
    "PyQt6/Qt6/plugins/imageformats/libqtga",
    "PyQt6/Qt6/plugins/imageformats/libqtiff",
    "PyQt6/Qt6/plugins/imageformats/libqwbmp",
    "PyQt6/Qt6/plugins/platforms/libqminimal",
    "PyQt6/Qt6/plugins/platforms/libqoffscreen",
    *(f"PyQt6/Qt6/lib/{name}.framework/" for name in DROP_FRAMEWORKS),
)


def keepEntry(entry):
    """Filter Qt frameworks, plugins and translations novelWriter does not use."""
    name = entry[0]
    if name in DROP_FRAMEWORKS or name.startswith(DROP_PREFIXES):
        return False
    if name.startswith("PyQt6/Qt6/translations/"):
        return os.path.basename(name).startswith("qtbase")
    return True


a = Analysis(
    [os.path.join(ROOT_DIR, "novelWriter.py")],
    datas=[
        (os.path.join(BUILD_DIR, "assets"), "assets"),
    ],
    excludes=["PyQt6.QtDBus", "PyQt6.QtNetwork", "PyQt6.QtPdf", "PyQt6.QtSvg", "tkinter", "unittest", "test"],
)
a.binaries = [x for x in a.binaries if keepEntry(x)]
a.datas = [x for x in a.datas if keepEntry(x)]

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="novelWriter",
    console=False,
    strip=True,
    upx=False,
    codesign_identity=os.environ.get("NW_CODESIGN_IDENTITY") or None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=True, upx=False, name="novelWriter")
app = BUNDLE(
    coll,
    name="novelWriter.app",
    icon=os.path.join(BUILD_DIR, "novelwriter.icns"),
    bundle_identifier="io.novelwriter.novelWriter",
    version=VERSION,
    info_plist={
        "CFBundleVersion": VERSION,
        "NSPrincipalClass": "NSApplication",
        "NSHumanReadableCopyright": f"Copyright {datetime.date.today().year}, Veronica Berglyd Olsen",
        "LSMinimumSystemVersion": MIN_MACOS,
        "CFBundleDocumentTypes": [
            {
                "CFBundleTypeExtensions": ["nwx"],
                "CFBundleTypeName": "novelWriter Project",
                "CFBundleTypeRole": "Viewer",
                "LSHandlerRank": "Alternate",
            }
        ],
    },
)
