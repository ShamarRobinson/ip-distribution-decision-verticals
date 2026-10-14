"""Where every number comes from: KPI definitions and worked calculations.

One source of truth for the README, the slide deck and the Tableau story. Every worked
example is computed from the files in /data, so the explanations stay in sync with the
numbers after each quarterly refresh. Run `python analysis/methods.py` to rewrite the
README section between the <!--METHODS--> markers and data/methods_reference.csv.
"""
import csv, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"

SOURCES = {
 "aap": ("AAP StatShot Annual Report 2025", "https://publishers.org/news/aap-statshot-annual-report-publishing-revenues-totaled-33-4-billion-for-calendar-year-2025/"),
 "bowker": ("Bowker via Publishers Weekly, Mar 2026", "https://www.publishersweekly.com/pw/print/20260323/99943-book-output-topped-4-million-in-2025.html"),
 "circana": ("Circana BookScan via Publishers Weekly", "https://www.publishersweekly.com/pw/by-topic/industry-news/bookselling/article/99417-print-book-sales-rose-slightly-in-2025.html"),
 "usco": ("U.S. Copyright Office, FY2025 Facts at a Glance", "https://copyright.gov/history/USCO-Annual-Report-Facts-at-a-Glance.pdf"),
 "uscotime": ("U.S. Copyright Office processing times", "https://www.copyright.gov/registration/docs/processing-times-faqs.pdf"),
 "uscofee": ("Hypebot on the 2026 USCO fee schedule", "https://www.hypebot.com/2-months-left-before-u-s-copyright-fees-jump-dramatically/"),
 "ingram": ("IngramSpark Help Center: 2026 pricing changes", "https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More"),
 "ingramtc": ("IngramSpark Agreement (Lightning Source)", "https://www.ingramspark.com/"),
 "kdp": ("Profitable.app KDP royalty calculator", "https://profitable.app/tools/kdp-royalty-calculator"),
 "kdped": ("BestWriting: KDP royalties explained", "https://bestwriting.com/kdp-royalties"),
 "bn": ("B&N Press Help Center: Getting paid", "https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales"),
 "lulu": ("Chapter: Lulu pricing (Sep 2026)", "https://blog.chapter.pub/lulu-pricing/"),
 "pd": ("PublishDrive Help: pricing plans", "https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans"),
 "d2d": ("PublishDrive vs Draft2Digital (Apr 2026)", "https://publishdrive.com/comparison-guide-publishdrive-vs-draft2digital.html"),
 "store": ("ScribeCount platform comparison", "https://scribecount.com/tools/platform-comparison"),
 "wwm": ("Written Word Media 2025 Indie Author Survey", "https://www.writtenwordmedia.com/2025-indie-author-survey-results/"),
 "kenp": ("Profitable.app KENP rate tracker", "https://profitable.app/kdp/stats/kenp-rate"),
 "tortora": ("Daniel Tortora: Self-publishing royalties 2026", "https://danieljtortora.com/blog/self-publishing-royalties"),
 "isbn": ("ScribeCount: How to publish on IngramSpark", "https://scribecount.com/author-resource/publishing-a-book/How-to-Publish-on-IngramSpark"),
 "bd": ("The Book Designer: B&N Press review", "https://www.thebookdesigner.com/barnes-and-noble-press-review/"),
 "booksby": ("Books.by: Draft2Digital comparison", "https://books.by/compare/booksby-vs-draft2digital"),
 "jf": ("Jane Friedman: IngramSpark 2026 pricing", "https://janefriedman.com/ingramspark-will-increase-pricing-in-2026/"),
 "model": ("Model in this repository (analysis/model.py)", "https://github.com/ShamarRobinson/ip-distribution-decision-verticals/blob/main/analysis/model.py"),
}


def _mn(m):
    import datetime as dt
    return dt.date(int(m[:4]), int(m[5:7]), 1).strftime("%B %Y")


ROUNDING = "Worked examples use unrounded values from the model, so a shown sum can differ from its parts by a cent."
FIRST_PAGE = 4  # story point number of the first analysis page (1 = introduction, 2 and 3 = KPI definitions)


