'''M3U editor'''
# pylint: disable=missing-function-docstring, missing-class-docstring, bare-except
# SPDX-License-Identifier: GPL-3.0-only
import os
from pathlib import Path
from unidecode import unidecode
from yuki_iptv.m3u import M3UParser
from yuki_iptv.xspf import parse_xspf
from yuki_iptv.qt6compat import _enum, qaction
from yuki_iptv.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

HOME_FOLDER = ""
try:
    HOME_FOLDER = os.environ['HOME']
except:
    pass

class M3UEditor(QtWidgets.QMainWindow):
    def clear_table(self):
        self.statusBar().clearMessage()
        self.table.clear()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels([])

    def fill_table(self, m3u_data1):
        self.table.clear()
        self.table.setColumnCount(len(self.labels))
        self.table.setRowCount(len(m3u_data1))
        self.table.setHorizontalHeaderLabels(self.labels)
        i = -1
        for channel in m3u_data1:
            i += 1
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(channel['title']))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(channel['tvg-name']))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(channel['tvg-ID']))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(channel['tvg-logo']))
            self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(channel['tvg-group']))
            self.table.setItem(i, 5, QtWidgets.QTableWidgetItem(channel['tvg-url']))
            if 'catchup' in channel:
                self.table.setItem(i, 6, QtWidgets.QTableWidgetItem(channel['catchup']))
                self.table.setItem(
                    i, 7, QtWidgets.QTableWidgetItem(channel['catchup-source'])
                )
                self.table.setItem(
                    i, 8, QtWidgets.QTableWidgetItem(channel['catchup-days'])
                )
            else:
                self.table.setItem(i, 6, QtWidgets.QTableWidgetItem(''))
                self.table.setItem(i, 7, QtWidgets.QTableWidgetItem(''))
                self.table.setItem(i, 8, QtWidgets.QTableWidgetItem(''))
            if 'useragent' in channel:
                self.table.setItem(i, 9, QtWidgets.QTableWidgetItem(channel['useragent']))
                self.table.setItem(i, 10, QtWidgets.QTableWidgetItem(channel['referer']))
            else:
                self.table.setItem(i, 9, QtWidgets.QTableWidgetItem(''))
                self.table.setItem(i, 10, QtWidgets.QTableWidgetItem(''))
            self.table.setItem(i, 11, QtWidgets.QTableWidgetItem(channel['url']))
        self.table.resizeColumnsToContents()

    def select_file(self):
        self.ask_changed(False)
        filename = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.data['_']('selectplaylist'),
            HOME_FOLDER
        )[0]
        if filename:
            m3u_parser = M3UParser(self.data['settings']['udp_proxy'], self.data['_'])
            try:
                file0 = open(filename, 'r')
                filedata = file0.read()
                file0.close()
                is_xspf = '<?xml version="' in filedata and ('http://xspf.org/' in filedata or \
                'https://xspf.org/' in filedata)
                if not is_xspf:
                    m3u_data = m3u_parser.parse_m3u(filedata)[0]
                else:
                    m3u_data = parse_xspf(filedata)[0]
            except:
                m3u_data = False
            if m3u_data:
                self.file_opened = False
                self.fill_table(m3u_data)
                self.statusBar().showMessage(str(filename) + " " + self.data['_']('m3u_loaded'), 0)
                self.file_opened = True
                self.table_changed = False
            else:
                self.clear_table()
                self.statusBar().showMessage(self.data['_']('playlistloaderror'), 0)
                self.file_opened = True
                self.table_changed = False

    def save_file(self):
        m3u_str = '#EXTM3U\n'
        for row in range(self.table.rowCount()):
            output = {}
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item:
                    output[self.table.horizontalHeaderItem(column).text()] = item.text()
            m3u_str += ('#EXTINF:0 tvg-name="{}" tvg-id="{}" tvg-logo="{}"' + \
                        ' tvg-group="{}" tvg-url="{}" catchup="{}" catchup-source="{}"' + \
                        ' catchup-days="{}",{}\n#EXTVLCOPT:http-user-agent={}\n' + \
                        '#EXTVLCOPT:http-referrer={}\n{}\n').format(
                output['tvg-name'],
                output['tvg-id'],
                output['tvg-logo'],
                output['tvg-group'],
                output['tvg-url'],
                output['catchup'],
                output['catchup-source'],
                output['catchup-days'],
                output['title'],
                output['useragent'],
                output['referer'],
                output['url']
            )
        # Writing to file
        save_fname = QtWidgets.QFileDialog.getSaveFileName(
            self,
            self.data['_']('m3u_savefile'),
            HOME_FOLDER,
            self.data['_']('m3u_playlists')
        )[0]
        if save_fname:
            try:
                save_file = open(save_fname, 'w')
                save_file.write(m3u_str)
                save_file.close()
                self.table_changed = False
                self.statusBar().showMessage(self.data['_']('m3u_playlistsaved'), 0)
            except:
                self.statusBar().showMessage(self.data['_']('error'), 0)
        # Cleaning memory
        output = {}
        m3u_str = ""

    def populate_menubar(self):
        # Menubar
        open_action = qaction(self.data['_']('m3u_loadm3u'), self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.select_file)

        save_action = qaction(self.data['_']('m3u_saveas'), self)
        save_action.setShortcut('Ctrl+Shift+S')
        save_action.triggered.connect(self.save_file)

        menubar = self.menuBar()
        file_menu = menubar.addMenu(self.data['_']('m3u_file'))
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)

    def delete_row(self):
        current_row1 = self.table.currentRow()
        if current_row1 != -1:
            self.table.removeRow(current_row1)
            self.table_changed = True

    def add_row(self):
        if not self.table.rowCount():
            self.table.setColumnCount(len(self.labels))
            self.table.setHorizontalHeaderLabels(self.labels)
            self.file_opened = True
        self.table.insertRow(self.table.currentRow() + 1)
        self.table_changed = True

    def replace_all(self):
        for row in range(self.table.rowCount()):
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item:
                    item.setText(item.text().replace(
                        self.data['search_edit'].text(), self.data['replace_edit'].text()
                    ))
                    self.table_changed = True

    def filter_table(self):
        for row1 in range(self.table.rowCount()):
            item1 = self.table.item(row1, self.data['filter_selector'].currentIndex())
            if item1:
                if unidecode(self.data['groupfilter_edit'].text()).lower().strip() in \
                unidecode(item1.text()).lower().strip():
                    self.table.showRow(row1)
                else:
                    self.table.hideRow(row1)

    def move_row(self, direction):
        current_row2 = self.table.currentRow()
        # If row selected
        if current_row2 != -1:
            # Down
            if direction == 1:
                # If selected row is not last row
                check = current_row2 != self.table.rowCount() - 1
            # Up
            elif direction == -1:
                # If selected row is not first row
                check = current_row2 != 0
            if check:
                # Save current selected column
                current_column = self.table.currentColumn()
                # Save current row data
                current_row_data = []
                for i_0, x_0 in enumerate(self.labels): # pylint: disable=unused-variable
                    item2 = self.table.item(current_row2, i_0)
                    if item2:
                        current_row_data.append(item2.text())
                    else:
                        current_row_data.append("")
                # Delete current row
                self.table.removeRow(current_row2)
                # Create new empty row
                self.table.insertRow(current_row2 + direction)
                # Restore row data
                for i_1, x_1 in enumerate(current_row_data):
                    self.table.setItem(
                        current_row2 + direction,
                        i_1,
                        QtWidgets.QTableWidgetItem(x_1)
                    )
                # Set selection to new row
                self.table.setCurrentCell(current_row2 + direction, current_column)
                # Cleaning memory
                current_row_data = []
                # Mark table as changed
                self.table_changed = True

    def populate_toolbar(self):
        # Toolbar
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(16, 16))

        # Search
        self.data['search_edit'] = QtWidgets.QLineEdit()
        self.data['search_edit'].setPlaceholderText(self.data['_']('m3u_find'))
        self.data['search_edit'].setFixedWidth(230)

        # Replace
        self.data['replace_edit'] = QtWidgets.QLineEdit()
        self.data['replace_edit'].setPlaceholderText(self.data['_']('m3u_replacewith'))
        self.data['replace_edit'].setFixedWidth(230)

        # Replace all
        replaceall_btn = QtWidgets.QToolButton()
        replaceall_btn.setText(self.data['_']('m3u_replaceall'))
        replaceall_btn.clicked.connect(self.replace_all)

        # Delete current row
        delete_btn = QtWidgets.QToolButton()
        delete_btn.setIcon(QtGui.QIcon(
            str(Path('yuki_iptv', self.data['icons_folder'], 'trash.png'))
        ))
        delete_btn.setToolTip(self.data['_']('m3u_deleterow'))
        delete_btn.clicked.connect(self.delete_row)

        # Add new empty row
        add_btn = QtWidgets.QToolButton()
        add_btn.setIcon(QtGui.QIcon(
            str(Path('yuki_iptv', self.data['icons_folder'], 'plus.png'))
        ))
        add_btn.setToolTip(self.data['_']('m3u_addrow'))
        add_btn.clicked.connect(self.add_row)

        # Down
        down_btn = QtWidgets.QToolButton()
        down_btn.setIcon(QtGui.QIcon(
            str(Path('yuki_iptv', self.data['icons_folder'], 'arrow-down.png'))
        ))
        down_btn.clicked.connect(lambda: self.move_row(1))

        # Up
        up_btn = QtWidgets.QToolButton()
        up_btn.setIcon(QtGui.QIcon(
            str(Path('yuki_iptv', self.data['icons_folder'], 'arrow-up.png'))
        ))
        up_btn.clicked.connect(lambda: self.move_row(-1))

        # Group filter
        self.data['groupfilter_edit'] = QtWidgets.QLineEdit()
        self.data['groupfilter_edit'].setPlaceholderText(self.data['_']('m3u_filtergroup'))
        self.data['groupfilter_edit'].setToolTip(self.data['_']('m3u_searchterm'))
        self.data['groupfilter_edit'].returnPressed.connect(self.filter_table)

        # Filter selector
        self.data['filter_selector'] = QtWidgets.QComboBox()
        for group in self.labels:
            self.data['filter_selector'].addItem(group)

        # Add widgets to toolbar
        toolbar.addWidget(self.data['search_edit'])
        toolbar.addSeparator()
        toolbar.addWidget(self.data['replace_edit'])
        toolbar.addSeparator()
        toolbar.addWidget(replaceall_btn)
        toolbar.addSeparator()
        toolbar.addWidget(delete_btn)
        toolbar.addSeparator()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(down_btn)
        toolbar.addWidget(up_btn)
        toolbar.addSeparator()
        toolbar.addWidget(self.data['groupfilter_edit'])
        toolbar.addWidget(self.data['filter_selector'])

        self.addToolBar(toolbar)

    def on_cell_changed(self, row, column): # pylint: disable=unused-argument
        if self.file_opened:
            self.table_changed = True

    def __init__(self, _=None, icon=None, icons_folder=None, settings=None):
        super().__init__()
        self.data = {
            '_': _,
            'settings': settings,
            'icons_folder': icons_folder
        }
        self.file_opened = False
        self.table_changed = False

        self.labels = [
            'title', 'tvg-name', 'tvg-id', 'tvg-logo', 'tvg-group',
            'tvg-url', 'catchup', 'catchup-source', 'catchup-days',
            'useragent', 'referer', 'url'
        ]

        self.setWindowTitle(_('m3u_m3ueditor'))
        self.setWindowIcon(icon)
        self.setGeometry(0, 0, 1200, 600)
        self.populate_menubar()
        self.populate_toolbar()

        # Table
        self.table = QtWidgets.QTableWidget(self)
        self.table.cellChanged.connect(self.on_cell_changed)
        self.setCentralWidget(self.table)
        self.statusBar().showMessage(self.data['_']('m3u_ready'), 0)

    def ask_changed(self, callback=False):
        if self.table_changed:
            reply = QtWidgets.QMessageBox.question(
                self,
                self.data['_']('m3u_saveconfirm'),
                "<b>{}</b>".format(self.data['_']('m3u_waschanged')),
                _enum(QtWidgets.QMessageBox, 'StandardButton.Yes') | \
                _enum(QtWidgets.QMessageBox, 'StandardButton.No'),
                _enum(QtWidgets.QMessageBox, 'StandardButton.Yes')
            )
            if reply == _enum(QtWidgets.QMessageBox, 'StandardButton.Yes'):
                if callback:
                    callback()
                self.save_file()

    def closeEvent(self, event): # pylint: disable=invalid-name
        self.ask_changed(event.accept)

    def show(self):
        self.clear_table()
        self.file_opened = False
        self.table_changed = False
        self.statusBar().showMessage(self.data['_']('m3u_ready'), 0)
        super().show()
