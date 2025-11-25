#!/bin/bash
#
# move_to_historical.sh
#
# Moves a year's data from cache/current/ to cache/historical/
# Use this after November ends to freeze the data.
#
# Usage: ./move_to_historical.sh 2025
#

set -e  # Exit on error

if [ $# -eq 0 ]; then
    echo "Usage: $0 <year>"
    echo "Example: $0 2025"
    exit 1
fi

YEAR=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/cache"
CURRENT_DIR="$CACHE_DIR/current/$YEAR"
HISTORICAL_DIR="$CACHE_DIR/historical/$YEAR"

echo "======================================"
echo "Move $YEAR to Historical Cache"
echo "======================================"
echo ""

# Check if source exists
if [ ! -d "$CURRENT_DIR" ]; then
    echo "✗ Error: No data found in cache/current/$YEAR/"
    echo ""
    echo "Available current years:"
    ls -1 "$CACHE_DIR/current/" 2>/dev/null || echo "  (none)"
    echo ""
    exit 1
fi

# Check if destination already exists
if [ -d "$HISTORICAL_DIR" ]; then
    echo "⚠️  Warning: cache/historical/$YEAR/ already exists"
    echo ""
    read -p "Overwrite existing historical data? (y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi
    rm -rf "$HISTORICAL_DIR"
fi

# Create historical directory
mkdir -p "$CACHE_DIR/historical"

# Move the directory
mv "$CURRENT_DIR" "$HISTORICAL_DIR"

echo "✓ Moved $YEAR data to historical cache"
echo ""
echo "Files:"
ls -lh "$HISTORICAL_DIR/" | grep -v "^total" | awk '{print "  " $9 " (" $5 ")"}'

echo ""
echo "======================================"
echo "✓ $YEAR is now in historical cache"
echo "======================================"
echo ""
echo "This data will no longer be updated by update_current_month.sh"
echo ""
