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
def convert_xtream_to_m3u(_, data, skip_init=False, append_group=""):
    output = '#EXTM3U\n' if not skip_init else ''
    for channel in data:
        name = channel.name
        try:
            group = channel.group_title if channel.group_title else ''
        except: # pylint: disable=bare-except
            group = _('allchannels')
        if append_group:
            group = append_group + " " + group
        logo = channel.logo if channel.logo else ''
        url = channel.url
        line = '#EXTINF:0'
        if logo:
            line += " tvg-logo=\"{}\"".format(logo)
        if group:
            line += " group-title=\"{}\"".format(group)
        line += ",{}".format(name)
        output += line + '\n' + url + '\n'
    return output
