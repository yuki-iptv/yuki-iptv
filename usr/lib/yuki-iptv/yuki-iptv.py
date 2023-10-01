#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
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
try:
    from yuki_iptv.plugin import init_plugins

    init_plugins()
except Exception as ex:  # to avoid module level import not at top error
    raise ex

from pathlib import Path
import sys
import os
import os.path
import time
import datetime
import json
import locale
import gettext
import logging
import signal
import argparse
import platform
import subprocess
import re
import textwrap
import hashlib
import webbrowser
import urllib
import urllib.parse
import threading
import traceback
from multiprocessing import Manager, active_children, get_context, freeze_support
from functools import partial
import chardet
import requests
import setproctitle
from unidecode import unidecode

try:
    from gi.repository import GLib
except Exception:
    pass

from yuki_iptv.qt import get_qt_library, show_exception
from yuki_iptv.epg import (
    worker,
    is_program_actual,
    load_epg_cache,
    save_epg_cache,
    exists_in_epg,
    get_epg,
)
from yuki_iptv.record import (
    record,
    record_return,
    stop_record,
    is_ffmpeg_recording,
    init_record,
)
from yuki_iptv.menubar import (
    init_yuki_iptv_menubar,
    init_menubar_player,
    populate_menubar,
    update_menubar,
    get_active_vf_filters,
    get_first_run,
    get_seq,
    reload_menubar_shortcuts,
)
from yuki_iptv.xtreamtom3u import convert_xtream_to_m3u
from yuki_iptv.m3u import M3UParser
from yuki_iptv.xspf import parse_xspf
from yuki_iptv.catchup import (
    get_catchup_url,
    parse_specifiers_now_url,
    format_url_clean,
    format_catchup_array,
)
from yuki_iptv.channel_logos import channel_logos_worker
from yuki_iptv.settings import parse_settings
from yuki_iptv.qt6compat import _exec
from yuki_iptv.m3u_editor import M3UEditor
from yuki_iptv.options import read_option, write_option
from yuki_iptv.keybinds import main_keybinds_internal, main_keybinds_default
from yuki_iptv.series import parse_series
from yuki_iptv.crossplatform import LOCAL_DIR, SAVE_FOLDER_DEFAULT
from yuki_iptv.mpv_opengl import MPVOpenGLWidget
from thirdparty.xtream import XTream, Serie

if platform.system() == "Windows":
    freeze_support()

parser = argparse.ArgumentParser(prog="yuki-iptv", description="yuki-iptv")
parser.add_argument("--version", action="store_true", help="Show version")
parser.add_argument(
    "--loglevel",
    action="store",
    help="Log level (CRITICAL, ERROR, WARNING, INFO, DEBUG) default: INFO",
)
parser.add_argument(
    "--disable-plugin", action="store", help="Disable some plugins, comma separated"
)
parser.add_argument(
    "--disable-plugins", action="store_true", help="Disable all plugins"
)
parser.add_argument("URL", help="Playlist URL or file", nargs="?")
args1, _unparsed_args = parser.parse_known_args()

