"""Render every static chart in /charts (SVG + PNG) from /data."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import statistics as st

ROOT = Path(__file__).resolve().parents[1]
D, C = ROOT / "data", ROOT / "charts"
C.mkdir(exist_ok=True)
for f in fm.findSystemFonts():
    if "Inter" in f: fm.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Inter", "font.size": 11, "axes.edgecolor": "#c9c8c2", "axes.labelcolor": "#52514e",
    "xtick.color": "#52514e", "ytick.color": "#52514e", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e9e8e4", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb",
    "axes.titlesize": 14, "axes.titleweight": "semibold", "axes.titlecolor": "#0b0b0b", "axes.titlelocation": "left", "text.parse_math": False,
})
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
COL = {"Amazon KDP": "#2a78d6", "IngramSpark": "#eb6834", "B&N Press": "#1baf7a", "Lulu Retail": "#eda100",
       "Lulu Bookstore": "#c98500", "Lulu": "#eda100", "PublishDrive": "#e87ba4", "Draft2Digital": "#008300",
       "Draft2Digital (ebook only)": "#008300", "Apple Books direct": "#6250d6", "KDP Expanded Distribution": "#e34948"}
POS, NEG, NEU = "#2a78d6", "#e34948", "#b9b8b2"

def rd(name): return list(csv.DictReader(open(D / name)))
def save(fig, name, src):
    fig.canvas.draw()
    bb = fig.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.dpi_scale_trans.inverted() + fig.transFigure.inverted()) if False else None
    r = fig.canvas.get_renderer()
    tb = fig.get_tightbbox(r)  # inches
    y = (tb.y0 * fig.dpi - 6) / (fig.get_figheight() * fig.dpi)
    x = tb.x0 / fig.get_figwidth()
    fig.text(x, y, "Source: " + src, fontsize=8.5, color=MUTED, ha="left", va="top")
    fig.savefig(C / f"{name}.svg", bbox_inches="tight", pad_inches=0.25)
    fig.savefig(C / f"{name}.png", dpi=200, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
def money(x, d=2): return f"-${abs(x):,.{d}f}" if x < 0 else f"${x:,.{d}f}"

# 1. Bowker stacked line (stacked area)
rows = rd("market_bowker_isbn.csv")
yrs = sorted({int(r["year"]) for r in rows})
sp = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Self-published"]
tr = [int(r["titles"])/1e6 for r in rows if r["segment"] == "Traditional"]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.stackplot(yrs, tr, sp, colors=["#6250d6", "#2a78d6"], alpha=0.9, edgecolor="#fcfcfb", linewidth=2)
ax.plot(yrs, [a+b for a, b in zip(tr, sp)], color=INK, lw=2, marker="o", ms=6)
for y, t, s in zip(yrs, tr, sp):
    ax.annotate(f"{t+s:.2f}M", (y, t+s), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10, color=INK)
ax.text(2022.05, tr[0]/2, "Traditional", color="white", fontsize=10, va="center", weight="semibold")
ax.text(2022.05, tr[0] + sp[0]/2, "Self-published", color="white", fontsize=10, va="center", weight="semibold")
ax.text(2024.92, 2.2, "Self-published\n+38.7% in 2025", color="white", fontsize=10.5, ha="right", va="center", weight="semibold")
ax.set_xticks(yrs); ax.set_ylabel("ISBNs issued (millions)"); ax.set_ylim(0, 4.7); ax.set_xlim(2021.85, 2025.2)
ax.set_title("U.S. ISBN output: self-published titles drive growth (stacked)")
save(fig, "01_market_isbn_stacked", "Bowker data via Publishers Weekly, March 23, 2026")

# 2. AAP formats
rows = rd("market_aap_formats_2025.csv")[::-1]
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.barh([r["format"] for r in rows], [float(r["revenue_billions"]) for r in rows], color="#2a78d6", height=0.55)
for i, r in enumerate(rows):
    ax.text(float(r["revenue_billions"]) + 0.1, i, f"${float(r['revenue_billions']):.1f}B  ({float(r['yoy_change']):+.1%} YoY)", va="center", fontsize=10, color=INK)
ax.set_xlim(0, 10.5); ax.set_xlabel("2025 U.S. publisher revenue ($ billions)"); ax.grid(axis="y", visible=False)
ax.set_title("Print still earns most of the revenue; digital audio grows fastest")
save(fig, "02_market_aap_formats", "Association of American Publishers, StatShot Annual Report 2025")

# 3. Price waterfall (stacked 100% bars) print
rows = rd("price_waterfall_long.csv")
plats = [p["platform"] for p in rd("print_unit_economics.csv")]
comps = ["Net royalty to IP owner", "Production cost", "Platform fee", "Channel share"]
ccol = {"Net royalty to IP owner": "#2a78d6", "Production cost": "#eda100", "Platform fee": "#e34948", "Channel share": "#b9b8b2"}
fig, ax = plt.subplots(figsize=(10, 4.8))
order = sorted(plats, key=lambda p: -float(next(r["amount"] for r in rows if r["platform"] == p and r["format"] == "Print" and r["component"] == comps[0])))[::-1]
for i, p in enumerate(order):
    left = 0
    for c in comps:
        v = float(next(r["amount"] for r in rows if r["platform"] == p and r["format"] == "Print" and r["component"] == c))
        ax.barh(i, v, left=left, color=ccol[c], height=0.6, edgecolor="#fcfcfb", linewidth=2, label=c if i == 0 else None)
        if c == comps[0]: ax.text(left + v/2, i, money(v), ha="center", va="center", color="white", fontsize=9.5, weight="semibold")
        left += v
ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.set_xlim(0, 17.5)
ax.set_xlabel("Where each $16.99 of list price goes (print)"); ax.grid(axis="y", visible=False)
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False, fontsize=9.5)
ax.set_title("Gross-to-net: the channel share is the largest deduction")
save(fig, "03_print_gross_to_net", "Model in this repository; platform rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive (see Sources)")

# 4. Cost variance drivers (diverging stacked)
pu = {r["platform"]: r for r in rd("print_unit_economics.csv")}
others = [p for p in plats if p != "Amazon KDP"]
others.sort(key=lambda p: float(pu[p]["variance_vs_kdp"]))
drv = [("Channel share", "var_channel_share", "#b9b8b2"), ("Production cost", "var_production", "#eda100"), ("Platform fee", "var_platform_fee", "#e34948")]
fig, ax = plt.subplots(figsize=(10, 4.8))
for i, p in enumerate(others):
    pos, neg = 0, 0
    for lab, k, col in drv:
        v = float(pu[p][k])
        if v >= 0: ax.barh(i, v, left=pos, color=col, height=0.6, edgecolor="#fcfcfb", linewidth=2, label=lab if i == 0 else None); pos += v
        else: ax.barh(i, v, left=neg, color=col, height=0.6, edgecolor="#fcfcfb", linewidth=2, label=lab if i == 0 else None); neg += v
    tot = float(pu[p]["variance_vs_kdp"])
    ax.plot(tot, i, marker="D", color=INK, ms=7, zorder=5)
    ax.text(max(pos, 0) + 0.2, i, f"Net variance {money(tot)}", va="center", fontsize=9.5, color=INK)
ax.axvline(0, color=INK2, lw=1)
ax.set_yticks(range(len(others))); ax.set_yticklabels(others); ax.grid(axis="y", visible=False)
ax.set_xlim(-8, 11); ax.set_xlabel("Variance vs Amazon KDP baseline, $ per print unit (right = favorable)")
h, l = ax.get_legend_handles_labels()
from matplotlib.lines import Line2D
h.append(Line2D([], [], marker="D", color=INK, ls="")); l.append("Total variance")
ax.legend(h, l, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False, fontsize=9.5)
ax.set_title("Cost variance analysis: each driver's contribution vs the KDP baseline")
save(fig, "04_cost_variance_drivers", "Model in this repository; baseline = Amazon KDP print royalty of $6.79 per unit")

# 5. Ebook net per unit
eu = rd("ebook_unit_economics.csv"); eu.sort(key=lambda r: float(r["net_royalty"]))
fig, ax = plt.subplots(figsize=(10, 4.4))
names = [r["platform"] for r in eu]
ax.barh(names, [float(r["net_royalty"]) for r in eu], color=[COL.get(n, "#2a78d6") for n in names], height=0.6)
for i, r in enumerate(eu):
    ax.text(float(r["net_royalty"]) + 0.04, i, f"{money(float(r['net_royalty']))}  ({float(r['net_margin_pct']):.0%} of list, {money(float(r['variance_vs_kdp']))} vs KDP)", va="center", fontsize=9.5, color=INK)
ax.set_xlim(0, 5.3); ax.grid(axis="y", visible=False); ax.set_xlabel("Net royalty per $4.99 ebook")
ax.set_title("Ebooks: going direct beats aggregators by $0.35 to $0.52 per unit")
save(fig, "05_ebook_net_per_unit", "Model in this repository; store payout rates from ScribeCount; fees from KDP, Draft2Digital and IngramSpark agreement Sec. 8.1.3")

# 6. Tornado
rows = rd("sensitivity_tornado.csv"); rows.sort(key=lambda r: float(r["swing"]))
fig, ax = plt.subplots(figsize=(10, 4.2))
for i, r in enumerate(rows):
    b, lo, hi = float(r["base_net"]), float(r["net_at_minus20"]), float(r["net_at_plus20"])
    ax.barh(i, lo - b, left=b, color=NEG, height=0.55, label="Input -20%" if i == 0 else None)
    ax.barh(i, hi - b, left=b, color=POS, height=0.55, label="Input +20%" if i == 0 else None)
    ax.text(max(lo, hi) + 0.1, i, f"swing {money(float(r['swing']))}", va="center", fontsize=9.5, color=INK)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([f"{r['platform']}: {r['input']}" for r in rows]); ax.grid(axis="y", visible=False)
ax.set_xlabel("Net royalty per print unit ($)"); ax.legend(frameon=False, loc="lower right", fontsize=9.5)
ax.set_xlim(0, 11)
ax.set_title("Sensitivity analysis: list price moves net royalty more than any cost")
save(fig, "06_sensitivity_tornado", "Model in this repository; each input flexed ±20% with all others held at base")

# 7. Breakeven units
be = rd("breakeven.csv"); be.sort(key=lambda r: int(r["breakeven_unit_pairs"]))
fig, ax = plt.subplots(figsize=(10, 4.4))
names = [r["stack"] for r in be]
ax.barh(names[::-1], [int(r["breakeven_unit_pairs"]) for r in be][::-1], color=[COL[n] for n in names][::-1], height=0.6)
for i, r in enumerate(be[::-1]):
    ax.text(int(r["breakeven_unit_pairs"]) + 6, i, f"{int(r['breakeven_unit_pairs'])} unit pairs  (contribution {money(float(r['contribution_per_unit_pair']))} per pair)", va="center", fontsize=9.5, color=INK)
ax.set_xlim(0, 800); ax.grid(axis="y", visible=False)
ax.set_xlabel("Unit pairs (1 print + 1 ebook) needed to recover Year-1 fixed costs")
ax.set_title("Breakeven analysis: KDP recovers launch costs fastest")
save(fig, "07_breakeven_units", "Model in this repository; fixed costs = platform one-time fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions")

# 8. Breakeven curve
cv = rd("breakeven_curve.csv")
fig, ax = plt.subplots(figsize=(10, 4.8))
for s in [r["stack"] for r in rd("breakeven.csv")]:
    pts = [r for r in cv if r["stack"] == s]
    ax.plot([int(p["unit_pairs"]) for p in pts], [float(p["cumulative_profit"]) for p in pts], color=COL[s], lw=2, label=s)
ax.axhline(0, color=INK, lw=1.2); ax.text(5, 60, "Breakeven line", fontsize=9, color=INK2)
ax.fill_between([0, 600], -2000, 0, color="#e34948", alpha=0.05)
ax.set_xlim(0, 600); ax.set_ylim(-2000, 4600)
ax.set_xlabel("Cumulative unit pairs sold"); ax.set_ylabel("Cumulative profit ($)")
ax.legend(frameon=False, fontsize=9.5, ncol=2, loc="upper left")
ax.set_title("Cumulative profit by platform: where each line crosses zero is breakeven")
save(fig, "08_breakeven_curve", "Model in this repository")

# 9. Crossover
cr = rd("crossover_publishdrive_ingramspark.csv"); x = [int(r["units_per_month"]) for r in cr]
fig, ax = plt.subplots(figsize=(10, 4.4))
ax.plot(x, [float(r["IngramSpark"]) for r in cr], color=COL["IngramSpark"], lw=2, label="IngramSpark (no subscription)")
ax.plot(x, [float(r["PublishDrive"]) for r in cr], color=COL["PublishDrive"], lw=2, label="PublishDrive ($13.99/mo plan)")
xc = float(rd("crossover_summary.csv")[0]["crossover_units_per_month"])
ax.axvline(xc, color=INK2, ls="--", lw=1)
ax.annotate(f"Crossover at {xc:.1f} units per format per month", xy=(xc, xc*6.296), xytext=(xc+3, 40),
            arrowprops=dict(arrowstyle="->", color=INK2), fontsize=10, color=INK)
ax.set_xlabel("Units sold per format per month"); ax.set_ylabel("Monthly net ($)"); ax.legend(frameon=False, loc="upper left")
ax.set_xlim(0, 40)
ax.set_title("Fixed vs variable cost: a subscription wins only above the crossover volume")
save(fig, "09_crossover_breakeven", "Model in this repository; PublishDrive pricing from PublishDrive Help Center")

# 10. Scenarios small multiples
sc = rd("scenario_analysis.csv"); stacks = [r["stack"] for r in rd("breakeven.csv")]
fig, axes = plt.subplots(1, 3, figsize=(12, 4.4), sharey=False)
for ax, lab in zip(axes, ["Bear", "Base", "Bull"]):
    rr = [r for r in sc if r["scenario"] == lab]
    vals = [float(next(r["year1_net"] for r in rr if r["stack"] == s)) for s in stacks]
    ax.barh(stacks[::-1], vals[::-1], color=[COL[s] for s in stacks][::-1], height=0.6)
    for i, v in enumerate(vals[::-1]):
        ax.text(v, i, " " + money(v, 0), va="center", ha="left", fontsize=8.5, color=INK)
    u = rr[0]["units_per_format_per_month"]
    ax.set_title(f"{lab}: {u} units/format/mo", fontsize=11.5)
    ax.grid(axis="y", visible=False); ax.axvline(0, color=INK2, lw=0.8)
    ax.set_xlim(min(0, min(vals))*1.2, max(vals)*1.45)
    if lab != "Bear": ax.set_yticklabels([])
    ax.set_xlabel("Year-1 net ($)")
fig.suptitle("Scenario analysis: Year-1 net after platform fees and copyright registration", x=0.01, ha="left", fontsize=14, weight="semibold")
save(fig, "10_scenario_analysis", "Model in this repository; volumes are planning scenarios, not forecasts")

# 11. Hybrid stack stacked line: cumulative earned (stacked) vs cumulative cash
ts = rd("hybrid_stack_24mo.csv"); chs = list(dict.fromkeys(r["channel"] for r in ts))
months = sorted({int(r["month"]) for r in ts})
ccols = ["#2a78d6", "#eb6834", "#008300"]
earned = [[float(r["cumulative_earned"]) for r in ts if r["channel"] == c] for c in chs]
cash = [sum(float(r["cumulative_cash"]) for r in ts if int(r["month"]) == m) for m in months]
fig, ax = plt.subplots(figsize=(10, 4.8))
ax.stackplot(months, *earned, colors=ccols, labels=[f"Earned: {c}" for c in chs], alpha=0.9, edgecolor="#fcfcfb", linewidth=1.5)
ax.plot(months, cash, color=INK, lw=2.2, ls="--", label="Cash actually received (all channels)")
gap = sum(e[11] for e in earned) - cash[11]
ax.annotate(f"Month 12 working-capital gap: {money(gap,0)}", xy=(12, cash[11]), xytext=(13.5, cash[11]*0.55),
            arrowprops=dict(arrowstyle="->", color=INK2), fontsize=10, color=INK)
ax.set_xlim(1, 24); ax.set_xlabel("Month after launch"); ax.set_ylabel("Cumulative royalties ($)")
ax.legend(frameon=False, fontsize=9, loc="upper left")
ax.set_title("Accrual vs cash: royalties earned (stacked) lead cash by 2 to 3 months")
save(fig, "11_hybrid_stack_accrual_vs_cash", "Model in this repository; launch curve and 65/35 channel mix are illustrative; Amazon share informed by Written Word Media 2025 survey")

# 12. Payout timing
pt = rd("payout_timing.csv")
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.barh([r["platform"] for r in pt][::-1], [int(r["avg_days_sale_to_cash"]) for r in pt][::-1], color=[COL[r["platform"]] for r in pt][::-1], height=0.55)
for i, r in enumerate(pt[::-1]):
    ax.text(int(r["avg_days_sale_to_cash"]) + 2, i, f"~{r['avg_days_sale_to_cash']} days  ({r['terms']})", va="center", fontsize=9.5, color=INK)
ax.set_xlim(0, 190); ax.grid(axis="y", visible=False); ax.set_xlabel("Average days from sale to cash (DSO analogue)")
ax.set_title("Days sales outstanding: payment terms differ by up to 60 days")
save(fig, "12_payout_timing_dso", "B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by")

# 13. KENP pool rate
kp = rd("kenp_pool_rate.csv"); vals = [float(r["per_page_rate"])*1000 for r in kp]; mths = [r["month"] for r in kp]
mu, sd = st.mean(vals), st.stdev(vals)
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.fill_between(range(len(vals)), mu-sd, mu+sd, color="#2a78d6", alpha=0.10, label="Mean ±1 standard deviation")
ax.axhline(mu, color="#2a78d6", lw=1, ls="--")
ax.plot(range(len(vals)), vals, color="#2a78d6", lw=2, marker="o", ms=6, label="Per-page payout ($ per 1,000 pages)")
hi = vals.index(max(vals)); lo = vals.index(min(vals))
ax.annotate(f"High {mths[hi]}: ${max(vals):.2f}", (hi, max(vals)), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=9.5)
ax.annotate(f"Low {mths[lo]}: ${min(vals):.2f}", (lo, min(vals)), xytext=(0, -16), textcoords="offset points", ha="center", fontsize=9.5)
ax.text(len(vals)-0.5, mu+0.02, f"Mean ${mu:.2f}  |  CV {sd/mu:.1%}", ha="right", fontsize=9.5, color=INK2)
ax.set_xticks(range(len(vals))); ax.set_xticklabels(mths, rotation=45, ha="right", fontsize=9)
ax.set_ylim(3.9, 5.3); ax.set_ylabel("$ per 1,000 pages read"); ax.legend(frameon=False, loc="upper left", fontsize=9.5)
ax.set_title("Pool-based payouts: Kindle Unlimited's per-page rate moves every month")
save(fig, "13_kenp_pool_volatility", "Profitable.app KENP tracker (author-reported), May 2025 to April 2026")

# 14. A/B required lift
ab = rd("ab_test_design.csv")
fig, ax = plt.subplots(figsize=(10, 3.6))
labels = ["Print price\n$16.99 vs $14.99", "Channel terms\n55% returnable vs 40% non-returnable", "Ebook price\n$4.99 vs $3.99"]
vals = [float(r["breakeven_lift_required"]) for r in ab]
ax.barh(labels[::-1], vals[::-1], color="#6250d6", height=0.55)
for i, (v, r) in enumerate(zip(vals[::-1], ab[::-1])):
    n = r["visitors_per_arm_80pct_power"]
    extra = f"  |  ~{int(n):,} visitors per arm for 80% power" if n else "  |  measure monthly units per arm"
    ax.text(v + 0.01, i, f"{v:.1%} lift to break even{extra}", va="center", fontsize=9.5, color=INK)
from matplotlib.ticker import PercentFormatter; ax.xaxis.set_major_formatter(PercentFormatter(1.0)); ax.set_xlim(0, 1.5); ax.grid(axis="y", visible=False); ax.set_xlabel("Volume lift the challenger needs just to match the control's contribution")
ax.set_title("A/B test design: the breakeven lift sets the bar for a winning variant")
save(fig, "14_ab_test_breakeven_lift", "Model in this repository; sample sizes use a two-proportion z-test, alpha 0.05, power 0.80")
print("charts:", len(list(C.glob('*.svg'))))
