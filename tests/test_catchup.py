#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 yuki-chan-nya <yukichandev@proton.me>
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
# along with yuki-iptv  If not, see <http://www.gnu.org/licenses/>.
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License
# https://creativecommons.org/licenses/by/4.0/
#
import os
import sys
import datetime
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), "usr", "lib", "yuki-iptv")))

from yuki_iptv.catchup import (get_catchup_url, parse_specifiers_now_url,  # noqa: E402
                               format_placeholders)


# https://github.com/kodi-pvr/pvr.iptvsimple/blob/2143e856dc3f21e4573210cfec73900e65919ef8/src/iptvsimple/data/Channel.cpp#L467
def test_catchup():
    urls = {
        "http://127.0.0.1/index.m3u8": [
            "shift",
            "http://127.0.0.1/index.m3u8?utc={utc}&lutc={lutc}",
        ],
        "http://127.0.0.1/index.m3u8?example": [
            "shift",
            "http://127.0.0.1/index.m3u8?example&utc={utc}&lutc={lutc}",
        ],
        "http://127.0.0.1/151/mpegts?token=my_token": [
            "flussonic",
            "http://127.0.0.1/151/timeshift_abs-{utc}.ts?token=my_token".replace(
                "{utc}", "${start}"
            ),
        ],
        "http://127.0.0.1:8888/325/index.m3u8?token=secret": [
            "flussonic",
            "http://127.0.0.1:8888/325/timeshift_rel-{offset:1}.m3u8?token=secret",
        ],
        "http://127.0.0.1:8888/325/mono.m3u8?token=secret": [
            "flussonic",
            "http://127.0.0.1:8888/325/mono-timeshift_rel-{offset:1}.m3u8?token=secret",
        ],
        # 'http://127.0.0.1:8888/325/live?token=my_token':
        #    ['flussonic', 'http://127.0.0.1:8888/325/{utc}.ts?token=my_token'],
        "http://127.0.0.1:8080/my@account.xc/my_password/1477": [
            "xc",
            (
                "http://127.0.0.1:8080/timeshift/my@account.xc/"
                "my_password/{duration}/{Y}-{m}-{d}:{H}-{M}/1477.ts"
            ).replace(
                "{duration}", "{duration:60}"
            ),
        ],
        "http://127.0.0.1:8080/live/my@account.xc/my_password/1477.m3u8": [
            "xc",
            (
                "http://127.0.0.1:8080/timeshift/my@account.xc/"
                "my_password/{duration}/{Y}-{m}-{d}:{H}-{M}/1477.m3u8"
            ).replace(
                "{duration}", "{duration:60}"
            ),
        ],
    }
    for url in urls:
        assert (
            get_catchup_url(url, {"catchup": urls[url][0]}, "TEST", None, None)
            == urls[url][1]
        )


def test_catchup_specifiers():
    assert parse_specifiers_now_url("http://127.0.0.1/index.m3u8?now={now:Ymd}") == \
        "http://127.0.0.1/index.m3u8?now=" + datetime.datetime.now().strftime("%Y%m%d")


def test_catchup_placeholders():
    assert format_placeholders(
        "01.01.1970 03:00:00",
        "01.01.1970 03:00:00",
        "",
        "http://127.0.0.1/index.m3u8?now={now:Ymd}"
    ) == "http://127.0.0.1/index.m3u8?now=" + datetime.datetime.now().strftime("%Y%m%d")
