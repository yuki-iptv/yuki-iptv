#
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
import logging
import traceback
import datetime
import struct
from yuki_iptv.settings import parse_settings

logger = logging.getLogger(__name__)


def parse_jtv(ndx, pdt, settings):
    jtv_headers = [
        b'JTV 3.x TV Program Data\x0A\x0A\x0A',
        b'JTV 3.x TV Program Data\xA0\xA0\xA0'
    ]
    if pdt[0:26] not in jtv_headers:
        logger.debug("Invalid PDT file!")
        return []

    schedules = []

    if len(ndx[0:2]) != 2:
        logger.debug("Invalid NDX file!")
        return []

    total_num = struct.unpack('<H', ndx[0:2])[0]
    ndx = ndx[2:]

    for i in range(0, total_num):
        try:
            entry = ndx[i * 12:12 + (i * 12)]

            if len(entry[0:2]) != 2 or entry[0:2] != b'\x00\x00':
                logger.debug("JTV format violation detected!")
                continue

            if len(entry[2:10]) != 8:
                logger.debug("Broken JTV time detected")
                continue
            filetime = struct.unpack('<Q', entry[2:10])[0]
            start_time = (datetime.datetime(
                year=1601, month=1, day=1  # FILETIME
            ) + datetime.timedelta(
                microseconds=filetime / 10
            )).timestamp() + (3600 * settings["epgoffset"])

            if len(entry[10:12]) != 2:
                logger.debug("Broken JTV offset detected")
                continue
            offset = struct.unpack('<H', entry[10:12])[0]

            if len(pdt[offset:offset + 2]) != 2:
                logger.debug("Broken JTV count detected")
                continue
            count = struct.unpack('<H', pdt[offset:offset + 2])[0]

            program_name = pdt[offset + 2:offset + 2 + count]
            try:
                program_name = program_name.decode('utf-8')
            except UnicodeDecodeError:
                program_name = program_name.decode('cp1251')

            if isinstance(program_name, str):
                if count < 1000:  # Workaround, do not allow broken entries
                    schedules.append({
                        'start': start_time,
                        'stop': 0,
                        'title': program_name,
                        'desc': ''
                    })
                    schedules[len(schedules) - 2]['stop'] = start_time
                else:
                    logger.debug("Broken JTV entry found!")
            else:
                raise Exception("Program name decoding failed!")
        except:
            logger.debug("JTV parse failed!")
            logger.debug(traceback.format_exc())
    # Remove last program because we don't know stop time
    if schedules:
        schedules.pop(len(schedules) - 1)
    return schedules


def parse_epg_zip_jtv(zip_file):
    settings, settings_loaded = parse_settings()
    array_out = {}
    namelist = zip_file.namelist()
    for name in namelist:
        if name.endswith('.ndx'):
            channel_name = name.replace('.ndx', '')
            pdt_filename = name.replace('.ndx', '.pdt')
            if pdt_filename in namelist:
                with zip_file.open(pdt_filename) as pdt_file:
                    with zip_file.open(name) as ndx_file:
                        parsed_jtv = parse_jtv(
                            ndx_file.read(), pdt_file.read(), settings
                        )
                        if parsed_jtv:
                            array_out[channel_name] = parsed_jtv
                            if channel_name.replace('_', ' ') not in array_out:
                                array_out[channel_name.replace('_', ' ')] = \
                                    parsed_jtv
            else:
                logger.debug("No PDT file found for channel!")
    if not array_out:
        raise Exception("JTV parse failed!")
    return array_out
