"""
PyNES - Picture Processing Unit (PPU) emulation
"""

import logging
import multiprocessing
import threading
import numpy as np
import time


log = logging.getLogger("PyNES")


class PPU(threading.Thread):
    class Memory:
        def __init__(self, console):
            self._console = console
            self._ram = [0] * 0xffff

        def write(self, address, value):
            # log.debug("PPU Memory Write to address {0:#06x}".format(address))
            if address < 0 or address > 0xffff:
                raise Exception("Memory write out of bounds: {0x:#4x}".format(address))

            # Pattern Tables
            if address < 0x2000:
                self._ram[address] = np.uint8(value)

            # Name tables are mirrored in 0x3000 - 0x3eff
            elif 0x2000 <= address < 0x3f00:
                t_address = address - 0x2000
                t_address %= 0x1000
                self._ram[t_address + 0x2000] = np.uint8(value)

            # Palettes are mirrored in 0x3f20 - 0x3fff
            elif 0x3f00 <= address < 0x4000:
                t_address = address - 0x3f00
                # Background color is mirrored every 4 bytes.
                if t_address % 4 == 0:
                    t_address = 0
                t_address %= 0x20
                self._ram[t_address + 0x3f00] = np.uint8(value)

            # Mirrors 0x0000 - 0x3fff
            elif address >= 0x4000:
                self.write(address % 0x4000, value)

            else:
                raise Exception("Unhandled memory write to address {0:#4x}".format(address))

        def read(self, address):
            # log.debug("Memory read from address {0:#4x}".format(address))
            if address < 0 or address > 0xffff:
                raise Exception("Memory read out of bounds: {0:#4x}".format(address))

            # Pattern Tables
            if address < 0x2000:
                return np.uint8(self._ram[address])

            # Name Tables (mirrored in 0x3000 - 0x3eff)
            elif 0x2000 <= address < 0x3f00:
                t_address = address - 0x2000
                t_address %= 0x1000
                return np.uint8(self._ram[t_address + 0x2000])

            # Palettes
            elif 0x3f00 <= address < 0x4000:
                t_address = address - 0x3f00
                # Background color is mirrored every 4 bytes
                if t_address % 4 == 0:
                    t_address = 0
                return np.uint8(self._ram[t_address + 0x3f00])

            elif address >= 0x4000:
                return self.read(address % 0x4000)

            else:
                raise Exception("Unhandled memory read at {0:#4x}".format(address))

    def __init__(self, console):
        log.debug('PPU: Initializing PPU...')

        self.memory = PPU.Memory(console)
        self._console = console
        self._palette = [(0x75, 0x75, 0x75),
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
                         (0x00, 0x00, 0x00)]

        self._sprite_ram = [0] * 0x100
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
        self.accept_vram_writes = True
        self.scanline_sprite_count = 0
        self.sprite_0_hit = False
        self.vblank = False  # Used to accurately reset cycle counter
        self._vblank = False  # Status flag, cleared when status is read

        self.spr_ram_addr = multiprocessing.Value('B', 0)
        self.vram_addr = 0
        self.temp_vram_addr = 0
        self.fine_y = 0
        self.fine_x = 0
        self.vert_scroll_reg = True
        self.reg_write_toggle = True

        self.starting_scanline = 0

        super(PPU, self).__init__()

    def update_control_1(self, value):
        log.debug('PPU: Updating control register 1 to {0:b}'.format(value))
        self.temp_vram_addr &= 0xf3ff
        self.temp_vram_addr |= (value & 0x3) << 10

        if value & (1 << 2):
            self.address_increment = 32
        else:
            self.address_increment = 1

        if value & (1 << 3):
            self.sprite_pattern_table = 0x1000
        else:
            self.sprite_pattern_table = 0x0000

        if value & (1 << 4):
            self.background_pattern_table = 0x1000
        else:
            self.background_pattern_table = 0x0000

        if value & (1 << 5):
            self.sprite_size = 16
        else:
            self.sprite_size = 8

        if value & (1 << 7):
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
        value = int(self.accept_vram_writes) << 4
        value |= (int(self.scanline_sprite_count > 8) << 5)
        value |= (int(self.sprite_0_hit) << 6)
        value |= (int(self._vblank) << 7)

        # Clear VBLANK flag and VRAM write toggle.
        self._vblank = False
        self.reg_write_toggle = True

        return value

    def enter_vblank(self):
        log.debug("**** VBLANK ****")

        # If the NMI bit is set, generate an NMI IRQ
        if self.NMI:
            self._console.CPU.IRQ.value = b'N'

        self._vblank = True
        self.vblank = True

    def exit_vblank(self):
        self._vblank = False
        self.vblank = False

    def write_sprram(self, value):
        self._sprite_ram[self.spr_ram_addr] = value
        self.spr_ram_addr += 1

    def read_sprram(self):
        return self._sprite_ram[self.spr_ram_addr]

    def dma_sprram(self, vals):
        if len(vals) != 256:
            log.critical("Invalid DMA write of {0} bytes.".format(len(vals)))
            raise Exception()

        self._sprite_ram = vals

    def reg_write(self, reg, value):
        if reg == 0x2005:
            if self.reg_write_toggle:
                self.temp_vram_addr &= 0xffe0
                self.temp_vram_addr |= (value >> 3)
                self.fine_x = (value & 0x7)
                self.reg_write_toggle = False
            else:
                self.temp_vram_addr &= 0x8c1f
                self.temp_vram_addr |= (value >> 3) << 5
                self.temp_vram_addr |= (value & 0x7) << 13
                self.reg_write_toggle = True

        elif reg == 0x2006:
            if self.reg_write_toggle:
                self.temp_vram_addr = (value & 0x3f) << 8
                self.reg_write_toggle = False
            else:
                self.temp_vram_addr |= (value & 0xff)
                self.vram_addr = self.temp_vram_addr
                self.reg_write_toggle = True

        elif reg == 0x2007:
            self.memory.write(self.vram_addr, value)
            self.vram_addr += self.address_increment


    def generate_frame(self):
        log.debug("PPU: Generating new frame...")
        time.sleep(1)
        # TODO
        pass

    def run(self):
        while True:
            self._console.CPU.EndOfCycle.wait()
            self._console.CPU.EndOfCycle.clear()
            self.starting_scanline = int(self._console.CPU.Cycles.value / 113.33)
            self.generate_frame()

