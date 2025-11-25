# Recurring Payment Analysis

Complete workflow for analyzing recurring payments from production Kubernetes pod with interactive visualizations.

## Files Created

1. **recurring_payment_analysis.rb** - Ruby script to extract payment data (updated with target_service_tier)
2. **run_payment_analysis.sh** - Bash orchestration script
3. **payment_analysis.html** - HTML template with Chart.js visualizations
4. **generate_analysis.py** - Python script to generate final HTML from JSON data

## What Gets Analyzed

### Cyber vs Regular Tracking
The system automatically identifies "Cyber" products by detecting SKUs matching the pattern `cyber_YYYY` (e.g., cyber_2025, cyber_2024). All metrics are calculated separately for:
- **Cyber Payments** - Products with cyber SKUs
- **Regular Payments** - All other products

### Metrics
- **Cyber vs Regular Comparison** - Side-by-side payment counts and revenue
- **Total Revenue** - Sum of all payment amounts
- **Revenue per Day** - Daily breakdown with counts (separate for cyber/regular)
- **Hourly Activity** - When during the day payments occur (separate for cyber/regular)
- **Target Service Tier Breakdown** - Revenue and count by tier (separate for cyber/regular)
- **SKU Analysis** - All SKUs grouped by their service tier (separate for cyber/regular)

### Data Fields Extracted
- Payment basics: id, amount, created_at, status, user_id
- Temporal: date, hour, day_of_week
- Product info: target_service_tier_name, sku, sku_price, interval
- Classification: is_cyber (boolean)
- Additional: offer_type, category, promo_code

## Usage

### Step 1: Run Analysis on Production Pod

```bash
./run_payment_analysis.sh
```

This will:
1. Find the first `admin-web` pod in the `hedgeye-apps-vf4dc` namespace (production context)
2. Copy `recurring_payment_analysis.rb` to the pod
3. Execute it via `rails runner`
4. Download `recurring_payments.json` and `recurring_payments.csv`

### Step 2: Generate Interactive Visualization

```bash
python3 generate_analysis.py
```

This will:
1. Read `recurring_payments.json`
2. Calculate all aggregations (daily, hourly, tier, SKU)
3. Generate `recurring_payment_analysis_output.html`

### Step 3: View Results

```bash
open recurring_payment_analysis_output.html
```

## Visualizations Included

### Overview Section
1. **Cyber vs Regular Comparison Cards** - Summary stats showing payment counts and revenue for each category
2. **Cyber vs Regular Bar Chart** - Visual comparison of counts and revenue

### Overall Statistics
3. **Summary Statistics** - Total payments, revenue, averages across all payments
4. **Overall Insights** - Key findings about peak hours and patterns

### Cyber Payments Section
5. **Daily Revenue Chart (Cyber)** - Dual-axis bar chart for cyber payments only
6. **Hourly Distribution (Cyber)** - When cyber payments occur throughout the day
7. **Tier Revenue Chart (Cyber)** - Target service tiers for cyber products
8. **SKU Tables (Cyber)** - All cyber SKUs grouped by tier

### Regular Payments Section
9. **Daily Revenue Chart (Regular)** - Dual-axis bar chart for regular payments only
10. **Hourly Distribution (Regular)** - When regular payments occur throughout the day
11. **Tier Revenue Chart (Regular)** - Target service tiers for regular products
12. **SKU Tables (Regular)** - All regular SKUs grouped by tier

### Additional
13. **Daily Details Table** - Sortable table with all daily metrics

## Customization

### Change Date Range

Edit line 131 in `recurring_payment_analysis.rb`:

```ruby
analyzer = RecurringPaymentAnalyzer.new(Date.new(2025, 11, 1))  # Change date here
```

### Custom Output Paths

The Python script accepts arguments:

```bash
python3 generate_analysis.py recurring_payments.json my_custom_output.html
```

### Add More Fields

To extract additional fields, update the `extract_payment_data` method in `recurring_payment_analysis.rb` (lines 27-65).

## Requirements

- **Kubernetes access**: `production` context configured with access to `hedgeye-apps-vf4dc` namespace
- **kubectl**: Installed and configured
- **Python 3**: For visualization generation (no external packages needed)
- **Modern browser**: To view the interactive HTML output

## Notes

- Analysis runs directly in the Rails console of the production pod
- All data is exported to `/tmp/` on the pod before retrieval
- The HTML uses Chart.js CDN (requires internet connection to view)
- No heavy Python frameworks needed - just stdlib JSON processing
