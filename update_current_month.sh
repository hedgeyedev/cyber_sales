#!/bin/bash
#
# update_current_month.sh
#
# Updates current month (November) data if we're currently in November.
# After November ends, this data becomes historical and shouldn't be updated.
# Stores current month data in cache/current/{year}/
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
CURRENT_DIR="$CACHE_DIR/current"
HISTORICAL_DIR="$CACHE_DIR/historical"

# Get current date info
CURRENT_YEAR=$(date +%Y)
CURRENT_MONTH=$(date +%m)
CURRENT_DAY=$(date +%d)

echo "======================================"
echo "Update Current Month Data"
echo "======================================"
echo "Current Date: $(date +%Y-%m-%d)"
echo ""

# Check if we're in Cyber period (November or December 1-9)
# Cyber Week runs through Friday Dec 5, extended buffer to allow final reports
IN_CYBER_PERIOD=false
if [ "$CURRENT_MONTH" = "11" ]; then
    IN_CYBER_PERIOD=true
    PERIOD_DESC="November (Cyber Month)"
elif [ "$CURRENT_MONTH" = "12" ] && [ "$CURRENT_DAY" -le "09" ]; then
    IN_CYBER_PERIOD=true
    PERIOD_DESC="Cyber Week (Dec 1-5)"
fi

if [ "$IN_CYBER_PERIOD" = false ]; then
    echo "⚠️  Not currently in Cyber period (month: $CURRENT_MONTH, day: $CURRENT_DAY)"
    echo ""
    echo "If Cyber period has ended, you should move $CURRENT_YEAR to historical:"
    echo "  ./move_to_historical.sh $CURRENT_YEAR"
    echo ""
    exit 0
fi

# We're in Cyber period, update current year data
echo "→ Updating $PERIOD_DESC $CURRENT_YEAR data..."
echo ""

# Run the analysis script for current year
if ./analyze_cyber_november.sh $CURRENT_YEAR; then
    echo ""
    echo "✓ Successfully fetched $CURRENT_YEAR data"

    # Create year directory if it doesn't exist
    mkdir -p "$CURRENT_DIR/$CURRENT_YEAR"

    # Move files to current cache
    if [ -f "recurring_payments_$CURRENT_YEAR.json" ]; then
        mv "recurring_payments_$CURRENT_YEAR.json" "$CURRENT_DIR/$CURRENT_YEAR/"
        echo "  ✓ Updated JSON in cache/current/$CURRENT_YEAR/"
    fi

    if [ -f "recurring_payments_$CURRENT_YEAR.csv" ]; then
        mv "recurring_payments_$CURRENT_YEAR.csv" "$CURRENT_DIR/$CURRENT_YEAR/"
        echo "  ✓ Updated CSV in cache/current/$CURRENT_YEAR/"
    fi

    if [ -f "recurring_payment_analysis_$CURRENT_YEAR.html" ]; then
        mv "recurring_payment_analysis_$CURRENT_YEAR.html" "$CURRENT_DIR/$CURRENT_YEAR/"
        echo "  ✓ Updated HTML in cache/current/$CURRENT_YEAR/"
    fi

    echo ""
    echo "======================================"
    echo "Update Summary"
    echo "======================================"

    if [ -f "$CURRENT_DIR/$CURRENT_YEAR/recurring_payments_$CURRENT_YEAR.json" ]; then
        # Show file info
        size=$(du -h "$CURRENT_DIR/$CURRENT_YEAR/recurring_payments_$CURRENT_YEAR.json" | cut -f1)
        payments=$(grep -o '"total_payments": [0-9]*' "$CURRENT_DIR/$CURRENT_YEAR/recurring_payments_$CURRENT_YEAR.json" | cut -d' ' -f2)
        revenue=$(grep -o '"total_revenue": [0-9.]*' "$CURRENT_DIR/$CURRENT_YEAR/recurring_payments_$CURRENT_YEAR.json" | cut -d' ' -f2)

        echo ""
        echo "$PERIOD_DESC $CURRENT_YEAR:"
        echo "  Payments: $payments"
        echo "  Revenue: \$$revenue"
        echo "  File size: $size"
        echo ""
        echo "View report: open cache/current/$CURRENT_YEAR/recurring_payment_analysis_$CURRENT_YEAR.html"
    fi

    echo ""
    echo "✓ Current month data updated successfully!"

    # Remind about historical archiving
    if [ "$CURRENT_DAY" -gt "25" ]; then
        echo ""
        echo "💡 Tip: November is nearly over. After Nov 30, move this to historical:"
        echo "   ./move_to_historical.sh $CURRENT_YEAR"
    fi
else
    echo ""
    echo "✗ Failed to fetch $CURRENT_YEAR data"
    echo "  Check your connection to production and try again"
    exit 1
fi

echo ""
