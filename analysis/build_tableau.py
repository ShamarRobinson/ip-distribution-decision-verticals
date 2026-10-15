"""Build a Tableau packaged workbook (.twbx) with sheets, annotated dashboards and a captioned Story."""
import csv, uuid, zipfile, html
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import json
ASOF = json.load(open(ROOT / "as_of.json"))["as_of_label"]
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import methods as MT
from titlecase import tc
KPIS, MPAGES = MT.build()
CALC = {r["dash"]: r for r in MPAGES}
OUT = ROOT / "tableau"
esc = lambda s: html.escape(str(s), quote=True)
COL = {"Amazon KDP": "#2a78d6", "IngramSpark": "#eb6834", "B&N Press": "#1baf7a", "Lulu Retail": "#eda100", "Lulu Bookstore": "#c98500",
       "Lulu": "#eda100", "PublishDrive": "#e87ba4", "Draft2Digital": "#008300", "Draft2Digital (ebook only)": "#008300",
       "Apple Books direct": "#6250d6", "KDP Expanded Distribution": "#e34948",
       "Self-published": "#2a78d6", "Traditional": "#6250d6",
       "Channel share": "#e15759", "Production cost": "#f28e2b", "Platform fee": "#4e79a7", "Net royalty to IP owner": "#76b7b2",
       "Amazon KDP (print + ebook)": "#2a78d6", "IngramSpark (print)": "#eb6834", "Draft2Digital (ebook)": "#008300",
       "Bear": "#e34948", "Base": "#8a8984", "Bull": "#2a78d6"}

PALETTES = {}  # named workbook palettes; colors listed in the alphabetical order of the values they color
def make_palette(name, mapping):
    PALETTES[name] = [mapping[k] for k in sorted(mapping)]
    return name

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
             "segment": {"Self-published": "Self-published (by authors)", "Traditional": "Traditional (by publishers)"},
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
        pn = make_palette(f"IPDDV {key} {color_field}", {v: COL.get(v, "#8a8984") for v in vals})
        style = (f"<style><style-rule element='mark'><encoding attr='color' field='[none:{esc(color_field)}:nk]' palette='{esc(pn)}' type='palette'>{maps}</encoding>"
                 f"</style-rule></style>")
    # a datasource-level color map only binds when the colored field also has a column-instance here
    ci_xml = (f"<column-instance column='[{esc(color_field)}]' derivation='None' name='[none:{esc(color_field)}:nk]' pivot='key' type='nominal' />" if color_field else "")
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
            f"<aliases enabled='yes' />{fields}{ci_xml}{extract}<layout dim-ordering='alphabetic' dim-percentage='0.5' measure-ordering='alphabetic' measure-percentage='0.4' show-structure='true' />{style}</datasource>")

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
def sheet(name, title, key, rows, cols, mark, color=None, label=None, filt=None, sort=None, subtitle="", lines=(), bands=(), notes=(), no_zero=None, axis_title=None, independent=None, note_width=190, fixed=None, raw_ann=""):
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
        pn = make_palette(f"IPDDV {key} {cf}", {v: COL.get(v, "#8a8984") for v in vals})
        tstyle = f"<style><style-rule element='mark'><encoding attr='color' field='[{ds}].[none:{esc(cf)}:nk]' palette='{esc(pn)}' type='palette'>{maps}</encoding></style-rule></style>"
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
        axis_inner = (f"<encoding attr='space' class='0' domain-expand='false' field='[{ds}].{esc(r0)}' "
                        f"field-type='quantitative' scope='{sc}' type='space' />")
    else:
        axis_inner = ""
    if axis_title or independent:
        # axis_title: (field, kind, scope, text); independent: (field, kind, scope)
        ax_rules = ""
        if axis_title:
            fa, ka, sa, ta = axis_title; ra, _ = ci(key, fa, ka); ta = tc(ta)
            ax_rules += f"<format attr='title' class='0' field='[{ds}].{esc(ra)}' scope='{sa}' value='{esc(ta)}' />"
        if independent:
            fi, ki, si = independent; ri, _ = ci(key, fi, ki)
            ax_rules += (f"<encoding attr='space' class='0' field='[{ds}].{esc(ri)}' field-type='quantitative' "
                         f"range-type='independent' scope='{si}' type='space' />")
        axis_inner += ax_rules
    if fixed:
        # fixed: (field, kind, scope, min, max) trims the empty space at the ends of an axis
        ff, fk, fs, fmin, fmax = fixed; rf, _ = ci(key, ff, fk)
        axis_inner += (f"<encoding attr='space' class='0' field='[{ds}].{esc(rf)}' field-type='quantitative' max='{fmax}' min='{fmin}' "
                       f"range-type='fixed' scope='{fs}' type='space' />")
    if axis_inner:
        extra_rules += f"<style-rule element='axis'>{axis_inner}</style-rule>"
    if extra_rules:
        tstyle = tstyle.replace("<style />", f"<style>{extra_rules}</style>") if tstyle == "<style />" else tstyle.replace("</style>", f"{extra_rules}</style>")
    ann = ""
    if notes:
        if rows[0][1] in ("nk", "ok"):
            dimf, dk, measf = rows[0][0], rows[0][1], cols[0][0]
        else:
            dimf, dk, measf = cols[0][0], cols[0][1], rows[0][0]
        dref, mref = f"[{ds}].[none:{esc(dimf)}:{dk}]", f"[{ds}].[sum:{esc(measf)}:qk]"
        xf, yf = (mref, dref) if rows[0][1] in ("nk", "ok") else (dref, mref)
        for k, (dv, mv, txt, dx, dy) in enumerate(notes):
            ann += (f"<annotation class='point' id='{k}' mark-position='1' pullback='12' text-width='{note_width}'>"
                    f"<formatted-text><run bold='true' fontcolor='{HL}'>{esc(txt)}</run></formatted-text>"
                    f"<point><visual-coordinate class='mark'><tuple-reference><tuple-descriptor><pane-descriptor>"
                    f"<x-fields><field>{xf}</field></x-fields><y-fields><field>{yf}</field></y-fields></pane-descriptor>"
                    f"<columns><field>{dref}</field><field>{mref}</field></columns></tuple-descriptor>"
                    f"<tuple><value>&quot;{esc(dv)}&quot;</value><value>{mv}</value></tuple></tuple-reference></visual-coordinate></point>"
                    f"<body x='{dx}' y='{dy}' /></annotation>")
        ann = f"<annotations>{ann}</annotations>"
    if raw_ann:
        ann = f"<annotations>{raw_ann(ds)}</annotations>"
    lbl_style = "<style><style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='true' />" + ("<format attr='mark-markers-mode' value='all' />" if mark == 'Line' else "") + "</style-rule></style>" if label else ("<style><style-rule element='mark'><format attr='mark-markers-mode' value='all' /></style-rule></style>" if mark == 'Line' else "")
    sub = f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(subtitle)}</run>" if subtitle else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontsize='14'>{esc(tc(title))}</run>{sub}</formatted-text></title></layout-options>"
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

