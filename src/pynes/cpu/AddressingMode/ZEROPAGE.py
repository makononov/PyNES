__author__ = 'misha'

size = 1


def read(cpu, param):
    return cpu.memory.read(param), 0


def write(cpu, param, value):
    cpu.memory.write(param, value)
