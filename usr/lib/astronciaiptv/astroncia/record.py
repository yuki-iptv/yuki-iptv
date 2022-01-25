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
import subprocess
import threading
from astroncia.ua import get_user_agent_for_channel
from astroncia.time import print_with_time

class AstronciaData: # pylint: disable=too-few-public-methods
    '''Main class'''
    ffmpeg_proc = None

def async_function(func):
    '''Used as a decorator to run things in the background'''
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

@async_function
def async_wait_process(proc):
    '''Wait for process to finish'''
    proc.wait()

def is_ffmpeg_recording():
    '''Check is currently recording'''
    ret = -2
    if AstronciaData.ffmpeg_proc:
        ffmpeg_ret_code = AstronciaData.ffmpeg_proc.returncode
        if ffmpeg_ret_code == 0:
            ffmpeg_ret_code = 1
        if ffmpeg_ret_code:
            AstronciaData.ffmpeg_proc = None
            ret = True
        else:
            ret = False
    return ret

def record( # pylint: disable=inconsistent-return-statements
    input_url, out_file, channel_name, http_referer,
    parse_url_ua, is_return=False, is_screenshot=False
): # pylint: disable=too-many-arguments
    '''Main recording function'''
    if http_referer == 'Referer: ':
        http_referer = ''
    user_agent = get_user_agent_for_channel(channel_name)
    input_url, ua_data = parse_url_ua(input_url)
    if ua_data['ua']:
        user_agent = ua_data['ua']
    if ua_data['ref']:
        http_referer = 'Referer: {}'.format(ua_data['ref'])
    action = 'record'
    if is_screenshot:
        action = 'screenshot'
    print_with_time("Using user agent '{}' for {} channel '{}'".format(
        user_agent, action, channel_name
    ))
    print_with_time("HTTP headers: '{}'".format(http_referer))
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            'ffmpeg',
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
            'ffmpeg',
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    if is_screenshot:
        if input_url.startswith('http://') or input_url.startswith('https://'):
            arr = [
                'ffmpeg',
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
                'ffmpeg',
                '-i', input_url,
                '-map', '-0:s?',
                '-sn',
                '-map', '-0:d?',
                '-an',
                '-frames:v', '1',
                '-max_muxing_queue_size', '4096',
                out_file
            ]
        AstronciaData.ffmpeg_proc_screenshot = subprocess.Popen(
            arr,
            shell=False,
            start_new_session=True,
            startupinfo=None
        )
        try:
            async_wait_process(AstronciaData.ffmpeg_proc_screenshot)
        except: # pylint: disable=bare-except
            pass
    else:
        if not is_return:
            AstronciaData.ffmpeg_proc = subprocess.Popen(
                arr,
                shell=False,
                start_new_session=True,
                startupinfo=None
            )
        else:
            return subprocess.Popen(
                arr,
                shell=False,
                start_new_session=True,
                startupinfo=None
            )

def record_return(input_url, out_file, channel_name, http_referer, parse_url_ua):
    '''Record with return subprocess'''
    return record(input_url, out_file, channel_name, http_referer, parse_url_ua, True)

def stop_record():
    '''Stop recording'''
    if AstronciaData.ffmpeg_proc:
        AstronciaData.ffmpeg_proc.terminate()
        try:
            async_wait_process(AstronciaData.ffmpeg_proc)
        except: # pylint: disable=bare-except
            pass
        #AstronciaData.ffmpeg_proc = None

def make_ffmpeg_screenshot(input_url, out_file, channel_name, http_referer, parse_url_ua):
    '''Create screenshot using ffmpeg'''
    record(input_url, out_file, channel_name, http_referer, parse_url_ua, False, True)
