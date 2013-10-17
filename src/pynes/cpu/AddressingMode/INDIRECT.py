"""
Indirect addressing for JMP instructions
"""
size = 2


def read(cpu, param):
    low_bit = cpu.memory.read(param)
    high_bit = cpu.memory.read(param + 1)
    return (high_bit << 8) | low_bit


def print(param):
    return "({0:#06x})".format(param)