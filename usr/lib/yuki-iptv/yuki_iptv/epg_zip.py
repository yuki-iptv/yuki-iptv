#
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
import zipfile
from yuki_iptv.epg_listtv import parse_txt
from yuki_iptv.epg_jtv import parse_epg_zip_jtv

logger = logging.getLogger(__name__)


def parse_epg_zip(zip_file):
    found = False
    with zipfile.ZipFile(zip_file) as myzip:
        namelist = myzip.namelist()
        for name in namelist:
            name = name.strip()
            if name.endswith(".txt"):
                logger.info("TXT format detected, trying to parse...")
                found = True
                with myzip.open(name) as myfile:
                    return parse_txt(myfile.read())
                break
            if name.endswith(".xml"):
                logger.info("XMLTV inside ZIP detected, trying to parse...")
                found = True
                with myzip.open(name) as myfile:
                    return ["xmltv", myfile.read()]
                break
            if name.endswith(".ndx"):
                logger.info("JTV format detected, trying to parse...")
                found = True
                return parse_epg_zip_jtv(myzip)
                break
    if not found:
        raise Exception("No known EPG formats found in ZIP file")
