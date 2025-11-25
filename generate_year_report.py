#!/usr/bin/env python3
"""
Generate Individual Year Deep-Dive Report

Creates detailed SKU-level analysis for a specific year showing:
- All SKUs with payment counts and revenue
- Cyber New vs Cyber Old breakdown
- Cohort analysis for Cyber Old payments
- Top performers and trends

Usage: python3 generate_year_report.py 2024
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
import re


def find_data_file(year):
    """Find the JSON data file for a given year."""
    year_str = str(year)

    # Check cache/historical first
    historical_path = Path(f"cache/historical/{year_str}/recurring_payments_{year_str}.json")
    if historical_path.exists():
        return historical_path

    # Check cache/current
    current_path = Path(f"cache/current/{year_str}/recurring_payments_{year_str}.json")
    if current_path.exists():
        return current_path

    # Check root directory
    root_path = Path(f"recurring_payments_{year_str}.json")
    if root_path.exists():
        return root_path

    return None


def extract_cohort_from_sku(sku):
    """Extract cohort year from SKU string."""
    if not sku:
        return None

    match = re.search(r'cyber_(\d{4})', sku)
    if match:
        return int(match.group(1))

    return None


def analyze_year_data(year):
    """Analyze payment data for a specific year."""
    file_path = find_data_file(year)
    if not file_path:
        print(f"✗ Error: No data file found for {year}")
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    payments = data['payments']
    cyber_current_category = f'cyber_{year}'

    # Organize by SKU
    sku_data = defaultdict(lambda: {
        'count': 0,
        'revenue': 0,
        'category': None,
        'payments': []
    })

    # Track cohort breakdown for Cyber Old
    cohort_breakdown = defaultdict(lambda: {
        'count': 0,
        'revenue': 0,
        'skus': defaultdict(lambda: {'count': 0, 'revenue': 0})
    })

    for payment in payments:
        sku = payment.get('sku', 'Unknown')
        category = payment.get('payment_category', 'normal')
        amount = payment['amount']

        sku_data[sku]['count'] += 1
        sku_data[sku]['revenue'] += amount
        sku_data[sku]['category'] = category
        sku_data[sku]['payments'].append(payment)

        # Track cohort for Cyber Old
        if category == 'cyber_old':
            cohort_year = extract_cohort_from_sku(sku)
            if cohort_year:
                cohort_breakdown[cohort_year]['count'] += 1
                cohort_breakdown[cohort_year]['revenue'] += amount
                cohort_breakdown[cohort_year]['skus'][sku]['count'] += 1
                cohort_breakdown[cohort_year]['skus'][sku]['revenue'] += amount

    # Categorize SKUs
    cyber_new_skus = {k: v for k, v in sku_data.items() if v['category'] == cyber_current_category}
    cyber_old_skus = {k: v for k, v in sku_data.items() if v['category'] == 'cyber_old'}
    normal_skus = {k: v for k, v in sku_data.items() if v['category'] == 'normal'}

    return {
        'year': year,
        'total_payments': data['total_payments'],
        'total_revenue': data['total_revenue'],
        'cyber_new_skus': cyber_new_skus,
        'cyber_old_skus': cyber_old_skus,
        'normal_skus': normal_skus,
        'cohort_breakdown': dict(cohort_breakdown),
        'data': data
    }


def generate_html_report(analysis, output_file):
    """Generate HTML report for year analysis."""
    year = analysis['year']

    # Calculate totals
    cyber_new_total = sum(s['revenue'] for s in analysis['cyber_new_skus'].values())
    cyber_new_count = sum(s['count'] for s in analysis['cyber_new_skus'].values())

    cyber_old_total = sum(s['revenue'] for s in analysis['cyber_old_skus'].values())
    cyber_old_count = sum(s['count'] for s in analysis['cyber_old_skus'].values())

    normal_total = sum(s['revenue'] for s in analysis['normal_skus'].values())
    normal_count = sum(s['count'] for s in analysis['normal_skus'].values())

    # Sort SKUs by revenue
    cyber_new_sorted = sorted(analysis['cyber_new_skus'].items(), key=lambda x: x[1]['revenue'], reverse=True)
    cyber_old_sorted = sorted(analysis['cyber_old_skus'].items(), key=lambda x: x[1]['revenue'], reverse=True)
    normal_sorted = sorted(analysis['normal_skus'].items(), key=lambda x: x[1]['revenue'], reverse=True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>November {year} - Detailed SKU Analysis</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #2c5aa0;
            padding-bottom: 15px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 25px 0;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-card h3 {{
            color: #666;
            font-size: 14px;
            margin: 0 0 10px 0;
        }}
        .summary-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #2c5aa0;
        }}
        .summary-card .sub {{
            font-size: 13px;
            color: #888;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #2c5aa0;
            margin-top: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .nav {{
            margin-bottom: 20px;
        }}
        .nav a {{
            color: #2c5aa0;
            text-decoration: none;
            font-size: 14px;
        }}
        .nav a:hover {{
            text-decoration: underline;
        }}
        .positive {{
            color: #28a745;
            font-weight: 600;
        }}
        .cohort-badge {{
            background: #e3f2fd;
            color: #2c5aa0;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="nav">
        <a href="index.html">← Back to Reports</a>
    </div>

    <h1>November {year} - Detailed Analysis</h1>

    <div class="summary">
        <div class="summary-card">
            <h3>Total Revenue</h3>
            <div class="value">${analysis['total_revenue']/1000000:.2f}M</div>
            <div class="sub">{analysis['total_payments']:,} payments</div>
        </div>
        <div class="summary-card">
            <h3>Cyber New</h3>
            <div class="value">${cyber_new_total/1000000:.2f}M</div>
            <div class="sub">{cyber_new_count:,} payments • {len(analysis['cyber_new_skus'])} SKUs</div>
        </div>
        <div class="summary-card">
            <h3>Cyber Old</h3>
            <div class="value">${cyber_old_total/1000000:.2f}M</div>
            <div class="sub">{cyber_old_count:,} payments • {len(analysis['cyber_old_skus'])} SKUs</div>
        </div>
        <div class="summary-card">
            <h3>Normal</h3>
            <div class="value">${normal_total/1000:.0f}K</div>
            <div class="sub">{normal_count:,} payments • {len(analysis['normal_skus'])} SKUs</div>
        </div>
    </div>
"""

    # Cyber New SKUs Section
    if cyber_new_sorted:
        html += f"""
    <div class="section">
        <h2>Cyber New SKUs ({len(cyber_new_sorted)} SKUs)</h2>
        <table>
            <thead>
                <tr>
                    <th>SKU</th>
                    <th style="text-align: right;">Payments</th>
                    <th style="text-align: right;">Revenue</th>
                    <th style="text-align: right;">Avg Price</th>
                    <th style="text-align: right;">% of Cyber New</th>
                </tr>
            </thead>
            <tbody>
"""
        for sku, data in cyber_new_sorted:
            pct = (data['revenue'] / cyber_new_total * 100) if cyber_new_total > 0 else 0
            avg = data['revenue'] / data['count'] if data['count'] > 0 else 0
            html += f"""
                <tr>
                    <td>{sku}</td>
                    <td style="text-align: right;">{data['count']:,}</td>
                    <td style="text-align: right;">${data['revenue']:,.2f}</td>
                    <td style="text-align: right;">${avg:.2f}</td>
                    <td style="text-align: right;">{pct:.1f}%</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

    # Cyber Old - Cohort Breakdown
    if analysis['cohort_breakdown']:
        html += """
    <div class="section">
        <h2>Cyber Old - Cohort Breakdown</h2>
        <p style="color: #666; margin-bottom: 20px;">
            Shows which cohorts (originating year) contributed to this year's Cyber Old revenue.
        </p>
        <table>
            <thead>
                <tr>
                    <th>Cohort Year</th>
                    <th style="text-align: right;">Payments</th>
                    <th style="text-align: right;">Revenue</th>
                    <th style="text-align: right;">% of Cyber Old</th>
                    <th style="text-align: right;">Unique SKUs</th>
                </tr>
            </thead>
            <tbody>
