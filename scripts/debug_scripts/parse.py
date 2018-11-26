import sys
import re
import string
import os

inp_file = sys.argv[1]
fn_name = sys.argv[2]

def main():
   with open(inp_file) as f:
     trace_lines = (line.rstrip() for line in f)
     trace_lines = list(line for line in trace_lines if line)

     relevant=0
     for text in trace_lines:
                index1 = find_nth(text,"|",2)
		index2 = find_nth(text,"|",3)
                fn = text[index1+1:index2-1]
                if(fn_name in fn):
                    print text[index2+1:]
    


def find_nth(haystack, needle, n):
 start = haystack.find(needle)
 while start >= 0 and n > 1:
  start = haystack.find(needle, start+len(needle))
  n -= 1
 return start

main()
