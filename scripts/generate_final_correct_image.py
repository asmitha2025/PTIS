from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "final_correct"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
BG = "#f8fafc"
CARD = "#ffffff"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#dbe5ef"
GRID = "#e8eef5"
BLUE = "#2563eb"
BLUE_D = "#1d4ed8"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
SLATE = "#334155"
SOFT_BLUE = "#eff6ff"
SOFT_GREEN = "#ecfdf5"
SOFT_AMBER = "#fff7ed"
SOFT_SLATE = "#f1f5f9"


def load_json(rel: str) -> dict[str, Any]:
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


route = load_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = load_json("evidence/extreme_batch_report.json")
suite = load_json("evidence/suite_report.json")


def font(size: int, bold: bool = False):
    paths = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for p in paths:
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


F = {
    "kicker": font(23, True),
    "title": font(50, True),
    "subtitle": font(24, False),
    "section": font(30, True),
    "body": font(21, False),
    "body_b": font(21, True),
    "small": font(17, False),
    "small_b": font(17, True),
    "tiny": font(14, False),
    "metric": font(38, True),
    "number": font(18, True),
}


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=INK, f=None, anchor=None):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor)


def tw(draw: ImageDraw.ImageDraw, value: str, f) -> int:
    b = draw.textbbox((0, 0), str(value), font=f)
    return b[2] - b[0]


def fit_text(draw: ImageDraw.ImageDraw, box, value: str, fonts, fill=INK, anchor=None):
    x1, y1, x2, y2 = box
    for f in fonts:
        if tw(draw, value, f) <= x2 - x1:
            text(draw, (x1, y1), value, fill=fill, f=f, anchor=anchor)
            return
    f = fonts[-1]
    value = str(value)
    while value and tw(draw, value + "...", f) > x2 - x1:
        value = value[:-1]
    text(draw, (x1, y1), value + "...", fill=fill, f=f, anchor=anchor)


