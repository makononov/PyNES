from utils import Enumerate
import numpy
import logging

addressing = Enumerate("NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")
log = logging.getLogger('PyNES')

class Instruction(object):
  def __init__(self, opcode, desc, addressing, cycles):
    self.opcode = opcode
    self.desc = desc
    self.addressing = addressing
    self.cycles = cycles

  def execute(self, cpu, param):
    if (self.desc == "ADC"):
      if (cpu.status['decimal']):
        raise Exception('ADC with BCD not yet implemented.')

      # Add value to accumulator with carry.
      carry = int(cpu.status['carry'])
      tempsum = cpu.get_value(self.addressing, param) + cpu.registers['a'].value() + carry

      if tempsum > 0xff:
        # Carry the 1
        tempsum -= 0x100
        cpu.status['carry'] = True
      else:
        # Clear any carry
        cpu.status['carry'] = False

      cpu.registers['a'].set(tempsum)
        
    elif (self.desc == "AND"):
      val = cpu.get_value(self.addressing, param)
      val &= cpu.registers['a'].value()
      cpu.registers['a'].set(val)
    
    elif (self.desc == "CLD"):
      cpu.status['decimal'] = False

    elif (self.desc == "LDA"):
      cpu.registers['a'].set(cpu.get_value(self.addressing, param))

    elif (self.desc == "LDX"):
      cpu.registers['x'].set(cpu.get_value(self.addressing, param))

    elif (self.desc == "LDY"):
      cpu.registers['y'].set(cpu.get_value(self.addressing, param))

    elif (self.desc == "SEI"):
      cpu.status['irqdis'] = True

    elif (self.desc == "STA"):
      cpu.write_back(self.addressing, param, cpu.registers['a'].value())

    elif (self.desc == "STX"):
      cpu.write_back(self.addressing, param, cpu.registers['x'].value())

    elif (self.desc == "STY"):
      cpu.write_back(self.addressing, param, cpu.registers['y'].value())

    else:
      raise Exception("PC: {0:#4x} - Instruction not implemented: {1}".format(cpu.registers['pc'].value(), self.desc))

  def __unicode__(self):
      if self.addressing == addressing.NONE:
        return "{0}({1:#3x})".format(self.desc, self.opcode)
      if self.addressing == addressing.IMMEDIATE:
        return "{0}({1:#3x}) #".format(self.desc, self.opcode)
      if self.addressing == addressing.ZEROPAGE:
        return "{0}({1:#3x}) 0x00".format(self.desc, self.opcode)
      if self.addressing == addressing.ZEROPAGE_X:
        return "{0}({1:#3x}) 0x00, X".format(self.desc, self.opcode)
      if self.addressing == addressing.ZEROPAGE_Y:
        return "{0}({1:#3x}) 0x00, Y".format(self.desc, self.opcode)
      if self.addressing == addressing.ABSOLUTE:
        return "{0}({1:#3x}) 0x0000".format(self.desc, self.opcode)
      if self.addressing == addressing.ABSOLUTE_X:
        return "{0}({1:#3x}) 0x0000, X".format(self.desc, self.opcode)
      if self.addressing == addressing.ABSOLUTE_Y:
        return "{0}({1:#3x}) 0x0000, Y".format(self.desc, self.opcode)
      if self.addressing == addressing.INDIRECT:
        return "{0}({1:#3x}) (0x0000)".format(self.desc, self.opcode)
      if self.addressing == addressing.INDIRECT_X:
        return "{0}({1:#3x}) (0x00, X)".format(self.desc, self.opcode)
      if self.addressing == addressing.INDIRECT_Y:
        return "{0}({1:#3x}) (0x00), Y".format(self.desc, self.opcode)
      if self.addressing == addressing.RELATIVE:
        return "{0}({1:#3x}) +/-127".format(self.desc, self.opcode)
      if self.addressing == addressing.ACCUMULATOR:
        return "{0}({1:#3x})".format(self.desc, self.opcode)

