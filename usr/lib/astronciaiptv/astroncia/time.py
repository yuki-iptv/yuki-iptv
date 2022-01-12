'''
Copyright (c) 2021-2022 Astroncia

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
    app_log = ''
    mpv_log = ''
    args1 = None

def args_init(args1):
    AppLog.args1 = args1

def print_with_time(str2, log_mpv=False):
    is_silent = False
    try:
        is_silent = AppLog.args1.silent
    except: # pylint: disable=bare-except
        pass
    try:
        cur_time = time.strftime('%H:%M:%S', time.localtime())
        if 'Invalid video timestamp: ' not in str(str2):
            out_str = '[{}] {}'.format(cur_time, str(str2))
            if not is_silent:
                print(out_str)
            if log_mpv:
                AppLog.mpv_log += out_str + '\n'
            else:
                AppLog.app_log += out_str + '\n'
    except: # pylint: disable=bare-except
        pass

def get_app_log():
    return AppLog.app_log

def get_mpv_log():
    return AppLog.mpv_log
