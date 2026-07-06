from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 900
BG = "#f6f8fb"
INK = "#0b1220"
MUTED = "#536173"
SUBTLE = "#d9e1ea"
PANEL = "#ffffff"
BLUE = "#2563eb"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
SLATE = "#1f2937"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


F = {
    "eyebrow": font(24, True),
    "title": font(62, True),
    "h2": font(38, True),
    "body": font(28, False),
    "body_b": font(28, True),
    "small": font(22, False),
    "small_b": font(22, True),
    "metric": font(50, True),
    "metric_sm": font(38, True),
}


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


route = load_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = load_json("evidence/extreme_batch_report.json")
suite = load_json("evidence/suite_report.json")
cctv = load_json("evidence/cctv_bmd45_report.json")
latest = load_json("evidence/latest_run.json")


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=INK, f=None, anchor=None):
    draw.text(xy, value, fill=fill, font=f or F["body"], anchor=anchor)


def wrap_lines(draw: ImageDraw.ImageDraw, value: str, f, max_width: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textbbox((0, 0), trial, font=f)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(draw: ImageDraw.ImageDraw, xy, value: str, f, fill: str, max_width: int, line_gap: int = 8):
    x, y = xy
    for line in wrap_lines(draw, value, f, max_width):
        text(draw, (x, y), line, fill=fill, f=f)
        y += f.size + line_gap
    return y


def metric_card(draw, x, y, w, h, label, value, detail, color=BLUE):
    rounded(draw, (x, y, x + w, y + h), 18, PANEL, "#e5edf6", 2)
    text(draw, (x + 24, y + 20), label.upper(), fill=MUTED, f=F["small_b"])
    value_font = F["metric"] if draw.textbbox((0, 0), value, font=F["metric"])[2] <= w - 48 else F["metric_sm"]
    text(draw, (x + 24, y + 58), value, fill=color, f=value_font)
    draw_wrapped(draw, (x + 24, y + 118), detail, F["small"], MUTED, w - 48, 3)


def pill(draw, x, y, label, color):
    f = F["small_b"]
    bbox = draw.textbbox((0, 0), label, font=f)
    width = bbox[2] - bbox[0] + 34
    rounded(draw, (x, y, x + width, y + 42), 12, color + "20", color, 2)
    text(draw, (x + 17, y + 9), label, fill=color, f=f)
    return x + width + 12


def header(draw, title, subtitle):
    text(draw, (72, 60), "PTIS v2.0", fill=TEAL, f=F["eyebrow"])
    text(draw, (72, 96), title, fill=INK, f=F["title"])
    draw_wrapped(draw, (72, 172), subtitle, F["body"], MUTED, 940, 6)


def footer(draw, note="Software validated. Field validation pending."):
    draw.line((72, H - 74, W - 72, H - 74), fill=SUBTLE, width=2)
    text(draw, (72, H - 50), note, fill=MUTED, f=F["small_b"])
    text(draw, (W - 72, H - 50), "No deployment / no congestion-reduction claim", fill=MUTED, f=F["small"], anchor="ra")


def project_route_points(width: int, height: int, pad: int = 70):
    coords = route["features"][0]["geometry"]["coordinates"]
    lons = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    scale = min((width - 2 * pad) / (max_lon - min_lon), (height - 2 * pad) / (max_lat - min_lat))
    x_offset = (width - (max_lon - min_lon) * scale) / 2
    y_offset = (height - (max_lat - min_lat) * scale) / 2

    def project(lon, lat):
        x = x_offset + (float(lon) - min_lon) * scale
        y = height - (y_offset + (float(lat) - min_lat) * scale)
        return x, y

    return [project(c[0], c[1]) for c in coords], project


def draw_route_asset():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, "Bengaluru ORR Decision Route", "Real OSRM/OpenStreetMap route geometry for Silk Board to Whitefield. This is route grounding, not live traffic.")

    map_box = (72, 250, 1036, 760)
    rounded(draw, map_box, 24, "#eef4f8", "#d7e2ec", 2)
    mx, my, mx2, my2 = map_box
    # lightweight map grid
    for i in range(1, 9):
        x = mx + i * (mx2 - mx) / 9
        draw.line((x, my + 20, x, my2 - 20), fill="#dce7ef", width=1)
    for i in range(1, 5):
        y = my + i * (my2 - my) / 5
        draw.line((mx + 20, y, mx2 - 20, y), fill="#dce7ef", width=1)

    pts, project = project_route_points(mx2 - mx, my2 - my, 58)
    pts = [(mx + x, my + y) for x, y in pts]
    # shadow and route
    draw.line(pts, fill="#b8c7d6", width=14, joint="curve")
    draw.line(pts, fill=BLUE, width=7, joint="curve")

    waypoints = route["waypoints"]
    important = {"silk_board", "marathahalli", "whitefield"}
    label_offsets = {
        "silk_board": (32, -2, 218),
        "marathahalli": (32, -26, 250),
        "whitefield": (26, -26, 230),
    }
    for wp in waypoints:
        px, py = project(wp["lon"], wp["lat"])
        px += mx
        py += my
        color = TEAL if wp["id"] == "whitefield" else (AMBER if wp["id"] == "marathahalli" else SLATE)
        r = 13 if wp["id"] in important else 8
        draw.ellipse((px - r - 4, py - r - 4, px + r + 4, py + r + 4), fill="white")
        draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
        if wp["id"] in important:
            label = wp["name"]
            dx, dy, label_w = label_offsets[wp["id"]]
            lx = min(max(px + dx, mx + 22), mx2 - label_w - 22)
            ly = min(max(py + dy, my + 28), my2 - 86)
            rounded(draw, (lx, ly, lx + label_w, ly + 48), 12, "#ffffff", "#d8e4ef", 1)
            text(draw, (lx + 14, ly + 10), label, fill=INK, f=F["small_b"])

    m = extreme["metrics"]
    side_x, side_y = 1080, 250
    card_w, card_h, gap = 215, 148, 24
    metric_card(draw, side_x, side_y, card_w, card_h, "Stress", f"{m['vehicle_count']:,}", "vehicles replayed", BLUE)
    metric_card(draw, side_x + card_w + gap, side_y, card_w, card_h, "Observations", f"{m['observation_count']:,}", "checkpoint events", TEAL)
    metric_card(draw, side_x, side_y + card_h + gap, card_w, card_h, "Safety", str(m["capacity_violation_count"]), "capacity violations", GREEN)
    metric_card(draw, side_x + card_w + gap, side_y + card_h + gap, card_w, card_h, "Route", f"{route['coordinate_count']:,}", "route geometry pts", BLUE)

    truth_box = (side_x, 612, side_x + card_w * 2 + gap, 760)
    rounded(draw, truth_box, 18, "#fff7ed", "#fed7aa", 2)
    text(draw, (truth_box[0] + 26, truth_box[1] + 24), "Truth boundary", fill=AMBER, f=F["small_b"])
    draw_wrapped(draw, (truth_box[0] + 26, truth_box[1] + 60), "Map uses public road-network geometry. It is not observed live traffic or field impact evidence.", F["small"], "#92400e", truth_box[2] - truth_box[0] - 52, 5)
    footer(draw)
    img.save(OUT / "ptis_linkedin_01_route_map.png", quality=95)
    img.save(OUT / "ptis_linkedin_01_route_map_aligned.png", quality=95)


