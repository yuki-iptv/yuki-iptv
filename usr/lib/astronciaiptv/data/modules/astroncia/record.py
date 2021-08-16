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
import threading
from pathlib import Path
from data.modules.astroncia.ua import get_user_agent_for_channel
from data.modules.astroncia.time import print_with_time

class astroncia_data: # pylint: disable=too-few-public-methods
    pass

astroncia_data.ffmpeg_proc = None

def record(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if os.name == 'nt':
        ffmpeg_path = str(Path(os.getcwd(), '..', '..', '..', 'binary_windows', 'ffmpeg.exe'))
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
    astroncia_data.ffmpeg_proc = subprocess.Popen(
        arr,
        shell=False,
        start_new_session=True,
        startupinfo=startupinfo
    )

def record_return(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if os.name == 'nt':
        ffmpeg_path = str(Path(os.getcwd(), '..', '..', '..', 'binary_windows', 'ffmpeg.exe'))
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
        start_new_session=True,
        startupinfo=startupinfo
    )

# Used as a decorator to run things in the background
def async_function(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@async_function
def async_wait_process(proc):
    proc.wait()

def stop_record():
    if astroncia_data.ffmpeg_proc:
        astroncia_data.ffmpeg_proc.terminate()
        try:
            async_wait_process(astroncia_data.ffmpeg_proc)
        except: # pylint: disable=bare-except
            pass
        astroncia_data.ffmpeg_proc = None

def make_ffmpeg_screenshot(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for screenshot channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if os.name == 'nt':
        ffmpeg_path = str(Path(os.getcwd(), '..', '..', '..', 'binary_windows', 'ffmpeg.exe'))
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
            '-an',
            '-frames:v', '1',
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
            '-an',
            '-frames:v', '1',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    astroncia_data.ffmpeg_proc_screenshot = subprocess.Popen(
        arr,
        shell=False,
        start_new_session=True,
        startupinfo=startupinfo
    )
    try:
        async_wait_process(astroncia_data.ffmpeg_proc_screenshot)
    except: # pylint: disable=bare-except
        pass
