#!/bin/bash
#
# cache_historical_years.sh
#
# Pulls and caches historical cyber sales data for years 2020-2023.
# Only fetches data if it doesn't already exist in the cache.
# This script should be run once to populate the historical cache.
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
HISTORICAL_DIR="$CACHE_DIR/historical"

echo "======================================"
echo "Caching Historical Cyber Sales Data"
echo "======================================"
echo ""

# Historical years to cache (completed Novembers)
HISTORICAL_YEARS=(2020 2021 2022 2023)

for year in "${HISTORICAL_YEARS[@]}"; do
    echo "--------------------------------------"
    echo "Processing Year: $year"
    echo "--------------------------------------"

    # Check if this year is already cached
    if [ -f "$HISTORICAL_DIR/$year/recurring_payments_$year.json" ]; then
        echo "✓ $year already cached, skipping..."
        echo ""
        continue
    fi

    echo "→ Fetching $year data from production..."

    # Run the analysis script for this year
    if ./analyze_cyber_november.sh $year; then
        echo "✓ Successfully fetched $year data"

        # Create year directory if it doesn't exist
        mkdir -p "$HISTORICAL_DIR/$year"

        # Move files to cache
        if [ -f "recurring_payments_$year.json" ]; then
            mv "recurring_payments_$year.json" "$HISTORICAL_DIR/$year/"
            echo "  ✓ Cached JSON"
        fi

        if [ -f "recurring_payments_$year.csv" ]; then
            mv "recurring_payments_$year.csv" "$HISTORICAL_DIR/$year/"
            echo "  ✓ Cached CSV"
        fi

        if [ -f "recurring_payment_analysis_$year.html" ]; then
            mv "recurring_payment_analysis_$year.html" "$HISTORICAL_DIR/$year/"
            echo "  ✓ Cached HTML"
        fi

        echo "✓ $year data cached successfully"
    else
        echo "✗ Failed to fetch $year data"
        echo "  You may need to run this script again later"
    fi

    echo ""
done

echo "======================================"
echo "Historical Cache Summary"
echo "======================================"
echo ""

# Show what's cached
for year in "${HISTORICAL_YEARS[@]}"; do
    if [ -f "$HISTORICAL_DIR/$year/recurring_payments_$year.json" ]; then
        size=$(du -h "$HISTORICAL_DIR/$year/recurring_payments_$year.json" | cut -f1)
        echo "✓ $year: Cached ($size)"
    else
        echo "✗ $year: Not cached"
    fi
done

echo ""
echo "Historical caching complete!"
echo ""
echo "To update current year data, use: ./update_current_month.sh"