# ---------------- story infographics: grid diagrams (highlight-table style) for the text-only cards
TONE = {"blue": "#a9c8f0", "blue light": "#d6e6fa", "orange": "#f7c79b", "orange light": "#fbe2cc",
        "green": "#a8dcc1", "green light": "#d4eedf", "purple": "#c9c0f2", "purple light": "#e4dff9",
        "teal": "#a6dcd8", "teal light": "#d3eeec", "red": "#f2b1b0", "red light": "#f9d8d7",
        "gray": "#d0d4dc", "gray light": "#e8eaee", "pink": "#f3bdd3", "yellow": "#f6dc9a", "arrow": "#ffffff"}
COL.update(TONE)
def _kv(i, pat):
    m = re.search(pat, KPIS[i]["worked"]); return m.group(1) if m else ""
import re
_W = [k["worked"] for k in KPIS]
def _g(i, pat, default=""):
    m = re.search(pat, _W[i]); return m.group(1) if m else default
# (group tone, headline value, context line) per KPI, all pulled from the worked examples
_KPI_VAL = [
 ("blue", _g(0, r"= (\$[\d,]+(?:\.\d\d)?)\."), "KDP paperback; IngramSpark " + _g(0, r"IngramSpark:.*= (\$[\d,]+(?:\.\d\d)?)")),
 ("blue", _g(1, r"= ([\d.]+%)"), "KDP paperback; ebook " + _g(1, r"ebook:.*= ([\d.]+%)")),
 ("blue", "40%", "Amazon's cut; bookstores take 55%"),
 ("blue", _g(3, r"= (-\$[\d,]+(?:\.\d\d)?)"), "IngramSpark vs KDP, per copy"),
 ("orange", _g(4, r"KDP: .*?= (\$[\d,]+(?:\.\d\d)?)"), "KDP pair; IngramSpark " + _g(4, r"IngramSpark: .*?= (\$[\d,]+(?:\.\d\d)?)")),
 ("orange", _g(5, r"up to (\d+)\."), "KDP pairs; IngramSpark " + _g(5, r"up to (\d+)\.$")),
 ("orange", _g(6, r"= ([\d.]+%)"), "KDP at 600 planned pairs"),
 ("purple", _g(7, r"= ([\d.]+) sales"), "sales of each format a month"),
 ("purple", _g(8, r"= (\$[\d,]+)"), "KDP at 50 sales a month"),
 ("teal", "45 to 105", "days from sale to cash"),
 ("teal", _g(10, r"= (\$[\d,]+)"), "earned, not yet paid, month 12"),
 ("gray", _g(11, r"Average (\$[\d.]+)"), "average per 1,000 pages"),
 ("red", _g(12, r"= ([\d.]+%)\.?$"), "more sales for a $2 price cut"),
 ("red", _g(13, r"lift: ([\d,]+) shoppers"), "shoppers per test group")]
_short = {"Net royalty per copy": "Net royalty per copy", "Net margin %": "Net margin", "Channel share (store's cut)": "Store's cut",
          "Cost variance vs KDP": "Cost variance", "Contribution per unit pair": "Contribution per pair",
          "Breakeven point (unit pairs)": "Breakeven point", "Margin of safety": "Margin of safety", "Switch point (crossover)": "Switch point",
          "Year-1 net (scenarios)": "Year-1 net", "DSO": "Days to cash", "Working capital gap": "Working capital gap",
          "KENP rate": "Kindle Unlimited rate", "Breakeven lift": "Breakeven lift", "Sample size per group": "Test sample size"}
DIAG = []
def _cell(d, c, r, tone, title, l1="", l2=""):
    DIAG.append(dict(diagram=d, col=c, row=r, tone=tone, title=title, line1=l1 or " ", line2=l2 or " ", w=1))
for i, (tone, val, ctx) in enumerate(_KPI_VAL):
    d = "KPI strip 1" if i < 7 else "KPI strip 2"
    _cell(d, i % 7 + 1, 1, tone, f"KPI {i+1}  {_short.get(KPIS[i]['kpi'], KPIS[i]['kpi'])}", val, ctx)
_FLOW = [("yellow", "Point 1: start here (you are here)", "Purpose, scope and who this is for"),
         ("gray", "Point 2: the market", "More books chase the same buyers"),
         ("purple", "Points 3 and 4: the KPIs", "14 measures, each with a formula"),
         ("blue", "Points 5 to 7: money kept", "What each store leaves you per sale"),
         ("orange", "Points 8 and 9: breakeven", "When launch costs are earned back"),
         ("green", "Point 10: profit calculator", "Try your own sales and budget"),
         ("teal", "Points 11 and 12: getting paid", "Cash timing and Kindle Unlimited swings"),
         ("red", "Point 13: price testing", "The sales lift a price cut needs"),
         ("pink", "Points 14 and 15: check and decide", "Every source, then the best route per owner")]
for r, (tone, t, l1) in enumerate(_FLOW, 1):
    _cell("Launch flow", 1, r, tone, t, l1)
_TREE = [("Buyers come to you directly?", "Yes", "yellow", "D. Own store + KDP"),
         ("Ebooks are most of your income?", "Yes", "green", "E. KDP + direct ebooks"),
         ("Need bookstores or libraries?", "No", "blue", "A. Amazon KDP"),
         ("17+ sales of each format a month?", "No", "orange", "B. KDP + IngramSpark"),
         ("", "Yes", "pink", "C. KDP + PublishDrive")]
for r, (q, a, pt, path) in enumerate(_TREE, 1):
    if q: _cell("Decision tree", 1, r, "gray light", q)
    _cell("Decision tree", 2, r, "arrow", f"{a}  \u2192")
    _cell("Decision tree", 3, r, pt, path)
_PIPE = [("gray", "Published sources", "Rates, fees and payout terms", "as of each refresh"),
         ("purple", "One assumptions list", "Every input written down once", "estimates marked"),
         ("blue", "analysis/model.py", "Runs every calculation", "in one place"),
         ("teal", "Data files in /data", "One CSV per result", "dated as of the refresh"),
         ("green", "Charts, deck, Excel and this story", "All read the same files", "so numbers always agree")]
