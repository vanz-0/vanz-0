#!/usr/bin/env python3
"""
Render data/contributions.json as a GitHub-style contribution heatmap SVG:
53-week x 7-day grid of rounded colored boxes, revealed with a diagonal
slide-down animation (CSS keyframes, plays once then freezes), a Less->More
legend, and a real stats footer.
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# GitHub-ish green ramp: empty -> brightest
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 12
GAP = 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30

BG = "#0a0e14"
BG2 = "#0d1420"
FRAME = "#1f6feb"
MUTED = "#7d8590"
TEXT = "#e6edf3"
ACCENT = "#22d3ee"
GREEN = "#39d353"
GOLD = "#f2cc60"

# reveal timing (one-shot)
COL_T = 0.018
ROW_T = 0.045
CELL_DUR = 0.42


def level_for(count):
    if count == 0:
        return 0
    if count <= 5:
        return 1
    if count <= 15:
        return 2
    if count <= 30:
        return 3
    if count <= 50:
        return 4
    return 5


def build_grid(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    lead_pad = (first.weekday() + 1) % 7  # sunday=0
    grid = []
    col = [None] * lead_pad
    for d in days:
        date = datetime.date.fromisoformat(d["date"])
        weekday = (date.weekday() + 1) % 7
        while len(col) < weekday:
            col.append(None)
        col.append((d["date"], d["count"], level_for(d["count"])))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        grid.append(col)
    return grid


def render(data):
    days = data["days"]
    stats = data.get("stats", {})
    grid = build_grid(days)
    n_cols = len(grid)
    art_w = n_cols * STEP
    art_h = 7 * STEP

    month_labels = []
    seen_months = set()
    for ci, column in enumerate(grid):
        for cell in column:
            if cell is None:
                continue
            date = datetime.date.fromisoformat(cell[0])
            key = (date.year, date.month)
            if key not in seen_months and date.day <= 7:
                seen_months.add(key)
                month_labels.append((ci, date.strftime("%b")))
            break

    canvas_w = PAD + LEFT_LABEL_W + art_w + PAD
    stats_h = 88
    canvas_h = TITLEBAR_H + TOP_LABEL_H + art_h + stats_h + PAD

    css = f"""
@keyframes cell {{
  0%   {{ opacity: 0; transform: translateY(-6px); }}
  100% {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes fadeIn {{
  0%   {{ opacity: 0; }}
  100% {{ opacity: 1; }}
}}
.cell {{
  opacity: 0;
  animation-fill-mode: forwards;
  animation-timing-function: ease-out;
}}
.legend-item {{
  opacity: 0;
  animation: fadeIn 0.5s ease-out forwards;
  animation-delay: 3.5s;
}}
.stats-text {{
  opacity: 0;
  animation: fadeIn 0.6s ease-out forwards;
  animation-delay: 3.2s;
}}
"""

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_w} {canvas_h}" '
                 f'width="{canvas_w}" height="{canvas_h}" font-family="monospace">')
    parts.append(f"<style>{css}</style>")

    # background
    parts.append(f'<rect width="{canvas_w}" height="{canvas_h}" rx="12" fill="{BG}"/>')
    parts.append(f'<rect x="1" y="1" width="{canvas_w-2}" height="{canvas_h-2}" rx="11" '
                 f'fill="none" stroke="{FRAME}" stroke-opacity="0.3"/>')

    # titlebar
    parts.append(f'<rect x="0" y="0" width="{canvas_w}" height="{TITLEBAR_H}" rx="12" fill="{BG2}"/>')
    parts.append(f'<rect x="0" y="16" width="{canvas_w}" height="{TITLEBAR_H - 16}" fill="{BG2}"/>')
    dots_y = TITLEBAR_H // 2
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        parts.append(f'<circle cx="{PAD + i * 20}" cy="{dots_y}" r="5" fill="{color}"/>')
    parts.append(f'<text x="{canvas_w//2}" y="{dots_y + 4}" text-anchor="middle" '
                 f'fill="{MUTED}" font-size="11">vanz-0 — contributions</text>')

    # day labels
    day_labels = ["", "Mon", "", "Wed", "", "Fri", ""]
    grid_x0 = PAD + LEFT_LABEL_W
    grid_y0 = TITLEBAR_H + TOP_LABEL_H

    for i, label in enumerate(day_labels):
        if label:
            y = grid_y0 + i * STEP + CELL * 0.75
            parts.append(f'<text x="{PAD + LEFT_LABEL_W - 6}" y="{y}" text-anchor="end" '
                         f'fill="{MUTED}" font-size="9" class="stats-text">{label}</text>')

    # month labels
    for ci, label in month_labels:
        x = grid_x0 + ci * STEP
        parts.append(f'<text x="{x}" y="{TITLEBAR_H + TOP_LABEL_H - 6}" '
                     f'fill="{MUTED}" font-size="9" class="stats-text">{label}</text>')

    # grid cells
    for ci, column in enumerate(grid):
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            _, count, lvl = cell
            x = grid_x0 + ci * STEP
            y = grid_y0 + ri * STEP
            color = PALETTE[lvl]
            delay = ci * COL_T + ri * ROW_T
            parts.append(f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                         f'rx="2" fill="{color}" '
                         f'style="animation: cell {CELL_DUR}s ease-out {delay:.3f}s forwards;">'
                         f'<title>{cell[0]}: {count} contributions</title></rect>')

    # stats footer
    total = stats.get("total", sum(d["count"] for d in days))
    current_streak = stats.get("current_streak", 0)
    longest_streak = stats.get("longest_streak", 0)

    footer_y = grid_y0 + art_h + 16

    # Legend
    legend_x = grid_x0
    parts.append(f'<text x="{legend_x}" y="{footer_y}" fill="{MUTED}" font-size="10" '
                 f'class="legend-item">Less</text>')
    for i, color in enumerate(PALETTE):
        bx = legend_x + 30 + i * (CELL + 3)
        parts.append(f'<rect class="legend-item" x="{bx}" y="{footer_y - 10}" '
                     f'width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{legend_x + 30 + len(PALETTE) * (CELL + 3) + 4}" y="{footer_y}" '
                 f'fill="{MUTED}" font-size="10" class="legend-item">More</text>')

    # Stats line
    stats_y = footer_y + 28
    parts.append(f'<text x="{grid_x0}" y="{stats_y}" fill="{GREEN}" font-size="13" '
                 f'font-weight="bold" class="stats-text">{total:,}</text>')
    parts.append(f'<text x="{grid_x0 + len(str(total)) * 9 + 8}" y="{stats_y}" '
                 f'fill="{TEXT}" font-size="12" class="stats-text">contributions in the last year</text>')

    stats_y2 = stats_y + 22
    parts.append(f'<text x="{grid_x0}" y="{stats_y2}" fill="{MUTED}" font-size="10" class="stats-text">'
                 f'🔥 Current streak: </text>')
    parts.append(f'<text x="{grid_x0 + 120}" y="{stats_y2}" fill="{GOLD}" font-size="10" '
                 f'font-weight="bold" class="stats-text">{current_streak} days</text>')
    parts.append(f'<text x="{grid_x0 + 220}" y="{stats_y2}" fill="{MUTED}" font-size="10" class="stats-text">'
                 f'⚡ Longest: </text>')
    parts.append(f'<text x="{grid_x0 + 300}" y="{stats_y2}" fill="{GOLD}" font-size="10" '
                 f'font-weight="bold" class="stats-text">{longest_streak} days</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    with open(IN_PATH) as f:
        data = json.load(f)
    svg = render(data)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
