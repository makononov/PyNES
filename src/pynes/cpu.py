class Cpu:
  memory_size = 0x10000

  def __init__(self):
    self._memory = [0xff] * Cpu.memory_size
    self.registers = {'pc': 0, 'sp': 0, 'a': 0, 'x': 0, 'y': 0, 's': 0x34}
    self._stack = []

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
  
  def print_rom(self, cart):
    while self.registers['pc'] < cart._prg_rom_size:
      pc = self.registers['pc']
      opcode = ord(cart.read_prg(pc, 1))
      print("OPCODE: {0:#2x}".format(opcode))
      if opcode == 0x00:
        print("BRK")
        pc = pc + 1
      elif opcode == 0x01:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ORA ({0:#2x}, X)".format(addr))
        pc = pc + 2
      elif opcode == 0x05:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ORA {0:#2x}".format(addr))
        pc = pc + 2
      elif opcode == 0x06:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ASL {0:#2x}".format(addr))
        pc = pc + 2
      elif opcode == 0x08:
        print("PHP")
        pc = pc + 1
      elif opcode == 0x09:
        val = ord(cart.read_prg(pc + 1, 1))
        print("ORA #{0:#2x}".format(val))
        pc = pc + 2
      elif opcode == 0x0a:
        print("ASL A")
        pc = pc + 1
      elif opcode == 0x0d:
        addr = ord(cart.read_prg(pc + 1, 1)) << 2
        addr = addr + ord(cart.read_prg(pc + 2, 1))
        print("ORA {0:#4x}".format(addr))
        pc = pc + 3
      elif opcode == 0x0e:
        addr = ord(cart.read_prg(pc + 1, 1)) << 2
        addr = addr + ord(cart.read_prg(pc + 2, 1))
        print("ASL {0:#4x}".format(addr))
        pc = pc + 3
      elif opcode == 0x10:
        offset = ord(cart.read_prg(pc + 1, 1))
        if (offset & 0x80):
          offset = (offset - 128) * -1  # Offset is a signed 7 bit value
        print("BPL {0:#2x}".format(offset))
        pc = pc + 2
      elif opcode == 0x11:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ORA ({0:#2x}), Y".format(addr))
        pc = pc + 2
      elif opcode == 0x15:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ORA {0:#2x}".format(addr))
        pc = pc + 2
      elif opcode == 0x16:
        addr = ord(cart.read_prg(pc + 1, 1))
        print("ASL {0:#2x}".format(addr))
        pc = pc + 2
      else:
        raise Exception("Illegal opcode!")
      
      print("PC: {0:#2x}".format(pc))
      self.registers['pc'] = pc

class MemoryError(Exception):
  pass
