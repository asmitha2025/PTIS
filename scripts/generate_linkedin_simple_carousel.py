from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "linkedin_assets" / "simple_carousel"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1350
BG = "#f8fafc"
CARD = "#ffffff"
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#dbe5ef"
GRID = "#e8eef5"
BLUE = "#2563eb"
TEAL = "#0f9f8f"
GREEN = "#16a34a"
AMBER = "#d97706"
RED = "#dc2626"
SLATE = "#334155"
SOFT_BLUE = "#eff6ff"
SOFT_TEAL = "#ecfdf5"
SOFT_GREEN = "#ecfdf5"
SOFT_AMBER = "#fff7ed"
SOFT_RED = "#fef2f2"
SOFT_SLATE = "#f1f5f9"


def load_json(rel: str) -> dict[str, Any]:
    return json.loads((ROOT / rel).read_text(encoding="utf-8-sig"))


route = load_json("data/orr_silk_board_whitefield_route_osrm.geojson")
extreme = load_json("evidence/extreme_batch_report.json")
suite = load_json("evidence/suite_report.json")
cctv = load_json("evidence/cctv_bmd45_report.json")


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
    "kicker": font(28, True),
    "title": font(60, True),
    "title_sm": font(50, True),
    "h2": font(38, True),
    "h3": font(30, True),
    "body": font(28, False),
    "body_b": font(28, True),
    "small": font(23, False),
    "small_b": font(23, True),
    "tiny": font(18, False),
    "metric": font(58, True),
    "huge": font(82, True),
}


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def text(draw: ImageDraw.ImageDraw, xy, value: str, fill=INK, f=None, anchor=None, align="left"):
    draw.text(xy, str(value), fill=fill, font=f or F["body"], anchor=anchor, align=align)


def text_w(draw: ImageDraw.ImageDraw, value: str, f) -> int:
    b = draw.textbbox((0, 0), str(value), font=f)
    return b[2] - b[0]


def wrap_lines(draw: ImageDraw.ImageDraw, value: str, f, max_w: int) -> list[str]:
    words = str(value).split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def wrapped(draw: ImageDraw.ImageDraw, xy, value: str, f, fill: str, max_w: int, gap: int = 6, max_lines: int | None = None):
    x, y = xy
    lines = wrap_lines(draw, value, f, max_w)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        while lines and text_w(draw, lines[-1] + "...", f) > max_w and " " in lines[-1]:
            lines[-1] = lines[-1].rsplit(" ", 1)[0]
        if lines:
            lines[-1] += "..."
    for line in lines:
        text(draw, (x, y), line, fill=fill, f=f)
        y += f.size + gap
    return y


def canvas():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    return img, draw


def header(draw: ImageDraw.ImageDraw, n: str, title: str, subtitle: str | None = None):
    text(draw, (72, 60), "PTIS v2.0", fill=TEAL, f=F["kicker"])
    text(draw, (W - 72, 64), n, fill=MUTED, f=F["small_b"], anchor="ra")
    wrapped(draw, (72, 126), title, F["title"], INK, 910, 8, max_lines=2)
    if subtitle:
        wrapped(draw, (72, 270), subtitle, F["body"], MUTED, 900, 7, max_lines=3)


def footer(draw: ImageDraw.ImageDraw, note="Software validated. Field validation pending."):
    draw.line((72, H - 96, W - 72, H - 96), fill=LINE, width=2)
    text(draw, (72, H - 64), note, fill=MUTED, f=F["tiny"])
    text(draw, (W - 72, H - 64), "No field-deployment claim", fill=MUTED, f=F["tiny"], anchor="ra")


def arrow(draw: ImageDraw.ImageDraw, start, end, color=LINE, width=5):
    draw.line((start, end), fill=color, width=width)
    sx, sy = start
    ex, ey = end
    ang = math.atan2(ey - sy, ex - sx)
    size = 22
    p1 = (ex - size * math.cos(ang - 0.45), ey - size * math.sin(ang - 0.45))
    p2 = (ex - size * math.cos(ang + 0.45), ey - size * math.sin(ang + 0.45))
    draw.polygon([end, p1, p2], fill=color)


