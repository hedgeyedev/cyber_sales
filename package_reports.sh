#!/bin/bash

# Package Cyber Sales Reports for Distribution
# Creates a self-contained zip file with index and all reports

echo "======================================"
echo "Packaging Cyber Sales Reports"
echo "======================================"

# Configuration
PACKAGE_NAME="cyber_sales_reports_$(date +%Y%m%d)"
PACKAGE_DIR="dist"
OUTPUT_ZIP="${PACKAGE_NAME}.zip"

# Create clean distribution directory
echo "Creating distribution directory..."
rm -rf "$PACKAGE_DIR"
mkdir -p "$PACKAGE_DIR"

# Copy index page
echo "Copying index page..."
if [ -f "index.html" ]; then
    cp index.html "$PACKAGE_DIR/"
else
    echo "⚠️  Warning: index.html not found"
fi

# Copy specific comparison HTML reports (exclude legacy)
echo "Copying comparison reports..."
comparison_count=0
for file in cyber_november_comparison_*.html; do
    if [ -f "$file" ]; then
        cp "$file" "$PACKAGE_DIR/"
        echo "  ✓ $file"
        ((comparison_count++))
    fi
done

# Copy individual year detail reports
echo "Copying year detail reports..."
year_count=0
for file in year_*_detail.html; do
    if [ -f "$file" ]; then
        cp "$file" "$PACKAGE_DIR/"
        echo "  ✓ $file"
        ((year_count++))
    fi
done

# Copy recurring payment analysis reports (time-of-day)
echo "Copying time-of-day analysis reports..."
time_count=0
for file in recurring_payment_analysis_20*.html; do
    if [ -f "$file" ]; then
        cp "$file" "$PACKAGE_DIR/"
        echo "  ✓ $file"
        ((time_count++))
    fi
done

report_count=$((comparison_count + year_count + time_count))

if [ $report_count -eq 0 ]; then
    echo "⚠️  Warning: No report files found!"
    exit 1
fi

# Create a README for users
echo "Creating README..."
cat > "$PACKAGE_DIR/README.txt" << 'EOF'
CYBER SALES REPORTS
===================

Welcome! This package contains interactive Cyber Sales analysis reports.

HOW TO USE:
-----------
1. Extract this ZIP file to a folder on your computer
2. Open "index.html" in your web browser (Chrome, Edge, Firefox, Safari)
3. Click on any report to view detailed analysis

REPORTS INCLUDED:
-----------------
COMPARISON REPORTS (2):
• Complete Analysis (2020-2025) - Full historical cohort analysis
• Year-over-Year Comparison (2024 vs 2025) - Recent trends and projections

YEAR DETAIL REPORTS (6):
• 2020-2025 Detailed SKU Analysis - Complete breakdown by SKU with cohort attribution
  Each report shows all SKUs, payment counts, revenue, and cohort breakdown

TIME-OF-DAY ANALYSIS (6):
• 2020-2025 Hourly Payment Analysis - Hour-by-hour breakdown with interactive charts
  Shows when payments occur throughout the day, peak hours, and processing patterns

FEATURES:
---------
✓ Interactive charts - Hover to see detailed numbers
✓ Cohort analysis - Track customer groups over time
✓ NRR tracking - Net Revenue Retention metrics
✓ Revenue projections - Forward-looking estimates
✓ Fully offline - No internet connection required

BROWSER COMPATIBILITY:
----------------------
These reports work best in:
• Google Chrome (recommended)
• Microsoft Edge
• Mozilla Firefox
• Safari

TROUBLESHOOTING:
----------------
If charts don't appear:
1. Make sure you extracted ALL files from the ZIP
2. Try a different browser (Chrome recommended)
3. Check that JavaScript is enabled in your browser
4. Open from your local hard drive (not from email/cloud directly)

NOTES:
------
• These reports use Chart.js for visualizations
• All data is embedded in the HTML files (no external connections)
• Safe to view offline and share within your organization

For questions or support, contact your analytics team.

Generated: $(date +"%Y-%m-%d %H:%M")
EOF

# Create ZIP file
echo ""
echo "Creating ZIP archive..."
cd "$PACKAGE_DIR" && zip -r "../$OUTPUT_ZIP" . && cd ..

# Clean up
echo "Cleaning up..."
rm -rf "$PACKAGE_DIR"

# Summary
echo ""
echo "======================================"
echo "✓ Package created successfully!"
echo "======================================"
echo ""
echo "📦 Package: $OUTPUT_ZIP"
echo "📊 Comparison Reports: $comparison_count"
echo "📊 Year Detail Reports: $year_count"
echo "📊 Time-of-Day Analysis: $time_count"
echo "📊 Total Reports: $report_count"
echo "📏 Size: $(du -h "$OUTPUT_ZIP" | cut -f1)"
echo ""
echo "DISTRIBUTION OPTIONS:"
echo "-------------------"
echo "1. Email: Attach $OUTPUT_ZIP to email"
echo "2. SharePoint: Upload to document library"
echo "3. Network Drive: Copy to shared folder"
echo "4. Teams: Share in channel files"
echo ""
echo "SHAREPOINT TIP:"
echo "If uploading to SharePoint, users should:"
echo "  • Download the ZIP file"
echo "  • Extract to their local computer"
echo "  • Open index.html"
echo ""
echo "Note: SharePoint won't display the reports directly"
echo "in the browser due to JavaScript security restrictions."
echo ""
