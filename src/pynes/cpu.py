from utils import Enumerate

addressing = Enumerate("NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")

class Cpu(object):

  def __init__(self, cartridge = None):
    self.cartridge = cartridge 

    self._memory = {}
    self._memory['zeropage'] = [0xff] * 0x100 # 0x0000 - 0x00ff
    self._memory['stack'] = [0xff] * 0x100 # 0x0100 - 0x01ff
    self._memory['RAM'] = [0xff] * 0x600 # 0x0200 - 0x07ff
    self._memory['expansion_rom'] = [0xff] * 0x1fe0 # 0x4020 - 0x5fff
    self._memory['SRAM'] = [0xff] * 0x2000 # 0x6000 - 0x7fff
    self._memory['PRG_ROM'] = [[], []] # 0x8000 - 0xbfff, 0xc000 - 0xffff, uninitialized since it is filled by the cartridge.

    self.registers = {'pc': 0, 'a': 0, 'x': 0, 'y': 0, 's': 0x34}

    self._instruction_set = {
      0x00: Instruction("BRK", addressing.NONE, 7),
      0x01: Instruction("ORA", addressing.INDIRECT_X, 6),
      0x05: Instruction("ORA", addressing.ZEROPAGE, 3),
      0x06: Instruction("ASL", addressing.ZEROPAGE, 3),
      0x08: Instruction("PHP", addressing.NONE, 3),
      0x09: Instruction("ORA", addressing.IMMEDIATE, 2),
      0x0a: Instruction("ASL", addressing.ACCUMULATOR, 2),
      0x0d: Instruction("ORA", addressing.ABSOLUTE, 4),
      0x0e: Instruction("ASL", addressing.ABSOLUTE, 6),
      0x10: Instruction("BPL", addressing.RELATIVE, 2),
      0x11: Instruction("ORA", addressing.INDIRECT_Y, 5),
      0x15: Instruction("ORA", addressing.ZEROPAGE_X, 4),
      0x16: Instruction("ASL", addressing.ZEROPAGE_X, 6),
      0x18: Instruction("CLC", addressing.NONE, 2),
      0x19: Instruction("ORA", addressing.ABSOLUTE_Y, 4),
      0x1d: Instruction("ORA", addressing.ABSOLUTE_X, 4),
      0x1e: Instruction("ASL", addressing.ABSOLUTE_X, 7),

      0x20: Instruction("JSR", addressing.ABSOLUTE, 6),
      0x21: Instruction("AND", addressing.INDIRECT_X, 6),
      0x24: Instruction("BIT", addressing.ZEROPAGE, 3),
      0x25: Instruction("AND", addressing.ZEROPAGE, 3),
      0x26: Instruction("ROL", addressing.ZEROPAGE, 5),
      0x28: Instruction("PLP", addressing.NONE, 4),
      0x29: Instruction("AND", addressing.IMMEDIATE, 2),
      0x2a: Instruction("ROL", addressing.ACCUMULATOR, 2),
      0x2c: Instruction("BIT", addressing.ABSOLUTE, 4),
      0x2d: Instruction("AND", addressing.ABSOLUTE, 4),
      0x2e: Instruction("ROL", addressing.ABSOLUTE, 6),
      0x30: Instruction("BMI", addressing.RELATIVE, 2),
      0x31: Instruction("AND", addressing.INDIRECT_Y, 5),
      0x35: Instruction("AND", addressing.ZEROPAGE_X, 6),
      0x36: Instruction("ROL", addressing.ZEROPAGE_X, 6),
      0x38: Instruction("SEC", addressing.NONE, 2),
      0x39: Instruction("AND", addressing.ABSOLUTE_Y, 4),
      0x3d: Instruction("AND", addressing.ABSOLUTE_X, 4),
      0x3e: Instruction("ROL", addressing.ABSOLUTE_X, 7),

      0x40: Instruction("RTI", addressing.NONE, 6),
      0x41: Instruction("EOR", addressing.INDIRECT_X, 6),
      0x45: Instruction("EOR", addressing.ZEROPAGE, 2),
      0x46: Instruction("LSR", addressing.ZEROPAGE, 5),
      0x48: Instruction("PHA", addressing.NONE, 3),
      0x49: Instruction("EOR", addressing.IMMEDIATE, 2),
      0x4a: Instruction("LSR", addressing.ACCUMULATOR, 2),
      0x4c: Instruction("JMP", addressing.ABSOLUTE, 3),
      0x4d: Instruction("EOR", addressing.ABSOLUTE, 4),
      0x4e: Instruction("LSR", addressing.ABSOLUTE, 6),
      0x50: Instruction("BVC", addressing.RELATIVE, 2),
      0x51: Instruction("EOR", addressing.INDIRECT_Y, 5),
      0x55: Instruction("EOR", addressing.ZEROPAGE_X, 4),
      0x56: Instruction("LSR", addressing.ZEROPAGE_X, 6),
      0x58: Instruction("CLI", addressing.NONE, 2),
      0x59: Instruction("EOR", addressing.ABSOLUTE_Y, 4),
      0x5d: Instruction("EOR", addressing.ABSOLUTE_X, 4),
      0x5e: Instruction("LSR", addressing.ABSOLUTE_X, 7),

      0x60: Instruction("RTS", addressing.NONE, 6),
      0x61: Instruction("ADC", addressing.INDIRECT_X, 6),
      0x65: Instruction("ADC", addressing.ZEROPAGE, 3),
      0x66: Instruction("ROR", addressing.ZEROPAGE, 5),
      0x68: Instruction("PLA", addressing.NONE, 4),
      0x69: Instruction("ADC", addressing.IMMEDIATE, 2),
      0x6a: Instruction("ROR", addressing.ACCUMULATOR, 2),
      0x6c: Instruction("JMP", addressing.INDIRECT, 5),
      0x6d: Instruction("ADC", addressing.ABSOLUTE, 4),
      0x6e: Instruction("ROR", addressing.ABSOLUTE, 6),
      0x70: Instruction("BVS", addressing.RELATIVE, 2),
      0x71: Instruction("ADC", addressing.INDIRECT_Y, 5),
      0x75: Instruction("ADC", addressing.ZEROPAGE_X, 4),
      0x76: Instruction("ROR", addressing.ZEROPAGE_X, 6),
      0x78: Instruction("SEI", addressing.NONE, 2),
      0x79: Instruction("ADC", addressing.ABSOLUTE_Y, 4),
      0x7d: Instruction("ADC", addressing.ABSOLUTE_X, 4),
      0x7e: Instruction("ROR", addressing.ABSOLUTE_X, 7),

      0x81: Instruction("STA", addressing.INDIRECT_X, 6),
      0x84: Instruction("STY", addressing.ZEROPAGE, 3),
      0x85: Instruction("STA", addressing.ZEROPAGE, 3),
      0x86: Instruction("STX", addressing.ZEROPAGE, 3),
      0x88: Instruction("DEY", addressing.NONE, 2),
      0x8a: Instruction("TXA", addressing.NONE, 2),
      0x8c: Instruction("STY", addressing.ABSOLUTE, 4),
      0x8d: Instruction("STA", addressing.ABSOLUTE, 4),
      0x8e: Instruction("STX", addressing.ABSOLUTE, 4),
      0x90: Instruction("BCC", addressing.NONE, 2),
      0x91: Instruction("STA", addressing.INDIRECT_Y, 6),
      0x94: Instruction("STY", addressing.ZEROPAGE_X, 4),
      0x95: Instruction("STA", addressing.ZEROPAGE_X, 4),
      0x96: Instruction("STX", addressing.ZEROPAGE_Y, 4),
      0x98: Instruction("TYA", addressing.NONE, 2),
      0x99: Instruction("STA", addressing.ABSOLUTE_Y, 5),
      0x9a: Instruction("TXS", addressing.NONE, 2),
      0x9d: Instruction("STA", addressing.ABSOLUTE_X, 5),

      0xa0: Instruction("LDY", addressing.IMMEDIATE, 2),
      0xa1: Instruction("LDA", addressing.INDIRECT_X, 6),
      0xa2: Instruction("LDX", addressing.IMMEDIATE, 2),
      0xa4: Instruction("LDY", addressing.ZEROPAGE, 3),
      0xa5: Instruction("LDA", addressing.ZEROPAGE, 3),
      0xa6: Instruction("LDX", addressing.ZEROPAGE, 3),
      0xa8: Instruction("TAY", addressing.NONE, 2),
      0xa9: Instruction("LDA", addressing.IMMEDIATE, 2),
      0xaa: Instruction("TAX", addressing.NONE, 2),
      0xac: Instruction("LDY", addressing.ABSOLUTE, 4),
      0xad: Instruction("LDA", addressing.ABSOLUTE, 4),
      0xae: Instruction("LDX", addressing.ABSOLUTE, 4),
      0xb0: Instruction("BCS", addressing.RELATIVE, 2),
      0xb1: Instruction("LDA", addressing.INDIRECT_Y, 5), 
      0xb4: Instruction("LDY", addressing.ZEROPAGE_X, 4),
      0xb5: Instruction("LDA", addressing.ZEROPAGE_X, 4),
      0xb6: Instruction("LDX", addressing.ZEROPAGE_Y, 4),
      0xb8: Instruction("CLV", addressing.NONE, 2),
      0xb9: Instruction("LDA", addressing.ABSOLUTE_Y, 4),
      0xba: Instruction("TSX", addressing.NONE, 2),
      0xbc: Instruction("LDY", addressing.ABSOLUTE_X, 4),
      0xbd: Instruction("LDA", addressing.ABSOLUTE_X, 4),
      0xbe: Instruction("LDX", addressing.ABSOLUTE_Y, 4),

      0xc0: Instruction("CPY", addressing.IMMEDIATE, 2),
      0xc1: Instruction("CMP", addressing.INDIRECT_X, 6),
      0xc4: Instruction("CPY", addressing.ZEROPAGE, 3),
      0xc5: Instruction("CMP", addressing.ZEROPAGE, 3),
      0xc6: Instruction("DEC", addressing.ZEROPAGE, 5),
      0xc8: Instruction("INY", addressing.NONE, 2),
      0xc9: Instruction("CMP", addressing.IMMEDIATE, 2),
      0xca: Instruction("DEX", addressing.NONE, 2),
      0xcc: Instruction("CPY", addressing.ABSOLUTE, 4),
      0xcd: Instruction("CMP", addressing.ABSOLUTE, 4),
      0xce: Instruction("DEC", addressing.ABSOLUTE, 6),
      0xd0: Instruction("BNE", addressing.RELATIVE, 2),
      0xd1: Instruction("CMP", addressing.INDIRECT_Y, 5),
      0xd5: Instruction("CMP", addressing.ZEROPAGE_X, 4),
      0xd6: Instruction("DEC", addressing.ZEROPAGE_X, 6),
      0xd8: Instruction("CLD", addressing.NONE, 2),
      0xd9: Instruction("CMP", addressing.ABSOLUTE_Y, 4),
      0xdd: Instruction("CMP", addressing.ABSOLUTE_X, 4),
      0xde: Instruction("DEC", addressing.ABSOLUTE_X, 7),

      0xe0: Instruction("CPX", addressing.IMMEDIATE, 2),
      0xe1: Instruction("SBC", addressing.INDIRECT_X, 6),
      0xe4: Instruction("CPX", addressing.ZEROPAGE, 3),
      0xe5: Instruction("SBC", addressing.ZEROPAGE, 3),
      0xe6: Instruction("INC", addressing.ZEROPAGE, 5),
      0xe8: Instruction("INX", addressing.NONE, 2),
      0xe9: Instruction("SBC", addressing.IMMEDIATE, 2),
      0xea: Instruction("NOP", addressing.NONE, 2),
      0xec: Instruction("CPX", addressing.ABSOLUTE, 4),
      0xed: Instruction("SBC", addressing.ABSOLUTE, 4),
      0xee: Instruction("INC", addressing.ABSOLUTE, 6),
      0xf0: Instruction("BEQ", addressing.RELATIVE, 2),
      0xf1: Instruction("SBC", addressing.INDIRECT_Y, 5),
      0xf5: Instruction("SBC", addressing.ZEROPAGE_X, 4),
      0xf6: Instruction("INC", addressing.ZEROPAGE_X, 6),
      0xf8: Instruction("SED", addressing.NONE, 2),
      0xf9: Instruction("SBC", addressing.ABSOLUTE_Y, 4),
      0xfd: Instruction("SBC", addressing.ABSOLUTE_X, 4),
      0xfe: Instruction("INC", addressing.ABSOLUTE_X, 7)
    }

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
    if address >= 0x8000 and address < 0xc000:
      # PRG_ROM lower bank
      return self._memory['PRG_ROM'][0][address - 0x8000]
    elif address >= 0xc000:
      # PRG_ROM upper bank
      return self._memory['PRG_ROM'][1][address - 0xc000]
  
  def print_rom(self, cart):
    while self.registers['pc'] < cart._prg_rom_size:
      pc = self.registers['pc']
      opcode = ord(cart.read_prg(pc, 1))
      try: 
        inst = self._instruction_set[opcode]
      except KeyError:
        print("Could not find instruction for opcode {0:#2x} at byte {1:#x}.".format(opcode, pc))
        raise

      if inst.addressing == addressing.NONE:
        print("{0}({1:#3x})".format(inst.desc, opcode))
        pc = pc + 1
      elif inst.addressing == addressing.IMMEDIATE:
        val = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) #{2:#3x}".format(inst.desc, opcode, val))
        pc = pc + 2
      elif inst.addressing == addressing.ZEROPAGE:
        # high byte is 0x00.
        address_low = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) {2:#5x}".format(inst.desc, opcode, address_low))
        pc = pc + 2
      elif inst.addressing == addressing.ZEROPAGE_X:
        address = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) {2:#3x}, X".format(inst.desc, opcode, address))
        pc = pc + 2
      elif inst.addressing == addressing.ZEROPAGE_Y:
        address = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) {2:#3x}, Y".format(inst.desc, opcode, address))
        pc = pc + 2
      elif inst.addressing == addressing.ABSOLUTE:
        address_low = ord(cart.read_prg(pc + 1, 1))
        address_high = ord(cart.read_prg(pc + 2, 1))
        address = (address_high << 8) + address_low
        print("{0}({1:#3x}) #{2:#4x}".format(inst.desc, opcode, address))
        pc = pc + 3
      elif inst.addressing == addressing.ABSOLUTE_X:
        address_low = ord(cart.read_prg(pc + 1, 1))
        address_high = ord(cart.read_prg(pc + 2, 2))
        address = (address_high << 8) + address_low
        print("{0}({1:#3x}) {2:#5x}, X".format(inst.desc, opcode, address))
        pc = pc + 3
      elif inst.addressing == addressing.ABSOLUTE_Y:
        address_low = ord(cart.read_prg(pc + 1, 1))
        address_high = ord(cart.read_prg(pc + 2, 2))
        address = (address_high << 8) + address_low
        print("{0}({1:#3x}) {2:#5x}, Y".format(inst.desc, opcode, address))
        pc = pc + 3
      elif inst.addressing == addressing.INDIRECT:
        address_low = ord(cart.read_prg(pc + 1, 1))
        address_high = ord(cart.read_prg(pc + 2, 2))
        address = (address_high << 8) + address_low
        print("{0}({1:#3x}) ({2:#5x})".format(inst.desc, opcode, address))
        pc = pc + 3
      elif inst.addressing == addressing.INDIRECT_X:
        indirect_address = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) ({2:#3x}, X)".format(inst.desc, opcode, indirect_address))
        pc = pc + 2
      elif inst.addressing == addressing.INDIRECT_Y:
        indirect_address = ord(cart.read_prg(pc + 1, 1))
        print("{0}({1:#3x}) ({2:#3x}), Y".format(inst.desc, opcode, indirect_address))
        pc = pc + 2
      elif inst.addressing == addressing.RELATIVE:
        val = ord(cart.read_prg(pc + 1, 1))
        if (val & 128):
          val = (val - 128) * -1
        print("{0}({1:#3x}) {2}".format(inst.desc, opcode, val))
        pc = pc + 2
      elif inst.addressing == addressing.ACCUMULATOR:
        print("{0}({1:#3x})".format(inst.desc, opcode))
        pc = pc + 1
      self.registers['pc'] = pc
  
  def power_on(self):
    self.reset()

  def reset(self):
    if self.cartridge == None:
      raise Exception("System reset with no cartridge loaded.")
    self.cartridge.load_prg(self._memory['PRG_ROM'])
    self.registers['pc'] = (self.mem_read(0xfffd) << 8) + self.mem_read(0xfffc)


class MemoryError(Exception):
  pass

class Instruction(object):
  def __init__(self, desc, addressing, cycles):
    self.desc = desc
    self.addressing = addressing
    self.cycles = cycles

