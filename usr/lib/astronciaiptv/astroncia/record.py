'''
Copyright (c) 2021-2022 Astroncia

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
from astroncia.ua import get_user_agent_for_channel
from astroncia.time import print_with_time

class astroncia_data: # pylint: disable=too-few-public-methods
    ffmpeg_proc = None

def is_ffmpeg_recording():
    ret = -2
    if astroncia_data.ffmpeg_proc:
        ffmpeg_ret_code = astroncia_data.ffmpeg_proc.returncode
        if ffmpeg_ret_code == 0:
            ffmpeg_ret_code = 1
        if ffmpeg_ret_code:
            astroncia_data.ffmpeg_proc = None
            ret = True
        else:
            ret = False
    return ret

def record(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    ffmpeg_path = 'ffmpeg'
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            ffmpeg_path,
            '-user_agent', user_agent,
            '-headers', http_referer,
            '-icy', '0',
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    astroncia_data.ffmpeg_proc = subprocess.Popen(
        arr,
        shell=False,
        start_new_session=True,
        startupinfo=None
    )

def record_return(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for record channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    ffmpeg_path = 'ffmpeg'
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            ffmpeg_path,
            '-user_agent', user_agent,
            '-headers', http_referer,
            '-icy', '0',
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    return subprocess.Popen(
        arr,
        shell=False,
        start_new_session=True,
        startupinfo=None
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
        #astroncia_data.ffmpeg_proc = None

def make_ffmpeg_screenshot(input_url, out_file, channel_name, http_referer):
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    print_with_time("Using user agent '{}' for screenshot channel '{}'".format(user_agent, channel_name))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    ffmpeg_path = 'ffmpeg'
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            ffmpeg_path,
            '-user_agent', user_agent,
            '-headers', http_referer,
            '-icy', '0',
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-an',
            '-frames:v', '1',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-an',
            '-frames:v', '1',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    astroncia_data.ffmpeg_proc_screenshot = subprocess.Popen(
        arr,
        shell=False,
        start_new_session=True,
        startupinfo=None
    )
    try:
        async_wait_process(astroncia_data.ffmpeg_proc_screenshot)
    except: # pylint: disable=bare-except
        pass
