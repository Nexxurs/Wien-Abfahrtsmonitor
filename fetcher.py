import requests
import requests.exceptions as req_exception
from datetime import datetime, timedelta
from threading import Thread
from time import sleep


class RBL:
    id = 0
    line = ''
    station = ''
    direction = ''
    time = -1
    errormsg = None

    def __str__(self):
        return "Line {}, Station {}, Direction {}, Time {}, Error: {}".format(self.line, self.station,
                                                                              self.direction, self.time,
                                                                              self.errormsg)


class Fetcher:
    def __init__(self, apikey, printer, rbls):
        """apikey is required, button and timeout are exclusive. if a button is given, the timeout will be ignored!"""
        self.apikey = apikey
        self.rbls = rbls
        self.printer = printer
        self.curr_rbl_id = 0
        self.last_fetch = datetime.min

    def _on_button_press(self, channel):
        if self.last_fetch + timedelta(seconds=1) > datetime.now():
            # Only one fetch per second max!
            return

        rbl = self.fetch_next()
        self.printer.print_rbl(rbl)

        self.last_fetch = datetime.now()

    def _timout_fetcher(self, timeout):
        while True:
            rbl = self.fetch_next()
            self.printer.print_rbl(rbl)
            sleep(timeout)

    def start_button_fetcher(self, button_pin):
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(button_pin, GPIO.RISING, callback=self._on_button_press)

    def start_timeout_fetcher(self, timeout=30):
        thread = Thread(target=self._timout_fetcher, args=[timeout])
        thread.start()

    def fetch_next(self):
        rbl_id = self.rbls[self.curr_rbl_id]
        rbl = self.fetch_rbl(rbl_id)
        self.curr_rbl_id = self.curr_rbl_id+1 % len(self.rbls)
        return rbl

    def fetch_rbl(self, rbl_id):
        url = 'https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl}&sender={apikey}'.format(rbl=rbl_id,
                                                                                                  apikey=self.apikey)
        rbl = RBL()
        rbl.id = rbl_id

        try:
            req = requests.get(url)
            if req.status_code == 200:
                json_monitor = req.json()['data']['monitors']
                if len(json_monitor) == 0:
                    print("Problematic JSON: {}".format(req.json()))
                    rbl.errormsg = "Problematic JSON: No monitors!"
                    return rbl

                soonest = json_monitor[0]
                for i in range(1, len(json_monitor)):
                    if json_monitor[i]['lines'][0]['departures']['departure'][0]['departureTime']['countdown'] < \
                            soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']:
                        soonest = json_monitor[i]
                rbl.line = soonest['lines'][0]['name']
                rbl.station = soonest['locationStop']['properties']['title']
                rbl.direction = soonest['lines'][0]['towards']
                rbl.time = soonest['lines'][0]['departures']['departure'][0]['departureTime']['countdown']

            else:
                rbl.errormsg = "Request Status Code Error: {}".format(req.status_code)
        except req_exception.ConnectionError as e:
            rbl.errormsg = "Connection Error!\n  {}\n  Will try again shortly".format(type(e))
            print("Connection Error", e)
        except Exception as e:
            print("Unknown Exception!", e)
            raise e
        return rbl
