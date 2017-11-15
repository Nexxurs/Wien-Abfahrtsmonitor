import sys
import getopt
import lcd
import time
import requests
import configparser
import requests.exceptions as req_exception

class RBL:
    id = 0
    line = ''
    station = ''
    direction = ''
    time = -1


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
    charlcd = lcd.LCD()


globalVals = Globals()


def main(argv):
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
            parseGlobals(arg)
    if globalVals.apikey is None:
        print("API Key is not set! Please add the line key=YOUR-KEY under the Settings Section in the config file")
        usage()
        sys.exit()
    if len(globalVals.rbls) == 0:
        print("No RBLs found! Please add the line \'rbls = XXXX, XXXX, XXXX\' "
              "(substitute XXXX to all the rbls you want to observe) into the Settings Section in the config file")
        usage()
        sys.exit()

    if(globalVals.gpioLCDUsage):
        globalVals.charlcd.gpio_init()

    if(globalVals.i2cLCDUsage):
        # todo maybe add address from config
        globalVals.charlcd.i2c_init()


    while True:
        for rbl in globalVals.rbls:
            lookupRBL(rbl)


def lookupRBL(rbl):
    url = globalVals.apiurl.replace('{apikey}', globalVals.apikey).replace('{rbl}', rbl.id)
    r = None

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
            if globalVals.consoleUsage:
                printConsole(rbl)
            globalVals.charlcd.write_rbl(rbl)
            time.sleep(globalVals.secondsBetweenLookups)
        else:
            print("Request Status Code: {}".format(r.status_code))
            globalVals.charlcd.clear()
            globalVals.charlcd.write("Request Status Code!\n{}".format(r.status_code))
            time.sleep(3)
    except KeyboardInterrupt:
        print("User exit by Keyboard Interrupt")
        globalVals.charlcd.clear()
        sys.exit()
    except req_exception.ConnectionError as e:
        print("Connection Error",e)
        globalVals.charlcd.clear()
        globalVals.charlcd.write("Connection Error!\nWill try again shortly")
        time.sleep(1)
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
            globalVals.charlcd.write("FATAL ERROR \nCheck the Logs")
            raise
        else:
            print(str(globalVals.errorCount) + " ERROR " + str(type(e)) + " - " + str(e))
            globalVals.charlcd.clear()
            globalVals.charlcd.write("ERROR-{}\nCheck the Logs".format(type(e)))
            time.sleep(1)


def printConsole(rbl):
    print(rbl.line + ' ' + rbl.station)
    print(rbl.direction)
    print(str(rbl.time) + ' Min.')


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

        strRBLS = globalVals.config["Settings"]["rbls"].split(',')
        for rbl in strRBLS:
            tmprbl = RBL()
            tmprbl.id = rbl
            globalVals.rbls.append(tmprbl)

    except:
        print("ERROR config file invalid")
        sys.exit(2)

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
