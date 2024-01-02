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
import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), "usr", "lib", "yuki-iptv")))

from yuki_iptv.epg_xmltv import parse_timestamp  # noqa: E402


def test_xmltv_timestamp():
    # TODO: 200007281733 BST
    assert int(parse_timestamp("200209", {"epgoffset": 0})) == 1030838400
    assert int(parse_timestamp("19880523083000 +0300", {"epgoffset": 0})) == 580368600
    # Positive EPG offset (+2 hours)
    assert int(parse_timestamp("200209", {"epgoffset": 2})) == 1030838400 + (3600 * 2)
    assert int(
        parse_timestamp("19880523083000 +0300", {"epgoffset": 2})
    ) == 580368600 + (3600 * 2)
    # Negative EPG offset (-2 hours)
    assert int(parse_timestamp("200209", {"epgoffset": -2})) == 1030838400 - (3600 * 2)
    assert int(
        parse_timestamp("19880523083000 +0300", {"epgoffset": -2})
    ) == 580368600 - (3600 * 2)
