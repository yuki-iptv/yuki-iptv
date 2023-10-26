#
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
import os
import sys
import time
import zipfile
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), "usr", "lib", "yuki-iptv")))

from yuki_iptv.epg_jtv import parse_epg_zip_jtv  # noqa: E402


def test_jtv():
    os.environ["TZ"] = "UTC"
    time.tzset()
    zip_file = zipfile.ZipFile(Path("tests", "jtv", "test_jtv.zip"), "r")
    jtv = parse_epg_zip_jtv(zip_file)
    assert jtv == {
        "Test Channel": [
            {
                "desc": "",
                "start": 1698307200.0,
                "stop": 1698307800.0,
                "title": "Example program 1",
            },
            {
                "desc": "",
                "start": 1698307800.0,
                "stop": 1698308100.0,
                "title": "Example program 2",
            },
        ]
    }
