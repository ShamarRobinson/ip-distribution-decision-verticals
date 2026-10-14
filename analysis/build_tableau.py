"""Build a Tableau packaged workbook (.twbx) with sheets, annotated dashboards and a captioned Story."""
import csv, uuid, zipfile, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import json
ASOF = json.load(open(ROOT / "as_of.json"))["as_of_label"]
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import methods as MT
KPIS, MPAGES = MT.build()
CALC = {r["dash"]: r for r in MPAGES}
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
             "test": {"Price elasticity: $16.99 (A, control) vs $14.99 (B)": "Print price: $16.99 vs $14.99",
                      "Channel terms: 55% discount, returnable (A) vs 40% non-returnable (B)": "Store terms: 55% returnable vs 40% non-returnable",
                      "Ebook price: $4.99 (A, control) vs $3.99 (B)": "Ebook price: $4.99 vs $3.99"},
             "channel": {"Amazon KDP (print + ebook)": "Amazon KDP", "IngramSpark (print)": "IngramSpark (print)", "Draft2Digital (ebook)": "Draft2Digital (ebook)"}}
    for fld, amap in ALIAS.items():
        tag = f"<column datatype='string' name='[{fld}]' role='dimension' type='nominal' />"
        if tag in fields:
            al = "".join(f"<alias key='&quot;{esc(k)}&quot;' value='{esc(v)}' />" for k, v in amap.items())
            fields = fields.replace(tag, f"<column datatype='string' name='[{fld}]' role='dimension' type='nominal'><aliases>{al}</aliases></column>")
    CAP = {"component": "Where the $16.99 goes", "driver": "Cause of the gap vs KDP", "segment": "Who published", "channel": "Royalties earned through", "sales_level": "Sales level",
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
HL = "#c2410c"
def sheet(name, title, key, rows, cols, mark, color=None, label=None, filt=None, sort=None, subtitle="", lines=(), bands=(), notes=(), no_zero=None, axis_title=None):
    """lines: (axis_ref, value, label); bands: (axis_ref, from, to, label, fill); notes: (dim_value, measure_value, text, dx, dy).
    axis_ref is a (field, kind) spec such as ("net_royalty", "sum") or ("month", "qk"). Notes work on single-dimension bar sheets."""
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
    rid = [0]; rl_xml = ""; band_rules = ""
    def axref(spec):
        f, kind = spec; r, x = ci(key, f, kind); used[r] = x; return f"[{ds}].{esc(r)}"
    def one_line(spec, val, lab, extra="", z=3):
        a = axref(spec); i = f"refline{rid[0]}"; rid[0] += 1
        lt = f"label='{esc(lab)}' label-type='custom'" if lab else "label-type='none'"
        return i, (f"<reference-line axis-column='{a}' enable-instant-analytics='true' formula='constant' id='{i}' {lt} "
                   f"scope='per-table' {extra}value='{val if val != 0 else 0.001}' value-column='{a}' z-order='{z}' />")
    for spec, v0, v1, lab, fill in bands:
        a_id, b_id = f"refline{rid[0]}", f"refline{rid[0]+1}"
        _, x0 = one_line(spec, v0, lab, f"paired-id='{b_id}' symmetric='false' ", z=1)
        _, x1 = one_line(spec, v1, "", f"paired-id='{a_id}' symmetric='false' ", z=1)
        rl_xml += x0 + x1
        band_rules += f"<format attr='fill-color' id='{a_id}' value='{fill}' />"
    for k, (spec, val, lab) in enumerate(lines):
        _, x = one_line(spec, val, lab, z=3 + k); rl_xml += x
    extra_rules = ""
    if band_rules:
        extra_rules += f"<style-rule element='refband'>{band_rules}</style-rule>"
    if no_zero:
        f0, k0, sc = no_zero; r0, _ = ci(key, f0, k0)
        extra_rules += (f"<style-rule element='axis'><encoding attr='space' class='0' domain-expand='false' field='[{ds}].{esc(r0)}' "
                        f"field-type='quantitative' scope='{sc}' type='space' /></style-rule>")
    if extra_rules:
        tstyle = tstyle.replace("<style />", f"<style>{extra_rules}</style>") if tstyle == "<style />" else tstyle.replace("</style>", f"{extra_rules}</style>")
    ann = ""
    if notes:
        dimf, measf = rows[0][0], cols[0][0]
        dref, mref = f"[{ds}].[none:{esc(dimf)}:nk]", f"[{ds}].[sum:{esc(measf)}:qk]"
        for k, (dv, mv, txt, dx, dy) in enumerate(notes):
            ann += (f"<annotation class='point' id='{k}' mark-position='1' pullback='12' text-width='190'>"
                    f"<formatted-text><run bold='true' fontcolor='{HL}'>{esc(txt)}</run></formatted-text>"
                    f"<point><visual-coordinate class='mark'><tuple-reference><tuple-descriptor><pane-descriptor>"
                    f"<x-fields><field>{mref}</field></x-fields><y-fields><field>{dref}</field></y-fields></pane-descriptor>"
                    f"<columns><field>{dref}</field><field>{mref}</field></columns></tuple-descriptor>"
                    f"<tuple><value>&quot;{esc(dv)}&quot;</value><value>{mv}</value></tuple></tuple-reference></visual-coordinate></point>"
                    f"<body x='{dx}' y='{dy}' /></annotation>")
        ann = f"<annotations>{ann}</annotations>"
    lbl_style = "<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' />" + ("<format attr='mark-markers-mode' value='all' />" if mark == 'Line' else "") + "</style-rule></style>" if label else ("<style><style-rule element='mark'><format attr='mark-markers-mode' value='all' /></style-rule></style>" if mark == 'Line' else "")
    sub = f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(subtitle)}</run>" if subtitle else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontsize='14'>{esc(title)}</run>{sub}</formatted-text></title></layout-options>"
         f"<table><view><datasources><datasource caption='{esc(DS[key]['caption'])}' name='{ds}' /></datasources>"
         f"<datasource-dependencies datasource='{ds}'>{deps}{''.join(used.values())}</datasource-dependencies>"
         f"{filt_xml}{sort_xml}<aggregation value='true' /></view>{tstyle}"
         f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
         f"<mark class='{mark}' /><encodings>{enc}</encodings>{rl_xml}{lbl_style}</pane></panes>"
         f"<rows>{rref}</rows><cols>{cref}</cols>{ann}</table><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></worksheet>")
    SHEETS.append((name, x))

