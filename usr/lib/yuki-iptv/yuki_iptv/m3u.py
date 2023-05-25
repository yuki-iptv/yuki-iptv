#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 Ame-chan-angel <amechanangel@proton.me>
#
# This file is part of yuki-iptv.
#
# yuki-iptv is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# yuki-iptv is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License.
# https://fontawesome.com/
# https://creativecommons.org/licenses/by/4.0/
#
import re
import logging

logger = logging.getLogger(__name__)


class M3UParser:
    """M3U parser"""

    def __init__(self, udp_proxy, _):
        self.udp_proxy = udp_proxy
        self.all_channels = _("All channels")
        self.epg_urls = []
        self.m3u_epg = ""
        self.epg_url_final = ""
        self.regexp_cache = {}

    def parse_regexp(self, name, line_info, default="", custom_regex=False):
        """Channel info regexp parser"""
        regexp = name
        if not custom_regex:
            regexp += '="(.*?)"'
        if regexp not in self.regexp_cache:
            self.regexp_cache[regexp] = re.compile(regexp)
        re_match = self.regexp_cache[regexp].search(line_info)
        try:
            res = re_match.group(1)
        except AttributeError:
            res = default
        # catchup-days check start
        if name == "catchup-days":
            try:
                res = str(int(res))
            except Exception:
                logger.warning(
                    f"M3U STANDARDS VIOLATION: catchup-days is not int (got '{res}')"
                )
                res = default
        # catchup-days check end
        res = res.strip()
        return res

    def parse_url_kodi_arguments(self, url):
        """Parse Kodi-style URL arguments"""
        useragent = ""
        referrer = ""
        if "|" in url:
            logger.debug("")
            logger.debug("Found Kodi-style arguments, parsing")
            split_kodi = url.split("|")[1]
            if "&" in split_kodi:
                logger.debug("Multiple")
                split_kodi = split_kodi.split("&")
            else:
                logger.debug("Single")
                split_kodi = [split_kodi]
            for kodi_str in split_kodi:
                if kodi_str.startswith("User-Agent="):
                    kodi_user_agent = kodi_str.replace("User-Agent=", "", 1)
                    logger.debug(f"Kodi-style User-Agent found: {kodi_user_agent}")
                    useragent = kodi_user_agent
                if kodi_str.startswith("user-agent="):
                    kodi_user_agent = kodi_str.replace("user-agent=", "", 1)
                    logger.debug(f"Kodi-style User-Agent found: {kodi_user_agent}")
                    useragent = kodi_user_agent
                if kodi_str.startswith("Referer="):
                    kodi_referer = kodi_str.replace("Referer=", "", 1)
                    logger.debug(f"Kodi-style Referer found: {kodi_referer}")
                    referrer = kodi_referer
                if kodi_str.startswith("referer="):
                    kodi_referer = kodi_str.replace("referer=", "", 1)
                    logger.debug(f"Kodi-style Referer found: {kodi_referer}")
                    referrer = kodi_referer
            url = url.split("|")[0]
            logger.debug("")
        return url, useragent, referrer

    def parse_channel(self, line_info, ch_url, overrides):
        """Parse EXTINF channel info"""
        if self.udp_proxy and (
            ch_url.startswith("udp://") or ch_url.startswith("rtp://")
        ):
            ch_url = (
                self.udp_proxy
                + "/"
                + ch_url.replace("udp://", "udp/").replace("rtp://", "rtp/")
            )
            ch_url = ch_url.replace("//udp/", "/udp/").replace("//rtp/", "/rtp/")
            ch_url = ch_url.replace("@", "")

        tvg_url = self.parse_regexp("tvg-url", line_info)
        url_tvg = self.parse_regexp("url-tvg", line_info)
        if not tvg_url and url_tvg:
            tvg_url = url_tvg

        group = self.parse_regexp("group-title", line_info, "")
        if not group:
            group = self.parse_regexp("tvg-group", line_info, self.all_channels)
            if not group:
                group = self.all_channels

        catchup_tag = self.parse_regexp("catchup", line_info, "")
        if not catchup_tag:
            catchup_tag = self.parse_regexp("catchup-type", line_info, "default")

        ch_array = {
            "title": self.parse_regexp("[,](?!.*[,])(.*?)$", line_info, "", True),
            "tvg-name": self.parse_regexp("tvg-name", line_info),
            "tvg-ID": self.parse_regexp("tvg-id", line_info),
            "tvg-logo": self.parse_regexp("tvg-logo", line_info),
            "tvg-group": group,
            "tvg-url": tvg_url,
            "catchup": catchup_tag,
            "catchup-source": self.parse_regexp("catchup-source", line_info),
            "catchup-days": self.parse_regexp("catchup-days", line_info, "1"),
            "useragent": self.parse_regexp("user-agent", line_info),
            "referer": "",
            "url": ch_url,
        }

        # search also for tvg-ID
        tvg_id_2 = self.parse_regexp("tvg-ID", line_info)
        if tvg_id_2 and not ch_array["tvg-ID"]:
            ch_array["tvg-ID"] = tvg_id_2

        # Parse Kodi-style URL arguments
        channel_url, kodi_useragent, kodi_referrer = self.parse_url_kodi_arguments(
            ch_array["url"]
        )
        if kodi_useragent:
            ch_array["useragent"] = kodi_useragent
        if kodi_referrer:
            ch_array["referer"] = kodi_referrer
        ch_array["url"] = channel_url

        # EXTGRP and EXTVLCOPT always have priority over EXTINF options
        for override in overrides:
            ch_array[override] = overrides[override]

        return ch_array

    def parse_m3u(self, m3u_str):
        """Parse m3u string"""
        self.epg_urls = []
        self.m3u_epg = ""
        self.epg_url_final = ""
        if not ("#EXTM3U" in m3u_str and "#EXTINF" in m3u_str):
            raise Exception("Malformed M3U")
        channels = []
        buffer = []
        for line in m3u_str.split("\n"):
            line = line.rstrip("\n").rstrip().strip()
            if line.startswith("#EXTM3U"):
                epg_m3u_url = ""
                if 'x-tvg-url="' in line:
                    try:
                        epg_m3u_url = re.findall('x-tvg-url="(.*?)"', line)[0]
                    except Exception:
                        pass
                else:
                    if 'tvg-url="' in line:
                        try:
                            epg_m3u_url = re.findall('tvg-url="(.*?)"', line)[0]
                        except Exception:
                            pass
                    else:
                        try:
                            epg_m3u_url = re.findall('url-tvg="(.*?)"', line)[0]
                        except Exception:
                            pass
                if epg_m3u_url:
                    self.m3u_epg = epg_m3u_url
            else:
                if line:
                    if line.startswith("#"):
                        buffer.append(line)
                    else:
                        chan = False
                        overrides = {}
                        for line1 in buffer:
                            if line1.startswith("#EXTINF:"):
                                chan = line1
                            if line1.startswith("#EXTGRP:"):
                                group1 = line1.replace("#EXTGRP:", "").strip()
                                if group1:
                                    overrides["tvg-group"] = group1
                            if line1.startswith("#EXTLOGO:"):
                                logo1 = line1.replace("#EXTLOGO:", "").strip()
                                if logo1:
                                    overrides["tvg-logo"] = logo1
                            if line1.startswith("#EXTVLCOPT:"):
                                extvlcopt = line1.replace("#EXTVLCOPT:", "").strip()
                                if extvlcopt.startswith("http-user-agent="):
                                    http_user_agent = extvlcopt.replace(
                                        "http-user-agent=", ""
                                    ).strip()
                                    if http_user_agent:
                                        overrides["useragent"] = http_user_agent
                                if extvlcopt.startswith("http-referrer="):
                                    http_referer = extvlcopt.replace(
                                        "http-referrer=", ""
                                    ).strip()
                                    if http_referer:
                                        overrides["referer"] = http_referer
                        if chan:
                            parsed_chan = self.parse_channel(chan, line, overrides)
                            if parsed_chan["tvg-url"]:
                                if parsed_chan["tvg-url"] not in self.epg_urls:
                                    self.epg_urls.append(parsed_chan["tvg-url"])
                            channels.append(parsed_chan)
                        buffer.clear()
        buffer.clear()
        self.epg_url_final = self.m3u_epg
        if self.epg_urls and not self.m3u_epg:
            self.epg_url_final = "^^::MULTIPLE::^^" + ":::^^^:::".join(self.epg_urls)
        if not channels:
            raise Exception("No channels found")
        return [channels, self.epg_url_final]
