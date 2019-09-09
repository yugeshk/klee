#!/bin/bash

set -euo pipefail

KLEE_DIR=~/projects/Bolt/klee
TRACES_DIR=${1:-klee-last}

pushd $TRACES_DIR

grep "TRAFFIC_CLASS" *.call_path | awk -F: '{print $1 "," $2}' | awk -F' = ' '{print $1 "," $2}' | sed 's/\.call_path//g' > tc_tags
python $KLEE_DIR/scripts/contract-tree/build_tree.py tc_tags combined_perf.txt perf-formula.txt "instruction count" tree.txt 100 perf_var

popd

dot $TRACES_DIR/tree.dot -T png -o tree.png