SRC_LINKS = {'D1 Market': [('Bowker via Publishers Weekly', 'https://www.publishersweekly.com/pw/print/20260323/99943-book-output-topped-4-million-in-2025.html'), ('Circana BookScan via Publishers Weekly', 'https://www.publishersweekly.com/pw/by-topic/industry-news/bookselling/article/99417-print-book-sales-rose-slightly-in-2025.html')], 'D2 Gross to Net': [('IngramSpark 2026 pricing', 'https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('B&N Press royalties', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales'), ('Lulu pricing', 'https://blog.chapter.pub/lulu-pricing/')], 'D3 Cost Variance': [('IngramSpark 2026 pricing', 'https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator')], 'D4 Ebook': [('ScribeCount platform comparison', 'https://scribecount.com/tools/platform-comparison'), ('PublishDrive vs Draft2Digital', 'https://publishdrive.com/comparison-guide-publishdrive-vs-draft2digital.html'), ('IngramSpark', 'https://www.ingramspark.com/')], 'D5 Breakeven': [('USCO 2026 fee schedule (Hypebot)', 'https://www.hypebot.com/2-months-left-before-u-s-copyright-fees-jump-dramatically/'), ('ISBN pricing (ScribeCount)', 'https://scribecount.com/author-resource/publishing-a-book/How-to-Publish-on-IngramSpark'), ('PublishDrive plans', 'https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans')], 'D6 Scenarios': [('PublishDrive plans', 'https://help.publishdrive.com/how-much-publishdrives-distribution-pricing-plans'), ('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('B&N Press royalties', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales')], 'D7 Cash': [('B&N Press payments', 'https://help-press.barnesandnoble.com/hc/en-us/articles/5359658688923-Getting-Paid-for-Sales'), ('IngramSpark', 'https://www.ingramspark.com/'), ('Written Word Media 2025 survey', 'https://www.writtenwordmedia.com/2025-indie-author-survey-results/')], 'D8 Pool Volatility': [('Profitable.app KENP tracker', 'https://profitable.app/kdp/stats/kenp-rate'), ('Written Word Media 2025 survey', 'https://www.writtenwordmedia.com/2025-indie-author-survey-results/')], 'D9 AB Test': [('KDP royalty calculator', 'https://profitable.app/tools/kdp-royalty-calculator'), ('Model and method on GitHub', 'https://github.com/ShamarRobinson/ip-distribution-decision-verticals')]}
# ---------------- sources table for named, clickable links
import csv as _csv
with open(ROOT / "data" / "story_sources.csv", "w", newline="") as _f:
    _w = _csv.writer(_f); _w.writerow(["dashboard", "n", "source", "url", "as_of"])
    for _d, _lst in SRC_LINKS.items():
        for _i, (_t, _u) in enumerate(_lst, 1):
            _w.writerow([_d, _i, _t, _u, json.load(open(ROOT / "as_of.json"))["as_of"]])

# ---------------- derived chart tables: simplified labels and friendlier units
def _derive(src, dst, fn, extra):
    rows = list(csv.DictReader(open(ROOT / "data" / src)))
    with open(ROOT / "data" / dst, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) + extra); w.writeheader()
        for r in rows: w.writerow({**r, **fn(r)})
_derive("price_waterfall_long.csv", "chart_gross_to_net.csv",
        lambda r: {"keep_label": r["amount"] if r["component"] == "Net royalty to IP owner" else ""}, ["keep_label"])
