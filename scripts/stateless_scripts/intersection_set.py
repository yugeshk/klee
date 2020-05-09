# Script to find intersection set of a number of lists
#
# $1: Directory with all the lists
# $2: Output file to write the intersection set
# $3: File which specifies the relevant files in $1. 

import re
import sys
import subprocess
import string
import os

ip_dir = sys.argv[1]  #
op_file = sys.argv[2]  #
relevant_traces = sys.argv[3]


def main():

    with open(relevant_traces, 'r') as rel_traces:
        traces = rel_traces.read().splitlines()

    intersection_set = []
    for root, dirs, files in os.walk(ip_dir):
        ctr = 0
        for file in files:
            with open(file) as f:
                if file.endswith(".packet.cache_remnants"):
                    lines = f.read().splitlines()

                    # We make assumptions on the name of the file, in particular it will be of the form test######.*
                    file_name = str(file)[0:10]
                    if (file_name in traces):
                        if (ctr == 0):
                            intersection_set = lines
                        else:
                            temp = set(intersection_set)
                            intersection_set = [
                                value for value in lines if value in temp]
                        ctr = ctr + 1

    with open(op_file, 'w') as output:
        for block in intersection_set:
            output.write(str(block)+"\n")


if __name__ == "__main__":
    main()
