'''xspf compatibility'''
import re
import xml.etree.ElementTree as ET
from astroncia.lang import _
from astroncia.time import print_with_time
# SPDX-License-Identifier: GPL-3.0-only
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
            'tvg-group': _('allchannels'),
            'tvg-url': '',
            'catchup': 'default',
            'catchup-source': '',
            'catchup-days': '1',
            'useragent': '',
            'referer': '',
            'url': location
        })
    return [array, []]
