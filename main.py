#!/usr/bin/python3

import datetime
import locale
import re
import sys
import textwrap
import traceback

from bs4 import BeautifulSoup
import icalendar
import pytz
import requests

__author__ = 'Jan-Philipp Litza <janphilipp@litza.de>'


def parse_time(datestr, timecomps):
    old_locale = locale.getlocale(locale.LC_TIME)
    locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')
    dt = datetime.datetime.strptime(
        '{} {}:{}'.format(
            datestr,
            timecomps[0],
            timecomps[1],
        ),
        '%d. %B %Y %H:%M',
    )
    locale.setlocale(locale.LC_TIME, old_locale)
    return pytz.timezone('Europe/Berlin').localize(dt)


def main(url, out):
    req = requests.get(url)
    html = BeautifulSoup(req.text, 'html.parser')
    cal = icalendar.Calendar()
    for event in html.select('.content_kachel > ul > li'):
        try:
            calevent = icalendar.Event()
            date, title, location, times = list(event.stripped_strings)[0:4]
            times = re.fullmatch(
                r'Von (\d\d?)(?::(\d\d))? bis (\d\d?)(?::(\d\d))? Uhr',
                times,
            ).groups('00')

            calevent.add('dtstart', parse_time(date, times[0:2]))
            calevent.add('dtend', parse_time(date, times[2:4]))
            calevent.add('summary', title)
            calevent.add('location', location)
            cal.add_component(calevent)
        except Exception as e:
            print(
                "Failed to parse event:\n{}".format(
                    textwrap.indent(event.get_text('\n', strip=True), '  '),
                ),
                file=sys.stderr,
            )
            traceback.print_exc(1)

    out.write(cal.to_ical())


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument(
        'outfile',
        type=argparse.FileType('wb'),
        nargs='?',
        default=sys.stdout.buffer,
    )
    args = parser.parse_args()
    main(args.url, args.outfile)