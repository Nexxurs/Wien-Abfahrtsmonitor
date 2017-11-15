# -*- coding: utf-8 -*-

import time
import threading

def replaceUmlaut(s):
    s = s.replace('Ä', "Ae")  # A umlaut
    s = s.replace('Ö', "Oe")  # O umlaut
    s = s.replace('Ü', "Ue")  # U umlaut
    s = s.replace('ä', "ae")  # a umlaut
    s = s.replace('ß', "ss")  # Sharp s
    s = s.replace('ö', "oe")  # o umlaut
    s = s.replace('ü', "ue")  # u umlaut
    return s


_i2cLCD = None
_backgroundThread = None
_backgroundThreadReset = False
_backgroundTimeout = 10

def timeoutBGoff():
    global _backgroundThreadReset
    global _backgroundTimeout
    t = _backgroundTimeout
    while t>0:
        if _backgroundThreadReset:
            _backgroundThreadReset = False
            t = _backgroundTimeout
        time.sleep(1)
        t = t-1
        _i2cLCD.lcd_set_background(on=False)

def callbackBG(channel):
    global _backgroundThreadReset
    global _backgroundThread
    if _i2cLCD:
        _i2cLCD.lcd_set_background(on=True)
        if _backgroundThread and _backgroundThread.is_alive():
            _backgroundThreadReset = True
        else:
            _backgroundThread = threading.Thread(target=timeoutBGoff)

class LCD:
    class DEFAULT:
        lcd_rs = 27
        lcd_en = 22
        lcd_d4 = 25
        lcd_d5 = 24
        lcd_d6 = 23
        lcd_d7 = 18
        lcd_backlight = 10
        i2c_address = 0x3f

    i2c = None
    gpio = None



    def gpio_init(self, rs=DEFAULT.lcd_rs, en=DEFAULT.lcd_en, d4=DEFAULT.lcd_d4, d5=DEFAULT.lcd_d5,
                  d6=DEFAULT.lcd_d6, d7=DEFAULT.lcd_d7, backlight=DEFAULT.lcd_backlight, rows=2, columns=16):
        import Adafruit_CharLCD as GPIO_LCD
        self.gpio = GPIO_LCD.Adafruit_CharLCD(rs, en, d4, d5, d6, d7, columns, rows, backlight)

    def i2c_init(self, address=DEFAULT.i2c_address):
        import libs.i2c_lcd as I2C_LCD
        self.i2c = I2C_LCD.lcd(address)

    def clear(self):
        if self.i2c:
            self.i2c.clear()

        if self.gpio:
            self.gpio.clear()

    def write(self, msg):
        if self.i2c:
            lines = msg.split('\n')
            for i in range(0,min(4,len(lines))):
                self.i2c.display_string(lines[i], i+1)

        if self.gpio:
            self.gpio.message(msg)

    def write_rbl(self, rbl):
        if self.i2c:
            line_1 = replaceUmlaut(rbl.line + ' ' + rbl.station)
            line_2 = replaceUmlaut('{:0>2d}'.format(rbl.time) + ' ' + ("%.*s" % (17, rbl.direction)))

            self.i2c.display_string(line_1, 1)
            self.i2c.display_string(line_2, 2)

        if self.gpio:
            self.gpio.message(replaceUmlaut(rbl.line + ' ' + rbl.station + '\n' + '{:0>2d}'.format(rbl.time)
                              + ' ' + ("%.*s" % (7, rbl.direction)) + ' ' + time.strftime("%H:%M", time.localtime())))

    def init_backlight_button(self, btn_pin, timeout):
        global _i2cLCD
        global _backgroundTimeout
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(btn_pin, GPIO.RISING, callback=callbackBG)
        _backgroundTimeout = timeout

        if self.i2c:
            _i2cLCD = self.i2c
            self.i2c.lcd_set_background(on=False)
