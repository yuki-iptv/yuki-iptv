import logging

from gi.repository import GLib
import pydbus

from .player import Player
from .playlists import Playlists
from .root import Root
from .base import NAME, BUS_TYPE
from .compat import get_dbus_name
from .adapters import MprisAdapter
from .tracklist import TrackList


logger = logging.getLogger(__name__)


class Server:
  def __init__(self,
               name: str = NAME,
               adapter: MprisAdapter = None):
    self.name = name
    self.adapter = adapter
    self.dbus_name = get_dbus_name(self.name)
    self.root = Root(name, self.adapter)
    self.player = Player(name, self.adapter)
    self.playlists = Playlists(name, self.adapter)
    self.tracklist = TrackList(name, self.adapter)

    self._loop = None
    self._publication_token = None

  def __del__(self):
    self.unpublish()

    if self._loop:
      self._loop.quit()

  def publish(self):
    bus_type = BUS_TYPE
    logger.debug(f"Connecting to D-Bus {bus_type} bus...")

    if bus_type == "system":
      bus = pydbus.SystemBus()

    else:
      bus = pydbus.SessionBus()

    logger.info(f"MPRIS server connected to D-Bus {bus_type} bus")

    self._publication_token = bus.publish(
      f"org.mpris.MediaPlayer2.{self.dbus_name}",
      ("/org/mpris/MediaPlayer2", self.root),
      ("/org/mpris/MediaPlayer2", self.player),
      ("/org/mpris/MediaPlayer2", self.playlists),
      ("/org/mpris/MediaPlayer2", self.tracklist)
    )

  def unpublish(self):
    if self._publication_token:
      self._publication_token.unpublish()
      self._publication_token = None

  def loop(self):
    if not self._publication_token:
      self.publish()

    self._loop = GLib.MainLoop()

    try:
      self._loop.run()

    finally:
      self._loop.quit()
      self._loop = None
