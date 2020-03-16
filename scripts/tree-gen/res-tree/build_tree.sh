#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee
RESOLUTION=$1
CONSTRAINT=${2:-none}
TRACES_DIR=${3:-klee-last}

pushd $TRACES_DIR >> /dev/null

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags

TREE_FILE="constraint-tree.txt"
CONSTRAINT_FILE="constraint-branches.txt"


# METRICS=("instruction count" "memory instructions" "execution cycles")
METRICS=("instruction count")
for METRIC in "${METRICS[@]}"; 
do 
  METRIC_NAME=$(echo "$METRIC" | sed -e 's/ /_/')
  python $KLEE_DIR/scripts/tree-gen/res-tree/build_tree.py tc_tags combined_perf.txt perf-formula.txt "$METRIC" $TREE_FILE $CONSTRAINT_FILE $RESOLUTION perf_var_$METRIC_NAME formula_var_$METRIC_NAME $CONSTRAINT
done

popd >> /dev/null

dot $TRACES_DIR/tree.dot -T png -o tree.png