#!/usr/bin/env python3
"""
Hadoop Streaming MAPPER - RFM building block.
Input : raw Online Retail CSV lines (InvoiceNo,StockCode,Description,Quantity,InvoiceDate,UnitPrice,CustomerID,Country)
Output: CustomerID \t invoice_no | epoch_day | line_amount
Cleaning: skips header, guest rows (no CustomerID), cancellations (InvoiceNo starts with 'C'),
          non-positive quantity or price.
"""
import csv, sys
from datetime import datetime

for row in csv.reader(sys.stdin):
    if len(row) < 8 or row[0] == "InvoiceNo":
        continue
    inv, _, _, qty, date, price, cust, _ = row[:8]
    if not cust.strip() or inv.startswith("C"):
        continue
    try:
        qty, price = float(qty), float(price)
        day = datetime.strptime(date.strip(), "%m/%d/%Y %H:%M").toordinal()
    except ValueError:
        continue
    if qty <= 0 or price <= 0:
        continue
    print(f"{cust.strip().split('.')[0]}\t{inv}|{day}|{qty * price:.2f}")
