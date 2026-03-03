#!/bin/bash
# =============================================================================
#  TimeTrack — macOS Build & DMG Packaging Script
#  Usage:  chmod +x build_mac.sh && ./build_mac.sh
#
#  What this does:
#    1. Checks Python 3.9+ is available
#    2. Creates a virtual environment & installs PySide6 + PyInstaller
#    3. Generates the app icon (TimeTrack.icns)
#    4. Builds TimeTrack.app with PyInstaller
#    5. Creates a distributable TimeTrack.dmg with a drag-to-Applications layout
# =============================================================================
set -e
cd "$(dirname "$0")"

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
DIM="\033[2m"
RESET="\033[0m"

banner() { echo -e "\n${CYAN}${BOLD}▶  $1${RESET}"; }
ok()     { echo -e "  ${GREEN}✔  $1${RESET}"; }
warn()   { echo -e "  ${YELLOW}⚠  $1${RESET}"; }
fail()   { echo -e "  ${RED}✘  $1${RESET}"; exit 1; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║       ⏱  TimeTrack  —  macOS Build       ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"

# ── 1. Check Python ────────────────────────────────────────────────────────
banner "Checking Python"
if ! command -v python3 &>/dev/null; then
    fail "python3 not found. Install from https://python.org or: brew install python"
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [[ $PY_MAJOR -lt 3 || ($PY_MAJOR -eq 3 && $PY_MINOR -lt 9) ]]; then
    fail "Python 3.9+ required (found $PY_VER). Download from https://python.org"
fi
ok "Python $PY_VER"

# ── 2. Virtual environment ─────────────────────────────────────────────────
banner "Setting up virtual environment"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "Created .venv"
else
    ok ".venv already exists"
fi
source .venv/bin/activate
ok "Activated"

# ── 3. Install dependencies ────────────────────────────────────────────────
banner "Installing dependencies (this may take a minute for PySide6…)"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "PySide6, requests, pyinstaller, Pillow installed"

# ── 4. Generate icon ───────────────────────────────────────────────────────
banner "Generating app icon"
python3 create_icon.py
ok "TimeTrack.icns ready"

# ── 5. Clean old build ─────────────────────────────────────────────────────
banner "Cleaning previous build"
rm -rf build dist
ok "Cleaned"

# ── 6. Build .app with PyInstaller ────────────────────────────────────────
banner "Building TimeTrack.app  (this takes 1–3 minutes…)"
pyinstaller TimeTrack.spec --noconfirm --clean
echo ""

APP="dist/TimeTrack.app"
if [ ! -d "$APP" ]; then
    fail "Build failed — $APP not found"
fi
APP_SIZE=$(du -sh "$APP" | cut -f1)
ok "TimeTrack.app built  ($APP_SIZE)"

# ── 7. Create DMG ─────────────────────────────────────────────────────────
banner "Creating TimeTrack.dmg"

DMG_NAME="TimeTrack"
DMG_FINAL="dist/TimeTrack.dmg"
DMG_TMP="dist/TimeTrack_tmp.dmg"
DMG_MOUNT="/Volumes/${DMG_NAME}"
VOLSIZE="300m"

# Remove any stale mounts or temp files
if [ -d "$DMG_MOUNT" ]; then
    hdiutil detach "$DMG_MOUNT" -quiet 2>/dev/null || true
fi
rm -f "$DMG_TMP" "$DMG_FINAL"

echo -e "  ${DIM}Creating blank disk image…${RESET}"
hdiutil create \
    -size "$VOLSIZE" \
    -fs HFS+ \
    -volname "$DMG_NAME" \
    -type UDIF \
    "$DMG_TMP" \
    -quiet

echo -e "  ${DIM}Mounting…${RESET}"
hdiutil attach "$DMG_TMP" -mountpoint "$DMG_MOUNT" -quiet

echo -e "  ${DIM}Copying TimeTrack.app…${RESET}"
cp -R "$APP" "$DMG_MOUNT/"

echo -e "  ${DIM}Adding Applications symlink…${RESET}"
ln -s /Applications "$DMG_MOUNT/Applications"

# ── 7a. DMG window layout via AppleScript ─────────────────────────────────
echo -e "  ${DIM}Setting Finder window layout…${RESET}"
osascript << APPLESCRIPT
tell application "Finder"
    tell disk "${DMG_NAME}"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {200, 150, 760, 470}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 128
        set position of item "TimeTrack.app" of container window to {155, 160}
        set position of item "Applications" of container window to {405, 160}
        update without registering applications
        delay 2
        close
    end tell
end tell
APPLESCRIPT

# Give Finder a moment to write .DS_Store
sleep 2

# Hide .DS_Store from Finder
SetFile -a V "${DMG_MOUNT}/.DS_Store" 2>/dev/null || true

# Bless the volume (makes it look nice)
bless --folder "$DMG_MOUNT" --openfolder "$DMG_MOUNT" 2>/dev/null || true

echo -e "  ${DIM}Unmounting…${RESET}"
hdiutil detach "$DMG_MOUNT" -quiet

echo -e "  ${DIM}Compressing to read-only DMG…${RESET}"
hdiutil convert "$DMG_TMP" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$DMG_FINAL" \
    -quiet

rm -f "$DMG_TMP"

if [ ! -f "$DMG_FINAL" ]; then
    fail "DMG creation failed"
fi

DMG_SIZE=$(du -sh "$DMG_FINAL" | cut -f1)
ok "TimeTrack.dmg created  ($DMG_SIZE)"

# ── 8. Code-signing (optional — signs if a Developer ID is available) ──────
banner "Code signing (optional)"
DEVID=$(security find-identity -v -p codesigning 2>/dev/null | grep "Developer ID Application" | head -1 | awk -F'"' '{print $2}')
if [ -n "$DEVID" ]; then
    echo -e "  Found: ${DIM}$DEVID${RESET}"
    codesign --force --deep --sign "$DEVID" "$APP" && ok "App signed"
    codesign --sign "$DEVID" "$DMG_FINAL"           && ok "DMG signed"
else
    warn "No Developer ID found — skipping code signing"
    warn "On first launch: right-click TimeTrack.app → Open to bypass Gatekeeper"
fi

# ── 9. Summary ─────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║          ✅  Build complete!              ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}App:${RESET} dist/TimeTrack.app"
echo -e "  ${BOLD}DMG:${RESET} dist/TimeTrack.dmg"
echo ""
echo -e "  ${DIM}Distribute the DMG — users open it, drag TimeTrack to Applications,${RESET}"
echo -e "  ${DIM}and launch it from Spotlight or the Dock.${RESET}"
echo ""

# ── 10. What to do next ────────────────────────────────────────────────────
echo -e "${BOLD}  What would you like to do now?${RESET}"
echo "  [1] Open dist/ folder in Finder"
echo "  [2] Install to /Applications right now"
echo "  [3] Done"
echo ""
read -p "  Enter choice [1/2/3]: " CHOICE

case "$CHOICE" in
    1)
        open dist/
        ;;
    2)
        rm -rf "/Applications/TimeTrack.app"
        cp -R "$APP" "/Applications/TimeTrack.app"
        ok "Installed to /Applications/TimeTrack.app"
        echo -e "  ${DIM}Right-click → Open for the first launch if Gatekeeper blocks it.${RESET}"
        open -a TimeTrack 2>/dev/null || true
        ;;
    *)
        echo -e "  Done.  Share ${BOLD}dist/TimeTrack.dmg${RESET} with anyone on macOS 11+."
        ;;
esac
echo ""
