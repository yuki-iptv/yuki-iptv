#!/usr/bin/python3
'''pfs compatibility for libmpv'''
# SPDX-License-Identifier: GPL-3.0-only
import os
MPV_OUT = ''
try:
    if os.path.isfile('/usr/bin/mpv'):
        MPV_F = open('/usr/bin/mpv', 'r')
        MPV_O = MPV_F.readlines()
        MPV_F.close()
        for mpv_line in MPV_O:
            if str(mpv_line).startswith('p1='):
                MPV_OUT = '/opt/' + mpv_line.strip().replace('p1=', '') + '/lib'
except: # pylint: disable=bare-except
    pass
OLD_LD_LIBRARY = ''
try:
    OLD_LD_LIBRARY = os.environ['LD_LIBRARY_PATH']
except: # pylint: disable=bare-except
    pass
NEW_LD_LIBRARY = MPV_OUT + ':' + OLD_LD_LIBRARY
print(NEW_LD_LIBRARY)
