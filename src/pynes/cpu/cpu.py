__author__ = 'misha'

from utils import Enumerate

addressing = Enumerate(
    "NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")


class opcode:
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

        opcode.__codes[self.__code] = wrapped_fn
        return wrapped_fn

    @staticmethod
    def execute(code, *args):
        opcode.__codes[code](*args)


@opcode(0x00, addressing.NONE)
def BRK():
    return (0, 7)