def _rows(name):
    return list(csv.DictReader(open(D / name)))


def _f(x, d=2):
    x = float(x)
    return f"-${abs(x):,.{d}f}" if x < 0 else f"${x:,.{d}f}"


def build():
    """Return (kpis, pages): lists of dicts with worked numbers from /data."""
    A = {r["key"]: float(r["value"]) for r in _rows("assumptions_register.csv")}
    P = {r["platform"]: r for r in _rows("print_unit_economics.csv")}
    E = {r["platform"]: r for r in _rows("ebook_unit_economics.csv")}
    BE = {r["stack"]: r for r in _rows("breakeven.csv")}
    SC = {(r["scenario"], r["stack"]): float(r["year1_net"]) for r in _rows("scenario_analysis.csv")}
    CR = _rows("crossover_summary.csv")
    AB = _rows("ab_test_design.csv")
    PT = {r["platform"]: r for r in _rows("payout_timing.csv")}
    KP = [float(r["per_page_rate"]) * 1000 for r in _rows("kenp_pool_rate.csv")]
    KM = [r["month"] for r in _rows("kenp_pool_rate.csv")]
    HS = _rows("hybrid_stack_24mo.csv")
    ISBN = {(int(r["year"]), r["segment"]): int(r["titles"]) for r in _rows("market_bowker_isbn.csv")}
    AAP = {r["format"]: float(r["revenue_billions"]) for r in _rows("market_aap_formats_2025.csv")}
    TOTAL = float(next(r["value"] for r in _rows("market_headlines.csv") if r["metric"].startswith("U.S. publisher")).strip("$B"))

    LP, EP = A["list_price"], A["ebook_price"]
    k, i = P["Amazon KDP"], P["IngramSpark"]
    kn, inet = float(k["net_royalty"]), float(i["net_royalty"])
    kdp_print_cost = A["kdp_fixed"] + A["pages"] * A["kdp_per_page"]
    deliv = A["ebook_mb"] * A["kdp_deliv"]
    direct = EP * A["store_rate"]
    bk, bi = BE["Amazon KDP"], BE["IngramSpark"]
    cr_is = float(next(r["crossover_units_per_month"] for r in CR if "IngramSpark" in r["comparison"]))
    cr_d2d = float(next(r["crossover_units_per_month"] for r in CR if "Draft2Digital" in r["comparison"]))
    pdn = float(P["PublishDrive"]["net_royalty"]) + float(E["PublishDrive"]["net_royalty"])
    isn = float(bi["contribution_per_unit_pair"])
    ab1 = next(r for r in AB if r["test"].startswith("Price"))
    ab2 = next(r for r in AB if r["test"].startswith("Channel"))
    ab3 = next(r for r in AB if r["test"].startswith("Ebook"))
    m12 = [r for r in HS if int(r["month"]) == 12]
    earned12 = sum(float(r["cumulative_earned"]) for r in m12); cash12 = sum(float(r["cumulative_cash"]) for r in m12)
    y0, y1 = 2024, 2025
    sp0, sp1 = ISBN[(y0, "Self-published")], ISBN[(y1, "Self-published")]
    tot0 = sp0 + ISBN[(y0, "Traditional")]; tot1 = sp1 + ISBN[(y1, "Traditional")]
    prt = AAP["Hardback"] + AAP["Paperback"]
    kavg = sum(KP) / len(KP)
    msafe = float(bk["margin_of_safety_at_600"])

    kpis = [
     dict(kpi="Net royalty per copy", full="What the creator keeps from one sale",
          meaning="The money left for the IP (intellectual property) owner after the store, the printer and the platform are paid. The main measure in this story.",
          formula="Net royalty = list price - store's cut - printing cost - platform fee",
          worked=f"KDP paperback: {_f(LP)} - {_f(k['channel_share'])} - {_f(k['production_cost'])} - {_f(k['platform_fee'])} = {_f(kn)}. IngramSpark: {_f(LP)} - {_f(i['channel_share'])} - {_f(i['production_cost'])} - {_f(i['platform_fee'])} = {_f(inet)}.",
          sources=["kdp", "ingram", "bn", "lulu", "pd"]),
     dict(kpi="Net margin %", full="Share of the list price the creator keeps",
          meaning="Lets you compare formats and prices on one scale.",
          formula="Net margin % = net royalty / list price",
          worked=f"KDP paperback: {_f(kn)} / {_f(LP)} = {kn/LP:.1%}. KDP ebook: {_f(E['Amazon KDP']['net_royalty'])} / {_f(EP)} = {float(E['Amazon KDP']['net_royalty'])/EP:.1%}.",
          sources=["model"]),
     dict(kpi="Channel share (store's cut)", full="Also called the take rate",
          meaning="The part of the price the store or wholesaler keeps. It is the biggest cost on almost every route.",
          formula="Store's cut = list price x (1 - royalty rate), or list price x wholesale discount",
          worked=f"KDP pays a {A['kdp_print_rate']:.0%} print royalty, so the store keeps {_f(LP)} x {1-A['kdp_print_rate']:.0%} = {_f(k['channel_share'])}. IngramSpark's {A['is_disc']:.0%} wholesale discount: {_f(LP)} x {A['is_disc']:.0%} = {_f(i['channel_share'])}.",
          sources=["kdp", "ingram"]),
     dict(kpi="Cost variance vs KDP", full="Gap to the Amazon KDP (Kindle Direct Publishing) baseline, split by cause",
          meaning="Shows how much more or less each route keeps than KDP, and why.",
          formula="Variance = route's net - KDP net = store-cut driver + printing driver + fee driver (each driver = KDP's cost - the route's cost)",
          worked=f"IngramSpark: store cut {_f(i['var_channel_share'])} + printing {_f(i['var_production'])} + fee {_f(i['var_platform_fee'])} = {_f(i['variance_vs_kdp'])} per copy.",
          sources=["model", "kdp", "ingram"]),
     dict(kpi="Contribution per unit pair", full="Contribution margin for one print sale plus one ebook sale",
          meaning="What one reader buying both formats adds toward paying back launch costs.",
          formula="Contribution per pair = print net royalty + ebook net royalty",
          worked=f"KDP: {_f(kn)} + {_f(E['Amazon KDP']['net_royalty'])} = {_f(bk['contribution_per_unit_pair'])}. IngramSpark: {_f(inet)} + {_f(E['IngramSpark']['net_royalty'])} = {_f(isn)}.",
          sources=["model"]),
     dict(kpi="Breakeven point (unit pairs)", full="Sales needed to earn back Year-1 fixed costs",
          meaning="How many print-plus-ebook sales it takes before the work is profitable. Lower is better.",
          formula="Breakeven = Year-1 fixed costs / contribution per pair, rounded up. Fixed costs = platform setup + $85 copyright registration + $1,500 launch budget + 12 x monthly fee",
          worked=f"KDP: {_f(bk['total_fixed_year1'],0)} / {_f(bk['contribution_per_unit_pair'])} = {float(bk['total_fixed_year1'])/float(bk['contribution_per_unit_pair']):.1f}, rounded up to {bk['breakeven_unit_pairs']}. IngramSpark: {_f(bi['total_fixed_year1'],0)} / {_f(isn)} = {float(bi['total_fixed_year1'])/isn:.1f}, rounded up to {bi['breakeven_unit_pairs']}.",
          sources=["model", "uscofee", "isbn"]),
     dict(kpi="Margin of safety", full="Cushion between planned sales and breakeven",
          meaning="How far sales could fall before you stop covering costs.",
          formula="Margin of safety = (planned sales - breakeven) / planned sales",
          worked=f"KDP at 600 planned pairs: (600 - {bk['breakeven_unit_pairs']}) / 600 = {msafe:.1%}.",
          sources=["model"]),
     dict(kpi="Switch point (crossover)", full="Monthly sales where a flat fee beats a per-sale fee",
          meaning="Below it, pay-per-sale routes cost less; above it, a subscription costs less.",
          formula="Switch point = monthly subscription / extra money kept per pair on the subscription route",
          worked=f"PublishDrive vs IngramSpark: {_f(A['pd_sub'])} / ({_f(pdn)} - {_f(isn)}) = {cr_is:.1f} sales of each format a month. Ebook only vs Draft2Digital: {cr_d2d:.1f} a month.",
          sources=["pd", "ingram", "d2d"]),
     dict(kpi="Year-1 net (scenarios)", full="Money kept in the first year at a given sales level",
          meaning="Tests whether the ranking holds if sales are slow (10 a month), normal (50) or great (250).",
          formula="Year-1 net = 12 x (monthly sales x contribution per pair - monthly fee) - platform setup - $85 copyright registration (launch budget excluded)",
          worked=f"KDP at 50 a month: 12 x (50 x {_f(bk['contribution_per_unit_pair'])}) - $85 = {_f(SC[('Base','Amazon KDP')],0)}.",
          sources=["model"]),
     dict(kpi="DSO", full="Days sales outstanding",
          meaning="The average number of days between a sale and the cash arriving. Longer waits need more cash on hand.",
          formula="Days to cash = payment terms in days after month end + about 15 days (the average sale happens mid-month)",
          worked=f"B&N Press pays about 30 days after month end: 30 + 15 = {PT['B&N Press']['avg_days_sale_to_cash']} days. IngramSpark pays about 90 days after month end: 90 + 15 = {PT['IngramSpark']['avg_days_sale_to_cash']} days.",
          sources=["bn", "ingramtc", "bd", "booksby"]),
     dict(kpi="Working capital gap", full="Money earned but not yet received",
          meaning="The cash you are owed at a point in time because stores pay late.",
          formula="Gap = cumulative royalties earned - cumulative cash received",
          worked=f"Month 12 of the illustrative launch: {_f(earned12,0)} earned - {_f(cash12,0)} received = {_f(earned12-cash12,0)}.",
          sources=["model", "wwm"]),
     dict(kpi="KENP rate", full="Kindle Edition Normalized Pages payout rate",
          meaning="What Kindle Unlimited pays per page read, set monthly from a shared pot. Shown per 1,000 pages.",
          formula="Pay per 1,000 pages = monthly per-page rate x 1,000; average = mean of 12 months; range = highest - lowest",
          worked=f"Average {_f(kavg)}; range {_f(max(KP))} - {_f(min(KP))} = {_f(max(KP)-min(KP))} ({max(KP)/min(KP)-1:.0%} from low to high).",
          sources=["kenp"]),
     dict(kpi="Breakeven lift", full="Extra sales a cheaper option needs just to tie",
          meaning="The bar an A/B test (a test of version A against version B) must clear before switching to a lower price.",
          formula="Breakeven lift = net per copy of A / net per copy of B - 1",
          worked=f"Print price test: KDP net at $16.99 = {_f(ab1['net_per_unit_A'])}; at $14.99 = $14.99 x 60% - {_f(kdp_print_cost)} = {_f(ab1['net_per_unit_B'])}; {_f(ab1['net_per_unit_A'])} / {_f(ab1['net_per_unit_B'])} - 1 = {float(ab1['breakeven_lift_required']):.1%}.",
          sources=["kdp", "model"]),
     dict(kpi="Sample size per group", full="Shoppers each version needs for a trustworthy A/B result",
          meaning="Too few shoppers and a difference may be luck.",
          formula="Two-proportion z-test at 95% confidence (z = 1.96) and 80% power (z = 0.84) for the breakeven lift",
          worked=f"Print price test at a 2% baseline conversion rate and a {float(ab1['breakeven_lift_required']):.1%} lift: {int(ab1['visitors_per_arm_80pct_power']):,} shoppers per group. Ebook test at 3%: {int(ab3['visitors_per_arm_80pct_power']):,}.",
          sources=["model"]),
    ]

    pages = [
     dict(page="Market context", dash="D1 Market", numbers=f"{sp1/1e6:.2f}M self-published ISBNs (International Standard Book Numbers) in {y1}, +{sp1/sp0-1:.1%}; total {tot1/1e6:.2f}M, +{tot1/tot0-1:.1%}",
          calc=f"Growth = {y1} count / {y0} count - 1 = {sp1:,} / {sp0:,} - 1 = {sp1/sp0-1:.1%}. Print share of revenue = (hardback {_f(AAP['Hardback'],1)}B + paperback {_f(AAP['Paperback'],1)}B) / {_f(TOTAL,1)}B = {prt/TOTAL:.0%}.",
          sources=["bowker", "circana", "aap"]),
     dict(page="Gross-to-net", dash="D2 Gross to Net", numbers=f"KDP keeps {_f(kn)}; IngramSpark {_f(inet)} on a {_f(LP)} paperback",
          calc=f"KDP printing = {_f(A['kdp_fixed'])} + {int(A['pages'])} pages x {_f(A['kdp_per_page'],3)} = {_f(kdp_print_cost)}. IngramSpark fee = {A['is_maf']:.3%} market access fee x {_f(LP)} = {_f(i['platform_fee'])}. Print costs for IngramSpark ({_f(A['ingram_print'])}), B&N Press ({_f(A['bn_print'])}) and Lulu ({_f(A['lulu_print'])}) are planning estimates.",
          sources=["kdp", "ingram", "bn", "lulu", "pd"]),
     dict(page="Cost variance", dash="D3 Cost Variance", numbers=f"IngramSpark keeps {_f(abs(float(i['variance_vs_kdp'])))} less per copy than KDP; {_f(abs(float(i['var_channel_share'])))} of it is the store's cut",
          calc=f"Store-cut driver = KDP {_f(k['channel_share'])} - IngramSpark {_f(i['channel_share'])} = {_f(i['var_channel_share'])}; printing = {_f(k['production_cost'])} - {_f(i['production_cost'])} = {_f(i['var_production'])}; fee = {_f(k['platform_fee'])} - {_f(i['platform_fee'])} = {_f(i['var_platform_fee'])}. The three add up to {_f(i['variance_vs_kdp'])}.",
          sources=["model", "kdp", "ingram"]),
     dict(page="Ebooks", dash="D4 Ebook", numbers=f"Direct uploads keep {_f(direct)}; KDP {_f(E['Amazon KDP']['net_royalty'])}; Draft2Digital {_f(E['Draft2Digital']['net_royalty'])}; IngramSpark {_f(E['IngramSpark']['net_royalty'])}",
          calc=f"Direct: {_f(EP)} x {A['store_rate']:.0%} = {_f(direct)}. KDP: ({_f(EP)} - {_f(deliv)} delivery fee) x {A['kdp_eb_hi']:.0%} = {_f(E['Amazon KDP']['net_royalty'])}. Draft2Digital: {_f(direct)} x {1-A['d2d_share']:.0%} = {_f(E['Draft2Digital']['net_royalty'])}. IngramSpark: {_f(direct)} x {1-A['is_digital']:.0%} = {_f(E['IngramSpark']['net_royalty'])}.",
          sources=["store", "kdp", "d2d", "ingramtc"]),
     dict(page="Breakeven", dash="D5 Breakeven", numbers=f"KDP {bk['breakeven_unit_pairs']} pairs; IngramSpark {bi['breakeven_unit_pairs']}; slowest {max(BE.values(), key=lambda r: int(r['breakeven_unit_pairs']))['breakeven_unit_pairs']}",
          calc=f"Year-1 fixed costs = platform setup (ISBN, or International Standard Book Number, {_f(A['isbn'],0)} where you buy your own) + {_f(A['copyright_fee'],0)} copyright registration + {_f(A['launch_budget'],0)} illustrative launch budget + subscription. KDP: {_f(bk['total_fixed_year1'],0)} / {_f(bk['contribution_per_unit_pair'])} per pair, rounded up = {bk['breakeven_unit_pairs']}.",
          sources=["model", "uscofee", "isbn", "pd"]),
     dict(page="Scenarios", dash="D6 Scenarios", numbers=f"KDP Year-1 net {_f(SC[('Bear','Amazon KDP')],0)} / {_f(SC[('Base','Amazon KDP')],0)} / {_f(SC[('Bull','Amazon KDP')],0)} at 10 / 50 / 250 sales a month; switch point {cr_is:.1f}",
          calc=f"12 x (monthly sales x contribution per pair - monthly fee) - platform setup - {_f(A['copyright_fee'],0)} copyright. Switch point = {_f(A['pd_sub'])} PublishDrive fee / ({_f(pdn)} - {_f(isn)}) = {cr_is:.1f}.",
          sources=["model", "pd"]),
     dict(page="Cash timing", dash="D7 Cash", numbers=f"{_f(earned12-cash12,0)} owed at month 12; {PT['B&N Press']['avg_days_sale_to_cash']} to {PT['IngramSpark']['avg_days_sale_to_cash']} days to cash",
          calc="Illustrative launch: 120 sales of each format in month 1, falling 8% a month to 40; 65% on Amazon, 35% elsewhere. KDP and Draft2Digital pay 2 months later, IngramSpark 3. Days to cash = payment terms + about 15 days.",
          sources=["model", "wwm", "bn", "ingramtc"]),
     dict(page="Kindle Unlimited", dash="D8 Pool Volatility", numbers=f"{_f(min(KP))} to {_f(max(KP))} per 1,000 pages; average {_f(kavg)}",
          calc=f"Author-reported monthly KENP (Kindle Edition Normalized Pages) rates from {_mn(KM[0])} to {_mn(KM[-1])}, multiplied by 1,000. Average = sum of 12 months / 12.",
          sources=["kenp"]),
     dict(page="A/B test", dash="D9 AB Test", numbers=f"Price cuts need {float(ab1['breakeven_lift_required']):.0%} to {float(ab3['breakeven_lift_required']):.0%} more sales; store terms {float(ab2['breakeven_lift_required']):.0%}",
          calc=f"Ebook: KDP net at $4.99 = {_f(ab3['net_per_unit_A'])}, at $3.99 = {_f(ab3['net_per_unit_B'])}, lift = {float(ab3['breakeven_lift_required']):.1%}. Store terms: IngramSpark net at a 40% non-returnable discount ({_f(ab2['net_per_unit_B'])}) / at 55% returnable ({_f(ab2['net_per_unit_A'])}) - 1 = {float(ab2['breakeven_lift_required']):.1%}.",
          sources=["kdp", "ingram", "model"]),
    ]
    return kpis, pages


