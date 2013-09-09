from pynes.cpu import CPU
import multiprocessing

__author__ = 'misha'


class Console:
    def __init__(self, cart):
        self.cycle_count = multiprocessing.Value("I")
        self.Cart = cart
        self.CPU = CPU(self.Cart, self.cycle_count)

    def boot(self):
        self.CPU.start()
