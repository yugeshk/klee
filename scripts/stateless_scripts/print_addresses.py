# Script to print concrete memory addresses touched by trace, both in stateless code and stateful code
# $1: This is the input trace, containing instructions from the stateless code.
# $2: This is the file containing metadata (value of each register) for each instruction in $1
# $3: This file contains the concrete memory locations touched by each stateful function called
# $4: Output file with list of addresses
# $5: This file keeps track of the number of concrete memory addresses from the stateful code now
#     being analysed as part of the concrete stateless code. Since we do a count of memory accesses, we must
#     make sure not to count them twice.

import sys
import re
import string
import os

from collections import namedtuple

ip_trace = sys.argv[1]
ip_metadata = sys.argv[2]
concrete_state_log = sys.argv[3]
op_file = sys.argv[4]
duplicated_stats_file = sys.argv[5]


def main():

    rel_cstate = {}
    with open(concrete_state_log) as cstate:
        # We make assumptions on the name of the file, in particular it will be of the form test######.*
        filename = ip_trace[0:10]
        # This file is small and we can bring it into memory
        trace_cstate = [line.rstrip() for line in cstate if filename in line]
        for line in trace_cstate:
            index1 = find_nth(line, "#", 1)
            index2 = find_nth(line, ":", 2)
            call_number = int(line[index1+1:index2])
            if call_number in rel_cstate:
                rel_cstate[call_number].append(line)
            else:
                rel_cstate[call_number] = [line]
    cstate.close()

    # This variable tells you how many memory accesses have been reported as concrete state.
    # Since we analyze it both in the stateful and stateless code, we shouldn't recount it when tallying mem. accesses in the stateless code.
    duplicated = 0

    # print(sorted(rel_cstate))
    #print("New trace")
    with open(ip_trace) as f, open(ip_metadata) as meta_f:
        with open(op_file, "w") as output:
            for line in f:
                meta_lines = []
                for i in range(17):  # Number of metalines
                    meta_lines.append(meta_f.readline())
                text = line.rstrip()
                if(text.startswith("Call")):
                    if(text.startswith("Call to libVig model")):
                        # Here we do the magic
                        index1 = find_nth(text, "-", 1)
                        called_fn_name = text[index1+2:]

                        if rel_cstate:
                            called_fn_id = sorted(rel_cstate)[0]
                            top_cstate_entry = rel_cstate[called_fn_id][0]
                            index2 = find_nth(top_cstate_entry, ":", 2)
                            index3 = find_nth(top_cstate_entry, ":", 3)
                            index4 = find_nth(top_cstate_entry, ":", 4)
                            fn_name = top_cstate_entry[index2+1:index3]
                            if(fn_name == called_fn_name):
                                # All the setup is done. Now pull in the regs, take the values, generate the cache lines, do this for the rest of the list  and delete the damn entry
                                for top_cstate_entry in rel_cstate[called_fn_id]:
                                    reg = top_cstate_entry[index3+1:index4]
                                    # print(top_cstate_entry)
                                    # print(reg)
                                    reg_values = [
                                        int(value) for value in top_cstate_entry[index4+1:].split()]
                                    meta_lines = [
                                        line.rstrip() for line in meta_lines if not "Call to libVig model" in line]
                                    for each_line in meta_lines:
                                        index5 = find_nth(each_line, "(", 1)
                                        meta_reg = each_line[0:index5-1]
                                        if(meta_reg == reg):
                                            # print(meta_reg)
                                            # print(meta_lines)
                                            index6 = find_nth(
                                                each_line, "=", 1)
                                            meta_reg_val = int(
                                                each_line[index6+2:], 16)
                                            for value in reg_values:
                                                output.write(
                                                    str(hex(meta_reg_val+value))[2:].upper()+"\n")
                                                duplicated = duplicated + 1
                                            # print(meta_reg_val)
                                            # print(reg_values)

                                    # Now need to generate the cache line

                                del rel_cstate[called_fn_id]

                    else:
                        output.write("Irrelevant to Trace\n")
                else:
                    index = find_nth(text, "|", 4)
                    text = text[index+1:]
                    if(text == ""):
                        output.write("Non-memory instruction\n")
                    words = text.split()
                    for addr in words:
                        addr = addr[1:]  # Removing 'r' and 'w' tags
                        output.write(addr)
                        output.write("\n")

    with open(duplicated_stats_file, "w") as dup_op:
        dup_op.write(str(duplicated)+"\n")


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


main()
