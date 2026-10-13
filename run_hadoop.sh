#!/usr/bin/env bash
# Run the same mapper/reducer on a real Hadoop cluster (pseudo-distributed works too).
# Usage: bash src/mapreduce/run_hadoop.sh   (SNAPSHOT_ORD=734481 is 2011-12-10, the day after the last invoice in the real dataset)
set -euo pipefail
hdfs dfs -mkdir -p /retail/input
hdfs dfs -put -f data/online_retail.csv /retail/input/
hdfs dfs -rm -r -f /retail/rfm_out
hadoop jar "$HADOOP_HOME"/share/hadoop/tools/lib/hadoop-streaming-*.jar \
  -D mapreduce.job.reduces=2 \
  -files src/mapreduce/mapper.py,src/mapreduce/reducer.py \
  -cmdenv SNAPSHOT_ORD=734481 \
  -mapper "python3 mapper.py" -reducer "python3 reducer.py" \
  -input /retail/input/online_retail.csv -output /retail/rfm_out
hdfs dfs -cat /retail/rfm_out/part-* > outputs/rfm_hadoop.csv
