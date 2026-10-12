"""Build a Tableau packaged workbook (.twbx) with sheets, annotated dashboards and a captioned Story."""
import csv, uuid, zipfile, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import json
ASOF = json.load(open(ROOT / "as_of.json"))["as_of_label"]
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
            cnt = c in ("n", "titles", "breakeven_unit_pairs", "breakeven_platform_only", "unit_pairs", "visitors_per_arm_80pct_power", "avg_days_sale_to_cash", "payout_lag_days", "units_per_format_per_month", "month")
            rate = c == "per_page_rate"
            fmt = "p0.0%" if pct else ("n#,##0" if cnt else ("c&quot;$&quot;#,##0.00000" if rate else ("c&quot;$&quot;#,##0" if c in ("year1_net","cumulative_earned","cumulative_cash","cumulative_profit","total_fixed_year1") else "c&quot;$&quot;#,##0.00")))
            fields += f"<column datatype='{t}' default-format='{fmt}' name='[{esc(c)}]' role='measure' type='quantitative' />"
    ALIAS = {"component": {"Channel share": "Store's cut (channel share)", "Net royalty to IP owner": "What the creator keeps (net royalty)", "Platform fee": "Platform fees", "Production cost": "Printing (production cost)"},
             "driver": {"Channel share": "Store's cut (channel share)", "Platform fee": "Platform fees", "Production cost": "Printing (production cost)"},
             "segment": {"Self-published": "Self-published (authors on their own)", "Traditional": "Traditional (publishing houses)"},
             "channel": {"Amazon KDP (print + ebook)": "Earned through Amazon KDP (print + ebook)", "IngramSpark (print)": "Earned through IngramSpark (print)", "Draft2Digital (ebook)": "Earned through Draft2Digital (ebook)"}}
    for fld, amap in ALIAS.items():
        tag = f"<column datatype='string' name='[{fld}]' role='dimension' type='nominal' />"
        if tag in fields:
            al = "".join(f"<alias key='&quot;{esc(k)}&quot;' value='{esc(v)}' />" for k, v in amap.items())
            fields = fields.replace(tag, f"<column datatype='string' name='[{fld}]' role='dimension' type='nominal'><aliases>{al}</aliases></column>")
    CAP = {"component": "Where the $16.99 goes", "driver": "Cause of the gap vs KDP", "segment": "Who published", "channel": "Sales channel",
           "platform": "Platform", "stack": "Platform", "test": "Test", "scenario": "Scenario", "month": "Month", "year": "Year"}
    for fld, cap in CAP.items():
        fields = fields.replace(f"<column datatype='string' name='[{fld}]'", f"<column caption='{esc(cap)}' datatype='string' name='[{fld}]'")
        fields = fields.replace(f"<column datatype='integer' name='[{fld}]'", f"<column caption='{esc(cap)}' datatype='integer' name='[{fld}]'")
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
    lbl_style = "<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' />" + ("<format attr='mark-markers-mode' value='all' />" if mark == 'Line' else "") + "</style-rule></style>" if label else ("<style><style-rule element='mark'><format attr='mark-markers-mode' value='all' /></style-rule></style>" if mark == 'Line' else "")
    sub = f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(subtitle)}</run>" if subtitle else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontsize='14'>{esc(title)}</run>{sub}</formatted-text></title></layout-options>"
         f"<table><view><datasources><datasource caption='{esc(DS[key]['caption'])}' name='{ds}' /></datasources>"
         f"<datasource-dependencies datasource='{ds}'>{deps}{''.join(used.values())}</datasource-dependencies>"
         f"{filt_xml}{sort_xml}<aggregation value='true' /></view>{tstyle}"
         f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
         f"<mark class='{mark}' /><encodings>{enc}</encodings>{lbl_style}</pane></panes>"
         f"<rows>{rref}</rows><cols>{cref}</cols></table><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></worksheet>")
    SHEETS.append((name, x))

