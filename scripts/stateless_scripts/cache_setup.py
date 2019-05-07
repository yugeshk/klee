# Script to analyze a sequence of memory address using a simple 1 level, set associative LRU cache.
# Prints the contents of the cache at the end of the trace.
# $1: Input trace of memory addresses
# $2: Output file, with final cache contents

import re
import sys
import subprocess
import string
import os

ip_file = sys.argv[1]  # Symbolic address trace
op_file = sys.argv[2]  # Classified address trace
cache_size = 32768
cache_block_size = 64
set_associativity = 8
set_size = cache_block_size*set_associativity
num_sets = cache_size/set_size
cache_contents = [[] for _ in xrange(num_sets)]
cache_ages = [[] for _ in xrange(num_sets)]

# Assuming replacement policy is LRU

symbol_re = re.compile("Irrelevant to Trace")
symbol2_re = re.compile("Non-memory instruction")


def main():
    global cache_contents
    global cache_ages
    with open(ip_file) as f:

        for line in f:
            text = line.rstrip()
            m1 = symbol_re.match(text)
            m2 = symbol2_re.match(text)
            if(m1):
                age_cache_contents()
            elif(not m2):
                addr = int(text, 16)
                block_no = addr/cache_block_size
                set_no = block_no % num_sets
                if block_no not in cache_contents[set_no]:
                    cache_contents[set_no].append(block_no)
                    cache_ages[set_no].append(None)
                update_ages(block_no, set_no)

    print_cache_contents(op_file)


def age_cache_contents():
    global cache_contents
    global cache_ages
    for x in xrange(len(cache_ages)):
        for y in xrange(len(cache_ages[x])):
            # cache_ages[x][y]=set_associativity+1 # Clear cache
            cache_ages[x][y] = cache_ages[x][y]  # Don't clear cache.


def update_ages(block_num, set_num):
    global cache_contents
    global cache_ages
    index = cache_contents[set_num].index(block_num)
    age = cache_ages[set_num][index]
    for x in xrange(len(cache_ages[set_num])):
        if(x == index):
            cache_ages[set_num][x] = 0
        elif(not(x == index) and cache_ages[set_num][x] <= age):
            cache_ages[set_num][x] += 1


def print_cache_contents(op_file):
    global cache_contents
    global cache_ages
    with open(op_file, "w") as output:
        for x in xrange(len(cache_ages)):
            for y in xrange(len(cache_ages[x])):
                if(cache_ages[x][y] < set_associativity):
                    output.write(str(hex(cache_contents[x][y]))+"\n")


main()
