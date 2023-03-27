'''Import settings from Astroncia IPTV'''
# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=missing-function-docstring, bare-except
import os
import os.path
import json
import shutil
from pathlib import Path
from yuki_iptv.time import print_with_time

def ast_settings_import():
    if os.path.isfile(Path(os.environ['HOME'], '.config', 'astronciaiptv', 'settings.json')) \
    and not os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json')):
        print_with_time("Importing settings from Astroncia IPTV...")
        try:
            for file in Path(os.environ['HOME'], '.config', 'astronciaiptv').glob('*'):
                if os.path.isfile(file):
                    shutil.copyfile(
                        Path(os.environ['HOME'], '.config', 'astronciaiptv', file.name),
                        Path(os.environ['HOME'], '.config', 'yuki-iptv', file.name),
                    )

            # Settings patch
            with open(
                Path(os.environ['HOME'], '.config', 'astronciaiptv', 'settings.json'),
                'r', encoding="utf8"
            ) as old_settings_file:
                settings = json.loads(old_settings_file.read())
            # save_folder
            if '/.config/astronciaiptv/' in settings['save_folder']:
                settings['save_folder'] = settings['save_folder'].replace(
                    '/.config/astronciaiptv/',
                    '/.config/yuki-iptv/'
                )
            # disable autoreconnection
            settings['autoreconnection'] = False
            # save new settings
            with open(
                Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json'),
                'w', encoding="utf8"
            ) as new_settings_file:
                new_settings_file.write(json.dumps(settings))

            print_with_time("Importing settings from Astroncia IPTV - OK")
            print_with_time("")
        except:
            print_with_time("Importing settings from Astroncia IPTV - FAILED!")
            print_with_time("")
