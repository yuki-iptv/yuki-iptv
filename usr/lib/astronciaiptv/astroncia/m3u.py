'''M3U parser'''
#
# Copyright (c) 2021-2022 Astroncia
#
#    This file is part of Astroncia IPTV.
#
#    Astroncia IPTV is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Astroncia IPTV is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
#
import re

class M3UParser:
    '''M3U parser'''
    def __init__(self, udp_proxy, _):
        self.udp_proxy = udp_proxy
        self._ = _
        self.epg_urls = []
        self.m3u_epg = ""
        self.epg_url_final = ""

    def parse_regexp(self, name, line_info, default="", custom_regex=False): # pylint: disable=no-self-use
        '''Channel info regexp parser'''
        regexp = name
        if not custom_regex:
            regexp += "=\"(.*?)\""
        re_match = re.search(regexp, line_info)
        try:
            res = re_match.group(1)
        except AttributeError:
            res = default
        res = res.strip()
        return res

    def parse_channel(self, line_info, ch_url, overrides):
        '''Parse EXTINF channel info'''
        if self.udp_proxy and (ch_url.startswith('udp://') or ch_url.startswith('rtp://')):
            ch_url = self.udp_proxy + \
            "/" + ch_url.replace("udp://", "udp/").replace("rtp://", "rtp/")
            ch_url = ch_url.replace('//udp/', '/udp/').replace('//rtp/', '/rtp/')

        tvg_url = self.parse_regexp("tvg-url", line_info)
        url_tvg = self.parse_regexp("url-tvg", line_info)
        if not tvg_url and url_tvg:
            tvg_url = url_tvg

        group = self.parse_regexp("group-title", line_info, self._('allchannels'))
        if not group:
            group = self._('allchannels')

        ch_array = {
            "title": self.parse_regexp("[,](?!.*[,])(.*?)$", line_info, "", True),
            "tvg-name": self.parse_regexp("tvg-name", line_info),
            "tvg-ID": self.parse_regexp("tvg-id", line_info),
            "tvg-logo": self.parse_regexp("tvg-logo", line_info),
            "tvg-group": group,
            "tvg-url": tvg_url,
            "catchup": self.parse_regexp("catchup", line_info, "default"),
            "catchup-source": self.parse_regexp("catchup-source", line_info),
            "catchup-days": self.parse_regexp("catchup-days", line_info, "1"),
            "useragent": "",
            "referer": "",
            "url": ch_url
        }
        for override in overrides:
            ch_array[override] = overrides[override]

        if ch_array['tvg-group'].lower() == 'vod':
            ch_array['tvg-group'] = '> ' + self._('movies')

        if ch_array['tvg-group'].lower().startswith('vod '):
            ch_array['tvg-group'] = re.sub(
                "^vod ", '> ' + self._('movies') + ' > ', ch_array['tvg-group'], flags=re.I
            )

        if ch_array['useragent']:
            ch_array['url'] += '^^^^^^^^^^useragent=' + ch_array['useragent'] + '@#@'
        if ch_array['referer']:
            ch_array['url'] += '^^^^^^^^^^referer=' + ch_array['referer'] + '@#@'

        return ch_array

    def parse_m3u(self, m3u_str): # pylint: disable=too-many-branches, too-many-statements
        '''Parse m3u string'''
        self.epg_urls = []
        self.m3u_epg = ""
        self.epg_url_final = ""
        if not ("#EXTM3U" in m3u_str and "#EXTINF" in m3u_str):
            raise Exception("Malformed M3U")
        channels = []
        buffer = []
        for line in m3u_str.split('\n'): # pylint: disable=too-many-nested-blocks
            line = line.rstrip('\n').rstrip().strip()
            if line.startswith('#EXTM3U'):
                epg_m3u_url = ""
                if 'x-tvg-url="' in line:
                    try:
                        epg_m3u_url = re.findall('x-tvg-url="(.*?)"', line)[0]
                    except: # pylint: disable=bare-except
                        pass
                else:
                    if 'tvg-url="' in line:
                        try:
                            epg_m3u_url = re.findall('tvg-url="(.*?)"', line)[0]
                        except: # pylint: disable=bare-except
                            pass
                    else:
                        try:
                            epg_m3u_url = re.findall('url-tvg="(.*?)"', line)[0]
                        except: # pylint: disable=bare-except
                            pass
                if epg_m3u_url:
                    self.m3u_epg = epg_m3u_url if epg_m3u_url != 'http://server/jtv.zip' else ''
            else:
                if line:
                    if line.startswith('#'):
                        buffer.append(line)
                    else:
                        chan = False
                        overrides = {}
                        for line1 in buffer:
                            if line1.startswith('#EXTINF:'):
                                chan = line1
                            if line1.startswith('#EXTGRP:'):
                                group1 = line1.replace('#EXTGRP:', '').strip()
                                if group1:
                                    overrides['tvg-group'] = group1
                            if line1.startswith('#EXTLOGO:'):
                                logo1 = line1.replace('#EXTLOGO:', '').strip()
                                if logo1:
                                    overrides['tvg-logo'] = logo1
                            if line1.startswith('#EXTVLCOPT:'):
                                extvlcopt = line1.replace('#EXTVLCOPT:', '').strip()
                                if extvlcopt.startswith('http-user-agent='):
                                    http_user_agent = extvlcopt.replace(
                                        'http-user-agent=', ''
                                    ).strip()
                                    overrides['useragent'] = http_user_agent
                                if extvlcopt.startswith('http-referrer='):
                                    http_referer = extvlcopt.replace(
                                        'http-referrer=', ''
                                    ).strip()
                                    overrides['referer'] = http_referer
                        if chan:
                            parsed_chan = self.parse_channel(chan, line, overrides)
                            if parsed_chan['tvg-url']:
                                if parsed_chan['tvg-url'] not in self.epg_urls:
                                    self.epg_urls.append(parsed_chan['tvg-url'])
                            channels.append(parsed_chan)
                        buffer.clear()
        buffer.clear()
        self.epg_url_final = self.m3u_epg
        if self.epg_urls and not self.m3u_epg:
            self.epg_url_final = '^^::MULTIPLE::^^' + ':::^^^:::'.join(self.epg_urls)
        if not channels:
            raise Exception("No channels found")
        return [channels, self.epg_url_final]
