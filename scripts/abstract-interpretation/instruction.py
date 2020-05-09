class Ins:


	def __init__(self,category,opcode,IP,disass,regs,addresses):
	  self.IP = IP    	    # Instruction pointer
	  self.regs = regs	    # Value of all registers before this instruction was executed 
	  self.category = category    # Instruction category
	  self.opcode = opcode	    # Opcode	 	
	  self.disass = disass 	    # Disassembled instruction
	  self.addresses = addresses  # Addresses read to and written from 

