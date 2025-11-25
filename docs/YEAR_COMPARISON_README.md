# Cyber November Year-over-Year Comparison

Compare Cyber November performance across multiple years to identify patterns and trends.

## Quick Start

### Compare Multiple Years (Recommended)

```bash
# Compare 2023, 2024, and 2025 (default)
./compare_novembers.sh

# Compare specific years
./compare_novembers.sh 2024 2025

# Compare any combination
./compare_novembers.sh 2023 2024 2025
```

This will:
1. Fetch data from production for each year
2. Generate individual year reports
3. Create a comparison report showing side-by-side metrics

### Analyze Single Year

```bash
# Analyze just one year
./analyze_cyber_november.sh 2024
```

## What You Get

### Individual Year Reports
- `recurring_payment_analysis_2023.html`
- `recurring_payment_analysis_2024.html`
- `recurring_payment_analysis_2025.html`

Each shows:
- Cyber current year (e.g., cyber_2024 for 2024)
- Cyber old (all other cyber years)
- Normal payments
- Daily patterns, hourly distribution, tier breakdowns

### Comparison Report
- `cyber_november_comparison.html`

Shows:
- Side-by-side revenue comparison table
- Stacked bar chart comparing all years
- Growth patterns and trends
- Percentage breakdowns

## How It Works

The system uses the `CYBER_YEAR` environment variable to:
1. Set the analysis period to November of that year
2. Categorize SKUs: `cyber_YYYY` matching the year = "current", others = "old"

Example:
- Analyzing 2024: `cyber_2024` = current, `cyber_2023` = old
- Analyzing 2025: `cyber_2025` = current, `cyber_2024` + `cyber_2023` = old

## Files Generated

### Data Files (per year)
- `recurring_payments_YYYY.json` - Full payment data
- `recurring_payments_YYYY.csv` - Spreadsheet export

### Reports (per year)
- `recurring_payment_analysis_YYYY.html` - Interactive visualization

### Comparison
- `cyber_november_comparison.html` - Multi-year comparison

## Use Cases

### Pattern Discovery
- Compare peak hours across years
- Identify which days of November perform best
- See if Cyber Monday patterns change

### Revenue Analysis
- Track year-over-year growth
- Compare cyber product adoption rates
- Identify declining/growing segments

### Strategic Planning
- Use historical patterns to forecast next year
- Identify successful promotional timing
- Compare product mix evolution

## Examples

### Compare last 3 years
```bash
./compare_novembers.sh
```

### Just analyze 2024
```bash
./analyze_cyber_november.sh 2024
```

### Compare 2024 vs 2025
```bash
./compare_novembers.sh 2024 2025
```

## Technical Notes

- Analysis runs on production admin-web pod
- Uses `CYBER_YEAR` environment variable for parameterization
- Each year's data is kept separate for clean comparison
- Comparison script aggregates and visualizes across years
