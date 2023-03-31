'''Import settings from Astroncia IPTV'''
# SPDX-License-Identifier: GPL-3.0-only
# pylint: disable=missing-function-docstring, bare-except
import os
import os.path
import logging
import json
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

def ast_settings_import():
    if os.path.isfile(Path(os.environ['HOME'], '.config', 'astronciaiptv', 'settings.json')) \
    and not os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json')):
        logger.info("Importing settings from Astroncia IPTV...")
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

            logger.info("Importing settings from Astroncia IPTV - OK")
            logger.info("")
        except:
            logger.warning("Importing settings from Astroncia IPTV - FAILED!")
            logger.warning("")

def convert_old_filenames():
    if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'playlist_separate.m3u')) \
    and not os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favplaylist.m3u')):
        os.rename(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'playlist_separate.m3u'),
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favplaylist.m3u')
        )

    if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'channels.json')) \
    and not os.path.isfile(
        Path(os.environ['HOME'], '.config', 'yuki-iptv', 'channelsettings.json')
    ):
        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'channels.json'),
            'r', encoding="utf8"
        ) as old_channels_file:
            old_channels = json.loads(old_channels_file.read())

        # settings start
        settings = {'m3u': ''}
        if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json')):
            with open(
                Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json'),
                'r', encoding="utf8"
            ) as old_settings_file:
                settings = json.loads(old_settings_file.read())
        # settings end

        new_channels = {}
        if settings['m3u']:
            new_channels[settings['m3u']] = old_channels

        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'channelsettings.json'),
            'w', encoding="utf8"
        ) as new_channels_file:
            new_channels_file.write(json.dumps(new_channels))
        os.remove(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'channels.json'))

    if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favourites.json')) \
    and not os.path.isfile(
        Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favouritechannels.json')
    ):
        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favourites.json'),
            'r', encoding="utf8"
        ) as old_favourites_file:
            old_favourites = json.loads(old_favourites_file.read())

        # settings start
        settings = {'m3u': ''}
        if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json')):
            with open(
                Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json'),
                'r', encoding="utf8"
            ) as old_settings_file:
                settings = json.loads(old_settings_file.read())
        # settings end

        new_favourites = {}
        if settings['m3u']:
            new_favourites[settings['m3u']] = old_favourites

        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favouritechannels.json'),
            'w', encoding="utf8"
        ) as new_favourites_file:
            new_favourites_file.write(json.dumps(new_favourites))
        os.remove(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'favourites.json'))

    if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'sort.json')) \
    and not os.path.isfile(
        Path(os.environ['HOME'], '.config', 'yuki-iptv', 'sortchannels.json')
    ):
        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'sort.json'),
            'r', encoding="utf8"
        ) as old_sort_file:
            old_sort = json.loads(old_sort_file.read())

        # settings start
        settings = {'m3u': ''}
        if os.path.isfile(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json')):
            with open(
                Path(os.environ['HOME'], '.config', 'yuki-iptv', 'settings.json'),
                'r', encoding="utf8"
            ) as old_settings_file:
                settings = json.loads(old_settings_file.read())
        # settings end

        new_sort = {}
        if settings['m3u']:
            new_sort[settings['m3u']] = old_sort

        with open(
            Path(os.environ['HOME'], '.config', 'yuki-iptv', 'sortchannels.json'),
            'w', encoding="utf8"
        ) as new_sort_file:
            new_sort_file.write(json.dumps(new_sort))
        os.remove(Path(os.environ['HOME'], '.config', 'yuki-iptv', 'sort.json'))
