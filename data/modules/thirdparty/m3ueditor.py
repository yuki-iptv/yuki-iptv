import sys
import os
import pandas as pd
from data.modules.astroncia.qt import get_qt_backend
qt_backend, QtWidgets, QtCore, QtGui, QShortcut = get_qt_backend()
from pathlib import Path
from data.modules.astroncia.extgrp import parse_extgrp
from data.modules.astroncia.lang import _ as get_translation

home_folder = ""
try:
    home_folder = os.environ['HOME']
except: # pylint: disable=bare-except
    pass

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, df = pd.DataFrame(), parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent=None)
        self._df = df
        self.setChanged = False
        self.dataChanged.connect(self.setModified)

    def setModified(self):
        self.setChanged = True

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            try:
                return self._df.columns.tolist()[section]
            except (IndexError, ):
                return None
        elif orientation == QtCore.Qt.Vertical:
            try:
                return self._df.index.tolist()[section]
            except (IndexError, ):
                return None

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if index.isValid():
            if (role == QtCore.Qt.EditRole):
                return self._df.values[index.row()][index.column()]
            elif (role == QtCore.Qt.DisplayRole):
                return self._df.values[index.row()][index.column()]
        return None

    def setData(self, index, value, role):
        row = self._df.index[index.row()]
        col = self._df.columns[index.column()]
        self._df.values[row][col] = value
        self.dataChanged.emit(index, index)
        return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self._df.columns)

    def sort(self, column, order):
        colname = self._df.columns.tolist()[column]
        self.layoutAboutToBeChanged.emit()
        self._df.sort_values(colname, ascending= order == QtCore.Qt.AscendingOrder, inplace=True)
        self._df.reset_index(inplace=True, drop=True)
        self.layoutChanged.emit()

