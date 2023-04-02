#
# Copyright (c) 2021-2022 Astroncia <kestraly@gmail.com>
# Copyright (c) 2023 yuki-chan-nya
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
import time
import datetime
import re
import traceback
import logging

logger = logging.getLogger(__name__)


def format_catchup_array(array0):
    if 'catchup' not in array0:
        array0['catchup'] = 'default'
    if 'catchup-source' not in array0:
        array0['catchup-source'] = ''
    if 'catchup-days' not in array0:
        array0['catchup-days'] = '1'

    if not array0['catchup-source'] and \
       array0['catchup'] not in ('flussonic', 'flussonic-hls', 'flussonic-ts', 'fs', 'xc'):
        array0['catchup'] = 'shift'

    if array0['catchup-source']:
        if not (
            array0['catchup-source'].startswith("http://") or array0['catchup-source'].startswith("https://")
        ):
            array0['catchup'] = 'append'
    return array0


def format_placeholders(start_time, end_time, catchup_id, orig_url):
    if start_time == 'TEST':
        return orig_url
    logger.info("")
    logger.info(f"orig placeholder url: {orig_url}")
    start_timestamp = int(time.mktime(time.strptime(start_time, '%d.%m.%Y %H:%M:%S')))
    end_timestamp = int(time.mktime(time.strptime(end_time, '%d.%m.%Y %H:%M:%S')))
    duration = int(end_timestamp - start_timestamp)

    current_utc = int(time.time())
    utcend = start_timestamp + duration
    offset2 = int(current_utc - start_timestamp)

    start_timestamp_1 = list(
        reversed(start_time.split(" ")[0].split("."))
    ) + start_time.split(" ")[1].split(":")

    orig_url = orig_url.replace('${utc}', str(start_timestamp))
    orig_url = orig_url.replace('{utc}', str(start_timestamp))

    orig_url = orig_url.replace('${start}', str(start_timestamp))
    orig_url = orig_url.replace('{start}', str(start_timestamp))

    orig_url = orig_url.replace('${lutc}', str(current_utc))
    orig_url = orig_url.replace('{lutc}', str(current_utc))

    orig_url = orig_url.replace('${now}', str(current_utc))
    orig_url = orig_url.replace('{now}', str(current_utc))

    orig_url = orig_url.replace('${timestamp}', str(current_utc))
    orig_url = orig_url.replace('{timestamp}', str(current_utc))

    orig_url = orig_url.replace('${utcend}', str(utcend))
    orig_url = orig_url.replace('{utcend}', str(utcend))

    orig_url = orig_url.replace('${end}', str(utcend))
    orig_url = orig_url.replace('{end}', str(utcend))

    orig_url = orig_url.replace('${Y}', str(start_timestamp_1[0]))
    orig_url = orig_url.replace('{Y}', str(start_timestamp_1[0]))

    orig_url = orig_url.replace('${m}', str(start_timestamp_1[1]))
    orig_url = orig_url.replace('{m}', str(start_timestamp_1[1]))

    orig_url = orig_url.replace('${d}', str(start_timestamp_1[2]))
    orig_url = orig_url.replace('{d}', str(start_timestamp_1[2]))

    orig_url = orig_url.replace('${H}', str(start_timestamp_1[3]))
    orig_url = orig_url.replace('{H}', str(start_timestamp_1[3]))

    orig_url = orig_url.replace('${M}', str(start_timestamp_1[4]))
    orig_url = orig_url.replace('{M}', str(start_timestamp_1[4]))

    orig_url = orig_url.replace('${S}', str(start_timestamp_1[5]))
    orig_url = orig_url.replace('{S}', str(start_timestamp_1[5]))

    orig_url = orig_url.replace('${duration}', str(duration))
    orig_url = orig_url.replace('{duration}', str(duration))

    orig_url = orig_url.replace('${catchup-id}', str(catchup_id))
    orig_url = orig_url.replace('{catchup-id}', str(catchup_id))

    try:
        duration_re = sorted(re.findall(r'\$?{duration:\d+}', orig_url))
        if duration_re:
            for duration_re_i in duration_re:
                duration_re_i_parse = int(duration_re_i.split(':')[1].split('}')[0])
                orig_url = orig_url.replace(
                    duration_re_i,
                    str(int(duration / duration_re_i_parse))
                )
    except:
        logger.warning("format_placeholders / duration_re parsing failed")
        logger.warning(traceback.format_exc())

    try:
        offset_re = sorted(re.findall(r'\$?{offset:\d+}', orig_url))
        if offset_re:
            for offset_re_i in offset_re:
                offset_re_i_parse = int(offset_re_i.split(':')[1].split('}')[0])
                orig_url = orig_url.replace(
                    offset_re_i,
                    str(int(offset2 / offset_re_i_parse))
                )
    except:
        logger.warning("format_placeholders / offset_re parsing failed")
        logger.warning(traceback.format_exc())

    utc_time = datetime.datetime.fromtimestamp(
        start_timestamp
    ).strftime("%Y-%m-%d-%H-%M-%S").split("-")
    lutc_time = datetime.datetime.fromtimestamp(
        current_utc
    ).strftime("%Y-%m-%d-%H-%M-%S").split("-")
    utcend_time = datetime.datetime.fromtimestamp(
        utcend
    ).strftime("%Y-%m-%d-%H-%M-%S").split("-")

    try:
        specifiers_re = re.findall(
            r"((\$?){(utc|start|lutc|now|timestamp|utcend|end):([YmdHMS])(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)})",  # noqa: E501
            orig_url
        )
        if specifiers_re:
            for specifiers_re_i in specifiers_re:
                specifiers_re_i_o = specifiers_re_i[0]
                spec_name = str(specifiers_re_i_o.split("{")[1].split(":")[0])
                spec_val = str(specifiers_re_i_o.split(":")[1].split("}")[0])
                if spec_name in ('utc', 'start'):
                    spec_val = spec_val.replace('Y', str(utc_time[0]))
                    spec_val = spec_val.replace('m', str(utc_time[1]))
                    spec_val = spec_val.replace('d', str(utc_time[2]))
                    spec_val = spec_val.replace('H', str(utc_time[3]))
                    spec_val = spec_val.replace('M', str(utc_time[4]))
                    spec_val = spec_val.replace('S', str(utc_time[5]))
                elif spec_name in ('lutc', 'now', 'timestamp'):
                    spec_val = spec_val.replace('Y', str(lutc_time[0]))
                    spec_val = spec_val.replace('m', str(lutc_time[1]))
                    spec_val = spec_val.replace('d', str(lutc_time[2]))
                    spec_val = spec_val.replace('H', str(lutc_time[3]))
                    spec_val = spec_val.replace('M', str(lutc_time[4]))
                    spec_val = spec_val.replace('S', str(lutc_time[5]))
                elif spec_name in ('utcend', 'end'):
                    spec_val = spec_val.replace('Y', str(utcend_time[0]))
                    spec_val = spec_val.replace('m', str(utcend_time[1]))
                    spec_val = spec_val.replace('d', str(utcend_time[2]))
                    spec_val = spec_val.replace('H', str(utcend_time[3]))
                    spec_val = spec_val.replace('M', str(utcend_time[4]))
                    spec_val = spec_val.replace('S', str(utcend_time[5]))
                orig_url = orig_url.replace(specifiers_re_i_o, str(spec_val))
    except:
        logger.warning("format_placeholders / specifiers_re parsing failed")
        logger.warning(traceback.format_exc())

    logger.info(f"formatted placeholder url: {orig_url}")
    logger.info("")
    return orig_url


