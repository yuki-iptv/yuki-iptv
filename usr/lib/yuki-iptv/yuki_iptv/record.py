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
import logging
import subprocess
import threading

logger = logging.getLogger(__name__)


class YukiData:
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
    if YukiData.ffmpeg_proc:
        ffmpeg_ret_code = YukiData.ffmpeg_proc.returncode
        if ffmpeg_ret_code == 0:
            ffmpeg_ret_code = 1
        if ffmpeg_ret_code:
            YukiData.ffmpeg_proc = None
            ret = True
        else:
            ret = False
    return ret


def record(
    input_url, out_file, channel_name, http_referer,
    get_ua_ref_for_channel, is_return=False, is_screenshot=False
):
    '''Main recording function'''
    if http_referer == 'Referer: ':
        http_referer = ''
    useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name)
    user_agent = useragent_ref
    if referer_ref:
        http_referer = f'Referer: {referer_ref}'
    action = 'record'
    if is_screenshot:
        action = 'screenshot'
    logger.info(f"Using user agent '{user_agent}' for {action} channel '{channel_name}'")
    logger.info(f"HTTP headers: '{http_referer}'")
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
        YukiData.ffmpeg_proc_screenshot = subprocess.Popen(
            arr,
            shell=False,
            start_new_session=True,
            startupinfo=None
        )
        try:
            async_wait_process(YukiData.ffmpeg_proc_screenshot)
        except:
            pass
    else:
        if not is_return:
            YukiData.ffmpeg_proc = subprocess.Popen(
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


def record_return(input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel):
    '''Record with return subprocess'''
    return record(input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel, True)


def stop_record():
    '''Stop recording'''
    if YukiData.ffmpeg_proc:
        YukiData.ffmpeg_proc.terminate()
        try:
            async_wait_process(YukiData.ffmpeg_proc)
        except:
            pass
        # YukiData.ffmpeg_proc = None
