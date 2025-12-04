#!/bin/bash
#
# refresh_analysis.sh
#
# Master script that intelligently refreshes cyber sales analysis:
# 1. Ensures all historical years are cached
# 2. Updates current month if in November
# 3. Regenerates individual year HTML reports
# 4. Generates comprehensive comparison report
#
# Usage: ./refresh_analysis.sh [start_year] [end_year]
# Example: ./refresh_analysis.sh 2020 2025
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default year range if not specified
START_YEAR=${1:-2020}
END_YEAR=${2:-$(date +%Y)}
CURRENT_MONTH=$(date +%m)
CURRENT_YEAR=$(date +%Y)
CURRENT_DAY=$(date +%d)

# Check if we're in Cyber period: November OR December 1-6 (Cyber Week through Friday Dec 5)
# Note: Dec 6 included to handle timezone differences (pod runs in EST)
IN_CYBER_PERIOD=false
if [ "$CURRENT_MONTH" = "11" ]; then
    IN_CYBER_PERIOD=true
elif [ "$CURRENT_MONTH" = "12" ] && [ "$CURRENT_DAY" -le "06" ]; then
    IN_CYBER_PERIOD=true
fi

echo "============================================================"
echo "Cyber Sales Analysis Refresh"
echo "============================================================"
echo "Year Range: $START_YEAR - $END_YEAR"
echo "Current Date: $(date +%Y-%m-%d)"
echo "============================================================"
echo ""

# Step 1: Cache historical years
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Checking Historical Data Cache"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for ((year=$START_YEAR; year<=$END_YEAR; year++)); do
    # Skip current year if we're in Cyber period (it's not historical yet)
    if [ "$year" -eq "$CURRENT_YEAR" ] && [ "$IN_CYBER_PERIOD" = true ]; then
        echo "→ Skipping $year (current Cyber period, will handle separately)"
        continue
    fi

    # Check if this year is already cached in historical
    if [ -f "cache/historical/$year/recurring_payments_$year.json" ]; then
        echo "✓ $year: Already cached"
    else
        echo "→ $year: Not cached, fetching..."
        if ./analyze_cyber_november.sh $year; then
            mkdir -p "cache/historical/$year"
            mv recurring_payments_$year.* recurring_payment_analysis_$year.html "cache/historical/$year/" 2>/dev/null || true
            echo "  ✓ Cached $year"
        else
            echo "  ✗ Failed to fetch $year (may not exist or connection issue)"
        fi
    fi
done

echo ""

# Step 2: Update current month if in Cyber period (November or December 1st)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Checking Current Month Data"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$IN_CYBER_PERIOD" = true ] && [ "$CURRENT_YEAR" -ge "$START_YEAR" ] && [ "$CURRENT_YEAR" -le "$END_YEAR" ]; then
    echo "→ Currently in Cyber period (Nov-Dec 1) for $CURRENT_YEAR, updating current month data..."
    echo ""
    ./update_current_month.sh
else
    echo "ℹ️  Not in Cyber period or current year outside range, skipping current month update"
fi

echo ""

# Step 3: Regenerate individual year HTML reports (for years that have data)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Regenerating Individual Year Reports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

YEARS_WITH_DATA=()

for ((year=$START_YEAR; year<=$END_YEAR; year++)); do
    # Find the JSON file for this year
    JSON_FILE=""
    if [ -f "cache/historical/$year/recurring_payments_$year.json" ]; then
        JSON_FILE="cache/historical/$year/recurring_payments_$year.json"
    elif [ -f "cache/current/$year/recurring_payments_$year.json" ]; then
        JSON_FILE="cache/current/$year/recurring_payments_$year.json"
    fi

    if [ -n "$JSON_FILE" ]; then
        echo "→ Regenerating $year HTML report..."
        OUTPUT_DIR=$(dirname "$JSON_FILE")
        OUTPUT_FILE="$OUTPUT_DIR/recurring_payment_analysis_$year.html"

        if python3 generate_analysis.py "$JSON_FILE" "$OUTPUT_FILE"; then
            echo "  ✓ Generated $OUTPUT_FILE"
            # Copy to working directory for packaging
            cp "$OUTPUT_FILE" "recurring_payment_analysis_$year.html"
            echo "  ✓ Copied to working directory"
            YEARS_WITH_DATA+=($year)
        else
            echo "  ✗ Failed to generate $year HTML"
        fi
    else
        echo "ℹ️  Skipping $year (no data available)"
    fi
