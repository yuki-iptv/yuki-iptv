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
from data.modules.astroncia.qt import get_qt_backend
from data.modules.astroncia.lang import _ as __
qt_backend, QtWidgets, QtCore, QtGui, QShortcut = get_qt_backend()

def _(str):
    return '{}{}'.format('&', __(str))

def init_astroncia_menubar(data, app):
    pass
    #exitAction = QtWidgets.QAction('&Exit', data)
    #exitAction.triggered.connect(app.quit)

    #fileMenu = data.menu_bar_qt.addMenu(_('error2'))
    #fileMenu.addAction(exitAction)