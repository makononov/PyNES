import logging
import pygame.surfarray as surfarray
log = logging.getLogger("PyNES")

class Ppu(object):
  def __init__(self, surface):
    log.debug('PPU: Initializing PPU...')

    self._surface = surface
    if self._surface.get_width() % 256 != 0 or self._surface.get_height() % 224 != 0:
      raise Exception("Invalid display size.")
    self._width_scalar = self._surface.get_width() / 256
    self._height_scalar = self._surface.get_height() / 224

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
    self.ignore_vram = False 
    self.scanline_sprite_count = 0
    self.sprite_0_hit = False
    self.vblank = False

    self._memory = {}
    self._memory['pattern_tables'] = [0] * 0x2000
    self._memory['name_tables'] = [0] * 0x1000
    self._memory['palettes'] = [0] * 0x20

    self._current_scanline = 0
    self._cycles = 0

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
    self.color = not bool(value & 1)
    self.bg_clipping = bool(value & (1 << 1))
    self.sprite_clipping = bool(value & (1 << 2))
    self.show_background = bool(value & (1 << 3))
    self.show_sprites = bool(value & (1 << 4))

  def status_register(self):
    value = int(self.ignore_vram) << 4
    value += (int(self.scanline_sprite_count > 8) << 5)
    value += (int(self.sprite_0_hit) << 6)
    value += (int(self.vblank) << 7)
    return value

  def vram_write(self, address, value):
    if not self.ignore_vram:
      if address >= 0 and address < 0x2000:
        self._memory['pattern_tables'][address] = value
      elif address >= 0x2000 and address < 0x3000:
        self._memory['name_tables'][address - 0x2000] = value
      elif address >= 0x3000 and address < 0x3f00:
        mirrored_address = address - 0x1000
        self.vram_write(address, value)
      elif address >= 0x3f00 and address < 0x3f20:
        self._memory['palettes'][address - 0x3f00] = value
      elif address >= 0x3f20 and address < 0x4000:
        mirrored_address = address - 0x3f20
        mirrored_address %= 0x20
        self._memory['palettes'][mirrored_address] = value
      elif address >= 0x4000 and address < 0x10000:
        address -= 0x4000
        address %= 0x4000
        self.vram_write(address, value)
      else:
        raise Exception('Unhandled write to VRAM address {0:#4x}'.format(address))

  def vram_read(self, address):
    if address >= 0 and address < 0x2000:
      return self._memory['pattern_tables'][address]
    elif address >= 0x2000 and address < 0x3000:
      return self._memory['name_tables'][address - 0x2000]
    elif address >= 0x3000 and address < 0x3f00:
      mirrored_address = address - 0x1000
      return self.vram_read(address)
    elif address >= 0x3f00 and address < 0x3f20:
      return self._memory['palettes'][address - 0x3f00]
    elif address >= 0x3f20 and address < 0x4000:
      mirrored_address = address - 0x3f20
      mirrored_address %= 0x20
      return self._memory['palettes'][mirrored_address]
    elif address >= 0x4000 and address < 0x10000:
      address -= 0x4000
      address %= 0x4000
      return self.vram_read(address)
    else:
      raise Exception('Unhandled read from VRAM address {0:#4x}'.format(address))

  def tick(self):
    self._cycles += 1

    if self._cycles == 27425:
      # Enter VBLANK
      log.debug("Entering VBLANK...")
      self.vblank = True

    if self._cycles == 29691:
      # End of VBLANK, update screen
      self.vblank = False
      self.update_disp()
      self._cycles = 0

    # log.debug("Scanline {0}".format(self._current_scanline))
    # if (self._busy_cycles > 0):
    #   self._busy_cycles -= 1
    # elif self._current_scanline < 243:
    #   self.vblank = False
    #   if (self._current_scanline < 8 or self._current_scanline > 232):
    #     # Top and bottom scanlines are trimmed.
    #     pass
    #   else:
    #     # background_color = self.vram_read(0x3f00)
    #     background_color = int(random() * 64)
    #     # Draw the current scanline.
    #     pixels = surfarray.pixels2d(self._surface)
    #     #FIXME
    #     pixels[self._current_scanline - 8].fill(background_color)
    #     pixels = None
    #   self._busy_cycles = 113
    #   self._current_scanline += 1
    # else:
    #   # Begin VBLANK
    #   log.debug('Entering VBLANK...')
    #   self.vblank = True
    #   self._busy_cycles = 113 * 20
    #   self._current_scanline = 0

  def update_disp(self):
    pass
