"""
Load segmentation output into Cassandra and run two sample queries.
Usage: python src/cassandra/load_to_cassandra.py --csv outputs/customer_segments.csv --host 127.0.0.1
Start Cassandra first:  docker compose up -d cassandra   (wait ~60s)
"""
import argparse, os
import pandas as pd
from cassandra.cluster import Cluster
from cassandra.concurrent import execute_concurrent_with_args

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="outputs/customer_segments.csv")
ap.add_argument("--host", default="127.0.0.1")
a = ap.parse_args()

df = pd.read_csv(a.csv)
session = Cluster([a.host]).connect()
with open(os.path.join(os.path.dirname(__file__), "schema.cql")) as f:
    for stmt in [s.strip() for s in f.read().split(";") if s.strip() and not s.strip().startswith("--")]:
        session.execute("\n".join(l for l in stmt.splitlines() if not l.strip().startswith("--")))
session.set_keyspace("retail")

ins1 = session.prepare("INSERT INTO customer_segments (customer_id,country,recency,frequency,monetary,segment) VALUES (?,?,?,?,?,?)")
ins2 = session.prepare("INSERT INTO customers_by_segment (segment,monetary,customer_id,country) VALUES (?,?,?,?)")
execute_concurrent_with_args(session, ins1, [(int(r.CustomerID), r.Country, int(r.Recency), int(r.Frequency), float(r.Monetary), r.Segment) for r in df.itertuples()])
execute_concurrent_with_args(session, ins2, [(r.Segment, float(r.Monetary), int(r.CustomerID), r.Country) for r in df.itertuples()])
print(f"Loaded {len(df)} customers")

cid = int(df.CustomerID.iloc[0])
print("Profile:", session.execute("SELECT * FROM customer_segments WHERE customer_id=%s", (cid,)).one())
top_seg = df.Segment.iloc[0]
print(f"Top 5 spenders in '{top_seg}':")
for row in session.execute("SELECT customer_id, monetary FROM customers_by_segment WHERE segment=%s LIMIT 5", (top_seg,)):
    print("  ", row.customer_id, row.monetary)
