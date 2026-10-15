# ---------------- profit calculator (story point 10): parameters, calculated fields, smiley shapes
# This file is exec'd inside build_tableau.py so it shares its helpers (DS, datasource, esc, SHEETS, ...).
import base64, io
from PIL import Image, ImageDraw

CALC_GREEN, CALC_AMBER, CALC_RED, CALC_INK = "#2e9e5b", "#f2a93b", "#d64545", "#1f2a44"
_be_rows = list(csv.DictReader(open(ROOT / "data" / "breakeven.csv")))
_ROUTES = [r["stack"] for r in _be_rows]
with open(ROOT / "data" / "calc_routes.csv", "w", newline="") as _f:
    _w = csv.writer(_f)
    _w.writerow(["stack", "part", "contribution_per_unit_pair", "platform_fixed_costs", "copyright_registration", "subscription_year1"])
    for r in _be_rows:
        for part in ("Earned back", "Still to earn back"):
            _w.writerow([r["stack"], part, r["contribution_per_unit_pair"], r["platform_fixed_costs"], r["copyright_registration"], r["subscription_year1"]])
with open(ROOT / "data" / "calc_curve.csv", "w", newline="") as _f:
    _w = csv.writer(_f)
    _w.writerow(["stack", "unit_pairs", "contribution_per_unit_pair", "platform_fixed_costs", "copyright_registration", "subscription_year1"])
    for r in _be_rows:
        for u in range(0, 1001, 10):
            _w.writerow([r["stack"], u, r["contribution_per_unit_pair"], r["platform_fixed_costs"], r["copyright_registration"], r["subscription_year1"]])

MOOD_COLOR_DS = {"In profit": CALC_GREEN, "Over halfway": CALC_AMBER, "Under halfway": CALC_RED}
P_UNITS, P_BUDGET, P_ROUTE = "[Parameters].[Parameter 1]", "[Parameters].[Parameter 2]", "[Parameters].[Parameter 3]"
_members = "".join(f"<member value='&quot;{esc(r)}&quot;' />" for r in _ROUTES)
PARAMS_DS = ("<datasource hasconnection='false' inline='true' name='Parameters' version='18.1'><aliases enabled='yes' />"
             "<column caption='Books sold (print + ebook pairs)' datatype='integer' default-format='n#,##0' name='[Parameter 1]' param-domain-type='range' role='measure' type='quantitative' value='300'>"
             "<calculation class='tableau' formula='300' /><range granularity='10' max='1000' min='0' /></column>"
             "<column caption='Launch budget' datatype='integer' default-format='c&quot;$&quot;#,##0' name='[Parameter 2]' param-domain-type='range' role='measure' type='quantitative' value='1500'>"
             "<calculation class='tableau' formula='1500' /><range granularity='100' max='5000' min='0' /></column>"
             f"<column caption='Route to look at' datatype='string' name='[Parameter 3]' param-domain-type='list' role='measure' type='nominal' value='&quot;Amazon KDP&quot;'>"
             f"<calculation class='tableau' formula='&quot;Amazon KDP&quot;' /><members>{_members}</members></column></datasource>")
PARAM_DEPS = ("<datasource-dependencies datasource='Parameters'>"
              "<column caption='Books sold (print + ebook pairs)' datatype='integer' default-format='n#,##0' name='[Parameter 1]' param-domain-type='range' role='measure' type='quantitative' value='300'><calculation class='tableau' formula='300' /><range granularity='10' max='1000' min='0' /></column>"
              "<column caption='Launch budget' datatype='integer' default-format='c&quot;$&quot;#,##0' name='[Parameter 2]' param-domain-type='range' role='measure' type='quantitative' value='1500'><calculation class='tableau' formula='1500' /><range granularity='100' max='5000' min='0' /></column>"
              f"<column caption='Route to look at' datatype='string' name='[Parameter 3]' param-domain-type='list' role='measure' type='nominal' value='&quot;Amazon KDP&quot;'><calculation class='tableau' formula='&quot;Amazon KDP&quot;' /><members>{_members}</members></column>"
              "</datasource-dependencies>")

