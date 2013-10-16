"""
Zero-page indexed addressing with X-Register
"""
size = 1


def read(cpu, param):
    address = param + cpu.registers['x'].read()
    return cpu.memory.read(address)


def write(cpu, param, value):
    address = param + cpu.registers['x'].read()
    cpu.memory.write(address, value)


def print(param):
    return "{0:#04x},X".format(param)