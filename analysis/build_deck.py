"""Build the hyperlinked HTML slide deck at docs/index.html."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
import json
AS = json.load(open(ROOT / "as_of.json"))
ASOF, NEXT = AS["as_of_label"], AS["next_refresh_label"]
GH = "https://github.com/ShamarRobinson/ip-distribution-decision-verticals"
PAGES = "https://shamarrobinson.github.io/ip-distribution-decision-verticals/"
TABLEAU = "https://public.tableau.com/app/profile/shamar.robinson/viz/IPDistributionDecisionVerticals/IPDistributionDecisionVerticals"
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
    return f'<div class="src">Prices, fees and rates as of {ASOF}. Sources: ' + "; ".join(f'<a href="{S[k][1]}" target="_blank" rel="noopener">{S[k][0]}</a>' for k in keys) + "</div>"
def img(path, alt):
    return f'<figure class="viz"><img src="assets/{path}" alt="{alt}" loading="lazy"></figure>'

slides = []
def slide(sid, kicker, title, body, cls=""):
    slides.append((sid, kicker, title, body, cls))
def pageimg(name, alt):
    return f'<figure class="viz page"><img src="assets/charts/pages/{name}.svg" alt="{alt}" loading="lazy"></figure>'
XLSX = f"{GH}/raw/main/workbook/IP_Distribution_Cost_Variance_Model.xlsx"
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import methods as MT
KPIS, MPAGES = MT.build()
def msrc(keys):
    return "; ".join(f'<a href="{MT.SOURCES[k][1]}" target="_blank" rel="noopener">{MT.SOURCES[k][0]}</a>' for k in keys)

# 1 Title -----------------------------------------------------------------
slide("title", "", "", f"""
<div class="hero">
  <div class="eyebrow">Intellectual property strategy &middot; Cost variance &middot; Breakeven &middot; A/B testing</div>
  <h1>IP Distribution<br>Decision Verticals</h1>
  <p class="lede">A decision guide that helps owners of intellectual property pick how to sell their work, explained step by step for five kinds of stakeholders, using unit economics, cost variance analysis, breakeven analysis and A/B testing.</p>
  <div class="cta">
    <a class="btn" href="#contents">Start the walkthrough &rarr;</a>
    <a class="btn ghost" href="#tree-how">Jump to your decision path</a>
    <a class="btn ghost" href="{TABLEAU}" target="_blank" rel="noopener">Tableau story</a>
    <a class="btn ghost" href="{GH}" target="_blank" rel="noopener">GitHub</a>
  </div>
  <p class="note">Status note: certain works referenced by this analysis are in the initial stage of pre-publication copyright registration with the <a href="https://www.copyright.gov/registration/" target="_blank" rel="noopener">U.S. Copyright Office</a>. No title-specific details are disclosed.</p>
  <p class="byline">Prepared by Shamar Robinson &middot; Data as of {ASOF} &middot; Refreshed quarterly; next refresh {NEXT}</p>
</div>""", "title-slide")

# 2 Contents --------------------------------------------------------------
toc = [("concepts", "Concepts you will see"), ("summary", "Executive summary"), ("decision", "Who this is for"),
       ("market", "Market context in numbers"), ("market-charts", "Market charts"), ("value-chain", "The IP value chain"),
       ("options", "The options on the table"), ("unit-econ", "Unit economics"), ("variance", "Cost variance and sensitivity"),
       ("breakeven", "Breakeven analysis"), ("scale", "Crossover and scenarios"), ("cash", "Cash timing"),
       ("testing", "Pool payouts and A/B tests"), ("risks", "Contract risk register"),
       ("tree-how", "How to read the decision tree"), ("v-a", "Path A: Independent creator"), ("v-b", "Path B: Small press or imprint"),
       ("v-c", "Path C: Catalog or backlist owner"), ("v-d", "Path D: Brand, educator or corporate IP owner"), ("v-e", "Path E: Wide ebook strategist"),
       ("tree-terms", "Follow-on decisions"), ("roles", "What each team should do"), ("choices", "Options at a glance"),
       ("recommendation", "Decision request"), ("method", "Methodology"), ("kpis-1", "KPI definitions"), ("numbers", "Where each number comes from"), ("glossary", "Glossary"), ("sources", "Sources")]
half = (len(toc)+1)//2
cols = "".join('<ol start="%d">%s</ol>' % (st+1, "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in part)) for st, part in ((0, toc[:half]), (half, toc[half:])))
slide("contents", "Navigate", "Contents", f"""<div class="toc">{cols}</div>
<div class="linkrow"><a href="{TABLEAU}" target="_blank" rel="noopener">Tableau story &#8599;</a><a href="{GH}" target="_blank" rel="noopener">GitHub repository &#8599;</a>
<a href="{GH}/tree/main/data" target="_blank" rel="noopener">Data (CSV) &#8599;</a><a href="{XLSX}">Excel model &#8595;</a><a href="{PDF}" target="_blank" rel="noopener">PDF version &#8595;</a></div>""")

