#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee
TREE_TYPE=$1
RESOLUTION=$2
CONSTRAINT=${3:-none}
TRACES_DIR=${4:-klee-last}

if [ "$TREE_TYPE" != "call-tree" ] && [ "$TREE_TYPE" != "full-tree" ] && [ "$TREE_TYPE" != "constraint-tree" ]; then
  echo "Unsupported tree type: $TREE_TYPE"
  exit
fi

pushd $TRACES_DIR >> /dev/null

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags
CONSTRAINT_FILE=""
if [ "$TREE_TYPE" == "full-tree" ]; then
  TREE_FILE="full-tree.txt"
  python $KLEE_DIR/scripts/contract-tree/rem-prefix.py ./ $TREE_FILE
elif [ "$TREE_TYPE" == "call-tree" ]; then
  TREE_FILE="call-tree.txt"
else 
  TREE_FILE="constraint-tree.txt"
  CONSTRAINT_FILE="constraint-branches.txt"
fi

# METRICS=("instruction count" "memory instructions" "execution cycles")
METRICS=("instruction count")
for METRIC in "${METRICS[@]}"; 
do 
  METRIC_NAME=$(echo "$METRIC" | sed -e 's/ /_/')
  python $KLEE_DIR/scripts/contract-tree/build_tree.py tc_tags combined_perf.txt perf-formula.txt "$METRIC" $TREE_FILE $TREE_TYPE $CONSTRAINT_FILE $RESOLUTION perf_var_$METRIC_NAME formula_var_$METRIC_NAME $CONSTRAINT
done

popd >> /dev/null

dot $TRACES_DIR/tree.dot -T png -o tree.png