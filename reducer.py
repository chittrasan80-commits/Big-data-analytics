#!/usr/bin/env python3
"""
Hadoop Streaming REDUCER - computes Recency, Frequency, Monetary per customer.
Input is sorted by key (guaranteed by Hadoop shuffle / `sort` locally).
Output: CustomerID,Recency,Frequency,Monetary
Recency   = days between snapshot date (max date in data + 1; passed via env SNAPSHOT_ORD) and last purchase
Frequency = number of distinct invoices
Monetary  = total spend
"""
import os, sys

snapshot = int(os.environ.get("SNAPSHOT_ORD", "0"))

def emit(cust, invoices, last_day, total):
    if cust is not None:
        print(f"{cust},{snapshot - last_day},{len(invoices)},{total:.2f}")

cur, invoices, last_day, total = None, set(), 0, 0.0
buffer = []
for line in sys.stdin:
    cust, val = line.rstrip("\n").split("\t")
    inv, day, amt = val.split("|")
    if cust != cur:
        emit(cur, invoices, last_day, total)
        cur, invoices, last_day, total = cust, set(), 0, 0.0
    invoices.add(inv)
    last_day = max(last_day, int(day))
    total += float(amt)
emit(cur, invoices, last_day, total)