def pill(draw: ImageDraw.ImageDraw, xy, label: str, color: str, fill: str):
    x, y = xy
    w = text_w(draw, label, F["small_b"]) + 44
    rounded(draw, (x, y, x + w, y + 50), 18, fill, color, 2)
    text(draw, (x + 22, y + 12), label, fill=color, f=F["small_b"])
    return x + w + 12


def slide_01():
    img, draw = canvas()
    header(draw, "01 / 06", "Most systems count vehicles.", "PTIS asks a different question.")

    rounded(draw, (72, 390, 486, 790), 30, CARD, LINE, 2)
    text(draw, (112, 430), "Traditional", fill=MUTED, f=F["small_b"])
    text(draw, (112, 494), "How many", fill=INK, f=F["title_sm"])
    text(draw, (112, 552), "vehicles are", fill=INK, f=F["title_sm"])
    text(draw, (112, 610), "here now?", fill=INK, f=F["title_sm"])
    rounded(draw, (112, 700, 300, 750), 16, SOFT_BLUE, BLUE, 2)
    text(draw, (136, 712), "reactive", fill=BLUE, f=F["small_b"])

    rounded(draw, (594, 390, 1008, 790), 30, CARD, LINE, 2)
    text(draw, (634, 430), "PTIS", fill=TEAL, f=F["small_b"])
    text(draw, (634, 494), "Where", fill=INK, f=F["title_sm"])
    text(draw, (634, 552), "are they", fill=INK, f=F["title_sm"])
    text(draw, (634, 610), "going?", fill=INK, f=F["title_sm"])
    rounded(draw, (634, 700, 824, 750), 16, SOFT_TEAL, TEAL, 2)
    text(draw, (658, 712), "predictive", fill=TEAL, f=F["small_b"])

    arrow(draw, (510, 590), (570, 590), "#94a3b8", 6)
    rounded(draw, (112, 900, 968, 1048), 26, SOFT_AMBER, "#fed7aa", 2)
    wrapped(draw, (150, 932), "One simple shift: use checkpoint observations to estimate destination pressure before a bottleneck fully forms.", F["body_b"], "#92400e", 760, 7)
    footer(draw)
    img.save(OUT / "ptis_simple_01_hook.png", quality=96)


def slide_02():
    img, draw = canvas()
    header(draw, "02 / 06", "Passing without turning is evidence.", "Every junction not taken reduces the possible destinations.")

    y = 560
    xs = [120, 300, 480, 660, 840]
    labels = ["Silk\nBoard", "HSR", "Sony", "Martha-\nhalli", "Whitefield"]
    colors = [BLUE, SLATE, SLATE, AMBER, TEAL]
    for i in range(len(xs) - 1):
        draw.line((xs[i] + 34, y, xs[i + 1] - 34, y), fill="#b8c7d6", width=10)
        draw.line((xs[i] + 34, y, xs[i + 1] - 34, y), fill=BLUE, width=4)
    for i, (x, label, color) in enumerate(zip(xs, labels, colors), start=1):
        draw.ellipse((x - 34, y - 34, x + 34, y + 34), fill="white", outline=LINE, width=2)
        draw.ellipse((x - 24, y - 24, x + 24, y + 24), fill=color)
        text(draw, (x, y - 15), str(i), fill="white", f=F["tiny"], anchor="ma")
        text(draw, (x, y + 55), label, fill=INK, f=F["small_b"], anchor="ma", align="center")

    rounded(draw, (112, 760, 968, 940), 28, CARD, LINE, 2)
    text(draw, (154, 798), "Signal", fill=TEAL, f=F["h3"])
    wrapped(draw, (154, 842), "If traffic passes HSR and Sony World without exiting, PTIS lowers those destination probabilities and raises downstream pressure.", F["body"], MUTED, 760, 7)

    rounded(draw, (112, 990, 968, 1118), 28, SOFT_TEAL, "#99f6e4", 2)
    text(draw, (154, 1028), "Validated replay example", fill=TEAL, f=F["small_b"])
    text(draw, (154, 1065), "Whitefield posterior: about 67%", fill=INK, f=F["h2"])
    footer(draw)
    img.save(OUT / "ptis_simple_02_signal.png", quality=96)


