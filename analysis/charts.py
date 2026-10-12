"""Render every chart in /charts (single charts) and /charts/pages (two-panel slide pages).

Each chart carries a plain-language note written so a 12-year-old can follow it,
plus an "as of" stamp and its source line.
"""
import csv, json, textwrap, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.ticker import PercentFormatter, FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
D, C = ROOT / "data", ROOT / "charts"
P = C / "pages"; C.mkdir(exist_ok=True); P.mkdir(exist_ok=True)
ASOF = json.load(open(ROOT / "as_of.json"))["as_of_label"]
for f in fm.findSystemFonts():
    if "Inter" in f: fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Inter", "font.size": 11, "axes.edgecolor": "#c9c8c2", "axes.labelcolor": "#52514e",
    "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e9e8e4", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    "axes.titlesize": 13.5, "axes.titleweight": "semibold", "axes.titlecolor": "#0b0b0b", "axes.titlelocation": "left",
    "text.parse_math": False,
})
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
COL = {"Amazon KDP": "#2a78d6", "IngramSpark": "#eb6834", "B&N Press": "#1baf7a", "Lulu Retail": "#eda100",
       "Lulu Bookstore": "#c98500", "Lulu": "#eda100", "PublishDrive": "#e87ba4", "Draft2Digital": "#008300",
       "Draft2Digital (ebook only)": "#008300", "Apple Books direct": "#6250d6", "KDP Expanded Distribution": "#e34948", "KDP Expanded Dist.": "#e34948"}
POS, NEG = "#2a78d6", "#e34948"
CC = {"Platform fee": "#4e79a7", "Production cost": "#f28e2b", "Channel share": "#e15759", "Net royalty to IP owner": "#76b7b2"}
LEG = {"Channel share": "Store's cut (channel share)", "Net royalty to IP owner": "What the creator keeps (net royalty)",
       "Platform fee": "Platform fees", "Production cost": "Printing (production cost)"}
CV = {"Platform fee": "#4e79a7", "Production cost": "#f28e2b", "Channel share": "#e15759"}

SHORT = {"KDP Expanded Distribution": "KDP Expanded Dist."}
def rd(name):
    rows = list(csv.DictReader(open(D / name)))
    for r in rows:
        for k in ("platform",):
            if k in r and r[k] in SHORT: r[k] = SHORT[r[k]]
    return rows
def money(x, d=2): return f"-${abs(x):,.{d}f}" if x < 0 else f"${x:,.{d}f}"
HL = "#c2410c"   # highlight ink for in-graph callouts
def callout(ax, text, xy, xytext, color=HL, ha="left", va="center", coords="data", fs=9, arrow=True, **kw):
    """Boxed in-graph note with an arrow pointing at the insight."""
    ax.annotate(text, xy=xy, xytext=xytext, textcoords=coords, ha=ha, va=va, fontsize=fs, color=color, weight="semibold",
                bbox=dict(boxstyle="round,pad=0.3", fc="#fffaf0", ec=color, lw=1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.2, connectionstyle="arc3,rad=0.15") if arrow else None,
                zorder=9, annotation_clip=False, **kw)

# ------------------------------------------------------------------ chart definitions
# Each function draws on the axes it is given (or a SubplotSpec for multi-axis charts)
# and returns (plain-language note, source line).

def c_isbn(ax):
    rows = rd("market_bowker_isbn.csv"); yrs = sorted({int(r["year"]) for r in rows})
    sp = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Self-published"]
    tr = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Traditional"]
    ax.stackplot(yrs, tr, sp, colors=["#f28e2b", "#4e79a7"], alpha=0.9, edgecolor="#fcfcfb", linewidth=2)
    ax.plot(yrs, [a+b for a, b in zip(tr, sp)], color=INK, lw=2, marker="o", ms=6)
    for y, t, s in zip(yrs, tr, sp):
        ax.annotate(f"{t+s:.2f}M", (y, t+s), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10, color=INK)
    ax.text(2022.05, tr[0]/2, "Traditional", color="white", fontsize=10, va="center", weight="semibold")
    ax.text(2022.05, tr[0]+sp[0]/2, "Self-published", color="white", fontsize=10, va="center", weight="semibold")
    ax.annotate("", xy=(2025, tr[-1]+sp[-1]), xytext=(2024, tr[-2]+sp[-2]), arrowprops=dict(arrowstyle="-|>", color="#e15759", lw=2.2))
    ax.text(2024.5, (tr[-1]+sp[-1]+tr[-2]+sp[-2])/2 + 0.35, "+32.5% total\n(+1.02M ISBNs)", ha="center", fontsize=9.5, color="#e15759", weight="semibold")
    ax.text(2024.92, 2.2, "Self-published\n+38.7% in 2025", color="white", fontsize=10.5, ha="right", va="center", weight="semibold")
    from matplotlib.patches import Patch
    ax.legend([Patch(color="#4e79a7"), Patch(color="#f28e2b"), Line2D([], [], color=INK, marker="o")],
              ["Self-published (authors on their own)", "Traditional (publishing houses)", "Total ISBNs"], frameon=False, fontsize=9, loc="upper left")
    ax.set_xticks(yrs); ax.set_ylabel("ISBNs issued (millions)"); ax.set_ylim(0, 5.4); ax.set_xlim(2021.85, 2025.2)
    ax.set_title("U.S. ISBN output: self-published titles drive growth (stacked)")
    return ('Every book edition gets an ID number called an ISBN, so counting ISBNs shows how many new books come out. Self-published titles (blue) jumped 38.7% in 2025 while printed-book sales stayed flat. More books are competing for the same buyers, which makes the share of each sale you keep more important.',
            "Bowker data via Publishers Weekly, March 23, 2026")

