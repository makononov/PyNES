import logging
import numpy
from utils import Enumerate

addressing = Enumerate("NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")
log = logging.getLogger("PyNES")

class Instruction(object):
  def __init__(self, opcode, desc, addmode, cycles):
    self.opcode = opcode
    self.desc = desc
    self.addressing = addmode
    self.cycles = cycles
    if addmode in (addressing.IMMEDIATE, addressing.ZEROPAGE, addressing.ZEROPAGE_X, addressing.ZEROPAGE_Y, addressing.INDIRECT_X, 
                      addressing.INDIRECT_Y, addressing.RELATIVE):
      self.param_length = 1
    elif addmode in (addressing.ABSOLUTE, addressing.ABSOLUTE_X, addressing.ABSOLUTE_Y, addressing.INDIRECT):
      self.param_length = 2
    else:
      self.param_length = 0

  def execute(self, param):
    log.debug("Executing {0}({1:#2x}) at PC {2:#4x}".format(self.desc, self.opcode, self.cpu.registers['pc']))
    try:
      method = getattr(self, self.desc)
    except AttributeError:
      print("Invalid instruction {0}.".format(self.desc))
      raise
    if self.param_length > 0:
      method(param)
    else:
      method()

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

  ###################
  ##  Individual instruction execution logic
  ###################

  # Add value to A with carry.
  def ADC(self, param):
    carry = int(self.cpu.status['carry'])
    src = self.cpu.get_value(self.addressing, param)
    tempsum = src + self.cpu.registers['a'] + carry
    set_zero(tempsum & 0xff)
    if (self.cpu.status['decimal']):
      if (self.cpu.registers['a'] & 0xf) + (src & 0xf) + carry > 9:
        tempsum += 6
      if tempsum > 0x99:
        tempsum += 96
      self.cpu.status['carry'] = (tempsum > 0x99)
    else:
      self.cpu.status['carry'] = (tempsum > 0xff)

    self.cpu.registers['a'] = tempsum
    self.cpu.set_zero(tempsum)
    self.cpu.set_negative(tempsum)
    self.cpu.status['overflow'] = (tempsum != self.cpu.registers['a'])
        
  # And value with A
  def AND(self, param):
    val = self.cpu.get_value(self.addressing, param)
    val &= self.cpu.registers['a']
    self.cpu.registers['a'] = val

  # Compare bits
  def BIT(self, param):
    src = self.cpu.get_value(self.addressing, param)
    self.cpu.set_negative(src)
    self.cpu.status['overflow'] = (src & 0x40)
    self.cpu.set_zero(src & self.cpu.registers['a'])

  
  # Branch if result not zero
  def BNE(self, param):
    if not self.cpu.status['zero']:
      offset = numpy.int8(param)
      pc = self.cpu.registers['pc']
      # Add an extra CPU cycle if going across pages.
      if (pc & 0xff00) != (pc + offset & 0xff00):
        self.cpu.busy_cycles += 1
      self.cpu.registers['pc'] += offset

  # Branch on a positive result
  def BPL(self, param): 
    if not self.cpu.status['negative']:
      offset = numpy.int8(param)
      pc = self.cpu.registers['pc']
      # Add an extra CPU cycle if going across pages.
      if (pc & 0xff00) != (pc + offset & 0xff00):
        self.cpu.busy_cycles += 1
      self.cpu.registers['pc'] += offset
    
  # Clear BCD status flag
  def CLD(self):
    self.cpu.status['decimal'] = False

  def CMP(self, param):
    #TODO
    pass

  # Decrement X
  def DEX(self):
    self.cpu.registers['x'] -= 1
    self.cpu.set_zero(self.cpu.registers['x'])
    self.cpu.set_negative(self.cpu.registers['x'])

  # Decrement Y
  def DEY(self):
    self.cpu.registers['y'] -= 1
    self.cpu.set_zero(self.cpu.registers['y'])
    self.cpu.set_negative(self.cpu.registers['y'])

  # Increment X
  def INX(self):
    src = numpy.uint8(self.cpu.registers['x'])
    src = numpy.uint8(src + 1)
    self.cpu.set_negative(src)
    self.cpu.set_zero(src)
    self.cpu.registers['x'] = src

  # Increment Y
  def INY(self):
    src = numpy.uint8(self.cpu.registers['y'])
    src = numpy.uint8(src + 1)
    self.cpu.set_negative(src)
    self.cpu.set_zero(src)
    self.cpu.registers['y'] = src

  # Jump to a new location
  def JMP(self, param):
    self.cpu.registers['pc'] = param

  # Jump and save return address
  def JSR(self, param):
    pc = self.cpu.registers['pc'] - 1
    self.cpu.stack_push((pc >> 8) & 0xff)
    self.cpu.stack_push(pc & 0xff)
    self.cpu.registers['pc'] = param

  # Load value into A
  def LDA(self, param):
    self.cpu.registers['a'] = self.cpu.get_value(self.addressing, param)

  # Load value into X
  def LDX(self, param):
    self.cpu.registers['x'] = self.cpu.get_value(self.addressing, param)

  # Load value into Y
  def LDY(self, param):
    self.cpu.registers['y'] = self.cpu.get_value(self.addressing, param)

  # Shift value right one bit
  def LSR(self, param = None):
    value = self.cpu.get_value(self.addressing, param)
    self.cpu.status['carry'] = bool(value & 1)
    value >>= 1
    self.cpu.set_negative(0)
    self.cpu.set_zero(value)
    self.cpu.write_back(self.addressing, param, value)
    
  # Return to location on stack after a JSR
  def RTS(self):
    pc = self.cpu.stack_pop()
    pc += (self.cpu.stack_pop() << 8) + 1
    self.cpu.registers['pc'] = pc

  # Set the interrupt disable flag.
  def SEI(self):
    self.cpu.status['irqdis'] = True

  # Store A in memory
  def STA(self, param):
    self.cpu.write_back(self.addressing, param, self.cpu.registers['a'])

  # Store X in memory
  def STX(self, param):
    self.cpu.write_back(self.addressing, param, self.cpu.registers['x'])

  # Store Y in memory
  def STY(self, param):
    self.cpu.write_back(self.addressing, param, self.cpu.registers['y'])

  # Transfer the value in X to SP
  def TXS(self):
    sp = numpy.uint8(self.cpu.registers['x'])
    self.cpu.registers['sp'] = sp


class InstructionSet(object):
  __instructions = {
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

  def __init__(self, cpu):
    for opcode, inst in InstructionSet.__instructions.items():
      inst.cpu = cpu

  def __getitem__(self, key):
    if type(key) == int:
      try:
        return InstructionSet.__instructions[key]
      except KeyError:
        raise Exception("Invalid Opcode {0:#2x}".format(key))
    else:
      for i in InstructionSet.__instructions:
        if i.desc == key:
          return i
      raise Exception("Invalid instruction {0}".format(key))