def _md_sources(keys):
    return "; ".join(f"[{SOURCES[k][0]}]({SOURCES[k][1]})" for k in keys)


def readme_section(kpis, pages):
    asof = json.load(open(ROOT / "as_of.json"))["as_of_label"]
    out = [f"Every figure below is computed from the files in [/data](data), which [analysis/model.py](analysis/model.py) builds from one assumptions list. Worked examples use the {asof} values and update with each quarterly refresh. {ROUNDING}\n",
           "### KPI definitions\n", "| KPI (key performance indicator) | What it tells you | Formula | Worked example | Sources |", "|---|---|---|---|---|"]
    for r in kpis:
        out.append(f"| **{r['kpi']}** ({r['full']}) | {r['meaning']} | {r['formula']} | {r['worked']} | {_md_sources(r['sources'])} |")
    out += ["", "### Where each story number comes from\n", "| Story point | Numbers shown | How they are calculated | Sources |", "|---|---|---|---|"]
    for n, r in enumerate(pages, FIRST_PAGE):
        out.append(f"| {n}. {r['page']} | {r['numbers']} | {r['calc']} | {_md_sources(r['sources'])} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    kpis, pages = build()
    with open(D / "methods_reference.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["type", "name", "description", "formula_or_numbers", "worked_or_calculation", "sources"])
        for r in kpis: w.writerow(["KPI", f"{r['kpi']} ({r['full']})", r["meaning"], r["formula"], r["worked"], "; ".join(SOURCES[k][0] for k in r["sources"])])
        for n, r in enumerate(pages, FIRST_PAGE): w.writerow(["Story point", f"{n}. {r['page']}", "", r["numbers"], r["calc"], "; ".join(SOURCES[k][0] for k in r["sources"])])
    rd = ROOT / "README.md"; t = rd.read_text()
    a, b = "<!--METHODS-->", "<!--/METHODS-->"
    if a in t:
        t = t[:t.index(a) + len(a)] + "\n" + readme_section(kpis, pages) + t[t.index(b):]
        rd.write_text(t)
    print("methods:", len(kpis), "KPIs,", len(pages), "story points")
