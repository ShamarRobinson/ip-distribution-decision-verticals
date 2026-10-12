"""Render every chart in /charts (single charts) and /charts/pages (two-panel slide pages).

Each chart carries a plain-language note written so a 12-year-old can follow it,
plus an "as of" stamp and its source line.
"""
import csv, json, textwrap, statistics as st
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
CC = {"Net royalty to IP owner": "#2a78d6", "Production cost": "#eda100", "Platform fee": "#e34948", "Channel share": "#b9b8b2"}

SHORT = {"KDP Expanded Distribution": "KDP Expanded Dist."}
def rd(name):
    rows = list(csv.DictReader(open(D / name)))
    for r in rows:
        for k in ("platform",):
            if k in r and r[k] in SHORT: r[k] = SHORT[r[k]]
    return rows
def money(x, d=2): return f"-${abs(x):,.{d}f}" if x < 0 else f"${x:,.{d}f}"

# ------------------------------------------------------------------ chart definitions
# Each function draws on the axes it is given (or a SubplotSpec for multi-axis charts)
# and returns (plain-language note, source line).

def c_isbn(ax):
    rows = rd("market_bowker_isbn.csv"); yrs = sorted({int(r["year"]) for r in rows})
    sp = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Self-published"]
    tr = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Traditional"]
    ax.stackplot(yrs, tr, sp, colors=["#6250d6", "#2a78d6"], alpha=0.9, edgecolor="#fcfcfb", linewidth=2)
    ax.plot(yrs, [a+b for a, b in zip(tr, sp)], color=INK, lw=2, marker="o", ms=6)
    for y, t, s in zip(yrs, tr, sp):
        ax.annotate(f"{t+s:.2f}M", (y, t+s), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10, color=INK)
    ax.text(2022.05, tr[0]/2, "Traditional", color="white", fontsize=10, va="center", weight="semibold")
    ax.text(2022.05, tr[0]+sp[0]/2, "Self-published", color="white", fontsize=10, va="center", weight="semibold")
    ax.text(2024.92, 2.2, "Self-published\n+38.7% in 2025", color="white", fontsize=10.5, ha="right", va="center", weight="semibold")
    ax.set_xticks(yrs); ax.set_ylabel("ISBNs issued (millions)"); ax.set_ylim(0, 4.8); ax.set_xlim(2021.85, 2025.2)
    ax.set_title("U.S. ISBN output: self-published titles drive growth (stacked)")
    return ("Every new book gets an ID number called an ISBN. The blue area is books people published on their own, "
            "and it jumped in 2025. More books means more competition for the same readers, so keeping more money from each sale matters.",
            "Bowker data via Publishers Weekly, March 23, 2026")

def c_aap(ax):
    rows = rd("market_aap_formats_2025.csv")[::-1]
    ax.barh([r["format"] for r in rows], [float(r["revenue_billions"]) for r in rows], color="#2a78d6", height=0.55)
    for i, r in enumerate(rows):
        ax.text(float(r["revenue_billions"])+0.1, i, f"${float(r['revenue_billions']):.1f}B ({float(r['yoy_change']):+.1%})", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, 11); ax.set_xlabel("2025 U.S. publisher revenue ($ billions)"); ax.grid(axis="y", visible=False)
    ax.set_title("Print still earns the most; audio grows fastest")
    return ("This shows where the money came from in 2025. Printed books (hardback and paperback) still bring in the most. "
            "Audiobooks are a smaller slice, but they grew the fastest.",
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
            ax.barh(i, v, left=left, color=CC[c], height=0.62, edgecolor="#fcfcfb", linewidth=2, label=c if i == 0 else None)
            if c == comps[0]: ax.text(left+v/2, i, money(v), ha="center", va="center", color="white", fontsize=9.5, weight="semibold")
            left += v
    ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.set_xlim(0, 17.2)
    ax.set_xlabel("Where each $16.99 of list price goes (print)"); ax.grid(axis="y", visible=False)
    ax.legend(ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), frameon=False, fontsize=9, handlelength=1.2, columnspacing=1)
    ax.set_title("Gross-to-net: who gets each slice of a $16.99 book", pad=26)
    return ("Think of each $16.99 book as a pizza. The store takes the gray slice, printing takes the yellow slice and fees take the red slice. "
            "The blue slice is what the creator keeps. A bigger blue slice is a better deal.",
            "Platform rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive (see Sources)")

