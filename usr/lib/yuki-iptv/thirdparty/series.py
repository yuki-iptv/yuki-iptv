# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring
import re
from yuki_iptv.time import print_with_time

SERIES = re.compile(
    r"(?P<series>.*?) S(?P<season>.\d{1,2}).*E(?P<episode>.\d{1,2}.*)$",
    re.IGNORECASE
)

class SerieM3U(): # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name
        self.logo = None
        self.logo_path = None
        self.seasons = {}
        self.episodes = []

class SeasonM3U(): # pylint: disable=too-few-public-methods
    def __init__(self, name):
        self.name = name
        self.episodes = {}

class ChannelM3U(): # pylint: disable=too-few-public-methods, too-many-instance-attributes
    def __init__(self):
        self.info = None
        self.id = None # pylint: disable=invalid-name
        self.name = None
        self.logo = None
        self.logo_path = None
        self.group_title = None
        self.title = None
        self.url = None

def get_series_name(obj):
    chan_name_1 = obj['tvg-name']
    if not chan_name_1:
        chan_name_1 = obj['title']
    return chan_name_1

def parse_series(obj1, series):
    is_matched = False
    chan_name_1 = get_series_name(obj1)
    series_match = SERIES.fullmatch(chan_name_1)
    if series_match is not None:
        try:
            res1 = series_match.groupdict()
            series_name = res1['series']
            if series_name in series:
                serie1 = series[series_name]
            else:
                serie1 = SerieM3U(series_name)
                serie1.logo = obj1['tvg-logo']
                series[series_name] = serie1
            season_name1 = res1['season']
            if season_name1 in serie1.seasons.keys():
                season1 = serie1.seasons[season_name1]
            else:
                season1 = SeasonM3U(season_name1)
                serie1.seasons[season_name1] = season1

            episode_name1 = res1['episode']
            ep_channel = ChannelM3U()
            ep_channel.name = chan_name_1
            ep_channel.title = chan_name_1
            ep_channel.logo = obj1['tvg-logo']
            ep_channel.url = obj1['url']
            season1.episodes[episode_name1] = ep_channel
            serie1.episodes.append(ep_channel)
            is_matched = True
        except: # pylint: disable=bare-except
            print_with_time("M3U Series parse FAILED")
    return series, is_matched
