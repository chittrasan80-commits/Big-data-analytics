#!/usr/bin/env bash
# Run the mapper/reducer on a real Hadoop cluster (pseudo-distributed works too).
# SNAPSHOT_ORD=734481 is 2011-12-10, the day after the last invoice in the real dataset.
set -euo pipefail
mkdir -p outputs
hdfs dfs -mkdir -p /retail/input
hdfs dfs -put -f online_retail.csv /retail/input/
hdfs dfs -rm -r -f /retail/rfm_out
hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=2 \
  -files mapper.py,reducer.py \
  -cmdenv SNAPSHOT_ORD=734481 \
  -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
  -input /retail/input/online_retail.csv -output /retail/rfm_out
hdfs dfs -cat /retail/rfm_out/part-* > outputs/rfm_hadoop.csv
