# Cyber Sales Analysis System

Comprehensive analysis system for cyber sales (Black Friday/Cyber Monday) with year-over-year comparisons, cohort tracking, and interactive visualizations.

## 🎯 Overview

Multi-year cyber sales analysis with:
- **Cohort Analysis**: Track customer groups from their first purchase year through renewals
- **Net Revenue Retention (NRR)**: Measure revenue retention and expansion (>100% = growth!)
- **Time-of-Day Patterns**: Hourly payment distribution analysis
- **SKU-Level Breakdowns**: Detailed product performance tracking
- **Interactive Reports**: Chart.js visualizations with hover details
- **Distribution Package**: One-click ZIP generation for sharing

## 📊 Report Types

### 1. Comparison Reports
**Historical Analysis (2020-2025)**
- Cohort compounding matrix showing which year's customers contribute to renewals
- Retention curves tracking each cohort's performance over time
- NRR analysis revealing revenue expansion patterns

**Year-over-Year (Recent)**
- Focused comparison of most recent years
- Projections for partial months
- Growth metrics and trends

### 2. Year Detail Reports (SKU Breakdown)
For each year (2020-2025):
- Complete SKU listing with payment counts and revenue
- Cohort attribution for Cyber Old SKUs
- Category breakdown (Cyber New/Old/Normal)
- Top performers by revenue

### 3. Time-of-Day Analysis (Hourly Patterns)
For each year (2020-2025):
- 24-hour payment distribution charts
- Peak hour identification
- Processing pattern insights
- Separate analysis for Cyber vs Other payments

## 🚀 Quick Start

### Generate All Reports (One Command!)

```bash
# Single command generates everything
./refresh_analysis.sh 2020 2025

# This does:
# 1. Checks/caches historical data (2020-2024)
# 2. Updates current month if in November (2025)
# 3. Regenerates individual year reports (time-of-day analysis)
# 4. Generates year detail reports (SKU breakdowns)
# 5. Creates comparison reports (all-years + 2024-2025)
```

### Package for Distribution

```bash
./package_reports.sh
```

### Output
- `cyber_sales_reports_YYYYMMDD.zip` - Complete package ready to share
- Contains 16 reports total (2 comparison + 6 hourly + 6 detail + index + README)
- Clean corporate styling
- Self-contained with index navigation

## 📁 Directory Structure

```
cyber_sales/
├── cache/
│   ├── historical/YEAR/        # Immutable completed Novembers
│   └── current/YEAR/           # Active month (updates during November)
├── Scripts (committed to git):
│   ├── recurring_payment_analysis.rb     # Data extraction from production
│   ├── generate_analysis.py              # Time-of-day HTML generator
│   ├── cyber_comparison_analysis.py      # Multi-year comparison with cohorts
│   ├── generate_year_report.py           # SKU detail report generator
│   ├── analyze_cyber_november.sh         # Fetch data for one year
│   ├── refresh_analysis.sh               # Master update script
│   ├── package_reports.sh                # Create distribution ZIP
│   └── compare_novembers.sh              # Legacy comparison script
└── Generated files (gitignored):
    ├── *.html                            # All reports
    ├── *.json                            # Data files
    ├── *.csv                             # Export files
    ├── *.zip                             # Distribution packages
    └── cache/                            # Cached data
```

## 🔍 Key Concepts

### Cohort Tracking
**What is a Cohort?**
A group of customers who first purchased in a specific year. For example:
- **2020 Cohort**: Customers who first bought `cyber_2020` SKUs
- Their renewals appear as `cyber_2020` SKUs in 2021, 2022, 2023...

**Cohort Compounding**
Each year's "Cyber Old" revenue is the sum of multiple aging cohorts:
```
2024 Cyber Old ($2.59M) =
    2020 Cohort: $0.39M (17% of original)
  + 2021 Cohort: $0.53M (22% of original)
  + 2022 Cohort: $0.82M (27% of original)
  + 2023 Cohort: $0.85M (59% of original)
```

### Net Revenue Retention (NRR)
**Formula**: (Next Year Cyber Old Revenue / This Year Cyber New Revenue) × 100

**Interpretation**:
- **< 100%**: Revenue decline from cohort (churn/downgrades)
- **= 100%**: Perfect retention (same revenue)
- **> 100%**: Revenue expansion! (upsells, upgrades, usage growth)

**Example from 2023→2024**:
- 2023 Cyber New: $1.44M
- 2024 Cyber Old: $2.59M
- **NRR: 180%** ← This is GOOD! Means revenue grew from existing customers

