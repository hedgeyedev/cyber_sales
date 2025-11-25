#!/usr/bin/env python3
"""
Generate interactive HTML visualization from recurring payments JSON data.

This script reads recurring_payments.json and creates an HTML file with:
- Cyber vs Regular payment comparison
- Total revenue and payment statistics
- Daily revenue breakdown (separate for cyber and regular)
- Hourly activity patterns (separate for cyber and regular)
- Target service tier analysis (separate for cyber and regular)
- SKU breakdown by tier (separate for cyber and regular)
"""

import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path


def extract_year_from_filename(filename):
    """Extract year from filename like 'recurring_payments_2024.json'."""
    import re
    match = re.search(r'_(\d{4})', filename)
    if match:
        return match.group(1)
    return None


def load_data(json_file='recurring_payments.json'):
    """Load payment data from JSON file."""
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Try to get year from JSON metadata first, then from filename
    if 'cyber_year' in data:
        data['_extracted_year'] = str(data['cyber_year'])
    else:
        year_from_filename = extract_year_from_filename(json_file)
        if year_from_filename:
            data['_extracted_year'] = year_from_filename
        else:
            data['_extracted_year'] = '2025'  # Default fallback

    return data


def filter_payments_by_category(payments, cyber_year):
    """Split payments into cyber_current, cyber_old, and normal based on payment_category field."""
    cyber_current_category = f'cyber_{cyber_year}'
    cyber_current = [p for p in payments if p.get('payment_category') == cyber_current_category]
    cyber_old = [p for p in payments if p.get('payment_category') == 'cyber_old']
    normal = [p for p in payments if p.get('payment_category') == 'normal']

    # "Other" combines cyber_old + normal
    other = cyber_old + normal

    # Debug info
    print(f"\n  Filtering payments by category:")
    print(f"    Total payments: {len(payments)}")
    print(f"    Cyber {cyber_year}: {len(cyber_current)}")
    print(f"    Cyber Old: {len(cyber_old)}")
    print(f"    Normal: {len(normal)}")
    print(f"    Other (Cyber Old + Normal): {len(other)}")

    # Check if payment_category field exists
    has_category = any('payment_category' in p for p in payments)
    if not has_category:
        print(f"\n  ⚠️  WARNING: No payments have 'payment_category' field!")
        print(f"     Did you run the updated recurring_payment_analysis.rb?")

    return cyber_current, cyber_old, normal, other


def calculate_category_stats(cyber_current, cyber_old, normal, payments, cyber_year):
    """Calculate statistics for all three categories."""
    total_payments = len(payments)
    total_revenue = sum(p['amount'] for p in payments)

    cyber_current_count = len(cyber_current)
    cyber_current_revenue = sum(p['amount'] for p in cyber_current)
    cyber_old_count = len(cyber_old)
    cyber_old_revenue = sum(p['amount'] for p in cyber_old)
    normal_count = len(normal)
    normal_revenue = sum(p['amount'] for p in normal)

    return {
        f'cyber_{cyber_year}_count': cyber_current_count,
        f'cyber_{cyber_year}_revenue': cyber_current_revenue,
        f'cyber_{cyber_year}_pct': (cyber_current_count / total_payments * 100) if total_payments > 0 else 0,
        f'cyber_{cyber_year}_revenue_pct': (cyber_current_revenue / total_revenue * 100) if total_revenue > 0 else 0,
        'cyber_old_count': cyber_old_count,
        'cyber_old_revenue': cyber_old_revenue,
        'cyber_old_pct': (cyber_old_count / total_payments * 100) if total_payments > 0 else 0,
        'cyber_old_revenue_pct': (cyber_old_revenue / total_revenue * 100) if total_revenue > 0 else 0,
        'normal_count': normal_count,
        'normal_revenue': normal_revenue,
        'normal_pct': (normal_count / total_payments * 100) if total_payments > 0 else 0,
        'normal_revenue_pct': (normal_revenue / total_revenue * 100) if total_revenue > 0 else 0,
    }


def aggregate_daily_data(payments):
    """Aggregate payments by day."""
    daily = defaultdict(lambda: {'count': 0, 'total': 0.0})

    for payment in payments:
        date = payment['date']
        daily[date]['count'] += 1
        daily[date]['total'] += payment['amount']

    # Convert to sorted list
    result = []
    for date in sorted(daily.keys()):
        day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
        result.append({
            'date': date,
            'day': day_name,
            'count': daily[date]['count'],
            'total': daily[date]['total']
        })

    return result


