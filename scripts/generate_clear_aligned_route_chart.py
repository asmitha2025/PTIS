from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "clear_aligned"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
BG = "#f8fafc"
PANEL = "#ffffff"
INK = "#0f172a"
MUTED = "#64748b"
SUBTLE = "#dbe5ef"
GRID = "#e8eef5"
BLUE = "#2563eb"
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
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for p in candidates:
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


F = {
    "brand": font(24, True),
    "title": font(52, True),
    "subtitle": font(25, False),
    "section": font(30, True),
    "body": font(22, False),
    "body_b": font(22, True),
    "small": font(18, False),
    "small_b": font(18, True),
    "tiny": font(15, False),
    "metric": font(38, True),
}


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=INK, f=None, anchor=None):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor)


def text_width(draw: ImageDraw.ImageDraw, value: str, f) -> int:
    b = draw.textbbox((0, 0), str(value), font=f)
    return b[2] - b[0]


def wrap_lines(draw: ImageDraw.ImageDraw, value: str, f, max_width: int) -> list[str]:
    words = str(value).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if text_width(draw, candidate, f) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrapped(draw: ImageDraw.ImageDraw, xy, value: str, f, fill: str, max_width: int, gap: int = 4, max_lines: int | None = None):
    x, y = xy
    lines = wrap_lines(draw, value, f, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_width(draw, lines[-1] + "...", f) > max_width and " " in lines[-1]:
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


def route_projector(box):
    coords = route["features"][0]["geometry"]["coordinates"]
    projected = [mercator(float(lon), float(lat)) for lon, lat in coords]
    xs = [p[0] for p in projected]
    ys = [p[1] for p in projected]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    x1, y1, x2, y2 = box
    pad = 44
    sx = (x2 - x1 - 2 * pad) / max(max_x - min_x, 0.000001)
    sy = (y2 - y1 - 2 * pad) / max(max_y - min_y, 0.000001)
    scale = min(sx, sy)
    route_w = (max_x - min_x) * scale
    route_h = (max_y - min_y) * scale
    ox = x1 + (x2 - x1 - route_w) / 2
    oy = y1 + (y2 - y1 - route_h) / 2

    def project(lon: float, lat: float) -> tuple[float, float]:
        px, py = mercator(float(lon), float(lat))
        return ox + (px - min_x) * scale, oy + route_h - (py - min_y) * scale

    return [project(lon, lat) for lon, lat in coords], project


def draw_header(draw: ImageDraw.ImageDraw):
    text(draw, (72, 42), "PTIS v2.0", fill=TEAL, f=F["brand"])
    text(draw, (72, 82), "Bengaluru ORR route and validation chart", fill=INK, f=F["title"])
    wrapped(
        draw,
        (72, 148),
        "Real OSRM/OpenStreetMap route geometry plus reproducible replay evidence. This is software validation, not a live-traffic or field-impact claim.",
        F["subtitle"],
        MUTED,
        1310,
        5,
        max_lines=2,
    )


def marker(draw: ImageDraw.ImageDraw, point, number: str, color: str):
    px, py = point
    r = 18
    draw.ellipse((px - r - 5, py - r - 5, px + r + 5, py + r + 5), fill="white")
    draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
    text(draw, (px, py - 11), number, fill="white", f=F["small_b"], anchor="ma")


def waypoint_chip(draw: ImageDraw.ImageDraw, box, number: str, label: str, color: str):
    x1, y1, x2, y2 = box
    rounded(draw, box, 13, SOFT_SLATE, SUBTLE, 1)
    draw.ellipse((x1 + 18, y1 + 15, x1 + 48, y1 + 45), fill=color)
    text(draw, (x1 + 33, y1 + 22), number, fill="white", f=F["tiny"], anchor="ma")
    text(draw, (x1 + 62, y1 + 13), label, fill=INK, f=F["body_b"])
    text(draw, (x1 + 62, y1 + 39), "route waypoint", fill=MUTED, f=F["tiny"])


def draw_route_panel(draw: ImageDraw.ImageDraw):
    panel = (72, 218, 980, 720)
    rounded(draw, panel, 22, PANEL, SUBTLE, 2)
    px1, py1, px2, py2 = panel
    text(draw, (px1 + 32, py1 + 26), "Correct route", fill=INK, f=F["section"])
    text(draw, (px1 + 32, py1 + 64), "Silk Board -> Marathahalli -> Whitefield", fill=MUTED, f=F["body"])

    map_box = (px1 + 32, py1 + 106, px2 - 32, py1 + 374)
    rounded(draw, map_box, 16, "#eef5fa", "#d6e3ee", 1)
    x1, y1, x2, y2 = map_box
    for i in range(1, 9):
        x = x1 + i * (x2 - x1) / 9
        draw.line((x, y1 + 16, x, y2 - 16), fill=GRID, width=1)
    for i in range(1, 4):
        y = y1 + i * (y2 - y1) / 4
        draw.line((x1 + 16, y, x2 - 16, y), fill=GRID, width=1)

    pts, project = route_projector(map_box)
    draw.line(pts, fill="#b7c6d7", width=17, joint="curve")
    draw.line(pts, fill=BLUE, width=8, joint="curve")

    wp_by_id = {wp["id"]: wp for wp in route["waypoints"]}
    key_points = [
        ("1", "silk_board", BLUE),
        ("2", "marathahalli", AMBER),
        ("3", "whitefield", TEAL),
    ]
    for number, wp_id, color in key_points:
        wp = wp_by_id[wp_id]
        marker(draw, project(wp["lon"], wp["lat"]), number, color)

    chip_y = py1 + 402
    gap = 20
    chip_w = (px2 - px1 - 64 - 2 * gap) // 3
    chips = [
        ("1", "Silk Board", BLUE),
        ("2", "Marathahalli", AMBER),
        ("3", "Whitefield", TEAL),
    ]
    for i, chip in enumerate(chips):
        cx1 = px1 + 32 + i * (chip_w + gap)
        waypoint_chip(draw, (cx1, chip_y, cx1 + chip_w, chip_y + 62), *chip)

    info = f"OSRM/OpenStreetMap route | {route['distance_m'] / 1000:.1f} km | {route['coordinate_count']:,} route geometry points"
    text(draw, (px1 + 32, py2 - 34), info, fill=MUTED, f=F["small_b"])


def draw_chart_panel(draw: ImageDraw.ImageDraw):
    panel = (1020, 218, 1528, 720)
    rounded(draw, panel, 22, PANEL, SUBTLE, 2)
    x1, y1, x2, y2 = panel
    text(draw, (x1 + 32, y1 + 26), "Replay chart", fill=INK, f=F["section"])
    text(draw, (x1 + 32, y1 + 64), "8,000 vehicles by actual destination", fill=MUTED, f=F["body"])

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
    label_x = x1 + 32
    bar_x = x1 + 178
    value_x = x2 - 32
    chart_top = y1 + 118
    row_h = 45
    bar_w = value_x - bar_x - 76
    for i, (label, value, color) in enumerate(bars):
        y = chart_top + i * row_h
        text(draw, (label_x, y + 5), label, fill=INK, f=F["small_b"])
        rounded(draw, (bar_x, y + 8, bar_x + bar_w, y + 28), 10, "#e8eef5")
        fill_w = int(bar_w * value / max_v)
        rounded(draw, (bar_x, y + 8, bar_x + fill_w, y + 28), 10, color)
        text(draw, (value_x, y + 4), f"{value:,}", fill=SLATE, f=F["small_b"], anchor="ra")

    metrics = extreme["metrics"]
    card_y = y2 - 112
    card_gap = 16
    card_w = (x2 - x1 - 64 - card_gap) // 2
    rounded(draw, (x1 + 32, card_y, x1 + 32 + card_w, card_y + 78), 14, SOFT_GREEN, "#bbf7d0", 1)
    text(draw, (x1 + 54, card_y + 13), "0", fill=GREEN, f=F["metric"])
    text(draw, (x1 + 104, card_y + 20), "capacity\nviolations", fill=SLATE, f=F["tiny"])

    cx = x1 + 32 + card_w + card_gap
    rounded(draw, (cx, card_y, cx + card_w, card_y + 78), 14, SOFT_BLUE, "#bfdbfe", 1)
    text(draw, (cx + 22, card_y + 13), f"{metrics['observation_count']:,}", fill=BLUE, f=F["metric"])
    text(draw, (cx + 22, card_y + 54), "checkpoint observations", fill=SLATE, f=F["tiny"])

    text(draw, (x1 + 32, y2 - 24), f"{suite['passed_count']}/{suite['scenario_count']} scenarios passed | 29/29 tests passed", fill=MUTED, f=F["small_b"])


def draw_boundary(draw: ImageDraw.ImageDraw):
    box = (72, 748, 1528, 820)
    rounded(draw, box, 18, SOFT_AMBER, "#fed7aa", 2)
    text(draw, (104, 770), "Truth boundary", fill=AMBER, f=F["body_b"])
    wrapped(
        draw,
        (284, 768),
        "This proves reproducible software behavior on a grounded route. It does not claim live traffic control, field travel-time savings, or congestion reduction yet.",
        F["body"],
        "#92400e",
        1180,
        4,
        max_lines=2,
    )
    text(draw, (72, 850), "Software validated. Field validation pending.", fill=MUTED, f=F["small_b"])
    text(draw, (1528, 850), "PTIS / Bengaluru ORR", fill=MUTED, f=F["small"], anchor="ra")


def generate():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw_header(draw)
    draw_route_panel(draw)
    draw_chart_panel(draw)
    draw_boundary(draw)
    out = OUT / "ptis_clear_correct_aligned.png"
    img.save(out, quality=96)
    (OUT / "README.md").write_text(
        "# PTIS Clear Correct Aligned Asset\n\nUse `ptis_clear_correct_aligned.png` as the clean LinkedIn image. It has a fixed two-column grid: route on the left, replay chart on the right, and truth boundary below.\n",
        encoding="utf-8",
    )
    print(json.dumps({"image": str(out), "size": [W, H]}, indent=2))


if __name__ == "__main__":
    generate()