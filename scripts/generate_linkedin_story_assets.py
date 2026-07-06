from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "story_carousel"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350
BG = "#f8fafc"
INK = "#0f172a"
MUTED = "#536173"
SOFT = "#e2e8f0"
PANEL = "#ffffff"
BLUE = "#2563eb"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
SLATE = "#263244"
LIGHT_BLUE = "#dbeafe"
LIGHT_TEAL = "#ccfbf1"
LIGHT_GREEN = "#dcfce7"
LIGHT_AMBER = "#fef3c7"
LIGHT_RED = "#fee2e2"
LIGHT_SLATE = "#eef2f7"


def load_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


route = load_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = load_json("evidence/extreme_batch_report.json")
suite = load_json("evidence/suite_report.json")
cctv = load_json("evidence/cctv_bmd45_report.json")


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
    "kicker": font(27, True),
    "title": font(62, True),
    "title2": font(54, True),
    "h2": font(42, True),
    "h3": font(34, True),
    "body": font(30, False),
    "body_b": font(30, True),
    "small": font(24, False),
    "small_b": font(24, True),
    "tiny": font(20, False),
    "metric": font(64, True),
    "metric2": font(54, True),
}


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def text(draw, xy, value, fill=INK, f=None, anchor=None, align="left"):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor, align=align)


def text_size(draw, value, f):
    box = draw.textbbox((0, 0), str(value), font=f)
    return box[2] - box[0], box[3] - box[1]


def wrap_lines(draw, value: str, f, max_width: int):
    words = str(value).split()
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


