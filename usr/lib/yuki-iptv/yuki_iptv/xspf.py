# SPDX-License-Identifier: GPL-3.0-or-later
'''xspf compatibility'''
import logging
import gettext
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)
_ = gettext.gettext

def parse_xspf(xspf): # pylint: disable=missing-function-docstring
    logger.info("Trying parsing as XSPF...")
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
