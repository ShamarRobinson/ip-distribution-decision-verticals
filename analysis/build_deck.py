"""Build the hyperlinked HTML slide deck at docs/index.html."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GH = "https://github.com/ShamarRobinson/ip-distribution-decision-verticals"
PAGES = "https://shamarrobinson.github.io/ip-distribution-decision-verticals/"
TABLEAU = "TABLEAU_URL"
PDF = "IP_Distribution_Decision_Verticals.pdf"

S = {  # sources
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
}
def src(*keys):
    return '<div class="src">Sources: ' + "; ".join(f'<a href="{S[k][1]}" target="_blank" rel="noopener">{S[k][0]}</a>' for k in keys) + "</div>"
def img(path, alt):
    return f'<figure class="viz"><img src="assets/{path}" alt="{alt}" loading="lazy"></figure>'

slides = []
def slide(sid, kicker, title, body, cls=""):
    slides.append((sid, kicker, title, body, cls))

# 1 Title
slide("title", "", "", f"""
<div class="hero">
  <div class="eyebrow">Intellectual property strategy &middot; Cost variance &middot; Breakeven &middot; A/B testing</div>
  <h1>IP Distribution<br>Decision Verticals</h1>
  <p class="lede">A decision framework that helps owners of intellectual property choose a distribution model that fits their business type, built on unit economics, cost variance analysis, breakeven analysis and testable hypotheses.</p>
  <div class="cta">
    <a class="btn" href="#contents">Start the walkthrough &rarr;</a>
    <a class="btn ghost" href="{TABLEAU}" target="_blank" rel="noopener">Open the Tableau story</a>
    <a class="btn ghost" href="{GH}" target="_blank" rel="noopener">View on GitHub</a>
  </div>
  <p class="note">Status note: certain works referenced by this analysis are in the initial stage of pre-publication copyright registration with the <a href="https://www.copyright.gov/registration/" target="_blank" rel="noopener">U.S. Copyright Office</a>. No title-specific details are disclosed.</p>
  <p class="byline">Prepared by Shamar Robinson &middot; October 2026</p>
</div>""", "title-slide")

# 2 Contents
toc = [("summary","Executive summary"),("decision","The decision and the five verticals"),("lens","A cross-industry lens"),
("market","Market context in numbers"),("market-charts","Market context charts"),("value-chain","The IP value chain"),
("options","The options on the table"),("gross-to-net","Gross-to-net unit economics"),("variance","Cost variance analysis"),
("ebook","Ebook economics"),("sensitivity","Sensitivity analysis"),("breakeven","Breakeven analysis"),("crossover","Breakeven curves and crossover"),
("scenarios","Scenario analysis"),("cash","Accrual vs cash and DSO"),("pool","Pool-based payout volatility"),("abtest","A/B test design"),
("tree-verticals","Decision tree by business type"),("tree-terms","Decision trees: exclusivity and returns"),("choices","Choice options by vertical"),
("risks","Contract risk register"),("recommendation","Recommendation and decision request"),("method","Methodology and assumptions"),
("glossary","Glossary of cross-industry terms"),("sources","Sources")]
half = (len(toc)+1)//2
cols = "".join('<ol start="%d">%s</ol>' % (start+1, "".join(f'<li><a href="#{a}">{t}</a></li>' for a,t in part)) for start, part in ((0, toc[:half]), (half, toc[half:])))
slide("contents", "Navigate", "Contents", f"""
<div class="toc">{cols}</div>
<div class="linkrow">
  <a href="{TABLEAU}" target="_blank" rel="noopener">Tableau story &#8599;</a>
  <a href="{GH}" target="_blank" rel="noopener">GitHub repository &#8599;</a>
  <a href="{GH}/tree/main/data" target="_blank" rel="noopener">Data (CSV) &#8599;</a>
  <a href="{GH}/raw/main/workbook/IP_Distribution_Cost_Variance_Model.xlsx">Excel model &#8595;</a>
  <a href="{PDF}" target="_blank" rel="noopener">PDF version &#8595;</a>
</div>""")

# 3 Exec summary
slide("summary", "Executive summary", "Three findings drive the decision", f"""
<div class="grid3">
  <div class="card"><div class="big">$6.79 vs $3.33</div><h3>Channel share drives the cost variance</h3><p>On a $16.99 paperback, Amazon KDP returns $6.79 per unit while IngramSpark's bookstore route returns $3.33. About $2.55 of that $3.47 gap is the retailer discount, not printing or platform fees. <a href="#variance">See the variance bridge</a>.</p></div>
  <div class="card"><div class="big">158 vs 272</div><h3>Breakeven depends on contribution, not fees</h3><p>With $1,585 to $1,710 in Year-1 fixed costs, KDP breaks even at 158 unit pairs (one print plus one ebook) and IngramSpark at 272. Platform fees alone are recovered within 20 pairs. <a href="#breakeven">See the breakeven analysis</a>.</p></div>
  <div class="card"><div class="big">16.6 / month</div><h3>A subscription only wins at scale</h3><p>PublishDrive's flat $13.99 monthly fee beats IngramSpark's per-sale fees only above 16.6 units per format per month. Below that, variable-cost models are cheaper. <a href="#crossover">See the crossover</a>.</p></div>
