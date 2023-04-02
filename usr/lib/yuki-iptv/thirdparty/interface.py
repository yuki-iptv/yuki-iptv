from yuki_iptv.qt import get_qt_library
from yuki_iptv.qt6compat import _enum
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()


class AstInterfaceData:
    settings = {}


def init_interface_widgets(settings1):
    AstInterfaceData.settings = settings1


class cwdg(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tooltip = ""
        self.textQVBoxLayout = QtWidgets.QVBoxLayout()
        self.textUpQLabel = QtWidgets.QLabel()
        myFont = QtGui.QFont()
        myFont.setBold(True)
        self.textUpQLabel.setFont(myFont)
        self.textDownQLabel = QtWidgets.QLabel()
        self.textQVBoxLayout.addWidget(self.textUpQLabel)
        self.textQVBoxLayout.addWidget(self.textDownQLabel)
        self.textQVBoxLayout.setSpacing(5)
        self.allQHBoxLayout = QtWidgets.QGridLayout()
        self.iconQLabel = QtWidgets.QLabel()
        self.progressLabel = QtWidgets.QLabel()
        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setFixedHeight(15)
        self.endLabel = QtWidgets.QLabel()
        self.op = QtWidgets.QGraphicsOpacityEffect()
        self.op.setOpacity(100)
        self.allQHBoxLayout.addWidget(self.iconQLabel, 0, 0)
        self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 0, 1)
        self.allQHBoxLayout.addWidget(self.progressLabel, 3, 0)
        self.allQHBoxLayout.addWidget(self.progressBar, 3, 1)
        self.allQHBoxLayout.addWidget(self.endLabel, 3, 2)
        self.allQHBoxLayout.setSpacing(10)
        self.setLayout(self.allQHBoxLayout)
        self.progressBar.setStyleSheet('''
          background-color: #C0C6CA;
          border: 0px;
          padding: 0px;
          height: 5px;
        ''')
        self.setStyleSheet('''
          QProgressBar::chunk {
            background: #7D94B0;
            width:5px
          }
        ''')

    def setTextUp(self, text):
        self.textUpQLabel.setText(text)

    def setTextDown(self, text, tooltip):
        progTooltip = tooltip
        self.tooltip = progTooltip
        self.setToolTip(progTooltip)
        self.textDownQLabel.setText(text)

    def setTextProgress(self, text):
        self.progressLabel.setText(text)

    def setTextEnd(self, text):
        self.endLabel.setText(text)

    def setIcon(self, image):
        self.iconQLabel.setPixmap(image.pixmap(QtCore.QSize(32, 32)))

    def setProgress(self, progress_val):
        self.op.setOpacity(100)
        self.progressBar.setGraphicsEffect(self.op)
        self.progressBar.setFormat('')
        self.progressBar.setValue(progress_val)

    def hideProgress(self):
        self.op.setOpacity(0)
        self.progressBar.setGraphicsEffect(self.op)


class cwdg_simple(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.textQHBoxLayout = QtWidgets.QHBoxLayout()
        self.textUpQLabel = QtWidgets.QLabel()
        myFont = QtGui.QFont()
        myFont.setBold(True)
        self.textUpQLabel.setFont(myFont)
        self.iconQLabel = QtWidgets.QLabel()
        if AstInterfaceData.settings['gui'] == 1:
            self.textQHBoxLayout.addWidget(self.iconQLabel)
        self.textQHBoxLayout.addWidget(self.textUpQLabel)
        self.textQHBoxLayout.addStretch()
        self.textQHBoxLayout.setSpacing(15)
        self.setLayout(self.textQHBoxLayout)

    def setTextUp(self, text):
        self.textUpQLabel.setText(text)

    def setTextDown(self, text, tooltip):
        pass

    def setTextProgress(self, text):
        pass

    def setTextEnd(self, text):
        pass

    def setIcon(self, image):
        self.iconQLabel.setPixmap(image.pixmap(QtCore.QSize(32, 20)))

    def setProgress(self, progress_val):
        pass

    def hideProgress(self):
        pass


class settings_scrollable_window(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initScroll()

    def initScroll(self):
        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(
            _enum(QtCore.Qt, 'ScrollBarPolicy.ScrollBarAlwaysOn')
        )
        self.scroll.setHorizontalScrollBarPolicy(
            _enum(QtCore.Qt, 'ScrollBarPolicy.ScrollBarAlwaysOn')
        )
        self.scroll.setWidgetResizable(True)
        self.setCentralWidget(self.scroll)


class ClickableLabel(QtWidgets.QLabel):
    def __init__(self, whenClicked, win, parent=None):
        QtWidgets.QLabel.__init__(self, win)
        self._whenClicked = whenClicked

    def mouseReleaseEvent(self, event):
        self._whenClicked(event)


class KeySequenceEdit(QtWidgets.QKeySequenceEdit):
    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.setKeySequence(QtGui.QKeySequence(self.keySequence()))
