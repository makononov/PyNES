import numpy
import logging
from ppu import Ppu
from cpu import InstructionSet
from utils import Enumerate

log = logging.getLogger('PyNES')
addressing = Enumerate("NONE IMMEDIATE ZEROPAGE ZEROPAGE_X ZEROPAGE_Y ABSOLUTE ABSOLUTE_X ABSOLUTE_Y INDIRECT INDIRECT_X INDIRECT_Y RELATIVE ACCUMULATOR")

class Cpu(object):
  def __init__(self, ppu, papu, cartridge = None, controller1 = None, controller2 = None):
    log.debug("Initializing CPU")
    self.cartridge = cartridge 
    self.cartridge.cpu = self

    self.controller1 = controller1
    self.controller2 = controller2

    self._instruction_set = InstructionSet(self)
    self.busy_cycles = 0

    self._ppu = ppu
    self._papu = papu

    self._memory = {}
    self._memory['RAM'] = [0xff] * 0x800 # 0x0000 - 0x07ff
    self._memory['expansion_rom'] = [0xff] * 0x1fe0 # 0x4020 - 0x5fff
    self._memory['SRAM'] = [0xff] * 0x2000 # 0x6000 - 0x7fff

    self.registers = {'pc': numpy.uint16(), 'a': numpy.int8(), 'x': numpy.uint8(), 'y': numpy.uint8(), 'sp': numpy.uint8()}
    self.status = {'carry': False, 'zero': False, 'irqdis': True, 'decimal': False, 'brk': True, 'overflow': False, 'negative': False}

  # Write a value to a memory location (or a mapped register)
  def mem_write(self, address, value):
    if address < 0 or address >= 0x10000:
      raise Exception('Memory write out of bounds: {0x:#4x}'.format(address))

    # RAM is mirrored 4x, so get the base address before writing to the RAM array.
    if (address < 0x2000):
      base_address = address % 0x800
      # log.debug("WRITE to RAM address {0:#x}".format(base_address))
      self._memory['RAM'][base_address] = value

    # PPU I/O registers
    elif address >= 0x2000 and address < 0x4000:
      self._ppu.mem_write(address, value)
    
    # pAPU I/O registers
    elif (address >= 0x4000 and address < 0x4014) or address == 0x4015:
      self._papu.register_write(address, value)

    # DMA Sprite Transfer
    elif address == 0x4014:
      raise Exception("DMA Sprite Transfer not implemented.")

    elif address == 0x4016:
      if self.controller1 != None:
        self.controller1.toggle_strobe(bool(value & 1))
    
    elif address == 0x4017:
      if self.controller2 != None:
        self.controller2.toggle_strobe(bool(value & 1))

    elif address >= 0x6000 and address < 0x8000:
      self._memory['SRAM'][address - 0x6000] = value
    
    elif address >= 0x8000 and address < 0x10000:
      self.cartridge.mapper.mem_write(address, value)

    else:
      raise Exception("Unhandled memory write to address {0:#4x} at {1:#4x}".format(address, self.registers['pc']))

  def mem_read(self, address):
    if address < 0 or address >= 0x10000:
      raise Exception('Memory read out of bounds: {0:#4x}'.format(address))
    
    # RAM is mirrored 4x, so get the base address before returning the value from the RAM array.
    if address < 0x2000:
      base_address = address % 0x800
      # log.debug("Read from RAM address {0:#x}".format(base_address))
      return self._memory['RAM'][address]
    
    elif address >= 0x2000 and address < 0x4000:
      address -= 0x2000
      base = address % 8
      if base == 2:
        return self._ppu.status_register()
      else:
        raise Exception('Unhandled I/O register read at {0:#4x}'.format(self.registers['pc']))

    elif address >= 0x6000 and address < 0x8000:
      return self._memory['SRAM'][address - 0x6000]

    elif address >= 0x8000:
      return self.cartridge.prg_rom[address - 0x8000]

    else:
      raise Exception('Unhandled memory read at {0:#4x}'.format(self.registers['pc']))
  
  def power_on(self):
    self.reset()

  def reset(self):
    if self.cartridge == None:
      raise Exception("System reset with no cartridge loaded.")
    self.registers['pc'] = (self.mem_read(0xfffd) << 8) + self.mem_read(0xfffc)
    log.debug("PC initialized to {0:#4x}".format(self.registers['pc']))

  def tick(self):
    if (self.busy_cycles == 0):
      # ready for the next instruction.
      opcode = self.mem_read(self.registers['pc'])
      self.registers['pc'] += 1
      param = 0
      for i in range(0, self._instruction_set[opcode].param_length):
        param += (self.mem_read(self.registers['pc'] + i) << (8 * i))

      self.busy_cycles += self._instruction_set[opcode].cycles
      self.registers['pc'] += self._instruction_set[opcode].param_length
      self._instruction_set[opcode].execute(param)
    else:
      self.busy_cycles = self.busy_cycles - 1

  def get_value(self, addmode, param):
    if (addmode == addressing.IMMEDIATE):
      return param
    elif (addmode == addressing.ZEROPAGE):
      return self.mem_read(param)
    elif (addmode == addressing.ZEROPAGE_X):
      address = numpy.uint8(param + self.registers['x'])
      return self.mem_read(address)
    elif (addmode == addressing.ZEROPAGE_Y):
      address = numpy.uint8(param + self.registers['y'])
      return self.mem_read(address)
    elif (addmode == addressing.ABSOLUTE):
      return self.mem_read(param)
    elif (addmode == addressing.ABSOLUTE_X):
      return self.mem_read(param + self.registers['x'])
    elif (addmode == addressing.ABSOLUTE_Y):
      return self.mem_read(param + self.registers['y'])
    elif (addmode == addressing.INDIRECT_X):
      indirect_address = param + self.registers['x']
      address = self.mem_read(indirect_address)
      address += (self.mem_read(indirect_address + 1) << 8)
      return self.mem_read(address)
    elif (addmode == addressing.INDIRECT_Y):
      address = self.mem_read(param)
      address += (self.mem_read(param + 1) << 8)
      return self.mem_read(address + self.registers['y'])
    elif (addmode == addressing.ACCUMULATOR):
      return self.registers['a']
    else:
      raise Exception("get_value called for unsupported addressing mode {0}.".format(addmode))

  def write_back(self, addmode, address, value):
    if addmode in (addressing.ZEROPAGE, addressing.ABSOLUTE):
      self.mem_write(address, value)
    elif addmode in (addressing.ZEROPAGE_X, addressing.ABSOLUTE_X):
      self.mem_write(self.registers['x'] + address, value)
    elif addmode in (addressing.ZEROPAGE_Y, addressing.ABSOLUTE_Y):
      self.mem_write(self.registers['y'] + address, value)
    elif addmode == addressing.INDIRECT_X:
      indirect_address = address + self.registers['x']
      address = self.mem_read(indirect_address)
      address += (self.mem_read(indirect_address + 1) << 8)
      self.mem_write(address, value)
    elif addmode == addressing.INDIRECT_Y:
      address = self.mem_read(address)
      address += (self.mem_rest(address + 1) << 8)
      self.mem_write(address + self.registers['y'], value)
    elif addmode == addressing.ACCUMULATOR:
      self.registers['a'] = numpy.int8(value)
    else:
      raise Exception("Write back not implemented for addressing mode {0}.".format(addmode))

  def set_zero(self, value):
    self.status['zero'] = (value == 0)

  def set_negative(self, value):
    self.status['negative'] = (numpy.int8(value) < 0) 
  
  def get_status_register(self):
    value = int(self.status['carry'])
    value += int(self.status['zero']) << 1
    value += int(self.status['irqdis']) << 2
    value += int(self.status['decimal']) << 3
    value += int(self.status['brk']) << 4
    value += 1 << 5
    value += int(self.status['overflow']) << 6
    value += int(self.status['negative']) << 7
    return value
  
  def set_status_register(self, value):
    self.status['carry'] = bool(value & (1))
    self.status['zero'] = bool(value & (1 << 1))
    self.status['irqdis'] = bool(value & (1 << 2))
    self.status['decimal'] = bool(value & (1 << 3))
    self.status['brk'] = bool(value & (1 << 4))
    self.status['overflow'] = bool(value & (1 << 6))
    self.status['negative'] = bool(value & (1 << 7))

  def stack_push(self, value):
    self.registers['sp'] -= 1
    self.mem_write(0x100 + self.registers['sp'], value)

  def stack_pop(self):
    val = self.mem_read(0x100 + self.registers['sp'])
    self.registers['sp'] += 1
    return val

  def interrupt(self, int_type):
    pc = self.registers['pc'] - 1
    self.stack_push((pc >> 8) & 0xff)
    self.stack_push(pc & 0xff)
    self.stack_push(self.get_status_register())

    if int_type == 'NMI':
      self.registers['pc'] = (self.mem_read(0xfffb) << 8) + self.mem_read(0xfffa)      
    elif int_type == 'IRQ':
      self.registers['pc'] = (self.mem_read(0xffff) << 8) + self.mem_read(0xfffe)
    else:
      raise Exception("Unhandled interrupt type {0}.".format(int_type))
    
