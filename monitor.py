import argparse
from fetcher import Fetcher
from printer import Printer
from time import sleep

import logging
import sys

logging_format = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(stream=sys.stdout, format=logging_format, level=logging.WARNING)

_logger = logging.getLogger(__name__)


def create_argparser():
    parser = argparse.ArgumentParser(description="Ein Abfahrtsmonitor für die Wiener Linien")
    parser.add_argument("-k", "--key", metavar="API-Key", required=True, dest="apikey", help="Der Wiener Linien API-Key")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug Flag")

    lcd_group = parser.add_mutually_exclusive_group()
    lcd_group.add_argument("--LCD", action="store_true", dest="lcd_usage",
                           help="Wenn ein I2C LCD Display verwendet werden soll. "
                                "Soll dies zusammen mit einem Button auf Abruf geschehen, "
                                "verwende \"--LCD-Button [Button-Pin]\"")
    lcd_group.add_argument("--LCD-Button", dest="lcd_button", type=int,
                           help="Wenn ein I2C LCD Display mit Button verwendet werden soll. Der Button-Pin bezieht sich"
                                " auf den GPIO Pin, an dem der Button angeschlossen ist")

    parser.add_argument("-c", "--Console", action="store_true", dest="console_usage",
                        help="Wenn die derzeitige Zeit in der Konsole ausgegeben werden soll. In Verbindung mit "
                             "--LCD-Button wird die neue Zeit nur dann ausgegeben, wenn der Button gedrueckt wird!")
    parser.add_argument("rbls", metavar="RBL", nargs='+', help="Die Nummer der Linie laut Wiener Linien API")
    return parser


def main():
    parser = create_argparser()
    args = parser.parse_args()

    printer = Printer()
    if args.lcd_usage or args.lcd_button:
        printer.add_lcd_usage()
    if args.console_usage:
        printer.add_console_usage()

    fetcher = Fetcher(apikey=args.apikey, printer=printer, rbls=args.rbls)
    if args.lcd_button:
        fetcher.start_button_fetcher(args.lcd_button)
        printer.add_sleep_timeout(10)
    else:
        fetcher.start_timeout_fetcher()

    while True:
        sleep(60)


if __name__ == '__main__':
    main()