# https://github.com/kodi-pvr/pvr.iptvsimple/blob/2143e856dc3f21e4573210cfec73900e65919ef8/src/iptvsimple/data/Channel.cpp#L440
def get_catchup_url(chan_url, arr1, start_time, end_time, catchup_id):
    play_url = chan_url
    if arr1['catchup'] == 'default':
        play_url = format_placeholders(
            start_time, end_time, catchup_id, arr1['catchup-source']
        )
    elif arr1['catchup'] == 'append':
        play_url = chan_url + format_placeholders(
            start_time, end_time, catchup_id, arr1['catchup-source']
        )
    elif arr1['catchup'] == 'shift':
        if '?' in chan_url:
            play_url = chan_url + format_placeholders(
                start_time, end_time, catchup_id, '&utc={utc}&lutc={lutc}'
            )
        else:
            play_url = chan_url + format_placeholders(
                start_time, end_time, catchup_id, '?utc={utc}&lutc={lutc}'
            )
    elif arr1['catchup'] in ('flussonic', 'flussonic-hls', 'flussonic-ts', 'fs'):
        fs_url = chan_url
        logger.info("")
        logger.info(f"orig fs url: {fs_url}")
        flussonic_re = re.findall(
            r"^(http[s]?://[^/]+)/(.*)/([^/]*)(mpegts|\.m3u8)(\?.+=.+)?$",
            chan_url
        )
        if flussonic_re:
            if len(flussonic_re[0]) == 5:
                fs_host = flussonic_re[0][0]
                fs_chanid = flussonic_re[0][1]
                fs_listtype = flussonic_re[0][2]
                fs_streamtype = flussonic_re[0][3]
                fs_urlappend = flussonic_re[0][4]
                if fs_streamtype == 'mpegts':
                    fs_url = "{}/{}/timeshift_abs-{}.ts{}".format(
                        fs_host,
                        fs_chanid,
                        '${start}',
                        fs_urlappend
                    )
                else:
                    if fs_listtype == 'index':
                        fs_url = "{}/{}/timeshift_rel-{}.m3u8{}".format(
                            fs_host,
                            fs_chanid,
                            '{offset:1}',
                            fs_urlappend
                        )
                    else:
                        fs_url = "{}/{}/{}-timeshift_rel-{}.m3u8{}".format(
                            fs_host,
                            fs_chanid,
                            fs_listtype,
                            '{offset:1}',
                            fs_urlappend
                        )
        else:
            flussonic_re_2 = re.findall(
                r"^(http[s]?://[^/]+)/(.*)/([^\\?]*)(\\?.+=.+)?$",
                chan_url
            )
            if flussonic_re_2:
                if len(flussonic_re_2[0]) == 4:
                    fs_host = flussonic_re_2[0][0]
                    fs_chanid = flussonic_re_2[0][1]
                    fs_urlappend = flussonic_re_2[0][3]
                    if arr1['catchup'] in ('flussonic-ts', 'fs'):
                        fs_url = "{}/{}/timeshift_abs-{}.ts{}".format(
                            fs_host,
                            fs_chanid,
                            '${start}',
                            fs_urlappend
                        )
                    elif arr1['catchup'] in ('flussonic', 'flussonic-hls'):
                        fs_url = "{}/{}/timeshift_rel-{}.m3u8{}".format(
                            fs_host,
                            fs_chanid,
                            '{offset:1}',
                            fs_urlappend
                        )
        play_url = format_placeholders(
            start_time, end_time, catchup_id, fs_url
        )
    elif arr1['catchup'] == 'xc':
        xc_url = chan_url
        logger.info("")
        logger.info(f"orig xc url: {xc_url}")
        xc_re = re.findall(
            r"^(http[s]?://[^/]+)/(?:live/)?([^/]+)/([^/]+)/([^/\.]+)(\.m3u[8]?)?$",
            chan_url
        )
        if xc_re:
            if len(xc_re[0]) == 5:
                xc_host = xc_re[0][0]
                xc_username = xc_re[0][1]
                xc_password = xc_re[0][2]
                xc_chanid = xc_re[0][3]
                xc_extension = xc_re[0][4]
                if not xc_extension:
                    xc_extension = ".ts"
                xc_url = "{}/timeshift/{}/{}/{}/{}/{}{}".format(
                    xc_host,
                    xc_username,
                    xc_password,
                    '{duration:60}',
                    '{Y}-{m}-{d}:{H}-{M}',
                    xc_chanid,
                    xc_extension
                )
        play_url = format_placeholders(
            start_time, end_time, catchup_id, xc_url
        )
    return play_url


