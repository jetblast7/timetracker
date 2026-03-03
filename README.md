# TimeTrack — macOS

Multi-project time tracker with Jira worklog sync, manual entry, export, and a menu-bar status icon.

---

## Quick Start (run from source)

```bash
pip3 install PySide6 requests
python3 time_tracker.py
```

---

## Building the DMG

### Requirements
- macOS 11 (Big Sur) or later
- Python 3.9+  (`python3 --version`)
- Xcode Command Line Tools  (`xcode-select --install`)

### One command

```bash
chmod +x build_mac.sh
./build_mac.sh
```

The script will:

1. Create a `.venv` and install PySide6, requests, pyinstaller, Pillow
2. Generate `TimeTrack.icns` from `create_icon.py`
3. Build `dist/TimeTrack.app` with PyInstaller
4. Produce `dist/TimeTrack.dmg` — a compressed, drag-to-install disk image
5. Optionally sign the app if a Developer ID certificate is in your keychain

### Output

```
dist/
  TimeTrack.app    <- standalone native app (no Python needed)
  TimeTrack.dmg    <- distributable installer image
```

Open the DMG, drag TimeTrack to Applications, then launch from Spotlight or the Dock.

---

## First launch (unsigned builds)

If you don't have an Apple Developer ID the app will be unsigned.
macOS Gatekeeper will block the first open. To fix:

- Right-click TimeTrack.app -> Open -> click Open in the dialog
- After that it launches normally

Or run once in Terminal:
```bash
xattr -dr com.apple.quarantine /Applications/TimeTrack.app
```

---

## Features

- Multi-project tracking with live timer
- Jira Cloud worklog sync (edit duration before posting)
- Manual time entry with notes
- Delete sessions (optionally removes Jira worklog too)
- CSV and JSON export with project and date filtering
- Customisable stat cards (click any card to change time window)
- Menu-bar icon: red when tracking, green when idle
  - Quick start/stop and project switching from the menu bar

---

## System Requirements

- macOS 11.0 (Big Sur) or later — required for PySide6
- Apple Silicon or Intel
- ~180 MB disk space (includes Qt framework)

---

## Data storage

All data saved to ~/.timetrack_data.json
Back this file up to preserve your history.
