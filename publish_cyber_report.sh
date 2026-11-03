#!/bin/bash
# Refresh Cyber reports and publish the folder to SharePoint (index + 3 reports, overwritten in place, stable URLs).
# Quiet when healthy; on failure prints what failed, notifies, and says readers see a stale copy.
# Needs: kubectl context "production" (read-only exec into admin-web), cultiv-sharepoint auth.
# DRY_RUN=1 (default) builds only. DRY_RUN=0 uploads. SKIP_FETCH=1 reuses cache/ (no production access).
# Runs only in the Cyber season (Nov, Dec 1-9) unless FORCE=1.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
MONTH=$(date +%m); DAY=$(date +%d)
if [ "${FORCE:-0}" != "1" ] && [ "$MONTH" != "11" ] && { [ "$MONTH" != "12" ] || [ "$DAY" -gt 9 ]; }; then exit 0; fi

YEAR=$(date +%Y); FIRST=2020
SITE="${CYBER_SP_SITE:-hedgeye.sharepoint.com/sites/operations2}"
FOLDER="${CYBER_SP_FOLDER:-General/File Transfer/Cyber/Cyber $YEAR}"
LOG="$HOME/Library/Logs/cyber-sales-report.last.log"; : > "$LOG"
fail() {
  echo "cyber report refresh FAILED at step: $1. Readers still see the previous copy (stale since last success)." >&2
  tail -n 30 "$LOG" >&2
  osascript -e "display notification \"Failed at: $1. Readers see a stale copy.\" with title \"Cyber report refresh\"" 2>/dev/null || true
  exit 1
}

JSON="cache/current/$YEAR/recurring_payments_$YEAR.json"
COMPARISON="cyber_november_comparison_${FIRST}_${YEAR}.html"
DETAIL="year_${YEAR}_detail.html"
HOURLY="recurring_payment_analysis_${YEAR}.html"

if [ "${SKIP_FETCH:-0}" != "1" ]; then
  # prior year must be historical before this year is current, or refresh_analysis refetches it from production
  [ -d "cache/historical/$((YEAR-1))" ] || ./move_to_historical.sh $((YEAR-1)) >>"$LOG" 2>&1 || fail "move_to_historical"
  # refresh_analysis.sh warns but exits 0 when a page fails to generate: remove old pages so a stale one cannot be stamped fresh
  rm -f "$COMPARISON" "$DETAIL" "$HOURLY"
  ./refresh_analysis.sh $FIRST "$YEAR" >>"$LOG" 2>&1 || fail "refresh_analysis (data fetch / kubectl auth?)"
fi
for f in "$JSON" "$COMPARISON" "$DETAIL" "$HOURLY"; do [ -f "$f" ] || fail "missing $f"; done

GEN=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['generated_at'])" "$JSON") || fail "read generated_at"
ASOF=$(python3 -c "import sys;from datetime import datetime;print(datetime.fromisoformat(sys.argv[1]).strftime('%b %-d, %Y %-I:%M %p ET'))" "$GEN") || fail "format Data-as-of"
OUT=dist_single; rm -rf $OUT; mkdir -p $OUT
python3 build_index.py $OUT/index.html "$YEAR" >>"$LOG" 2>&1 || fail "build_index"
python3 make_single_file.py "$COMPARISON" "$OUT/Cyber-$YEAR-vs-prior-years.html" "$ASOF" >>"$LOG" 2>&1 || fail "comparison page"
python3 make_single_file.py "$DETAIL" "$OUT/Year-$YEAR-SKU-detail.html" "$ASOF" >>"$LOG" 2>&1 || fail "SKU detail page"
python3 make_single_file.py "$HOURLY" "$OUT/Hourly-$YEAR.html" "$ASOF" >>"$LOG" 2>&1 || fail "hourly page"

if [ "${DRY_RUN:-1}" = "1" ]; then echo "dry run: built $OUT/, not uploaded"; exit 0; fi
# index last: the page that claims freshness changes only after the reports are up
for f in "$OUT/Cyber-$YEAR-vs-prior-years.html" "$OUT/Year-$YEAR-SKU-detail.html" "$OUT/Hourly-$YEAR.html" "$OUT/index.html"; do
  ~/work/cultiv-ai/bin/cultiv-sharepoint upload "$SITE" "$FOLDER" "$PWD/$f" >>"$LOG" 2>&1 || fail "sharepoint upload $f (readers may see a mix of new and old pages)"
done
