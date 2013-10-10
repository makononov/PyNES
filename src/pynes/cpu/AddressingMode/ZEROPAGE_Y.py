__author__ = 'misha'

size = 1


def read(cpu, param):
    address = param + cpu.registers['y'].read()
    return cpu.memory.read(address), 0


def write(cpu, param, value):
    address = param + cpu.registers['y'].read()
    cpu.memory.write(address, value)