# 3 Concepts -------------------------------------------------------------
concepts = [
 ("Intellectual property (IP)", "Something you created that the law protects, like a book, song, course or design.", "Like owning the rights to a song you wrote: others need your permission to copy or sell it.", "Registering a copyright with the U.S. Copyright Office is what lets you enforce it in court."),
 ("Distribution channel", "A company that sells your work to buyers, such as Amazon KDP or IngramSpark.", "The stores and services between you and your buyer, the way an app store sits between developers and users.", "Every industry picks channels: apps use app stores, bands use streaming."),
 ("Gross-to-net and unit economics", "The path from the price a buyer pays to the money you keep, one sale at a time.", "A receipt showing every cut taken out of the price before you get paid.", "Pharma, consumer goods and music all track gross-to-net."),
 ("Contribution margin", "Money left from one sale after the costs of making that sale.", "What each sale adds toward paying off your launch costs.", "Restaurants and retailers price menus and products with it."),
 ("Cost variance analysis", "Explaining why one result costs more than another by splitting the gap into causes.", "Pinpointing exactly which cost made your take-home smaller than another option's.", "Finance teams use it every month to compare plan vs actual."),
 ("Breakeven analysis", "How many sales it takes to earn back what you spent to start.", "The sale that finally pays back everything you spent to launch.", "Startups, factories and new product launches all use it."),
 ("Sensitivity and scenarios", "Changing one number, or a few at once, to see what moves the result.", "Asking 'what if?' before you commit money.", "Budget planning, investment cases and infrastructure finance."),
 ("A/B testing", "Comparing two versions fairly to see which one really works better.", "Testing two video thumbnails and keeping the one more people click.", "Websites, apps and marketing teams run these daily."),
 ("Cash timing (DSO)", "How many days pass between a sale and the money reaching your bank.", "A job that pays you a month after you work the shift.", "Every business plans cash this way to pay its bills."),
 ("Pool-based payouts", "Getting paid a share of one shared pot, split by usage.", "Splitting a team's prize money by how many points each player scored.", "Music streaming royalties and ad networks pay this way."),
]
cards = "".join(f'<div class="ccard"><h4>{a}</h4><p><b>What it is:</b> {b}</p><p><b>Think of it as:</b> {c}</p><p><b>How it is used:</b> {d}</p></div>' for a, b, c, d in concepts)
slide("concepts", "Introduction", "Ten ideas you will see in this deck, explained simply", f'<div class="cgrid">{cards}</div>')

# 4 Executive summary -----------------------------------------------------
slide("summary", "Executive summary", "Three findings drive the decision", f"""
<div class="grid3">
  <div class="card"><div class="big">$6.79 vs $3.33</div><h3>The store's cut drives the gap</h3><p>On a $16.99 paperback, Amazon KDP leaves the creator $6.79 and IngramSpark's bookstore route leaves $3.33. About $2.55 of that $3.47 gap is the store's discount. <a href="#variance">See the variance</a>.</p></div>
  <div class="card"><div class="big">158 vs 272</div><h3>Payback depends on contribution per sale</h3><p>KDP earns back Year-1 costs after 158 sales of one print plus one ebook; IngramSpark needs 272. Platform fees alone are earned back within 42. <a href="#breakeven">See breakeven</a>.</p></div>
  <div class="card"><div class="big">16.6 / month</div><h3>Flat fees only win at volume</h3><p>A $13.99 monthly plan beats per-sale fees only above about 17 sales of each format a month. <a href="#scale">See the crossover</a>.</p></div>
</div>
<p class="callout"><b>Decision ask:</b> launch on two channels (KDP plus one route picked from <a href="#tree-how">your decision path</a>), keep print non-returnable at launch, and run one 90-day A/B test per quarter. <a href="#recommendation">Go to the recommendation</a>.</p>""")

# 5 Who this is for --------------------------------------------------------
slide("decision", "Stakeholders", "Who this is for: five kinds of IP owners", """
<p class="lede-s">Every IP owner faces the same question: <b>which sales channels turn a protected work into the most money kept per sale, with risk and cash timing you can live with?</b> The right answer depends on what kind of business you are, so this deck gives each type its own path.</p>
<div class="grid5">
 <a class="vcard a" href="#v-a"><span>A</span><h4>Independent creator</h4><p>One work, sold mostly on Amazon, small budget.</p></a>
 <a class="vcard b" href="#v-b"><span>B</span><h4>Small press or imprint</h4><p>Wants books on bookstore and library shelves.</p></a>
 <a class="vcard c" href="#v-c"><span>C</span><h4>Catalog or backlist owner</h4><p>Many titles that sell steadily every month.</p></a>
 <a class="vcard d" href="#v-d"><span>D</span><h4>Brand, educator or corporate IP owner</h4><p>Has its own audience: events, courses, clients, a website.</p></a>
 <a class="vcard e" href="#v-e"><span>E</span><h4>Wide ebook strategist</h4><p>Digital-first, wants readers on every store.</p></a>
</div>
<p class="muted">Also inside: guidance for finance and FP&amp;A, marketing, rights and legal, and investors (<a href="#roles">jump to roles</a>). Click a card to jump to that path.</p>""")

