from mappers import Mapper

class MMC1(Mapper):
  def load_prg(self, prg_rom):
    # Load page 0 into lower bank
    prg_rom[0] = self._cart._prg_rom[0:0x4000]

    # Load last page into upper bank
    prg_rom[1] = self._cart._prg_rom[self._cart._prg_rom_size - 0x4000:self._cart._prg_rom_size]