"""
        cohort_sorted = sorted(analysis['cohort_breakdown'].items(), key=lambda x: x[0])
        for cohort_year, cohort_data in cohort_sorted:
            pct = (cohort_data['revenue'] / cyber_old_total * 100) if cyber_old_total > 0 else 0
            html += f"""
                <tr>
                    <td><span class="cohort-badge">{cohort_year} Cohort</span></td>
                    <td style="text-align: right;">{cohort_data['count']:,}</td>
                    <td style="text-align: right;">${cohort_data['revenue']:,.2f}</td>
                    <td style="text-align: right;">{pct:.1f}%</td>
                    <td style="text-align: right;">{len(cohort_data['skus'])}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

    # Cyber Old SKUs Section
    if cyber_old_sorted:
        html += f"""
    <div class="section">
        <h2>Cyber Old SKUs - All ({len(cyber_old_sorted)} SKUs)</h2>
        <table>
            <thead>
                <tr>
                    <th>SKU</th>
                    <th>Cohort</th>
                    <th style="text-align: right;">Payments</th>
                    <th style="text-align: right;">Revenue</th>
                    <th style="text-align: right;">Avg Price</th>
                    <th style="text-align: right;">% of Cyber Old</th>
                </tr>
            </thead>
            <tbody>
"""
        for sku, data in cyber_old_sorted:
            pct = (data['revenue'] / cyber_old_total * 100) if cyber_old_total > 0 else 0
            avg = data['revenue'] / data['count'] if data['count'] > 0 else 0
            cohort = extract_cohort_from_sku(sku)
            cohort_display = f'<span class="cohort-badge">{cohort}</span>' if cohort else '—'
            html += f"""
                <tr>
                    <td>{sku}</td>
                    <td>{cohort_display}</td>
                    <td style="text-align: right;">{data['count']:,}</td>
                    <td style="text-align: right;">${data['revenue']:,.2f}</td>
                    <td style="text-align: right;">${avg:.2f}</td>
                    <td style="text-align: right;">{pct:.1f}%</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

    # Normal SKUs Section (if any)
    if normal_sorted:
        html += f"""
    <div class="section">
        <h2>Normal SKUs ({len(normal_sorted)} SKUs)</h2>
        <table>
            <thead>
                <tr>
                    <th>SKU</th>
                    <th style="text-align: right;">Payments</th>
                    <th style="text-align: right;">Revenue</th>
                    <th style="text-align: right;">Avg Price</th>
                </tr>
            </thead>
            <tbody>
"""
        for sku, data in normal_sorted:
            avg = data['revenue'] / data['count'] if data['count'] > 0 else 0
            html += f"""
                <tr>
                    <td>{sku}</td>
                    <td style="text-align: right;">{data['count']:,}</td>
                    <td style="text-align: right;">${data['revenue']:,.2f}</td>
                    <td style="text-align: right;">${avg:.2f}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

    html += """
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"✓ Generated {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_year_report.py <year>")
        print("Example: python3 generate_year_report.py 2024")
        sys.exit(1)

    year = int(sys.argv[1])

    print(f"Generating detailed report for {year}...")
    analysis = analyze_year_data(year)

    if not analysis:
        sys.exit(1)

    output_file = f"year_{year}_detail.html"
    generate_html_report(analysis, output_file)

    print(f"\n✓ Report ready: {output_file}")
    print(f"  Total Revenue: ${analysis['total_revenue']:,.2f}")
    print(f"  Cyber New SKUs: {len(analysis['cyber_new_skus'])}")
    print(f"  Cyber Old SKUs: {len(analysis['cyber_old_skus'])}")
    print(f"  Cohorts: {len(analysis['cohort_breakdown'])}")


if __name__ == '__main__':
    main()
