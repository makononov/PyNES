import logging
log = logging.getLogger("PyNES")

class Ppu(object):
  def __init__:
    log.debug('PPU: Initializing PPU...')
    self.name_table_address = 0x2000
    self.address_increment = 1
    self.sprite_pattern_table = 0x0000
    self.background_pattern_table = 0x0000
    self.sprite_size = 8
    self.NMI = False
    self.color = True
    self.bg_clipping = False
    self.sprite_clipping = False
    self.show_background = False
    self.show_sprites = False
    self.color_intensity = 0

  def update_control_1(self, value):
    log.debug('PPU: Updating control register 1 to {0:b}'.format(value))
    self.name_table_address = 0x2000 + (0x400 * (value & 0b11)) # bits 0-1 

    if (value & (1 << 2)):
      self.address_increment = 32
    else:
      self.address_increment = 1

    if (value & (1 << 3)):
      self.sprite_pattern_table = 0x1000
    else:
      self.sprite_pattern_table = 0x0000

    if (value & (1 << 4)):
      self.background_pattern_table = 0x1000
    else:
      self.backgroun_pattern_table = 0x0000

    if (value & (1 << 5)):
      self.sprite_size = 16
    else:
      self.sprite_size = 8

    if (value & (1 << 7)):
      self.NMI = True
    else:
      self.NMI = False
    
  def update_control_2(self, value):
    log.debug('PPU: Updating control register 2 to {0:b}'.format(value))
    self.color = bool(value & 1)
    self.bg_clipping = bool(value & (1 << 1))
    self.sprite_clipping = bool(value & (1 << 2))
    self.show_background = bool(value & (1 << 3))
    self.show_sprites = bool(value & (1 << 4))

