#!/usr/bin/env python3

import sys
import getopt
import zzz_lcd_old
import time
import requests
import configparser
import requests.exceptions as req_exception
import threading
import datetime


class RBL:
    id = 0
    line = ''
    station = ''
    direction = ''
    time = -1
    errormsg = None
    updatetime = datetime.datetime.min

    def __str__(self):
        return "Line {}, Station {}, Direction {}, Time {}, Error: {}".format(self.line, self.station,
                                                                              self.direction, self.time, self.errormsg)


class Globals:
    apiurl = 'https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl}&sender={apikey}'
    apikey = None
    gpioLCDUsage = False
    i2cLCDUsage = False
    consoleUsage = False
    secondsBetweenLookups = 10
    maxError = 10
    config = configparser.ConfigParser()
    errorCount = 0
    rbls = []
    charlcd = zzz_lcd_old.LCD()
    backlightButtonGPIO = None
    backlightTimer = 10
    lastRBL = None
    backgroundThread = None
    backgroundThreadReset = False
    backgroundTimeout = 10
    backgroundLightOn = True


globalVals = Globals()


def main(argv):
    debug = False
    try:
        opts, args = getopt.getopt(argv, "dhc:", ["debug", "help", "config="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--config"):
            parseGlobals(arg)
        elif opt in ("-d", "--debug"):
            debug = True
    if globalVals.apikey is None:
        print("API Key is not set! Please add the line key=YOUR-KEY under the Settings Section in the config file")
        usage()
        sys.exit()
    if len(globalVals.rbls) == 0:
        print("No RBLs found! Please add the line \'rbls = XXXX, XXXX, XXXX\' "
              "(substitute XXXX to all the rbls you want to observe) into the Settings Section in the config file")
        usage()
        sys.exit()

    if globalVals.gpioLCDUsage:
        globalVals.charlcd.gpio_init()

    if globalVals.i2cLCDUsage:
        # todo maybe add address from config
        globalVals.charlcd.i2c_init(debug=debug)
        if globalVals.backlightButtonGPIO:
            init_backlight_button(globalVals.backlightButtonGPIO, globalVals.backlightTimer)
    try:
        while True:
            for rbl in globalVals.rbls:
                lookupRBL(rbl)
                globalVals.lastRBL = rbl
                printConsole(rbl)
                if globalVals.backgroundLightOn:
                    globalVals.charlcd.write_rbl(rbl)
                time.sleep(globalVals.secondsBetweenLookups)
    except KeyboardInterrupt:
        print("User exit by Keyboard Interrupt")
        globalVals.charlcd.clear()
        sys.exit()


def lookupRBL(rbl):
    url = globalVals.apiurl.replace('{apikey}', globalVals.apikey).replace('{rbl}', rbl.id)
    print(url)
    r = None

    rbl.updatetime = datetime.datetime.now()
    rbl.errormsg = None

    try:
        r = requests.get(url)
        if r.status_code == 200:
            mon_json = r.json()['data']['monitors']
            if len(mon_json) == 0:
                print("Problematic JSON: {}".format(r.json()))
                globalVals.charlcd.clear()
                globalVals.charlcd.write("Problematic JSON!")
                time.sleep(1)
            else:
                soonest = mon_json[0]
                for i in range(1, len(mon_json)):
                    if mon_json[i]['lines'][0]['departures']['departure'][0]['departureTime']['countdown'] < \
                            soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']:
                        soonest = mon_json[i]
                rbl.line = soonest['lines'][0]['name']
                rbl.station = soonest['locationStop']['properties']['title']
                rbl.direction = soonest['lines'][0]['towards']
                rbl.time = soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']
                globalVals.errorCount = 0
                return rbl
        else:
            rbl.errormsg = "Request Status Code: {}".format(r.status_code)
            return rbl
    except req_exception.ConnectionError as e:
        rbl.errormsg = "Connection Error!\n{}\nWill try again shortly".format(type(e))
        print("Connection Error", e)
        return rbl
    except Exception as e:
        globalVals.errorCount = globalVals.errorCount+1
        if globalVals.errorCount > globalVals.maxError:
            print("FATAL ERROR")
            print("Type: {}".format(type(e)))
            if r is not None:
                json = r.json()
                if json is not None:
                    print("With JSON:")
                    print(str(json))
            writeLCD("FATAL ERROR \nCheck the Logs")
            raise
        else:
            print(str(globalVals.errorCount) + " ERROR " + str(type(e)) + " - " + str(e))
            writeLCD("ERROR-{}\nCheck the Logs".format(type(e)))
            time.sleep(1)


def printConsole(rbl):
    if rbl.errormsg is None and globalVals.consoleUsage:
        print(rbl.line + ' ' + rbl.station)
        print(rbl.direction)
        print(str(rbl.time) + ' Min.\t\t' + rbl.updatetime.time().strftime("%H:%M"))
    elif rbl.errormsg is not None:
        print("Error: {}".format(rbl.errormsg))


def parseGlobals(file):
    readFiles = globalVals.config.read(file)
    if len(readFiles) == 0:
        usage()
        print("ERROR config file not found")
        sys.exit(2)

    try:
        globalVals.apikey = globalVals.config.get("Settings", "key", fallback=None)
        globalVals.gpioLCDUsage = globalVals.config.getboolean("Settings", "gpiolcd", fallback=False)
        globalVals.i2cLCDUsage = globalVals.config.getboolean("Settings", "i2clcd", fallback=False)
        globalVals.consoleUsage = globalVals.config.getboolean("Settings", "console", fallback=True)
        globalVals.secondsBetweenLookups = globalVals.config.getint("Settings", "time", fallback=10)
        globalVals.backlightButtonGPIO = globalVals.config.getint("I2C-LCD", "backlightButtonGPIO", fallback=None)
        globalVals.backlightTimer = globalVals.config.getint("I2C-LCD", "backlightTimer", fallback=10)

        strRBLS = globalVals.config["Settings"]["rbls"].split(',')
        for rbl in strRBLS:
            tmprbl = RBL()
            tmprbl.id = rbl
            globalVals.rbls.append(tmprbl)

    except:
        print("ERROR config file invalid")
        sys.exit(2)


def backgroundTimeoutOff():
    t = globalVals.backgroundTimeout
    while t>0:
        t = t-1
        if globalVals.backgroundThreadReset:
            globalVals.backgroundThreadReset = False
            t = globalVals.backgroundTimeout
        time.sleep(1)

    globalVals.charlcd.i2c.lcd_set_background(on=False)
    globalVals.backgroundLightOn = False


def backgroundButtonCallback(channel):
    if globalVals.charlcd.i2c:
        globalVals.charlcd.i2c.lcd_set_background(on=True)
        globalVals.backgroundLightOn = True
        globalVals.charlcd.clear()
        globalVals.charlcd.write_rbl(globalVals.lastRBL)
        if globalVals.backgroundThread and globalVals.backgroundThread.is_alive():
            globalVals.backgroundThreadReset = True
        else:
            globalVals.backgroundThread = threading.Thread(target=backgroundTimeoutOff)
            globalVals.backgroundThread.start()


def writeLCD(msg):
    globalVals.charlcd.clear()
    globalVals.charlcd.write(msg)
    if globalVals.charlcd.i2c:
        globalVals.charlcd.i2c.lcd_set_background(on=True)
        globalVals.backgroundLightOn = True
        if globalVals.backgroundThread and globalVals.backgroundThread.is_alive():
            globalVals.backgroundThreadReset = True
        else:
            globalVals.backgroundThread = threading.Thread(target=backgroundTimeoutOff)
            globalVals.backgroundThread.start()


def init_backlight_button(btn_pin, timeout):
    import RPi.GPIO as GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(btn_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(btn_pin, GPIO.RISING, callback=backgroundButtonCallback)
    globalVals.backgroundTimeout = timeout

    if globalVals.charlcd.i2c:
        globalVals.charlcd.i2c.lcd_set_background(on=False)
        globalVals.backgroundLightOn = False


def usage():
    print('usage: ' + __file__ + ' [-h] -c configFile\n')
    print('arguments:')
    print('  -c, --config\tconfig file with API Key and rbl numbers')
    print('optional arguments:')
    print('  -h, --help\tshow this help')
    print('')
    print('Config File Content:')
    print('[Settings]')
    print('key = YOUR_KEY')
    print('rbls = XXXX, YYYY, ZZZZ')
    print('i2clcd = True|False')
    print('gpiolcd = True|False')
    print('console = True|False')
    print('time = 10')
    print('[I2C-LCD]')
    print('address = I2C_HEX_ADR #0x3f is default')


if __name__ == "__main__":
    main(sys.argv[1:])