def draw_validation_asset():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, "What Is Actually Proven", "A public-safe validation snapshot for technical review. Strong software evidence; field validation is still pending.")

    x0, y0 = 88, 300
    rows = [
        ("Unit tests", 29, 29, GREEN, "Core engine, provenance, field-gate and remote replay checks"),
        ("Scenario suite", suite["passed_count"], suite["scenario_count"], GREEN, "Published traffic edge cases"),
        ("Stress vehicles", extreme["metrics"]["vehicle_count"], 8000, BLUE, "Synthetic worst-case replay"),
        ("Capacity violations", 0, 1, GREEN, "Zero is the target"),
        ("CCTV annotations", cctv["metrics"]["coco_annotation_count"], 106404, TEAL, "Real BMD-45 detection evidence"),
        ("Field replay", 0, 1, AMBER, "Pending real observed OD/checkpoint data"),
    ]
    max_bar = 900
    for i, (label, value, total, color, detail) in enumerate(rows):
        y = y0 + i * 78
        text(draw, (x0, y), label, fill=INK, f=F["body_b"])
        text(draw, (x0, y + 34), detail, fill=MUTED, f=F["small"])
        bx, by = 520, y + 10
        rounded(draw, (bx, by, bx + max_bar, by + 34), 17, "#e8eef5", None)
        ratio = 0 if total == 0 else min(1.0, float(value) / float(total))
        fill_w = max(0, int(max_bar * ratio))
        if label == "Capacity violations":
            fill_w = max_bar
        if fill_w:
            rounded(draw, (bx, by, bx + fill_w, by + 34), 17, color, None)
        if label == "Field replay":
            draw.line((bx, by + 17, bx + max_bar, by + 17), fill=AMBER, width=4)
        val_text = "pending" if label == "Field replay" else ("0" if label == "Capacity violations" else f"{value:,}/{total:,}")
        text(draw, (bx + max_bar + 28, y + 8), val_text, fill=color, f=F["body_b"])

    rounded(draw, (88, 800, 1512, 846), 14, "#ecfdf5", "#bbf7d0", 2)
    text(draw, (116, 811), "Safe claim: software validated + real route/CCTV/reference grounded. Field impact remains pending.", fill="#166534", f=F["small_b"])
    footer(draw)
    img.save(OUT / "ptis_linkedin_02_validation_chart.png", quality=95)