def c_ebook(ax):
    eu = rd("ebook_unit_economics.csv"); eu.sort(key=lambda r: float(r["net_royalty"]))
    names = [r["platform"] for r in eu]
    ax.barh(names, [float(r["net_royalty"]) for r in eu], color=[COL.get(n, "#2a78d6") for n in names], height=0.6)
    for i, r in enumerate(eu):
        ax.text(float(r["net_royalty"])+0.04, i, f"{money(float(r['net_royalty']))} ({float(r['net_margin_pct']):.0%})", va="center", fontsize=9.5, color=INK)
    ax.set_xlim(0, 4.6); ax.grid(axis="y", visible=False); ax.set_xlabel("Creator keeps per $4.99 ebook")
    ax.set_title("Ebooks: selling direct keeps the most")
    return ("For a $4.99 ebook, a longer bar means more money for the creator. Selling straight to a store like Apple keeps the most. "
            "Middlemen that send your book to many stores keep a small piece for doing that work.",
            "ScribeCount store rates; KDP, Draft2Digital and IngramSpark terms")

def c_variance(ax):
    pu = {r["platform"]: r for r in rd("print_unit_economics.csv")}
    others = sorted([p for p in pu if p != "Amazon KDP"], key=lambda p: float(pu[p]["variance_vs_kdp"]))
    drv = [("Channel share", "var_channel_share"), ("Production cost", "var_production"), ("Platform fee", "var_platform_fee")]
    for i, p in enumerate(others):
        pos = neg = 0
        for lab, k in drv:
            v = float(pu[p][k])
            if v >= 0: ax.barh(i, v, left=pos, color=CC[lab], height=0.6, edgecolor="#fcfcfb", linewidth=2, label=lab if i == 0 else None); pos += v
            else: ax.barh(i, v, left=neg, color=CC[lab], height=0.6, edgecolor="#fcfcfb", linewidth=2, label=lab if i == 0 else None); neg += v
        tot = float(pu[p]["variance_vs_kdp"])
        ax.plot(tot, i, marker="D", color=INK, ms=7, zorder=5)
        ax.text(max(pos, 0)+0.2, i, f"{money(tot)}", va="center", fontsize=9.5, color=INK, weight="semibold")
    ax.axvline(0, color=INK2, lw=1)
    ax.set_yticks(range(len(others))); ax.set_yticklabels(others); ax.grid(axis="y", visible=False)
    ax.set_xlim(-8, 9.5); ax.set_xlabel("$ per print copy vs Amazon KDP (right = better)")
    h, l = ax.get_legend_handles_labels(); h.append(Line2D([], [], marker="D", color=INK, ls="")); l.append("Total gap")
    ax.legend(h, l, ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=9, frameon=False, handlelength=1.2, columnspacing=1)
    ax.set_title("Cost variance: why each option pays more or less than KDP", pad=26)
    return ("We line every option up against Amazon KDP. Bars to the left mean you keep less money per book than on KDP, and the colors show why. "
            "The gray piece, the store's cut, is almost always the biggest reason.",
            "Model in this repository; KDP print royalty of $6.79 is the baseline")

