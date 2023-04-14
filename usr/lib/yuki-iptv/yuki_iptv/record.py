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
import gettext
from yuki_iptv.qt import get_qt_library
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

logger = logging.getLogger(__name__)
_ = gettext.gettext


class YukiData:
    ffmpeg_proc = None
    ffmpeg_processes = None
    show_record_exception = None


def is_ffmpeg_recording():
    ret = -2
    if YukiData.ffmpeg_proc:
        if YukiData.ffmpeg_proc.processId() == 0:
            YukiData.ffmpeg_proc = None
            ret = True
        else:
            ret = False
    return ret


def exit_handler(exit_code, exit_status):
    if exit_status != QtCore.QProcess.ExitStatus.NormalExit:
        logger.warning("ffmpeg process crashed")
        ffmpeg_process_found = False
        if YukiData.show_record_exception:
            try:
                if YukiData.ffmpeg_proc and YukiData.ffmpeg_proc.processId() == 0 \
                   and YukiData.ffmpeg_proc.exitCode() == exit_code \
                   and YukiData.ffmpeg_proc.exitStatus() == exit_status:
                    standard_output = YukiData.ffmpeg_proc.readAllStandardOutput()
                    try:
                        standard_output = bytes(standard_output).decode('utf-8')
                        standard_output = '\n'.join(standard_output.split('\n')[-15:])
                    except:
                        pass
                    standard_error = YukiData.ffmpeg_proc.readAllStandardError()
                    try:
                        standard_error = bytes(standard_error).decode('utf-8')
                        standard_error = '\n'.join(standard_error.split('\n')[-15:])
                    except:
                        pass
                    ffmpeg_process_found = True
                    YukiData.show_record_exception(
                        _('ffmpeg crashed!') + '\n'
                        '' + _('exit code:') + ' ' + str(exit_code) + ''
                        '\nstdout:\n' + str(standard_output) + ''
                        '\nstderr:\n' + str(standard_error)
                    )
                else:
                    if YukiData.ffmpeg_processes:
                        for ffmpeg_process in YukiData.ffmpeg_processes:
                            if ffmpeg_process and ffmpeg_process.processId() == 0 \
                               and ffmpeg_process[0].exitCode() == exit_code \
                               and ffmpeg_process[0].exitStatus() == exit_status:
                                standard_output = ffmpeg_process[0].readAllStandardOutput()
                                try:
                                    standard_output = bytes(standard_output).decode('utf-8')
                                    standard_output = '\n'.join(standard_output.split('\n')[-15:])
                                except:
                                    pass
                                standard_error = ffmpeg_process[0].readAllStandardError()
                                try:
                                    standard_error = bytes(standard_error).decode('utf-8')
                                    standard_error = '\n'.join(standard_error.split('\n')[-15:])
                                except:
                                    pass
                                ffmpeg_process_found = True
                                YukiData.show_record_exception(
                                    _('ffmpeg crashed!') + '\n'
                                    '' + _('exit code:') + ' ' + str(exit_code) + ''
                                    '\nstdout:\n' + str(standard_output) + ''
                                    '\nstderr:\n' + str(standard_error)
                                )
            except:
                pass
            if not ffmpeg_process_found:
                YukiData.show_record_exception(_('ffmpeg crashed!'))


def record(
    input_url, out_file, channel_name, http_referer,
    get_ua_ref_for_channel, is_return=False
):
    if http_referer == 'Referer: ':
        http_referer = ''
    useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name)
    user_agent = useragent_ref
    if referer_ref:
        http_referer = f'Referer: {referer_ref}'
    logger.info(f"Using user agent '{user_agent}' for record channel '{channel_name}'")
    logger.info(f"HTTP headers: '{http_referer}'")
    if input_url.startswith('http://') or input_url.startswith('https://'):
        arr = [
            '-nostats',
            '-hide_banner',
            '-loglevel', 'warning',
            '-user_agent', user_agent,
            '-headers', http_referer,
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
            '-nostats',
            '-hide_banner',
            '-loglevel', 'warning',
            '-i', input_url,
            '-map', '-0:s?',
            '-sn',
            '-map', '-0:d?',
            '-codec', 'copy',
            '-acodec', 'aac',
            '-max_muxing_queue_size', '4096',
            out_file
        ]
    if not is_return:
        YukiData.ffmpeg_proc = QtCore.QProcess()
        YukiData.ffmpeg_proc.start('ffmpeg', arr)
        YukiData.ffmpeg_proc.finished.connect(exit_handler)
    else:
        ffmpeg_ret_proc = QtCore.QProcess()
        ffmpeg_ret_proc.start('ffmpeg', arr)
        ffmpeg_ret_proc.finished.connect(exit_handler)
        return ffmpeg_ret_proc


def record_return(input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel):
    return record(input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel, True)


def stop_record():
    if YukiData.ffmpeg_proc:
        YukiData.ffmpeg_proc.terminate()


def init_record(show_exception, ffmpeg_processes):
    YukiData.show_record_exception = show_exception
    YukiData.ffmpeg_processes = ffmpeg_processes
