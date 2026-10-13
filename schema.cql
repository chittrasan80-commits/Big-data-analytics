-- Cassandra (NoSQL) schema: query-first design.
-- Run:  cqlsh -f src/cassandra/schema.cql
CREATE KEYSPACE IF NOT EXISTS retail
  WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
USE retail;

-- Q: "Give me the profile of customer X"  -> partition key = customer_id
CREATE TABLE IF NOT EXISTS customer_segments (
  customer_id bigint PRIMARY KEY,
  country     text,
  recency     int,
  frequency   int,
  monetary    double,
  segment     text
);

-- Q: "List all customers in segment S, biggest spenders first" -> partition key = segment
CREATE TABLE IF NOT EXISTS customers_by_segment (
  segment     text,
  monetary    double,
  customer_id bigint,
  country     text,
  PRIMARY KEY ((segment), monetary, customer_id)
) WITH CLUSTERING ORDER BY (monetary DESC, customer_id ASC);