def slide_03():
    img, draw = canvas()
    header(draw, "03 / 06", "PTIS does not act on belief alone.", "A simulated activation must pass two gates.")

    gate_y = 425
    rounded(draw, (92, gate_y, 492, gate_y + 300), 30, CARD, LINE, 2)
    text(draw, (132, gate_y + 38), "Gate 1", fill=BLUE, f=F["small_b"])
    text(draw, (132, gate_y + 88), "Confidence", fill=INK, f=F["h2"])
    wrapped(draw, (132, gate_y + 146), "Is one destination becoming likely enough to consider action?", F["body"], MUTED, 310, 7)
    rounded(draw, (132, gate_y + 232, 292, gate_y + 278), 15, SOFT_BLUE, BLUE, 2)
    text(draw, (154, gate_y + 242), "about 67%", fill=BLUE, f=F["small_b"])

    rounded(draw, (588, gate_y, 988, gate_y + 300), 30, CARD, LINE, 2)
    text(draw, (628, gate_y + 38), "Gate 2", fill=GREEN, f=F["small_b"])
    text(draw, (628, gate_y + 88), "Capacity", fill=INK, f=F["h2"])
    wrapped(draw, (628, gate_y + 146), "Can the receiving route safely accept more flow right now?", F["body"], MUTED, 310, 7)
    rounded(draw, (628, gate_y + 232, 808, gate_y + 278), 15, SOFT_GREEN, GREEN, 2)
    text(draw, (650, gate_y + 242), "must pass", fill=GREEN, f=F["small_b"])

    arrow(draw, (492, gate_y + 150), (588, gate_y + 150), "#94a3b8", 6)

    rounded(draw, (112, 840, 968, 1038), 28, SOFT_AMBER, "#fed7aa", 2)
    wrapped(draw, (154, 878), "If capacity is full, PTIS blocks the action even when destination confidence is high.", F["h2"], "#92400e", 760, 8)
    footer(draw)
    img.save(OUT / "ptis_simple_03_gates.png", quality=96)


def metric_card(draw: ImageDraw.ImageDraw, box, value: str, label: str, color: str):
    x1, y1, x2, y2 = box
    rounded(draw, box, 26, CARD, LINE, 2)
    text(draw, (x1 + 28, y1 + 24), value, fill=color, f=F["metric"])
    wrapped(draw, (x1 + 28, y1 + 92), label, F["small_b"], MUTED, x2 - x1 - 56, 4, max_lines=2)


def slide_04():
    img, draw = canvas()
    header(draw, "04 / 06", "What is proven so far", "Reproducible software replay, not field deployment.")

    m = extreme["metrics"]
    cards = [
        ((72, 380, 506, 550), "29/29", "tests passed", GREEN),
        ((574, 380, 1008, 550), f"{suite['passed_count']}/{suite['scenario_count']}", "scenarios passed", GREEN),
        ((72, 590, 506, 760), f"{m['vehicle_count']:,}", "vehicles in stress replay", BLUE),
        ((574, 590, 1008, 760), f"{m['observation_count']:,}", "checkpoint observations", TEAL),
        ((72, 800, 506, 970), "0", "capacity violations", GREEN),
        ((574, 800, 1008, 970), "0", "false-positive activations", GREEN),
    ]
    for box, value, label, color in cards:
        metric_card(draw, box, value, label, color)

    rounded(draw, (112, 1050, 968, 1138), 24, SOFT_BLUE, "#bfdbfe", 2)
    text(draw, (154, 1078), "This proves the decision logic under replay.", fill=BLUE, f=F["body_b"])
    footer(draw)
    img.save(OUT / "ptis_simple_04_proof.png", quality=96)


