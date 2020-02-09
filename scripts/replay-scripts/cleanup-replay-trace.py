# Script to extract the portions of a executable trace that will be used to match a replayed PCAP
# with a KLEE generated path.
# $1: This is the input trace, containing instructions from both stateless
#     code and modelled stateful functions.
# $2: This is the output trace, which is the subset of the input trace.
#     We only retain jumps and the immediate instruction after them.

import sys
import string

ip_trace = sys.argv[1]
op_trace = sys.argv[2]

jumps = ["ja", "jnbe", "jae", "jnb", "jnc", "jb", "jnae", "jc", "jbe", "jna", "jcxz", "jecxz", "je", "jz", "jg",
         "jge", "jnle", "jl", "jnge", "jle", "jnl", "jne", "jnz", "jng", "jno", "jnp", "jpo", "jns", "jo", "jp", "jpe", "js"]
jumps_uncond = ["jmp", "jmpq"]
calls = ["call", "callq"]
rets = ["ret", "retq", "repz", "repz ret", "repz retq"]


def main():

    branch = 0
    prev_line = ""

    with open(ip_trace) as f, open(op_trace, "w") as output:

        for line in f:
            text = line.rstrip()
            if(text.startswith("Call to")):
                if(not branch):
                    print(ip_trace)
                    print(text)
                    assert(0 and "Something wrong with how call was made")
                elif("libVig" in text):
                    assert(len(prev_line) > 0)
                    output.write(prev_line + "\n")
                    output.write(text + "\n")

                branch = 0
                prev_line = ""
                continue

            # The line will be of the form: IP | Call Stack | Function | Instruction | Memory Accesses
            index = find_nth(text, "|", 2)
            disass = text[index+1:].split()
            if(index == -1):
                assert (0 and "Something wrong with opcode")
            else:
                opcode = disass[0].strip()

            if(branch):
                output.write(prev_line + "\n")
                output.write(text + "\n")
                branch = 0
                prev_line = ""

            if(opcode in jumps or opcode in jumps_uncond or opcode in calls or opcode in rets):
                prev_line = text
                branch = 1


def find_nth(haystack, needle, n):
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start+len(needle))
        n -= 1
    return start


main()
