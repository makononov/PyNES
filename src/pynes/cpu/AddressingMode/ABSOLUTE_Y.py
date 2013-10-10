__author__ = 'misha'

size = 2


def read(cpu, param):
    return cpu.memory.read(param + cpu.registers['y'].read()), 0


def write(cpu, param, value):
    cpu.memory.write(param + cpu.registers['y'].read(), value)
