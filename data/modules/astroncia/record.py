'''
Copyright (C) 2021 Astroncia

    This file is part of Astroncia IPTV.

    Astroncia IPTV is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Astroncia IPTV is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Astroncia IPTV.  If not, see <https://www.gnu.org/licenses/>.
'''
import os
import subprocess
from pathlib import Path
from data.modules.astroncia.ua import get_user_agent_for_channel
from data.modules.astroncia.time import print_with_time

ffmpeg_proc = None

def record(input_url, out_file, channel_name, http_referer):
    global ffmpeg_proc
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open(os.devnull, 'wb')
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if os.name == 'nt':
        ffmpeg_path = str(Path(os.getcwd(), 'data', 'modules', 'binary', 'ffmpeg.exe'))
    else:
        if os.path.isfile(str(Path(os.getcwd(), 'ffmpeg'))):
            ffmpeg_path = str(Path(os.getcwd(), 'ffmpeg'))
        else:
            ffmpeg_path = 'ffmpeg'
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            ffmpeg_path,
            '-user_agent', user_agent,
            '-headers', http_referer,
            '-icy', '0',
            '-i', input_url,
            '-map', '0:0',
            '-map', '0:1',
            '-map', '-0:s',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '0:0',
            '-map', '0:1',
            '-map', '-0:s',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    ffmpeg_proc = subprocess.Popen(
        arr,
        shell=False,
        startupinfo=startupinfo,
        stdout=DEVNULL,
        stderr=subprocess.STDOUT
    )

def record_return(input_url, out_file, channel_name, http_referer):
    try:
        from subprocess import DEVNULL
    except ImportError:
        DEVNULL = open(os.devnull, 'wb')
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if os.name == 'nt':
        ffmpeg_path = str(Path(os.getcwd(), 'data', 'modules', 'binary', 'ffmpeg.exe'))
    else:
        if os.path.isfile(str(Path(os.getcwd(), 'ffmpeg'))):
            ffmpeg_path = str(Path(os.getcwd(), 'ffmpeg'))
        else:
            ffmpeg_path = 'ffmpeg'
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            ffmpeg_path,
            '-user_agent', user_agent,
            '-headers', http_referer,
            '-icy', '0',
            '-i', input_url,
            '-map', '0:0',
            '-map', '0:1',
            '-map', '-0:s',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '0:0',
            '-map', '0:1',
            '-map', '-0:s',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.Popen(
        arr,
        shell=False,
        startupinfo=startupinfo,
        stdout=DEVNULL,
        stderr=subprocess.STDOUT
    )

def stop_record():
    global ffmpeg_proc
    if ffmpeg_proc:
        ffmpeg_proc.kill()
        ffmpeg_proc.wait()
        ffmpeg_proc = None
