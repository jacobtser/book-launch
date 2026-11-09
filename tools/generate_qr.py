#!/usr/bin/env python3
"""Generate the official, art-directed QR code for the book launch programme.

Usage:
    py -3 tools/generate_qr.py

The destination URL is defined once below. Change it, re-run, and both the
web PNG, the print PNG, and the editable SVG are regenerated.
"""

from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# The only thing you normally need to edit:
URL = "https://jacobtser.github.io/book-launch/"
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

INK = "#0C332B"       # deep forest ink
IVORY = "#F7F1E5"     # warm paper
GOLD = "#C79A3B"      # burnished gold

FINAL = 2048          # design canvas (all drawing coordinates are in this space)
SS = 3                # supersampling factor for smooth edges
C = FINAL * SS

qr = segno.make_qr(URL, error="H")
matrix = qr.matrix
n = len(matrix)

# 40 px modules at final size -> a 1800 px code + built-in quiet zone,
# leaving a generous margin for the gold frame.
MODULE = 40
QUIET = 4
TOTAL = (n + QUIET * 2) * MODULE
OFFSET = (FINAL - TOTAL) // 2

M = MODULE * SS
OX = OFFSET * SS
OY = OFFSET * SS


def px(v: float) -> int:
    """Scale a final-canvas coordinate to the supersampled canvas."""
    return int(round(v * SS))


img = Image.new("RGB", (C, C), IVORY)
draw = ImageDraw.Draw(img)


def rounded(x0, y0, x1, y1, radius, fill=None, outline=None, width=0):
    draw.rounded_rectangle(
        [px(x0), px(y0), px(x1), px(y1)],
        radius=px(radius),
        fill=fill,
        outline=outline,
        width=px(width) if width else 0,
    )


# --- Paper margin frame ------------------------------------------------------
rounded(26, 26, FINAL - 26, FINAL - 26, 18, outline=GOLD, width=2)
rounded(36, 36, FINAL - 36, FINAL - 36, 12, outline=GOLD, width=1)

# Small gold corner marks, kept well outside the code's quiet zone.
mark_len = 54
mark_gap = 16
for cx, cy, sx, sy in (
    (mark_gap, mark_gap, 1, 1),
    (FINAL - mark_gap, mark_gap, -1, 1),
    (mark_gap, FINAL - mark_gap, 1, -1),
    (FINAL - mark_gap, FINAL - mark_gap, -1, -1),
):
    draw.line(
        [px(cx), px(cy), px(cx + sx * mark_len), px(cy)],
        fill=GOLD,
        width=px(2),
    )
    draw.line(
        [px(cx), px(cy), px(cx), px(cy + sy * mark_len)],
        fill=GOLD,
        width=px(2),
    )

# --- Data modules -----------------------------------------------------------
dark_modules = []

for row in range(n):
    for col in range(n):
        if matrix[row][col]:
            x = OX + col * M
            y = OY + row * M
            draw.rounded_rectangle(
                [x, y, x + M, y + M],
                radius=int(M * 0.24),
                fill=INK,
            )
            dark_modules.append((col, row))


def draw_eye(col0: int, row0: int) -> None:
    """A rounded finder eye that keeps the standard 7-5-3 structure."""
    x0 = OX + col0 * M
    y0 = OY + row0 * M

    # 7 x 7 outer ring
    draw.rounded_rectangle(
        [x0, y0, x0 + 7 * M, y0 + 7 * M],
        radius=int(M * 1.55),
        fill=INK,
    )
    # 5 x 5 light ring
    draw.rounded_rectangle(
        [x0 + M, y0 + M, x0 + 6 * M, y0 + 6 * M],
        radius=int(M * 1.12),
        fill=IVORY,
    )
    # 3 x 3 dark centre
    draw.rounded_rectangle(
        [x0 + 2 * M, y0 + 2 * M, x0 + 5 * M, y0 + 5 * M],
        radius=int(M * 0.78),
        fill=INK,
    )


# Redraw the three functional eyes with the custom treatment.
for col0, row0 in ((0, 0), (n - 7, 0), (0, n - 7)):
    draw_eye(col0, row0)

# --- Centre medallion -------------------------------------------------------
# The canvas itself is the centre (the symbol sits inside a four-module quiet
# zone), so use the supersampled canvas centre rather than the matrix centre.
code_center_x = C / 2
code_center_y = C / 2

