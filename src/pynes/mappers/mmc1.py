from mappers import Mapper
from utils import Enumerate
import logging

log = logging.getLogger("PyNES")


class MMC1(Mapper):
    mirroring = Enumerate("SINGLE_LOWER SINGLE_UPPER VERTICAL HORIZONTAL")

    def __init__(self, cartridge):
        super().__init__(cartridge)
        self.loaded_pages = [0, cartridge._prg_rom_pages - 1]

        self.register_buffer = 0
        self.write_count = 0

        # Variables controlled by register 1
        self.mirroring = None
        self.vrom_swap_4k = False
        self.swap_low = False
        self.swap_32k = False

        # Variables controlled by register 2
        self.vrom_bank_number_1 = 0
        self.selection_register_0 = 0

        # Register 3
        self.vrom_bank_number_2 = 0
        self.selection_register_1 = 0

        # Register 4
        self.prg_rom_bank_number = 0

    def mem_write(self, address, value):
        if value & (1 << 7):
            self.register_buffer = 0
            self.write_count = 0
            return
        if self.write_count < 5:
            self.register_buffer += ((value & 1) << self.write_count)
            self.write_count += 1
        if self.write_count == 5:
            log.debug('Writing value {0:b} to mapper address {1:#4x}'.format(self.register_buffer, address))
            # Transfer the buffered data to the registers.
            if 0x8000 <= address < 0xa000:
                self.mirroring = self.register_buffer & 0b11
                self.swap_low = bool(self.register_buffer & 0b100)
                self.swap_32k = not bool(self.register_buffer & 0b1000)
                self.vrom_swap_4k = bool(self.register_buffer & 0b10000)

            elif 0xa000 <= address < 0xc000:
                self.vrom_bank_number_1 = self.register_buffer & 0b1111
                self.vrom_selection_register_0 = self.register_buffer >> 5

            elif 0xc000 <= address < 0xe000:
                self.vrom_bank_number_2 = self.register_buffer & 0b1111
                self.vrom_selection_register_1 = self.register_buffer >> 5

            elif 0xe000 <= address < 0x10000:
                bank = self.register_buffer & 0b1111
                if self.swap_32k:
                    self.loaded_pages = [bank * 2, (bank * 2) + 1]
                elif self.swap_low:
                    self.loaded_pages[0] = bank
                else:
                    self.loaded_pages[1] = bank

            # Reset the buffer and write count
            self.register_buffer = 0
            self.write_count = 0