for k, (tone, t, l1, l2) in enumerate(_PIPE):
    _cell("Pipeline", k + 1, 1, tone, f"{k+1}. {t}" + ("  →" if k < len(_PIPE) - 1 else ""), l1, l2)
with open(ROOT / "data" / "story_diagrams.csv", "w", newline="") as _f:
    _w = csv.DictWriter(_f, fieldnames=list(DIAG[0].keys())); _w.writeheader(); _w.writerows(DIAG)
import story_images as SI
IMG = SI.render({"launch": (487, 696), "kpi": (1260, 136), "tree": (617, 208), "pipe": (1260, 104)})
def img_zone(key, h, w, x, y, zid):
    return f"<zone h='{h}' id='{zid}' is-scaled='1' param='Image/{IMG[key].name}' type-v2='bitmap' w='{w}' x='{x}' y='{y}' />"

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
 datasource("diag", "story_diagrams.csv", "tone"),
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
BAND = "#fde2b6"  # amber highlight: strong enough to read as a range, light enough to keep labels legible
_kmon = [r["month"] for r in _r("kenp")]
_kv = {r["month"]: float(r["per_page_rate"]) * 1000 for r in _r("kenp")}
_k_hi_m = max(_kv, key=_kv.get); _k_lo_m = min(_kv, key=_kv.get); _k_last = _kmon[-1]
_k_avg = sum(_kv.values()) / len(_kv)
_k_dip = min((m for m in _kmon if m > _k_hi_m), key=_kv.get)  # lowest month after the peak

sheet("01 Market ISBNs", "U.S. ISBN output by segment, 2022 to 2025 (stacked)", "isbn", [("titles","sum")], [("year","qk")], "Area", color=("segment","nk"),
      subtitle=f"Source: Bowker via Publishers Weekly, March 2026. Shaded: {_y0} to {_y1}, when self-published ISBNs rose {SP_GROWTH:.1%}",
      bands=[(("year", "qk"), _y0, _y1, "", "#fff1de")],
      axis_title=("titles", "sum", "rows", "New ISBNs issued"),
      fixed=("year", "qk", "cols", _yrs[0], _yrs[-1]),
      raw_ann=lambda ds: (
        f"<annotation class='point' id='0' mark-position='1' pullback='0' text-width='260'>"
        f"<formatted-text><run bold='true' fontcolor='{HL}'>Shaded {_y0} to {_y1}: The Jump</run>"
        f"<run fontcolor='#1f1f1f'>&#10;Self-published ISBNs rose {SP_GROWTH:.1%} in one year, from "
        f"{_iso[(_y0, 'Self-published')]/1e6:.2f}M to {_iso[(_y1, 'Self-published')]/1e6:.2f}M.</run></formatted-text>"
        f"<point><visual-coordinate class='mark'><tuple-reference><tuple-descriptor><pane-descriptor>"
        f"<x-fields><field>[{ds}].[none:year:qk]</field></x-fields><y-fields><field>[{ds}].[sum:titles:qk]</field></y-fields></pane-descriptor>"
        f"<columns><field>[{ds}].[none:segment:nk]</field><field>[{ds}].[none:year:qk]</field><field>[{ds}].[sum:titles:qk]</field></columns></tuple-descriptor>"
        f"<tuple><value>&quot;Self-published&quot;</value><value>{_y0}</value><value>{_iso[(_y0, 'Self-published')]}</value></tuple></tuple-reference></visual-coordinate></point>"
        f"<body x='-420' y='-85' /></annotation>"))
# marker: an orange pointer line ending in a dot where the shaded range starts
_i = [n for n, _ in SHEETS].index("01 Market ISBNs")
SHEETS[_i] = (SHEETS[_i][0], SHEETS[_i][1].replace("</style><panes>",
    f"<style-rule element='annotation'><format attr='line-end' id='annotation_0' value='dot' /><format attr='stroke-size' id='annotation_0' value='3' />"
    f"<format attr='stroke-color' id='annotation_0' value='{HL}' /></style-rule></style><panes>", 1))
sheet("02 Gross to Net", "Where each $16.99 of list price goes (print)", "gtn", [("platform","nk")], [("amount","sum")], "Bar", color=("component","nk"), label=("keep_label","sum"), filt=("format","Print"),
      subtitle=f"Model in this repository; rates from IngramSpark, KDP, B&N Press, Lulu and PublishDrive. Black line: what KDP leaves the creator (${KDP_NET:.2f})",
      lines=[(("amount", "sum"), round(KDP_NET, 3), "")],
      axis_title=("amount", "sum", "cols", "Dollars of the $16.99 list price"))
sheet("03 Cost Variance", "Cost variance vs Amazon KDP by driver, $ per print copy", "var", [("platform","nk")], [("variance","sum")], "Bar", color=("driver","nk"), label=("store_cut_label","sum"), filt=("format","Print"),
      subtitle="Positive = favorable to the IP owner. Drivers sum to the total variance.",
      lines=[(("variance", "sum"), 0, "KDP baseline")],
      axis_title=("variance", "sum", "cols", "Dollars per print copy compared with Amazon KDP"))
sheet("04 Ebook Net", "Net royalty per $4.99 ebook", "ebook", [("platform","nk")], [("net_royalty","sum")], "Bar", color=("platform","nk"), label=("net_royalty","sum"), sort=("platform","net_royalty"),
      subtitle="Store payout rates from ScribeCount; fees from KDP, Draft2Digital and the IngramSpark agreement",
      lines=[(("net_royalty", "sum"), EB_TOP, f"Best possible: ${EB_TOP:.2f} (70%)")],
      bands=[(("net_royalty", "sum"), EB_LO, EB_TOP, "", BAND)],
      fixed=("net_royalty", "sum", "cols", 0, 4.99),
      axis_title=("net_royalty", "sum", "cols", "Creator keeps per $4.99 ebook (axis runs to the full $4.99 price)"))
EBOOK_NOTE = f"Middlemen cost {round((EB_TOP-EB_HI)*100)} to {round((EB_TOP-EB_LO)*100)} cents a sale"
sheet("05 Breakeven Units", "Unit pairs needed to recover year-1 fixed costs", "be", [("stack","nk")], [("breakeven_unit_pairs","sum")], "Bar", color=("stack","nk"), label=("breakeven_unit_pairs","sum"),
      subtitle=f"Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions. Black line: fastest route, {BE_MIN['stack']} at {BE_MIN['breakeven_unit_pairs']} pairs",
      lines=[(("breakeven_unit_pairs", "sum"), int(BE_MIN["breakeven_unit_pairs"]), "")],
      notes=[(BE_MAX["stack"], BE_MAX["breakeven_unit_pairs"], f"{int(BE_MAX['breakeven_unit_pairs'])/int(BE_MIN['breakeven_unit_pairs']):.1f}x as many sales as the fastest route", 0, -40)],
      note_width=165,
      axis_title=("breakeven_unit_pairs", "sum", "cols", "Unit pairs sold (one print book plus one ebook)"))
