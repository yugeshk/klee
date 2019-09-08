# Script to combine performance formulae from the stateful and stateless code
#
# $1 - File with formulae from stateful code
# $2 - File with performance of stateless code
# $3: Output file

import sys
import re
import string
import os

stateful_file = sys.argv[1]
stateless_file = sys.argv[2]
op_file = sys.argv[3]

stateless_perf = {}
stateful_perf = {}
metrics = ["instruction count", "memory instructions", "execution cycles"]

with open(stateless_file, 'r') as sless_file:
    for line in sless_file:
        line = line.rstrip()
        line = line.split(',')
        assert(len(line) == 3)  # Something wrong with output format
        if(line[0] in stateless_perf):
            stateless_perf[line[0]][line[1]] = line[2]
        else:
            stateless_perf[line[0]] = {}
            stateless_perf[line[0]][line[1]] = line[2]

with open(stateful_file, 'r') as sful_file:
    for line in sful_file:
        line = line.rstrip()
        line = line.split(',')
        assert(len(line) == 3)  # Something wrong with output format
        if(line[0] in stateful_perf):
            stateful_perf[line[0]][line[1]] = line[2]
        else:
            stateful_perf[line[0]] = {}
            stateful_perf[line[0]][line[1]] = line[2]

with open(op_file, "w") as op:
    for key, val in stateful_perf.items():
        for metric in metrics:
            formula = val[metric].split('+')
            final_formula = ""
            for term in formula:
                term = term.strip()
                if("*" not in term):
                    term = str(int(term)+int(stateless_perf[key][metric]))
                if(final_formula != ""):
                    final_formula = final_formula + " + "
                final_formula = final_formula + term
            op.write("%s,%s,%s\n" % (key, metric, final_formula))