class Register(object):
  def __init__(self, cpu, dtype = numpy.int8, ignore_overflow = False):
    self._value = 0
    self._cpu = cpu
    self._dt = dtype
    self._ignore_overflow = ignore_overflow
  
  def set(self, value):
    self._value = self._dt(value)
    if not self._ignore_overflow and self._value != value:
      self._cpu.status['overflow'] = True
    if not self._ignore_overflow and self._value == 0:
      self._cpu.status['zero'] = True
    if self._value < 0:
      self._cpu.status['negative'] = True

  def value(self):
    return self._value

  def __add__(self, val):
    return self._value + val

  def __iadd__(self, val):
    self._value = self._dt(self._value + val)
    return self

  def __isub__(self, val):
    return self.__iadd__(-1 * val)


class Cpu(object):
  instruction_set = {
    0x00: Instruction(0x00, "BRK", addressing.NONE, 7),
    0x01: Instruction(0x01, "ORA", addressing.INDIRECT_X, 6),
    0x05: Instruction(0x05, "ORA", addressing.ZEROPAGE, 3),
    0x06: Instruction(0x06, "ASL", addressing.ZEROPAGE, 3),
    0x08: Instruction(0x08, "PHP", addressing.NONE, 3),
    0x09: Instruction(0x09, "ORA", addressing.IMMEDIATE, 2),
    0x0a: Instruction(0x0a, "ASL", addressing.ACCUMULATOR, 2),
    0x0d: Instruction(0x0d, "ORA", addressing.ABSOLUTE, 4),
    0x0e: Instruction(0x0e, "ASL", addressing.ABSOLUTE, 6),
    0x10: Instruction(0x10, "BPL", addressing.RELATIVE, 2),
    0x11: Instruction(0x11, "ORA", addressing.INDIRECT_Y, 5),
    0x15: Instruction(0x15, "ORA", addressing.ZEROPAGE_X, 4),
    0x16: Instruction(0x16, "ASL", addressing.ZEROPAGE_X, 6),
    0x18: Instruction(0x18, "CLC", addressing.NONE, 2),
    0x19: Instruction(0x19, "ORA", addressing.ABSOLUTE_Y, 4),
    0x1d: Instruction(0x1d, "ORA", addressing.ABSOLUTE_X, 4),
    0x1e: Instruction(0x1e, "ASL", addressing.ABSOLUTE_X, 7),

    0x20: Instruction(0x20, "JSR", addressing.ABSOLUTE, 6),
    0x21: Instruction(0x21, "AND", addressing.INDIRECT_X, 6),
    0x24: Instruction(0x24, "BIT", addressing.ZEROPAGE, 3),
    0x25: Instruction(0x25, "AND", addressing.ZEROPAGE, 3),
    0x26: Instruction(0x26, "ROL", addressing.ZEROPAGE, 5),
    0x28: Instruction(0x28, "PLP", addressing.NONE, 4),
    0x29: Instruction(0x29, "AND", addressing.IMMEDIATE, 2),
    0x2a: Instruction(0x2a, "ROL", addressing.ACCUMULATOR, 2),
    0x2c: Instruction(0x2c, "BIT", addressing.ABSOLUTE, 4),
    0x2d: Instruction(0x2d, "AND", addressing.ABSOLUTE, 4),
    0x2e: Instruction(0x2e, "ROL", addressing.ABSOLUTE, 6),
    0x30: Instruction(0x30, "BMI", addressing.RELATIVE, 2),
    0x31: Instruction(0x31, "AND", addressing.INDIRECT_Y, 5),
    0x35: Instruction(0x35, "AND", addressing.ZEROPAGE_X, 6),
    0x36: Instruction(0x36, "ROL", addressing.ZEROPAGE_X, 6),
    0x38: Instruction(0x38, "SEC", addressing.NONE, 2),
    0x39: Instruction(0x39, "AND", addressing.ABSOLUTE_Y, 4),
    0x3d: Instruction(0x3d, "AND", addressing.ABSOLUTE_X, 4),
    0x3e: Instruction(0x3e, "ROL", addressing.ABSOLUTE_X, 7),

    0x40: Instruction(0x40, "RTI", addressing.NONE, 6),
    0x41: Instruction(0x41, "EOR", addressing.INDIRECT_X, 6),
    0x45: Instruction(0x45, "EOR", addressing.ZEROPAGE, 2),
    0x46: Instruction(0x46, "LSR", addressing.ZEROPAGE, 5),
    0x48: Instruction(0x48, "PHA", addressing.NONE, 3),
    0x49: Instruction(0x49, "EOR", addressing.IMMEDIATE, 2),
    0x4a: Instruction(0x4a, "LSR", addressing.ACCUMULATOR, 2),
    0x4c: Instruction(0x4c, "JMP", addressing.ABSOLUTE, 3),
    0x4d: Instruction(0x4d, "EOR", addressing.ABSOLUTE, 4),
    0x4e: Instruction(0x4e, "LSR", addressing.ABSOLUTE, 6),
    0x50: Instruction(0x50, "BVC", addressing.RELATIVE, 2),
    0x51: Instruction(0x51, "EOR", addressing.INDIRECT_Y, 5),
    0x55: Instruction(0x55, "EOR", addressing.ZEROPAGE_X, 4),
    0x56: Instruction(0x56, "LSR", addressing.ZEROPAGE_X, 6),
    0x58: Instruction(0x58, "CLI", addressing.NONE, 2),
    0x59: Instruction(0x59, "EOR", addressing.ABSOLUTE_Y, 4),
    0x5d: Instruction(0x5d, "EOR", addressing.ABSOLUTE_X, 4),
    0x5e: Instruction(0x5e, "LSR", addressing.ABSOLUTE_X, 7),

    0x60: Instruction(0x60, "RTS", addressing.NONE, 6),
    0x61: Instruction(0x61, "ADC", addressing.INDIRECT_X, 6),
    0x65: Instruction(0x65, "ADC", addressing.ZEROPAGE, 3),
    0x66: Instruction(0x66, "ROR", addressing.ZEROPAGE, 5),
    0x68: Instruction(0x68, "PLA", addressing.NONE, 4),
    0x69: Instruction(0x69, "ADC", addressing.IMMEDIATE, 2),
    0x6a: Instruction(0x6a, "ROR", addressing.ACCUMULATOR, 2),
    0x6c: Instruction(0x6c, "JMP", addressing.INDIRECT, 5),
    0x6d: Instruction(0x6d, "ADC", addressing.ABSOLUTE, 4),
    0x6e: Instruction(0x6e, "ROR", addressing.ABSOLUTE, 6),
    0x70: Instruction(0x70, "BVS", addressing.RELATIVE, 2),
    0x71: Instruction(0x71, "ADC", addressing.INDIRECT_Y, 5),
    0x75: Instruction(0x75, "ADC", addressing.ZEROPAGE_X, 4),
    0x76: Instruction(0x76, "ROR", addressing.ZEROPAGE_X, 6),
    0x78: Instruction(0x78, "SEI", addressing.NONE, 2),
    0x79: Instruction(0x79, "ADC", addressing.ABSOLUTE_Y, 4),
    0x7d: Instruction(0x7d, "ADC", addressing.ABSOLUTE_X, 4),
    0x7e: Instruction(0x7e, "ROR", addressing.ABSOLUTE_X, 7),

    0x81: Instruction(0x81, "STA", addressing.INDIRECT_X, 6),
    0x84: Instruction(0x84, "STY", addressing.ZEROPAGE, 3),
    0x85: Instruction(0x85, "STA", addressing.ZEROPAGE, 3),
    0x86: Instruction(0x86, "STX", addressing.ZEROPAGE, 3),
    0x88: Instruction(0x88, "DEY", addressing.NONE, 2),
    0x8a: Instruction(0x8a, "TXA", addressing.NONE, 2),
    0x8c: Instruction(0x8c, "STY", addressing.ABSOLUTE, 4),
    0x8d: Instruction(0x8d, "STA", addressing.ABSOLUTE, 4),
    0x8e: Instruction(0x8e, "STX", addressing.ABSOLUTE, 4),
    0x90: Instruction(0x90, "BCC", addressing.NONE, 2),
    0x91: Instruction(0x91, "STA", addressing.INDIRECT_Y, 6),
    0x94: Instruction(0x94, "STY", addressing.ZEROPAGE_X, 4),
    0x95: Instruction(0x95, "STA", addressing.ZEROPAGE_X, 4),
    0x96: Instruction(0x96, "STX", addressing.ZEROPAGE_Y, 4),
    0x98: Instruction(0x98, "TYA", addressing.NONE, 2),
    0x99: Instruction(0x99, "STA", addressing.ABSOLUTE_Y, 5),
    0x9a: Instruction(0x9a, "TXS", addressing.NONE, 2),
    0x9d: Instruction(0x9d, "STA", addressing.ABSOLUTE_X, 5),

    0xa0: Instruction(0xa0, "LDY", addressing.IMMEDIATE, 2),
    0xa1: Instruction(0xa1, "LDA", addressing.INDIRECT_X, 6),
    0xa2: Instruction(0xa2, "LDX", addressing.IMMEDIATE, 2),
    0xa4: Instruction(0xa4, "LDY", addressing.ZEROPAGE, 3),
    0xa5: Instruction(0xa5, "LDA", addressing.ZEROPAGE, 3),
    0xa6: Instruction(0xa6, "LDX", addressing.ZEROPAGE, 3),
    0xa8: Instruction(0xa8, "TAY", addressing.NONE, 2),
    0xa9: Instruction(0xa9, "LDA", addressing.IMMEDIATE, 2),
    0xaa: Instruction(0xaa, "TAX", addressing.NONE, 2),
    0xac: Instruction(0xac, "LDY", addressing.ABSOLUTE, 4),
    0xad: Instruction(0xad, "LDA", addressing.ABSOLUTE, 4),
    0xae: Instruction(0xae, "LDX", addressing.ABSOLUTE, 4),
    0xb0: Instruction(0xb0, "BCS", addressing.RELATIVE, 2),
    0xb1: Instruction(0xb1, "LDA", addressing.INDIRECT_Y, 5), 
    0xb4: Instruction(0xb4, "LDY", addressing.ZEROPAGE_X, 4),
    0xb5: Instruction(0xb5, "LDA", addressing.ZEROPAGE_X, 4),
    0xb6: Instruction(0xb6, "LDX", addressing.ZEROPAGE_Y, 4),
    0xb8: Instruction(0xb8, "CLV", addressing.NONE, 2),
    0xb9: Instruction(0xb9, "LDA", addressing.ABSOLUTE_Y, 4),
    0xba: Instruction(0xba, "TSX", addressing.NONE, 2),
    0xbc: Instruction(0xbc, "LDY", addressing.ABSOLUTE_X, 4),
    0xbd: Instruction(0xbd, "LDA", addressing.ABSOLUTE_X, 4),
    0xbe: Instruction(0xbe, "LDX", addressing.ABSOLUTE_Y, 4),

    0xc0: Instruction(0xc0, "CPY", addressing.IMMEDIATE, 2),
    0xc1: Instruction(0xc1, "CMP", addressing.INDIRECT_X, 6),
    0xc4: Instruction(0xc4, "CPY", addressing.ZEROPAGE, 3),
    0xc5: Instruction(0xc5, "CMP", addressing.ZEROPAGE, 3),
    0xc6: Instruction(0xc6, "DEC", addressing.ZEROPAGE, 5),
    0xc8: Instruction(0xc8, "INY", addressing.NONE, 2),
    0xc9: Instruction(0xc9, "CMP", addressing.IMMEDIATE, 2),
    0xca: Instruction(0xca, "DEX", addressing.NONE, 2),
    0xcc: Instruction(0xcc, "CPY", addressing.ABSOLUTE, 4),
    0xcd: Instruction(0xcd, "CMP", addressing.ABSOLUTE, 4),
    0xce: Instruction(0xce, "DEC", addressing.ABSOLUTE, 6),
    0xd0: Instruction(0xd0, "BNE", addressing.RELATIVE, 2),
    0xd1: Instruction(0xd1, "CMP", addressing.INDIRECT_Y, 5),
    0xd5: Instruction(0xd5, "CMP", addressing.ZEROPAGE_X, 4),
    0xd6: Instruction(0xd6, "DEC", addressing.ZEROPAGE_X, 6),
    0xd8: Instruction(0xd8, "CLD", addressing.NONE, 2),
    0xd9: Instruction(0xd9, "CMP", addressing.ABSOLUTE_Y, 4),
    0xdd: Instruction(0xdd, "CMP", addressing.ABSOLUTE_X, 4),
    0xde: Instruction(0xde, "DEC", addressing.ABSOLUTE_X, 7),

    0xe0: Instruction(0xe0, "CPX", addressing.IMMEDIATE, 2),
    0xe1: Instruction(0xe1, "SBC", addressing.INDIRECT_X, 6),
    0xe4: Instruction(0xe4, "CPX", addressing.ZEROPAGE, 3),
    0xe5: Instruction(0xe5, "SBC", addressing.ZEROPAGE, 3),
    0xe6: Instruction(0xe6, "INC", addressing.ZEROPAGE, 5),
    0xe8: Instruction(0xe8, "INX", addressing.NONE, 2),
    0xe9: Instruction(0xe9, "SBC", addressing.IMMEDIATE, 2),
    0xea: Instruction(0xea, "NOP", addressing.NONE, 2),
    0xec: Instruction(0xec, "CPX", addressing.ABSOLUTE, 4),
    0xed: Instruction(0xed, "SBC", addressing.ABSOLUTE, 4),
    0xee: Instruction(0xee, "INC", addressing.ABSOLUTE, 6),
    0xf0: Instruction(0xf0, "BEQ", addressing.RELATIVE, 2),
    0xf1: Instruction(0xf1, "SBC", addressing.INDIRECT_Y, 5),
    0xf5: Instruction(0xf5, "SBC", addressing.ZEROPAGE_X, 4),
    0xf6: Instruction(0xf6, "INC", addressing.ZEROPAGE_X, 6),
    0xf8: Instruction(0xf8, "SED", addressing.NONE, 2),
    0xf9: Instruction(0xf9, "SBC", addressing.ABSOLUTE_Y, 4),
    0xfd: Instruction(0xfd, "SBC", addressing.ABSOLUTE_X, 4),
    0xfe: Instruction(0xfe, "INC", addressing.ABSOLUTE_X, 7)
  }

  def __init__(self, cartridge = None):
    log.debug("Initializing CPU")
    self.cartridge = cartridge 
    self.busy_cycles = 0

    self._memory = {}
    self._memory['RAM'] = [0xff] * 0x800 # 0x0000 - 0x07ff
    self._memory['expansion_rom'] = [0xff] * 0x1fe0 # 0x4020 - 0x5fff
    self._memory['SRAM'] = [0xff] * 0x2000 # 0x6000 - 0x7fff
    self._memory['PRG_ROM'] = [[], []] # 0x8000 - 0xbfff, 0xc000 - 0xffff, uninitialized since it is filled by the cartridge.

    self.registers = {'pc': Register(self, numpy.uint16), 'a': Register(self), 'x': Register(self), 'y': Register(self), 'sp': Register(self, numpy.uint8, True)}
    self.status = {'carry': False, 'zero': False, 'irqdis': True, 'decimal': False, 'brk': True, 'overflow': False, 'negative': False}


  def mem_write(self, address, value):
    if address < 0 or address >= 0x10000:
      raise Exception('Memory write out of bounds: {0x:#4x}'.format(address))

    # RAM is mirrored 4x, so get the base address before writing to the RAM array.
    if (address < 0x2000):
      base_address = address % 0x800
      self._memory['RAM'] = value

    if address >= 0x2000 and address < 0x4000:
      # TODO
      pass

    else:
      self._memory[address] = value

  def mem_read(self, address):
    if address < 0 or address >= 0x10000:
      raise Exception('Memory read out of bounds: {0:#4x}'.format(address))
    
    # RAM is mirrored 4x, so get the base address before returning the value from the RAM array.
    if address < 0x2000:
      base_address = address % 0x800
      return self._memory['RAM'][address]

    if address >= 0x8000 and address < 0xc000:
      # PRG_ROM lower bank
      return self._memory['PRG_ROM'][0][address - 0x8000]
    elif address >= 0xc000:
      # PRG_ROM upper bank
      return self._memory['PRG_ROM'][1][address - 0xc000]
  
  
  def power_on(self):
    self.reset()

  def reset(self):
    if self.cartridge == None:
      raise Exception("System reset with no cartridge loaded.")
    self.cartridge.load_prg(self._memory['PRG_ROM'])
    self.registers['pc'].set((self.mem_read(0xfffd) << 8) + self.mem_read(0xfffc))
    log.debug("PC initialized to {0:#4x}".format(self.registers['pc'].value()))

  def tick(self):
    if (self.busy_cycles == 0):
      # ready for the next instruction.
      opcode = self.mem_read(self.registers['pc'].value())
      param = None
      instruction_length = 1
      try:
        if Cpu.instruction_set[opcode].addressing in (addressing.IMMEDIATE, addressing.ZEROPAGE, addressing.ZEROPAGE_X, addressing.ZEROPAGE_Y, addressing.INDIRECT_X, addressing.INDIRECT_Y, addressing.RELATIVE):
          param = self.mem_read(self.registers['pc'].value() + 1)
          instruction_length = 2
        elif Cpu.instruction_set[opcode].addressing in (addressing.INDIRECT, addressing.ABSOLUTE, addressing.ABSOLUTE_X, addressing.ABSOLUTE_Y):
          param = self.mem_read(self.registers['pc'].value() + 1)
          param += (self.mem_read(self.registers['pc'].value() + 2) << 8)
          instruction_length = 3
      except KeyError:
        log.debug("Invalid opcode: {0:#2x}".format(opcode))
      self.registers['pc'] += instruction_length
      self.busy_cycles += Cpu.instruction_set[opcode].cycles
      Cpu.instruction_set[opcode].execute(self, param)
    else:
      self.busy_cycles = self.busy_cycles - 1

  def get_value(self, addmode, param):
    if (addmode == addressing.IMMEDIATE):
      return param
    elif (addmode == addressing.ZEROPAGE):
      return self.mem_read(param)
    elif (addmode == addressing.ZEROPAGE_X):
      address = param + self.registers['x'].value()
      # Wrap address so that it is always on the zero page.
      if address > 0xff:
        address -= 0x100
      return self.mem_read(address)
    elif (addmode == addressing.ZEROPAGE_Y):
      address = param + self.registers['y'].value()
      # Wrap address so that it is always on the zero page.
      if address > 0xff:
        address -= 0x100
      return self.mem_read(address)
    elif (addmode == addressing.ABSOLUTE):
      return self.mem_read(param)
    elif (addmode == addressing.ABSOLUTE_X):
      return self.mem_read(param + self.registers['x'].value())
    elif (addmode == addressing.ABSOLUTE_Y):
      return self.mem_read(param + self.registers['y'].value())
    elif (addmode == addressing.INDIRECT_X):
      indirect_address = param + self.registers['x'].value()
      address = self.mem_read(indirect_address)
      address += (self.mem_read(indirect_address + 1) << 8)
      return self.mem_read(address)
    elif (addmode == addressing.INDIRECT_Y):
      address = self.mem_read(param)
      address += (self.mem_read(param + 1) << 8)
      return self.mem_read(address + self.registers['y'].value())

  def write_back(self, addmode, address, value):
    if addmode in (addressing.ZEROPAGE, addressing.ABSOLUTE):
      self.mem_write(address, value)
    elif addmode in (addressing.ZEROPAGE_X, addressing.ABSOLUTE_X):
      self.mem_write(self.registers['x'].value() + address, value)
    elif addmode in (addressing.ZEROPAGE_Y, addressing.ABSOLUTE_Y):
      self.mem_write(self.registers['y'].value() + address, value)
    elif addmode == addressing.INDIRECT_X:
      indirect_address = address + self.registers['x'].value()
      address = self.mem_read(indirect_address)
      address += (self.mem_read(indirect_address + 1) << 8)
      self.mem_write(address, value)
    elif addmode == addressing.INDIRECT_Y:
      address = self.mem_read(address)
      address += (self.mem_rest(address + 1) << 8)
      self.mem_write(address + self.registers['y'].value(), value)
    else:
      raise Exception("Write back not implemented for addressing mode {0}.".format(addressing))


