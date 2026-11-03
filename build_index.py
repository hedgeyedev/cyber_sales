#!/usr/bin/env python3
"""Build the landing page (index.html) for the SharePoint Cyber folder: headline, same-day-vs-prior-years table,
cumulative revenue curves (Chart.js inlined). Aggregates only; reads cache/*/YEAR/recurring_payments_YEAR.json.

Usage: python3 build_index.py OUT.html [YEAR]
"""
import json, sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent


def load(year):
    for kind in ("current", "historical"):
        f = HERE / "cache" / kind / str(year) / f"recurring_payments_{year}.json"
        if f.exists():
            return json.load(open(f))
    return None


def daily(data, year):
    """{day_of_nov: [payments, revenue, cyber_payments, cyber_revenue]} for Nov 1..30, categorised as cyber_<year>."""
    out = defaultdict(lambda: [0, 0.0, 0, 0.0])
    for p in data["payments"]:
        if not p["date"].startswith(f"{year}-11-"):
            continue
        d = int(p["date"][-2:])
        out[d][0] += 1
        out[d][1] += p["amount"]
        if p.get("payment_category") == f"cyber_{year}":
            out[d][2] += 1
            out[d][3] += p["amount"]
    return out


def cum(days, idx, upto):
    tot, res = 0, []
    for d in range(1, upto + 1):
        tot += days[d][idx] if d in days else 0
        res.append(round(tot, 2))
    return res


def money(x):
    return f"${x/1e6:.2f}M" if x >= 1e6 else f"${x/1e3:,.0f}K"


def pct(a, b):
    return "n/a" if not b else f"{(a-b)/b*100:+.0f}%"


