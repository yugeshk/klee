import sys
import re
import string
import os

inp_file = sys.argv[1]

def main():
   with open(inp_file) as f:
     trace_lines = (line.rstrip() for line in f)
     trace_lines = list(line for line in trace_lines if line)

     relevant=0
     for text in trace_lines:
     	if(text.startswith("Call")):
        	output.write("Irrelevant to Trace\n")
        else:
        	index = find_nth(text,"|",4)
        	text = text[index+1:]
        	if(text != ""):
         		relevant = relevant+1
     print relevant


def find_nth(haystack, needle, n):
 start = haystack.find(needle)
 while start >= 0 and n > 1:
  start = haystack.find(needle, start+len(needle))
  n -= 1
 return start

main()