plaque_w = 480
plaque_h = 254
plaque_x0 = (FINAL - plaque_w) / 2
plaque_y0 = (FINAL - plaque_h) / 2
plaque_x1 = plaque_x0 + plaque_w
plaque_y1 = plaque_y0 + plaque_h

# A double gold rule around an ivory plaque. It covers ~6% of the symbol area,
# comfortably inside the 30% error-correction budget of level H.
rounded(plaque_x0, plaque_y0, plaque_x1, plaque_y1, 30, fill=IVORY)
rounded(
    plaque_x0 + 8,
    plaque_y0 + 8,
    plaque_x1 - 8,
    plaque_y1 - 8,
    24,
    outline=GOLD,
    width=2,
)
rounded(
    plaque_x0 + 16,
    plaque_y0 + 16,
    plaque_x1 - 16,
    plaque_y1 - 16,
    19,
    outline=GOLD,
    width=1,
)

# Monogram: 5 -> 1st, with a hand-drawn gold arrow (Georgia has no arrow glyph).
monogram_font = ImageFont.truetype(r"C:\Windows\Fonts\georgiaz.ttf", px(124))
caption_font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", px(22))

left, right = "5", "1st"
left_bbox = draw.textbbox((0, 0), left, font=monogram_font)
right_bbox = draw.textbbox((0, 0), right, font=monogram_font)
left_w = left_bbox[2] - left_bbox[0]
right_w = right_bbox[2] - right_bbox[0]
gap = px(78)
group_w = left_w + gap + right_w
group_x = code_center_x - group_w / 2
mono_y = code_center_y - px(12)

draw.text((group_x, mono_y), left, font=monogram_font, fill=INK, anchor="lm")
right_x = group_x + left_w + gap
draw.text((right_x, mono_y), right, font=monogram_font, fill=INK, anchor="lm")

arrow_y = mono_y - px(2)
arrow_x0 = group_x + left_w + px(12)
arrow_x1 = right_x - px(14)
draw.line([arrow_x0, arrow_y, arrow_x1, arrow_y], fill=GOLD, width=px(4))
head = px(15)
draw.polygon(
    [
        (arrow_x1, arrow_y),
        (arrow_x1 - head, arrow_y - head * 0.62),
        (arrow_x1 - head, arrow_y + head * 0.62),
    ],
    fill=GOLD,
)

caption = "O F F I C I A L   P R O G R A M M E"
cbbox = draw.textbbox((0, 0), caption, font=caption_font)
cw = cbbox[2] - cbbox[0]
draw.text(
    (code_center_x - cw / 2 - cbbox[0], code_center_y + px(54)),
    caption,
    font=caption_font,
    fill=GOLD,
)

# --- Export raster files ----------------------------------------------------
master = img.resize((FINAL, FINAL), Image.LANCZOS)
web = master.resize((1200, 1200), Image.LANCZOS)
print_version = master.resize((2000, 2000), Image.LANCZOS)

web.save(ASSETS / "qr-code.png", optimize=True)
print_version.save(ASSETS / "qr-code-print.png", optimize=True)

# --- Export a clean, editable SVG ------------------------------------------
parts = [
    '<?xml version="1.0" encoding="UTF-8"?>',
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{FINAL}" height="{FINAL}" '
    f'viewBox="0 0 {FINAL} {FINAL}" role="img" '
    f'aria-labelledby="qrTitle qrDesc">',
    "<title id=\"qrTitle\">Official programme QR code</title>",
    f'<desc id="qrDesc">Scan to open the book launch programme at {URL}</desc>',
    f'<rect width="{FINAL}" height="{FINAL}" fill="{IVORY}"/>',
    f'<rect x="26" y="26" width="{FINAL - 52}" height="{FINAL - 52}" rx="18" '
    f'fill="none" stroke="{GOLD}" stroke-width="2"/>',
    f'<rect x="36" y="36" width="{FINAL - 72}" height="{FINAL - 72}" rx="12" '
    f'fill="none" stroke="{GOLD}" stroke-width="1"/>',
]

