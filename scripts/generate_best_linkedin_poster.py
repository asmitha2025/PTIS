from __future__ import annotations

import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "best_post"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1600, 2000
NAVY = "#07111f"
NAVY2 = "#0a1628"
PANEL = "#ffffff"
INK = "#101827"
MUTED = "#64748b"
SUBTLE = "#dbe5ef"
BLUE = "#2563eb"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
SLATE = "#334155"
LIGHT_BLUE = "#eff6ff"
LIGHT_TEAL = "#ecfdf5"
LIGHT_AMBER = "#fffbeb"
LIGHT_RED = "#fef2f2"


def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8-sig"))


route = load_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = load_json("evidence/extreme_batch_report.json")
cctv = load_json("evidence/cctv_bmd45_report.json")
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
    "brand": font(34, True),
    "tag": font(28, True),
    "title": font(86, True),
    "subtitle": font(42, False),
    "h2": font(48, True),
    "h3": font(34, True),
    "body": font(30, False),
    "body_b": font(30, True),
    "small": font(25, False),
    "small_b": font(25, True),
    "tiny": font(21, False),
    "metric": font(74, True),
    "metric2": font(58, True),
}


def rounded(draw, box, r, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def text(draw, xy, value, fill=INK, f=None, anchor=None):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor)


def wrap_lines(draw, value: str, f, max_width: int):
    words = str(value).split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textbbox((0, 0), trial, font=f)[2] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrapped(draw, xy, value, f, fill, max_width, gap=8, max_lines=None):
    x, y = xy
    lines = wrap_lines(draw, value, f, max_width)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        last = lines[-1]
        while draw.textbbox((0, 0), last + "...", font=f)[2] > max_width and " " in last:
            last = last.rsplit(" ", 1)[0]
        lines[-1] = last + "..."
    for line in lines:
        text(draw, (x, y), line, fill=fill, f=f)
        y += f.size + gap
    return y


def draw_shadow(base, box, radius=42, offset=(0, 18), alpha=55):
    x1, y1, x2, y2 = box
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x1 + offset[0], y1 + offset[1], x2 + offset[0], y2 + offset[1]), radius=radius, fill=(15, 23, 42, alpha))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    base.alpha_composite(shadow)


