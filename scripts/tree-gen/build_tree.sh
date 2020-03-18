#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee

#Defaults
EXPECTED_PERF=0
TRACES_DIR=klee-last
CONSTRAINT_NODE=none


while getopts ":t:e:r:c:p" opt; do
  case $opt in
    t) TREE_TYPE="$OPTARG"
    ;;
    e) EXPECTED_PERF="$OPTARG"
    ;;
    r) RESOLUTION="$OPTARG"
    ;;
    c) CONSTRAINT_NODE="$OPTARG"
    ;;
    p) TRACES_DIR="$OPTARG"
    ;;
    \?) echo "Invalid option -$OPTARG" >&2
    ;;
  esac
done

if [ "$TREE_TYPE" != "neg-tree" ] && [ "$TREE_TYPE" != "res-tree" ]; then 
  echo "Unsupported tree type $TREE_TYPE"
  exit
fi

pushd $TRACES_DIR >> /dev/null

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags

TREE_FILE="constraint-tree.txt"
CONSTRAINT_FILE="constraint-branches.txt"

# METRICS=("instruction count" "memory instructions" "execution cycles")
METRICS=("instruction count")
for METRIC in "${METRICS[@]}"; 
do 
  METRIC_NAME=$(echo "$METRIC" | sed -e 's/ /_/')
  python3 $KLEE_DIR/scripts/tree-gen/build_tree.py tc_tags combined_perf.txt perf-formula.txt "$METRIC" $TREE_TYPE $TREE_FILE $CONSTRAINT_FILE $EXPECTED_PERF $RESOLUTION $CONSTRAINT_NODE
done

popd >> /dev/null

dot $TRACES_DIR/tree.dot -T png -o tree.png