**Why >100%?**
2024's Cyber Old includes renewals from 2020, 2021, 2022, AND 2023 cohorts. The compounding effect of multiple cohorts can exceed any single year's new sales.

### Payment Categories

**Cyber New**: First-time purchases for current year
- SKU pattern: `cyber_2025`, `elite_pass_cyber_2025_reg`, etc.
- Indicator of future renewal revenue

**Cyber Old**: Renewals from previous years
- SKU pattern: `cyber_2020`, `cyber_2021`, etc. (any year ≠ current)
- Shows compounding effect of retained customers

**Normal**: Regular (non-cyber) subscriptions
- Everything else
- Baseline recurring revenue

## 📊 Main Scripts

### `refresh_analysis.sh` - Master Script ⭐
```bash
# Update data and regenerate ALL reports
./refresh_analysis.sh 2025

# Full historical refresh (2020-2025)
./refresh_analysis.sh 2020 2025
```

**What it does** (all in one!):
1. Checks historical cache (pulls if missing)
2. Updates current month if in November
3. Regenerates individual year reports (time-of-day analysis)
4. Generates year detail reports (SKU breakdowns)
5. Creates all-years comparison (2020-2025)
6. Creates 2-year comparison (2024-2025)
7. Smart caching - only fetches what's needed

### `cyber_comparison_analysis.py` - Cohort Analysis
```bash
# Full historical analysis
python3 cyber_comparison_analysis.py 2020 2021 2022 2023 2024 2025

# Recent comparison
python3 cyber_comparison_analysis.py 2024 2025
```

**Output**:
- Cohort compounding matrix
- Retention curves by cohort
- NRR metrics
- Revenue projections

### `generate_year_report.py` - SKU Details
```bash
# Generate detail report for specific year
python3 generate_year_report.py 2025
```

**Output**:
- Complete SKU listing
- Cohort attribution for renewals
- Revenue and payment counts
- Category breakdowns

### `package_reports.sh` - Distribution Package
```bash
# Create ZIP with all reports
./package_reports.sh
```

**Output**:
- `cyber_sales_reports_YYYYMMDD.zip`
- Includes index.html for navigation
- README with instructions
- All 14 reports (comparison + detail + hourly)

## 🎓 Reading the Reports

### Cohort Compounding Matrix
Shows revenue contribution by cohort to each year:

| Analysis Year | 2020 Cohort | 2021 Cohort | 2022 Cohort | Total Cyber Old |
|---------------|-------------|-------------|-------------|-----------------|
| 2021          | $1.46M      | —           | —           | $1.46M          |
| 2022          | $0.94M      | $1.45M      | —           | $2.39M          |
| 2023          | $0.58M      | $0.81M      | $1.42M      | $2.81M          |

**Insight**: Each cohort declines over time, but total grows as new cohorts are added.

### Retention Curves
Track each cohort's journey:
- **2020 Cohort**: Started at $2.27M → 64% year 1 → 41% year 2 → 26% year 3
- **2021 Cohort**: Started at $2.41M → 60% year 1 → 34% year 2
- Shows retention patterns and cohort health

### Time-of-Day Insights
From hourly analysis:
- **Peak Hours**: 5am-10am EST accounts for ~74% of payments
- **Peak Hour**: 5am (automated recurring billing)
- **Revenue Peak**: 9am (higher-value transactions)

## 🛠️ Development & Customization

### Adding a New Report Type

1. Create generator script (Python/Ruby)
2. Add to `package_reports.sh`:
```bash
echo "Copying new report type..."
for file in new_report_*.html; do
    cp "$file" "$PACKAGE_DIR/"
done
```
3. Update `index.html` with navigation links
4. Update README in package script

### Modifying Cohort Analysis

Edit `cyber_comparison_analysis.py`:
- `analyze_cohort_breakdown()` - Cohort aggregation logic
- `build_cohort_compounding_matrix()` - Matrix construction
- `calculate_cohort_retention_curves()` - Retention tracking

### Customizing HTML Styling

All reports use consistent color scheme:
- Primary: `#2c5aa0` (blue)
- Backgrounds: `#f8f9fa` (light gray)
- Hover: `rgba(44, 90, 160, 0.1)`

Edit CSS in generator scripts to change styling.

## 🚀 Nightly SharePoint publishing (2026 onward)

Replaces the daily zip + email. One folder in SharePoint, same file names overwritten every night, so readers keep one link:
`hedgeye.sharepoint.com/sites/operations2` > `General/File Transfer/Cyber/Cyber <year>` (`index.html`, `Cyber-<year>-vs-prior-years.html`, `Year-<year>-SKU-detail.html`, `Hourly-<year>.html`). SharePoint renders these (Chart.js is inlined, no CDN).