def c_tornado(ax):
    rows = rd("sensitivity_tornado.csv"); rows.sort(key=lambda r: float(r["swing"]))
    for i, r in enumerate(rows):
        b, lo, hi = float(r["base_net"]), float(r["net_at_minus20"]), float(r["net_at_plus20"])
        ax.barh(i, lo-b, left=b, color=NEG, height=0.55, label="Input 20% lower" if i == 0 else None)
        ax.barh(i, hi-b, left=b, color=POS, height=0.55, label="Input 20% higher" if i == 0 else None)
        ax.text(max(lo, hi)+0.1, i, f"swing {money(float(r['swing']))}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{r['platform']}: {r['input'].replace(' ±20%','')}" for r in rows])
    ax.grid(axis="y", visible=False); ax.set_xlabel("Creator keeps per print copy ($)"); ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.set_xlim(0, 11.5); ax.set_title("Sensitivity: which number matters most?")
    return ("We nudged each number up and down by 20% to see which one moves earnings the most. The widest bar wins: "
            "the book's price matters more than printing costs, so pick the price carefully and test it.",
            "Model in this repository; each input flexed 20% with others held steady")

def c_be_units(ax):
    be = rd("breakeven.csv"); be.sort(key=lambda r: -int(r["breakeven_unit_pairs"]))
    names = [r["stack"].replace(" (ebook only)", "\n(ebook only)") for r in be]
    ax.barh(names, [int(r["breakeven_unit_pairs"]) for r in be], color=[COL[r["stack"]] for r in be], height=0.6)
    for i, r in enumerate(be):
        ax.text(int(r["breakeven_unit_pairs"])+6, i, f"{r['breakeven_unit_pairs']} pairs", va="center", fontsize=9.5, color=INK)
    ax.set_xlim(0, 620); ax.grid(axis="y", visible=False); ax.set_xlabel("Sales (1 print + 1 ebook) to earn back Year-1 costs")
    ax.set_title("Breakeven: how many sales to earn back the start-up cost?")
    return ("Starting costs are like a hole you have to fill. Every sale adds a scoop of money. "
            "This shows how many scoops it takes to fill the hole. A shorter bar means you get your money back sooner.",
            "Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions")

