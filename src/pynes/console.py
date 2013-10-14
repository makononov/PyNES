__author__ = 'misha'

from cpu import CPU
from ppu import PPU

class Console:
    def __init__(self, cart):
        self.Cart = cart
        self.CPU = CPU(self)
        self.PPU = PPU(self)

    def boot(self):
        self.CPU.start()
        self.PPU.start()