def wrap(draw: ImageDraw.ImageDraw, value: str, f, max_width: int) -> list[str]:
    words = str(value).split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if tw(draw, trial, f) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrapped(draw: ImageDraw.ImageDraw, xy, value: str, f, fill: str, max_width: int, gap: int = 4, max_lines: int | None = None):
    x, y = xy
    lines = wrap(draw, value, f, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and tw(draw, lines[-1] + "...", f) > max_width and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        if lines:
            lines[-1] += "..."
    for line in lines:
        text(draw, (x, y), line, fill=fill, f=f)
        y += f.size + gap
    return y


def mercator(lon: float, lat: float) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    return lon, math.degrees(math.log(math.tan(math.pi / 4 + lat_rad / 2)))


def route_projection(box):
    coords = route["features"][0]["geometry"]["coordinates"]
    projected = [mercator(float(lon), float(lat)) for lon, lat in coords]
    xs = [p[0] for p in projected]
    ys = [p[1] for p in projected]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    x1, y1, x2, y2 = box
    pad = 44
    scale = min((x2 - x1 - pad * 2) / (max_x - min_x), (y2 - y1 - pad * 2) / (max_y - min_y))
    route_w = (max_x - min_x) * scale
    route_h = (max_y - min_y) * scale
    ox = x1 + (x2 - x1 - route_w) / 2
    oy = y1 + (y2 - y1 - route_h) / 2

    def project(lon, lat):
        px, py = mercator(float(lon), float(lat))
        return ox + (px - min_x) * scale, oy + route_h - (py - min_y) * scale

    return [project(lon, lat) for lon, lat in coords], project


def header(draw: ImageDraw.ImageDraw):
    text(draw, (72, 44), "PTIS v2.0", fill=TEAL, f=F["kicker"])
    text(draw, (72, 80), "Bengaluru ORR route + replay validation", fill=INK, f=F["title"])
    wrapped(
        draw,
        (72, 144),
        "Correct OSRM/OpenStreetMap route geometry for Silk Board to Whitefield, paired with reproducible software replay evidence.",
        F["subtitle"],
        MUTED,
        1280,
        5,
        max_lines=2,
    )


def draw_map_panel(draw: ImageDraw.ImageDraw):
    panel = (72, 214, 996, 696)
    rounded(draw, panel, 22, CARD, LINE, 2)
    x1, y1, x2, y2 = panel
    text(draw, (x1 + 32, y1 + 24), "Correct route", fill=INK, f=F["section"])
    text(draw, (x1 + 32, y1 + 62), "Real routed road geometry, not a straight-line sketch", fill=MUTED, f=F["body"])

    map_box = (x1 + 32, y1 + 104, x2 - 32, y1 + 350)
    rounded(draw, map_box, 16, "#eef5fa", "#d7e3ee", 1)
    mx1, my1, mx2, my2 = map_box
    for i in range(1, 9):
        xx = mx1 + i * (mx2 - mx1) / 9
        draw.line((xx, my1 + 14, xx, my2 - 14), fill=GRID, width=1)
    for i in range(1, 4):
        yy = my1 + i * (my2 - my1) / 4
        draw.line((mx1 + 14, yy, mx2 - 14, yy), fill=GRID, width=1)

    pts, project = route_projection(map_box)
    draw.line(pts, fill="#b8c7d6", width=17, joint="curve")
    draw.line(pts, fill=BLUE, width=8, joint="curve")

    colors = [BLUE, SLATE, SLATE, AMBER, SLATE, SLATE, TEAL]
    for idx, wp in enumerate(route["waypoints"], start=1):
        px, py = project(wp["lon"], wp["lat"])
        color = colors[idx - 1]
        r = 13 if idx in {1, 4, 7} else 9
        draw.ellipse((px - r - 4, py - r - 4, px + r + 4, py + r + 4), fill="white")
        draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
        if idx in {1, 4, 7}:
            text(draw, (px, py - 10), str(idx), fill="white", f=F["tiny"], anchor="ma")

    # Aligned route sequence legend.
    legend_y = y1 + 380
    names = ["Silk Board", "HSR", "Sony", "Marathahalli", "Doddanekkundi", "ITPL", "Whitefield"]
    col_gap = 8
    col_w = (x2 - x1 - 64 - col_gap * 6) / 7
    for i, name in enumerate(names, start=1):
        lx = x1 + 32 + (i - 1) * (col_w + col_gap)
        color = colors[i - 1]
        rounded(draw, (lx, legend_y, lx + col_w, legend_y + 58), 12, SOFT_SLATE, LINE, 1)
        draw.ellipse((lx + 10, legend_y + 16, lx + 36, legend_y + 42), fill=color)
        text(draw, (lx + 23, legend_y + 21), str(i), fill="white", f=F["tiny"], anchor="ma")
        fit_text(draw, (lx + 43, legend_y + 16, lx + col_w - 8, legend_y + 38), name, [F["small_b"], F["tiny"]], INK)

    text(draw, (x1 + 32, y2 - 32), f"{route['distance_m'] / 1000:.1f} km | {route['coordinate_count']:,} geometry points | source: OSRM/OpenStreetMap", fill=MUTED, f=F["small_b"])


def draw_chart_panel(draw: ImageDraw.ImageDraw):
    panel = (1036, 214, 1528, 696)
    rounded(draw, panel, 22, CARD, LINE, 2)
    x1, y1, x2, y2 = panel
    text(draw, (x1 + 32, y1 + 24), "Replay chart", fill=INK, f=F["section"])
    text(draw, (x1 + 32, y1 + 62), "Actual destinations in 8,000-vehicle stress replay", fill=MUTED, f=F["body"])

    counts = extreme["metrics"]["actual_destination_counts"]
    bars = [
        ("HSR Layout", counts["hsr_layout"], BLUE),
        ("Sony World", counts["sony_world"], BLUE),
        ("Marathahalli", counts["marathahalli"], AMBER),
        ("Whitefield", counts["whitefield"], GREEN),
        ("ITPL", counts["itpl"], TEAL),
        ("Doddanekkundi", counts["doddanekkundi"], TEAL),
    ]
    max_v = max(v for _, v, _ in bars)
    total = sum(v for _, v, _ in bars)
    label_x = x1 + 32
    bar_x = x1 + 174
    value_x = x2 - 32
    bar_w = value_x - bar_x - 88
    start_y = y1 + 118
    row_h = 44
    for idx, (label, value, color) in enumerate(bars):
        yy = start_y + idx * row_h
        fit_text(draw, (label_x, yy + 6, bar_x - 10, yy + 24), label, [F["small_b"], F["tiny"]], INK)
        rounded(draw, (bar_x, yy + 8, bar_x + bar_w, yy + 28), 10, "#e8eef5")
        fill_w = max(5, int(bar_w * value / max_v))
        rounded(draw, (bar_x, yy + 8, bar_x + fill_w, yy + 28), 10, color)
        pct = value / total * 100
        text(draw, (value_x, yy + 4), f"{value:,} ({pct:.1f}%)", fill=SLATE, f=F["small_b"], anchor="ra")

    metrics = extreme["metrics"]
    card_y = y2 - 116
    card_w = (x2 - x1 - 64 - 14) / 2
    rounded(draw, (x1 + 32, card_y, x1 + 32 + card_w, card_y + 82), 14, SOFT_GREEN, "#bbf7d0", 1)
    text(draw, (x1 + 54, card_y + 14), "0", fill=GREEN, f=F["metric"])
    text(draw, (x1 + 104, card_y + 23), "capacity\nviolations", fill=SLATE, f=F["tiny"])

    cx = x1 + 32 + card_w + 14
    rounded(draw, (cx, card_y, cx + card_w, card_y + 82), 14, SOFT_BLUE, "#bfdbfe", 1)
    text(draw, (cx + 22, card_y + 12), f"{metrics['observation_count']:,}", fill=BLUE_D, f=F["metric"])
    text(draw, (cx + 22, card_y + 54), "checkpoint observations", fill=SLATE, f=F["tiny"])

    text(draw, (x1 + 32, y2 - 24), f"{suite['passed_count']}/{suite['scenario_count']} scenarios passed | 29/29 tests passed", fill=MUTED, f=F["small_b"])


def metric_strip(draw: ImageDraw.ImageDraw):
    y = 722
    x = 72
    gap = 18
    w = (1528 - 72 - gap * 3) / 4
    items = [
        ("8,000", "vehicles replayed", BLUE),
        ("23,314", "checkpoint events", TEAL),
        ("0", "capacity violations", GREEN),
        ("29/29", "tests passed", GREEN),
    ]
    for i, (value, label, color) in enumerate(items):
        x1 = x + i * (w + gap)
        rounded(draw, (x1, y, x1 + w, y + 78), 16, CARD, LINE, 2)
        text(draw, (x1 + 24, y + 14), value, fill=color, f=F["metric"])
        text(draw, (x1 + 24, y + 53), label, fill=MUTED, f=F["small_b"])


def boundary(draw: ImageDraw.ImageDraw):
    y = 822
    text(draw, (72, y), "Truth boundary:", fill=AMBER, f=F["small_b"])
    text(draw, (210, y), "Software validated. Field validation pending. No live-traffic control or congestion-reduction claim.", fill=MUTED, f=F["small_b"])
    text(draw, (1528, y), "PTIS / Bengaluru ORR", fill=MUTED, f=F["small"], anchor="ra")


def generate():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw)
    draw_map_panel(draw)
    draw_chart_panel(draw)
    metric_strip(draw)
    boundary(draw)
    out = OUT / "ptis_final_correct_route_chart.png"
    img.save(out, quality=96)
    (OUT / "README.md").write_text(
        "# PTIS Final Correct Image\n\nUse `ptis_final_correct_route_chart.png` for the LinkedIn post. It contains the corrected route, replay destination chart, proof metrics, and a compact truth boundary.\n",
        encoding="utf-8",
    )
    print(json.dumps({"image": str(out), "size": [W, H]}, indent=2))


if __name__ == "__main__":
    generate()