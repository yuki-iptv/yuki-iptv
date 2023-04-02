#
# Copyright (c) 2021-2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 yuki-chan-nya
#
# This file is part of yuki-iptv.
#
# yuki-iptv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# yuki-iptv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with yuki-iptv  If not, see <http://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License
# https://creativecommons.org/licenses/by/4.0/
#

def get_qt_library():
    '''Get correct Qt library - PyQt6/5'''
    qt_library = "none"
    QShortcut = False
    QtWidgets = False
    QtCore = False
    QtGui = False
    try:
        from PyQt6 import QtWidgets
        from PyQt6 import QtCore
        from PyQt6 import QtGui
        QShortcut = QtGui.QShortcut
        qt_library = "PyQt6"
    except:
        from PyQt5 import QtWidgets
        from PyQt5 import QtCore
        from PyQt5 import QtGui
        QShortcut = QtWidgets.QShortcut
        qt_library = "PyQt5"
    return qt_library, QtWidgets, QtCore, QtGui, QShortcut
