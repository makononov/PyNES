from mappers import *
import numpy as np

class Cartridge:
  def __init__(self, filename = None):
    if filename is not None:
      self.load(filename)
    self.cpu = None
    self._mapper_id = 0

  def __getattr__(self, name):
    if name == "prg_rom":
      pages = self.mapper.loaded_pages
      return self._prg_rom[pages[0] * 0x4000:(pages[0] + 1) * 0x4000] + self._prg_rom[pages[1] * 0x4000:(pages[1] + 1) * 0x4000]

  def load(self, file):
    with open(file, "rb") as f:
      header = f.read(16)
      self._parse_header(header)

      # Read trainer, if exists
      if (self._flags6 & 0b100):
        self._trainer = f.read(512)

      # Read PRG ROM
      self._prg_rom = f.read(self._prg_rom_pages * 0x4000)

      # Read CHR ROM
      self._chr_rom = f.read(self._chr_rom_pages * 0x2000)

  def _parse_header(self, header):
    # Verify legal header.
    if (header[0:4] != b"NES\x1a"):
      raise Exception("Invalid file header.")
    
    self._header = header
    self._prg_rom_pages = header[4]
    self._chr_rom_pages = header[5]
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
    self._mapper_id = self._flags6 >> 4
    if header[11:15] is b"\x00\x00\x00\x00":
      self._mapper_id = self._mapper_id + ((self._flags7 >> 4) << 4)
    self.load_mapper()

  def read_prg(self, pc, bytes):
    return self._prg_rom[pc:pc+bytes]

  def load_mapper(self):
    if self._mapper_id == 1:
      self.mapper = MMC1(self)