</div>
<p class="callout"><b>Decision ask:</b> approve a two-channel launch (KDP plus one wide-distribution route chosen by business vertical), with a 90-day A/B test on price and channel terms before committing to exclusivity. <a href="#recommendation">Go to the recommendation</a>.</p>""")

# 4 decision + verticals
slide("decision", "Scope", "The decision, and who it is for", """
<p class="lede-s">Every owner of intellectual property faces the same make-or-buy distribution question: <b>which channels turn a protected work into the most contribution margin, at acceptable risk and cash timing?</b> The answer differs by business type, so this analysis is organized into five decision verticals.</p>
<div class="grid5">
 <div class="vcard a"><span>A</span><h4>Independent creator</h4><p>One work, Amazon-led discovery, limited capital.</p></div>
 <div class="vcard b"><span>B</span><h4>Small press or imprint</h4><p>Needs bookstore and library placement for a curated list.</p></div>
 <div class="vcard c"><span>C</span><h4>Catalog or backlist owner</h4><p>Many titles and steady volume; fixed fees amortize well.</p></div>
 <div class="vcard d"><span>D</span><h4>Brand, educator or corporate IP owner</h4><p>Owns an audience; sells through events, courses or a website.</p></div>
 <div class="vcard e"><span>E</span><h4>Wide ebook strategist</h4><p>Digital-first, wants reach beyond one retailer.</p></div>
