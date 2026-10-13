"""
Generate a synthetic dataset with the SAME schema as the UCI Online Retail dataset.
Used so the project (and GitHub Actions CI) runs without downloading anything.

Usage: python data/generate_sample_data.py [--customers 1200] [--out data/online_retail_sample.csv]
"""
import argparse
import numpy as np
import pandas as pd

SEGMENTS = {
    # name: (share, avg orders, avg item qty, avg unit price, days-since-last-order range)
    "champions":  (0.12, 25, 12, 3.5, (0, 20)),
    "loyal":      (0.20, 10, 8, 3.0, (10, 60)),
    "promising":  (0.25, 4, 6, 2.5, (30, 120)),
    "at_risk":    (0.23, 3, 5, 2.8, (120, 250)),
    "lost":       (0.20, 1, 4, 2.0, (250, 370)),
}
COUNTRIES = ["United Kingdom"] * 8 + ["Germany", "France", "EIRE", "Spain"]


def main(n_customers, out, seed=42):
    rng = np.random.default_rng(seed)
    end = pd.Timestamp("2011-12-09 12:00")
    rows, inv = [], 536365
    names = list(SEGMENTS)
    for cid in range(12346, 12346 + n_customers):
        seg = rng.choice(names, p=[SEGMENTS[n][0] for n in names])
        _, lam, qty, price, (lo, hi) = SEGMENTS[seg]
        n_orders = max(1, rng.poisson(lam))
        last = int(rng.integers(lo, hi + 1))
        country = rng.choice(COUNTRIES)
        for k in range(n_orders):
            day = last if k == 0 else last + int(rng.integers(1, max(2, 373 - last)))
            ts = end - pd.Timedelta(days=day, hours=int(rng.integers(0, 8)))
            inv += 1
            for _ in range(int(rng.integers(1, 8))):
                rows.append([str(inv), f"{rng.integers(10000, 10200)}", "SAMPLE PRODUCT",
                             int(max(1, rng.poisson(qty))), ts.strftime("%m/%d/%Y %H:%M"),
                             round(float(max(0.2, rng.normal(price, 1))), 2), cid, country])
    df = pd.DataFrame(rows, columns=["InvoiceNo", "StockCode", "Description", "Quantity",
                                     "InvoiceDate", "UnitPrice", "CustomerID", "Country"])
    # dirty rows, like the real dataset: cancellations, guest checkouts, zero prices
    cancel = df.sample(frac=0.02, random_state=1).copy()
    cancel["InvoiceNo"] = "C" + cancel["InvoiceNo"]
    cancel["Quantity"] = -cancel["Quantity"]
    guests = df.sample(frac=0.05, random_state=2).copy()
    guests["CustomerID"] = np.nan
    bad = df.sample(frac=0.003, random_state=3).copy()
    bad["UnitPrice"] = 0.0
    df = pd.concat([df, cancel, guests, bad], ignore_index=True)
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows, {n_customers} customers -> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--customers", type=int, default=1200)
    ap.add_argument("--out", default="data/online_retail_sample.csv")
    a = ap.parse_args()
    main(a.customers, a.out)