sheet("06 Breakeven Curve", "Cumulative profit by unit pairs sold", "curve", [("cumulative_profit","sum")], [("unit_pairs","qk")], "Line", color=("stack","nk"),
      subtitle="Each line crosses zero at its breakeven point",
      lines=[(("cumulative_profit", "sum"), 0, "Breakeven ($0)")],
      bands=[(("unit_pairs", "qk"), int(BE_MIN["breakeven_unit_pairs"]), int(BE_MAX["breakeven_unit_pairs"]), f"Breakeven range: {BE_MIN['breakeven_unit_pairs']} to {BE_MAX['breakeven_unit_pairs']} pairs", BAND)])
sheet("07 Scenarios", "Year-1 net by sales level (10, 50 and 250 sales of each format a month)", "scen", [("stack","nk")], [("sales_level","nk"), ("year1_net","sum")], "Bar", color=("stack","nk"), label=("year1_net","sum"),
      subtitle="Planning scenarios, not forecasts. Each panel has its own scale so every bar is readable; compare ranks across panels, and dollars within a panel",
      axis_title=("year1_net", "sum", "cols", "Year-1 net (each panel has its own scale)"),
      independent=("year1_net", "sum", "cols"))
sheet("08 Accrual vs Cash", "Cumulative royalties earned by channel (stacked), 24 months", "cash", [("cumulative_earned","sum")], [("month","qk")], "Area", color=("channel","nk"),
      subtitle=f"Illustrative hybrid stack; launch curve and 65/35 channel mix are assumptions. Line at month 12: ${CASH_GAP12:,.0f} earned but not yet paid",
      lines=[(("month", "qk"), 12, "Month 12")],
      axis_title=("cumulative_earned", "sum", "rows", "Royalties earned to date"))
sheet("09 Days to Cash", "Average days from sale to cash", "pay", [("platform","nk")], [("avg_days_sale_to_cash","sum")], "Bar", color=("platform","nk"), label=("avg_days_sale_to_cash","sum"),
      subtitle=f"B&N Press Help Center; IngramSpark Agreement Sec. 9; The Book Designer; Books.by. Shaded: the {int(_pay[-1]['avg_days_sale_to_cash']) - int(_pay[0]['avg_days_sale_to_cash'])}-day gap between the fastest and slowest payer",
      bands=[(("avg_days_sale_to_cash", "sum"), int(_pay[0]["avg_days_sale_to_cash"]), int(_pay[-1]["avg_days_sale_to_cash"]), "", BAND)],
      axis_title=("avg_days_sale_to_cash", "sum", "cols", "Days from sale to cash"))
sheet("10 KENP Pool Rate", "Kindle Unlimited pay per 1,000 pages read", "kenp", [("pay_per_1000_pages","sum")], [("month","ok")], "Line", label=("pay_per_1000_pages","sum"),
      subtitle=f"Profitable.app KENP tracker (author-reported), May 2025 to April 2026. Each dot is one month; the flat line is the 12-month average (${_k_avg:.2f})",
      lines=[(("pay_per_1000_pages", "sum"), round(_k_avg, 2), f"Average: ${_k_avg:.2f}")],
      notes=[(_k_hi_m, round(_kv[_k_hi_m], 2), f"Peak: ${_kv[_k_hi_m]:.2f} in {_mname(_k_hi_m)}, the best month of the year", -160, 0),
             (_k_lo_m, round(_kv[_k_lo_m], 2), f"Low: ${_kv[_k_lo_m]:.2f} in {_mname(_k_lo_m)}, {1-_kv[_k_lo_m]/_kv[_k_hi_m]:.0%} less than the peak", -10, -150),
             (_k_dip, round(_kv[_k_dip], 2), f"{_mname(_k_dip)}: dropped to ${_kv[_k_dip]:.2f}, almost back to the low, then recovered", 200, -35),
             (_k_last, round(_kv[_k_last], 2), f"Latest: ${_kv[_k_last]:.2f} in {_mname(_k_last)}, above the average", -230, -40)],
      note_width=170,
      no_zero=("pay_per_1000_pages", "sum", "rows"),
      axis_title=("pay_per_1000_pages", "sum", "rows", "Dollars paid per 1,000 pages read"))
sheet("11 AB Breakeven Lift", "Volume lift a challenger needs to match the control", "ab", [("test","nk")], [("breakeven_lift_required","sum")], "Bar", label=("breakeven_lift_required","sum"),
      sort=("test", "breakeven_lift_required"),
      subtitle="Two-proportion z-test sizing at alpha 0.05 and power 0.80. Shaded strip: the range the two price tests must beat",
      bands=[(("breakeven_lift_required", "sum"), min(float(r["breakeven_lift_required"]) for r in _ab_price), max(float(r["breakeven_lift_required"]) for r in _ab_price),
              f"Price cuts need {min(float(r['breakeven_lift_required']) for r in _ab_price):.0%} to {max(float(r['breakeven_lift_required']) for r in _ab_price):.0%} more sales", BAND)],
      notes=[(_ab_hard["test"], _ab_hard["breakeven_lift_required"], "Hardest bar to clear: returns eat the margin", -220, 72)],
      note_width=170,
      axis_title=("breakeven_lift_required", "sum", "cols", "Extra sales needed just to tie (breakeven lift)"))

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

