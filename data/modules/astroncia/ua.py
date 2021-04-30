'''
Copyright (C) 2021 Astroncia

    This file is part of Astroncia IPTV.

    Astroncia IPTV is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Astroncia IPTV is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
'''
import os
import json
from pathlib import Path
user_agent = ''
uas = [
    '',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36',
    'Dalvik/2.1.0 (Linux; U; Android 10; AGS3-L09 Build/HUAWEIAGS3-L09)',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'OnlineTvAppDroid',
    'smartlabs'
]
ua_names = [
    '',
    'Windows Browser',
    'Android',
    'iPhone',
    'Linux Browser',
    'OnlineTvAppDroid',
    'Smartlabs'
]

if 'HOME' in os.environ and os.path.isdir(os.environ['HOME']):
    LOCAL_DIR = str(Path(os.environ['HOME'], '.AstronciaIPTV'))
    SAVE_FOLDER_DEFAULT = str(Path(os.environ['HOME'], '.AstronciaIPTV', 'saves'))
    if not os.path.isdir(LOCAL_DIR):
        os.mkdir(LOCAL_DIR)
    if not os.path.isdir(SAVE_FOLDER_DEFAULT):
        os.mkdir(SAVE_FOLDER_DEFAULT)
else:
    LOCAL_DIR = 'local'
    SAVE_FOLDER_DEFAULT = str(Path(os.path.dirname(os.path.abspath(__file__)), 'AstronciaIPTV_saves'))

def get_default_user_agent():
    if os.path.isfile(str(Path(LOCAL_DIR, 'settings.json'))):
        settings_file1 = open(str(Path(LOCAL_DIR, 'settings.json')), 'r', encoding="utf8")
        settings1 = json.loads(settings_file1.read())
        settings_file1.close()
    else:
        settings1 = {
            "useragent": 2
        }
    if 'useragent' not in settings1:
        settings1['useragent'] = 2
    def_user_agent = uas[settings1['useragent']]
    return def_user_agent

def get_user_agent_for_channel(ch):
    ua1 = get_default_user_agent()
    channel_sets1 = {}
    if os.path.isfile(str(Path(LOCAL_DIR, 'channels.json'))):
        file2 = open(str(Path(LOCAL_DIR, 'channels.json')), 'r', encoding="utf8")
        channel_sets1 = json.loads(file2.read())
        file2.close()
    if ch in channel_sets1:
        ch_data = channel_sets1[ch]
        if 'useragent' in ch_data:
            try:
                ua1 = uas[ch_data['useragent']]
            except: # pylint: disable=bare-except
                ua1 = get_default_user_agent()
    return ua1
