#!/usr/bin/env python3
"""
Convert a portrait photo into a CLEAN, monochrome ASCII-art SVG that "types"
itself in like a terminal, then holds.
"""
from PIL import Image, ImageEnhance, ImageFilter
import html
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "vanz-ascii.svg")

COLS = 100
ROWS = 53
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright(sparse) -> dark(dense); leading space clears bg

CONTRAST = 1.05
BRIGHTNESS = 1.0
GAMMA = 1.18
SHARPEN = False
WHITE_FLOOR = 0.80

PAD = 20
TITLEBAR_H = 30
STATUS_H = 30
ART_W = COLS * CELL_W
ART_H = ROWS * CELL_H
CANVAS_W = ART_W + PAD * 2
CANVAS_H = TITLEBAR_H + ART_H + STATUS_H + PAD

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"
INK = "#c9d1d9"
CURSOR = "#c9d1d9"

ROW_DUR = 0.11
STAGGER = 0.11

im = Image.open(SRC).convert("L")
if SHARPEN:
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))
im = ImageEnhance.Brightness(im).enhance(BRIGHTNESS)
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

STATIC = bool(os.environ.get("STATIC"))

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = px[x, y] / 255.0
        lum = pow(lum, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = int((1.0 - lum) * (len(RAMP) - 1))
        idx = max(0, min(len(RAMP) - 1, idx))
        chars.append(RAMP[idx])
    
    line = "".join(chars)
    # Right-trim whitespace to save bytes and prevent bounding-box issues
    line = line.rstrip()
    rows_txt.append(line)

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
           f'width="{CANVAS_W}" height="{CANVAS_H}" font-family="monospace">')

css = """
@keyframes wipe {
  0%   { width: 0; }
  100% { width: 100%; }
}
@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.row {
  white-space: pre;
}
"""
svg.append(f'<style>{css}</style>')

# Window background and frame
svg.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="{BG}"/>')
svg.append(f'<rect x="1" y="1" width="{CANVAS_W-2}" height="{CANVAS_H-2}" rx="11" fill="none" stroke="{FRAME}"/>')
svg.append(f'<rect x="0" y="0" width="{CANVAS_W}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>')
svg.append(f'<rect x="0" y="16" width="{CANVAS_W}" height="{TITLEBAR_H-16}" fill="{BG2}"/>')

# Mac window dots
dots_y = TITLEBAR_H // 2
for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    svg.append(f'<circle cx="{PAD + i * 20}" cy="{dots_y}" r="5" fill="{color}"/>')

svg.append(f'<text x="{CANVAS_W//2}" y="{dots_y + 4}" text-anchor="middle" fill="{TITLE_TEXT}" font-size="11">vanz-0 — photo.jpg</text>')

# Content bounds
content_x = PAD
content_y = TITLEBAR_H + 20

total_dur = ROWS * STAGGER

# Define a clip path for each row so it wipes in
svg.append('<defs>')
for i in range(ROWS):
    if STATIC:
        # If static, just show it
        pass
    else:
        # A rectangle that grows from 0 to 100% width
        begin = i * STAGGER
        svg.append(f'<clipPath id="clip-{i}">')
        svg.append(f'  <rect x="0" y="0" height="{CELL_H + 5}" width="0">')
        svg.append(f'    <animate attributeName="width" from="0" to="{ART_W}" dur="{ROW_DUR}s" '
                   f'begin="{begin}s" fill="freeze" />')
        svg.append(f'  </rect>')
        svg.append(f'</clipPath>')
svg.append('</defs>')

svg.append(f'<g transform="translate({content_x}, {content_y})" font-size="13" fill="{INK}">')
for i, text in enumerate(rows_txt):
    if not text:
        continue
    y = i * CELL_H
    escaped = html.escape(text).replace(" ", "&#160;")
    clip_attr = "" if STATIC else f'clip-path="url(#clip-{i})"'
    # The text line
    svg.append(f'<text x="0" y="{y}" {clip_attr} class="row">{escaped}</text>')

    if not STATIC:
        # The cursor that rides the edge of the wipe
        begin = i * STAGGER
        svg.append(f'<rect x="0" y="{y - CELL_H + 4}" width="7" height="{CELL_H - 2}" fill="{CURSOR}" opacity="0">')
        # Appear when this row starts
        svg.append(f'  <set attributeName="opacity" to="1" begin="{begin}s" />')
        # Move across
        svg.append(f'  <animate attributeName="x" from="0" to="{len(text)*CELL_W}" dur="{ROW_DUR}s" begin="{begin}s" fill="freeze" />')
        # Disappear when this row is done, unless it\'s the last row
        if i < ROWS - 1:
            svg.append(f'  <set attributeName="opacity" to="0" begin="{begin + ROW_DUR}s" />')
        else:
            # Last row cursor blinks
            svg.append(f'  <animate attributeName="opacity" values="1;0;1" dur="1s" begin="{begin + ROW_DUR}s" repeatCount="indefinite" />')
        svg.append(f'</rect>')

svg.append('</g>')
svg.append('</svg>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print(f"Wrote ASCII SVG to {OUT}")
