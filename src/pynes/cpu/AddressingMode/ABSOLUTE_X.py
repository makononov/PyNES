"""
Indexed absolute addressing with X-Register
"""
size = 2


def read(cpu, param):
    return cpu.memory.read(param + cpu.registers['x'].read())


def write(cpu, param, value):
    cpu.memory.write(param + cpu.registers['x'].read(), value)


def print(param):
    return "{0:#06x}, X".format(param)