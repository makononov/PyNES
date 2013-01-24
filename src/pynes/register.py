import numpy

class Register(object):
  def __init__(self, dtype = numpy.int8):
    self._value = 0
    self._dt = dtype
    self.overflow = False
  
  def set(self, value):
    self._value = self._dt(value)
    self.overflow = (value != self._value) 
  def value(self):
    return self._value

  def __add__(self, val):
    return self._value + val

  def __iadd__(self, val):
    self._value = self._dt(self._value + val)
    return self

  def __isub__(self, val):
    return self.__iadd__(-1 * val)

