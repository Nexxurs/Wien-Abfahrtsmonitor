# -*- coding: utf-8 -*-

from datetime import datetime
from threading import Thread
from time import sleep

import logging
_logger = logging.getLogger(__name__)

def replace_umlaut(s):
    s = s.replace('Ä', "Ae")  # A umlaut
    s = s.replace('Ö', "Oe")  # O umlaut
    s = s.replace('Ü', "Ue")  # U umlaut
    s = s.replace('ä', "ae")  # a umlaut
    s = s.replace('ß', "ss")  # Sharp s
    s = s.replace('ö', "oe")  # o umlaut
    s = s.replace('ü', "ue")  # u umlaut
    return s


class Printer:
    def __init__(self):
        self.console_usage = False
        self.lcd = None
        self.timeout = None
        self.timeout_thread = None
        self.timeout_reset = False

    def add_console_usage(self):
        self.console_usage = True

    def add_lcd_usage(self):
        import libs.i2c_lcd as I2C_LCD
        self.lcd = I2C_LCD.lcd()

    def add_sleep_timeout(self, timeout):
        self.timeout = timeout
        if self.lcd is not None:
            self.lcd.lcd_set_background(False)

    def print_rbl(self, rbl):
        self.refresh_sleep_timeout()
        if rbl.errormsg is not None:
            _logger.warning("Error: {}".format(rbl.errormsg))
        elif self.console_usage:
            print(rbl.line + ' ' + rbl.station)
            print(rbl.direction)
            print(str(rbl.time) + ' Min')

        if self.lcd is not None:
            lines = []
            if rbl.errormsg is None:
                lines.append(rbl.line + ' ' + rbl.station)
                lines.append('{:0>2d}'.format(rbl.time) + ' ' + ("%.*s" % (17, rbl.direction)))
            else:
                lines.append("An Error Occured:")
                lines.append(rbl.errormsg)
            lines.append(datetime.now().time().strftime("%H:%M"))

            for i in range(0, min(4, len(lines))):
                line = replace_umlaut(lines[i])
                self.lcd.display_string(line[:20], i+1)

    def print_message(self, msg: str):
        self.refresh_sleep_timeout()
        if self.console_usage:
            print(msg)

        if self.lcd is not None:
            lines = msg.split('\n')
            for i in range(0, min(4, len(lines))):
                line = replace_umlaut(lines[i])
                self.lcd.display_string(line[:20], i+1)

    def _timeout_thread_target(self):
        timer = self.timeout
        while timer > 0:
            timer -= 1
            if self.timeout_reset:
                self.timeout_reset = False
                timer = self.timeout
            sleep(1)
        self.lcd.lcd_set_background(False)

    def refresh_sleep_timeout(self):
        if self.lcd is None or self.timeout is None:
            return
        if self.timeout_thread is None or not self.timeout_thread.is_alive():
            self.lcd.lcd_set_background(True)
            self.timeout_thread = Thread(target=self._timeout_thread_target)
            self.timeout_thread.start()
        else:
            self.timeout_reset = True
