#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 yuki-chan-nya <yukichandev@proton.me>
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
from yuki_iptv.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()


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


def qaction(arg1, arg2):
    if qt_library == 'PyQt6':
        func = QtGui.QAction
    else:
        func = QtWidgets.QAction
    return func(arg1, arg2)