def c_aap(ax):
    rows = rd("market_aap_formats_2025.csv")[::-1]
    ax.barh([r["format"] for r in rows], [float(r["revenue_billions"]) for r in rows], color="#2a78d6", height=0.55)
    for i, r in enumerate(rows):
        ax.text(float(r["revenue_billions"])+0.1, i, f"${float(r['revenue_billions']):.1f}B ({float(r['yoy_change']):+.1%})", va="center", fontsize=10, color=INK)
    total = float(next(r["value"] for r in rd("market_headlines.csv") if r["metric"].startswith("U.S. publisher revenue")).strip("$B"))
    names = [r["format"] for r in rows]; vals = {r["format"]: float(r["revenue_billions"]) for r in rows}
    pr = vals["Hardback"] + vals["Paperback"]; ih, ip = names.index("Hardback"), names.index("Paperback")
    ax.axhspan(min(ih, ip) - 0.4, max(ih, ip) + 0.4, color="#2a78d6", alpha=0.07, zorder=0)
    ax.annotate("", xy=(10.75, min(ih, ip) - 0.3), xytext=(10.75, max(ih, ip) + 0.3), arrowprops=dict(arrowstyle="-", color=HL, lw=2))
    ax.text(10.95, (ih + ip) / 2, f"Print:\n${pr:.1f}B,\n{pr/total:.0%} of\n${total:.1f}B", ha="left", va="center", fontsize=9, color=HL, weight="semibold")
    fast = max(rows, key=lambda r: float(r["yoy_change"])); fi = names.index(fast["format"])
    ax.plot(float(fast["revenue_billions"]) + 2.75, fi, marker="*", ms=14, color=HL, zorder=6)
    callout(ax, "Fastest growth", (float(fast["revenue_billions"]) + 2.95, fi), (float(fast["revenue_billions"]) + 4.3, fi - 0.55))
    ax.set_xlim(0, 12.6); ax.set_xlabel("2025 U.S. publisher revenue ($ billions)"); ax.grid(axis="y", visible=False)
    ax.set_title("Print still earns the most; audio grows fastest")
    return ('This splits 2025 U.S. book revenue by format. Hardbacks and paperbacks still bring in about $16 billion of the $33.4 billion total, while audiobooks are smaller but grew fastest (+5.3%). That is why print distribution choices carry the most dollars.',
            "Association of American Publishers, StatShot Annual Report 2025")

def c_gtn(ax):
    rows = rd("price_waterfall_long.csv"); plats = [p["platform"] for p in rd("print_unit_economics.csv")]
    comps = ["Net royalty to IP owner", "Production cost", "Platform fee", "Channel share"]
    get = lambda p, c: float(next(r["amount"] for r in rows if r["platform"] == p and r["format"] == "Print" and r["component"] == c))
    order = sorted(plats, key=lambda p: get(p, comps[0]))
    for i, p in enumerate(order):
        left = 0
        for c in comps:
            v = get(p, c)
            ax.barh(i, v, left=left, color=CC[c], height=0.62, edgecolor="#fcfcfb", linewidth=2, label=LEG[c] if i == 0 else None)
            if c == comps[0]: ax.text(left+v/2, i, money(v), ha="center", va="center", color=INK, fontsize=9.5, weight="semibold")
            left += v
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.set_xlim(0, 17.2)
    ax.set_xlabel("Where each $16.99 of list price goes (print)"); ax.grid(axis="y", visible=False)
    ax.legend(ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=9, handlelength=1.2, columnspacing=1)
    # marker: bracket showing the KDP vs IngramSpark gap in what the creator keeps
    iy, ik = order.index("IngramSpark"), order.index("Amazon KDP")
    kx, ix = get("Amazon KDP", comps[0]), get("IngramSpark", comps[0])
    ax.vlines(kx, iy - 0.35, ik + 0.35, colors=INK, linestyles=":", lw=1.4, zorder=6)
    ax.annotate("", xy=(kx, iy - 0.45), xytext=(ix, iy - 0.45), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.4, shrinkA=0, shrinkB=0), zorder=7)
    ax.text((kx + ix) / 2, iy - 0.47, "KDP keeps $3.46 more", ha="center", va="top", fontsize=8.5, color=INK, weight="semibold",
            bbox=dict(boxstyle="round,pad=0.15", fc="#fcfcfb", ec="none"), zorder=8)
    ax.set_title("Gross-to-net: who gets paid from a $16.99 book", pad=50)
    return ("Each bar is one $16.99 book split by who gets paid. Red is the store's cut, orange is printing, blue is platform fees, and teal is what the creator keeps. KDP leaves the creator $6.79, while IngramSpark's bookstore route leaves $3.33. Finance teams call this breakdown gross-to-net.",
            "Platform rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive (see Sources)")

