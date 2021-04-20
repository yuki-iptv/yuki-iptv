'''Converting bitrate (bytes) to human friendly string'''
'''
Copyright 2021 Astroncia

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
# pylint: disable=no-else-return, inconsistent-return-statements
def humanbytes(B, names):
    'Return the given bytes as a human friendly KB, MB, GB, or TB string'
    B = float(B)
    KB = float(1024)
    MB = float(KB ** 2) # 1,048,576
    GB = float(KB ** 3) # 1,073,741,824
    TB = float(KB ** 4) # 1,099,511,627,776

    if B < KB:
        return '{0} {1}'.format(B, names[0] if 0 == B > 1 else names[0])
    elif KB <= B < MB:
        return '{0:.2f}'.format(B/KB) + " " + names[1]
    elif MB <= B < GB:
        return '{0:.2f}'.format(B/MB) + " " + names[2]
    elif GB <= B < TB:
        return '{0:.2f}'.format(B/GB) + " " + names[3]
    elif TB <= B:
        return '{0:.2f}'.format(B/TB) + " " + names[4]
