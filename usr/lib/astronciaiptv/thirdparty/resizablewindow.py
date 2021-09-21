from contextlib import suppress
from astroncia.qt import get_qt_library
from astroncia.qt6compat import globalPos, getX, getY
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

class C(QtWidgets.QWidget):
    def __init__(N, parent, e, sepPlaylist, add_sep_flag, del_sep_flag, resize_func):
        QtWidgets.QWidget.__init__(N,parent);N.add_sep_flag=add_sep_flag;N.del_sep_flag=del_sep_flag;N.resize_func=resize_func
        if e==QtCore.Qt.TopEdge:
            if not sepPlaylist:
                N.setCursor(QtCore.Qt.SizeVerCursor);N.rszf = N.rszup
            else:
                N.setCursor(QtCore.Qt.SizeVerCursor);N.rszf = N.rszup_1
        elif e==QtCore.Qt.BottomEdge:
            N.setCursor(QtCore.Qt.SizeVerCursor);N.rszf = N.rszdown
        elif e==QtCore.Qt.LeftEdge:
            if sepPlaylist:N.setCursor(QtCore.Qt.SizeHorCursor);N.rszf = N.rszleft
        elif e==QtCore.Qt.RightEdge:
            if sepPlaylist:N.setCursor(QtCore.Qt.SizeHorCursor);N.rszf = N.rszright
        N.mp=None
    def rszup(N, dl):I=N.window();height=max(I.minimumHeight(),I.height()-dl.y());geo = I.geometry();geo.setTop(geo.bottom() - height);I.setGeometry(geo);N.window().callback(I.height())
    def rszup_1(N, dl):N.add_sep_flag();I=N.window();height=max(I.minimumHeight(), I.height() - dl.y());geo = I.geometry();geo.setTop(geo.bottom() - height);I.setGeometry(geo);N.window().callback(I.height())
    def rszdown(N, dl):I = N.window();height = max(I.minimumHeight(), I.height() + dl.y());I.resize(I.width(), height);N.window().callback(height)
    def rszleft(N, dl):
        I=N.window();width=max(I.minimumWidth(),I.width()-dl.x());geo=I.geometry();geo.setLeft(geo.right()-width);I.setGeometry(geo);
        N.resize_func(True, I.width())
    def rszright(N, dl):
        I=N.window();width=max(I.minimumWidth(),I.width()+dl.x());I.resize(width,I.height());
    def mousePressEvent(N, event):
        if event.button() == QtCore.Qt.LeftButton:N.mp = event.pos();
    def mouseMoveEvent(N, event):
        if N.mp is not None:dl = event.pos() - N.mp;
        with suppress(Exception):N.rszf(dl)
    def mouseReleaseEvent(N, event):N.mp = None

class ResizableWindow(QtWidgets.QMainWindow):
    x1 = 4*2
    def __init__(y,sepPlaylist,add_sep_flag=None,del_sep_flag=None,resize_func=None):QtWidgets.QMainWindow.__init__(y);y.setWindowFlags(QtCore.Qt.FramelessWindowHint);y.array=[C(y,QtCore.Qt.TopEdge,sepPlaylist,add_sep_flag,del_sep_flag,resize_func),C(y,QtCore.Qt.BottomEdge,sepPlaylist,add_sep_flag,del_sep_flag,resize_func),C(y,QtCore.Qt.LeftEdge,sepPlaylist,add_sep_flag,del_sep_flag,resize_func),C(y,QtCore.Qt.RightEdge,sepPlaylist,add_sep_flag,del_sep_flag,resize_func)]
    @property
    def alcSize(y):return y.x1
    def setalcSize(y, X):
        if X == y.x1:return;
        y.x1 = max(int(4/2),X);y.upd()
    def upd(y):y.setContentsMargins(*[y.alcSize]*int(44/11));n=y.rect();irec=n.adjusted(y.alcSize,y.alcSize,-y.alcSize,-y.alcSize);y.array[0].setGeometry(irec.left(),0,irec.width(),y.alcSize);y.array[1].setGeometry(y.alcSize,irec.top()+irec.height(),irec.width(),y.alcSize);y.array[2].setGeometry(0,irec.top(),y.alcSize,irec.height());y.array[3].setGeometry(irec.left()+irec.width(),irec.top(),y.alcSize,irec.height())
    def resizeEvent(y,s):QtWidgets.QMainWindow.resizeEvent(y,s);y.upd()
    def moveEvent(y,e):y.callback_move(e);super(ResizableWindow,y).moveEvent(e)
    def mousePressEvent(y,s):y.oldpos = globalPos(s)
    def mouseMoveEvent(y,s):
        with suppress(Exception):f=QtCore.QPoint(globalPos(s)-y.oldpos);y.move(getX(y)+getX(f),getY(y)+getY(f));y.oldpos=globalPos(s)