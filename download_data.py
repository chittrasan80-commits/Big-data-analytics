"""
Download the real UCI Online Retail dataset and convert it to CSV.
Output: data/online_retail.csv  (541,909 rows)

If the download is blocked, get "Online Retail.xlsx" manually from
https://archive.ics.uci.edu/dataset/352/online+retail  (or the Kaggle mirror),
put it in data/, then run:  python data/download_data.py --xlsx "data/Online Retail.xlsx"
"""
import argparse, io, urllib.request, zipfile
import pandas as pd

URL = "https://archive.ics.uci.edu/static/public/352/online+retail.zip"

ap = argparse.ArgumentParser()
ap.add_argument("--xlsx", help="path to an already downloaded Online Retail.xlsx")
ap.add_argument("--out", default="data/online_retail.csv")
a = ap.parse_args()

if a.xlsx:
    df = pd.read_excel(a.xlsx)
else:
    print("Downloading", URL)
    z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(URL).read()))
    name = [n for n in z.namelist() if n.lower().endswith(".xlsx")][0]
    df = pd.read_excel(z.open(name))

df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"]).dt.strftime("%m/%d/%Y %H:%M")
df["CustomerID"] = df["CustomerID"].astype("Int64")
df.to_csv(a.out, index=False)
print(f"Saved {len(df):,} rows -> {a.out}")
