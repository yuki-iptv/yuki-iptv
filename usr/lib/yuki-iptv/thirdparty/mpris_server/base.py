# https://github.com/alexdelorenzo/mpris_server/tree/f55313f3a0383de4606f7589a770430d90a11c7d
from typing import Iterable, Union, Dict, Tuple, Optional, NamedTuple, List
from enum import Enum, auto
from string import ascii_letters, digits

from gi.repository.GLib import Variant


INTERFACE = "org.mpris.MediaPlayer2"
NAME = "mprisServer"
MIME_TYPES = ["audio/mpeg", "application/ogg", "video/mpeg"]
BUS_TYPE = "session"
URI = ["file"]
DEFAULT_DESKTOP = ''

# typically, these are the props that dbus needs to be notified about
# upon specific state-change events.
ON_ENDED_PROPS = ['PlaybackStatus']
ON_VOLUME_PROPS = ['Volume', 'Metadata']
ON_PLAYBACK_PROPS = ['PlaybackStatus', 'Metadata']
ON_PLAYPAUSE_PROPS = ['PlaybackStatus']
ON_TITLE_PROPS = ['Metadata']
ON_OPTION_PROPS = ['LoopStatus', 'Shuffle', 'CanGoPrevious', 'CanGoNext']
ON_SEEK_PROPS = ['Position']

ON_TRACKS_PROPS = ['Tracks']
ON_PLAYLIST_PROPS = ['PlaylistCount', 'Orderings', 'ActivePlaylist']

DEFAULT_RATE = 1.0
PAUSE_RATE = 0
MIN_RATE = 1.0
MAX_RATE = 1.0

MUTE_VOL = 0
MAX_VOL = 1
BEGINNING = 0

DEFAULT_TRACK_ID = '/default/1'
DEFAULT_PLAYLIST_COUNT = 1
DEFAULT_ORDERINGS = ["Alphabetical", "User"]

# valid characters for a DBus name 
VALID_PUNC = '_'
VALID_CHARS = set(digits + ascii_letters + VALID_PUNC)
NAME_PREFIX = "Mpris_Server_"
RAND_CHARS = 5

DEFAULT_METADATA = {}

# type aliases
Microseconds = int
VolumeDecimal = float
RateDecimal = float
DbusTypes = Union[str, float, int, bool, list]
Metadata = Dict[str, DbusTypes]
DbusMetadata = Dict[str, Variant]
DbusObj = str
PlaylistEntry = Tuple[str, str, str]
PlaylistValidity = bool


# See https://docs.python.org/3/library/enum.html#using-automatic-values
class AutoName(Enum):
    def _generate_next_value_(name: str, *args, **kwargs) -> str:
        return name


class PlayState(AutoName):
    PLAYING = auto()
    PAUSED = auto()
    STOPPED = auto()


class Artist(NamedTuple):
    name: str = "Default Artist"


class Album(NamedTuple):
    name: str = "Default Album"
    artists: Tuple[Artist] = tuple()
    art_url: Optional[str] = None


class Track(NamedTuple):
    track_id: DbusObj = DEFAULT_TRACK_ID
    name: str = "Default Track"
    track_no: Optional[int] = None
    length: Microseconds = 0
    uri: Optional[str] = None
    artists: Tuple[Artist] = tuple()
    album: Optional[Album] = None
    art_url: Optional[str] = None
    disc_no: Optional[int] = None
    type: Optional[Enum] = None


def dbus_emit_changes(interface: 'MprisInterface',
                      changes: Iterable[str]):
    attr_vals = {attr: getattr(interface, attr)
                 for attr in changes}

    interface.PropertiesChanged(interface.INTERFACE, attr_vals, [])
