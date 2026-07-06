from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "clean_post"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
BG = "#f8fafc"
PANEL = "#ffffff"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#d9e3ee"
GRID = "#e7edf4"
BLUE = "#2563eb"
BLUE_2 = "#1d4ed8"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
SLATE = "#334155"
SOFT_BLUE = "#eff6ff"
SOFT_TEAL = "#ecfdf5"
SOFT_AMBER = "#fff7ed"


def read_json(rel: str) -> dict[str, Any]:
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


route = read_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = read_json("evidence/extreme_batch_report.json")
suite = read_json("evidence/suite_report.json")
cctv = read_json("evidence/cctv_bmd45_report.json")


def font(size: int, bold: bool = False):
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


F = {
    "brand": font(24, True),
    "title": font(54, True),
    "subtitle": font(27, False),
    "h2": font(32, True),
    "h3": font(25, True),
    "body": font(23, False),
    "body_b": font(23, True),
    "small": font(19, False),
    "small_b": font(19, True),
    "tiny": font(16, False),
    "metric": font(42, True),
}


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=INK, f=None, anchor=None):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor)


def text_w(draw: ImageDraw.ImageDraw, value: str, f) -> int:
    b = draw.textbbox((0, 0), str(value), font=f)
    return b[2] - b[0]


def wrap_lines(draw: ImageDraw.ImageDraw, value: str, f, max_width: int) -> list[str]:
    words = str(value).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if text_w(draw, candidate, f) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrapped(draw: ImageDraw.ImageDraw, xy, value: str, f, fill: str, max_width: int, gap: int = 5, max_lines: int | None = None):
    x, y = xy
    lines = wrap_lines(draw, value, f, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_w(draw, lines[-1] + "...", f) > max_width and " " in lines[-1]:
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
    pad = 58
    sx = (x2 - x1 - 2 * pad) / max(0.000001, max_x - min_x)
    sy = (y2 - y1 - 2 * pad) / max(0.000001, max_y - min_y)
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
    text(draw, (72, 48), "PTIS v2.0", fill=TEAL, f=F["brand"])
    text(draw, (72, 88), "Bengaluru ORR: route + validation chart", fill=INK, f=F["title"])
    wrapped(
        draw,
        (72, 156),
        "Correct OSRM/OpenStreetMap route geometry for Silk Board to Whitefield, paired with reproducible replay evidence. Software validated; field validation pending.",
        F["subtitle"],
        MUTED,
        1320,
        6,
        max_lines=2,
    )


def draw_label(draw: ImageDraw.ImageDraw, point, label: str, box, color: str):
    px, py = point
    x1, y1, x2, y2 = box
    w, h = 220, 48
    # Keep labels on fixed sides so the route never looks messy.
    if label == "Silk Board":
        lx, ly = x1 + 92, y2 - 88
    elif label == "Marathahalli":
        lx, ly = x2 - 350, y1 + 250
    else:
        lx, ly = x2 - 300, y1 + 106
    draw.line((px, py, lx, ly + h / 2), fill="#a8b6c6", width=2)
    rounded(draw, (lx, ly, lx + w, ly + h), 11, "#ffffff", "#d7e2ec", 1)
    draw.ellipse((lx + 15, ly + 16, lx + 31, ly + 32), fill=color)
    text(draw, (lx + 42, ly + 12), label, fill=INK, f=F["small_b"])


def draw_route_panel(draw: ImageDraw.ImageDraw):
    panel = (72, 236, 980, 708)
    rounded(draw, panel, 22, PANEL, LINE, 2)
    text(draw, (104, 266), "Real route geometry", fill=INK, f=F["h2"])
    text(draw, (104, 306), "Silk Board -> Marathahalli -> Whitefield", fill=MUTED, f=F["body"])

    map_box = (104, 350, 948, 660)
    rounded(draw, map_box, 18, "#eef5fa", "#d8e5ef", 1)
    x1, y1, x2, y2 = map_box
    for i in range(1, 9):
        x = x1 + i * (x2 - x1) / 9
        draw.line((x, y1 + 18, x, y2 - 18), fill=GRID, width=1)
    for i in range(1, 5):
        y = y1 + i * (y2 - y1) / 5
        draw.line((x1 + 18, y, x2 - 18, y), fill=GRID, width=1)

    pts, project = route_projector(map_box)
    draw.line(pts, fill="#b8c7d6", width=16, joint="curve")
    draw.line(pts, fill=BLUE, width=7, joint="curve")

    important = {
        "silk_board": ("Silk Board", BLUE),
        "marathahalli": ("Marathahalli", AMBER),
        "whitefield": ("Whitefield", TEAL),
    }
    for wp in route["waypoints"]:
        px, py = project(wp["lon"], wp["lat"])
        if wp["id"] in important:
            label, color = important[wp["id"]]
            r = 13
            draw.ellipse((px - r - 5, py - r - 5, px + r + 5, py + r + 5), fill="white")
            draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
            draw_label(draw, (px, py), label, map_box, color)
        else:
            draw.ellipse((px - 6, py - 6, px + 6, py + 6), fill=SLATE, outline="white", width=2)

    distance_km = route["distance_m"] / 1000
    bottom = f"{distance_km:.1f} km OSRM route | {route['coordinate_count']:,} geometry points | route reference, not live traffic"
    text(draw, (104, 674), bottom, fill=MUTED, f=F["small_b"])


def draw_bar_chart(draw: ImageDraw.ImageDraw):
    panel = (1020, 236, 1528, 708)
    rounded(draw, panel, 22, PANEL, LINE, 2)
    x1, y1, x2, y2 = panel
    text(draw, (x1 + 32, y1 + 30), "Worst-case replay chart", fill=INK, f=F["h2"])
    text(draw, (x1 + 32, y1 + 70), "8,000 vehicles by actual destination", fill=MUTED, f=F["body"])

    counts = extreme["metrics"]["actual_destination_counts"]
    labels = [
        ("HSR", counts["hsr_layout"], BLUE),
        ("Sony", counts["sony_world"], BLUE),
        ("Marathahalli", counts["marathahalli"], AMBER),
        ("Doddanekkundi", counts["doddanekkundi"], TEAL),
        ("ITPL", counts["itpl"], TEAL),
        ("Whitefield", counts["whitefield"], GREEN),
    ]
    max_count = max(v for _, v, _ in labels)
    chart_x = x1 + 142
    chart_y = y1 + 132
    chart_w = 285
    row_h = 47
    for i, (label, value, color) in enumerate(labels):
        y = chart_y + i * row_h
        text(draw, (x1 + 32, y + 8), label, fill=INK, f=F["small_b"])
        rounded(draw, (chart_x, y + 9, chart_x + chart_w, y + 28), 9, "#e8eef5")
        bw = int(chart_w * value / max_count)
        rounded(draw, (chart_x, y + 9, chart_x + bw, y + 28), 9, color)
        text(draw, (x2 - 32, y + 5), f"{value:,}", fill=SLATE, f=F["small_b"], anchor="ra")

    metrics = extreme["metrics"]
    rounded(draw, (x1 + 32, y2 - 104, x1 + 232, y2 - 34), 14, SOFT_TEAL, "#bbf7d0", 1)
    text(draw, (x1 + 52, y2 - 92), "0", fill=GREEN, f=F["metric"])
    text(draw, (x1 + 104, y2 - 82), "capacity\nviolations", fill=SLATE, f=F["tiny"])
    rounded(draw, (x1 + 256, y2 - 104, x2 - 32, y2 - 34), 14, SOFT_BLUE, "#bfdbfe", 1)
    text(draw, (x1 + 276, y2 - 88), f"{metrics['observation_count']:,} checkpoint observations", fill=BLUE_2, f=F["small_b"])
    text(draw, (x1 + 276, y2 - 60), f"{suite['passed_count']}/{suite['scenario_count']} scenarios | 29/29 tests", fill=MUTED, f=F["tiny"])


def draw_footer(draw: ImageDraw.ImageDraw):
    y = 748
    rounded(draw, (72, y, 1528, 818), 18, SOFT_AMBER, "#fed7aa", 2)
    text(draw, (104, y + 17), "Truth boundary", fill=AMBER, f=F["h3"])
    wrapped(
        draw,
        (290, y + 16),
        "This proves reproducible software behavior and grounded route/CCTV/reference evidence. It does not claim live traffic control, field impact, or congestion reduction yet.",
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
    draw_bar_chart(draw)
    draw_footer(draw)
    out = OUT / "ptis_clean_route_chart.png"
    img.save(out, quality=96)

    readme = """# PTIS Clean LinkedIn Asset\n\nUse this as the corrected public image:\n\n- `ptis_clean_route_chart.png`\n\nIt combines the actual OSRM/OpenStreetMap route geometry with the 8,000-vehicle replay destination chart. It keeps the public claim boundary visible: software validated, field validation pending.\n"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"image": str(out), "size": [W, H]}, indent=2))


if __name__ == "__main__":
    generate()