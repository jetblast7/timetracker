#!/bin/bash
# =============================================================================
#  TimeTrack — local macOS build script
#  Usage:  chmod +x build_mac.sh && ./build_mac.sh
# =============================================================================
set -e
cd "$(dirname "$0")"

BOLD="\033[1m"; GREEN="\033[32m"; CYAN="\033[36m"
YELLOW="\033[33m"; RED="\033[31m"; DIM="\033[2m"; RESET="\033[0m"

banner() { echo -e "\n${CYAN}${BOLD}▶  $1${RESET}"; }
ok()     { echo -e "  ${GREEN}✔  $1${RESET}"; }
warn()   { echo -e "  ${YELLOW}⚠  $1${RESET}"; }
fail()   { echo -e "  ${RED}✘  $1${RESET}"; exit 1; }

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║       ⏱  TimeTrack  —  macOS Build       ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"

banner "Checking Python"
command -v python3 &>/dev/null || fail "python3 not found. brew install python"
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "Python $PY_VER"

banner "Virtual environment"
[ ! -d ".venv" ] && python3 -m venv .venv && ok "Created .venv" || ok ".venv exists"
source .venv/bin/activate && ok "Activated"

banner "Installing dependencies"
pip install --quiet --upgrade pip
pip install --quiet PySide6 requests pyinstaller Pillow
ok "Dependencies ready"

banner "Generating icons"
python scripts/create_icon.py

banner "Cleaning previous build"
rm -rf build dist && ok "Cleaned"

banner "Building TimeTrack.app  (1–3 minutes…)"
pyinstaller TimeTrack_mac.spec --noconfirm --clean

APP="dist/TimeTrack.app"
[ ! -d "$APP" ] && fail "Build failed — $APP not found"
ok "TimeTrack.app built  ($(du -sh "$APP" | cut -f1))"

banner "Creating DMG"
bash scripts/make_dmg.sh

banner "Code signing (optional)"
DEVID=$(security find-identity -v -p codesigning 2>/dev/null \
    | grep "Developer ID Application" | head -1 | awk -F'"' '{print $2}')
if [ -n "$DEVID" ]; then
    codesign --force --deep --sign "$DEVID" "$APP"            && ok "App signed"
    codesign --sign "$DEVID" dist/TimeTrack.dmg               && ok "DMG signed"
else
    warn "No Developer ID — skipping signing"
    warn "First launch: right-click → Open to bypass Gatekeeper"
fi

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║          ✅  Build complete!              ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  ${BOLD}App:${RESET}  dist/TimeTrack.app"
echo -e "  ${BOLD}DMG:${RESET}  dist/TimeTrack.dmg"
echo ""
echo -e "${BOLD}  What next?${RESET}"
echo "  [1] Open dist/ in Finder"
echo "  [2] Install to /Applications"
echo "  [3] Done"
echo ""
read -p "  Choice [1/2/3]: " CHOICE
case "$CHOICE" in
    1) open dist/ ;;
    2) rm -rf "/Applications/TimeTrack.app"
       cp -R "$APP" "/Applications/TimeTrack.app" && ok "Installed to /Applications"
       open -a TimeTrack 2>/dev/null || true ;;
    *) echo -e "  Share ${BOLD}dist/TimeTrack.dmg${RESET} whenever you're ready." ;;
esac
echo ""
