# Script to perform longest prefix matching on the branches that a replayed trace takes
# This is used to identify which symbex path the packet actually went down
# $1: This is the input trace.
# $2: This is the folder containing all the candidate execution paths

import sys
import re
import string
import os

ip_trace = sys.argv[1]
candidates_path = sys.argv[2]


def main():

    lines = [line.rstrip("\n")
             for line in open(ip_trace)]  # Small file

    lpm_trace_num = ""

    lpm_match_dist = 0

    for root, dirs, files in os.walk(candidates_path):
        for file in files:
            if(file.endswith(".packet.comparison.trace")):
                candidate_lines = [line.rstrip("\n")
                                   for line in open(file)]  # Small file
                for i in range(0, len(lines)):
                    if lines[i] != candidate_lines[i]:
                        break

                match_len = i

                if(match_len > lpm_match_dist):
                    lpm_match_dist = match_len
                    lpm_trace_num = file.replace(
                        ".packet.comparison.trace", "")

    print("Given PCAP file matched with trace %s" % (lpm_trace_num[4:]))


main()
