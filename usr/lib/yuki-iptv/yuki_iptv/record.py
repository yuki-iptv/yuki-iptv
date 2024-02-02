#
# Copyright (c) 2021, 2022 Astroncia
# Copyright (c) 2023, 2024 Ame-chan-angel <amechanangel@proton.me>
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
# Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
# License - https://creativecommons.org/licenses/by/4.0/
#
import logging
import uuid
import gettext
import subprocess
import os
import signal
import urllib.parse
from yuki_iptv.qt import get_qt_library
from yuki_iptv.settings import parse_settings

# TODO: YouTube recording is horribly broken, needs fix
# for example, how to correctly stop yt-dlp?

qt_library, QtWidgets, QtCore, QtGui, QShortcut, QtOpenGLWidgets = get_qt_library()

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
    is_ok = True
    if exit_code != 0:
        is_ok = False
    if exit_code == 255:
        is_ok = True
    if not is_ok or exit_status != QtCore.QProcess.ExitStatus.NormalExit:
        ffmpeg_proc_program = YukiData.ffmpeg_proc.program()
        if not (
            ("yt-dlp" in ffmpeg_proc_program or "youtube-dl" in ffmpeg_proc_program)
            and exit_code == 15
        ):
            logger.warning("ffmpeg process crashed")
            ffmpeg_process_found = False
            if YukiData.show_record_exception:
                try:
                    if (
                        YukiData.ffmpeg_proc
                        and YukiData.ffmpeg_proc.processId() == 0
                        and YukiData.ffmpeg_proc.exitCode() == exit_code
                        and YukiData.ffmpeg_proc.exitStatus() == exit_status
                    ):
                        standard_output = YukiData.ffmpeg_proc.readAllStandardOutput()
                        try:
                            standard_output = bytes(standard_output).decode("utf-8")
                            standard_output = "\n".join(
                                standard_output.split("\n")[-15:]
                            )
                        except Exception:
                            pass
                        standard_error = YukiData.ffmpeg_proc.readAllStandardError()
                        try:
                            standard_error = bytes(standard_error).decode("utf-8")
                            standard_error = "\n".join(standard_error.split("\n")[-15:])
                        except Exception:
                            pass
                        ffmpeg_process_found = True
                        YukiData.show_record_exception(
                            _("ffmpeg crashed!") + "\n"
                            "" + _("exit code:") + " " + str(exit_code) + ""
                            "\nstdout:\n" + str(standard_output) + ""
                            "\nstderr:\n" + str(standard_error)
                        )
                    else:
                        if YukiData.ffmpeg_processes:
                            for ffmpeg_process in YukiData.ffmpeg_processes:
                                if (
                                    ffmpeg_process
                                    and ffmpeg_process.processId() == 0
                                    and ffmpeg_process[0].exitCode() == exit_code
                                    and ffmpeg_process[0].exitStatus() == exit_status
                                ):
                                    standard_output = ffmpeg_process[
                                        0
                                    ].readAllStandardOutput()
                                    try:
                                        standard_output = bytes(standard_output).decode(
                                            "utf-8"
                                        )
                                        standard_output = "\n".join(
                                            standard_output.split("\n")[-15:]
                                        )
                                    except Exception:
                                        pass
                                    standard_error = ffmpeg_process[
                                        0
                                    ].readAllStandardError()
                                    try:
                                        standard_error = bytes(standard_error).decode(
                                            "utf-8"
                                        )
                                        standard_error = "\n".join(
                                            standard_error.split("\n")[-15:]
                                        )
                                    except Exception:
                                        pass
                                    ffmpeg_process_found = True
                                    YukiData.show_record_exception(
                                        _("ffmpeg crashed!") + "\n"
                                        "" + _("exit code:") + " " + str(exit_code) + ""
                                        "\nstdout:\n" + str(standard_output) + ""
                                        "\nstderr:\n" + str(standard_error)
                                    )
                except Exception:
                    pass
                if not ffmpeg_process_found:
                    YukiData.show_record_exception(_("ffmpeg crashed!"))


