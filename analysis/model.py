"""
IP Distribution Decision Verticals: analytical model.

Builds every dataset in /data from one set of documented assumptions, so the
deck, the charts, the Excel workbook and the Tableau story all read the same
numbers. Run:  python analysis/model.py
"""
import csv, math, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

# ---------------------------------------------------------------- assumptions
A = dict(
    list_price=16.99, pages=200, ebook_price=4.99, ebook_mb=2.0,
    kdp_print_rate=0.60, kdp_ed_rate=0.40, kdp_fixed=1.00, kdp_per_page=0.012,
    kdp_eb_hi=0.70, kdp_deliv=0.15,
    is_disc=0.55, is_maf=0.01875, ingram_print=4.00, is_digital=0.15,
    bn_print_rate=0.55, bn_print=3.50, bn_eb_rate=0.70,
    lulu_print=5.00, lulu_dist=0.50, lulu_share=0.20,
    store_rate=0.70, d2d_share=0.10,
    isbn=125.0, d2d_acct=20.0, lulu_proof=12.0, pd_sub=13.99,
    copyright_fee=85.0,          # USCO Standard Application after the Nov-2026 fee schedule
    launch_budget=1500.0,        # ILLUSTRATIVE production budget (cover, edit, layout)
)
SRC = {
    "ingram": "https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More",
    "kdp": "https://profitable.app/tools/kdp-royalty-calculator",
    "kdp_ed": "https://bestwriting.com/kdp-royalties",
    "bn": "https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales",
    "lulu": "https://blog.chapter.pub/lulu-pricing/",
    "pd": "https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans",
    "d2d": "https://publishdrive.com/comparison-guide-publishdrive-vs-draft2digital.html",
    "store": "https://scribecount.com/tools/platform-comparison",
    "isbn": "https://scribecount.com/author-resource/publishing-a-book/How-to-Publish-on-IngramSpark",
    "usco_fee": "https://www.hypebot.com/2-months-left-before-u-s-copyright-fees-jump-dramatically/",
    "tortora": "https://danieljtortora.com/blog/self-publishing-royalties",
}

