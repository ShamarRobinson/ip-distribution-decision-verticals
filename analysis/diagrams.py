"""Render the business-type decision tree, plus one copy per stakeholder vertical with its path highlighted."""
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "diagrams"
NODES = {
 "q1": ("Where will most\nbuyers come from?", "q"),
 "q2": ("Need bookstore or\nlibrary placement?", "q"),
 "q3": ("Selling more than ~17 of\neach format a month?", "q"),
 "q4": ("Do you own an audience?\n(email list, events,\nclients, students)", "q"),
 "A": ("A. Independent creator\nKDP print + ebook", "#2a78d6"),
 "B": ("B. Small press or imprint\nKDP + IngramSpark", "#eb6834"),
 "C": ("C. Catalog or backlist owner\nKDP + PublishDrive", "#e87ba4"),
 "D": ("D. Brand, educator or\ncorporate IP owner\nOwn store (Lulu Direct) + KDP", "#eda100"),
 "E": ("E. Wide ebook strategist\nKDP + Draft2Digital or\ndirect Apple / Kobo / B&N", "#1baf7a"),
}
EDGES = [("q1", "q2", "Stores and\nonline retail"), ("q1", "q4", "My own\nchannels"), ("q2", "A", "No, Amazon\nis enough"),
         ("q2", "q3", "Yes"), ("q3", "B", "No"), ("q3", "C", "Yes"), ("q4", "D", "Yes"), ("q4", "E", "No,\nebook-led")]
PATHS = {"A": ["q1", "q2", "A"], "B": ["q1", "q2", "q3", "B"], "C": ["q1", "q2", "q3", "C"], "D": ["q1", "q4", "D"], "E": ["q1", "q4", "E"]}
TINT = {"#2a78d6": "#e8f0fb", "#eb6834": "#fdeee7", "#e87ba4": "#fcecf2", "#eda100": "#fdf4df", "#1baf7a": "#e3f5ee"}

def dot(highlight=None, title="Decision tree: which distribution stack fits your business type?"):
    path = PATHS.get(highlight, [])
    on_edges = set(zip(path, path[1:]))
    hcol = NODES[highlight][1] if highlight else None
    out = ['digraph G { rankdir=TB; bgcolor="#fcfcfb"; pad=0.3; nodesep=0.35; ranksep=0.5;',
           f'labelloc=t; label=<<b>{title}</b>>; fontname="Inter"; fontsize=16;',
           'node [fontname="Inter", fontsize=12, penwidth=1.3]; edge [fontname="Inter", fontsize=10.5, arrowsize=0.75];']
    for k, (lab, kind) in NODES.items():
        lit = (not highlight) or k in path
        if kind == "q":
            fill = "#fff6dc" if (highlight and lit) else "#f0efec"
            col = hcol if (highlight and lit) else "#c9c8c2"
            out.append(f'{k} [label="{lab}", shape=diamond, style=filled, fillcolor="{fill}", color="{col}", fontcolor="{"#0b0b0b" if lit else "#b0afa9"}", margin="0.04,0.04", penwidth={2.4 if (highlight and lit) else 1.2}];')
        else:
            fill = TINT[kind] if lit else "#f6f6f4"; col = kind if lit else "#dedcd6"
            out.append(f'{k} [label="{lab}", shape=box, style="rounded,filled", fillcolor="{fill}", color="{col}", fontcolor="{"#0b0b0b" if lit else "#b0afa9"}", margin="0.18,0.1", penwidth={3 if highlight == k else 1.3}];')
    for a, b, lab in EDGES:
        on = (a, b) in on_edges
        c = hcol if on else ("#8a8984" if not highlight else "#dedcd6")
        out.append(f'{a} -> {b} [label="{lab}", color="{c}", fontcolor="{"#0b0b0b" if (on or not highlight) else "#c9c8c2"}", penwidth={3.2 if on else 1.3}];')
    out.append("}")
    return "\n".join(out)

def render(name, src):
    (OUT / f"{name}.dot").write_text(src)
    subprocess.run(["dot", "-Tsvg", str(OUT / f"{name}.dot"), "-o", str(OUT / f"{name}.svg")], check=True)
    subprocess.run(["dot", "-Tpng", "-Gdpi=170", str(OUT / f"{name}.dot"), "-o", str(OUT / f"{name}.png")], check=True)

if __name__ == "__main__":
    render("d2_vertical_decision_tree", dot())
    for v in PATHS:
        render(f"d2_path_{v}", dot(v, title=f"Your path through the decision tree: Vertical {v}"))
    print("ok")
