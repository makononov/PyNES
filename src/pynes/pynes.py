#!/usr/bin/env python
"""
PyNES - A Nintendo Entertainment System emulator written in Python
"""

import argparse
import logging
import pyglet
from cartridge import Cartridge
from console import Console
from utils import ColorFormatter

__author__ = "Misha Kononov"
__copyright__ = "Copyright 2013, Misha Kononov"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Misha Kononov"
__email__ = "misha@mishakononov.com"
__status__ = "Development"


window = pyglet.window.Window(visible=False)
console = None


def init():
    FORMAT = "[$BOLD%(name)s$RESET][%(levelname)-8s]  $COLOR%(message)s$RESET ($BOLD%(filename)s$RESET:%(lineno)d)"
    shandler = logging.StreamHandler()
    shandler.setFormatter(ColorFormatter(FORMAT))
    log = logging.getLogger('PyNES')
    log.addHandler(shandler)
    log.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(description="Parse command line options for PyNES")
    parser.add_argument('romfile', metavar="filename", type=str, help="The ROM file to load")
    args = parser.parse_args()

    window.set_size(512, 448)

    cartridge = Cartridge(args.romfile)
    console = Console(cartridge)
    console.boot()

    window.set_visible(True)


@window.event
def on_draw():
    window.clear()

if __name__ == "__main__":
    init()
    pyglet.app.run()
