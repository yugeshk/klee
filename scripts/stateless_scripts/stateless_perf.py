# Script to calculate performance of each trace, from computed parameters
#
# $1-$5: Input files with instruction count, mem accesses,
#        hits, misses and order of traces
# $2: Output file, with performance value for each trace

import sys
import re
import string
import os

num_insns = sys.argv[1]
num_accesses_file = sys.argv[2]
hits_file = sys.argv[3]
misses_file = sys.argv[4]
trace_nos = sys.argv[5]
perf_out = sys.argv[6]


dram_latency = 200
l1_latency = 2
cpi = 1

with open(perf_out, 'w') as output:
    with open(num_insns, 'r') as f1, open(num_accesses_file, 'r') as f2, open(hits_file, 'r') as f3, open(misses_file) as f4, open(trace_nos) as f5:
        for line1, line2, line3, line4, line5 in zip(f1, f2, f3, f4, f5):
            l1 = int(line1)
            l2 = int(line2)
            l3 = int(line3)
            l4 = int(line4)
            line5 = line5.strip()
            line5 = line5.replace(".packet.stateless_mem_trace.classified", "")
            perf = l1*cpi + (l4)*dram_latency + l3*l1_latency
            output.write(line5 + "," + "instruction count" +
                         "," + str(l1+l2)+"\n")
            output.write(line5 + "," + "memory instructions" +
                         "," + str(l2)+"\n")
            output.write(line5 + "," + "execution cycles" +
                         "," + str(perf)+"\n")
