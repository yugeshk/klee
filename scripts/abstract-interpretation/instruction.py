class Ins:

	def _init_(self,category,opcode,IP,disass,regs)
		self.IP = IP    	    # Instruction pointer
		self.regs = regs	    # Value of all registers before this instruction was executed 
		self.category = category    # Instruction category
		self.opcode = opcode	    # Opcode	 	
		self.disass = disass 	    # Disassembled instruction 	
