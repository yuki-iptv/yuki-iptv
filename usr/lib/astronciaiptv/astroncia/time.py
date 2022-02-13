# pylint: disable=missing-module-docstring, missing-function-docstring
# SPDX-License-Identifier: GPL-3.0-only
import time

class AppLog: # pylint: disable=too-few-public-methods
    '''Data class'''
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
