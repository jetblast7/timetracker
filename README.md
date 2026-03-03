# ⏱ TimeTrack — macOS App

A dark-themed desktop time tracker with multi-project support, manual entry, and Jira worklog sync.

---

## Build the Mac App — 3 steps

**Step 1 — Open Terminal and go to this folder**
```bash
cd /path/to/timetrack_package
```

**Step 2 — Make the script executable (first time only)**
```bash
chmod +x build_mac.sh
```

**Step 3 — Run the build**
```bash
./build_mac.sh
```

The script will:
- Check your Python version (3.9+ required)
- Create an isolated virtual environment
- Install all dependencies automatically
- Generate the app icon
- Build `TimeTrack.app` via PyInstaller
- Offer to install it to `/Applications` for you

Total build time: ~30–60 seconds.

---

## Requirements

- **macOS 10.13 (High Sierra) or later**
- **Python 3.9+** — download from https://python.org  
  *(Homebrew also works: `brew install python`)*
- **tkinter** — if missing, run: `brew install python-tk`

---

## First launch (Gatekeeper)

Because the app isn't signed with an Apple Developer certificate, macOS will
show a warning the first time.

**To open it:**
1. Right-click `TimeTrack.app` in Finder
2. Choose **Open**
3. Click **Open** in the dialog

After this, it opens normally like any other app.

---

## Run without building (from source)

```bash
pip3 install requests
python3 time_tracker.py
```

---

## Files

| File | Purpose |
|---|---|
| `time_tracker.py` | Main application source |
| `TimeTrack.spec` | PyInstaller build configuration |
| `create_icon.py` | Generates `TimeTrack.icns` |
| `requirements.txt` | Python dependencies |
| `build_mac.sh` | One-command macOS builder |

---

## Jira Setup

1. Click **⚙ Jira Settings** in the app header
2. Enter your Jira Cloud URL, Atlassian email, and API token
3. Generate a token at **id.atlassian.com → Security → API tokens**
4. Edit any project (✎) to link a Jira ticket key (e.g. `PROJ-42`)
5. Time is logged to Jira automatically when the timer stops

---

## Data

All data is stored at `~/.timetrack_data.json` — it persists across app updates.