# 6 Market tiles -----------------------------------------------------------
tiles = [("$33.4B", "U.S. publisher revenue, 2025", "+2.5% vs 2024", "aap"), ("4.17M", "ISBNs issued in the U.S., 2025", "3.53M self-published, +38.7%", "bowker"),
         ("762.4M", "Print units sold, 2025", "+0.3% vs 2024", "circana"), ("415,780", "Copyright registrations, FY2025", "169,098 were literary works", "usco"),
         ("3.4 mo", "Average e-filed registration time", "5.3 months with correspondence", "uscotime"), ("$65 &rarr; $85", "Standard Application fee", "New fee schedule from mid-November 2026", "uscofee")]
slide("market", "Market context", "Mainstream benchmarks frame the opportunity", '<div class="tiles">' + "".join(
f'<a class="tile" href="{S[k][1]}" target="_blank" rel="noopener"><div class="tv">{v}</div><div class="tl">{l}</div><div class="td">{d}</div><div class="ts">{S[k][0]} &#8599;</div></a>' for v, l, d, k in tiles) +
'</div><p class="lede-s"><b>In plain words:</b> the number of new books jumped by about a third in 2025, but the number of printed books people bought barely moved. More creators are competing for the same readers, so the money you keep from each sale matters more every year.</p>')

slide("market-charts", "Market context", "More books, the same number of buyers", pageimg("p1_market", "ISBN output and revenue by format") + src("bowker", "aap"))

slide("value-chain", "Process flow", "The IP value chain: from protected work to cash in the bank",
img("diagrams/d1_ip_value_chain.svg", "Flowchart of the IP value chain") +
'<div class="grid2s"><p><b>Step 2 is where rights are secured.</b> Certain works covered here are in the initial stage of pre-publication copyright registration with the U.S. Copyright Office. Registration lets an owner file an infringement suit over a U.S. work and seek statutory damages, so it is counted as a launch cost ($85 under the new fee schedule).</p><p><b>In plain words:</b> you make something, protect it, give it an ID, choose formats and stores, and then money flows back to you after each store takes its share. The dashed arrow means you keep testing and adjusting.</p></div>' + src("usco", "uscofee", "uscotime"))

opt_rows = [("Amazon KDP", "60% of list minus print", "70% ($2.99 to $9.99)", "Free", "~60 days after month end", "Amazon only"),
("IngramSpark", "List minus 35 to 55% discount, print, 1.875% fee", "85% of store payout", "Free setup; own ISBN", "~90 days after month end", "Bookstores, libraries, 45,000+ outlets"),
("B&amp;N Press", "55% of list minus print", "70% flat", "Free; print ISBN free", "~30 days after month end", "BN.com (U.S.)"),
("Lulu", "Retail: 50% fee, print, then 20% commission", "Fee plus commission", "Free; proof required", "Monthly", "Own store, retail, your site"),
("PublishDrive", "Ingram network, 0% commission", "100% of store payout", "$13.99 to $83.99/mo", "Monthly", "400+ stores"),
("Draft2Digital", "Print via partners", "~90% of store payout", "$20 account fee", "Monthly, ~60-day lag", "Apple, Kobo, Google, libraries")]
slide("options", "Choice set", "Six options, three ways of charging", '<table class="tbl sm"><thead><tr><th>Platform</th><th>Print</th><th>Ebook</th><th>Fixed cost</th><th>Payment terms</th><th>Reach</th></tr></thead><tbody>' +
"".join("<tr>" + "".join(f"<td>{c}</td>" if i else f"<td><b>{c}</b></td>" for i, c in enumerate(r)) + "</tr>" for r in opt_rows) +
'</tbody></table><p class="lede-s"><b>In plain words:</b> some stores sell to buyers directly (KDP, B&amp;N), some act as a wholesaler that charges per sale (IngramSpark, Lulu, Draft2Digital), and one charges a flat monthly fee and takes nothing from each sale (PublishDrive).</p>' + src("ingram", "kdp", "bn", "lulu", "pd", "d2d", "store"))

slide("unit-econ", "Unit economics", "Gross-to-net: how much of each sale the creator keeps", pageimg("p2_unit_economics", "Gross-to-net print and ebook net per unit") + src("kdp", "ingram", "bn", "lulu", "store", "d2d"))
slide("variance", "Cost variance analysis", "Why some options pay less, and which number matters most", pageimg("p3_variance_sensitivity", "Cost variance drivers and sensitivity tornado") + src("ingram", "kdp"))
slide("breakeven", "Breakeven analysis", "How many sales it takes to earn back the start-up cost", pageimg("p4_breakeven", "Breakeven units and cumulative profit curves") +
      f'<p class="muted">Formula: breakeven sales = Year-1 fixed costs &divide; money kept per sale. The $1,500 launch budget is a placeholder; replace it with your own in the <a href="{XLSX}">Excel model</a>.</p>' + src("uscofee", "isbn", "pd"))
