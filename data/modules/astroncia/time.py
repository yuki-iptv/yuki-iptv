'''
Copyright (C) 2021 Astroncia

    This file is part of Astroncia IPTV.

    Astroncia IPTV is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Astroncia IPTV is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
'''
import time

class AppLog: # pylint: disable=too-few-public-methods
    pass

AppLog.app_log = ''
AppLog.mpv_log = ''

def print_with_time(str2, log_mpv=False):
    try:
        cur_time = time.strftime('%H:%M:%S', time.localtime())
        if not 'Invalid video timestamp: ' in str(str2):
            OUT_STR = '[{}] {}'.format(cur_time, str(str2))
            print(OUT_STR)
            if log_mpv:
                AppLog.mpv_log += OUT_STR + '\n'
            else:
                AppLog.app_log += OUT_STR + '\n'
    except: # pylint: disable=bare-except
        pass

def get_app_log():
    return AppLog.app_log

def get_mpv_log():
    return AppLog.mpv_log
