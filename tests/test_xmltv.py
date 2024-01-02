#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
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
import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), "usr", "lib", "yuki-iptv")))

from yuki_iptv.epg_xmltv import parse_as_xmltv  # noqa: E402


def test_xmltv():
    with open(Path("tests", "xmltv.xml"), "r", encoding="utf8") as xmltv_file_fd:
        xmltv_file = xmltv_file_fd.read()
    for epgoffset in [0, -124, 3490]:
        xmltv = parse_as_xmltv(
            xmltv_file, {"epgoffset": epgoffset, "epgdays": 1}, 1, {}, 0, ""
        )
        assert xmltv == [
            {
                "Test channel 1": [
                    {
                        "start": 1680390000.0 + (3600 * epgoffset),
                        "stop": 1680393600.0 + (3600 * epgoffset),
                        "title": "Test program 1",
                        "desc": "",
                        "catchup-id": "",
                    },
                    {
                        "start": 1680393600.0 + (3600 * epgoffset),
                        "stop": 1680397200.0 + (3600 * epgoffset),
                        "title": "Test program 2",
                        "desc": "Test description",
                        "catchup-id": "",
                    },
                ]
            },
            {"testchan": ["Test channel 1"]},
            {"test channel 1": "http://127.0.0.1/testchannel1.png"},
        ]
