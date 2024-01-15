#
# Copyright (c) 2021, 2022 Astroncia
# Copyright (c) 2023, 2024 Ame-chan-angel <amechanangel@proton.me>
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
import logging
import gettext
import gzip
import lzma
import datetime
import xml.etree.ElementTree as ET

_ = gettext.gettext
logger = logging.getLogger(__name__)


def parse_timestamp(ts_string, settings):
    # TODO: support string timezones like 'DST'

    # Assume UTC if no timezone specified
    if " " not in ts_string.strip():
        ts_string += " +0000"

    timestamp_formats = [
        "%Y%m%d%H%M%S %z",
        "%Y%m%d%H%M %z",
        "%Y%m%d%H %z",
        "%Y%m%d %z",
        "%Y%m %z",
        "%Y %z",
    ]

    ts = 0
    for timestamp_format in timestamp_formats:
        try:
            ts = datetime.datetime.strptime(ts_string, timestamp_format).timestamp() + (
                3600 * settings["epgoffset"]
            )
            break
        except Exception:
            pass
    return ts


def parse_as_xmltv(
    epg, settings, catchup_days1, progress_dict, epg_i, epg_settings_url
):
    """Load EPG file"""
    logger.info("Trying parsing as XMLTV...")
    logger.info(f"catchup-days = {catchup_days1}")
    try:
        tree = ET.ElementTree(ET.fromstring(epg))
    except ET.ParseError:
        progress_dict["epg_progress"] = _(
            "Updating TV guide... (unpacking {}/{})"
        ).format(epg_i, len(epg_settings_url))
        try:
            logger.info("Trying to unpack as gzip...")
            tree = ET.ElementTree(ET.fromstring(gzip.decompress(epg)))
        except Exception:
            logger.info("Trying to unpack as xz...")
            tree = ET.ElementTree(
                ET.fromstring(lzma.LZMADecompressor().decompress(epg))
            )
    progress_dict["epg_progress"] = _("Updating TV guide... (parsing {}/{})").format(
        epg_i, len(epg_settings_url)
    )
    ids = {}
    programmes_epg = {}
    icons = {}
    for channel_epg in tree.findall("./channel"):
        for display_name in channel_epg.findall("./display-name"):
            if display_name.text:
                if not channel_epg.attrib["id"].strip() in ids:
                    ids[channel_epg.attrib["id"].strip()] = []
                ids[channel_epg.attrib["id"].strip()].append(display_name.text.strip())
            try:
                all_icons = channel_epg.findall("./icon")
                if all_icons:
                    for icon in all_icons:
                        try:
                            if "src" in icon.attrib:
                                icons[display_name.text.strip().lower()] = icon.attrib[
                                    "src"
                                ].strip()
                        except Exception:
                            pass
            except Exception:
                pass
    for programme in tree.findall("./programme"):
        try:
            start = parse_timestamp(programme.attrib["start"], settings)
        except Exception:
            start = 0
        try:
            stop = parse_timestamp(programme.attrib["stop"], settings)
        except Exception:
            stop = 0
        try:
            chans = ids[programme.attrib["channel"].strip()]
            catchup_id = ""
            try:
                if "catchup-id" in programme.attrib:
                    catchup_id = programme.attrib["catchup-id"]
            except Exception:
                pass
            for channel_epg_1 in chans:
                if channel_epg_1 not in programmes_epg:
                    programmes_epg[channel_epg_1] = []
                try:
                    prog_title = programme.find("./title").text
                except Exception:
                    prog_title = ""
                try:
                    prog_desc = programme.find("./desc").text
                except Exception:
                    prog_desc = ""
                programmes_epg[channel_epg_1].append(
                    {
                        "start": start,
                        "stop": stop,
                        "title": prog_title,
                        "desc": prog_desc,
                        "catchup-id": catchup_id,
                    }
                )
        except Exception:
            pass
    return [programmes_epg, ids, icons]
