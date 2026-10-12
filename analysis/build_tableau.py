"""Build a Tableau packaged workbook (.twbx) with sheets, annotated dashboards and a captioned Story."""
import csv, uuid, zipfile, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tableau"
esc = lambda s: html.escape(str(s), quote=True)
COL = {"Amazon KDP": "#2a78d6", "IngramSpark": "#eb6834", "B&N Press": "#1baf7a", "Lulu Retail": "#eda100", "Lulu Bookstore": "#c98500",
       "Lulu": "#eda100", "PublishDrive": "#e87ba4", "Draft2Digital": "#008300", "Draft2Digital (ebook only)": "#008300",
       "Apple Books direct": "#6250d6", "KDP Expanded Distribution": "#e34948",
       "Self-published": "#2a78d6", "Traditional": "#6250d6",
       "Channel share": "#b9b8b2", "Production cost": "#eda100", "Platform fee": "#e34948", "Net royalty to IP owner": "#2a78d6",
       "Amazon KDP (print + ebook)": "#2a78d6", "IngramSpark (print)": "#eb6834", "Draft2Digital (ebook)": "#008300",
       "Bear": "#e34948", "Base": "#8a8984", "Bull": "#2a78d6"}

def sniff(fname):
    rows = list(csv.DictReader(open(ROOT / "data" / fname)))
    cols = []
    for k in rows[0].keys():
        vals = [r[k] for r in rows if r[k] not in ("", "None")]
        def isnum(v):
            try: float(v); return True
            except: return False
        if k == "year":
            cols.append((k, "integer"))
        elif not vals or not all(isnum(v) for v in vals):
            cols.append((k, "string"))
        elif all(float(v).is_integer() and "." not in v for v in vals):
            cols.append((k, "integer"))
        else:
            cols.append((k, "real"))
    return cols, rows

