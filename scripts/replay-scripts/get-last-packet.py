#!/usr/bin/env python


# Script to extract the portions of a replayed trace that correspond to the last packet replayed
# $1: This is the input trace
# $2: This is the output trace, with only the instructions from the last packet.

import sys
import string

ip_trace = sys.argv[1]
op_trace = sys.argv[2]

lines = [line.rstrip("\n") for line in open(ip_trace)]
assert(lines[-1] == "New Packet" and "Last line is poor")
del lines[-1]

if("New Packet" not in lines):  # Only one packet
    start = 0
else:
    start = next(i for i in reversed(range(len(lines)))
                 if "New Packet" == lines[i]) + 1

lines = lines[start:]

with open(op_trace, "w") as output:
    for line in lines:
        output.write(line + "\n")
