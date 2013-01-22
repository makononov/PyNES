import pygame
from pygame.locals import *
from cpu import Cpu
from cartridge import Cartridge
import logging, sys


class Pynes:
  def __init__(self):
    self._running = True
    self._display_surf = None
    self.size = self.width, self.height = 640, 400

  def on_init(self):
    pygame.init()
    self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
    self._running = True
    self.cartridge = Cartridge("../../test/ff.nes")
    self.cpu = Cpu(self.cartridge)
    self.cpu.power_on()

  def on_event(self, event):
    if event.type == pygame.QUIT:
      self._running = False
  
  def on_loop(self):
    self.cpu.tick() 

  def on_render(self):
    pass

  def on_cleanup(self):
    pygame.quit()
  
  def on_execute(self):
    if self.on_init() == False:
      self._running = False

    while( self._running ):
      for event in pygame.event.get():
        self.on_event(event)
      self.on_loop()
      self.on_render()
    self.on_cleanup()

if __name__ == "__main__":
  logging.basicConfig(stream = sys.stderr)
  log = logging.getLogger('PyNES')
  log.setLevel(logging.DEBUG)
  theApp = Pynes()
  theApp.on_execute()