slide("scale", "Breakeven analysis", "When a flat fee beats a per-sale cut, and what if sales are slow or great", pageimg("p5_scale", "Crossover and scenario analysis") + src("pd", "ingram", "kdp", "bn"))
slide("cash", "Working capital", "Earning money is not the same as having it", pageimg("p6_cash", "Accrual vs cash and days to payment") + src("bn", "ingramtc", "bd", "booksby", "wwm"))
slide("testing", "Uncertainty and experiments", "Pay that moves every month, and how to test a price fairly", pageimg("p7_uncertainty_testing", "KENP pool volatility and A/B breakeven lift") + src("kenp", "wwm", "kdp"))

risks = [("Returns liability", "Returnable titles bill returns back to the IP owner; a 180-day tail applies after switching to non-returnable", "High", "Start non-returnable; test returnability later", "Sec. 5.4.5"),
("Payment timing and offsets", "Paid ~90 days after month end; can be held or offset for returns and other Ingram accounts", "Medium", "Plan cash with DSO assumptions; keep a reserve", "Sec. 8.5, 9"),
("Counterparty non-payment", "IP owner bears its share if a retailer never pays", "Low to medium", "Reconcile statements monthly", "Sec. 8.3"),
("Unilateral changes", "Terms and pricing can change; compensation changes take effect after 30 days", "Medium", "Re-run the model on each change", "Sec. 2"),
("Early release", "Enabling distribution lets orders ship before the publication date", "Medium", "Enable distribution only at launch", "Sec. 5.1.2"),
("Liability cap", "Platform liability capped at $500; broad indemnity owed by the IP owner", "Low frequency, high impact", "Confirm rights and clearances before upload", "Sec. 12, 13")]
slide("risks", "Risk register", "Contract terms that change the economics", '<table class="tbl sm"><thead><tr><th>Risk</th><th>What the agreement says</th><th>Rating</th><th>Mitigation</th><th>Reference</th></tr></thead><tbody>' +
"".join("<tr>" + "".join(f"<td>{c}</td>" if i else f"<td><b>{c}</b></td>" for i, c in enumerate(r)) + "</tr>" for r in risks) +
'</tbody></table><p class="lede-s"><b>In plain words:</b> the fine print can take money back later (returns), pay you late, or change the rules. Knowing these ahead of time is part of choosing well.</p><p class="muted">References are to the IngramSpark Agreement (last updated March 20, 2025). Plain-language business summary, not legal advice.</p>' + src("ingramtc"))

# Decision tree walkthrough ----------------------------------------------
slide("tree-how", "Decision walkthrough", "How to read the decision tree", f"""
<div class="split"><div>{img("diagrams/d2_vertical_decision_tree.svg", "Decision tree by business type")}</div>
<div class="steps"><ol>
<li><b>Start at the top diamond.</b> Ask where most of your buyers will come from: stores and online retailers, or channels you own like an email list, events or a website.</li>
<li><b>Store path:</b> if Amazon alone is enough, you land on <a href="#v-a">Path A</a>. If you need bookstores or libraries, ask how many you sell each month.</li>
<li><b>Volume check:</b> under about 17 sales of each format a month, a per-sale wholesaler is cheaper (<a href="#v-b">Path B</a>). Above it, a flat monthly plan wins (<a href="#v-c">Path C</a>).</li>
<li><b>Own-channel path:</b> if you already have an audience, sell direct and keep the store's slice (<a href="#v-d">Path D</a>). If you are ebook-first, spread across every ebook store (<a href="#v-e">Path E</a>).</li>
<li><b>Then:</b> answer the two follow-on questions on <a href="#tree-terms">exclusivity and returns</a>.</li></ol>
<p class="muted">The 17-a-month switch point comes from the <a href="#scale">crossover analysis</a>.</p></div></div>""")

