import sys
import re
import string
import os

trace_path = sys.argv[1]
num_insns = sys.argv[2]
num_accesses_file=sys.argv[3]
hits_file=sys.argv[4]
misses_file = sys.argv[5]
trace_nos_file = sys.argv[6]

def main():
 with open(num_insns,"w") as insns_output,open(hits_file,'w') as hit_output,open(num_accesses_file,'w') as num_output,open(misses_file,'w') as miss_output,open(trace_nos_file,'w') as trace_output:
  for root, dirs, files in os.walk(trace_path):
   for file in files:
    with open(file) as f:
     if file.endswith(".packet.classified_mem_trace"):
      file_name = file.replace('.packet.classified_mem_trace','')
      trace_output.write(file_name+"\n")
      insns = 0
      num_accesses = 0
      hits = 0
      for line in f:
       text = line.rstrip()
       if(not(text=="Irrelevant to Trace")):
        if(text=="Non-memory instruction"):
         insns = insns + 1
        else:
         num_accesses+=1
        if(text == "Hit"):
         hits+=1
      
      dup_file=file.replace('classified_mem_trace','duplicated')
      with open(dup_file) as dup_ip:
	dup = [line.rstrip() for line in dup_ip]
        dup_accesses = int(dup[0])
      insns_output.write(str(insns) + "\n")
      hit_output.write(str(hits)+"\n")
      miss_output.write(str(num_accesses-hits)+"\n")
      num_accesses= num_accesses - dup_accesses
      num_output.write(str(num_accesses)+"\n")

main()
