# E-Commerce Customer Segmentation using Big Data

**CCS334 – Big Data Analytics · Mini Project (Assignment Component II) · Team 5**
Team: Harish S (814724104048) · Chittrasan K (814724104026)
SDG 8 – Decent Work & Economic Growth · Level L2 · Dataset: UCI Online Retail

Segments e-commerce customers by **Recency, Frequency, Monetary (RFM)** behaviour so a retailer can target
champions, win back at-risk buyers and stop wasting marketing spend on lost ones.

## Syllabus / tools mapping

| Requirement | Where it is in this repo |
|---|---|
| MapReduce | `src/mapreduce/` – Hadoop Streaming mapper + reducer computing RFM |
| Hive | `src/hive/retail_segmentation.hql` – ETL, RFM table, NTILE scoring, analytics queries |
| NoSQL (Cassandra) | `src/cassandra/` – query-first schema + loader |
| Hadoop / HDFS | `src/mapreduce/run_hadoop.sh` – same job on a real cluster |
| PySpark + Scikit-learn style ML | `src/segmentation_pyspark.py` – cleaning, RFM, scaling, KMeans, silhouette |
| Power BI | import `outputs/customer_segments.csv` + `outputs/segment_summary.csv` (see `docs/POWERBI.md`) |
| GitHub / Docker | `.github/workflows/ci.yml` runs the pipeline on every push; `docker-compose.yml` for Cassandra |

## Architecture

```
Online Retail CSV ─► HDFS ─┬─► MapReduce (streaming) ─► RFM ─┐
                           ├─► Hive (ORC tables, NTILE)      ├─► PySpark KMeans ─► segments.csv ─┬─► Power BI
                           └─────────────────────────────────┘                                    └─► Cassandra
```

## Quick start (no download needed)

```bash
pip install -r requirements.txt            # needs Java 11/17 for PySpark
python data/generate_sample_data.py         # synthetic data, same schema as Online Retail
bash src/mapreduce/run_local.sh             # MapReduce RFM (simulated Hadoop Streaming)
python src/segmentation_pyspark.py          # PySpark clustering -> outputs/
python src/visualize.py                     # charts -> outputs/*.png
```

## Run on the real dataset

```bash
python data/download_data.py                # saves data/online_retail.csv (541,909 rows)
bash src/mapreduce/run_local.sh data/online_retail.csv outputs/rfm_mapreduce.csv
python src/segmentation_pyspark.py --input data/online_retail.csv --k-min 3 --k-max 8
python src/visualize.py
```

If the download is blocked, grab `Online Retail.xlsx` from the UCI page manually and run
`python data/download_data.py --xlsx "data/Online Retail.xlsx"`.

## Hive and Cassandra

```bash
hive -f src/hive/retail_segmentation.hql         # needs Hive + data in HDFS /retail/input/
docker compose up -d cassandra                   # wait ~60 s
python src/cassandra/load_to_cassandra.py        # loads outputs/customer_segments.csv
```

## Method

1. **Clean** – drop guest rows (no CustomerID), cancellations (InvoiceNo starting with `C`), non-positive quantity/price.
2. **RFM** – Recency = days from snapshot (last invoice date + 1) to last purchase; Frequency = distinct invoices; Monetary = total spend.
3. **Transform** – `log1p` on all three (heavy right skew), then standardise.
4. **Cluster** – KMeans, k in [3, 6] by default, best k by silhouette (elbow/WSSSE saved too).
5. **Label** – clusters ranked by a composite RFM score and named Champions → Lost / Hibernating.
6. **Validate** – MapReduce and PySpark RFM tables must match (checked in CI).

## Sample results

`outputs/` is committed from a run on the *synthetic* sample data, so numbers there only demonstrate the pipeline.
Re-run on the real dataset for your report figures.

## Business use (SDG 8)

Targeted retention and pricing improve small/medium retailer profitability and sustainable growth: spend marketing on
customers who respond, rather than blanket discounts.
