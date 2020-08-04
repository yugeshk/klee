import re
import os
import sys

output_file = sys.argv[1]
symbols_file = sys.argv[2]

symbol_map=list()
symbol_re=re.compile("\_[0-9]")

def main():
  with open(symbols_file,'r') as ip:
    for line in ip:
      text = line.rstrip().split(' ')
      for index, word in enumerate(text):
        word = word.strip()
        text[index] = word
      match = symbol_re.search(text[0])
      if(match):
        end = text[0].find(match.group(0))
      else:
        end=len(text[0])
      symbol_map.append((text[0],(text[1]+text[0][text[0].find('_in_'):end]).strip()))
    
  with open(output_file,'r') as ip:
    lines = [line.rstrip('\n') for line in ip]
  
  with open(output_file,'w') as op:
    for line in lines:
      for pattern in reversed(symbol_map):
        line = line.replace(pattern[0],pattern[1])
      op.write(line+"\n")
      
if __name__ == "__main__":
    main()
