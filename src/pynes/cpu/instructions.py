__author__ = 'misha'

import numpy as np

class Instruction:
    class AddressingMode:
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


    @staticmethod
    def ADC(self, param):
        pass

    def __init__(self, cpu, fn, addressing):
        self._cpu = cpu
        self._fn = fn
        self._addmode = addressing

    def __call__(self, *args, **kwargs):
        pass