V = [
 ("v-a", "A", "Independent creator", "One work, discovered mostly on Amazon, with a small budget.",
  [("$6.79", "kept per $16.99 paperback on KDP"), ("158", "sales (print + ebook) to break even"), ("$5,961", "Year-1 money kept at 50 sales a month")],
  "Amazon is where your readers already shop, and KDP keeps the biggest slice of each sale, so it pays back your start-up costs fastest. Adding bookstore distribution now would cut what you keep per book in half without a plan to get shelf space.",
  ["Publish print and ebook on KDP; price the ebook between $2.99 and $9.99 to earn 70%.", "Register the copyright before launch and budget for the $85 fee.", "Skip KDP Expanded Distribution; it keeps only $3.40 per copy."],
  ["Run a 90-day price test ($16.99 vs $14.99); keep the lower price only if sales rise more than 21%."],
  ["Watch breakeven progress monthly; when you pass 158 sales, consider adding a wide ebook route (Path E)."],
  "KDP print + ebook", "KDP + Draft2Digital for other ebook stores", "KDP + KDP Select (Kindle Unlimited)"),
 ("v-b", "B", "Small press or imprint", "A curated list that needs bookstore and library placement.",
  [("$3.33", "kept per copy at a 55% discount"), ("272", "sales to break even"), ("105 days", "average wait for IngramSpark cash")],
  "Bookstores expect a 55% discount and the right to return books, which shrinks what you keep and adds risk. In exchange you reach 45,000+ outlets that KDP cannot. KDP still handles Amazon, where it pays twice as much per copy.",
  ["Use KDP for Amazon and IngramSpark for bookstores and libraries.", "Start IngramSpark titles non-returnable; switching later leaves a 180-day return tail.", "Keep a cash reserve for the 90-day payment lag."],
  ["Test 55% returnable against 40% non-returnable; returnable must sell 77% more copies to come out ahead."],
  ["Reconcile IngramSpark statements monthly for returns and offsets; revisit Path C if any title passes 17 sales of each format a month."],
  "KDP + IngramSpark, 55% returnable", "KDP + IngramSpark, 40% non-returnable", "KDP + B&N Press + IngramSpark"),
 ("v-c", "C", "Catalog or backlist owner", "Many titles with steady monthly sales.",
  [("16.6", "sales/format/month where the flat fee wins"), ("$3,905", "Year-1 kept on PublishDrive vs $3,568 IngramSpark"), ("$21,038", "Year-1 kept at 250 sales a month")],
  "With steady volume, a flat monthly fee costs less than paying a cut on every sale. PublishDrive prints through the same Ingram network, so you keep wide reach while dropping the 1.875% per-sale fee.",
  ["Keep KDP for Amazon; move wide print and ebook distribution to a PublishDrive plan sized to your title count.", "Check each title's monthly sales against the 16.6 switch point.", "Use the Excel model to compare plan tiers ($13.99 to $83.99)."],
  ["Move half the catalog first and compare 90 days of results against titles left on IngramSpark."],
  ["Watch per-title volume each quarter; low sellers may be cheaper on a per-sale route."],
  "KDP + PublishDrive", "KDP + IngramSpark + Draft2Digital", "PublishDrive for everything"),
 ("v-d", "D", "Brand, educator or corporate IP owner", "Already has an audience: clients, students, events or a website.",
  [("$9.59", "kept per $16.99 copy sold on Lulu's own store"), ("+$2.80", "more per copy than KDP"), ("~167", "own-store sales to break even (estimate)")],
  "When you bring the buyers yourself, you do not need to give a store its slice. Selling through your own site with print-on-demand fulfillment keeps the most per copy, while KDP lets new people discover you.",
  ["Sell print copies from your own site with Lulu Direct (no revenue share; you pay printing and shipping).", "Keep KDP listed for discovery and reviews.", "Use IngramSpark Share &amp; Sell links for one-off campaigns."],
  ["Send half your audience to your own store and half to Amazon for one campaign; compare money kept per visitor."],
  ["Watch fulfillment costs and customer support load as direct sales grow."],
  "Own store (Lulu Direct) + KDP", "IngramSpark Share &amp; Sell links + KDP", "Lulu Bookstore + KDP"),
 ("v-e", "E", "Wide ebook strategist", "Digital-first and wants readers on every ebook store.",
  [("$3.49", "kept per $4.99 ebook sold direct"), ("$3.14", "kept through Draft2Digital"), ("6.1%", "monthly swing in Kindle Unlimited pay")],
  "Going direct to Apple, Kobo and B&N keeps the most, but takes more uploads. Draft2Digital trades about 35 cents a sale for one upload. Kindle Unlimited pays from a shared pot that changes monthly, so it is less predictable.",
  ["Publish the Kindle edition on KDP directly.", "Use Draft2Digital for other stores, or go direct to Apple, Kobo and B&N if you can manage several uploads.", "Price between $2.99 and $9.99 to keep KDP's 70% rate."],
  ["Test exclusivity: enroll one title in KDP Select for one 90-day term and compare to a wide title."],
  ["Plan Kindle Unlimited income as a range; above 40 ebook sales a month, compare a PublishDrive plan."],
  "KDP + direct Apple, Kobo, B&amp;N", "KDP + Draft2Digital", "KDP + PublishDrive (above 40/month)"),
]
for sid, letter, name, who, stats, summary, now, test, watch, o1, o2, o3 in V:
    chips = "".join(f'<div class="chip"><b>{a}</b><span>{b}</span></div>' for a, b in stats)
    body = f"""<div class="split">
<div>{img(f"diagrams/d2_path_{letter}.svg", f"Highlighted decision path for vertical {letter}")}
<div class="opts"><div><span>Option 1 (recommended)</span>{o1}</div><div><span>Option 2 (test arm)</span>{o2}</div><div><span>Option 3 (stretch)</span>{o3}</div></div></div>
<div class="vpanel {letter.lower()}">
<p class="who"><b>Who you are:</b> {who}</p>
<div class="chips">{chips}</div>
<h4>Summary and insight</h4><p>{summary}</p>
<h4>What to do</h4>
<ul class="todo"><li class="now"><b>Do now:</b> {'</li><li class="now"><b>Do now:</b> '.join(now)}</li>
<li class="test"><b>Test next:</b> {' '.join(test)}</li><li class="watch"><b>Watch:</b> {' '.join(watch)}</li></ul>
</div></div>"""
    slide(sid, f"Decision walkthrough &middot; Path {letter}", f"If you are {'an' if name[0] in 'AEIOU' else 'a'} {name[0].lower() + name[1:]}: here is your path", body)

