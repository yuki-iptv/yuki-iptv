# SPDX-License-Identifier: GPL-3.0-only
'''xspf compatibility'''
import gettext
import xml.etree.ElementTree as ET
from yuki_iptv.time import print_with_time

_ = gettext.gettext

def parse_xspf(xspf): # pylint: disable=missing-function-docstring
    print_with_time("Trying parsing as XSPF...")
    array = []
    tree = ET.ElementTree(ET.fromstring(xspf)).getroot()
    for track in tree.findall("{*}trackList/{*}track"):
        title = track.find('{*}title').text.strip()
        location = track.find('{*}location').text.strip()
        array.append({
            'title': title,
            'tvg-name': '',
            'tvg-ID': '',
            'tvg-logo': '',
            'tvg-group': _('All channels'),
            'tvg-url': '',
            'catchup': 'default',
            'catchup-source': '',
            'catchup-days': '1',
            'useragent': '',
            'referer': '',
            'url': location
        })
    return [array, []]
