#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee
TRACES_DIR=${1:-klee-last}

pushd $TRACES_DIR

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags
METRICS=("instruction count" "memory instructions" "execution cycles")
for METRIC in "${METRICS[@]}"; 
do 
  METRIC_NAME=$(echo "$METRIC" | sed -e 's/ /_/')
  python $KLEE_DIR/scripts/contract-tree/build_tree.py tc_tags combined_perf.txt perf-formula.txt "$METRIC" tree.txt 0 perf_var_$METRIC_NAME formula_var_$METRIC_NAME 
done

popd

dot $TRACES_DIR/tree.dot -T png -o tree.png