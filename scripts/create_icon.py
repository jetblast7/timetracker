#!/usr/bin/env python3
"""
Generates TimeTrack.icns (macOS) and TimeTrack.ico (Windows) from a single
vector-style drawing using Pillow.

Run before building:  python scripts/create_icon.py
Requires:             pip install Pillow
"""
import io
import math
import os
import struct
from PIL import Image, ImageDraw

# ── Output paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR   = os.path.dirname(SCRIPT_DIR)
ICNS_OUT   = os.path.join(ROOT_DIR, "TimeTrack.icns")
ICO_OUT    = os.path.join(ROOT_DIR, "TimeTrack.ico")


def draw_icon(size: int) -> Image.Image:
    """Render the TimeTrack clock icon at the given pixel size."""
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m    = max(2, int(size * 0.04))

    # Background circle
    draw.ellipse([m, m, size - m, size - m], fill="#1a1a2e")
    # Outer accent ring
    ring = max(2, int(size * 0.055))
    draw.ellipse([m, m, size - m, size - m], outline="#e94560", width=ring)
    # Inner clock face
    im = int(size * 0.18)
    draw.ellipse([im, im, size - im, size - im], fill="#0f3460")

    cx, cy = size / 2, size / 2

    # Hour tick marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        major = (i % 3 == 0)
        r1 = size * (0.26 if major else 0.28)
        r2 = size * 0.33
        w  = max(1, int(size * (0.024 if major else 0.012)))
        c  = "#e94560" if major else "#8892b0"
        draw.line(
            [cx + r1 * math.cos(angle), cy + r1 * math.sin(angle),
             cx + r2 * math.cos(angle), cy + r2 * math.sin(angle)],
            fill=c, width=w,
        )

    # Hour hand  (~10 o'clock)
    ah = math.radians(-60)
    draw.line(
        [cx, cy,
         cx + size * 0.18 * math.cos(ah),
         cy + size * 0.18 * math.sin(ah)],
        fill="#eaeaea", width=max(2, int(size * 0.022)),
    )

    # Minute hand  (~2 o'clock)
    am = math.radians(60)
    draw.line(
        [cx, cy,
         cx + size * 0.26 * math.cos(am),
         cy + size * 0.26 * math.sin(am)],
        fill="#64ffda", width=max(1, int(size * 0.015)),
    )

    # Centre dot
    dr = int(size * 0.035)
    draw.ellipse([cx - dr, cy - dr, cx + dr, cy + dr], fill="#e94560")

    return img


# ── ICNS builder ──────────────────────────────────────────────────────────────

def make_icns(out: str = ICNS_OUT) -> None:
    SIZE_MAP = {
        16:  b"icp4", 32:  b"icp5", 64:  b"icp6",
        128: b"ic07", 256: b"ic08", 512: b"ic09",
    }
    entries = []
    for sz, ostype in SIZE_MAP.items():
        buf = io.BytesIO()
        draw_icon(sz).save(buf, "PNG")
        entries.append((ostype, buf.getvalue()))

    total = 8 + sum(8 + len(d) for _, d in entries)
    with open(out, "wb") as f:
        f.write(b"icns")
        f.write(struct.pack(">I", total))
        for ostype, data in entries:
            f.write(ostype)
            f.write(struct.pack(">I", 8 + len(data)))
            f.write(data)
    print(f"  ✔  {out}  ({total:,} bytes)")


# ── ICO builder ───────────────────────────────────────────────────────────────

def make_ico(out: str = ICO_OUT) -> None:
    # Windows ICO standard sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    # Pillow can write multi-size .ico directly
    images[0].save(
        out,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )
    file_size = os.path.getsize(out)
    print(f"  ✔  {out}  ({file_size:,} bytes)")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating icons…")
    make_icns()
    make_ico()
    print("Done.")