```bash
./publish_cyber_report.sh                       # DRY_RUN=1 default: fetch + build into dist_single/, no upload
DRY_RUN=0 ./publish_cyber_report.sh             # also upload to SharePoint
SKIP_FETCH=1 DRY_RUN=0 ./publish_cyber_report.sh  # reuse cache/, no production access
```

- **Schedule:** `launchd/com.hedgeye.cyber-sales-report.plist`, twice daily, 02:45 and 17:00 local (Mac on PST = 5:45 AM ET and 8 PM ET / COB Pacific). The morning run compares complete days; the evening run includes today and counts every prior year only up to the same hour. Install: copy to `~/Library/LaunchAgents/` and `launchctl load` it. Logs: `~/Library/Logs/cyber-sales-report.log`. A failure shows a macOS notification naming the step; readers see the last good copy, and every page carries a "Data as of" banner.
- **Data:** one read-only `kubectl exec` into production admin-web per run (`analyze_cyber_november.sh`), recurring payments only. `plan_pricing_analysis.rb` / `analyze_plan_pricings.sh` pull plan pricing config for classification checks.
- **Cyber 2026 classification** (`recurring_payment_analysis.rb`): SKU contains `CY26`/`CYBER26` (also `cyber_YYYY` for earlier years); `cyber_202603` (March flash sale) is not Cyber; `MNG-SUBS-COMP-UPG` is Cyber (comp conversion), `MNG-SUBS-INT-UPG` is not (monthly to annual, runs all year). Per Matt, 2026-11-03.
- **Index** (`build_index.py`) compares through the last complete day, so a 6 AM run never compares a partial day to full prior-year days.
- Active Nov 1 to Dec 9; `launchctl unload` it afterward.

## 📦 Distribution (legacy zip)

### For SharePoint
1. Upload `cyber_sales_reports_YYYYMMDD.zip`
2. Users download and extract
3. Open `index.html` to navigate

**Note**: SharePoint won't display HTML directly due to JavaScript security. Download-based distribution works perfectly.

### For Email
- Attach ZIP file (typically < 200KB)
- Include brief instructions to extract and open index.html

### For Teams
- Share in Files tab of channel
- Provide link for download

## 🔧 Troubleshooting

### Missing Data for Year
```bash
# Fetch specific year
./refresh_analysis.sh YEAR
```

### Charts Not Rendering
- Requires internet for Chart.js CDN
- Open in browser with active connection

### Regenerate Everything
```bash
# Clean slate
rm -f *.html *.zip

# Regenerate all reports (one command does it all!)
./refresh_analysis.sh 2020 2025

# Package for distribution
./package_reports.sh
```

## 💡 Pro Tips

1. **Track NRR Trends**: Is it improving or declining year-over-year?
2. **Watch Cohort Half-Life**: How long until cohort drops to 50% of original revenue?
3. **Project Next Year**: Current year Cyber New × Average NRR = Expected renewals
4. **Compare Peak Hours**: Are payment patterns shifting over time?
5. **SKU Performance**: Which products have best renewal rates?

## 📈 Key Metrics to Monitor

**Business Health**:
- NRR > 100% = Revenue expansion (excellent)
- NRR 80-100% = Solid retention (good)
- NRR < 80% = Concerning churn (investigate)

**Growth Indicators**:
- Cyber New revenue (predictor of future renewals)
- Year-over-year Cyber New growth
- Cohort retention curves (getting better or worse?)

**Operational Insights**:
- Peak payment hours (optimize for system capacity)
- SKU diversity (product portfolio health)
- Payment concentration (dependency risk)

## 🔮 Future Enhancements

- User-level cohort tracking (match user_ids across years)
- Upgrade/downgrade path analysis
- Predictive modeling for renewal rates
- Automated anomaly detection
- Integration with BI tools (Looker, Tableau)
- Real-time dashboard during November

## 👥 Team Usage

### For Analysts
- Run `./refresh_analysis.sh` weekly during November
- Package and distribute reports: `./package_reports.sh`
- Focus on NRR and cohort trends

### For Executives
- Open `index.html` in distributed package
- Navigate to comparison reports for high-level view
- Key metrics: NRR, Cyber New growth, retention trends

### For Product Team
- Review year detail reports for SKU performance
- Analyze which products drive renewals
- Use cohort attribution to understand upgrade patterns

## 📞 Support

Questions or issues:
1. Check this README
2. Review script comments
3. Verify K8s production access
4. Check `cache/` directory structure

---

**Last Updated**: November 2025
**System Version**: 3.0 (Cohort Analysis + Distribution Package)
**Author**: Forrest Chang
