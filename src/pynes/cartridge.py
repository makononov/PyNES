class Cartridge:
  def __init__(self):
    self._mapper = 0

  def load(self, file):
    with open(file, "rb") as f:
      header = f.read(16)
      self._parse_header(header)

      # Read trainer, if exists
      if (self._flags6 & 0b100):
        self._trainer = f.read(512)

      # Read PRG ROM
      self._prg_rom = f.read(self._prg_rom_size * 0x4000)

      # Read CHR ROM
      self._chr_rom = f.read(self._chr_rom_size * 0x2000)

  def _parse_header(self, header):
    # Verify legal header.
    if (header[0:4] != b"NES\x1a"):
      raise Exception("Invalid file header.")
    
    self._header = header
    self._prg_rom_size = header[4]
    self._chr_rom_size = header[5]
    self._flags6 = header[6]
    self._flags7 = header[7]

    if (self._flags7 & 0b100):
      # NES 2.0 format
      raise Exception("NES 2.0 format not yet implemented.")

    # iNES format
    self._prg_ram_size = header[8]
    self._flags9 = header[9]
    self._flags10 = header[10]

    # Determine mapper ID
    self._mapper = self._flags6 >> 4
    if header[11:15] is b"\x00\x00\x00\x00":
      self._mapper = self._mapper + ((self._flags7 >> 4) << 4)
      
      
