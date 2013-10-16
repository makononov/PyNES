__author__ = 'misha'

size = 0


def read(cpu, *args):
    return cpu.registers['a'].read(), 0


def write(cpu, param, value):
    cpu.registers['a'].write(value)


def print(param):
    return "A"
