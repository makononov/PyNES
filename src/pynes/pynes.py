import pyglet
from cartridge import Cartridge
from console import Console
import logging
import sys

window = pyglet.window.Window(visible=False)


def init():
    logging.basicConfig(stream=sys.stderr)
    log = logging.getLogger('PyNES')
    log.setLevel(logging.DEBUG)

    window.set_size(512, 448)
    window.set_visible()

    cartridge = Cartridge("../../test/tetris.nes")
    console = Console(cartridge)
    console.boot()


@window.event
def on_draw():
    pass


if __name__ == "__main__":
    init()
    pyglet.app.run()