</div>
<p class="muted">Stakeholders: IP owners, finance and FP&amp;A partners, marketing leads, rights and contracts teams, and investors evaluating content businesses.</p>""")

# 5 lens
rows = [("Cost variance analysis","Net royalty per unit vs a KDP baseline, split into channel, production and fee drivers","Manufacturing, SaaS, healthcare budgeting"),
("Gross-to-net (GTN)","List price to net royalty waterfall","Pharma, CPG, music streaming"),
("Contribution margin and breakeven","Units needed to recover launch costs","Retail, restaurants, hardware startups"),
("Fixed vs variable cost crossover","Subscription vs per-sale fee models","Cloud pricing, payments, logistics"),
("Sensitivity and scenario analysis","Tornado chart; bear, base and bull volumes","Corporate FP&amp;A, infrastructure finance"),
("A/B testing and breakeven lift","Price and channel-term experiments with sample sizes","E-commerce, product, marketing"),
("Days sales outstanding (DSO)","45 to 105 days from sale to cash","Every B2B business, working-capital planning"),
("Pool-based payouts","Kindle Unlimited per-page rate","Music streaming pro-rata pools, ad networks"),
("Returns reserve and counterparty risk","Returnable wholesale terms; retailer non-payment","Retail, distribution, insurance")]
slide("lens", "Why it matters beyond publishing", "A cross-industry lens on one IP decision", 
'<table class="tbl"><thead><tr><th>Concept</th><th>How it is used here</th><th>Where else you see it</th></tr></thead><tbody>' +
"".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a,b,c in rows) + '</tbody></table><p class="muted">Full definitions are in the <a href="#glossary">glossary</a>.</p>')

# 6 market tiles
tiles = [("$33.4B","U.S. publisher revenue, 2025","+2.5% vs 2024","aap"),("4.17M","ISBNs issued in the U.S., 2025","3.53M self-published, +38.7%","bowker"),
("762.4M","Print units sold, 2025","+0.3% vs 2024","circana"),("415,780","Copyright registrations, FY2025","169,098 were literary works","usco"),
("3.4 mo","Average e-filed registration time","5.3 months with correspondence","uscotime"),("$65 &rarr; $85","Standard Application fee","New fee schedule from mid-November 2026","uscofee")]
slide("market", "Market context", "Mainstream benchmarks frame the opportunity", '<div class="tiles">' + "".join(
f'<a class="tile" href="{S[k][1]}" target="_blank" rel="noopener"><div class="tv">{v}</div><div class="tl">{l}</div><div class="td">{d}</div><div class="ts">{S[k][0]} &#8599;</div></a>' for v,l,d,k in tiles) +
'</div><p class="lede-s">Supply of new works is growing much faster than unit demand: ISBN output rose 32.5% in 2025 while print unit sales rose 0.3%. More works compete for the same buyers, so the margin kept per sale and the cost to launch matter more every year.</p>')

slide("market-charts", "Market context", "Self-published supply is surging while print still earns most revenue",
'<div class="two">' + img("charts/01_market_isbn_stacked.svg","Stacked line chart of ISBN output 2022 to 2025") + img("charts/02_market_aap_formats.svg","Bar chart of 2025 revenue by format") + '</div>' +
'<p class="lede-s">The stacked line shows self-published ISBNs climbing to 3.53 million in 2025. Hardback and paperback still bring in $16.2 billion of the $33.4 billion market, which is why print distribution choices carry the most dollars.</p>' + src("bowker","aap"))

slide("value-chain", "Process flow", "The IP value chain: from protected work to reconciled cash",
img("diagrams/d1_ip_value_chain.svg","Flowchart of the IP value chain") +
'<div class="grid2s"><p><b>Step 2 is where rights are secured.</b> Certain works covered here are in the initial stage of pre-publication copyright registration with the U.S. Copyright Office. Registration is a prerequisite for filing an infringement suit over a U.S. work and for statutory damages, so it is treated as a fixed launch cost ($85 Standard Application under the new schedule).</p><p><b>Steps 7 through 10 are where finance lives.</b> Gross-to-net deductions, cash timing and reconciliation are the same disciplines used in film participations, music royalties and SaaS revenue operations.</p></div>' + src("usco","uscofee","uscotime"))

opt_rows = [("Amazon KDP","60% of list minus print","70% ($2.99 to $9.99)","Free","~60 days after month end","Amazon only"),
("IngramSpark","List minus 35 to 55% discount, print, 1.875% fee","85% of store payout","Free setup; own ISBN","~90 days after month end","Bookstores, libraries, 45,000+ outlets"),
("B&amp;N Press","55% of list minus print","70% flat","Free; print ISBN free","~30 days after month end","BN.com (U.S.)"),
("Lulu","Retail: 50% fee, print, then 20% commission","Fee plus commission","Free; proof required","Monthly","Own store, retail, your site"),
("PublishDrive","Ingram network, 0% commission","100% of store payout","$13.99 to $83.99/mo","Monthly","400+ stores"),
("Draft2Digital","Print via partners","~90% of store payout","$20 account fee","Monthly, ~60-day lag","Apple, Kobo, Google, libraries")]
slide("options", "Choice set", "Six options, three cost models", '<table class="tbl sm"><thead><tr><th>Platform</th><th>Print economics</th><th>Ebook economics</th><th>Fixed cost</th><th>Payment terms</th><th>Reach</th></tr></thead><tbody>' +
"".join("<tr>" + "".join(f"<td>{c}</td>" if i else f"<td><b>{c}</b></td>" for i,c in enumerate(r)) + "</tr>" for r in opt_rows) +
'</tbody></table><p class="lede-s">The options fall into three cost models: <b>retailer-direct</b> (KDP, B&amp;N), <b>wholesale with per-sale fees</b> (IngramSpark, Lulu, Draft2Digital) and <b>subscription with zero commission</b> (PublishDrive).</p>' + src("ingram","kdp","bn","lulu","pd","d2d","store"))

slide("gross-to-net", "Unit economics", "Gross-to-net: where each $16.99 goes", img("charts/03_print_gross_to_net.svg","Stacked bar of list price components by platform") +
'<p class="lede-s">The gray channel share is the largest deduction on every wholesale route. Lulu&rsquo;s own bookstore keeps $9.59 because no retailer takes a cut, but it brings almost no shoppers on its own. Print costs for IngramSpark, B&amp;N and Lulu are planning estimates to be replaced with each platform&rsquo;s calculator output.</p>' + src("kdp","ingram","bn","lulu","jf"))

slide("variance", "Cost variance analysis", "The variance bridge: channel share explains most of the gap", img("charts/04_cost_variance_drivers.svg","Diverging stacked bar of variance drivers vs KDP") +
'<p class="lede-s">Each bar decomposes one platform&rsquo;s variance against the KDP baseline into three drivers that sum to the total, the same price, cost and mix logic used in a budget-vs-actual review. For IngramSpark, the 55% discount costs $2.55, higher print costs $0.60 and the market access fee $0.32, for a total unfavorable variance of $3.47 per unit.</p>' + src("ingram","kdp"))

slide("ebook", "Unit economics", "Ebooks: direct uploads beat aggregators", img("charts/05_ebook_net_per_unit.svg","Bar chart of ebook net royalty by platform") +
'<p class="lede-s">On a $4.99 ebook, direct stores pay $3.49. KDP pays $3.28 after a $0.30 delivery fee. Aggregators trade $0.35 to $0.52 per unit for one-upload reach, which is a classic take-rate versus convenience trade-off.</p>' + src("store","kdp","d2d","ingramtc"))

slide("sensitivity", "Risk", "Sensitivity analysis: price is the biggest lever", img("charts/06_sensitivity_tornado.svg","Tornado chart") +
'<p class="lede-s">Flexing each input by 20% shows that list price moves KDP&rsquo;s net royalty by $4.08 per unit, four times the effect of page count. On IngramSpark, the wholesale discount is the largest controllable lever, which makes discount terms the first thing to test.</p>' + src("kdp","ingram"))

slide("breakeven", "Breakeven analysis", "How many sales recover the launch investment?", img("charts/07_breakeven_units.svg","Breakeven units by platform") +
'<div class="formula">Breakeven units = Year-1 fixed costs &divide; contribution per unit pair &nbsp;&nbsp;|&nbsp;&nbsp; Fixed costs = platform fees + $85 copyright registration + $1,500 illustrative launch budget + subscriptions</div>' +
'<p class="lede-s">KDP needs 158 unit pairs and IngramSpark 272. Without the illustrative launch budget, platform-only fixed costs are recovered within 0 to 42 pairs, so the real breakeven risk sits in production spend, not platform fees. Stakeholders should replace the $1,500 placeholder with their own budget in the <a href="' + GH + '/raw/main/workbook/IP_Distribution_Cost_Variance_Model.xlsx">Excel model</a>.</p>' + src("uscofee","isbn","pd"))

slide("crossover", "Breakeven analysis", "Breakeven curves and the subscription crossover", '<div class="two">' + img("charts/08_breakeven_curve.svg","Cumulative profit curves") + img("charts/09_crossover_breakeven.svg","Crossover chart") + '</div>' +
'<p class="lede-s">Left: each line crosses zero at its breakeven point, and steeper slopes mean higher contribution margin. Right: PublishDrive&rsquo;s fixed fee overtakes IngramSpark&rsquo;s variable fees at 16.6 units per format per month, and overtakes Draft2Digital for ebooks at 40.1 units per month.</p>' + src("pd","ingram","d2d"))

slide("scenarios", "Scenario planning", "Bear, base and bull volumes change the ranking very little", img("charts/10_scenario_analysis.svg","Small multiples of scenario results") +
'<p class="lede-s">KDP leads in every scenario, followed by B&amp;N Press. PublishDrive moves ahead of IngramSpark once volume clears the crossover, which happens in the base and bull cases. These are planning scenarios, not forecasts; reach differs by channel, so equal volume per platform is a simplifying assumption.</p>' + src("kdp","bn","pd"))

slide("cash", "Working capital", "Accrual vs cash: royalties earned lead cash by two to three months", '<div class="two w64">' + img("charts/11_hybrid_stack_accrual_vs_cash.svg","Stacked line of cumulative earned royalties vs cash") + img("charts/12_payout_timing_dso.svg","Days from sale to cash by platform") + '</div>' +
'<p class="lede-s">In an illustrative hybrid stack (KDP plus IngramSpark plus Draft2Digital), $948 of earned royalties is still uncollected at month 12. IngramSpark&rsquo;s terms add about 60 days of DSO versus B&amp;N Press, and the agreement also lets it hold payments while a retailer has not paid (counterparty risk).</p>' + src("bn","ingramtc","bd","booksby","wwm"))

slide("pool", "Variable revenue", "Pool-based payouts add volatility to exclusive ebook income", img("charts/13_kenp_pool_volatility.svg","KENP per-page rate line chart") +
'<p class="lede-s">Kindle Unlimited pays from a monthly pool divided by pages read, the same pro-rata mechanism used by music streaming services. Over the last 12 reported months the rate averaged $4.55 per 1,000 pages with a 6.1% coefficient of variation, swinging from $4.19 to $5.01. In the 2025 Written Word Media survey, 38% of authors kept every book in KDP Select and 30% were fully wide.</p>' + src("kenp","wwm"))

slide("abtest", "Experimentation", "A/B test design: know the breakeven lift before you test", '<div class="stack">' + img("diagrams/d5_ab_test_flow.svg","A/B test workflow") + img("charts/14_ab_test_breakeven_lift.svg","Breakeven lift by test") + '</div>' +
'<p class="lede-s">A price cut must lift unit sales by more than its breakeven lift to raise profit: 21.4% for a $16.99 to $14.99 print test and 27.1% for a $4.99 to $3.99 ebook test. Detecting a lift that size at a 2% baseline conversion takes about 18,467 visitors per arm. Retail platforms do not split traffic, so run time-boxed sequential tests or route paid traffic to two purchase links (for example, IngramSpark Share &amp; Sell links).</p>' + src("kdp","ingramtc"))

slide("tree-verticals", "Decision tree", "Which distribution stack fits your business type?", img("diagrams/d2_vertical_decision_tree.svg","Decision tree by business vertical") +
'<p class="lede-s">The thresholds come from the model: a 16.6-unit monthly crossover separates Vertical B from Vertical C, and owned-audience businesses (Vertical D) keep the most margin by selling direct, where Lulu Direct takes no revenue share.</p>' + src("pd","lulu"))

slide("tree-terms", "Decision trees", "Two follow-on decisions: exclusivity and returns", '<div class="two">' + img("diagrams/d3_exclusivity_tree.svg","Ebook exclusivity decision tree") + img("diagrams/d4_returns_discount_tree.svg","Returns and discount decision tree") + '</div>' +
'<p class="lede-s">Exclusivity trades reach for pool income; returnability trades margin and return risk for shelf placement. Both are reversible on known terms (90-day KDP Select periods; a 180-day return tail on IngramSpark), so both are good candidates for time-boxed tests.</p>' + src("wwm","ingramtc"))

ch = [("A","Independent creator","KDP print + ebook","KDP + Draft2Digital (wide ebook)","KDP + KDP Select","158 pairs"),
("B","Small press or imprint","KDP + IngramSpark 55% returnable","KDP + IngramSpark 40% non-returnable","KDP + B&amp;N Press + IngramSpark","272 pairs (IngramSpark)"),
("C","Catalog or backlist owner","KDP + PublishDrive","KDP + IngramSpark + Draft2Digital","PublishDrive only","264 pairs; crossover 16.6/mo"),
("D","Brand, educator or corporate","Lulu Direct on own site + KDP","IngramSpark Share &amp; Sell links","Lulu Bookstore + KDP","Driven by owned traffic"),
("E","Wide ebook strategist","KDP + direct Apple, Kobo, B&amp;N","KDP + Draft2Digital","KDP + PublishDrive (above 40/mo)","Ebook-only economics")]
slide("choices", "Choice options", "Three options per vertical, from lowest risk to widest reach", '<table class="tbl sm"><thead><tr><th></th><th>Vertical</th><th>Option 1: Recommended</th><th>Option 2: Alternative</th><th>Option 3: Stretch</th><th>Breakeven marker</th></tr></thead><tbody>' +
"".join(f'<tr><td><span class="pill {r[0].lower()}">{r[0]}</span></td><td><b>{r[1]}</b></td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>' for r in ch) +
'</tbody></table><p class="lede-s">Option 1 maximizes contribution per unit for each business type. Option 2 changes one variable and doubles as the B arm of an A/B test. Option 3 adds reach once volume supports it.</p>')

risks = [("Returns liability","Returnable titles bill returns back to the IP owner; a 180-day tail applies after switching to non-returnable","High","Start non-returnable; test returnability later","Sec. 5.4.5"),
("Payment timing and offsets","Compensation paid ~90 days after month end; can be held or offset for returns and other Ingram accounts","Medium","Plan cash with DSO assumptions; keep a reserve","Sec. 8.5, 9"),
("Counterparty non-payment","IP owner bears its share if a retailer never pays","Low to medium","Monitor statements; reconcile monthly","Sec. 8.3"),
("Unilateral changes","Terms and pricing can change; compensation changes take effect after 30 days","Medium","Review notices; re-run the model on each change","Sec. 2"),
("Early release","Enabling distribution lets orders ship before the publication date","Medium","Enable distribution only at launch","Sec. 5.1.2"),
("Liability cap","Platform liability capped at $500; broad indemnity owed by the IP owner","Low frequency, high impact","Confirm rights and clearances before upload","Sec. 12, 13")]
slide("risks", "Risk register", "Contract terms that change the economics", '<table class="tbl sm"><thead><tr><th>Risk</th><th>What the agreement says</th><th>Rating</th><th>Mitigation</th><th>Reference</th></tr></thead><tbody>' +
"".join("<tr>" + "".join(f"<td>{c}</td>" if i else f"<td><b>{c}</b></td>" for i,c in enumerate(r)) + "</tr>" for r in risks) +
'</tbody></table><p class="muted">Section references are to the IngramSpark Agreement (last updated March 20, 2025). This is a plain-language business summary, not legal advice.</p>' + src("ingramtc"))

slide("recommendation", "Recommendation", "Decision request: a two-channel launch with a 90-day test window", """
<div class="grid3">
 <div class="card"><h3>1. Launch</h3><p>List print and ebook on KDP for every vertical. Add one wide route chosen from the <a href="#tree-verticals">decision tree</a>. Keep print non-returnable at launch and enable distribution only on the release date.</p></div>
 <div class="card"><h3>2. Test</h3><p>Run one A/B test per 90 days: price first, then channel terms. Pre-register the metric (net royalty per visitor) and the <a href="#abtest">breakeven lift</a>, and stop only at the planned sample size.</p></div>
 <div class="card"><h3>3. Review</h3><p>Hold a monthly variance review (budget vs actual by driver) and a quarterly re-forecast. Revisit exclusivity and subscriptions when volume crosses 16.6 units per format per month.</p></div>
