#!/usr/bin/env bash
# Look up every food red-list entry through FDA's FEI API, within FDA's ~50 searches/hour limit.
# Batches of 45 at one call per 80 s; after each batch, publish found FEIs (fei-apply has the 98% agreement guard).
# Exit code 2 from fei-lookup = FDA refused service (hourly limit, outage or block): wait an hour, then continue.
# Any other failure stops the loop. Safe to stop and restart: entries already asked are never asked again.
# Usage (keeps the Mac awake):  caffeinate -i scripts/fei_backfill.sh [initial_wait_seconds]
set -u
cd "$(dirname "$0")/.."
ETL=.venv/bin/st-etl
sleep "${1:-0}"
while true; do
  out=$($ETL fei-lookup --limit 45 2>&1); rc=$?
  echo "$(date '+%F %T') lookup rc=$rc $(echo "$out" | tr '\n' ' ' | tail -c 400)"
  if [ $rc -ne 0 ] && [ $rc -ne 2 ]; then echo "stopping: lookup failed"; exit $rc; fi
  $ETL fei-apply 2>&1 | tr '\n' ' '; arc=${PIPESTATUS[0]}; echo
  if [ $arc -ne 0 ]; then echo "stopping: fei-apply refused (see st-etl fei-report)"; exit $arc; fi
  if [ $rc -eq 2 ]; then sleep 3600; continue; fi
  if echo "$out" | grep -q '"looked_up": 0'; then echo "done: no entries left"; exit 0; fi
done
