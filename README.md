# ⏱ TimeTrack

Multi-project time tracker with Jira sync, categories, manual entry, export, and a menu-bar icon.

---

## Repository layout

```
timetrack/
├── time_tracker.py          ← application source (single file)
├── requirements.txt
├── TimeTrack_mac.spec       ← PyInstaller config for macOS
├── TimeTrack_windows.spec   ← PyInstaller config for Windows
├── build_mac.sh             ← local macOS build script
├── build_windows.bat        ← local Windows build script
├── scripts/
│   ├── create_icon.py       ← generates TimeTrack.icns + TimeTrack.ico
│   ├── make_dmg.sh          ← creates the macOS DMG (called by build_mac.sh)
│   └── installer.iss        ← Inno Setup config for the Windows installer
└── .github/
    └── workflows/
        └── release.yml      ← GitHub Actions: builds both platforms on tag push
```

---

## Quick start (run from source)

```bash
pip install PySide6 requests
python time_tracker.py
```

---

## Local builds

### macOS
```bash
chmod +x build_mac.sh
./build_mac.sh
```
Produces `dist/TimeTrack.app` and `dist/TimeTrack.dmg`.  
Requires macOS 11+ and Python 3.9+.

### Windows
Double-click `build_windows.bat`, or from a terminal:
```
build_windows.bat
```
Produces `dist/TimeTrack.exe` (portable) and `dist/TimeTrack_Setup.exe` (installer, if Inno Setup is installed).  
Download Inno Setup free from https://jrsoftware.org/isinfo.php

---

## Automated builds with GitHub Actions

Every time you push a version tag, GitHub automatically builds both the macOS DMG and the Windows installer and attaches them to a GitHub Release.

### One-time setup

1. Push this repository to GitHub
2. That's it — no secrets or extra configuration needed for unsigned builds

### Releasing a new version

```bash
git add .
git commit -m "Release v1.1.0"
git tag v1.1.0
git push origin main --tags
```

GitHub Actions will:
1. Build `TimeTrack.dmg` on a macOS runner
2. Build `TimeTrack_Setup.exe` on a Windows runner  
3. Create a GitHub Release named `TimeTrack v1.1.0` with both files attached

You can also trigger a build manually from the **Actions** tab → **Build & Release** → **Run workflow**.

### Viewing build output

Go to your repo on GitHub → **Actions** → click the latest run → download the artifacts from the bottom of the summary page.

---

## Code signing

### macOS
If you have an Apple Developer ID certificate in your keychain, `build_mac.sh` signs both the `.app` and `.dmg` automatically. Without it, users right-click → Open on first launch.

For CI signing, add your certificate to GitHub Secrets and update the workflow.

### Windows  
Without an Authenticode certificate, Windows Defender SmartScreen shows a warning on first run. Users click "More info" → "Run anyway". For production distribution, purchase a certificate from DigiCert or Sectigo and add signing to the workflow.

---

## System requirements

| Platform | Minimum OS          | Python (source only) |
|----------|---------------------|----------------------|
| macOS    | 11.0 (Big Sur)      | 3.9+                 |
| Windows  | Windows 10 (1809+)  | 3.9+                 |

Bundled app: ~150–200 MB (includes Qt framework). No Python required for end users.

---

## Data

All data saved to `~/.timetrack_data.json` (macOS/Linux) or `C:\Users\you\.timetrack_data.json` (Windows). Back this file up to preserve your history.
