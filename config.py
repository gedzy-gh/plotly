import glob
import os
import datetime

import dateparser
import pytz


class Key:
    public = ''  # Your API Key
    secret = ''  # Your Secret Key


class File:

    def __init__(self):
        pass

    @staticmethod
    def to_desktop(folder_name, sub_folder_name, file_type, lvl):
        path = os.environ['USERPROFILE'] + '\\Desktop'
        if lvl[1] == 0:
            try:
                if lvl[0] == 0:
                    current_path = path + '\\' + folder_name
                    if not os.path.isdir(current_path):
                        os.mkdir(current_path)
                current_path = path + '\\' + folder_name + '\\' + sub_folder_name
                if os.path.isdir(current_path):
                    files = glob.glob(current_path + '\\' + file_type)
                    for f in files:
                        os.remove(f)
                    os.rmdir(current_path)
                os.mkdir(current_path)
                os.chdir(current_path)
            except OSError as e:
                print(e)


class Converter:

    def __init__(self):
        pass

    def some_func(self):
        pass

    @staticmethod
    def unix_to_timestamp(n):
        return datetime.datetime.fromtimestamp(int(n) / 1000, tz=pytz.utc).strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def date_to_milliseconds(date_str):
        """Convert UTC date to milliseconds
        If using offset strings add "UTC" to date string e.g. "now UTC", "11 hours ago UTC"
        See date-parse docs for formats http://dateparser.readthedocs.io/en/latest/
        :param date_str: date in readable format, i.e. "January 01, 2018", "11 hours ago UTC", "now UTC"
        :type date_str: str
        """
        # get epoch value in UTC
        epoch = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=pytz.utc)
        # parse our date string
        d = dateparser.parse(date_str)
        # if the date is not timezone aware apply UTC timezone
        if d.tzinfo is None or d.tzinfo.utcoffset(d) is None:
            d = d.replace(tzinfo=pytz.utc)

        # return the difference in time
        return int((d - epoch).total_seconds() * 1000.0)

    @staticmethod
    def interval_to_milliseconds(interval):
        """Convert a Binance interval string to milliseconds
        :param interval: Binance interval string 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w
        :type interval: str
        :return:
            None if unit not one of m, h, d or w
            None if string not in correct format
            int value of interval in milliseconds
        """
        ms = None
        seconds_per_unit = {
            "m": 60,
            "h": 60 * 60,
            "d": 24 * 60 * 60,
            "w": 7 * 24 * 60 * 60
        }

        unit = interval[-1]
        if unit in seconds_per_unit:
            try:
                ms = int(interval[:-1]) * seconds_per_unit[unit] * 1000
            except ValueError:
                pass
        return ms


class Formatter:

    def __init__(self):
        pass

    @staticmethod
    def tidy_string_decimal(s):
        p = 2
        try:
            s = str(s)
            v = s.split('.')[1].rstrip('0')
            if len(v) > 2 < 8:
                p = 2
            if len(v) > 2 >= 8:
                p = 8
            del v
            return f'{float(s):.{p}f}'
        except (IndexError, ValueError):
            return str(s)

    @staticmethod
    def get_string_decimal(s):
        p = 2
        try:
            s = str(s)
            v = s.split('.')[1].rstrip('0')
            if len(v) > 2 < 8:
                p = 2
            if len(v) > 2 >= 8:
                p = 8
            del v
            return p
        except (IndexError, ValueError):
            return p

    @staticmethod
    def float(value, place=2):
        return f'{value:.{place}f}'

    @staticmethod
    def tidy_df_decimal(df):
        p = 2
        try:
            s = str(df[0])
            v = s.split('.')[1].rstrip('0')
            if len(v) > 2 < 8:
                p = 2
            if len(v) > 2 >= 8:
                p = 8
            del v
            return p
        except (IndexError, ValueError):
            return p
