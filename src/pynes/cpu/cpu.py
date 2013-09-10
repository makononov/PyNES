import multiprocessing
from pynes.cpu.instructions import Instruction

__author__ = 'misha'

from utils import Enumerate
import numpy as np
import threading
import logging


log = logging.getLogger("PyNES")


class CPU(threading.Thread):
    class Memory:
        def __init__(self, console):
            self._console = console
            self._ram = []

        def write(self, address, value):
            if address < 0 or address > 0xffff:
                raise Exception("Memory write out of bounds: {0x:#4x}".format(address))

            # RAM - Mirrored four times, so get the base address before writing.
            if address < 0x2000:
                base_address = address % 0x800
                self._ram[base_address] = np.uint8(value)

            elif 0x2000 <= address < 0x4000:
                self._console.PPU.write(address, value)

            elif 0x4000 <= address < 0x4014 or address == 0x4015:
                # pAPU registers
                log.debug("Unhandled write to pAPU registers")

            elif address == 0x4014:
                log.debug("Unhandled DMS Sprite Transfer")
                # DMA Sprite Transfer

            elif address == 0x4016 or address == 0x4017:
                log.debug("Unhandled write to controller registers")
                # Controller registers

            elif 0x6000 <= address < 0x8000:
                log.debug("Unhandled write to Save RAM")
                # Save RAM

            elif 0x8000 <= address < 0x10000:
                self._console.Cart.mem_write(address, value)

            else:
                raise Exception("Unhandled memory write to address {0:#4x}".format(address))

        def read(self, address):
            if address < 0 or address > 0xffff:
                raise Exception("Memory read out of bounds: {0:#4x}".format(address))

            if address < 0x2000:
                # RAM
                base_address = address % 0x800
                return np.uint8(self._ram[base_address])

            elif 0x2000 <= address < 0x4000:
                # I/O Registers
                address -= 0x2000
                base = address % 8
                if base == 2:
                    return self._console.PPU.status_register()
                else:
                    log.debug("Unhandled I/O register read: {0:#4x}".format(address))

            elif 0x6000 <= address < 0x8000:
                log.debug("Unhandled read from Save RAM")

            elif 0x8000 <= address < 0x10000:
                return self._console.Cart.prg_rom[address - 0x8000]

            else:
                raise Exception("Unhandled memory read at {0:#4x}".format(address))

    class Register:
        def __init__(self, dtype):
            self._dtype = dtype
            self._value = None

        def write(self, value):
            self._value = self._dtype(value)

        def read(self):
            return self._value


    def __init__(self, console):
        self.memory = CPU.Memory(console)
        self.registers = {'pc': CPU.Register(np.uint16), 'a': CPU.Register(np.int8), 'x': CPU.Register(np.uint8),
                          'y': CPU.Register(np.uint8), 'sp': CPU.Register(np.uint8)}
        self._cart = console.Cart
        self.CycleLock = multiprocessing.Lock()
        self.Cycles = multiprocessing.Value("I", 0)
        self.IRQ = multiprocessing.Value("c")
        self.IRQ.value = 'R' # Set reset IRQ

        self._instructionSet = {
            0x00: lambda: Instruction.BRK(self),
            0x65: lambda x: Instruction.ADC(self, Instruction.AddressingMode.ZEROPAGE, x),
        }

        super(CPU, self).__init__()


    def run(self):
        while True:
            # Check IRQs
            if self.IRQ.value is not None:
                # TODO: Push PC to stack
                if self.IRQ.value == 'N': # NMI
                    self.registers['pc'].write(self.memory.read(0xfffb) << 8 + self.memory.read(0xfffa))
                elif self.IRQ.value == 'R': # Reset
                    self.registers['pc'].write((self.memory.read(0xfffd) << 8) + self.memory.read(0xfffc))
                elif self.IRQ.value == 'I' and not self.status.irqdis: # Maskable Interrupt
                    self.registers['pc'].write((self.memory.read(0xffff) << 8) + self.memory.read(0xfffe))

            # Fetch the next instruction, execute it, update PC and cycle counter.
            pc = self.registers['pc'].read()
            increment_pc, increment_cycles = CPU.execute(self._cart['prg_rom'][pc:pc + 4])
            self.registers['pc'].write(pc + increment_pc)
            with self.CycleLock:
                self.Cycles += increment_cycles;
