import re
import os
import sys

tree_file = sys.argv[1]



def main():
  with open(tree_file,'r') as ip:
    lines = [line.rstrip('\n') for line in ip]
  
  with open(tree_file,'w') as output:
    output.write("** Perf Envelope Violations **\n")
    for line in lines:
      words = line.split(',')
      assert(len(words) == 2 and "Malformed neg-tree")
      constraints = words[0].split('\t')
      output.write("if (")
      loop_ctr = 0
      for term in constraints:
        output.write(term)
        loop_ctr = loop_ctr + 1
        if( loop_ctr < len(constraints) -1 ):
          output.write(" and ")
      output.write("): perf = %s\n" % (words[1]))
      
if __name__ == "__main__":
    main()