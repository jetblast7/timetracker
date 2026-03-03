# -*- mode: python ; coding: utf-8 -*-
# TimeTrack.spec — PyInstaller build config for macOS (PySide6)

import os

block_cipher = None

a = Analysis(
    ["time_tracker.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        "requests",
        "urllib3",
        "certifi",
        "charset_normalizer",
        "idna",
        "PySide6",
        "PySide6.QtWidgets",
        "PySide6.QtCore",
        "PySide6.QtGui",
        "shiboken6",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "scipy"],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TimeTrack",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    icon="TimeTrack.icns" if os.path.exists("TimeTrack.icns") else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="TimeTrack",
)

app = BUNDLE(
    coll,
    name="TimeTrack.app",
    icon="TimeTrack.icns" if os.path.exists("TimeTrack.icns") else None,
    bundle_identifier="com.timetrack.app",
    info_plist={
        "CFBundleName":               "TimeTrack",
        "CFBundleDisplayName":        "TimeTrack",
        "CFBundleVersion":            "2.0.0",
        "CFBundleShortVersionString": "2.0.0",
        "CFBundleIdentifier":         "com.timetrack.app",
        "NSHighResolutionCapable":    True,
        "LSMinimumSystemVersion":     "11.0.0",
        "NSHumanReadableCopyright":   "TimeTrack",
        "LSUIElement":                False,
        "NSAppTransportSecurity": {
            "NSAllowsArbitraryLoads": True,
        },
    },
)