slide("tree-terms", "Decision walkthrough", "Two follow-on decisions for every path: exclusivity and returns",
'<div class="two">' + img("diagrams/d3_exclusivity_tree.svg", "Exclusivity decision tree") + img("diagrams/d4_returns_discount_tree.svg", "Returns decision tree") + '</div>' +
'<div class="grid2s"><p><b>Exclusivity, in plain words:</b> Kindle Unlimited is like a library pass that pays authors from a shared pot. You must sell the ebook only on Amazon for 90 days. Choose it if your genre lives there and you can handle pay that changes monthly; otherwise stay wide. 38% of surveyed authors keep every book exclusive and 30% stay fully wide.</p>'
'<p><b>Returns, in plain words:</b> letting stores return unsold books gets you on more shelves, but you pay for the books that come back, and that bill can be bigger than what you earned. Start non-returnable unless shelf space is the main goal and you have cash set aside.</p></div>' + src("wwm", "kenp", "ingramtc"))

roles = [("Finance and FP&amp;A", "Own the model and the monthly variance review.", "Track money kept per sale vs plan by driver; forecast cash with 45 to 105 day lags; re-run breakeven when any fee changes."),
 ("Marketing", "Own price tests and where traffic goes.", "Run one A/B test per quarter with a pre-set breakeven lift; send owned audiences to the highest-margin store."),
 ("Rights and legal", "Own copyright registration and contract terms.", "Register before launch; review returns, liability and change-notice clauses; confirm all rights and clearances before upload."),
 ("Investors and partners", "Judge whether the plan pays back.", "Ask for breakeven units, margin of safety, DSO and the scenario range rather than a single sales forecast."),
 ("Operations", "Own uploads, metadata and timing.", "Turn on distribution only at launch; keep ISBNs and metadata consistent across stores; log every price change.")]
slide("roles", "Stakeholder roles", "What each team should do, whatever the path", '<table class="tbl"><thead><tr><th>Team</th><th>Their job here</th><th>What they should do</th></tr></thead><tbody>' +
"".join(f"<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>" for a, b, c in roles) + '</tbody></table>')

ch = [("A", "Independent creator", "KDP print + ebook", "KDP + Draft2Digital", "KDP + KDP Select", "158 sales"),
("B", "Small press or imprint", "KDP + IngramSpark 55% returnable", "KDP + IngramSpark 40% non-returnable", "KDP + B&amp;N Press + IngramSpark", "272 sales"),
("C", "Catalog or backlist owner", "KDP + PublishDrive", "KDP + IngramSpark + Draft2Digital", "PublishDrive only", "Switch point 16.6/month"),
("D", "Brand, educator or corporate", "Own store (Lulu Direct) + KDP", "IngramSpark Share &amp; Sell + KDP", "Lulu Bookstore + KDP", "~167 own-store sales"),
("E", "Wide ebook strategist", "KDP + direct Apple, Kobo, B&amp;N", "KDP + Draft2Digital", "KDP + PublishDrive (above 40/month)", "Ebook-only economics")]
slide("choices", "Choice options", "Options at a glance for every stakeholder type", '<table class="tbl sm"><thead><tr><th></th><th>Stakeholder</th><th>Option 1: Recommended</th><th>Option 2: Test arm</th><th>Option 3: Stretch</th><th>Breakeven marker</th></tr></thead><tbody>' +
"".join(f'<tr><td><a class="pill {r[0].lower()}" href="#v-{r[0].lower()}">{r[0]}</a></td><td><b>{r[1]}</b></td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{r[5]}</td></tr>' for r in ch) +
'</tbody></table><p class="lede-s">Option 1 keeps the most money per sale for that business type. Option 2 changes one thing and doubles as the B group in an A/B test. Option 3 adds reach once sales can support it.</p>')