def format_url_clean(url5):
    if '^^^^^^^^^^' in url5:
        url5 = url5.split('^^^^^^^^^^')[0]
    return url5


def parse_specifiers_now_url(url4):
    if url4.endswith("/icons/main.png") or url4.endswith("/icons_dark/main.png"):
        return url4
    logger.info("")
    logger.info(f"orig spec url: {format_url_clean(url4)}")
    current_utc_str = int(time.time())
    url4 = url4.replace('${lutc}', str(current_utc_str))
    url4 = url4.replace('{lutc}', str(current_utc_str))

    url4 = url4.replace('${now}', str(current_utc_str))
    url4 = url4.replace('{now}', str(current_utc_str))

    url4 = url4.replace('${timestamp}', str(current_utc_str))
    url4 = url4.replace('{timestamp}', str(current_utc_str))

    cur_utc_time = datetime.datetime.fromtimestamp(
        current_utc_str
    ).strftime("%Y-%m-%d-%H-%M-%S").split("-")

    try:
        specifiers_re_url = re.findall(
            r"((\$?){(lutc|now|timestamp):([YmdHMS])(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)(-?)([YmdHMS]?)})",  # noqa: E501
            url4
        )
        if specifiers_re_url:
            for specifiers_re_url_i in specifiers_re_url:
                spec_val_1 = str(specifiers_re_url_i[0].split(":")[1].split("}")[0])
                spec_val_1 = spec_val_1.replace('Y', str(cur_utc_time[0]))
                spec_val_1 = spec_val_1.replace('m', str(cur_utc_time[1]))
                spec_val_1 = spec_val_1.replace('d', str(cur_utc_time[2]))
                spec_val_1 = spec_val_1.replace('H', str(cur_utc_time[3]))
                spec_val_1 = spec_val_1.replace('M', str(cur_utc_time[4]))
                spec_val_1 = spec_val_1.replace('S', str(cur_utc_time[5]))
                url4 = url4.replace(specifiers_re_url_i[0], str(spec_val_1))
    except:
        logger.warning("parse_specifiers_now_url / specifiers_re_url parsing failed")
        logger.warning(traceback.format_exc())

    logger.info(f"after spec url: {format_url_clean(url4)}")
    logger.info("")
    return url4