def diag_sheet(name, title, diagram, sub="", title_size=10, line_size=9, ban=False, size=None, lines=3):
    key = "diag"; ds = DS[key]["name"]
    insts = {}
    def r_(f, k):
        rr, xx = ci(key, f, k); insts[rr] = xx; return f"[{ds}].{rr}"
    rr, cc, tn = r_("row", "ok"), r_("col", "ok"), r_("tone", "nk")
    ww = r_("w", "sum")
    t0, t1, t2, dg = r_("title", "nk"), r_("line1", "nk"), r_("line2", "nk"), r_("diagram", "nk")
    deps = "".join(f"<column datatype='{DS[key]['cols'][f]}' name='[{f}]' role='dimension' type='{'nominal' if DS[key]['cols'][f]=='string' else 'ordinal'}' />"
                   for f in ("col", "diagram", "line1", "line2", "row", "title", "tone"))
    deps += "<column datatype='integer' name='[w]' role='measure' type='quantitative' />"
    vals = list(dict.fromkeys(r["tone"] for r in DS[key]["rows"]))
    pn = make_palette(f"IPDDV diag tone", {v: COL[v] for v in vals})
    maps = "".join(f"<map to='{COL[v]}'><bucket>&quot;{esc(v)}&quot;</bucket></map>" for v in vals)
    filt = (f"<filter class='categorical' column='{dg}'><groupfilter function='member' level='[none:diagram:nk]' member='&quot;{esc(diagram)}&quot;' "
            f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")
    ink = "#1f2a44"
    if ban:  # scorecard tile: small label, big bold value, small context line
        lab = (f"<customized-label><formatted-text><run bold='true' fontcolor='#3b4660' fontsize='9'>&lt;{t0}&gt;</run>"
               f"<run bold='true' fontcolor='{ink}' fontsize='20'>&#10;&lt;{t1}&gt;</run><run fontcolor='#3b4660' fontsize='8'>&#10;&lt;{t2}&gt;</run></formatted-text></customized-label>")
    else:
        runs = f"<run bold='true' fontcolor='{ink}' fontsize='{title_size}'>&lt;{t0}&gt;</run>"
        if lines >= 2: runs += f"<run fontcolor='{ink}' fontsize='{line_size}'>&#10;&lt;{t1}&gt;</run>"
        if lines >= 3: runs += f"<run fontcolor='#3b4660' fontsize='{line_size}'>&#10;&lt;{t2}&gt;</run>"
        lab = f"<customized-label><formatted-text>{runs}</formatted-text></customized-label>"
    style = (f"<style><style-rule element='header'><format attr='display' class='0' field='{rr}' scope='rows' value='false' />"
             f"<format attr='display' class='0' field='{cc}' scope='cols' value='false' /></style-rule>"
             f"<style-rule element='axis'><encoding attr='space' class='0' field='{ww}' field-type='quantitative' max='1.05' min='-0.05' range-type='fixed' scope='cols' type='space' />"
             f"<format attr='display' class='0' field='{ww}' scope='cols' value='false' /></style-rule>"
             f"<style-rule element='label'><format attr='display' field='{rr}' value='false' /><format attr='display' field='{cc}' value='false' /></style-rule>"
             f"<style-rule element='mark'><encoding attr='color' field='{tn}' palette='{pn}' type='palette'>{maps}</encoding></style-rule>"
             f"<style-rule element='worksheet'><format attr='display-field-labels' scope='rows' value='false' /><format attr='display-field-labels' scope='cols' value='false' /></style-rule></style>")
    subrun = f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(sub)}</run>" if sub else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontsize='13'>{esc(title)}</run>{subrun}</formatted-text></title></layout-options>"
         f"<table><view><datasources><datasource caption='{esc(DS[key]['caption'])}' name='{ds}' /></datasources>"
         f"<datasource-dependencies datasource='{ds}'>{deps}{''.join(insts[k] for k in sorted(insts))}</datasource-dependencies>"
         f"{filt}<aggregation value='true' /></view>{style}"
         f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
         f"<mark class='Bar' />{"<mark-sizing mark-sizing-setting='marks-scaling-off' />" if size else ""}<encodings><color column='{tn}' /><text column='{t0}' /><text column='{t1}' /><text column='{t2}' /></encodings>{lab}"
         f"<style><style-rule element='cell'><format attr='text-align' value='center' /><format attr='vertical-align' value='center' /></style-rule>"
         f"<style-rule element='mark'><format attr='mark-labels-show' value='true' /><format attr='mark-labels-cull' value='false' />{f"<format attr='size' value='{size}' />" if size else ""}</style-rule></style></pane></panes>"
         f"<rows>{rr}</rows><cols>({cc} / {ww})</cols></table><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></worksheet>")
    SHEETS.append((name, x))