_FIXED = f"[platform_fixed_costs] + [copyright_registration] + [subscription_year1] + {P_BUDGET}"
CALCS_R = [  # (name, caption, datatype, role, type, formula, default-format)
    ("c_fixed", "Launch costs to earn back", "real", "measure", "quantitative", _FIXED, "c&quot;$&quot;#,##0"),
    ("c_kept", "Money kept from sales", "real", "measure", "quantitative", f"{P_UNITS} * [contribution_per_unit_pair]", "c&quot;$&quot;#,##0"),
    ("c_profit", "Profit", "real", "measure", "quantitative", f"{P_UNITS} * [contribution_per_unit_pair] - ({_FIXED})", "c&quot;$&quot;#,##0;&quot;-$&quot;#,##0"),
    ("c_be", "Breakeven point", "integer", "measure", "quantitative", f"CEILING(({_FIXED}) / [contribution_per_unit_pair])", "n#,##0"),
    ("c_need", "Books still needed", "integer", "measure", "quantitative", f"MAX(CEILING(({_FIXED}) / [contribution_per_unit_pair]) - {P_UNITS}, 0)", "n#,##0"),
    ("c_rec", "Share earned back", "real", "measure", "quantitative", f"MIN({P_UNITS} * [contribution_per_unit_pair] / ({_FIXED}), 1)", "p0%"),
    ("c_donut", "Donut slice", "real", "measure", "quantitative",
     f"IF [part] = 'Earned back' THEN MIN({P_UNITS} * [contribution_per_unit_pair], {_FIXED}) ELSE MAX(({_FIXED}) - {P_UNITS} * [contribution_per_unit_pair], 0) END", "c&quot;$&quot;#,##0"),
    ("c_mood", "How it feels", "string", "dimension", "nominal",
     f"IF {P_UNITS} * [contribution_per_unit_pair] >= {_FIXED} THEN 'In profit' ELSEIF {P_UNITS} * [contribution_per_unit_pair] >= 0.5 * ({_FIXED}) THEN 'Over halfway' ELSE 'Under halfway' END", None),
    ("c_face", "Face", "string", "dimension", "nominal",
     f"IF {P_UNITS} * [contribution_per_unit_pair] >= {_FIXED} THEN '\U0001F600' ELSEIF {P_UNITS} * [contribution_per_unit_pair] >= 0.5 * ({_FIXED}) THEN '\U0001F610' ELSE '\U0001F641' END", None),
    ("c_sign", "Profit or loss", "string", "dimension", "nominal",
     f"IF {P_UNITS} * [contribution_per_unit_pair] >= {_FIXED} THEN 'Profit' ELSE 'Loss' END", None),
    ("c_sel", "Is the chosen route", "boolean", "dimension", "nominal", f"[stack] = {P_ROUTE}", None),
]
CALCS_C = [
    ("k_profit", "Profit at this many books", "real", "measure", "quantitative", f"[unit_pairs] * [contribution_per_unit_pair] - ({_FIXED})", "c&quot;$&quot;#,##0;&quot;-$&quot;#,##0"),
    ("k_param", "Your books sold", "integer", "measure", "quantitative", P_UNITS, "n#,##0"),
    ("k_sel", "Is the chosen route", "boolean", "dimension", "nominal", f"[stack] = {P_ROUTE}", None),
]
def _calc_xml(c):
    n, cap, dt, role, typ, f, fmt = c
    df = f" default-format='{fmt}'" if fmt else ""
    return f"<column caption='{esc(cap)}' datatype='{dt}'{df} name='[{n}]' role='{role}' type='{typ}'><calculation class='tableau' formula='{esc(f)}' /></column>"

def _with_calcs(ds_xml, calcs):
    anchor = "<column-instance " if "<column-instance " in ds_xml else "<extract "
    return ds_xml.replace(anchor, "".join(_calc_xml(c) for c in calcs) + anchor, 1)

