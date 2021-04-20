from typing import Optional
import logging

from gi.repository.GLib import Variant
from pydbus.generic import signal

from .base import PlayState, MUTE_VOL, MAX_VOL, PAUSE_RATE, BEGINNING, \
    Microseconds, RateDecimal, VolumeDecimal, MAX_RATE, MIN_RATE, \
    Track, DbusMetadata, DEFAULT_METADATA
from .compat import get_dbus_metadata
from .interface import MprisInterface

logger = logging.getLogger(__name__)


class Player(MprisInterface):
    """
    <node>
      <interface name="org.mpris.MediaPlayer2.Player">
        <method name="Next"/>
        <method name="Previous"/>
        <method name="Pause"/>
        <method name="PlayPause"/>
        <method name="Stop"/>
        <method name="Play"/>
        <method name="Seek">
          <arg name="Offset" type="x" direction="in"/>
        </method>
        <method name="SetPosition">
          <arg name="TrackId" type="o" direction="in"/>
          <arg name="Position" type="x" direction="in"/>
        </method>
        <method name="OpenUri">
          <arg name="Uri" type="s" direction="in"/>
        </method>
        <signal name="Seeked">
          <arg name="Position" type="x"/>
        </signal>
        <property name="PlaybackStatus" type="s" access="read"/>
        <property name="LoopStatus" type="s" access="readwrite"/>
        <property name="Rate" type="d" access="readwrite"/>
        <property name="Shuffle" type="b" access="readwrite"/>
        <property name="Metadata" type="a{sv}" access="read"/>
        <property name="Volume" type="d" access="readwrite"/>
        <property name="Position" type="x" access="read"/>
        <property name="MinimumRate" type="d" access="read"/>
        <property name="MaximumRate" type="d" access="read"/>
        <property name="CanGoNext" type="b" access="read"/>
        <property name="CanGoPrevious" type="b" access="read"/>
        <property name="CanPlay" type="b" access="read"/>
        <property name="CanPause" type="b" access="read"/>
        <property name="CanSeek" type="b" access="read"/>
        <property name="CanControl" type="b" access="read"/>
      </interface>
    </node>
    """

    INTERFACE = "org.mpris.MediaPlayer2.Player"

    Seeked = signal()
    MinimumRate = MIN_RATE
    MaximumRate = MAX_RATE

    def _dbus_metadata(self) -> Optional[DbusMetadata]:
        metadata = self.adapter.metadata()
        
        if metadata:
            return get_dbus_metadata(metadata)

    def Next(self):
        logger.debug("%s.Next called", self.INTERFACE)
        if not self.CanGoNext:
            logger.debug("%s.Next not allowed", self.INTERFACE)
            return

        self.adapter.next()

    def Previous(self):
        logger.debug("%s.Previous called", self.INTERFACE)
        if not self.CanGoPrevious:
            logger.debug("%s.Previous not allowed", self.INTERFACE)
            return

        self.adapter.previous()

    def Pause(self):
        logger.debug("%s.Pause called", self.INTERFACE)
        if not self.CanPause:
            logger.debug("%s.Pause not allowed", self.INTERFACE)
            return

        self.adapter.pause()

    def PlayPause(self):
        logger.debug("%s.PlayPause called", self.INTERFACE)
        if not self.CanPause:
            logger.debug("%s.PlayPause not allowed", self.INTERFACE)
            return

        state = self.adapter.get_playstate()

        if state == PlayState.PLAYING:
            self.adapter.pause()
        elif state == PlayState.PAUSED:
            self.adapter.resume()
        elif state == PlayState.STOPPED:
            self.adapter.play()

    def Stop(self):
        logger.debug("%s.Stop called", self.INTERFACE)

        if not self.CanControl:
            logger.debug("%s.Stop not allowed", self.INTERFACE)
            return

        self.adapter.stop()

    def Play(self):
        logger.debug("%s.Play called", self.INTERFACE)

        if not self.CanPlay:
            logger.debug("%s.Play not allowed", self.INTERFACE)
            return

        state = self.adapter.get_playstate()

        if state == PlayState.PAUSED:
            self.adapter.resume()
        else:
            self.adapter.play()

    def Seek(self, offset: Microseconds):
        logger.debug("%s.Seek called", self.INTERFACE)

        if not self.CanSeek:
            logger.debug("%s.Seek not allowed", self.INTERFACE)
            return

        current_position = self.adapter.get_current_position()
        new_position = current_position + offset

        if new_position < BEGINNING:
            new_position = BEGINNING

        self.adapter.seek(new_position)

    def SetPosition(self, track_id: str, position: Microseconds):
        logger.debug("%s.SetPosition called", self.INTERFACE)

        if not self.CanSeek:
            logger.debug("%s.SetPosition not allowed", self.INTERFACE)
            return

        metadata = self.adapter.metadata()

        # use metadata from adapter if available
        if metadata and \
          'mpris:trackid' in metadata and \
          'mpris:length' in metadata:
            current_track = Track(
                track_id=metadata['mpris:trackid'],
                length=metadata['mpris:length']
            )

        # if no metadata, build metadata from Track interface
        else:
            current_track = self.adapter.get_current_track()

        if current_track is None:
            return

        if track_id != current_track.track_id:
            return

        if position < BEGINNING:
            return

        if current_track.length < position:
            return

        self.adapter.seek(position)

    def OpenUri(self, uri: str):
        logger.debug("%s.OpenUri called", self.INTERFACE)
        if not self.CanControl:
            logger.debug("%s.OpenUri not allowed", self.INTERFACE)
            return
        # NOTE Check if URI has MIME type known to the backend, if MIME support
        # is added to the backend.
        self.adapter.open_uri(uri)

    @property
    def PlaybackStatus(self):
        self.log_trace("Getting %s.PlaybackStatus", self.INTERFACE)
        state = self.adapter.get_playstate()
        return state.value.title()

    @property
    def LoopStatus(self):
        self.log_trace("Getting %s.LoopStatus", self.INTERFACE)
        if not self.adapter.is_repeating():
            return "None"

        else:
            if not self.adapter.is_playlist():
                return "Track"

            else:
                return "Playlist"

    @LoopStatus.setter
    def LoopStatus(self, value: str):
        if not self.CanControl:
            logger.debug("Setting %s.LoopStatus not allowed", self.INTERFACE)
            return
        logger.debug("Settideng %s.LoopStatus to %s", self.INTERFACE, value)

        self.adapter.set_loop_status(value)
        # if value == "None":
        # self.core.tracklist.set_repeat(False)
        # self.core.tracklist.set_single(False)
        # elif value == "Track":
        # self.core.tracklist.set_repeat(True)
        # self.core.tracklist.set_single(True)
        # elif value == "Playlist":
        # self.core.tracklist.set_repeat(True)
        # self.core.tracklist.set_single(False)

    @property
    def Rate(self):
        self.log_trace("Getting %s.Rate", self.INTERFACE)
        return self.adapter.get_rate()

    @Rate.setter
    def Rate(self, value: RateDecimal):
        if not self.CanControl:
            logger.debug("Setting %s.Rate not allowed", self.INTERFACE)
            return

        logger.debug("Setting %s.Rate to %s", self.INTERFACE, value)
        self.adapter.set_rate(value)

        if value == PAUSE_RATE:
            self.Pause()

    @property
    def Shuffle(self):
        self.log_trace("Getting %s.Shuffle", self.INTERFACE)
        return self.adapter.get_shuffle()

    @Shuffle.setter
    def Shuffle(self, value: bool):
        if not self.CanControl:
            logger.debug("Setting %s.Shuffle not allowed", self.INTERFACE)
            return

        logger.debug("Setting %s.Shuffle to %s", self.INTERFACE, value)
        self.adapter.set_shuffle(value)

    @property
    def Metadata(self):
        # prefer adapter's metadata to building our own
        metadata: DbusMetadata = self._dbus_metadata()

        if metadata:
            return metadata

        # build metadata if no metadata supplied by adapter
        self.log_trace("Building %s.Metadata", self.INTERFACE)
        track = self.adapter.get_current_track()
        stream_title = self.adapter.get_stream_title()

        if track is None:
            return DEFAULT_METADATA

        track_id = track.track_id
        res = {"mpris:trackid": Variant("o", track_id)}

        if track.length:
            res["mpris:length"] = Variant("x", track.length)

        if track.uri:
            res["xesam:url"] = Variant("s", track.uri)

        if stream_title or track.name:
            res["xesam:title"] = Variant("s", stream_title or track.name)

        if track.artists:
            artists = list(track.artists)
            artists.sort(key=lambda a: a.name or "")
            res["xesam:artist"] = Variant("as", [a.name for a in artists if a.name])

        if track.album and track.album.name:
            res["xesam:album"] = Variant("s", track.album.name)

        if track.album and track.album.artists:
            artists = list(track.album.artists)
            artists.sort(key=lambda a: a.name or "")
            res["xesam:albumArtist"] = Variant(
                "as", [a.name for a in artists if a.name]
            )

        art_url = self._get_art_url(track)
        if art_url:
            res["mpris:artUrl"] = Variant("s", art_url)
        if track.disc_no:
            res["xesam:discNumber"] = Variant("i", track.disc_no)
        if track.track_no:
            res["xesam:trackNumber"] = Variant("i", track.track_no)

        return res

    def _get_art_url(self, track: 'Track'):
        return self.adapter.get_art_url(track)

    @property
    def Volume(self):
        self.log_trace("Getting %s.Volume", self.INTERFACE)
        mute = self.adapter.is_mute()
        volume = self.adapter.get_volume()

        if volume is None or mute is True:
            return MUTE_VOL

        return volume

    @Volume.setter
    def Volume(self, value: VolumeDecimal):
        if not self.CanControl:
            logger.debug("Setting %s.Volume not allowed", self.INTERFACE)
            return
        logger.debug("Setting %s.Volume to %s", self.INTERFACE, value)

        if value is None:
            return

        if value < MUTE_VOL:
            value = MUTE_VOL
        elif value > MAX_VOL:
            value = MAX_VOL

        self.adapter.set_volume(value)

        if value > MUTE_VOL:
            self.adapter.set_mute(False)

    @property
    def Position(self):
        self.log_trace("Getting %s.Position", self.INTERFACE)
        return self.adapter.get_current_position()

    @property
    def CanGoNext(self):
        self.log_trace("Getting %s.CanGoNext", self.INTERFACE)
        if not self.CanControl:
            return False

        return self.adapter.can_go_next()

    @property
    def CanGoPrevious(self):
        self.log_trace("Getting %s.CanGoPrevious", self.INTERFACE)
        if not self.CanControl:
            return False

        return self.adapter.can_go_previous()

    @property
    def CanPlay(self):
        self.log_trace("Getting %s.CanPlay", self.INTERFACE)
        if not self.CanControl:
            return False

        return self.adapter.can_play()

    @property
    def CanPause(self):
        self.log_trace("Getting %s.CanPause", self.INTERFACE)
        if not self.CanControl:
            return False

        return True

    @property
    def CanSeek(self):
        self.log_trace("Getting %s.CanSeek", self.INTERFACE)
        if not self.CanControl:
            return False

        return True

    @property
    def CanControl(self):
        return self.adapter.can_control()
