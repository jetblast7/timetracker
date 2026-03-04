@echo off
:: =============================================================================
::  TimeTrack — local Windows build script
::  Usage: double-click, or run from Command Prompt / PowerShell
:: =============================================================================
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================
echo    TimeTrack  --  Windows Build
echo ============================================

:: ── Check Python ──────────────────────────────────────────────────────────────
where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: python not found.
    echo Download from https://python.org and make sure "Add to PATH" is checked.
    pause & exit /b 1
)
for /f "tokens=*" %%v in ('python --version') do echo   Found: %%v

:: ── Virtual environment ────────────────────────────────────────────────────────
if not exist ".venv" (
    echo.
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

:: ── Install dependencies ──────────────────────────────────────────────────────
echo.
echo Installing dependencies (PySide6 is large, may take a minute)...
pip install --quiet --upgrade pip
pip install --quiet PySide6 requests pyinstaller Pillow
echo   Dependencies ready.

:: ── Generate icons ────────────────────────────────────────────────────────────
echo.
echo Generating icons...
python scripts\create_icon.py

:: ── Clean ─────────────────────────────────────────────────────────────────────
echo.
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist  rmdir /s /q dist
echo   Cleaned.

:: ── PyInstaller ───────────────────────────────────────────────────────────────
echo.
echo Building TimeTrack.exe  (this takes 1-3 minutes)...
pyinstaller TimeTrack_windows.spec --noconfirm --clean
if not exist "dist\TimeTrack.exe" (
    echo ERROR: Build failed -- dist\TimeTrack.exe not found.
    pause & exit /b 1
)
echo   TimeTrack.exe built successfully.

:: ── Inno Setup installer (optional) ──────────────────────────────────────────
echo.
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist %ISCC% (
    echo Building installer with Inno Setup...
    %ISCC% scripts\installer.iss
    if exist "dist\TimeTrack_Setup.exe" (
        echo   TimeTrack_Setup.exe created.
    ) else (
        echo   WARNING: Inno Setup ran but installer not found.
    )
) else (
    echo   Inno Setup not found -- skipping installer creation.
    echo   Download from https://jrsoftware.org/isinfo.php to create an installer.
    echo   Portable build is at: dist\TimeTrack.exe
)

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo ============================================
echo    Build complete!
echo ============================================
echo.
if exist "dist\TimeTrack_Setup.exe" (
    echo   Installer:  dist\TimeTrack_Setup.exe
) else (
    echo   Portable:   dist\TimeTrack.exe
)
echo.

set /p OPEN="Open dist\ folder? [y/N]: "
if /i "!OPEN!"=="y" explorer dist

pause
