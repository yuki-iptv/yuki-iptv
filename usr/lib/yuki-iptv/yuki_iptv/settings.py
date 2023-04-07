#
# Copyright (c) 2021-2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 yuki-chan-nya <yukichandev@proton.me>
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
# along with yuki-iptv  If not, see <http://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License
# https://creativecommons.org/licenses/by/4.0/
#
import os
import json
from pathlib import Path


def parse_settings(
    local_dir, save_folder_default,
    def_timezone
):
    settings_default = {
        "m3u": "",
        "epg": "",
        "deinterlace": False,
        "udp_proxy": "",
        "save_folder": save_folder_default,
        "nocache": True,
        "epgoffset": def_timezone,
        "hwaccel": False,
        "sort": 0,
        "cache_secs": 0,
        "epgdays": 1,
        "ua": "Mozilla/5.0",
        "mpv_options": '',
        'donotupdateepg': False,
        'openprevchan': False,
        'hidempv': False,
        'hideepgpercentage': False,
        'hidebitrateinfo': False,
        'styleredefoff': True,
        'volumechangestep': 1,
        'mouseswitchchannels': False,
        'autoreconnection': False,
        'showplaylistmouse': True,
        'channellogos': 0,
        'nocacheepg': False,
        'scrrecnosubfolders': False,
        'hidetvprogram': False,
        'showcontrolsmouse': True,
        'catchupenable': False,
        'flpopacity': 0.7,
        'panelposition': 0,
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