def slide_05():
    img, draw = canvas()
    header(draw, "05 / 06", "Real evidence vs pending evidence", "This boundary is important.")

    rounded(draw, (72, 350, 506, 920), 30, SOFT_GREEN, "#bbf7d0", 2)
    text(draw, (112, 394), "Grounded today", fill=GREEN, f=F["h2"])
    y = 474
    done_items = [
        "Software tests and replay",
        "OSRM/OpenStreetMap route",
        "DULT/CMP planning context",
        "BMD-45 CCTV detection audit",
    ]
    for item in done_items:
        draw.ellipse((112, y + 8, 136, y + 32), fill=GREEN)
        text(draw, (120, y + 7), "OK", fill="white", f=F["tiny"])
        wrapped(draw, (154, y), item, F["body_b"], INK, 300, 4, max_lines=2)
        y += 96

    rounded(draw, (574, 350, 1008, 920), 30, SOFT_RED, "#fecaca", 2)
    text(draw, (614, 394), "Not claimed yet", fill=RED, f=F["h2"])
    y = 474
    pending_items = [
        "Live BTP integration",
        "Google Maps/Waze integration",
        "Public-road control",
        "Congestion reduction",
        "Field-proven OD prediction",
    ]
    for item in pending_items:
        draw.line((616, y + 20, 640, y + 20), fill=RED, width=4)
        wrapped(draw, (658, y), item, F["body_b"], INK, 290, 4, max_lines=2)
        y += 78

    rounded(draw, (112, 1010, 968, 1120), 26, CARD, LINE, 2)
    wrapped(draw, (154, 1042), "Public claim: software validated; field validation pending.", F["h2"], INK, 760, 6, max_lines=2)
    footer(draw)
    img.save(OUT / "ptis_simple_05_boundary.png", quality=96)


def slide_06():
    img, draw = canvas()
    header(draw, "06 / 06", "What would prove it in the field?", "The next step is better observed data, not bigger claims.")

    steps = [
        ("1", "Checkpoint counts", "Minute-by-minute observed flow at key ORR points", BLUE),
        ("2", "Capacity time series", "Measured spare capacity on the receiving route", TEAL),
        ("3", "Ground-truth labels", "Observed destination/OD labels for validation", AMBER),
        ("4", "Shadow pilot", "Run PTIS without controlling public roads first", GREEN),
    ]
    y = 380
    for n, title, detail, color in steps:
        rounded(draw, (112, y, 968, y + 138), 26, CARD, LINE, 2)
        draw.ellipse((150, y + 36, 214, y + 100), fill=color)
        text(draw, (182, y + 52), n, fill="white", f=F["h3"], anchor="ma")
        text(draw, (246, y + 30), title, fill=INK, f=F["h3"])
        wrapped(draw, (246, y + 72), detail, F["small"], MUTED, 660, 4, max_lines=2)
        y += 170

    footer(draw, "Next honest step: remote replay or agency-controlled shadow pilot.")
    img.save(OUT / "ptis_simple_06_next.png", quality=96)


def caption_file():
    caption = """Use this carousel instead of the dashboard-style image.

Slide order:
1. Most systems count vehicles. PTIS asks where they are going.
2. Passing without turning is evidence.
3. PTIS acts only if confidence and capacity gates pass.
4. What is proven in replay.
5. What is real vs what is not claimed yet.
6. What field evidence is needed next.

Safe public status: software validated, real route grounded, real CCTV detection evidence audited, official planning reference grounded, field validation pending.
"""
    (OUT / "README.md").write_text(caption, encoding="utf-8")


def main():
    slide_01()
    slide_02()
    slide_03()
    slide_04()
    slide_05()
    slide_06()
    caption_file()
    print(json.dumps({
        "output_dir": str(OUT),
        "slides": [p.name for p in sorted(OUT.glob("ptis_simple_*.png"))],
    }, indent=2))


if __name__ == "__main__":
    main()