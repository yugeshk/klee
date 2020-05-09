
from exec_state import ExecutionState
from instruction import Ins 

class ExecutionEngine:
	
	def __init__(self,state):
	  self.state = state   #State of the engine before execution begins 
	
	def execute(self,ins_list):
	  for ins in ins_list:
	    self.execute_instruction(ins)	

        def execute_instruction(self,ins):

          #This can possibly be modularised better, but for now, all the junk goes in here
          if (ins.opcode == "push"):
            disass = ins.disass.split('|')[2]
            #assert len(disass.split()) == 2
	  
	  if(len(disass.split()) == 2):
	    rsp = self.state.regs["rsp"]
	    rsp = str(int(rsp) - 8)
	    target = disass.split()[1]
	    self.state.mem[rsp] = self.state.regs[target]

	  elif(len(disass.split()) != 2):
	      print disass

          else:
            print("Opcode %s not found error" %(ins.opcode))