def gradient_bg():
    img = Image.new("RGBA", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        r = int(7 + 8 * t)
        g = int(17 + 11 * t)
        b = int(31 + 18 * t)
        draw.line((0, y, W, y), fill=(r, g, b, 255))
    # subtle grid
    for x in range(0, W, 80):
        draw.line((x, 0, x, H), fill=(255, 255, 255, 10), width=1)
    for y in range(0, H, 80):
        draw.line((0, y, W, y), fill=(255, 255, 255, 10), width=1)
    # glow bands
    for i in range(9):
        cx = 180 + i * 170
        draw.ellipse((cx - 340, 320 - 160, cx + 340, 320 + 160), fill=(37, 99, 235, 9))
    return img


def metric_card(base, draw, x, y, w, h, value, label, detail, color):
    box = (x, y, x + w, y + h)
    draw_shadow(base, box, 34, (0, 14), 35)
    rounded(draw, box, 34, PANEL, "#dbe5ef", 2)
    text(draw, (x + 34, y + 28), value, fill=color, f=F["metric2"])
    text(draw, (x + 34, y + 92), label, fill=INK, f=F["body_b"])
    wrapped(draw, (x + 34, y + 136), detail, F["small"], MUTED, w - 68, 5, max_lines=2)


def pill(draw, x, y, label, color, fill):
    f = F["small_b"]
    bw = draw.textbbox((0, 0), label, font=f)[2] + 38
    rounded(draw, (x, y, x + bw, y + 48), 18, fill, color, 2)
    text(draw, (x + 19, y + 11), label, fill=color, f=f)
    return x + bw + 14


def project_route(box):
    coords = route["features"][0]["geometry"]["coordinates"]
    x1, y1, x2, y2 = box
    pad = 55
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


def draw_arrow(draw, p1, p2, color, width=6):
    draw.line((p1, p2), fill=color, width=width)
    sx, sy = p1
    ex, ey = p2
    angle = math.atan2(ey - sy, ex - sx)
    size = 22
    a = (ex - size * math.cos(angle - 0.45), ey - size * math.sin(angle - 0.45))
    b = (ex - size * math.cos(angle + 0.45), ey - size * math.sin(angle + 0.45))
    draw.polygon([p2, a, b], fill=color)


def generate():
    base = gradient_bg()
    draw = ImageDraw.Draw(base)

    # Header
    text(draw, (90, 80), "PTIS v2.0", fill="#8ff5de", f=F["brand"])
    rounded(draw, (1250, 70, 1510, 122), 18, (15, 159, 143, 28), "#5eead4", 2)
    text(draw, (1280, 84), "Bengaluru ORR", fill="#b5f7ea", f=F["tag"])

    text(draw, (90, 178), "Traffic decisions", fill="#ffffff", f=F["title"])
    text(draw, (90, 276), "before the bottleneck fully forms", fill="#ffffff", f=F["title"])
    wrapped(draw, (94, 390), "Predict destination pressure. Check receiving capacity. Act only if safe.", F["subtitle"], "#cbd5e1", 1180, 10, max_lines=2)

    # Main map panel
    map_box = (90, 540, 1510, 1116)
    draw_shadow(base, map_box, 46, (0, 22), 70)
    rounded(draw, map_box, 46, "#f8fbff", "#d7e3ef", 2)
    mx1, my1, mx2, my2 = map_box
    # map texture
    for i in range(1, 13):
        x = mx1 + i * (mx2 - mx1) / 13
        draw.line((x, my1 + 38, x, my2 - 38), fill="#e4edf5", width=1)
    for i in range(1, 7):
        y = my1 + i * (my2 - my1) / 7
        draw.line((mx1 + 38, y, mx2 - 38, y), fill="#e4edf5", width=1)

    pts, project = project_route((mx1 + 36, my1 + 42, mx2 - 36, my2 - 120))
    draw.line(pts, fill="#c0ccda", width=24, joint="curve")
    draw.line(pts, fill=BLUE, width=11, joint="curve")
    # route flow dots
    for i in range(14, len(pts), max(1, len(pts)//14)):
        px, py = pts[i]
        draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=TEAL, outline="white", width=3)

    important = {
        "silk_board": ("Silk Board", BLUE),
        "marathahalli": ("Marathahalli gate", AMBER),
        "whitefield": ("Whitefield pressure", GREEN),
    }
    for wp in route["waypoints"]:
        px, py = project(wp["lon"], wp["lat"])
        if wp["id"] in important:
            label, color = important[wp["id"]]
            r = 19
            draw.ellipse((px - r - 6, py - r - 6, px + r + 6, py + r + 6), fill="white")
            draw.ellipse((px - r, py - r, px + r, py + r), fill=color)
            lx = min(max(px + 28, mx1 + 50), mx2 - 360)
            ly = py - 32
            rounded(draw, (lx, ly, lx + 318, ly + 62), 18, "#ffffff", "#d8e4ef", 1)
            text(draw, (lx + 18, ly + 15), label, fill=INK, f=F["small_b"])
        else:
            draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=SLATE, outline="white", width=3)

    # Process strip inside map panel
    strip_y = 1010
    steps = [("Observe", BLUE), ("Infer", TEAL), ("Check capacity", AMBER), ("Act only if safe", GREEN)]
    sx = 155
    last = None
    for label, color in steps:
        rounded(draw, (sx, strip_y, sx + 270, strip_y + 66), 20, "#ffffff", "#dce7f2", 2)
        draw.ellipse((sx + 18, strip_y + 18, sx + 48, strip_y + 48), fill=color)
        text(draw, (sx + 64, strip_y + 18), label, fill=INK, f=F["small_b"])
        if last is not None:
            draw_arrow(draw, (last + 8, strip_y + 33), (sx - 18, strip_y + 33), "#94a3b8", 5)
        last = sx + 270
        sx += 340

    # Metrics
    m = extreme["metrics"]
    y = 1190
    metric_card(base, draw, 90, y, 330, 222, "29/29", "tests passed", "reproducible verification", GREEN)
    metric_card(base, draw, 448, y, 330, 222, f"{m['vehicle_count']:,}", "vehicles", "stress replay", BLUE)
    metric_card(base, draw, 806, y, 330, 222, f"{m['observation_count']:,}", "observations", "checkpoint events", TEAL)
    metric_card(base, draw, 1164, y, 346, 222, "0", "violations", "capacity safety", GREEN)

    # Evidence and boundary panel
    evidence_box = (90, 1495, 1510, 1765)
    draw_shadow(base, evidence_box, 42, (0, 18), 55)
    rounded(draw, evidence_box, 42, PANEL, "#d7e3ef", 2)
    text(draw, (132, 1532), "What is real today", fill=INK, f=F["h2"])
    x = 132
    x = pill(draw, x, 1605, "real route geometry", BLUE, LIGHT_BLUE)
    x = pill(draw, x, 1605, "official references", SLATE, LIGHT_SLATE := "#eef2f7")
    x = pill(draw, x, 1605, "BMD-45 CCTV audit", TEAL, LIGHT_TEAL)
    rounded(draw, (132, 1676, 1468, 1728), 17, LIGHT_AMBER, "#facc15", 2)
    text(draw, (160, 1687), "Boundary: software validated. Field validation pending. No deployment or congestion-reduction claim.", fill="#92400e", f=F["small_b"])

    # Footer
    text(draw, (90, 1860), "Project status", fill="#94a3b8", f=F["small_b"])
    text(draw, (90, 1896), "Software validated + real evidence grounded + field validation pending", fill="#ffffff", f=F["body_b"])
    text(draw, (1510, 1898), "PTIS / Bengaluru ORR", fill="#94a3b8", f=F["small"], anchor="ra")

    out = OUT / "ptis_best_linkedin_poster.png"
    base.convert("RGB").save(out, quality=96)

    caption = """PTIS v2.0: a traffic-intelligence proof for Bengaluru ORR

Most traffic systems are discussed after congestion is already visible: long queues, blocked junctions, and frustrated commuters. I wanted to explore an earlier question:

Can a system detect where traffic pressure is likely going before the bottleneck fully forms, and still avoid unsafe intervention?

That is the idea behind PTIS: Predictive Traffic Intelligence System.

The goal is not to blindly open a route, push vehicles somewhere else, or claim a magic congestion reduction. The goal is narrower and testable:

1. Observe checkpoint events along a corridor.
2. Estimate which destination is becoming more likely.
3. Check whether the receiving route has spare capacity.
4. Activate an intervention only if confidence and capacity gates both pass.

For the current Bengaluru ORR prototype, I used the Silk Board to Whitefield corridor as the reference route. The route visual is based on real OSRM/OpenStreetMap road-network geometry. Official Bengaluru mobility planning references are used for corridor grounding. A real BMD-45 Bengaluru CCTV validation sample is audited as vehicle-detection/counting evidence.

Current proof status:

- 29/29 tests passed
- 6/6 traffic scenarios passed
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

PTIS can process checkpoint observations, update destination belief, and keep smart-link action bounded by receiving capacity in reproducible software replay. In the 8,000-vehicle stress replay, the system preserved capacity safety with zero capacity violations.

What this does not prove yet:

This is not a field-deployment claim. I am not claiming real-world congestion reduction, travel-time savings, public-road control, live BTP/FASTag/Google/Waze integration, or field-proven route prediction.

Current status:

Software validated.
Real route grounded.
Official reference grounded.
Real CCTV detection evidence audited.
Field validation pending.

Next validation step:

Because I am not physically in Bengaluru, I added a no-travel validation path: remote aggregate-count replay. A trusted observer can count vehicles at Marathahalli/ORR toward Whitefield every minute, without recording number plates, faces, or private identifiers. PTIS can then replay the measured aggregate load and check whether the capacity-safety gate still behaves correctly.

That still will not prove destination accuracy or field impact. It will only add measured-load evidence. The stronger field validation step would require observed checkpoint data, capacity time series, and OD/ground-truth labels.

I am posting this for technical criticism from traffic engineers, ML engineers, civic-tech builders, and Bengaluru mobility professionals.

If there is a flaw in the reasoning, validation method, or evidence boundary, I want to find it now before making stronger claims.

Project status: software validated, field validation pending.

#Bengaluru #TrafficEngineering #UrbanMobility #CivicTech #MachineLearning #BuildInPublic
"""
    (OUT / "caption_best.txt").write_text(caption, encoding="utf-8")
    (OUT / "README.md").write_text("""# Best PTIS LinkedIn Post Asset

Use this single image first:

- `ptis_best_linkedin_poster.png`

Use this caption:

- `caption_best.txt`

This version is intentionally simple: one route visual, one process strip, four proof metrics, and one truth boundary.
""", encoding="utf-8")
    print(json.dumps({"poster": str(out), "caption": str(OUT / "caption_best.txt")}, indent=2))


if __name__ == "__main__":
    generate()