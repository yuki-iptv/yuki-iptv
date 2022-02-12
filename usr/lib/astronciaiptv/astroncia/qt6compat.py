# pylint: disable=missing-function-docstring, no-else-return, invalid-name
'''
SPDX-License-Identifier: GPL-3.0-only

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
from astroncia.time import print_with_time
from astroncia.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

class AstronciaData: # pylint: disable=too-few-public-methods
    '''Data class'''
    WRITTEN = False
    WRITTENQT = False

def globalPos(arg):
    try:
        ret = arg.globalPosition().toPoint()
    except: # pylint: disable=bare-except
        if not AstronciaData.WRITTEN:
            AstronciaData.WRITTEN = True
            print_with_time("Qt 5 (globalPos) compatibility enabled")
        ret = arg.globalPos()
    return ret

def getX(arg1):
    return arg1.x()

def getY(arg2):
    return arg2.y()

def _exec(obj, arg=None):
    if hasattr(obj, 'exec'):
        if arg:
            return obj.exec(arg)
        else:
            return obj.exec()
    else:
        if arg:
            return obj.exec_(arg)
        else:
            return obj.exec_()

def _enum(obj, name):
    parent, child = name.split('.')
    try:
        return getattr(getattr(obj, parent), child)
    except: # pylint: disable=bare-except
        if not AstronciaData.WRITTENQT:
            AstronciaData.WRITTENQT = True
            print_with_time("Falling back to short names for Qt enums")
        return getattr(obj, child)

def qaction(arg1, arg2):
    if qt_library == 'PyQt6':
        func = QtGui.QAction
    else:
        func = QtWidgets.QAction
    return func(arg1, arg2)
