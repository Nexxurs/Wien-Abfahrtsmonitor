#!/usr/bin/python3
# Version 2 Debug
import sys
import getopt
import time
import requests
import configparser
import urllib3.exceptions as urlexceptions


class RBL:
    id = 0
    line = ''
    station = ''
    direction = ''
    time = -1


def replaceUmlaut(s):
    s = s.replace('Ä', "Ae")  # A umlaut
    s = s.replace('Ö', "Oe")  # O umlaut
    s = s.replace('Ü', "Ue")  # U umlaut
    s = s.replace('ä', "ae")  # a umlaut
    s = s.replace('ß', "ss")  # Sharp s
    s = s.replace('ö', "oe")  # o umlaut
    s = s.replace('ü', "ue")  # u umlaut
    return s


def main(argv):
    apikey = False
    apiurl = 'https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl}&sender={apikey}'
    lcdUsage = True
    consoleUsage = True
    st = 10
    maxError = 10
    global config
    config = config = configparser.ConfigParser()
    try:
        opts, args = getopt.getopt(argv, "hk:t:c:", ["help", "config="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--config"):
            tmp = config.read(arg)
            if len(tmp) == 0:
                usage()
                print("ERROR config file not found")
                sys.exit(2)
            try:
                apikey = config["Settings"]["key"]
                lcdUsage = config.getboolean("Settings", "lcd")
                consoleUsage = config.getboolean("Settings", "console")
                st = config.getint("Settings", "time")
            except:
                print("ERROR config file invalid")
                sys.exit(2)

    if not apikey:
        usage()
        sys.exit()

    if lcdUsage == consoleUsage:
        debug = eq
    else:
        debug = uneq

    rbls = []
    configrbls = config["Settings"]["rbls"].split(',')

    for rbl in configrbls:
        tmprbl = RBL()
        tmprbl.id = rbl
        rbls.append(tmprbl)

    if len(rbls) == 0:
        usage()
        print("No RBLS found!")
        sys.exit(2)

    if lcdUsage:
        configLCD()

    x = 0
    while True:
        for rbl in rbls:
            url = apiurl.replace('{apikey}', apikey).replace('{rbl}', rbl.id)

            if not debug(consoleUsage, lcdUsage):
                raise Exception("Change in Usage: Console=%s, LCD=%s" % (consoleUsage, lcdUsage))

            try:
                r = requests.get(url)
                if r.status_code == 200:
                    json = r.json()['data']['monitors']

                    soonest = json[0]

                    if len(json) > 1:
                        for i in range(1,len(json)):
                            if json[i]['lines'][0]['departures']['departure'][0]['departureTime']['countdown'] < \
                                    soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']:
                                soonest = json[i]

                    rbl.line = soonest['lines'][0]['name']
                    rbl.station = soonest['locationStop']['properties']['title']
                    rbl.direction = soonest['lines'][0]['towards']
                    rbl.time = soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']
                    if consoleUsage:
                        dumpRBL(rbl)
                    if lcdUsage:
                        lcdShow(rbl)
                    x = 0
                    time.sleep(st)
            except KeyboardInterrupt:
                print("User exit by Keyboard Interrupt")
                if lcdUsage:
                    lcd.clear()
                sys.exit(0)
            except urlexceptions.MaxRetryError as e:
                print("Max Retries Exception!")
                if lcdUsage:
                    lcd.clear()
                    lcd.message("Connection Error!\nWill try again shortly")
                time.sleep(1)
            except Exception as e:
                x += 1
                if x > maxError:
                    print(str(x) + "FATAL ERROR")
                    print(e)
                    if lcdUsage:
                        lcd.clear()
                        lcd.message("FATAL ERROR \nPlease check the Logs")
                    raise
                else:
                    print(str(x) + " ERROR " + str(e))
                    if lcdUsage:
                        lcd.clear()
                        lcd.message("ERROR - Please\ncheck the Logs")
                    time.sleep(1)


def configLCD():
    import Adafruit_CharLCD as LCD
    global lcd
    lcd_rs = 27
    lcd_en = 22
    lcd_d4 = 25
    lcd_d5 = 24
    lcd_d6 = 23
    lcd_d7 = 18
    lcd_backlight = 4

    lcd_columns = 16
    lcd_rows = 2

    lcd = lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows,
                                     lcd_backlight)
    lcd.clear()


def lcdShow(rbl):
    lcd.clear()
    lcd.message(replaceUmlaut(rbl.line + ' ' + rbl.station + '\n' + '{:0>2d}'.format(rbl.time)
                              + ' ' + ("%.*s" % (7, rbl.direction)) + ' ' + time.strftime("%H:%M", time.localtime())))


def dumpRBL(rbl):
    print(rbl.line + ' ' + rbl.station)
    print(rbl.direction)
    print(str(rbl.time) + ' Min.')


def usage():
    print('usage: ' + __file__ + ' [-h] -c configFile\n');
    print('arguments:')
    print('  -c, --config\tconfig file with API Key and rbl numbers')
    print('optional arguments:')
    print('  -h, --help\tshow this help')


def eq(b1, b2):
    return b1 == b2


def uneq(b1, b2):
    return b1 != b2


if __name__ == "__main__":
    main(sys.argv[1:])
