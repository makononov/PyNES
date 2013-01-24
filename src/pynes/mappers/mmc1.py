from mappers import Mapper

class MMC1(Mapper):
  def __init__(self, cartridge):
    self._cart = cartridge
    self.register_buffer = 0
    self.write_count = 0

    # Variables controlled by register 1
    self.vertical_mirroring = False
    self.single_screen_mirroring = False
    self.swap_location = 0xc000
    self.swap_16k = False
    self.vrom_swap_4k = False

    # Variables controlled by register 2
    self.vrom_bank_number_1 = 0
    self.selection_register_0 = 0

    # Register 3
    self.vrom_bank_number_2 = 0
    self.selection_register_1 = 0

    # Register 4
    self.prg_rom_bank_number = 0


  def load_prg(self, prg_rom):
    # Load page 0 into lower bank
    prg_rom[0] = self._cart._prg_rom[0:0x4000]

    # Load last page into upper bank
    prg_rom[1] = self._cart._prg_rom[self._cart._prg_rom_size - 0x4000:self._cart._prg_rom_size]

  def mem_write(self, address, value):
    if (value & (1 << 7)):
      self.register_buffer = 0
      self.write_count = 0
    if self.write_count < 5:
      self.register_buffer += ((value & 1) << self.write_count)
      self.write_count += 1
    if self.write_count == 5:
      # Transfer the buffered data to the registers.
      if address >= 0x8000 and address < 0xa000:
        self.vertical_mirroring = bool(self.register_buffer & 0b1)
        self.single_screen_mirroring = bool(self.register_buffer & 0b10)
        if self.register_buffer & 0b100:
          self.swap_location = 0x8000
        else:
          self.swap_location = 0xc000
        self.swap_16k = bool(self.register_buffer & 0b1000)
        self.vrom_swap_4k = bool(self.register_buffer & 0b10000)
      elif address >= 0xa000 and address < 0xc000:
        self.vrom_bank_number_1 = self.register_buffer & 0b1111
        self.vrom_selection_register_0 = self.register_buffer >> 5
      elif address >= 0xc000 and address < 0xe000:
        self.vrom_bank_number_2 = self.register_buffer & 0b1111
        self.vrom_selection_register_1 = self.register_buffer >> 5
      elif address >= 0xe000 and address < 0x10000:
        self.prg_rom_bank_number = self.register_buffer & 0b1111





