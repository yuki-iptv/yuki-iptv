from astroncia.qt import get_qt_backend
qt_backend, QtWidgets, QtCore, QtGui, QShortcut = get_qt_backend()
D=max
B=None
class C(QtWidgets.QWidget):
        def __init__(A,parent):QtWidgets.QWidget.__init__(A,parent);A.setCursor(QtCore.Qt.SizeVerCursor);A.resizeFunc=A.resizeBottom;A.mousePos=B
        def resizeBottom(B,delta):
            A=B.window();C=D(A.minimumHeight(),A.height()+delta.y());A.resize(A.width(),C);
            B.window().callback(C)
        def mousePressEvent(B,event):
                A=event
                if A.button()==QtCore.Qt.LeftButton:B.mousePos=A.pos()
        def mouseMoveEvent(A,event):
                if A.mousePos is not B:C=event.pos()-A.mousePos;A.resizeFunc(C)
        def mouseReleaseEvent(A,event):A.mousePos=B
class ResizableWindow(QtWidgets.QMainWindow):
        _alcSize=8
        def __init__(A):QtWidgets.QMainWindow.__init__(A);A.setWindowFlags(QtCore.Qt.FramelessWindowHint);A.classes=[C(A)]
        @property
        def alcSize(self):return self._alcSize
        def setalcSize(A,size):
                if size==A._alcSize:return
                A._alcSize=D(2,size);A.updatealcs()
        def updatealcs(A):A.setContentsMargins(*[A.alcSize]*4);C=A.rect();B=C.adjusted(A.alcSize,A.alcSize,-A.alcSize,-A.alcSize);A.classes[0].setGeometry(A.alcSize,B.top()+B.height(),B.width(),A.alcSize)
        def resizeEvent(A,event):QtWidgets.QMainWindow.resizeEvent(A,event);A.updatealcs()
        def moveEvent(A,e):A.callback_move(e);super(ResizableWindow,A).moveEvent(e)
        def mousePressEvent(A,event):A.old_position = event.globalPos()
        def mouseMoveEvent(A,event):
            try:
                calc_d = QtCore.QPoint(event.globalPos() - A.old_position);A.move(A.x() + calc_d.x(), A.y() + calc_d.y());
                A.old_position = event.globalPos()
            except: # pylint: disable=bare-except
                pass