_derive("cost_variance_drivers.csv", "chart_cost_variance.csv",
        lambda r: {"store_cut_label": r["variance"] if r["driver"] == "Channel share" and float(r["variance"]) != 0 else ""}, ["store_cut_label"])
_SCN = {"Bear": "1. Slow (10 a month)", "Base": "2. Normal (50 a month)", "Bull": "3. Great (250 a month)"}
_derive("scenario_analysis.csv", "chart_scenarios.csv", lambda r: {"sales_level": _SCN[r["scenario"]]}, ["sales_level"])
_derive("kenp_pool_rate.csv", "chart_kenp_per_1000.csv",
        lambda r: {"pay_per_1000_pages": f"{float(r['per_page_rate']) * 1000:.2f}"}, ["pay_per_1000_pages"])

# ---------------- data sources
dsx = [
 datasource("isbn", "market_bowker_isbn.csv", "segment"),
 datasource("gtn", "chart_gross_to_net.csv", "component"),
 datasource("var", "chart_cost_variance.csv", "driver"),
 datasource("ebook", "ebook_unit_economics.csv", "platform"),
 datasource("be", "breakeven.csv", "stack"),
 datasource("curve", "breakeven_curve.csv", "stack"),
 datasource("scen", "chart_scenarios.csv", "stack"),
 datasource("cash", "hybrid_stack_24mo.csv", "channel"),
 datasource("kenp", "chart_kenp_per_1000.csv"),
 datasource("ab", "ab_test_design.csv"),
 datasource("pay", "payout_timing.csv", "platform"),
 datasource("src", "story_sources.csv"),
]

# ---------------- worksheets
# ---------------- in-graph highlights (all computed from the data files)
_r = lambda k: DS[k]["rows"]
_iso = {(int(r["year"]), r["segment"]): int(r["titles"]) for r in _r("isbn")}
_yrs = sorted({y for y, _ in _iso}); _y0, _y1 = _yrs[-2], _yrs[-1]
SP_GROWTH = _iso[(_y1, "Self-published")] / _iso[(_y0, "Self-published")] - 1
_eb = {r["platform"]: r for r in _r("ebook")}
KDP_NET = next(float(r["amount"]) for r in _r("gtn") if r["platform"] == "Amazon KDP" and r["format"] == "Print" and r["component"] == "Net royalty to IP owner")
EB_TOP = max(float(r["net_royalty"]) for r in _r("ebook"))
EB_AGG = ("Draft2Digital", "IngramSpark")
EB_LO = min(float(_eb[p]["net_royalty"]) for p in EB_AGG); EB_HI = max(float(_eb[p]["net_royalty"]) for p in EB_AGG)
_be = sorted(_r("be"), key=lambda r: int(r["breakeven_unit_pairs"]))
BE_MIN, BE_MAX = _be[0], _be[-1]
_cash = _r("cash")
CASH_GAP12 = sum(float(r["cumulative_earned"]) - float(r["cumulative_cash"]) for r in _cash if int(r["month"]) == 12)
_pay = sorted(_r("pay"), key=lambda r: int(r["avg_days_sale_to_cash"]))
_kp = [float(r["per_page_rate"]) for r in _r("kenp")]
import datetime as _dt
_mname = lambda m: _dt.date(int(m[:4]), int(m[5:7]), 1).strftime("%b %Y")
_kp_hi = _mname(_r("kenp")[_kp.index(max(_kp))]["month"]); _kp_lo = _mname(_r("kenp")[_kp.index(min(_kp))]["month"])
_ab = _r("ab"); _ab_price = [r for r in _ab if r["test"].startswith(("Price", "Ebook"))]
_ab_hard = max(_ab, key=lambda r: float(r["breakeven_lift_required"]))
BAND = "#fff1de"

sheet("01 Market ISBNs", "U.S. ISBN output by segment, 2022 to 2025 (stacked)", "isbn", [("titles","sum")], [("year","qk")], "Area", color=("segment","nk"),
      subtitle="Source: Bowker via Publishers Weekly, March 2026",
      bands=[(("year", "qk"), _y0, _y1, f"Self-published +{SP_GROWTH:.1%} in {_y1}", BAND)])
sheet("02 Gross to Net", "Where each $16.99 of list price goes (print)", "gtn", [("platform","nk")], [("amount","sum")], "Bar", color=("component","nk"), label=("keep_label","sum"), filt=("format","Print"),
      subtitle="Model in this repository; platform rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive",
      lines=[(("amount", "sum"), round(KDP_NET, 3), f"KDP keeps ${KDP_NET:.2f}")])
sheet("03 Cost Variance", "Cost variance vs Amazon KDP by driver, $ per print unit", "var", [("platform","nk")], [("variance","sum")], "Bar", color=("driver","nk"), label=("store_cut_label","sum"), filt=("format","Print"),
      subtitle="Positive = favorable to the IP owner. Drivers sum to the total variance.",
      lines=[(("variance", "sum"), 0, "KDP baseline")])
