"""Render the story infographics as crisp PNG images in the deck's style.

Tableau Public's web renderer sizes mark-based diagrams differently from Desktop, so the
diagrams for the text-only story cards are drawn here as images (the approach top Tableau
Public authors use for infographic elements) and placed on the dashboards as image objects.
Every value comes from data/story_diagrams.csv, which build_tableau.py writes from the model,
so the images update with each quarterly refresh.
"""
import csv
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from titlecase import tc

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tableau" / "_images"
FONT_DIR = Path("/usr/share/fonts/opentype/inter")
S = 2  # render at 2x for sharp text on high-density screens

TONE = {"blue": "#a9c8f0", "blue light": "#d6e6fa", "orange": "#f7c79b", "orange light": "#fbe2cc",
        "green": "#a8dcc1", "green light": "#d4eedf", "purple": "#c9c0f2", "purple light": "#e4dff9",
        "teal": "#a6dcd8", "teal light": "#d3eeec", "red": "#f2b1b0", "red light": "#f9d8d7",
        "gray": "#d0d4dc", "gray light": "#e8eaee", "pink": "#f3bdd3", "yellow": "#f6dc9a", "arrow": "#ffffff"}
INK, INK2, MUTED = "#1f2a44", "#3b4660", "#5b6475"


def font(weight, size):
    name = {"regular": "Inter-Regular.otf", "medium": "Inter-Medium.otf", "semibold": "Inter-SemiBold.otf", "bold": "Inter-Bold.otf"}[weight]
    path = FONT_DIR / name
    if not path.exists():
        path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if weight in ("semibold", "bold") else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(str(path), size * S)


