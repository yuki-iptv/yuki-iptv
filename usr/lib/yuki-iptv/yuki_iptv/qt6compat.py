# pylint: disable=missing-module-docstring, missing-function-docstring, no-else-return, invalid-name
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
from yuki_iptv.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

logger = logging.getLogger(__name__)

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
            logger.debug("Qt 5 (globalPos) compatibility enabled")
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
    return getattr(getattr(obj, parent), child)

def qaction(arg1, arg2):
    if qt_library == 'PyQt6':
        func = QtGui.QAction
    else:
        func = QtWidgets.QAction
    return func(arg1, arg2)
