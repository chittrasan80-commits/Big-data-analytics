#!/usr/bin/env bash
# Simulates Hadoop Streaming locally:  cat | mapper | sort | reducer
# Usage: bash src/mapreduce/run_local.sh data/online_retail_sample.csv outputs/rfm_mapreduce.csv
set -euo pipefail
IN="${1:-data/online_retail_sample.csv}"
OUT="${2:-outputs/rfm_mapreduce.csv}"
DIR="$(cd "$(dirname "$0")" && pwd)"

# snapshot date = last invoice date in the data + 1 day
export SNAPSHOT_ORD=$(python3 - "$IN" <<'PY'
import csv, sys
from datetime import datetime
m = 0
for r in csv.reader(open(sys.argv[1])):
    if r[0] == "InvoiceNo": continue
    try: m = max(m, datetime.strptime(r[4], "%m/%d/%Y %H:%M").toordinal())
    except ValueError: pass
print(m + 1)
PY
)
echo "CustomerID,Recency,Frequency,Monetary" > "$OUT"
cat "$IN" | python3 "$DIR/mapper.py" | sort -t$'\t' -k1,1 | python3 "$DIR/reducer.py" >> "$OUT"
echo "MapReduce RFM written to $OUT ($(($(wc -l < "$OUT") - 1)) customers)"
