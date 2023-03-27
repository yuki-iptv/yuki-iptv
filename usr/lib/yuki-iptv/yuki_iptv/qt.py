'''Qt loader'''
# pylint: disable=no-member, c-extension-no-member, import-outside-toplevel, invalid-name
# SPDX-License-Identifier: GPL-3.0-only
import sys
from yuki_iptv.time import print_with_time

class YukiData: # pylint: disable=too-few-public-methods, missing-class-docstring
    pass

YukiData.qt6_disable_printed = False

def get_qt_library():
    '''Get correct Qt library - PyQt6/5'''
    qt_library = "none"
    QShortcut = False
    QtWidgets = False
    QtCore = False
    QtGui = False
    try:
        if '--disable-qt6' in sys.argv:
            if not YukiData.qt6_disable_printed:
                YukiData.qt6_disable_printed = True
                print_with_time("Qt6 force disabled\n")
            raise Exception("")
        from PyQt6 import QtWidgets
        from PyQt6 import QtCore
        from PyQt6 import QtGui
        QShortcut = QtGui.QShortcut
        qt_library = "PyQt6"
    except: # pylint: disable=bare-except
        from PyQt5 import QtWidgets
        from PyQt5 import QtCore
        from PyQt5 import QtGui
        QShortcut = QtWidgets.QShortcut
        qt_library = "PyQt5"
    return qt_library, QtWidgets, QtCore, QtGui, QShortcut
