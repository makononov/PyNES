__author__ = 'misha'

import numpy as np


class Instruction:
    class AddressingMode:
        # TODO: Add proper returns to addressing modes.
        class NONE:
            size = 0

            @staticmethod
            def read(cpu, param):
                return None, 0

        class IMMEDIATE:
            size = 1

            @staticmethod
            def read(cpu, param):
                return param, 0

        class RELATIVE:
            size = 1

            @staticmethod
            def read(cpu, param):
                return np.int8(param), 0

        class ZEROPAGE:
            size = 1

            @staticmethod
            def read(cpu, param):
                return cpu.memory.read(param), 0

            @staticmethod
            def write(cpu, param, value):
                cpu.memory.write(param, value)

        class ZEROPAGE_X:
            size = 1

            @staticmethod
            def read(cpu, param):
                address = np.uint8(param + cpu.registers['x'].read())
                return cpu.memory.read(address), 0

            @staticmethod
            def write(cpu, param, value):
                address = np.uint8(param + cpu.registers['x'].read())
                cpu.memory.write(address, value)

        class ZEROPAGE_Y:
            size = 1

            @staticmethod
            def read(cpu, param):
                address = np.uint8(param + cpu.registers['y'].read())
                return cpu.memory.read(address), 0

            def write(cpu, param, value):
                address = np.uint8(param + cpu.registers['y'].read())
                cpu.memory.write(address, value)


        class ABSOLUTE:
            size = 2

            @staticmethod
            def read(cpu, param):
                return cpu.memory.read(param), 0

            @staticmethod
            def write(cpu, param, value):
                cpu.memory.write(param, value)


        class ABSOLUTE_X:
            size = 2

            @staticmethod
            def read(cpu, param):
                return cpu.memory.read(param + cpu.registers['x'].read()), 0

            @staticmethod
            def write(cpu, param, value):
                cpu.memory.write(param + cpu.registers['x'].read(), value)

        class ABSOLUTE_Y:
            size = 2

            @staticmethod
            def read(cpu, param):
                return cpu.memory.read(param + cpu.registers['y'].read()), 0

            @staticmethod
            def write(cpu, param, value):
                cpu.memory.write(param + cpu.registers['y'].read(), value)

        class INDIRECT:
            size = 2

            @staticmethod
            def read(cpu, param):
                return param

        class INDIRECT_X:
            size = 2

            @staticmethod
            def read(cpu, param):
                indirect_address = param + cpu.registers['x']
                address = cpu.memory.read(indirect_address)
                address += (cpu.memory.read(indirect_address + 1) << 8)
                return cpu.memory.read(address), 0

            @staticmethod
            def write(cpu, param, value):
                indirect_address = param + cpu.registers['x']
                address = cpu.memory.read(indirect_address)
                address += (cpu.memory.read(indirect_address + 1) << 8)
                cpu.memory.write(address, value)


        class INDIRECT_Y:
            size = 2

            @staticmethod
            def read(cpu, param):
                address = cpu.memory.read(param)
                address += (cpu.memory.read(param + 1) << 8)
                return cpu.memory.read(address + cpu.registers['y']), 0

            @staticmethod
            def write(cpu, param, value):
                address = cpu.memory.read(param)
                address += (cpu.memory.read(param + 1) << 8)
                cpu.memory.write(address + cpu.registers['y'], value)

        class ACCUMULATOR:
            size = 0

            @staticmethod
            def read(cpu):
                return cpu.registers['a'], 0


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
        self._cpu.register['pc'].increment(value=1 + self._admode.size)
        fn_value, fnscycles = self._fn(self._cpu, value)
        if fn_value is not None:
            self._admode.write(self._cpu, fn_value)

        return self._cycles + adcycles + fncycles


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

        return None, 0

    @staticmethod
    def AND(cpu, value):
        """
        'AND' memory with Accumulator
        """
        value &= cpu.registers['a'].read()
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['a'].write(value)
        return None, 0

    @staticmethod
    def ASL(cpu, value):
        """
        Shift left one bit
        """
        cpu.set_status('carry', bool(value & 0x80))
        value = (value << 1) & 0xff
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        return value, 0

    @staticmethod
    def BCC(cpu, offset):
        """
        Branch if carry flag is *not* set
        """
        extra_cycle = 0
        if cpu.get_status('carry') is not True:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def BCS(cpu, offset):
        """
        Branch if carry flag is set
        """
        extra_cycle = 0
        if cpu.get_status('carry') is True:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def BEQ(cpu, offset):
        """
        Branch if result was zero
        """
        extra_cycle = 0
        if cpu.get_status('zero') is True:
            pc = cpu.regisers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.regisers['pc'].increment(value=offset)
        return None, extra_cycle


    @staticmethod
    def BIT(cpu, value):
        """
        Compare bits
        """
        cpu.set_status('negative', value)
        cpu.set_status('overflow', value & 0x40)
        cpu.set_status('zero', value & cpu.registers['a'].read())
        return None, 0

    @staticmethod
    def BMI(cpu, offset):
        """
        Branch if result was negative
        """
        extra_cycle = 0
        if cpu.get_status('negative') is True:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def BNE(self, param):
        """
        Branch if result was *not* zero
        """
        extra_cycle = 0
        if cpu.get_status('zero') is False:
            pc = cpu.regisers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.regisers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def BPL(cpu, offset):
        """
        Branch if result was positive
        """
        extra_cycle = 0
        if cpu.get_status('negative') is False:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def BRK(cpu, value):
        """
        Request a maskable interrupt (IRQ)
        """
        cpu.registers['pc'].increment()
        pc = cpu.registers['pc'].read()
        cpu.stack_push((pc >> 8) & 0xff) # Push high byte
        cpu.stack_push(pc & 0xff) # ...followed by low byte
        cpu.set_status('break', True)
        cpu.stack_push(cpu.registers['p'].read())
        cpu.IRQ.value = "I"

    @staticmethod
    def BVC(cpu, offset):
        """
        Branch if overflow flag is *not* set
        """
        extra_cycle = 0
        if cpu.get_status('overflow') is False:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle


    @staticmethod
    def BVS(cpu, offset):
        """
        Branch if overflow flag is set
        """
        extra_cycle = 0
        if cpu.get_status('overflow') is True:
            pc = cpu.registers['pc'].read()
            # Add an extra cycle if going across pages
            if (pc * 0xff00) != (pc + offset & 0xff00):
                extra_cycle = 1
            cpu.registers['pc'].increment(value=offset)
        return None, extra_cycle

    @staticmethod
    def CLC(cpu, value):
        """
        Clear carry status flag
        """
        cpu.set_status('carry', False)
        return None, 0

    @staticmethod
    def CLD(cpu, value):
        """
        Clear decimal status flag
        """
        cpu.set_status('decimal', False)
        return None, 0

    @staticmethod
    def CLI(cpu, value):
        """
        Clear interrupt status flag
        """
        cpu.set_status('interrupt', False)
        return None, 0

    @staticmethod
    def CLV(cpu, value):
        """
        Clear overflow status flag
        """
        cpu.set_status('overflow', False)
        return None, 0

    @staticmethod
    def CMP(cpu, value):
        """
        Compare accumulator with value
        """
        comp = cpu.registers['a'].read() - value
        cpu.set_status('carry', (comp < 0x100))
        cpu.set_status('negative', comp)
        cpu.set_status('zero', comp & 0xff)
        return None, 0

    @staticmethod
    def CPX(cpu, value):
        """
        Compare X-register with value
        """
        comp = cpu.registers['x'].read() - value
        cpu.set_status('carry', (comp < 0x100))
        cpu.set_status('negative', comp)
        cpu.set_status('zero', comp & 0xff)
        return None, 0

    @staticmethod
    def CPY(cpu, value):
        """
        Compare Y-register with value
        """
        comp = cpu.registers['y'].read() - value
        cpu.set_status('carry', (comp < 0x100))
        cpu.set_status('negative', comp)
        cpu.set_status('zero', comp & 0xff)
        return None, 0

    @staticmethod
    def DEC(cpu, value):
        """
        Decrement memory
        """
        value = (value - 1) & 0xff
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        return value, 0

    @staticmethod
    def DEX(cpu, value):
        """
        Decrement X-register
        """
        x = cpu.registers['x'].read()
        cpu.registers['x'].write(x - 1)
        cpu.set_status('negative', x)
        cpu.set_status('zero', x)
        return None, 0

    @staticmethod
    def DEY(cpu, value):
        """
        Decrement Y-register
        """
        y = cpu.registers['y'].read()
        cpu.registers['y'].write(y - 1)
        cpu.set_status('negative', y)
        cpu.set_status('zero', y)
        return None, 0

    @staticmethod
    def EOR(cpu, value):
        """
        XOR value with accumulator
        """
        value ^= cpu.registers['a'].read()
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['a'].write(value)
        return None, 0

    @staticmethod
    def INC(cpu, value):
        """
        Increment memory
        """
        value = (value + 1) & 0xff
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        return value, 0

    @staticmethod
    def INX(cpu, value):
        """
        Increment X-register
        """
        x = cpu.registers['x'].read()
        x = (x + 1) & 0xff
        cpu.registers['x'].write(x)
        cpu.set_status('negative', x)
        cpu.set_status('zero', x)
        return None, 0

    @staticmethod
    def INY(cpu, value):
        """
        Increment Y-register
        """
        y = cpu.registers['y'].read()
        y = (y + 1) & 0xff
        cpu.registers['y'].write(y)
        cpu.set_status('negative', y)
        cpu.set_status('zero', y)
        return None, 0

    @staticmethod
    def JMP(cpu, value):
        """
        Jump to a location in memory
        """
        cpu.registers['pc'].write(value)
        return None, 0

    @staticmethod
    def JSR(cpu, value):
        """
        Jump to a location in memory and store the return address on the stack
        """
        pc = cpu.registers['pc'].read() - 1
        cpu.stack_push((pc >> 8) & 0xff)
        cpu.stack_push(pc & 0xff)
        cpu.registers['pc'].write(value)
        return None, 0

    @staticmethod
    def LDA(cpu, value):
        """
        Load a value into the accumulator
        """
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['a'].write(value)
        return None, 0

    @staticmethod
    def LDX(cpu, value):
        """
        Load a value into the X-register
        """
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['x'].write(value)
        return None, 0

    @staticmethod
    def LDY(cpu, value):
        """
        Load a value into the Y-register
        """
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['y'].write(value)
        return None, 0

    @staticmethod
    def ORA(cpu, value):
        """
        'OR' memory with Accumulator
        """
        value |= cpu.registers['a'].read()
        cpu.set_status('negative', value)
        cpu.set_status('zero', value)
        cpu.registers['a'].write(value)
        return None
