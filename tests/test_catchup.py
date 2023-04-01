# SPDX-License-Identifier: GPL-3.0-or-later
# pylint: disable=missing-module-docstring, missing-function-docstring, line-too-long
import os
import sys
from pathlib import Path

sys.path.append(str(Path(os.getcwd(), 'usr', 'lib', 'yuki-iptv')))

from yuki_iptv.catchup import get_catchup_url # pylint: disable=import-error, wrong-import-position

def test_catchup():
    urls = {
        'http://127.0.0.1/index.m3u8':
            ['shift', 'http://127.0.0.1/index.m3u8?utc={utc}&lutc={lutc}'],
        'http://127.0.0.1/index.m3u8?example':
            ['shift', 'http://127.0.0.1/index.m3u8?example&utc={utc}&lutc={lutc}'],
        'http://127.0.0.1/151/mpegts?token=my_token':
            ['flussonic', 'http://127.0.0.1/151/timeshift_abs-{utc}.ts?token=my_token'.replace('{utc}', '${start}')],
        'http://127.0.0.1:8888/325/index.m3u8?token=secret':
            ['flussonic', 'http://127.0.0.1:8888/325/timeshift_rel-{offset:1}.m3u8?token=secret'],
        'http://127.0.0.1:8888/325/mono.m3u8?token=secret':
            ['flussonic', 'http://127.0.0.1:8888/325/mono-timeshift_rel-{offset:1}.m3u8?token=secret'],
        #'http://127.0.0.1:8888/325/live?token=my_token':
        #    ['flussonic', 'http://127.0.0.1:8888/325/{utc}.ts?token=my_token'],
        'http://127.0.0.1:8080/my@account.xc/my_password/1477':
            ['xc', 'http://127.0.0.1:8080/timeshift/my@account.xc/my_password/{duration}/{Y}-{m}-{d}:{H}-{M}/1477.ts'.replace('{duration}', '{duration:60}')],
        'http://127.0.0.1:8080/live/my@account.xc/my_password/1477.m3u8':
            ['xc', 'http://127.0.0.1:8080/timeshift/my@account.xc/my_password/{duration}/{Y}-{m}-{d}:{H}-{M}/1477.m3u8'.replace('{duration}', '{duration:60}')]
    }
    for url in urls:
        assert get_catchup_url(
            url,
            {
                'catchup': urls[url][0]
            },
            'TEST', None, None
        ) == urls[url][1]