DS = {}
from tableauhyperapi import HyperProcess, Telemetry, Connection, CreateMode, TableDefinition, SqlType, TableName, Inserter
EXT = ROOT / "tableau" / "_extracts"
EXT.mkdir(exist_ok=True)
def write_hyper(fname, cols, rows):
    path = EXT / fname.replace(".csv", ".hyper")
    if path.exists(): path.unlink()
    st = {"string": SqlType.text(), "integer": SqlType.big_int(), "real": SqlType.double()}
    with HyperProcess(telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
        with Connection(hp.endpoint, str(path), CreateMode.CREATE_AND_REPLACE) as cx:
            cx.catalog.create_schema("Extract")
            td = TableDefinition(TableName("Extract", "Extract"), [TableDefinition.Column(c, st[t]) for c, t in cols])
            cx.catalog.create_table(td)
            conv = {"string": lambda v: v, "integer": lambda v: int(float(v)) if v not in ("", "None") else None, "real": lambda v: float(v) if v not in ("", "None") else None}
            with Inserter(cx, td) as ins:
                ins.add_rows([[conv[t](r[c]) for c, t in cols] for r in rows]); ins.execute()
    return path
def datasource(key, fname, color_field=None):
    cols, rows = sniff(fname)
    name = f"federated.{key}"
    conn = f"textscan.{key}"
    colxml = "".join(f"<column datatype='{t}' name='{esc(c)}' ordinal='{i}' />" for i, (c, t) in enumerate(cols))
    meta = "".join(
        f"<metadata-record class='column'><remote-name>{esc(c)}</remote-name><remote-type>{ {'string':129,'integer':20,'real':5}[t] }</remote-type>"
        f"<local-name>[{esc(c)}]</local-name><parent-name>[{esc(fname.replace('.csv','#csv'))}]</parent-name><remote-alias>{esc(c)}</remote-alias>"
        f"<ordinal>{i}</ordinal><local-type>{t}</local-type><aggregation>{'Count' if t=='string' else 'Sum'}</aggregation>"
        f"<contains-null>true</contains-null></metadata-record>" for i, (c, t) in enumerate(cols))
    fields = ""
    for c, t in cols:
        if t == "string" or c == "year":
            fields += f"<column datatype='{t}' name='[{esc(c)}]' role='dimension' type='{'ordinal' if c in ('year','month') else 'nominal'}' />"
        else:
            pct = c in ("breakeven_lift_required", "net_margin_pct", "variance_pct", "share_of_price", "yoy_change", "margin_of_safety_at_600", "baseline_conversion")
            cnt = c in ("titles", "breakeven_unit_pairs", "breakeven_platform_only", "unit_pairs", "visitors_per_arm_80pct_power", "avg_days_sale_to_cash", "payout_lag_days", "units_per_format_per_month", "month")
            rate = c == "per_page_rate"
            fmt = "p0.0%" if pct else ("n#,##0" if cnt else ("c&quot;$&quot;#,##0.00000" if rate else ("c&quot;$&quot;#,##0" if c in ("year1_net","cumulative_earned","cumulative_cash","cumulative_profit","total_fixed_year1") else "c&quot;$&quot;#,##0.00")))
            fields += f"<column datatype='{t}' default-format='{fmt}' name='[{esc(c)}]' role='measure' type='quantitative' />"
    style = ""
    if color_field:
        vals = list(dict.fromkeys(r[color_field] for r in rows))
        maps = "".join(f"<map to='{COL.get(v, '#8a8984')}'><bucket>&quot;{esc(v)}&quot;</bucket></map>" for v in vals)
        style = (f"<style><style-rule element='mark'><encoding attr='color' field='[none:{esc(color_field)}:nk]' type='palette'>{maps}</encoding>"
                 f"</style-rule></style>")
    DS[key] = dict(name=name, cols=dict(cols), caption=fname.replace(".csv", ""), rows=rows)
    write_hyper(fname, cols, rows)
    hyp = fname.replace(".csv", ".hyper")
    emeta = "".join(
        f"<metadata-record class='column'><remote-name>{esc(c)}</remote-name><remote-type>{ {'string':129,'integer':20,'real':5}[t] }</remote-type>"
        f"<local-name>[{esc(c)}]</local-name><parent-name>[Extract]</parent-name><remote-alias>{esc(c)}</remote-alias>"
        f"<ordinal>{i}</ordinal><family>[{esc(fname.replace('.csv','#csv'))}]</family><local-type>{t}</local-type><aggregation>{'Count' if t=='string' else 'Sum'}</aggregation>"
        f"<approx-count>{len(rows)}</approx-count><contains-null>true</contains-null></metadata-record>" for i, (c, t) in enumerate(cols))
    extract = (f"<extract count='-1' enabled='true' units='records'>"
               f"<connection access_mode='readonly' author-locale='en_US' class='hyper' dbname='Data/Extracts/{hyp}' default-settings='hyper' schema='Extract' sslmode='' tablename='Extract' update-time='10/12/2026 06:30:00 AM' username='tableau_internal_user'>"
               f"<relation name='Extract' table='[Extract].[Extract]' type='table' />"
               f"<refresh increment-key='' incremental-updates='false'><refresh-event add-from-file-path='' increment-value='%null%' refresh-type='create' rows-inserted='{len(rows)}' timestamp-start='2026-10-12 06:30:00.000' /></refresh>"
               f"<metadata-records>{emeta}</metadata-records></connection></extract>")
    return (f"<datasource caption='{esc(DS[key]['caption'])}' inline='true' name='{name}' version='18.1'>"
            f"<connection class='federated'><named-connections><named-connection caption='data' name='{conn}'>"
            f"<connection class='textscan' directory='Data/data' filename='{fname}' password='' server='' />"
            f"</named-connection></named-connections>"
            f"<relation connection='{conn}' name='{fname}' table='[{fname.replace('.csv','#csv')}]' type='table'>"
            f"<columns character-set='UTF-8' header='yes' locale='en_US' separator=','>{colxml}</columns></relation>"
            f"<metadata-records>{meta}</metadata-records></connection>"
            f"<aliases enabled='yes' />{fields}{extract}<layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.4' show-structure='true' />{style}</datasource>")

def ci(key, field, kind):
    """kind: nk (nominal dim), ok (ordinal dim), qk (continuous dim), sum/avg (measure)"""
    t = DS[key]["cols"][field]
    if kind in ("nk", "ok"):
        return (f"[none:{field}:{kind}]", f"<column-instance column='[{esc(field)}]' derivation='None' name='[none:{esc(field)}:{kind}]' pivot='key' type='{'nominal' if kind=='nk' else 'ordinal'}' />")
    if kind == "qk":
        return (f"[none:{field}:qk]", f"<column-instance column='[{esc(field)}]' derivation='None' name='[none:{esc(field)}:qk]' pivot='key' type='quantitative' />")
    d = {"sum": "Sum", "avg": "Avg"}[kind]
    return (f"[{kind}:{field}:qk]", f"<column-instance column='[{esc(field)}]' derivation='{d}' name='[{kind}:{esc(field)}:qk]' pivot='key' type='quantitative' />")

SHEETS = []
SHEET_COLOR = {}
def sheet(name, title, key, rows, cols, mark, color=None, label=None, filt=None, sort=None, subtitle=""):
    ds = DS[key]["name"]
    used = {}
    def ref(spec):
        f, kind = spec
        r, x = ci(key, f, kind); used[r] = x
        return f"[{ds}].{esc(r)}"
    rref = " / ".join(ref(s) for s in rows) if rows else ""
    cref = " / ".join(ref(s) for s in cols) if cols else ""
    enc = ""
    if color:
        enc += f"<color column='{ref(color)}' />"
        SHEET_COLOR[name] = f"[{ds}].[none:{esc(color[0])}:nk]"
    if label: enc += f"<text column='{ref(label)}' />"
    filt_xml = ""
    if filt:
        f, val = filt
        r = ref((f, "nk"))
        filt_xml = (f"<filter class='categorical' column='{r}'><groupfilter function='member' level='[none:{esc(f)}:nk]' "
                    f"member='&quot;{esc(val)}&quot;' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
    deps = "".join(f"<column datatype='{DS[key]['cols'][f]}' name='[{esc(f)}]' role='{'dimension' if DS[key]['cols'][f]=='string' or f=='year' else 'measure'}' type='{'nominal' if DS[key]['cols'][f]=='string' else 'quantitative'}' />"
                   for f in sorted({s[0] for s in (rows + cols + [c for c in (color, label) if c] + ([ (filt[0],'nk') ] if filt else []))}))
    sort_xml = ""
    if sort:
        dimf, measf = sort
        sort_xml = (f"<sort class='computed' column='[{ds}].[none:{esc(dimf)}:nk]' direction='DESC' using='[{ds}].[sum:{esc(measf)}:qk]' />")
    tstyle = "<style />"
    if color:
        cf = color[0]
        vals = list(dict.fromkeys(r[cf] for r in DS[key]["rows"]))
        maps = "".join(f"<map to='{COL.get(v, '#8a8984')}'><bucket>&quot;{esc(v)}&quot;</bucket></map>" for v in vals)
        tstyle = f"<style><style-rule element='mark'><encoding attr='color' field='[{ds}].[none:{esc(cf)}:nk]' type='palette'>{maps}</encoding></style-rule></style>"
    lbl_style = "<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' /></style-rule></style>" if label else ""
    sub = f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(subtitle)}</run>" if subtitle else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontsize='14'>{esc(title)}</run>{sub}</formatted-text></title></layout-options>"
         f"<table><view><datasources><datasource caption='{esc(DS[key]['caption'])}' name='{ds}' /></datasources>"
         f"<datasource-dependencies datasource='{ds}'>{deps}{''.join(used.values())}</datasource-dependencies>"
         f"{filt_xml}{sort_xml}<aggregation value='true' /></view>{tstyle}"
         f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
         f"<mark class='{mark}' /><encodings>{enc}</encodings>{lbl_style}</pane></panes>"
         f"<rows>{rref}</rows><cols>{cref}</cols></table><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></worksheet>")
    SHEETS.append((name, x))

