__author__ = 'misha'

size = 1


def read(cpu, param):
    indirect_address = param + cpu.registers['x'].read()
    address = cpu.memory.read(indirect_address)
    address += (cpu.memory.read(indirect_address + 1) << 8)
    return cpu.memory.read(address), 0


def write(cpu, param, value):
    indirect_address = param + cpu.registers['x'].read()
    address = cpu.memory.read(indirect_address)
    address += (cpu.memory.read(indirect_address + 1) << 8)
    cpu.memory.write(address, value)


def print(param):
    return "({0:#04x},X)".format(param)