def c_ebook(ax):
    eu = rd("ebook_unit_economics.csv"); eu.sort(key=lambda r: float(r["net_royalty"]))
    names = [r["platform"] for r in eu]
    ax.barh(names, [float(r["net_royalty"]) for r in eu], color=[COL.get(n, "#2a78d6") for n in names], height=0.6)
    for i, r in enumerate(eu):
        ax.text(float(r["net_royalty"])+0.04, i, f"{money(float(r['net_royalty']))} ({float(r['net_margin_pct']):.0%})", va="center", fontsize=9.5, color=INK)
    top = max(float(r["net_royalty"]) for r in eu)
    ax.axvline(top, color=HL, ls="--", lw=1.3, zorder=4)
    ax.text(top + 0.04, -1.05, f"Best possible:\n{money(top)} (70%)", ha="left", va="center", fontsize=8.5, color=HL, weight="semibold")
    agg = [r for r in eu if r["platform"] in ("Draft2Digital", "IngramSpark")]
    lo_a = min(float(r["net_royalty"]) for r in agg); hi_a = max(float(r["net_royalty"]) for r in agg)
    ia = [names.index(r["platform"]) for r in agg]
    ax.fill_betweenx([min(ia) - 0.4, max(ia) + 0.4], lo_a, top, color=HL, alpha=0.10, zorder=0)
    callout(ax, f"Middlemen cost {(top-hi_a)*100:.0f} to {(top-lo_a)*100:.0f} cents a sale", (lo_a + 0.1, min(ia) - 0.4), (0.1, -1.05))
    ax.set_ylim(-1.5, len(eu) - 0.45)
    ax.set_xlim(0, 4.6); ax.grid(axis="y", visible=False); ax.set_xlabel("Creator keeps per $4.99 ebook")
    ax.set_title("Ebooks: selling direct keeps the most")
    return ('For a $4.99 ebook, each bar shows what the creator keeps after the store and any middleman are paid. Selling directly to Apple or B&N keeps $3.49. Aggregators like Draft2Digital keep 35 to 52 cents more per sale in exchange for sending your book to many stores with one upload.',
            "ScribeCount store rates; KDP, Draft2Digital and IngramSpark terms")

def c_variance(ax):
    pu = {r["platform"]: r for r in rd("print_unit_economics.csv")}
    others = sorted([p for p in pu if p != "Amazon KDP"], key=lambda p: float(pu[p]["variance_vs_kdp"]))
    drv = [("Channel share", "var_channel_share"), ("Production cost", "var_production"), ("Platform fee", "var_platform_fee")]
    for i, p in enumerate(others):
        pos = neg = 0
        for lab, k in drv:
            v = float(pu[p][k])
            if v >= 0: ax.barh(i, v, left=pos, color=CV[lab], height=0.6, edgecolor="#fcfcfb", linewidth=2, label=LEG[lab] if i == 0 else None); pos += v
            else: ax.barh(i, v, left=neg, color=CV[lab], height=0.6, edgecolor="#fcfcfb", linewidth=2, label=LEG[lab] if i == 0 else None); neg += v
        tot = float(pu[p]["variance_vs_kdp"])
        ax.plot(tot, i, marker="D", color=INK, ms=7, zorder=5)
        ax.text(max(pos, 0)+0.2, i, f"{money(tot)}", va="center", fontsize=9.5, color=INK, weight="semibold")
    ax.axvline(0, color=INK2, lw=1)
    ax.axvspan(0, 9.5, color="#1baf7a", alpha=0.05, zorder=0); ax.axvspan(-8, 0, color="#e34948", alpha=0.04, zorder=0)
    ax.text(9.3, -0.75, "Better than KDP", ha="right", fontsize=8.5, color="#13795a", weight="semibold")
    ax.text(-7.8, -0.75, "Worse than KDP", ha="left", fontsize=8.5, color="#b4232a", weight="semibold")
    ii = others.index("IngramSpark"); ics = float(pu["IngramSpark"]["var_channel_share"]); itot = float(pu["IngramSpark"]["variance_vs_kdp"])
    callout(ax, f"Store's cut = {money(abs(ics))} of the\n{money(abs(itot))} IngramSpark gap", (ics / 2, ii), (2.1, ii + 0.5))
    ax.set_ylim(-1.1, len(others) - 0.4)
    ax.set_yticks(range(len(others))); ax.set_yticklabels(others); ax.grid(axis="y", visible=False)
    ax.set_xlim(-8, 9.5); ax.set_xlabel("$ per print copy vs Amazon KDP (right = better)")
    h, l = ax.get_legend_handles_labels(); h.append(Line2D([], [], marker="D", color=INK, ls="")); l.append("Total gap vs KDP")
    ax.legend(h, l, ncol=2, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=9, frameon=False, handlelength=1.2, columnspacing=1)
    ax.set_title("Cost variance: why each option pays more or less than KDP", pad=50)
    return ("This is a cost variance analysis: every option is compared with Amazon KDP. Bars left of zero mean you keep less per book than on KDP, and each color is one cause (red = store's cut, orange = printing, blue = platform fees). For most options, the store's cut explains most of the gap.",
            "Model in this repository; KDP print royalty of $6.79 is the baseline")

