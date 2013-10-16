"""
Accumulator based addressing
"""
size = 0


def read(cpu, *args):
    return cpu.registers['a'].read()


def write(cpu, param, value):
    cpu.registers['a'].write(value)


def print(param):
    return "A"
