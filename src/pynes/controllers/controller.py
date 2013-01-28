import logging

log = logging.getLogger("PyNES")
class Controller(object):
  def toggle_strobe(self, on):
    if (on):
      log.debug("Controller strobe activated!")
    else:
      log.debug("Controller strobe deactivated.")
