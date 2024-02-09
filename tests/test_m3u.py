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
# Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
# License - https://creativecommons.org/licenses/by/4.0/
#
import os
import sys
import gettext
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), "usr", "lib", "yuki-iptv")))

from yuki_iptv.m3u import M3UParser  # noqa: E402

m3u_parser = M3UParser("", gettext.gettext)


def read_m3u(path):
    file = open(path, encoding="utf8")
    contents = file.read()
    file.close()
    return m3u_parser.parse_m3u(contents)


def test_m3u():
    data = [
        [
            Path("tests", "m3u", "1.m3u"),
            "http://127.0.0.1/0",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "http://127.0.0.1/referrer",
                    "title": "Example 1",
                    "tvg-ID": "EX1",
                    "tvg-group": "Example group 1",
                    "tvg-logo": "http://127.0.0.1/1,1,1,1.png",
                    "tvg-name": "Example 1",
                    "tvg-url": "http://127.0.0.1/1.xml.gz",
                    "url": "http://127.0.0.1/1.mp4",
                    "useragent": "Example/1.0",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 2",
                    "tvg-ID": "EX2",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/2.m3u8",
                    "useragent": "",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "=>(★ Example 2 ★)<=",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/2.mp4",
                    "useragent": "",
                },
                {
                    "catchup": "shift",
                    "catchup-days": "3",
                    "catchup-source": "http://127.0.0.1/?utc=11&lutc=11",
                    "referer": "",
                    "title": "Example 3",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": (
                        "http://127.0.0.1/iObU3FB)_9(A2(74(Qpw)sRer)Yk2mTbLU7LCWBab"
                        "G4wnpQwa2JZ9w)esa_uf)Tst()8PE_BR2O6JYYfzoi(wNyYatYq_)3LI()H"
                        "AUTQQc5U0hdPBjg3goTnuaPm)86Cjyhcrn6nUKlv's29sl4Q5oXn(5y(F)0"
                        "utO1iOstALx)vUU7Fs-szCOw2OZWq6AMYgV(8vk1(eOuA)A(pCZu93z(2s0"
                        "h)ope0_'1br)a)PuO(RV((O9t99Y()(WZnV0)RfeIE(Agkh(OOjm(lFdnae"
                        "abID)x_OLs)bFwbE4GsZxQGZTVxVwr480CZkKgnGDi)44YBlH()s9MK'mwv"
                        "Tc/3.mp4"
                    ),
                    "useragent": "",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 4,comma",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/ú",
                    "useragent": "",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 5",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "Example 5 tvg-name",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/5",
                    "useragent": "",
                },
            ],
        ],
        [
            Path("tests", "m3u", "2.m3u"),
            "",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 1",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/",
                    "useragent": "",
                }
            ],
        ],
        [
            Path("tests", "m3u", "3.m3u"),
            "http://127.0.0.1/example.xml.gz",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example channel",
                    "tvg-ID": "ex-tvg-id",
                    "tvg-group": "Example group",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/example",
                    "useragent": "Example/1.0",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example channel",
                    "tvg-ID": "ex-tvg-id",
                    "tvg-group": "Example group",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/example",
                    "useragent": "Example/1.0",
                },
            ],
        ],
        [
            Path("tests", "m3u", "4.m3u"),
            "http://127.0.0.1/example.xml.gz",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 1",
                    "tvg-ID": "2",
                    "tvg-group": "1",
                    "tvg-logo": "http://127.0.0.1/3.png",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/example.m3u",
                    "useragent": "Example/1.0 (Example;Example) Example",
                }
            ],
        ],
        [
            Path("tests", "m3u", "5.m3u"),
            "",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "http://127.0.0.1/examplereferer",
                    "title": "Example 1",
                    "tvg-ID": "ExampleId1",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/1",
                    "useragent": "Example/1.0 (Example; Example; Example) example",
                },
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "http://127.0.0.1/example2",
                    "title": "Example 2",
                    "tvg-ID": "ExampleId2",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1:9999/2",
                    "useragent": "Example/2.0 (Example; Example; Example) example",
                },
            ],
        ],
        [
            Path("tests", "m3u", "6.m3u"),
            "http://127.0.0.1/example6.xml.gz",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example 1",
                    "tvg-ID": "ex-tvg-id",
                    "tvg-group": "ex-group 1",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/example",
                    "useragent": "Example/1.0 (Example; example) Example",
                }
            ],
        ],
        [
            Path("tests", "m3u", "7.m3u"),
            "",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Test",
                    "tvg-ID": "ex1",
                    "tvg-group": "Group 1",
                    "tvg-logo": "",
                    "tvg-name": "",
                    "tvg-url": "",
                    "url": "https://127.0.0.1/example",
                    "useragent": (
                        "Example/1.0 (Example; example) "
                        "Example/1.0 (Example) Example/111"
                    ),
                }
            ],
        ],
        [
            Path("tests", "m3u", "8.m3u"),
            "",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example",
                    "tvg-ID": "",
                    "tvg-group": "GroupAlt",
                    "tvg-logo": "",
                    "tvg-name": "ExampleTvgId",
                    "tvg-url": "",
                    "url": "http://127.0.0.1/example",
                    "useragent": '"Example/1.0 (Example; Example; Example;)"',
                }
            ],
        ],
        [
            Path("tests", "m3u", "9.m3u"),
            "",
            [
                {
                    "catchup": "default",
                    "catchup-days": "7",
                    "catchup-source": "",
                    "referer": "",
                    "title": "Example, Example, Example",
                    "tvg-ID": "",
                    "tvg-group": "All channels",
                    "tvg-logo": "",
                    "tvg-name": "Example1, Example2, Example3",
                    "tvg-url": "",
                    "url": "http://127.0.0.1",
                    "useragent": "",
                }
            ],
        ],
    ]
    for file in data:
        m3u, tvg_url = read_m3u(file[0])
        assert tvg_url == file[1] and m3u == file[2]
