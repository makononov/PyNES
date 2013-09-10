from cpu import CPU
import multiprocessing

__author__ = 'misha'


class Console:
    def __init__(self, cart):
        self.Cart = cart
        self.CPU = CPU(self)

    def boot(self):
        self.CPU.start()