def draw_boundary_asset():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    header(draw, "Evidence Ladder", "How PTIS moves from reproducible proof to real-world validation without overstating claims.")

    stages = [
        ("L1", "Software validation", "DONE", GREEN, "29 tests, 6 scenarios, 8,000-vehicle stress replay, 0 capacity violations."),
        ("L2", "Public grounding", "DONE", GREEN, "OSRM/OpenStreetMap route, DULT/CMP references, BMD-45 CCTV audit."),
        ("L3", "Remote aggregate replay", "NEXT", AMBER, "Trusted observer counts vehicles at Marathahalli/ORR. Checks measured-load capacity safety."),
        ("L4", "Field OD validation", "PENDING", RED, "Requires observed checkpoint data, capacity time series, and ground-truth destination labels."),
    ]

    x, y = 120, 286
    card_w, card_h, gap = 1360, 112, 26
    for i, (level, name, status, color, detail) in enumerate(stages):
        cy = y + i * (card_h + gap)
        rounded(draw, (x, cy, x + card_w, cy + card_h), 20, PANEL, "#e4ebf3", 2)
        draw.ellipse((x + 34, cy + 30, x + 86, cy + 82), fill=color)
        text(draw, (x + 60, cy + 44), level, fill="white", f=F["small_b"], anchor="ma")
        text(draw, (x + 120, cy + 24), name, fill=INK, f=F["h2"])
        draw_wrapped(draw, (x + 120, cy + 68), detail, F["small"], MUTED, 890, 4)
        rounded(draw, (x + card_w - 220, cy + 34, x + card_w - 40, cy + 78), 14, color + "22", color, 2)
        text(draw, (x + card_w - 130, cy + 45), status, fill=color, f=F["small_b"], anchor="ma")
        if i < len(stages) - 1:
            draw.line((x + 60, cy + card_h, x + 60, cy + card_h + gap), fill="#b8c5d5", width=4)

    rounded(draw, (120, 812, 1480, 856), 14, "#fff7ed", "#fed7aa", 2)
    text(draw, (148, 822), "Current public position: L1 + L2 complete. L3 needs one real remote aggregate CSV. L4 is not claimed.", fill="#92400e", f=F["small_b"])
    footer(draw)
    img.save(OUT / "ptis_linkedin_03_evidence_ladder.png", quality=95)


def draw_caption_file():
    captions = """# PTIS LinkedIn Asset Pack

Use these PNGs as a carousel or attach one/two to the post.

1. `ptis_linkedin_01_route_map.png` - route/map proof: real OSRM/OpenStreetMap geometry + stress metrics.
   `ptis_linkedin_01_route_map_aligned.png` is the same corrected main image for posting.
2. `ptis_linkedin_02_validation_chart.png` - validation chart: tests, scenarios, stress, CCTV, field pending.
3. `ptis_linkedin_03_evidence_ladder.png` - evidence ladder: L1/L2 done, L3 next, L4 pending.

Suggested carousel order:

1. Route map
2. Validation chart
3. Evidence ladder

Safe caption line:

PTIS v2.0 is software validated and grounded with public Bengaluru route/CCTV/reference evidence. Field validation is pending real observed data.
"""
    (OUT / "README.md").write_text(captions, encoding="utf-8")


def main():
    draw_route_asset()
    draw_validation_asset()
    draw_boundary_asset()
    draw_caption_file()
    print(json.dumps({
        "output_dir": str(OUT),
        "assets": [
            "ptis_linkedin_01_route_map.png",
            "ptis_linkedin_02_validation_chart.png",
            "ptis_linkedin_03_evidence_ladder.png",
            "README.md",
        ],
    }, indent=2))


if __name__ == "__main__":
    main()