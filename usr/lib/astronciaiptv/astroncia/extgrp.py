'''
Copyright (c) 2021-2022 Astroncia

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
from astroncia.time import print_with_time

def parse_extgrp(m3u_string): # pylint: disable=too-many-branches
    '''Parse EXTGRP M3U'''
    print_with_time("EXTGRP parsing...")
    name = '""'
    group = ""
    url = '""'
    logo = '""'
    result = ["#EXTM3U"]

    for x in range(1, len(m3u_string)-1):
        line = m3u_string[x]
        nextline = m3u_string[x+1]
        if "#EXTINF" in line and not "tvg-name-astroncia-iptv" in line:
            name = line.rpartition(",")[2]
            if 'group-title=' in line:
                group = line.rpartition('group-title="')[2].partition('"')[0]
            else:
                group = ""
            if 'tvg-logo=' in line:
                logo = line.rpartition('tvg-logo="')[2].partition('"')[0]
            else:
                logo = ""
            if 'tvg-name=' in line:
                tvgname = line.rpartition('tvg-name="')[2].partition('"')[0]
            else:
                tvgname = ""
            if 'tvg-url=' in line:
                tvgurl = line.rpartition('tvg-url="')[2].partition('"')[0]
            else:
                tvgurl = ""
            if 'tvg-id=' in line:
                tvgid = line.rpartition('tvg-id="')[2].partition('"')[0]
            else:
                tvgid = ""
            if 'url-tvg=' in line:
                urltvg = line.rpartition('url-tvg="')[2].partition('"')[0]
            else:
                urltvg = ""
            if not tvgurl and urltvg:
                tvgurl = urltvg
            if not "EXTGRP" in nextline:
                url = nextline
            else:
                group = nextline.partition('#EXTGRP:')[2]
                url = m3u_string[x+2]
            result.append(f"#EXTINF:-1 tvg-id=\"{tvgid}\" tvg-name=\"{tvgname}\" tvg-name-astroncia-iptv=\"{name}\" group-title=\"{group}\" tvg-logo=\"{logo}\" tvg-url=\"{tvgurl}\",{name}\n{url}")

    return '\n'.join(result).split('\n')