class Viewer(QtWidgets.QMainWindow):
    def __init__(self, parent=None, lang=None, iconsFolder=None):
      super(Viewer, self).__init__(parent)
      self.iconsFolder = iconsFolder
      self.LANG = lang
      self.df = None
      self.filename = ""
      self.fname = ""
      self.csv_file = ""
      self.m3u_file = ""
      self.setGeometry(0, 0, 1000, 600)
      self.lb = QtWidgets.QTableView()
      self.lb.horizontalHeader().hide()
      self.model =  PandasModel()
      self.lb.setModel(self.model)
      self.lb.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked)
      self.lb.setSelectionBehavior(self.lb.SelectRows)
      self.lb.setSelectionMode(self.lb.SingleSelection)
      self.lb.setDragDropMode(self.lb.InternalMove)
      self.setStyleSheet(stylesheet(self))
      self.lb.setAcceptDrops(True)
      self.setCentralWidget(self.lb)
      self.setContentsMargins(10, 10, 10, 10)
      self.statusBar().showMessage(get_translation('m3u_ready'), 0)
      self.setWindowTitle(get_translation('m3u_m3ueditor'))
      self.setWindowIcon(QtGui.QIcon.fromTheme("multimedia-playlist"))
      self.createMenuBar()
      self.createToolBar()
      self.lb.setFocus()

    def convert_to_csv(self):
        mylist = [line.strip() for line in open(self.m3u_file, 'r').read().splitlines() if not line.strip().startswith('#EXTVLCOPT:')]
        mylist = parse_extgrp(mylist)

        headers = ['tvg-name', 'group-title', 'tvg-logo', 'tvg-id', 'url']
        group = ""
        ch = ""
        url = ""
        id = ""
        logo = ""
        csv_content = ""
        csv_content += '\t'.join(headers)
        csv_content += "\n"
        for x in range(1, len(mylist)-1):
            line = mylist[x]
            nextline = mylist[x+1]
            if line.startswith("#EXTINF") and not "**********" in line:
                if 'tvg-name-astroncia-iptv="' in line:
                    ch = line.partition('tvg-name-astroncia-iptv="')[2].partition('"')[0]
                elif 'tvg-name="' in line:
                    ch = line.partition('tvg-name="')[2].partition('"')[0]
                elif 'tvg-name=' in line:
                    ch = line.partition('tvg-name=')[2].partition(' tvg')[0]
                else:
                    ch = line.rpartition(',')[2]
                if ch == "":
                    ch = get_translation('m3u_noname')
                ch = ch.replace('"', '')

                if 'group-title="' in line:
                    group = line.partition('group-title="')[2].partition('"')[0]

                elif "group-title=" in line:
                    group = line.partition('group-title=')[2].partition(' tvg')[0]
                else:
                    group = "TV"
                group = group.replace('"', '')

                if 'tvg-id="' in line:
                    id = line.partition('tvg-id="')[2].partition('"')[0]
                elif 'tvg-id=' in line:
                    id = line.partition('tvg-id=')[2].partition(' ')[0]
                else:
                    id = ""
                id = id.replace('"', '')

                url = nextline
                if 'tvg-logo="' in line:
                    logo = line.partition('tvg-logo="')[2].partition('"')[0]
                elif 'tvg-logo=' in line:
                    logo = line.partition('tvg-logo=')[2].partition(' ')[0]
                else:
                    logo = ""
                csv_content += ('{}\t{}\t{}\t{}\t{}\n'.format(ch, group, logo, id, url))
        self.fname = self.m3u_file.rpartition("/")[2].replace(".m3u", ".csv")
        self.csv_file = '/tmp/{}'.format(self.fname)
        with open(self.csv_file, 'w') as f:
            f.write(csv_content)

    def closeEvent(self, event):
        if  self.model.setChanged == True:
            quit_msg = "<b>{}</b>".format(get_translation('m3u_waschanged'))
            reply = QtWidgets.QMessageBox.question(self, get_translation('m3u_saveconfirm'),
                     quit_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                event.accept()
                self.writeCSV()

    def createMenuBar(self):
        bar=self.menuBar()
        self.filemenu=bar.addMenu(get_translation('m3u_file'))
        self.separatorAct = self.filemenu.addSeparator()
        self.filemenu.addAction(QtGui.QIcon.fromTheme("document-open"), get_translation('m3u_loadm3u'),  self.loadM3U, QtGui.QKeySequence.Open)
        self.filemenu.addAction(QtGui.QIcon.fromTheme("document-save-as"), "{} ...".format(get_translation('m3u_saveas')),  self.writeCSV, QtGui.QKeySequence.SaveAs)

    def createToolBar(self):
        tb = self.addToolBar("Tools")
        tb.setIconSize(QtCore.QSize(16, 16))

        self.findfield = QtWidgets.QLineEdit(placeholderText = "{} ...".format(get_translation('m3u_find')))
        self.findfield.setClearButtonEnabled(True)
        self.findfield.setFixedWidth(200)
        tb.addWidget(self.findfield)

        tb.addSeparator()

        self.replacefield = QtWidgets.QLineEdit(placeholderText = "{} ...".format(get_translation('m3u_replacewith')))
        self.replacefield.setClearButtonEnabled(True)
        self.replacefield.setFixedWidth(200)
        tb.addWidget(self.replacefield)

        tb.addSeparator()

        btn = QtWidgets.QToolButton()
        btn.setText(get_translation('m3u_replaceall'))
        btn.setToolTip(get_translation('m3u_replaceall'))
        btn.clicked.connect(self.replace_in_table)
        tb.addWidget(btn)

        tb.addSeparator()

        del_btn = QtWidgets.QToolButton()
        del_btn.setIcon(QtGui.QIcon(str(Path('data', self.iconsFolder, 'trash.png'))))
        del_btn.setToolTip(get_translation('m3u_deleterow'))
        del_btn.clicked.connect(self.del_row)
        tb.addWidget(del_btn)

        tb.addSeparator()

        add_btn = QtWidgets.QToolButton()
        add_btn.setIcon(QtGui.QIcon(str(Path('data', self.iconsFolder, 'plus.png'))))
        add_btn.setToolTip(get_translation('m3u_addrow'))
        add_btn.clicked.connect(self.add_row)
        tb.addWidget(add_btn)

        move_down_btn = QtWidgets.QToolButton()
        move_down_btn.setIcon(QtGui.QIcon(str(Path('data', self.iconsFolder, 'arrow-down.png'))))
        move_down_btn.setToolTip(get_translation('m3u_movedown'))
        move_down_btn.clicked.connect(self.move_down)
        tb.addWidget(move_down_btn)

        move_up_up = QtWidgets.QToolButton()
        move_up_up.setIcon(QtGui.QIcon(str(Path('data', self.iconsFolder, 'arrow-up.png'))))
        move_up_up.setToolTip(get_translation('m3u_moveup'))
        move_up_up.clicked.connect(self.move_up)
        tb.addWidget(move_up_up)

        tb.addSeparator()

        self.filter_field = QtWidgets.QLineEdit(placeholderText = get_translation('m3u_filtergroup'))
        self.filter_field.setClearButtonEnabled(True)
        self.filter_field.setToolTip(get_translation('m3u_searchterm'))
        self.filter_field.setFixedWidth(200)
        self.filter_field.returnPressed.connect(self.filter_table)
        self.filter_field.textChanged.connect(self.update_filter)
        tb.addWidget(self.filter_field)

        self.filter_combo = QtWidgets.QComboBox()
        self.filter_combo.setToolTip(get_translation('m3u_choosecolumn'))
        self.filter_combo.setFixedWidth(100)
        self.filter_combo.addItems(['tvg-name', 'group-title', 'tvg-logo', 'tvg-id', 'url'])
        self.filter_combo.currentIndexChanged.connect(self.filter_table)
        tb.addWidget(self.filter_combo)

    def move_down(self):
        if self.model.rowCount() < 1:
            return
        i = self.lb.selectionModel().selection().indexes()[0].row()
        b, c = self.df.iloc[i].copy(), self.df.iloc[i+1].copy()
        self.df.iloc[i],self.df.iloc[i+1] = c,b
        self.model.setChanged = True
        self.lb.selectRow(i+1)

    def move_up(self):
        if self.model.rowCount() < 1:
            return
        i = self.lb.selectionModel().selection().indexes()[0].row()
        b, c = self.df.iloc[i].copy(), self.df.iloc[i-1].copy()
        self.df.iloc[i],self.df.iloc[i-1] = c,b
        self.model.setChanged = True
        self.lb.selectRow(i-1)

    def del_row(self):
        if self.model.rowCount() < 1:
            return
        i = self.lb.selectionModel().selection().indexes()[0].row()
        if len(self.df.index) > 0:
            self.df = self.df.drop(self.df.index[i])
            self.model = PandasModel(self.df)
            self.lb.setModel(self.model)
            self.model.setChanged = True
            self.lb.selectRow(i)

    def add_row(self):
        if self.model.rowCount() < 1:
            return
        i = self.lb.selectionModel().selection().indexes()[0].row()
        newrow = {0:'name', 1:'title', 2:'logo', 3:'id', 4:'url'}
        self.df = self.df.append(newrow, ignore_index=True)
        self.model = PandasModel(self.df)
        self.lb.setModel(self.model)
        self.model.setChanged = True
        self.lb.selectRow(self.model.rowCount() - 1)

    def openFile(self, path=None):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, get_translation('m3u_openfile'), home_folder,get_translation('m3u_playlists'))
        if path:
            return path

    def loadM3U(self):
        if self.model.setChanged == True:
            save_msg = "<b>{}</b>".format(get_translation('m3u_waschanged'))
            reply = QtWidgets.QMessageBox.question(self, get_translation('m3u_saveconfirm'),
                     save_msg, QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                self.writeCSV()
                self.open_m3u()
            else:
                self.model.setChanged = False
                self.open_m3u()
        else:
            self.model.setChanged = False
            self.open_m3u()

    def open_m3u(self):
        fileName = self.openFile()
        if fileName:
            self.m3u_file = fileName
            self.convert_to_csv()
            f = open(self.csv_file, 'r+b')
            with f:
                self.filename = fileName
                self.df = pd.read_csv(f, delimiter = '\t', keep_default_na = False, low_memory=False, header=None)
                self.model = PandasModel(self.df)
                self.lb.setModel(self.model)
                self.lb.resizeColumnsToContents()
                self.lb.selectRow(0)
                self.statusBar().showMessage("{} ".format(fileName) + get_translation('m3u_loaded'), 0)
                self.model.setChanged = False
                self.lb.verticalHeader().setMinimumWidth(24)


    def writeCSV(self):
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self, get_translation('m3u_savefile'), self.fname.replace(".csv", ".m3u"),get_translation('m3u_m3ufiles'), home_folder)
        if fileName:
            # save temporary csv
            f = open(self.csv_file, 'w')
            newModel = self.model
            dataFrame = newModel._df.copy()
            dataFrame.to_csv(f, sep='\t', index = False, header = False)
            f.close()

            # convert to m3u
            mylist = open(self.csv_file, 'r').read().splitlines()
            group = ""
            ch = ""
            url = ""
            id = ""
            logo = ""
            m3u_content = ""

            headers = ['tvg-name', 'group-title', 'tvg-logo', 'tvg-id', 'url']
            m3u_content += "#EXTM3U\n"

            for x in range(1, len(mylist)):
                line = mylist[x].split('\t')
                ch = line[0]
                group = line[1]
                logo = line[2]
                id = line[3]
                url = line[4]

                m3u_content += '#EXTINF:-1 tvg-name="{}" group-title="{}" tvg-logo="{}" tvg-id="{}",{}\n{}\n'.format(ch, group, logo, id, ch, url)

            with open(fileName, 'w') as f:
                f.write(m3u_content)

            self.model.setChanged = False


    def replace_in_table(self):
        if self.model.rowCount() < 1:
            return
        searchterm = self.findfield.text()
        replaceterm = self.replacefield.text()
        if searchterm == "" or replaceterm == "":
            return
        else:
            if len(self.df.index) > 0:
                self.df.replace(searchterm, replaceterm, inplace=True, regex=True)
                self.lb.resizeColumnsToContents()

    def filter_table(self):
        if self.model.rowCount() < 1:
            return
        index = self.filter_combo.currentIndex()
        searchterm = self.filter_field.text()
        df_filtered = self.df[self.df[index].str.contains(searchterm, case=False)]
        self.model = PandasModel(df_filtered)
        self.lb.setModel(self.model)
        self.lb.resizeColumnsToContents()

    def update_filter(self):
        if self.filter_field.text() == "":
            self.filter_table()

def stylesheet(self):
        return """
    QMenuBar
        {
            background: transparent;
            border: 0px;
        }

    QMenuBar:hover
        {
            background: #d3d7cf;
        }

    QTableView
        {
            border: 1px solid #d3d7cf;
            border-radius: 0px;
            font-size: 8pt;
            background: #eeeeec;
            selection-color: #ffffff
        }
    QTableView::item:hover
        {
            color: black;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #729fcf, stop:1 #d3d7cf);
        }

    QTableView::item:selected {
            color: #F4F4F4;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #6169e1, stop:1 #3465a4);
        }

    QTableView QTableCornerButton::section {
            background: #D6D1D1;
            border: 0px outset black;
        }

    QHeaderView:section {
            background: #d3d7cf;
            color: #555753;
            font-size: 8pt;
        }

    QHeaderView:section:checked {
            background: #204a87;
            color: #ffffff;
        }

    QStatusBar
        {
        font-size: 7pt;
        color: #555753;
        }

    """

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = Viewer()
    main.show()
    sys.exit(app.exec_())
