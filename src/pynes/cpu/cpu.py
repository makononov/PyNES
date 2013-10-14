import multiprocessing
from cpu import instructions
from cpu import AddressingMode

__author__ = 'misha'

import numpy as np
import threading
import logging


log = logging.getLogger("PyNES")


class CPU(threading.Thread):
    class Memory:
        def __init__(self, console):
            self._console = console
            self._ram = [0] * 0xffff

        def write(self, address, value):
            # log.debug("Memory write to address {0:#4x}".format(address))
            if address < 0 or address > 0xffff:
                raise Exception("Memory write out of bounds: {0x:#4x}".format(address))

            # RAM - Mirrored four times, so get the base address before writing.
            if address < 0x2000:
                base_address = address % 0x800
                self._ram[base_address] = np.uint8(value)

            elif 0x2000 <= address < 0x4000:
                 # PPU Registers
                address -= 0x2000
                base = address % 8
                if base == 0:
                    self._console.PPU.update_control_1(value)
                elif base == 1:
                    self._console.PPU.update_control_2(value)
                else:
                    log.debug("Unhandled I/O register read: {0:#4x}".format(address))

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
            # log.debug("Memory read from address {0:#4x}".format(address))
            if address < 0 or address > 0xffff:
                raise Exception("Memory read out of bounds: {0:#4x}".format(address))

            if address < 0x2000:
                # RAM
                base_address = address % 0x800
                return np.uint8(self._ram[base_address])

            elif 0x2000 <= address < 0x4000:
                # PPU Registers
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
            self._value = 0xff

        def write(self, value):
            self._value = self._dtype(value)

        def read(self):
            return self._dtype(self._value)

        def set_bit(self, bitnum, isset):
            if isset:
                self._value |= (1 << bitnum)
            else:
                self._value &= ~(1 << bitnum)

        def increment(self, value=1):
            self._value = self._dtype(value + self._value)

    class Instruction:
        def __init__(self, cpu, fn, addressing, base_cycles):
            self._cpu = cpu
            self._fn = fn
            self._admode = addressing
            self._cycles = base_cycles

        def __call__(self, mem):
            param = 0
            for i in range(0, self._admode.size):
                param += mem[i] << (8 * i)
            value, adcycles = self._admode.read(self._cpu, param)
            # log.debug("{2:#06x}: {0} {1}(cycles: {3})".format(self._fn.__name__, self._admode.print(param), self._cpu.registers['pc'].read(), self._cpu.Cycles.value))
            self._cpu.registers['pc'].increment(value=1 + self._admode.size)
            fn_value, fncycles = self._fn(self._cpu, value)
            if fn_value is not None:
                self._admode.write(self._cpu, param, fn_value)

            return self._cycles + adcycles + fncycles

    def __init__(self, console):
        self._console = console
        self.memory = CPU.Memory(console)
        self.registers = {'pc': CPU.Register(np.uint16), 'a': CPU.Register(np.int8), 'x': CPU.Register(np.uint8),
                          'y': CPU.Register(np.uint8), 'sp': CPU.Register(np.uint8), 'p': CPU.Register(np.uint8)}
        self.registers['p'].write(0b00100000)
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
        self.IRQ.value = b'R'  # Set reset IRQ

        self._opcodes = {
            0x00: CPU.Instruction(self, instructions.BRK, AddressingMode.NONE, 7),
            0x01: CPU.Instruction(self, instructions.ORA, AddressingMode.INDIRECT_X, 6),
            0x05: CPU.Instruction(self, instructions.ORA, AddressingMode.ZEROPAGE, 3),
            0x06: CPU.Instruction(self, instructions.ASL, AddressingMode.ZEROPAGE, 3),
            0x08: CPU.Instruction(self, instructions.PHP, AddressingMode.NONE, 3),
            0x09: CPU.Instruction(self, instructions.ORA, AddressingMode.IMMEDIATE, 2),
            0x0a: CPU.Instruction(self, instructions.ASL, AddressingMode.ACCUMULATOR, 2),
            0x0d: CPU.Instruction(self, instructions.ORA, AddressingMode.ABSOLUTE, 4),
            0x0e: CPU.Instruction(self, instructions.ASL, AddressingMode.ABSOLUTE, 6),
            0x10: CPU.Instruction(self, instructions.BPL, AddressingMode.RELATIVE, 2),
            0x11: CPU.Instruction(self, instructions.ORA, AddressingMode.INDIRECT_Y, 5),
            0x15: CPU.Instruction(self, instructions.ORA, AddressingMode.ZEROPAGE_X, 4),
            0x16: CPU.Instruction(self, instructions.ASL, AddressingMode.ZEROPAGE_X, 6),
            0x18: CPU.Instruction(self, instructions.CLC, AddressingMode.NONE, 2),
            0x19: CPU.Instruction(self, instructions.ORA, AddressingMode.ABSOLUTE_Y, 4),
            0x1d: CPU.Instruction(self, instructions.ORA, AddressingMode.ABSOLUTE_X, 4),
            0x1e: CPU.Instruction(self, instructions.ASL, AddressingMode.ABSOLUTE_X, 7),

            0x20: CPU.Instruction(self, instructions.JSR, AddressingMode.ABSOLUTE, 6),
            0x21: CPU.Instruction(self, instructions.AND, AddressingMode.INDIRECT_X, 6),
            0x24: CPU.Instruction(self, instructions.BIT, AddressingMode.ZEROPAGE, 3),
            0x25: CPU.Instruction(self, instructions.AND, AddressingMode.ZEROPAGE, 3),
            0x26: CPU.Instruction(self, instructions.ROL, AddressingMode.ZEROPAGE, 5),
            0x28: CPU.Instruction(self, instructions.PLP, AddressingMode.NONE, 4),
            0x29: CPU.Instruction(self, instructions.AND, AddressingMode.IMMEDIATE, 2),
            0x2a: CPU.Instruction(self, instructions.ROL, AddressingMode.ACCUMULATOR, 2),
            0x2c: CPU.Instruction(self, instructions.BIT, AddressingMode.ABSOLUTE, 4),
            0x2d: CPU.Instruction(self, instructions.AND, AddressingMode.ABSOLUTE, 4),
            0x2e: CPU.Instruction(self, instructions.ROL, AddressingMode.ABSOLUTE, 6),
            0x30: CPU.Instruction(self, instructions.BMI, AddressingMode.RELATIVE, 2),
            0x31: CPU.Instruction(self, instructions.AND, AddressingMode.INDIRECT_Y, 5),
            0x35: CPU.Instruction(self, instructions.AND, AddressingMode.ZEROPAGE_X, 6),
            0x36: CPU.Instruction(self, instructions.ROL, AddressingMode.ZEROPAGE_X, 6),
            0x38: CPU.Instruction(self, instructions.SEC, AddressingMode.NONE, 2),
            0x39: CPU.Instruction(self, instructions.AND, AddressingMode.ABSOLUTE_Y, 4),
            0x3d: CPU.Instruction(self, instructions.AND, AddressingMode.ABSOLUTE_X, 4),
            0x3e: CPU.Instruction(self, instructions.ROL, AddressingMode.ABSOLUTE_X, 7),

            0x40: CPU.Instruction(self, instructions.RTI, AddressingMode.NONE, 6),
            0x41: CPU.Instruction(self, instructions.EOR, AddressingMode.INDIRECT_X, 6),
            0x45: CPU.Instruction(self, instructions.EOR, AddressingMode.ZEROPAGE, 2),
            0x46: CPU.Instruction(self, instructions.LSR, AddressingMode.ZEROPAGE, 5),
            0x48: CPU.Instruction(self, instructions.PHA, AddressingMode.NONE, 3),
            0x49: CPU.Instruction(self, instructions.EOR, AddressingMode.IMMEDIATE, 2),
            0x4a: CPU.Instruction(self, instructions.LSR, AddressingMode.ACCUMULATOR, 2),
            0x4c: CPU.Instruction(self, instructions.JMP, AddressingMode.ABSOLUTE, 3),
            0x4d: CPU.Instruction(self, instructions.EOR, AddressingMode.ABSOLUTE, 4),
            0x4e: CPU.Instruction(self, instructions.LSR, AddressingMode.ABSOLUTE, 6),
            0x50: CPU.Instruction(self, instructions.BVC, AddressingMode.RELATIVE, 2),
            0x51: CPU.Instruction(self, instructions.EOR, AddressingMode.INDIRECT_Y, 5),
            0x55: CPU.Instruction(self, instructions.EOR, AddressingMode.ZEROPAGE_X, 4),
            0x56: CPU.Instruction(self, instructions.LSR, AddressingMode.ZEROPAGE_X, 6),
            0x58: CPU.Instruction(self, instructions.CLI, AddressingMode.NONE, 2),
            0x59: CPU.Instruction(self, instructions.EOR, AddressingMode.ABSOLUTE_Y, 4),
            0x5d: CPU.Instruction(self, instructions.EOR, AddressingMode.ABSOLUTE_X, 4),
            0x5e: CPU.Instruction(self, instructions.LSR, AddressingMode.ABSOLUTE_X, 7),

            0x60: CPU.Instruction(self, instructions.RTS, AddressingMode.NONE, 6),
            0x61: CPU.Instruction(self, instructions.ADC, AddressingMode.INDIRECT_X, 6),
            0x65: CPU.Instruction(self, instructions.ADC, AddressingMode.ZEROPAGE, 3),
            0x66: CPU.Instruction(self, instructions.ROR, AddressingMode.ZEROPAGE, 5),
            0x68: CPU.Instruction(self, instructions.PLA, AddressingMode.NONE, 4),
            0x69: CPU.Instruction(self, instructions.ADC, AddressingMode.IMMEDIATE, 2),
            0x6a: CPU.Instruction(self, instructions.ROR, AddressingMode.ACCUMULATOR, 2),
            0x6c: CPU.Instruction(self, instructions.JMP, AddressingMode.INDIRECT, 5),
            0x6d: CPU.Instruction(self, instructions.ADC, AddressingMode.ABSOLUTE, 4),
            0x6e: CPU.Instruction(self, instructions.ROR, AddressingMode.ABSOLUTE, 6),
            0x70: CPU.Instruction(self, instructions.BVS, AddressingMode.RELATIVE, 2),
            0x71: CPU.Instruction(self, instructions.ADC, AddressingMode.INDIRECT_Y, 5),
            0x75: CPU.Instruction(self, instructions.ADC, AddressingMode.ZEROPAGE_X, 4),
            0x76: CPU.Instruction(self, instructions.ROR, AddressingMode.ZEROPAGE_X, 6),
            0x78: CPU.Instruction(self, instructions.SEI, AddressingMode.NONE, 2),
            0x79: CPU.Instruction(self, instructions.ADC, AddressingMode.ABSOLUTE_Y, 4),
            0x7d: CPU.Instruction(self, instructions.ADC, AddressingMode.ABSOLUTE_X, 4),
            0x7e: CPU.Instruction(self, instructions.ROR, AddressingMode.ABSOLUTE_X, 7),

            0x81: CPU.Instruction(self, instructions.STA, AddressingMode.INDIRECT_X, 6),
            0x84: CPU.Instruction(self, instructions.STY, AddressingMode.ZEROPAGE, 3),
            0x85: CPU.Instruction(self, instructions.STA, AddressingMode.ZEROPAGE, 3),
            0x86: CPU.Instruction(self, instructions.STX, AddressingMode.ZEROPAGE, 3),
            0x88: CPU.Instruction(self, instructions.DEY, AddressingMode.NONE, 2),
            0x8a: CPU.Instruction(self, instructions.TXA, AddressingMode.NONE, 2),
            0x8c: CPU.Instruction(self, instructions.STY, AddressingMode.ABSOLUTE, 4),
            0x8d: CPU.Instruction(self, instructions.STA, AddressingMode.ABSOLUTE, 4),
            0x8e: CPU.Instruction(self, instructions.STX, AddressingMode.ABSOLUTE, 4),
            0x90: CPU.Instruction(self, instructions.BCC, AddressingMode.RELATIVE, 2),
            0x91: CPU.Instruction(self, instructions.STA, AddressingMode.INDIRECT_Y, 6),
            0x94: CPU.Instruction(self, instructions.STY, AddressingMode.ZEROPAGE_X, 4),
            0x95: CPU.Instruction(self, instructions.STA, AddressingMode.ZEROPAGE_X, 4),
            0x96: CPU.Instruction(self, instructions.STX, AddressingMode.ZEROPAGE_Y, 4),
            0x98: CPU.Instruction(self, instructions.TYA, AddressingMode.NONE, 2),
            0x99: CPU.Instruction(self, instructions.STA, AddressingMode.ABSOLUTE_Y, 5),
            0x9a: CPU.Instruction(self, instructions.TXS, AddressingMode.NONE, 2),
            0x9d: CPU.Instruction(self, instructions.STA, AddressingMode.ABSOLUTE_X, 5),

            0xa0: CPU.Instruction(self, instructions.LDY, AddressingMode.IMMEDIATE, 2),
            0xa1: CPU.Instruction(self, instructions.LDA, AddressingMode.INDIRECT_X, 6),
            0xa2: CPU.Instruction(self, instructions.LDX, AddressingMode.IMMEDIATE, 2),
            0xa4: CPU.Instruction(self, instructions.LDY, AddressingMode.ZEROPAGE, 3),
            0xa5: CPU.Instruction(self, instructions.LDA, AddressingMode.ZEROPAGE, 3),
            0xa6: CPU.Instruction(self, instructions.LDX, AddressingMode.ZEROPAGE, 3),
            0xa8: CPU.Instruction(self, instructions.TAY, AddressingMode.NONE, 2),
            0xa9: CPU.Instruction(self, instructions.LDA, AddressingMode.IMMEDIATE, 2),
            0xaa: CPU.Instruction(self, instructions.TAX, AddressingMode.NONE, 2),
            0xac: CPU.Instruction(self, instructions.LDY, AddressingMode.ABSOLUTE, 4),
            0xad: CPU.Instruction(self, instructions.LDA, AddressingMode.ABSOLUTE, 4),
            0xae: CPU.Instruction(self, instructions.LDX, AddressingMode.ABSOLUTE, 4),
            0xb0: CPU.Instruction(self, instructions.BCS, AddressingMode.RELATIVE, 2),
            0xb1: CPU.Instruction(self, instructions.LDA, AddressingMode.INDIRECT_Y, 5),
            0xb4: CPU.Instruction(self, instructions.LDY, AddressingMode.ZEROPAGE_X, 4),
            0xb5: CPU.Instruction(self, instructions.LDA, AddressingMode.ZEROPAGE_X, 4),
            0xb6: CPU.Instruction(self, instructions.LDX, AddressingMode.ZEROPAGE_Y, 4),
            0xb8: CPU.Instruction(self, instructions.CLV, AddressingMode.NONE, 2),
            0xb9: CPU.Instruction(self, instructions.LDA, AddressingMode.ABSOLUTE_Y, 4),
            0xba: CPU.Instruction(self, instructions.TSX, AddressingMode.NONE, 2),
            0xbc: CPU.Instruction(self, instructions.LDY, AddressingMode.ABSOLUTE_X, 4),
            0xbd: CPU.Instruction(self, instructions.LDA, AddressingMode.ABSOLUTE_X, 4),
            0xbe: CPU.Instruction(self, instructions.LDX, AddressingMode.ABSOLUTE_Y, 4),

            0xc0: CPU.Instruction(self, instructions.CPY, AddressingMode.IMMEDIATE, 2),
            0xc1: CPU.Instruction(self, instructions.CMP, AddressingMode.INDIRECT_X, 6),
            0xc4: CPU.Instruction(self, instructions.CPY, AddressingMode.ZEROPAGE, 3),
            0xc5: CPU.Instruction(self, instructions.CMP, AddressingMode.ZEROPAGE, 3),
            0xc6: CPU.Instruction(self, instructions.DEC, AddressingMode.ZEROPAGE, 5),
            0xc8: CPU.Instruction(self, instructions.INY, AddressingMode.NONE, 2),
            0xc9: CPU.Instruction(self, instructions.CMP, AddressingMode.IMMEDIATE, 2),
            0xca: CPU.Instruction(self, instructions.DEX, AddressingMode.NONE, 2),
            0xcc: CPU.Instruction(self, instructions.CPY, AddressingMode.ABSOLUTE, 4),
            0xcd: CPU.Instruction(self, instructions.CMP, AddressingMode.ABSOLUTE, 4),
            0xce: CPU.Instruction(self, instructions.DEC, AddressingMode.ABSOLUTE, 6),
            0xd0: CPU.Instruction(self, instructions.BNE, AddressingMode.RELATIVE, 2),
            0xd1: CPU.Instruction(self, instructions.CMP, AddressingMode.INDIRECT_Y, 5),
            0xd5: CPU.Instruction(self, instructions.CMP, AddressingMode.ZEROPAGE_X, 4),
            0xd6: CPU.Instruction(self, instructions.DEC, AddressingMode.ZEROPAGE_X, 6),
            0xd8: CPU.Instruction(self, instructions.CLD, AddressingMode.NONE, 2),
            0xd9: CPU.Instruction(self, instructions.CMP, AddressingMode.ABSOLUTE_Y, 4),
            0xdd: CPU.Instruction(self, instructions.CMP, AddressingMode.ABSOLUTE_X, 4),
            0xde: CPU.Instruction(self, instructions.DEC, AddressingMode.ABSOLUTE_X, 7),

            0xe0: CPU.Instruction(self, instructions.CPX, AddressingMode.IMMEDIATE, 2),
            0xe1: CPU.Instruction(self, instructions.SBC, AddressingMode.INDIRECT_X, 6),
            0xe4: CPU.Instruction(self, instructions.CPX, AddressingMode.ZEROPAGE, 3),
            0xe5: CPU.Instruction(self, instructions.SBC, AddressingMode.ZEROPAGE, 3),
            0xe6: CPU.Instruction(self, instructions.INC, AddressingMode.ZEROPAGE, 5),
            0xe8: CPU.Instruction(self, instructions.INX, AddressingMode.NONE, 2),
            0xe9: CPU.Instruction(self, instructions.SBC, AddressingMode.IMMEDIATE, 2),
            0xea: CPU.Instruction(self, instructions.NOP, AddressingMode.NONE, 2),
            0xec: CPU.Instruction(self, instructions.CPX, AddressingMode.ABSOLUTE, 4),
            0xed: CPU.Instruction(self, instructions.SBC, AddressingMode.ABSOLUTE, 4),
            0xee: CPU.Instruction(self, instructions.INC, AddressingMode.ABSOLUTE, 6),
            0xf0: CPU.Instruction(self, instructions.BEQ, AddressingMode.RELATIVE, 2),
            0xf1: CPU.Instruction(self, instructions.SBC, AddressingMode.INDIRECT_Y, 5),
            0xf5: CPU.Instruction(self, instructions.SBC, AddressingMode.ZEROPAGE_X, 4),
            0xf6: CPU.Instruction(self, instructions.INC, AddressingMode.ZEROPAGE_X, 6),
            0xf8: CPU.Instruction(self, instructions.SED, AddressingMode.NONE, 2),
            0xf9: CPU.Instruction(self, instructions.SBC, AddressingMode.ABSOLUTE_Y, 4),
            0xfd: CPU.Instruction(self, instructions.SBC, AddressingMode.ABSOLUTE_X, 4),
            0xfe: CPU.Instruction(self, instructions.INC, AddressingMode.ABSOLUTE_X, 7)
        }

        super(CPU, self).__init__()

    def set_status(self, status, value):
        if status == "zero":
            self.registers['p'].set_bit(1, value == 0)
        elif status == "negative":
            self.registers['p'].set_bit(7, value & (1 << 7))
        else:
            self.registers['p'].set_bit(self._status_bits[status], value)

    def get_status(self, status):
        bitnum = self._status_bits[status]
        return bool(self.registers['p'].read() & (1 << bitnum))

    def execute(self, mem):
        code = mem[0]
        try:
            return self._opcodes[code](mem[1:3])
        except:
            log.critical("Exception while executing: {0:#06x}: {1}".format(self.registers['pc'].read(), ["{0:#04x}".format(x) for x in mem]))
            for register_name in self.registers:
                log.critical("{0}: {1:#06x}".format(register_name, self.registers[register_name].read()))
            raise

    def stack_push(self, value):
        self.registers['sp'].increment(value=-1)
        self.memory.write(0x100 + self.registers['sp'].read(), value)

    def stack_pop(self):
        val = self.memory.read(0x100 + self.registers['sp'].read())
        self.registers['sp'].increment()
        return val

    def run(self):
        while True:
            # Check IRQs
            if self.IRQ.value != b'\x00':
                log.debug("IRQ triggered with code {0}.".format(self.IRQ.value))
                self.stack_push((self.registers['pc'].read() << 8) & 0xff)
                self.stack_push((self.registers['pc'].read()) & 0xff)
                self.stack_push(self.registers['p'].read())
                self.set_status('interrupt', True)

                if self.IRQ.value == b'N':  # NMI
                    self.registers['pc'].write(self.memory.read(0xfffb) << 8 | self.memory.read(0xfffa))
                elif self.IRQ.value == b'R':  # Reset
                    self.registers['pc'].write((self.memory.read(0xfffd) << 8) | self.memory.read(0xfffc))
                elif self.IRQ.value == b'I' and not self.get_status('interrupt'):  # Maskable Interrupt
                    self.registers['pc'].write((self.memory.read(0xffff) << 8) | self.memory.read(0xfffe))

                # Clear the IRQ
                self.IRQ.value = 0

            # Fetch the next instruction, execute it, update PC and cycle counter.
            pc = self.registers['pc'].read()
            # Go directly to the cartridge prg_rom to read multiple bytes.
            pc -= 0x8000
            increment_cycles = self.execute(self._cart.prg_rom[pc:pc+3])
            with self.CycleLock:
                self.Cycles.value += increment_cycles
                if self.Cycles.value >= 27426:
                    self._console.PPU.VBLANK_LOCK.notify()
