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
import re
import datetime
import logging
from yuki_iptv.settings import parse_settings

logger = logging.getLogger(__name__)

months = [
    "января",
    "февраля",
    "марта",
    "апреля",
    "мая",
    "июня",
    "июля",
    "августа",
    "сентября",
    "октября",
    "ноября",
    "декабря",
]
months_regex = re.compile(
    "^(.*)\\. (([0-9][0-9]) (января|февраля|марта|апреля|мая|июня|июля|августа"
    "|сентября|октября|ноября|декабря))\\. (.*)"
)
date_regex = re.compile(r"^([0-9][0-9]:[0-9][0-9]) (.*)")


def parse_programmes(programmes_chan, channel, array_out, settings):
    i = -1
    morning_passed = False
    for programme in programmes_chan:
        i += 1
        re2 = date_regex.findall(programme)
        if re2 and len(re2[0]) == 2:
            timestamp = channel[0]

            hour = int(re2[0][0].split(":")[0])
            minute = int(re2[0][0].split(":")[1])
            start_time = timestamp.replace(hour=hour, minute=minute).timestamp() + (
                3600 * settings["epgoffset"]
            )

            if hour > 6:
                morning_passed = True

            if hour < 7 and morning_passed:
                start_time += 60 * 60 * 24  # 1 day

            title = re2[0][1]
            description = ""

            k = 0
            m = i
            while k < 500:  # Reasonable description limit
                k += 1
                m += 1
                if m > len(programmes_chan) - 1:
                    break
                re3 = date_regex.findall(programmes_chan[m])
                re4 = months_regex.findall(programmes_chan[m])
                if (re3 and len(re3[0]) == 2) or (re4 and len(re4[0]) == 5):
                    break
                else:
                    # Description
                    description += f"{programmes_chan[m]}\n"

            if channel[1] not in array_out:
                array_out[channel[1]] = []
            array_out[channel[1]].append(
                {"start": start_time, "stop": 0, "title": title, "desc": description}
            )
    return array_out


def parse_txt(txt):
    array_out = {}
    settings, settings_loaded = parse_settings()
    try:
        txt = txt.decode("windows-1251")
    except UnicodeDecodeError:
        try:
            txt = txt.decode("utf-8")
        except Exception:
            pass
    if txt[0:6] == "tv.all":
        logger.info("TV.ALL format detected, trying to parse...")
        txt = [str1.strip() for str1 in txt.split("\n")[2:] if str1.strip()] + ["\n"]
        # day and channel name
        current_channel = None
        programmes_chan = []
        i = 0
        for text in txt:
            i += 1
            re1 = months_regex.findall(text)
            if re1 and len(re1[0]) == 5:
                if programmes_chan:
                    array_out = parse_programmes(
                        programmes_chan, current_channel, array_out, settings
                    )
                re_time = datetime.datetime.strptime(
                    f"{re1[0][2]}.{months.index(re1[0][3]) + 1}", "%d.%m"
                ).replace(year=datetime.datetime.now().year)

                if re_time < datetime.datetime.now():
                    if (
                        datetime.datetime.now().timestamp() - re_time.timestamp()
                    ) > 30 * 60 * 60 * 24:  # 30 days
                        re_time = datetime.datetime.strptime(
                            f"{re1[0][2]}.{months.index(re1[0][3]) + 1}", "%d.%m"
                        ).replace(year=datetime.datetime.now().year + 1)

                current_channel = [re_time, re1[0][4]]
                programmes_chan.clear()
            else:
                programmes_chan.append(text)
                if (i + 1) == len(txt):
                    # EOF
                    array_out = parse_programmes(
                        programmes_chan, current_channel, array_out, settings
                    )

        # Set stop time
        for channel in array_out:
            i = 0
            for programme in array_out[channel]:
                i += 1
                if i == len(array_out[channel]):
                    array_out[channel].pop(i - 1)
                else:
                    programme["stop"] = array_out[channel][i]["start"]
    else:
        logger.warning("Invalid TXT format")
        raise Exception("Invalid TXT format")
    return array_out
