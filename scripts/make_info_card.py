#!/usr/bin/env python3
"""
Build a neofetch-style info card SVG.
"""
import os
import html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")

PAD = 20
TITLEBAR_H = 30
CANVAS_W = 490
CANVAS_H = 845  # Align with portrait height

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
TITLE_TEXT = "#7d8590"

TEXT = "#c9d1d9"
LABEL = "#22d3ee"  # Cyan label
SEP = "#7d8590"

LINE_H = 26
STAGGER = 0.3
DUR = 0.5

INFO = [
    ("Name", "vanz-0"),
    ("Role", "Web Development, Security, API, AI Automation"),
    ("Stack", "Python, JS, Node, APIs"),
    ("Focus", "Building secure, automated systems"),
]

STATIC = bool(os.environ.get("STATIC"))

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" '
           f'width="{CANVAS_W}" height="{CANVAS_H}" font-family="monospace">')

css = """
@keyframes slideFade {
  0% { opacity: 0; transform: translateX(-10px); }
  100% { opacity: 1; transform: translateX(0); }
}
.line {
  opacity: 0;
  animation: slideFade 0.5s ease-out forwards;
}
"""
svg.append(f'<style>{css}</style>')

# Window background and frame
svg.append(f'<rect width="{CANVAS_W}" height="{CANVAS_H}" rx="12" fill="{BG}"/>')
svg.append(f'<rect x="1" y="1" width="{CANVAS_W-2}" height="{CANVAS_H-2}" rx="11" fill="none" stroke="{FRAME}"/>')
svg.append(f'<rect x="0" y="0" width="{CANVAS_W}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>')
svg.append(f'<rect x="0" y="16" width="{CANVAS_W}" height="{TITLEBAR_H-16}" fill="{BG2}"/>')

dots_y = TITLEBAR_H // 2
for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    svg.append(f'<circle cx="{PAD + i * 20}" cy="{dots_y}" r="5" fill="{color}"/>')

svg.append(f'<text x="{CANVAS_W//2}" y="{dots_y + 4}" text-anchor="middle" fill="{TITLE_TEXT}" font-size="11">vanz-0 — system_info</text>')

content_x = PAD + 20
content_y = TITLEBAR_H + 40

svg.append(f'<g transform="translate({content_x}, {content_y})" font-size="14">')

# Header
svg.append(f'<text x="0" y="0" fill="{TEXT}" font-weight="bold" class="line" style="animation-delay: 0s;">vanz-0@github</text>')
svg.append(f'<text x="0" y="{LINE_H*0.5}" fill="{SEP}" class="line" style="animation-delay: {STAGGER}s;">-------------------</text>')

y = LINE_H * 2
for i, (label, value) in enumerate(INFO):
    delay = (i + 2) * STAGGER
    
    anim_style = "" if STATIC else f'style="animation-delay: {delay}s;"'
    
    svg.append(f'<g class="line" {anim_style}>')
    svg.append(f'  <text x="0" y="{y}" fill="{LABEL}">{html.escape(label)}</text>')
    svg.append(f'  <text x="{len(label)*8 + 10}" y="{y}" fill="{SEP}">:</text>')
    svg.append(f'  <text x="120" y="{y}" fill="{TEXT}">{html.escape(value)}</text>')
    svg.append(f'</g>')
    y += LINE_H * 1.5

svg.append('</g>')
svg.append('</svg>')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(svg))

print(f"Wrote Info Card SVG to {OUT}")
