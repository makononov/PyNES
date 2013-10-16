"""
Immediate addressing
"""
size = 1


def read(cpu, param):
    return param


def print(param):
    return "#{0:#04x}".format(param)
