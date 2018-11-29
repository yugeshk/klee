import re
import sys
import subprocess 
import string 
import os 

ip_dir = sys.argv[1] #Directory with all the cache_remnants files 
op_file = sys.argv[2] #Output file to write the intersection set 
def main():

  intersection_set = []
  for root, dirs, files in os.walk(ip_dir):
    ctr = 0
    for file in files:
      with open(file) as f:
        if file.endswith(".packet.cache_remnants"):
          lines = f.read().splitlines()
	  if (ctr == 0):
            intersection_set = lines
          else:
            temp = set(intersection_set)
            intersection_set = [value for value in lines if value in temp]
          ctr = ctr + 1

  with open(op_file,'w') as output:  
    for block in intersection_set:
      output.write(str(block)+"\n")

if __name__ == "__main__":
    main()
