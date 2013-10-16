from controllers import Controller


class KeyboardController(Controller):
    def __init__(self, display):
        self._display = display
        Controller.__init__(self)

    def toggle_strobe(self, on):
        if on:
            #TODO
            pass
        else:
            pass
