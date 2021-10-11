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
from astroncia.time import print_with_time

class astroncia_data: # pylint: disable=too-few-public-methods
    pass

astroncia_data.qt6_disable_printed = False

def get_qt_library():
    qt_library = "none"
    QShortcut = False
    QtWidgets = False
    QtCore = False
    QtGui = False
    try:
        if '--disable-qt6' in sys.argv or True:
            if not astroncia_data.qt6_disable_printed:
                astroncia_data.qt6_disable_printed = True
                #print_with_time("Qt6 force disabled\n")
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
