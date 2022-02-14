'''settings.json parser'''
# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=missing-function-docstring, invalid-name
import os
import json
from pathlib import Path

def parse_settings( # pylint: disable=too-many-arguments
    LOCAL_DIR, DEF_DEINTERLACE, SAVE_FOLDER_DEFAULT, LANG_DEFAULT, DEF_TIMEZONE, DOCK_WIDGET_WIDTH
):
    settings_default = {
        "m3u": "",
        "epg": "",
        "deinterlace": DEF_DEINTERLACE,
        "udp_proxy": "",
        "save_folder": SAVE_FOLDER_DEFAULT,
        "provider": "",
        "nocache": True,
        "lang": LANG_DEFAULT,
        "epgoffset": DEF_TIMEZONE,
        "hwaccel": True,
        "sort": 0,
        "cache_secs": 0,
        "useragent": 2,
        "mpv_options": '',
        'donotupdateepg': False,
        'channelsonpage': 100,
        'openprevchan': False,
        'remembervol': True,
        'hidempv': False,
        'hideepgpercentage': False,
        'hidebitrateinfo': False,
        'movedragging': False,
        'styleredefoff': True,
        'volumechangestep': 1,
        'exp2': DOCK_WIDGET_WIDTH,
        'mouseswitchchannels': False,
        'autoreconnection': True,
        'showplaylistmouse': True,
        'hideplaylistleftclk': False,
        'channellogos': 0,
        'nocacheepg': False,
        'scrrecnosubfolders': False,
        'hidetvprogram': False,
        'showcontrolsmouse': True,
        'catchupenable': False,
        'flpopacity': 0.7,
        'panelposition': 0,
        'playlistsep': False,
        'screenshot': 0,
        'videoaspect': 0,
        'zoom': 0,
        'panscan': 0.0,
        'referer': '',
        'gui': 0
    }

    settings = settings_default
    settings_loaded = False

    if os.path.isfile(str(Path(LOCAL_DIR, 'settings.json'))):
        settings_file = open(str(Path(LOCAL_DIR, 'settings.json')), 'r', encoding="utf8")
        settings = json.loads(settings_file.read())
        settings_file.close()

        for option in settings_default:
            if option not in settings:
                settings[option] = settings_default[option]

        settings_loaded = True

    return settings, settings_loaded