# ---------------- data sources
dsx = [
 datasource("isbn", "market_bowker_isbn.csv", "segment"),
 datasource("gtn", "price_waterfall_long.csv", "component"),
 datasource("var", "cost_variance_drivers.csv", "driver"),
 datasource("ebook", "ebook_unit_economics.csv", "platform"),
 datasource("be", "breakeven.csv", "stack"),
 datasource("curve", "breakeven_curve.csv", "stack"),
 datasource("scen", "scenario_analysis.csv", "stack"),
 datasource("cash", "hybrid_stack_24mo.csv", "channel"),
 datasource("kenp", "kenp_pool_rate.csv"),
 datasource("ab", "ab_test_design.csv"),
 datasource("pay", "payout_timing.csv", "platform"),
]

# ---------------- worksheets
sheet("01 Market ISBNs", "U.S. ISBN output by segment, 2022 to 2025 (stacked)", "isbn", [("titles","sum")], [("year","qk")], "Area", color=("segment","nk"),
      subtitle="Source: Bowker via Publishers Weekly, March 2026")
sheet("02 Gross to Net", "Where each $16.99 of list price goes (print)", "gtn", [("platform","nk")], [("amount","sum")], "Bar", color=("component","nk"), label=("amount","sum"), filt=("format","Print"),
      subtitle="Model in this repository; platform rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive")
