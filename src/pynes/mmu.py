class Mmu(object):
	def __init__(self, console):
		self.console = console
			self._memory = {}
			self._memory['RAM'] = [0xff] * 0x800 # 0x0000 - 0x07ff
			self._memory['expansion_rom'] = [0xff] * 0x1fe0 # 0x4020 - 0x5fff
			self._memory['SRAM'] = [0xff] * 0x2000 # 0x6000 - 0x7fff

	def write(self, address, value):
		if address < 0 or address >= 0x10000:
			raise Exception('Memory write out of bounds: {0x:#4x}'.format(address))

		# RAM is mirrored 4x, so get the base address before writing to the RAM array.
		if (address < 0x2000):
			base_address = address % 0x800
			# log.debug("WRITE to RAM address {0:#x}".format(base_address))
			self._memory['RAM'][base_address] = value

		# PPU I/O registers
		elif address >= 0x2000 and address < 0x4000:
			self._ppu.mem_write(address, value)
		
		# pAPU I/O registers
		elif (address >= 0x4000 and address < 0x4014) or address == 0x4015:
			self._papu.register_write(address, value)

		# DMA Sprite Transfer
		elif address == 0x4014:
			raise Exception("DMA Sprite Transfer not implemented.")

		elif address == 0x4016:
			if self.controller1 != None:
				self.controller1.toggle_strobe(bool(value & 1))
		
		elif address == 0x4017:
			if self.controller2 != None:
				self.controller2.toggle_strobe(bool(value & 1))

		elif address >= 0x6000 and address < 0x8000:
			self._memory['SRAM'][address - 0x6000] = value
		
		elif address >= 0x8000 and address < 0x10000:
			self.cartridge.mapper.mem_write(address, value)

		else:
			raise Exception("Unhandled memory write to address {0:#4x} at {1:#4x}".format(address, self.registers['pc']))

	def read(self, address):
		if address < 0 or address >= 0x10000:
			raise Exception('Memory read out of bounds: {0:#4x}'.format(address))
		
		# RAM is mirrored 4x, so get the base address before returning the value from the RAM array.
		if address < 0x2000:
			base_address = address % 0x800
			# log.debug("Read from RAM address {0:#x}".format(base_address))
			return self._memory['RAM'][address]
		
		elif address >= 0x2000 and address < 0x4000:
			address -= 0x2000
			base = address % 8
			if base == 2:
				return self.console.ppu.status_register()
			else:
				raise Exception('Unhandled I/O register read at {0:#4x}'.format(self.registers['pc']))

		elif address >= 0x6000 and address < 0x8000:
			return self._memory['SRAM'][address - 0x6000]

		elif address >= 0x8000:
			return self.cartridge.prg_rom[address - 0x8000]

		else:
			raise Exception('Unhandled memory read at {0:#4x}'.format(self.registers['pc']))