done

echo ""

# Step 4: Generate year detail reports (SKU-level deep dives)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Generating Year Detail Reports (SKU Breakdowns)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for year in "${YEARS_WITH_DATA[@]}"; do
    echo "→ Generating SKU detail for $year..."
    if python3 generate_year_report.py $year; then
        echo "  ✓ Generated year_${year}_detail.html"
    else
        echo "  ✗ Failed to generate year detail for $year"
    fi
done

echo ""

# Step 5: Generate comparison reports
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Generating Comparison Reports"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ ${#YEARS_WITH_DATA[@]} -ge 2 ]; then
    # Generate all-years comparison
    echo "→ Generating comparison for all years: ${YEARS_WITH_DATA[*]}"
    echo ""
    if python3 cyber_comparison_analysis.py "${YEARS_WITH_DATA[@]}"; then
        # Get first and last year for filename (bash 3.x compatible)
        FIRST_YEAR=${YEARS_WITH_DATA[0]}
        LAST_YEAR=${YEARS_WITH_DATA[${#YEARS_WITH_DATA[@]}-1]}
        COMPARISON_FILE="cyber_november_comparison_${FIRST_YEAR}_${LAST_YEAR}.html"
        echo ""
        echo "  ✓ All-years comparison ready: $COMPARISON_FILE"
    else
        echo "  ✗ Failed to generate all-years comparison report"
    fi

    echo ""

    # Generate 2-year comparison if we have 2024 and 2025
    if [[ " ${YEARS_WITH_DATA[*]} " =~ " 2024 " ]] && [[ " ${YEARS_WITH_DATA[*]} " =~ " 2025 " ]]; then
        echo "→ Generating 2024-2025 comparison (comprehensive format)..."
        if python3 cyber_comparison_analysis.py 2024 2025; then
            echo "  ✓ 2-year comparison ready: cyber_november_comparison_2024_2025.html"
        else
            echo "  ✗ Failed to generate 2024-2025 comparison"
        fi
    fi
else
    echo "ℹ️  Need at least 2 years of data for comparison (found ${#YEARS_WITH_DATA[@]})"
fi

echo ""
echo "============================================================"
echo "✓ Refresh Complete!"
echo "============================================================"
echo ""
echo "Data Summary:"
echo "  Years with data: ${#YEARS_WITH_DATA[@]} (${YEARS_WITH_DATA[*]})"
echo ""
echo "View Reports:"
for year in "${YEARS_WITH_DATA[@]}"; do
    if [ -f "cache/historical/$year/recurring_payment_analysis_$year.html" ]; then
        echo "  $year: cache/historical/$year/recurring_payment_analysis_$year.html"
    elif [ -f "cache/current/$year/recurring_payment_analysis_$year.html" ]; then
        echo "  $year: cache/current/$year/recurring_payment_analysis_$year.html"
    fi
done

if [ ${#YEARS_WITH_DATA[@]} -ge 2 ]; then
    FIRST_YEAR=${YEARS_WITH_DATA[0]}
    LAST_YEAR=${YEARS_WITH_DATA[${#YEARS_WITH_DATA[@]}-1]}
    COMPARISON_FILE="cyber_november_comparison_${FIRST_YEAR}_${LAST_YEAR}.html"

    if [ -f "$COMPARISON_FILE" ]; then
        echo ""
        echo "  All-years comparison: $COMPARISON_FILE"
    fi

    if [ -f "cyber_november_comparison_2024_2025.html" ]; then
        echo "  2024-2025 comparison: cyber_november_comparison_2024_2025.html"
    fi
fi

echo ""
echo "Year Detail Reports:"
for year in "${YEARS_WITH_DATA[@]}"; do
    if [ -f "year_${year}_detail.html" ]; then
        echo "  $year SKU breakdown: year_${year}_detail.html"
    fi
done

echo ""
echo "Quick View:"
echo "  open index.html"

echo ""