def c_be_curve(ax):
    cv = rd("breakeven_curve.csv")
    for s in [r["stack"] for r in rd("breakeven.csv")]:
        pts = [r for r in cv if r["stack"] == s]
        ax.plot([int(p["unit_pairs"]) for p in pts], [float(p["cumulative_profit"]) for p in pts], color=COL[s], lw=2, label=s)
    ax.axhline(0, color=INK, lw=1.4)
    ax.fill_between([0, 600], -2000, 0, color="#e34948", alpha=0.05)
    ax.text(590, -1850, "Below the line = still paying back costs", ha="right", fontsize=9, color=INK2)
    ax.annotate("KDP crosses zero at 158 pairs", xy=(158, 0), xytext=(230, -1200), arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlim(0, 600); ax.set_ylim(-2000, 4600); ax.set_xlabel("Sales so far (pairs)"); ax.set_ylabel("Total profit so far ($)")
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper left")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.set_title("Breakeven curves: profit climbs with every sale")
    return ("Every line starts below zero because of starting costs, and each sale lifts it up. Where a line crosses the black zero line, "
            "that option has paid for itself. Everything above the line is profit. Steeper lines get there faster.",
            "Model in this repository")

def c_crossover(ax):
    cr = rd("crossover_publishdrive_ingramspark.csv"); x = [int(r["units_per_month"]) for r in cr]
    ax.plot(x, [float(r["IngramSpark"]) for r in cr], color=COL["IngramSpark"], lw=2.2, label="IngramSpark: small cut of each sale")
    ax.plot(x, [float(r["PublishDrive"]) for r in cr], color=COL["PublishDrive"], lw=2.2, label="PublishDrive: $13.99 monthly fee")
    xc = float(rd("crossover_summary.csv")[0]["crossover_units_per_month"])
    ax.axvline(xc, color=INK2, ls="--", lw=1)
    ax.annotate(f"Switch point: {xc:.1f} sales of each\nformat per month", xy=(xc, xc*6.296), xytext=(xc+4, 30),
                arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlabel("Sales of each format per month"); ax.set_ylabel("Money kept per month ($)"); ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_xlim(0, 40); ax.set_title("Fixed fee vs per-sale cut: where they cross")
    return ("One option charges a flat monthly fee (pink). The other takes a small cut of every sale (orange). "
            "If you sell only a few books, the cut is cheaper. Past about 17 sales of each format a month, the flat fee becomes the better deal.",
            "PublishDrive Help Center pricing; IngramSpark 2026 fees")

def c_scenarios(ax):
    sc = rd("scenario_analysis.csv"); stacks = [r["stack"] for r in rd("breakeven.csv")]
    for i, s in enumerate(stacks[::-1]):
        v = {r["scenario"]: float(r["year1_net"]) for r in sc if r["stack"] == s}
        ax.plot([v["Bear"], v["Bull"]], [i, i], color=COL[s], lw=3, alpha=0.35, solid_capstyle="round")
        for lab, mk in (("Bear", "o"), ("Base", "D"), ("Bull", "o")):
            ax.plot(v[lab], i, marker=mk, color=COL[s], ms=8 if lab == "Base" else 6, markeredgecolor="#fcfcfb")
        ax.text(v["Bull"]*1.15, i, f"base {money(v['Base'], 0)}", va="center", fontsize=9, color=INK)
    ax.set_xscale("log"); ax.set_xlim(200, 150000)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.set_yticks(range(len(stacks))); ax.set_yticklabels([s.replace(" (ebook only)", " (ebook)") for s in stacks[::-1]])
    ax.grid(axis="y", visible=False); ax.set_xlabel("Year-1 money kept (log scale) at 10, 50 and 250 sales a month")
    ax.set_title("Scenarios: slow, normal and great sales")
    return ("We tried three 'what if' sales levels. Each line runs from slow sales (left dot) to great sales (right dot), and the diamond is normal. "
            "KDP stays on top in every case, so the choice does not depend on guessing sales exactly right.",
            "Model in this repository; planning scenarios, not forecasts")

def c_cash(ax):
    ts = rd("hybrid_stack_24mo.csv"); chs = list(dict.fromkeys(r["channel"] for r in ts)); months = sorted({int(r["month"]) for r in ts})
    earned = [[float(r["cumulative_earned"]) for r in ts if r["channel"] == c] for c in chs]
    cash = [sum(float(r["cumulative_cash"]) for r in ts if int(r["month"]) == m) for m in months]
    ax.stackplot(months, *earned, colors=["#2a78d6", "#eb6834", "#008300"], labels=[f"Earned: {c}" for c in chs], alpha=0.9, edgecolor="#fcfcfb", linewidth=1.5)
    ax.plot(months, cash, color=INK, lw=2.2, ls="--", label="Cash in the bank")
    gap = sum(e[11] for e in earned) - cash[11]
    ax.annotate(f"Month 12: {money(gap,0)} earned\nbut not yet paid", xy=(12, cash[11]), xytext=(14, cash[11]*0.45),
                arrowprops=dict(arrowstyle="->", color=INK2), fontsize=9.5, color=INK)
    ax.set_xlim(1, 24); ax.set_xlabel("Months after launch"); ax.set_ylabel("Total royalties ($)")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: money(v, 0)))
    ax.legend(frameon=False, fontsize=8.5, loc="upper left"); ax.set_title("Earned vs paid: money arrives late")
    return ("The colored areas are money you have earned. The dashed line is money that has actually reached your bank. "
            "The space between them is money you are still waiting on, because stores pay two to three months after a sale.",
            "Model in this repository; launch curve and 65/35 channel mix are illustrative")

def c_dso(ax):
    pt = rd("payout_timing.csv")
    ax.barh([r["platform"] for r in pt][::-1], [int(r["avg_days_sale_to_cash"]) for r in pt][::-1], color=[COL[r["platform"]] for r in pt][::-1], height=0.55)
    for i, r in enumerate(pt[::-1]):
        ax.text(int(r["avg_days_sale_to_cash"])+2, i, f"~{r['avg_days_sale_to_cash']} days", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, 135); ax.grid(axis="y", visible=False); ax.set_xlabel("Days from a sale until the money arrives")
    ax.set_title("Days sales outstanding: how long you wait to get paid")
    return ("This is how many days you wait for your money after a sale. Shorter bars mean faster cash. "
            "IngramSpark takes the longest, about three and a half months, so plan your spending around it.",
            "B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by")

