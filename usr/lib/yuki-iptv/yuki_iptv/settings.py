'''settings.json parser'''
# SPDX-License-Identifier: GPL-3.0-or-later
# pylint: disable=missing-function-docstring
import os
import json
from pathlib import Path

def parse_settings( # pylint: disable=too-many-arguments
    local_dir, def_deinterlace, save_folder_default,
    def_timezone, dock_widget_width
):
    settings_default = {
        "m3u": "",
        "epg": "",
        "deinterlace": def_deinterlace,
        "udp_proxy": "",
        "save_folder": save_folder_default,
        "provider": "",
        "nocache": True,
        "epgoffset": def_timezone,
        "hwaccel": True,
        "sort": 0,
        "cache_secs": 0,
        "ua": "Mozilla/5.0",
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
        'exp2': dock_widget_width,
        'mouseswitchchannels': False,
        'autoreconnection': False,
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
        'videoaspect': 0,
        'zoom': 0,
        'panscan': 0.0,
        'referer': '',
        'gui': 0
    }

    settings = settings_default
    settings_loaded = False

    if os.path.isfile(str(Path(local_dir, 'settings.json'))):
        settings_file = open(str(Path(local_dir, 'settings.json')), 'r', encoding="utf8")
        settings = json.loads(settings_file.read())
        settings_file.close()

        for option in settings_default:
            if option not in settings:
                settings[option] = settings_default[option]

        settings_loaded = True

    return settings, settings_loaded