def wrapped(draw, xy, value, f, fill, max_width, gap=8, max_lines=None):
    x, y = xy
    lines = wrap_lines(draw, value, f, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and draw.textbbox((0, 0), lines[-1] + "...", font=f)[2] > max_width:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        if lines:
            lines[-1] += "..."
    for line in lines:
        text(draw, (x, y), line, fill=fill, f=f)
        y += f.size + gap
    return y


def fit_wrapped(draw, box, value, fonts, fill, gap=7):
    x1, y1, x2, y2 = box
    max_w = x2 - x1
    max_h = y2 - y1
    for f in fonts:
        lines = wrap_lines(draw, value, f, max_w)
        total_h = len(lines) * f.size + max(0, len(lines) - 1) * gap
        if total_h <= max_h:
            y = y1
            for line in lines:
                text(draw, (x1, y), line, fill=fill, f=f)
                y += f.size + gap
            return y
    f = fonts[-1]
    line_h = f.size + gap
    max_lines = max(1, max_h // line_h)
    return wrapped(draw, (x1, y1), value, f, fill, max_w, gap, max_lines=max_lines)


def canvas():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def header(draw, num, title, subtitle=None):
    rounded(draw, (58, 54, 214, 102), 18, LIGHT_TEAL, TEAL, 2)
    text(draw, (78, 66), f"PTIS / {num}", fill=TEAL, f=F["small_b"])
    text(draw, (58, 138), title, fill=INK, f=F["title"])
    if subtitle:
        fit_wrapped(draw, (60, 220, 1000, 310), subtitle, [F["body"], F["small"]], MUTED, 8)


def footer(draw, note="Software validated. Field validation pending."):
    draw.line((58, H - 92, W - 58, H - 92), fill=SOFT, width=2)
    text(draw, (60, H - 64), note, fill=MUTED, f=F["tiny"])
    text(draw, (W - 60, H - 64), "No deployment claim", fill=MUTED, f=F["tiny"], anchor="ra")


def metric(draw, x, y, w, h, value, label, detail, color):
    rounded(draw, (x, y, x + w, y + h), 24, PANEL, "#d7e1ec", 2)
    text(draw, (x + 28, y + 24), value, fill=color, f=F["metric2"])
    text(draw, (x + 28, y + 88), label, fill=INK, f=F["body_b"])
    fit_wrapped(draw, (x + 28, y + 130, x + w - 28, y + h - 22), detail, [F["small"], F["tiny"]], MUTED, 4)


def project_route(box):
    coords = route["features"][0]["geometry"]["coordinates"]
    x1, y1, x2, y2 = box
    pad = 52
    lons = [float(c[0]) for c in coords]
    lats = [float(c[1]) for c in coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)
    sx = (x2 - x1 - 2 * pad) / max(0.000001, max_lon - min_lon)
    sy = (y2 - y1 - 2 * pad) / max(0.000001, max_lat - min_lat)
    s = min(sx, sy)
    ox = x1 + ((x2 - x1) - (max_lon - min_lon) * s) / 2
    oy = y1 + ((y2 - y1) - (max_lat - min_lat) * s) / 2

    def p(lon, lat):
        return (ox + (float(lon) - min_lon) * s, y2 - (oy - y1 + (float(lat) - min_lat) * s))

    return [p(c[0], c[1]) for c in coords], p


def draw_flow_arrow(draw, start, end, color, width=6):
    draw.line((start, end), fill=color, width=width)
    sx, sy = start
    ex, ey = end
    angle = math.atan2(ey - sy, ex - sx)
    size = 20
    p1 = (ex - size * math.cos(angle - 0.45), ey - size * math.sin(angle - 0.45))
    p2 = (ex - size * math.cos(angle + 0.45), ey - size * math.sin(angle + 0.45))
    draw.polygon([end, p1, p2], fill=color)


def slide_01_problem():
    img, draw = canvas()
    header(draw, "01", "The traffic question", "What if traffic control could see pressure forming before the junction is already blocked?")
    road_y = 690
    rounded(draw, (78, 500, 1002, 880), 36, "#eef3f8", "#d8e2ee", 2)
    draw.line((130, road_y, 950, road_y), fill="#334155", width=36)
    draw.line((130, road_y, 950, road_y), fill="#f8fafc", width=4)
    for i in range(13):
        x = 175 + i * 42
        color = [BLUE, TEAL, AMBER, SLATE][i % 4]
        rounded(draw, (x, road_y - 70, x + 28, road_y - 48), 5, color)
    for i in range(9):
        x = 450 + i * 48
        color = [SLATE, BLUE, TEAL][i % 3]
        rounded(draw, (x, road_y + 48, x + 30, road_y + 70), 5, color)
    draw.ellipse((734, road_y - 85, 824, road_y + 5), fill=LIGHT_RED, outline=RED, width=4)
    text(draw, (779, road_y - 60), "!", fill=RED, f=F["h2"], anchor="ma")
    text(draw, (710, road_y + 36), "bottleneck", fill=RED, f=F["small_b"])

    rounded(draw, (98, 940, 982, 1110), 28, PANEL, "#dfe7f1", 2)
    text(draw, (132, 976), "Most systems react after congestion is visible.", fill=INK, f=F["h3"])
    fit_wrapped(draw, (132, 1032, 940, 1092), "PTIS asks a smaller, testable question: can we infer where flow is going and open an action only when capacity is safe?", [F["body"], F["small"]], MUTED, 7)
    footer(draw)
    img.save(OUT / "ptis_story_01_problem.png", quality=95)


def step_card(draw, box, n, title, detail, color):
    x1, y1, x2, y2 = box
    rounded(draw, box, 26, PANEL, "#d7e1ec", 2)
    draw.ellipse((x1 + 28, y1 + 28, x1 + 88, y1 + 88), fill=color)
    text(draw, (x1 + 58, y1 + 43), n, fill="white", f=F["body_b"], anchor="ma")
    text(draw, (x1 + 112, y1 + 30), title, fill=INK, f=F["h3"])
    fit_wrapped(draw, (x1 + 112, y1 + 82, x2 - 24, y2 - 22), detail, [F["small"], F["tiny"]], MUTED, 5)


def slide_02_how():
    img, draw = canvas()
    header(draw, "02", "PTIS in one picture", "Destination-aware, capacity-safe traffic intervention.")

    steps = [
        ("1", "Observe", "Read checkpoint events from the corridor.", BLUE),
        ("2", "Infer", "Update the likely destination pressure.", TEAL),
        ("3", "Check", "Compare demand with receiving capacity.", AMBER),
        ("4", "Act", "Activate only if the safety gate passes.", GREEN),
    ]
    boxes = [(76, 365, 502, 535), (578, 365, 1004, 535), (76, 570, 502, 740), (578, 570, 1004, 740)]
    for box, item in zip(boxes, steps):
        step_card(draw, box, *item)

    map_box = (90, 820, 990, 1045)
    rounded(draw, map_box, 30, "#eff6ff", "#bfdbfe", 2)
    pts, project = project_route((130, 850, 940, 990))
    draw.line(pts, fill="#b6c6d8", width=16, joint="curve")
    draw.line(pts, fill=BLUE, width=8, joint="curve")
    for wp in route["waypoints"]:
        px, py = project(wp["lon"], wp["lat"])
        important = wp["id"] in {"silk_board", "marathahalli", "whitefield"}
        r = 12 if important else 7
        c = GREEN if wp["id"] == "whitefield" else (AMBER if wp["id"] == "marathahalli" else SLATE)
        draw.ellipse((px - r, py - r, px + r, py + r), fill=c, outline="white", width=4)
        if important:
            text(draw, (px + 16, py - 14), wp["name"], fill=INK, f=F["tiny"])
    fit_wrapped(draw, (128, 1006, 940, 1034), "Example corridor: Silk Board -> Marathahalli -> Whitefield. Route geometry is public map reference, not live traffic.", [F["tiny"]], MUTED, 3)
    footer(draw)
    img.save(OUT / "ptis_story_02_how_it_works.png", quality=95)


def slide_03_proof():
    img, draw = canvas()
    header(draw, "03", "What is proven so far", "This is software validation, not field deployment.")
    m = extreme["metrics"]
    metric(draw, 78, 360, 442, 210, "29/29", "tests passed", "Core engine and evidence boundary checks.", GREEN)
    metric(draw, 560, 360, 442, 210, "6/6", "scenarios passed", "Published traffic edge cases.", GREEN)
    metric(draw, 78, 610, 442, 210, f"{m['vehicle_count']:,}", "vehicles replayed", "Worst-case synthetic stress replay.", BLUE)
    metric(draw, 560, 610, 442, 210, f"{m['observation_count']:,}", "observations", "Checkpoint events processed.", TEAL)
    metric(draw, 78, 860, 442, 210, "0", "capacity violations", "Gate never exceeded receiving capacity.", GREEN)
    metric(draw, 560, 860, 442, 210, "0", "overcommands", "No command above actual destination demand.", GREEN)

    rounded(draw, (78, 1130, 1002, 1210), 22, LIGHT_AMBER, "#facc15", 2)
    fit_wrapped(draw, (110, 1154, 970, 1196), "Truth boundary: stress replay is reproducible software evidence, not observed field traffic.", [F["small_b"], F["small"]], "#92400e", 5)
    footer(draw)
    img.save(OUT / "ptis_story_03_software_proof.png", quality=95)


def evidence_card(draw, box, title, value, detail, color, fill):
    x1, y1, x2, y2 = box
    rounded(draw, box, 26, fill, color, 2)
    text(draw, (x1 + 28, y1 + 24), title, fill=color, f=F["small_b"])
    text(draw, (x1 + 28, y1 + 68), value, fill=INK, f=F["h2"])
    fit_wrapped(draw, (x1 + 28, y1 + 124, x2 - 28, y2 - 22), detail, [F["small"], F["tiny"]], MUTED, 4)


def slide_04_real_vs_pending():
    img, draw = canvas()
    header(draw, "04", "Real evidence vs pending", "The system is stronger when the evidence boundary is visible.")
    evidence_card(draw, (76, 340, 502, 560), "REAL ROUTE", f"{route['coordinate_count']:,} pts", "OSRM/OpenStreetMap route geometry. Visualization/reference layer.", BLUE, LIGHT_BLUE)
    evidence_card(draw, (578, 340, 1004, 560), "REAL CCTV", f"{cctv['metrics']['coco_annotation_count']:,}", "BMD-45 COCO annotations audited for detection/counting evidence.", TEAL, LIGHT_TEAL)
    evidence_card(draw, (76, 600, 502, 820), "OFFICIAL CONTEXT", "DULT/CMP", "Official Bengaluru planning references ground the corridor problem.", SLATE, LIGHT_SLATE)
    evidence_card(draw, (578, 600, 1004, 820), "SOFTWARE REPLAY", "8,000", "Synthetic stress replay proves decision logic under published tests.", GREEN, LIGHT_GREEN)

    rounded(draw, (76, 890, 1004, 1090), 30, LIGHT_AMBER, "#f59e0b", 3)
    text(draw, (112, 926), "Still pending", fill=AMBER, f=F["h2"])
    fit_wrapped(draw, (112, 990, 960, 1066), "Real field replay needs observed checkpoint data, capacity time series, and destination/OD labels. PTIS does not claim this yet.", [F["body"], F["small"]], "#92400e", 8)
    footer(draw)
    img.save(OUT / "ptis_story_04_evidence_boundary.png", quality=95)


def wide_step(draw, box, n, title, detail, color, fill):
    x1, y1, x2, y2 = box
    rounded(draw, box, 30, fill, color, 2)
    draw.ellipse((x1 + 32, y1 + 34, x1 + 102, y1 + 104), fill=color)
    text(draw, (x1 + 67, y1 + 53), n, fill="white", f=F["h3"], anchor="ma")
    text(draw, (x1 + 132, y1 + 32), title, fill=INK, f=F["h3"])
    fit_wrapped(draw, (x1 + 132, y1 + 86, x2 - 34, y2 - 28), detail, [F["body"], F["small"]], MUTED, 6)


def slide_05_next():
    img, draw = canvas()
    header(draw, "05", "Next honest validation step", "Because I am not in Bengaluru, the next step is remote aggregate-count replay.")

    wide_step(draw, (78, 365, 1002, 535), "1", "Count", "A trusted Bengaluru observer counts vehicles at one checkpoint every 1 minute.", BLUE, LIGHT_BLUE)
    wide_step(draw, (78, 575, 1002, 745), "2", "Protect privacy", "No number plates, no faces, no private IDs. Only aggregate counts by class.", TEAL, LIGHT_TEAL)
    wide_step(draw, (78, 785, 1002, 955), "3", "Replay measured load", "PTIS checks that any action remains inside the capacity-safety gate.", GREEN, LIGHT_GREEN)

    rounded(draw, (78, 1018, 1002, 1136), 26, LIGHT_RED, "#fecaca", 2)
    text(draw, (112, 1042), "Still not a field-deployment claim", fill=RED, f=F["h3"])
    fit_wrapped(draw, (112, 1090, 960, 1122), "It will not prove destination accuracy or congestion reduction. That needs true field OD validation.", [F["small"], F["tiny"]], "#991b1b", 4)
    footer(draw, "Posting for technical criticism before field claims.")
    img.save(OUT / "ptis_story_05_next_step.png", quality=95)


def summary_one_image():
    img, draw = canvas()
    header(draw, "SUMMARY", "PTIS v2.0", "A traffic-intelligence proof for Bengaluru ORR: predict destination pressure, check capacity, act only if safe.")
    metric(draw, 78, 350, 290, 190, "29/29", "tests", "passed", GREEN)
    metric(draw, 395, 350, 290, 190, "8,000", "vehicles", "stress replay", BLUE)
    metric(draw, 712, 350, 290, 190, "0", "violations", "capacity safety", GREEN)

    rounded(draw, (78, 610, 1002, 834), 30, PANEL, "#dfe7f1", 2)
    text(draw, (118, 650), "What is real today", fill=INK, f=F["h2"])
    fit_wrapped(draw, (118, 714, 950, 805), "Software proof, public route geometry, official planning references, and BMD-45 CCTV detection audit.", [F["body"], F["small"]], MUTED, 8)

    rounded(draw, (78, 880, 1002, 1104), 30, LIGHT_AMBER, "#f59e0b", 2)
    text(draw, (118, 920), "What is pending", fill=AMBER, f=F["h2"])
    fit_wrapped(draw, (118, 984, 950, 1078), "Remote aggregate-count replay first; true field OD validation later. No deployment or congestion-reduction claim yet.", [F["body"], F["small"]], "#92400e", 8)
    footer(draw)
    img.save(OUT / "ptis_story_00_single_summary.png", quality=95)


def caption_files():
    caption = """PTIS v2.0: a traffic-intelligence proof for Bengaluru ORR

Bengaluru ORR traffic is usually discussed after the pain is already visible: long queues, blocked junctions, and wasted time. I wanted to explore the earlier question: can a system detect where traffic pressure is likely going before the bottleneck fully forms, and still avoid unsafe intervention?

That is the idea behind PTIS: Predictive Traffic Intelligence System.

The goal is not to blindly open a route, push vehicles somewhere else, or claim a magic congestion reduction. The goal is narrower and more testable:

1. Observe checkpoint events along a corridor.
2. Estimate which destination is becoming more likely.
3. Check whether the receiving route has spare capacity.
4. Activate an intervention only if the confidence and capacity gates both pass.

For the current Bengaluru ORR prototype, I used the Silk Board to Whitefield corridor as the reference route. The visible route geometry is real OSRM/OpenStreetMap road-network geometry. Official Bengaluru mobility planning references are used for corridor grounding. A real BMD-45 Bengaluru CCTV validation sample is audited as vehicle-detection/counting evidence.

Current proof status:

- 29/29 tests passed
- 6/6 scenarios passed
- 240-vehicle batch replay passed
- 8,000-vehicle stress replay passed
- 23,314 checkpoint observations processed
- 0 capacity violations
- 0 overcommands
- 0 false-positive aggregate activations
- 1,185-point OSRM/OpenStreetMap route geometry
- 10,194 BMD-45 image records audited
- 106,404 COCO annotations checked

What this currently proves:

PTIS can process checkpoint observations, update destination belief, and keep the smart-link action bounded by receiving capacity in reproducible software replay. In the 8,000-vehicle stress replay, the system preserved capacity safety with zero capacity violations.

What this does not prove yet:

This is not a field-deployment claim. I am not claiming real-world congestion reduction, travel-time savings, public-road control, live BTP/FASTag/Google/Waze integration, or field-proven route prediction.

The current status is:

Software validated.
Real route grounded.
Official reference grounded.
Real CCTV detection evidence audited.
Field validation pending.

The next honest validation step:

I am not physically in Bengaluru, so I added a no-travel validation path: remote aggregate-count replay. A trusted observer can count vehicles at Marathahalli/ORR toward Whitefield every minute, without recording number plates, faces, or private identifiers. PTIS can then replay the measured aggregate load and check whether the capacity-safety gate still behaves correctly.

That still will not prove destination accuracy or field impact. It will only add measured-load evidence. The stronger field validation step would require observed checkpoint data, capacity time series, and OD/ground-truth labels.

I am posting this for technical criticism from traffic engineers, ML engineers, civic-tech builders, and Bengaluru mobility professionals.

If there is a flaw in the reasoning, the validation method, or the evidence boundary, I want to find it now before making stronger claims.

Project status: software validated, field validation pending.

#Bengaluru #TrafficEngineering #UrbanMobility #CivicTech #MachineLearning #BuildInPublic
"""
    short = """PTIS v2.0 is software validated and grounded with public Bengaluru route/CCTV/reference evidence. Field validation is pending real observed data.

Carousel flow:
1. The traffic question
2. How PTIS works
3. What is proven
4. What is real vs pending
5. Next validation step
"""
    readme = """# PTIS Story Carousel

Recommended LinkedIn order:

1. `ptis_story_01_problem.png`
2. `ptis_story_02_how_it_works.png`
3. `ptis_story_03_software_proof.png`
4. `ptis_story_04_evidence_boundary.png`
5. `ptis_story_05_next_step.png`

Optional single-image post:

- `ptis_story_00_single_summary.png`

Use `caption_story.txt` as the main post text.
"""
    (OUT / "caption_story.txt").write_text(caption, encoding="utf-8")
    (OUT / "caption_short.txt").write_text(short, encoding="utf-8")
    (OUT / "README.md").write_text(readme, encoding="utf-8")


def main():
    summary_one_image()
    slide_01_problem()
    slide_02_how()
    slide_03_proof()
    slide_04_real_vs_pending()
    slide_05_next()
    caption_files()
    print(json.dumps({
        "output_dir": str(OUT),
        "assets": [p.name for p in sorted(OUT.iterdir())],
    }, indent=2))


if __name__ == "__main__":
    main()