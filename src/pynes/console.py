from cpu import Cpu
from ppu import Ppu

class Console(object):
	def __init__(self, controllers):
		self.cpu = Cpu(self)
		self.ppu = Ppu(self)
		self.cycle_count = 0