def c_tornado(ax):
    rows = rd("sensitivity_tornado.csv"); rows.sort(key=lambda r: float(r["swing"]))
    for i, r in enumerate(rows):
        b, lo, hi = float(r["base_net"]), float(r["net_at_minus20"]), float(r["net_at_plus20"])
        ax.barh(i, lo-b, left=b, color=NEG, height=0.55, label="Earnings if the input is 20% lower" if i == 0 else None)
        ax.barh(i, hi-b, left=b, color=POS, height=0.55, label="Earnings if the input is 20% higher" if i == 0 else None)
        ax.plot(b, i, marker="|", color=INK, ms=20, mew=2, zorder=5)
        ax.text(max(lo, hi)+0.1, i, f"range {money(min(lo,hi))} to {money(max(lo,hi))}", va="center", fontsize=9, color=INK)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{r['platform']}: {r['input'].replace(' ±20%','')}" for r in rows])
    ax.grid(axis="y", visible=False); ax.set_xlabel("Creator keeps per print copy ($)"); ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.plot([], [], marker="|", color=INK, ls="", ms=12, mew=2, label="Base case today")
    ax.legend(frameon=False, loc="lower left", fontsize=8.5)
    top = rows[-1]; ti = len(rows) - 1
    lo_t, hi_t = sorted((float(top["net_at_minus20"]), float(top["net_at_plus20"])))
    ax.add_patch(matplotlib.patches.FancyBboxPatch((lo_t - 0.08, ti - 0.36), hi_t - lo_t + 0.16, 0.72, boxstyle="round,pad=0.02", fc="none", ec=HL, lw=2, zorder=6))
    callout(ax, f"Biggest lever: price\nmoves earnings {money(hi_t - lo_t)} a copy", (hi_t + 0.08, ti - 0.3), (8.9, ti - 1.0), ha="left")
    ax.set_xlim(0, 13); ax.set_title("Sensitivity: which number matters most?")
    return ('Sensitivity analysis changes one input by 20% up or down while holding everything else steady. The wider the bar, the more that input moves your earnings. List price has the biggest effect, which is why price is the first thing worth testing.',
            "Model in this repository; each input flexed 20% with others held steady")

def c_be_units(ax):
    be = rd("breakeven.csv"); be.sort(key=lambda r: -int(r["breakeven_unit_pairs"]))
    names = [r["stack"].replace(" (ebook only)", "\n(ebook only)") for r in be]
    ax.barh(names, [int(r["breakeven_unit_pairs"]) for r in be], color=[COL[r["stack"]] for r in be], height=0.6)
    for i, r in enumerate(be):
        ax.text(int(r["breakeven_unit_pairs"])+6, i, f"{r['breakeven_unit_pairs']} pairs", va="center", fontsize=9.5, color=INK)
    bmin = min(be, key=lambda r: int(r["breakeven_unit_pairs"])); bmax = max(be, key=lambda r: int(r["breakeven_unit_pairs"]))
    vmin, vmax = int(bmin["breakeven_unit_pairs"]), int(bmax["breakeven_unit_pairs"])
    ax.axvline(vmin, color=HL, ls="--", lw=1.3, zorder=4)
    ax.text(vmin + 4, len(be) - 0.45, f"Fastest: {vmin} pairs", fontsize=8.5, color=HL, weight="semibold", va="bottom")
    callout(ax, f"{vmax / vmin:.1f}x as many sales\nas the fastest route", (vmax, 0.25), (vmax - 40, 1.5), ha="right")
    ax.set_ylim(-0.6, len(be) - 0.1)
    ax.set_xlim(0, 620); ax.grid(axis="y", visible=False); ax.set_xlabel("Sales (1 print + 1 ebook) to earn back Year-1 costs")
    ax.set_title("Breakeven: how many sales to earn back the start-up cost?")
    return ("Breakeven is the number of sales needed to earn back what you spent to launch: the copyright fee, platform fees and a production budget. Each sale's contribution chips away at that total. KDP gets there after 158 sales of a print book plus an ebook; Draft2Digital alone needs 511.",
            "Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions")

