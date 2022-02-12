#!/usr/bin/python3
'''pfs compatibility for libmpv'''
#
# SPDX-License-Identifier: GPL-3.0-only
#
# Copyright (c) 2021-2022 Astroncia
#
#     This file is part of Astroncia IPTV.
#
#     Astroncia IPTV is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Astroncia IPTV is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
#
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
