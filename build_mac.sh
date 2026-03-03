#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
#  TimeTrack — macOS Build Script
#  Usage:  chmod +x build_mac.sh && ./build_mac.sh
# ─────────────────────────────────────────────────────────────────────────────
set -e
cd "$(dirname "$0")"

BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
RED="\033[31m"
DIM="\033[2m"
RESET="\033[0m"

banner() { echo -e "\n${CYAN}${BOLD}▶  $1${RESET}"; }
ok()     { echo -e "  ${GREEN}✔  $1${RESET}"; }
fail()   { echo -e "  ${RED}✘  $1${RESET}"; exit 1; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║       ⏱  TimeTrack  —  macOS Build       ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"

# ── 1. Check Python ────────────────────────────────────────────────────────────
banner "Checking Python"
if ! command -v python3 &>/dev/null; then
    fail "python3 not found. Install from https://python.org or via Homebrew: brew install python"
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [[ $PY_MAJOR -lt 3 || ($PY_MAJOR -eq 3 && $PY_MINOR -lt 9) ]]; then
    fail "Python 3.9+ required (found $PY_VER). Download from https://python.org"
fi
ok "Python $PY_VER"

# Check tkinter is available
if ! python3 -c "import tkinter" 2>/dev/null; then
    echo ""
    echo -e "  ${RED}✘  tkinter not found.${RESET}"
    echo ""
    echo "  Fix options:"
    echo "    • Homebrew:  brew install python-tk"
    echo "    • Or download Python from https://python.org (includes tkinter)"
    exit 1
fi
ok "tkinter available"

# ── 2. Virtual environment ─────────────────────────────────────────────────────
banner "Setting up virtual environment"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    ok "Created .venv"
else
    ok ".venv already exists"
fi
source .venv/bin/activate
ok "Activated"

# ── 3. Install dependencies ────────────────────────────────────────────────────
banner "Installing dependencies"
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
ok "PySide6, requests, pyinstaller, Pillow installed"
ok "requests, pyinstaller, Pillow installed"

# ── 4. Generate icon ───────────────────────────────────────────────────────────
banner "Generating app icon"
python3 create_icon.py
ok "TimeTrack.icns ready"

# ── 5. Clean old build ─────────────────────────────────────────────────────────
banner "Cleaning previous build"
rm -rf build dist
ok "Cleaned"

# ── 6. Build with PyInstaller ──────────────────────────────────────────────────
banner "Building TimeTrack.app  (this takes ~30–60 seconds…)"
pyinstaller TimeTrack.spec --noconfirm --clean
echo ""

# ── 7. Verify ──────────────────────────────────────────────────────────────────
APP="dist/TimeTrack.app"
if [ ! -d "$APP" ]; then
    fail "Build failed — $APP not found"
fi

SIZE=$(du -sh "$APP" | cut -f1)
ok "TimeTrack.app built successfully  ($SIZE)"

# ── 8. Offer to copy to /Applications ─────────────────────────────────────────
echo ""
echo -e "${BOLD}  What would you like to do?${RESET}"
echo "  [1] Copy to /Applications  (makes it launchable from Spotlight & Dock)"
echo "  [2] Open the dist/ folder  (drag it yourself)"
echo "  [3] Done"
echo ""
read -p "  Enter choice [1/2/3]: " CHOICE

case "$CHOICE" in
    1)
        echo "  Copying to /Applications …"
        # Remove old version if present
        rm -rf "/Applications/TimeTrack.app"
        cp -R "$APP" "/Applications/TimeTrack.app"
        ok "Installed to /Applications/TimeTrack.app"
        echo ""
        echo -e "  ${DIM}First launch: right-click → Open to bypass Gatekeeper.${RESET}"
        echo -e "  ${DIM}After that it opens normally.${RESET}"
        open -a TimeTrack 2>/dev/null || true
        ;;
    2)
        open dist/
        ;;
    *)
        echo ""
        echo -e "  App is at:  ${BOLD}dist/TimeTrack.app${RESET}"
        echo -e "  Drag it to /Applications whenever you're ready."
        ;;
esac

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║          ✅  Build complete!              ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
echo ""