sheet("04 Ebook Net", "Net royalty per $4.99 ebook", "ebook", [("platform","nk")], [("net_royalty","sum")], "Bar", color=("platform","nk"), label=("net_royalty","sum"), sort=("platform","net_royalty"),
      subtitle="Store payout rates from ScribeCount; fees from KDP, Draft2Digital and the IngramSpark agreement",
      lines=[(("net_royalty", "sum"), EB_TOP, f"Best possible: ${EB_TOP:.2f} (70%)")],
      bands=[(("net_royalty", "sum"), EB_LO, EB_TOP, "", BAND)],
      notes=[("IngramSpark", _eb["IngramSpark"]["net_royalty"], f"Middlemen cost {round((EB_TOP-EB_HI)*100)} to {round((EB_TOP-EB_LO)*100)} cents a sale", -170, 40)])
sheet("05 Breakeven Units", "Unit pairs needed to recover Year-1 fixed costs", "be", [("stack","nk")], [("breakeven_unit_pairs","sum")], "Bar", color=("stack","nk"), label=("breakeven_unit_pairs","sum"),
      subtitle="Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions",
      lines=[(("breakeven_unit_pairs", "sum"), int(BE_MIN["breakeven_unit_pairs"]), f"Fastest: {BE_MIN['stack']} at {BE_MIN['breakeven_unit_pairs']} pairs")],
      notes=[(BE_MAX["stack"], BE_MAX["breakeven_unit_pairs"], f"{int(BE_MAX['breakeven_unit_pairs'])/int(BE_MIN['breakeven_unit_pairs']):.1f}x as many sales as the fastest route", -30, 42)])
sheet("06 Breakeven Curve", "Cumulative profit by unit pairs sold", "curve", [("cumulative_profit","sum")], [("unit_pairs","qk")], "Line", color=("stack","nk"),
      subtitle="Each line crosses zero at its breakeven point",
      lines=[(("cumulative_profit", "sum"), 0, "Breakeven ($0)")],
      bands=[(("unit_pairs", "qk"), int(BE_MIN["breakeven_unit_pairs"]), int(BE_MAX["breakeven_unit_pairs"]), f"Breakeven range: {BE_MIN['breakeven_unit_pairs']} to {BE_MAX['breakeven_unit_pairs']} pairs", BAND)])
sheet("07 Scenarios", "Year-1 net by sales level (10, 50 and 250 sales of each format a month)", "scen", [("stack","nk")], [("sales_level","nk"), ("year1_net","sum")], "Bar", color=("stack","nk"), label=("year1_net","sum"),
      subtitle="Planning scenarios, not forecasts")
sheet("08 Accrual vs Cash", "Cumulative royalties earned by channel (stacked), 24 months", "cash", [("cumulative_earned","sum")], [("month","qk")], "Area", color=("channel","nk"),
      subtitle="Illustrative hybrid stack; launch curve and 65/35 channel mix are assumptions",
      lines=[(("month", "qk"), 12, f"Month 12: ${CASH_GAP12:,.0f} not yet paid")])
sheet("09 Days to Cash", "Average days from sale to cash", "pay", [("platform","nk")], [("avg_days_sale_to_cash","sum")], "Bar", color=("platform","nk"), label=("avg_days_sale_to_cash","sum"),
      subtitle="B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by",
      bands=[(("avg_days_sale_to_cash", "sum"), int(_pay[0]["avg_days_sale_to_cash"]), int(_pay[-1]["avg_days_sale_to_cash"]),
              f"{int(_pay[-1]['avg_days_sale_to_cash']) - int(_pay[0]['avg_days_sale_to_cash'])}-day gap", BAND)])
sheet("10 KENP Pool Rate", "Kindle Unlimited pay per 1,000 pages read", "kenp", [("pay_per_1000_pages","sum")], [("month","ok")], "Line",
      subtitle="Profitable.app KENP tracker (author-reported), May 2025 to April 2026",
      lines=[(("pay_per_1000_pages", "sum"), round(max(_kp) * 1000, 2), f"High: ${max(_kp)*1000:.2f} ({_kp_hi})"),
             (("pay_per_1000_pages", "sum"), round(sum(_kp) / len(_kp) * 1000, 2), f"Average: ${sum(_kp)/len(_kp)*1000:.2f}"),
             (("pay_per_1000_pages", "sum"), round(min(_kp) * 1000, 2), f"Low: ${min(_kp)*1000:.2f} ({_kp_lo})")],
      no_zero=("pay_per_1000_pages", "sum", "rows"))
