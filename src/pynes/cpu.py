__author__ = 'misha'

from utils import Enumerate
import numpy as np
import threading

addressing = Enumerate(
    "NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")


class CPU (threading.Thread):
    class Memory:
        def __init__(self):
            self._ram = []

        def write(self, address, value):
            pass

        def read(self, address):
            pass

    class Register:
        def __init__(self, dtype):
            self._dtype = dtype
            self._value = None

        def write(self, value):
            self._value = self._dtype(value)

        def read(self):
            return self._value

    class Instruction:
        class Opcode:
            __codes = {}

            def __init__(self, code, addmode):
                self.__addmode = addmode
                self.__code = code

            def __call__(self, fn, *args):
                def wrapped_fn(*args):
                    if self.__addmode == addressing.NONE:
                        fn()
                    elif self.__addmode in (
                        addressing.ABSOLUTE, addressing.ABSOLUTE_X, addressing.ABSOLUTE_Y, addressing.INDIRECT):
                        addspace = args[0]
                        fn(*addspace[1:3])
                    else:
                        addspace = args[0]
                        fn(*addspace[1:2])

                self.__class__.__codes[self.__code] = wrapped_fn
                return wrapped_fn

            @staticmethod
            def execute(code, *args):
                CPU.Instruction.Opcode.__codes[code](*args)

        @staticmethod
        @Opcode(0x00, addressing.NONE)
        def BRK(self):
            return (1, 7)

    def __init__(self, cart, cycle_count):
        self.memory = CPU.Memory()
        self.registers = {'pc': Register(np.uint16), 'a': Register(np.int8), 'x': Register(np.uint8),
                          'y': Register(np.uint8), 'sp': Register(np.uint8)}
        self._cart = cart
        self._cycle_count = cycle_count

        # Initialize the PC to the 16 bit value in 0xfffc.
        self.registers['pc'].write((self.memory.read(0xfffd) << 8) + self.memory.read(0xfffc))

        super(CPU, self).__init__()


    def run(self):
        while True:
            # Fetch the next instruction, execute it, update PC and cycle counter.
            pc = self.registers['pc'].read()
            increment_pc, increment_cycles = CPU.execute(self._cart['prg_rom'][pc:pc+4])
            self.registers['pc'].write(pc + increment_pc)
            self._cycle_count += increment_cycles;
