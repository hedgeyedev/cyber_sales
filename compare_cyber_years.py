#!/usr/bin/env python3
"""
Compare Cyber November performance across multiple years.
Generates a side-by-side comparison HTML report.
"""

import json
import sys
from pathlib import Path


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

    # Check root directory (for backwards compatibility)
    root_path = Path(f"recurring_payments_{year_str}.json")
    if root_path.exists():
        return root_path

    return None


def load_year_data(year):
    """Load data for a specific year."""
    json_file = find_data_file(year)
    if json_file is None:
        print(f"Warning: Data for {year} not found in cache/historical, cache/current, or current directory, skipping year {year}")
        return None

    try:
        with open(json_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {json_file} not found, skipping year {year}")
        return None


def calculate_stats(data):
    """Calculate key stats for a year."""
    payments = data['payments']

    cyber_2025 = [p for p in payments if p.get('payment_category') == 'cyber_2025']
    cyber_old = [p for p in payments if p.get('payment_category') == 'cyber_old']
    normal = [p for p in payments if p.get('payment_category') == 'normal']

    total_revenue = sum(p['amount'] for p in payments)
    cyber_2025_revenue = sum(p['amount'] for p in cyber_2025)
    cyber_old_revenue = sum(p['amount'] for p in cyber_old)
    normal_revenue = sum(p['amount'] for p in normal)

    return {
        'total_count': len(payments),
        'total_revenue': total_revenue,
        'avg_payment': total_revenue / len(payments) if payments else 0,
        'cyber_2025_count': len(cyber_2025),
        'cyber_2025_revenue': cyber_2025_revenue,
        'cyber_2025_pct': (cyber_2025_revenue / total_revenue * 100) if total_revenue > 0 else 0,
        'cyber_old_count': len(cyber_old),
        'cyber_old_revenue': cyber_old_revenue,
        'cyber_old_pct': (cyber_old_revenue / total_revenue * 100) if total_revenue > 0 else 0,
        'normal_count': len(normal),
        'normal_revenue': normal_revenue,
        'normal_pct': (normal_revenue / total_revenue * 100) if total_revenue > 0 else 0,
    }


def generate_comparison_html(years_data, output_file='cyber_november_comparison.html'):
    """Generate HTML comparison report."""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber November Year-over-Year Comparison</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .comparison-table {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #e0e0e0;
        }
        th:first-child, td:first-child {
            text-align: left;
            font-weight: 600;
        }
        th {
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .growth-positive {
            color: #28a745;
        }
        .growth-negative {
            color: #dc3545;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        canvas {
            max-height: 400px;
        }
    </style>
</head>
<body>
    <h1>Cyber November Year-over-Year Comparison</h1>
"""

    # Build comparison table
    html += '<div class="comparison-table"><h2>Revenue Comparison</h2><table><thead><tr><th>Metric</th>'

    years = sorted(years_data.keys())
    for year in years:
        html += f'<th>Nov {year}</th>'
    html += '</tr></thead><tbody>'

    # Total Revenue
    html += '<tr><td>Total Revenue</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>${stats["total_revenue"]:,.0f}</td>'
    html += '</tr>'

    # Total Payments
    html += '<tr><td>Total Payments</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>{stats["total_count"]:,}</td>'
    html += '</tr>'

    # Avg Payment
    html += '<tr><td>Avg Payment</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>${stats["avg_payment"]:,.2f}</td>'
    html += '</tr>'

    # Cyber Current Year
    html += '<tr><td><strong>Cyber Current Year Revenue</strong></td>'
    for year in years:
        stats = years_data[year]
        html += f'<td><strong>${stats["cyber_2025_revenue"]:,.0f}</strong> ({stats["cyber_2025_pct"]:.1f}%)</td>'
    html += '</tr>'

    html += '<tr><td>Cyber Current Year Payments</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>{stats["cyber_2025_count"]:,}</td>'
    html += '</tr>'

    # Cyber Old
    html += '<tr><td>Cyber Old Revenue</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>${stats["cyber_old_revenue"]:,.0f} ({stats["cyber_old_pct"]:.1f}%)</td>'
    html += '</tr>'

    # Normal
    html += '<tr><td>Normal Revenue</td>'
    for year in years:
        stats = years_data[year]
        html += f'<td>${stats["normal_revenue"]:,.0f} ({stats["normal_pct"]:.1f}%)</td>'
    html += '</tr>'

    html += '</tbody></table></div>'

    # Add chart
    html += '<div class="chart-container"><h2>Revenue Comparison Chart</h2><canvas id="comparisonChart"></canvas></div>'

    # JavaScript for chart
    html += '<script>'
    html += f'const years = {json.dumps(years)};'
    html += f'const totalRevenue = {json.dumps([years_data[y]["total_revenue"] for y in years])};'
    html += f'const cyberCurrentRevenue = {json.dumps([years_data[y]["cyber_2025_revenue"] for y in years])};'
    html += f'const cyberOldRevenue = {json.dumps([years_data[y]["cyber_old_revenue"] for y in years])};'
    html += f'const normalRevenue = {json.dumps([years_data[y]["normal_revenue"] for y in years])};'

    html += """
new Chart(document.getElementById('comparisonChart'), {
    type: 'bar',
    data: {
        labels: years,
        datasets: [
            {
                label: 'Cyber Current Year',
                data: cyberCurrentRevenue,
                backgroundColor: 'rgba(44, 90, 160, 0.8)'
            },
            {
                label: 'Cyber Old',
                data: cyberOldRevenue,
                backgroundColor: 'rgba(100, 140, 200, 0.8)'
            },
            {
                label: 'Normal',
                data: normalRevenue,
                backgroundColor: 'rgba(255, 159, 64, 0.8)'
            }
        ]
    },
    options: {
        responsive: true,
        scales: {
            x: { stacked: true },
            y: {
                stacked: true,
                ticks: {
                    callback: function(value) {
                        return '$' + value.toLocaleString();
                    }
                }
            }
        }
    }
});
</script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"\n✓ Generated {output_file}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compare_cyber_years.py 2023 2024 2025")
        sys.exit(1)

    years = [int(y) for y in sys.argv[1:]]

    print(f"\nLoading data for years: {years}")

    years_data = {}
    for year in years:
        data = load_year_data(year)
        if data:
            years_data[year] = calculate_stats(data)
            print(f"  ✓ {year}: {years_data[year]['total_count']:,} payments, ${years_data[year]['total_revenue']:,.0f}")

    if not years_data:
        print("\nERROR: No data files found!")
        sys.exit(1)

    # Generate output filename based on years
    sorted_years = sorted(years_data.keys())
    if len(sorted_years) == 2:
        output_file = f"cyber_november_comparison_{sorted_years[0]}_{sorted_years[1]}.html"
    else:
        first_year = sorted_years[0]
        last_year = sorted_years[-1]
        output_file = f"cyber_november_comparison_{first_year}_{last_year}.html"

    generate_comparison_html(years_data, output_file)

    print("\nComparison Summary:")
    print("=" * 80)
    for year in sorted(years_data.keys()):
        stats = years_data[year]
        print(f"\nNovember {year}:")
        print(f"  Total Revenue: ${stats['total_revenue']:,.0f}")
        print(f"  Cyber Current: ${stats['cyber_2025_revenue']:,.0f} ({stats['cyber_2025_pct']:.1f}%)")
        print(f"  Cyber Old: ${stats['cyber_old_revenue']:,.0f} ({stats['cyber_old_pct']:.1f}%)")
        print(f"  Normal: ${stats['normal_revenue']:,.0f} ({stats['normal_pct']:.1f}%)")


if __name__ == '__main__':
    main()
