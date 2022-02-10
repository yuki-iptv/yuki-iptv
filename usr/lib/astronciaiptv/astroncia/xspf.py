'''xspf compatibility'''
import re
import xml.etree.ElementTree as ET
from astroncia.lang import _
from astroncia.time import print_with_time
#
# Copyright (c) 2021-2022 Astroncia
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
def parse_xspf(xspf): # pylint: disable=missing-function-docstring
    print_with_time("Trying parsing as XSPF...")
    array = []
    tree = ET.ElementTree(ET.fromstring(xspf)).getroot()
    for track in tree.findall("{*}trackList/{*}track"):
        title = track.find('{*}title').text.strip()
        location = track.find('{*}location').text.strip()
        if location.startswith('file:///'):
            # Windows
            if re.match(r'file:///.:/', location):
                location = location.replace('file:///', '').replace('/', '\\')
            else:
                # Linux
                location = location.replace('file://', '')
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