</div>
<p class="callout"><b>Success measures:</b> breakeven reached within the planned unit count; contribution per unit within 5% of plan; cash received within the modeled DSO; one decision-grade A/B result per quarter.</p>""")

slide("method", "Methodology", "How the numbers were built", f"""
<div class="grid2s">
<div><h4>Model</h4><ul>
<li>One Python model (<a href="{GH}/blob/main/analysis/model.py">analysis/model.py</a>) writes every dataset in <a href="{GH}/tree/main/data">/data</a>; the deck, Excel workbook and Tableau story all read the same numbers.</li>
<li>Base case: $16.99 paperback, 200 pages, $4.99 ebook (2 MB), equal unit volume per platform.</li>
<li>Variance = platform net royalty minus KDP net royalty, decomposed into channel share, production and platform-fee drivers that sum exactly to the total.</li>
<li>A/B sample sizes use a two-proportion z-test (alpha 0.05, power 0.80).</li></ul></div>
<div><h4>Assumptions to replace</h4><ul>
<li>Print costs for IngramSpark ($4.00), B&amp;N Press ($3.50) and Lulu ($5.00) are planning estimates.</li>
<li>The $1,500 launch budget, the 65/35 channel mix and the launch-decay curve are illustrative.</li>
<li>Platform terms reflect sources available as of October 2026 and change often.</li>
<li>Status note: certain works referenced are in the initial stage of pre-publication copyright registration with the U.S. Copyright Office.</li></ul></div>
</div>""")

gl = [("A/B test","A controlled comparison of two variants on one metric, run long enough to reach a pre-set sample size."),
("Breakeven lift","The minimum increase in volume a cheaper variant needs just to match the control's contribution."),
("Breakeven point","Units at which cumulative contribution equals fixed costs."),
("Channel share / take rate","The portion of the sale price kept by the retailer or marketplace."),
("Coefficient of variation (CV)","Standard deviation divided by mean; a unit-free measure of volatility."),
("Contribution margin","Revenue per unit minus variable costs per unit; what each sale adds toward fixed costs."),
("Cost variance analysis","Explaining the difference between two cost outcomes by isolating each driver."),
("Days sales outstanding (DSO)","Average days between a sale and the cash arriving."),
("Gross-to-net (GTN)","The waterfall from list price to net revenue after discounts, fees and allowances."),
("Margin of safety","How far planned volume can fall before reaching breakeven."),
("Pool-based payout","Revenue paid from a fixed pool shared by usage, as in streaming royalties."),
("Returns reserve","Cash or earnings held back to cover expected returns."),
("Scenario analysis","Comparing outcomes under bear, base and bull assumptions."),
("Sensitivity analysis","Flexing one input at a time to see which one moves the result most."),
("Working capital gap","Revenue earned but not yet collected in cash.")]
slide("glossary", "Reference", "Glossary of cross-industry analytics and FP&amp;A terms", '<dl class="gloss">' + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a,b in gl) + "</dl>")

order = ["aap","bowker","circana","usco","uscotime","uscofee","ingram","ingramtc","jf","kdp","kdped","bn","bd","lulu","pd","d2d","booksby","store","isbn","tortora","wwm","kenp"]
slide("sources", "Attribution", "Sources", '<ol class="srclist">' + "".join(f'<li><a href="{S[k][1]}" target="_blank" rel="noopener">{S[k][0]}</a> <span>{S[k][1]}</span></li>' for k in order) +
'</ol><p class="muted">Mainstream industry sources (AAP, Bowker, Circana BookScan, U.S. Copyright Office) frame the market; platform help centers and agreements set the rates. Figures reflect sources available as of October 2026.</p>')

# ---------------------------------------------------------------- render
n = len(slides)
sec = []
for i, (sid, kicker, title, body, cls) in enumerate(slides):
    prev_id = slides[i-1][0] if i else None
    next_id = slides[i+1][0] if i < n-1 else None
    head = "" if sid == "title" else f'<header><div class="kicker">{kicker}</div><h2>{title}</h2></header>'
    nav = (f'<nav class="snav"><a href="#contents">Contents</a>'
           + (f'<a href="#{prev_id}">&larr; Prev</a>' if prev_id else "")
           + (f'<a href="#{next_id}">Next &rarr;</a>' if next_id else "")
           + f'<a href="{TABLEAU}" target="_blank" rel="noopener">Tableau</a><a href="{GH}" target="_blank" rel="noopener">GitHub</a>'
           + f'<span class="pg">{i+1} / {n}</span></nav>')
    sec.append(f'<section class="slide {cls}" id="{sid}" aria-label="Slide {i+1}: {title or "Title"}"><div class="inner">{head}<div class="body">{body}</div></div>{nav}</section>')

html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>IP Distribution Decision Verticals</title>
<meta name="description" content="A cost variance, breakeven and A/B testing framework for choosing how to distribute intellectual property, organized by business type.">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600&display=swap" rel="stylesheet">
<style>
:root {{ --bg:#0b1424; --panel:#111d33; --line:#22314d; --ink:#eef2f8; --ink2:#b7c2d6; --muted:#8392ad; --accent:#5aa2ff; --accent2:#f0894f; --card:#fcfcfb; }}
* {{ box-sizing:border-box; }}
html {{ scroll-behavior:smooth; scroll-snap-type:y mandatory; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font-family:Inter,system-ui,sans-serif; font-size:16px; line-height:1.5; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
.slide {{ scroll-snap-align:start; min-height:100vh; display:flex; flex-direction:column; justify-content:center; align-items:center; padding:28px 16px 64px; position:relative; border-bottom:1px solid var(--line);
  background: radial-gradient(1200px 600px at 85% -10%, rgba(90,162,255,.10), transparent 60%), var(--bg); }}
.inner {{ width:100%; max-width:1240px; }}
header .kicker {{ text-transform:uppercase; letter-spacing:.12em; font-size:12px; color:var(--accent2); font-weight:600; }}
h2 {{ font-family:Fraunces,Georgia,serif; font-weight:600; font-size:clamp(24px,3vw,36px); margin:4px 0 16px; line-height:1.15; }}
h1 {{ font-family:Fraunces,Georgia,serif; font-size:clamp(40px,7vw,84px); line-height:1.02; margin:12px 0 18px; }}
h3 {{ margin:6px 0 6px; font-size:17px; }} h4 {{ margin:4px 0; font-size:15px; }}
.hero .eyebrow {{ color:var(--accent2); font-weight:600; letter-spacing:.08em; text-transform:uppercase; font-size:13px; }}
.lede {{ font-size:clamp(16px,1.6vw,20px); color:var(--ink2); max-width:820px; }}
.lede-s {{ color:var(--ink2); font-size:15.5px; margin:12px 0 6px; max-width:1180px; }}
.note {{ margin-top:28px; color:var(--ink2); font-size:14px; border-left:3px solid var(--accent2); padding-left:12px; max-width:820px; }}
.byline {{ color:var(--muted); font-size:13px; }}
.cta {{ display:flex; gap:12px; flex-wrap:wrap; margin-top:22px; }}
.btn {{ background:var(--accent); color:#06101f; padding:10px 16px; border-radius:8px; font-weight:600; }}
.btn.ghost {{ background:transparent; color:var(--ink); border:1px solid var(--line); }}
.muted {{ color:var(--muted); font-size:13.5px; }}
.viz {{ margin:0; background:var(--card); border-radius:10px; padding:10px; }}
.viz img {{ width:100%; height:auto; display:block; max-height:58vh; object-fit:contain; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; align-items:center; }}
.two.w64 {{ grid-template-columns:1.35fr 1fr; }} .two.w55 {{ grid-template-columns:1fr 1.2fr; }}
.stack {{ display:grid; gap:10px; }} .stack .viz:first-child img {{ max-height:20vh; }} .stack .viz:last-child img {{ max-height:34vh; }}
.grid3 {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
.grid2s {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; color:var(--ink2); font-size:15px; }}
.grid5 {{ display:grid; grid-template-columns:repeat(5,1fr); gap:12px; margin:14px 0; }}
.card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; color:var(--ink2); }}
.card .big {{ font-family:Fraunces,serif; font-size:30px; color:var(--ink); }}
.vcard {{ background:var(--panel); border:1px solid var(--line); border-top:4px solid; border-radius:10px; padding:14px; color:var(--ink2); font-size:14px; }}
.vcard span {{ font-weight:700; font-size:22px; color:var(--ink); }}
.vcard.a {{ border-top-color:#2a78d6; }} .vcard.b {{ border-top-color:#eb6834; }} .vcard.c {{ border-top-color:#e87ba4; }} .vcard.d {{ border-top-color:#eda100; }} .vcard.e {{ border-top-color:#1baf7a; }}
.pill {{ display:inline-block; width:26px; height:26px; border-radius:50%; text-align:center; line-height:26px; font-weight:700; color:#06101f; }}
.pill.a {{ background:#5aa2ff; }} .pill.b {{ background:#f0894f; }} .pill.c {{ background:#e87ba4; }} .pill.d {{ background:#eda100; }} .pill.e {{ background:#1baf7a; }}
.callout {{ margin-top:18px; background:rgba(90,162,255,.08); border:1px solid rgba(90,162,255,.35); border-radius:10px; padding:14px 16px; color:var(--ink); }}
.tbl {{ width:100%; border-collapse:collapse; font-size:14.5px; background:var(--panel); border-radius:10px; overflow:hidden; }}
.tbl.sm {{ font-size:13.5px; }}
.tbl th {{ text-align:left; background:#16243f; color:var(--ink); padding:9px 12px; font-weight:600; }}
.tbl td {{ padding:8px 12px; border-top:1px solid var(--line); color:var(--ink2); vertical-align:top; }}
.tbl td b {{ color:var(--ink); }}
.tiles {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; }}
.tile {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:18px; color:var(--ink2); display:block; }}
.tile:hover {{ border-color:var(--accent); text-decoration:none; }}
.tv {{ font-family:Fraunces,serif; font-size:34px; color:var(--ink); }} .tl {{ color:var(--ink); font-weight:600; }} .td {{ font-size:14px; }} .ts {{ font-size:12px; color:var(--accent); margin-top:8px; }}
.toc {{ display:grid; grid-template-columns:1fr 1fr; gap:4px 40px; font-size:16px; }}
.toc ol {{ margin:0; padding-left:28px; }} .toc li {{ padding:3px 0; color:var(--muted); }}
.linkrow {{ display:flex; gap:20px; flex-wrap:wrap; margin-top:22px; padding-top:14px; border-top:1px solid var(--line); font-weight:600; }}
.formula {{ font-family:ui-monospace,Menlo,monospace; font-size:13px; background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:10px 12px; margin-top:12px; color:var(--ink); }}
.src {{ margin-top:10px; font-size:12px; color:var(--muted); }} .src a {{ color:#8fbfff; }}
ul {{ padding-left:20px; }} li {{ margin:4px 0; }}
.gloss {{ display:grid; grid-template-columns:240px 1fr 240px 1fr; gap:8px 16px; font-size:14px; }}
.gloss dt {{ font-weight:600; color:var(--ink); }} .gloss dd {{ margin:0; color:var(--ink2); }}
.srclist {{ columns:2; font-size:13.5px; column-gap:40px; }} .srclist li {{ break-inside:avoid; margin-bottom:6px; }} .srclist span {{ display:block; color:var(--muted); font-size:11px; word-break:break-all; }}
.snav {{ position:absolute; bottom:14px; left:50%; transform:translateX(-50%); display:flex; gap:16px; font-size:13px; align-items:center; width:min(1240px, calc(100% - 32px)); justify-content:flex-end; }}
.snav .pg {{ color:var(--muted); margin-left:auto; order:-1; }}
@media (max-width: 900px) {{
  .two, .two.w64, .two.w55, .grid3, .grid2s, .tiles, .toc {{ grid-template-columns:1fr; }}
  .grid5 {{ grid-template-columns:1fr 1fr; }} .gloss {{ grid-template-columns:1fr; }} .srclist {{ columns:1; }}
  html {{ scroll-snap-type:none; }} .tbl {{ display:block; overflow-x:auto; }}
}}
@media print {{
  @page {{ size: 13.333in 7.5in; margin:0; }}
  html {{ scroll-snap-type:none; }}
  body {{ -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  .slide {{ height:7.5in; min-height:0; page-break-after:always; break-after:page; overflow:hidden; padding:0.35in 0.45in 0.55in; justify-content:flex-start; }}
  .viz img {{ max-height:3.9in; }}
  .two .viz img {{ max-height:3.6in; }}
}}
</style></head>
<body>
{''.join(sec)}
<script>
document.addEventListener('keydown', e => {{
  if (['ArrowDown','ArrowRight','PageDown','ArrowUp','ArrowLeft','PageUp'].indexOf(e.key) < 0) return;
  const s = [...document.querySelectorAll('.slide')];
  const y = window.scrollY + 5;
  let i = s.findIndex((el, k) => el.offsetTop <= y && (k === s.length-1 || s[k+1].offsetTop > y));
  i += (['ArrowDown','ArrowRight','PageDown'].includes(e.key) ? 1 : -1);
  if (s[i]) {{ e.preventDefault(); s[i].scrollIntoView({{behavior:'smooth'}}); history.replaceState(null,'','#'+s[i].id); }}
}});
</script>
</body></html>"""
(ROOT / "docs" / "index.html").write_text(html)
print("slides:", n)
