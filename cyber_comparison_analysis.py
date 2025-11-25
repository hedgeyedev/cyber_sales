#!/usr/bin/env python3
"""
Cyber Sales Year-over-Year Comparison Analysis

Generates comprehensive comparison report across multiple years with:
- Side-by-side revenue charts
- Year-over-year growth metrics
- Aggregate renewal/drop-off analysis
- Key insights and projections

Usage: python3 cyber_comparison_analysis.py 2023 2024 2025
"""

import json
import sys
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def find_data_file(year):
    """Find the JSON data file for a given year (check cache directories)."""
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


def load_year_data(year):
    """Load payment data for a specific year."""
    file_path = find_data_file(year)
    if not file_path:
        print(f"⚠️  Warning: No data file found for {year}")
        return None

    with open(file_path, 'r') as f:
        data = json.load(f)

    print(f"✓ Loaded {year} data: {data['total_payments']:,} payments, ${data['total_revenue']:,.2f} revenue")
    return data


def extract_cohort_from_sku(sku):
    """
    Extract cohort year from SKU string.

    Examples:
      elite_pass_cyber_2023_reg -> 2023
      platinum_all_access_pass_cyber_2021_reg -> 2021
      macro_pro_cyber_2022_main -> 2022

    Returns: int year or None if no cohort found
    """
    if not sku:
        return None

    match = re.search(r'cyber_(\d{4})', sku)
    if match:
        return int(match.group(1))

    return None


def categorize_payments_by_type(payments, year):
    """Categorize payments into cyber_current, cyber_old, and normal."""
    cyber_current_category = f'cyber_{year}'

    cyber_current = [p for p in payments if p.get('payment_category') == cyber_current_category]
    cyber_old = [p for p in payments if p.get('payment_category') == 'cyber_old']
    normal = [p for p in payments if p.get('payment_category') == 'normal']

    return {
        'cyber_current': cyber_current,
        'cyber_old': cyber_old,
        'normal': normal,
        'total': payments
    }


def calculate_year_stats(payments_by_type):
    """Calculate statistics for a year."""
    stats = {}

    for category, payments in payments_by_type.items():
        count = len(payments)
        revenue = sum(p['amount'] for p in payments)
        avg = revenue / count if count > 0 else 0

        stats[category] = {
            'count': count,
            'revenue': revenue,
            'avg': avg
        }

    return stats


def analyze_cohort_breakdown(payments_by_type, analysis_year):
    """
    Break down Cyber Old revenue by originating cohort year.

    Returns a dict with:
      - cohort_breakdown: {cohort_year: {'count': n, 'revenue': $, 'payments': [...]}}
      - total_cyber_old: aggregate stats
    """
    cyber_old_payments = payments_by_type['cyber_old']

    cohort_data = defaultdict(lambda: {'count': 0, 'revenue': 0.0, 'payments': []})

    for payment in cyber_old_payments:
        sku = payment.get('sku', '')
        cohort_year = extract_cohort_from_sku(sku)

        if cohort_year:
            cohort_data[cohort_year]['count'] += 1
            cohort_data[cohort_year]['revenue'] += payment['amount']
            cohort_data[cohort_year]['payments'].append(payment)

    # Convert defaultdict to regular dict and sort by cohort year
    cohort_breakdown = {
        year: {
            'count': data['count'],
            'revenue': data['revenue'],
            'avg': data['revenue'] / data['count'] if data['count'] > 0 else 0
        }
        for year, data in sorted(cohort_data.items())
    }

    return {
        'cohort_breakdown': cohort_breakdown,
        'total_cyber_old': {
            'count': len(cyber_old_payments),
            'revenue': sum(p['amount'] for p in cyber_old_payments)
        }
    }


def calculate_yoy_growth(current_stats, previous_stats):
    """Calculate year-over-year growth percentages."""
    if not previous_stats:
        return None

    growth = {}
    for category in current_stats:
        if category not in previous_stats:
            continue

        curr_rev = current_stats[category]['revenue']
        prev_rev = previous_stats[category]['revenue']
        curr_count = current_stats[category]['count']
        prev_count = previous_stats[category]['count']

        rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0
        count_growth = ((curr_count - prev_count) / prev_count * 100) if prev_count > 0 else 0

        growth[category] = {
            'revenue_growth_pct': rev_growth,
            'count_growth_pct': count_growth
        }

    return growth


def build_cohort_compounding_matrix(all_year_data):
    """
    Build a matrix showing how each cohort contributes to each year's Cyber Old revenue.

    Returns:
      {
        analysis_year: {
          cohort_year: {'revenue': $, 'count': n},
          ...
        },
        ...
      }

    Example:
      2024: {
        2020: {'revenue': 393332, 'count': 355},
        2021: {'revenue': 525532, 'count': 339},
        2022: {'revenue': 818995, 'count': 466},
        2023: {'revenue': 850090, 'count': 720}
      }
    """
    matrix = {}

    for year, data in all_year_data.items():
        if 'cohort_analysis' in data:
            matrix[year] = data['cohort_analysis']['cohort_breakdown']

    return matrix


