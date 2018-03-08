import requests
import requests.exceptions as req_exception
from datetime import datetime


class WienerLinienAPI:
    class RBL:
        id = 0
        line = ''
        station = ''
        direction = ''
        time = -1
        errormsg = None
        updatetime = datetime.min

        def __str__(self):
            return "Line {}, Station {}, Direction {}, Time {}, Error: {}".format(self.line, self.station,
                                                                                  self.direction, self.time,
                                                                                  self.errormsg)

    def __init__(self, apikey):
        self.apikey = apikey

    def fetch_rbl(self, rbl_id):
        url = 'https://www.wienerlinien.at/ogd_realtime/monitor?rbl={rbl}&sender={apikey}'.format(rbl=rbl_id,
                                                                                                  apikey=self.apikey)
        rbl = self.RBL()
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