sheet("11 AB Breakeven Lift", "Volume lift a challenger needs to match the control", "ab", [("test","nk")], [("breakeven_lift_required","sum")], "Bar", label=("breakeven_lift_required","sum"),
      subtitle="Two-proportion z-test sizing at alpha 0.05 and power 0.80",
      bands=[(("breakeven_lift_required", "sum"), min(float(r["breakeven_lift_required"]) for r in _ab_price), max(float(r["breakeven_lift_required"]) for r in _ab_price),
              f"Price cuts need {min(float(r['breakeven_lift_required']) for r in _ab_price):.0%} to {max(float(r['breakeven_lift_required']) for r in _ab_price):.0%} more sales", BAND)],
      notes=[(_ab_hard["test"], _ab_hard["breakeven_lift_required"], "Hardest bar to clear: returns eat the margin", -80, -40)])

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
    chart_h = 56000
    w_each = 100000 // n
    inner = ""
    for i, s in enumerate(sheets):
        if s in SHEET_COLOR:
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each-15000}' x='{i*w_each}' y='8000' />"
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' pane-specification-id='0' param='{SHEET_COLOR[s]}' type-v2='color' w='15000' x='{i*w_each + w_each - 15000}' y='8000' />"
        else:
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each}' x='{i*w_each}' y='8000' />"
    hdr = f"<zone h='8000' id='{nid()}' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontcolor='#0b0b0b' fontsize='18'>{esc(header)}</run></formatted-text></zone>"
    ctype, tech, plain, terms = GUIDE[name]
    term_runs = "".join(f"<run bold='true' fontcolor='#1f1f1f' fontsize='10'>{'&#10;Terms: ' if k == 0 else '; '}{esc(a)} ({esc(full)}): </run>"
                        f"<run fontcolor='#1f1f1f' fontsize='10'>{esc(desc)}</run>" for k, (a, full, desc) in enumerate(terms))
    ann = (f"<zone h='36000' id='{nid()}' type-v2='text' w='64000' x='0' y='64000'><formatted-text>"
           f"<run bold='true' fontcolor='#0b0b0b' fontsize='10'>As of {esc(ASOF)}: </run>"
           f"<run fontcolor='#1f1f1f' fontsize='10'>{esc(note)}</run>"
           f"<run bold='true' fontcolor='#52514e' fontsize='10'>&#10;Chart type: </run><run fontcolor='#52514e' fontsize='10'>{esc(ctype)}. </run>"
           f"<run bold='true' fontcolor='#52514e' fontsize='10'>For analysts: </run><run fontcolor='#52514e' fontsize='10'>{esc(tech[0].upper() + tech[1:])} </run>"
           f"<run bold='true' fontcolor='#52514e' fontsize='10'>In plain terms: </run><run fontcolor='#52514e' fontsize='10'>{esc(plain)}</run>"
           f"<run bold='true' fontcolor='#c2410c' fontsize='10'>&#10;How it is calculated: </run><run fontcolor='#1f1f1f' fontsize='10'>{esc(CALC[name]['calc'])}</run>"
           f"{term_runs}</formatted-text></zone>"
           f"<zone h='36000' id='{nid()}' name='Sources {esc(name[:2])}' show-title='true' w='36000' x='64000' y='64000' />")
    return (f"<dashboard name='{esc(name)}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{hdr}{''.join(f for f in [inner])}{ann}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

# ---------------- chart guide per dashboard: chart type, analyst reading, plain reading, terms
T_KDP = ("KDP", "Kindle Direct Publishing", "Amazon's self-publishing service for print books and ebooks")
T_BN = ("B&N", "Barnes & Noble", "the U.S. bookstore chain; B&N Press is its self-publishing service")
T_ISBN = ("ISBN", "International Standard Book Number", "the ID code every book edition gets")
T_DSO = ("DSO", "days sales outstanding", "the average number of days between a sale and the cash arriving")
T_KENP = ("KENP", "Kindle Edition Normalized Pages", "Amazon's standard page count used to pay authors when Kindle Unlimited readers read their books")
T_AB = ("A/B test", "a test of version A against version B", "real shoppers see one of two options, then you compare which earns more")
T_IP = ("IP", "intellectual property", "a creative work you own, such as a book, guide or course")
GUIDE = {
 "D1 Market": ("Stacked area chart", "x is the year, y is ISBNs issued; layers stack, so the top edge is the total and each layer is one segment.",
               "The colored layers pile up: the top edge is all new books, the blue layer is books authors published themselves.", [T_ISBN]),
 "D2 Gross to Net": ("Stacked horizontal bar chart (a gross-to-net breakdown)", "each bar splits the $16.99 list price into store share, printing, platform fees and net royalty; the line marks KDP's net.",
               "Each bar is one book's price cut into slices for who gets paid; the teal slice and its number is what you keep.", [T_KDP, T_BN]),
 "D3 Cost Variance": ("Diverging stacked bar chart (a variance bridge against a baseline)", "dollars per copy versus the KDP baseline, split by driver; left of the line is unfavorable.",
               "Bars that reach left mean you keep less than on Amazon; colors show why, and the red number is the store's cut.", [T_KDP, T_BN]),
 "D4 Ebook": ("Sorted horizontal bar chart with a reference line and shaded band", "net royalty per $4.99 ebook; the line is the 70% royalty ceiling and the band is the aggregator gap.",
               "Longer bars keep more money; the shaded strip shows what middlemen take from each sale.", [T_KDP, T_BN]),
 "D5 Breakeven": ("Sorted horizontal bar chart with a reference line", "breakeven unit pairs = Year-1 fixed costs divided by contribution per print-plus-ebook pair.",
               "Shorter bars mean you earn back your start-up money sooner; the line marks the fastest route.", [T_KDP, T_BN]),
 "D6 Scenarios": ("Grouped bar chart in three panels (small multiples)", "Year-1 net by platform at 10, 50 and 250 sales per format per month; the same rank order in every panel shows a robust choice.",
               "Three side-by-side charts for slow, normal and great sales; the longest bar wins in all three.", [T_KDP, T_BN]),
 "D7 Cash": ("Stacked area chart and horizontal bar chart with a shaded range", "left: cumulative accrued royalties by channel with a month-12 marker; right: average DSO by platform.",
               "Left: money earned piles up, but it arrives months later. Right: how long each store takes to pay you.", [T_DSO, T_KDP, T_BN]),
 "D8 Pool Volatility": ("Line chart with reference lines", "monthly KENP rate shown as dollars per 1,000 pages; the axis starts near the lowest value so changes are visible.",
               "The line shows what Kindle Unlimited paid each month; the three flat lines mark the best month, the average and the worst month.", [T_KENP, T_KDP]),
 "D9 AB Test": ("Horizontal bar chart with a shaded range", "breakeven lift = net per unit of A divided by net per unit of B, minus 1; sample sizes use a two-proportion z-test at 95% confidence and 80% power.",
               "Each bar is how many more sales a cheaper option needs just to tie; beat the bar or keep the original.", [T_AB]),
}
DASH = [
 ("D1 Market", ["01 Market ISBNs"], "Every book edition gets an ID number called an ISBN, so counting ISBNs shows how many new books come out. Self-published titles (blue area) jumped 38.7% in 2025 while printed-book sales rose only 0.3%. More books are competing for the same buyers, which makes the share of each sale you keep more important.", "Market context: more works are competing for the same buyers",
  "Self-published ISBNs rose 38.7% in 2025."),
 ("D2 Gross to Net", ["02 Gross to Net"], "Each bar is one $16.99 book split by who gets paid. Red is the store's cut, orange is printing, blue is platform fees, and teal is what the creator keeps. KDP leaves the creator $6.79, while IngramSpark's bookstore route leaves $3.33. Finance teams call this breakdown gross-to-net.", "Gross-to-net: where each $16.99 goes",
  "KDP nets $6.79 per paperback; IngramSpark nets $3.33."),
 ("D3 Cost Variance", ["03 Cost Variance"], "This is a cost variance analysis: every option is compared with Amazon KDP. Bars left of zero mean you keep less per book than on KDP, and each color is one cause (red = store's cut, orange = printing, blue = platform fees). For IngramSpark, the store's cut explains $2.55 of the $3.47 gap.", "Cost variance analysis vs the KDP baseline",
  "Retailer discounts drive most of the cost variance."),
 ("D4 Ebook", ["04 Ebook Net"], "For a $4.99 ebook, each bar shows what the creator keeps after the store and any middleman are paid. Selling directly to Apple or B&N keeps $3.49. Aggregators like Draft2Digital keep 35 to 52 cents more per sale in exchange for sending your book to many stores with one upload.", "Ebook economics: direct uploads beat aggregators",
  "Direct ebook uploads keep the most per sale."),
 ("D5 Breakeven", ["05 Breakeven Units"], "Breakeven is the number of sales needed to earn back what you spent to launch: the copyright fee, platform fees and a production budget. KDP gets there after 158 sales of a print book plus an ebook, and IngramSpark after 272.", "Breakeven analysis",
  "KDP breaks even at 158 unit pairs; IngramSpark at 272."),
 ("D6 Scenarios", ["07 Scenarios"], "Scenario analysis asks 'what if?' at three sales levels: slow (10 a month), normal (50) and great (250). KDP finishes first in every case, so the decision holds up even if the sales forecast is off. A flat monthly fee (PublishDrive) only beats a per-sale fee once you sell about 17 of each format a month.", "Scenario analysis: the ranking is stable across volumes",
  "Subscriptions win only above 16.6 units a month."),
 ("D7 Cash", ["08 Accrual vs Cash", "09 Days to Cash"], "The stacked areas show royalties earned over 24 months. Stores pay two to three months after a sale, so at month 12 about $948 has been earned but not yet received. The bars show days sales outstanding (DSO): B&N Press pays in about 45 days, IngramSpark in about 105, so longer waits require more cash on hand.", "Accrual vs cash and days sales outstanding",
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
    zones = (f"<zone h='14000' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='11'>&#10;Find your type, then read its best choice. As of {esc(ASOF)}. Decision trees for each path are in the slide deck linked from the GitHub page.</run>"
             f"<run fontcolor='#52514e' fontsize='10'>&#10;Terms: KDP (Kindle Direct Publishing): Amazon's self-publishing service; KDP Select: Amazon's 90-day ebook exclusivity program; B&amp;N (Barnes &amp; Noble): the bookstore chain behind B&amp;N Press; IP (intellectual property): the creative work you own.</run></formatted-text></zone>")
    cols = [items[:3], items[3:]]
    zid = 20
    for ci_, col in enumerate(cols):
        h = (100000 - 14500) // 3
        for ri, (t, c, rows) in enumerate(col):
            runs = f"<run bold='true' fontcolor='{c}' fontsize='14'>{esc(t)}</run>"
            for lab, txt in rows:
                runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='10'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='10'>{esc(txt)}</run>"
            zones += f"<zone h='{h}' id='{zid}' type-v2='text' w='49000' x='{ci_*51000}' y='{14500 + ri*h}'><formatted-text>{runs}</formatted-text></zone>"
            zid += 1
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
INTRO = [
 ("Purpose", "#2a78d6", [
  ("The question", "Where should you sell a creative work, such as a book, guide or course, so you keep the most money from each sale, with risk and payment timing you can live with?"),
  ("What you get", "Each story point compares the same six platforms using their published prices, fees and payout rates, explains the result in plain language, and names its sources. Points 2 and 3 define each KPI (key performance indicator) with its formula, point 13 gives a recommendation for each type of owner, and point 14 shows where every number comes from.")]),
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
 ("Key terms", "#6250d6", [(f"{a} ({full})", desc) for a, full, desc in (T_KDP, T_BN, T_IP, T_ISBN)]),
]
def intro_dash(dname, items, heading):
    zones = (f"<zone h='10000' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='11'>&#10;Prices, fees and rates as of {esc(ASOF)}. Use the arrows or the cards above to move through the story.</run></formatted-text></zone>")
    hs = [18000, 25000, 26000, 20500]
    y = 10500
    for i, ((t, c, rows), h) in enumerate(zip(items, hs)):
        runs = f"<run bold='true' fontcolor='{c}' fontsize='17'>{esc(t)}</run>"
        for lab, txt in rows:
            runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='11'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='11'>{esc(txt)}</run>"
        zones += f"<zone h='{h}' id='{20+i}' type-v2='text' w='100000' x='0' y='{y}'><formatted-text>{runs}</formatted-text></zone>"
        y += h
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
dash_xml.insert(0, intro_dash("D0 Introduction", INTRO, "Introduction: purpose, scope and stakeholders"))

def text_page(dname, heading, sub, items, cols=2, top=10000):
    """items: list of (title, [(label, text), ...]) laid out in columns."""
    zones = (f"<zone h='{top}' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(sub)}</run></formatted-text></zone>")
    per = math.ceil(len(items) / cols); h = (100000 - top - 500) // per; zid = 20
    for c in range(cols):
        for r, (t, rows) in enumerate(items[c*per:(c+1)*per]):
            runs = f"<run bold='true' fontcolor='#2a78d6' fontsize='11'>{esc(t)}</run>"
            for lab, txt in rows:
                runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='9'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='9'>{esc(txt)}</run>"
            zones += f"<zone h='{h}' id='{zid}' type-v2='text' w='{100000//cols - 1000}' x='{c*(100000//cols)}' y='{top + 500 + r*h}'><formatted-text>{runs}</formatted-text></zone>"
            zid += 1
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
import math
KPI_ITEMS = [(f"{r['kpi']} ({r['full']})", [("What it tells you", r["meaning"]), ("Formula", r["formula"]), ("Example", r["worked"])]) for r in KPIS]
dash_xml.insert(1, text_page("D0 KPIs", "KPI (key performance indicator) definitions, part 1: money kept per sale",
    f"Each formula is worked with the {ASOF} numbers. {MT.ROUNDING}", KPI_ITEMS[:7]))
dash_xml.insert(2, text_page("D0 KPIs 2", "KPI definitions, part 2: scale, cash timing and testing",
    f"Each formula is worked with the {ASOF} numbers. {MT.ROUNDING}", KPI_ITEMS[7:]))
SRC_ITEMS = [(f"{n}. {r['page']}", [("Numbers shown", r["numbers"]), ("Sources", "; ".join(MT.SOURCES[k][0] for k in r["sources"]))]) for n, r in enumerate(MPAGES, MT.FIRST_PAGE)]
SRC_ITEMS.append(("How the model works", [("Pipeline", "analysis/model.py turns one documented list of prices, fees and rates into every data file; the charts, deck, Excel model and this story all read those files."),
    ("Estimates", "Print costs for IngramSpark, B&N Press and Lulu, the $1,500 launch budget, the 65/35 channel mix and the launch curve are planning assumptions, not published rates."),
    ("Clickable sources", "Each analysis page lists its sources by name; click a name to open it. The GitHub page lists every formula in its How the numbers work section.")]))
dash_xml.append(rec_dash("D10 Recommendations", PATHS, "Recommendations: the best route for each type of owner"))
dash_xml.append(text_page("D11 Number Sources", "Where the numbers come from",
    f"Prices, fees and rates as of {ASOF}; refreshed quarterly. Each analysis page also shows its calculation under How it is calculated.", SRC_ITEMS))

ACTIONS = "".join(
    f"<action caption='Open source: {esc(d[0])}' name='[Action_url_{i}]'><activation auto-clear='true' type='on-select' />"
    f"<source dashboard='{esc(d[0])}' type='sheet' worksheet='Sources {esc(d[0][:2])}' />"
    f"<link caption='' delimiter=',' escape='\\' expression='&lt;url&gt;' include-null='true' multi-select='false' url-escape='false' /></action>"
    for i, d in enumerate(DASH))

# ---------------- story
points = "<story-point captured-sheet='D0 Introduction' caption='1. Start here: purpose, scope and who this is for.' id='1' />"
points += "<story-point captured-sheet='D0 KPIs' caption='2. KPIs, part 1: money kept per sale and breakeven.' id='2' />"
points += "<story-point captured-sheet='D0 KPIs 2' caption='3. KPIs, part 2: scale, cash timing and testing.' id='3' />"
points += "".join(f"<story-point captured-sheet='{esc(n)}' caption='{i+MT.FIRST_PAGE}. {esc(cap)}' id='{i+MT.FIRST_PAGE}' />" for i, (n, s, note, hdr, cap) in enumerate(DASH))
points += f"<story-point captured-sheet='D10 Recommendations' caption='{len(DASH)+MT.FIRST_PAGE}. Recommendations: find your type and its best choice.' id='{len(DASH)+MT.FIRST_PAGE}' />"
points += f"<story-point captured-sheet='D11 Number Sources' caption='{len(DASH)+MT.FIRST_PAGE+1}. Where the numbers come from.' id='{len(DASH)+MT.FIRST_PAGE+1}' />"
story = (f"<dashboard name='IP Distribution Decision Verticals' type='storyboard'><style /><size maxheight='1110' maxwidth='1366' minheight='1110' minwidth='1366' sizing-mode='fixed' />"
         f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"
         f"<zone h='98000' id='2' param='vert' removable='false' type-v2='layout-flow' w='98800' x='600' y='1000'>"
         f"<zone h='4000' id='3' type-v2='text' w='98800' x='600' y='800'><formatted-text><run bold='true' fontsize='18'>IP Distribution Decision Verticals</run><run fontcolor='#52514e' fontsize='11'>   Prices, fees and rates as of {esc(ASOF)}; refreshed quarterly</run></formatted-text></zone>"
         f"<zone h='13500' id='4' is-fixed='true' paired-zone-id='5' removable='false' type-v2='flipboard-nav' w='98800' x='600' y='4800' />"
         f"<zone h='81200' id='5' paired-zone-id='4' removable='false' type-v2='flipboard' w='98800' x='600' y='18300'><flipboard active-id='1' nav-type='caption' show-nav-arrows='true'>"
         f"<story-points>{points}</story-points></flipboard></zone></zone></zone></zones>"
         f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

windows = "".join(f"<window class='worksheet' name='{esc(n)}'><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for n, _ in SHEETS)
windows += "".join(f"<window class='dashboard' name='{esc(d[0])}'><viewpoints>{''.join(f"<viewpoint name='{esc(x)}'><zoom type='entire-view' /></viewpoint>" for x in d[1] + ['Sources ' + d[0][:2]])}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for d in DASH)
windows += f"<window class='dashboard' name='D0 Introduction'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D0 KPIs 2'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D0 KPIs'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D11 Number Sources'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
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
    f.write("**Story points 2 and 3.** KPI definitions with formulas and worked examples. See the How the numbers work section of the README.\n\n")
    for i, (n, s, note, hdr, cap) in enumerate(DASH, MT.FIRST_PAGE):
        f.write(f"**Story point {i}.** {cap}\n\n{note}\n\nHow it is calculated: {CALC[n]['calc']}\n\nSources: " + " | ".join(f"[{t}]({u})" for t, u in SRC_LINKS[n]) + "\n\n")
with open(OUT / "story_captions.md", "a") as f:
    f.write(f"**Story point {len(DASH)+MT.FIRST_PAGE}.** Recommendations: find your type and its best choice.\n\n")
    for _t, _c, _rows in PATHS:
        f.write(f"*{_t}.* " + " ".join(f"{_l}: {_x}" for _l, _x in _rows) + "\n\n")
with open(OUT / "story_captions.md", "a") as f:
    f.write(f"**Story point {len(DASH)+MT.FIRST_PAGE+1}.** Where the numbers come from. See the How the numbers work section of the README.\n")
print("ok", len(twb))
