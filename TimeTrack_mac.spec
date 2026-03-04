# -*- mode: python ; coding: utf-8 -*-
# TimeTrack_mac.spec — PyInstaller build config for macOS (PySide6)
# Used by:  build_mac.sh  and  GitHub Actions

import os

block_cipher = None

a = Analysis(
    ["time_tracker.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "requests", "urllib3", "certifi", "charset_normalizer", "idna",
        "PySide6", "PySide6.QtWidgets", "PySide6.QtCore",
        "PySide6.QtGui", "PySide6.QtNetwork",
        "shiboken6",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "scipy", "PyQt5", "PyQt6"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="TimeTrack",
    debug=False, strip=False, upx=False, console=False,
    icon="TimeTrack.icns" if os.path.exists("TimeTrack.icns") else None,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name="TimeTrack",
)

app = BUNDLE(
    coll,
    name="TimeTrack.app",
    icon="TimeTrack.icns" if os.path.exists("TimeTrack.icns") else None,
    bundle_identifier="com.timetrack.app",
    info_plist={
        "CFBundleName":               "TimeTrack",
        "CFBundleDisplayName":        "TimeTrack",
        "CFBundleVersion":            "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleIdentifier":         "com.timetrack.app",
        "NSHighResolutionCapable":    True,
        "LSMinimumSystemVersion":     "11.0.0",
        "NSHumanReadableCopyright":   "2025 TimeTrack",
        "LSUIElement":                False,
        "NSAppTransportSecurity":     {"NSAllowsArbitraryLoads": True},
    },
)