def aggregate_hourly_data(payments):
    """Aggregate payments by hour of day."""
    hourly = defaultdict(lambda: {'count': 0, 'total': 0.0})

    for payment in payments:
        hour = payment['hour']
        hourly[hour]['count'] += 1
        hourly[hour]['total'] += payment['amount']

    # Convert to sorted list
    result = []
    for hour in range(24):
        result.append({
            'hour': hour,
            'count': hourly[hour]['count'],
            'total': hourly[hour]['total']
        })

    return result


def aggregate_tier_data(payments):
    """Aggregate payments by target service tier."""
    tiers = defaultdict(lambda: {'count': 0, 'total': 0.0})

    for payment in payments:
        tier = payment.get('target_service_tier_name', 'Unknown')
        if tier:
            tiers[tier]['count'] += 1
            tiers[tier]['total'] += payment['amount']

    # Convert to list sorted by revenue (descending)
    result = [
        {'tier': tier, 'count': data['count'], 'total': data['total']}
        for tier, data in tiers.items()
    ]
    result.sort(key=lambda x: x['total'], reverse=True)

    return result


def aggregate_daily_by_category(payments, cyber_year):
    """Aggregate payments by day and category."""
    cyber_current_key = f'cyber_{cyber_year}'
    cyber_current_category = f'cyber_{cyber_year}'

    daily = defaultdict(lambda: {
        'total_count': 0,
        'total_revenue': 0.0,
        cyber_current_key: 0.0,
        'cyber_old': 0.0,
        'normal': 0.0
    })

    for payment in payments:
        date = payment['date']
        category = payment.get('payment_category', 'normal')
        amount = payment['amount']

        daily[date]['total_count'] += 1
        daily[date]['total_revenue'] += amount

        if category == cyber_current_category:
            daily[date][cyber_current_key] += amount
        elif category == 'cyber_old':
            daily[date]['cyber_old'] += amount
        else:
            daily[date]['normal'] += amount

    # Convert to sorted list
    result = []
    for date in sorted(daily.keys()):
        day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%a')
        result.append({
            'date': date,
            'day': day_name,
            'total_count': daily[date]['total_count'],
            'total_revenue': daily[date]['total_revenue'],
            cyber_current_key: daily[date][cyber_current_key],
            'cyber_old': daily[date]['cyber_old'],
            'normal': daily[date]['normal']
        })

    return result


def aggregate_sku_by_tier_data(payments):
    """Aggregate SKUs grouped by target service tier."""
    tier_skus = defaultdict(lambda: defaultdict(lambda: {'count': 0, 'total': 0.0}))

    for payment in payments:
        tier = payment.get('target_service_tier_name', 'Unknown')
        sku = payment.get('sku', 'Unknown')

        if tier and sku:
            tier_skus[tier][sku]['count'] += 1
            tier_skus[tier][sku]['total'] += payment['amount']

    # Convert to nested structure
    result = {}
    for tier, skus in tier_skus.items():
        result[tier] = [
            {'sku': sku, 'count': data['count'], 'total': data['total']}
            for sku, data in skus.items()
        ]
        # Sort by revenue within each tier
        result[tier].sort(key=lambda x: x['total'], reverse=True)

    return result


def calculate_summary_stats(data, payments):
    """Calculate summary statistics."""
    total_payments = len(payments)
    total_revenue = sum(p['amount'] for p in payments)
    avg_per_payment = total_revenue / total_payments if total_payments > 0 else 0

    # Calculate unique days
    unique_days = len(set(p['date'] for p in payments))
    daily_avg = total_payments / unique_days if unique_days > 0 else 0

    return {
        'total_payments': total_payments,
        'total_revenue': total_revenue,
        'avg_per_payment': avg_per_payment,
        'daily_average': daily_avg
    }


