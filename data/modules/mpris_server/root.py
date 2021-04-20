import logging

from .base import INTERFACE as _INTERFACE, NAME
from .interface import MprisInterface


logger = logging.getLogger(__name__)


class Root(MprisInterface):
    """
    <node>
      <interface name="org.mpris.MediaPlayer2">
        <method name="Raise"/>
        <method name="Quit"/>
        <property name="CanQuit" type="b" access="read"/>
        <property name="CanRaise" type="b" access="read"/>
        <property name="Fullscreen" type="b" access="readwrite"/>
        <property name="CanSetFullscreen" type="b" access="read"/>
        <property name="HasTrackList" type="b" access="read"/>
        <property name="Identity" type="s" access="read"/>
        <property name="DesktopEntry" type="s" access="read"/>
        <property name="SupportedUriSchemes" type="as" access="read"/>
        <property name="SupportedMimeTypes" type="as" access="read"/>
      </interface>
    </node>
    """

    INTERFACE = _INTERFACE

    def Raise(self):
        logger.debug("%s.Raise called", self.INTERFACE)
        self.adapter.set_raise(True)

    def Quit(self):
        logger.debug("%s.Quit called", self.INTERFACE)
        self.adapter.quit()

    @property
    def Fullscreen(self):
        self.log_trace("Getting %s.Fullscreen", self.INTERFACE)
        return self.adapter.get_fullscreen()

    @Fullscreen.setter
    def Fullscreen(self, value):
        logger.debug("Setting %s.Fullscreen to %s", self.INTERFACE, value)
        self.adapter.set_fullscreen(value)

    @property
    def DesktopEntry(self):
        self.log_trace("Getting %s.DesktopEntry", self.INTERFACE)
        return self.adapter.get_desktop_entry()

    @property
    def SupportedUriSchemes(self):
        self.log_trace("Getting %s.SupportedUriSchemes", self.INTERFACE)
        return self.adapter.get_uri_schemes()

    @property
    def SupportedMimeTypes(self):
        self.log_trace("Getting %s.SupportedMimeTypes", self.INTERFACE)
        return self.adapter.get_mime_types()

    @property
    def Identity(self) -> str:
        return self.name

    @property
    def CanQuit(self) -> bool:
        return self.adapter.can_quit()

    @property
    def CanRaise(self) -> bool:
        return self.adapter.can_raise()

    @property
    def CanSetFullscreen(self) -> bool:
        return self.adapter.can_fullscreen()

    @property
    def HasTrackList(self) -> bool:
        return self.adapter.has_tracklist()