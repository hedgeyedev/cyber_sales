#!/bin/bash
# Refresh Cyber reports and publish the folder to SharePoint (index + 3 reports, overwritten in place, stable URLs).
# Quiet when healthy; on failure prints what failed and that readers see a stale copy.
# Needs: kubectl context "production" (read-only exec into admin-web), cultiv-sharepoint auth.
# DRY_RUN=1 (default) builds only. DRY_RUN=0 uploads. SKIP_FETCH=1 reuses cache/ (no production access).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
YEAR=$(date +%Y); FIRST=2020
SITE="${CYBER_SP_SITE:-hedgeye.sharepoint.com/sites/operations2}"
FOLDER="${CYBER_SP_FOLDER:-General/File Transfer/Cyber/Cyber $YEAR}"
LOG=$(mktemp)
fail() {
  echo "cyber report refresh FAILED at step: $1. Readers still see the previous copy (stale since last success). Log: $LOG" >&2
  osascript -e "display notification \"Failed at: $1. Readers see a stale copy.\" with title \"Cyber report refresh\"" 2>/dev/null || true
  exit 1
}

if [ "${SKIP_FETCH:-0}" != "1" ]; then
  # prior year must be historical before this year is current, or refresh_analysis refetches it from production
  [ -d "cache/historical/$((YEAR-1))" ] || ./move_to_historical.sh $((YEAR-1)) >>"$LOG" 2>&1 || fail "move_to_historical"
  ./refresh_analysis.sh $FIRST "$YEAR" >>"$LOG" 2>&1 || fail "refresh_analysis (data fetch / kubectl auth?)"
fi
GEN=$(python3 -c "import json;print(json.load(open('cache/current/$YEAR/recurring_payments_$YEAR.json'))['generated_at'])")
ASOF=$(python3 -c "from datetime import datetime;print(datetime.fromisoformat('$GEN').strftime('%b %-d, %Y %-I:%M %p ET'))")
OUT=dist_single; rm -rf $OUT; mkdir -p $OUT
python3 build_index.py $OUT/index.html "$YEAR" >>"$LOG" 2>&1 || fail "build_index"
python3 make_single_file.py "cyber_november_comparison_${FIRST}_${YEAR}.html" "$OUT/Cyber-$YEAR-vs-prior-years.html" "$ASOF" >>"$LOG" 2>&1 || fail "comparison page"
python3 make_single_file.py "year_${YEAR}_detail.html" "$OUT/Year-$YEAR-SKU-detail.html" "$ASOF" >>"$LOG" 2>&1 || fail "SKU detail page"
python3 make_single_file.py "recurring_payment_analysis_${YEAR}.html" "$OUT/Hourly-$YEAR.html" "$ASOF" >>"$LOG" 2>&1 || fail "hourly page"

if [ "${DRY_RUN:-1}" = "1" ]; then echo "dry run: built $OUT/, not uploaded"; exit 0; fi
for f in $OUT/*.html; do
  ~/work/cultiv-ai/bin/cultiv-sharepoint upload "$SITE" "$FOLDER" "$PWD/$f" >>"$LOG" 2>&1 || fail "sharepoint upload $f"
done
