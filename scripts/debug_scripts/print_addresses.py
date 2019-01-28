import sys
import re
import string
import os

ip_file = sys.argv[1]
op_file = sys.argv[2]

def main():
   with open(ip_file) as f:
     with open(op_file,"w") as output:
      irrelevant=0
      for line in f:
       text = line.rstrip()
       if(text.startswith("Call")):
        output.write("Irrelevant to Trace\n")
       else:
        index = find_nth(text,"|",3)
        addresses = text[index+1:]
        if(addresses == ""):
         output.write("Non-memory instruction\n")
        words = addresses.split() 
        i=0
        while i < len(words):
         words[i]=words[i][1:]
         output.write(words[i])
  	 output.write("\n")
         i+=1
       


def find_nth(haystack, needle, n):
 start = haystack.find(needle)
 while start >= 0 and n > 1:
  start = haystack.find(needle, start+len(needle))
  n -= 1
 return start

main()

