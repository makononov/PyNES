__author__ = 'misha'

class Memory:
    def __init__(self):
        self._memory = []

    def read(self, address):
        return self._memory[address]

    def write(self, address, value):
        self._memory[address] = value
