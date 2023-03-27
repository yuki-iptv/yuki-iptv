# pylint: disable=missing-module-docstring, missing-function-docstring, no-else-return, invalid-name
# SPDX-License-Identifier: GPL-3.0-only
from yuki_iptv.time import print_with_time
from yuki_iptv.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

class YukiData: # pylint: disable=too-few-public-methods
    '''Data class'''
    WRITTEN = False
    WRITTENQT = False

def globalPos(arg):
    try:
        ret = arg.globalPosition().toPoint()
    except: # pylint: disable=bare-except
        if not YukiData.WRITTEN:
            YukiData.WRITTEN = True
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
        if not YukiData.WRITTENQT:
            YukiData.WRITTENQT = True
            print_with_time("Falling back to short names for Qt enums")
        return getattr(obj, child)

def qaction(arg1, arg2):
    if qt_library == 'PyQt6':
        func = QtGui.QAction
    else:
        func = QtWidgets.QAction
    return func(arg1, arg2)
