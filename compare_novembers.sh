#!/bin/bash

# Compare multiple Cyber November years
# Usage: ./compare_novembers.sh [years...]
# Example: ./compare_novembers.sh 2023 2024 2025
#          ./compare_novembers.sh 2024 2025
#
# This script uses the smart caching system:
# - Checks cache first before fetching from production
# - Updates current month if in November
# - Generates comprehensive comparison report

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Default to last 3 years if no args provided
if [ $# -eq 0 ]; then
    CURRENT_YEAR=$(date +%Y)
    YEARS=($((CURRENT_YEAR - 2)) $((CURRENT_YEAR - 1)) $CURRENT_YEAR)
else
    YEARS=("$@")
fi

CURRENT_MONTH=$(date +%m)
CURRENT_YEAR=$(date +%Y)
CURRENT_DAY=$(date +%d)

# Check if we're in Cyber period: November OR December 1st (Cyber Monday)
IN_CYBER_PERIOD=false
if [ "$CURRENT_MONTH" = "11" ]; then
    IN_CYBER_PERIOD=true
elif [ "$CURRENT_MONTH" = "12" ] && [ "$CURRENT_DAY" = "01" ]; then
    IN_CYBER_PERIOD=true
fi

echo "======================================"
echo "  Cyber November Year Comparison"
echo "  Years: ${YEARS[@]}"
echo "======================================"
echo ""

YEARS_WITH_DATA=()

# Analyze/fetch each year (using smart caching)
for year in "${YEARS[@]}"; do
    echo ""
    echo ">>> Processing ${year}..."

    # Check if data already exists in cache
    CACHED=false
    if [ -f "cache/historical/$year/recurring_payments_$year.json" ]; then
        echo "  ✓ Found in historical cache"
        CACHED=true
        YEARS_WITH_DATA+=($year)
    elif [ -f "cache/current/$year/recurring_payments_$year.json" ]; then
        echo "  ✓ Found in current cache"
        CACHED=true
        YEARS_WITH_DATA+=($year)

        # If it's current year during Cyber period, update it
        if [ "$year" -eq "$CURRENT_YEAR" ] && [ "$IN_CYBER_PERIOD" = true ]; then
            echo "  → Updating current Cyber period data..."
            ./update_current_month.sh
        fi
    fi

    # If not cached, fetch it
    if [ "$CACHED" = false ]; then
        echo "  → Not cached, fetching from production..."
        if ./analyze_cyber_november.sh $year; then
            # Decide where to store it
            if [ "$year" -eq "$CURRENT_YEAR" ] && [ "$IN_CYBER_PERIOD" = true ]; then
                # Current Cyber period - store in current/
                mkdir -p "cache/current/$year"
                mv recurring_payments_$year.* recurring_payment_analysis_$year.html "cache/current/$year/" 2>/dev/null || true
                echo "  ✓ Stored in cache/current/$year/"
            else
                # Historical - store in historical/
                mkdir -p "cache/historical/$year"
                mv recurring_payments_$year.* recurring_payment_analysis_$year.html "cache/historical/$year/" 2>/dev/null || true
                echo "  ✓ Stored in cache/historical/$year/"
            fi
            YEARS_WITH_DATA+=($year)
        else
            echo "  ✗ Failed to fetch $year (may not exist)"
        fi
    fi
done

echo ""
echo "======================================"
echo "  Data Collection Complete"
echo "======================================"
echo ""
echo "Years with data: ${#YEARS_WITH_DATA[@]} (${YEARS_WITH_DATA[*]})"
echo ""

if [ ${#YEARS_WITH_DATA[@]} -lt 2 ]; then
    echo "✗ Error: Need at least 2 years of data for comparison"
    exit 1
fi

# Regenerate individual year HTML reports
echo "Regenerating individual year reports..."
for year in "${YEARS_WITH_DATA[@]}"; do
    # Find the JSON file
    JSON_FILE=""
    if [ -f "cache/historical/$year/recurring_payments_$year.json" ]; then
        JSON_FILE="cache/historical/$year/recurring_payments_$year.json"
    elif [ -f "cache/current/$year/recurring_payments_$year.json" ]; then
        JSON_FILE="cache/current/$year/recurring_payments_$year.json"
    fi

    if [ -n "$JSON_FILE" ]; then
        OUTPUT_DIR=$(dirname "$JSON_FILE")
        OUTPUT_FILE="$OUTPUT_DIR/recurring_payment_analysis_$year.html"
        python3 generate_analysis.py "$JSON_FILE" "$OUTPUT_FILE"
        echo "  ✓ $year"
    fi
done

echo ""
echo "Generating comparison report..."
python3 cyber_comparison_analysis.py "${YEARS_WITH_DATA[@]}"

# Get first and last year for filename (bash 3.x compatible)
FIRST_YEAR=${YEARS_WITH_DATA[0]}
LAST_YEAR=${YEARS_WITH_DATA[${#YEARS_WITH_DATA[@]}-1]}
COMPARISON_FILE="cyber_november_comparison_${FIRST_YEAR}_${LAST_YEAR}.html"

echo ""
echo "======================================"
echo "  ✓ COMPARISON COMPLETE"
echo "======================================"
echo ""
echo "View individual year reports:"
for year in "${YEARS_WITH_DATA[@]}"; do
    if [ -f "cache/historical/$year/recurring_payment_analysis_$year.html" ]; then
        echo "  - cache/historical/$year/recurring_payment_analysis_$year.html"
    elif [ -f "cache/current/$year/recurring_payment_analysis_$year.html" ]; then
        echo "  - cache/current/$year/recurring_payment_analysis_$year.html"
    fi
done
echo ""
echo "View comparison report:"
echo "  - $COMPARISON_FILE"
echo ""
echo "Quick view: open $COMPARISON_FILE"
echo ""