def wrap(d, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def centered(d, box, rows):
    """rows: list of (text, font, color); draws them centred in box, wrapping each to the box width."""
    x0, y0, x1, y1 = box
    laid = []
    for text, f, col in rows:
        if not text.strip(): continue
        for ln in wrap(d, text, f, (x1 - x0) - 16 * S):
            laid.append((ln, f, col))
    heights = [f.getbbox("Ag")[3] + 4 * S for _, f, _ in laid]
    y = y0 + ((y1 - y0) - sum(heights)) / 2
    for (ln, f, col), h in zip(laid, heights):
        w = d.textlength(ln, font=f)
        d.text((x0 + ((x1 - x0) - w) / 2, y), ln, font=f, fill=col)
        y += h


def canvas(w, h, title, sub):
    im = Image.new("RGB", (w * S, h * S), "#ffffff")
    d = ImageDraw.Draw(im)
    y = 4 * S
    d.text((6 * S, y), tc(title), font=font("semibold", 14), fill=INK)
    y += 22 * S
    if sub:
        d.text((6 * S, y), sub, font=font("regular", 10), fill=MUTED)
        y += 18 * S
    return im, d, y + 4 * S


def arrow(d, x0, y0, x1, y1, col="#8392ad"):
    d.line((x0, y0, x1, y1), fill=col, width=2 * S)
    if abs(x1 - x0) >= abs(y1 - y0):
        s = 1 if x1 > x0 else -1
        d.polygon([(x1, y1), (x1 - s * 7 * S, y1 - 5 * S), (x1 - s * 7 * S, y1 + 5 * S)], fill=col)
    else:
        s = 1 if y1 > y0 else -1
        d.polygon([(x1, y1), (x1 - 5 * S, y1 - s * 7 * S), (x1 + 5 * S, y1 - s * 7 * S)], fill=col)


def load():
    rows = list(csv.DictReader(open(ROOT / "data" / "story_diagrams.csv")))
    by = {}
    for r in rows:
        r["col"], r["row"] = int(r["col"]), int(r["row"])
        r["title"] = tc(r["title"])  # box titles are headings, so they take title case
        by.setdefault(r["diagram"], []).append(r)
    return by


def launch_flow(cells, w, h, path):
    im, d, top = canvas(w, h, "How the story follows a launch", "Read top to bottom; each step is one or more story points")
    cells = sorted(cells, key=lambda r: r["row"])
    n, gap = len(cells), 12 * S
    bh = ((h * S - top - 6 * S) - gap * (n - 1)) / n
    for i, c in enumerate(cells):
        y0 = top + i * (bh + gap)
        d.rounded_rectangle((6 * S, y0, w * S - 6 * S, y0 + bh), radius=8 * S, fill=TONE[c["tone"]])
        centered(d, (6 * S, y0, w * S - 6 * S, y0 + bh), [(c["title"], font("semibold", 12), INK), (c["line1"], font("regular", 10), INK2)])
        if i < n - 1:
            arrow(d, w * S / 2, y0 + bh + 1 * S, w * S / 2, y0 + bh + gap - 1 * S)
    im.save(path)


def kpi_tiles(cells, w, h, path, title, sub):
    im, d, top = canvas(w, h, title, sub)
    cells = sorted(cells, key=lambda r: r["col"])
    n, gap = len(cells), 8 * S
    tw = ((w * S - 12 * S) - gap * (n - 1)) / n
    for i, c in enumerate(cells):
        x0 = 6 * S + i * (tw + gap)
        box = (x0, top, x0 + tw, h * S - 6 * S)
        d.rounded_rectangle(box, radius=8 * S, fill=TONE[c["tone"]])
        centered(d, box, [(c["title"], font("semibold", 10), INK2), (c["line1"], font("bold", 22), INK), (c["line2"], font("regular", 9), INK2)])
    im.save(path)


def decision_tree(cells, w, h, path):
    im, d, top = canvas(w, h, "Which path fits you?", "Start at the top; a different answer moves you down a row")
    rows = max(c["row"] for c in cells)
    gap = 13 * S
    rh = ((h * S - top - 6 * S) - gap * (rows - 1)) / rows
    cw = [0.47, 0.13, 0.40]
    xs = [6 * S]
    for f in cw: xs.append(xs[-1] + f * (w * S - 12 * S))
    for c in cells:
        y0 = top + (c["row"] - 1) * (rh + gap)
        x0, x1 = xs[c["col"] - 1], xs[c["col"]]
        if c["tone"] == "arrow":
            centered(d, (x0, y0, x1, y0 + rh), [(c["title"], font("semibold", 10), INK2)])
            continue
        d.rounded_rectangle((x0 + 2 * S, y0, x1 - 2 * S, y0 + rh), radius=6 * S, fill=TONE[c["tone"]])
        centered(d, (x0 + 2 * S, y0, x1 - 2 * S, y0 + rh), [(c["title"], font("semibold" if c["col"] == 3 else "medium", 10), INK)])
    # "No" connectors down the question column
    for r in range(1, rows - 1):
        y = top + r * (rh + gap) - gap / 2
        d.text((xs[0] + 8 * S, y - 6 * S), "No ↓", font=font("medium", 8), fill=MUTED)
    im.save(path)


def pipeline(cells, w, h, path):
    im, d, top = canvas(w, h, "How every number is made", "")
    cells = sorted(cells, key=lambda r: r["col"])
    n, gap = len(cells), 26 * S
    bw = ((w * S - 12 * S) - gap * (n - 1)) / n
    for i, c in enumerate(cells):
        x0 = 6 * S + i * (bw + gap)
        box = (x0, top, x0 + bw, h * S - 6 * S)
        d.rounded_rectangle(box, radius=8 * S, fill=TONE[c["tone"]])
        centered(d, box, [(c["title"].replace("  →", ""), font("semibold", 11), INK), (c["line1"], font("regular", 9), INK2)])
        if i < n - 1:
            ym = (top + h * S - 6 * S) / 2
            arrow(d, x0 + bw + 4 * S, ym, x0 + bw + gap - 4 * S, ym)
    im.save(path)


def render(sizes):
    """sizes: {key: (width_px, height_px)} of each image zone's inner area on its dashboard."""
    OUT.mkdir(parents=True, exist_ok=True)
    by = load()
    files = {}
    def p(k): files[k] = OUT / f"info_{k}.png"; return files[k]
    launch_flow(by["Launch flow"], *sizes["launch"], p("launch"))
    kpi_tiles(by["KPI strip 1"], *sizes["kpi"], p("kpi1"), "KPIs 1 to 7 at a glance", "Blue: money kept per sale. Orange: breakeven. Headline values use the KDP route")
    kpi_tiles(by["KPI strip 2"], *sizes["kpi"], p("kpi2"), "KPIs 8 to 14 at a glance", "Purple: scale. Teal: cash timing. Gray: Kindle Unlimited. Red: testing")
    decision_tree(by["Decision tree"], *sizes["tree"], p("tree"))
    pipeline(by["Pipeline"], *sizes["pipe"], p("pipe"))
    return files
