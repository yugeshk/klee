#!/usr/bin/env python

import sys 
import string

from instruction import Ins

ip_file = sys.argv[1]
instruction_info_size = 10   #This is the output format of the pin tool. Each instruction contains 9 lines of metadata, 10 lines in total 

def main():
  with open(ip_file) as trace_file:
    for line in trace_file:
      ctr = 0
      text = line.rstrip()
      if(ctr % instruction_info_size == 0):   #First up is instruction category 
        category = text
      elif(