def generate_html(data, output_file='recurring_payment_analysis_output.html'):
    """Generate HTML file with visualizations."""
    payments = data['payments']
    cyber_year = data.get('_extracted_year', '2025')

    # Split into categories
    cyber_current, cyber_old, normal, other = filter_payments_by_category(payments, cyber_year)

    # Calculate category statistics
    category_stats = calculate_category_stats(cyber_current, cyber_old, normal, payments, cyber_year)

    # Calculate daily breakdown by category
    daily_by_category = aggregate_daily_by_category(payments, cyber_year)

    # Calculate aggregations for overall data
    daily_data = aggregate_daily_data(payments)
    hourly_data = aggregate_hourly_data(payments)
    tier_data = aggregate_tier_data(payments)
    sku_by_tier_data = aggregate_sku_by_tier_data(payments)
    stats = calculate_summary_stats(data, payments)

    # Calculate aggregations for Cyber current year payments
    cyber_current_daily_data = aggregate_daily_data(cyber_current)
    cyber_current_hourly_data = aggregate_hourly_data(cyber_current)
    cyber_current_tier_data = aggregate_tier_data(cyber_current)
    cyber_current_sku_by_tier_data = aggregate_sku_by_tier_data(cyber_current)

    # Calculate aggregations for Other payments (Cyber Old + Normal)
    other_daily_data = aggregate_daily_data(other)
    other_hourly_data = aggregate_hourly_data(other)
    other_tier_data = aggregate_tier_data(other)
    other_sku_by_tier_data = aggregate_sku_by_tier_data(other)

    # Read template
    template_path = Path(__file__).parent / 'payment_analysis.html'
    with open(template_path, 'r') as f:
        html = f.read()

    # Format summary stats
    html = html.replace('<div class="stat-value">1,971</div>',
                       f'<div class="stat-value">{stats["total_payments"]:,}</div>')
    html = html.replace('<div class="stat-value">$1.31M</div>',
                       f'<div class="stat-value">${stats["total_revenue"]/1000000:.2f}M</div>')
    html = html.replace('<div class="stat-value">$667.75</div>',
                       f'<div class="stat-value">${stats["avg_per_payment"]:.2f}</div>')
    html = html.replace('<div class="stat-value">281/day</div>',
                       f'<div class="stat-value">{stats["daily_average"]:.0f}/day</div>')

    # Update date range in subtitle and title year
    if payments:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').strftime('%B %d')
        end_date = datetime.strptime(payments[-1]['date'], '%Y-%m-%d').strftime('%B %d, %Y')
        html = html.replace('November 1-7, 2025', f'{start_date}-{end_date}')

    # Replace year references in title and headers
    html = html.replace('Nov 2025', f'Nov {cyber_year}')
    html = html.replace('Recurring Payment Analysis - Nov 2025</title>', f'Recurring Payment Analysis - Nov {cyber_year}</title>')
    html = html.replace('CYBER 2025 PAYMENTS', f'CYBER {cyber_year} PAYMENTS')
    html = html.replace('Cyber 2025', f'Cyber {cyber_year}')
    html = html.replace('- Cyber 2025', f'- Cyber {cyber_year}')

    # Update JavaScript variable names and keys to use the dynamic year
    html = html.replace('cyber_2025_count', f'cyber_{cyber_year}_count')
    html = html.replace('cyber_2025_revenue', f'cyber_{cyber_year}_revenue')
    html = html.replace('cyber_2025_pct', f'cyber_{cyber_year}_pct')
    html = html.replace('cyber_2025_revenue_pct', f'cyber_{cyber_year}_revenue_pct')

    # Replace data placeholders
    html = html.replace('const dailyData = [', f'const dailyData = {json.dumps(daily_data, indent=12)}; const _dailyData_old = [')
    html = html.replace('const hourlyData = [', f'const hourlyData = {json.dumps(hourly_data, indent=12)}; const _hourlyData_old = [')
    html = html.replace('/*TIER_DATA_PLACEHOLDER*/[]', json.dumps(tier_data))
    html = html.replace('/*SKU_BY_TIER_DATA_PLACEHOLDER*/{}', json.dumps(sku_by_tier_data))

    # Replace category placeholders
    html = html.replace('/*CATEGORY_STATS_PLACEHOLDER*/{}', json.dumps(category_stats))
    html = html.replace('/*CYBER2025_DAILY_DATA_PLACEHOLDER*/[]', json.dumps(cyber_current_daily_data))
    html = html.replace('/*CYBER2025_HOURLY_DATA_PLACEHOLDER*/[]', json.dumps(cyber_current_hourly_data))
    html = html.replace('/*CYBER2025_TIER_DATA_PLACEHOLDER*/[]', json.dumps(cyber_current_tier_data))
    html = html.replace('/*CYBER2025_SKU_BY_TIER_DATA_PLACEHOLDER*/{}', json.dumps(cyber_current_sku_by_tier_data))
    html = html.replace('/*OTHER_DAILY_DATA_PLACEHOLDER*/[]', json.dumps(other_daily_data))
    html = html.replace('/*OTHER_HOURLY_DATA_PLACEHOLDER*/[]', json.dumps(other_hourly_data))
    html = html.replace('/*OTHER_TIER_DATA_PLACEHOLDER*/[]', json.dumps(other_tier_data))
    html = html.replace('/*OTHER_SKU_BY_TIER_DATA_PLACEHOLDER*/{}', json.dumps(other_sku_by_tier_data))
    html = html.replace('/*DAILY_BY_CATEGORY_PLACEHOLDER*/[]', json.dumps(daily_by_category))

    # Calculate and update key insight
    if hourly_data:
        peak_hours = sorted(hourly_data, key=lambda x: x['count'], reverse=True)[:5]
        peak_hour = peak_hours[0]
        peak_hour_str = f"{peak_hour['hour']}:00"
        peak_revenue = peak_hour['total']

        morning_hours = [h for h in hourly_data if 5 <= h['hour'] <= 10]
        morning_payments = sum(h['count'] for h in morning_hours)
        morning_pct = (morning_payments / stats['total_payments'] * 100) if stats['total_payments'] > 0 else 0

        insight = f"""<h4>Key Insight: Peak Processing Hours</h4>
            <p><strong>5am-10am EST</strong> accounts for <strong>~{morning_pct:.0f}% of all payments</strong> with the absolute peak at <strong>{peak_hour_str}</strong> (${peak_revenue/1000:.0f}K in revenue). The early morning spikes suggest automated recurring billing processing.</p>"""

        html = html.replace('<h4>Key Insight: Peak Processing Hours</h4>', insight)

    # Write output file
    with open(output_file, 'w') as f:
        f.write(html)

    # Get the dynamic keys for the current year
    cyber_current_count_key = f'cyber_{cyber_year}_count'
    cyber_current_revenue_key = f'cyber_{cyber_year}_revenue'
    cyber_current_pct_key = f'cyber_{cyber_year}_pct'
    cyber_current_revenue_pct_key = f'cyber_{cyber_year}_revenue_pct'

    print(f"✓ Generated {output_file}")
    print(f"\nSummary:")
    print(f"  Total Payments: {stats['total_payments']:,}")
    print(f"  Total Revenue: ${stats['total_revenue']:,.2f}")
    print(f"  Average per Payment: ${stats['avg_per_payment']:.2f}")
    print(f"\nPayment Categories:")
    print(f"  Cyber {cyber_year} Payments: {category_stats[cyber_current_count_key]:,} ({category_stats[cyber_current_pct_key]:.1f}%)")
    print(f"  Cyber {cyber_year} Revenue: ${category_stats[cyber_current_revenue_key]:,.2f} ({category_stats[cyber_current_revenue_pct_key]:.1f}%)")
    print(f"  Cyber Old Payments: {category_stats['cyber_old_count']:,} ({category_stats['cyber_old_pct']:.1f}%)")
    print(f"  Cyber Old Revenue: ${category_stats['cyber_old_revenue']:,.2f} ({category_stats['cyber_old_revenue_pct']:.1f}%)")
    print(f"  Normal Payments: {category_stats['normal_count']:,} ({category_stats['normal_pct']:.1f}%)")
    print(f"  Normal Revenue: ${category_stats['normal_revenue']:,.2f} ({category_stats['normal_revenue_pct']:.1f}%)")
    print(f"\nTarget Service Tiers: {len(tier_data)}")
    print(f"Total SKUs: {sum(len(skus) for skus in sku_by_tier_data.values())}")
    print(f"\nOpen {output_file} in your browser to view the interactive visualization")


if __name__ == '__main__':
    import sys

    json_file = sys.argv[1] if len(sys.argv) > 1 else 'recurring_payments.json'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'recurring_payment_analysis_output.html'

    print(f"Loading data from {json_file}...")
    data = load_data(json_file)

    print(f"Generating visualization...")
    generate_html(data, output_file)
