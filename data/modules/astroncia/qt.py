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
import sys
from data.modules.astroncia.time import print_with_time

qt6_disable_printed = False

def get_qt_backend():
    global qt6_disable_printed
    qt_backend = "none"
    QShortcut = False
    QtWidgets = False
    QtCore = False
    QtGui = False
    try:
        if '--disable-qt6' in sys.argv:
            if not qt6_disable_printed:
                qt6_disable_printed = True
                print_with_time("Qt6 force disabled\n")
            raise Exception("")
        from PySide6 import QtWidgets
        from PySide6 import QtCore
        from PySide6 import QtGui
        QShortcut = QtGui.QShortcut
        qt_backend = "PySide6"
    except: # pylint: disable=bare-except
        try:
            # Do not use PySide2
            # ===
            # data/modules/thirdparty/selectionmodel.py", line 140, in dropMimeData
            #     text = bytes(text).decode('utf-8')
            # TypeError: 'bytes' object cannot be interpreted as an integer
            # ===
            from PySide2_FAIL import QtWidgets
            from PySide2_FAIL import QtCore
            from PySide2_FAIL import QtGui
            QShortcut = QtWidgets.QShortcut
            qt_backend = "PySide2"
        except: # pylint: disable=bare-except
            from PyQt5 import QtWidgets
            from PyQt5 import QtCore
            from PyQt5 import QtGui
            QShortcut = QtWidgets.QShortcut
            qt_backend = "PyQt5"
    return qt_backend, QtWidgets, QtCore, QtGui, QShortcut
