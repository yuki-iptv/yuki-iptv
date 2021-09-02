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
from astroncia.time import print_with_time

class astroncia_data: # pylint: disable=too-few-public-methods
    WRITTEN = False
    WRITTENX = False
    WRITTENY = False

def globalPos(arg):
    try:
        ret = arg.globalPosition().toPoint()
    except: # pylint: disable=bare-except
        if not astroncia_data.WRITTEN:
            astroncia_data.WRITTEN = True
            print_with_time("Qt 5 (globalPos) compatibility enabled")
        ret = arg.globalPos()
    return ret

def getX(arg1):
    return arg1.x()

def getY(arg2):
    return arg2.y()
