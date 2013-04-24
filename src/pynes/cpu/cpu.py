import numpy
import logging
from ppu import Ppu
from cpu import InstructionSet
from utils import Enumerate

log = logging.getLogger('PyNES')
addressing = Enumerate("NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")

class Cpu(object):
	def __init__(self, console):
		log.debug("Initializing CPU")
		self.console = console
		
		self._instruction_set = InstructionSet(self)

		self.registers = {'pc': numpy.uint16(), 'a': numpy.int8(), 'x': numpy.uint8(), 'y': numpy.uint8(), 'sp': numpy.uint8()}
		self.status = {'carry': False, 'zero': False, 'irqdis': True, 'decimal': False, 'brk': True, 'overflow': False, 'negative': False} 

	def reset(self):
		self.registers['pc'] = (self.mem_read(0xfffd) << 8) + self.mem_read(0xfffc)
		log.debug("PC initialized to {0:#4x}".format(self.registers['pc']))

	def get_value(self, addmode, param):
		if (addmode == addressing.IMMEDIATE):
			return param
		elif (addmode == addressing.ZEROPAGE):
			return self.mem_read(param)
		elif (addmode == addressing.ZEROPAGE_X):
			address = numpy.uint8(param + self.registers['x'])
			return self.mem_read(address)
		elif (addmode == addressing.ZEROPAGE_Y):
			address = numpy.uint8(param + self.registers['y'])
			return self.mem_read(address)
		elif (addmode == addressing.ABSOLUTE):
			return self.mem_read(param)
		elif (addmode == addressing.ABSOLUTE_X):
			return self.mem_read(param + self.registers['x'])
		elif (addmode == addressing.ABSOLUTE_Y):
			return self.mem_read(param + self.registers['y'])
		elif (addmode == addressing.INDIRECT_X):
			indirect_address = param + self.registers['x']
			address = self.mem_read(indirect_address)
			address += (self.mem_read(indirect_address + 1) << 8)
			return self.mem_read(address)
		elif (addmode == addressing.INDIRECT_Y):
			address = self.mem_read(param)
			address += (self.mem_read(param + 1) << 8)
			return self.mem_read(address + self.registers['y'])
		elif (addmode == addressing.ACCUMULATOR):
			return self.registers['a']
		else:
			raise Exception("get_value called for unsupported addressing mode {0}.".format(addmode))

	def write_back(self, addmode, address, value):
		if addmode in (addressing.ZEROPAGE, addressing.ABSOLUTE):
			self.mem_write(address, value)
		elif addmode in (addressing.ZEROPAGE_X, addressing.ABSOLUTE_X):
			self.mem_write(self.registers['x'] + address, value)
		elif addmode in (addressing.ZEROPAGE_Y, addressing.ABSOLUTE_Y):
			self.mem_write(self.registers['y'] + address, value)
		elif addmode == addressing.INDIRECT_X:
			indirect_address = address + self.registers['x']
			address = self.mem_read(indirect_address)
			address += (self.mem_read(indirect_address + 1) << 8)
			self.mem_write(address, value)
		elif addmode == addressing.INDIRECT_Y:
			address = self.mem_read(address)
			address += (self.mem_rest(address + 1) << 8)
			self.mem_write(address + self.registers['y'], value)
		elif addmode == addressing.ACCUMULATOR:
			self.registers['a'] = numpy.int8(value)
		else:
			raise Exception("Write back not implemented for addressing mode {0}.".format(addmode))

	def set_zero(self, value):
		self.status['zero'] = (value == 0)

	def set_negative(self, value):
		self.status['negative'] = (numpy.int8(value) < 0) 
	
	def get_status_register(self):
		value = int(self.status['carry'])
		value += int(self.status['zero']) << 1
		value += int(self.status['irqdis']) << 2
		value += int(self.status['decimal']) << 3
		value += int(self.status['brk']) << 4
		value += 1 << 5
		value += int(self.status['overflow']) << 6
		value += int(self.status['negative']) << 7
		return value
	
	def set_status_register(self, value):
		self.status['carry'] = bool(value & (1))
		self.status['zero'] = bool(value & (1 << 1))
		self.status['irqdis'] = bool(value & (1 << 2))
		self.status['decimal'] = bool(value & (1 << 3))
		self.status['brk'] = bool(value & (1 << 4))
		self.status['overflow'] = bool(value & (1 << 6))
		self.status['negative'] = bool(value & (1 << 7))

	def stack_push(self, value):
		self.registers['sp'] -= 1
		self.mem_write(0x100 + self.registers['sp'], value)

	def stack_pop(self):
		val = self.mem_read(0x100 + self.registers['sp'])
		self.registers['sp'] += 1
		return val

	def interrupt(self, int_type):
		pc = self.registers['pc'] - 1
		self.stack_push((pc >> 8) & 0xff)
		self.stack_push(pc & 0xff)
		self.stack_push(self.get_status_register())

		if int_type == 'NMI':
			self.registers['pc'] = (self.mem_read(0xfffb) << 8) + self.mem_read(0xfffa)			
		elif int_type == 'IRQ':
			self.registers['pc'] = (self.mem_read(0xffff) << 8) + self.mem_read(0xfffe)
		else:
			raise Exception("Unhandled interrupt type {0}.".format(int_type))