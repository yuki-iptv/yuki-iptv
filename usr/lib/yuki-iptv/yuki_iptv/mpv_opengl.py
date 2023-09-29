#
# Copyright (c) 2023 Ame-chan-angel <amechanangel@proton.me>
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
# along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License.
# https://fontawesome.com/
# https://creativecommons.org/licenses/by/4.0/
#
try:
    from PySide6 import QtCore
    from PySide6 import QtOpenGLWidgets
    from PySide6.QtGui import QOpenGLContext

    opengl_widget = QtOpenGLWidgets.QOpenGLWidget
    use_slot = QtCore.Slot
except Exception:
    try:
        from PyQt6 import QtCore
        from PyQt6 import QtOpenGLWidgets
        from PyQt6.QtGui import QOpenGLContext

        opengl_widget = QtOpenGLWidgets.QOpenGLWidget
        use_slot = QtCore.pyqtSlot
    except Exception:
        from PyQt5 import QtCore, QtWidgets
        from PyQt5.QtGui import QOpenGLContext

        opengl_widget = QtWidgets.QOpenGLWidget
        use_slot = QtCore.pyqtSlot

# https://github.com/feeluown/FeelUOwn/blob/25a0a714b39a0a8e12cd09dd9b7c92bf3c75667c/feeluown/gui/widgets/mpv.py

from thirdparty.mpv import MpvRenderContext, MpvGlGetProcAddressFn


def get_process_address(_, name):
    glctx = QOpenGLContext.currentContext()
    if glctx is None:
        return 0
    return int(glctx.getProcAddress(name))


class MPVOpenGLWidget(opengl_widget):
    def __init__(self, app, player):
        super().__init__()
        self.app = app
        self._mpv = player
        self.ctx = None
        self._proc_addr_wrapper = MpvGlGetProcAddressFn(get_process_address)

    def initializeGL(self):
        self.ctx = MpvRenderContext(
            self._mpv,
            "opengl",
            opengl_init_params={"get_proc_address": self._proc_addr_wrapper},
        )
        self.ctx.update_cb = self.on_update

    def shutdown(self):
        if self.ctx is not None:
            self.ctx.free()
            self.ctx = None

    def paintGL(self):
        if self.ctx is None:
            self.initializeGL()
            assert self.ctx is not None
        ratio = self.app.devicePixelRatio()
        w = int(self.width() * ratio)
        h = int(self.height() * ratio)
        opengl_fbo = {"w": w, "h": h, "fbo": self.defaultFramebufferObject()}
        self.ctx.render(flip_y=True, opengl_fbo=opengl_fbo)

    @use_slot()
    def maybe_update(self):
        if self.window().isMinimized():
            self.makeCurrent()
            self.paintGL()
            self.context().swapBuffers(self.context().surface())
            self.doneCurrent()
        else:
            self.update()

    def on_update(self, ctx=None):
        QtCore.QMetaObject.invokeMethod(self, "maybe_update")