import json
AS_OF = json.load(open(ROOT / "as_of.json"))["as_of"]
def w(name, rows, fields=None):
    rows = [dict(r, as_of=AS_OF) for r in rows]
    fields = fields or list(rows[0].keys())
    with open(DATA / name, "w", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader(); wr.writerows(rows)

def r2(x): return round(x, 4)

kdp_cost = A["kdp_fixed"] + A["pages"] * A["kdp_per_page"] if A["pages"] > 108 else 2.30
LP, EP = A["list_price"], A["ebook_price"]

# ---------------------------------------------------------------- print unit economics
print_rows = [
    # platform, channel, channel share, production, platform fee, payout lag days, reach
    ("Amazon KDP", "Amazon.com", LP*(1-A["kdp_print_rate"]), kdp_cost, 0.0, 75, "Amazon only", SRC["kdp"]),
    ("KDP Expanded Distribution", "Other retailers via KDP", LP*(1-A["kdp_ed_rate"]), kdp_cost, 0.0, 75, "Limited wholesale", SRC["kdp_ed"]),
    ("IngramSpark", "Bookstores, libraries, online", LP*A["is_disc"], A["ingram_print"], LP*A["is_maf"], 105, "Widest wholesale", SRC["ingram"]),
    ("B&N Press", "BN.com (U.S.)", LP*(1-A["bn_print_rate"]), A["bn_print"], 0.0, 45, "Barnes & Noble only", SRC["bn"]),
    ("Lulu Bookstore", "Lulu.com", 0.0, A["lulu_print"], (LP-A["lulu_print"])*A["lulu_share"], 45, "Own storefront", SRC["lulu"]),
    ("Lulu Retail", "Retailers via Lulu", LP*A["lulu_dist"], A["lulu_print"], (LP-LP*A["lulu_dist"]-A["lulu_print"])*A["lulu_share"], 45, "Wholesale via partner", SRC["lulu"]),
    ("PublishDrive", "Bookstores via Ingram", LP*A["is_disc"], A["ingram_print"], 0.0, 75, "Widest wholesale", SRC["pd"]),
]
P = []
for name, ch, share, prod, fee, lag, reach, src in print_rows:
    net = LP - share - prod - fee
    P.append(dict(platform=name, format="Print", channel=ch, list_price=LP, channel_share=r2(share),
                  production_cost=r2(prod), platform_fee=r2(fee), net_royalty=r2(net),
                  net_margin_pct=r2(net/LP), payout_lag_days=lag, reach=reach, source=src))
base = next(p for p in P if p["platform"] == "Amazon KDP")
for p in P:
    p["variance_vs_kdp"] = r2(p["net_royalty"] - base["net_royalty"])
    p["var_channel_share"] = r2(base["channel_share"] - p["channel_share"])
    p["var_production"] = r2(base["production_cost"] - p["production_cost"])
    p["var_platform_fee"] = r2(base["platform_fee"] - p["platform_fee"])
    p["variance_pct"] = r2(p["variance_vs_kdp"] / base["net_royalty"])

# ---------------------------------------------------------------- ebook unit economics
deliv = A["ebook_mb"]*A["kdp_deliv"] if 2.99 <= EP <= 9.99 else 0
store_cut = EP*(1-A["store_rate"])
ebook_rows = [
    ("Amazon KDP", "Kindle", (EP-deliv)*(1-A["kdp_eb_hi"]), deliv, 0.0, 75, SRC["kdp"]),
    ("Apple Books direct", "Apple Books", store_cut, 0, 0.0, 45, SRC["store"]),
    ("B&N Press", "Nook", EP*(1-A["bn_eb_rate"]), 0, 0.0, 45, SRC["bn"]),
    ("Draft2Digital", "Apple, Kobo, Google, libraries", store_cut, 0, (EP-store_cut)*A["d2d_share"], 75, SRC["d2d"]),
    ("IngramSpark", "Ingram ebook network", store_cut, 0, (EP-store_cut)*A["is_digital"], 105, "https://www.ingramspark.com/"),
    ("PublishDrive", "400+ stores", store_cut, 0, 0.0, 75, SRC["pd"]),
    ("Lulu Retail", "Retailers via Lulu", EP*A["lulu_dist"], 0, (EP-EP*A["lulu_dist"])*A["lulu_share"], 45, SRC["lulu"]),
]
E = []
for name, ch, cut, dl, fee, lag, src in ebook_rows:
    net = EP - cut - dl - fee
    E.append(dict(platform=name, format="Ebook", channel=ch, list_price=EP, channel_share=r2(cut),
                  delivery_fee=r2(dl), platform_fee=r2(fee), net_royalty=r2(net),
                  net_margin_pct=r2(net/EP), payout_lag_days=lag, source=src))
eb = next(e for e in E if e["platform"] == "Amazon KDP")
for e in E:
    e["variance_vs_kdp"] = r2(e["net_royalty"] - eb["net_royalty"])
    e["var_channel_share"] = r2(eb["channel_share"] - e["channel_share"])
    e["var_delivery"] = r2(eb["delivery_fee"] - e["delivery_fee"])
    e["var_platform_fee"] = r2(eb["platform_fee"] - e["platform_fee"])
w("print_unit_economics.csv", P); w("ebook_unit_economics.csv", E)

# long-format waterfall for Tableau / stacked bars
wf = []
for p in P:
    for comp, val in (("Channel share", p["channel_share"]), ("Production cost", p["production_cost"]),
                      ("Platform fee", p["platform_fee"]), ("Net royalty to IP owner", p["net_royalty"])):
        wf.append(dict(format="Print", platform=p["platform"], component=comp, amount=r2(val), share_of_price=r2(val/LP)))
for e in E:
    for comp, val in (("Channel share", e["channel_share"]), ("Production cost", e["delivery_fee"]),
                      ("Platform fee", e["platform_fee"]), ("Net royalty to IP owner", e["net_royalty"])):
        wf.append(dict(format="Ebook", platform=e["platform"], component=comp, amount=r2(val), share_of_price=r2(val/EP)))
w("price_waterfall_long.csv", wf)

# variance drivers long
vd = []
for p in P:
    for d, k in (("Channel share", "var_channel_share"), ("Production cost", "var_production"), ("Platform fee", "var_platform_fee")):
        vd.append(dict(format="Print", platform=p["platform"], driver=d, variance=p[k], total_variance=p["variance_vs_kdp"]))
for e in E:
    for d, k in (("Channel share", "var_channel_share"), ("Production cost", "var_delivery"), ("Platform fee", "var_platform_fee")):
        vd.append(dict(format="Ebook", platform=e["platform"], driver=d, variance=e[k], total_variance=e["variance_vs_kdp"]))
w("cost_variance_drivers.csv", vd)

# ---------------------------------------------------------------- platform stacks (a "stack" = print + ebook route)
STACKS = [
    # name, print row, ebook row, fixed one-time, monthly fee
    ("Amazon KDP", "Amazon KDP", "Amazon KDP", 0.0, 0.0),
    ("IngramSpark", "IngramSpark", "IngramSpark", A["isbn"], 0.0),
    ("B&N Press", "B&N Press", "B&N Press", A["isbn"], 0.0),
    ("Lulu", "Lulu Retail", "Lulu Retail", A["lulu_proof"], 0.0),
    ("PublishDrive", "PublishDrive", "PublishDrive", A["isbn"], A["pd_sub"]),
    ("Draft2Digital (ebook only)", None, "Draft2Digital", A["d2d_acct"], 0.0),
]
pn = {p["platform"]: p["net_royalty"] for p in P}
en = {e["platform"]: e["net_royalty"] for e in E}
stack_rows = []
for s, pr, er, fx, mo in STACKS:
    stack_rows.append(dict(stack=s, print_net=pn.get(pr, 0.0) if pr else 0.0, ebook_net=en[er],
                           one_time_fixed=fx, monthly_fee=mo))

# ---------------------------------------------------------------- breakeven
# Fixed cost base = platform one-time costs + copyright registration + illustrative launch budget.
# Contribution per "unit pair" = print net + ebook net (one print + one ebook sale).
be = []
for s in stack_rows:
    contrib = s["print_net"] + s["ebook_net"]
    fixed_platform = s["one_time_fixed"]
    fixed_total = fixed_platform + A["copyright_fee"] + A["launch_budget"]
    yr_fee = s["monthly_fee"] * 12
    be.append(dict(stack=s["stack"], contribution_per_unit_pair=r2(contrib),
                   platform_fixed_costs=r2(fixed_platform), copyright_registration=A["copyright_fee"],
                   illustrative_launch_budget=A["launch_budget"], subscription_year1=r2(yr_fee),
                   total_fixed_year1=r2(fixed_total + yr_fee),
                   breakeven_unit_pairs=math.ceil((fixed_total + yr_fee) / contrib),
                   breakeven_platform_only=math.ceil((fixed_platform + yr_fee) / contrib) if (fixed_platform + yr_fee) else 0,
                   margin_of_safety_at_600=r2((600 - math.ceil((fixed_total + yr_fee)/contrib)) / 600)))
w("breakeven.csv", be)

# cumulative profit curve (units 0..600) for breakeven chart
curve = []
for s in stack_rows:
    contrib = s["print_net"] + s["ebook_net"]
    fixed = s["one_time_fixed"] + A["copyright_fee"] + A["launch_budget"] + s["monthly_fee"]*12
    for u in range(0, 601, 10):
        curve.append(dict(stack=s["stack"], unit_pairs=u, cumulative_profit=r2(u*contrib - fixed)))
w("breakeven_curve.csv", curve)

# crossover: PublishDrive vs IngramSpark per month
pdx = next(s for s in stack_rows if s["stack"] == "PublishDrive")
isx = next(s for s in stack_rows if s["stack"] == "IngramSpark")
crossover_pd_is = pdx["monthly_fee"] / ((pdx["print_net"] + pdx["ebook_net"]) - (isx["print_net"] + isx["ebook_net"]))
d2d = next(s for s in stack_rows if s["stack"].startswith("Draft2Digital"))
crossover_pd_d2d = pdx["monthly_fee"] / (pdx["ebook_net"] - d2d["ebook_net"])
cross = []
for u in range(0, 41, 1):
    cross.append(dict(units_per_month=u, IngramSpark=r2(u*(isx["print_net"]+isx["ebook_net"])),
                      PublishDrive=r2(u*(pdx["print_net"]+pdx["ebook_net"]) - pdx["monthly_fee"])))
w("crossover_publishdrive_ingramspark.csv", cross)
w("crossover_summary.csv", [
    dict(comparison="PublishDrive vs IngramSpark (print + ebook)", crossover_units_per_month=r2(crossover_pd_is),
         interpretation="Above this monthly volume per format, the flat subscription costs less than IngramSpark's per-sale fees."),
    dict(comparison="PublishDrive vs Draft2Digital (ebook only)", crossover_units_per_month=r2(crossover_pd_d2d),
         interpretation="Above this monthly ebook volume, the subscription beats Draft2Digital's ~10% share."),
])

# ---------------------------------------------------------------- scenarios (bear/base/bull)
scen = []
for label, units in (("Bear", 10), ("Base", 50), ("Bull", 250)):
    for s in stack_rows:
        fixed = s["one_time_fixed"] + A["copyright_fee"]
        yr = 12*(units*(s["print_net"]+s["ebook_net"]) - s["monthly_fee"]) - fixed
        scen.append(dict(scenario=label, units_per_format_per_month=units, stack=s["stack"], year1_net=r2(yr)))
w("scenario_analysis.csv", scen)

# ---------------------------------------------------------------- sensitivity (tornado) on print net
def kdp_net(lp=LP, pages=A["pages"], rate=A["kdp_print_rate"]):
    return lp*rate - (A["kdp_fixed"] + pages*A["kdp_per_page"])
def is_net(lp=LP, disc=A["is_disc"], pc=A["ingram_print"]):
    return lp - lp*disc - pc - lp*A["is_maf"]
sens = []
for plat, f, inputs in (
    ("Amazon KDP", kdp_net, [("List price ±20%", "lp", LP), ("Page count ±20%", "pages", A["pages"])]),
    ("IngramSpark", is_net, [("List price ±20%", "lp", LP), ("Wholesale discount ±20%", "disc", A["is_disc"]),
                             ("Print cost ±20%", "pc", A["ingram_print"])]),
):
    b = f()
    for lab, k, v in inputs:
        lo, hi = f(**{k: v*0.8}), f(**{k: v*1.2})
        sens.append(dict(platform=plat, input=lab, base_net=r2(b), net_at_minus20=r2(lo), net_at_plus20=r2(hi),
                         swing=r2(abs(hi-lo))))
w("sensitivity_tornado.csv", sens)

# ---------------------------------------------------------------- A/B test design
def n_per_arm(p, rel_lift, alpha_z=1.959964, power_z=0.841621):
    p2 = p*(1+rel_lift); pbar = (p+p2)/2
    num = (alpha_z*math.sqrt(2*pbar*(1-pbar)) + power_z*math.sqrt(p*(1-p)+p2*(1-p2)))**2
    return math.ceil(num/((p2-p)**2))
ab = []
# Test 1: price $14.99 vs $16.99 on KDP print
a_net, b_net = kdp_net(16.99), kdp_net(14.99)
lift = a_net/b_net - 1
ab.append(dict(test="Price elasticity: $16.99 (A, control) vs $14.99 (B)", platform="Amazon KDP print",
               metric="Net royalty per product-page visitor", net_per_unit_A=r2(a_net), net_per_unit_B=r2(b_net),
               breakeven_lift_required=r2(lift), baseline_conversion=0.02,
               visitors_per_arm_80pct_power=n_per_arm(0.02, lift),
               decision_rule=f"Ship B only if unit conversion rises more than {lift:.1%}; otherwise keep A."))
# Test 2: discount 55% returnable vs 40% non-returnable on IngramSpark
a2 = is_net(disc=0.55); b2 = is_net(disc=0.40)
lift2 = b2/a2 - 1
ab.append(dict(test="Channel terms: 55% discount, returnable (A) vs 40% non-returnable (B)", platform="IngramSpark print",
               metric="Net royalty per month after returns", net_per_unit_A=r2(a2), net_per_unit_B=r2(b2),
               breakeven_lift_required=r2(b2/a2 - 1), baseline_conversion=None,
               visitors_per_arm_80pct_power=None,
               decision_rule=f"Here the lift applies to arm A: A must sell {b2/a2:.2f}x the units of arm B (net of returns) to match B's contribution."))
# Test 3: ebook price $4.99 vs $3.99 KDP
def kdp_eb(p): return (p - A["ebook_mb"]*A["kdp_deliv"])*A["kdp_eb_hi"] if 2.99 <= p <= 9.99 else p*0.35
a3, b3 = kdp_eb(4.99), kdp_eb(3.99); lift3 = a3/b3 - 1
ab.append(dict(test="Ebook price: $4.99 (A, control) vs $3.99 (B)", platform="Amazon KDP ebook",
               metric="Net royalty per product-page visitor", net_per_unit_A=r2(a3), net_per_unit_B=r2(b3),
               breakeven_lift_required=r2(lift3), baseline_conversion=0.03,
               visitors_per_arm_80pct_power=n_per_arm(0.03, lift3),
               decision_rule=f"Ship B only if unit conversion rises more than {lift3:.1%}."))
w("ab_test_design.csv", ab)

# ---------------------------------------------------------------- 24-month accrual vs cash (stacked line)
# Illustrative hybrid stack: KDP print+ebook on Amazon, IngramSpark print for wide print, Draft2Digital for wide ebook.
# Launch curve: month-1 volume 120 units/format, decaying 8%/month to a floor of 40.
# Channel mix assumption: 65% Amazon / 35% other retail, reflecting Amazon as the top revenue source for 83% of
# surveyed indie authors (Written Word Media 2025). Lags = payment terms converted to whole months.
channels = [
    ("Amazon KDP (print + ebook)", 0.65, pn["Amazon KDP"] + en["Amazon KDP"], 2),
    ("IngramSpark (print)", 0.35, pn["IngramSpark"], 3),
    ("Draft2Digital (ebook)", 0.35, en["Draft2Digital"], 2),
]
months = 24
vol = [max(40, 120*(0.92**m)) for m in range(months)]
ts = []
cum_e = {c[0]: 0 for c in channels}; cum_c = {c[0]: 0 for c in channels}
earned_by = {c[0]: [] for c in channels}
for m in range(months):
    for name, share, unit, lag in channels:
        if name.startswith("Amazon"):
            earned = vol[m]*share*unit
        else:
            earned = vol[m]*share*unit
        earned_by[name].append(earned)
        cash = earned_by[name][m-lag] if m-lag >= 0 else 0.0
        cum_e[name] += earned; cum_c[name] += cash
        ts.append(dict(month=m+1, channel=name, units_per_format=r2(vol[m]*share), earned=r2(earned), cash_received=r2(cash),
                       cumulative_earned=r2(cum_e[name]), cumulative_cash=r2(cum_c[name]),
                       payout_lag_months=lag))
w("hybrid_stack_24mo.csv", ts)

# ---------------------------------------------------------------- payout timing (DSO analogue)
dso = [
    dict(platform="B&N Press", terms="~30 days after month end", avg_days_sale_to_cash=45, source=SRC["bn"]),
    dict(platform="Amazon KDP", terms="~60 days after month end", avg_days_sale_to_cash=75, source="https://www.thebookdesigner.com/barnes-and-noble-press-review/"),
    dict(platform="Draft2Digital", terms="Monthly, ~60-day lag", avg_days_sale_to_cash=75, source="https://books.by/compare/booksby-vs-draft2digital"),
    dict(platform="IngramSpark", terms="~90 days after month end (Sec. 9 of agreement)", avg_days_sale_to_cash=105, source="https://www.ingramspark.com/"),
]
w("payout_timing.csv", dso)

# ---------------------------------------------------------------- market context (mainstream sources)
w("market_bowker_isbn.csv", [
    dict(year=y, segment=s, titles=t, source="Bowker via Publishers Weekly (Mar 2026)",
         url="https://www.publishersweekly.com/pw/print/20260323/99943-book-output-topped-4-million-in-2025.html")
    for y, sp, tr in ((2022, 2459367, 584283), (2023, 2637565, 563019), (2024, 2545885, 602428), (2025, 3529980, 642242))
    for s, t in (("Self-published", sp), ("Traditional", tr))])
w("market_aap_formats_2025.csv", [
    dict(format=f, revenue_billions=v, yoy_change=c, source="Association of American Publishers StatShot Annual 2025",
         url="https://publishers.org/news/aap-statshot-annual-report-publishing-revenues-totaled-33-4-billion-for-calendar-year-2025/")
    for f, v, c in (("Hardback", 8.2, 0.039), ("Paperback", 8.0, 0.021), ("Digital audio", 2.5, 0.053), ("Ebook", 2.2, 0.032))])
w("market_headlines.csv", [
    dict(metric="U.S. publisher revenue, 2025", value="$33.4B", detail="+2.5% vs 2024", source="AAP StatShot Annual",
         url="https://publishers.org/news/aap-statshot-annual-report-publishing-revenues-totaled-33-4-billion-for-calendar-year-2025/"),
    dict(metric="ISBNs issued in the U.S., 2025", value="4.17M", detail="3.53M self-published (+38.7%)", source="Bowker via Publishers Weekly",
         url="https://www.publishersweekly.com/pw/print/20260323/99943-book-output-topped-4-million-in-2025.html"),
    dict(metric="Print units sold, 2025", value="762.4M", detail="+0.3% vs 2024", source="Circana BookScan via Publishers Weekly",
         url="https://www.publishersweekly.com/pw/by-topic/industry-news/bookselling/article/99417-print-book-sales-rose-slightly-in-2025.html"),
    dict(metric="Copyright registrations, FY2025", value="415,780", detail="169,098 literary works", source="U.S. Copyright Office",
         url="https://copyright.gov/history/USCO-Annual-Report-Facts-at-a-Glance.pdf"),
    dict(metric="Avg. e-filed registration time", value="3.4 months", detail="5.3 months with correspondence (Apr to Sep 2026)", source="U.S. Copyright Office",
         url="https://www.copyright.gov/registration/docs/processing-times-faqs.pdf"),
    dict(metric="Standard Application fee", value="$65 to $85", detail="New schedule effective mid-Nov 2026", source="Hypebot / Federal Register",
         url="https://www.hypebot.com/2-months-left-before-u-s-copyright-fees-jump-dramatically/"),
])
w("usco_registrations_fy2025.csv", [
    dict(category=c, registrations=n, url="https://copyright.gov/history/USCO-Annual-Report-Facts-at-a-Glance.pdf")
    for c, n in (("Literary", 169098), ("Performing arts", 166822), ("Visual arts", 79712))])
w("kenp_pool_rate.csv", [
    dict(month=m, per_page_rate=v, source="Profitable.app KENP tracker (author-reported)", url="https://profitable.app/kdp/stats/kenp-rate")
    for m, v in (("2025-05", 0.00440), ("2025-06", 0.00430), ("2025-07", 0.00419), ("2025-08", 0.00428),
                 ("2025-09", 0.00452), ("2025-10", 0.00501), ("2025-11", 0.00475), ("2025-12", 0.00480),
                 ("2026-01", 0.00420), ("2026-02", 0.00469), ("2026-03", 0.00469), ("2026-04", 0.00482))])
w("author_survey_2025.csv", [
    dict(segment=s, all_in_kdp_select=a, fully_wide=b, mixed=round(1-a-b, 2), source="Written Word Media 2025 Indie Author Survey",
         url="https://www.writtenwordmedia.com/2025-indie-author-survey-results/")
    for s, a, b in (("All respondents", 0.38, 0.30), ("Earning over $5,000/month", 0.43, 0.15))])

# ---------------------------------------------------------------- assumptions register
w("assumptions_register.csv", [dict(key=k, value=v) for k, v in A.items()])

summary = dict(kdp_print=pn["Amazon KDP"], is_print=pn["IngramSpark"], crossover_pd_is=crossover_pd_is,
               crossover_pd_d2d=crossover_pd_d2d)
print(summary)
for b in be: print(b["stack"], b["contribution_per_unit_pair"], b["breakeven_unit_pairs"], b["breakeven_platform_only"])
for a in ab: print(a["test"], a["breakeven_lift_required"], a["visitors_per_arm_80pct_power"])