def c_kenp(ax):
    kp = rd("kenp_pool_rate.csv"); vals = [float(r["per_page_rate"])*1000 for r in kp]; mths = [r["month"][2:] for r in kp]
    mu, sd = st.mean(vals), st.stdev(vals)
    ax.fill_between(range(len(vals)), mu-sd, mu+sd, color="#2a78d6", alpha=0.10, label="Normal range (mean ±1 SD)")
    ax.axhline(mu, color="#2a78d6", lw=1, ls="--")
    ax.plot(range(len(vals)), vals, color="#2a78d6", lw=2, marker="o", ms=6, label="Pay per 1,000 pages read")
    hi, lo = vals.index(max(vals)), vals.index(min(vals))
    ax.annotate(f"High ${max(vals):.2f}", (hi, max(vals)), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9.5)
    ax.annotate(f"Low ${min(vals):.2f}", (lo, min(vals)), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=9.5)
    ax.text(len(vals)-0.5, mu+0.03, f"Average ${mu:.2f}", ha="right", fontsize=9.5, color=INK2)
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(mths, rotation=45, ha="right", fontsize=8.5)
    ax.set_ylim(3.9, 5.35); ax.set_ylabel("$ per 1,000 pages"); ax.legend(frameon=False, loc="upper left", fontsize=9)
    ax.set_title("Pool payouts: Kindle Unlimited pay changes monthly")
    return ("Kindle Unlimited pays authors from one big shared pot each month, split by pages read. The pot changes, "
            "so pay per page goes up and down like the weather. Plan for a range, not one exact number.",
            "Profitable.app KENP tracker (author-reported), May 2025 to April 2026")

def c_ab(ax):
    ab = rd("ab_test_design.csv")
    labels = ["Print price\n$16.99 vs $14.99", "Store terms\n55% returnable\nvs 40% non-returnable", "Ebook price\n$4.99 vs $3.99"]
    vals = [float(r["breakeven_lift_required"]) for r in ab]
    ax.barh(labels[::-1], vals[::-1], color="#6250d6", height=0.55)
    for i, (v, r) in enumerate(zip(vals[::-1], ab[::-1])):
        n = r["visitors_per_arm_80pct_power"]
        ax.text(v+0.015, i, f"{v:.0%} more sales needed" + (f"\n~{int(n):,} shoppers per group" if n else "\ntrack monthly sales"), va="center", fontsize=9.5, color=INK)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0)); ax.set_xlim(0, 1.35); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Extra sales the cheaper option needs just to break even"); ax.set_title("A/B tests: the bar a cheaper price must clear")
    return ("Lowering the price means you earn less on each book, so you must sell more books just to stay even. "
            "Each bar shows how many more. Keep the cheaper option only if a fair test shows sales jumped by more than the bar.",
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
    fig = plt.figure(figsize=(size[0], size[1] + 1.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[size[1], 1.15], hspace=0.42, left=0.2, right=0.97, top=0.93, bottom=0.07)
    ax = fig.add_subplot(gs[0]); note, src = fn(ax)
    note_box(fig.add_subplot(gs[1]), note, 120)
    stamp(fig, [src])
    fig.savefig(C / f"{name}.svg"); fig.savefig(C / f"{name}.png", dpi=180); plt.close(fig)

def page(name, left, right, ratio=(1, 1)):
    fig = plt.figure(figsize=(16, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[4.9, 1.25], width_ratios=ratio, hspace=0.42, wspace=0.5,
                          left=0.12, right=0.985, top=0.92, bottom=0.07)
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
