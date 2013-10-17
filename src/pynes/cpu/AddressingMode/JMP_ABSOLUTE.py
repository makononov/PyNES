"""
Absolute addressing for JMP instructions -- 2 byte immediate value for memory locations
"""
size = 2


def read(cpu, param):
    return param


def print(param):
    return "{0:#06x}".format(param)