def calculate_cohort_retention_curves(all_year_data, cohort_matrix):
    """
    Calculate retention curves for each cohort showing its journey over time.

    Returns:
      {
        cohort_year: {
          'initial_revenue': $ (from cyber_new in cohort year),
          'journey': [
            {'year': analysis_year, 'revenue': $, 'retention_pct': %},
            ...
          ]
        },
        ...
      }
    """
    cohort_curves = {}
    years = sorted(all_year_data.keys())

    # Get all unique cohorts across all years
    all_cohorts = set()
    for year_cohorts in cohort_matrix.values():
        all_cohorts.update(year_cohorts.keys())

    for cohort_year in sorted(all_cohorts):
        # Get initial revenue (cyber_new from cohort year)
        initial_revenue = 0
        if cohort_year in all_year_data:
            initial_revenue = all_year_data[cohort_year]['stats']['cyber_current']['revenue']

        # Track journey through subsequent years
        journey = []
        for analysis_year in years:
            if analysis_year <= cohort_year:
                # Can't have renewals before the cohort exists
                continue

            if analysis_year in cohort_matrix and cohort_year in cohort_matrix[analysis_year]:
                revenue = cohort_matrix[analysis_year][cohort_year]['revenue']
                count = cohort_matrix[analysis_year][cohort_year]['count']
                retention_pct = (revenue / initial_revenue * 100) if initial_revenue > 0 else 0

                journey.append({
                    'year': analysis_year,
                    'revenue': revenue,
                    'count': count,
                    'retention_pct': retention_pct,
                    'years_elapsed': analysis_year - cohort_year
                })

        if journey:  # Only include cohorts that have renewal data
            cohort_curves[cohort_year] = {
                'initial_revenue': initial_revenue,
                'initial_year': cohort_year,
                'journey': journey
            }

    return cohort_curves


def analyze_renewal_flow(all_year_data):
    """
    Analyze renewal patterns: Track how much cyber_new from Year N
    becomes cyber_old revenue in Year N+1.

    This is aggregate analysis based on revenue patterns, not individual user tracking.
    """
    years = sorted(all_year_data.keys())
    renewal_flow = []

    for i in range(len(years) - 1):
        current_year = years[i]
        next_year = years[i + 1]

        if current_year not in all_year_data or next_year not in all_year_data:
            continue

        current_cyber_new = all_year_data[current_year]['stats']['cyber_current']['revenue']
        next_cyber_old = all_year_data[next_year]['stats']['cyber_old']['revenue']

        # Calculate Net Revenue Retention (NRR)
        # >100% indicates revenue expansion from upsells/upgrades
        nrr = (next_cyber_old / current_cyber_new * 100) if current_cyber_new > 0 else 0

        renewal_flow.append({
            'from_year': current_year,
            'to_year': next_year,
            'cyber_new_revenue': current_cyber_new,
            'next_year_cyber_old': next_cyber_old,
            'nrr_pct': nrr,
            'revenue_change': next_cyber_old - current_cyber_new
        })

    return renewal_flow


def project_future_cohort_revenue(cohort_curves, current_year):
    """
    Project future Cyber Old revenue based on cohort retention patterns.

    Uses historical retention curves to estimate how each active cohort
    will perform in future years.

    Returns:
      {
        projected_year: {
          'by_cohort': {cohort: projected_revenue, ...},
          'total': sum of all cohorts
        },
        ...
      }
    """
    projections = {}

    # Calculate average retention rate per year elapsed
    retention_rates_by_year = defaultdict(list)
    for cohort_year, data in cohort_curves.items():
        for point in data['journey']:
            years_elapsed = point['years_elapsed']
            retention_pct = point['retention_pct']
            retention_rates_by_year[years_elapsed].append(retention_pct)

    # Average retention by years since cohort started
    avg_retention = {}
    for years_elapsed, rates in retention_rates_by_year.items():
        avg_retention[years_elapsed] = sum(rates) / len(rates) if rates else 0

    # Project next year based on active cohorts
    next_year = current_year + 1
    next_year_projection = {}

    for cohort_year, data in cohort_curves.items():
        initial_revenue = data['initial_revenue']
        years_elapsed = next_year - cohort_year

        # Use average retention rate for this time period if available
        if years_elapsed in avg_retention:
            projected_retention = avg_retention[years_elapsed]
        elif data['journey']:
            # Extrapolate from last known retention rate with decay
            last_point = data['journey'][-1]
            decay_rate = 0.85  # Assume 15% decay per year
            years_to_project = years_elapsed - last_point['years_elapsed']
            projected_retention = last_point['retention_pct'] * (decay_rate ** years_to_project)
        else:
            projected_retention = 0

        projected_revenue = initial_revenue * (projected_retention / 100)
        next_year_projection[cohort_year] = projected_revenue

    projections[next_year] = {
        'by_cohort': next_year_projection,
        'total': sum(next_year_projection.values())
    }

    return projections


