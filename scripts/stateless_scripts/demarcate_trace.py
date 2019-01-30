import sys
import re
import string 
import os

ip_trace = sys.argv[1]
op_trace = sys.argv[2]
ip_metadata = sys.argv[3]
op_metadata = sys.argv[4]
stateful_file = sys.argv[5]
dpdk_file = sys.argv[6]
time_file = sys.argv[7]
verification_file = sys.argv[8]

stateful_fns = {}
verif_fns = {}
dpdk_fns = {}
time_fns = {}
symbol_re = re.compile('klee*')
symbol2_re = re.compile('_exit@plt*')

def main():
 with open(stateful_file,"r") as stateful:
  stateful_fns = (line.rstrip() for line in stateful) 
  stateful_fns = list(line for line in stateful_fns if line)

 with open(verification_file,"r") as verif:
  verif_fns = (line.rstrip() for line in verif)
  verif_fns = list(line for line in verif_fns if line)

 with open(dpdk_file,"r") as dpdk:
  dpdk_fns = (line.rstrip() for line in dpdk)
  dpdk_fns = list(line for line in dpdk_fns if line)

 with open(time_file,"r") as time:
  time_fns = (line.rstrip() for line in time)
  time_fns = list(line for line in time_fns if line)

 with open(ip_trace) as f, open(ip_metadata) as meta_f :
     with open(op_trace,"w") as output, open(op_metadata,"w") as meta_output:
      currently_demarcated = 0
      currently_demarcated_fn = ""

      for line in f:
       meta_lines=[]
       for i in range(17): #Number of metalines
        meta_lines.append(meta_f.readline())
       text=line.rstrip()
       index1 = find_nth(text,"|",1)
       index2 = find_nth(text,"|",2)
       index3 = find_nth(text,"|",3)
       disass = text[index3+1:].split()
       if(len(disass)==0):
        continue #Something wrong 
       else:
        opcode = disass[0]
       fn_call_stack = text[index1+1:index2-1]+text[index2+1:index3-1]
       current_fn_name = text[index2+1:index3-1]
       words = fn_call_stack.split(" ")
       stateful = 0
       dpdk = 0
       time = 0
       verif = 0

       if(currently_demarcated and opcode != "ret"):
	 continue
   
       elif(currently_demarcated and str(opcode) == "ret" and current_fn_name == currently_demarcated_fn):
	currently_demarcated = 0
	currently_demarcated_fn = ""
       
       elif (currently_demarcated == 0):
        for fn_name in words:
         if(fn_name in stateful_fns):
	  stateful = 1
          break
         elif(fn_name in dpdk_fns):
          dpdk = 1
          break
         elif(fn_name in time_fns):
          time = 1
          break
         elif(fn_name in verif_fns or symbol_re.match(fn_name) or symbol2_re.match(fn_name)):
          verif = 1
          break
        
        if(stateful or dpdk or verif or time):
	 currently_demarcated = 1
	 if(current_fn_name == " dmap_get_value" or current_fn_name == " vector_return_half" or current_fn_name == " vector_return_full"):
	  current_fn_name = " klee_forbid_access" #Jump instead of call
	 if(current_fn_name == " flood"):
	  current_fn_name = "flood"  #Will always fail and exit
	 currently_demarcated_fn = current_fn_name
	 meta_lines = [ line for line in meta_lines if not "|" in line]

	for each_line in meta_lines:
          meta_output.write(each_line)
        
	if(stateful):
         output.write("Call to libVig model - " + fn_name + "\n")
         meta_output.write("Call to libVig model - " + fn_name + "\n")
        elif(dpdk):
	 output.write("Call to DPDK model - " + fn_name + "\n")
	 meta_output.write("Call to DPDK model - " + fn_name + "\n")
        elif(time):
         output.write("Call to Time model - " + fn_name + "\n")
         meta_output.write("Call to Time model - " + fn_name + "\n")
        elif(verif):
         output.write("Call to Verification Code - " + fn_name + "\n")
         meta_output.write("Call to Verification Code - " + fn_name + "\n")
        else:
         output.write(text)
         output.write("\n") 

  
def find_nth(haystack, needle, n):
 start = haystack.find(needle)
 while start >= 0 and n > 1:
  start = haystack.find(needle, start+len(needle))
  n -= 1
 return start

main()
