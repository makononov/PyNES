"""
Zeropage absolute addressing
"""
size = 1


def read(cpu, param):
    return cpu.memory.read(param)


def write(cpu, param, value):
    cpu.memory.write(param, value)


def print(param):
    return "{0:#04x}".format(param)