def calculate_projection(current_year, all_year_data, cohort_curves=None):
    """
    Calculate projection for current year if data is partial (< 30 days).

    Returns projection data with:
    - Conservative: Linear extrapolation from current pace
    - Expected: Weighted by previous year's daily distribution
    - Cohort-based: Using historical cohort retention patterns
    """
    current_data = all_year_data[current_year]
    payments = current_data['data']['payments']

    # Count unique days in dataset
    unique_days = len(set(p['date'] for p in payments))

    # Only project if we have < 30 days
    if unique_days >= 30:
        return None

    # Get current stats
    current_stats = current_data['stats']
    total_revenue = current_data['data']['total_revenue']
    total_payments = current_data['data']['total_payments']

    # Conservative projection: Current pace × 30 days
    daily_avg_revenue = total_revenue / unique_days
    daily_avg_payments = total_payments / unique_days

    conservative = {
        'total_revenue': daily_avg_revenue * 30,
        'total_payments': int(daily_avg_payments * 30),
        'cyber_current_revenue': current_stats['cyber_current']['revenue'] / unique_days * 30,
        'cyber_old_revenue': current_stats['cyber_old']['revenue'] / unique_days * 30,
        'normal_revenue': current_stats['normal']['revenue'] / unique_days * 30,
    }

    # Expected projection: Account for Cyber Monday surge (typically days 25-28)
    # Assume last week of November sees 30% higher volume than average
    # This is a simplified model - we could weight by previous year's exact pattern
    surge_factor = 1.15  # Assume 15% overall boost from Cyber Monday week

    expected = {
        'total_revenue': conservative['total_revenue'] * surge_factor,
        'total_payments': int(conservative['total_payments'] * surge_factor),
        'cyber_current_revenue': conservative['cyber_current_revenue'] * surge_factor,
        'cyber_old_revenue': conservative['cyber_old_revenue'] * surge_factor,
        'normal_revenue': conservative['normal_revenue'] * surge_factor,
    }

    # Cohort-based projection (if cohort data available)
    cohort_projection = None
    if cohort_curves:
        future_projections = project_future_cohort_revenue(cohort_curves, current_year)
        if current_year + 1 in future_projections:
            cohort_projection = future_projections[current_year + 1]

    # Calculate vs previous year (if available)
    prev_year = current_year - 1
    vs_previous = None
    if prev_year in all_year_data:
        prev_revenue = all_year_data[prev_year]['data']['total_revenue']
        vs_previous = {
            'conservative_growth': ((conservative['total_revenue'] - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0,
            'expected_growth': ((expected['total_revenue'] - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0,
            'prev_year_revenue': prev_revenue
        }

    return {
        'days_elapsed': unique_days,
        'conservative': conservative,
        'expected': expected,
        'cohort_projection': cohort_projection,
        'vs_previous': vs_previous,
        'current_actual': {
            'total_revenue': total_revenue,
            'total_payments': total_payments,
            'cyber_current_revenue': current_stats['cyber_current']['revenue'],
            'cyber_old_revenue': current_stats['cyber_old']['revenue'],
            'normal_revenue': current_stats['normal']['revenue'],
        }
    }


def generate_comparison_html(all_year_data, renewal_flow, output_file, projection=None, cohort_matrix=None, cohort_curves=None):
    """Generate HTML comparison report with cohort analysis."""
    years = sorted(all_year_data.keys())
    start_year = years[0]
    end_year = years[-1]

    # Generate projection HTML first if needed (before main template)
    projection_html = ""
    if projection:
        proj = projection
        days = proj['days_elapsed']
        curr = proj['current_actual']
        cons = proj['conservative']
        exp = proj['expected']
        vs_prev = proj['vs_previous']

        # Determine growth indicator
        growth_class_cons = "positive" if vs_prev and vs_prev['conservative_growth'] >= 0 else "negative"
        growth_class_exp = "positive" if vs_prev and vs_prev['expected_growth'] >= 0 else "negative"

        projection_html = f"""
    <div class="section" style="background: linear-gradient(to right, #e3f2fd 0%, #fff 100%); border-left: 5px solid #2c5aa0;">
        <h2>📊 November {end_year} Projection</h2>
        <p style="color: #666; font-style: italic; margin-bottom: 20px;">
            Based on <strong>{days} days</strong> of data (Nov 1-{days}, {end_year}). Projection assumes:
            <br>• <strong>Conservative</strong>: Current pace continues linearly
            <br>• <strong>Expected</strong>: 15% surge during Cyber Monday week (typical pattern)
        </p>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 25px;">
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #666;">
                <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Current ({days} days)</div>
                <div style="font-size: 28px; font-weight: bold; color: #333; margin: 10px 0;">${curr['total_revenue']/1000000:.2f}M</div>
                <div style="font-size: 14px; color: #666;">{curr['total_payments']:,} payments</div>
            </div>
            <div style="background: #fff3cd; padding: 20px; border-radius: 8px; border-left: 4px solid #ffc107;">
                <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Conservative (30 days)</div>
                <div style="font-size: 28px; font-weight: bold; color: #f57c00; margin: 10px 0;">~${cons['total_revenue']/1000000:.2f}M</div>
                <div style="font-size: 14px; color: #666;">~{cons['total_payments']:,} payments</div>
                {f'<div style="font-size: 13px; margin-top: 8px;" class="{growth_class_cons}">{vs_prev["conservative_growth"]:+.1f}% vs {end_year-1}</div>' if vs_prev else ''}
            </div>
            <div style="background: #d1f2eb; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745;">
                <div style="font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Expected (w/ Cyber Mon)</div>
                <div style="font-size: 28px; font-weight: bold; color: #28a745; margin: 10px 0;">~${exp['total_revenue']/1000000:.2f}M</div>
                <div style="font-size: 14px; color: #666;">~{exp['total_payments']:,} payments</div>
                {f'<div style="font-size: 13px; margin-top: 8px;" class="{growth_class_exp}">{vs_prev["expected_growth"]:+.0f}% vs {end_year-1}</div>' if vs_prev else ''}
            </div>
        </div>

        <h3 style="margin-top: 25px; margin-bottom: 15px;">Projected Revenue Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Scenario</th>
                    <th>Total Revenue</th>
                    <th>Cyber New</th>
                    <th>Cyber Old</th>
                    <th>Normal</th>
                </tr>
            </thead>
            <tbody>
                <tr style="background: #f8f9fa;">
                    <td><strong>Current ({days} days)</strong></td>
                    <td>${curr['total_revenue']/1000:.0f}K</td>
                    <td>${curr['cyber_current_revenue']/1000:.0f}K</td>
                    <td>${curr['cyber_old_revenue']/1000:.0f}K</td>
                    <td>${curr['normal_revenue']/1000:.0f}K</td>
                </tr>
                <tr>
                    <td><strong>Conservative</strong></td>
                    <td><strong>${cons['total_revenue']/1000000:.2f}M</strong></td>
                    <td>${cons['cyber_current_revenue']/1000000:.2f}M</td>
                    <td>${cons['cyber_old_revenue']/1000000:.2f}M</td>
                    <td>${cons['normal_revenue']/1000:.0f}K</td>
                </tr>
                <tr style="background: #d1f2eb;">
                    <td><strong>Expected</strong></td>
                    <td><strong>${exp['total_revenue']/1000000:.2f}M</strong></td>
                    <td>${exp['cyber_current_revenue']/1000000:.2f}M</td>
                    <td>${exp['cyber_old_revenue']/1000000:.2f}M</td>
                    <td>${exp['normal_revenue']/1000:.0f}K</td>
                </tr>
            </tbody>
        </table>

        <div class="insight" style="margin-top: 20px;">
            <h4>💡 Key Insight</h4>
            <p>With {days} days of data, {end_year} is tracking <strong>{(curr['cyber_current_revenue']/curr['total_revenue']*100):.0f}% Cyber New revenue</strong>.
            {f"At the expected pace, {end_year} could deliver <strong>${exp['total_revenue']/1000000:.2f}M in total revenue</strong> ({vs_prev['expected_growth']:+.0f}% vs {end_year-1}'s ${vs_prev['prev_year_revenue']/1000000:.2f}M)." if vs_prev else ""}</p>
            <p style="margin-top: 10px;"><em>Note: Projections assume typical Cyber Monday surge patterns. Actual results may vary based on promotional timing and market conditions.</em></p>
        </div>
    </div>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Sales Comparison {start_year}-{end_year}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            text-align: center;
            border-bottom: 3px solid #2c5aa0;
            padding-bottom: 15px;
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
        .positive {{
            color: #28a745;
            font-weight: 600;
        }}
        .negative {{
            color: #dc3545;
            font-weight: 600;
        }}
        .neutral {{
            color: #666;
        }}
        .chart-container {{
            position: relative;
            height: 400px;
            margin: 20px 0;
        }}
        .insight {{
            background: #e3f2fd;
            border-left: 4px solid #2c5aa0;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .insight h3 {{
            margin-top: 0;
            color: #1565c0;
        }}
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            text-align: center;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c5aa0;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <h1>Cyber Sales Year-over-Year Comparison</h1>
    <p style="text-align: center; color: #666; margin-bottom: 30px;">
        November {start_year} - November {end_year} Analysis
    </p>

    <!-- Overall Summary -->
    <div class="section">
        <h2>📊 Overall Summary by Year</h2>
        <table>
            <thead>
                <tr>
                    <th>Year</th>
                    <th>Total Payments</th>
                    <th>Total Revenue</th>
                    <th>Cyber New</th>
                    <th>Cyber Old</th>
                    <th>Normal</th>
                    <th>Avg/Payment</th>
                </tr>
            </thead>
            <tbody id="summaryTableBody">
            </tbody>
        </table>
    </div>

    <!-- Projection Section (only shown if projection data exists) -->
    {projection_html}

    <!-- YoY Growth -->
    <div class="section">
        <h2>📈 Year-over-Year Growth</h2>
        <table>
            <thead>
                <tr>
                    <th>Comparison</th>
                    <th>Total Revenue Growth</th>
                    <th>Payment Count Growth</th>
                    <th>Cyber New Growth</th>
                    <th>Avg Price Change</th>
                </tr>
            </thead>
            <tbody id="growthTableBody">
            </tbody>
        </table>
    </div>

    <!-- Renewal Flow Analysis -->
    <div class="section">
        <h2>🔄 Renewal Flow & Net Revenue Retention (NRR)</h2>
        <p style="color: #666; margin-bottom: 20px;">
            This tracks how much new Cyber revenue from Year N appears as Cyber Old revenue in Year N+1.
            <strong>Net Revenue Retention (NRR)</strong> > 100% indicates revenue expansion from upsells, upgrades, or increased usage.
        </p>
        <table>
            <thead>
                <tr>
                    <th>Flow</th>
                    <th>Cyber New Revenue</th>
                    <th>Next Year Cyber Old</th>
                    <th>Net Revenue Retention (NRR)</th>
                    <th>Revenue Change</th>
                </tr>
            </thead>
            <tbody id="renewalFlowTableBody">
            </tbody>
        </table>
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 4px; font-size: 14px;">
            <strong>📝 Note:</strong> NRR measures revenue retention/expansion. Values >100% show revenue <em>growth</em> from existing customers
            through upsells, upgrades, or increased usage - a very positive indicator in SaaS businesses.
        </div>
    </div>

    <!-- Cohort Compounding Matrix -->
    <div class="section" id="cohortMatrixSection" style="display: none;">
        <h2>🔢 Cohort Compounding Matrix</h2>
        <p style="color: #666; margin-bottom: 20px;">
            This shows how each year's Cyber Old revenue is composed of contributions from different cohorts.
            Each row shows an analysis year, and columns show how much each cohort contributed to that year's renewals.
        </p>
        <div id="cohortMatrixContainer"></div>
        <div style="margin-top: 15px; padding: 10px; background: #e3f2fd; border-radius: 4px; font-size: 14px;">
            <strong>💡 Key Insight:</strong> Cyber Old revenue compounds from multiple aging cohorts. As cohorts mature,
            their individual contributions may decline, but the total grows as new cohorts are added each year.
        </div>
    </div>

    <!-- Cohort Retention Curves -->
    <div class="section" id="cohortCurvesSection" style="display: none;">
        <h2>📈 Cohort Retention Curves</h2>
        <p style="color: #666; margin-bottom: 20px;">
            Track each cohort's revenue journey over time, showing how retention evolves year-over-year.
        </p>
        <div class="chart-container">
            <canvas id="cohortRetentionChart"></canvas>
        </div>
        <div id="cohortStatsContainer" style="margin-top: 20px;"></div>
    </div>

    <!-- Charts -->
    <div class="section">
        <h2>📉 Revenue Trends</h2>
        <div class="chart-container">
            <canvas id="revenueComparisonChart"></canvas>
        </div>
    </div>

    <div class="section">
        <h2>📊 Payment Volume Trends</h2>
        <div class="chart-container">
            <canvas id="paymentComparisonChart"></canvas>
        </div>
    </div>

    <div class="section">
        <h2>🎯 Cyber New vs Renewal Mix</h2>
        <div class="chart-container">
            <canvas id="cyberMixChart"></canvas>
        </div>
    </div>

    <!-- Key Insights -->
    <div class="section">
        <div class="insight">
            <h3>💡 Key Insights</h3>
            <div id="insightsContent"></div>
        </div>
    </div>

    <script>
        const allYearData = {json.dumps({str(year): {
            'year': year,
            'stats': {
                category: {
                    'count': stats['count'],
                    'revenue': stats['revenue'],
                    'avg': stats['avg']
                }
                for category, stats in all_year_data[year]['stats'].items()
            },
            'total_payments': data['data']['total_payments'],
            'total_revenue': data['data']['total_revenue']
        } for year, data in all_year_data.items()}, indent=8)};

        const renewalFlow = {json.dumps(renewal_flow, indent=8)};

        const cohortMatrix = {json.dumps(cohort_matrix if cohort_matrix else {}, indent=8)};
        const cohortCurves = {json.dumps(cohort_curves if cohort_curves else {}, indent=8)};

        // Populate summary table
        const summaryBody = document.getElementById('summaryTableBody');
        const years = Object.keys(allYearData).sort();

        years.forEach(year => {{
            const data = allYearData[year];
            const row = summaryBody.insertRow();
            row.innerHTML = `
                <td><strong>${{year}}</strong></td>
                <td>${{data.total_payments.toLocaleString()}}</td>
                <td>$${{(data.total_revenue / 1000000).toFixed(2)}}M</td>
                <td>$${{(data.stats.cyber_current.revenue / 1000).toFixed(0)}}K</td>
                <td>$${{(data.stats.cyber_old.revenue / 1000).toFixed(0)}}K</td>
                <td>$${{(data.stats.normal.revenue / 1000).toFixed(0)}}K</td>
                <td>$${{data.stats.total.avg.toFixed(2)}}</td>
            `;
        }});

        // Populate growth table
        const growthBody = document.getElementById('growthTableBody');
        for (let i = 1; i < years.length; i++) {{
            const prevYear = years[i-1];
            const currYear = years[i];
            const prev = allYearData[prevYear];
            const curr = allYearData[currYear];

            const revGrowth = ((curr.total_revenue - prev.total_revenue) / prev.total_revenue * 100).toFixed(1);
            const countGrowth = ((curr.total_payments - prev.total_payments) / prev.total_payments * 100).toFixed(1);
            const cyberNewGrowth = ((curr.stats.cyber_current.revenue - prev.stats.cyber_current.revenue) / prev.stats.cyber_current.revenue * 100).toFixed(1);
            const avgChange = ((curr.stats.total.avg - prev.stats.total.avg) / prev.stats.total.avg * 100).toFixed(1);

            const revClass = revGrowth >= 0 ? 'positive' : 'negative';
            const countClass = countGrowth >= 0 ? 'positive' : 'negative';
            const cyberClass = cyberNewGrowth >= 0 ? 'positive' : 'negative';
            const avgClass = avgChange >= 0 ? 'positive' : 'negative';

            const row = growthBody.insertRow();
            row.innerHTML = `
                <td>${{prevYear}} → ${{currYear}}</td>
                <td class="${{revClass}}">${{revGrowth}}%</td>
                <td class="${{countClass}}">${{countGrowth}}%</td>
                <td class="${{cyberClass}}">${{cyberNewGrowth}}%</td>
                <td class="${{avgClass}}">${{avgChange}}%</td>
            `;
        }}

        // Populate renewal flow table
        const renewalBody = document.getElementById('renewalFlowTableBody');
        renewalFlow.forEach(flow => {{
            const nrr = flow.nrr_pct;
            const nrrClass = nrr >= 100 ? 'positive' : nrr >= 70 ? 'neutral' : 'negative';
            const revenueChange = flow.revenue_change;
            const changeClass = revenueChange >= 0 ? 'positive' : 'negative';
            const changeSymbol = revenueChange >= 0 ? '+' : '';

            const row = renewalBody.insertRow();
            row.innerHTML = `
                <td>${{flow.from_year}} Cyber New → ${{flow.to_year}} Cyber Old</td>
                <td>$${{(flow.cyber_new_revenue / 1000000).toFixed(2)}}M</td>
                <td>$${{(flow.next_year_cyber_old / 1000000).toFixed(2)}}M</td>
                <td class="${{nrrClass}}">${{nrr.toFixed(1)}}%</td>
                <td class="${{changeClass}}">${{changeSymbol}}$${{(revenueChange / 1000000).toFixed(2)}}M</td>
            `;
        }});

        // Render Cohort Matrix
        if (Object.keys(cohortMatrix).length > 0) {{
            document.getElementById('cohortMatrixSection').style.display = 'block';

            // Get all unique cohorts
            const allCohorts = new Set();
            Object.values(cohortMatrix).forEach(yearData => {{
                Object.keys(yearData).forEach(cohort => allCohorts.add(parseInt(cohort)));
            }});
            const cohorts = Array.from(allCohorts).sort();
            const matrixYears = Object.keys(cohortMatrix).sort();

            // Build matrix table
            let matrixHTML = '<table><thead><tr><th>Analysis Year</th>';
            cohorts.forEach(cohort => {{
                matrixHTML += `<th>${{cohort}} Cohort</th>`;
            }});
            matrixHTML += '<th><strong>Total Cyber Old</strong></th></tr></thead><tbody>';

            matrixYears.forEach(year => {{
                matrixHTML += `<tr><td><strong>${{year}}</strong></td>`;
                let yearTotal = 0;

                cohorts.forEach(cohort => {{
                    if (cohortMatrix[year][cohort]) {{
                        const revenue = cohortMatrix[year][cohort].revenue;
                        const count = cohortMatrix[year][cohort].count;
                        yearTotal += revenue;
                        matrixHTML += `<td>$${{(revenue / 1000).toFixed(0)}}K<br><span style="font-size: 11px; color: #666;">(${{count}} pmt)</span></td>`;
                    }} else {{
                        matrixHTML += '<td style="color: #ccc;">—</td>';
                    }}
                }});

                matrixHTML += `<td><strong>$${{(yearTotal / 1000000).toFixed(2)}}M</strong></td></tr>`;
            }});

            matrixHTML += '</tbody></table>';
            document.getElementById('cohortMatrixContainer').innerHTML = matrixHTML;
        }}

        // Render Cohort Retention Curves
        if (Object.keys(cohortCurves).length > 0) {{
            document.getElementById('cohortCurvesSection').style.display = 'block';

            // Prepare data for chart
            const cohortColors = [
                'rgba(44, 90, 160, 1)',
                'rgba(100, 140, 200, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)'
            ];

            const datasets = [];
            let colorIndex = 0;

            Object.keys(cohortCurves).sort().forEach(cohort => {{
                const data = cohortCurves[cohort];
                const dataPoints = data.journey.map(point => ({{
                    x: point.year,
                    y: point.retention_pct
                }}));

                datasets.push({{
                    label: `${{cohort}} Cohort`,
                    data: dataPoints,
                    borderColor: cohortColors[colorIndex % cohortColors.length],
                    backgroundColor: cohortColors[colorIndex % cohortColors.length].replace('1)', '0.1)'),
                    fill: false,
                    tension: 0.4
                }});

                colorIndex++;
            }});

            new Chart(document.getElementById('cohortRetentionChart'), {{
                type: 'line',
                data: {{
                    datasets: datasets
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: true,
                            text: 'Cohort Retention Over Time (% of Initial Revenue)'
                        }}
                    }},
                    scales: {{
                        x: {{
                            type: 'linear',
                            title: {{
                                display: true,
                                text: 'Year'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Retention %'
                            }},
                            ticks: {{
                                callback: function(value) {{
                                    return value.toFixed(0) + '%';
                                }}
                            }}
                        }}
                    }}
                }}
            }});

            // Add cohort stats table
            let statsHTML = '<h3>Cohort Retention Summary</h3><table><thead><tr>';
            statsHTML += '<th>Cohort</th><th>Initial Revenue</th><th>Latest Retention</th><th>Years Tracked</th><th>Retention Trend</th></tr></thead><tbody>';

            Object.keys(cohortCurves).sort().forEach(cohort => {{
                const data = cohortCurves[cohort];
                const lastPoint = data.journey[data.journey.length - 1];
                const firstPoint = data.journey[0];
                const trend = lastPoint.retention_pct < firstPoint.retention_pct ? '📉 Declining' : '📈 Growing';
                const trendClass = lastPoint.retention_pct < firstPoint.retention_pct ? 'negative' : 'positive';

                statsHTML += `<tr>
                    <td><strong>${{cohort}}</strong></td>
                    <td>$${{(data.initial_revenue / 1000000).toFixed(2)}}M</td>
                    <td>${{lastPoint.retention_pct.toFixed(1)}}%</td>
                    <td>${{data.journey.length}} years</td>
                    <td class="${{trendClass}}">${{trend}}</td>
                </tr>`;
            }});

            statsHTML += '</tbody></table>';
            document.getElementById('cohortStatsContainer').innerHTML = statsHTML;
        }}

        // Create revenue chart (with cohort-based stacking if available)
        const revenueChartDatasets = [];

        if (Object.keys(cohortMatrix).length > 0) {{
            // Create stacked chart by cohort
            const allCohorts = new Set();
            Object.values(cohortMatrix).forEach(yearData => {{
                Object.keys(yearData).forEach(cohort => allCohorts.add(parseInt(cohort)));
            }});
            const cohorts = Array.from(allCohorts).sort();

            const cohortColorPalette = [
                'rgba(44, 90, 160, 0.9)',
                'rgba(100, 140, 200, 0.9)',
                'rgba(255, 99, 132, 0.9)',
                'rgba(54, 162, 235, 0.9)',
                'rgba(255, 206, 86, 0.9)',
                'rgba(75, 192, 192, 0.9)'
            ];

            cohorts.forEach((cohort, index) => {{
                revenueChartDatasets.push({{
                    label: `${{cohort}} Cohort (Old)`,
                    data: years.map(y => {{
                        if (cohortMatrix[y] && cohortMatrix[y][cohort]) {{
                            return cohortMatrix[y][cohort].revenue;
                        }}
                        return 0;
                    }}),
                    backgroundColor: cohortColorPalette[index % cohortColorPalette.length],
                    stack: 'cyber_old'
                }});
            }});

            // Add Cyber New as separate stack
            revenueChartDatasets.push({{
                label: 'Cyber New',
                data: years.map(y => allYearData[y].stats.cyber_current.revenue),
                backgroundColor: 'rgba(40, 167, 69, 0.8)',
                stack: 'cyber_new'
            }});

            revenueChartDatasets.push({{
                label: 'Normal',
                data: years.map(y => allYearData[y].stats.normal.revenue),
                backgroundColor: 'rgba(255, 159, 64, 0.8)',
                stack: 'normal'
            }});
        }} else {{
            // Fallback to original grouping
            revenueChartDatasets.push(
                {{
                    label: 'Cyber New',
                    data: years.map(y => allYearData[y].stats.cyber_current.revenue),
                    backgroundColor: 'rgba(44, 90, 160, 0.8)'
                }},
                {{
                    label: 'Cyber Old (Renewals)',
                    data: years.map(y => allYearData[y].stats.cyber_old.revenue),
                    backgroundColor: 'rgba(100, 140, 200, 0.8)'
                }},
                {{
                    label: 'Normal',
                    data: years.map(y => allYearData[y].stats.normal.revenue),
                    backgroundColor: 'rgba(255, 159, 64, 0.8)'
                }}
            );
        }}

        // Create revenue chart
        new Chart(document.getElementById('revenueComparisonChart'), {{
            type: 'bar',
            data: {{
                labels: years,
                datasets: revenueChartDatasets
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Revenue by Category and Year'
                    }}
                }},
                scales: {{
                    x: {{ stacked: true }},
                    y: {{
                        stacked: true,
                        ticks: {{
                            callback: function(value) {{
                                return '$$' + (value/1000000).toFixed(1) + 'M';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Create payment count chart
        new Chart(document.getElementById('paymentComparisonChart'), {{
            type: 'line',
            data: {{
                labels: years,
                datasets: [
                    {{
                        label: 'Total Payments',
                        data: years.map(y => allYearData[y].total_payments),
                        borderColor: 'rgba(44, 90, 160, 1)',
                        backgroundColor: 'rgba(44, 90, 160, 0.1)',
                        fill: true,
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'Total Payment Volume Over Time'
                    }}
                }}
            }}
        }});

        // Create cyber mix chart
        new Chart(document.getElementById('cyberMixChart'), {{
            type: 'line',
            data: {{
                labels: years,
                datasets: [
                    {{
                        label: 'Cyber New Revenue',
                        data: years.map(y => allYearData[y].stats.cyber_current.revenue),
                        borderColor: 'rgba(44, 90, 160, 1)',
                        backgroundColor: 'rgba(44, 90, 160, 0.1)',
                        fill: false,
                        tension: 0.4
                    }},
                    {{
                        label: 'Cyber Old (Renewals) Revenue',
                        data: years.map(y => allYearData[y].stats.cyber_old.revenue),
                        borderColor: 'rgba(100, 140, 200, 1)',
                        backgroundColor: 'rgba(100, 140, 200, 0.1)',
                        fill: false,
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: 'New vs Renewal Revenue Trends'
                    }}
                }},
                scales: {{
                    y: {{
                        ticks: {{
                            callback: function(value) {{
                                return '$$' + (value/1000000).toFixed(1) + 'M';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Generate insights
        const insightsContent = document.getElementById('insightsContent');
        let insights = '<ul>';

        // Best performing year
        const bestYear = years.reduce((best, year) =>
            allYearData[year].total_revenue > allYearData[best].total_revenue ? year : best
        );
        insights += `<li><strong>Best Year:</strong> ${{bestYear}} with $${{(allYearData[bestYear].total_revenue/1000000).toFixed(2)}}M in total revenue</li>`;

        // Best cyber new acquisition
        const bestCyberYear = years.reduce((best, year) =>
            allYearData[year].stats.cyber_current.revenue > allYearData[best].stats.cyber_current.revenue ? year : best
        );
        insights += `<li><strong>Best New Customer Acquisition:</strong> ${{bestCyberYear}} with $${{(allYearData[bestCyberYear].stats.cyber_current.revenue/1000000).toFixed(2)}}M in new Cyber sales</li>`;

        // Average NRR
        if (renewalFlow.length > 0) {{
            const avgNRR = renewalFlow.reduce((sum, f) => sum + f.nrr_pct, 0) / renewalFlow.length;
            insights += `<li><strong>Average Net Revenue Retention (NRR):</strong> ${{avgNRR.toFixed(1)}}% (based on revenue flow from Cyber New to Cyber Old)</li>`;
        }}

        // Trend analysis
        if (years.length >= 3) {{
            const recentYears = years.slice(-3);
            const trend = recentYears.map(y => allYearData[y].stats.cyber_current.revenue);
            const isGrowing = trend[2] > trend[1] && trend[1] > trend[0];
            const trendMsg = isGrowing
                ? 'New Cyber sales are <strong>trending upward</strong> 📈'
                : 'New Cyber sales show <strong>mixed results</strong> 📊';
            insights += `<li><strong>Trend:</strong> ${{trendMsg}}</li>`;
        }}

        // Projection for next year
        const latestYear = years[years.length - 1];
        const latestCyberNew = allYearData[latestYear].stats.cyber_current.revenue;
        const avgNRRPct = renewalFlow.length > 0
            ? renewalFlow.reduce((sum, f) => sum + f.nrr_pct, 0) / renewalFlow.length
            : 60;
        const projectedRenewal = latestCyberNew * (avgNRRPct / 100);
        const nextYear = parseInt(latestYear) + 1;
        insights += `<li><strong>Projection for ${{nextYear}}:</strong> Based on ${{latestYear}} Cyber New sales ($${{(latestCyberNew/1000000).toFixed(2)}}M) and avg NRR (${{avgNRRPct.toFixed(1)}}%), expect approximately $${{(projectedRenewal/1000000).toFixed(2)}}M in renewal revenue</li>`;

        insights += '</ul>';
        insightsContent.innerHTML = insights;
    </script>
</body>
</html>
"""

    with open(output_file, 'w') as f:
        f.write(html)

    print(f"\n✓ Generated comparison report: {output_file}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 cyber_comparison_analysis.py <year1> <year2> [year3] ...")
        print("Example: python3 cyber_comparison_analysis.py 2023 2024 2025")
        sys.exit(1)

    years = [int(year) for year in sys.argv[1:]]
    years.sort()

    print(f"\n{'='*60}")
    print(f"Cyber Sales Year-over-Year Comparison Analysis")
    print(f"{'='*60}")
    print(f"Years: {', '.join(str(y) for y in years)}")
    print(f"{'='*60}\n")

    # Load data for all years
    all_year_data = {}
    for year in years:
        print(f"Loading {year} data...")
        data = load_year_data(year)
        if data is None:
            print(f"⚠️  Skipping {year} - no data available")
            continue

        payments = data['payments']
        payments_by_type = categorize_payments_by_type(payments, year)
        stats = calculate_year_stats(payments_by_type)

        # Perform cohort analysis
        cohort_analysis = analyze_cohort_breakdown(payments_by_type, year)

        all_year_data[year] = {
            'data': data,
            'payments_by_type': payments_by_type,
            'stats': stats,
            'cohort_analysis': cohort_analysis
        }

    if len(all_year_data) < 2:
        print("\n✗ Error: Need at least 2 years of data for comparison")
        sys.exit(1)

    print(f"\n✓ Loaded data for {len(all_year_data)} years\n")

    # Analyze renewal flow
    print("Analyzing renewal patterns...")
    renewal_flow = analyze_renewal_flow(all_year_data)

    # Build cohort compounding matrix
    print("Building cohort compounding matrix...")
    cohort_matrix = build_cohort_compounding_matrix(all_year_data)

    # Calculate cohort retention curves
    print("Calculating cohort retention curves...")
    cohort_curves = calculate_cohort_retention_curves(all_year_data, cohort_matrix)

    # Calculate projection for most recent year if applicable
    latest_year = max(all_year_data.keys())
    projection = None
    print(f"Checking if {latest_year} needs projection...")
    projection = calculate_projection(latest_year, all_year_data, cohort_curves)
    if projection:
        print(f"✓ {latest_year} has {projection['days_elapsed']} days of data - generating projections")
    else:
        print(f"✓ {latest_year} has full month data - no projection needed")

    # Generate comparison HTML
    output_file = f"cyber_november_comparison_{min(years)}_{max(years)}.html"
    print(f"Generating comparison report...")
    generate_comparison_html(all_year_data, renewal_flow, output_file, projection, cohort_matrix, cohort_curves)

    print(f"\n{'='*60}")
    print(f"Comparison Summary")
    print(f"{'='*60}\n")

    for year in sorted(all_year_data.keys()):
        stats = all_year_data[year]['stats']
        print(f"{year}:")
        print(f"  Total Revenue: ${stats['total']['revenue']:,.2f}")
        print(f"  Cyber New: ${stats['cyber_current']['revenue']:,.2f} ({stats['cyber_current']['count']} payments)")
        print(f"  Cyber Old: ${stats['cyber_old']['revenue']:,.2f} ({stats['cyber_old']['count']} payments)")
        print()

    if renewal_flow:
        print("Renewal Flow (Net Revenue Retention):")
        for flow in renewal_flow:
            print(f"  {flow['from_year']} → {flow['to_year']}: {flow['nrr_pct']:.1f}% NRR "
                  f"(${flow['cyber_new_revenue']/1000000:.2f}M → ${flow['next_year_cyber_old']/1000000:.2f}M)")
        print()

    print(f"{'='*60}")
    print(f"✓ Report ready: {output_file}")
    print(f"{'='*60}\n")
    print(f"Open in browser: open {output_file}\n")


if __name__ == '__main__':
    main()
