"""
Post-indexed indirect addressing with Y-Register
"""
size = 1


def read(cpu, param):
    address = cpu.memory.read(param)
    address += (cpu.memory.read(param + 1) << 8)
    return cpu.memory.read(address + cpu.registers['y'].read())


def write(cpu, param, value):
    address = cpu.memory.read(param)
    address += (cpu.memory.read(param + 1) << 8)
    cpu.memory.write(address + cpu.registers['y'].read(), value)


def print(param):
    return "({0:#04x}),Y".format(param)