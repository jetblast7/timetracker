#!/usr/bin/env python3
"""
Generates TimeTrack.icns for the macOS app bundle.
Run once before building: python3 create_icon.py
Requires Pillow:  pip install Pillow
"""
import io, math, struct, os
from PIL import Image, ImageDraw

def draw_icon(size):
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    m    = max(2, int(size * 0.04))

    # Background circle
    draw.ellipse([m, m, size-m, size-m], fill="#1a1a2e")
    # Outer accent ring
    ring = max(2, int(size * 0.055))
    draw.ellipse([m, m, size-m, size-m], outline="#e94560", width=ring)
    # Inner clock face
    im = int(size * 0.18)
    draw.ellipse([im, im, size-im, size-im], fill="#0f3460")

    cx, cy = size / 2, size / 2

    # Hour tick marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        major = (i % 3 == 0)
        r1 = size * (0.26 if major else 0.28)
        r2 = size * 0.33
        w  = max(1, int(size * (0.024 if major else 0.012)))
        c  = "#e94560" if major else "#8892b0"
        draw.line([cx + r1*math.cos(angle), cy + r1*math.sin(angle),
                   cx + r2*math.cos(angle), cy + r2*math.sin(angle)],
                  fill=c, width=w)

    # Hour hand  (~10 o'clock)
    ah = math.radians(-60)
    draw.line([cx, cy,
               cx + size*0.18*math.cos(ah),
               cy + size*0.18*math.sin(ah)],
              fill="#eaeaea", width=max(2, int(size*0.022)))

    # Minute hand  (~2 o'clock)
    am = math.radians(60)
    draw.line([cx, cy,
               cx + size*0.26*math.cos(am),
               cy + size*0.26*math.sin(am)],
              fill="#64ffda", width=max(1, int(size*0.015)))

    # Centre dot
    dr = int(size * 0.035)
    draw.ellipse([cx-dr, cy-dr, cx+dr, cy+dr], fill="#e94560")
    return img


def make_icns(out="TimeTrack.icns"):
    """Build a proper ICNS file from PNG payloads."""
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
    print(f"  ✅  {out}  ({total:,} bytes)")


if __name__ == "__main__":
    print("Generating TimeTrack.icns …")
    make_icns()
    print("Done.")
