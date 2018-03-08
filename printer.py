class Printer:
    def __init__(self):
        self.console_usage = False
        self.lcd_usage = False

    def add_console_usage(self):
        self.console_usage = True

    def add_lcd_usage(self):
        self.lcd_usage = True

    def print_rbl(self, rbl):
        pass

    def print_message(self, msg):
        pass