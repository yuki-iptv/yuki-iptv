'''Qt loader'''
# pylint: disable=no-member, c-extension-no-member, import-outside-toplevel, invalid-name
# SPDX-License-Identifier: GPL-3.0-or-later

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
    except: # pylint: disable=bare-except
        from PyQt5 import QtWidgets
        from PyQt5 import QtCore
        from PyQt5 import QtGui
        QShortcut = QtWidgets.QShortcut
        qt_library = "PyQt5"
    return qt_library, QtWidgets, QtCore, QtGui, QShortcut
