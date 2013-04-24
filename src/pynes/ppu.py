import logging
log = logging.getLogger("PyNES")

class Ppu(object):
	def __init__(self, console):
		log.debug('PPU: Initializing PPU...')
		self.console = console
		self.pallete = [
			(0x75, 0x75, 0x75),
			(0x27, 0x1b, 0x8f),
			(0x00, 0x00, 0xab),
			(0x47, 0x00, 0x9f),
			(0x8f, 0x00, 0x77),
			(0xab, 0x00, 0x13),
			(0xa7, 0x00, 0x00),
			(0x7f, 0x0b, 0x00),
			(0x43, 0x2f, 0x00),
			(0x00, 0x47, 0x00),
			(0x00, 0x51, 0x00),
			(0x00, 0x3f, 0x17),
			(0x1b, 0x3f, 0x5f),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0xbc, 0xbc, 0xbc),
			(0x00, 0x73, 0xef),
			(0x23, 0x3b, 0xef),
			(0x83, 0x00, 0xf3),
			(0xbf, 0x00, 0xbf),
			(0xe7, 0x00, 0x5b),
			(0xdb, 0x2b, 0x00),
			(0xcb, 0x4f, 0x0f),
			(0x8b, 0x73, 0x00),
			(0x00, 0x97, 0x00),
			(0x00, 0xab, 0x00),
			(0x00, 0x93, 0x3b),
			(0x00, 0x83, 0x8b),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0xff, 0xff, 0xff),
			(0x3f, 0xbf, 0xff),
			(0x5f, 0x97, 0xff),
			(0xa7, 0x8b, 0xfd),
			(0xf7, 0x7b, 0xff),
			(0xff, 0x77, 0xb7),
			(0xff, 0x77, 0x63),
			(0xff, 0x9b, 0x3b),
			(0xf3, 0xbf, 0x3f),
			(0x83, 0xd3, 0x13),
			(0x4f, 0xdf, 0x4b),
			(0x58, 0xf8, 0x98),
			(0x00, 0xeb, 0xdb),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0xff, 0xff, 0xff),
			(0xab, 0xe7, 0xff),
			(0xc7, 0xd7, 0xff),
			(0xd7, 0xcb, 0xff),
			(0xff, 0xc7, 0xff),
			(0xff, 0xc7, 0xdb),
			(0xff, 0xbf, 0xb3),
			(0xff, 0xdb, 0xab),
			(0xff, 0xe7, 0xa3),
			(0xe3, 0xff, 0xa3),
			(0xab, 0xf3, 0xbf),
			(0xb3, 0xff, 0xcf),
			(0x9f, 0xff, 0xf3),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00),
			(0x00, 0x00, 0x00)
		]

		self.name_table_address = 0x2000
		self.address_increment = 1
		self.sprite_pattern_table = 0x0000
		self.background_pattern_table = 0x0000
		self.sprite_size = 8
		self.NMI = False
		self.color = True
		self.bg_clipping = False
		self.sprite_clipping = False
		self.show_background = False
		self.show_sprites = False
		self.color_intensity = 0
		self.ignore_vram = False 
		self.scanline_sprite_count = 0
		self.sprite_0_hit = False
		self.vblank = False

		self._memory = {}
		self._memory['pattern_tables'] = [0] * 0x2000
		self._memory['name_tables'] = [0] * 0x1000
		self._memory['palettes'] = [0] * 0x20
		self._memory['SPR_RAM'] = [0] * 0xff

		self.spr_ram_addr = 0
		self.vram_addr = 0
		self.vertical_scroll_register = 0
		self.hotizontal_scroll_register = 0
		self.vert_scroll_reg = True 

		self._current_scanline = 0
		self._cycles = 0

	def update_control_1(self, value):
		log.debug('PPU: Updating control register 1 to {0:b}'.format(value))
		self.name_table_address = 0x2000 + (0x400 * (value & 0b11)) # bits 0-1 

		if (value & (1 << 2)):
			self.address_increment = 32
		else:
			self.address_increment = 1

		if (value & (1 << 3)):
			self.sprite_pattern_table = 0x1000
		else:
			self.sprite_pattern_table = 0x0000

		if (value & (1 << 4)):
			self.background_pattern_table = 0x1000
		else:
			self.background_pattern_table = 0x0000

		if (value & (1 << 5)):
			self.sprite_size = 16
		else:
			self.sprite_size = 8

		if (value & (1 << 7)):
			self.NMI = True
		else:
			self.NMI = False
		
	def update_control_2(self, value):
		log.debug('PPU: Updating control register 2 to {0:b}'.format(value))
		self.color = not bool(value & 1)
		self.bg_clipping = bool(value & (1 << 1))
		self.sprite_clipping = bool(value & (1 << 2))
		self.show_background = bool(value & (1 << 3))
		self.show_sprites = bool(value & (1 << 4))

	def status_register(self):
		value = int(self.ignore_vram) << 4
		value += (int(self.scanline_sprite_count > 8) << 5)
		value += (int(self.sprite_0_hit) << 6)
		value += (int(self.vblank) << 7)

		# Clear VBLANK flag and both VRAM address registers.
		self.vblank = False
		self.vram_addr_1 = 0
		self.vram_addr_2 = 0
		return value

	def mem_write(self, address, value):
		base_address = address - 0x2000
		register = address % 8
		if register == 0:
			self.update_control_1(value)
		elif register == 1:
			self.update_control_2(value)
		elif register == 2:
			raise Exception("Write to read-only register at 0x2002")
		elif register == 3:
			self.spr_ram_addr = value
		elif register == 4:
			self._memory['SPR_RAM'][self.spr_ram_addr] = value
		elif register == 5:
			if self.vert_scroll_reg:
				log.debug("Writing {0:#4x} to the VSR.".format(value))
				if (value <= 0xef):
					self.vertical_scroll_register = value
				self.vert_scroll_reg = False
			else:
				log.debug("Writing {0:#4x} to the HSR.".format(value))
				self.horizontal_scroll_register = value
				self.vert_scroll_reg = True
		elif register == 6:
			self.vram_addr_2 = (self.vram_addr_2 << 8) & 0xff00
			self.vram_addr_2 += value
		elif register == 7:
			self.vram_write(self.vram_addr_2, value)
			self.vram_addr_2 += self.address_increment
			


	def vram_write(self, address, value):
		# log.debug('Write to VRAM address {0:#4x}'.format(address))
		if self._cycles < 27425:
			log.warn("Write to VRAM outside of VBLANK. Mid-frame update currently unimplemented.")
		if not self.ignore_vram:
			if address >= 0 and address < 0x2000:
				self._memory['pattern_tables'][address] = value
			elif address >= 0x2000 and address < 0x3000:
				self._memory['name_tables'][address - 0x2000] = value
			elif address >= 0x3000 and address < 0x3f00:
				mirrored_address = address - 0x1000
				self.vram_write(address, value)
			elif address >= 0x3f00 and address < 0x4000:
				address -= 0x3f00
				address %= 20
				self._memory['palettes'][address] = value
			elif address >= 0x4000 and address < 0x10000:
				address -= 0x4000
				address %= 0x4000
				self.vram_write(address, value)
			else:
				raise Exception('Unhandled write to VRAM address {0:#4x}'.format(address))

	def vram_read(self, address):
		if address >= 0 and address < 0x2000:
			return self._memory['pattern_tables'][address]
		elif address >= 0x2000 and address < 0x3000:
			return self._memory['name_tables'][address - 0x2000]
		elif address >= 0x3000 and address < 0x3f00:
			mirrored_address = address - 0x1000
			return self.vram_read(address)
		elif address >= 0x3f00 and address < 0x3f20:
			return self._memory['palettes'][address - 0x3f00]
		elif address >= 0x3f20 and address < 0x4000:
			mirrored_address = address - 0x3f20
			mirrored_address %= 0x20
			return self._memory['palettes'][mirrored_address]
		elif address >= 0x4000 and address < 0x10000:
			address -= 0x4000
			address %= 0x4000
			return self.vram_read(address)
		else:
			raise Exception('Unhandled read from VRAM address {0:#4x}'.format(address))

	def tick(self):
		self._cycles += 1

		if self._cycles == 27425:
			# Enter VBLANK
			self.enter_vblank()
			return True

		if self._cycles == 29691:
			# End of VBLANK, update screen
			self.vblank = False
			self.update_disp()
			self._cycles = 0
		
		return False

	def update_disp(self):
		pass

	def enter_vblank(self):
		log.debug("Entering VBLANK...")
		self.vblank = True

	def get_screen(self):
		return [0] * (256 * 224)
