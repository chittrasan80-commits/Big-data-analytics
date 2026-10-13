# Mini Project Report – E-Commerce Customer Segmentation using Big Data

**Course:** CCS334 Big Data Analytics · **Team 5:** Harish S, Chittrasan K · **SDG 8**

## 1. Abstract
Online retailers hold millions of transaction rows but treat all customers alike. This project processes the UCI Online Retail
transactions with Hadoop-style MapReduce, Hive and PySpark to build RFM features and clusters customers with KMeans into
actionable segments, stored in Cassandra and visualised in Power BI.

## 2. Problem statement
Identify distinct customer groups from transaction history to enable targeted marketing and retention, supporting sustainable
growth of retail businesses (SDG 8).

## 3. Dataset
UCI Online Retail: 541,909 transactions (Dec 2010 – Dec 2011) of a UK-based online gift retailer, 8 attributes
(InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country). About 25% of rows lack CustomerID
and ~2% are cancellations; these are removed.

## 4. Architecture and tools
HDFS storage → MapReduce / Hive for batch aggregation → PySpark MLlib for clustering → Cassandra for serving segment lookups →
Power BI for dashboards. See README for the diagram and file mapping.

## 5. Methodology
Cleaning, RFM computation, log transform + standardisation, KMeans with silhouette-based k selection, rank-based segment naming.

## 6. NoSQL design
Cassandra tables are modelled per query: `customer_segments` (lookup by customer) and `customers_by_segment` (partition by
segment, clustered by spend descending).

## 7. Results
*(Fill from your real-data run: `outputs/segment_summary.csv`, `k_selection.png`, `revenue_share.png`, `segments_scatter.png`.)*
Typical pattern for this dataset: a small Champions group contributes the majority of revenue while a large low-frequency
group contributes little.

## 8. Business recommendations
Champions – loyalty/early access; Loyal & Potential – upsell/bundles; At Risk – win-back offers; Lost – low-cost email only.

## 9. Limitations and future work
Single UK retailer, one year of data, no product-level or demographic features. Future: add market-basket analysis, churn
prediction, streaming ingestion with Kafka.

## 10. Conclusion
Distributed RFM segmentation is cheap to compute and gives directly usable customer groups.
