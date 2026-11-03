#!/bin/bash
# Refresh Cyber reports and publish ONE file to SharePoint (overwrite in place).
# Quiet when healthy; on failure prints what failed and that readers see a stale file.
# Needs: kubectl context "production" (read-only exec into admin-web), cultiv-sharepoint auth.
# DRY_RUN=1 (default) builds the file but does NOT upload. Set DRY_RUN=0 only once approved.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
YEAR=$(date +%Y); FIRST=2020
SITE="${CYBER_SP_SITE:?set CYBER_SP_SITE, e.g. hedgeye.sharepoint.com/sites/<site>}"
FOLDER="${CYBER_SP_FOLDER:?set CYBER_SP_FOLDER}"
NAME="Cyber-Sales-Report-${YEAR}.html"
ASOF="$(date '+%b %-d, %Y %-I:%M %p %Z')"
LOG=$(mktemp)
fail() { echo "cyber report refresh FAILED at step: $1. Readers still see the previous file (stale since last success). Log: $LOG" >&2; exit 1; }

# 2025 must be historical before 2026 is current, or refresh_analysis refetches it from production.
[ -d "cache/historical/$((YEAR-1))" ] || ./move_to_historical.sh $((YEAR-1)) >>"$LOG" 2>&1 || fail "move_to_historical"
./refresh_analysis.sh $FIRST "$YEAR" >>"$LOG" 2>&1 || fail "refresh_analysis (data fetch / kubectl auth?)"
OUT="cyber_november_comparison_${FIRST}_${YEAR}.html"
[ -f "$OUT" ] || fail "comparison report missing"
mkdir -p dist_single
python3 make_single_file.py "$OUT" "dist_single/$NAME" "$ASOF" >>"$LOG" 2>&1 || fail "make_single_file"

if [ "${DRY_RUN:-1}" = "1" ]; then echo "dry run: built dist_single/$NAME, not uploaded"; exit 0; fi
~/work/cultiv-ai/bin/cultiv-sharepoint upload "$SITE" "$FOLDER" "dist_single/$NAME" >>"$LOG" 2>&1 || fail "sharepoint upload"
