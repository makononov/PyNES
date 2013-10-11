import pyglet
from cartridge import Cartridge
from console import Console
import logging
from utils import ColorFormatter
import sys

window = pyglet.window.Window(visible=False)
console = None


def init():
    FORMAT = "[$BOLD%(name)s$RESET][%(levelname)-8s]  $COLOR%(message)s$RESET ($BOLD%(filename)s$RESET:%(lineno)d)"
    shandler = logging.StreamHandler()
    shandler.setFormatter(ColorFormatter(FORMAT))
    log = logging.getLogger('PyNES')
    log.addHandler(shandler)
    log.setLevel(logging.DEBUG)

    window.set_size(512, 448)

    cartridge = Cartridge("../../test/tetris.nes")
    console = Console(cartridge)
    console.boot()

    window.set_visible(True)


@window.event
def on_draw():
    window.clear()

if __name__ == "__main__":
    init()
    pyglet.app.run()