slide("recommendation", "Recommendation", "Decision request: two channels now, one test every 90 days", f"""
<div class="grid3">
 <div class="card"><h3>1. Launch</h3><p>Every path lists on KDP plus the one route your <a href="#tree-how">decision path</a> picks. Keep print non-returnable at launch and turn on distribution only on release day.</p></div>
 <div class="card"><h3>2. Test</h3><p>One A/B test per 90 days: price first, then store terms. Write down the metric (money kept per visitor) and the <a href="#testing">breakeven lift</a> before starting, and do not stop early.</p></div>
 <div class="card"><h3>3. Review</h3><p>Hold a monthly variance review and a quarterly re-forecast. Revisit exclusivity and subscriptions once sales pass 17 of each format a month.</p></div>
</div>
{img("diagrams/d5_ab_test_flow.svg", "A/B test workflow")}
<p class="callout"><b>Success measures:</b> breakeven reached within the planned number of sales; money kept per sale within 5% of plan; cash received within the modeled wait; one decision-grade A/B result per quarter.</p>""")

slide("method", "Methodology", "How the numbers were built", f"""
<div class="grid2s">
<div><h4>Model</h4><ul>
<li>One Python model (<a href="{GH}/blob/main/analysis/model.py">analysis/model.py</a>) writes every dataset in <a href="{GH}/tree/main/data">/data</a>; the deck, Excel model and Tableau story read the same numbers.</li>
<li>Base case: $16.99 paperback, 200 pages, $4.99 ebook (2 MB), equal sales per platform.</li>
<li>Variance = platform's money kept minus KDP's, split into store share, production and fee drivers that add up exactly.</li>
<li>A/B sample sizes use a two-proportion z-test (95% confidence, 80% power).</li></ul></div>
<div><h4>Assumptions to replace</h4><ul>
<li>Print costs for IngramSpark ($4.00), B&amp;N Press ($3.50) and Lulu ($5.00) are planning estimates.</li>
<li>The $1,500 launch budget, the 65/35 channel mix, the launch-decay curve and Path D's own-store breakeven are illustrative.</li>
<li>All prices, fees and rates are as of {ASOF}. The data is refreshed every three months; next refresh {NEXT}.</li>
<li>Status note: certain works referenced are in the initial stage of pre-publication copyright registration with the U.S. Copyright Office.</li></ul></div>
</div>""")

def kpi_table(rows):
    return ('<table class="tbl xs"><thead><tr><th>KPI</th><th>What it tells you</th><th>Formula</th><th>Worked example</th></tr></thead><tbody>'
            + "".join(f"<tr><td><b>{r['kpi']}</b><br><span class='muted'>{r['full']}</span></td><td>{r['meaning']}</td><td>{r['formula']}</td><td>{r['worked']}</td></tr>" for r in rows)
            + "</tbody></table>")
slide("kpis-1", "How the numbers work", "KPI (key performance indicator) definitions, part 1: money kept per sale",
      kpi_table(KPIS[:7]) + f'<div class="src">Worked with the {ASOF} numbers. {MT.ROUNDING} Sources: ' + msrc(["kdp", "ingram", "bn", "lulu", "pd", "uscofee", "isbn", "model"]) + "</div>")
slide("kpis-2", "How the numbers work", "KPI definitions, part 2: scale, cash timing and testing",
      kpi_table(KPIS[7:]) + f'<div class="src">Worked with the {ASOF} numbers. {MT.ROUNDING} Sources: ' + msrc(["pd", "ingram", "d2d", "bn", "ingramtc", "bd", "booksby", "wwm", "kenp", "kdp", "model"]) + "</div>")
slide("numbers", "How the numbers work", "Where each number in the story comes from",
      '<table class="tbl xs"><thead><tr><th>Story point</th><th>Numbers shown</th><th>How they are calculated</th><th>Sources</th></tr></thead><tbody>'
      + "".join((f"<tr><td><b>{MT.PAGE_NO[r['dash']]}. {r['page']}</b></td><td>{r['numbers']}</td><td>{r['calc']}</td><td>{msrc(r['sources'])}</td></tr>"
                 + (f"<tr><td><b>10. Profit calculator</b></td><td>Profit, breakeven books, books still needed, share of costs earned back</td><td>Profit = books sold x money kept per print + ebook pair, minus launch costs (your launch budget plus the route's setup fees, copyright registration and year-1 subscription); breakeven = launch costs / money kept per pair. Uses the same per-sale numbers as points 5 to 9.</td><td>{msrc(['model'])}</td></tr>" if MT.PAGE_NO[r['dash']] == 9 else ""))
                for r in sorted(MPAGES, key=lambda r: MT.PAGE_NO[r["dash"]]))
      + f'</tbody></table><div class="src">Story point numbers match the <a href="{TABLEAU}" target="_blank" rel="noopener">Tableau story</a>. Every formula is also listed in the <a href="{GH}#how-the-numbers-work-kpis-and-calculations" target="_blank" rel="noopener">How the numbers work</a> section on GitHub.</div>')

