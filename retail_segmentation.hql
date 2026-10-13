-- Hive implementation of the RFM feature build (HiveQL).
-- Run:  hive -f src/hive/retail_segmentation.hql
-- Assumes online_retail.csv is in HDFS at /retail/input/

CREATE DATABASE IF NOT EXISTS retail;
USE retail;

DROP TABLE IF EXISTS raw_transactions;
CREATE EXTERNAL TABLE raw_transactions (
  InvoiceNo   STRING,
  StockCode   STRING,
  Description STRING,
  Quantity    INT,
  InvoiceDate STRING,
  UnitPrice   DOUBLE,
  CustomerID  STRING,
  Country     STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES ("separatorChar" = ",", "quoteChar" = "\"")
STORED AS TEXTFILE
LOCATION '/retail/input/'
TBLPROPERTIES ("skip.header.line.count"="1");

-- Cleaned transactions (no guests, no cancellations, positive qty/price)
DROP TABLE IF EXISTS clean_transactions;
CREATE TABLE clean_transactions STORED AS ORC AS
SELECT InvoiceNo,
       CAST(CAST(CustomerID AS DOUBLE) AS BIGINT)                          AS CustomerID,
       Country,
       Quantity * UnitPrice                                                AS Amount,
       CAST(from_unixtime(unix_timestamp(InvoiceDate, 'MM/dd/yyyy HH:mm')) AS TIMESTAMP) AS InvoiceTs
FROM raw_transactions
WHERE CustomerID IS NOT NULL AND CustomerID <> ''
  AND InvoiceNo NOT LIKE 'C%'
  AND Quantity > 0 AND UnitPrice > 0;

-- RFM table (snapshot = last invoice date + 1 day)
DROP TABLE IF EXISTS rfm;
CREATE TABLE rfm STORED AS ORC AS
SELECT t.CustomerID,
       DATEDIFF(s.snap, MAX(TO_DATE(t.InvoiceTs))) AS Recency,
       COUNT(DISTINCT t.InvoiceNo)                 AS Frequency,
       ROUND(SUM(t.Amount), 2)                     AS Monetary
FROM clean_transactions t
CROSS JOIN (SELECT DATE_ADD(MAX(TO_DATE(InvoiceTs)), 1) AS snap FROM clean_transactions) s
GROUP BY t.CustomerID, s.snap;

-- Rule-based quintile scoring (complements the ML clustering; good for the report)
DROP VIEW IF EXISTS rfm_scored;
CREATE VIEW rfm_scored AS
SELECT CustomerID, Recency, Frequency, Monetary,
       NTILE(5) OVER (ORDER BY Recency DESC)  AS R_score,
       NTILE(5) OVER (ORDER BY Frequency ASC) AS F_score,
       NTILE(5) OVER (ORDER BY Monetary ASC)  AS M_score
FROM rfm;

-- Analytical queries ------------------------------------------------------------
-- Q1: revenue by country (top 10)
SELECT Country, ROUND(SUM(Amount),2) AS revenue, COUNT(DISTINCT CustomerID) AS customers
FROM clean_transactions GROUP BY Country ORDER BY revenue DESC LIMIT 10;

-- Q2: monthly revenue trend
SELECT DATE_FORMAT(InvoiceTs,'yyyy-MM') AS month, ROUND(SUM(Amount),2) AS revenue
FROM clean_transactions GROUP BY DATE_FORMAT(InvoiceTs,'yyyy-MM') ORDER BY month;

-- Q3: segment by score rules
SELECT CASE WHEN R_score>=4 AND F_score>=4 AND M_score>=4 THEN 'Champions'
            WHEN R_score>=3 AND F_score>=3                  THEN 'Loyal'
            WHEN R_score<=2 AND F_score>=3                  THEN 'At Risk'
            WHEN R_score<=2 AND F_score<=2                  THEN 'Lost'
            ELSE 'Potential' END AS segment,
       COUNT(*) AS customers, ROUND(AVG(Monetary),2) AS avg_spend
FROM rfm_scored GROUP BY 1 ORDER BY customers DESC;
