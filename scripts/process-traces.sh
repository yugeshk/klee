#!/bin/bash

set -euo pipefail

TRACES_DIR=${1:-klee-last}
verif_arg=${2:-verify-dpdk}
shift || true

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Generating instruction traces."
$SCRIPT_DIR/trace-instruction.sh $TRACES_DIR

echo "Computing stateless bounds."
$SCRIPT_DIR/stateless_perf.sh $TRACES_DIR stateless_perf.txt $verif_arg

echo "Computing stateful bounds."
$SCRIPT_DIR/stitch-traces.sh $TRACES_DIR $@
