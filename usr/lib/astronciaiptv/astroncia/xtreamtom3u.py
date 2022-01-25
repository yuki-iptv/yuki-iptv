'''Convert XTream to M3U playlist'''
# pylint: disable=missing-class-docstring, missing-function-docstring
#
# Copyright (c) 2021-2022 Astroncia
#
#     This file is part of Astroncia IPTV.
#
#     Astroncia IPTV is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Astroncia IPTV is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
#
class AstronciaData: # pylint: disable=too-few-public-methods
    pass

AstronciaData.m3u = '#EXTM3U\n'

def convert_xtream_to_m3u(data):
    for channel in data:
        name = channel.name
        group = channel.group_title if channel.group_title else ''
        logo = channel.logo if channel.logo else ''
        url = channel.url
        output = '#EXTINF:0'
        if logo:
            output += " tvg-logo=\"{}\"".format(logo)
        if group:
            output += " group-title=\"{}\"".format(group)
        output += ",{}".format(name)
        AstronciaData.m3u += output + '\n' + url + '\n'
    return AstronciaData.m3u
