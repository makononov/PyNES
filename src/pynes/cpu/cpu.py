import multiprocessing
from pynes.cpu.instructions import Instruction

__author__ = 'misha'

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

        def set_bit(self, bitnum, set):
            if set:
                self._value |= (1 << bitnum)
            else:
                self._value ^= ~(1 << bitnum)


    def __init__(self, console):
        self.memory = CPU.Memory(console)
        self.registers = {'pc': CPU.Register(np.uint16), 'a': CPU.Register(np.int8), 'x': CPU.Register(np.uint8),
                          'y': CPU.Register(np.uint8), 'sp': CPU.Register(np.uint8), 'p': CPU.Register(np.uint8)}
        self._status_bits = {
            "carry": 0,
            "zero": 1,
            "interrupt": 2,
            "decimal": 3,
            "break": 4,
            "overflow": 6,
            "negative": 7,
            }
        self._cart = console.Cart
        self.CycleLock = multiprocessing.Lock()
        self.Cycles = multiprocessing.Value("I", 0)
        self.IRQ = multiprocessing.Value("c")
        self.IRQ.value = 'R' # Set reset IRQ

        self._opcodes = {
            0x00: Instruction(self, Instruction.BRK, Instruction.AddressingMode.NONE),
            0x01: Instruction(self, Instruction.ORA, Instruction.AddressingMode.INDIRECT_X),
            0x05: Instruction(0x05, "ORA", addressing.ZEROPAGE, 3),
            0x06: Instruction(0x06, "ASL", addressing.ZEROPAGE, 3),
            0x08: Instruction(0x08, "PHP", addressing.NONE, 3),
            0x09: Instruction(0x09, "ORA", addressing.IMMEDIATE, 2),
            0x0a: Instruction(0x0a, "ASL", addressing.ACCUMULATOR, 2),
            0x0d: Instruction(0x0d, "ORA", addressing.ABSOLUTE, 4),
            0x0e: Instruction(0x0e, "ASL", addressing.ABSOLUTE, 6),
            0x10: Instruction(0x10, "BPL", addressing.RELATIVE, 2),
            0x11: Instruction(0x11, "ORA", addressing.INDIRECT_Y, 5),
            0x15: Instruction(0x15, "ORA", addressing.ZEROPAGE_X, 4),
            0x16: Instruction(0x16, "ASL", addressing.ZEROPAGE_X, 6),
            0x18: Instruction(0x18, "CLC", addressing.NONE, 2),
            0x19: Instruction(0x19, "ORA", addressing.ABSOLUTE_Y, 4),
            0x1d: Instruction(0x1d, "ORA", addressing.ABSOLUTE_X, 4),
            0x1e: Instruction(0x1e, "ASL", addressing.ABSOLUTE_X, 7),

            0x20: Instruction(0x20, "JSR", addressing.ABSOLUTE, 6),
            0x21: Instruction(0x21, "AND", addressing.INDIRECT_X, 6),
            0x24: Instruction(0x24, "BIT", addressing.ZEROPAGE, 3),
            0x25: Instruction(0x25, "AND", addressing.ZEROPAGE, 3),
            0x26: Instruction(0x26, "ROL", addressing.ZEROPAGE, 5),
            0x28: Instruction(0x28, "PLP", addressing.NONE, 4),
            0x29: Instruction(0x29, "AND", addressing.IMMEDIATE, 2),
            0x2a: Instruction(0x2a, "ROL", addressing.ACCUMULATOR, 2),
            0x2c: Instruction(0x2c, "BIT", addressing.ABSOLUTE, 4),
            0x2d: Instruction(0x2d, "AND", addressing.ABSOLUTE, 4),
            0x2e: Instruction(0x2e, "ROL", addressing.ABSOLUTE, 6),
            0x30: Instruction(0x30, "BMI", addressing.RELATIVE, 2),
            0x31: Instruction(0x31, "AND", addressing.INDIRECT_Y, 5),
            0x35: Instruction(0x35, "AND", addressing.ZEROPAGE_X, 6),
            0x36: Instruction(0x36, "ROL", addressing.ZEROPAGE_X, 6),
            0x38: Instruction(0x38, "SEC", addressing.NONE, 2),
            0x39: Instruction(0x39, "AND", addressing.ABSOLUTE_Y, 4),
            0x3d: Instruction(0x3d, "AND", addressing.ABSOLUTE_X, 4),
            0x3e: Instruction(0x3e, "ROL", addressing.ABSOLUTE_X, 7),

            0x40: Instruction(0x40, "RTI", addressing.NONE, 6),
            0x41: Instruction(0x41, "EOR", addressing.INDIRECT_X, 6),
            0x45: Instruction(0x45, "EOR", addressing.ZEROPAGE, 2),
            0x46: Instruction(0x46, "LSR", addressing.ZEROPAGE, 5),
            0x48: Instruction(0x48, "PHA", addressing.NONE, 3),
            0x49: Instruction(0x49, "EOR", addressing.IMMEDIATE, 2),
            0x4a: Instruction(0x4a, "LSR", addressing.ACCUMULATOR, 2),
            0x4c: Instruction(0x4c, "JMP", addressing.ABSOLUTE, 3),
            0x4d: Instruction(0x4d, "EOR", addressing.ABSOLUTE, 4),
            0x4e: Instruction(0x4e, "LSR", addressing.ABSOLUTE, 6),
            0x50: Instruction(0x50, "BVC", addressing.RELATIVE, 2),
            0x51: Instruction(0x51, "EOR", addressing.INDIRECT_Y, 5),
            0x55: Instruction(0x55, "EOR", addressing.ZEROPAGE_X, 4),
            0x56: Instruction(0x56, "LSR", addressing.ZEROPAGE_X, 6),
            0x58: Instruction(0x58, "CLI", addressing.NONE, 2),
            0x59: Instruction(0x59, "EOR", addressing.ABSOLUTE_Y, 4),
            0x5d: Instruction(0x5d, "EOR", addressing.ABSOLUTE_X, 4),
            0x5e: Instruction(0x5e, "LSR", addressing.ABSOLUTE_X, 7),

            0x60: Instruction(0x60, "RTS", addressing.NONE, 6),
            0x61: Instruction(0x61, "ADC", addressing.INDIRECT_X, 6),
            0x65: Instruction(0x65, "ADC", addressing.ZEROPAGE, 3),
            0x66: Instruction(0x66, "ROR", addressing.ZEROPAGE, 5),
            0x68: Instruction(0x68, "PLA", addressing.NONE, 4),
            0x69: Instruction(0x69, "ADC", addressing.IMMEDIATE, 2),
            0x6a: Instruction(0x6a, "ROR", addressing.ACCUMULATOR, 2),
            0x6c: Instruction(0x6c, "JMP", addressing.INDIRECT, 5),
            0x6d: Instruction(0x6d, "ADC", addressing.ABSOLUTE, 4),
            0x6e: Instruction(0x6e, "ROR", addressing.ABSOLUTE, 6),
            0x70: Instruction(0x70, "BVS", addressing.RELATIVE, 2),
            0x71: Instruction(0x71, "ADC", addressing.INDIRECT_Y, 5),
            0x75: Instruction(0x75, "ADC", addressing.ZEROPAGE_X, 4),
            0x76: Instruction(0x76, "ROR", addressing.ZEROPAGE_X, 6),
            0x78: Instruction(0x78, "SEI", addressing.NONE, 2),
            0x79: Instruction(0x79, "ADC", addressing.ABSOLUTE_Y, 4),
            0x7d: Instruction(0x7d, "ADC", addressing.ABSOLUTE_X, 4),
            0x7e: Instruction(0x7e, "ROR", addressing.ABSOLUTE_X, 7),

            0x81: Instruction(0x81, "STA", addressing.INDIRECT_X, 6),
            0x84: Instruction(0x84, "STY", addressing.ZEROPAGE, 3),
            0x85: Instruction(0x85, "STA", addressing.ZEROPAGE, 3),
            0x86: Instruction(0x86, "STX", addressing.ZEROPAGE, 3),
            0x88: Instruction(0x88, "DEY", addressing.NONE, 2),
            0x8a: Instruction(0x8a, "TXA", addressing.NONE, 2),
            0x8c: Instruction(0x8c, "STY", addressing.ABSOLUTE, 4),
            0x8d: Instruction(0x8d, "STA", addressing.ABSOLUTE, 4),
            0x8e: Instruction(0x8e, "STX", addressing.ABSOLUTE, 4),
            0x90: Instruction(0x90, "BCC", addressing.RELATIVE, 2),
            0x91: Instruction(0x91, "STA", addressing.INDIRECT_Y, 6),
            0x94: Instruction(0x94, "STY", addressing.ZEROPAGE_X, 4),
            0x95: Instruction(0x95, "STA", addressing.ZEROPAGE_X, 4),
            0x96: Instruction(0x96, "STX", addressing.ZEROPAGE_Y, 4),
            0x98: Instruction(0x98, "TYA", addressing.NONE, 2),
            0x99: Instruction(0x99, "STA", addressing.ABSOLUTE_Y, 5),
            0x9a: Instruction(0x9a, "TXS", addressing.NONE, 2),
            0x9d: Instruction(0x9d, "STA", addressing.ABSOLUTE_X, 5),

            0xa0: Instruction(0xa0, "LDY", addressing.IMMEDIATE, 2),
            0xa1: Instruction(0xa1, "LDA", addressing.INDIRECT_X, 6),
            0xa2: Instruction(0xa2, "LDX", addressing.IMMEDIATE, 2),
            0xa4: Instruction(0xa4, "LDY", addressing.ZEROPAGE, 3),
            0xa5: Instruction(0xa5, "LDA", addressing.ZEROPAGE, 3),
            0xa6: Instruction(0xa6, "LDX", addressing.ZEROPAGE, 3),
            0xa8: Instruction(0xa8, "TAY", addressing.NONE, 2),
            0xa9: Instruction(0xa9, "LDA", addressing.IMMEDIATE, 2),
            0xaa: Instruction(0xaa, "TAX", addressing.NONE, 2),
            0xac: Instruction(0xac, "LDY", addressing.ABSOLUTE, 4),
            0xad: Instruction(0xad, "LDA", addressing.ABSOLUTE, 4),
            0xae: Instruction(0xae, "LDX", addressing.ABSOLUTE, 4),
            0xb0: Instruction(0xb0, "BCS", addressing.RELATIVE, 2),
            0xb1: Instruction(0xb1, "LDA", addressing.INDIRECT_Y, 5),
            0xb4: Instruction(0xb4, "LDY", addressing.ZEROPAGE_X, 4),
            0xb5: Instruction(0xb5, "LDA", addressing.ZEROPAGE_X, 4),
            0xb6: Instruction(0xb6, "LDX", addressing.ZEROPAGE_Y, 4),
            0xb8: Instruction(0xb8, "CLV", addressing.NONE, 2),
            0xb9: Instruction(0xb9, "LDA", addressing.ABSOLUTE_Y, 4),
            0xba: Instruction(0xba, "TSX", addressing.NONE, 2),
            0xbc: Instruction(0xbc, "LDY", addressing.ABSOLUTE_X, 4),
            0xbd: Instruction(0xbd, "LDA", addressing.ABSOLUTE_X, 4),
            0xbe: Instruction(0xbe, "LDX", addressing.ABSOLUTE_Y, 4),

            0xc0: Instruction(0xc0, "CPY", addressing.IMMEDIATE, 2),
            0xc1: Instruction(0xc1, "CMP", addressing.INDIRECT_X, 6),
            0xc4: Instruction(0xc4, "CPY", addressing.ZEROPAGE, 3),
            0xc5: Instruction(0xc5, "CMP", addressing.ZEROPAGE, 3),
            0xc6: Instruction(0xc6, "DEC", addressing.ZEROPAGE, 5),
            0xc8: Instruction(0xc8, "INY", addressing.NONE, 2),
            0xc9: Instruction(0xc9, "CMP", addressing.IMMEDIATE, 2),
            0xca: Instruction(0xca, "DEX", addressing.NONE, 2),
            0xcc: Instruction(0xcc, "CPY", addressing.ABSOLUTE, 4),
            0xcd: Instruction(0xcd, "CMP", addressing.ABSOLUTE, 4),
            0xce: Instruction(0xce, "DEC", addressing.ABSOLUTE, 6),
            0xd0: Instruction(0xd0, "BNE", addressing.RELATIVE, 2),
            0xd1: Instruction(0xd1, "CMP", addressing.INDIRECT_Y, 5),
            0xd5: Instruction(0xd5, "CMP", addressing.ZEROPAGE_X, 4),
            0xd6: Instruction(0xd6, "DEC", addressing.ZEROPAGE_X, 6),
            0xd8: Instruction(0xd8, "CLD", addressing.NONE, 2),
            0xd9: Instruction(0xd9, "CMP", addressing.ABSOLUTE_Y, 4),
            0xdd: Instruction(0xdd, "CMP", addressing.ABSOLUTE_X, 4),
            0xde: Instruction(0xde, "DEC", addressing.ABSOLUTE_X, 7),

            0xe0: Instruction(0xe0, "CPX", addressing.IMMEDIATE, 2),
            0xe1: Instruction(0xe1, "SBC", addressing.INDIRECT_X, 6),
            0xe4: Instruction(0xe4, "CPX", addressing.ZEROPAGE, 3),
            0xe5: Instruction(0xe5, "SBC", addressing.ZEROPAGE, 3),
            0xe6: Instruction(0xe6, "INC", addressing.ZEROPAGE, 5),
            0xe8: Instruction(0xe8, "INX", addressing.NONE, 2),
            0xe9: Instruction(0xe9, "SBC", addressing.IMMEDIATE, 2),
            0xea: Instruction(0xea, "NOP", addressing.NONE, 2),
            0xec: Instruction(0xec, "CPX", addressing.ABSOLUTE, 4),
            0xed: Instruction(0xed, "SBC", addressing.ABSOLUTE, 4),
            0xee: Instruction(0xee, "INC", addressing.ABSOLUTE, 6),
            0xf0: Instruction(0xf0, "BEQ", addressing.RELATIVE, 2),
            0xf1: Instruction(0xf1, "SBC", addressing.INDIRECT_Y, 5),
            0xf5: Instruction(0xf5, "SBC", addressing.ZEROPAGE_X, 4),
            0xf6: Instruction(0xf6, "INC", addressing.ZEROPAGE_X, 6),
            0xf8: Instruction(0xf8, "SED", addressing.NONE, 2),
            0xf9: Instruction(0xf9, "SBC", addressing.ABSOLUTE_Y, 4),
            0xfd: Instruction(0xfd, "SBC", addressing.ABSOLUTE_X, 4),
            0xfe: Instruction(0xfe, "INC", addressing.ABSOLUTE_X, 7)
        }

        super(CPU, self).__init__()


    def set_status(self, status, value):
        p = self.registers['p'].read()

        if status == "zero":
            self.registers['p'].set_bit(1, value == 0)
        elif status == "negative":
            self.registers['p'].set_bit(7, value < 0)
        else:
            self.registers['p'].set_bit(self._status_bits[status], value)


    def get_status(self, status):
        bitnum = self._status_bits[status]
        return bool(self.registers['p'].read() & (1 << bitnum))


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