exec(open(Path(__file__).resolve().parent / 'calc_block.py').read())

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
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' show-title='true' w='{w_each-19000}' x='{i*w_each}' y='8000' />"
            inner += f"<zone h='{chart_h}' id='{nid()}' name='{esc(s)}' pane-specification-id='0' param='{SHEET_COLOR[s]}' type-v2='color' w='19000' x='{i*w_each + w_each - 19000}' y='8000' />"
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
           f"<run bold='true' fontcolor='#52514e' fontsize='10'>Technical/analytic audience: </run><run fontcolor='#52514e' fontsize='10'>{esc(tech[0].upper() + tech[1:])} </run>"
           f"<run bold='true' fontcolor='#52514e' fontsize='10'>In plain terms (non-technical audiences): </run><run fontcolor='#52514e' fontsize='10'>{esc(plain)}</run>"
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
               "The line shows what Kindle Unlimited paid each month; the flat line is the average, and the call-outs point to the peak, the low, the January dip and the latest month.", [T_KENP, T_KDP]),
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
             f"<run fontcolor='#52514e' fontsize='11'>&#10;Find your type, then read its best choice, or follow the questions in the box at the lower right. As of {esc(ASOF)}.</run>"
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
    zones += img_zone("tree", h, 49000, 51000, 14500 + 2*h, zid)
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
INTRO = [
 ("Purpose", "#2a78d6", [
  ("The question", "Where should you sell a creative work, such as a book, guide or course, so you keep the most money from each sale, with risk and payment timing you can live with?"),
  ("What you get", "Each story point compares the same six platforms using their published prices, fees and payout rates, explains the result in plain language, and names its sources. The points follow the order of a real launch: point 2 shows the market, points 3 and 4 define each KPI (key performance indicator) with its formula, points 5 to 9 compare money kept and breakeven, point 10 is a profit calculator you can try, points 11 to 13 cover getting paid and testing prices, point 14 shows where every number comes from, and point 15 gives a recommendation for each type of owner.")]),
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
    hs = [24500, 22000, 22500, 20500]
    y = 10500
    for i, ((t, c, rows), h) in enumerate(zip(items, hs)):
        runs = f"<run bold='true' fontcolor='{c}' fontsize='16'>{esc(t)}</run>"
        for lab, txt in rows:
            runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='10'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='10'>{esc(txt)}</run>"
        zones += f"<zone h='{h}' id='{20+i}' type-v2='text' w='61000' x='0' y='{y}'><formatted-text>{runs}</formatted-text></zone>"
        y += h
    zones += img_zone("launch", sum(hs), 39000, 61000, 10500, 30)
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
dash_xml.insert(0, intro_dash("D0 Introduction", INTRO, "Introduction: purpose, scope and stakeholders"))

def text_page(dname, heading, sub, items, cols=2, top=10000, info=None):
    """items: list of (title, [(label, text), ...]) laid out in columns."""
    zones = (f"<zone h='{top}' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text><run bold='true' fontsize='18'>{esc(heading)}</run>"
             f"<run fontcolor='#52514e' fontsize='10'>&#10;{esc(sub)}</run></formatted-text></zone>")
    if info:
        zones += img_zone(info[0], info[1], 100000, 0, top, 19)
        top += info[1]
    avail = 100000 - top - 500; zid = 20
    _w = lambda it: 300 + len(it[0]) + sum(len(l) + len(x) for l, x in it[1])
    if cols == 2:  # split where the two columns hold about the same amount of text
        tot = sum(_w(it) for it in items); acc = 0; cut = len(items)
        for k, it in enumerate(items):
            if acc + _w(it) / 2 > tot / 2: cut = k; break
            acc += _w(it)
        groups = [items[:cut], items[cut:]]
    else:
        per = math.ceil(len(items) / cols); groups = [items[c*per:(c+1)*per] for c in range(cols)]
    for c in range(cols):
        col_items = groups[c]
        # each box gets height in proportion to its text (plus a fixed share for its heading and padding)
        wts = [300 + len(t) + sum(len(l) + len(x) for l, x in rows) for t, rows in col_items]
        ys = [top + 500]
        for wv in wts: ys.append(ys[-1] + int(avail * wv / sum(wts)))
        for r, (t, rows) in enumerate(col_items):
            h = ys[r + 1] - ys[r]
            runs = f"<run bold='true' fontcolor='#2a78d6' fontsize='11'>{esc(t)}</run>"
            for lab, txt in rows:
                runs += f"<run bold='true' fontcolor='#1f1f1f' fontsize='9'>&#10;{esc(lab)}: </run><run fontcolor='#1f1f1f' fontsize='9'>{esc(txt)}</run>"
            zones += f"<zone h='{h}' id='{zid}' type-v2='text' w='{100000//cols - 1000}' x='{c*(100000//cols)}' y='{ys[r]}'><formatted-text>{runs}</formatted-text></zone>"
            zid += 1
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{zones}</zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
import math
KPI_ITEMS = [(f"KPI {i}. {r['kpi']} ({r['full']})", [("What it tells you", r["meaning"]), ("Formula", r["formula"]), ("Example", r["worked"])]) for i, r in enumerate(KPIS, 1)]
dash_xml.insert(1, text_page("D0 KPIs", "KPI (key performance indicator) definitions, part 1: money kept per sale",
    f"Each formula is worked with the {ASOF} numbers. {MT.ROUNDING}", KPI_ITEMS[:7], info=("kpi1", 19500)))
dash_xml.insert(2, text_page("D0 KPIs 2", "KPI definitions, part 2: scale, cash timing and testing",
    f"Each formula is worked with the {ASOF} numbers. {MT.ROUNDING}", KPI_ITEMS[7:], info=("kpi2", 19500)))
SRC_ITEMS = [(f"{MT.PAGE_NO[r['dash']]}. {r['page']}", [("Numbers shown", r["numbers"]), ("Sources", "; ".join(MT.SOURCES[k][0] for k in r["sources"]))]) for r in sorted(MPAGES, key=lambda r: MT.PAGE_NO[r["dash"]])]
SRC_ITEMS.insert(6, ("10. Profit calculator", [("Numbers shown", "Profit, breakeven point, books still needed and share of launch costs earned back, for the books sold and launch budget you choose"), ("Sources", "Contribution per unit pair and fixed costs from the Breakeven page; same sources as points 5 to 9")]))
SRC_ITEMS.append(("How the model works", [("Estimates", "Print costs for IngramSpark, B&N Press and Lulu, the $1,500 launch budget, the 65/35 channel mix and the launch curve are planning assumptions, not published rates."),
    ("Clickable sources", "Each analysis page lists its sources by name; click a name to open it. The GitHub page lists every formula in its How the numbers work section.")]))
dash_xml.append(calc_dash("D12 Calculator"))
dash_xml.append(rec_dash("D10 Recommendations", PATHS, "Recommendations: the best route for each type of owner"))
dash_xml.append(text_page("D11 Number Sources", "Where the numbers come from",
    f"Prices, fees and rates as of {ASOF}; refreshed quarterly. Each analysis page also shows its calculation under How it is calculated.", SRC_ITEMS, info=("pipe", 15500)))

ACTIONS = "".join(
    f"<action caption='Open source: {esc(d[0])}' name='[Action_url_{i}]'><activation auto-clear='true' type='on-select' />"
    f"<source dashboard='{esc(d[0])}' type='sheet' worksheet='Sources {esc(d[0][:2])}' />"
    f"<link caption='' delimiter=',' escape='\\' expression='&lt;url&gt;' include-null='true' multi-select='false' url-escape='false' /></action>"
    for i, d in enumerate(DASH))

# ---------------- theme: match the slide deck (docs/index.html)
# navy page, dark panel cards for text, white cards for charts, orange kickers, serif headings
TH = dict(bg="#1b2a47", panel="#253759", line="#3a5079", ink="#eef2f8", ink2="#b7c2d6", muted="#8392ad",
          accent="#5aa2ff", accent2="#f0894f", card="#ffffff", serif="Georgia")
KICKER = {"D0 Introduction": "Introduction", "D1 Market": "Market context", "D0 KPIs": "How the numbers work",
          "D0 KPIs 2": "How the numbers work", "D2 Gross to Net": "Unit economics", "D3 Cost Variance": "Cost variance analysis",
          "D4 Ebook": "Unit economics", "D5 Breakeven": "Breakeven analysis", "D6 Scenarios": "Breakeven analysis",
          "D12 Calculator": "Try it yourself", "D7 Cash": "Working capital", "D8 Pool Volatility": "Uncertainty and experiments",
          "D9 AB Test": "Uncertainty and experiments", "D10 Recommendations": "Recommendation", "D11 Number Sources": "How the numbers work"}
_RECOLOR = {"#0b0b0b": TH["ink"], "#1f1f1f": "#dfe6f2", "#52514e": TH["ink2"], "#5b6475": TH["ink2"], CALC_INK: TH["ink"],
            "#c2410c": TH["accent2"], "#2a78d6": TH["accent"], "#eb6834": TH["accent2"], "#6250d6": "#a99bf5"}
def _zstyle(bg, border=None, margin=4, padding=8):
    b = f"<format attr='border-color' value='{border}' /><format attr='border-style' value='solid' /><format attr='border-width' value='1' />" if border else ""
    return f"<zone-style>{b}<format attr='margin' value='{margin}' /><format attr='padding' value='{padding}' /><format attr='background-color' value='{bg}' /></zone-style>"
def theme_dash(x):
    dname = _re.search(r"<dashboard name='([^']+)'", x).group(1)
    root_open = "<zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"
    i0 = x.index(root_open) + len(root_open); i1 = x.rindex("</zones>")
    body = x[i0:i1]
    body = _re.sub(r"<zone-style><format attr='background-color' value='#f6f4ef' /></zone-style></zone>$", "</zone>", body)
    body = body[:-len("</zone>")]
    # recolor text runs for the dark theme
    for a, b in _RECOLOR.items():
        body = body.replace(f"fontcolor='{a}'", f"fontcolor='{b}'")
    body = _re.sub(r"<run bold='true' fontsize='18'>", f"<run bold='true' fontcolor='{TH['ink']}' fontsize='18'>", body)
    # existing tiles (calculator): swap the light border for the deck's line color
    body = body.replace("<format attr='border-color' value='#e3e0d8' />", f"<format attr='border-color' value='{TH['line']}' />")
    tight = dname == "D12 Calculator"
    snug = dname in ("D0 KPIs", "D0 KPIs 2", "D11 Number Sources", "D10 Recommendations")
    out = []
    for m in _re.finditer(r"<zone [^>]*?(?:/>|>.*?</zone>)", body, flags=_re.S):
        z = m.group(0)
        is_text = "type-v2='text'" in z
        if "<zone-style>" in z or "type-v2='paramctrl'" in z:
            out.append(z); continue
        if is_text and "fontsize='18'" in z:
            # page heading: kicker + serif title on the page background, like a deck slide header
            k = KICKER.get(dname, "")
            z = z.replace("<formatted-text><run bold='true' fontcolor='" + TH['ink'] + "' fontsize='18'>",
                          f"<formatted-text><run bold='true' fontcolor='{TH['accent2']}' fontsize='9'>{esc(k.upper())}</run>"
                          f"<run bold='true' fontcolor='{TH['ink']}' fontname='{TH['serif']}' fontsize='19'>&#10;", 1)
            z = z.replace("</formatted-text></zone>", "</formatted-text>" + _zstyle(TH["bg"], margin=0, padding=4) + "</zone>")
        elif is_text and "YOUR NUMBERS" in z:
            z = z.replace("</formatted-text></zone>", "</formatted-text>" + _zstyle(TH["bg"], margin=0, padding=4) + "</zone>")
        elif is_text:
            z = z.replace("</formatted-text></zone>", "</formatted-text>" + _zstyle(TH["panel"], TH["line"], margin=3 if snug else 4, padding=4 if (tight or snug) else 8) + "</zone>")
        elif "name='Calc Donut Center'" in z:
            pass
        else:
            st = _zstyle(TH["card"], TH["line"], margin=4, padding=6)
            z = z[:-2] + ">" + st + "</zone>" if z.endswith("/>") else z.replace("</zone>", st + "</zone>")
        out.append(z)
    body = "".join(out) + _zstyle(TH["bg"], margin=0, padding=0 if tight else 10) + "</zone>"
    return x[:i0] + body + x[i1:]
import re as _re
# ebook card: call-out in the empty right side of the plot, so it never covers a bar or a value label
_ov = (f"<zone h='8500' id='90' type-v2='text' w='15500' x='60500' y='41500'><formatted-text>"
       f"<run bold='true' fontcolor='{HL}' fontsize='11'>\u25c0 Shaded strip</run>"
       f"<run fontcolor='#2b3445' fontsize='10'>&#10;{esc(EBOOK_NOTE)}.</run></formatted-text>"
       f"<zone-style><format attr='margin' value='0' /><format attr='padding' value='4' /><format attr='background-color' value='#ffffff' /></zone-style></zone>")
for _k, _d in enumerate(dash_xml):
    if "<dashboard name='D4 Ebook'>" in _d:
        _i = _d.rindex("</zone></zones>"); dash_xml[_k] = _d[:_i] + _ov + _d[_i:]
dash_xml = [theme_dash(d) for d in dash_xml]
def _tc_run(m):
    t = m.group(2)
    if "&lt;" in t: return m.group(0)  # field references stay as written
    return m.group(1) + esc(tc(html.unescape(t))).replace("\n", "&#10;") + "</run>"
dash_xml = [_re.sub(r"(<run bold='true'[^>]*>)(.*?)</run>", _tc_run, d) for d in dash_xml]

# ---------------- story
# story order follows a launch: market, KPI definitions, money kept per sale, breakeven, scenarios, the calculator, getting paid, testing
_order = [("D0 Introduction", "Start here: purpose, scope and who this is for."),
          ("D1 Market", None),
          ("D0 KPIs", "KPIs, part 1: money kept per sale and breakeven."),
          ("D0 KPIs 2", "KPIs, part 2: scale, cash timing and testing."),
          ("D2 Gross to Net", None), ("D3 Cost Variance", None), ("D4 Ebook", None), ("D5 Breakeven", None), ("D6 Scenarios", None),
          ("D12 Calculator", "Profit calculator: slide to see when each route turns a profit."),
          ("D7 Cash", None), ("D8 Pool Volatility", None), ("D9 AB Test", None),
          ("D11 Number Sources", "Where the numbers come from."),
          ("D10 Recommendations", "Recommendations: find your type and its best choice.")]
_caps = {n: cap for n, s_, note, hdr, cap in DASH}
STORY_ORDER = [(i, n, c or _caps[n]) for i, (n, c) in enumerate(_order, 1)]
points = "".join(f"<story-point captured-sheet='{esc(n)}' caption='{i}. {esc(tc(c))}' id='{i}' />" for i, n, c in STORY_ORDER)
story = (f"<dashboard name='IP Distribution Decision Verticals' type='storyboard'><style><style-rule element='story-point-caption'><format attr='background-color' value='{TH['accent']}' /><format attr='color' value='#06101f' /></style-rule></style><size maxheight='1110' maxwidth='1366' minheight='1110' minwidth='1366' sizing-mode='fixed' />"
         f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"
         f"<zone h='98000' id='2' param='vert' removable='false' type-v2='layout-flow' w='98800' x='600' y='1000'>"
         f"<zone h='4000' id='3' type-v2='text' w='98800' x='600' y='800'><formatted-text><run bold='true' fontcolor='{TH['ink']}' fontname='{TH['serif']}' fontsize='20'>IP Distribution Decision Verticals</run><run fontcolor='{TH['ink2']}' fontsize='11'>   Prices, fees and rates as of {esc(ASOF)}; refreshed quarterly</run></formatted-text>{_zstyle(TH['bg'], margin=0, padding=2)}</zone>"
         f"<zone h='13500' id='4' is-fixed='true' paired-zone-id='5' removable='false' type-v2='flipboard-nav' w='98800' x='600' y='4800' />"
         f"<zone h='81200' id='5' paired-zone-id='4' removable='false' type-v2='flipboard' w='98800' x='600' y='18300'><flipboard active-id='1' nav-type='caption' show-nav-arrows='true'>"
         f"<story-points>{points}</story-points></flipboard></zone></zone>{_zstyle(TH['bg'], margin=0, padding=0)}</zone></zones>"
         f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")

windows = "".join(f"<window class='worksheet' name='{esc(n)}'><cards><edge name='left'><strip size='160'><card type='pages' /><card type='filters' /><card type='marks' /></strip></edge><edge name='top'><strip size='2147483647'><card type='columns' /></strip><strip size='2147483647'><card type='rows' /></strip><strip size='31'><card type='title' /></strip></edge></cards><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for n, _ in SHEETS)
windows += "".join(f"<window class='dashboard' name='{esc(d[0])}'><viewpoints>{''.join(f"<viewpoint name='{esc(x)}'><zoom type='entire-view' /></viewpoint>" for x in d[1] + ['Sources ' + d[0][:2]])}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>" for d in DASH)
windows += f"<window class='dashboard' name='D0 Introduction'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D0 KPIs 2'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D0 KPIs'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D11 Number Sources'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D10 Recommendations'><viewpoints /><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
windows += f"<window class='dashboard' name='D12 Calculator'><viewpoints>{''.join(f"<viewpoint name='{x}'><zoom type='entire-view' /></viewpoint>" for x in CALC_SHEETS)}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"
_story_vp = ""
windows += f"<window class='dashboard' maximized='true' name='IP Distribution Decision Verticals'><viewpoints>{_story_vp}</viewpoints><active id='-1' /><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></window>"

PAL_XML = ''.join("<color-palette name='" + esc(n) + "' type='regular'>" + ''.join('<color>' + c + '</color>' for c in cs) + '</color-palette>' for n, cs in list(PALETTES.items()) + list(CALC_PALETTES.items()))
PREFS = "<preferences><preference name='ui.encoding.shelf.height' value='24' /><preference name='ui.shelf.height' value='26' />" + PAL_XML + "</preferences>"
twb = ("<?xml version='1.0' encoding='utf-8' ?>\n"
       "<workbook original-version='18.1' source-build='2024.1.0 (20241.24.0312.0830)' source-platform='mac' version='18.1' xmlns:user='http://www.tableausoftware.com/xml/user'>"
       "<document-format-change-manifest><_.fcp.MarkAnimation.true...MarkAnimation /><_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy /><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>"
       + PREFS +
       f"<datasources>{''.join(dsx)}</datasources>"
       f"<actions>{ACTIONS}</actions>"
       f"<worksheets>{''.join(x for _, x in SHEETS)}</worksheets>"
       f"<dashboards>{''.join(dash_xml)}{story}</dashboards>"
       f"<windows source-height='30'>{windows}</windows>{EXTERNAL}</workbook>")
twb = twb.replace("<document-format-change-manifest><_.fcp.MarkAnimation.true...MarkAnimation /><_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy /><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>",
                  "<document-format-change-manifest><SheetIdentifierTracking /><WindowsPersistSimpleIdentifiers /></document-format-change-manifest>")
# Tableau reads style rules in schema (alphabetical) order and silently drops rules that come out of order,
# which is why hand-written color maps used to be ignored. Sort every <style> block's rules by element name.
import re as _re2
def _sort_rules(m):
    body = m.group(1)
    rules = _re2.findall(r"<style-rule element='[^']+'>.*?</style-rule>", body)
    if "".join(rules) != body:
        return m.group(0)
    rules.sort(key=lambda r: _re2.match(r"<style-rule element='([^']+)'", r).group(1))
    return "<style>" + "".join(rules) + "</style>"
twb = _re2.sub(r"<style>((?:<style-rule element='[^']+'>.*?</style-rule>)+)</style>", _sort_rules, twb)
twb = twb.replace("<color-palette name=", "<color-palette custom='true' name=")
name = "IP_Distribution_Decision_Verticals"
(OUT / f"{name}.twb").write_text(twb)
with zipfile.ZipFile(OUT / f"{name}.twbx", "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(f"{name}.twb", twb)
    for f in (ROOT / "data").glob("*.csv"):
        z.write(f, f"Data/data/{f.name}")
    for f in EXT.glob("*.hyper"):
        z.write(f, f"Data/Extracts/{f.name}")
    for f in IMG.values():
        z.write(f, f"Image/{f.name}")
# story caption export for README, in story order
with open(OUT / "story_captions.md", "w") as f:
    f.write("# Tableau Story Captions\n\n")
    for i, n, c in STORY_ORDER:
        f.write(f"**Story Point {i}.** {tc(c)}\n\n")
        if n == "D0 Introduction":
            for _t, _c, _rows in INTRO:
                f.write(f"*{tc(_t)}.* " + " ".join(f"{_l}: {_x}" for _l, _x in _rows) + "\n\n")
        elif n.startswith("D0 KPIs"):
            f.write("KPI definitions with formulas and worked examples. See the How the numbers work section of the README.\n\n")
        elif n == "D12 Calculator":
            f.write("Sliders set books sold (print + ebook pairs, 0 to 1,000) and the launch budget ($0 to $5,000); a picker chooses the route. "
                    "Scorecards show year-1 profit, the breakeven point, books still needed and the share of launch costs earned back; a donut shows costs earned back; "
                    "a smiley face per route turns green (in profit), amber (over halfway) or red (under halfway); a line chart shows profit as sales grow for every route, "
                    "and a bar chart ranks year-1 profit by route.\n\n")
        elif n == "D10 Recommendations":
            for _t, _c, _rows in PATHS:
                f.write(f"*{tc(_t)}.* " + " ".join(f"{_l}: {_x}" for _l, _x in _rows) + "\n\n")
        elif n == "D11 Number Sources":
            f.write("See the How the numbers work section of the README.\n")
        else:
            note = next(d[2] for d in DASH if d[0] == n)
            f.write(f"{note}\n\nHow it is calculated: {CALC[n]['calc']}\n\nSources: " + " | ".join(f"[{t}]({u})" for t, u in SRC_LINKS[n]) + "\n\n")
print("ok", len(twb))