sheet("03 Cost Variance", "Cost variance vs Amazon KDP by driver, $ per print unit", "var", [("platform","nk")], [("variance","sum")], "Bar", color=("driver","nk"), label=("variance","sum"), filt=("format","Print"),
      subtitle="Positive = favorable to the IP owner. Drivers sum to the total variance.")
sheet("04 Ebook Net", "Net royalty per $4.99 ebook", "ebook", [("platform","nk")], [("net_royalty","sum")], "Bar", color=("platform","nk"), label=("net_royalty","sum"), sort=("platform","net_royalty"),
      subtitle="Store payout rates from ScribeCount; fees from KDP, Draft2Digital and the IngramSpark agreement")
sheet("05 Breakeven Units", "Unit pairs needed to recover Year-1 fixed costs", "be", [("stack","nk")], [("breakeven_unit_pairs","sum")], "Bar", color=("stack","nk"), label=("breakeven_unit_pairs","sum"),
      subtitle="Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions")
sheet("06 Breakeven Curve", "Cumulative profit by unit pairs sold", "curve", [("cumulative_profit","sum")], [("unit_pairs","qk")], "Line", color=("stack","nk"),
      subtitle="Each line crosses zero at its breakeven point")
sheet("07 Scenarios", "Year-1 net by scenario (bear 10, base 50, bull 250 units per format per month)", "scen", [("stack","nk")], [("scenario","nk"), ("year1_net","sum")], "Bar", color=("stack","nk"), label=("year1_net","sum"),
      subtitle="Planning scenarios, not forecasts")
sheet("08 Accrual vs Cash", "Cumulative royalties earned by channel (stacked), 24 months", "cash", [("cumulative_earned","sum")], [("month","qk")], "Area", color=("channel","nk"),
      subtitle="Illustrative hybrid stack; launch curve and 65/35 channel mix are assumptions")
sheet("09 Days to Cash", "Average days from sale to cash", "pay", [("platform","nk")], [("avg_days_sale_to_cash","sum")], "Bar", color=("platform","nk"), label=("avg_days_sale_to_cash","sum"),
      subtitle="B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by")
sheet("10 KENP Pool Rate", "Kindle Unlimited per-page payout rate", "kenp", [("per_page_rate","sum")], [("month","ok")], "Line", label=("per_page_rate","sum"),
      subtitle="Profitable.app KENP tracker (author-reported), May 2025 to April 2026")
sheet("11 AB Breakeven Lift", "Volume lift a challenger needs to match the control", "ab", [("test","nk")], [("breakeven_lift_required","sum")], "Bar", label=("breakeven_lift_required","sum"),
      subtitle="Two-proportion z-test sizing at alpha 0.05 and power 0.80")

