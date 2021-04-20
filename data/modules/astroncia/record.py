'''
Copyright 2021 Astroncia

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
from data.modules.astroncia.ua import user_agent

ffmpeg_proc = None

def record(input_url, out_file):
    global ffmpeg_proc
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
            '-icy', '0',
            '-i', input_url,
            '-map', '0',
            '-map', '-0:s',
            '-codec', 'copy',
            out_file
        ]
    else:
        arr = [
            ffmpeg_path,
            '-i', input_url,
            '-map', '0',
            '-map', '-0:s',
            '-codec', 'copy',
            out_file
        ]
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    ffmpeg_proc = subprocess.Popen(
        arr,
        shell=False,
        startupinfo=startupinfo
    )

def stop_record():
    global ffmpeg_proc
    if ffmpeg_proc:
        ffmpeg_proc.kill()
        ffmpeg_proc.wait()
        ffmpeg_proc = None
