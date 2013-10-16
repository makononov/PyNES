"""
Relative addressing for branch instructions
"""
import numpy as np

size = 1


def read(cpu, param):
    return np.int8(param)


def print(param):
    return np.int8(param)