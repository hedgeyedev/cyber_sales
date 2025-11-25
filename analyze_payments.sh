#!/bin/bash

# Complete recurring payment analysis workflow
# This script executes all 3 steps:
# 1. Run analysis on production pod
# 2. Generate interactive visualization
# 3. Open the results in browser

set -e  # Exit on error

echo "======================================"
echo "  Recurring Payment Analysis"
echo "  Complete Workflow"
echo "======================================"
echo ""

# Step 1: Run analysis on production pod
echo "STEP 1/3: Running analysis on production pod..."
echo "--------------------------------------"
./run_payment_analysis.sh

echo ""
echo "======================================"
echo ""

# Step 2: Generate visualization
echo "STEP 2/3: Generating interactive visualization..."
echo "--------------------------------------"
python3 generate_analysis.py

echo ""
echo "======================================"
echo ""

# Step 3: Open in browser
echo "STEP 3/3: Opening visualization in browser..."
echo "--------------------------------------"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open recurring_payment_analysis_output.html
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open recurring_payment_analysis_output.html
else
    echo "Please manually open recurring_payment_analysis_output.html in your browser"
fi

echo ""
echo "======================================"
echo "  ✓ COMPLETE"
echo "======================================"
echo ""
echo "Files generated:"
echo "  - recurring_payments.json"
echo "  - recurring_payments.csv"
echo "  - recurring_payment_analysis_output.html"
echo ""
