#!/usr/bin/env python
# vim: set ts=2 sts=2 sw=2 et si tw=80:

import sys
import string
import os
import subprocess

ip_dir = sys.argv[1]
op_file = sys.argv[2]
lines_list = list()
common_prefix_len = 0

for root, dirs, files in os.walk(ip_dir):
    for file in files:
        with open(file) as f:
            if file.endswith(".path"):
                lines_list.append([line.rstrip() for line in f])
                # lines_list.append([1, 2, 3, 4])
                if(len(lines_list) == 1):
                    continue
                else:
                    assert(len(lines_list) == 2)
                    lines_list[0] = os.path.commonprefix(lines_list)
                    del lines_list[1]
    assert(len(lines_list) == 1)
common_prefix_len = len(lines_list[0])
del lines_list[0]
with open(op_file, "w") as op:
    for root, dirs, files in os.walk(ip_dir):
        for file in files:
            with open(file) as f:
                if file.endswith(".path"):
                    file_name = file.replace(
                        '.sym.path', '')
                    file_name = file_name[len(file_name)-3:]
                    lines_list = [line.rstrip() for line in f]
                    lines_list = lines_list[common_prefix_len:]
                    string_list = ','.join(lines_list)
                    string_list = file_name + ":" + string_list
                    op.write(string_list+"\n")