def c_be_curve(ax):
    cv = rd("breakeven_curve.csv")
    for s in [r["stack"] for r in rd("breakeven.csv")]:
        pts = [r for r in cv if r["stack"] == s]
        ax.plot([int(p["unit_pairs"]) for p in pts], [float(p["cumulative_profit"]) for p in pts], color=COL[s], lw=2, label=s)
    for r in rd("breakeven.csv"):
        u = int(r["breakeven_unit_pairs"])
        if u <= 600: ax.plot(u, 0, marker="o", ms=8, color=COL[r["stack"]], markeredgecolor=INK, zorder=6)
    bvals = [int(r["breakeven_unit_pairs"]) for r in rd("breakeven.csv")]
    ax.axvspan(min(bvals), max(bvals), ymin=0, ymax=1, color="#eda100", alpha=0.08, zorder=0)
    ax.text(min(bvals) + 6, -1850, f"Breakeven range: {min(bvals)} to {max(bvals)} pairs", ha="left", fontsize=8.5, color=HL, weight="semibold")
    ax.plot([], [], marker="o", ls="", color="#cccccc", markeredgecolor=INK, label="Breakeven point")
    ax.axhline(0, color=INK, lw=1.4)
    ax.fill_between([0, 600], -2000, 0, color="#e34948", alpha=0.05)
    ax.text(590, -1450, "Below the line = still paying back costs", ha="right", fontsize=9, color=INK2)
    ax.annotate("KDP crosses zero at 158 pairs", xy=(158, 0), xytext=(230, -1200), arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlim(0, 600); ax.set_ylim(-2000, 4600); ax.set_xlabel("Sales so far (pairs)"); ax.set_ylabel("Total profit so far ($)")
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper left")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.set_title("Breakeven curves: profit climbs with every sale")
    return ('Each line tracks total profit as sales add up. Every line starts below zero because of launch costs, and the point where it crosses the black zero line is breakeven. Steeper lines mean each sale contributes more, so they reach profit sooner.',
            "Model in this repository")

def c_crossover(ax):
    cr = rd("crossover_publishdrive_ingramspark.csv"); x = [int(r["units_per_month"]) for r in cr]
    ax.plot(x, [float(r["IngramSpark"]) for r in cr], color=COL["IngramSpark"], lw=2.2, label="IngramSpark: fee on every sale")
    ax.plot(x, [float(r["PublishDrive"]) for r in cr], color=COL["PublishDrive"], lw=2.2, label="PublishDrive: flat $13.99 a month")
    xc = float(rd("crossover_summary.csv")[0]["crossover_units_per_month"])
    ax.axvline(xc, color=INK2, ls="--", lw=1)
    ax.plot(xc, xc*6.296, marker="o", ms=10, color="#fcfcfb", markeredgecolor=INK, mew=2, zorder=6, label="Switch point")
    ax.axvspan(0, xc, color="#eb6834", alpha=0.06); ax.axvspan(xc, 40, color="#e87ba4", alpha=0.06)
    ax.text(xc/2, -22, "Per-sale fee is cheaper", ha="center", fontsize=9, color=INK2, weight="semibold")
    ax.text((xc+40)/2, -22, "Flat fee is cheaper", ha="center", fontsize=9, color=INK2, weight="semibold")
    ax.set_ylim(-32, 285)
    ax.annotate(f"Switch point: {xc:.1f} sales of each\nformat per month", xy=(xc, xc*6.296), xytext=(xc+4, 45),
                arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlabel("Sales of each format per month"); ax.set_ylabel("Money kept per month ($)"); ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_xlim(0, 40); ax.set_title("Fixed fee vs per-sale cut: where they cross")
    return ('PublishDrive charges a flat $13.99 a month (pink line), while IngramSpark takes a small fee from every sale (orange line). At low sales the per-sale fee costs less, but past about 17 sales of each format a month the flat fee wins. This is the classic fixed-cost versus variable-cost trade-off.',
            "PublishDrive Help Center pricing; IngramSpark 2026 fees")

def c_scenarios(ax):
    sc = rd("scenario_analysis.csv"); stacks = [r["stack"] for r in rd("breakeven.csv")]
    for i, s in enumerate(stacks[::-1]):
        v = {r["scenario"]: float(r["year1_net"]) for r in sc if r["stack"] == s}
        ax.plot([v["Bear"], v["Bull"]], [i, i], color=COL[s], lw=3, alpha=0.35, solid_capstyle="round")
        for lab, mk in (("Bear", "o"), ("Base", "D"), ("Bull", "o")):
            ax.plot(v[lab], i, marker=mk, color=COL[s], ms=8 if lab == "Base" else 6, markeredgecolor="#fcfcfb")
        ax.text(v["Bull"]*1.15, i, f"base {money(v['Base'], 0)}", va="center", fontsize=9, color=INK)
    base = {r["stack"]: float(r["year1_net"]) for r in sc if r["scenario"] == "Base"}
    lead = sorted(base, key=base.get, reverse=True)
    ki = len(stacks) - 1 - stacks.index(lead[0])
    ax.add_patch(matplotlib.patches.FancyBboxPatch((300, ki - 0.38), 140000, 0.76, boxstyle="round,pad=0.02", fc="none", ec=HL, lw=1.6, zorder=6))
    callout(ax, f"Leader at every level; {money(base[lead[0]] - base[lead[1]], 0)}\nahead of {lead[1]} at normal sales", (base[lead[0]], ki - 0.38), (1200, ki - 1.35), ha="left")
    ax.plot([], [], marker="o", color="#8a8984", ls="", label="Slow (10/month) or great (250/month)")
    ax.plot([], [], marker="D", color="#8a8984", ls="", ms=8, label="Normal (50/month)")
    ax.plot([], [], color="#8a8984", lw=3, alpha=0.35, label="Range of outcomes")
    ax.legend(frameon=False, fontsize=8.5, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, handlelength=1.2, columnspacing=1)
    ax.set_xscale("log"); ax.set_xlim(200, 150000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.set_yticks(range(len(stacks))); ax.set_yticklabels([s.replace(" (ebook only)", " (ebook)") for s in stacks[::-1]])
    ax.grid(axis="y", visible=False); ax.set_xlabel("Year-1 money kept (log scale) at 10, 50 and 250 sales a month")
    ax.set_title("Scenarios: slow, normal and great sales", pad=30)
    return ("Scenario analysis asks 'what if?' at three sales levels: slow (10 a month), normal (50) and great (250). Each line runs from the slow result to the great result, with the diamond at normal. KDP finishes first in every case, so the decision holds up even if the sales forecast is off.",
            "Model in this repository; planning scenarios, not forecasts")

def c_cash(ax):
    ts = rd("hybrid_stack_24mo.csv"); chs = list(dict.fromkeys(r["channel"] for r in ts)); months = sorted({int(r["month"]) for r in ts})
    earned = [[float(r["cumulative_earned"]) for r in ts if r["channel"] == c] for c in chs]
    cash = [sum(float(r["cumulative_cash"]) for r in ts if int(r["month"]) == m) for m in months]
    ax.stackplot(months, *earned, colors=["#2a78d6", "#eb6834", "#008300"], labels=[f"Earned through {c}" for c in chs], alpha=0.9, edgecolor="#fcfcfb", linewidth=1.5)
    ax.plot(months, cash, color=INK, lw=2.2, ls="--", label="Cash actually received")
    gap = sum(e[11] for e in earned) - cash[11]
    tot12 = sum(e[11] for e in earned)
    ax.annotate("", xy=(12, tot12), xytext=(12, cash[11]), arrowprops=dict(arrowstyle="<->", color="#e15759", lw=2, shrinkA=0, shrinkB=0))
    ax.plot([12, 12], [cash[11], tot12], marker="o", color="#e15759", ls="", ms=6)
    ax.annotate(f"Month 12: {money(gap,0)} earned\nbut not yet paid", xy=(12, (cash[11]+tot12)/2), xytext=(14, cash[11]*0.45),
                arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlim(1, 24); ax.set_xlabel("Months after launch"); ax.set_ylabel("Total royalties ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left"); ax.set_title("Earned vs paid: money arrives late")
    return ('The stacked areas show royalties earned over 24 months, and the dashed line shows cash actually received. Stores pay two to three months after a sale, so earnings run ahead of cash, leaving $948 still owed at month 12. Accountants call this the difference between accrual and cash.',
            "Model in this repository; launch curve and 65/35 channel mix are illustrative")

def c_dso(ax):
    pt = rd("payout_timing.csv")
    ax.barh([r["platform"] for r in pt][::-1], [int(r["avg_days_sale_to_cash"]) for r in pt][::-1], color=[COL[r["platform"]] for r in pt][::-1], height=0.55)
    for i, r in enumerate(pt[::-1]):
        ax.text(int(r["avg_days_sale_to_cash"])+2, i, f"~{r['avg_days_sale_to_cash']} days", va="center", fontsize=10, color=INK)
    ax.axvline(45, color="#1baf7a", ls=":", lw=1.4); ax.axvline(105, color="#eb6834", ls=":", lw=1.4)
    ax.annotate("", xy=(105, 3.55), xytext=(45, 3.55), arrowprops=dict(arrowstyle="<->", color=INK, lw=1.3), annotation_clip=False)
    ax.text(75, 3.7, "60-day difference", ha="center", fontsize=9.5, color=INK, weight="semibold", annotation_clip=False) if False else ax.text(75, 3.75, "60-day difference", ha="center", fontsize=9.5, color=INK, weight="semibold")
    ax.set_ylim(-0.6, 4.1)
    ax.set_xlim(0, 135); ax.grid(axis="y", visible=False); ax.set_xlabel("Days from a sale until the money arrives")
    ax.set_title("Days sales outstanding: how long you wait to get paid")
    return ('Days sales outstanding (DSO) measures how long you wait to get paid after a sale. B&N Press pays in about 45 days, while IngramSpark takes about 105. Longer waits mean you need more cash on hand to cover costs in the meantime.',
            "B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by")

def c_kenp(ax):
    kp = rd("kenp_pool_rate.csv"); vals = [float(r["per_page_rate"])*1000 for r in kp]; mths = [r["month"][2:] for r in kp]
    mu, sd = st.mean(vals), st.stdev(vals)
    ax.fill_between(range(len(vals)), mu-sd, mu+sd, color="#2a78d6", alpha=0.10, label="Typical range (average ± 1 standard deviation)")
    ax.axhline(mu, color="#2a78d6", lw=1, ls="--")
    ax.plot(range(len(vals)), vals, color="#2a78d6", lw=2, marker="o", ms=6, label="Monthly pay per 1,000 pages read")
    hi, lo = vals.index(max(vals)), vals.index(min(vals))
    ax.annotate(f"High ${max(vals):.2f}", (hi, max(vals)), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9.5)
    ax.annotate(f"Low ${min(vals):.2f}", (lo, min(vals)), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=9.5)
    ax.text(0, mu+0.03, f"Average ${mu:.2f}", ha="left", fontsize=9.5, color=INK2)
    ax.annotate("", xy=(len(vals)-0.2, max(vals)), xytext=(len(vals)-0.2, min(vals)), arrowprops=dict(arrowstyle="<->", color="#e15759", lw=1.6), annotation_clip=False)
    ax.text(len(vals)+0.05, max(vals) - 0.02, f"Range\n${max(vals)-min(vals):.2f}\n(+{max(vals)/min(vals)-1:.0%})", fontsize=9, color="#e15759", va="top", weight="semibold")
    ax.set_xlim(-0.5, len(vals)+1.6)
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(mths, rotation=45, ha="right", fontsize=8.5)
    ax.set_ylim(3.9, 5.35); ax.set_ylabel("$ per 1,000 pages"); ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_title("Pool payouts: Kindle Unlimited pay changes monthly")
    return ('Kindle Unlimited pays authors from one shared monthly pot, split by pages read, so the rate per page changes every month. Over the past year it ranged from $4.19 to $5.01 per 1,000 pages, averaging $4.55. Treat this income as a range, not a fixed number.',
            "Profitable.app KENP tracker (author-reported), May 2025 to April 2026")

def c_ab(ax):
    ab = rd("ab_test_design.csv")
    labels = ["Print price\n$16.99 vs $14.99", "Store terms\n55% returnable\nvs 40% non-returnable", "Ebook price\n$4.99 vs $3.99"]
    vals = [float(r["breakeven_lift_required"]) for r in ab]
    ax.barh(labels[::-1], vals[::-1], color="#6250d6", height=0.55)
    for i, (v, r) in enumerate(zip(vals[::-1], ab[::-1])):
        n = r["visitors_per_arm_80pct_power"]
        ax.text(v+0.015, i, f"{v:.0%} more sales needed" + (f"\n~{int(n):,} shoppers per group" if n else "\ntrack monthly sales"), va="center", fontsize=9.5, color=INK)
    for i, v in enumerate(vals[::-1]):
        ax.plot(v, i, marker="|", ms=26, mew=3, color="#e15759", zorder=5)
    pv = [vals[0], vals[2]]
    ax.axvspan(min(pv), max(pv), color="#eda100", alpha=0.12, zorder=0)
    ax.text((min(pv) + max(pv)) / 2, 2.62, f"Price cuts: {min(pv):.0%} to {max(pv):.0%}", ha="center", fontsize=8.5, color=HL, weight="semibold")
    callout(ax, "Hardest bar to clear:\nreturns eat the margin", (vals[1], 1.28), (vals[1] + 0.05, 1.75), ha="left")
    ax.set_ylim(-0.6, 2.75)
    ax.plot([], [], marker="|", ls="", ms=12, mew=3, color="#e15759", label="Breakeven line: the bar to beat")
    ax.legend(frameon=False, loc="lower right", fontsize=8.5)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0)); ax.set_xlim(0, 1.35); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Extra sales the cheaper option needs just to break even"); ax.set_title("A/B tests: the bar a cheaper price must clear")
    return ('A cheaper price earns less per book, so it only helps if it sells enough extra copies. Each bar shows that minimum boost, called the breakeven lift. In an A/B test, switch to the cheaper option only if sales rise by more than the bar, measured with enough shoppers to trust the result.',
            "Model in this repository; two-proportion z-test, 95% confidence, 80% power")

CHARTS = [("01_market_isbn_stacked", c_isbn, (10, 4.6)), ("02_market_aap_formats", c_aap, (10, 4.2)),
          ("03_print_gross_to_net", c_gtn, (10, 5)), ("04_cost_variance_drivers", c_variance, (10, 5)),
          ("05_ebook_net_per_unit", c_ebook, (10, 4.6)), ("06_sensitivity_tornado", c_tornado, (10, 4.4)),
          ("07_breakeven_units", c_be_units, (10, 4.6)), ("08_breakeven_curve", c_be_curve, (10, 5)),
          ("09_crossover_breakeven", c_crossover, (10, 4.6)), ("10_scenario_analysis", c_scenarios, (10, 4.8)),
          ("11_hybrid_stack_accrual_vs_cash", c_cash, (10, 5)), ("12_payout_timing_dso", c_dso, (10, 4)),
          ("13_kenp_pool_volatility", c_kenp, (10, 4.6)), ("14_ab_test_breakeven_lift", c_ab, (10, 4.4))]
FN = {n: f for n, f, _ in CHARTS}

def note_box(nax, text, width_chars=None):
    text = f"As of {ASOF}: {text}"
    nax.axis("off")
    fig = nax.figure
    w_in = nax.get_position().width * fig.get_figwidth()
    width_chars = int(w_in * 11.6)
    nax.text(0, 1, "\n".join(textwrap.wrap(text, width_chars)), transform=nax.transAxes, va="top", ha="left",
             fontsize=11, color=INK, linespacing=1.45,
             bbox=dict(boxstyle="round,pad=0.7", facecolor="#fff6dc", edgecolor="#eda100", linewidth=1.2))

def stamp(fig, srcs):
    fig.text(0.01, 0.005, f"Data as of {ASOF}. Sources: " + "; ".join(srcs), fontsize=8.5, color=MUTED, ha="left", va="bottom")

def single(name, fn, size):
    fig = plt.figure(figsize=(size[0], size[1] + 1.8))
    gs = fig.add_gridspec(2, 1, height_ratios=[size[1], 1.35], hspace=0.42, left=0.2, right=0.97, top=0.86, bottom=0.07)
    ax = fig.add_subplot(gs[0]); note, src = fn(ax)
    note_box(fig.add_subplot(gs[1]), note, 120)
    stamp(fig, [src])
    fig.savefig(C / f"{name}.svg"); fig.savefig(C / f"{name}.png", dpi=180); plt.close(fig)

def page(name, left, right, ratio=(1, 1)):
    fig = plt.figure(figsize=(16, 8.3))
    gs = fig.add_gridspec(2, 2, height_ratios=[4.7, 1.75], width_ratios=ratio, hspace=0.42, wspace=0.5,
                          left=0.12, right=0.985, top=0.875, bottom=0.07)
    srcs = []
    for col, key in enumerate((left, right)):
        ax = fig.add_subplot(gs[0, col]); note, src = FN[key](ax); srcs.append(src)
        note_box(fig.add_subplot(gs[1, col]), note, int(78 * ratio[col] / (sum(ratio) / 2)))
    stamp(fig, srcs)
    fig.savefig(P / f"{name}.svg"); fig.savefig(P / f"{name}.png", dpi=150); plt.close(fig)

PAGES = [("p1_market", "01_market_isbn_stacked", "02_market_aap_formats", (1.1, 0.9)),
         ("p2_unit_economics", "03_print_gross_to_net", "05_ebook_net_per_unit", (1.15, 0.85)),
         ("p3_variance_sensitivity", "04_cost_variance_drivers", "06_sensitivity_tornado", (1, 1)),
         ("p4_breakeven", "07_breakeven_units", "08_breakeven_curve", (0.9, 1.1)),
         ("p5_scale", "09_crossover_breakeven", "10_scenario_analysis", (1, 1)),
         ("p6_cash", "11_hybrid_stack_accrual_vs_cash", "12_payout_timing_dso", (1.15, 0.85)),
         ("p7_uncertainty_testing", "13_kenp_pool_volatility", "14_ab_test_breakeven_lift", (1, 1))]

if __name__ == "__main__":
    for n, f, s in CHARTS: single(n, f, s)
    for n, l, r, ratio in PAGES: page(n, l, r, ratio)
    print("charts:", len(CHARTS), "pages:", len(PAGES))
