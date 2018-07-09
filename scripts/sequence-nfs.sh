#!/bin/bash

set -euo pipefail

SENDER_TRACES_DIR=$1
RECEIVER_TRACES_DIR=$2

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

parallel 'check-call-path-compatibility {1} {2} >/dev/null 2>/dev/null && echo $(basename {1} .call_path),$(basename {2} .call_path) || true' \
    ::: $SENDER_TRACES_DIR/*.call_path \
    ::: $RECEIVER_TRACES_DIR/*.call_path \
    | sort > compatible-paths.csv

join -t , -1 1 -2 1 <(sort $SENDER_TRACES_DIR/stateless-perf.txt) <(sort $SENDER_TRACES_DIR/stateful-perf.txt) \
    | awk '
        BEGIN { FS=","; OFS="," }
        $2 == $4 { print $1,$2,$3,$5 }' \
    | sort \
    > $SENDER_TRACES_DIR/all-perf.csv

join -t , -1 1 -2 1 <(sort $RECEIVER_TRACES_DIR/stateless-perf.txt) <(sort $RECEIVER_TRACES_DIR/stateful-perf.txt) \
    | awk '
        BEGIN { FS=","; OFS="," }
        $2 == $4 { print $1,$2,$3,$5 }' \
    | sort \
    > $RECEIVER_TRACES_DIR/all-perf.csv

join -t , -1 1 -2 1 compatible-paths.csv $SENDER_TRACES_DIR/all-perf.csv \
    | sort -t , -k 2 \
    | join -t , -1 2 -2 1 - $RECEIVER_TRACES_DIR/all-perf.csv \
    | awk '
        BEGIN { FS=","; OFS="," }
        $3 == $6 { print $2,$1,$3,$4,$5,$7,$8,($4+$5+$7+$8) }' \
    | sort \
    > sequence-perf.csv

    awk -F, '
      {
        if ($8 > max_performance[$3]) {
          max_performance[$3] = $8;
        }
      }

      END {
        for (metric in max_performance) {
          print metric "," max_performance[metric];
        }
      }' sequence-perf.csv