loglevel = args1.loglevel if args1.loglevel else "INFO"
numeric_level = getattr(logging, loglevel.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError("Invalid log level: %s" % loglevel)

logging.basicConfig(
    format="%(asctime)s.%(msecs)03d %(name)s %(levelname)s: %(message)s",
    level=numeric_level,
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("yuki-iptv")
mpv_logger = logging.getLogger("libmpv")

if platform.system() == "Linux":
    try:
        from thirdparty.mpris_server.adapters import (
            PlayState,
            MprisAdapter,
            Microseconds,
            VolumeDecimal,
            RateDecimal,
            Track,
            DEFAULT_RATE,
        )
        from thirdparty.mpris_server.events import EventAdapter
        from thirdparty.mpris_server.server import Server
    except Exception:
        logger.warning("Failed to init MPRIS libraries!")
        logger.warning(traceback.format_exc())

qt_library, QtWidgets, QtCore, QtGui, QShortcut, QtOpenGLWidgets = get_qt_library()

if "PyQt6" in sys.modules or "PyQt5" in sys.modules:
    Signal = QtCore.pyqtSignal
else:
    Signal = QtCore.Signal

if qt_library == "PyQt5":
    qt_icon_critical = 3
    qt_icon_warning = 2
    qt_icon_information = 1
else:
    qt_icon_critical = QtWidgets.QMessageBox.Icon.Critical
    qt_icon_warning = QtWidgets.QMessageBox.Icon.Warning
    qt_icon_information = QtWidgets.QMessageBox.Icon.Information

APP_VERSION = "__DEB_VERSION__"
COPYRIGHT_YEAR = "2023"

setproctitle.setproctitle("yuki-iptv")
try:
    setproctitle.setthreadtitle("yuki-iptv")
except Exception:
    pass

# i18n start


class YukiLang:
    cache = {}


old_pwd = os.getcwd()
if platform.system() == "Windows" or platform.system() == "Darwin":
    if not os.path.isdir(Path(os.path.dirname(os.path.abspath(__file__)), "usr")):
        os.mkdir(Path(os.path.dirname(os.path.abspath(__file__)), "usr"))
    if not os.path.isdir(
        Path(os.path.dirname(os.path.abspath(__file__)), "usr", "lib")
    ):
        os.mkdir(Path(os.path.dirname(os.path.abspath(__file__)), "usr", "lib"))
    if not os.path.isdir(
        Path(
            os.path.dirname(os.path.abspath(__file__)),
            "usr",
            "lib",
            "yuki-iptv",
        )
    ):
        os.mkdir(
            Path(
                os.path.dirname(os.path.abspath(__file__)),
                "usr",
                "lib",
                "yuki-iptv",
            )
        )
    if not os.path.isdir(
        Path(
            os.path.dirname(os.path.abspath(__file__)),
            "usr",
            "lib",
            "yuki-iptv",
            "yuki_iptv",
        )
    ):
        os.mkdir(
            Path(
                os.path.dirname(os.path.abspath(__file__)),
                "usr",
                "lib",
                "yuki-iptv",
                "yuki_iptv",
            )
        )

    os.chdir(
        Path(
            os.path.dirname(os.path.abspath(__file__)),
            "usr",
            "lib",
            "yuki-iptv",
        )
    )
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Mac OS locale fix/workaround
if platform.system() == "Darwin" and not locale.getlocale()[0]:
    try:
        mac_lang = (
            subprocess.check_output(["defaults", "read", "-g", "AppleLocale"])
            .decode("utf-8")
            .strip()
        )
        if ".UTF-8" not in mac_lang:
            mac_lang = mac_lang + ".UTF-8"
        if "_" in mac_lang:
            logger.info(f"Fixing Mac OS locale, set to {mac_lang}")
            locale.setlocale(locale.LC_ALL, mac_lang)
        else:
            logger.info("Failed to fix Mac OS locale!")
    except Exception:
        logger.info("Failed to fix Mac OS locale!")

APP = "yuki-iptv"
LOCALE_DIR = str(Path(os.getcwd(), "..", "..", "share", "locale"))
if platform.system() == "Linux":
    locale.bindtextdomain(APP, LOCALE_DIR)
gettext.bindtextdomain(APP, LOCALE_DIR)
gettext.textdomain(APP)


def cached_gettext(gettext_str):
    if gettext_str not in YukiLang.cache:
        YukiLang.cache[gettext_str] = gettext.gettext(gettext_str)
    return YukiLang.cache[gettext_str]


_ = cached_gettext
# i18n end

MAIN_WINDOW_TITLE = "yuki-iptv"
WINDOW_SIZE = (1200, 600)
DOCK_WIDGET2_HEIGHT = int(WINDOW_SIZE[1] / 10)
DOCK_WIDGET2_HEIGHT_OFFSET = 10
DOCK_WIDGET2_HEIGHT_HIGH = DOCK_WIDGET2_HEIGHT + DOCK_WIDGET2_HEIGHT_OFFSET
DOCK_WIDGET2_HEIGHT_LOW = DOCK_WIDGET2_HEIGHT_HIGH - (DOCK_WIDGET2_HEIGHT_OFFSET + 10)
DOCK_WIDGET_WIDTH = int((WINDOW_SIZE[0] / 2) - 200)
TVGUIDE_WIDTH = int((WINDOW_SIZE[0] / 5))
BCOLOR = "#A2A3A3"

UPDATE_BR_INTERVAL = 5

AUDIO_SAMPLE_FORMATS = {
    "u16": "unsigned 16 bits",
    "s16": "signed 16 bits",
    "s16p": "signed 16 bits, planar",
    "flt": "float",
    "float": "float",
    "fltp": "float, planar",
    "floatp": "float, planar",
    "dbl": "double",
    "dblp": "double, planar",
}

MPV_OPTIONS_LINK = "https://mpv.io/manual/master/#options"


class stream_info:
    pass


class YukiData:
    compact_mode = False
    playlist_hidden = False
    controlpanel_hidden = False
    fullscreen_locked = False
    selected_shortcut_row = -1
    shortcuts_state = False
    use_dark_icon_theme = False
    playmodeIndex = 0
    serie_selected = False
    movies = {}
    series = {}
    osc = -1
    volume = 100


stream_info.video_properties = {}
stream_info.audio_properties = {}
stream_info.video_bitrates = []
stream_info.audio_bitrates = []

DOCK_WIDGET2_HEIGHT = max(DOCK_WIDGET2_HEIGHT, 0)
DOCK_WIDGET_WIDTH = max(DOCK_WIDGET_WIDTH, 0)

if args1.version:
    print(f"{MAIN_WINDOW_TITLE} {APP_VERSION}")
    sys.exit(0)

if platform.system() != "Windows":
    if not os.path.isdir(str(Path(os.environ["HOME"], ".config"))):
        os.mkdir(str(Path(os.environ["HOME"], ".config")))

    if not os.path.isdir(str(Path(os.environ["HOME"], ".cache"))):
        os.mkdir(str(Path(os.environ["HOME"], ".cache")))

if not os.path.isdir(LOCAL_DIR):
    os.mkdir(LOCAL_DIR)
if not os.path.isdir(SAVE_FOLDER_DEFAULT):
    os.mkdir(SAVE_FOLDER_DEFAULT)


# Used as a decorator to run things in the main loop, from another thread
def idle_function(func):
    def wrapper(*args):
        exInMainThread_partial(partial(func, *args))

    return wrapper


# Used as a decorator to run things in the background (GUI blocking)
def async_gui_blocking_function(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread

    return wrapper


if __name__ == "__main__":
    logger.info("Qt init...")
    if "APPIMAGE_TEST_EXIT_YUKI_IPTV" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    logger.info("Qt init successful")
    logger.info("")

    setAppFusion = True
    try:
        if os.path.isfile(str(Path(LOCAL_DIR, "settings.json"))):
            with open(
                str(Path(LOCAL_DIR, "settings.json")), "r", encoding="utf8"
            ) as settings_tmp:
                settings_tmp_json = json.loads(settings_tmp.read())
                if "styleredefoff" in settings_tmp_json:
                    setAppFusion = settings_tmp_json["styleredefoff"]
    except Exception:
        logger.warning("failed to read settings.json")

    try:
        if setAppFusion:
            app.setStyle("fusion")
            logger.info('app.setStyle("fusion") OK')
        else:
            logger.info("fusion style turned OFF")
    except Exception:
        logger.warning('app.setStyle("fusion") FAILED')

    # dummy, for xgettext
    PLAYERNAME = _("IPTV player")

    # This is necessary since PyQT stomps over the locale settings needed by libmpv.
    # This needs to happen after importing PyQT before
    # creating the first mpv.MPV instance.
    locale.setlocale(locale.LC_NUMERIC, "C")

    try:
        logger.info("")
        logger.info(f"{MAIN_WINDOW_TITLE} starting...")
        logger.info("Copyright (c) 2021, 2022 Astroncia")
        logger.info("Copyright (c) 2023 Ame-chan-angel")
        logger.info("")
        logger.info(
            "This program is free software: you can redistribute it and/or modify"
        )
        logger.info(
            "it under the terms of the GNU General Public License as published by"
        )
        logger.info("the Free Software Foundation, either version 3 of the License, or")
        logger.info("(at your option) any later version.")
        logger.info("")
        logger.info(
            "The Font Awesome pictograms are licensed under the CC BY 4.0 License."
        )
        logger.info("https://fontawesome.com/")
        logger.info("https://creativecommons.org/licenses/by/4.0/")
        logger.info("")
        logger.info(f"yuki-iptv version: {APP_VERSION}")
        logger.info("Using Python " + sys.version.replace("\n", ""))
        logger.info(f"System: {platform.system()}")
        logger.info(f"Qt library: {qt_library}")
        logger.info(f"Qt version: {QtCore.QT_VERSION_STR}")
        try:
            logger.info(f"Qt platform: {app.platformName()}")
        except Exception:
            logger.info("Failed to determine Qt platform!")
        logger.info("")

        enable_libmpv_render_context = platform.system() == "Darwin"  # Mac OS

        multiprocessing_manager = Manager()
        multiprocessing_manager_dict = multiprocessing_manager.dict()

        m3u = ""

        from thirdparty import mpv

        if "APPIMAGE_TEST_EXIT_YUKI_IPTV" in os.environ:
            logger.info("Checking mpv version...")
            player_test = mpv.MPV()
            logger.info(player_test.mpv_version)
            logger.info("Checking ffmpeg version...")
            logger.info(
                subprocess.check_output(["ffmpeg", "-version"])
                .decode("utf-8")
                .split("\n")[0]
            )
            logger.info("AppImage test completed")
            sys.exit(0)

        if not os.path.isdir(LOCAL_DIR):
            os.mkdir(LOCAL_DIR)

        if not os.path.isfile(str(Path(LOCAL_DIR, "favplaylist.m3u"))):
            file01 = open(str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8")
            file01.write("#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n")
            file01.close()

        channel_sets = {}
        prog_ids = {}
        epg_icons = {}

        def save_channel_sets():
            global channel_sets
            file2 = open(
                str(Path(LOCAL_DIR, "channelsettings.json")), "w", encoding="utf8"
            )
            file2.write(json.dumps(channel_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, "channelsettings.json"))):
            save_channel_sets()
        else:
            file1 = open(
                str(Path(LOCAL_DIR, "channelsettings.json")), "r", encoding="utf8"
            )
            channel_sets = json.loads(file1.read())
            file1.close()

        settings, settings_loaded = parse_settings()
        if not settings_loaded:
            m3u = ""

        favourite_sets = []

        def save_favourite_sets():
            global favourite_sets
            favourite_sets_2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "favouritechannels.json")):
                with open(
                    Path(LOCAL_DIR, "favouritechannels.json"), "r", encoding="utf8"
                ) as fsetfile:
                    favourite_sets_2 = json.loads(fsetfile.read())
            if settings["m3u"]:
                favourite_sets_2[settings["m3u"]] = favourite_sets
            file2 = open(
                Path(LOCAL_DIR, "favouritechannels.json"), "w", encoding="utf8"
            )
            file2.write(json.dumps(favourite_sets_2))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, "favouritechannels.json"))):
            save_favourite_sets()
        else:
            file1 = open(
                Path(LOCAL_DIR, "favouritechannels.json"), "r", encoding="utf8"
            )
            favourite_sets1 = json.loads(file1.read())
            if settings["m3u"] in favourite_sets1:
                favourite_sets = favourite_sets1[settings["m3u"]]
            file1.close()

        player_tracks = {}

        def save_player_tracks():
            global player_tracks
            player_tracks_2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "tracks.json")):
                with open(
                    Path(LOCAL_DIR, "tracks.json"), "r", encoding="utf8"
                ) as tracks_file0:
                    player_tracks_2 = json.loads(tracks_file0.read())
            if settings["m3u"]:
                player_tracks_2[settings["m3u"]] = player_tracks
            tracks_file1 = open(Path(LOCAL_DIR, "tracks.json"), "w", encoding="utf8")
            tracks_file1.write(json.dumps(player_tracks_2))
            tracks_file1.close()

        if os.path.isfile(str(Path(LOCAL_DIR, "tracks.json"))):
            tracks_file = open(Path(LOCAL_DIR, "tracks.json"), "r", encoding="utf8")
            player_tracks1 = json.loads(tracks_file.read())
            if settings["m3u"] in player_tracks1:
                player_tracks = player_tracks1[settings["m3u"]]
            tracks_file.close()

        if settings["hwaccel"]:
            logger.info("Hardware acceleration enabled")
        else:
            logger.info("Hardware acceleration disabled")

        dark_label = QtWidgets.QLabel("Darkness test")
        is_dark_theme = (
            dark_label.palette().color(QtGui.QPalette.ColorRole.WindowText).value()
            > dark_label.palette().color(QtGui.QPalette.ColorRole.Window).value()
        )
        if is_dark_theme:
            logger.info("Detected dark window theme, applying icons compat")
            YukiData.use_dark_icon_theme = True
        else:
            YukiData.use_dark_icon_theme = False

        if settings["catchupenable"]:
            logger.info("Catchup enabled")
        else:
            logger.info("Catchup disabled")

        # URL override for command line
        if args1.URL:
            settings["m3u"] = args1.URL
            if args1.URL == "http://____PLUGIN_M3U____":
                settings["epg"] = "http://____PLUGIN_EPG____"
            else:
                settings["epg"] = ""

        tvguide_sets = {}

        epg_thread_2 = None

        @idle_function
        def start_epg_hdd_animation(unused=None):
            try:
                hdd_gif_label.setVisible(True)
            except Exception:
                pass

        @idle_function
        def stop_epg_hdd_animation(unused=None):
            try:
                hdd_gif_label.setVisible(False)
            except Exception:
                pass

        @async_gui_blocking_function
        def save_tvguide_sets():
            global epg_thread_2, tvguide_sets
            try:
                start_epg_hdd_animation()
            except Exception:
                pass
            logger.info("Writing EPG cache...")
            epg_thread_2 = get_context("spawn").Process(
                name="[yuki-iptv] save_epg_cache",
                target=save_epg_cache,
                daemon=True,
                args=(
                    tvguide_sets,
                    settings,
                    prog_ids,
                    epg_icons,
                ),
            )
            epg_thread_2.start()
            epg_thread_2.join()
            logger.info("Writing EPG cache done")
            try:
                stop_epg_hdd_animation()
            except Exception:
                pass

        first_boot = False
        epg_updating = False

        def force_update_epg():
            global use_local_tvguide, first_boot
            if os.path.exists(str(Path(LOCAL_DIR, "epg.cache"))):
                os.remove(str(Path(LOCAL_DIR, "epg.cache")))
            use_local_tvguide = False
            if not epg_updating:
                first_boot = False

        epg_update_allowed = True

        if settings["donotupdateepg"]:
            epg_update_allowed = False

        def force_update_epg_act():
            global epg_failed, epg_update_allowed
            logger.info("Force update EPG triggered")
            epg_update_allowed = True
            if epg_failed:
                epg_failed = False
            force_update_epg()

        use_local_tvguide = True
        epg_ready = False

        def mainwindow_isvisible():
            try:
                return win.isVisible()
            except Exception:
                return False

        @idle_function
        def update_epg_func_static_enable(unused=None):
            global static_text, time_stop
            l1.setStatic2(True)
            l1.show()
            static_text = _("Loading TV guide cache...")
            l1.setText2("")
            time_stop = time.time() + 3

        @idle_function
        def update_epg_func_static_disable(unused=None):
            global time_stop
            l1.setStatic2(False)
            l1.hide()
            l1.setText2("")
            time_stop = time.time()

        @async_gui_blocking_function
        def update_epg_func():
            global settings, tvguide_sets, prog_ids, epg_icons, programmes, epg_ready
            if settings["nocacheepg"]:
                logger.info("No cache EPG active, deleting old EPG cache file")
                try:
                    if os.path.isfile(str(Path(LOCAL_DIR, "epg.cache"))):
                        os.remove(str(Path(LOCAL_DIR, "epg.cache")))
                except Exception:
                    pass
            tvguide_read_time = time.time()
            if os.path.isfile(str(Path(LOCAL_DIR, "epg.cache"))):
                logger.info("Reading cached TV guide...")

                update_epg_func_static_enable()

                # Loading epg.cache
                tvguide_json = (
                    get_context("spawn")
                    .Pool(1)
                    .apply(
                        load_epg_cache,
                        (
                            settings["m3u"],
                            settings["epg"],
                            epg_ready,
                        ),
                    )
                )
                is_program_actual1 = False
                if tvguide_json:
                    if "tvguide_sets" in tvguide_json:
                        tvguide_sets = tvguide_json["tvguide_sets"]
                    if "prog_ids" in tvguide_json:
                        prog_ids = tvguide_json["prog_ids"]
                    if "epg_icons" in tvguide_json:
                        epg_icons = tvguide_json["epg_icons"]
                    if "is_program_actual" in tvguide_json:
                        is_program_actual1 = tvguide_json["is_program_actual"]
                    if "programmes_1" in tvguide_json:
                        programmes = tvguide_json["programmes_1"]
                    tvguide_json = None
                if not is_program_actual1:
                    logger.info("EPG cache expired, updating...")
                    epg_ready = True
                    force_update_epg()
                epg_ready = True

                update_epg_func_static_disable()

                logger.info(
                    "TV guide read done, took "
                    f"{round(time.time() - tvguide_read_time, 2)} seconds"
                )
                btn_update.click()
            else:
                logger.info("No EPG cache found")
                epg_ready = True
                force_update_epg()

        if YukiData.use_dark_icon_theme:
            ICONS_FOLDER = str(
                Path("..", "..", "..", "share", "yuki-iptv", "icons_dark")
            )
        else:
            ICONS_FOLDER = str(Path("..", "..", "..", "share", "yuki-iptv", "icons"))

        main_icon = QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "tv-blue.png")))
        channels = {}
        programmes = {}

        logger.info("Init m3u editor")
        m3u_editor = M3UEditor(
            _=_, icon=main_icon, icons_folder=ICONS_FOLDER, settings=settings
        )
        logger.info("M3u editor init done")

        def show_m3u_editor():
            if m3u_editor.isVisible():
                m3u_editor.hide()
            else:
                moveWindowToCenter(m3u_editor)
                m3u_editor.show()
                moveWindowToCenter(m3u_editor)

        save_folder = settings["save_folder"]

        if not os.path.isdir(str(Path(save_folder))):
            try:
                os.mkdir(str(Path(save_folder)))
            except Exception:
                logger.warning("Failed to create save folder!")
                save_folder = SAVE_FOLDER_DEFAULT
                if not os.path.isdir(str(Path(save_folder))):
                    os.mkdir(str(Path(save_folder)))

        if not settings["scrrecnosubfolders"]:
            if not os.path.isdir(str(Path(save_folder, "screenshots"))):
                os.mkdir(str(Path(save_folder, "screenshots")))
            if not os.path.isdir(str(Path(save_folder, "recordings"))):
                os.mkdir(str(Path(save_folder, "recordings")))
        else:
            if os.path.isdir(str(Path(save_folder, "screenshots"))):
                try:
                    os.rmdir(str(Path(save_folder, "screenshots")))
                except Exception:
                    pass
            if os.path.isdir(str(Path(save_folder, "recordings"))):
                try:
                    os.rmdir(str(Path(save_folder, "recordings")))
                except Exception:
                    pass

        def getArrayItem(arr_item):
            arr_item_ret = None
            if arr_item in array:
                arr_item_ret = array[arr_item]
            elif arr_item in YukiData.movies:
                arr_item_ret = YukiData.movies[arr_item]
            else:
                try:
                    if " ::: " in arr_item:
                        arr_item_split = arr_item.split(" ::: ")
                        for season_name in YukiData.series[
                            arr_item_split[2]
                        ].seasons.keys():
                            season = YukiData.series[arr_item_split[2]].seasons[
                                season_name
                            ]
                            if season.name == arr_item_split[1]:
                                for episode_name in season.episodes.keys():
                                    episode = season.episodes[episode_name]
                                    if episode.title == arr_item_split[0]:
                                        arr_item_ret = {
                                            "title": episode.title,
                                            "tvg-name": "",
                                            "tvg-ID": "",
                                            "tvg-logo": "",
                                            "tvg-group": _("All channels"),
                                            "tvg-url": "",
                                            "catchup": "default",
                                            "catchup-source": "",
                                            "catchup-days": "7",
                                            "useragent": "",
                                            "referer": "",
                                            "url": episode.url,
                                        }
                                        break
                                break
                except Exception:
                    logger.warning("Exception in getArrayItem (series)")
                    logger.warning(traceback.format_exc())
            return arr_item_ret

        array = {}
        groups = []

        class EmptyClass:
            pass

        class PlaylistsFail:
            status_code = 0

        m3uFailed = False

        use_cache = settings["m3u"].startswith("http://") or settings["m3u"].startswith(
            "https://"
        )
        if settings["nocache"]:
            use_cache = False
        if not use_cache:
            logger.info("Playlist caching off")
        if use_cache and os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
            pj = open(str(Path(LOCAL_DIR, "playlistcache.json")), "r", encoding="utf8")
            pj1 = json.loads(pj.read())["url"]
            pj.close()
            if pj1 != settings["m3u"]:
                os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
        if (not use_cache) and os.path.isfile(
            str(Path(LOCAL_DIR, "playlistcache.json"))
        ):
            os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
        if os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
            try:
                playlist_load_tmp = open(
                    str(Path(LOCAL_DIR, "playlistcache.json")), "r", encoding="utf8"
                )
                playlist_load_tmp_data = playlist_load_tmp.read()
                playlist_load_tmp.close()
                playlist_load_tmp_data = json.loads(playlist_load_tmp_data)
                if (
                    not playlist_load_tmp_data["m3u"]
                    and not playlist_load_tmp_data["array"]
                ):
                    logger.warning("Cached playlist broken, ignoring and deleting")
                    os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
            except Exception:
                pass
        if not os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
            logger.info("Loading playlist...")
            if settings["m3u"]:
                # Parsing m3u
                if settings["m3u"].startswith("XTREAM::::::::::::::"):
                    # XTREAM::::::::::::::username::::::::::::::password::::::::::::::url
                    logger.info("Using XTream API")
                    xtream_sha512 = hashlib.sha512(
                        settings["m3u"].encode("utf-8")
                    ).hexdigest()
                    xtream_split = settings["m3u"].split("::::::::::::::")
                    xtream_username = xtream_split[1]
                    xtream_password = xtream_split[2]
                    xtream_url = xtream_split[3]
                    if not os.path.isdir(str(Path(LOCAL_DIR, "xtream"))):
                        os.mkdir(str(Path(LOCAL_DIR, "xtream")))
                    try:
                        xt = XTream(
                            xtream_sha512,
                            xtream_username,
                            xtream_password,
                            xtream_url,
                            "",
                        )
                    except Exception:
                        logger.warning("XTream init failure")
                        xt = EmptyClass()
                        xt.auth_data = {}
                    if xt.auth_data != {}:
                        xt.load_iptv()
                        try:
                            m3u = convert_xtream_to_m3u(_, xt.channels)
                            try:
                                m3u += convert_xtream_to_m3u(_, xt.movies, True, "VOD")
                            except Exception:
                                logger.warning("XTream movies parse FAILED")
                            for movie1 in xt.series:
                                if isinstance(movie1, Serie):
                                    YukiData.series[movie1.name] = movie1
                        except Exception as e3:
                            message2 = "{}\n\n{}".format(
                                _("yuki-iptv error"),
                                str(
                                    "XTream API: {}\n\n{}".format(
                                        _("Processing error"), str(e3)
                                    )
                                ),
                            )
                            msg2 = QtWidgets.QMessageBox(
                                qt_icon_warning,
                                _("Error"),
                                message2,
                                QtWidgets.QMessageBox.StandardButton.Ok,
                            )
                            msg2.exec()
                    else:
                        message1 = "{}\n\n{}".format(
                            _("yuki-iptv error"),
                            str("XTream API: {}".format(_("Could not connect"))),
                        )
                        msg1 = QtWidgets.QMessageBox(
                            qt_icon_warning,
                            _("Error"),
                            message1,
                            QtWidgets.QMessageBox.StandardButton.Ok,
                        )
                        msg1.exec()
                else:
                    if os.path.isfile(settings["m3u"]):
                        try:
                            file = open(settings["m3u"], "r", encoding="utf8")
                            m3u = file.read()
                            file.close()
                        except Exception:
                            logger.warning("Playlist is not UTF-8 encoding")
                            logger.info("Trying to detect encoding...")
                            file_222_encoding = ""
                            try:
                                file_222 = open(settings["m3u"], "rb")
                                file_222_encoding = chardet.detect(file_222.read())[
                                    "encoding"
                                ]
                                file_222.close()
                            except Exception:
                                pass
                            if file_222_encoding:
                                logger.info(f"Guessed encoding: {file_222_encoding}")
                                try:
                                    file_111 = open(
                                        settings["m3u"], "r", encoding=file_222_encoding
                                    )
                                    m3u = file_111.read()
                                    file_111.close()
                                except Exception:
                                    logger.warning("Wrong encoding guess!")
                                    show_exception(
                                        _(
                                            "Failed to load playlist - unknown "
                                            "encoding! Please use playlists "
                                            "in UTF-8 encoding."
                                        )
                                    )
                            else:
                                logger.warning("Unknown encoding!")
                                show_exception(
                                    _(
                                        "Failed to load playlist - unknown "
                                        "encoding! Please use playlists "
                                        "in UTF-8 encoding."
                                    )
                                )
                    else:
                        try:
                            try:
                                m3u_req = requests.get(
                                    settings["m3u"],
                                    headers={"User-Agent": settings["ua"]},
                                    timeout=(5, 15),  # connect, read timeout
                                )
                            except Exception:
                                m3u_req = PlaylistsFail()
                                m3u_req.status_code = 400

                            if m3u_req.status_code != 200:
                                logger.warning(
                                    "Playlist load failed, trying empty user agent"
                                )
                                m3u_req = requests.get(
                                    settings["m3u"],
                                    headers={"User-Agent": ""},
                                    timeout=(5, 15),  # connect, read timeout
                                )

                            logger.info(f"Status code: {m3u_req.status_code}")
                            logger.info(f"{len(m3u_req.content)} bytes")
                            m3u = m3u_req.content
                            try:
                                m3u = m3u.decode("utf-8")
                            except Exception:
                                logger.warning("Playlist is not UTF-8 encoding")
                                logger.info("Trying to detect encoding...")
                                guess_encoding = ""
                                try:
                                    guess_encoding = chardet.detect(m3u)["encoding"]
                                except Exception:
                                    pass
                                if guess_encoding:
                                    logger.info(f"Guessed encoding: {guess_encoding}")
                                    try:
                                        m3u = m3u.decode(guess_encoding)
                                    except Exception:
                                        logger.warning("Wrong encoding guess!")
                                        show_exception(
                                            _(
                                                "Failed to load playlist - unknown "
                                                "encoding! Please use playlists "
                                                "in UTF-8 encoding."
                                            )
                                        )
                                else:
                                    logger.warning("Unknown encoding!")
                                    show_exception(
                                        _(
                                            "Failed to load playlist - unknown "
                                            "encoding! Please use playlists "
                                            "in UTF-8 encoding."
                                        )
                                    )
                        except Exception:
                            m3u = ""
                            exp3 = traceback.format_exc()
                            logger.warning("Playlist URL loading error!" + "\n" + exp3)
                            show_exception(_("Playlist loading error!"))

            m3u_parser = M3UParser(settings["udp_proxy"], _)
            epg_url = ""
            m3uFailed = False
            if m3u:
                try:
                    is_xspf = '<?xml version="' in m3u and (
                        "http://xspf.org/" in m3u or "https://xspf.org/" in m3u
                    )
                    if not is_xspf:
                        m3u_data0 = m3u_parser.parse_m3u(m3u)
                    else:
                        m3u_data0 = parse_xspf(m3u)
                    m3u_data_got = m3u_data0[0]
                    m3u_data = []

                    for m3u_datai in m3u_data_got:
                        if "tvg-group" in m3u_datai:
                            if m3u_datai["tvg-group"].lower() == "vod" or m3u_datai[
                                "tvg-group"
                            ].lower().startswith("vod "):
                                YukiData.movies[m3u_datai["title"]] = m3u_datai
                            else:
                                YukiData.series, is_matched = parse_series(
                                    m3u_datai, YukiData.series
                                )
                                if not is_matched:
                                    m3u_data.append(m3u_datai)

                    epg_url = m3u_data0[1]
                    if epg_url and not settings["epg"]:
                        settings["epg"] = epg_url
                    for m3u_line in m3u_data:
                        array[m3u_line["title"]] = m3u_line
                        if not m3u_line["tvg-group"] in groups:
                            groups.append(m3u_line["tvg-group"])
                except Exception:
                    logger.warning(
                        "Playlist parsing error!" + "\n" + traceback.format_exc()
                    )
                    show_exception(_("Playlist loading error!"))
                    m3u = ""
                    array = {}
                    groups = []
                    m3uFailed = True

            logger.info(
                "{} channels, {} groups, {} movies, {} series".format(
                    len(array),
                    len([group2 for group2 in groups if group2 != _("All channels")]),
                    len(YukiData.movies),
                    len(YukiData.series),
                )
            )

            logger.info("Playling loading done!")
            if use_cache:
                logger.info("Caching playlist...")
                cm3u = json.dumps(
                    {
                        "url": settings["m3u"],
                        "array": array,
                        "groups": groups,
                        "m3u": m3u,
                        "epgurl": epg_url,
                        "movies": YukiData.movies,
                    }
                )
                cm3uf = open(
                    str(Path(LOCAL_DIR, "playlistcache.json")), "w", encoding="utf8"
                )
                cm3uf.write(cm3u)
                cm3uf.close()
                logger.info("Playlist cache saved!")
        else:
            logger.info("Using cached playlist")
            cm3uf = open(
                str(Path(LOCAL_DIR, "playlistcache.json")), "r", encoding="utf8"
            )
            cm3u = json.loads(cm3uf.read())
            cm3uf.close()
            array = cm3u["array"]
            groups = cm3u["groups"]
            m3u = cm3u["m3u"]
            try:
                epg_url = cm3u["epgurl"]
                if epg_url and not settings["epg"]:
                    settings["epg"] = epg_url
            except Exception:
                pass
            try:
                if "movies" in cm3u:
                    YukiData.movies = cm3u["movies"]
            except Exception:
                pass

        for ch3 in array.copy():
            if settings["m3u"] in channel_sets:
                if ch3 in channel_sets[settings["m3u"]]:
                    if "group" in channel_sets[settings["m3u"]][ch3]:
                        if channel_sets[settings["m3u"]][ch3]["group"]:
                            array[ch3]["tvg-group"] = channel_sets[settings["m3u"]][
                                ch3
                            ]["group"]
                            if (
                                channel_sets[settings["m3u"]][ch3]["group"]
                                not in groups
                            ):
                                groups.append(
                                    channel_sets[settings["m3u"]][ch3]["group"]
                                )
                    if "hidden" in channel_sets[settings["m3u"]][ch3]:
                        if channel_sets[settings["m3u"]][ch3]["hidden"]:
                            array.pop(ch3)

        if _("All channels") in groups:
            groups.remove(_("All channels"))
        groups = [_("All channels"), _("Favourites")] + groups

        if m3uFailed and os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
            os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))

        try:
            if os.path.isfile(str(Path(LOCAL_DIR, "settings.json"))):
                settings_file2 = open(
                    str(Path(LOCAL_DIR, "settings.json")), "r", encoding="utf8"
                )
                settings_file2_json = json.loads(settings_file2.read())
                settings_file2.close()
                if settings["epg"] and not settings_file2_json["epg"]:
                    settings_file2_json["epg"] = settings["epg"]
                    settings_file4 = open(
                        str(Path(LOCAL_DIR, "settings.json")), "w", encoding="utf8"
                    )
                    settings_file4.write(json.dumps(settings_file2_json))
                    settings_file4.close()
        except Exception:
            pass

        def sigint_handler(*args):
            """Handler for the SIGINT signal."""
            global mpris_loop
            if mpris_loop:
                mpris_loop.quit()
            app.quit()

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        TV_ICON = QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "tv.png")))
        MOVIE_ICON = QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "movie.png")))

        def get_current_time():
            return time.strftime("%d.%m.%y %H:%M", time.localtime())

        def empty_function(arg1):
            pass

        class ScrollableLabel(QtWidgets.QScrollArea):
            def __init__(self, *args, **kwargs):
                QtWidgets.QScrollArea.__init__(self, *args, **kwargs)
                self.setWidgetResizable(True)
                label_qwidget = QtWidgets.QWidget(self)
                bcolor_scrollabel = "white"
                if YukiData.use_dark_icon_theme:
                    bcolor_scrollabel = "black"
                label_qwidget.setStyleSheet("background-color: " + bcolor_scrollabel)
                self.setWidget(label_qwidget)
                label_layout = QtWidgets.QVBoxLayout(label_qwidget)
                self.label = QtWidgets.QLabel(label_qwidget)
                self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                self.label.setWordWrap(True)
                self.label.setStyleSheet("background-color: " + bcolor_scrollabel)
                label_layout.addWidget(self.label)

            def setText(self, text):
                self.label.setText(text)

        class SettingsScrollableWindow(QtWidgets.QMainWindow):
            def __init__(self):
                super().__init__()
                self.scroll = QtWidgets.QScrollArea()
                self.scroll.setVerticalScrollBarPolicy(
                    QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
                )
                self.scroll.setHorizontalScrollBarPolicy(
                    QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOn
                )
                self.scroll.setWidgetResizable(True)
                self.setCentralWidget(self.scroll)

        settings_win = SettingsScrollableWindow()
        settings_win.resize(800, 600)
        settings_win.setWindowTitle(_("Settings"))
        settings_win.setWindowIcon(main_icon)

        shortcuts_win = QtWidgets.QMainWindow()
        shortcuts_win.resize(720, 500)
        shortcuts_win.setWindowTitle(_("Shortcuts"))
        shortcuts_win.setWindowIcon(main_icon)

        shortcuts_central_widget = QtWidgets.QWidget(shortcuts_win)
        shortcuts_win.setCentralWidget(shortcuts_central_widget)

        shortcuts_grid_layout = QtWidgets.QVBoxLayout()
        shortcuts_central_widget.setLayout(shortcuts_grid_layout)

        shortcuts_table = QtWidgets.QTableWidget(shortcuts_win)
        # shortcuts_table.setColumnCount(3)
        shortcuts_table.setColumnCount(2)

        # shortcuts_table.setHorizontalHeaderLabels(
        #     [_('Description'), _('Shortcut'), "Header 3"]
        # )
        shortcuts_table.setHorizontalHeaderLabels([_("Description"), _("Shortcut")])

        shortcuts_table.horizontalHeaderItem(0).setTextAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        shortcuts_table.horizontalHeaderItem(1).setTextAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter
        )
        # shortcuts_table.horizontalHeaderItem(2).setTextAlignment(
        #     QtCore.Qt.AlignmentFlag.AlignHCenter
        # )

        def resettodefaults_btn_clicked():
            global main_keybinds
            resettodefaults_btn_clicked_msg = QtWidgets.QMessageBox.question(
                None,
                MAIN_WINDOW_TITLE,
                _("Are you sure?"),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if (
                resettodefaults_btn_clicked_msg
                == QtWidgets.QMessageBox.StandardButton.Yes
            ):
                logger.info("Restoring default keybinds")
                main_keybinds = main_keybinds_default.copy()
                shortcuts_table.setRowCount(len(main_keybinds))
                keybind_i = -1
                for keybind in main_keybinds:
                    keybind_i += 1
                    shortcuts_table.setItem(
                        keybind_i,
                        0,
                        get_widget_item(main_keybinds_translations[keybind]),
                    )
                    if isinstance(main_keybinds[keybind], str):
                        keybind_str = main_keybinds[keybind]
                    else:
                        keybind_str = QtGui.QKeySequence(
                            main_keybinds[keybind]
                        ).toString()
                    kbd_widget = get_widget_item(keybind_str)
                    kbd_widget.setToolTip(_("Double click to change"))
                    shortcuts_table.setItem(keybind_i, 1, kbd_widget)
                shortcuts_table.resizeColumnsToContents()
                hotkeys_file_1 = open(
                    str(Path(LOCAL_DIR, "hotkeys.json")), "w", encoding="utf8"
                )
                hotkeys_file_1.write(
                    json.dumps({"current_profile": {"keys": main_keybinds}})
                )
                hotkeys_file_1.close()
                reload_keybinds()

        resettodefaults_btn = QtWidgets.QPushButton()
        resettodefaults_btn.setText(_("Reset to defaults"))
        resettodefaults_btn.clicked.connect(resettodefaults_btn_clicked)

        shortcuts_grid_layout.addWidget(shortcuts_table)
        shortcuts_grid_layout.addWidget(resettodefaults_btn)

        shortcuts_win_2 = QtWidgets.QMainWindow()
        shortcuts_win_2.resize(300, 100)
        shortcuts_win_2.setWindowTitle(_("Modify shortcut"))
        shortcuts_win_2.setWindowIcon(main_icon)

        class KeySequenceEdit(QtWidgets.QKeySequenceEdit):
            def keyPressEvent(self, event):
                super().keyPressEvent(event)
                self.setKeySequence(QtGui.QKeySequence(self.keySequence()))

        keyseq = KeySequenceEdit()

        bold_fnt_1 = QtGui.QFont()
        bold_fnt_1.setBold(True)

        la_sl = QtWidgets.QLabel()
        la_sl.setFont(bold_fnt_1)
        la_sl.setText(_("Press the key combination\nyou want to assign"))

        def keyseq_ok_clicked():
            if YukiData.selected_shortcut_row != -1:
                sel_keyseq = keyseq.keySequence().toString()
                search_value = shortcuts_table.item(
                    YukiData.selected_shortcut_row, 0
                ).text()
                shortcut_taken = False
                for sci1 in range(shortcuts_table.rowCount()):
                    if sci1 != YukiData.selected_shortcut_row:
                        if shortcuts_table.item(sci1, 1).text() == sel_keyseq:
                            shortcut_taken = True
                forbidden_hotkeys = [
                    "Return",
                    "Key.Key_MediaNext",
                    "Key.Key_MediaPause",
                    "Key.Key_MediaPlay",
                    "Key.Key_MediaPrevious",
                    "Key.Key_MediaRecord",
                    "Key.Key_MediaStop",
                    "Key.Key_MediaTogglePlayPause",
                    "Key.Key_Play",
                    "Key.Key_Stop",
                    "Key.Key_VolumeDown",
                    "Key.Key_VolumeMute",
                    "Key.Key_VolumeUp",
                ]
                if sel_keyseq in forbidden_hotkeys:
                    shortcut_taken = True
                if not shortcut_taken:
                    shortcuts_table.item(YukiData.selected_shortcut_row, 1).setText(
                        sel_keyseq
                    )
                    for name55, value55 in main_keybinds_translations.items():
                        if value55 == search_value:
                            main_keybinds[name55] = sel_keyseq
                            hotkeys_file = open(
                                str(Path(LOCAL_DIR, "hotkeys.json")),
                                "w",
                                encoding="utf8",
                            )
                            hotkeys_file.write(
                                json.dumps({"current_profile": {"keys": main_keybinds}})
                            )
                            hotkeys_file.close()
                            reload_keybinds()
                    shortcuts_win_2.hide()
                else:
                    msg_shortcut_taken = QtWidgets.QMessageBox(
                        qt_icon_warning,
                        MAIN_WINDOW_TITLE,
                        _("Shortcut already used"),
                        QtWidgets.QMessageBox.StandardButton.Ok,
                    )
                    msg_shortcut_taken.exec()

        keyseq_cancel = QtWidgets.QPushButton(_("Cancel"))
        keyseq_cancel.clicked.connect(shortcuts_win_2.hide)
        keyseq_ok = QtWidgets.QPushButton(_("OK"))
        keyseq_ok.clicked.connect(keyseq_ok_clicked)

        shortcuts_win_2_widget_2 = QtWidgets.QWidget()
        shortcuts_win_2_layout_2 = QtWidgets.QHBoxLayout()
        shortcuts_win_2_layout_2.addWidget(keyseq_cancel)
        shortcuts_win_2_layout_2.addWidget(keyseq_ok)
        shortcuts_win_2_widget_2.setLayout(shortcuts_win_2_layout_2)

        shortcuts_win_2_widget = QtWidgets.QWidget()
        shortcuts_win_2_layout = QtWidgets.QVBoxLayout()
        shortcuts_win_2_layout.addWidget(la_sl)
        shortcuts_win_2_layout.addWidget(keyseq)
        shortcuts_win_2_layout.addWidget(shortcuts_win_2_widget_2)
        shortcuts_win_2_widget.setLayout(shortcuts_win_2_layout)

        shortcuts_win_2.setCentralWidget(shortcuts_win_2_widget)

        streaminfo_win = QtWidgets.QMainWindow()
        streaminfo_win.setWindowIcon(main_icon)

        help_win = QtWidgets.QMainWindow()
        help_win.resize(500, 600)
        help_win.setWindowTitle(_("&About yuki-iptv").replace("&", ""))
        help_win.setWindowIcon(main_icon)

        license_win = QtWidgets.QMainWindow()
        license_win.resize(600, 600)
        license_win.setWindowTitle(_("License"))
        license_win.setWindowIcon(main_icon)

        sort_win = QtWidgets.QMainWindow()
        sort_win.resize(400, 500)
        sort_win.setWindowTitle(_("Channel\nsort").replace("\n", " "))
        sort_win.setWindowIcon(main_icon)

        chan_win = QtWidgets.QMainWindow()
        chan_win.resize(400, 250)
        chan_win.setWindowTitle(_("Video settings"))
        chan_win.setWindowIcon(main_icon)

        ext_win = QtWidgets.QMainWindow()
        ext_win.resize(300, 60)
        ext_win.setWindowTitle(_("Open in external player"))
        ext_win.setWindowIcon(main_icon)

        epg_win = QtWidgets.QMainWindow()
        epg_win.resize(1000, 600)
        epg_win.setWindowTitle(_("TV guide"))
        epg_win.setWindowIcon(main_icon)

        def epg_win_checkbox_changed():
            tvguide_lbl_2.verticalScrollBar().setSliderPosition(
                tvguide_lbl_2.verticalScrollBar().minimum()
            )
            tvguide_lbl_2.setText(_("No TV guide for channel"))
            try:
                ch_3 = epg_win_checkbox.currentText()
                ch_3_guide = update_tvguide(
                    ch_3, True, date_selected=epg_selected_date
                ).replace("!@#$%^^&*(", "\n")
                ch_3_guide = ch_3_guide.replace("\n", "<br>").replace("<br>", "", 1)
                if ch_3_guide.strip():
                    tvguide_lbl_2.setText(ch_3_guide)
                else:
                    tvguide_lbl_2.setText(_("No TV guide for channel"))
            except Exception:
                logger.warning("Exception in epg_win_checkbox_changed")

        def showonlychplaylist_chk_clk():
            update_tvguide_2()

        def tvguide_channelfilter_do():
            try:
                filter_txt3 = tvguidechannelfilter.text()
            except Exception:
                filter_txt3 = ""
            for item6 in range(epg_win_checkbox.count()):
                if (
                    unidecode(filter_txt3).lower().strip()
                    in unidecode(epg_win_checkbox.itemText(item6)).lower().strip()
                ):
                    epg_win_checkbox.view().setRowHidden(item6, False)
                else:
                    epg_win_checkbox.view().setRowHidden(item6, True)

        tvguidechannelfilter = QtWidgets.QLineEdit()
        tvguidechannelfilter.setPlaceholderText(_("Search channel"))
        tvguidechannelfiltersearch = QtWidgets.QPushButton()
        tvguidechannelfiltersearch.setText(_("Search"))
        tvguidechannelfiltersearch.clicked.connect(tvguide_channelfilter_do)
        tvguidechannelfilter.returnPressed.connect(tvguide_channelfilter_do)

        tvguidechannelwidget = QtWidgets.QWidget()
        tvguidechannellayout = QtWidgets.QHBoxLayout()
        tvguidechannellayout.addWidget(tvguidechannelfilter)
        tvguidechannellayout.addWidget(tvguidechannelfiltersearch)
        tvguidechannelwidget.setLayout(tvguidechannellayout)

        showonlychplaylist_lbl = QtWidgets.QLabel()
        showonlychplaylist_lbl.setText(
            "{}:".format(_("Show only channels in playlist"))
        )
        showonlychplaylist_chk = QtWidgets.QCheckBox()
        showonlychplaylist_chk.setChecked(True)
        showonlychplaylist_chk.clicked.connect(showonlychplaylist_chk_clk)
        epg_win_checkbox = QtWidgets.QComboBox()
        epg_win_checkbox.currentIndexChanged.connect(epg_win_checkbox_changed)

        epg_win_count = QtWidgets.QLabel()
        epg_win_count.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        epg_select_date = QtWidgets.QCalendarWidget()
        epg_select_date.setDateRange(
            QtCore.QDate().currentDate().addDays(-31),
            QtCore.QDate().currentDate().addDays(31),
        )
        epg_select_date.setMaximumWidth(300)

        epg_selected_date = datetime.datetime.fromordinal(
            datetime.date.today().toordinal()
        ).timestamp()

        def getPyDate(epg_date_1):
            if qt_library == "PySide6":
                date_ret = epg_date_1.toPython()
            else:
                date_ret = epg_date_1.toPyDate()
            return date_ret

        def epg_date_changed(epg_date):
            global epg_selected_date
            if "__plugin_trigger" in globals():
                globals()["__plugin_trigger"](
                    datetime.datetime.fromordinal(
                        getPyDate(epg_date).toordinal()
                    ).strftime("%Y-%m-%d"),
                    getArrayItem(epg_win_checkbox.currentText()),
                )
            epg_selected_date = datetime.datetime.fromordinal(
                getPyDate(epg_date).toordinal()
            ).timestamp()
            epg_win_checkbox_changed()

        epg_select_date.activated.connect(epg_date_changed)
        epg_select_date.clicked.connect(epg_date_changed)

        epg_win_1_widget = QtWidgets.QWidget()
        epg_win_1_layout = QtWidgets.QHBoxLayout()
        epg_win_1_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        epg_win_1_layout.addWidget(showonlychplaylist_lbl)
        epg_win_1_layout.addWidget(showonlychplaylist_chk)
        epg_win_1_widget.setLayout(epg_win_1_layout)

        def do_open_archive(link):
            if "#__archive__" in link:
                archive_json = json.loads(
                    urllib.parse.unquote_plus(link.split("#__archive__")[1])
                )
                arr1 = getArrayItem(archive_json[0])
                arr1 = format_catchup_array(arr1)

                chan_url = getArrayItem(archive_json[0])["url"]
                start_time = archive_json[1]
                end_time = archive_json[2]
                prog_index = archive_json[3]

                catchup_id = ""
                try:
                    match1 = archive_json[0].lower()
                    try:
                        match1 = prog_match_arr[match1]
                    except Exception:
                        pass
                    if exists_in_epg(match1, programmes):
                        if get_epg(programmes, match1):
                            if (
                                "catchup-id"
                                in get_epg(programmes, match1)[int(prog_index)]
                            ):
                                catchup_id = get_epg(programmes, match1)[
                                    int(prog_index)
                                ]["catchup-id"]
                except Exception:
                    logger.warning("do_open_archive / catchup_id parsing failed")
                    logger.warning(traceback.format_exc())

                play_url = get_catchup_url(
                    chan_url, arr1, start_time, end_time, catchup_id
                )

                itemClicked_event(archive_json[0], play_url, True)
                setChanText("({}) {}".format(_("Archive"), archive_json[0]), True)
                progress.hide()
                start_label.setText("")
                start_label.hide()
                stop_label.setText("")
                stop_label.hide()
                epg_win.hide()

                return False

        tvguide_lbl_2 = ScrollableLabel()
        tvguide_lbl_2.label.linkActivated.connect(do_open_archive)

        epg_win_widget2 = QtWidgets.QWidget()
        epg_win_layout2 = QtWidgets.QHBoxLayout()
        epg_win_layout2.addWidget(epg_select_date)
        epg_win_layout2.addWidget(tvguide_lbl_2)
        epg_win_widget2.setLayout(epg_win_layout2)

        epg_win_widget = QtWidgets.QWidget()
        epg_win_layout = QtWidgets.QVBoxLayout()
        epg_win_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        epg_win_layout.addWidget(epg_win_1_widget)
        epg_win_layout.addWidget(tvguidechannelwidget)
        epg_win_layout.addWidget(epg_win_checkbox)
        epg_win_layout.addWidget(epg_win_count)
        epg_win_layout.addWidget(epg_win_widget2)
        epg_win_widget.setLayout(epg_win_layout)
        epg_win.setCentralWidget(epg_win_widget)

        xtream_win = QtWidgets.QMainWindow()
        xtream_win.resize(400, 140)
        xtream_win.setWindowTitle("XTream")
        xtream_win.setWindowIcon(main_icon)

        xtream_win_2 = QtWidgets.QMainWindow()
        xtream_win_2.resize(400, 140)
        xtream_win_2.setWindowTitle("XTream")
        xtream_win_2.setWindowIcon(main_icon)

        scheduler_win = QtWidgets.QMainWindow()
        scheduler_win.resize(1200, 650)
        scheduler_win.setWindowTitle(_("Recording scheduler"))
        scheduler_win.setWindowIcon(main_icon)

        playlists_win = QtWidgets.QMainWindow()
        playlists_win.resize(500, 600)
        playlists_win.setWindowTitle(_("Playlists"))
        playlists_win.setWindowIcon(main_icon)

        playlists_win_edit = QtWidgets.QMainWindow()
        playlists_win_edit.resize(500, 180)
        playlists_win_edit.setWindowTitle(_("Playlists"))
        playlists_win_edit.setWindowIcon(main_icon)

        epg_select_win = QtWidgets.QMainWindow()
        epg_select_win.resize(400, 500)
        epg_select_win.setWindowTitle(_("TV guide"))
        epg_select_win.setWindowIcon(main_icon)

        class playlists_data:
            pass

        playlists_data.oldName = ""

        def playlists_win_save():
            if m3u_edit_1.text():
                channel_text_prov = name_edit_1.text()
                if channel_text_prov:
                    if playlists_data.oldName == "":
                        playlists_list.addItem(channel_text_prov)
                    playlists_data.playlists_used[channel_text_prov] = {
                        "m3u": m3u_edit_1.text(),
                        "epg": epg_edit_1.text(),
                        "epgoffset": soffset_1.value(),
                    }
                    playlists_save_json()
                    playlists_win_edit.hide()
                else:
                    noemptyname_msg = QtWidgets.QMessageBox(
                        qt_icon_warning,
                        MAIN_WINDOW_TITLE,
                        _("Name should not be empty!"),
                        QtWidgets.QMessageBox.StandardButton.Ok,
                    )
                    noemptyname_msg.exec()
            else:
                nourlset_msg = QtWidgets.QMessageBox(
                    qt_icon_warning,
                    MAIN_WINDOW_TITLE,
                    _("URL not specified!"),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                nourlset_msg.exec()

        def m3u_file_1_clicked():
            fname_1 = QtWidgets.QFileDialog.getOpenFileName(
                playlists_win_edit, _("Select m3u playlist"), home_folder
            )[0]
            if fname_1:
                m3u_edit_1.setText(fname_1)

        def epg_file_1_clicked():
            fname_2 = QtWidgets.QFileDialog.getOpenFileName(
                playlists_win_edit, _("Select EPG file"), home_folder
            )[0]
            if fname_2:
                epg_edit_1.setText(fname_2)

        name_label_1 = QtWidgets.QLabel("{}:".format(_("Name")))
        m3u_label_1 = QtWidgets.QLabel("{}:".format(_("M3U / XSPF playlist")))
        epg_label_1 = QtWidgets.QLabel("{}:".format(_("TV guide\naddress")))
        name_edit_1 = QtWidgets.QLineEdit()
        m3u_edit_1 = QtWidgets.QLineEdit()
        m3u_edit_1.setPlaceholderText(_("Path to file or URL"))
        epg_edit_1 = QtWidgets.QLineEdit()
        epg_edit_1.setPlaceholderText(_("Path to file or URL"))
        m3u_file_1 = QtWidgets.QPushButton()
        m3u_file_1.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "file.png")))
        )
        m3u_file_1.clicked.connect(m3u_file_1_clicked)
        epg_file_1 = QtWidgets.QPushButton()
        epg_file_1.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "file.png")))
        )
        epg_file_1.clicked.connect(epg_file_1_clicked)
        save_btn_1 = QtWidgets.QPushButton(_("Save"))
        save_btn_1.setStyleSheet("font-weight: bold; color: green;")
        save_btn_1.clicked.connect(playlists_win_save)
        soffset_1 = QtWidgets.QDoubleSpinBox()
        soffset_1.setMinimum(-240)
        soffset_1.setMaximum(240)
        soffset_1.setSingleStep(1)
        soffset_1.setDecimals(1)
        offset_label_1 = QtWidgets.QLabel("{}:".format(_("TV guide offset")))
        offset_label_hours = QtWidgets.QLabel(
            (gettext.ngettext("%d hour", "%d hours", 0) % 0).replace("0 ", "")
        )

        def lo_xtream_select_1():
            xtream_select_1()

        xtream_btn_1 = QtWidgets.QPushButton("XTream")
        xtream_btn_1.clicked.connect(lo_xtream_select_1)

        playlists_win_edit_widget = QtWidgets.QWidget()
        playlists_win_edit_layout = QtWidgets.QGridLayout()
        playlists_win_edit_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        playlists_win_edit_layout.addWidget(name_label_1, 0, 0)
        playlists_win_edit_layout.addWidget(name_edit_1, 0, 1)
        playlists_win_edit_layout.addWidget(m3u_label_1, 1, 0)
        playlists_win_edit_layout.addWidget(m3u_edit_1, 1, 1)
        playlists_win_edit_layout.addWidget(m3u_file_1, 1, 2)
        if platform.system() != "Windows":
            playlists_win_edit_layout.addWidget(xtream_btn_1, 2, 0)
        playlists_win_edit_layout.addWidget(epg_label_1, 3, 0)
        playlists_win_edit_layout.addWidget(epg_edit_1, 3, 1)
        playlists_win_edit_layout.addWidget(epg_file_1, 3, 2)
        playlists_win_edit_layout.addWidget(offset_label_1, 4, 0)
        playlists_win_edit_layout.addWidget(soffset_1, 4, 1)
        playlists_win_edit_layout.addWidget(offset_label_hours, 4, 2)
        playlists_win_edit_layout.addWidget(save_btn_1, 5, 1)
        playlists_win_edit_widget.setLayout(playlists_win_edit_layout)
        playlists_win_edit.setCentralWidget(playlists_win_edit_widget)

        yuki_iptv_icon = QtWidgets.QLabel()
        yuki_iptv_icon.setPixmap(TV_ICON.pixmap(QtCore.QSize(32, 32)))
        yuki_iptv_label = QtWidgets.QLabel()
        myFont6 = QtGui.QFont()
        myFont6.setPointSize(11)
        myFont6.setBold(True)
        yuki_iptv_label.setFont(myFont6)
        yuki_iptv_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        yuki_iptv_label.setText(
            '<br>&nbsp;<span style="color: #b35900;">yuki-iptv</span><br>'
        )

        yuki_iptv_widget = QtWidgets.QWidget()
        yuki_iptv_layout = QtWidgets.QHBoxLayout()
        yuki_iptv_layout.addWidget(yuki_iptv_icon)
        yuki_iptv_layout.addWidget(yuki_iptv_label)
        yuki_iptv_widget.setLayout(yuki_iptv_layout)

        yuki_iptv_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )

        def esw_input_edit():
            esw_input_text = esw_input.text().lower()
            for est_w in range(0, esw_select.count()):
                if esw_select.item(est_w).text().lower().startswith(esw_input_text):
                    esw_select.item(est_w).setHidden(False)
                else:
                    esw_select.item(est_w).setHidden(True)

        def esw_select_clicked(item1):
            epg_select_win.hide()
            if item1.text():
                epgname_lbl.setText(item1.text())
            else:
                epgname_lbl.setText(_("Default"))

        esw_input = QtWidgets.QLineEdit()
        esw_input.setPlaceholderText(_("Search"))
        esw_button = QtWidgets.QPushButton()
        esw_button.setText(_("Search"))
        esw_button.clicked.connect(esw_input_edit)
        esw_select = QtWidgets.QListWidget()
        esw_select.itemDoubleClicked.connect(esw_select_clicked)

        esw_widget = QtWidgets.QWidget()
        esw_widget_layout = QtWidgets.QHBoxLayout()
        esw_widget_layout.addWidget(esw_input)
        esw_widget_layout.addWidget(esw_button)
        esw_widget.setLayout(esw_widget_layout)

        epg_select_win_widget = QtWidgets.QWidget()
        epg_select_win_layout = QtWidgets.QVBoxLayout()
        epg_select_win_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        epg_select_win_layout.addWidget(esw_widget, 0)
        epg_select_win_layout.addWidget(esw_select, 1)
        epg_select_win_widget.setLayout(epg_select_win_layout)
        epg_select_win.setCentralWidget(epg_select_win_widget)

        def ext_open_btn_clicked():
            ext_player_file_1 = open(
                str(Path(LOCAL_DIR, "extplayer.json")), "w", encoding="utf8"
            )
            ext_player_file_1.write(json.dumps({"player": ext_player_txt.text()}))
            ext_player_file_1.close()
            subprocess.Popen(
                ext_player_txt.text().split(" ") + [getArrayItem(item_selected)["url"]]
            )
            ext_win.close()

        ext_player_txt = QtWidgets.QLineEdit()
        player_ext = "mpv"
        if os.path.isfile(str(Path(LOCAL_DIR, "extplayer.json"))):
            ext_player_file = open(
                str(Path(LOCAL_DIR, "extplayer.json")), "r", encoding="utf8"
            )
            ext_player_file_out = json.loads(ext_player_file.read())
            ext_player_file.close()
            player_ext = ext_player_file_out["player"]
        ext_player_txt.setText(player_ext)
        ext_open_btn = QtWidgets.QPushButton()
        ext_open_btn.clicked.connect(ext_open_btn_clicked)
        ext_open_btn.setText(_("Open"))
        ext_widget = QtWidgets.QWidget()
        ext_layout = QtWidgets.QGridLayout()
        ext_layout.addWidget(ext_player_txt, 0, 0)
        ext_layout.addWidget(ext_open_btn, 0, 1)
        ext_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        ext_widget.setLayout(ext_layout)
        ext_win.setCentralWidget(ext_widget)

        playlists_saved = {}

        if os.path.isfile(str(Path(LOCAL_DIR, "playlists.json"))):
            playlists_json = open(
                str(Path(LOCAL_DIR, "playlists.json")), "r", encoding="utf8"
            )
            playlists_saved = json.loads(playlists_json.read())
            playlists_json.close()

        playlists_list = QtWidgets.QListWidget()
        playlists_select = QtWidgets.QPushButton(_("Select"))
        playlists_select.setStyleSheet("font-weight: bold; color: green;")
        playlists_add = QtWidgets.QPushButton(_("Add"))
        playlists_edit = QtWidgets.QPushButton(_("Edit"))
        playlists_delete = QtWidgets.QPushButton(_("Delete"))
        playlists_favourites = QtWidgets.QPushButton(_("Favourites+"))
        playlists_settings = QtWidgets.QPushButton(_("Settings"))
        playlists_settings.setStyleSheet("color: blue;")

        playlists_win_widget = QtWidgets.QWidget()
        playlists_win_layout = QtWidgets.QGridLayout()
        playlists_win_layout.addWidget(playlists_add, 0, 0)
        playlists_win_layout.addWidget(playlists_edit, 0, 1)
        playlists_win_layout.addWidget(playlists_delete, 0, 2)
        playlists_win_layout.addWidget(playlists_favourites, 0, 3)
        playlists_win_widget.setLayout(playlists_win_layout)

        playlists_win_widget_main = QtWidgets.QWidget()
        playlists_win_widget_main_layout = QtWidgets.QVBoxLayout()
        playlists_win_widget_main_layout.addWidget(yuki_iptv_widget)
        playlists_win_widget_main_layout.addWidget(playlists_list)
        playlists_win_widget_main_layout.addWidget(playlists_select)
        playlists_win_widget_main_layout.addWidget(playlists_win_widget)
        playlists_win_widget_main_layout.addWidget(playlists_settings)
        playlists_win_widget_main.setLayout(playlists_win_widget_main_layout)

        playlists_win.setCentralWidget(playlists_win_widget_main)

        def playlists_favourites_do():
            playlists_win.close()
            sm3u.setText(str(Path(LOCAL_DIR, "favplaylist.m3u")))
            sepg.setText("")
            save_settings()

        playlists_favourites.clicked.connect(playlists_favourites_do)

        def playlists_json_save(playlists_save0=None):
            if not playlists_save0:
                playlists_save0 = playlists_saved
            playlists_json1 = open(
                str(Path(LOCAL_DIR, "playlists.json")), "w", encoding="utf8"
            )
            playlists_json1.write(json.dumps(playlists_save0))
            playlists_json1.close()

        time_stop = 0

        def moveWindowToCenter(win_arg, force=False):
            used_screen = QtWidgets.QApplication.primaryScreen()
            if not force:
                try:
                    used_screen = win.screen()
                except Exception:
                    pass
            qr0 = win_arg.frameGeometry()
            qr0.moveCenter(QtGui.QScreen.availableGeometry(used_screen).center())
            win_arg.move(qr0.topLeft())

        qr = settings_win.frameGeometry()
        qr.moveCenter(
            QtGui.QScreen.availableGeometry(
                QtWidgets.QApplication.primaryScreen()
            ).center()
        )
        settings_win_l = qr.topLeft()
        origY = settings_win_l.y() - 150
        settings_win_l.setY(origY)
        settings_win.move(qr.topLeft())

        moveWindowToCenter(epg_win)

        ffmpeg_processes = []

        init_record(show_exception, ffmpeg_processes)

        def convert_time(times_1):
            yr = time.strftime("%Y", time.localtime())
            yr = yr[0] + yr[1]
            times_1_sp = times_1.split(" ")
            times_1_sp_0 = times_1_sp[0].split(".")
            times_1_sp_0[2] = yr + times_1_sp_0[2]
            times_1_sp[0] = ".".join(times_1_sp_0)
            return " ".join(times_1_sp)

        def programme_clicked(item):
            times = item.text().split("\n")[0]
            start_time = convert_time(times.split(" - ")[0])
            end_time = convert_time(times.split(" - ")[1])
            starttime_w.setDateTime(
                QtCore.QDateTime.fromString(start_time, "d.M.yyyy hh:mm")
            )
            endtime_w.setDateTime(
                QtCore.QDateTime.fromString(end_time, "d.M.yyyy hh:mm")
            )

        def addrecord_clicked():
            selected_chan = choosechannel_ch.currentText()
            if qt_library == "PySide6":
                start_time_r = (
                    starttime_w.dateTime().toPython().strftime("%d.%m.%y %H:%M")
                )
                end_time_r = endtime_w.dateTime().toPython().strftime("%d.%m.%y %H:%M")
            else:
                start_time_r = (
                    starttime_w.dateTime().toPyDateTime().strftime("%d.%m.%y %H:%M")
                )
                end_time_r = (
                    endtime_w.dateTime().toPyDateTime().strftime("%d.%m.%y %H:%M")
                )
            schedulers.addItem(
                _("Channel") + ": " + selected_chan + "\n"
                "{}: ".format(_("Start record time")) + start_time_r + "\n"
                "{}: ".format(_("End record time")) + end_time_r + "\n"
            )

        sch_recordings = {}

        def do_start_record(name1):
            ch_name = name1.split("_")[0]
            ch = ch_name.replace(" ", "_")
            for char in FORBIDDEN_CHARS:
                ch = ch.replace(char, "")
            cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
            if not settings["scrrecnosubfolders"]:
                out_file = str(
                    Path(
                        save_folder,
                        "recordings",
                        "recording_-_" + cur_time + "_-_" + ch + ".mkv",
                    )
                )
            else:
                out_file = str(
                    Path(save_folder, "recording_-_" + cur_time + "_-_" + ch + ".mkv")
                )
            record_url = getArrayItem(ch_name)["url"]
            return [
                record_return(
                    record_url,
                    out_file,
                    ch_name,
                    f"Referer: {settings['referer']}",
                    get_ua_ref_for_channel,
                ),
                time.time(),
                out_file,
                ch_name,
            ]

        def do_stop_record(name2):
            if name2 in sch_recordings:
                ffmpeg_process = sch_recordings[name2][0]
                if ffmpeg_process:
                    if platform.system() == "Windows":
                        ffmpeg_process.write(bytes("q\r\n", "utf-8"))
                        ffmpeg_process.waitForBytesWritten()
                        ffmpeg_process.closeWriteChannel()
                    else:
                        ffmpeg_process.terminate()

        recViaScheduler = False

        @async_gui_blocking_function
        def record_post_action():
            while True:
                if is_recording_func() is True:
                    break
                time.sleep(1)
            logger.info("Record via scheduler ended, executing post-action...")
            # 0 - nothing to do
            if praction_choose.currentIndex() == 1:  # 1 - Press Stop
                mpv_stop()

        def format_bytes(bytes1, hbnames):
            idx = 0
            while bytes1 >= 1024 and idx + 1 < len(hbnames):
                bytes1 = bytes1 / 1024
                idx += 1
            return f"{bytes1:.1f} {hbnames[idx]}"

        def format_seconds(seconds):
            return time.strftime("%H:%M:%S", time.gmtime(seconds))

        def convert_size(size_bytes):
            return format_bytes(
                size_bytes, ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
            )

        def record_thread_2():
            try:
                global recViaScheduler
                activerec_list_value = activerec_list.verticalScrollBar().value()
                activerec_list.clear()
                for sch0 in sch_recordings:
                    counted_time0 = format_seconds(
                        time.time() - sch_recordings[sch0][1]
                    )
                    channel_name0 = sch_recordings[sch0][3]
                    file_name0 = sch_recordings[sch0][2]
                    file_size0 = "WAITING"
                    if os.path.isfile(file_name0):
                        file_size0 = convert_size(os.path.getsize(file_name0))
                    activerec_list.addItem(
                        channel_name0 + "\n" + counted_time0 + " " + file_size0
                    )
                activerec_list.verticalScrollBar().setValue(activerec_list_value)
                pl_text = "REC / " + _("Scheduler")
                if activerec_list.count() != 0:
                    recViaScheduler = True
                    lbl2.setText(pl_text)
                    lbl2.show()
                else:
                    if recViaScheduler:
                        logger.info(
                            "Record via scheduler ended, waiting"
                            " for ffmpeg process completion..."
                        )
                        record_post_action()
                    recViaScheduler = False
                    if lbl2.text() == pl_text:
                        lbl2.hide()
            except Exception:
                pass

        is_recording_old = False

        @idle_function
        def set_record_icon(unused=None):
            label5_1.setIcon(record_icon)

        @idle_function
        def set_record_stop_icon(unused=None):
            label5_1.setIcon(record_stop_icon)

        def record_thread():
            try:
                global is_recording, is_recording_old, ffmpeg_processes
                if is_recording != is_recording_old:
                    is_recording_old = is_recording
                    if is_recording:
                        set_record_stop_icon()
                    else:
                        set_record_icon()
                status = _("No planned recordings")
                sch_items = [
                    str(schedulers.item(i1).text()) for i1 in range(schedulers.count())
                ]
                i3 = -1
                for sch_item in sch_items:
                    i3 += 1
                    status = _("Waiting for record")
                    sch_item = [i2.split(": ")[1] for i2 in sch_item.split("\n") if i2]
                    channel_name_rec = sch_item[0]
                    current_time = time.strftime("%d.%m.%y %H:%M", time.localtime())
                    start_time_1 = sch_item[1]
                    end_time_1 = sch_item[2]
                    array_name = (
                        str(channel_name_rec)
                        + "_"
                        + str(start_time_1)
                        + "_"
                        + str(end_time_1)
                    )
                    if start_time_1 == current_time:
                        if array_name not in sch_recordings:
                            st_planned = (
                                "Starting planned record"
                                + " (start_time='{}' end_time='{}' channel='{}')"
                            )
                            logger.info(
                                st_planned.format(
                                    start_time_1, end_time_1, channel_name_rec
                                )
                            )
                            sch_recordings[array_name] = do_start_record(array_name)
                            ffmpeg_processes.append(sch_recordings[array_name])
                    if end_time_1 == current_time:
                        if array_name in sch_recordings:
                            schedulers.takeItem(i3)
                            stop_planned = (
                                "Stopping planned record"
                                + " (start_time='{}' end_time='{}' channel='{}')"
                            )
                            logger.info(
                                stop_planned.format(
                                    start_time_1, end_time_1, channel_name_rec
                                )
                            )
                            do_stop_record(array_name)
                            sch_recordings.pop(array_name)
                    if sch_recordings:
                        status = _("Recording")
                statusrec_lbl.setText("{}: {}".format(_("Status"), status))
            except Exception:
                pass

        def delrecord_clicked():
            schCurrentRow = schedulers.currentRow()
            if schCurrentRow != -1:
                sch_index = "_".join(
                    [
                        xs.split(": ")[1]
                        for xs in schedulers.item(schCurrentRow).text().split("\n")
                        if xs
                    ]
                )
                schedulers.takeItem(schCurrentRow)
                if sch_index in sch_recordings:
                    do_stop_record(sch_index)
                    sch_recordings.pop(sch_index)

        scheduler_widget = QtWidgets.QWidget()
        scheduler_layout = QtWidgets.QGridLayout()
        scheduler_clock = QtWidgets.QLabel(get_current_time())
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(11)
        myFont4.setBold(True)
        scheduler_clock.setFont(myFont4)
        scheduler_clock.setStyleSheet("color: green")
        plannedrec_lbl = QtWidgets.QLabel("{}:".format(_("Planned recordings")))
        activerec_lbl = QtWidgets.QLabel("{}:".format(_("Active recordings")))
        statusrec_lbl = QtWidgets.QLabel()
        myFont5 = QtGui.QFont()
        myFont5.setBold(True)
        statusrec_lbl.setFont(myFont5)
        choosechannel_lbl = QtWidgets.QLabel("{}:".format(_("Choose channel")))
        choosechannel_ch = QtWidgets.QComboBox()
        tvguide_sch = QtWidgets.QListWidget()
        tvguide_sch.itemClicked.connect(programme_clicked)
        addrecord_btn = QtWidgets.QPushButton(_("Add"))
        addrecord_btn.clicked.connect(addrecord_clicked)
        delrecord_btn = QtWidgets.QPushButton(_("Remove"))
        delrecord_btn.clicked.connect(delrecord_clicked)

        def scheduler_channelfilter_do():
            try:
                filter_txt2 = schedulerchannelfilter.text()
            except Exception:
                filter_txt2 = ""
            for item5 in range(choosechannel_ch.count()):
                if (
                    unidecode(filter_txt2).lower().strip()
                    in unidecode(choosechannel_ch.itemText(item5)).lower().strip()
                ):
                    choosechannel_ch.view().setRowHidden(item5, False)
                else:
                    choosechannel_ch.view().setRowHidden(item5, True)

        schedulerchannelfilter = QtWidgets.QLineEdit()
        schedulerchannelfilter.setPlaceholderText(_("Search channel"))
        schedulerchannelfiltersearch = QtWidgets.QPushButton()
        schedulerchannelfiltersearch.setText(_("Search"))
        schedulerchannelfiltersearch.clicked.connect(scheduler_channelfilter_do)
        schedulerchannelfilter.returnPressed.connect(scheduler_channelfilter_do)

        schedulerchannelwidget = QtWidgets.QWidget()
        schedulerchannellayout = QtWidgets.QHBoxLayout()
        schedulerchannellayout.addWidget(schedulerchannelfilter)
        schedulerchannellayout.addWidget(schedulerchannelfiltersearch)
        schedulerchannelwidget.setLayout(schedulerchannellayout)

        scheduler_layout.addWidget(scheduler_clock, 0, 0)
        scheduler_layout.addWidget(choosechannel_lbl, 1, 0)
        scheduler_layout.addWidget(schedulerchannelwidget, 2, 0)
        scheduler_layout.addWidget(choosechannel_ch, 3, 0)
        scheduler_layout.addWidget(tvguide_sch, 4, 0)

        starttime_lbl = QtWidgets.QLabel("{}:".format(_("Start record time")))
        endtime_lbl = QtWidgets.QLabel("{}:".format(_("End record time")))
        starttime_w = QtWidgets.QDateTimeEdit()
        starttime_w.setDateTime(
            QtCore.QDateTime.fromString(
                time.strftime("%d.%m.%Y %H:%M", time.localtime()), "d.M.yyyy hh:mm"
            )
        )
        endtime_w = QtWidgets.QDateTimeEdit()
        endtime_w.setDateTime(
            QtCore.QDateTime.fromString(
                time.strftime("%d.%m.%Y %H:%M", time.localtime(time.time() + 60)),
                "d.M.yyyy hh:mm",
            )
        )

        praction_lbl = QtWidgets.QLabel("{}:".format(_("Post-recording\naction")))
        praction_choose = QtWidgets.QComboBox()
        praction_choose.addItem(_("Nothing to do"))
        praction_choose.addItem(_("Press Stop"))

        schedulers = QtWidgets.QListWidget()
        activerec_list = QtWidgets.QListWidget()

        scheduler_layout_2 = QtWidgets.QGridLayout()
        scheduler_layout_2.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        scheduler_layout_2.addWidget(starttime_lbl, 0, 0)
        scheduler_layout_2.addWidget(starttime_w, 1, 0)
        scheduler_layout_2.addWidget(endtime_lbl, 2, 0)
        scheduler_layout_2.addWidget(endtime_w, 3, 0)
        scheduler_layout_2.addWidget(addrecord_btn, 4, 0)
        scheduler_layout_2.addWidget(delrecord_btn, 5, 0)
        scheduler_layout_2.addWidget(QtWidgets.QLabel(), 6, 0)
        scheduler_layout_2.addWidget(praction_lbl, 7, 0)
        scheduler_layout_2.addWidget(praction_choose, 8, 0)

        scheduler_layout_3 = QtWidgets.QGridLayout()
        scheduler_layout_3.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        scheduler_layout_3.addWidget(statusrec_lbl, 0, 0)
        scheduler_layout_3.addWidget(plannedrec_lbl, 1, 0)
        scheduler_layout_3.addWidget(schedulers, 2, 0)

        scheduler_layout_4 = QtWidgets.QGridLayout()
        scheduler_layout_4.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        scheduler_layout_4.addWidget(activerec_lbl, 0, 0)
        scheduler_layout_4.addWidget(activerec_list, 1, 0)

        scheduler_layout_main_w = QtWidgets.QWidget()
        scheduler_layout_main_w.setLayout(scheduler_layout)

        scheduler_layout_main_w2 = QtWidgets.QWidget()
        scheduler_layout_main_w2.setLayout(scheduler_layout_2)

        scheduler_layout_main_w3 = QtWidgets.QWidget()
        scheduler_layout_main_w3.setLayout(scheduler_layout_3)

        scheduler_layout_main_w4 = QtWidgets.QWidget()
        scheduler_layout_main_w4.setLayout(scheduler_layout_4)

        scheduler_layout_main1 = QtWidgets.QHBoxLayout()
        scheduler_layout_main1.addWidget(scheduler_layout_main_w)
        scheduler_layout_main1.addWidget(scheduler_layout_main_w2)
        scheduler_layout_main1.addWidget(scheduler_layout_main_w3)
        scheduler_layout_main1.addWidget(scheduler_layout_main_w4)
        scheduler_widget.setLayout(scheduler_layout_main1)

        warning_lbl = QtWidgets.QLabel(
            _("Recording of two channels simultaneously is not available!")
        )
        myFont5 = QtGui.QFont()
        myFont5.setPointSize(11)
        myFont5.setBold(True)
        warning_lbl.setFont(myFont5)
        warning_lbl.setStyleSheet("color: red")
        warning_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        scheduler_layout_main = QtWidgets.QVBoxLayout()
        scheduler_layout_main.addWidget(scheduler_widget)
        scheduler_widget_main = QtWidgets.QWidget()
        scheduler_widget_main.setLayout(scheduler_layout_main)

        scheduler_win.setCentralWidget(scheduler_widget_main)

        def save_sort():
            global channel_sort
            channel_sort = [
                sort_list.item(z0).text() for z0 in range(sort_list.count())
            ]
            channel_sort2 = {}
            if os.path.isfile(Path(LOCAL_DIR, "sortchannels.json")):
                with open(
                    Path(LOCAL_DIR, "sortchannels.json"), "r", encoding="utf8"
                ) as file5:
                    channel_sort2 = json.loads(file5.read())
            channel_sort2[settings["m3u"]] = channel_sort
            with open(
                Path(LOCAL_DIR, "sortchannels.json"), "w", encoding="utf8"
            ) as file4:
                file4.write(json.dumps(channel_sort2))
            sort_win.hide()

        close_sort_btn = QtWidgets.QPushButton(_("Close"))
        close_sort_btn.clicked.connect(sort_win.hide)
        close_sort_btn.setStyleSheet("color: red;")

        save_sort_btn = QtWidgets.QPushButton(_("Save"))
        save_sort_btn.setStyleSheet("font-weight: bold; color: green;")
        save_sort_btn.clicked.connect(save_sort)

        sort_label = QtWidgets.QLabel(
            _("Do not forget\nto set custom sort order in settings!")
        )
        sort_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        sort_widget3 = QtWidgets.QWidget()

        sort_widget4 = QtWidgets.QWidget()
        sort_widget4_layout = QtWidgets.QHBoxLayout()
        sort_widget4_layout.addWidget(save_sort_btn)
        sort_widget4_layout.addWidget(close_sort_btn)
        sort_widget4.setLayout(sort_widget4_layout)

        sort_widget_main = QtWidgets.QWidget()
        sort_layout = QtWidgets.QVBoxLayout()
        sort_layout.addWidget(sort_label)
        sort_layout.addWidget(sort_widget3)
        sort_layout.addWidget(sort_widget4)
        sort_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )
        sort_widget_main.setLayout(sort_layout)
        sort_win.setCentralWidget(sort_widget_main)

        home_folder = ""
        try:
            home_folder = os.environ["HOME"]
        except Exception:
            pass

        def m3u_select():
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win, _("Select m3u playlist"), home_folder
            )[0]
            if fname:
                sm3u.setText(fname)

        def epg_select():
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win, _("Select EPG file"), home_folder
            )[0]
            if fname:
                sepg.setText(fname if not fname.startswith("^^::MULTIPLE::^^") else "")

        def save_folder_select():
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                settings_win,
                _("Select folder for recordings and screenshots"),
                options=QtWidgets.QFileDialog.Option.ShowDirsOnly,
            )
            if folder_name:
                sfld.setText(folder_name)

        # Channel settings window
        wid = QtWidgets.QWidget()

        title = QtWidgets.QLabel()
        myFont2 = QtGui.QFont()
        myFont2.setBold(True)
        title.setFont(myFont2)
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        deinterlace_lbl = QtWidgets.QLabel("{}:".format(_("Deinterlace")))
        useragent_lbl = QtWidgets.QLabel("{}:".format(_("User agent")))
        group_lbl = QtWidgets.QLabel("{}:".format(_("Group")))
        group_text = QtWidgets.QLineEdit()
        hidden_lbl = QtWidgets.QLabel("{}:".format(_("Hide")))
        deinterlace_chk = QtWidgets.QCheckBox()
        hidden_chk = QtWidgets.QCheckBox()
        useragent_choose = QtWidgets.QLineEdit()

        def epgname_btn_action():
            prog_ids_0 = []
            for x0 in prog_ids:
                for x1 in prog_ids[x0]:
                    if x1 not in prog_ids_0:
                        prog_ids_0.append(x1)
            esw_select.clear()
            esw_select.addItem("")
            for prog_ids_0_dat in prog_ids_0:
                esw_select.addItem(prog_ids_0_dat)
            esw_input_edit()
            moveWindowToCenter(epg_select_win)
            epg_select_win.show()

        contrast_lbl = QtWidgets.QLabel("{}:".format(_("Contrast")))
        brightness_lbl = QtWidgets.QLabel("{}:".format(_("Brightness")))
        hue_lbl = QtWidgets.QLabel("{}:".format(_("Hue")))
        saturation_lbl = QtWidgets.QLabel("{}:".format(_("Saturation")))
        gamma_lbl = QtWidgets.QLabel("{}:".format(_("Gamma")))
        videoaspect_lbl = QtWidgets.QLabel("{}:".format(_("Aspect ratio")))
        zoom_lbl = QtWidgets.QLabel("{}:".format(_("Scale / Zoom")))
        panscan_lbl = QtWidgets.QLabel("{}:".format(_("Pan and scan")))
        epgname_btn = QtWidgets.QPushButton(_("EPG name"))
        epgname_btn.clicked.connect(epgname_btn_action)

        epgname_lbl = QtWidgets.QLabel()

        contrast_choose = QtWidgets.QSpinBox()
        contrast_choose.setMinimum(-100)
        contrast_choose.setMaximum(100)
        brightness_choose = QtWidgets.QSpinBox()
        brightness_choose.setMinimum(-100)
        brightness_choose.setMaximum(100)
        hue_choose = QtWidgets.QSpinBox()
        hue_choose.setMinimum(-100)
        hue_choose.setMaximum(100)
        saturation_choose = QtWidgets.QSpinBox()
        saturation_choose.setMinimum(-100)
        saturation_choose.setMaximum(100)
        gamma_choose = QtWidgets.QSpinBox()
        gamma_choose.setMinimum(-100)
        gamma_choose.setMaximum(100)
        videoaspect_vars = {
            _("Default"): -1,
            "16:9": "16:9",
            "16:10": "16:10",
            "1.85:1": "1.85:1",
            "2.21:1": "2.21:1",
            "2.35:1": "2.35:1",
            "2.39:1": "2.39:1",
            "4:3": "4:3",
            "5:4": "5:4",
            "5:3": "5:3",
            "1:1": "1:1",
        }
        videoaspect_choose = QtWidgets.QComboBox()
        for videoaspect_var in videoaspect_vars:
            videoaspect_choose.addItem(videoaspect_var)

        zoom_choose = QtWidgets.QComboBox()
        zoom_vars = {
            _("Default"): 0,
            "1.05": "1.05",
            "1.1": "1.1",
            "1.2": "1.2",
            "1.3": "1.3",
            "1.4": "1.4",
            "1.5": "1.5",
            "1.6": "1.6",
            "1.7": "1.7",
            "1.8": "1.8",
            "1.9": "1.9",
            "2": "2",
        }
        for zoom_var in zoom_vars:
            zoom_choose.addItem(zoom_var)

        panscan_choose = QtWidgets.QDoubleSpinBox()
        panscan_choose.setMinimum(0)
        panscan_choose.setMaximum(1)
        panscan_choose.setSingleStep(0.1)
        panscan_choose.setDecimals(1)

        def_user_agent = settings["ua"]
        logger.info(f"Default user agent: {def_user_agent}")
        if settings["referer"]:
            logger.info(f"Default HTTP referer: {settings['referer']}")
        else:
            logger.info("Default HTTP referer: (empty)")

        YukiData.bitrate_failed = False

        referer_lbl_custom = QtWidgets.QLabel(_("HTTP Referer:"))
        referer_choose_custom = QtWidgets.QLineEdit()

        def on_bitrate(prop, bitrate):
            try:
                if not bitrate or prop not in ["video-bitrate", "audio-bitrate"]:
                    return

                if _("Average Bitrate") in stream_info.video_properties:
                    if _("Average Bitrate") in stream_info.audio_properties:
                        if not streaminfo_win.isVisible():
                            return

                rates = {
                    "video": stream_info.video_bitrates,
                    "audio": stream_info.audio_bitrates,
                }
                rate = "video"
                if prop == "audio-bitrate":
                    rate = "audio"

                rates[rate].append(int(bitrate) / 1000.0)
                rates[rate] = rates[rate][-30:]
                br = sum(rates[rate]) / float(len(rates[rate]))

                if rate == "video":
                    stream_info.video_properties[_("General")][_("Average Bitrate")] = (
                        "%.f " + _("kbps")
                    ) % br
                else:
                    stream_info.audio_properties[_("General")][_("Average Bitrate")] = (
                        "%.f " + _("kbps")
                    ) % br
            except Exception:
                if not YukiData.bitrate_failed:
                    YukiData.bitrate_failed = True
                    logger.warning("on_bitrate FAILED with exception!")
                    logger.warning(traceback.format_exc())

        def on_video_params(property1, params):
            try:
                if not params or not isinstance(params, dict):
                    return
                if "w" in params and "h" in params:
                    stream_info.video_properties[_("General")][
                        _("Dimensions")
                    ] = "%sx%s" % (params["w"], params["h"])
                if "aspect" in params:
                    aspect = round(float(params["aspect"]), 2)
                    stream_info.video_properties[_("General")][_("Aspect")] = (
                        "%s" % aspect
                    )
                if "pixelformat" in params:
                    stream_info.video_properties[_("Color")][
                        _("Pixel Format")
                    ] = params["pixelformat"]
                if "gamma" in params:
                    stream_info.video_properties[_("Color")][_("Gamma")] = params[
                        "gamma"
                    ]
                if "average-bpp" in params:
                    stream_info.video_properties[_("Color")][
                        _("Bits Per Pixel")
                    ] = params["average-bpp"]
            except Exception:
                pass

        def on_video_format(property1, vformat):
            try:
                if not vformat:
                    return
                stream_info.video_properties[_("General")][_("Codec")] = vformat
            except Exception:
                pass

        def on_audio_params(property1, params):
            try:
                if not params or not isinstance(params, dict):
                    return
                if "channels" in params:
                    chans = params["channels"]
                    if "5.1" in chans or "7.1" in chans:
                        chans += " " + _("surround sound")
                    stream_info.audio_properties[_("Layout")][_("Channels")] = chans
                if "samplerate" in params:
                    sr = float(params["samplerate"]) / 1000.0
                    stream_info.audio_properties[_("General")][_("Sample Rate")] = (
                        "%.1f KHz" % sr
                    )
                if "format" in params:
                    fmt = params["format"]
                    fmt = AUDIO_SAMPLE_FORMATS.get(fmt, fmt)
                    stream_info.audio_properties[_("General")][_("Format")] = fmt
                if "channel-count" in params:
                    stream_info.audio_properties[_("Layout")][
                        _("Channel Count")
                    ] = params["channel-count"]
            except Exception:
                pass

        def on_audio_codec(property1, codec):
            try:
                if not codec:
                    return
                stream_info.audio_properties[_("General")][_("Codec")] = codec.split()[
                    0
                ]
            except Exception:
                pass

        @async_gui_blocking_function
        def monitor_playback():
            try:
                player.wait_until_playing()
                player.observe_property("video-params", on_video_params)
                player.observe_property("video-format", on_video_format)
                player.observe_property("audio-params", on_audio_params)
                player.observe_property("audio-codec", on_audio_codec)
                player.observe_property("video-bitrate", on_bitrate)
                player.observe_property("audio-bitrate", on_bitrate)
            except Exception:
                pass

        def hideLoading():
            loading.hide()
            loading_movie.stop()
            loading1.hide()

        def showLoading():
            centerwidget(loading1)
            loading.show()
            loading_movie.start()
            loading1.show()

        event_handler = None

        def on_before_play():
            streaminfo_win.hide()
            stream_info.video_properties.clear()
            stream_info.video_properties[_("General")] = {}
            stream_info.video_properties[_("Color")] = {}

            stream_info.audio_properties.clear()
            stream_info.audio_properties[_("General")] = {}
            stream_info.audio_properties[_("Layout")] = {}

            stream_info.video_bitrates.clear()
            stream_info.audio_bitrates.clear()

        def get_ua_ref_for_channel(channel_name1):
            useragent_ref = settings["ua"]
            referer_ref = settings["referer"]
            if channel_name1 and channel_name1 in array:
                useragent_ref = (
                    array[channel_name1]["useragent"]
                    if array[channel_name1]["useragent"]
                    else settings["ua"]
                )
                referer_ref = (
                    array[channel_name1]["referer"]
                    if array[channel_name1]["referer"]
                    else settings["referer"]
                )
            if settings["m3u"] in channel_sets:
                channel_set = channel_sets[settings["m3u"]]
                if channel_name1 and channel_name1 in channel_set:
                    channel_config = channel_set[channel_name1]
                    if (
                        "ua" in channel_config
                        and channel_config["ua"]
                        and channel_config["ua"] != settings["ua"]
                    ):
                        useragent_ref = channel_config["ua"]
                    if (
                        "ref" in channel_config
                        and channel_config["ref"]
                        and channel_config["ref"] != settings["referer"]
                    ):
                        referer_ref = channel_config["ref"]
            return useragent_ref, referer_ref

        def mpv_override_play(arg_override_play, channel_name1=""):
            global event_handler
            on_before_play()
            useragent_ref, referer_ref = get_ua_ref_for_channel(channel_name1)
            player.user_agent = useragent_ref
            if referer_ref:
                player.http_header_fields = f"Referer: {referer_ref}"
            else:
                player.http_header_fields = ""

            is_main = arg_override_play.endswith(
                "/main.png"
            ) or arg_override_play.endswith("\\main.png")
            if not is_main:
                logger.info(f"Using User-Agent: {player.user_agent}")
                cur_ref = ""
                try:
                    for ref1 in player.http_header_fields:
                        if ref1.startswith("Referer: "):
                            ref1 = ref1.replace("Referer: ", "", 1)
                            cur_ref = ref1
                except Exception:
                    pass
                if cur_ref:
                    logger.info(f"Using HTTP Referer: {cur_ref}")
                else:
                    logger.info("Using HTTP Referer: (empty)")

            player.pause = False
            player.play(parse_specifiers_now_url(arg_override_play))
            if event_handler:
                try:
                    event_handler.on_title()
                except Exception:
                    pass
                try:
                    event_handler.on_options()
                except Exception:
                    pass
                try:
                    event_handler.on_playback()
                except Exception:
                    pass

        def mpv_override_stop(ignore=False):
            global event_handler
            player.command("stop")
            if not ignore:
                logger.info("Disabling deinterlace for main.png")
                player.deinterlace = False
            player.play(str(Path("yuki_iptv", ICONS_FOLDER, "main.png")))
            player.pause = True
            if event_handler:
                try:
                    event_handler.on_title()
                except Exception:
                    pass
                try:
                    event_handler.on_options()
                except Exception:
                    pass
                try:
                    event_handler.on_ended()
                except Exception:
                    pass

        firstVolRun = True

        def mpv_override_volume(volume_val):
            global event_handler, firstVolRun
            player.volume = volume_val
            YukiData.volume = volume_val
            if event_handler:
                try:
                    event_handler.on_volume()
                except Exception:
                    pass

        def mpv_override_mute(mute_val):
            global event_handler
            player.mute = mute_val
            if event_handler:
                try:
                    event_handler.on_volume()
                except Exception:
                    pass

        def stopPlayer(ignore=False):
            try:
                mpv_override_stop(ignore)
            except Exception:
                player.loop = True
                mpv_override_play(str(Path("yuki_iptv", ICONS_FOLDER, "main.png")))
                player.pause = True

        def setVideoAspect(va):
            if va == 0:
                va = -1
            try:
                player.video_aspect_override = va
            except Exception:
                player.video_aspect = va

        def setZoom(zm):
            player.video_zoom = zm

        def setPanscan(ps):
            player.panscan = ps

        def getVideoAspect():
            try:
                va1 = player.video_aspect_override
            except Exception:
                va1 = player.video_aspect
            return va1

        def doPlay(play_url1, ua_ch=def_user_agent, chan_name_0=""):
            comm_instance.do_play_args = (play_url1, ua_ch, chan_name_0)
            logger.info("")
            logger.info(f"Playing '{chan_name_0}' ('{format_url_clean(play_url1)}')")
            # Loading
            loading.setText(_("Loading..."))
            loading.setStyleSheet("color: #778a30")
            showLoading()
            # Optimizations
            if play_url1.startswith("udp://") or play_url1.startswith("rtp://"):
                if settings["multicastoptimization"]:
                    try:
                        # For low latency on multicast
                        logger.info("Using multicast optimized settings")
                        player.cache = "no"
                        player.untimed = True
                        player["cache-pause"] = False
                        player["audio-buffer"] = 0
                        player["vd-lavc-threads"] = 1
                        player["demuxer-lavf-probe-info"] = "nostreams"
                        player["demuxer-lavf-analyzeduration"] = 0.1
                        player["video-sync"] = "audio"
                        player["interpolation"] = False
                        player["video-latency-hacks"] = True
                    except Exception:
                        logger.warning("Failed to set multicast optimized settings!")
            try:
                if settings["autoreconnection"]:
                    player.stream_lavf_o = (
                        "-reconnect=1 -reconnect_at_eof=1 "
                        "-reconnect_streamed=1 -reconnect_delay_max=2"
                    )
            except Exception:
                pass
            player.loop = False
            # Playing
            mpv_override_play(play_url1, chan_name_0)
            # Set channel (video) settings
            setPlayerSettings(chan_name_0)
            # Monitor playback (for stream information)
            monitor_playback()

        def chan_set_save():
            chan_3 = title.text()
            if settings["m3u"] not in channel_sets:
                channel_sets[settings["m3u"]] = {}
            channel_sets[settings["m3u"]][chan_3] = {
                "deinterlace": deinterlace_chk.isChecked(),
                "ua": useragent_choose.text(),
                "ref": referer_choose_custom.text(),
                "group": group_text.text(),
                "hidden": hidden_chk.isChecked(),
                "contrast": contrast_choose.value(),
                "brightness": brightness_choose.value(),
                "hue": hue_choose.value(),
                "saturation": saturation_choose.value(),
                "gamma": gamma_choose.value(),
                "videoaspect": videoaspect_choose.currentIndex(),
                "zoom": zoom_choose.currentIndex(),
                "panscan": panscan_choose.value(),
                "epgname": epgname_lbl.text()
                if epgname_lbl.text() != _("Default")
                else "",
            }
            save_channel_sets()
            if playing_chan == chan_3:
                player.deinterlace = deinterlace_chk.isChecked()
                player.contrast = contrast_choose.value()
                player.brightness = brightness_choose.value()
                player.hue = hue_choose.value()
                player.saturation = saturation_choose.value()
                player.gamma = gamma_choose.value()
                player.video_zoom = zoom_vars[
                    list(zoom_vars)[zoom_choose.currentIndex()]
                ]
                player.panscan = panscan_choose.value()
                setVideoAspect(
                    videoaspect_vars[
                        list(videoaspect_vars)[videoaspect_choose.currentIndex()]
                    ]
                )
            btn_update.click()
            chan_win.close()

        save_btn = QtWidgets.QPushButton(_("Save settings"))
        save_btn.clicked.connect(chan_set_save)

        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addWidget(title)

        horizontalLayout2 = QtWidgets.QHBoxLayout()
        horizontalLayout2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2.addWidget(deinterlace_lbl)
        horizontalLayout2.addWidget(deinterlace_chk)
        horizontalLayout2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_1 = QtWidgets.QHBoxLayout()
        horizontalLayout2_1.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_1.addWidget(useragent_lbl)
        horizontalLayout2_1.addWidget(useragent_choose)
        horizontalLayout2_1.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_13 = QtWidgets.QHBoxLayout()
        horizontalLayout2_13.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_13.addWidget(referer_lbl_custom)
        horizontalLayout2_13.addWidget(referer_choose_custom)
        horizontalLayout2_13.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_13.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_2 = QtWidgets.QHBoxLayout()
        horizontalLayout2_2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_2.addWidget(group_lbl)
        horizontalLayout2_2.addWidget(group_text)
        horizontalLayout2_2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_3 = QtWidgets.QHBoxLayout()
        horizontalLayout2_3.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_3.addWidget(hidden_lbl)
        horizontalLayout2_3.addWidget(hidden_chk)
        horizontalLayout2_3.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_4 = QtWidgets.QHBoxLayout()
        horizontalLayout2_4.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_4.addWidget(contrast_lbl)
        horizontalLayout2_4.addWidget(contrast_choose)
        horizontalLayout2_4.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_4.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_5 = QtWidgets.QHBoxLayout()
        horizontalLayout2_5.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_5.addWidget(brightness_lbl)
        horizontalLayout2_5.addWidget(brightness_choose)
        horizontalLayout2_5.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_6 = QtWidgets.QHBoxLayout()
        horizontalLayout2_6.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_6.addWidget(hue_lbl)
        horizontalLayout2_6.addWidget(hue_choose)
        horizontalLayout2_6.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_7 = QtWidgets.QHBoxLayout()
        horizontalLayout2_7.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_7.addWidget(saturation_lbl)
        horizontalLayout2_7.addWidget(saturation_choose)
        horizontalLayout2_7.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_8 = QtWidgets.QHBoxLayout()
        horizontalLayout2_8.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_8.addWidget(gamma_lbl)
        horizontalLayout2_8.addWidget(gamma_choose)
        horizontalLayout2_8.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_9 = QtWidgets.QHBoxLayout()
        horizontalLayout2_9.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_9.addWidget(videoaspect_lbl)
        horizontalLayout2_9.addWidget(videoaspect_choose)
        horizontalLayout2_9.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_9.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_10 = QtWidgets.QHBoxLayout()
        horizontalLayout2_10.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_10.addWidget(zoom_lbl)
        horizontalLayout2_10.addWidget(zoom_choose)
        horizontalLayout2_10.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_10.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_11 = QtWidgets.QHBoxLayout()
        horizontalLayout2_11.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_11.addWidget(panscan_lbl)
        horizontalLayout2_11.addWidget(panscan_choose)
        horizontalLayout2_11.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_11.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout2_12 = QtWidgets.QHBoxLayout()
        horizontalLayout2_12.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_12.addWidget(epgname_btn)
        horizontalLayout2_12.addWidget(epgname_lbl)
        horizontalLayout2_12.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_12.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        horizontalLayout3 = QtWidgets.QHBoxLayout()
        horizontalLayout3.addWidget(save_btn)

        verticalLayout = QtWidgets.QVBoxLayout(wid)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addLayout(horizontalLayout2)
        verticalLayout.addLayout(horizontalLayout2_1)
        verticalLayout.addLayout(horizontalLayout2_13)
        verticalLayout.addLayout(horizontalLayout2_2)
        verticalLayout.addLayout(horizontalLayout2_3)
        verticalLayout.addLayout(horizontalLayout2_4)
        verticalLayout.addLayout(horizontalLayout2_5)
        verticalLayout.addLayout(horizontalLayout2_6)
        verticalLayout.addLayout(horizontalLayout2_7)
        verticalLayout.addLayout(horizontalLayout2_8)
        verticalLayout.addLayout(horizontalLayout2_9)
        verticalLayout.addLayout(horizontalLayout2_10)
        verticalLayout.addLayout(horizontalLayout2_11)
        verticalLayout.addLayout(horizontalLayout2_12)
        verticalLayout.addLayout(horizontalLayout3)
        verticalLayout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignTop
        )

        wid.setLayout(verticalLayout)
        chan_win.setCentralWidget(wid)

        do_save_settings = False

        # Settings window
        def save_settings():
            global epg_thread_2, do_save_settings
            settings_old = settings.copy()
            udp_proxy_text = sudp.text()
            udp_proxy_starts = udp_proxy_text.startswith(
                "http://"
            ) or udp_proxy_text.startswith("https://")
            if udp_proxy_text and not udp_proxy_starts:
                udp_proxy_text = "http://" + udp_proxy_text
            if udp_proxy_text:
                if os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
                    os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
            if settings["epgoffset"] != soffset.value():
                if os.path.isfile(str(Path(LOCAL_DIR, "epg.cache"))):
                    os.remove(str(Path(LOCAL_DIR, "epg.cache")))
            if sort_widget.currentIndex() != settings["sort"]:
                if os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
                    os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
            sfld_text = sfld.text()
            HOME_SYMBOL = "~"
            try:
                if "HOME" in os.environ:
                    HOME_SYMBOL = os.environ["HOME"]
            except Exception:
                pass
            try:
                if sfld_text:
                    if sfld_text[0] == "~":
                        sfld_text = sfld_text.replace("~", HOME_SYMBOL, 1)
            except Exception:
                pass

            if settings["epgdays"] != epgdays.value():
                logger.info("EPG days option changed, removing cache")
                if os.path.exists(str(Path(LOCAL_DIR, "epg.cache"))):
                    os.remove(str(Path(LOCAL_DIR, "epg.cache")))

            settings_arr = {
                "m3u": sm3u.text(),
                "epg": sepg.text(),
                "deinterlace": sdei.isChecked(),
                "udp_proxy": udp_proxy_text,
                "save_folder": sfld_text,
                "nocache": supdate.isChecked(),
                "epgoffset": soffset.value(),
                "hwaccel": shwaccel.isChecked(),
                "sort": sort_widget.currentIndex(),
                "cache_secs": scache1.value(),
                "epgdays": epgdays.value(),
                "ua": useragent_choose_2.text(),
                "mpv_options": mpv_options.text(),
                "donotupdateepg": donot_flag.isChecked(),
                "openprevchan": openprevchan_flag.isChecked(),
                "hidempv": hidempv_flag.isChecked(),
                "hideepgpercentage": hideepgpercentage_flag.isChecked(),
                "hideepgfromplaylist": hideepgfromplaylist_flag.isChecked(),
                "multicastoptimization": multicastoptimization_flag.isChecked(),
                "hidebitrateinfo": hidebitrateinfo_flag.isChecked(),
                "styleredefoff": styleredefoff_flag.isChecked(),
                "volumechangestep": volumechangestep_choose.value(),
                "mouseswitchchannels": mouseswitchchannels_flag.isChecked(),
                "autoreconnection": autoreconnection_flag.isChecked(),
                "showplaylistmouse": showplaylistmouse_flag.isChecked(),
                "channellogos": channellogos_select.currentIndex(),
                "nocacheepg": nocacheepg_flag.isChecked(),
                "scrrecnosubfolders": scrrecnosubfolders_flag.isChecked(),
                "hidetvprogram": hidetvprogram_flag.isChecked(),
                "showcontrolsmouse": showcontrolsmouse_flag.isChecked(),
                "catchupenable": catchupenable_flag.isChecked(),
                "flpopacity": flpopacity_input.value(),
                "panelposition": panelposition_choose.currentIndex(),
                "videoaspect": videoaspect_def_choose.currentIndex(),
                "zoom": zoom_def_choose.currentIndex(),
                "panscan": panscan_def_choose.value(),
                "referer": referer_choose.text(),
            }
            if catchupenable_flag.isChecked() != settings_old["catchupenable"]:
                if os.path.exists(str(Path(LOCAL_DIR, "epg.cache"))):
                    os.remove(str(Path(LOCAL_DIR, "epg.cache")))
            settings_file1 = open(
                str(Path(LOCAL_DIR, "settings.json")), "w", encoding="utf8"
            )
            settings_file1.write(json.dumps(settings_arr))
            settings_file1.close()
            settings_win.hide()
            if platform.system() == "Windows" or platform.system() == "Darwin":
                os.chdir(old_pwd)
            if "YUKI_IPTV_IS_APPIMAGE" in os.environ or platform.system() == "Darwin":
                for window in QtWidgets.QApplication.topLevelWidgets():
                    window.close()
            do_save_settings = True
            app.quit()

        wid2 = QtWidgets.QWidget()

        m3u_label = QtWidgets.QLabel("{}:".format(_("M3U / XSPF playlist")))
        update_label = QtWidgets.QLabel("{}:".format(_("Update playlist\nat launch")))
        epg_label = QtWidgets.QLabel("{}:".format(_("TV guide\naddress")))
        dei_label = QtWidgets.QLabel("{}:".format(_("Deinterlace")))
        hwaccel_label = QtWidgets.QLabel("{}:".format(_("Hardware\nacceleration")))
        sort_label = QtWidgets.QLabel("{}:".format(_("Channel\nsort")))
        cache_label = QtWidgets.QLabel("{}:".format(_("Cache")))
        udp_label = QtWidgets.QLabel("{}:".format(_("UDP proxy")))
        fld_label = QtWidgets.QLabel(
            "{}:".format(_("Folder for recordings\nand screenshots"))
        )

        def reset_channel_settings():
            if os.path.isfile(str(Path(LOCAL_DIR, "channelsettings.json"))):
                os.remove(str(Path(LOCAL_DIR, "channelsettings.json")))
            if os.path.isfile(str(Path(LOCAL_DIR, "favouritechannels.json"))):
                os.remove(str(Path(LOCAL_DIR, "favouritechannels.json")))
            if os.path.isfile(str(Path(LOCAL_DIR, "sortchannels.json"))):
                os.remove(str(Path(LOCAL_DIR, "sortchannels.json")))
            save_settings()

        def do_clear_logo_cache():
            logger.info("Clearing channel logos cache...")
            if os.path.isdir(Path(LOCAL_DIR, "logo_cache")):
                channel_logos = os.listdir(Path(LOCAL_DIR, "logo_cache"))
                for channel_logo in channel_logos:
                    if os.path.isfile(Path(LOCAL_DIR, "logo_cache", channel_logo)):
                        os.remove(Path(LOCAL_DIR, "logo_cache", channel_logo))
            logger.info("Channel logos cache cleared!")

        sm3u = QtWidgets.QLineEdit()
        sm3u.setPlaceholderText(_("Path to file or URL"))
        sm3u.setText(settings["m3u"])
        sepg = QtWidgets.QLineEdit()
        sepg.setPlaceholderText(_("Path to file or URL"))
        sepg.setText(
            settings["epg"]
            if not settings["epg"].startswith("^^::MULTIPLE::^^")
            else ""
        )
        sudp = QtWidgets.QLineEdit()
        sudp.setText(settings["udp_proxy"])
        sdei = QtWidgets.QCheckBox()
        sdei.setChecked(settings["deinterlace"])
        shwaccel = QtWidgets.QCheckBox()
        shwaccel.setChecked(settings["hwaccel"])
        supdate = QtWidgets.QCheckBox()
        supdate.setChecked(settings["nocache"])
        sfld = QtWidgets.QLineEdit()
        sfld.setText(settings["save_folder"])
        scache = QtWidgets.QLabel(
            (gettext.ngettext("%d second", "%d seconds", 0) % 0).replace("0 ", "")
        )
        sselect = QtWidgets.QLabel("{}:".format(_("Or select provider")))
        sselect.setStyleSheet("color: #00008B;")
        ssave = QtWidgets.QPushButton(_("Save settings"))
        ssave.setStyleSheet("font-weight: bold; color: green;")
        ssave.clicked.connect(save_settings)
        sreset = QtWidgets.QPushButton(_("Reset channel settings and sorting"))
        sreset.clicked.connect(reset_channel_settings)
        clear_logo_cache = QtWidgets.QPushButton(_("Clear logo cache"))
        clear_logo_cache.clicked.connect(do_clear_logo_cache)
        sort_widget = QtWidgets.QComboBox()
        sort_widget.addItem(_("as in playlist"))
        sort_widget.addItem(_("alphabetical order"))
        sort_widget.addItem(_("reverse alphabetical order"))
        sort_widget.addItem(_("custom"))
        sort_widget.setCurrentIndex(settings["sort"])

        def close_settings():
            settings_win.hide()
            if not win.isVisible():
                if not playlists_win.isVisible():
                    myExitHandler_before()
                    sys.exit(0)

        sclose = QtWidgets.QPushButton(_("Close"))
        sclose.setStyleSheet("color: red;")
        sclose.clicked.connect(close_settings)

        def update_m3u():
            if os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
                os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
            save_settings()

        sm3ufile = QtWidgets.QPushButton()
        sm3ufile.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "file.png"))))
        sm3ufile.clicked.connect(m3u_select)
        sm3uupd = QtWidgets.QPushButton()
        sm3uupd.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "update.png"))))
        sm3uupd.clicked.connect(update_m3u)
        sm3uupd.setToolTip(_("Update"))

        sepgfile = QtWidgets.QPushButton()
        sepgfile.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "file.png"))))
        sepgfile.clicked.connect(epg_select)
        sepgupd = QtWidgets.QPushButton()
        sepgupd.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "update.png"))))
        sepgupd.clicked.connect(force_update_epg_act)
        sepgupd.setToolTip(_("Update"))

        sfolder = QtWidgets.QPushButton()
        sfolder.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "file.png"))))
        sfolder.clicked.connect(save_folder_select)

        soffset = QtWidgets.QDoubleSpinBox()
        soffset.setMinimum(-240)
        soffset.setMaximum(240)
        soffset.setSingleStep(1)
        soffset.setDecimals(1)
        soffset.setValue(settings["epgoffset"])

        scache1 = QtWidgets.QSpinBox()
        scache1.setMinimum(0)
        scache1.setMaximum(120)
        scache1.setValue(settings["cache_secs"])

        epgdays_p = QtWidgets.QLabel(
            (gettext.ngettext("%d day", "%d days", 0) % 0).replace("0 ", "")
        )

        epgdays_label = QtWidgets.QLabel("{}:".format(_("Load EPG for")))

        epgdays = QtWidgets.QSpinBox()
        epgdays.setMinimum(1)
        epgdays.setMaximum(7)
        epgdays.setValue(settings["epgdays"])

        def xtream_select():
            sm3u_text = sm3u.text()
            if sm3u_text.startswith("XTREAM::::::::::::::"):
                sm3u_text_sp = sm3u_text.split("::::::::::::::")
                xtr_username_input.setText(sm3u_text_sp[1])
                xtr_password_input.setText(sm3u_text_sp[2])
                xtr_url_input.setText(sm3u_text_sp[3])
            moveWindowToCenter(xtream_win)
            xtream_win.show()

        def xtream_select_1():
            m3u_edit_1_text = m3u_edit_1.text()
            if m3u_edit_1_text.startswith("XTREAM::::::::::::::"):
                m3u_edit_1_text_sp = m3u_edit_1_text.split("::::::::::::::")
                xtr_username_input_2.setText(m3u_edit_1_text_sp[1])
                xtr_password_input_2.setText(m3u_edit_1_text_sp[2])
                xtr_url_input_2.setText(m3u_edit_1_text_sp[3])
            moveWindowToCenter(xtream_win_2)
            xtream_win_2.show()

        useragent_lbl_2 = QtWidgets.QLabel("{}:".format(_("User agent")))
        referer_lbl = QtWidgets.QLabel(_("HTTP Referer:"))
        referer_choose = QtWidgets.QLineEdit()
        referer_choose.setText(settings["referer"])
        useragent_choose_2 = QtWidgets.QLineEdit()
        useragent_choose_2.setText(settings["ua"])

        mpv_label = QtWidgets.QLabel(
            "{} ({}):".format(
                _("mpv options"),
                '<a href="' + MPV_OPTIONS_LINK + '">{}</a>'.format(_("list")),
            )
        )
        mpv_label.setOpenExternalLinks(True)
        mpv_label.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        mpv_options = QtWidgets.QLineEdit()
        mpv_options.setText(settings["mpv_options"])
        donot_label = QtWidgets.QLabel("{}:".format(_("Do not update\nEPG at boot")))
        donot_flag = QtWidgets.QCheckBox()
        donot_flag.setChecked(settings["donotupdateepg"])

        openprevchan_label = QtWidgets.QLabel(
            "{}:".format(_("Open previous channel\nat startup"))
        )
        hidempv_label = QtWidgets.QLabel("{}:".format(_("Hide mpv panel")))
        hideepgpercentage_label = QtWidgets.QLabel(
            "{}:".format(_("Hide EPG percentage"))
        )
        hideepgfromplaylist_label = QtWidgets.QLabel(
            "{}:".format(_("Hide EPG from playlist"))
        )
        multicastoptimization_label = QtWidgets.QLabel(
            "{}:".format(_("Multicast optimization"))
        )
        hidebitrateinfo_label = QtWidgets.QLabel(
            "{}:".format(_("Hide bitrate / video info"))
        )
        styleredefoff_label = QtWidgets.QLabel(
            "{}:".format(_("Enable styles redefinition"))
        )
        volumechangestep_label = QtWidgets.QLabel("{}:".format(_("Volume change step")))
        volumechangestep_percent = QtWidgets.QLabel("%")

        openprevchan_flag = QtWidgets.QCheckBox()
        openprevchan_flag.setChecked(settings["openprevchan"])

        hidempv_flag = QtWidgets.QCheckBox()
        hidempv_flag.setChecked(settings["hidempv"])

        hideepgpercentage_flag = QtWidgets.QCheckBox()
        hideepgpercentage_flag.setChecked(settings["hideepgpercentage"])

        hideepgfromplaylist_flag = QtWidgets.QCheckBox()
        hideepgfromplaylist_flag.setChecked(settings["hideepgfromplaylist"])

        multicastoptimization_flag = QtWidgets.QCheckBox()
        multicastoptimization_flag.setChecked(settings["multicastoptimization"])

        hidebitrateinfo_flag = QtWidgets.QCheckBox()
        hidebitrateinfo_flag.setChecked(settings["hidebitrateinfo"])

        styleredefoff_flag = QtWidgets.QCheckBox()
        styleredefoff_flag.setChecked(settings["styleredefoff"])

        volumechangestep_choose = QtWidgets.QSpinBox()
        volumechangestep_choose.setMinimum(1)
        volumechangestep_choose.setMaximum(50)
        volumechangestep_choose.setValue(settings["volumechangestep"])

        flpopacity_label = QtWidgets.QLabel("{}:".format(_("Floating panels opacity")))
        flpopacity_input = QtWidgets.QDoubleSpinBox()
        flpopacity_input.setMinimum(0.01)
        flpopacity_input.setMaximum(1)
        flpopacity_input.setSingleStep(0.1)
        flpopacity_input.setDecimals(2)
        flpopacity_input.setValue(settings["flpopacity"])

        panelposition_label = QtWidgets.QLabel(
            "{}:".format(_("Floating panel\nposition"))
        )
        panelposition_choose = QtWidgets.QComboBox()
        panelposition_choose.addItem(_("Right"))
        panelposition_choose.addItem(_("Left"))
        panelposition_choose.setCurrentIndex(settings["panelposition"])

        mouseswitchchannels_label = QtWidgets.QLabel(
            "{}:".format(_("Switch channels with\nthe mouse wheel"))
        )
        autoreconnection_label = QtWidgets.QLabel(
            "{}:".format(_("Automatic\nreconnection"))
        )
        defaultchangevol_label = QtWidgets.QLabel(
            "({})".format(_("by default:\nchange volume"))
        )
        defaultchangevol_label.setStyleSheet("color:blue")
        mouseswitchchannels_flag = QtWidgets.QCheckBox()
        mouseswitchchannels_flag.setChecked(settings["mouseswitchchannels"])
        autoreconnection_flag = QtWidgets.QCheckBox()
        autoreconnection_flag.setChecked(settings["autoreconnection"])

        # Mark option as experimental
        autoreconnection_flag.setToolTip(
            _("WARNING: experimental function, working with problems")
        )
        autoreconnection_label.setToolTip(
            _("WARNING: experimental function, working with problems")
        )
        autoreconnection_label.setStyleSheet("color: #cf9e17")

        showplaylistmouse_label = QtWidgets.QLabel(
            "{}:".format(_("Show playlist\non mouse move"))
        )
        showplaylistmouse_flag = QtWidgets.QCheckBox()
        showplaylistmouse_flag.setChecked(settings["showplaylistmouse"])
        showcontrolsmouse_label = QtWidgets.QLabel(
            "{}:".format(_("Show controls\non mouse move"))
        )
        showcontrolsmouse_flag = QtWidgets.QCheckBox()
        showcontrolsmouse_flag.setChecked(settings["showcontrolsmouse"])

        channellogos_label = QtWidgets.QLabel("{}:".format(_("Channel logos")))
        channellogos_select = QtWidgets.QComboBox()
        channellogos_select.addItem(_("Prefer M3U"))
        channellogos_select.addItem(_("Prefer EPG"))
        channellogos_select.addItem(_("Do not load from EPG"))
        channellogos_select.addItem(_("Do not load any logos"))
        channellogos_select.setCurrentIndex(settings["channellogos"])

        nocacheepg_label = QtWidgets.QLabel("{}:".format(_("Do not cache EPG")))
        nocacheepg_flag = QtWidgets.QCheckBox()
        nocacheepg_flag.setChecked(settings["nocacheepg"])

        scrrecnosubfolders_label = QtWidgets.QLabel(
            "{}:".format(_("Do not create screenshots\nand recordings subfolders"))
        )
        scrrecnosubfolders_flag = QtWidgets.QCheckBox()
        scrrecnosubfolders_flag.setChecked(settings["scrrecnosubfolders"])

        hidetvprogram_label = QtWidgets.QLabel(
            "{}:".format(_("Hide the current television program"))
        )
        hidetvprogram_flag = QtWidgets.QCheckBox()
        hidetvprogram_flag.setChecked(settings["hidetvprogram"])

        videoaspectdef_label = QtWidgets.QLabel("{}:".format(_("Aspect ratio")))
        zoomdef_label = QtWidgets.QLabel("{}:".format(_("Scale / Zoom")))
        panscan_def_label = QtWidgets.QLabel("{}:".format(_("Pan and scan")))

        videoaspect_def_choose = QtWidgets.QComboBox()
        for videoaspect_var_1 in videoaspect_vars:
            videoaspect_def_choose.addItem(videoaspect_var_1)

        zoom_def_choose = QtWidgets.QComboBox()
        for zoom_var_1 in zoom_vars:
            zoom_def_choose.addItem(zoom_var_1)

        panscan_def_choose = QtWidgets.QDoubleSpinBox()
        panscan_def_choose.setMinimum(0)
        panscan_def_choose.setMaximum(1)
        panscan_def_choose.setSingleStep(0.1)
        panscan_def_choose.setDecimals(1)

        videoaspect_def_choose.setCurrentIndex(settings["videoaspect"])
        zoom_def_choose.setCurrentIndex(settings["zoom"])
        panscan_def_choose.setValue(settings["panscan"])

        catchupenable_label = QtWidgets.QLabel("{}:".format(_("Enable catchup")))
        catchupenable_flag = QtWidgets.QCheckBox()
        catchupenable_flag.setChecked(settings["catchupenable"])

        tabs = QtWidgets.QTabWidget()

        tab_main = QtWidgets.QWidget()
        tab_video = QtWidgets.QWidget()
        tab_network = QtWidgets.QWidget()
        tab_other = QtWidgets.QWidget()
        tab_gui = QtWidgets.QWidget()
        tab_actions = QtWidgets.QWidget()
        tab_catchup = QtWidgets.QWidget()
        tab_debug = QtWidgets.QWidget()
        tab_epg = QtWidgets.QWidget()

        tabs.addTab(tab_main, _("Main"))
        tabs.addTab(tab_video, _("Video"))
        tabs.addTab(tab_network, _("Network"))
        tabs.addTab(tab_gui, _("GUI"))
        tabs.addTab(tab_actions, _("Actions"))
        tabs.addTab(tab_catchup, _("Catchup"))
        tabs.addTab(tab_epg, _("EPG"))
        tabs.addTab(tab_other, _("Other"))
        tabs.addTab(tab_debug, _("Debug"))

        tab_main.layout = QtWidgets.QGridLayout()
        tab_main.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_main.layout.addWidget(fld_label, 0, 0)
        tab_main.layout.addWidget(sfld, 0, 1)
        tab_main.layout.addWidget(sfolder, 0, 2)
        tab_main.layout.addWidget(scrrecnosubfolders_label, 1, 0)
        tab_main.layout.addWidget(scrrecnosubfolders_flag, 1, 1)
        tab_main.layout.addWidget(sort_label, 2, 0)
        tab_main.layout.addWidget(sort_widget, 2, 1)
        # tab_main.layout.addWidget(update_label, 3, 0)
        # tab_main.layout.addWidget(supdate, 3, 1)
        tab_main.layout.addWidget(openprevchan_label, 3, 0)
        tab_main.layout.addWidget(openprevchan_flag, 3, 1)
        tab_main.setLayout(tab_main.layout)

        tab_video.layout = QtWidgets.QGridLayout()
        tab_video.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_video.layout.addWidget(dei_label, 0, 0)
        tab_video.layout.addWidget(sdei, 0, 1)
        tab_video.layout.addWidget(hwaccel_label, 1, 0)
        tab_video.layout.addWidget(shwaccel, 1, 1)
        tab_video.layout.addWidget(videoaspectdef_label, 2, 0)
        tab_video.layout.addWidget(videoaspect_def_choose, 2, 1)
        tab_video.layout.addWidget(zoomdef_label, 3, 0)
        tab_video.layout.addWidget(zoom_def_choose, 3, 1)
        tab_video.layout.addWidget(panscan_def_label, 4, 0)
        tab_video.layout.addWidget(panscan_def_choose, 4, 1)
        tab_video.setLayout(tab_video.layout)

        tab_network.layout = QtWidgets.QGridLayout()
        tab_network.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_network.layout.addWidget(udp_label, 0, 0)
        tab_network.layout.addWidget(sudp, 0, 1)
        tab_network.layout.addWidget(cache_label, 1, 0)
        tab_network.layout.addWidget(scache1, 1, 1)
        tab_network.layout.addWidget(scache, 1, 2)
        tab_network.layout.addWidget(useragent_lbl_2, 2, 0)
        tab_network.layout.addWidget(useragent_choose_2, 2, 1)
        tab_network.layout.addWidget(referer_lbl, 3, 0)
        tab_network.layout.addWidget(referer_choose, 3, 1)
        tab_network.layout.addWidget(multicastoptimization_label, 4, 0)
        tab_network.layout.addWidget(multicastoptimization_flag, 4, 1)
        tab_network.setLayout(tab_network.layout)

        tab_gui.layout = QtWidgets.QGridLayout()
        tab_gui.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_gui.layout.addWidget(panelposition_label, 0, 0)
        tab_gui.layout.addWidget(panelposition_choose, 0, 1)
        tab_gui.layout.addWidget(hideepgfromplaylist_label, 1, 0)
        tab_gui.layout.addWidget(hideepgfromplaylist_flag, 1, 1)
        tab_gui.layout.addWidget(hideepgpercentage_label, 2, 0)
        tab_gui.layout.addWidget(hideepgpercentage_flag, 2, 1)
        tab_gui.layout.addWidget(hidebitrateinfo_label, 3, 0)
        tab_gui.layout.addWidget(hidebitrateinfo_flag, 3, 1)
        tab_gui.layout.addWidget(hidetvprogram_label, 4, 0)
        tab_gui.layout.addWidget(hidetvprogram_flag, 4, 1)
        tab_gui.setLayout(tab_gui.layout)

        tab_actions.layout = QtWidgets.QGridLayout()
        tab_actions.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_actions.layout.addWidget(mouseswitchchannels_label, 0, 0)
        tab_actions.layout.addWidget(mouseswitchchannels_flag, 0, 1)
        tab_actions.layout.addWidget(defaultchangevol_label, 1, 0)
        tab_actions.layout.addWidget(showplaylistmouse_label, 3, 0)
        tab_actions.layout.addWidget(showplaylistmouse_flag, 3, 1)
        tab_actions.layout.addWidget(showcontrolsmouse_label, 4, 0)
        tab_actions.layout.addWidget(showcontrolsmouse_flag, 4, 1)
        tab_actions.setLayout(tab_actions.layout)

        tab_catchup.layout = QtWidgets.QGridLayout()
        tab_catchup.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_catchup.layout.addWidget(catchupenable_label, 0, 0)
        tab_catchup.layout.addWidget(catchupenable_flag, 0, 1)
        tab_catchup.setLayout(tab_catchup.layout)

        tab_epg.layout = QtWidgets.QGridLayout()
        tab_epg.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        # tab_epg.layout.addWidget(epgdays_label, 0, 0)
        # tab_epg.layout.addWidget(epgdays, 0, 1)
        # tab_epg.layout.addWidget(epgdays_p, 0, 2)
        tab_epg.layout.addWidget(donot_label, 0, 0)
        tab_epg.layout.addWidget(donot_flag, 0, 1)
        tab_epg.layout.addWidget(nocacheepg_label, 1, 0)
        tab_epg.layout.addWidget(nocacheepg_flag, 1, 1)
        tab_epg.setLayout(tab_epg.layout)

        tab_other.layout = QtWidgets.QGridLayout()
        tab_other.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_other.layout.addWidget(mpv_label, 0, 0)
        tab_other.layout.addWidget(mpv_options, 0, 1)
        tab_other.layout.addWidget(hidempv_label, 1, 0)
        tab_other.layout.addWidget(hidempv_flag, 1, 1)
        tab_other.layout.addWidget(channellogos_label, 2, 0)
        tab_other.layout.addWidget(channellogos_select, 2, 1)
        tab_other.layout.addWidget(volumechangestep_label, 3, 0)
        tab_other.layout.addWidget(volumechangestep_choose, 3, 1)
        tab_other.layout.addWidget(volumechangestep_percent, 3, 2)
        tab_other.setLayout(tab_other.layout)

        tab_debug_warning = QtWidgets.QLabel(
            _("WARNING: experimental function, working with problems")
        )
        tab_debug_warning.setStyleSheet("color: #cf9e17")

        tab_debug_widget = QtWidgets.QWidget()
        tab_debug_layout = QtWidgets.QGridLayout()
        tab_debug_layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_debug_layout.addWidget(styleredefoff_label, 0, 0)
        tab_debug_layout.addWidget(styleredefoff_flag, 0, 1)
        tab_debug_layout.addWidget(autoreconnection_label, 1, 0)
        tab_debug_layout.addWidget(autoreconnection_flag, 1, 1)
        tab_debug_widget.setLayout(tab_debug_layout)

        tab_debug.layout = QtWidgets.QVBoxLayout()
        tab_debug.layout.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        tab_debug.layout.addWidget(tab_debug_warning)
        tab_debug.layout.addWidget(tab_debug_widget)
        tab_debug.setLayout(tab_debug.layout)

        grid = QtWidgets.QVBoxLayout()
        grid.addWidget(tabs)

        grid2 = QtWidgets.QGridLayout()
        grid2.setSpacing(0)

        ssaveclose = QtWidgets.QWidget()
        ssaveclose_layout = QtWidgets.QHBoxLayout()
        ssaveclose_layout.addWidget(ssave)
        ssaveclose_layout.addWidget(sclose)
        ssaveclose.setLayout(ssaveclose_layout)

        sbtns = QtWidgets.QWidget()
        sbtns_layout = QtWidgets.QHBoxLayout()
        sbtns_layout.addWidget(sreset)
        sbtns_layout.addWidget(clear_logo_cache)
        sbtns.setLayout(sbtns_layout)

        grid2.addWidget(ssaveclose, 2, 1)
        grid2.addWidget(sbtns, 3, 1)

        layout2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(grid)
        layout2.addLayout(grid2)

        wid2.setLayout(layout2)
        settings_win.scroll.setWidget(wid2)

        def xtream_save_btn_action():
            if (
                xtr_username_input.text()
                and xtr_password_input.text()
                and xtr_url_input.text()
            ):
                xtream_gen_url = "XTREAM::::::::::::::" + "::::::::::::::".join(
                    [
                        xtr_username_input.text(),
                        xtr_password_input.text(),
                        xtr_url_input.text(),
                    ]
                )
                sm3u.setText(xtream_gen_url)
            xtream_win.hide()

        def xtream_save_btn_action_2():
            if (
                xtr_username_input_2.text()
                and xtr_password_input_2.text()
                and xtr_url_input_2.text()
            ):
                xtream_gen_url_2 = "XTREAM::::::::::::::" + "::::::::::::::".join(
                    [
                        xtr_username_input_2.text(),
                        xtr_password_input_2.text(),
                        xtr_url_input_2.text(),
                    ]
                )
                m3u_edit_1.setText(xtream_gen_url_2)
            xtream_win_2.hide()

        wid3 = QtWidgets.QWidget()
        wid4 = QtWidgets.QWidget()

        save_btn_xtream = QtWidgets.QPushButton(_("Save"))
        save_btn_xtream.setStyleSheet("font-weight: bold; color: green;")
        save_btn_xtream.clicked.connect(xtream_save_btn_action)
        xtr_username_input = QtWidgets.QLineEdit()
        xtr_password_input = QtWidgets.QLineEdit()
        xtr_url_input = QtWidgets.QLineEdit()

        layout34 = QtWidgets.QGridLayout()
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_("Username"))), 0, 0)
        layout34.addWidget(xtr_username_input, 0, 1)
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_("Password"))), 1, 0)
        layout34.addWidget(xtr_password_input, 1, 1)
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_("URL"))), 2, 0)
        layout34.addWidget(xtr_url_input, 2, 1)
        layout34.addWidget(save_btn_xtream, 3, 1)
        wid3.setLayout(layout34)

        save_btn_xtream_2 = QtWidgets.QPushButton(_("Save"))
        save_btn_xtream_2.setStyleSheet("font-weight: bold; color: green;")
        save_btn_xtream_2.clicked.connect(xtream_save_btn_action_2)
        xtr_username_input_2 = QtWidgets.QLineEdit()
        xtr_password_input_2 = QtWidgets.QLineEdit()
        xtr_url_input_2 = QtWidgets.QLineEdit()

        layout35 = QtWidgets.QGridLayout()
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_("Username"))), 0, 0)
        layout35.addWidget(xtr_username_input_2, 0, 1)
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_("Password"))), 1, 0)
        layout35.addWidget(xtr_password_input_2, 1, 1)
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_("URL"))), 2, 0)
        layout35.addWidget(xtr_url_input_2, 2, 1)
        layout35.addWidget(save_btn_xtream_2, 3, 1)
        wid4.setLayout(layout35)

        xtream_win.setCentralWidget(wid3)
        xtream_win_2.setCentralWidget(wid4)

        wid5 = QtWidgets.QWidget()
        layout36 = QtWidgets.QGridLayout()
        wid5.setLayout(layout36)
        streaminfo_win.setCentralWidget(wid5)

        def show_license():
            if not license_win.isVisible():
                moveWindowToCenter(license_win)
                license_win.show()
            else:
                license_win.hide()

        with open(
            str(
                Path(
                    "..", "..", "share", "yuki-iptv", "licenses", "GPL-3.0-or-later.txt"
                )
            ),
            "r",
            encoding="utf8",
        ) as license_gpl_file:
            license_gpl_str = license_gpl_file.read()

        with open(
            str(Path("..", "..", "share", "yuki-iptv", "licenses", "CC-BY-4.0.txt")),
            "r",
            encoding="utf8",
        ) as license_ccby_file:
            license_ccby_str = license_ccby_file.read()

        license_str = (
            "This program is free software: you can redistribute it and/or modify it"
            " under the terms of the GNU General Public License as published by the"
            " Free Software Foundation, either version 3 of the License"
            ", or (at your option) any later version."
            "\n\n"
            "This program is distributed in the hope that it will be useful"
            ", but WITHOUT ANY WARRANTY; without even the implied warranty"
            " of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE."
            " See the GNU General Public License for more details."
            "\n\n"
            "------------------------------------\n\n"
            "The Font Awesome pictograms are licensed under the CC BY 4.0 License.\n"
            "https://fontawesome.com/\n"
            "https://creativecommons.org/licenses/by/4.0/\n\n"
            "------------------------------------"
            "\n\n"
            "" + license_gpl_str + ""
            "\n\n"
            "------------------------------------\n\n"
            "" + license_ccby_str
        )

        licensebox = QtWidgets.QPlainTextEdit()
        licensebox.setReadOnly(True)
        licensebox.setPlainText(license_str)

        licensebox_close_btn = QtWidgets.QPushButton()
        licensebox_close_btn.setText(_("Close"))
        licensebox_close_btn.clicked.connect(license_win.close)

        licensewin_widget = QtWidgets.QWidget()
        licensewin_layout = QtWidgets.QVBoxLayout()
        licensewin_layout.addWidget(licensebox)
        licensewin_layout.addWidget(licensebox_close_btn)
        licensewin_widget.setLayout(licensewin_layout)
        license_win.setCentralWidget(licensewin_widget)

        textbox = QtWidgets.QTextBrowser()
        textbox.setOpenExternalLinks(True)
        textbox.setReadOnly(True)

        class Communicate(QtCore.QObject):
            winPosition = False
            winPosition2 = False
            do_play_args = ()
            j_save = None
            comboboxIndex = -1
            mainThread = Signal(type(lambda x: None))
            mainThread_partial = Signal(type(partial(int, 2)))

        def exInMainThread_partial(m_func_2):
            comm_instance.mainThread_partial.emit(m_func_2)

        def comm_instance_main_thread(th_func):
            th_func()

        comm_instance = Communicate()
        comm_instance.mainThread.connect(comm_instance_main_thread)
        comm_instance.mainThread_partial.connect(comm_instance_main_thread)

        license_btn = QtWidgets.QPushButton()
        license_btn.setText(_("License"))
        license_btn.clicked.connect(show_license)

        def aboutqt_show():
            QtWidgets.QMessageBox.aboutQt(QtWidgets.QWidget(), MAIN_WINDOW_TITLE)
            help_win.raise_()
            help_win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
            help_win.activateWindow()

        aboutqt_btn = QtWidgets.QPushButton()
        aboutqt_btn.setText(_("About Qt"))
        aboutqt_btn.clicked.connect(aboutqt_show)

        close_btn = QtWidgets.QPushButton()
        close_btn.setText(_("Close"))
        close_btn.clicked.connect(help_win.close)

        helpwin_widget_btns = QtWidgets.QWidget()
        helpwin_widget_btns_layout = QtWidgets.QHBoxLayout()
        helpwin_widget_btns_layout.addWidget(license_btn)
        helpwin_widget_btns_layout.addWidget(aboutqt_btn)
        helpwin_widget_btns_layout.addWidget(close_btn)
        helpwin_widget_btns.setLayout(helpwin_widget_btns_layout)

        helpwin_widget = QtWidgets.QWidget()
        helpwin_layout = QtWidgets.QVBoxLayout()
        helpwin_layout.addWidget(textbox)
        helpwin_layout.addWidget(helpwin_widget_btns)
        helpwin_widget.setLayout(helpwin_layout)
        help_win.setCentralWidget(helpwin_widget)

        btn_update = QtWidgets.QPushButton()
        btn_update.hide()

        def shortcuts_table_clicked(row1, column1):
            if column1 == 1:  # keybind
                sc1_text = shortcuts_table.item(row1, column1).text()
                keyseq.setKeySequence(sc1_text)
                YukiData.selected_shortcut_row = row1
                keyseq.setFocus()
                moveWindowToCenter(shortcuts_win_2)
                shortcuts_win_2.show()

        shortcuts_table.cellDoubleClicked.connect(shortcuts_table_clicked)

        def get_widget_item(widget_str):
            twi = QtWidgets.QTableWidgetItem(widget_str)
            twi.setFlags(twi.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            return twi

        def show_shortcuts():
            if not shortcuts_win.isVisible():
                # start
                shortcuts_table.setRowCount(len(main_keybinds))
                keybind_i = -1
                for keybind in main_keybinds:
                    keybind_i += 1
                    shortcuts_table.setItem(
                        keybind_i,
                        0,
                        get_widget_item(main_keybinds_translations[keybind]),
                    )
                    if isinstance(main_keybinds[keybind], str):
                        keybind_str = main_keybinds[keybind]
                    else:
                        keybind_str = QtGui.QKeySequence(
                            main_keybinds[keybind]
                        ).toString()
                    kbd_widget = get_widget_item(keybind_str)
                    kbd_widget.setToolTip(_("Double click to change"))
                    shortcuts_table.setItem(keybind_i, 1, kbd_widget)
                shortcuts_table.resizeColumnsToContents()
                # end
                moveWindowToCenter(shortcuts_win)
                shortcuts_win.show()
            else:
                shortcuts_win.hide()

        def show_settings():
            if not settings_win.isVisible():
                moveWindowToCenter(settings_win)
                settings_win.show()
            else:
                settings_win.hide()

        def show_help():
            if not help_win.isVisible():
                moveWindowToCenter(help_win)
                help_win.show()
            else:
                help_win.hide()

        def show_sort():
            if not sort_win.isVisible():
                moveWindowToCenter(sort_win)
                sort_win.show()
            else:
                sort_win.hide()

        def show_playlists():
            if not playlists_win.isVisible():
                playlists_list.clear()
                playlists_data.playlists_used = playlists_saved
                for item2 in playlists_data.playlists_used:
                    playlists_list.addItem(item2)
                moveWindowToCenter(playlists_win)
                playlists_win.show()
            else:
                playlists_win.hide()

        def reload_playlist():
            logger.info("Reloading playlist...")
            if os.path.isfile(str(Path(LOCAL_DIR, "playlistcache.json"))):
                os.remove(str(Path(LOCAL_DIR, "playlistcache.json")))
            save_settings()

        def playlists_selected():
            try:
                prov_data = playlists_data.playlists_used[
                    playlists_list.currentItem().text()
                ]
                prov_m3u = prov_data["m3u"]
                prov_epg = ""
                prov_offset = 0
                if "epg" in prov_data:
                    prov_epg = prov_data["epg"]
                if "epgoffset" in prov_data:
                    prov_offset = prov_data["epgoffset"]
                sm3u.setText(prov_m3u)
                sepg.setText(
                    prov_epg if not prov_epg.startswith("^^::MULTIPLE::^^") else ""
                )
                soffset.setValue(prov_offset)
                playlists_save_json()
                playlists_win.hide()
                playlists_win_edit.hide()
                save_settings()
            except Exception:
                pass

        def playlists_save_json():
            playlists_json_save(playlists_data.playlists_used)

        def playlists_edit_do(ignore0=False):
            try:
                currentItem_text = playlists_list.currentItem().text()
            except Exception:
                currentItem_text = ""
            if ignore0:
                name_edit_1.setText("")
                m3u_edit_1.setText("")
                epg_edit_1.setText("")
                soffset_1.setValue(0)
                playlists_data.oldName = ""
                moveWindowToCenter(playlists_win_edit)
                playlists_win_edit.show()
            else:
                if currentItem_text:
                    item_m3u = playlists_data.playlists_used[currentItem_text]["m3u"]
                    try:
                        item_epg = playlists_data.playlists_used[currentItem_text][
                            "epg"
                        ]
                    except Exception:
                        item_epg = ""
                    try:
                        item_offset = playlists_data.playlists_used[currentItem_text][
                            "epgoffset"
                        ]
                    except Exception:
                        item_offset = 0
                    name_edit_1.setText(currentItem_text)
                    m3u_edit_1.setText(item_m3u)
                    epg_edit_1.setText(item_epg)
                    soffset_1.setValue(item_offset)
                    playlists_data.oldName = currentItem_text
                    moveWindowToCenter(playlists_win_edit)
                    playlists_win_edit.show()

        def playlists_delete_do():
            resettodefaults_btn_clicked_msg_1 = QtWidgets.QMessageBox.question(
                None,
                MAIN_WINDOW_TITLE,
                _("Are you sure?"),
                QtWidgets.QMessageBox.StandardButton.Yes
                | QtWidgets.QMessageBox.StandardButton.No,
                QtWidgets.QMessageBox.StandardButton.Yes,
            )
            if (
                resettodefaults_btn_clicked_msg_1
                == QtWidgets.QMessageBox.StandardButton.Yes
            ):
                try:
                    currentItem_text = playlists_list.currentItem().text()
                except Exception:
                    currentItem_text = ""
                if currentItem_text:
                    playlists_list.takeItem(playlists_list.currentRow())
                    playlists_data.playlists_used.pop(currentItem_text)
                    playlists_save_json()

        def playlists_add_do():
            playlists_edit_do(True)

        playlists_list.itemDoubleClicked.connect(playlists_selected)
        playlists_select.clicked.connect(playlists_selected)
        playlists_add.clicked.connect(playlists_add_do)
        playlists_edit.clicked.connect(playlists_edit_do)
        playlists_delete.clicked.connect(playlists_delete_do)
        playlists_settings.clicked.connect(show_settings)

        fullscreen = False

        def set_mpv_osc(osc_value):
            if mpv_osc_enabled:
                if osc_value != YukiData.osc:
                    YukiData.osc = osc_value
                    player.osc = osc_value

        mpv_osc_enabled = True

        def init_mpv_player():
            global player, mpv_osc_enabled
            mpv_loglevel = "info" if loglevel.lower() != "debug" else "debug"
            mpv_osc_enabled = True
            if "osc" in options:
                # To prevent 'multiple values for keyword argument'!
                mpv_osc_enabled = options.pop("osc") != "no"
            if not enable_libmpv_render_context:
                options["wid"] = str(int(win.container.winId()))
            else:
                options["vo"] = "null"
            try:
                player = mpv.MPV(
                    **options,
                    osc=mpv_osc_enabled,
                    script_opts="osc-layout=box,osc-seekbarstyle=bar,"
                    "osc-deadzonesize=0,osc-minmousemove=3",
                    ytdl=True,
                    log_handler=my_log,
                    loglevel=mpv_loglevel,
                )
            except Exception:
                logger.warning("mpv init with ytdl failed")
                try:
                    player = mpv.MPV(
                        **options,
                        osc=mpv_osc_enabled,
                        script_opts="osc-layout=box,osc-seekbarstyle=bar,"
                        "osc-deadzonesize=0,osc-minmousemove=3",
                        log_handler=my_log,
                        loglevel=mpv_loglevel,
                    )
                except Exception:
                    logger.warning("mpv init with osc failed")
                    player = mpv.MPV(
                        **options,
                        log_handler=my_log,
                        loglevel=mpv_loglevel,
                    )
            if settings["hidempv"]:
                try:
                    set_mpv_osc(False)
                except Exception:
                    logger.warning("player.osc set failed")

            if enable_libmpv_render_context:
                container_layout = QtWidgets.QVBoxLayout()
                container_layout.setContentsMargins(0, 0, 0, 0)
                container_layout.setSpacing(0)
                mpv_opengl_widget = MPVOpenGLWidget(app, player)
                container_layout.addWidget(mpv_opengl_widget)
                win.container.setLayout(container_layout)

            try:
                player["force-seekable"] = True
            except Exception:
                pass
            if not settings["hwaccel"]:
                try:
                    player["x11-bypass-compositor"] = "yes"
                except Exception:
                    pass
            try:
                player["network-timeout"] = 5
            except Exception:
                pass

            try:
                player.title = MAIN_WINDOW_TITLE
            except Exception:
                pass

            try:
                player["audio-client-name"] = "yuki-iptv"
            except Exception:
                logger.warning("mpv audio-client-name set failed")

            try:
                mpv_version = player.mpv_version
                if not mpv_version.startswith("mpv "):
                    mpv_version = "mpv " + mpv_version
            except Exception:
                mpv_version = "unknown mpv version"

            logger.info(f"Using {mpv_version}")

            textbox.setText(
                format_about_text(
                    _(
                        "yuki-iptv {}\n\n© 2021, 2022 Astroncia\n© {} Ame-chan-angel\n"
                        "https://github.com/Ame-chan-angel\n\nIPTV player\n\nIcons by"
                        " Font Awesome ( https://fontawesome.com/ )\nIcons licensed"
                        " under the CC BY 4.0 License\n"
                        "( https://creativecommons.org/licenses/by/4.0/ )"
                    )
                    .format(APP_VERSION, COPYRIGHT_YEAR)
                    .replace("©", "Copyright ©")
                )
            )

            if settings["cache_secs"] != 0:
                try:
                    player["demuxer-readahead-secs"] = settings["cache_secs"]
                    logger.info(f'Demuxer cache set to {settings["cache_secs"]}s')
                except Exception:
                    pass
                try:
                    player["cache-secs"] = settings["cache_secs"]
                    logger.info(f'Cache set to {settings["cache_secs"]}s')
                except Exception:
                    pass
            else:
                logger.info("Using default cache settings")
            player.user_agent = def_user_agent
            if settings["referer"]:
                player.http_header_fields = f"Referer: {settings['referer']}"
                logger.info(f"HTTP referer: '{settings['referer']}'")
            else:
                logger.info("No HTTP referer set up")
            mpv_override_volume(100)
            player.loop = True

            aot_action1 = None
            try:
                aot_action1 = populate_menubar(
                    0,
                    win.menu_bar_qt,
                    win,
                    player.track_list,
                    playing_chan,
                    get_keybind,
                )
                populate_menubar(
                    1,
                    right_click_menu,
                    win,
                    player.track_list,
                    playing_chan,
                    get_keybind,
                )
            except Exception:
                logger.warning("populate_menubar failed")
                show_exception("populate_menubar failed\n\n" + traceback.format_exc())
            redraw_menubar()

            @player.event_callback("file-loaded")
            def file_loaded_2(event):
                file_loaded_callback()

            @player.event_callback("end_file")
            def ready_handler_2(event):
                if event["event"]["error"] != 0:
                    end_file_error_callback()
                else:
                    end_file_callback()

            if not enable_libmpv_render_context:

                @player.on_key_press("MBTN_RIGHT")
                def my_mouse_right():
                    my_mouse_right_callback()

                @player.on_key_press("MBTN_LEFT")
                def my_mouse_left():
                    my_mouse_left_callback()

                @player.on_key_press("MBTN_LEFT_DBL")
                def my_leftdbl_binding():
                    mpv_fullscreen()

                @player.on_key_press("MBTN_FORWARD")
                def my_forward_binding():
                    next_channel()

                @player.on_key_press("MBTN_BACK")
                def my_back_binding():
                    prev_channel()

                @player.on_key_press("WHEEL_UP")
                def my_up_binding():
                    my_up_binding_execute()

                @player.on_key_press("WHEEL_DOWN")
                def my_down_binding():
                    my_down_binding_execute()

            @idle_function
            def pause_handler(unused=None, unused2=None, unused3=None):
                global event_handler
                try:
                    if not player.pause:
                        label3.setIcon(
                            QtGui.QIcon(
                                str(Path("yuki_iptv", ICONS_FOLDER, "pause.png"))
                            )
                        )
                        label3.setToolTip(_("Pause"))
                    else:
                        label3.setIcon(
                            QtGui.QIcon(
                                str(Path("yuki_iptv", ICONS_FOLDER, "play.png"))
                            )
                        )
                        label3.setToolTip(_("Play"))
                    if event_handler:
                        try:
                            event_handler.on_playpause()
                        except Exception:
                            pass
                except Exception:
                    pass

            player.observe_property("pause", pause_handler)

            def yuki_track_set(track, type1):
                global player_tracks
                logger.info(f"Set {type1} track to {track}")
                if playing_chan not in player_tracks:
                    player_tracks[playing_chan] = {}
                if type1 == "vid":
                    player.vid = track
                    player_tracks[playing_chan]["vid"] = track
                elif type1 == "aid":
                    player.aid = track
                    player_tracks[playing_chan]["aid"] = track
                elif type1 == "sid":
                    player.sid = track
                    player_tracks[playing_chan]["sid"] = track

            init_menubar_player(
                player,
                mpv_play,
                mpv_stop,
                prev_channel,
                next_channel,
                mpv_fullscreen,
                showhideeverything,
                main_channel_settings,
                show_settings,
                show_help,
                do_screenshot,
                mpv_mute,
                showhideplaylist,
                lowpanel_ch_1,
                open_stream_info,
                app.quit,
                redraw_menubar,
                QtGui.QIcon(
                    QtGui.QIcon(
                        str(Path("yuki_iptv", ICONS_FOLDER, "circle.png"))
                    ).pixmap(8, 8)
                ),
                my_up_binding_execute,
                my_down_binding_execute,
                show_m3u_editor,
                show_playlists,
                show_sort,
                show_exception,
                get_curwindow_pos,
                force_update_epg_act,
                get_keybind,
                show_tvguide_2,
                enable_always_on_top,
                disable_always_on_top,
                reload_playlist,
                show_shortcuts,
                str(Path(LOCAL_DIR, "alwaysontop.json")),
                yuki_track_set,
            )

            volume_option1 = read_option("volume")
            if volume_option1 is not None:
                logger.info(f"Set volume to {vol_remembered}")
                label7.setValue(vol_remembered)
                mpv_volume_set()
            else:
                label7.setValue(100)
                mpv_volume_set()

            return aot_action1

        def move_label(label, x, y):
            label.move(x, y)

        def set_label_width(label, width):
            if width > 0:
                label.setFixedWidth(width)

        def get_global_cursor_position():
            return QtGui.QCursor.pos()

        class MainWindow(QtWidgets.QMainWindow):
            oldpos = None
            oldpos1 = None

            def __init__(self, parent=None):
                super().__init__(parent)
                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.container = None
                self.listWidget = None
                self.moviesWidget = None
                self.seriesWidget = None
                self.latestWidth = 0
                self.latestHeight = 0
                self.createMenuBar_mw()

                #
                # == mpv init ==
                #

                class Container(QtWidgets.QWidget):
                    def mousePressEvent(self, event3):
                        if event3.button() == QtCore.Qt.MouseButton.LeftButton:
                            my_mouse_left_callback()
                        elif event3.button() == QtCore.Qt.MouseButton.RightButton:
                            my_mouse_right_callback()
                        elif event3.button() in [
                            QtCore.Qt.MouseButton.BackButton,
                            QtCore.Qt.MouseButton.XButton1,
                            QtCore.Qt.MouseButton.ExtraButton1,
                        ]:
                            prev_channel()
                        elif event3.button() in [
                            QtCore.Qt.MouseButton.ForwardButton,
                            QtCore.Qt.MouseButton.XButton2,
                            QtCore.Qt.MouseButton.ExtraButton2,
                        ]:
                            next_channel()
                        else:
                            super().mousePressEvent(event3)

                    def mouseDoubleClickEvent(self, event3):
                        if event3.button() == QtCore.Qt.MouseButton.LeftButton:
                            mpv_fullscreen()

                    def wheelEvent(self, event3):
                        if event3.angleDelta().y() > 0:
                            # up
                            my_up_binding_execute()
                        else:
                            # down
                            my_down_binding_execute()
                        event3.accept()

                if not enable_libmpv_render_context:
                    self.container = QtWidgets.QWidget(self)
                else:
                    self.container = Container(self)
                self.setCentralWidget(self.container)
                self.container.setAttribute(
                    QtCore.Qt.WidgetAttribute.WA_DontCreateNativeAncestors
                )
                if not enable_libmpv_render_context:
                    self.container.setAttribute(
                        QtCore.Qt.WidgetAttribute.WA_NativeWindow
                    )
                self.container.setFocus()
                self.container.setStyleSheet(
                    """
                    background-color: #C0C6CA;
                """
                )

            def updateWindowSize(self):
                if (
                    self.width() != self.latestWidth
                    or self.height() != self.latestHeight
                ):
                    self.latestWidth = self.width()
                    self.latestHeight = self.height()

            def update(self):
                global l1, tvguide_lbl, fullscreen

                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.updateWindowSize()
                if settings["panelposition"] == 0:
                    move_label(tvguide_lbl, 2, tvguide_lbl_offset)
                else:
                    move_label(
                        tvguide_lbl,
                        win.width() - tvguide_lbl.width(),
                        tvguide_lbl_offset,
                    )
                if not fullscreen:
                    if not dockWidget2.isVisible():
                        set_label_width(l1, self.windowWidth - dockWidget.width() + 58)
                        move_label(
                            l1,
                            int(
                                ((self.windowWidth - l1.width()) / 2)
                                - (dockWidget.width() / 1.7)
                            ),
                            int(((self.windowHeight - l1.height()) - 20)),
                        )
                        h = 0
                        h2 = 10
                    else:
                        set_label_width(l1, self.windowWidth - dockWidget.width() + 58)
                        move_label(
                            l1,
                            int(
                                ((self.windowWidth - l1.width()) / 2)
                                - (dockWidget.width() / 1.7)
                            ),
                            int(
                                (
                                    (self.windowHeight - l1.height())
                                    - dockWidget2.height()
                                    - 10
                                )
                            ),
                        )
                        h = dockWidget2.height()
                        h2 = 20
                else:
                    set_label_width(l1, self.windowWidth)
                    move_label(
                        l1,
                        int(((self.windowWidth - l1.width()) / 2)),
                        int(((self.windowHeight - l1.height()) - 20)),
                    )
                    h = 0
                    h2 = 10
                if dockWidget.isVisible():
                    if settings["panelposition"] == 0:
                        move_label(lbl2, 0, lbl2_offset)
                    else:
                        move_label(
                            lbl2, tvguide_lbl.width() + lbl2.width(), lbl2_offset
                        )
                else:
                    move_label(lbl2, 0, lbl2_offset)
                if l1.isVisible():
                    l1_h = l1.height()
                else:
                    l1_h = 15
                tvguide_lbl.setFixedHeight(
                    ((self.windowHeight - l1_h - h) - 40 - l1_h + h2)
                )

            def moveEvent(self, event):
                try:
                    comm_instance.winPosition2 = {
                        "x": win.pos().x(),
                        "y": win.pos().y(),
                    }
                except Exception:
                    pass
                QtWidgets.QMainWindow.moveEvent(self, event)

            def resizeEvent(self, event):
                try:
                    self.update()
                except Exception:
                    pass
                QtWidgets.QMainWindow.resizeEvent(self, event)

            def closeEvent(self, event1):
                if streaminfo_win.isVisible():
                    streaminfo_win.hide()

            def createMenuBar_mw(self):
                self.menu_bar_qt = self.menuBar()
                init_yuki_iptv_menubar(self, app, self.menu_bar_qt)

        win = MainWindow()
        win.setMinimumSize(1, 1)
        win.setWindowTitle(MAIN_WINDOW_TITLE)
        win.setWindowIcon(main_icon)

        window_data = read_option("window")
        if window_data:
            win.setGeometry(
                window_data["x"], window_data["y"], window_data["w"], window_data["h"]
            )
        else:
            win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])
            qr = win.frameGeometry()
            qr.moveCenter(
                QtGui.QScreen.availableGeometry(
                    QtWidgets.QApplication.primaryScreen()
                ).center()
            )
            win.move(qr.topLeft())

        def get_curwindow_pos():
            try:
                win_geometry = win.screen().availableGeometry()
            except Exception:
                win_geometry = QtWidgets.QDesktopWidget().screenGeometry(win)
            win_width = win_geometry.width()
            win_height = win_geometry.height()
            logger.info(f"Screen size: {win_width}x{win_height}")
            return (
                win_width,
                win_height,
            )

        def get_curwindow_pos_actual():
            try:
                win_geometry_1 = win.screen().availableGeometry()
            except Exception:
                win_geometry_1 = QtWidgets.QDesktopWidget().screenGeometry(win)
            return win_geometry_1

        chan = QtWidgets.QLabel(_("No channel selected"))
        chan.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        chan.setStyleSheet("color: green")
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(11)
        myFont4.setBold(True)
        chan.setFont(myFont4)
        chan.resize(200, 30)

        def centerwidget(wdg3, offset1=0):
            fg1 = win.container.frameGeometry()
            xg1 = (fg1.width() - wdg3.width()) / 2
            yg1 = (fg1.height() - wdg3.height()) / 2
            wdg3.move(int(xg1), int(yg1) + int(offset1))

        loading1 = QtWidgets.QLabel(win)
        loading_movie = QtGui.QMovie(
            str(Path("yuki_iptv", ICONS_FOLDER, "loading.gif"))
        )
        loading1.setMovie(loading_movie)
        loading1.setStyleSheet("background-color: white;")
        loading1.resize(32, 32)
        loading1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        centerwidget(loading1)
        loading1.hide()

        loading2 = QtWidgets.QLabel(win)
        loading_movie2 = QtGui.QMovie(
            str(Path("yuki_iptv", ICONS_FOLDER, "recordwait.gif"))
        )
        loading2.setMovie(loading_movie2)
        loading2.setToolTip(_("Processing record..."))
        loading2.resize(32, 32)
        loading2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        centerwidget(loading2, 50)
        loading2.hide()
        loading_movie2.stop()

        def showLoading2():
            if not loading2.isVisible():
                centerwidget(loading2, 50)
                loading_movie2.stop()
                loading_movie2.start()
                loading2.show()

        def hideLoading2():
            if loading2.isVisible():
                loading2.hide()
                loading_movie2.stop()

        lbl2_offset = 15
        tvguide_lbl_offset = 30 + lbl2_offset

        lbl2 = QtWidgets.QLabel(win)
        lbl2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl2.setStyleSheet("color: #e0071a")
        lbl2.setWordWrap(True)
        lbl2.resize(230, 30)
        lbl2.move(0, lbl2_offset)
        lbl2.hide()

        playing = False
        playing_chan = ""
        playing_group = -1

        def show_progress(prog):
            global playing_archive, fullscreen
            if not settings["hidetvprogram"] and (prog and not playing_archive):
                prog_percentage = round(
                    (time.time() - prog["start"]) / (prog["stop"] - prog["start"]) * 100
                )
                prog_title = prog["title"]
                prog_start = prog["start"]
                prog_stop = prog["stop"]
                prog_start_time = datetime.datetime.fromtimestamp(prog_start).strftime(
                    "%H:%M"
                )
                prog_stop_time = datetime.datetime.fromtimestamp(prog_stop).strftime(
                    "%H:%M"
                )
                progress.setValue(prog_percentage)
                progress.setFormat(str(prog_percentage) + "% " + prog_title)
                progress.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                start_label.setText(prog_start_time)
                stop_label.setText(prog_stop_time)
                if not fullscreen:
                    progress.show()
                    start_label.show()
                    stop_label.show()
            else:
                progress.hide()
                start_label.setText("")
                start_label.hide()
                stop_label.setText("")
                stop_label.hide()

        playing_url = ""

        @idle_function
        def set_mpv_title(unused=None):
            try:
                player.title = win.windowTitle()
            except Exception:
                pass

        def setChanText(chanText, do_chan_set=False):
            global time_stop
            chTextStrip = chanText.strip()
            if chTextStrip:
                win.setWindowTitle(chTextStrip + " - " + MAIN_WINDOW_TITLE)
            else:
                win.setWindowTitle(MAIN_WINDOW_TITLE)
            set_mpv_title()
            if not do_chan_set:
                chan.setText(chanText)
            if fullscreen and chTextStrip:
                l1.show()
                l1.setText2(chTextStrip)
                time_stop = time.time() + 1

        playing_archive = False

        @async_gui_blocking_function
        def setPlayerSettings(j):
            global playing_chan
            try:
                logger.info("setPlayerSettings waiting for channel load...")
                try:
                    player.wait_until_playing()
                except Exception:
                    pass
                if j == playing_chan:
                    logger.info(f"setPlayerSettings '{j}'")
                    if (
                        settings["m3u"] in channel_sets
                        and j in channel_sets[settings["m3u"]]
                    ):
                        d = channel_sets[settings["m3u"]][j]
                        player.deinterlace = d["deinterlace"]
                        if "ua" not in d:
                            d["ua"] = ""
                        if "ref" not in d:
                            d["ref"] = ""
                        if "contrast" in d:
                            player.contrast = d["contrast"]
                        else:
                            player.contrast = 0
                        if "brightness" in d:
                            player.brightness = d["brightness"]
                        else:
                            player.brightness = 0
                        if "hue" in d:
                            player.hue = d["hue"]
                        else:
                            player.hue = 0
                        if "saturation" in d:
                            player.saturation = d["saturation"]
                        else:
                            player.saturation = 0
                        if "gamma" in d:
                            player.gamma = d["gamma"]
                        else:
                            player.gamma = 0
                        if "videoaspect" in d:
                            setVideoAspect(
                                videoaspect_vars[
                                    list(videoaspect_vars)[d["videoaspect"]]
                                ]
                            )
                        else:
                            setVideoAspect(
                                videoaspect_vars[
                                    videoaspect_def_choose.itemText(
                                        settings["videoaspect"]
                                    )
                                ]
                            )
                        if "zoom" in d:
                            setZoom(zoom_vars[list(zoom_vars)[d["zoom"]]])
                        else:
                            setZoom(
                                zoom_vars[zoom_def_choose.itemText(settings["zoom"])]
                            )
                        if "panscan" in d:
                            setPanscan(d["panscan"])
                        else:
                            setPanscan(settings["panscan"])
                    else:
                        player.deinterlace = settings["deinterlace"]
                        setVideoAspect(
                            videoaspect_vars[
                                videoaspect_def_choose.itemText(settings["videoaspect"])
                            ]
                        )
                        setZoom(zoom_vars[zoom_def_choose.itemText(settings["zoom"])])
                        setPanscan(settings["panscan"])
                        player.gamma = 0
                        player.saturation = 0
                        player.hue = 0
                        player.brightness = 0
                        player.contrast = 0
                    # Print settings
                    if player.deinterlace:
                        logger.info("Deinterlace: enabled")
                    else:
                        logger.info("Deinterlace: disabled")
                    logger.info(f"Contrast: {player.contrast}")
                    logger.info(f"Brightness: {player.brightness}")
                    logger.info(f"Hue: {player.hue}")
                    logger.info(f"Saturation: {player.saturation}")
                    logger.info(f"Gamma: {player.gamma}")
                    logger.info(f"Video aspect: {getVideoAspect()}")
                    logger.info(f"Zoom: {player.video_zoom}")
                    logger.info(f"Panscan: {player.panscan}")
                    try:
                        player["cursor-autohide"] = 1000
                        player["force-window"] = True
                    except Exception:
                        pass
                    # Restore video / audio / subtitle tracks for channel
                    if playing_chan in player_tracks:
                        last_track = player_tracks[playing_chan]
                        if "vid" in last_track:
                            logger.info(
                                f"Restoring last video track: '{last_track['vid']}'"
                            )
                            player.vid = last_track["vid"]
                        else:
                            player.vid = "auto"
                        if "aid" in last_track:
                            logger.info(
                                f"Restoring last audio track: '{last_track['aid']}'"
                            )
                            player.aid = last_track["aid"]
                        else:
                            player.aid = "auto"
                        if "sid" in last_track:
                            logger.info(
                                f"Restoring last sub track: '{last_track['sid']}'"
                            )
                            player.sid = last_track["sid"]
                        else:
                            player.sid = "auto"
                    else:
                        player.vid = "auto"
                        player.aid = "auto"
                        player.sid = "auto"
                    file_loaded_callback()
            except Exception:
                pass

        def itemClicked_event(item, custom_url="", archived=False):
            global playing, playing_chan, item_selected
            global playing_group, playing_url, playing_archive
            is_ic_ok = True
            try:
                is_ic_ok = item.text() != _("Nothing found")
            except Exception:
                pass
            if is_ic_ok:
                playing_archive = archived
                try:
                    j = item.data(QtCore.Qt.ItemDataRole.UserRole)
                except Exception:
                    j = item
                playing_chan = j
                playing_group = playmode_selector.currentIndex()
                item_selected = j
                try:
                    play_url = getArrayItem(j)["url"]
                except Exception:
                    play_url = custom_url
                MAX_CHAN_SIZE = 35
                channel_name = j
                if len(channel_name) > MAX_CHAN_SIZE:
                    channel_name = channel_name[: MAX_CHAN_SIZE - 3] + "..."
                setChanText("  " + channel_name)
                current_prog = None
                jlower = j.lower()
                try:
                    jlower = prog_match_arr[jlower]
                except Exception:
                    pass
                if settings["epg"] and exists_in_epg(jlower, programmes):
                    for pr in get_epg(programmes, jlower):
                        if time.time() > pr["start"] and time.time() < pr["stop"]:
                            current_prog = pr
                            break
                show_progress(current_prog)
                if start_label.isVisible():
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
                else:
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
                playing = True
                win.update()
                playing_url = play_url
                ua_choose = def_user_agent
                if (
                    settings["m3u"] in channel_sets
                    and j in channel_sets[settings["m3u"]]
                ):
                    ua_choose = channel_sets[settings["m3u"]][j]["ua"]
                if not custom_url:
                    doPlay(play_url, ua_choose, j)
                else:
                    doPlay(custom_url, ua_choose, j)
                btn_update.click()

        item_selected = ""

        def itemSelected_event(item):
            global item_selected
            try:
                n_1 = item.data(QtCore.Qt.ItemDataRole.UserRole)
                item_selected = n_1
                update_tvguide(n_1)
            except Exception:
                pass

        def mpv_play():
            player.pause = not player.pause

        def mpv_stop():
            global playing, playing_chan, playing_group, playing_url
            playing_chan = ""
            playing_group = -1
            playing_url = ""
            hideLoading()
            setChanText("")
            playing = False
            stopPlayer()
            player.loop = True
            player.deinterlace = False
            mpv_override_play(str(Path("yuki_iptv", ICONS_FOLDER, "main.png")))
            player.pause = True
            chan.setText(_("No channel selected"))
            progress.hide()
            start_label.hide()
            stop_label.hide()
            start_label.setText("")
            stop_label.setText("")
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
            win.update()
            btn_update.click()
            redraw_menubar()

        def esc_handler():
            global fullscreen
            if fullscreen:
                mpv_fullscreen()

        def get_always_on_top():
            global cur_aot_state
            return cur_aot_state

        def set_always_on_top(aot_state):
            global cur_aot_state
            cur_aot_state = aot_state
            logger.debug(f"set_always_on_top: {aot_state}")
            whint1 = QtCore.Qt.WindowType.WindowStaysOnTopHint
            if (aot_state and (win.windowFlags() & whint1)) or (
                not aot_state and (not win.windowFlags() & whint1)
            ):
                logger.debug("set_always_on_top: nothing to do")
                return
            winIsVisible = win.isVisible()
            winPos1 = win.pos()
            if aot_state:
                win.setWindowFlags(
                    win.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
                )
            else:
                win.setWindowFlags(
                    win.windowFlags() & ~QtCore.Qt.WindowType.WindowStaysOnTopHint
                )
            win.move(winPos1)
            if winIsVisible:
                win.show()
                win.raise_()
                win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
                win.activateWindow()

        @idle_function
        def enable_always_on_top(unused=None):
            set_always_on_top(True)

        @idle_function
        def disable_always_on_top(unused=None):
            set_always_on_top(False)

        # Always on top
        is_aot = False
        if os.path.isfile(str(Path(LOCAL_DIR, "alwaysontop.json"))):
            try:
                aot_f1 = open(
                    str(Path(LOCAL_DIR, "alwaysontop.json")), "r", encoding="utf-8"
                )
                aot_f1_data = json.loads(aot_f1.read())["alwaysontop"]
                aot_f1.close()
                is_aot = aot_f1_data
            except Exception:
                pass
        if is_aot:
            logger.info("Always on top enabled")
            enable_always_on_top()
        else:
            logger.info("Always on top disabled")

        cur_aot_state = is_aot

        currentWidthHeight = [win.width(), win.height()]
        currentMaximized = win.isMaximized()
        currentDockWidgetPos = -1

        isPlaylistVisible = False
        isControlPanelVisible = False

        def dockWidget_out_clicked():
            global fullscreen, l1, time_stop, currentWidthHeight, currentMaximized
            global currentDockWidgetPos, isPlaylistVisible, isControlPanelVisible
            if not fullscreen:
                # Entering fullscreen
                if not YukiData.fullscreen_locked:
                    YukiData.fullscreen_locked = True
                    logger.info("Entering fullscreen started")
                    time01 = time.time()
                    isControlPanelVisible = dockWidget2.isVisible()
                    isPlaylistVisible = dockWidget.isVisible()
                    setShortcutState(True)
                    comm_instance.winPosition = win.geometry()
                    currentWidthHeight = [win.width(), win.height()]
                    currentMaximized = win.isMaximized()
                    channelfilter.usePopup = False
                    win.menu_bar_qt.hide()
                    fullscreen = True
                    dockWidget.hide()
                    chan.hide()
                    label12.hide()
                    for lbl3 in hlayout2_btns:
                        if lbl3 not in show_lbls_fullscreen:
                            lbl3.hide()
                    progress.hide()
                    start_label.hide()
                    stop_label.hide()
                    dockWidget2.hide()
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
                    win.update()
                    win.showFullScreen()
                    if settings["panelposition"] == 1:
                        tvguide_close_lbl.move(
                            get_curwindow_pos()[0] - tvguide_lbl.width() - 40,
                            tvguide_lbl_offset,
                        )
                    centerwidget(loading1)
                    centerwidget(loading2, 50)
                    time02 = time.time() - time01
                    logger.info(
                        f"Entering fullscreen ended, took {round(time02, 2)} seconds"
                    )
                    YukiData.fullscreen_locked = False
            else:
                # Leaving fullscreen
                if not YukiData.fullscreen_locked:
                    YukiData.fullscreen_locked = True
                    logger.info("Leaving fullscreen started")
                    time03 = time.time()
                    setShortcutState(False)
                    if l1.isVisible() and l1.text().startswith(_("Volume")):
                        l1.hide()
                    win.menu_bar_qt.show()
                    hide_playlist()
                    hide_controlpanel()
                    dockWidget.setWindowOpacity(1)
                    dockWidget.hide()
                    dockWidget2.setWindowOpacity(1)
                    dockWidget2.hide()
                    fullscreen = False
                    if l1.text().endswith(
                        "{} F".format(_("To exit fullscreen mode press"))
                    ):
                        l1.setText2("")
                        if not gl_is_static:
                            l1.hide()
                            win.update()
                    if not player.pause and playing and start_label.text():
                        progress.show()
                        start_label.show()
                        stop_label.show()
                        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
                    label12.show()
                    for lbl3 in hlayout2_btns:
                        if lbl3 not in show_lbls_fullscreen:
                            lbl3.show()
                    dockWidget2.show()
                    dockWidget.show()
                    chan.show()
                    win.update()
                    if not currentMaximized:
                        win.showNormal()
                    else:
                        win.showMaximized()
                    win.resize(currentWidthHeight[0], currentWidthHeight[1])
                    if comm_instance.winPosition:
                        win.move(
                            comm_instance.winPosition.x(), comm_instance.winPosition.y()
                        )
                    else:
                        moveWindowToCenter(win, True)
                    if not isPlaylistVisible:
                        key_t()
                    if settings["panelposition"] == 1:
                        tvguide_close_lbl.move(
                            win.width() - tvguide_lbl.width() - 40, tvguide_lbl_offset
                        )
                    centerwidget(loading1)
                    centerwidget(loading2, 50)
                    if isControlPanelVisible:
                        dockWidget2.show()
                    else:
                        dockWidget2.hide()
                    if YukiData.compact_mode:
                        win.menu_bar_qt.hide()
                        setShortcutState(True)
                    time04 = time.time() - time03
                    logger.info(
                        f"Leaving fullscreen ended, took {round(time04, 2)} seconds"
                    )
                    YukiData.fullscreen_locked = False

        dockWidget_out = QtWidgets.QPushButton()
        dockWidget_out.clicked.connect(dockWidget_out_clicked)

        @idle_function
        def mpv_fullscreen(unused=None):
            dockWidget_out.click()

        old_value = 100

        def is_show_volume():
            global fullscreen
            showdata = fullscreen
            if not fullscreen and win.isVisible():
                showdata = not dockWidget2.isVisible()
            return showdata and not controlpanel_widget.isVisible()

        def show_volume(v1):
            if is_show_volume():
                l1.show()
                if isinstance(v1, str):
                    l1.setText2(v1)
                else:
                    l1.setText2("{}: {}%".format(_("Volume"), int(v1)))

        def mpv_mute():
            global old_value, time_stop, l1
            time_stop = time.time() + 3
            if player.mute:
                if old_value > 50:
                    label6.setIcon(
                        QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "volume.png")))
                    )
                else:
                    label6.setIcon(
                        QtGui.QIcon(
                            str(Path("yuki_iptv", ICONS_FOLDER, "volume-low.png"))
                        )
                    )
                mpv_override_mute(False)
                label7.setValue(old_value)
                show_volume(old_value)
            else:
                label6.setIcon(
                    QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "mute.png")))
                )
                mpv_override_mute(True)
                old_value = label7.value()
                label7.setValue(0)
                show_volume(_("Volume off"))

        def mpv_volume_set():
            global time_stop, l1, fullscreen
            time_stop = time.time() + 3
            vol = int(label7.value())
            try:
                if vol == 0:
                    show_volume(_("Volume off"))
                else:
                    show_volume(vol)
            except NameError:
                pass
            mpv_override_volume(vol)
            if vol == 0:
                mpv_override_mute(True)
                label6.setIcon(
                    QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "mute.png")))
                )
            else:
                mpv_override_mute(False)
                if vol > 50:
                    label6.setIcon(
                        QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "volume.png")))
                    )
                else:
                    label6.setIcon(
                        QtGui.QIcon(
                            str(Path("yuki_iptv", ICONS_FOLDER, "volume-low.png"))
                        )
                    )

        dockWidget = QtWidgets.QDockWidget(win)

        win.listWidget = QtWidgets.QListWidget()
        win.moviesWidget = QtWidgets.QListWidget()
        win.seriesWidget = QtWidgets.QListWidget()

        def tvguide_close_lbl_func(arg):
            hide_tvguide()

        tvguide_lbl = ScrollableLabel(win)
        tvguide_lbl.move(0, tvguide_lbl_offset)
        tvguide_lbl.setFixedWidth(TVGUIDE_WIDTH)
        tvguide_lbl.hide()

        class ClickableLabel(QtWidgets.QLabel):
            def __init__(self, whenClicked, win, parent=None):
                QtWidgets.QLabel.__init__(self, win)
                self._whenClicked = whenClicked

            def mouseReleaseEvent(self, event):
                self._whenClicked(event)

        tvguide_close_lbl = ClickableLabel(tvguide_close_lbl_func, win)
        tvguide_close_lbl.setPixmap(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "close.png"))).pixmap(
                32, 32
            )
        )
        tvguide_close_lbl.setStyleSheet(
            "background-color: {};".format(
                "black" if YukiData.use_dark_icon_theme else "white"
            )
        )
        tvguide_close_lbl.resize(32, 32)
        if settings["panelposition"] == 0:
            tvguide_close_lbl.move(tvguide_lbl.width() + 5, tvguide_lbl_offset)
        else:
            tvguide_close_lbl.move(
                win.width() - tvguide_lbl.width() - 40, tvguide_lbl_offset
            )
            lbl2.move(tvguide_lbl.width() + lbl2.width(), lbl2_offset)
        tvguide_close_lbl.hide()

        current_group = _("All channels")

        channel_sort = {}
        if os.path.isfile(str(Path(LOCAL_DIR, "sortchannels.json"))):
            with open(
                str(Path(LOCAL_DIR, "sortchannels.json")), "r", encoding="utf8"
            ) as file3:
                channel_sort3 = json.loads(file3.read())
                if settings["m3u"] in channel_sort3:
                    channel_sort = channel_sort3[settings["m3u"]]

        def sort_custom(sub):
            try:
                return channel_sort.index(sub)
            except Exception:
                return 0

        def doSort(arr0):
            if settings["sort"] == 0:
                return arr0
            if settings["sort"] == 1:
                return sorted(arr0)
            if settings["sort"] == 2:
                return sorted(arr0, reverse=True)
            if settings["sort"] == 3:
                try:
                    return sorted(arr0, reverse=False, key=sort_custom)
                except Exception:
                    return arr0
            return arr0

        if not os.path.isdir(str(Path(LOCAL_DIR, "logo_cache"))):
            os.mkdir(str(Path(LOCAL_DIR, "logo_cache")))

        def get_of_txt(of_num):
            # try:
            #     of_txt = gettext.ngettext("of %d", "", of_num) % of_num
            # except Exception:
            #     of_txt = f"of {of_num}"
            # return of_txt
            return _("of") + " " + str(of_num)

        prog_match_arr = {}

        channel_logos_request_old = {}
        channel_logos_process = None
        multiprocessing_manager_dict["logos_inprogress"] = False
        multiprocessing_manager_dict["logos_completed"] = False
        logos_cache = {}

        def get_pixmap_from_filename(pixmap_filename):
            if pixmap_filename in logos_cache:
                return logos_cache[pixmap_filename]
            else:
                try:
                    if os.path.isfile(pixmap_filename):
                        icon_pixmap = QtGui.QIcon(pixmap_filename)
                        logos_cache[pixmap_filename] = icon_pixmap
                        icon_pixmap = None
                        return logos_cache[pixmap_filename]
                    else:
                        return None
                except Exception:
                    return None

        thread_logos_update_lock = False

        def thread_logos_update():
            global thread_logos_update_lock, multiprocessing_manager_dict
            try:
                if not thread_logos_update_lock:
                    thread_logos_update_lock = True
                    if multiprocessing_manager_dict["logos_completed"]:
                        multiprocessing_manager_dict["logos_completed"] = False
                        btn_update.click()
                    thread_logos_update_lock = False
            except Exception:
                pass

        class PlaylistWidget(QtWidgets.QWidget):
            def __init__(self, parent=None):
                super().__init__(parent)

                self.name_label = QtWidgets.QLabel()
                myFont = QtGui.QFont()
                myFont.setBold(True)
                self.name_label.setFont(myFont)
                self.description_label = QtWidgets.QLabel()

                self.icon_label = QtWidgets.QLabel()
                self.progress_label = QtWidgets.QLabel()
                self.progress_bar = QtWidgets.QProgressBar()
                self.progress_bar.setFixedHeight(15)
                self.end_label = QtWidgets.QLabel()
                self.opacity = QtWidgets.QGraphicsOpacityEffect()
                self.opacity.setOpacity(100)

                self.layout = QtWidgets.QVBoxLayout()
                self.layout.addWidget(self.name_label)
                self.layout.addWidget(self.description_label)
                self.layout.setSpacing(5)

                self.layout1 = QtWidgets.QGridLayout()
                self.layout1.addWidget(self.progress_label, 0, 0)
                self.layout1.addWidget(self.progress_bar, 0, 1)
                self.layout1.addWidget(self.end_label, 0, 2)

                self.layout2 = QtWidgets.QGridLayout()
                self.layout2.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
                self.layout2.addWidget(self.icon_label, 0, 0)
                self.layout2.addLayout(self.layout, 0, 1)
                self.layout2.setSpacing(10)

                self.layout3 = QtWidgets.QVBoxLayout()
                self.layout3.addLayout(self.layout2)
                self.layout3.addLayout(self.layout1)

                self.setLayout(self.layout3)

                self.progress_bar.setStyleSheet(
                    """
                  background-color: #C0C6CA;
                  border: 0px;
                  padding: 0px;
                  height: 5px;
                """
                )
                self.setStyleSheet(
                    """
                  QProgressBar::chunk {
                    background: #7D94B0;
                    width:5px
                  }
                """
                )

            def setDescription(self, text, tooltip):
                self.setToolTip(tooltip)
                self.description_label.setText(text)

            def setIcon(self, image):
                self.icon_label.setPixmap(image.pixmap(QtCore.QSize(32, 32)))

            def setProgress(self, progress_val):
                self.opacity.setOpacity(100)
                self.progress_bar.setGraphicsEffect(self.opacity)
                self.progress_bar.setFormat("")
                self.progress_bar.setValue(progress_val)

            def hideProgress(self):
                self.opacity.setOpacity(0)
                self.progress_bar.setGraphicsEffect(self.opacity)

            def showDescription(self):
                self.description_label.show()
                self.progress_label.show()
                self.progress_bar.show()
                self.end_label.show()

            def hideDescription(self):
                self.description_label.hide()
                self.progress_label.hide()
                self.progress_bar.hide()
                self.end_label.hide()

        all_channels_lang = _("All channels")
        favourites_lang = _("Favourites")

        def gen_chans():
            global playing_chan, current_group, array, page_box, channelfilter
            global prog_match_arr, channel_logos_request_old
            global channel_logos_process, multiprocessing_manager_dict

            channel_logos_request = {}

            try:
                idx = (page_box.value() - 1) * 100
            except Exception:
                idx = 0
            try:
                filter_txt = channelfilter.text()
            except Exception:
                filter_txt = ""

            # Group and favourites filter
            array_filtered = {}
            for j1 in array:
                group1 = array[j1]["tvg-group"]
                if current_group != all_channels_lang:
                    if current_group == favourites_lang:
                        if j1 not in favourite_sets:
                            continue
                    else:
                        if group1 != current_group:
                            continue
                array_filtered[j1] = array[j1]

            ch_array = {
                x13: array_filtered[x13]
                for x13 in array_filtered
                if unidecode(filter_txt).lower().strip()
                in unidecode(x13).lower().strip()
            }
            ch_array = list(ch_array.values())[idx : idx + 100]
            ch_array = dict([(x14["title"], x14) for x14 in ch_array])
            try:
                if filter_txt:
                    page_box.setMaximum(round(len(ch_array) / 100) + 1)
                    of_lbl.setText(get_of_txt(round(len(ch_array) / 100) + 1))
                else:
                    page_box.setMaximum(round(len(array_filtered) / 100) + 1)
                    of_lbl.setText(get_of_txt(round(len(array_filtered) / 100) + 1))
            except Exception:
                pass
            res = {}
            k0 = -1
            k = 0
            for i in doSort(ch_array):
                k0 += 1
                k += 1
                prog = ""
                prog_desc = ""
                is_epgname_found = False

                # First, match EPG name from settings
                if (
                    settings["m3u"] in channel_sets
                    and i in channel_sets[settings["m3u"]]
                ):
                    if "epgname" in channel_sets[settings["m3u"]][i]:
                        if channel_sets[settings["m3u"]][i]["epgname"]:
                            epg_name = channel_sets[settings["m3u"]][i]["epgname"]
                            if exists_in_epg(str(epg_name).lower(), programmes):
                                prog_search = str(epg_name).lower()
                                is_epgname_found = True

                # Second, match from tvg-id
                if not is_epgname_found:
                    if array_filtered[i]["tvg-ID"]:
                        if str(array_filtered[i]["tvg-ID"]) in prog_ids:
                            prog_search_lst = prog_ids[str(array_filtered[i]["tvg-ID"])]
                            if prog_search_lst:
                                prog_search = prog_search_lst[0].lower()
                                is_epgname_found = True

                # Third, match from tvg-name
                if not is_epgname_found:
                    if array_filtered[i]["tvg-name"]:
                        if exists_in_epg(
                            str(array_filtered[i]["tvg-name"]).lower(), programmes
                        ):
                            prog_search = str(array_filtered[i]["tvg-name"]).lower()
                            is_epgname_found = True
                        else:
                            spaces_replaced_name = array_filtered[i][
                                "tvg-name"
                            ].replace(" ", "_")
                            if exists_in_epg(
                                str(spaces_replaced_name).lower(), programmes
                            ):
                                prog_search = str(spaces_replaced_name).lower()
                                is_epgname_found = True

                # Last, match from channel name
                if not is_epgname_found:
                    prog_search = i.lower()
                    is_epgname_found = True

                prog_match_arr[i.lower()] = prog_search
                if exists_in_epg(prog_search, programmes):
                    current_prog = {"start": 0, "stop": 0, "title": "", "desc": ""}
                    for pr in get_epg(programmes, prog_search):
                        if time.time() > pr["start"] and time.time() < pr["stop"]:
                            current_prog = pr
                            break
                    if current_prog["start"] != 0:
                        start_time = datetime.datetime.fromtimestamp(
                            current_prog["start"]
                        ).strftime("%H:%M")
                        stop_time = datetime.datetime.fromtimestamp(
                            current_prog["stop"]
                        ).strftime("%H:%M")
                        t_t = time.time()
                        percentage = round(
                            (t_t - current_prog["start"])
                            / (current_prog["stop"] - current_prog["start"])
                            * 100
                        )
                        if settings["hideepgpercentage"]:
                            prog = current_prog["title"]
                        else:
                            prog = str(percentage) + "% " + current_prog["title"]
                        try:
                            if current_prog["desc"]:
                                prog_desc = "\n\n" + textwrap.fill(
                                    current_prog["desc"], 100
                                )
                            else:
                                prog_desc = ""
                        except Exception:
                            prog_desc = ""
                    else:
                        start_time = ""
                        stop_time = ""
                        t_t = time.time()
                        percentage = 0
                        prog = ""
                        prog_desc = ""
                MyPlaylistWidget = PlaylistWidget()
                MAX_SIZE_CHAN = 21
                chan_name = i

                orig_chan_name = chan_name

                if settings["channellogos"] != 3:
                    try:
                        channel_logo1 = ""
                        if "tvg-logo" in array_filtered[i]:
                            channel_logo1 = array_filtered[i]["tvg-logo"]

                        epg_logo1 = ""
                        if prog_search in epg_icons:
                            epg_logo1 = epg_icons[prog_search]

                        req_data_ua, req_data_ref = get_ua_ref_for_channel(
                            orig_chan_name
                        )
                        channel_logos_request[array_filtered[i]["title"]] = [
                            channel_logo1,
                            epg_logo1,
                            req_data_ua,
                            req_data_ref,
                        ]
                    except Exception:
                        logger.warning(f"Exception in channel logos (channel '{i}')")
                        logger.warning(traceback.format_exc())

                if len(chan_name) > MAX_SIZE_CHAN:
                    chan_name = chan_name[0:MAX_SIZE_CHAN] + "..."
                unicode_play_symbol = chr(9654) + " "
                append_symbol = ""
                if playing_chan == chan_name:
                    append_symbol = unicode_play_symbol
                MyPlaylistWidget.name_label.setText(
                    append_symbol + str(k) + ". " + chan_name
                )
                MAX_SIZE = 28
                orig_prog = prog
                try:
                    tooltip_group = "{}: {}".format(
                        _("Group"), array_filtered[i]["tvg-group"]
                    )
                except Exception:
                    tooltip_group = "{}: {}".format(_("Group"), _("All channels"))
                if len(prog) > MAX_SIZE:
                    prog = prog[0:MAX_SIZE] + "..."
                if (
                    exists_in_epg(prog_search, programmes)
                    and orig_prog
                    and not settings["hideepgfromplaylist"]
                ):
                    MyPlaylistWidget.setDescription(
                        prog,
                        (
                            f"<b>{i}</b>" + f"<br>{tooltip_group}<br><br>"
                            "<i>" + orig_prog + "</i>" + prog_desc
                        ).replace("\n", "<br>"),
                    )
                    MyPlaylistWidget.showDescription()
                    try:
                        if start_time:
                            MyPlaylistWidget.progress_label.setText(start_time)
                            MyPlaylistWidget.end_label.setText(stop_time)
                            MyPlaylistWidget.setProgress(int(percentage))
                        else:
                            MyPlaylistWidget.hideProgress()
                    except Exception:
                        logger.warning("Async EPG load problem, ignoring")
                else:
                    MyPlaylistWidget.setDescription(
                        "", f"<b>{i}</b><br>{tooltip_group}"
                    )
                    MyPlaylistWidget.hideProgress()
                    MyPlaylistWidget.hideDescription()

                MyPlaylistWidget.setIcon(TV_ICON)

                if settings["channellogos"] != 3:  # Do not load any logos
                    try:
                        if f"LOGO:::{orig_chan_name}" in multiprocessing_manager_dict:
                            if settings["channellogos"] == 0:  # Prefer M3U
                                first_loaded = False
                                if multiprocessing_manager_dict[
                                    f"LOGO:::{orig_chan_name}"
                                ][0]:
                                    chan_logo = get_pixmap_from_filename(
                                        multiprocessing_manager_dict[
                                            f"LOGO:::{orig_chan_name}"
                                        ][0]
                                    )
                                    if chan_logo:
                                        first_loaded = True
                                        MyPlaylistWidget.setIcon(chan_logo)
                                if not first_loaded:
                                    chan_logo = get_pixmap_from_filename(
                                        multiprocessing_manager_dict[
                                            f"LOGO:::{orig_chan_name}"
                                        ][1]
                                    )
                                    if chan_logo:
                                        MyPlaylistWidget.setIcon(chan_logo)
                            elif settings["channellogos"] == 1:  # Prefer EPG
                                first_loaded = False
                                if multiprocessing_manager_dict[
                                    f"LOGO:::{orig_chan_name}"
                                ][1]:
                                    chan_logo = get_pixmap_from_filename(
                                        multiprocessing_manager_dict[
                                            f"LOGO:::{orig_chan_name}"
                                        ][1]
                                    )
                                    if chan_logo:
                                        first_loaded = True
                                        MyPlaylistWidget.setIcon(chan_logo)
                                if not first_loaded:
                                    chan_logo = get_pixmap_from_filename(
                                        multiprocessing_manager_dict[
                                            f"LOGO:::{orig_chan_name}"
                                        ][0]
                                    )
                                    if chan_logo:
                                        MyPlaylistWidget.setIcon(chan_logo)
                            elif (
                                settings["channellogos"] == 2
                            ):  # Do not load from EPG (only M3U)
                                if multiprocessing_manager_dict[
                                    f"LOGO:::{orig_chan_name}"
                                ][0]:
                                    chan_logo = get_pixmap_from_filename(
                                        multiprocessing_manager_dict[
                                            f"LOGO:::{orig_chan_name}"
                                        ][0]
                                    )
                                    if chan_logo:
                                        MyPlaylistWidget.setIcon(chan_logo)
                    except Exception:
                        logger.warning("Set failed logos failed with exception")
                        logger.warning(traceback.format_exc())

                # Create QListWidgetItem
                myQListWidgetItem = QtWidgets.QListWidgetItem()
                myQListWidgetItem.setData(QtCore.Qt.ItemDataRole.UserRole, i)
                # Set size hint
                myQListWidgetItem.setSizeHint(MyPlaylistWidget.sizeHint())
                res[k0] = [myQListWidgetItem, MyPlaylistWidget, k0, i]
            j1 = playing_chan.lower()
            try:
                j1 = prog_match_arr[j1]
            except Exception:
                pass
            if j1:
                current_chan = None
                try:
                    cur = get_epg(programmes, j1)
                    for pr in cur:
                        if time.time() > pr["start"] and time.time() < pr["stop"]:
                            current_chan = pr
                            break
                except Exception:
                    pass
                show_progress(current_chan)

            # Fetch channel logos
            try:
                if settings["channellogos"] != 3:
                    if channel_logos_request != channel_logos_request_old:
                        channel_logos_request_old = channel_logos_request
                        logger.debug("Channel logos request")
                        if channel_logos_process and channel_logos_process.is_alive():
                            # logger.debug(
                            #     "Old channel logos request found, stopping it"
                            # )
                            channel_logos_process.kill()
                        channel_logos_process = get_context("spawn").Process(
                            name="[yuki-iptv] channel_logos_worker",
                            target=channel_logos_worker,
                            daemon=True,
                            args=(
                                channel_logos_request,
                                multiprocessing_manager_dict,
                            ),
                        )
                        channel_logos_process.start()
            except Exception:
                logger.warning("Fetch channel logos failed with exception:")
                logger.warning(traceback.format_exc())

            return res

        row0 = -1

        def redraw_chans():
            channels_1 = gen_chans()
            global row0
            update_tvguide()
            row0 = win.listWidget.currentRow()
            val0 = win.listWidget.verticalScrollBar().value()
            win.listWidget.clear()
            if channels_1:
                for channel_1 in channels_1.values():
                    chan_3 = channel_1
                    win.listWidget.addItem(chan_3[0])
                    win.listWidget.setItemWidget(chan_3[0], chan_3[1])
            else:
                win.listWidget.addItem(_("Nothing found"))
            win.listWidget.setCurrentRow(row0)
            win.listWidget.verticalScrollBar().setValue(val0)

        first_change = False

        def group_change(self):
            comm_instance.comboboxIndex = combobox.currentIndex()
            global current_group, first_change
            current_group = groups[self]
            if not first_change:
                first_change = True
            else:
                btn_update.click()

        btn_update.clicked.connect(redraw_chans)

        first_playmode_change = False

        def playmode_change(self=False):
            YukiData.playmodeIndex = playmode_selector.currentIndex()
            global first_playmode_change
            if not first_playmode_change:
                first_playmode_change = True
            else:
                tv_widgets = [combobox, win.listWidget, widget4]
                movies_widgets = [movies_combobox, win.moviesWidget]
                series_widgets = [win.seriesWidget]
                # Clear search text when play mode is changed
                # (TV channels, movies, series)
                try:
                    channelfilter.setText("")
                    channelfiltersearch.click()
                except Exception:
                    pass
                if playmode_selector.currentIndex() == 0:
                    for lbl5 in movies_widgets:
                        lbl5.hide()
                    for lbl6 in series_widgets:
                        lbl6.hide()
                    for lbl4 in tv_widgets:
                        lbl4.show()
                    try:
                        channelfilter.setPlaceholderText(_("Search channel"))
                    except Exception:
                        pass
                if playmode_selector.currentIndex() == 1:
                    for lbl4 in tv_widgets:
                        lbl4.hide()
                    for lbl6 in series_widgets:
                        lbl6.hide()
                    for lbl5 in movies_widgets:
                        lbl5.show()
                    try:
                        channelfilter.setPlaceholderText(_("Search movie"))
                    except Exception:
                        pass
                if playmode_selector.currentIndex() == 2:
                    for lbl4 in tv_widgets:
                        lbl4.hide()
                    for lbl5 in movies_widgets:
                        lbl5.hide()
                    for lbl6 in series_widgets:
                        lbl6.show()
                    try:
                        channelfilter.setPlaceholderText(_("Search series"))
                    except Exception:
                        pass

        channels = gen_chans()
        modelA = []
        for channel in channels:
            # Add QListWidgetItem into QListWidget
            modelA.append(channels[channel][3])
            win.listWidget.addItem(channels[channel][0])
            win.listWidget.setItemWidget(channels[channel][0], channels[channel][1])

        def sort_upbtn_clicked():
            curIndex = sort_list.currentRow()
            if curIndex != -1 and curIndex > 0:
                curItem = sort_list.takeItem(curIndex)
                sort_list.insertItem(curIndex - 1, curItem)
                sort_list.setCurrentRow(curIndex - 1)

        def sort_downbtn_clicked():
            curIndex1 = sort_list.currentRow()
            if curIndex1 != -1 and curIndex1 < sort_list.count() - 1:
                curItem1 = sort_list.takeItem(curIndex1)
                sort_list.insertItem(curIndex1 + 1, curItem1)
                sort_list.setCurrentRow(curIndex1 + 1)

        sort_upbtn = QtWidgets.QPushButton()
        sort_upbtn.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "arrow-up.png")))
        )
        sort_upbtn.clicked.connect(sort_upbtn_clicked)
        sort_downbtn = QtWidgets.QPushButton()
        sort_downbtn.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "arrow-down.png")))
        )
        sort_downbtn.clicked.connect(sort_downbtn_clicked)

        sort_widget2 = QtWidgets.QWidget()
        sort_layout2 = QtWidgets.QVBoxLayout()
        sort_layout2.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        sort_layout2.addWidget(sort_upbtn)
        sort_layout2.addWidget(sort_downbtn)
        sort_widget2.setLayout(sort_layout2)

        sort_list = QtWidgets.QListWidget()
        sort_layout3 = QtWidgets.QHBoxLayout()
        sort_layout3.addWidget(sort_list)
        sort_layout3.addWidget(sort_widget2)
        sort_widget3.setLayout(sort_layout3)
        if not channel_sort:
            sort_label_data = modelA
        else:
            sort_label_data = channel_sort
        for sort_label_ch in sort_label_data:
            sort_list.addItem(sort_label_ch)

        def tvguide_context_menu():
            update_tvguide()
            tvguide_lbl.show()
            tvguide_close_lbl.show()

        def settings_context_menu():
            if chan_win.isVisible():
                chan_win.close()
            title.setText(str(item_selected))
            if (
                settings["m3u"] in channel_sets
                and item_selected in channel_sets[settings["m3u"]]
            ):
                deinterlace_chk.setChecked(
                    channel_sets[settings["m3u"]][item_selected]["deinterlace"]
                )
                try:
                    useragent_choose.setText(
                        channel_sets[settings["m3u"]][item_selected]["ua"]
                    )
                except Exception:
                    useragent_choose.setText("")
                try:
                    referer_choose_custom.setText(
                        channel_sets[settings["m3u"]][item_selected]["ref"]
                    )
                except Exception:
                    referer_choose_custom.setText("")
                try:
                    group_text.setText(
                        channel_sets[settings["m3u"]][item_selected]["group"]
                    )
                except Exception:
                    group_text.setText("")
                try:
                    hidden_chk.setChecked(
                        channel_sets[settings["m3u"]][item_selected]["hidden"]
                    )
                except Exception:
                    hidden_chk.setChecked(False)
                try:
                    contrast_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["contrast"]
                    )
                except Exception:
                    contrast_choose.setValue(0)
                try:
                    brightness_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["brightness"]
                    )
                except Exception:
                    brightness_choose.setValue(0)
                try:
                    hue_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["hue"]
                    )
                except Exception:
                    hue_choose.setValue(0)
                try:
                    saturation_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["saturation"]
                    )
                except Exception:
                    saturation_choose.setValue(0)
                try:
                    gamma_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["gamma"]
                    )
                except Exception:
                    gamma_choose.setValue(0)
                try:
                    videoaspect_choose.setCurrentIndex(
                        channel_sets[settings["m3u"]][item_selected]["videoaspect"]
                    )
                except Exception:
                    videoaspect_choose.setCurrentIndex(0)
                try:
                    zoom_choose.setCurrentIndex(
                        channel_sets[settings["m3u"]][item_selected]["zoom"]
                    )
                except Exception:
                    zoom_choose.setCurrentIndex(0)
                try:
                    panscan_choose.setValue(
                        channel_sets[settings["m3u"]][item_selected]["panscan"]
                    )
                except Exception:
                    panscan_choose.setValue(0)
                try:
                    epgname_saved = channel_sets[settings["m3u"]][item_selected][
                        "epgname"
                    ]
                    if not epgname_saved:
                        epgname_saved = _("Default")
                    epgname_lbl.setText(epgname_saved)
                except Exception:
                    epgname_lbl.setText(_("Default"))
            else:
                deinterlace_chk.setChecked(settings["deinterlace"])
                hidden_chk.setChecked(False)
                contrast_choose.setValue(0)
                brightness_choose.setValue(0)
                hue_choose.setValue(0)
                saturation_choose.setValue(0)
                gamma_choose.setValue(0)
                videoaspect_choose.setCurrentIndex(0)
                zoom_choose.setCurrentIndex(0)
                panscan_choose.setValue(0)
                useragent_choose.setText("")
                referer_choose_custom.setText("")
                group_text.setText("")
                epgname_lbl.setText(_("Default"))
            moveWindowToCenter(chan_win)
            chan_win.show()

        def tvguide_favourites_add():
            if item_selected in favourite_sets:
                isdelete_fav_msg = QtWidgets.QMessageBox.question(
                    None,
                    MAIN_WINDOW_TITLE,
                    str(_("Delete from favourites")) + "?",
                    QtWidgets.QMessageBox.StandardButton.Yes
                    | QtWidgets.QMessageBox.StandardButton.No,
                    QtWidgets.QMessageBox.StandardButton.Yes,
                )
                if isdelete_fav_msg == QtWidgets.QMessageBox.StandardButton.Yes:
                    favourite_sets.remove(item_selected)
            else:
                favourite_sets.append(item_selected)
            save_favourite_sets()
            btn_update.click()

        def open_external_player():
            moveWindowToCenter(ext_win)
            ext_win.show()

        def tvguide_hide():
            tvguide_lbl.setText("")
            tvguide_lbl.hide()
            tvguide_close_lbl.hide()

        def favoritesplaylistsep_add():
            ps_data = getArrayItem(item_selected)
            str1 = "#EXTINF:-1"
            if ps_data["tvg-name"]:
                str1 += f" tvg-name=\"{ps_data['tvg-name']}\""
            if ps_data["tvg-ID"]:
                str1 += f" tvg-id=\"{ps_data['tvg-ID']}\""
            if ps_data["tvg-logo"]:
                str1 += f" tvg-logo=\"{ps_data['tvg-logo']}\""
            if ps_data["tvg-group"]:
                str1 += f" tvg-group=\"{ps_data['tvg-group']}\""
            if ps_data["tvg-url"]:
                str1 += f" tvg-url=\"{ps_data['tvg-url']}\""
            else:
                str1 += f" tvg-url=\"{settings['epg']}\""
            if ps_data["catchup"]:
                str1 += f" catchup=\"{ps_data['catchup']}\""
            if ps_data["catchup-source"]:
                str1 += f" catchup-source=\"{ps_data['catchup-source']}\""
            if ps_data["catchup-days"]:
                str1 += f" catchup-days=\"{ps_data['catchup-days']}\""

            str_append = ""
            if ps_data["useragent"]:
                str_append += f"#EXTVLCOPT:http-user-agent={ps_data['useragent']}\n"
            if ps_data["referer"]:
                str_append += f"#EXTVLCOPT:http-referrer={ps_data['referer']}\n"

            str1 += f",{item_selected}\n{str_append}{ps_data['url']}\n"
            file03 = open(str(Path(LOCAL_DIR, "favplaylist.m3u")), "r", encoding="utf8")
            file03_contents = file03.read()
            file03.close()
            if file03_contents == "#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n":
                file04 = open(
                    str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8"
                )
                file04.write("#EXTM3U\n" + str1)
                file04.close()
            else:
                if str1 in file03_contents:
                    playlistsep_del_msg = QtWidgets.QMessageBox.question(
                        None,
                        MAIN_WINDOW_TITLE,
                        _("Are you sure?"),
                        QtWidgets.QMessageBox.StandardButton.Yes
                        | QtWidgets.QMessageBox.StandardButton.No,
                        QtWidgets.QMessageBox.StandardButton.Yes,
                    )
                    if playlistsep_del_msg == QtWidgets.QMessageBox.StandardButton.Yes:
                        new_data = file03_contents.replace(str1, "")
                        if new_data == "#EXTM3U\n":
                            new_data = "#EXTM3U\n#EXTINF:-1,-\nhttp://255.255.255.255\n"
                        file05 = open(
                            str(Path(LOCAL_DIR, "favplaylist.m3u")),
                            "w",
                            encoding="utf8",
                        )
                        file05.write(new_data)
                        file05.close()
                else:
                    file02 = open(
                        str(Path(LOCAL_DIR, "favplaylist.m3u")), "w", encoding="utf8"
                    )
                    file02.write(file03_contents + str1)
                    file02.close()

        def show_context_menu(pos):
            is_continue = True
            try:
                is_continue = win.listWidget.selectedItems()[0].text() != _(
                    "Nothing found"
                )
            except Exception:
                pass
            try:
                if is_continue:
                    self = win.listWidget
                    itemSelected_event(self.selectedItems()[0])
                    menu = QtWidgets.QMenu()
                    menu.addAction(_("TV guide"), tvguide_context_menu)
                    menu.addAction(_("Hide TV guide"), tvguide_hide)
                    menu.addAction(_("Favourites"), tvguide_favourites_add)
                    menu.addAction(
                        _("Favourites+ (separate playlist)"), favoritesplaylistsep_add
                    )
                    menu.addAction(_("Open in external player"), open_external_player)
                    menu.addAction(_("Video settings"), settings_context_menu)
                    _exec(menu, self.mapToGlobal(pos))
            except Exception:
                pass

        win.listWidget.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        win.listWidget.customContextMenuRequested.connect(show_context_menu)
        win.listWidget.currentItemChanged.connect(itemSelected_event)
        win.listWidget.itemClicked.connect(itemSelected_event)
        win.listWidget.itemDoubleClicked.connect(itemClicked_event)

        def enterPressed():
            itemClicked_event(win.listWidget.currentItem())

        shortcuts = {}
        shortcuts_return = QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key.Key_Return),
            win.listWidget,
            activated=enterPressed,
        )

        def channelfilter_do():
            try:
                filter_txt1 = channelfilter.text()
            except Exception:
                filter_txt1 = ""
            if YukiData.playmodeIndex == 0:  # TV channels
                btn_update.click()
            elif YukiData.playmodeIndex == 1:  # Movies
                for item3 in range(win.moviesWidget.count()):
                    if (
                        unidecode(filter_txt1).lower().strip()
                        in unidecode(win.moviesWidget.item(item3).text())
                        .lower()
                        .strip()
                    ):
                        win.moviesWidget.item(item3).setHidden(False)
                    else:
                        win.moviesWidget.item(item3).setHidden(True)
            elif YukiData.playmodeIndex == 2:  # Series
                try:
                    redraw_series()
                except Exception:
                    logger.warning("redraw_series FAILED")
                for item4 in range(win.seriesWidget.count()):
                    if (
                        unidecode(filter_txt1).lower().strip()
                        in unidecode(win.seriesWidget.item(item4).text())
                        .lower()
                        .strip()
                    ):
                        win.seriesWidget.item(item4).setHidden(False)
                    else:
                        win.seriesWidget.item(item4).setHidden(True)

        loading = QtWidgets.QLabel(_("Loading..."))
        loading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        loading.setStyleSheet("color: #778a30")
        hideLoading()

        myFont2 = QtGui.QFont()
        myFont2.setPointSize(12)
        myFont2.setBold(True)
        loading.setFont(myFont2)
        combobox = QtWidgets.QComboBox()
        combobox.currentIndexChanged.connect(group_change)
        for group in groups:
            combobox.addItem(group)

        currentMoviesGroup = {}

        def movies_group_change():
            global currentMoviesGroup
            if YukiData.movies:
                current_movies_group = movies_combobox.currentText()
                if current_movies_group:
                    win.moviesWidget.clear()
                    currentMoviesGroup = {}
                    for movies1 in YukiData.movies:
                        if "tvg-group" in YukiData.movies[movies1]:
                            if (
                                YukiData.movies[movies1]["tvg-group"]
                                == current_movies_group
                            ):
                                win.moviesWidget.addItem(
                                    YukiData.movies[movies1]["title"]
                                )
                                currentMoviesGroup[
                                    YukiData.movies[movies1]["title"]
                                ] = YukiData.movies[movies1]
            else:
                win.moviesWidget.clear()
                win.moviesWidget.addItem(_("Nothing found"))

        def movies_play(mov_item):
            global playing_url
            if mov_item.text() in currentMoviesGroup:
                itemClicked_event(
                    mov_item.text(), currentMoviesGroup[mov_item.text()]["url"]
                )

        win.moviesWidget.itemDoubleClicked.connect(movies_play)

        movies_groups = []
        movies_combobox = QtWidgets.QComboBox()
        for movie_combobox in YukiData.movies:
            if "tvg-group" in YukiData.movies[movie_combobox]:
                if YukiData.movies[movie_combobox]["tvg-group"] not in movies_groups:
                    movies_groups.append(YukiData.movies[movie_combobox]["tvg-group"])
        for movie_group in movies_groups:
            movies_combobox.addItem(movie_group)
        movies_combobox.currentIndexChanged.connect(movies_group_change)
        movies_group_change()

        def redraw_series():
            YukiData.serie_selected = False
            win.seriesWidget.clear()
            if YukiData.series:
                for serie2 in YukiData.series:
                    win.seriesWidget.addItem(serie2)
            else:
                win.seriesWidget.addItem(_("Nothing found"))

        def series_change(series_item):
            sel_serie = series_item.text()
            if sel_serie == "< " + _("Back"):
                redraw_series()
            else:
                if YukiData.serie_selected:
                    try:
                        serie_data = series_item.data(QtCore.Qt.ItemDataRole.UserRole)
                        if serie_data:
                            series_name = serie_data.split(":::::::::::::::::::")[2]
                            season_name = serie_data.split(":::::::::::::::::::")[1]
                            serie_url = serie_data.split(":::::::::::::::::::")[0]
                            itemClicked_event(
                                sel_serie
                                + " ::: "
                                + season_name
                                + " ::: "
                                + series_name,
                                serie_url,
                            )
                    except Exception:
                        pass
                else:
                    logger.info(f"Fetching data for serie '{sel_serie}'")
                    win.seriesWidget.clear()
                    win.seriesWidget.addItem("< " + _("Back"))
                    win.seriesWidget.item(0).setForeground(QtCore.Qt.GlobalColor.blue)
                    try:
                        if not YukiData.series[sel_serie].seasons:
                            xt.get_series_info_by_id(YukiData.series[sel_serie])
                        for season_name in YukiData.series[sel_serie].seasons.keys():
                            season = YukiData.series[sel_serie].seasons[season_name]
                            season_item = QtWidgets.QListWidgetItem()
                            season_item.setText("== " + season.name + " ==")
                            season_item.setFont(bold_fnt_1)
                            win.seriesWidget.addItem(season_item)
                            for episode_name in season.episodes.keys():
                                episode = season.episodes[episode_name]
                                episode_item = QtWidgets.QListWidgetItem()
                                episode_item.setText(episode.title)
                                episode_item.setData(
                                    QtCore.Qt.ItemDataRole.UserRole,
                                    episode.url
                                    + ":::::::::::::::::::"
                                    + season.name
                                    + ":::::::::::::::::::"
                                    + sel_serie,
                                )
                                win.seriesWidget.addItem(episode_item)
                        YukiData.serie_selected = True
                        logger.info(f"Fetching data for serie '{sel_serie}' completed")
                    except Exception:
                        logger.warning(f"Fetching data for serie '{sel_serie}' FAILED")

        win.seriesWidget.itemDoubleClicked.connect(series_change)

        redraw_series()

        playmode_selector = QtWidgets.QComboBox()
        playmode_selector.currentIndexChanged.connect(playmode_change)
        for playmode in [_("TV channels"), _("Movies"), _("Series")]:
            playmode_selector.addItem(playmode)

        def focusOutEvent_after(
            playlist_widget_visible,
            controlpanel_widget_visible,
            channelfiltersearch_has_focus,
        ):
            channelfilter.usePopup = False
            playlist_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            controlpanel_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            if playlist_widget_visible:
                playlist_widget.show()
            if controlpanel_widget_visible:
                controlpanel_widget.show()
            if channelfiltersearch_has_focus:
                channelfiltersearch.click()

        @async_gui_blocking_function
        def mainthread_timer_2(t2):
            time.sleep(0.05)
            exInMainThread_partial(t2)

        def mainthread_timer(t1):
            mainthread_timer_2(t1)

        class MyLineEdit(QtWidgets.QLineEdit):
            usePopup = False
            click_event = Signal()

            def mousePressEvent(self, event1):
                if event1.button() == QtCore.Qt.MouseButton.LeftButton:
                    self.click_event.emit()
                else:
                    super().mousePressEvent(event1)

            def focusOutEvent(self, event2):
                super().focusOutEvent(event2)
                if fullscreen:
                    playlist_widget_visible1 = playlist_widget.isVisible()
                    controlpanel_widget_visible1 = controlpanel_widget.isVisible()
                    channelfiltersearch_has_focus1 = channelfiltersearch.hasFocus()
                    focusOutEvent_after_partial = partial(
                        focusOutEvent_after,
                        playlist_widget_visible1,
                        controlpanel_widget_visible1,
                        channelfiltersearch_has_focus1,
                    )
                    mainthread_timer_1 = partial(
                        mainthread_timer, focusOutEvent_after_partial
                    )
                    exInMainThread_partial(mainthread_timer_1)

        def channelfilter_clicked():
            if fullscreen:
                playlist_widget_visible1 = playlist_widget.isVisible()
                controlpanel_widget_visible1 = controlpanel_widget.isVisible()
                channelfilter.usePopup = True
                playlist_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
                if playlist_widget_visible1:
                    playlist_widget.show()
                if controlpanel_widget_visible1:
                    controlpanel_widget.show()

        tvguide_many_win = QtWidgets.QMainWindow()
        tvguide_many_win.setWindowTitle((_("TV guide")))
        tvguide_many_win.setWindowIcon(main_icon)
        tvguide_many_win.resize(1000, 700)

        tvguide_many_widget = QtWidgets.QWidget()
        tvguide_many_layout = QtWidgets.QGridLayout()
        tvguide_many_widget.setLayout(tvguide_many_layout)
        tvguide_many_win.setCentralWidget(tvguide_many_widget)

        tvguide_many_table = QtWidgets.QTableWidget()
        tvguide_many_layout.addWidget(tvguide_many_table, 0, 0)

        def tvguide_many_clicked():
            tvguide_many_chans = []
            tvguide_many_chans_names = []
            tvguide_many_i = -1
            for tvguide_m_chan in [x6[0] for x6 in sorted(array.items())]:
                epg_search = tvguide_m_chan.lower()
                if epg_search in prog_match_arr:
                    epg_search = prog_match_arr[epg_search.lower()]
                if exists_in_epg(epg_search, programmes):
                    tvguide_many_i += 1
                    tvguide_many_chans.append(epg_search)
                    tvguide_many_chans_names.append(tvguide_m_chan)
            tvguide_many_table.setRowCount(len(tvguide_many_chans))
            tvguide_many_table.setVerticalHeaderLabels(tvguide_many_chans_names)
            logger.info(tvguide_many_table.horizontalHeader())
            a_1_len_array = []
            a_1_array = {}
            for chan_6 in tvguide_many_chans:
                a_1 = [
                    a_2
                    for a_2 in get_epg(programmes, chan_6)
                    if a_2["stop"] > time.time() - 1
                ]
                a_1_array[chan_6] = a_1
                a_1_len_array.append(len(a_1))
            tvguide_many_table.setColumnCount(max(a_1_len_array))
            tvguide_many_i2 = -1
            for chan_7 in tvguide_many_chans:
                tvguide_many_i2 += 1
                a_3_i = -1
                for a_3 in a_1_array[chan_7]:
                    a_3_i += 1
                    start_3_many = (
                        datetime.datetime.fromtimestamp(a_3["start"]).strftime("%H:%M")
                        + " - "
                    )
                    stop_3_many = (
                        datetime.datetime.fromtimestamp(a_3["stop"]).strftime("%H:%M")
                        + "\n"
                    )
                    try:
                        title_3_many = a_3["title"] if "title" in a_3 else ""
                    except Exception:
                        title_3_many = ""
                    try:
                        desc_3_many = (
                            ("\n" + a_3["desc"] + "\n") if "desc" in a_3 else ""
                        )
                    except Exception:
                        desc_3_many = ""
                    a_3_text = start_3_many + stop_3_many + title_3_many + desc_3_many
                    tvguide_many_table.setItem(
                        tvguide_many_i2, a_3_i, QtWidgets.QTableWidgetItem(a_3_text)
                    )
            tvguide_many_table.setHorizontalHeaderLabels(
                [
                    time.strftime("%H:%M", time.localtime()),
                    time.strftime("%H:%M", time.localtime()),
                ]
            )
            if not tvguide_many_win.isVisible():
                moveWindowToCenter(tvguide_many_win)
                tvguide_many_win.show()
                moveWindowToCenter(tvguide_many_win)
            else:
                tvguide_many_win.hide()

        tvguide_many = QtWidgets.QPushButton()
        tvguide_many.setText(_("TV guide"))
        tvguide_many.clicked.connect(tvguide_many_clicked)

        tvguide_widget = QtWidgets.QWidget()
        tvguide_layout = QtWidgets.QHBoxLayout()
        tvguide_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        tvguide_layout.addWidget(tvguide_many)
        tvguide_widget.setLayout(tvguide_layout)

        channelfilter = MyLineEdit()
        channelfilter.click_event.connect(channelfilter_clicked)
        channelfilter.setPlaceholderText(_("Search channel"))
        channelfiltersearch = QtWidgets.QPushButton()
        channelfiltersearch.setText(_("Search"))
        channelfiltersearch.clicked.connect(channelfilter_do)
        channelfilter.returnPressed.connect(channelfilter_do)
        widget3 = QtWidgets.QWidget()
        layout3 = QtWidgets.QHBoxLayout()
        layout3.addWidget(channelfilter)
        layout3.addWidget(channelfiltersearch)
        widget3.setLayout(layout3)
        widget4 = QtWidgets.QWidget()
        layout4 = QtWidgets.QHBoxLayout()
        layout4.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop
        )
        page_lbl = QtWidgets.QLabel("{}:".format(_("Page")))
        of_lbl = QtWidgets.QLabel()
        page_box = QtWidgets.QSpinBox()
        page_box.setSuffix("        ")
        page_box.setMinimum(1)
        page_box.setMaximum(round(len(array) / 100) + 1)
        if platform.system() == "Windows":
            page_box.setStyleSheet(
                """
                QSpinBox::down-button  {
                  subcontrol-origin: margin;
                  subcontrol-position: center left;
                  left: 1px;
                  height: 24px;
                  width: 24px;
                }

                QSpinBox::up-button  {
                  subcontrol-origin: margin;
                  subcontrol-position: center right;
                  right: 1px;
                  height: 24px;
                  width: 24px;
                }
            """
            )
        else:
            page_box.setStyleSheet(
                """
                QSpinBox::down-button  {
                  subcontrol-origin: margin;
                  subcontrol-position: center left;
                  left: 1px;
                  image: url("""
                + str(Path("yuki_iptv", ICONS_FOLDER, "leftarrow.png"))
                + """);
                  height: 24px;
                  width: 24px;
                }

                QSpinBox::up-button  {
                  subcontrol-origin: margin;
                  subcontrol-position: center right;
                  right: 1px;
                  image: url("""
                + str(Path("yuki_iptv", ICONS_FOLDER, "rightarrow.png"))
                + """);
                  height: 24px;
                  width: 24px;
                }
            """
            )
        page_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        of_lbl.setText(get_of_txt(round(len(array) / 100) + 1))

        def page_change():
            win.listWidget.verticalScrollBar().setValue(0)
            redraw_chans()

        page_box.valueChanged.connect(page_change)
        layout4.addWidget(page_lbl)
        layout4.addWidget(page_box)
        layout4.addWidget(of_lbl)
        widget4.setLayout(layout4)
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        layout.setSpacing(0)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.layout().addWidget(QtWidgets.QLabel())
        widget.layout().addWidget(playmode_selector)
        widget.layout().addWidget(combobox)
        # == Movies start ==
        movies_combobox.hide()
        widget.layout().addWidget(movies_combobox)
        # == Movies end ==
        widget.layout().addWidget(widget3)
        widget.layout().addWidget(win.listWidget)
        # Movies start
        win.moviesWidget.hide()
        widget.layout().addWidget(win.moviesWidget)
        # Movies end
        # Series start
        win.seriesWidget.hide()
        widget.layout().addWidget(win.seriesWidget)
        # Series end
        widget.layout().addWidget(widget4)
        widget.layout().addWidget(chan)
        widget.layout().addWidget(loading)
        dockWidget.setFixedWidth(DOCK_WIDGET_WIDTH)
        dockWidget.setTitleBarWidget(QtWidgets.QWidget())
        dockWidget.setWidget(widget)
        dockWidget.setFloating(False)
        dockWidget.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )
        if settings["panelposition"] == 0:
            win.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dockWidget)
        else:
            win.addDockWidget(QtCore.Qt.DockWidgetArea.LeftDockWidgetArea, dockWidget)

        FORBIDDEN_CHARS = ('"', "*", ":", "<", ">", "?", "\\", "/", "|", "[", "]")

        def do_screenshot():
            global l1, time_stop, playing_chan
            if playing_chan:
                l1.show()
                l1.setText2(_("Doing screenshot..."))
                ch = playing_chan.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                file_name = "screenshot_-_" + cur_time + "_-_" + ch + ".png"
                if not settings["scrrecnosubfolders"]:
                    file_path = str(Path(save_folder, "screenshots", file_name))
                else:
                    file_path = str(Path(save_folder, file_name))
                try:
                    player.screenshot_to_file(file_path, includes="subtitles")
                    l1.show()
                    l1.setText2(_("Screenshot saved!"))
                except Exception:
                    l1.show()
                    l1.setText2(_("Screenshot saving error!"))
                time_stop = time.time() + 1
            else:
                l1.show()
                l1.setText2("{}!".format(_("No channel selected")))
                time_stop = time.time() + 1

        def update_tvguide(
            chan_1="",
            do_return=False,
            show_all_guides=False,
            mark_integers=False,
            date_selected=None,
        ):
            global item_selected
            if array:
                if not chan_1:
                    if item_selected:
                        chan_2 = item_selected
                    else:
                        chan_2 = sorted(array.items())[0][0]
                else:
                    chan_2 = chan_1
                try:
                    chan_1_item = getArrayItem(chan_1)
                except Exception:
                    chan_1_item = None
                txt = _("No TV guide for channel")
                chan_2 = chan_2.lower()
                newline_symbol = "\n"
                if do_return:
                    newline_symbol = "!@#$%^^&*("
                try:
                    chan_3 = prog_match_arr[chan_2]
                except Exception:
                    chan_3 = chan_2
                if exists_in_epg(chan_3, programmes):
                    txt = newline_symbol
                    prog = get_epg(programmes, chan_3)
                    for pr in prog:
                        override_this = False
                        if show_all_guides:
                            override_this = pr["start"] < time.time() + 1
                        else:
                            override_this = pr["stop"] > time.time() - 1
                        archive_btn = ""
                        if date_selected is not None:
                            override_this = pr["start"] > date_selected - 1 and pr[
                                "start"
                            ] < (date_selected + 86401)
                        if override_this:
                            def_placeholder = "%d.%m.%y %H:%M"
                            if mark_integers:
                                def_placeholder = "%d.%m.%Y %H:%M:%S"
                            start_2 = (
                                datetime.datetime.fromtimestamp(pr["start"]).strftime(
                                    def_placeholder
                                )
                                + " - "
                            )
                            stop_2 = (
                                datetime.datetime.fromtimestamp(pr["stop"]).strftime(
                                    def_placeholder
                                )
                                + "\n"
                            )
                            try:
                                title_2 = pr["title"] if "title" in pr else ""
                            except Exception:
                                title_2 = ""
                            try:
                                desc_2 = (
                                    ("\n" + pr["desc"] + "\n") if "desc" in pr else ""
                                )
                            except Exception:
                                desc_2 = ""
                            attach_1 = ""
                            if mark_integers:
                                try:
                                    marked_integer = prog.index(pr)
                                except Exception:
                                    marked_integer = -1
                                attach_1 = f" ({marked_integer})"
                            if (
                                date_selected is not None
                                and settings["catchupenable"]
                                and showonlychplaylist_chk.isChecked()
                            ):
                                try:
                                    catchup_days2 = int(chan_1_item["catchup-days"])
                                except Exception:
                                    catchup_days2 = 7
                                # support for seconds
                                if catchup_days2 < 1000:
                                    catchup_days2 = catchup_days2 * 86400
                                if (
                                    pr["start"] < time.time() + 1
                                    and not (
                                        time.time() > pr["start"]
                                        and time.time() < pr["stop"]
                                    )
                                    and pr["stop"] > time.time() - catchup_days2
                                ):
                                    archive_link = urllib.parse.quote_plus(
                                        json.dumps(
                                            [
                                                chan_1,
                                                datetime.datetime.fromtimestamp(
                                                    pr["start"]
                                                ).strftime("%d.%m.%Y %H:%M:%S"),
                                                datetime.datetime.fromtimestamp(
                                                    pr["stop"]
                                                ).strftime("%d.%m.%Y %H:%M:%S"),
                                                prog.index(pr),
                                            ]
                                        )
                                    )
                                    archive_btn = (
                                        '\n<a href="#__archive__'
                                        + archive_link
                                        + '">'
                                        + _("Open archive")
                                        + "</a>"
                                    )
                            start_symbl = ""
                            stop_symbl = ""
                            if YukiData.use_dark_icon_theme:
                                start_symbl = '<span style="color: white;">'
                                stop_symbl = "</span>"
                            use_epg_color = "green"
                            if time.time() > pr["start"] and time.time() < pr["stop"]:
                                use_epg_color = "red"
                            txt += (
                                f'<span style="color: {use_epg_color};">'
                                + start_2
                                + stop_2
                                + "</span>"
                                + start_symbl
                                + "<b>"
                                + title_2
                                + "</b>"
                                + archive_btn
                                + desc_2
                                + attach_1
                                + stop_symbl
                                + newline_symbol
                            )
                if do_return:
                    return txt
                txt = txt.replace("\n", "<br>").replace("<br>", "", 1)
                tvguide_lbl.setText(txt)
            return ""

        def show_tvguide():
            if tvguide_lbl.isVisible():
                tvguide_lbl.setText("")
                tvguide_lbl.hide()
                tvguide_close_lbl.hide()
            else:
                update_tvguide()
                tvguide_lbl.show()
                tvguide_close_lbl.show()

        def hide_tvguide():
            if tvguide_lbl.isVisible():
                tvguide_lbl.setText("")
                tvguide_lbl.hide()
                tvguide_close_lbl.hide()

        def update_tvguide_2():
            epg_win_checkbox.clear()
            if showonlychplaylist_chk.isChecked():
                for chan_0 in array:
                    epg_win_count.setText("({}: {})".format(_("channels"), len(array)))
                    epg_win_checkbox.addItem(chan_0)
            else:
                for chan_0 in programmes:
                    epg_win_count.setText(
                        "({}: {})".format(_("channels"), len(programmes))
                    )
                    epg_win_checkbox.addItem(chan_0)

        def show_tvguide_2():
            if epg_win.isVisible():
                epg_win.hide()
            else:
                epg_index = epg_win_checkbox.currentIndex()
                update_tvguide_2()
                if epg_index != -1:
                    epg_win_checkbox.setCurrentIndex(epg_index)
                epg_win.show()

        def show_archive():
            if not epg_win.isVisible():
                show_tvguide_2()
                find_chan = item_selected
                if not find_chan:
                    find_chan = playing_chan
                if find_chan:
                    try:
                        find_chan_index = epg_win_checkbox.findText(
                            find_chan, QtCore.Qt.MatchFlag.MatchExactly
                        )
                    except Exception:
                        find_chan_index = -1
                    if find_chan_index != -1:
                        epg_win_checkbox.setCurrentIndex(find_chan_index)
                epg_date_changed(epg_select_date.selectedDate())
            else:
                epg_win.hide()

        is_recording = False
        recording_time = 0
        record_file = None

        def start_record(ch1, url3):
            global is_recording, record_file, time_stop, recording_time
            orig_channel_name = ch1
            if not is_recording:
                is_recording = True
                lbl2.show()
                lbl2.setText(_("Preparing record"))
                ch = ch1.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
                if not settings["scrrecnosubfolders"]:
                    out_file = str(
                        Path(
                            save_folder,
                            "recordings",
                            "recording_-_" + cur_time + "_-_" + ch + ".mkv",
                        )
                    )
                else:
                    out_file = str(
                        Path(
                            save_folder, "recording_-_" + cur_time + "_-_" + ch + ".mkv"
                        )
                    )
                record_file = out_file
                record(
                    url3,
                    out_file,
                    orig_channel_name,
                    f"Referer: {settings['referer']}",
                    get_ua_ref_for_channel,
                )
            else:
                is_recording = False
                recording_time = 0
                stop_record()
                lbl2.setText("")
                lbl2.hide()

        def do_record():
            global time_stop
            if playing_chan:
                start_record(playing_chan, playing_url)
            else:
                time_stop = time.time() + 1
                l1.show()
                l1.setText2(_("No channel selected for record"))

        def my_log(mpv_loglevel1, component, message):
            mpv_log_str = f"[{mpv_loglevel1}] {component}: {message}"
            if "Invalid video timestamp: " not in str(mpv_log_str):
                if "[debug] " in str(mpv_log_str):
                    mpv_logger.debug(str(mpv_log_str))
                else:
                    mpv_logger.info(str(mpv_log_str))

        def playLastChannel():
            global playing_url, playing_chan, combobox, m3u
            isPlayingLast = False
            if (
                os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json")))
                and settings["openprevchan"]
            ):
                try:
                    lastfile_1 = open(
                        str(Path(LOCAL_DIR, "lastchannels.json")), "r", encoding="utf8"
                    )
                    lastfile_1_dat = json.loads(lastfile_1.read())
                    lastfile_1.close()
                    if lastfile_1_dat[0] in m3u:
                        isPlayingLast = True
                        player.user_agent = lastfile_1_dat[2]
                        setChanText("  " + lastfile_1_dat[0])
                        itemClicked_event(lastfile_1_dat[0])
                        setChanText("  " + lastfile_1_dat[0])
                        try:
                            if lastfile_1_dat[3] < combobox.count():
                                combobox.setCurrentIndex(lastfile_1_dat[3])
                        except Exception:
                            pass
                        try:
                            win.listWidget.setCurrentRow(lastfile_1_dat[4])
                        except Exception:
                            pass
                except Exception:
                    if os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json"))):
                        os.remove(str(Path(LOCAL_DIR, "lastchannels.json")))
            return isPlayingLast

        VIDEO_OUTPUT = "gpu,x11" if platform.system() == "Linux" else ""
        HWACCEL = "auto-safe" if settings["hwaccel"] else "no"

        # Wayland fix
        is_apply_wayland_fix = False

        if "WAYLAND_DISPLAY" in os.environ:
            if os.environ["WAYLAND_DISPLAY"]:
                logger.info("Found environ WAYLAND_DISPLAY")
                is_apply_wayland_fix = True
        if "XDG_SESSION_TYPE" in os.environ:
            if os.environ["XDG_SESSION_TYPE"] == "wayland":
                logger.info("Environ XDG_SESSION_TYPE == wayland")
                is_apply_wayland_fix = True

        if is_apply_wayland_fix:
            logger.info("")
            logger.info("[NOTE] Applying video output fix for Wayland")
            VIDEO_OUTPUT = "x11"

        options = {
            "vo": VIDEO_OUTPUT,
            "hwdec": HWACCEL,
            "cursor-autohide": 1000,
            "force-window": True,
        }
        options_orig = options.copy()
        options_2 = {}
        try:
            mpv_options_1 = settings["mpv_options"]
            if "=" in mpv_options_1:
                pairs = mpv_options_1.split()
                for pair in pairs:
                    key, value = pair.split("=")
                    options[key.replace("--", "")] = value
                    options_2[key.replace("--", "")] = value
        except Exception as e1:
            logger.warning("Could not parse MPV options!")
            logger.warning(e1)
        logger.info("Testing custom mpv options...")
        logger.info(options_2)
        try:
            test_options = mpv.MPV(**options_2)
            logger.info("mpv options OK")
        except Exception:
            logger.warning("mpv options test failed, ignoring them")
            msg_wrongmpvoptions = QtWidgets.QMessageBox(
                qt_icon_warning,
                MAIN_WINDOW_TITLE,
                _("Custom MPV options invalid, ignoring them")
                + "\n\n"
                + str(json.dumps(options_2)),
                QtWidgets.QMessageBox.StandardButton.Ok,
            )
            msg_wrongmpvoptions.exec()
            options = options_orig

        logger.info(f"Using mpv options: {json.dumps(options)}")

        player = None

        QT_URL = "<a href='https://www.qt.io/'>https://www.qt.io/</a>"
        MPV_URL = "<a href='https://mpv.io/'>mpv</a> "
        CLICKABLE_LINKS = [
            "https://github.com/Ame-chan-angel",
            "https://github.com/yuki-iptv/yuki-iptv",
            "https://fontawesome.com/",
            "https://creativecommons.org/licenses/by/4.0/",
        ]

        def format_about_text(about_txt):
            about_txt += "\n\n" + _("Using Qt {} ({})").format(
                QtCore.QT_VERSION_STR, qt_library
            )
            mpv_version = player.mpv_version
            if " " in mpv_version:
                mpv_version = mpv_version.split(" ", 1)[1]
            if not mpv_version:
                mpv_version = "UNKNOWN"
            about_txt += "\n" + _("Using libmpv {}").format(mpv_version)
            about_txt += "\n\nhttps://github.com/yuki-iptv/yuki-iptv"
            about_txt = about_txt.replace("\n", "<br>")
            for clickable_link in CLICKABLE_LINKS:
                about_txt = about_txt.replace(
                    clickable_link, f"<a href='{clickable_link}'>{clickable_link}</a>"
                )
            return about_txt

        # logger.info("")
        # logger.info(f"M3U: '{settings['m3u'}' EPG: '{settings['epg']}'")
        # logger.info("")

        def main_channel_settings():
            global item_selected, playing_chan
            if playing_chan:
                item_selected = playing_chan
                settings_context_menu()
            else:
                msg = QtWidgets.QMessageBox(
                    qt_icon_warning,
                    MAIN_WINDOW_TITLE,
                    _("No channel selected"),
                    QtWidgets.QMessageBox.StandardButton.Ok,
                )
                msg.exec()

        @idle_function
        def showhideplaylist(arg33=None):
            global fullscreen
            if not fullscreen:
                try:
                    key_t()
                except Exception:
                    pass

        @idle_function
        def lowpanel_ch_1(arg33=None):
            global fullscreen
            if not fullscreen:
                try:
                    lowpanel_ch()
                except Exception:
                    pass

        def showhideeverything():
            global fullscreen
            if not fullscreen:
                if dockWidget.isVisible():
                    YukiData.compact_mode = True
                    dockWidget.hide()
                    dockWidget2.hide()
                    win.menu_bar_qt.hide()
                else:
                    YukiData.compact_mode = False
                    dockWidget.show()
                    dockWidget2.show()
                    win.menu_bar_qt.show()

        stream_info.data = {}

        def process_stream_info(
            dat_count, name44, stream_props_out, stream_info_lbname
        ):
            bold_fnt = QtGui.QFont()
            bold_fnt.setBold(True)

            if stream_info_lbname:
                la2 = QtWidgets.QLabel()
                la2.setStyleSheet("color:green")
                la2.setFont(bold_fnt)
                la2.setText("\n" + stream_info_lbname + "\n")
                layout36.addWidget(la2, dat_count, 0)
                dat_count += 1

            la1 = QtWidgets.QLabel()
            la1.setFont(bold_fnt)
            la1.setText(name44)
            layout36.addWidget(la1, dat_count, 0)

            for dat1 in stream_props_out:
                dat_count += 1
                wdg1 = QtWidgets.QLabel()
                wdg2 = QtWidgets.QLabel()
                wdg1.setText(str(dat1))
                wdg2.setText(str(stream_props_out[dat1]))

                if (
                    str(dat1) == _("Average Bitrate")
                    and stream_props_out == stream_info.video_properties[_("General")]
                ):
                    stream_info.data["video"] = [wdg2, stream_props_out]

                if (
                    str(dat1) == _("Average Bitrate")
                    and stream_props_out == stream_info.audio_properties[_("General")]
                ):
                    stream_info.data["audio"] = [wdg2, stream_props_out]

                layout36.addWidget(wdg1, dat_count, 0)
                layout36.addWidget(wdg2, dat_count, 1)
            return dat_count + 1

        def thread_bitrate():
            try:
                if streaminfo_win.isVisible():
                    if "video" in stream_info.data:
                        stream_info.data["video"][0].setText(
                            stream_info.data["video"][1][_("Average Bitrate")]
                        )
                    if "audio" in stream_info.data:
                        stream_info.data["audio"][0].setText(
                            stream_info.data["audio"][1][_("Average Bitrate")]
                        )
            except Exception:
                pass

        def open_stream_info():
            global playing_chan, time_stop
            if playing_chan:
                for stream_info_i in reversed(range(layout36.count())):
                    layout36.itemAt(stream_info_i).widget().setParent(None)

                stream_props = [
                    stream_info.video_properties[_("General")],
                    stream_info.video_properties[_("Color")],
                    stream_info.audio_properties[_("General")],
                    stream_info.audio_properties[_("Layout")],
                ]

                dat_count = 1
                stream_info_video_lbl = QtWidgets.QLabel(_("Video") + "\n")
                stream_info_video_lbl.setStyleSheet("color:green")
                bold_fnt_2 = QtGui.QFont()
                bold_fnt_2.setBold(True)
                stream_info_video_lbl.setFont(bold_fnt_2)
                layout36.addWidget(stream_info_video_lbl, 0, 0)
                dat_count = process_stream_info(
                    dat_count, _("General"), stream_props[0], ""
                )
                dat_count = process_stream_info(
                    dat_count, _("Color"), stream_props[1], ""
                )
                dat_count = process_stream_info(
                    dat_count, _("General"), stream_props[2], _("Audio")
                )
                dat_count = process_stream_info(
                    dat_count, _("Layout"), stream_props[3], ""
                )

                if not streaminfo_win.isVisible():
                    streaminfo_win.show()
                    moveWindowToCenter(streaminfo_win)
                else:
                    streaminfo_win.hide()
            else:
                l1.show()
                l1.setText2("{}!".format(_("No channel selected")))
                time_stop = time.time() + 1

        streaminfo_win.setWindowTitle(_("Stream Information"))

        def is_recording_func():
            global ffmpeg_processes
            ret_code_rec = False
            if ffmpeg_processes:
                ret_code_array = []
                for ffmpeg_process_1 in ffmpeg_processes:
                    if ffmpeg_process_1[0].processId() == 0:
                        ret_code_array.append(True)
                        ffmpeg_processes.remove(ffmpeg_process_1)
                    else:
                        ret_code_array.append(False)
                ret_code_rec = False not in ret_code_array
            else:
                ret_code_rec = True
            return ret_code_rec

        win.oldpos = None

        force_turnoff_osc = False

        def redraw_menubar():
            global playing_chan
            try:
                update_menubar(
                    player.track_list,
                    playing_chan,
                    settings["m3u"],
                    str(Path(LOCAL_DIR, "alwaysontop.json")),
                )
            except Exception:
                logger.warning("redraw_menubar failed")
                show_exception("redraw_menubar failed\n\n" + traceback.format_exc())

        right_click_menu = QtWidgets.QMenu()

        @idle_function
        def do_reconnect1(unused=None):
            global playing_chan
            if playing_chan:
                logger.info("Reconnecting to stream")
                try:
                    doPlay(*comm_instance.do_play_args)
                except Exception:
                    logger.warning("Failed reconnecting to stream - no known URL")

        @async_gui_blocking_function
        def do_reconnect1_async():
            time.sleep(1)
            do_reconnect1()

        @idle_function
        def end_file_error_callback(unused=None):
            if loading.isVisible():
                mpv_stop()
                chan.setText("")
                loading.setText(_("Playing error"))
                loading.setStyleSheet("color: red")
                showLoading()
                loading1.hide()
                loading_movie.stop()

        @idle_function
        def end_file_callback(unused=None):
            global playing_chan
            if playing_chan and player.path is None:
                if settings["autoreconnection"] and playing_group == 0:
                    logger.info("Connection to stream lost, waiting 1 sec...")
                    do_reconnect1_async()
                else:
                    mpv_stop()

        @idle_function
        def file_loaded_callback(unused=None):
            global playing_chan
            if playing_chan:
                redraw_menubar()

        @idle_function
        def my_mouse_right_callback(unused=None):
            global right_click_menu
            _exec(right_click_menu, QtGui.QCursor.pos())

        @idle_function
        def my_mouse_left_callback(unused=None):
            global right_click_menu, fullscreen
            if right_click_menu.isVisible():
                right_click_menu.hide()

        @idle_function
        def my_up_binding_execute(unused=None):
            global l1, time_stop
            if settings["mouseswitchchannels"]:
                next_channel()
            else:
                volume = int(player.volume + settings["volumechangestep"])
                volume = min(volume, 200)
                label7.setValue(volume)
                mpv_volume_set()

        @idle_function
        def my_down_binding_execute(unused=None):
            global l1, time_stop, fullscreen
            if settings["mouseswitchchannels"]:
                prev_channel()
            else:
                volume = int(player.volume - settings["volumechangestep"])
                volume = max(volume, 0)
                time_stop = time.time() + 3
                show_volume(volume)
                label7.setValue(volume)
                mpv_volume_set()

        dockWidget2 = QtWidgets.QDockWidget(win)

        dockWidget.setObjectName("dockWidget")
        dockWidget2.setObjectName("dockWidget2")

        def open_recording_folder():
            absolute_path = Path(save_folder).absolute()
            if platform.system() == "Linux":
                xdg_open = subprocess.Popen(["xdg-open", str(absolute_path)])
                xdg_open.wait()
            else:
                webbrowser.open("file:///" + str(absolute_path))

        def go_channel(i1):
            row = win.listWidget.currentRow()
            if row == -1:
                row = row0
            next_row = row + i1
            next_row = max(next_row, 0)
            next_row = min(next_row, win.listWidget.count() - 1)
            win.listWidget.setCurrentRow(next_row)
            itemClicked_event(win.listWidget.currentItem())

        @idle_function
        def prev_channel(unused=None):
            go_channel(-1)

        @idle_function
        def next_channel(unused=None):
            go_channel(1)

        if qt_library == "PyQt6" or qt_library == "PySide6":
            qaction_prio = QtGui.QAction.Priority.HighPriority
        else:
            qaction_prio = QtWidgets.QAction.Priority.HighPriority

        def get_keybind(func1):
            return main_keybinds[func1]

        stopped = False

        # MPRIS
        mpris_loop = None
        try:

            class MyAppAdapter(MprisAdapter):
                def metadata(self) -> dict:
                    channel_keys = list(array.keys())
                    mpris_trackid = str(
                        channel_keys.index(playing_chan) + 1
                        if playing_chan in channel_keys
                        else 0
                    )
                    metadata = {
                        "mpris:trackid": f"/com/yuki/iptv/playlist/{mpris_trackid}",
                        "xesam:url": playing_url,
                        "xesam:title": playing_chan,
                    }
                    return metadata

                def can_quit(self) -> bool:
                    return True

                def quit(self):
                    key_quit()

                def can_raise(self) -> bool:
                    return False

                def can_fullscreen(self) -> bool:
                    return False

                def has_tracklist(self) -> bool:
                    return False

                def get_current_position(self) -> Microseconds:
                    return player.time_pos * 1000000 if player.time_pos else 0

                def next(self):
                    next_channel()

                def previous(self):
                    prev_channel()

                def pause(self):
                    mpv_play()

                def resume(self):
                    mpv_play()

                def stop(self):
                    mpv_stop()

                def play(self):
                    mpv_play()

                def get_playstate(self) -> PlayState:
                    if playing_chan:
                        if player.pause:
                            return PlayState.PAUSED
                        else:
                            return PlayState.PLAYING
                    else:
                        return PlayState.STOPPED

                def seek(self, time: Microseconds):
                    pass

                def open_uri(self, uri: str):
                    pass

                def is_repeating(self) -> bool:
                    return False

                def is_playlist(self) -> bool:
                    return self.can_go_next() or self.can_go_previous()

                def set_repeating(self, val: bool):
                    pass

                def set_loop_status(self, val: str):
                    pass

                def get_rate(self) -> RateDecimal:
                    return DEFAULT_RATE

                def set_rate(self, val: RateDecimal):
                    pass

                def get_shuffle(self) -> bool:
                    return False

                def set_shuffle(self, val: bool):
                    return False

                def get_art_url(self, track: int) -> str:
                    return ""

                def get_volume(self) -> VolumeDecimal:
                    return player.volume / 100

                def set_volume(self, val: VolumeDecimal):
                    label7.setValue(int(val * 100))
                    mpv_volume_set()

                def is_mute(self) -> bool:
                    return player.mute

                def set_mute(self, val: bool):
                    mpv_override_mute(val)

                def can_go_next(self) -> bool:
                    return True

                def can_go_previous(self) -> bool:
                    return True

                def can_play(self) -> bool:
                    return True

                def can_pause(self) -> bool:
                    return True

                def can_seek(self) -> bool:
                    return False

                def can_control(self) -> bool:
                    return True

                def get_stream_title(self) -> str:
                    return playing_chan

                def get_previous_track(self) -> Track:
                    return ""

                def get_next_track(self) -> Track:
                    return ""

            # create mpris adapter and initialize mpris server
            my_adapter = MyAppAdapter()
            mpris = Server("yuki_iptv_" + str(os.getpid()), adapter=my_adapter)
            event_handler = EventAdapter(mpris.player, mpris.root)

            def wait_until():
                global stopped
                while True:
                    if win.isVisible() or stopped:
                        return True
                    else:
                        time.sleep(0.1)
                return False

            def mpris_loop_start():
                global stopped
                wait_until()
                if not stopped:
                    logger.info("Starting MPRIS loop")
                    try:
                        mpris.publish()
                        mpris_loop.run()
                    except Exception:
                        logger.warning("Failed to start MPRIS loop!")

            mpris_loop = GLib.MainLoop()
            mpris_thread = threading.Thread(target=mpris_loop_start)
            mpris_thread.start()
        except Exception as mpris_e:
            if platform.system() == "Linux":
                logger.warning(mpris_e)
                logger.warning("Failed to set up MPRIS!")

        def update_scheduler_programme():
            channel_list_2 = [chan_name for chan_name in doSort(array)]
            ch_choosed = choosechannel_ch.currentText()
            tvguide_sch.clear()
            if ch_choosed in channel_list_2:
                tvguide_got = re.sub(
                    "<[^<]+?>", "", update_tvguide(ch_choosed, True)
                ).split("!@#$%^^&*(")[2:]
                for tvguide_el in tvguide_got:
                    if tvguide_el:
                        tvguide_sch.addItem(tvguide_el)

        def show_scheduler():
            if scheduler_win.isVisible():
                scheduler_win.hide()
            else:
                choosechannel_ch.clear()
                channel_list = [chan_name for chan_name in doSort(array)]
                for chan1 in channel_list:
                    choosechannel_ch.addItem(chan1)
                if item_selected in channel_list:
                    choosechannel_ch.setCurrentIndex(channel_list.index(item_selected))
                choosechannel_ch.currentIndexChanged.connect(update_scheduler_programme)
                update_scheduler_programme()
                moveWindowToCenter(scheduler_win)
                scheduler_win.show()

        def mpv_volume_set_custom():
            mpv_volume_set()

        record_icon = QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "record.png")))
        record_stop_icon = QtGui.QIcon(
            str(Path("yuki_iptv", ICONS_FOLDER, "stoprecord.png"))
        )

        label3 = QtWidgets.QPushButton()
        label3.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "pause.png"))))
        label3.setToolTip(_("Pause"))
        label3.clicked.connect(mpv_play)
        label4 = QtWidgets.QPushButton()
        label4.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "stop.png"))))
        label4.setToolTip(_("Stop"))
        label4.clicked.connect(mpv_stop)
        label5 = QtWidgets.QPushButton()
        label5.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "fullscreen.png")))
        )
        label5.setToolTip(_("Fullscreen"))
        label5.clicked.connect(mpv_fullscreen)
        label5_0 = QtWidgets.QPushButton()
        label5_0.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "folder.png")))
        )
        label5_0.setToolTip(_("Open recordings folder"))
        label5_0.clicked.connect(open_recording_folder)
        label5_1 = QtWidgets.QPushButton()
        label5_1.setIcon(record_icon)
        label5_1.setToolTip(_("Record"))
        label5_1.clicked.connect(do_record)
        label5_2 = QtWidgets.QPushButton()
        label5_2.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "calendar.png")))
        )
        label5_2.setToolTip(_("Recording scheduler"))
        label5_2.clicked.connect(show_scheduler)
        label6 = QtWidgets.QPushButton()
        label6.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "volume.png"))))
        label6.setToolTip(_("Volume"))
        label6.clicked.connect(mpv_mute)
        LABEL7_SET_WIDTH = 150
        label7 = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        label7.setMinimum(0)
        label7.setMaximum(200)
        label7.setFixedWidth(LABEL7_SET_WIDTH)
        label7.valueChanged.connect(mpv_volume_set_custom)
        label7_1 = QtWidgets.QPushButton()
        label7_1.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "screenshot.png")))
        )
        label7_1.setToolTip(_("Screenshot").capitalize())
        label7_1.clicked.connect(do_screenshot)
        label7_2 = QtWidgets.QPushButton()
        label7_2.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "timeshift.png")))
        )
        label7_2.setToolTip(_("Archive"))
        label7_2.clicked.connect(show_archive)
        if not settings["catchupenable"]:
            label7_2.setVisible(False)
        label8 = QtWidgets.QPushButton()
        label8.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "settings.png")))
        )
        label8.setToolTip(_("Settings"))
        label8.clicked.connect(show_settings)
        label8_0 = QtWidgets.QPushButton()
        label8_0.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "tv-blue.png")))
        )
        label8_0.setToolTip(_("Playlists"))
        label8_0.clicked.connect(show_playlists)
        label8_1 = QtWidgets.QPushButton()
        label8_1.setIcon(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "tvguide.png")))
        )
        label8_1.setToolTip(_("TV guide"))
        label8_1.clicked.connect(show_tvguide)
        label8_4 = QtWidgets.QPushButton()
        label8_4.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "sort.png"))))
        label8_4.setToolTip(_("Channel\nsort").replace("\n", " "))
        label8_4.clicked.connect(show_sort)
        label8_2 = QtWidgets.QPushButton()
        label8_2.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "prev.png"))))
        label8_2.setToolTip(_("Previous channel"))
        label8_2.clicked.connect(prev_channel)
        label8_3 = QtWidgets.QPushButton()
        label8_3.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "next.png"))))
        label8_3.setToolTip(_("Next channel"))
        label8_3.clicked.connect(next_channel)
        label8_5 = QtWidgets.QPushButton()
        label8_5.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "edit.png"))))
        label8_5.setToolTip(_("m3u Editor"))
        label8_5.clicked.connect(show_m3u_editor)
        label9 = QtWidgets.QPushButton()
        label9.setIcon(QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "help.png"))))
        label9.setToolTip(_("Help"))
        label9.clicked.connect(show_help)

        label12 = QtWidgets.QLabel("")
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(12)
        label13 = QtWidgets.QLabel("")
        label13.setMinimumWidth(50)
        label12.setFont(myFont4)
        myFont5 = QtGui.QFont()
        myFont5.setPointSize(12)
        label13.setFont(myFont5)

        hdd_gif_label = QtWidgets.QLabel()
        hdd_gif_label.setPixmap(
            QtGui.QIcon(str(Path("yuki_iptv", ICONS_FOLDER, "hdd.png"))).pixmap(
                QtCore.QSize(32, 32)
            )
        )
        hdd_gif_label.setToolTip("{}...".format(_("Writing EPG cache")))
        hdd_gif_label.setVisible(False)

        progress = QtWidgets.QProgressBar()
        progress.setValue(0)
        start_label = QtWidgets.QLabel()
        stop_label = QtWidgets.QLabel()

        vlayout3 = QtWidgets.QVBoxLayout()
        hlayout1 = QtWidgets.QHBoxLayout()
        hlayout2 = QtWidgets.QHBoxLayout()

        hlayout1.addWidget(start_label)
        hlayout1.addWidget(progress)
        hlayout1.addWidget(stop_label)

        hlayout2_btns = [
            label3,
            label4,
            label5,
            label5_1,
            label5_2,
            label5_0,
            label6,
            label7,
            label13,
            label7_1,
            label7_2,
            label8_1,
            label8_2,
            label8_3,
        ]

        show_lbls_fullscreen = [
            label3,
            label4,
            label5,
            label5_1,
            label6,
            label7,
            label13,
            label7_1,
            label7_2,
            label8_1,
            label8_2,
            label8_3,
        ]

        fs_widget = QtWidgets.QWidget()
        fs_widget_l = QtWidgets.QHBoxLayout()
        label8.setMaximumWidth(32)
        fs_widget_l.addWidget(label8)
        fs_widget.setLayout(fs_widget_l)

        for hlayout2_btn in hlayout2_btns:
            hlayout2.addWidget(hlayout2_btn)
        hlayout2.addStretch(1000000)
        hlayout2.addWidget(label12)
        hlayout2.addWidget(hdd_gif_label)

        vlayout3.addLayout(hlayout2)
        hlayout2.addStretch(1)
        vlayout3.addLayout(hlayout1)

        widget2 = QtWidgets.QWidget()
        widget2.setLayout(vlayout3)
        dockWidget2.setTitleBarWidget(QtWidgets.QWidget())
        dockWidget2.setWidget(widget2)
        dockWidget2.setFloating(False)
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
        dockWidget2.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFeature.NoDockWidgetFeatures
        )
        win.addDockWidget(QtCore.Qt.DockWidgetArea.BottomDockWidgetArea, dockWidget2)

        progress.hide()
        start_label.hide()
        stop_label.hide()
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)

        l1 = QtWidgets.QLabel(win)
        myFont1 = QtGui.QFont()
        myFont1.setPointSize(12)
        myFont1.setBold(True)
        l1.setStyleSheet("background-color: " + BCOLOR)
        l1.setFont(myFont1)
        l1.setWordWrap(True)
        l1.move(50, 50)
        l1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        static_text = ""
        gl_is_static = False
        previous_text = ""

        def set_text_l1(text="", is_previous=False):
            global static_text, gl_is_static, previous_text
            if is_previous:
                text = previous_text
            else:
                previous_text = text
            if gl_is_static:
                br = "    "
                if not text or not static_text:
                    br = ""
                text = static_text + br + text
            win.update()
            l1.setText(text)

        def set_text_static(is_static):
            global gl_is_static, static_text
            static_text = ""
            gl_is_static = is_static

        l1.setText2 = set_text_l1
        l1.setStatic2 = set_text_static
        l1.hide()

        def getUserAgent():
            try:
                userAgent2 = player.user_agent
            except Exception:
                userAgent2 = def_user_agent
            return userAgent2

        def saveLastChannel():
            if playing_url and playmode_selector.currentIndex() == 0:
                current_group_0 = 0
                if combobox.currentIndex() != 0:
                    try:
                        current_group_0 = groups.index(array[playing_chan]["tvg-group"])
                    except Exception:
                        pass
                current_channel_0 = 0
                try:
                    current_channel_0 = win.listWidget.currentRow()
                except Exception:
                    pass
                lastfile = open(
                    str(Path(LOCAL_DIR, "lastchannels.json")), "w", encoding="utf8"
                )
                lastfile.write(
                    json.dumps(
                        [
                            playing_chan,
                            playing_url,
                            getUserAgent(),
                            current_group_0,
                            current_channel_0,
                        ]
                    )
                )
                lastfile.close()
            else:
                if os.path.isfile(str(Path(LOCAL_DIR, "lastchannels.json"))):
                    os.remove(str(Path(LOCAL_DIR, "lastchannels.json")))

        def cur_win_width():
            w1_width = 0
            for app_scr in app.screens():
                w1_width += app_scr.size().width()
            return w1_width

        def cur_win_height():
            w1_height = 0
            for app_scr in app.screens():
                w1_height += app_scr.size().height()
            return w1_height

        def myExitHandler_before():
            global stopped, epg_thread_2, mpris_loop
            if comm_instance.comboboxIndex != -1:
                write_option(
                    "comboboxindex",
                    {"m3u": settings["m3u"], "index": comm_instance.comboboxIndex},
                )
            try:
                if get_first_run():
                    logger.info("Saving active vf filters...")
                    write_option("vf_filters", get_active_vf_filters())
                    logger.info("Active vf filters saved")
            except Exception:
                pass
            try:
                logger.info("Saving main window position / width / height...")
                write_option(
                    "window",
                    {
                        "x": win.geometry().x(),
                        "y": win.geometry().y(),
                        "w": win.width(),
                        "h": win.height(),
                    },
                )
                logger.info("Main window position / width / height saved")
            except Exception:
                pass
            try:
                write_option(
                    "compactstate",
                    {
                        "compact_mode": YukiData.compact_mode,
                        "playlist_hidden": YukiData.playlist_hidden,
                        "controlpanel_hidden": YukiData.controlpanel_hidden,
                    },
                )
            except Exception:
                pass
            try:
                write_option("volume", int(YukiData.volume))
            except Exception:
                pass
            save_player_tracks()
            saveLastChannel()
            stop_record()
            for rec_1 in sch_recordings:
                do_stop_record(rec_1)
            if mpris_loop:
                mpris_loop.quit()
            stopped = True
            if epg_thread_2:
                try:
                    epg_thread_2.kill()
                except Exception:
                    try:
                        epg_thread_2.terminate()
                    except Exception:
                        pass
            if multiprocessing_manager:
                multiprocessing_manager.shutdown()
            for process_3 in active_children():
                try:
                    process_3.kill()
                except Exception:
                    try:
                        process_3.terminate()
                    except Exception:
                        pass

        def myExitHandler():
            myExitHandler_before()
            logger.info("Stopped")
            if not do_save_settings:
                sys.exit(0)

        first_boot_1 = True

        waiting_for_epg = False
        epg_failed = False

        def get_catchup_days(is_seconds=False):
            try:
                catchup_days1 = min(
                    max(
                        1,
                        max(
                            [
                                int(array[xc1]["catchup-days"])
                                for xc1 in array
                                if "catchup-days" in array[xc1]
                            ]
                        ),
                    ),
                    7,
                )
            except Exception:
                catchup_days1 = 7
            if not settings["catchupenable"]:
                catchup_days1 = 7
            if is_seconds:
                catchup_days1 = 86400 * (catchup_days1 + 1)
            return catchup_days1

        logger.info(f"catchup-days = {get_catchup_days()}")

        epg_data = None

        def thread_channels_redraw():
            global ic, multiprocessing_manager_dict
            ic += 0.1
            # redraw every 15 seconds
            if ic > (
                14.9 if not multiprocessing_manager_dict["logos_inprogress"] else 2.9
            ):
                ic = 0
                btn_update.click()

        @idle_function
        def thread_tvguide_update_1():
            global static_text, time_stop
            l1.setStatic2(True)
            l1.show()
            static_text = _("Updating TV guide...")
            l1.setText2("")
            time_stop = time.time() + 3

        @idle_function
        def thread_tvguide_update_2():
            global time_stop
            l1.setStatic2(False)
            l1.show()
            l1.setText2(_("TV guide update error!"))
            time_stop = time.time() + 3

        @async_gui_blocking_function
        def thread_tvguide_update():
            global stopped, first_boot, programmes, btn_update
            global tvguide_sets, epg_updating, waiting_for_epg
            global epg_failed, first_boot_1, multiprocessing_manager_dict
            global epg_update_allowed, epg_data
            while not stopped:
                if not first_boot:
                    first_boot = True
                    if settings["epg"] and not epg_failed:
                        if not use_local_tvguide:
                            update_epg = not settings["donotupdateepg"]
                            if not first_boot_1:
                                update_epg = True
                            if update_epg:
                                if epg_update_allowed:
                                    epg_updating = True
                                    thread_tvguide_update_1()
                                    try:
                                        epg_data = None
                                        waiting_for_epg = True
                                        epg_data = (
                                            get_context("spawn")
                                            .Pool(1)
                                            .apply(
                                                worker,
                                                (
                                                    settings,
                                                    get_catchup_days(),
                                                    multiprocessing_manager_dict,
                                                ),
                                            )
                                        )
                                    except Exception as e1:
                                        epg_failed = True
                                        logger.warning(
                                            "[TV guide, part 1] Caught exception: "
                                            + str(e1)
                                        )
                                        logger.warning(traceback.format_exc())
                                        thread_tvguide_update_2()
                                        epg_updating = False
                            else:
                                logger.info("EPG update at boot disabled")
                            first_boot_1 = False
                        else:
                            programmes = {
                                prog0.lower(): tvguide_sets[prog0]
                                for prog0 in tvguide_sets
                            }
                            btn_update.click()  # start update in main thread
                time.sleep(0.1)

        def thread_record():
            try:
                global time_stop, gl_is_static, static_text, recording_time, ic1
                ic1 += 0.1
                if ic1 > 0.9:
                    ic1 = 0
                    # executing every second
                    if is_recording:
                        if not recording_time:
                            recording_time = time.time()
                        record_time = format_seconds(time.time() - recording_time)
                        if os.path.isfile(record_file):
                            record_size = convert_size(os.path.getsize(record_file))
                            lbl2.setText("REC " + record_time + " - " + record_size)
                        else:
                            recording_time = time.time()
                            lbl2.setText(_("Waiting for record"))
                win.update()
                if (time.time() > time_stop) and time_stop != 0:
                    time_stop = 0
                    if not gl_is_static:
                        l1.hide()
                        win.update()
                    else:
                        l1.setText2("")
            except Exception:
                pass

        x_conn = None

        def do_reconnect():
            global x_conn
            if (playing_chan and not loading.isVisible()) and (
                player.cache_buffering_state == 0
            ):
                logger.info("Reconnecting to stream")
                try:
                    doPlay(*comm_instance.do_play_args)
                except Exception:
                    logger.warning("Failed reconnecting to stream - no known URL")
            x_conn = None

        YukiData.connprinted = False

        def check_connection():
            global x_conn
            if settings["autoreconnection"]:
                if playing_group == 0:
                    if not YukiData.connprinted:
                        YukiData.connprinted = True
                        logger.info("Connection loss detector enabled")
                    try:
                        if (
                            playing_chan and not loading.isVisible()
                        ) and player.cache_buffering_state == 0:
                            if not x_conn:
                                logger.info(
                                    "Connection to stream lost, waiting 5 secs..."
                                )
                                x_conn = QtCore.QTimer()
                                x_conn.timeout.connect(do_reconnect)
                                x_conn.start(5000)
                    except Exception:
                        logger.warning("Failed to set connection loss detector!")
            else:
                if not YukiData.connprinted:
                    YukiData.connprinted = True
                    logger.info("Connection loss detector disabled")

        def thread_check_tvguide_obsolete():
            try:
                global first_boot, ic2
                check_connection()
                try:
                    if player.video_bitrate:
                        bitrate_arr = [
                            _("bps"),
                            _("kbps"),
                            _("Mbps"),
                            _("Gbps"),
                            _("Tbps"),
                        ]
                        video_bitrate = " - " + str(
                            format_bytes(player.video_bitrate, bitrate_arr)
                        )
                    else:
                        video_bitrate = ""
                except Exception:
                    video_bitrate = ""
                try:
                    audio_codec = player.audio_codec.split(" ")[0]
                except Exception:
                    audio_codec = "no audio"
                try:
                    codec = player.video_codec.split(" ")[0]
                    width = player.width
                    height = player.height
                except Exception:
                    codec = "png"
                    width = 800
                    height = 600
                if player.avsync:
                    avsync = str(round(player.avsync, 2))
                    deavsync = round(player.avsync, 2)
                    if deavsync < 0:
                        deavsync = deavsync * -1
                    if deavsync > 0.999:
                        avsync = f"<span style='color: #B58B00;'>{avsync}</span>"
                else:
                    avsync = "0.0"
                if (not (codec == "png" and width == 800 and height == 600)) and (
                    width and height
                ):
                    if settings["hidebitrateinfo"]:
                        label12.setText("")
                    else:
                        label12.setText(
                            f"  {width}x{height}{video_bitrate}"
                            f" - {codec} / {audio_codec} - A-V {avsync}"
                        )
                    if loading.text() == _("Loading..."):
                        hideLoading()
                else:
                    label12.setText("")
                ic2 += 0.1
                if ic2 > 9.9:
                    ic2 = 0
                    if not epg_updating:
                        if not is_program_actual(programmes, epg_ready):
                            force_update_epg()
            except Exception:
                pass

        @idle_function
        def thread_tvguide_update_pt2_1():
            global time_stop
            l1.setStatic2(False)
            l1.show()
            l1.setText2(_("TV guide update done!"))
            time_stop = time.time() + 3

        thread_tvguide_update_pt2_e2 = ""

        @idle_function
        def thread_tvguide_update_pt2_2():
            global time_stop
            l1.setStatic2(False)
            l1.show()
            if "Programme not actual" in str(thread_tvguide_update_pt2_e2):
                l1.setText2(_("EPG is outdated!"))
            else:
                l1.setText2(_("TV guide update error!"))
            time_stop = time.time() + 3

        @async_gui_blocking_function
        def thread_tvguide_update_pt2():
            global stopped, time_stop, first_boot, programmes, btn_update
            global static_text, tvguide_sets, epg_updating, ic
            global waiting_for_epg, epg_failed, prog_ids
            global epg_icons, thread_tvguide_update_pt2_e2
            while not stopped:
                if waiting_for_epg and epg_data and len(epg_data) == 7:
                    try:
                        if not epg_data[3]:
                            raise epg_data[4]
                        thread_tvguide_update_pt2_1()
                        programmes = {
                            prog0.lower(): epg_data[1][prog0] for prog0 in epg_data[1]
                        }
                        if not is_program_actual(programmes, epg_ready):
                            raise Exception("Programme not actual")
                        prog_ids = epg_data[5]
                        epg_icons = epg_data[6]
                        tvguide_sets = programmes
                        save_tvguide_sets()
                        btn_update.click()  # start update in main thread
                    except Exception as e2:
                        epg_failed = True
                        logger.warning(
                            "[TV guide, part 2] Caught exception: " + str(e2)
                        )
                        logger.warning(traceback.format_exc())
                        thread_tvguide_update_pt2_e2 = e2
                        thread_tvguide_update_pt2_2()
                    epg_updating = False
                    waiting_for_epg = False
                time.sleep(1)

        thread_5_lock = False

        def thread_tvguide_progress():
            try:
                global thread_5_lock, waiting_for_epg
                global multiprocessing_manager_dict, static_text
                if not thread_5_lock:
                    thread_5_lock = True
                    try:
                        if waiting_for_epg:
                            if (
                                "epg_progress" in multiprocessing_manager_dict
                                and multiprocessing_manager_dict["epg_progress"]
                            ):
                                static_text = multiprocessing_manager_dict[
                                    "epg_progress"
                                ]
                                l1.setText2(is_previous=True)
                    except Exception:
                        pass
                    thread_5_lock = False
            except Exception:
                pass

        def thread_update_time():
            try:
                scheduler_clock.setText(get_current_time())
            except Exception:
                pass

        def thread_osc():
            try:
                global playing_url, force_turnoff_osc
                if playing_url:
                    if not settings["hidempv"]:
                        try:
                            if not force_turnoff_osc:
                                set_mpv_osc(True)
                            else:
                                set_mpv_osc(False)
                        except Exception:
                            pass
                else:
                    try:
                        set_mpv_osc(False)
                    except Exception:
                        pass
            except Exception:
                pass

        dockWidgetVisible = False
        dockWidget2Visible = False

        dockWidget.installEventFilter(win)

        prev_cursor = QtGui.QCursor.pos()
        last_cursor_moved = 0
        last_cursor_time = 0

        def thread_cursor():
            global fullscreen, prev_cursor, last_cursor_moved, last_cursor_time
            show_cursor = False
            cursor_offset = (
                QtGui.QCursor.pos().x()
                - prev_cursor.x()
                + QtGui.QCursor.pos().y()
                - prev_cursor.y()
            )
            if cursor_offset < 0:
                cursor_offset = cursor_offset * -1
            if cursor_offset > 5:
                prev_cursor = QtGui.QCursor.pos()
                if (time.time() - last_cursor_moved) > 0.3:
                    last_cursor_moved = time.time()
                    last_cursor_time = time.time() + 1
                    show_cursor = True
            show_cursor_really = True
            if not show_cursor:
                show_cursor_really = time.time() < last_cursor_time
            if fullscreen:
                try:
                    if show_cursor_really:
                        win.container.unsetCursor()
                    else:
                        win.container.setCursor(QtCore.Qt.CursorShape.BlankCursor)
                except Exception:
                    pass
            else:
                try:
                    win.container.unsetCursor()
                except Exception:
                    pass

        playlist_widget = QtWidgets.QMainWindow()
        playlist_widget_orig = QtWidgets.QWidget(playlist_widget)
        playlist_widget.setCentralWidget(playlist_widget_orig)
        pl_layout = QtWidgets.QGridLayout()
        pl_layout.setVerticalSpacing(0)
        pl_layout.setContentsMargins(0, 0, 0, 0)
        pl_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        pl_layout.setSpacing(0)
        playlist_widget_orig.setLayout(pl_layout)
        playlist_widget.hide()

        controlpanel_widget = QtWidgets.QWidget()
        cp_layout = QtWidgets.QVBoxLayout()
        controlpanel_widget.setLayout(cp_layout)
        controlpanel_widget.hide()

        def maptoglobal(x6, y6):
            return win.mapToGlobal(QtCore.QPoint(x6, y6))

        def show_playlist():
            if settings["panelposition"] == 0:
                playlist_widget.move(maptoglobal(win.width() - dockWidget.width(), 0))
            else:
                playlist_widget.move(maptoglobal(0, 0))
            playlist_widget.setFixedWidth(dockWidget.width())
            playlist_widget_height = win.height() - 50
            playlist_widget.resize(playlist_widget.width(), playlist_widget_height)
            playlist_widget.setWindowOpacity(0.55)
            playlist_widget.setWindowFlags(
                QtCore.Qt.WindowType.CustomizeWindowHint
                | QtCore.Qt.WindowType.FramelessWindowHint
                | QtCore.Qt.WindowType.X11BypassWindowManagerHint
            )
            pl_layout.addWidget(widget)
            playlist_widget.show()

        def hide_playlist():
            pl_layout.removeWidget(widget)
            dockWidget.setWidget(widget)
            playlist_widget.hide()

        LABEL7_WIDTH = False

        def resizeandmove_controlpanel():
            lb2_width = 0
            cur_screen = QtWidgets.QApplication.primaryScreen()
            try:
                cur_screen = win.screen()
            except Exception:
                pass
            cur_width = cur_screen.availableGeometry().width()
            controlpanel_widget.setFixedWidth(cur_width)
            for lb2_wdg in show_lbls_fullscreen:
                if hlayout2.indexOf(lb2_wdg) != -1 and lb2_wdg.isVisible():
                    lb2_width += lb2_wdg.width() + 10
            controlpanel_widget.setFixedWidth(lb2_width + 30)
            p_3 = (
                win.container.frameGeometry().center()
                - QtCore.QRect(QtCore.QPoint(), controlpanel_widget.sizeHint()).center()
            )
            controlpanel_widget.move(maptoglobal(p_3.x() - 100, win.height() - 100))

        def show_controlpanel():
            global LABEL7_WIDTH
            if not LABEL7_WIDTH:
                LABEL7_WIDTH = label7.width()
            label7.setFixedWidth(LABEL7_SET_WIDTH)
            controlpanel_widget.setWindowOpacity(0.55)
            if channelfilter.usePopup:
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                    | QtCore.Qt.WindowType.Popup
                )
            else:
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.WindowType.CustomizeWindowHint
                    | QtCore.Qt.WindowType.FramelessWindowHint
                    | QtCore.Qt.WindowType.X11BypassWindowManagerHint
                )
            cp_layout.addWidget(widget2)
            resizeandmove_controlpanel()
            controlpanel_widget.show()
            resizeandmove_controlpanel()

        def hide_controlpanel():
            if LABEL7_WIDTH:
                label7.setFixedWidth(LABEL7_WIDTH)
            cp_layout.removeWidget(widget2)
            dockWidget2.setWidget(widget2)
            controlpanel_widget.hide()

        def thread_afterrecord():
            try:
                cur_recording = False
                if not lbl2.isVisible():
                    if "REC / " not in lbl2.text():
                        cur_recording = is_ffmpeg_recording() is False
                    else:
                        cur_recording = not is_recording_func() is True
                    if cur_recording:
                        showLoading2()
                    else:
                        hideLoading2()
            except Exception:
                pass

        win_has_focus = False

        def is_win_has_focus():
            return (
                win.isActiveWindow()
                or help_win.isActiveWindow()
                or streaminfo_win.isActiveWindow()
                or license_win.isActiveWindow()
                or sort_win.isActiveWindow()
                or chan_win.isActiveWindow()
                or ext_win.isActiveWindow()
                or scheduler_win.isActiveWindow()
                or xtream_win.isActiveWindow()
                or xtream_win_2.isActiveWindow()
                or playlists_win.isActiveWindow()
                or playlists_win_edit.isActiveWindow()
                or epg_select_win.isActiveWindow()
                or tvguide_many_win.isActiveWindow()
                or m3u_editor.isActiveWindow()
                or settings_win.isActiveWindow()
                or shortcuts_win.isActiveWindow()
                or shortcuts_win_2.isActiveWindow()
            )

        def is_other_wins_has_focus():
            return (
                help_win.isActiveWindow()
                or streaminfo_win.isActiveWindow()
                or license_win.isActiveWindow()
                or sort_win.isActiveWindow()
                or chan_win.isActiveWindow()
                or ext_win.isActiveWindow()
                or scheduler_win.isActiveWindow()
                or xtream_win.isActiveWindow()
                or xtream_win_2.isActiveWindow()
                or playlists_win.isActiveWindow()
                or playlists_win_edit.isActiveWindow()
                or epg_select_win.isActiveWindow()
                or tvguide_many_win.isActiveWindow()
                or m3u_editor.isActiveWindow()
                or settings_win.isActiveWindow()
                or shortcuts_win.isActiveWindow()
                or shortcuts_win_2.isActiveWindow()
            )

        menubar_st = False
        YukiData.fcstate = True

        def thread_shortcuts():
            global fullscreen, menubar_st, win_has_focus
            try:
                if not fullscreen:
                    menubar_new_st = win.menuBar().isVisible()
                    if menubar_new_st != menubar_st:
                        menubar_st = menubar_new_st
                        if menubar_st:
                            setShortcutState(False)
                        else:
                            setShortcutState(True)
            except Exception:
                pass

        def thread_mouse():
            try:
                global fullscreen, key_t_visible, dockWidgetVisible, dockWidget2Visible
                if (
                    l1.isVisible()
                    and l1.text().startswith(_("Volume"))
                    and not is_show_volume()
                ):
                    l1.hide()
                label13.setText(f"{int(player.volume)}%")
                dockWidget.setFixedWidth(DOCK_WIDGET_WIDTH)
                if fullscreen and not key_t_visible:
                    # Check cursor inside window
                    cur_pos = QtGui.QCursor.pos()
                    is_inside_window = (
                        cur_pos.x() > win.pos().x() - 1
                        and cur_pos.x() < (win.pos().x() + win.width())
                    ) and (
                        cur_pos.y() > win.pos().y() - 1
                        and cur_pos.y() < (win.pos().y() + win.height())
                    )
                    # Playlist
                    if settings["showplaylistmouse"]:
                        cursor_x = win.container.mapFromGlobal(QtGui.QCursor.pos()).x()
                        win_width = win.width()
                        if settings["panelposition"] == 0:
                            is_cursor_x = cursor_x > win_width - (
                                DOCK_WIDGET_WIDTH + 10
                            )
                        else:
                            is_cursor_x = cursor_x < (DOCK_WIDGET_WIDTH + 10)
                        if is_cursor_x and cursor_x < win_width and is_inside_window:
                            if not dockWidgetVisible:
                                dockWidgetVisible = True
                                show_playlist()
                        else:
                            dockWidgetVisible = False
                            hide_playlist()
                    # Control panel
                    if settings["showcontrolsmouse"]:
                        cursor_y = win.container.mapFromGlobal(QtGui.QCursor.pos()).y()
                        win_height = win.height()
                        is_cursor_y = cursor_y > win_height - (
                            dockWidget2.height() + 250
                        )
                        if is_cursor_y and cursor_y < win_height and is_inside_window:
                            if not dockWidget2Visible:
                                dockWidget2Visible = True
                                show_controlpanel()
                        else:
                            dockWidget2Visible = False
                            hide_controlpanel()
            except Exception:
                pass

        key_t_visible = False

        def key_t():
            global fullscreen
            if not fullscreen:
                if dockWidget.isVisible():
                    YukiData.playlist_hidden = True
                    dockWidget.hide()
                else:
                    YukiData.playlist_hidden = False
                    dockWidget.show()

        def lowpanel_ch():
            if dockWidget2.isVisible():
                YukiData.controlpanel_hidden = True
                dockWidget2.hide()
            else:
                YukiData.controlpanel_hidden = False
                dockWidget2.show()

        # Key bindings
        def key_quit():
            settings_win.close()
            shortcuts_win.close()
            shortcuts_win_2.close()
            win.close()
            help_win.close()
            streaminfo_win.close()
            license_win.close()
            myExitHandler()
            app.quit()

        def dockwidget_resize_thread():
            try:
                if start_label.text() and start_label.isVisible():
                    if dockWidget2.height() != DOCK_WIDGET2_HEIGHT_HIGH:
                        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
                else:
                    if dockWidget2.height() != DOCK_WIDGET2_HEIGHT_LOW:
                        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
            except Exception:
                pass

        def set_playback_speed(spd):
            global playing_chan
            try:
                if playing_chan:
                    logger.info(f"Set speed to {spd}")
                    player.speed = spd
            except Exception:
                logger.warning("set_playback_speed failed")

        def mpv_seek(secs):
            global playing_chan
            try:
                if playing_chan:
                    logger.info(f"Seeking to {secs} seconds")
                    player.command("seek", secs)
            except Exception:
                logger.warning("mpv_seek failed")

        def change_aot_mode():
            global aot_action, fullscreen
            if not fullscreen:
                if aot_action.isChecked():
                    logger.info("change_aot_mode to False")
                    aot_action.setChecked(False)
                    disable_always_on_top()
                else:
                    logger.info("change_aot_mode to True")
                    aot_action.setChecked(True)
                    enable_always_on_top()

        funcs = {
            "show_sort": show_sort,
            "key_t": key_t,
            "esc_handler": esc_handler,
            "mpv_fullscreen": mpv_fullscreen,
            "mpv_fullscreen_2": mpv_fullscreen,
            "open_stream_info": open_stream_info,
            "mpv_mute": mpv_mute,
            "key_quit": key_quit,
            "mpv_play": mpv_play,
            "mpv_stop": mpv_stop,
            "do_screenshot": do_screenshot,
            "show_tvguide": show_tvguide,
            "do_record": do_record,
            "prev_channel": prev_channel,
            "next_channel": next_channel,
            "(lambda: my_up_binding())": (lambda: my_up_binding_execute()),
            "(lambda: my_down_binding())": (lambda: my_down_binding_execute()),
            "show_timeshift": show_archive,
            "show_scheduler": show_scheduler,
            "showhideeverything": showhideeverything,
            "show_settings": show_settings,
            "(lambda: set_playback_speed(1.00))": (lambda: set_playback_speed(1.00)),
            "app.quit": app.quit,
            "show_playlists": show_playlists,
            "reload_playlist": reload_playlist,
            "force_update_epg": force_update_epg_act,
            "main_channel_settings": main_channel_settings,
            "show_m3u_editor": show_m3u_editor,
            "my_down_binding_execute": my_down_binding_execute,
            "my_up_binding_execute": my_up_binding_execute,
            "(lambda: mpv_seek(-10))": (lambda: mpv_seek(-10)),
            "(lambda: mpv_seek(10))": (lambda: mpv_seek(10)),
            "(lambda: mpv_seek(-60))": (lambda: mpv_seek(-60)),
            "(lambda: mpv_seek(60))": (lambda: mpv_seek(60)),
            "(lambda: mpv_seek(-600))": (lambda: mpv_seek(-600)),
            "(lambda: mpv_seek(600))": (lambda: mpv_seek(600)),
            "lowpanel_ch_1": lowpanel_ch_1,
            "show_tvguide_2": show_tvguide_2,
            "alwaysontop": change_aot_mode,
            # INTERNAL
            "do_record_1_INTERNAL": do_record,
            "mpv_mute_1_INTERNAL": mpv_mute,
            "mpv_play_1_INTERNAL": mpv_play,
            "mpv_play_2_INTERNAL": mpv_play,
            "mpv_play_3_INTERNAL": mpv_play,
            "mpv_play_4_INTERNAL": mpv_play,
            "mpv_stop_1_INTERNAL": mpv_stop,
            "mpv_stop_2_INTERNAL": mpv_stop,
            "next_channel_1_INTERNAL": next_channel,
            "prev_channel_1_INTERNAL": prev_channel,
            "(lambda: my_up_binding())_INTERNAL": (lambda: my_up_binding_execute()),
            "(lambda: my_down_binding())_INTERNAL": (lambda: my_down_binding_execute()),
        }

        mki2 = []
        mki2.append(gettext.ngettext("-%d second", "-%d seconds", 10) % 10)
        mki2.append(gettext.ngettext("+%d second", "+%d seconds", 10) % 10)
        mki2.append(gettext.ngettext("-%d minute", "-%d minutes", 1) % 1)
        mki2.append(gettext.ngettext("+%d minute", "+%d minutes", 1) % 1)
        mki2.append(gettext.ngettext("-%d minute", "-%d minutes", 10) % 10)
        mki2.append(gettext.ngettext("+%d minute", "+%d minutes", 10) % 10)

        main_keybinds_translations = {
            "(lambda: mpv_seek(-10))": mki2[0],
            "(lambda: mpv_seek(-60))": mki2[2],
            "(lambda: mpv_seek(-600))": mki2[4],
            "(lambda: mpv_seek(10))": mki2[1],
            "(lambda: mpv_seek(60))": mki2[3],
            "(lambda: mpv_seek(600))": mki2[5],
            "(lambda: my_down_binding())": _("V&olume -").replace("&", ""),
            "(lambda: my_up_binding())": _("Vo&lume +").replace("&", ""),
            "(lambda: set_playback_speed(1.00))": _("&Normal speed").replace("&", ""),
            "app.quit": _("Quit the program") + " (2)",
            "do_record": _("Record"),
            "do_screenshot": _("Screenshot").capitalize(),
            "esc_handler": _("Exit fullscreen"),
            "force_update_epg": _("&Update TV guide").replace("&", ""),
            "key_quit": _("Quit the program"),
            "key_t": _("Show/hide playlist"),
            "lowpanel_ch_1": _("Show/hide controls panel"),
            "main_channel_settings": _("&Video settings").replace("&", ""),
            "mpv_fullscreen": _("&Fullscreen").replace("&", ""),
            "mpv_fullscreen_2": _("&Fullscreen").replace("&", "") + " (2)",
            "mpv_mute": _("&Mute audio").replace("&", ""),
            "mpv_play": _("&Play / Pause").replace("&", ""),
            "mpv_stop": _("&Stop").replace("&", ""),
            "my_down_binding_execute": _("V&olume -").replace("&", ""),
            "my_up_binding_execute": _("Vo&lume +").replace("&", ""),
            "next_channel": _("&Next").replace("&", ""),
            "open_stream_info": _("Stream Information"),
            "prev_channel": _("&Previous").replace("&", ""),
            "show_m3u_editor": _("&m3u Editor").replace("&", ""),
            "show_playlists": _("&Playlists").replace("&", ""),
            "reload_playlist": _("&Update current playlist").replace("&", ""),
            "show_scheduler": _("Scheduler"),
            "show_settings": _("Settings"),
            "show_sort": _("&Channel sort").replace("&", " ").strip(),
            "show_timeshift": _("Archive"),
            "show_tvguide": _("TV guide"),
            "showhideeverything": _("&Compact mode").replace("&", ""),
            "show_tvguide_2": _("TV guide for all channels"),
            "alwaysontop": _("Window always on top"),
        }

        if os.path.isfile(str(Path(LOCAL_DIR, "hotkeys.json"))):
            try:
                with open(
                    str(Path(LOCAL_DIR, "hotkeys.json")), "r", encoding="utf8"
                ) as hotkeys_file_tmp:
                    hotkeys_tmp = json.loads(hotkeys_file_tmp.read())[
                        "current_profile"
                    ]["keys"]
                    main_keybinds = hotkeys_tmp
                    logger.info("hotkeys.json found, using it as hotkey settings")
            except Exception:
                logger.warning("failed to read hotkeys.json, using default shortcuts")
                main_keybinds = main_keybinds_default.copy()
        else:
            logger.info("No hotkeys.json found, using default hotkeys")
            main_keybinds = main_keybinds_default.copy()

        if "show_clock" in main_keybinds:
            main_keybinds.pop("show_clock")

        seq = get_seq()

        def setShortcutState(st1):
            YukiData.shortcuts_state = st1
            for shortcut_arr in shortcuts:
                for shortcut in shortcuts[shortcut_arr]:
                    if shortcut.key() in seq:
                        shortcut.setEnabled(st1)

        def reload_keybinds():
            for shortcut_1 in shortcuts:
                if not shortcut_1.endswith("_INTERNAL"):
                    sc_new_keybind = QtGui.QKeySequence(get_keybind(shortcut_1))
                    for shortcut_2 in shortcuts[shortcut_1]:
                        shortcut_2.setKey(sc_new_keybind)
            reload_menubar_shortcuts()

        all_keybinds = main_keybinds.copy()
        all_keybinds.update(main_keybinds_internal)
        for kbd in all_keybinds:
            shortcuts[kbd] = [
                # Main window
                QShortcut(
                    QtGui.QKeySequence(all_keybinds[kbd]), win, activated=funcs[kbd]
                ),
                # Control panel widget
                QShortcut(
                    QtGui.QKeySequence(all_keybinds[kbd]),
                    controlpanel_widget,
                    activated=funcs[kbd],
                ),
                # Playlist widget
                QShortcut(
                    QtGui.QKeySequence(all_keybinds[kbd]),
                    playlist_widget,
                    activated=funcs[kbd],
                ),
            ]
        all_keybinds = False

        setShortcutState(False)

        app.aboutToQuit.connect(myExitHandler)

        vol_remembered = 100
        volume_option = read_option("volume")
        if volume_option is not None:
            vol_remembered = int(volume_option)
            YukiData.volume = vol_remembered
        firstVolRun = False

        def restore_compact_state():
            try:
                compactstate = read_option("compactstate")
                if compactstate:
                    if compactstate["compact_mode"]:
                        showhideeverything()
                    else:
                        if compactstate["playlist_hidden"]:
                            key_t()
                        if compactstate["controlpanel_hidden"]:
                            lowpanel_ch()
            except Exception:
                pass

        if settings["m3u"] and m3u:
            win.show()
            aot_action = init_mpv_player()
            win.raise_()
            win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
            win.activateWindow()
            try:
                combobox_index1 = read_option("comboboxindex")
                if combobox_index1:
                    if combobox_index1["m3u"] == settings["m3u"]:
                        if combobox_index1["index"] < combobox.count():
                            combobox.setCurrentIndex(combobox_index1["index"])
            except Exception:
                pass

            def after_mpv_init():
                if enable_libmpv_render_context:
                    logger.info("Render context enabled, switching vo to libmpv")
                    player["vo"] = "libmpv"
                if not playLastChannel():
                    logger.info("Show splash")
                    mpv_override_play(str(Path("yuki_iptv", ICONS_FOLDER, "main.png")))
                    player.pause = True
                else:
                    logger.info("Playing last channel, splash turned off")
                restore_compact_state()

            if not enable_libmpv_render_context:
                after_mpv_init()
            else:
                # Workaround for "No render context set"
                QtCore.QTimer.singleShot(0, after_mpv_init)

            ic, ic1, ic2 = 0, 0, 0
            timers_array = {}
            timers = {
                thread_shortcuts: 25,
                thread_mouse: 50,
                thread_cursor: 50,
                thread_channels_redraw: 100,
                thread_record: 100,
                thread_osc: 100,
                thread_check_tvguide_obsolete: 100,
                thread_tvguide_progress: 100,
                thread_update_time: 1000,
                thread_logos_update: 1000,
                record_thread: 1000,
                record_thread_2: 1000,
                thread_afterrecord: 50,
                thread_bitrate: UPDATE_BR_INTERVAL * 1000,
                dockwidget_resize_thread: 50,
            }
            for timer in timers:
                timers_array[timer] = QtCore.QTimer()
                timers_array[timer].timeout.connect(timer)
                timers_array[timer].start(timers[timer])

            # Updating EPG, async
            thread_tvguide_update()
            thread_tvguide_update_pt2()
            update_epg_func()
        else:
            show_playlists()
            playlists_win.show()
            playlists_win.raise_()
            playlists_win.setFocus(QtCore.Qt.FocusReason.PopupFocusReason)
            playlists_win.activateWindow()
            moveWindowToCenter(playlists_win)

        app_exit_code = _exec(app)
        if do_save_settings:
            s_p = subprocess.Popen([sys.executable] + sys.argv)
            if "YUKI_IPTV_IS_APPIMAGE" in os.environ:
                s_p.wait()
        sys.exit(app_exit_code)
    except Exception as e3:
        logger.warning("ERROR")
        logger.warning("")
        e3_traceback = traceback.format_exc()
        logger.warning(e3_traceback)
        show_exception(e3, e3_traceback)
        try:
            myExitHandler_before()
        except Exception:
            pass
        for process_4 in active_children():
            try:
                process_4.kill()
            except Exception:
                process_4.terminate()
        sys.exit(1)
