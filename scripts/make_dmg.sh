#!/bin/bash
# scripts/make_dmg.sh
# Creates dist/TimeTrack.dmg from dist/TimeTrack.app
# Called by both build_mac.sh (local) and GitHub Actions (CI)
set -e

APP="dist/TimeTrack.app"
DMG_NAME="TimeTrack"
DMG_FINAL="dist/TimeTrack.dmg"
DMG_TMP="dist/TimeTrack_tmp.dmg"
DMG_MOUNT="/Volumes/${DMG_NAME}"
VOLSIZE="350m"

if [ ! -d "$APP" ]; then
    echo "ERROR: $APP not found — run PyInstaller first." >&2
    exit 1
fi

# Detach any stale mount
if [ -d "$DMG_MOUNT" ]; then
    hdiutil detach "$DMG_MOUNT" -quiet 2>/dev/null || true
fi
rm -f "$DMG_TMP" "$DMG_FINAL"

echo "  Creating blank disk image…"
hdiutil create -size "$VOLSIZE" -fs HFS+ -volname "$DMG_NAME" -type UDIF "$DMG_TMP" -quiet

echo "  Mounting…"
hdiutil attach "$DMG_TMP" -mountpoint "$DMG_MOUNT" -quiet

echo "  Copying TimeTrack.app…"
cp -R "$APP" "$DMG_MOUNT/"

echo "  Adding /Applications symlink…"
ln -s /Applications "$DMG_MOUNT/Applications"

echo "  Setting Finder window layout…"
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

sleep 2
SetFile -a V "${DMG_MOUNT}/.DS_Store" 2>/dev/null || true
bless --folder "$DMG_MOUNT" --openfolder "$DMG_MOUNT" 2>/dev/null || true

echo "  Unmounting…"
hdiutil detach "$DMG_MOUNT" -quiet

echo "  Compressing…"
hdiutil convert "$DMG_TMP" -format UDZO -imagekey zlib-level=9 -o "$DMG_FINAL" -quiet
rm -f "$DMG_TMP"

SIZE=$(du -sh "$DMG_FINAL" | cut -f1)
echo "  ✔  dist/TimeTrack.dmg  ($SIZE)"
