# -*- mode: python ; coding: utf-8 -*-
# TimeTrack_windows.spec — PyInstaller build config for Windows (PySide6)
# Used by:  build_windows.bat  and  GitHub Actions

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
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TimeTrack",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can break PySide6 — keep off
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # no console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="TimeTrack.ico" if os.path.exists("TimeTrack.ico") else None,
    version_file=None,
)
