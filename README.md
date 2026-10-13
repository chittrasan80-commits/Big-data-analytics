# E-Commerce Customer Segmentation using Big Data – Big Data Analytics 


Segments e-commerce customers by **Recency, Frequency, Monetary (RFM)** behaviour so a retailer can target
champions, win back at-risk buyers and stop spending marketing money on lost ones.

[![pipeline](https://github.com/chittrasan80-commits/Big-data-analytics/actions/workflows/main.yml/badge.svg)](https://github.com/chittrasan80-commits/Big-data-analytics/actions)

## Syllabus / tools mapping

| Requirement | File(s) |
|---|---|
| MapReduce | `mapper.py`, `reducer.py`, `run_local.sh` (Hadoop Streaming RFM job) |
| Hadoop / HDFS | `run_hadoop.sh` (same job on a real cluster) |
| Hive | `retail_segmentation.hql` (ETL, RFM table, NTILE scoring, analytics queries) |
| NoSQL (Cassandra) | `schema.cql`, `load_to_cassandra.py`, `docker-compose.yml` |
| PySpark ML | `segmentation_pyspark.py` (cleaning, RFM, scaling, KMeans, silhouette) |
| Charts / Power BI | `visualize.py`, `POWERBI.md`, `customer_segments.csv`, `segment_summary.csv` |
| CI on GitHub | `.github/workflows/main.yml` |
| Report | `REPORT.md` |

## Architecture

```
Online Retail CSV ─► HDFS ─┬─► MapReduce (streaming) ─► RFM ─┐
                           ├─► Hive (ORC tables, NTILE)      ├─► PySpark KMeans ─► segments.csv ─┬─► Power BI
                           └─────────────────────────────────┘                                    └─► Cassandra
```

## Quick start (sample data, no download)

Needs Python 3.9+ and Java 11/17 (for PySpark).

```bash
pip install -r requirements.txt
python generate_sample_data.py --out online_retail_sample.csv
mkdir -p outputs
bash run_local.sh online_retail_sample.csv outputs/rfm_mapreduce.csv
python segmentation_pyspark.py --input online_retail_sample.csv --out outputs
python visualize.py --out outputs
```

Results appear in `outputs/` (`customer_segments.csv`, `segment_summary.csv`, `k_selection.csv`, PNG charts).

## Run on the real dataset

```bash
python download_data.py --out online_retail.csv      # 541,909 rows
mkdir -p outputs
bash run_local.sh online_retail.csv outputs/rfm_mapreduce.csv
python segmentation_pyspark.py --input online_retail.csv --out outputs --k-min 3 --k-max 8
python visualize.py --out outputs
```

If the download is blocked, get `Online Retail.xlsx` from the UCI page and run
`python download_data.py --xlsx "Online Retail.xlsx" --out online_retail.csv`.

## Hive and Cassandra

```bash
hive -f retail_segmentation.hql                      # data must be in HDFS /retail/input/
docker compose up -d cassandra                       # wait ~60 s
python load_to_cassandra.py --csv outputs/customer_segments.csv
```

## Method

1. **Clean** – drop guest rows (no CustomerID), cancellations (InvoiceNo starts with `C`), non-positive quantity/price.
2. **RFM** – Recency = days from snapshot (last invoice date + 1) to last purchase; Frequency = distinct invoices; Monetary = total spend.
3. **Transform** – `log1p` on all three (heavy right skew), then standardise.
4. **Cluster** – KMeans, k in [3, 6] by default, best k by silhouette (WSSSE saved for the elbow plot).
5. **Label** – clusters ranked by composite RFM score and named Champions → Lost / Hibernating.
6. **Validate** – MapReduce and PySpark RFM tables must match (checked in CI).

## Results

Files in this repo marked as sample output come from synthetic data and only demonstrate the pipeline.
Real-data results are in `REPORT.md` section 7.

## Business use (SDG 8)

Targeted retention improves small and medium retailer profitability and sustainable growth: marketing goes to customers
who respond instead of blanket discounts.