# decorative corner ticks
for cx, cy, sx, sy in (
    (mark_gap, mark_gap, 1, 1),
    (FINAL - mark_gap, mark_gap, -1, 1),
    (mark_gap, FINAL - mark_gap, 1, -1),
    (FINAL - mark_gap, FINAL - mark_gap, -1, -1),
):
    parts.append(
        f'<path d="M {cx} {cy} h {sx * mark_len} M {cx} {cy} v {sy * mark_len}" '
        f'stroke="{GOLD}" stroke-width="2" fill="none"/>'
    )

# Modules (skip the three finder areas, drawn separately below)
eye_cells = set()
for col0, row0 in ((0, 0), (n - 7, 0), (0, n - 7)):
    for r in range(row0, row0 + 7):
        for c in range(col0, col0 + 7):
            eye_cells.add((c, r))

for col, row in dark_modules:
    if (col, row) in eye_cells:
        continue
    x = OFFSET + col * MODULE
    y = OFFSET + row * MODULE
    parts.append(
        f'<rect x="{x}" y="{y}" width="{MODULE}" height="{MODULE}" '
        f'rx="{int(MODULE * 0.24)}" fill="{INK}"/>'
    )

# eyes
for col0, row0 in ((0, 0), (n - 7, 0), (0, n - 7)):
    x = OFFSET + col0 * MODULE
    y = OFFSET + row0 * MODULE
    parts.append(f'<g>')
    parts.append(
        f'<rect x="{x}" y="{y}" width="{7 * MODULE}" height="{7 * MODULE}" '
        f'rx="{int(MODULE * 1.55)}" fill="{INK}"/>'
    )
    parts.append(
        f'<rect x="{x + MODULE}" y="{y + MODULE}" width="{5 * MODULE}" '
        f'height="{5 * MODULE}" rx="{int(MODULE * 1.12)}" fill="{IVORY}"/>'
    )
    parts.append(
        f'<rect x="{x + 2 * MODULE}" y="{y + 2 * MODULE}" width="{3 * MODULE}" '
        f'height="{3 * MODULE}" rx="{int(MODULE * 0.78)}" fill="{INK}"/>'
    )
    parts.append("</g>")

parts.append(
    f'<rect x="{plaque_x0}" y="{plaque_y0}" width="{plaque_w}" height="{plaque_h}" '
    f'rx="30" fill="{IVORY}"/>'
)
parts.append(
    f'<rect x="{plaque_x0 + 8}" y="{plaque_y0 + 8}" width="{plaque_w - 16}" '
    f'height="{plaque_h - 16}" rx="24" fill="none" stroke="{GOLD}" stroke-width="2"/>'
)
parts.append(
    f'<rect x="{plaque_x0 + 16}" y="{plaque_y0 + 16}" width="{plaque_w - 32}" '
    f'height="{plaque_h - 32}" rx="19" fill="none" stroke="{GOLD}" stroke-width="1"/>'
)
parts.append(
    f'<text x="909" y="1055" text-anchor="middle" '
    f'font-family="Georgia, \'Times New Roman\', serif" '
    f'font-style="italic" font-weight="700" font-size="124" fill="{INK}">5</text>'
)
parts.append(
    f'<text x="1098" y="1055" text-anchor="middle" '
    f'font-family="Georgia, \'Times New Roman\', serif" '
    f'font-style="italic" font-weight="700" font-size="124" fill="{INK}">1st</text>'
)
parts.append(
    f'<path d="M 956 1010 H 1009" stroke="{GOLD}" stroke-width="4" fill="none"/>'
)
parts.append(
    f'<polygon points="1009,1010 994,1019 994,1001" fill="{GOLD}"/>'
)
parts.append(
    f'<text x="{FINAL / 2}" y="1096" text-anchor="middle" '
    f'font-family="Segoe UI, Arial, sans-serif" '
    f'font-weight="700" font-size="22" letter-spacing="4" fill="{GOLD}">OFFICIAL PROGRAMME</text>'
)
parts.append("</svg>")

(ASSETS / "qr-code.svg").write_text("\n".join(parts), encoding="utf-8")

print(f"URL: {URL}")
print(f"QR version: {qr.version}  modules: {n}x{n}")
print(f"Wrote: {ASSETS / 'qr-code.png'}")
print(f"Wrote: {ASSETS / 'qr-code-print.png'}")
print(f"Wrote: {ASSETS / 'qr-code.svg'}")
