from console import Console
from cartridge import Cartridge
from controllers import KeyboardController
import pyglet
import logging, sys

BREAKPOINTS = []

class Pynes:
	def __init__(self):
		self._running = True
		self.window = pyglet.window.Window(width = 512, height = 448)
		self.console = Console()
		# self.console.load_cartridge(Cartridge("../../test/ff.nes"))

	@self.window.event
	def on_draw():
		self.window.clear()
		screen = pyglet.image.ImageData(256, 224, "RGB", self.console.ppu.get_screen())
		screen.blit(0, 0)
	
	def execute(self):
		pyglet.app.run()

if __name__ == "__main__":
	logging.basicConfig(stream = sys.stderr)
	log = logging.getLogger('PyNES')
	log.setLevel(logging.DEBUG)
	theApp = Pynes()
	theApp.execute()
