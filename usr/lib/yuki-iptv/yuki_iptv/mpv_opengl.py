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
import os
import logging
import platform
import traceback
from pathlib import Path
from yuki_iptv.qt import get_qt_library, show_exception

# https://github.com/feeluown/FeelUOwn/blob/25a0a714b39a0a8e12cd09dd9b7c92bf3c75667c/feeluown/gui/widgets/mpv.py

logger = logging.getLogger(__name__)
qt_library, QtWidgets, QtCore, QtGui, QShortcut, QtOpenGLWidgets = get_qt_library()

if platform.system() == "Windows" or platform.system() == "Darwin":
    os.environ["PATH"] = (
        str(Path(Path(os.path.dirname(__file__)).parent, "bin"))
        + os.pathsep
        + os.environ["PATH"]
    )

try:
    from thirdparty.mpv import MpvRenderContext, MpvGlGetProcAddressFn
except Exception as e3:
    logger.warning("ERROR")
    logger.warning("")
    e3_traceback = traceback.format_exc()
    logger.warning(e3_traceback)
    show_exception(e3, e3_traceback)
    raise e3

if qt_library == "PySide6":
    use_slot = QtCore.Slot
else:
    use_slot = QtCore.pyqtSlot


def get_process_address(_, name):
    glctx = QtGui.QOpenGLContext.currentContext()
    if glctx is None:
        return 0
    return int(glctx.getProcAddress(name))


class MPVOpenGLWidget(QtOpenGLWidgets.QOpenGLWidget):
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