_calc_ds = _with_calcs(datasource("calc", "calc_routes.csv"), CALCS_R)
def _ds_enc(field, mapping, pname):
    maps = "".join(f"<map to='{c}'><bucket>&quot;{esc(v)}&quot;</bucket></map>" for v, c in mapping.items())
    return f"<encoding attr='color' field='[none:{field}:nk]' palette='{esc(pname)}' type='palette'>{maps}</encoding>"
_calc_ds = _calc_ds.replace("<extract ", "".join(f"<column-instance column='[{f}]' derivation='None' name='[none:{f}:nk]' pivot='key' type='nominal' />" for f in ("c_mood", "c_sign", "part")) + "<extract ", 1)
_calc_ds = _calc_ds.replace("</datasource>", "<style><style-rule element='mark'>"
    + _ds_enc("c_mood", MOOD_COLOR_DS, "Calc In profit-Over halfway-Under halfway")
    + _ds_enc("c_sign", {"Loss": "#d64545", "Profit": "#2e9e5b"}, "Calc Loss-Profit")
    + _ds_enc("part", {"Earned back": "#2e9e5b", "Still to earn back": "#e5e7eb"}, "Calc Earned back-Still to earn back")
    + "</style-rule></style></datasource>")
dsx.append(_calc_ds)
dsx.append(_with_calcs(datasource("ccurve", "calc_curve.csv", "stack"), CALCS_C))
dsx.insert(0, PARAMS_DS)

