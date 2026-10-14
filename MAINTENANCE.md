# Maintenance and troubleshooting

How to rebuild, back up and debug this repository's three outputs: the slide deck on GitHub Pages, the Tableau Public story, and this repository itself.

## Where everything lives

| Output | Location | Built from |
|---|---|---|
| Slide deck | [GitHub Pages](https://shamarrobinson.github.io/ip-distribution-decision-verticals/) (served from `docs/` on `main`) | `analysis/build_deck.py` writes `docs/index.html`; charts copied into `docs/assets/` |
| Deck PDF | `docs/IP_Distribution_Decision_Verticals.pdf` | `docs/index.html` printed with Playwright/Chromium at 13.333 x 7.5 in |
| Tableau story | [Tableau Public](https://public.tableau.com/app/profile/shamar.robinson/viz/IPDistributionDecisionVerticals/IPDistributionDecisionVerticals) | `tableau/IP_Distribution_Decision_Verticals.twbx` from `analysis/build_tableau.py` |
| Excel model | `workbook/IP_Distribution_Cost_Variance_Model.xlsx` | Live formulas; `analysis/stamp_workbook.py` updates the as-of note |
| Data | `data/*.csv` | `analysis/model.py` (single source of truth for every number) |
| As-of date | `as_of.json` | Edited by hand or by the quarterly refresh |

Backups: the GitHub repository (with dated restore-point tags), a git clone on the author's Mac in `~/Documents/Github/ip-distribution-decision-verticals`, and the published Tableau Public workbook.

## Rebuild everything

```bash
pip install matplotlib tableauhyperapi openpyxl playwright
python analysis/model.py
python analysis/methods.py      # rewrites the How the numbers work section of the README
python analysis/charts.py
python analysis/diagrams.py
cp charts/*.svg charts/*.png docs/assets/charts/ && cp charts/pages/* docs/assets/charts/pages/ && cp diagrams/*.svg diagrams/*.png docs/assets/diagrams/
python analysis/build_deck.py
python analysis/build_tableau.py
python analysis/stamp_workbook.py
```

Then regenerate the PDF from `docs/index.html`, delete any `hyperd*.log` files, commit and push. GitHub Pages redeploys within a minute or two.

## Restore a working version

Each known-good state is tagged `restore-YYYY-MM-DD`.

```bash
git tag -l "restore-*"                 # list restore points
git checkout restore-2026-10-12 -- .   # bring files back from a restore point
```

To restore the Tableau story, open `tableau/IP_Distribution_Decision_Verticals.twbx` from the restore point in Tableau Public and use File > Save to Tableau Public As with the title "IP Distribution Decision Verticals" (overwrite).

## Known Tableau gotchas (learned while building)

- **Tableau Public only opens workbooks with extracts.** Every datasource carries an `<extract>` block pointing to a `.hyper` file in `Data/Extracts/` inside the `.twbx`. The `.hyper` files are created by the Hyper API in `build_tableau.py`.
- **Schema order matters.** Inside a datasource the order is connection, aliases, columns, extract, layout, style. `<layout>` needs `dim-percentage` and `measure-percentage`.
- **Font sizes must be whole numbers** (`fontsize='12'`, never `12.5`), or the workbook will not load.
- **Dashboards need viewpoints.** Each dashboard window lists its sheets in `<viewpoints>`; otherwise Tableau reports "no visual representation".
- **Colors are pinned with custom palettes.** A color map only sticks when (1) the datasource has a `<column-instance>` for the colored field, placed after the calculated columns and before `<extract>`, (2) the encoding names `palette='NAME'` and a matching `<color-palette custom='true' name='NAME'>` sits in `<preferences>` with colors in alphabetical order of the values, and (3) the style rules in each `<style>` are sorted by element name. `build_tableau.py` handles all three (`make_palette`, `_sort_rules`). Current mapping on the cost charts: blue = platform fees, orange = printing, red = store's cut, teal = what the creator keeps; the static charts in `analysis/charts.py` match. If you rename a value, re-check the palette and the notes.
- **Clickable source names** use a URL action whose link expression is `<url>` with `url-escape='false'`. With escaping on, Tableau URL-encodes the whole address and the link breaks.
- **Tableau caches workbooks by file name.** When testing a changed `.twbx`, open it under a new file name or Tableau may show the old version.
- **Theme:** `TH` in `build_tableau.py` mirrors the deck's CSS variables in `build_deck.py` (`--bg`, `--panel`, `--line`, `--ink`, `--accent`, `--accent2`). Change both together. `theme_dash()` applies it to every dashboard; the story navigator color is the `story-point-caption` style rule.
- **Story infographics** (`diag_sheet` in `build_tableau.py`, data in `data/story_diagrams.csv`): each box is a Bar mark on a hidden 0 to 1 axis, one pane per column, so boxes stretch to fill their cell (Square marks stay square and cannot). Hiding discrete headers needs both a `header` and a `label` style rule; centered labels need a `cell` rule with `text-align` and `vertical-align`; bar thickness is `mark-sizing` off plus a `size` value.
- **Annotation line styles** (colour, weight, dot or arrow end) live in the worksheet style as `<style-rule element='annotation'>` with `id='annotation_N'`, not inside the annotation itself.
- **Tableau Desktop caches extracts by file name**, so test a changed build under a new name or old data may show.
- **Custom shapes are dropped on load** when injected through `<external><shapes>`; the calculator's faces are emoji text marks instead, which render on Tableau Public.
- **A reference line on a parameter** needs a calculated field equal to the parameter placed on Detail, with the line using `min` of that field.
- **Text-box line breaks:** start a run with `&#10;` followed by text; a run that holds only a line break is dropped.

## Plain-language and style rules

- Notes are written for readers about 14 to 15 years old, start with "As of <date>:", and name the colors exactly as drawn.
- No em dashes in body text; keep the established naming (IP Distribution Decision Verticals, "verticals", "stakeholders").
- Every figure carries a source, shown by name, with the name as the clickable link.

## Quarterly refresh

A scheduled task runs on January 11, April 11, July 11 and October 11. It re-checks every rate and source, updates `as_of.json`, rebuilds all outputs, logs changes in `CHANGELOG.md`, pushes to GitHub and republishes the Tableau story.
