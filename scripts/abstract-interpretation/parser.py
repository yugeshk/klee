#!/usr/bin/env python

import sys 
import string

from instruction import Ins

class Parser:
 
 @staticmethod
 def parse(ip_file):
  ins_list = []
  ctr = 0
  instruction_info_size = 18   #This is the output format of the pin tool. Each instruction contains N-1  lines of metadata
  with open(ip_file) as trace_file:
    for line in trace_file:
      text = line.rstrip()
      if(ctr % instruction_info_size == 0):   #Reset everything for new instruction  
        category = text #First line is category
	IP = ""
	regs = {}
	opcode = ""
	disass = ""
	addresses = []
        ctr = ctr+1
	continue 

      elif(ctr % instruction_info_size > 0 and ctr % instruction_info_size < instruction_info_size-1): #Register values 
      	reg_line = line.split()
	regs[reg_line[0]] = reg_line[2]
	ctr = ctr+1
	continue

      elif(ctr % instruction_info_size == instruction_info_size-1): #Assembly instruction
	ins_components = line.split('|')
	IP = ins_components[0].split()[0]    # Removing the trailing space
	opcode = ins_components[2].split()[0]
	disass = line	# For now, including all the metadata
	addresses = ins_components[3].split()

	# Done parsing this instruction, add it to the list 
	instr = Ins(category, opcode, IP, disass, regs, addresses)
	ins_list.append(instr)

	ctr = ctr+1 
        continue
  
  return ins_list    

 @staticmethod
 def find_nth(haystack, needle, n):
  start = haystack.find(needle)
  while start >= 0 and n > 1:
   start = haystack.find(needle, start+len(needle))
   n -= 1
  return start