SRC_LINKS = {'D1 Market': [('Bowker via Publishers Weekly', 'https://www.publishersweekly.com/pw/print/20260323/99943-book-output-topped-4-million-in-2025.html'), ('Circana BookScan via Publishers Weekly', 'https://www.publishersweekly.com/pw/by-topic/industry-news/bookselling/article/99417-print-book-sales-rose-slightly-in-2025.html')], 'D2 Gross to Net': [('IngramSpark 2026 pricing', 'https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('B&N Press royalties', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales'), ('Lulu pricing', 'https://blog.chapter.pub/lulu-pricing/')], 'D3 Cost Variance': [('IngramSpark 2026 pricing', 'https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator')], 'D4 Ebook': [('ScribeCount platform comparison', 'https://scribecount.com/tools/platform-comparison'), ('PublishDrive vs Draft2Digital', 'https://publishdrive.com/comparison-guide-publishdrive-vs-draft2digital.html'), ('IngramSpark', 'https://www.ingramspark.com/')], 'D5 Breakeven': [('USCO 2026 fee schedule (Hypebot)', 'https://www.hypebot.com/2-months-left-before-u-s-copyright-fees-jump-dramatically/'), ('ISBN pricing (ScribeCount)', 'https://scribecount.com/author-resource/publishing-a-book/How-to-Publish-on-IngramSpark'), ('PublishDrive plans', 'https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans')], 'D6 Scenarios': [('PublishDrive plans', 'https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('B&N Press royalties', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales')], 'D7 Cash': [('B&N Press payments', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales'), ('IngramSpark', 'https://www.ingramspark.com/'), ('Written Word Media 2025 survey', 'https://www.writtenwordmedia.com/2025-indie-author-survey-results/')], 'D8 Pool Volatility': [('Profitable.app KENP tracker', 'https://profitable.app/kdp/stats/kenp-rate'), ('Written Word Media 2025 survey', 'https://www.writtenwordmedia.com/2025-indie-author-survey-results/')], 'D9 AB Test': [('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('Model and method on GitHub', 'https://github.com/ShamarRobinson/ip-distribution-decision-verticals')]}
# ---------------- sources table for named, clickable links
import csv as _csv
with open(ROOT / "data" / "story_sources.csv", "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["dashboard", "n", "source", "url", "as_of"])
    for _d, _lst in SRC_LINKS.items():
        for _i, (_t, _u) in enumerate(_lst, 1):
            _w.writerow([_d, _i, _t, _u, json.load(open(ROOT / "as_of.json"))["as_of"]])

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
 datasource("src", "story_sources.csv"),
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

for _d in SRC_LINKS:
    sheet(f"Sources {_d[:2]}", "Sources (click a name to open it)", "src", [("n", "ok")], [], "Text", label=("source", "nk"), filt=("dashboard", _d))
# add url to detail of each source sheet so the URL action can read it
import re as _re
for _i, (_n, _x) in enumerate(SHEETS):
    if _n.startswith("Sources "):
        ds = DS["src"]["name"]
        _x = _x.replace("<encodings>", f"<encodings><lod column='[{ds}].[none:url:nk]' />")
        _x = _x.replace("</view><style /><panes>", "</view><style><style-rule element='worksheet'><format attr='display-field-labels' scope='rows' value='false' /></style-rule></style><panes>")
        _x = _x.replace("</datasource-dependencies>", f"<column-instance column='[url]' derivation='None' name='[none:url:nk]' pivot='key' type='nominal' /></datasource-dependencies>", 1)
        _x = _x.replace("<column datatype='string' name='[source]'", "<column datatype='string' name='[url]' role='dimension' type='nominal' /><column datatype='string' name='[source]'", 1)
        SHEETS[_i] = (_n, _x)

# ---------------- dashboards with annotation text boxes
def dash(name, sheets, note, header):
    zid = [10]
    def nid(): zid[0] += 1; return zid[0]
    n = len(sheets)
    chart_h = 64000
    w_each = 100000 // n
    inner = ""
    for i, s in enumerate(sheets):
        if s in SHEET_COLOR:
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each-15000}' x='{i*w_each}' y='8000' />"
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' pane-specification-id='0' param='{SHEET_COLOR[s]}' type-v2='color' w='15000' x='{i*w_each + w_each - 15000}' y='8000' />"
        else:
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each}' x='{i*w_each}' y='8000' />"
    hdr = f"<zone h='8000' id='{nid()}' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontcolor='#0b0b0b' fontsize='18'>{esc(header)}</run></formatted-text></zone>"
    ann = (f"<zone h='28000' id='{nid()}' type-v2='text' w='64000' x='0' y='72000'><formatted-text>"
           f"<run bold='true' fontcolor='#0b0b0b' fontsize='11'>As of {esc(ASOF)}: </run>"
           f"<run fontcolor='#1f1f1f' fontsize='11'>{esc(note)}</run></formatted-text></zone>"
           f"<zone h='28000' id='{nid()}' name='Sources {esc(name[:2])}' show-title='true' w='36000' x='64000' y='72000' />")
    return (f"<dashboard name='{esc(name)}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{hdr}{''.join(f for f in [inner])}{ann}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

DASH = [
 ("D1 Market", ["01 Market ISBNs"], "Every book edition gets an ID number called an ISBN, so counting ISBNs shows how many new books come out. Self-published titles (blue area) jumped 38.7% in 2025 while printed-book sales rose only 0.3%. More books are competing for the same buyers, which makes the share of each sale you keep more important.", "Market context: more works are competing for the same buyers",
  "Self-published ISBNs rose 38.7% in 2025."),
 ("D2 Gross to Net", ["02 Gross to Net"], "Each bar is one $16.99 book split by who gets paid. Red is the store's cut, orange is printing, blue is platform fees, and teal is what the creator keeps. KDP leaves the creator $6.79, while IngramSpark's bookstore route leaves $3.33. Finance teams call this breakdown gross-to-net.", "Gross-to-net: where each $16.99 goes",
  "KDP nets $6.79 per paperback; IngramSpark nets $3.33."),
 ("D3 Cost Variance", ["03 Cost Variance"], "This is a cost variance analysis: every option is compared with Amazon KDP. Bars left of zero mean you keep less per book than on KDP, and each color is one cause (red = store's cut, orange = printing, blue = platform fees). For IngramSpark, the store's cut explains $2.55 of the $3.47 gap.", "Cost variance analysis vs the KDP baseline",
  "Retailer discounts drive most of the cost variance."),
 ("D4 Ebook", ["04 Ebook Net"], "For a $4.99 ebook, each bar shows what the creator keeps after the store and any middleman are paid. Selling directly to Apple or B&N keeps $3.49. Aggregators like Draft2Digital keep 35 to 52 cents more per sale in exchange for sending your book to many stores with one upload.", "Ebook economics: direct uploads beat aggregators",
  "Direct ebook uploads keep the most per sale."),
 ("D5 Breakeven", ["05 Breakeven Units", "06 Breakeven Curve"], "Breakeven is the number of sales needed to earn back what you spent to launch: the copyright fee, platform fees and a production budget. KDP gets there after 158 sales of a print book plus an ebook, and IngramSpark after 272. On the right, the point where each line crosses $0 is breakeven; steeper lines get there sooner.", "Breakeven analysis",
  "KDP breaks even at 158 unit pairs; IngramSpark at 272."),
 ("D6 Scenarios", ["07 Scenarios"], "Scenario analysis asks 'what if?' at three sales levels: slow (10 a month), normal (50) and great (250). KDP finishes first in every case, so the decision holds up even if the sales forecast is off. A flat monthly fee (PublishDrive) only beats a per-sale fee once you sell about 17 of each format a month.", "Scenario analysis: the ranking is stable across volumes",
  "Subscriptions win only above 16.6 units a month."),
 ("D7 Cash", ["08 Accrual vs Cash", "09 Days to Cash"], "The stacked areas show royalties earned over 24 months. Stores pay two to three months after a sale, so at month 12 about $948 has been earned but not yet received. The bars show days sales outstanding: B&N Press pays in about 45 days, IngramSpark in about 105, so longer waits require more cash on hand.", "Accrual vs cash and days sales outstanding",
  "Cash arrives two to three months after each sale."),
 ("D8 Pool Volatility", ["10 KENP Pool Rate"], "Kindle Unlimited pays authors from one shared monthly pot, split by pages read, so the rate per page changes every month. Over the past year it ranged from $4.19 to $5.01 per 1,000 pages, averaging $4.55. Treat this income as a range, not a fixed number.", "Pool-based payouts: exclusive ebook income varies monthly",
  "Kindle Unlimited payouts vary month to month."),
 ("D9 AB Test", ["11 AB Breakeven Lift"], "A cheaper price earns less per book, so it only helps if it sells enough extra copies. Each bar shows that minimum boost, called the breakeven lift: a $2 print price cut needs 21% more sales. In an A/B test, switch only if sales rise by more than the bar, measured with enough shoppers (about 18,467 per group) to trust the result.", "A/B test design: the breakeven lift sets the bar",
  "A $2 price cut needs a 21.4% sales lift to pay off."),
]
dash_xml = [dash(n, s, note, hdr) for n, s, note, hdr, cap in DASH]

PATHS = [
 ("A. Independent creator", "#2a78d6", [
  ("Best choice", "Amazon KDP for both print and ebook."),
  ("Choose this when", "you have one or two titles, most readers find you on Amazon, and your launch budget is tight."),
  ("Why", "KDP keeps the most per print copy ($6.79 of a $16.99 book), costs nothing to start, and breaks even fastest (158 sales of a print book plus an ebook). Adding bookstore distribution now would roughly halve what you keep per copy without a plan to win shelf space."),
  ("Next move", "Test $14.99 against $16.99 for 90 days and switch only if sales rise more than 21%. After breakeven, add a wide ebook route (Path E), or try KDP Select if your genre is popular in Kindle Unlimited.")]),
 ("B. Small press or imprint", "#eb6834", [
  ("Best choice", "KDP for Amazon plus IngramSpark for bookstores and libraries."),
  ("Choose this when", "shelf placement, library orders or event sales matter, and each title sells fewer than about 17 copies of each format a month."),
  ("Why", "Only IngramSpark reaches 45,000+ stores and libraries, and at this volume its per-sale fees cost less than a subscription. The trade-off: bookstores expect a 55% discount, so you keep $3.33 a copy versus $6.79 on KDP."),
  ("Next move", "Start non-returnable, because returns can cost more than you earned and switching later leaves a 180-day tail. Test a 40% non-returnable discount ($5.87 a copy) against 55% returnable; returnable must sell 77% more to win. Plan for a 105-day wait to get paid.")]),
 ("C. Catalog or backlist owner", "#e87ba4", [
  ("Best choice", "KDP for Amazon plus a PublishDrive monthly plan for everywhere else."),
  ("Choose this when", "you have many titles or steady sales above about 17 of each format a month."),
  ("Why", "A flat fee replaces IngramSpark's 1.875% fee on every sale and its 15% ebook cut, while printing through the same Ingram network. At 50 sales a month, Year-1 earnings are $3,905 versus $3,568 on IngramSpark; at 250 a month, $21,038 versus $18,678."),
  ("Next move", "Move half the catalog first and compare 90 days of results. Keep slow sellers on a per-sale route, and pick the plan tier ($13.99 to $83.99) by title count.")]),
 ("D. Brand, educator or corporate IP owner", "#eda100", [
  ("Best choice", "Your own online store with print-on-demand (Lulu Direct) plus KDP."),
  ("Choose this when", "buyers come from you (clients, students, events, an email list or your website) rather than from browsing a store."),
  ("Why", "No store takes a cut, so you keep about $9.59 or more per $16.99 copy versus $6.79 on KDP, and you keep the customer relationship. KDP still adds discovery and reviews."),
  ("Next move", "Split one campaign's traffic between your store and Amazon and compare money kept per visitor. Watch printing, shipping and support costs as direct sales grow; use IngramSpark Share & Sell links for one-off campaigns.")]),
 ("E. Wide ebook strategist", "#1baf7a", [
  ("Best choice", "KDP for Kindle plus direct uploads to Apple, Kobo and B&N, or Draft2Digital to reach them all."),
  ("Choose this when", "ebooks drive most of your income and you want readers outside Amazon, such as libraries, Apple users or international buyers."),
  ("Why", "Direct uploads keep $3.49 per $4.99 ebook; Draft2Digital keeps $3.14 but saves time with one upload. Price between $2.99 and $9.99 to earn KDP's 70% rate."),
  ("Next move", "Go direct if you can manage several dashboards; use Draft2Digital if your time is worth more than 35 cents a sale. Test Kindle Unlimited with one title for one 90-day term (pay swings $4.19 to $5.01 per 1,000 pages), and compare a PublishDrive plan above about 40 ebook sales a month.")]),
]
def rec_dash(dname, items, heading):
    zones = (f"<zone h='8500' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='11'>&#10;Find your type, then read its best choice. As of {esc(ASOF)}. Decision trees for each path are in the slide deck linked from the GitHub page.</run></formatted-text></zone>")
    cols = [items[:3], items[3:]]
    zid = 20
    for ci_, col in enumerate(cols):
        h = (100000 - 9000) // 3
        for ri, (t, c, rows) in enumerate(col):
            runs = f"<run bold='true' fontcolor='{c}' fontsize='14'>{esc(t)}</run>"
            for lab, txt in rows:
                runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='10'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='10'>{esc(txt)}</run>"
            zones += f"<zone h='{h}' id='{zid}' type-v2='text' w='49000' x='{ci_*51000}' y='{9000 + ri*h}'><formatted-text>{runs}</formatted-text></zone>"
            zid += 1
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
INTRO = [
 ("Purpose", "#2a78d6", [
  ("The question", "Where should you sell a creative work, such as a book, guide or course, so you keep the most money from each sale, with risk and payment timing you can live with?"),
  ("What you get", "Each story point compares the same six platforms using their published prices, fees and payout rates, explains the result in plain language, and names its sources. The last point turns the findings into a recommendation for each type of owner.")]),
 ("Scope", "#eb6834", [
  ("Platforms", "Amazon KDP, IngramSpark, Barnes & Noble Press, Lulu, PublishDrive and Draft2Digital."),
  ("Base case", "A $16.99 paperback (200 pages) and a $4.99 ebook sold in the United States."),
  ("Measures", "What the creator keeps per sale, cost variance against KDP, breakeven, slow, normal and strong sales scenarios, time from sale to cash, Kindle Unlimited payouts and A/B test sizing."),
  ("Not covered", "Tax or legal advice, audiobooks and traditional publishing contracts. Figures are planning estimates, not forecasts, and are refreshed every quarter.")]),
 ("Stakeholders", "#1baf7a", [
  ("A. Independent creator", "one or two titles, Amazon-led discovery and a tight budget."),
  ("B. Small press or imprint", "needs bookstore and library placement."),
  ("C. Catalog or backlist owner", "many titles with steady sales."),
  ("D. Brand, educator or corporate IP owner", "has its own audience and sells direct."),
  ("E. Wide ebook strategist", "digital-first, selling through many stores."),
  ("Also useful for", "finance, operations and marketing teams at any business that sells through middlemen.")]),
]
def intro_dash(dname, items, heading):
    zones = (f"<zone h='10000' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='11'>&#10;Prices, fees and rates as of {esc(ASOF)}. Use the arrows or the cards above to move through the story.</run></formatted-text></zone>")
    hs = [26000, 32000, 31500]
    y = 10500
    for i, ((t, c, rows), h) in enumerate(zip(items, hs)):
        runs = f"<run bold='true' fontcolor='{c}' fontsize='17'>{esc(t)}</run>"
        for lab, txt in rows:
            runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='12'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='12'>{esc(txt)}</run>"
        zones += f"<zone h='{h}' id='{20+i}' type-v2='text' w='100000' x='0' y='{y}'><formatted-text>{runs}</formatted-text></zone>"
        y += h
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
dash_xml.insert(0, intro_dash("D0 Introduction", INTRO, "Introduction: purpose, scope and stakeholders"))
dash_xml.append(rec_dash("D10 Recommendations", PATHS, "Recommendations: the best route for each type of owner"))

ACTIONS = "".join(
    f"<action caption='Open source: {esc(d[0])}' name='[Action_url_{i}]'><activation auto-clear='true' type='on-select' />"
    f"<source dashboard='{esc(d[0])}' type='sheet' worksheet='Sources {esc(d[0][:2])}' />"
    f"<link caption='' delimiter=',' escape='\\' expression='&lt;url&gt;' include-null='true' multi-select='false' url-escape='false' /></action>"
    for i, d in enumerate(DASH))

# ---------------- story
points = "<story-point captured-sheet='D0 Introduction' caption='Start here: purpose, scope and who this is for.' id='1' />"
points += "".join(f"<story-point captured-sheet='{esc(n)}' caption='{esc(cap)}' id='{i+2}' />" for i, (n, s, note, hdr, cap) in enumerate(DASH))
points += f"<story-point captured-sheet='D10 Recommendations' caption='Recommendations: find your type and its best choice.' id='{len(DASH)+2}' />"
story = (f"<dashboard name='IP Distribution Decision Verticals' type='storyboard'><style /><size maxheight='964' maxwidth='1366' minheight='964' minwidth='1366' sizing-mode='fixed' />"
         f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"
         f"<zone h='98000' id='2' param='vert' removable='false' type-v2='layout-flow' w='98800' x='600' y='1000'>"
         f"<zone h='5000' id='3' type-v2='text' w='98800' x='600' y='1000'><formatted-text><run bold='true' fontsize='18'>IP Distribution Decision Verticals</run><run fontcolor='#52514e' fontsize='11'>   Prices, fees and rates as of {esc(ASOF)}; refreshed quarterly</run></formatted-text></zone>"
         f"<zone h='17000' id='4' is-fixed='true' paired-zone-id='5' removable='false' type-v2='flipboard-nav' w='98800' x='600' y='6000' />"
         f"<zone h='75000' id='5' paired-zone-id='4' removable='false' type-v2='flipboard' w='98800' x='600' y='23000'><flipboard active-id='1' nav-type='caption' show-nav-arrows='true'>"
         f"<story-points>{points}</story-points></flipboard></zone></zone></zone></zones>"
         f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

windows = "".join(f"<window class='worksheet' name='{esc(n)}'><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for n, _ in SHEETS)
windows += "".join(f"<window class='dashboard' name='{esc(d[0])}'><viewpoints>{''.join(f"<viewpoint name='{esc(x)}'><zoom type='entire-view' /></viewpoint>" for x in d[1] + ['Sources ' + d[0][:2]])}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for d in DASH)
windows += f"<window class='dashboard' name='D0 Introduction'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D10 Recommendations'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' maximized='true' name='IP Distribution Decision Verticals'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"

twb = ("<?xml version='1.0' encoding='utf-8' ?>\n"
       "<workbook original-version='18.1' source-build='2024.1.0 (20241.24.0312.0830)' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>"
       "<document-format-change-manifest><_.fcp.MarkAnimation.true...MarkAnimation /><_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy /><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>"
       "<preferences><preference name='ui.encoding.shelf.height' value='24' /><preference name='ui.shelf.height' value='26' /></preferences>"
       f"<datasources>{''.join(dsx)}</datasources>"
       f"<actions>{ACTIONS}</actions>"
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
    f.write("**Story point 1.** Start here: purpose, scope and who this is for.\n\n")
    for _t, _c, _rows in INTRO:
        f.write(f"*{_t}.* " + " ".join(f"{_l}: {_x}" for _l, _x in _rows) + "\n\n")
    for i, (n, s, note, hdr, cap) in enumerate(DASH, 2):
        f.write(f"**Story point {i}.** {cap}\n\n{note}\n\nSources: " + " | ".join(f"[{t}]({u})" for t, u in SRC_LINKS[n]) + "\n\n")
with open(OUT / "story_captions.md", "a") as f:
    f.write(f"**Story point {len(DASH)+2}.** Recommendations: find your type and its best choice.\n\n")
    for _t, _c, _rows in PATHS:
        f.write(f"*{_t}.* " + " ".join(f"{_l}: {_x}" for _l, _x in _rows) + "\n\n")
print("ok", len(twb))
