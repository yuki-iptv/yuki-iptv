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
