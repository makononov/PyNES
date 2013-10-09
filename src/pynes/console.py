__author__ = 'misha'

from cpu import CPU


class Console:
    def __init__(self, cart):
        self.Cart = cart
        self.CPU = CPU(self)

    def boot(self):
        self.CPU.start()
