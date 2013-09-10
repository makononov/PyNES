from setuptools import setup

setup(name='PyNES',
      version='0.1',
      description='A NES emulator',
      url='http://github.com/makononov/pynes',
      author='Misha Kononov',
      author_email='misha@mishakononov.com',
      license='MIT',
      packages=['pynes'],
      zip_safe=False, requires=['pyglet', 'numpy'])