def record(
    input_url,
    out_file,
    channel_name,
    http_referer,
    get_ua_ref_for_channel,
    is_return=False,
):
    settings, settings_loaded = parse_settings()
    if http_referer == "Referer: ":
        http_referer = ""
    useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name)
    user_agent = useragent_ref
    if referer_ref:
        http_referer = f"Referer: {referer_ref}"
    logger.info(f"Using user agent '{user_agent}' for record channel '{channel_name}'")
    logger.info(f"HTTP headers: '{http_referer}'")
    uuid_add = ""
    uuid_arr = []
    if settings["uuid"]:
        uuid_add = "X-Playback-Session-Id: " + str(uuid.uuid1()) + "\r\n"
        uuid_arr = ["-headers", uuid_add]
    if input_url.startswith("http://") or input_url.startswith("https://"):
        arr = [
            "-nostats",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-user_agent",
            user_agent,
            "-headers",
            http_referer + "\r\n" + uuid_add,
            "-i",
            input_url,
            "-map",
            "-0:s?",
            "-sn",
            "-map",
            "-0:d?",
            "-codec",
            "copy",
            "-acodec",
            "aac",
            "-max_muxing_queue_size",
            "4096",
            out_file,
        ]
    else:
        arr = (
            [
                "-nostats",
                "-hide_banner",
                "-loglevel",
                "warning",
            ]
            + uuid_arr
            + [
                "-i",
                input_url,
                "-map",
                "-0:s?",
                "-sn",
                "-map",
                "-0:d?",
                "-codec",
                "copy",
                "-acodec",
                "aac",
                "-max_muxing_queue_size",
                "4096",
                out_file,
            ]
        )
    process = "ffmpeg"
    if urllib.parse.urlparse(input_url).netloc in (
        "youtube.com",
        "www.youtube.com",
        "youtube-nocookie.com",
        "www.youtube-nocookie.com",
        "youtu.be",
        "www.youtu.be",
    ):
        process = "yt-dlp"
        try:
            yt_detect_process = subprocess.Popen(
                [process, "--version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            yt_detect_process.wait()
            returncode = yt_detect_process.returncode
        except Exception:
            returncode = 1
        if returncode != 0:
            process = "youtube-dl"
        logger.info(f"YouTube detected, using {process} for recording")
        arr = [
            "--merge-output-format",
            "mkv",
            "--no-part",
            "--output",
            out_file,
            input_url,
        ]
    if not is_return:
        YukiData.ffmpeg_proc = QtCore.QProcess()
        YukiData.ffmpeg_proc.start(process, arr)
        YukiData.ffmpeg_proc.finished.connect(exit_handler)
    else:
        ffmpeg_ret_proc = QtCore.QProcess()
        ffmpeg_ret_proc.start(process, arr)
        ffmpeg_ret_proc.finished.connect(exit_handler)
        return ffmpeg_ret_proc


def record_return(
    input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel
):
    return record(
        input_url, out_file, channel_name, http_referer, get_ua_ref_for_channel, True
    )


def stop_record():
    if YukiData.ffmpeg_proc:
        ffmpeg_proc_program = YukiData.ffmpeg_proc.program()
        if "yt-dlp" in ffmpeg_proc_program or "youtube-dl" in ffmpeg_proc_program:
            try:
                child_process_ids = [
                    int(line)
                    for line in subprocess.run(
                        [
                            "ps",
                            "-opid",
                            "--no-headers",
                            "--ppid",
                            str(YukiData.ffmpeg_proc.processId()),
                        ],
                        stdout=subprocess.PIPE,
                        encoding="utf8",
                    ).stdout.splitlines()
                ]
                for child_process_id in child_process_ids:
                    logger.info(f"Terminating process with PID {child_process_id}")
                    os.kill(child_process_id, signal.SIGTERM)
            except Exception:
                pass
        YukiData.ffmpeg_proc.terminate()


def init_record(show_exception, ffmpeg_processes):
    YukiData.show_record_exception = show_exception
    YukiData.ffmpeg_processes = ffmpeg_processes