# smiley shapes drawn here so the workbook carries its own illustrations
def _face(color, mood):
    im = Image.new("RGBA", (256, 256), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((8, 8, 248, 248), fill=color, outline="#ffffff", width=6)
    d.ellipse((80, 82, 108, 118), fill=CALC_INK); d.ellipse((148, 82, 176, 118), fill=CALC_INK)
    if mood == "happy":
        d.arc((64, 96, 192, 206), 20, 160, fill=CALC_INK, width=14)
        d.ellipse((52, 140, 82, 160), fill="#ffffff55"); d.ellipse((174, 140, 204, 160), fill="#ffffff55")
    elif mood == "neutral":
        d.line((88, 172, 168, 172), fill=CALC_INK, width=14)
    else:
        d.arc((70, 156, 186, 250), 200, 340, fill=CALC_INK, width=14)
    b = io.BytesIO(); im.save(b, "PNG"); return base64.b64encode(b.getvalue()).decode()
SHAPES = {"Smileys/in_profit.png": _face(CALC_GREEN, "happy"), "Smileys/over_halfway.png": _face(CALC_AMBER, "neutral"),
          "Smileys/under_halfway.png": _face(CALC_RED, "sad")}
for _n, _b in SHAPES.items():
    p = ROOT / "tableau" / "_shapes" / _n.split("/")[1]; p.parent.mkdir(exist_ok=True); p.write_bytes(base64.b64decode(_b))
EXTERNAL = ""  # custom shapes are not used; the faces are emoji text marks
MOOD_SHAPE = {"In profit": "Smileys/in_profit.png", "Over halfway": "Smileys/over_halfway.png", "Under halfway": "Smileys/under_halfway.png"}
MOOD_COLOR = {"In profit": CALC_GREEN, "Over halfway": CALC_AMBER, "Under halfway": CALC_RED}

def _deps(key, calcs, insts):
    ds = DS[key]["name"]
    base = "".join(f"<column datatype='{t}' name='[{esc(c)}]' role='{'dimension' if t == 'string' else 'measure'}' type='{'nominal' if t == 'string' else 'quantitative'}' />"
                   for c, t in DS[key]["cols"].items())
    return f"<datasource-dependencies datasource='{ds}'>{base}{''.join(_calc_xml(c) for c in calcs)}{''.join(insts)}</datasource-dependencies>" + PARAM_DEPS

def _inst(name, kind):
    if kind in ("nk", "ok"):
        return f"[none:{name}:{kind}]", f"<column-instance column='[{name}]' derivation='None' name='[none:{name}:{kind}]' pivot='key' type='{'nominal' if kind == 'nk' else 'ordinal'}' />"
    if kind == "qk":
        return f"[none:{name}:qk]", f"<column-instance column='[{name}]' derivation='None' name='[none:{name}:qk]' pivot='key' type='quantitative' />"
    d = {"sum": "Sum", "min": "Min", "avg": "Avg"}[kind]
    return f"[{kind}:{name}:qk]", f"<column-instance column='[{name}]' derivation='{d}' name='[{kind}:{name}:qk]' pivot='key' type='quantitative' />"

def _filter(ds, inst_name, member, quoted=True):
    level = inst_name
    mv = f"&quot;{esc(member)}&quot;" if quoted else member
    return (f"<filter class='categorical' column='[{ds}].{inst_name}'><groupfilter function='member' level='{level}' member='{mv}' "
            f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' /></filter>")

CALC_PALETTES = {}
def _palette(ds, inst_name, mapping):
    # Tableau ignores per-value color maps written by hand, so each mapping becomes a named workbook palette
    # whose colors follow the alphabetical order of the values; the explicit maps are kept as a fallback.
    pname = "Calc " + "-".join(sorted(mapping))[:40]
    CALC_PALETTES[pname] = [mapping[k] for k in sorted(mapping)]
    maps = "".join(f"<map to='{c}'><bucket>&quot;{esc(v)}&quot;</bucket></map>" for v, c in mapping.items())
    return f"<encoding attr='color' field='[{ds}].{inst_name}' palette='{esc(pname)}' type='palette'>{maps}</encoding>"

def _ws(name, title, key, calcs, insts, filters, rows, cols, mark, enc, extra_pane="", style_rules="", sub=""):
    ds = DS[key]["name"]
    st = f"<style>{style_rules}</style>" if style_rules else "<style />"
    subrun = f"<run fontcolor='#5b6475' fontsize='9'>&#10;{esc(sub)}</run>" if sub else ""
    x = (f"<worksheet name='{esc(name)}'><layout-options><title><formatted-text><run bold='true' fontcolor='{CALC_INK}' fontsize='11'>{esc(tc(title))}</run>{subrun}</formatted-text></title></layout-options>"
         f"<table><view><datasources><datasource caption='{esc(DS[key]['caption'])}' name='{ds}' /><datasource name='Parameters' /></datasources>"
         f"{_deps(key, calcs, insts)}{''.join(filters)}<aggregation value='true' /></view>{st}"
         f"<panes><pane selection-relaxation-option='selection-relaxation-allow'><view><breakdown value='auto' /></view>"
         f"<mark class='{mark}' /><encodings>{enc}</encodings>{extra_pane}</pane></panes>"
         f"<rows>{rows}</rows><cols>{cols}</cols></table><simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></worksheet>")
    SHEETS.append((name, x))

_dsr, _dsc = DS["calc"]["name"], DS["ccurve"]["name"]
_part, _part_x = _inst("part", "nk"); _stack, _stack_x = _inst("stack", "nk"); _sel, _sel_x = _inst("c_sel", "nk")
_f_part = _filter(_dsr, _part, "Earned back"); _f_sel = _filter(_dsr, _sel, "true", quoted=False)

# big-number tiles (BANs)
def _ban(name, label, calc, kind, color, sub, sign_color=False):
    ref, refx = _inst(calc, kind)
    insts = [_part_x, _sel_x, refx]
    enc = f"<text column='[{_dsr}].{ref}' />"
    rules = f"<style-rule element='mark'><format attr='mark-labels-show' value='true' /></style-rule>"
    if sign_color:
        sg, sgx = _inst("c_sign", "nk"); insts.append(sgx)
        enc = f"<color column='[{_dsr}].{sg}' />" + enc
        rules = f"<style-rule element='mark'>{_palette(_dsr, sg, {'Profit': CALC_GREEN, 'Loss': CALC_RED})}<format attr='mark-labels-show' value='true' /></style-rule>"
    lab = (f"<customized-label><formatted-text><run bold='true' fontcolor='{color}' fontsize='20'>&lt;[{_dsr}].{ref}&gt;</run></formatted-text></customized-label>")
    rules += ("<style-rule element='cell'><format attr='text-align' value='center' /><format attr='vertical-align' value='center' /></style-rule>"
              "<style-rule element='worksheet'><format attr='display-field-labels' scope='rows' value='false' /></style-rule><style-rule element='table'><format attr='background-color' value='#ffffff' /></style-rule>")
    _ws(name, label, "calc", CALCS_R, insts, [_f_part, _f_sel], "", "", "Text", enc, lab, rules, sub)

_ban("Calc BAN Profit", "PROFIT IN YEAR 1", "c_profit", "sum", CALC_INK, "money kept minus launch costs", sign_color=True)
_ban("Calc BAN Breakeven", "BREAKEVEN POINT", "c_be", "sum", CALC_INK, "books needed to earn back costs")
_ban("Calc BAN Needed", "BOOKS STILL NEEDED", "c_need", "sum", "#c2410c", "0 means you are already in profit")
_ban("Calc BAN Recovered", "COSTS EARNED BACK", "c_rec", "sum", "#2563eb", "share of launch costs covered")

# donut: a pie of earned back vs still to earn back, with a white center tile floated on top in the dashboard
_don, _donx = _inst("c_donut", "sum")
_ws("Calc Donut", "Launch costs earned back", "calc", CALCS_R, [_part_x, _sel_x, _donx], [_f_sel], "", "", "Pie",
    f"<color column='[{_dsr}].{_part}' /><wedge-size column='[{_dsr}].{_don}' />", "",
    f"<style-rule element='mark'>{_palette(_dsr, _part, {'Earned back': CALC_GREEN, 'Still to earn back': '#e5e7eb'})}<format attr='size' value='1.2' /></style-rule>"
    "<style-rule element='table'><format attr='background-color' value='#ffffff' /></style-rule>",
    "green = sales so far, gray = still to go")
_rec, _recx = _inst("c_rec", "sum")
_ws("Calc Donut Center", "", "calc", CALCS_R, [_part_x, _sel_x, _recx], [_f_part, _f_sel], "", "", "Text",
    f"<text column='[{_dsr}].{_rec}' />",
    f"<customized-label><formatted-text><run bold='true' fontcolor='{CALC_INK}' fontsize='24'>&lt;[{_dsr}].{_rec}&gt;</run><run fontcolor='#5b6475' fontsize='9'>&#10;earned back</run></formatted-text></customized-label>",
    "<style-rule element='mark'><format attr='mark-labels-show' value='true' /></style-rule><style-rule element='table'><format attr='background-color' value='#ffffff' /></style-rule>")

# smiley strip: one face per route (emoji text marks, so no custom shape files are needed), colored caption by mood
_md, _mdx = _inst("c_mood", "nk"); _fc, _fcx = _inst("c_face", "nk")
_ws("Calc Faces", "How each route feels at your numbers", "calc", CALCS_R, [_part_x, _stack_x, _mdx, _fcx], [_f_part], "", f"[{_dsr}].{_stack}", "Text",
    f"<color column='[{_dsr}].{_md}' /><text column='[{_dsr}].{_fc}' /><text column='[{_dsr}].{_md}' />",
    f"<customized-label><formatted-text><run fontsize='44'>&lt;[{_dsr}].{_fc}&gt;</run><run bold='true' fontsize='10'>&#10;&lt;[{_dsr}].{_md}&gt;</run></formatted-text></customized-label>",
    f"<style-rule element='mark'>{_palette(_dsr, _md, MOOD_COLOR)}<format attr='mark-labels-show' value='true' /></style-rule>"
    "<style-rule element='table'><format attr='background-color' value='#ffffff' /></style-rule>",
    "smile = in profit, straight face = over halfway, frown = under halfway")

# leaderboard: profit by route at the slider settings
_pr, _prx = _inst("c_profit", "sum"); _sg, _sgx = _inst("c_sign", "nk")
_ws("Calc Leaderboard", "Year-1 profit by route", "calc", CALCS_R, [_part_x, _stack_x, _prx, _sgx], [_f_part],
    f"[{_dsr}].{_stack}", f"[{_dsr}].{_pr}", "Bar",
    f"<color column='[{_dsr}].{_sg}' /><text column='[{_dsr}].{_pr}' />", "",
    f"<style-rule element='mark'>{_palette(_dsr, _sg, {'Profit': CALC_GREEN, 'Loss': CALC_RED})}<format attr='mark-labels-show' value='true' /></style-rule>"
    f"<style-rule element='axis'><format attr='title' class='0' field='[{_dsr}].{_pr}' scope='cols' value='Profit (green) or loss (red)' /></style-rule>",
    "updates as you move the sliders")
# sort the leaderboard by profit
SHEETS[-1] = (SHEETS[-1][0], SHEETS[-1][1].replace("<aggregation value='true' />",
    f"<sort class='computed' column='[{_dsr}].{_stack}' direction='DESC' using='[{_dsr}].{_pr}' /><aggregation value='true' />", 1))

# profit curve for every route with a marker at the chosen number of books
_kp, _kpx = _inst("k_profit", "sum"); _u, _ux = _inst("unit_pairs", "qk"); _cs, _csx = _inst("stack", "nk")
_kq, _kqx = _inst("k_param", "min")
_curve_cols = {r: COL.get(r, "#8a8984") for r in _ROUTES}
_ws("Calc Curve", "Profit as sales grow, every route", "ccurve", CALCS_C, [_kpx, _ux, _csx, _kqx], [], f"[{_dsc}].{_kp}", f"[{_dsc}].{_u}", "Line",
    f"<color column='[{_dsc}].{_cs}' /><lod column='[{_dsc}].{_kq}' />",
    f"<reference-line axis-column='[{_dsc}].{_u}' enable-instant-analytics='true' formula='min' id='refline0' label='Your books sold: &lt;Value&gt;' label-type='custom' scope='per-table' value-column='[{_dsc}].{_kq}' z-order='2' />"
    f"<reference-line axis-column='[{_dsc}].{_kp}' enable-instant-analytics='true' formula='constant' id='refline1' label='Breakeven ($0)' label-type='custom' scope='per-table' value='0.001' value-column='[{_dsc}].{_kp}' z-order='3' />",
    f"<style-rule element='mark'>{_palette(_dsc, _cs, _curve_cols)}</style-rule>"
    f"<style-rule element='axis'><format attr='title' class='0' field='[{_dsc}].{_kp}' scope='rows' value='Profit' /><format attr='title' class='0' field='[{_dsc}].{_u}' scope='cols' value='Books sold (print + ebook pairs)' /></style-rule>",
    "lines cross $0 at each breakeven point; the vertical line follows your slider")
SHEET_COLOR["Calc Curve"] = f"[{_dsc}].{_cs}"

CALC_SHEETS = ["Calc BAN Profit", "Calc BAN Breakeven", "Calc BAN Needed", "Calc BAN Recovered", "Calc Donut", "Calc Donut Center", "Calc Faces", "Calc Leaderboard", "Calc Curve"]

def _tile(inner_xml):
    return inner_xml.replace(" />", "><zone-style><format attr='border-color' value='#e3e0d8' /><format attr='border-style' value='solid' /><format attr='border-width' value='1' /><format attr='margin' value='6' /><format attr='background-color' value='#ffffff' /></zone-style></zone>", 1)

def calc_dash(dname):
    z = []
    z.append(f"<zone h='9500' id='11' type-v2='text' w='100000' x='0' y='0'><formatted-text>"
             f"<run bold='true' fontcolor='{CALC_INK}' fontsize='18'>Profit calculator: how many books until you are in profit?</run>"
             f"<run fontcolor='#5b6475' fontsize='10'>&#10;Move the sliders to set how many books you sell in year 1 and what you spend to launch, then pick a route to see its numbers. "
             f"One book here means one print copy plus one ebook. As of {esc(ASOF)}.</run></formatted-text></zone>")
    # control panel
    z.append(f"<zone h='4200' id='12' type-v2='text' w='22000' x='0' y='10000'><formatted-text><run bold='true' fontcolor='#c2410c' fontsize='11'>YOUR NUMBERS</run></formatted-text></zone>")
    z.append(_tile(f"<zone h='9500' id='13' mode='slider' param='{P_UNITS}' type-v2='paramctrl' w='22000' x='0' y='14500' />"))
    z.append(_tile(f"<zone h='9500' id='14' mode='slider' param='{P_BUDGET}' type-v2='paramctrl' w='22000' x='0' y='24500' />"))
    z.append(_tile(f"<zone h='9500' id='15' mode='compact' param='{P_ROUTE}' type-v2='paramctrl' w='22000' x='0' y='34500' />"))
    z.append(f"<zone h='31500' id='16' type-v2='text' w='22000' x='0' y='44500'><formatted-text>"
             f"<run bold='true' fontcolor='{CALC_INK}' fontsize='10'>How it is calculated</run>"
             f"<run fontcolor='#1f1f1f' fontsize='9'>&#10;Money kept = books sold x what you keep per print + ebook pair.&#10;Launch costs = platform fees + $85 copyright + launch budget + any subscription.&#10;Profit = money kept - launch costs.&#10;Breakeven = launch costs / money kept per pair, rounded up.</run>"
             f"<run bold='true' fontcolor='{CALC_INK}' fontsize='10'>&#10;&#10;Try this</run>"
             f"<run fontcolor='#1f1f1f' fontsize='9'>&#10;Set the budget to $0 and KDP is in profit after its first sale. Raise it to $5,000 and watch the faces turn red.</run></formatted-text></zone>")
    # BAN row
    for i, n in enumerate(CALC_SHEETS[:4]):
        z.append(_tile(f"<zone h='15500' id='{20+i}' name='{n}' show-title='true' w='19000' x='{23500 + i*19200}' y='10000' />"))
    # donut and its center
    z.append(_tile(f"<zone h='33000' id='30' name='Calc Donut' show-title='true' w='24000' x='23500' y='26000' />"))
    z.append(f"<zone h='9000' id='31' name='Calc Donut Center' show-title='false' w='9000' x='31000' y='41000' />")
    # faces
    z.append(_tile(f"<zone h='33000' id='32' name='Calc Faces' show-title='true' w='52500' x='48000' y='26000' />"))
    # curve + legend, leaderboard
    z.append(_tile(f"<zone h='40000' id='33' name='Calc Curve' show-title='true' w='33000' x='23500' y='59500' />"))
    z.append(f"<zone h='40000' id='34' name='Calc Curve' pane-specification-id='0' param='{SHEET_COLOR['Calc Curve']}' type-v2='color' w='11000' x='56800' y='59500' />")
    z.append(_tile(f"<zone h='40000' id='35' name='Calc Leaderboard' show-title='true' w='32500' x='68000' y='59500' />"))
    z.append(f"<zone h='24000' id='36' type-v2='text' w='22000' x='0' y='76000'><formatted-text>"
             f"<run bold='true' fontcolor='{CALC_INK}' fontsize='10'>Reading the faces</run>"
             f"<run fontcolor='#1f1f1f' fontsize='9'>&#10;Green smile: sales cover all launch costs.&#10;Amber face: over halfway there.&#10;Red frown: under halfway.&#10;Planning estimates, not forecasts.</run></formatted-text></zone>")
    return (f"<dashboard name='{dname}'><style /><size maxheight='800' maxwidth='1300' minheight='800' minwidth='1300' sizing-mode='fixed' />"
            f"<zones><zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>{''.join(z)}"
            f"<zone-style><format attr='background-color' value='#f6f4ef' /></zone-style></zone></zones>"
            f"<simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' /></dashboard>")
