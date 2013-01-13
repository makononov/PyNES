class Cpu:
  memory_size = 0x10000

  def __init__(self):
    self._memory = [0] * Cpu.memory_size

  def mem_write(self, address, value):
    if (address >= Cpu.memory_size):
      raise MemoryError('Memory write out of bounds.')
    if (address <= 0x2000):
      # Mirror the first 2kB of memory 4 times on write
      base_address = address % 0x800
      for mirror in range(0, 4):
        self._memory[base_address + (mirror * 0x800)] = value
    else:
      self._memory[address] = value

  def mem_read(self, address):
    if (address >= Cpu.memory_size):
      raise MemoryError('Memory read out of bounds.')
    return self._memory[address]

class MemoryError(Exception):
  pass
