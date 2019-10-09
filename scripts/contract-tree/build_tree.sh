#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee
TREE_TYPE=$1
TRACES_DIR=${2:-klee-last}

if [ "$TREE_TYPE" != "call-tree" ] && [ "$TREE_TYPE" != "full-tree" ]; then
  echo "Unsupported tree type: $TREE_TYPE"
  exit
fi

pushd $TRACES_DIR

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags
if [ "$TREE_TYPE" == "full-tree" ]; then
  TREE_FILE="full-tree.txt"
  python $KLEE_DIR/scripts/contract-tree/rem-prefix.py ./ $TREE_FILE
else
  TREE_FILE="call-tree.txt"
fi

# METRICS=("instruction count" "memory instructions" "execution cycles")
METRICS=("instruction count")
for METRIC in "${METRICS[@]}"; 
do 
  METRIC_NAME=$(echo "$METRIC" | sed -e 's/ /_/')
  python $KLEE_DIR/scripts/contract-tree/build_tree.py tc_tags combined_perf.txt perf-formula.txt "$METRIC" $TREE_FILE $TREE_TYPE 0 perf_var_$METRIC_NAME formula_var_$METRIC_NAME 
done

popd

dot $TRACES_DIR/tree.dot -T png -o tree.png