gl = [("A/B test", "A fair comparison of two versions on one measure, run long enough to trust the result."),
("Breakeven lift", "How many more sales a cheaper option needs just to match the original."),
("Breakeven point", "Sales at which total money kept equals start-up costs."),
("Channel share / take rate", "The part of the price the store or marketplace keeps."),
("Coefficient of variation (CV)", "How much something swings, compared to its average."),
("Contribution margin", "Money kept from one sale after that sale's own costs."),
("Cost variance analysis", "Explaining a cost gap by splitting it into its causes."),
("Days sales outstanding (DSO)", "Average days between a sale and the cash arriving."),
("Gross-to-net (GTN)", "The steps from list price to the money you keep."),
("Margin of safety", "How far sales can drop before you stop covering costs."),
("Pool-based payout", "Pay that comes from a shared pot split by usage."),
("Returns reserve", "Money held back to cover books that may be returned."),
("Scenario analysis", "Comparing results under slow, normal and great outcomes."),
("Sensitivity analysis", "Changing one input at a time to see which matters most."),
("Working capital gap", "Money earned but not yet collected.")]
slide("glossary", "Reference", "Glossary of analytics and FP&amp;A terms", '<dl class="gloss">' + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in gl) + "</dl>")

order = ["aap", "bowker", "circana", "usco", "uscotime", "uscofee", "ingram", "ingramtc", "jf", "kdp", "kdped", "bn", "bd", "lulu", "pd", "d2d", "booksby", "store", "isbn", "tortora", "wwm", "kenp"]
slide("sources", "Attribution", "Sources", '<ol class="srclist">' + "".join(f'<li><a href="{S[k][1]}" target="_blank" rel="noopener">{S[k][0]}</a></li>' for k in order) +
f'</ol><p class="muted">Mainstream industry and government sources (AAP, Bowker, Circana BookScan, U.S. Copyright Office) frame the market; platform help centers and agreements set the rates. Prices, fees and rates are as of {ASOF} and are refreshed quarterly (next: {NEXT}).</p>')

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
           + f'<span class="pg">{i+1} / {n} &middot; Data as of {ASOF}</span></nav>')
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
.viz.page img {{ max-height:72vh; }}
.cgrid {{ display:grid; grid-template-columns:repeat(5,1fr); gap:10px; }}
.ccard {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:11px 12px; font-size:12.4px; color:var(--ink2); line-height:1.4; }}
.ccard h4 {{ color:var(--ink); font-size:14px; margin:0 0 6px; }} .ccard p {{ margin:4px 0; }} .ccard b {{ color:#f0b98f; font-weight:600; }}
.split {{ display:grid; grid-template-columns:1.08fr 1fr; gap:18px; align-items:start; }}
.split .viz img {{ max-height:46vh; }}
.steps ol {{ padding-left:20px; color:var(--ink2); font-size:15px; }} .steps li {{ margin:8px 0; }} .steps b {{ color:var(--ink); }}
.vpanel {{ background:var(--panel); border:1px solid var(--line); border-top:4px solid; border-radius:12px; padding:14px 16px; color:var(--ink2); font-size:14px; }}
.vpanel.a {{ border-top-color:#2a78d6; }} .vpanel.b {{ border-top-color:#eb6834; }} .vpanel.c {{ border-top-color:#e87ba4; }} .vpanel.d {{ border-top-color:#eda100; }} .vpanel.e {{ border-top-color:#1baf7a; }}
.vpanel h4 {{ color:var(--ink); margin:10px 0 4px; font-size:14.5px; }} .vpanel p {{ margin:4px 0; }} .who b {{ color:var(--ink); }}
.chips {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:8px 0; }}
.chip {{ background:#0e1930; border:1px solid var(--line); border-radius:8px; padding:8px; }} .chip b {{ display:block; font-family:Fraunces,serif; font-size:22px; color:var(--ink); }} .chip span {{ font-size:12px; }}
.todo {{ list-style:none; padding:0; margin:4px 0; }} .todo li {{ padding:5px 8px; border-left:3px solid; margin:5px 0; background:#0e1930; border-radius:4px; }}
.todo .now {{ border-color:#5aa2ff; }} .todo .test {{ border-color:#c59bff; }} .todo .watch {{ border-color:#f0894f; }} .todo b {{ color:var(--ink); }}
.opts {{ display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-top:10px; font-size:13px; color:var(--ink); }}
.opts div {{ background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:8px; }} .opts span {{ display:block; font-size:11px; color:var(--muted); text-transform:uppercase; letter-spacing:.05em; margin-bottom:3px; }}
a.vcard {{ text-decoration:none; }} a.vcard:hover {{ border-color:var(--accent); }} a.pill {{ text-decoration:none; }}
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
.tbl.xs {{ font-size:11.5px; line-height:1.3; }} .tbl.xs td, .tbl.xs th {{ padding:5px 8px; }}
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
  .cgrid, .split, .chips, .opts {{ grid-template-columns:1fr; }}
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
  .viz.page img {{ max-height:5.6in; }}
  .split .viz img {{ max-height:3.0in; }}
  .ccard {{ font-size:10.5px; padding:7px 9px; }}
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
