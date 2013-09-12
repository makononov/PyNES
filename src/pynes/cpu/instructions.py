__author__ = 'misha'

import numpy as np


class Instruction:
    class AddressingMode:
        # TODO: Add proper returns to addressing modes.
        class NONE:
            pass

        class IMMEDIATE:
            @staticmethod
            def get_value(cpu, param):
                return param

        class ZEROPAGE:
            @staticmethod
            def get_value(cpu, param):
                return cpu.memory.read(param)

        class ZEROPAGE_X:
            @staticmethod
            def get_value(cpu, param):
                address = np.uint8(param + cpu.registers['x'])
                return cpu.memory.read(address)

        class ZEROPAGE_Y:
            @staticmethod
            def get_value(cpu, param):
                address = np.uint8(param + cpu.registers['y'])
                return cpu.memory.read(address)

        class ABSOLUTE:
            @staticmethod
            def get_value(cpu, param):
                return cpu.memory.read(param)

        class ABSOLUTE_X:
            @staticmethod
            def get_value(cpu, param):
                return cpu.memory.read(param + cpu.registers['x'])

        class ABSOLUTE_Y:
            @staticmethod
            def get_value(cpu, param):
                return cpu.memory.read(param + cpu.registers['y'])

        class INDIRECT_X:
            @staticmethod
            def get_value(cpu, param):
                indirect_address = param + cpu.registers['x']
                address = cpu.memory.read(indirect_address)
                address += (cpu.memory.read(indirect_address + 1) << 8)
                return cpu.memory.read(address)

        class INDIRECT_Y:
            @staticmethod
            def get_value(cpu, param):
                address = cpu.memory.read(param)
                address += (cpu.memory.read(param + 1) << 8)
                return cpu.memory.read(address + cpu.registers['y'])

        class ACCUMULATOR:
            @staticmethod
            def get_value(cpu, param):
                return cpu.registers['a']


    def __init__(self, cpu, fn, addressing):
        self._cpu = cpu
        self._fn = fn
        self._admode = addressing


    def __call__(self, *args, **kwargs):
        value, cycles, memlocs = self._admode.get_value(*args)
        fn_value, fn_cycles = self._fn(self._cpu, value)
        if fn_value is not None:
            self._admode.write_value(fn_value)

        return cycles + fn_cycles, memlocs


    @staticmethod
    def ADC(cpu, value):
        """
        Add value to A with carry
        """
        carry = int(cpu.get_status('carry'))
        total = value + cpu.registers['a'].read() + carry
        cpu.set_status('zero', total & 0xff)
        if cpu.get_status('decimal'):
            if (cpu.registers['a'].read() & 0xf) + (value & 0xf) + carry > 9:
                total += 6
            if total > 0x99:
                total += 96
            cpu.set_status('carry', total > 0x99)
        else:
            cpu.set_status('carry', total > 0xff)

        cpu.registers['a'].write(total)
        cpu.set_status('zero', total)
        cpu.set_status('negative', total)
        cpu.set_status('overflow', (total != cpu.registers['a'].read()))

        return None, 3

