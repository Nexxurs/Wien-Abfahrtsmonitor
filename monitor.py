import argparse
from wienerlinien_api import WienerLinienAPI


def create_argparser():
    parser = argparse.ArgumentParser(description="Ein Abfahrtsmonitor für die Wiener Linien")
    parser.add_argument("-k", "--key", metavar="API-Key", required=True, dest="apikey", help="Der Wiener Linien API-Key")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug Flag")

    lcd_group = parser.add_mutually_exclusive_group()
    lcd_group.add_argument("--LCD", action="store_true", dest="lcd_usage",
                           help="Wenn ein I2C LCD Display verwendet werden soll. "
                                "Soll dies zusammen mit einem Button auf Abruf geschehen, "
                                "verwende \"--LCD-Button [Button-Pin]\"")
    lcd_group.add_argument("--LCD-Button", dest="lcd_button",
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
    wiener_linien = WienerLinienAPI(args.apikey)


if __name__ == '__main__':
    main()
