"""
E-Commerce Customer Segmentation using Big Data  (CCS334 - Big Data Analytics)
PySpark pipeline: clean -> RFM -> scale -> KMeans (k chosen by silhouette) -> label segments -> export

Usage:
  python src/segmentation_pyspark.py --input data/online_retail_sample.csv --out outputs
  python src/segmentation_pyspark.py --input data/online_retail.csv --out outputs --k-min 3 --k-max 8
"""
import argparse, os, shutil
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

LABELS = ["Champions", "Loyal Customers", "Potential Loyalists", "Needs Attention", "At Risk", "Lost / Hibernating"]


def load_and_clean(spark, path):
    df = (spark.read.option("header", True).csv(path)
          .withColumn("Quantity", F.col("Quantity").cast("int"))
          .withColumn("UnitPrice", F.col("UnitPrice").cast("double"))
          .withColumn("InvoiceTs", F.to_timestamp("InvoiceDate", "M/d/yyyy H:mm")))
    n_raw = df.count()
    clean = (df.filter(F.col("CustomerID").isNotNull() & (F.trim(F.col("CustomerID")) != ""))
               .filter(~F.col("InvoiceNo").startswith("C"))          # cancellations
               .filter((F.col("Quantity") > 0) & (F.col("UnitPrice") > 0))
               .filter(F.col("InvoiceTs").isNotNull())
               .withColumn("CustomerID", F.col("CustomerID").cast("double").cast("long"))
               .withColumn("Amount", F.col("Quantity") * F.col("UnitPrice")))
    return clean, n_raw


def build_rfm(clean):
    snapshot = clean.agg(F.date_add(F.max(F.to_date("InvoiceTs")), 1).alias("d")).first()["d"]
    rfm = (clean.groupBy("CustomerID")
           .agg(F.datediff(F.lit(snapshot), F.max(F.to_date("InvoiceTs"))).alias("Recency"),
                F.countDistinct("InvoiceNo").alias("Frequency"),
                F.round(F.sum("Amount"), 2).alias("Monetary"),
                F.first("Country").alias("Country")))
    return rfm, snapshot


def choose_k(scaled, k_min, k_max, seed):
    ev = ClusteringEvaluator(featuresCol="features", metricName="silhouette", distanceMeasure="squaredEuclidean")
    scores = []
    for k in range(k_min, k_max + 1):
        m = KMeans(k=k, seed=seed, featuresCol="features").fit(scaled)
        scores.append((k, float(m.summary.trainingCost), ev.evaluate(m.transform(scaled))))
        print(f"  k={k}  WSSSE={scores[-1][1]:.1f}  silhouette={scores[-1][2]:.4f}")
    best = max(scores, key=lambda t: t[2])[0]
    return best, scores


def label_clusters(profile_rows):
    """Rank clusters by composite score (low recency good, high frequency/monetary good) -> readable names."""
    import pandas as pd
    p = pd.DataFrame(profile_rows)
    score = (-p["avg_recency"].rank() + p["avg_frequency"].rank() + p["avg_monetary"].rank())
    order = score.sort_values(ascending=False).index.tolist()
    k = len(order)
    names = {}
    for i, idx in enumerate(order):
        li = 0 if k == 1 else round(i * (len(LABELS) - 1) / (k - 1))
        names[int(p.loc[idx, "cluster"])] = LABELS[li]
    return names


def write_single_csv(sdf, path):
    tmp = path + "_tmp"
    sdf.coalesce(1).write.mode("overwrite").option("header", True).csv(tmp)
    part = [f for f in os.listdir(tmp) if f.startswith("part-") and f.endswith(".csv")][0]
    shutil.move(os.path.join(tmp, part), path)
    shutil.rmtree(tmp)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/online_retail_sample.csv")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--k-min", type=int, default=3)
    ap.add_argument("--k-max", type=int, default=6)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    spark = (SparkSession.builder.appName("EcommerceCustomerSegmentation")
             .config("spark.sql.shuffle.partitions", "8").getOrCreate())
    spark.sparkContext.setLogLevel("ERROR")

    clean, n_raw = load_and_clean(spark, a.input)
    clean.cache()
    print(f"Rows: raw={n_raw:,}  after cleaning={clean.count():,}")

    rfm, snapshot = build_rfm(clean)
    rfm.cache()
    print(f"Customers: {rfm.count():,}   snapshot date: {snapshot}")

    # log1p transform tames the heavy right-skew of F and M, then standardise
    logged = (rfm.withColumn("R_log", F.log1p("Recency"))
                 .withColumn("F_log", F.log1p("Frequency"))
                 .withColumn("M_log", F.log1p("Monetary")))
    vec = VectorAssembler(inputCols=["R_log", "F_log", "M_log"], outputCol="raw").transform(logged)
    scaled = StandardScaler(inputCol="raw", outputCol="features", withMean=True, withStd=True).fit(vec).transform(vec)

    print("Selecting k (silhouette):")
    k, scores = choose_k(scaled, a.k_min, a.k_max, a.seed)
    print(f"Chosen k = {k}")
    model = KMeans(k=k, seed=a.seed, featuresCol="features", predictionCol="cluster").fit(scaled)
    result = model.transform(scaled)

    profile = (result.groupBy("cluster")
               .agg(F.count("*").alias("customers"),
                    F.round(F.avg("Recency"), 1).alias("avg_recency"),
                    F.round(F.avg("Frequency"), 1).alias("avg_frequency"),
                    F.round(F.avg("Monetary"), 2).alias("avg_monetary"),
                    F.round(F.sum("Monetary"), 2).alias("total_revenue")))
    rows = [r.asDict() for r in profile.collect()]
    names = label_clusters(rows)
    mapping = F.create_map([F.lit(x) for kv in names.items() for x in kv])
    result = result.withColumn("Segment", mapping[F.col("cluster")])

    seg_summary = (result.groupBy("Segment")
                   .agg(F.count("*").alias("customers"),
                        F.round(F.avg("Recency"), 1).alias("avg_recency_days"),
                        F.round(F.avg("Frequency"), 1).alias("avg_orders"),
                        F.round(F.avg("Monetary"), 2).alias("avg_spend"),
                        F.round(F.sum("Monetary"), 2).alias("total_revenue"))
                   .withColumn("revenue_share_pct", F.round(100 * F.col("total_revenue") / F.sum("total_revenue").over(Window.partitionBy()), 1))
                   .orderBy(F.desc("total_revenue")))
    seg_summary.show(truncate=False)

    cols = ["CustomerID", "Country", "Recency", "Frequency", "Monetary", "cluster", "Segment"]
    write_single_csv(result.select(*cols).orderBy("CustomerID"), os.path.join(a.out, "customer_segments.csv"))
    write_single_csv(seg_summary, os.path.join(a.out, "segment_summary.csv"))
    import pandas as pd
    pd.DataFrame(scores, columns=["k", "wssse", "silhouette"]).to_csv(os.path.join(a.out, "k_selection.csv"), index=False)
    print(f"Outputs written to {a.out}/")
    spark.stop()


if __name__ == "__main__":
    main()