# ---------------- dashboards with annotation text boxes
def dash(name, sheets, note, header):
    zid = [10]
    def nid(): zid[0] += 1; return zid[0]
    n = len(sheets)
    chart_h = 74000
    w_each = 100000 // n
    inner = ""
    for i, s in enumerate(sheets):
        if s in SHEET_COLOR and not s.startswith(("09", "05", "04", "07")):
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each-15000}' x='{i*w_each}' y='8000' />"
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' pane-specification-id='0' param='{SHEET_COLOR[s]}' type-v2='color' w='15000' x='{i*w_each + w_each - 15000}' y='8000' />"
        else:
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each}' x='{i*w_each}' y='8000' />"
    hdr = f"<zone h='8000' id='{nid()}' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontcolor='#0b0b0b' fontsize='18'>{esc(header)}</run></formatted-text></zone>"
    ann = (f"<zone h='18000' id='{nid()}' type-v2='text' w='100000' x='0' y='82000'><formatted-text>"
           f"<run bold='true' fontcolor='#eb6834' fontsize='11'>Annotation: </run><run fontcolor='#333333' fontsize='11'>{esc(note)}</run></formatted-text></zone>")
    return (f"<dashboard name='{esc(name)}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{hdr}{''.join(f for f in [inner])}{ann}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

DASH = [
 ("D1 Market", ["01 Market ISBNs"], "Self-published ISBNs rose 38.7% to 3.53 million in 2025, while Circana BookScan reports print unit sales up only 0.3% to 762.4 million. Supply is outgrowing demand, so margin per sale matters more each year.", "Market context: more works are competing for the same buyers",
  "Self-published ISBNs rose 38.7% in 2025."),
 ("D2 Gross to Net", ["02 Gross to Net"], "The gray channel share is the largest deduction on every wholesale route. On IngramSpark, the 55% bookstore discount takes $9.34 of each $16.99 before printing.", "Gross-to-net: where each $16.99 goes",
  "KDP nets $6.79 per paperback; IngramSpark nets $3.33."),
 ("D3 Cost Variance", ["03 Cost Variance"], "IngramSpark's $3.47 unfavorable variance to KDP breaks down into $2.55 of channel share, $0.60 of print cost and $0.32 of market access fee. The channel discount, not printing, is the main driver.", "Cost variance analysis vs the KDP baseline",
  "Retailer discounts drive most of the cost variance."),
 ("D4 Ebook", ["04 Ebook Net"], "Direct stores pay $3.49 on a $4.99 ebook. Aggregators trade $0.35 (Draft2Digital) to $0.52 (IngramSpark) per unit for one-upload reach.", "Ebook economics: direct uploads beat aggregators",
  "Direct ebook uploads keep the most per sale."),
 ("D5 Breakeven", ["05 Breakeven Units", "06 Breakeven Curve"], "KDP recovers $1,585 of Year-1 fixed costs after 158 unit pairs; IngramSpark needs 272. Platform fees alone are recovered within 42 pairs on every route, so the real breakeven risk sits in production spend.", "Breakeven analysis",
  "KDP breaks even at 158 unit pairs; IngramSpark at 272."),
 ("D6 Scenarios", ["07 Scenarios"], "KDP leads in the bear, base and bull cases. PublishDrive moves ahead of IngramSpark once volume passes the 16.6-unit monthly crossover, which happens in the base and bull cases.", "Scenario analysis: the ranking is stable across volumes",
  "Subscriptions win only above 16.6 units a month."),
 ("D7 Cash", ["08 Accrual vs Cash", "09 Days to Cash"], "At month 12, $948 of royalties has been earned but not yet received. IngramSpark pays about 60 days later than B&N Press, which raises days sales outstanding and the working-capital need.", "Accrual vs cash and days sales outstanding",
  "Cash arrives two to three months after each sale."),
 ("D8 Pool Volatility", ["10 KENP Pool Rate"], "The per-page rate averaged $4.55 per 1,000 pages with a 6.1% coefficient of variation, ranging from $4.19 to $5.01. Pool-based income works like music-streaming royalties and should be forecast as a range.", "Pool-based payouts: exclusive ebook income varies monthly",
  "Kindle Unlimited payouts vary month to month."),
 ("D9 AB Test", ["11 AB Breakeven Lift"], "A $16.99 to $14.99 price cut needs a 21.4% unit lift just to break even, which takes about 18,467 visitors per arm to detect at a 2% conversion rate. Set the breakeven lift before the test starts.", "A/B test design: the breakeven lift sets the bar",
  "A $2 price cut needs a 21.4% sales lift to pay off."),
]
dash_xml = [dash(n, s, note, hdr) for n, s, note, hdr, cap in DASH]

# ---------------- story
points = "".join(f"<story-point captured-sheet='{esc(n)}' caption='{esc(cap)}' id='{i+1}' />" for i, (n, s, note, hdr, cap) in enumerate(DASH))
story = (f"<dashboard name='IP Distribution Decision Verticals' type='storyboard'><style /><size maxheight='964' maxwidth='1366' minheight='964' minwidth='1366' sizing-mode='fixed' />"
         f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"
         f"<zone h='98000' id='2' param='vert' removable='false' type-v2='layout-flow' w='98800' x='600' y='1000'>"
         f"<zone h='5000' id='3' type-v2='title' w='98800' x='600' y='1000' />"
         f"<zone h='17000' id='4' is-fixed='true' paired-zone-id='5' removable='false' type-v2='flipboard-nav' w='98800' x='600' y='6000' />"
         f"<zone h='75000' id='5' paired-zone-id='4' removable='false' type-v2='flipboard' w='98800' x='600' y='23000'><flipboard active-id='1' nav-type='caption' show-nav-arrows='true'>"
         f"<story-points>{points}</story-points></flipboard></zone></zone></zone></zones>"
         f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

windows = "".join(f"<window class='worksheet' name='{esc(n)}'><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for n, _ in SHEETS)
windows += "".join(f"<window class='dashboard' name='{esc(d[0])}'><viewpoints>{''.join(f"<viewpoint name='{esc(x)}'><zoom type='entire-view' /></viewpoint>" for x in d[1])}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for d in DASH)
windows += f"<window class='dashboard' maximized='true' name='IP Distribution Decision Verticals'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"

twb = ("<?xml version='1.0' encoding='utf-8' ?>\n"
       "<workbook original-version='18.1' source-build='2024.1.0 (20241.24.0312.0830)' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>"
       "<document-format-change-manifest><_.fcp.MarkAnimation.true...MarkAnimation /><_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy /><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>"
       "<preferences><preference name='ui.encoding.shelf.height' value='24' /><preference name='ui.shelf.height' value='26' /></preferences>"
       f"<datasources>{''.join(dsx)}</datasources>"
       f"<worksheets>{''.join(x for _, x in SHEETS)}</worksheets>"
       f"<dashboards>{''.join(dash_xml)}{story}</dashboards>"
       f"<windows source-height='30'>{windows}</windows></workbook>")
twb = twb.replace("<document-format-change-manifest><_.fcp.MarkAnimation.true...MarkAnimation /><_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy /><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>",
                  "<document-format-change-manifest><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>")
name = "IP_Distribution_Decision_Verticals"
(OUT / f"{name}.twb").write_text(twb)
with zipfile.ZipFile(OUT / f"{name}.twbx", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"{name}.twb", twb)
    for f in (ROOT / "data").glob("*.csv"):
        z.write(f, f"Data/data/{f.name}")
    for f in EXT.glob("*.hyper"):
        z.write(f, f"Data/Extracts/{f.name}")
# story caption export for README
with open(OUT / "story_captions.md", "w") as f:
    f.write("# Tableau story captions\n\n")
    for i, (n, s, note, hdr, cap) in enumerate(DASH, 1):
        f.write(f"**Story point {i}.** {cap}\n\n*Annotation:* {note}\n\n")
print("ok", len(twb))
