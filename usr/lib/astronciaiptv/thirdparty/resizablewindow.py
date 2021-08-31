from astroncia.qt import get_qt_backend
qt_backend, QtWidgets, QtCore, QtGui, QShortcut = get_qt_backend()

class C(QtWidgets.QWidget):
    def __init__(N, parent, e, ignoreResize):
        QtWidgets.QWidget.__init__(N, parent)
        if e == QtCore.Qt.TopEdge:
            if not ignoreResize:
                N.setCursor(QtCore.Qt.SizeVerCursor)
                N.rszf = N.rszup
        else:N.setCursor(QtCore.Qt.SizeVerCursor);N.rszf = N.rszdown
        N.mp = None
    def rszup(N, dl):I = N.window();height = max(I.minimumHeight(), I.height() - dl.y());geo = I.geometry();geo.setTop(geo.bottom() - height);I.setGeometry(geo);N.window().callback(I.height())
    def rszdown(N, dl):I = N.window();height = max(I.minimumHeight(), I.height() + dl.y());I.resize(I.width(), height);N.window().callback(height)
    def mousePressEvent(N, event):
        if event.button() == QtCore.Qt.LeftButton:N.mp = event.pos()
    def mouseMoveEvent(N, event):
        if N.mp is not None:dl = event.pos() - N.mp;
        try:
            N.rszf(dl)
        except:
            pass
    def mouseReleaseEvent(N, event):N.mp = None

class ResizableWindow(QtWidgets.QMainWindow):
    x1 = 4*2
    def __init__(y, ignoreResize):QtWidgets.QMainWindow.__init__(y);y.setWindowFlags(QtCore.Qt.FramelessWindowHint);y.array = [C(y, QtCore.Qt.TopEdge, ignoreResize),C(y, QtCore.Qt.BottomEdge, ignoreResize)]
    @property
    def alcSize(y):return y.x1
    def setalcSize(y, X):
        if X == y.x1:return;
        y.x1 = max(2, X);y.upd()
    def upd(y):y.setContentsMargins(*[y.alcSize] * 4);n = y.rect();irec = n.adjusted(y.alcSize,y.alcSize,-y.alcSize,-y.alcSize);y.array[0].setGeometry(irec.left(), 0, irec.width(), y.alcSize);y.array[1].setGeometry(y.alcSize, irec.top() + irec.height(),irec.width(), y.alcSize)
    def resizeEvent(y, s):QtWidgets.QMainWindow.resizeEvent(y, s);y.upd()
    def moveEvent(y,e):y.callback_move(e);super(ResizableWindow,y).moveEvent(e)
    def mousePressEvent(y,s):y.oldpos = s.globalPos()
    def mouseMoveEvent(y,s):
        try:f = QtCore.QPoint(s.globalPos() - y.oldpos);y.move(y.x() + f.x(), y.y() + f.y());y.oldpos = s.globalPos()
        except:pass
