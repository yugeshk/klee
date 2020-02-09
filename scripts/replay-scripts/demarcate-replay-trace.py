# Script to extract the portions of the replayed trace that are part of the
# stateless code, hence removing the contents of modelled functions.
# $1: This is the input trace.
# $2: This is the output trace, which is the subset of the input trace.
#     All instructions from the stateless code is retained.
#     Instructions from stateful code is replaced with a one-line description
#     of the function call and the path taken through it.
# $5: List of stateful functions that are modelled out during Symbex
# $6: List of framework functions modelled out. This is either DPDK functions
#     (if only the NF is being analyzed) and HW functions (if NF+DPDK is being analyzed)
# $7: List of time functions modelled out during Symbex

import sys
import re
import string
import os

ip_trace = sys.argv[1]
op_trace = sys.argv[2]
stateful_file = sys.argv[3]
dpdk_file = sys.argv[4]
time_file = sys.argv[5]

stateful_fns = {}
dpdk_fns = {}
time_fns = {}


def main():

    with open(stateful_file, "r") as stateful:
        stateful_fns = (line.rstrip() for line in stateful)
        stateful_fns = list(line for line in stateful_fns if line)

    with open(dpdk_file, "r") as dpdk:
        dpdk_fns = (line.rstrip() for line in dpdk)
        dpdk_fns = list(line for line in dpdk_fns if line)

    with open(time_file, "r") as time:
        time_fns = (line.rstrip() for line in time)
        time_fns = list(line for line in time_fns if line)

    with open(ip_trace) as f:
        with open(op_trace, "w") as output:
            currently_demarcated = 0
            currently_demarcated_fn = ""

            for line in f:

                text = line.rstrip()

                # The line will be of the form: IP | Function | Instruction | Memory Accesses
                index1 = find_nth(text, "|", 1)
                if(index1 == -1):
                    continue
                index2 = find_nth(text, "|", 2)
                disass = text[index2+1:].split()
                if(len(disass) == 0):
                    continue  # Something wrong
                else:
                    opcode = disass[0]
                current_fn_name = text[index1+1:index2-1]

                if(currently_demarcated):
                    if("ds_path" in current_fn_name):
                        output.write(". DS PATH-%s" %
                                     (current_fn_name[len(current_fn_name)-1:]) + "\n")

                    if(opcode != "ret"):
                        continue

                if(currently_demarcated and str(opcode) == "ret" and current_fn_name == currently_demarcated_fn):
                    currently_demarcated = 0
                    currently_demarcated_fn = ""

                elif (currently_demarcated == 0):

                    if(current_fn_name in stateful_fns):
                        currently_demarcated = 1
                        if(current_fn_name == "vector_return"):
                            current_fn_name = "ds_path_1"  # Jump instead of call
                        currently_demarcated_fn = current_fn_name
                        output.write(
                            "Call to libVig model - " + current_fn_name)  # Add the "\n" after adding the path

                    elif(current_fn_name in dpdk_fns):
                        currently_demarcated = 1
                        currently_demarcated_fn = current_fn_name
                        output.write(
                            "Call to DPDK model - " + current_fn_name + "\n")  # Add the "\n" after adding the path

                    elif(current_fn_name in time_fns):
                        assert(0 and "Time functions unsupported in replay trace")

                    else:
                        output.write(text+"\n")


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


main()
