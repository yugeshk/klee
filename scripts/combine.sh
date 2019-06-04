
set -euo pipefail

TRACES_DIR=${1:-klee-last}

join -t, -j1 \
      <(sort $TRACES_DIR/stateful-perf.txt | awk -F, '{print $1 "_" $2 "," $3}') \
      <(sort $TRACES_DIR/stateless-perf.txt | awk -F, '{print $1 "_" $2 "," $3}') \
    | sed -e 's/_/,/' \
    | awk -F, '
      {
        performance = ($3 + $4);
        if (performance > max_performance[$2]) {
          max_performance[$2] = performance;
          trace[$2] = $1;
        }
      }

      END {
        for (metric in max_performance) {
          print metric "," max_performance[metric]" -  " trace[metric];
        }
      }'