def build(out, year):
    years = [y for y in range(2020, year + 1) if load(y)]
    D = {y: daily(load(y), y) for y in years}
    cur = load(year)
    gen = datetime.fromisoformat(cur["generated_at"])
    last_day = max(1, gen.day - 1) if gen.month == 11 else 30  # last COMPLETE day: today is partial at 6 AM
    as_of = gen.strftime("%b %-d, %Y %-I:%M %p ET")
    prior = [y for y in years if y != year]
    rows = []
    for y in reversed(years):
        c = [sum(D[y][d][i] for d in range(1, last_day + 1) if d in D[y]) for i in range(4)]
        rows.append((y, c))
    cy = dict(rows)[year]
    p1 = dict(rows).get(year - 1)

    def cell(v, money_=False):
        return money(v) if money_ else f"{int(v):,}"

    trs = ""
    for y, c in rows:
        b = ' style="font-weight:700;background:#eef3fb"' if y == year else ""
        trs += (f"<tr{b}><td>{y}</td><td>{cell(c[0])}</td><td>{cell(c[1], True)}</td>"
                f"<td>{cell(c[2])}</td><td>{cell(c[3], True)}</td>"
                f"<td>{pct(cy[3], c[3]) if y != year else ''}</td></tr>")
    colors = ["#9aa5b1", "#8fb4e3", "#6c8ebf", "#f2a65a", "#7fc8a9", "#d98880", "#2c5aa0"]
    ds_total, ds_cyber = [], []
    for i, y in enumerate(years):
        n = last_day if y == year else 30
        for lst, idx in ((ds_total, 1), (ds_cyber, 3)):
            lst.append({"label": str(y), "data": cum(D[y], idx, n), "borderColor": colors[i % 7],
                        "borderWidth": 4 if y == year else 1.5, "pointRadius": 0, "tension": 0.2})
    labels = list(range(1, 31))
    chart_js = (HERE / "vendor" / "chart.umd.js").read_text()
    delta = f"{pct(cy[3], p1[3])} vs {year-1}" if p1 else ""
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Cyber {year} Sales Reports</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{{font:15px/1.5 -apple-system,Segoe UI,sans-serif;margin:0;background:#f8f9fa;color:#222}}
.bar{{background:#2c5aa0;color:#fff;padding:10px 20px}} main{{max-width:1000px;margin:0 auto;padding:20px}}
.cards{{display:flex;gap:14px;flex-wrap:wrap}} .card{{background:#fff;border-radius:8px;padding:14px 18px;flex:1;min-width:200px;box-shadow:0 1px 3px #0002}}
.big{{font-size:28px;font-weight:700;color:#2c5aa0}} table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{padding:8px 12px;border-bottom:1px solid #e3e6ea;text-align:right}} td:first-child,th:first-child{{text-align:left}}
h2{{margin-top:32px}} .note{{color:#666;font-size:13px}} a{{color:#2c5aa0}} .links li{{margin:6px 0}}
.chart{{background:#fff;border-radius:8px;padding:12px;margin:12px 0}}</style></head><body>
<div class="bar"><strong>Cyber {year} Sales Reports</strong> &middot; Data as of {as_of} &middot; refreshed nightly at 6 AM ET</div>
<main>
<p>How Cyber November {year} is tracking against prior years, same days only (Nov 1 to Nov {last_day}).
Figures are <b>recurring payments</b> (renewals and promo-priced subscriptions processed in billing), not total company sales.</p>
<div class="cards">
<div class="card"><div class="note">Cyber {year} revenue, Nov 1-{last_day}</div><div class="big">{money(cy[3])}</div><div>{delta}</div></div>
<div class="card"><div class="note">Cyber {year} payments</div><div class="big">{int(cy[2]):,}</div><div>{pct(cy[2], p1[2]) + f' vs {year-1}' if p1 else ''}</div></div>
<div class="card"><div class="note">All recurring revenue, Nov 1-{last_day}</div><div class="big">{money(cy[1])}</div><div>{pct(cy[1], p1[1]) + f' vs {year-1}' if p1 else ''}</div></div>
</div>
<h2>Same days, every year (Nov 1 to Nov {last_day})</h2>
<table><tr><th>Year</th><th>All payments</th><th>All revenue</th><th>Cyber payments</th><th>Cyber revenue</th><th>{year} Cyber vs this year</th></tr>{trs}</table>
<p class="note">"Cyber" = payments on that year's Cyber SKUs/plan pricings. Last column: how {year} Cyber revenue compares to that year's at the same point.</p>
<h2>Cumulative Cyber revenue by day of November</h2><div class="chart"><canvas id="c2" height="110"></canvas></div>
<h2>Cumulative all recurring revenue by day of November</h2><div class="chart"><canvas id="c1" height="110"></canvas></div>
<h2>Reports</h2><ul class="links">
<li><a href="Cyber-{year}-vs-prior-years.html">{year} vs prior years</a>: cohorts, retention, net revenue retention, revenue trends</li>
<li><a href="Year-{year}-SKU-detail.html">{year} SKU detail</a>: every SKU, payments and revenue</li>
<li><a href="Hourly-{year}.html">{year} hourly</a>: when payments land through the day</li></ul>
<p class="note">Each report shows its own Data-as-of banner. If the date above is more than a day old, the nightly refresh did not run and this is the last good copy.</p>
</main><script>{chart_js}</script><script>
const L={json.dumps(labels)};
function mk(id,ds){{new Chart(document.getElementById(id),{{type:'line',data:{{labels:L,datasets:ds}},options:{{
 interaction:{{mode:'index',intersect:false}},scales:{{x:{{title:{{display:true,text:'Day of November'}}}},
 y:{{ticks:{{callback:v=>'$'+(v/1e6>=1?(v/1e6).toFixed(1)+'M':(v/1e3).toFixed(0)+'K')}}}}}}}}}});}}
mk('c1',{json.dumps(ds_total)});mk('c2',{json.dumps(ds_cyber)});</script></body></html>"""
    Path(out).write_text(html)
    print(f"wrote {out}: through Nov {last_day}, as of {as_of}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    build(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else datetime.now().year)
