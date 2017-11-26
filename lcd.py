# -*- coding: utf-8 -*-

def replaceUmlaut(s):
    s = s.replace('Ä', "Ae")  # A umlaut
    s = s.replace('Ö', "Oe")  # O umlaut
    s = s.replace('Ü', "Ue")  # U umlaut
    s = s.replace('ä', "ae")  # a umlaut
    s = s.replace('ß', "ss")  # Sharp s
    s = s.replace('ö', "oe")  # o umlaut
    s = s.replace('ü', "ue")  # u umlaut
    return s

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

    def i2c_init(self, address=DEFAULT.i2c_address, debug=False):
        import libs.i2c_lcd as I2C_LCD
        self.i2c = I2C_LCD.lcd(address)
        self.i2cdebug = debug

    def clear(self):
        if self.i2c:
            self.i2c.clear()

        if self.gpio:
            self.gpio.clear()

    def write_i2c(self, msg):
        if self.i2cdebug:
            print("I2C LCD Write: " + msg)
        lines = msg.split('\n')
        to_print = []
        for l in lines:
            number_lines = int(len(l) / 20) + 1
            for i in range(number_lines):
                to_print.append(l[i * 20:(i + 1) * 20])

        for i in range(0, min(4, len(to_print))):
            self.i2c.display_string(to_print[i], i + 1)

    def write(self, msg):
        if self.i2c:
            self.write_i2c(msg)

        if self.gpio:
            self.gpio.message(msg)

    def write_rbl(self, rbl):
        self.lastrbl = rbl
        if self.i2c:
            if self.i2cdebug:
                print("I2C LCD RBL Write: "+str(rbl))
            line_3 = rbl.updatetime.time().strftime("%H:%M")
            if rbl.errormsg is None:
                line_1 = replaceUmlaut(rbl.line + ' ' + rbl.station)
                line_2 = replaceUmlaut('{:0>2d}'.format(rbl.time) + ' ' + ("%.*s" % (17, rbl.direction)))
            else:
                line_1 = "An Error Occured:"
                line_2 = replaceUmlaut(rbl.errormsg)

            msg = line_1+'\n'+line_2+'\n'+line_3
            self.write_i2c(msg)


        if self.gpio:
            if rbl.errormsg is None:
                self.gpio.message(replaceUmlaut(rbl.line + ' ' + rbl.station + '\n' + '{:0>2d}'.format(rbl.time)
                                                + ' ' + ("%.*s" % (7, rbl.direction)) + ' ' + rbl.updatetime.time().strftime("%H:%M")))
            else:
                self.gpio.message("Error: " + rbl.errormsg + "\n" + rbl.updatetime.time().strftime("%H:%M"))
