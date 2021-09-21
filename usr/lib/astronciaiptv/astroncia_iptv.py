'''Astroncia IPTV - Cross platform IPTV player'''
# pylint: disable=invalid-name, global-statement, missing-docstring, wrong-import-position
# pylint: disable=too-many-lines, ungrouped-imports, too-many-statements, broad-except
#
# Icons by Font Awesome ( https://fontawesome.com/ ) ( https://fontawesome.com/license )
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License
# https://creativecommons.org/licenses/by/4.0/
#
# Copyright (C) 2021 Astroncia
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
from pathlib import Path
import sys
import os
import time
import datetime
import json
import locale
import signal
import base64
import argparse
import subprocess
import copy
import re
import textwrap
import hashlib
import codecs
import ctypes
import webbrowser
import threading
import traceback
from multiprocessing import Process, Manager, freeze_support, active_children
freeze_support()
from functools import partial
import chardet
import requests
import setproctitle
from unidecode import unidecode
from astroncia.qt import get_qt_library
from astroncia.lang import lang, init_lang, _
from astroncia.ua import user_agent, uas, ua_names
from astroncia.epg import worker
from astroncia.record import record, record_return, stop_record, \
    async_wait_process, make_ffmpeg_screenshot, is_ffmpeg_recording
from astroncia.playlists import iptv_playlists
from astroncia.menubar import init_astroncia_menubar, init_menubar_player, \
    populate_menubar, update_menubar, get_active_vf_filters, get_first_run, get_seq
from astroncia.time import print_with_time, get_app_log, get_mpv_log, args_init
from astroncia.epgurls import EPG_URLS
from astroncia.xtreamtom3u import convert_xtream_to_m3u
from astroncia.xspf import parse_xspf
from astroncia.qt6compat import globalPos, getX, getY
from thirdparty.conversion import convert_size, format_bytes, human_secs
from thirdparty.m3u import M3uParser
from thirdparty.m3ueditor import Viewer
from thirdparty.xtream import XTream
#from thirdparty.levenshtein import damerau_levenshtein

qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()
if qt_library == 'none' or not QtWidgets:
    print_with_time("ERROR: No Qt library found!")
    sys.exit(1)

from thirdparty.resizablewindow import ResizableWindow

if qt_library == 'PyQt5':
    qt_icon_critical = 3
    qt_icon_warning = 2
    qt_icon_information = 1
else:
    qt_icon_critical = QtWidgets.QMessageBox.Icon.Critical
    qt_icon_warning = QtWidgets.QMessageBox.Icon.Warning
    qt_icon_information = QtWidgets.QMessageBox.Icon.Information

if not os.name == 'nt':
    try:
        from gi.repository import GLib
        from thirdparty.mpris_server.adapters import PlayState, MprisAdapter, \
          Microseconds, VolumeDecimal, RateDecimal, Track, DEFAULT_RATE
        from thirdparty.mpris_server.events import EventAdapter
        from thirdparty.mpris_server.server import Server
    except: # pylint: disable=bare-except
        print_with_time("Failed to init MPRIS libraries!")
        try:
            print(traceback.format_exc())
        except: # pylint: disable=bare-except
            pass

APP_VERSION = '__DEB_VERSION__'

if not sys.version_info >= (3, 6, 0):
    print_with_time("Incompatible Python version! Required >= 3.6")
    sys.exit(1)

if not (os.name == 'nt' or os.name == 'posix'):
    print_with_time("Unsupported platform!")
    sys.exit(1)

MAIN_WINDOW_TITLE = 'Astroncia IPTV'
WINDOW_SIZE = (1200, 600)
DOCK_WIDGET2_HEIGHT = int(WINDOW_SIZE[1] / 10)
DOCK_WIDGET2_HEIGHT_OFFSET = 10
DOCK_WIDGET2_HEIGHT_HIGH = DOCK_WIDGET2_HEIGHT + DOCK_WIDGET2_HEIGHT_OFFSET
DOCK_WIDGET2_HEIGHT_LOW = DOCK_WIDGET2_HEIGHT_HIGH - (DOCK_WIDGET2_HEIGHT_OFFSET + 10)
DOCK_WIDGET_WIDTH = int((WINDOW_SIZE[0] / 2) - 200)
TVGUIDE_WIDTH = int((WINDOW_SIZE[0] / 5))
BCOLOR = "#A2A3A3"

EMAIL_ADDRESS = "kestraly (at) gmail.com"

# Set this option to False if you want to disable check updates button in menubar
# for example, if you packaging this into (stable) repository
CHECK_UPDATES_ENABLED = True

UPDATE_URL = "https://gitlab.com/astroncia/iptv/-/raw/master/version.txt"
UPDATE_RELEASES_URL = "https://gitlab.com/astroncia/iptv/-/releases"

UPDATE_BR_INTERVAL = 5

AUDIO_SAMPLE_FORMATS = {"u16": "unsigned 16 bits", \
    "s16": "signed 16 bits", \
    "s16p": "signed 16 bits, planar", \
    "flt" : "float", \
    "float" : "float", \
    "fltp" : "float, planar", \
    "floatp" : "float, planar", \
    "dbl" : "double", \
    "dblp": "double, planar"}

class stream_info: # pylint: disable=too-few-public-methods
    pass

class AstronciaData: # pylint: disable=too-few-public-methods
    compact_mode = False
    playlist_hidden = False
    controlpanel_hidden = False

setproctitle.setproctitle("astronciaiptv")

stream_info.video_properties = {}
stream_info.audio_properties = {}
stream_info.video_bitrates = []
stream_info.audio_bitrates = []

DOCK_WIDGET2_HEIGHT = max(DOCK_WIDGET2_HEIGHT, 0)
DOCK_WIDGET_WIDTH = max(DOCK_WIDGET_WIDTH, 0)

parser = argparse.ArgumentParser(description=MAIN_WINDOW_TITLE)
parser.add_argument('--python')
parser.add_argument(
    '--version',
    action='store_true',
    help='Show version'
)
parser.add_argument(
    '--disable-qt6',
    action='store_true',
    help='Force use Qt 5'
)
parser.add_argument(
    '--silent',
    action='store_true',
    help='Do not output to console'
)
parser.add_argument(
    'URL',
    help='Playlist URL or file',
    nargs='?'
)
args1 = parser.parse_args()
args_init(args1)

if args1.version:
    print("{} {}".format(MAIN_WINDOW_TITLE, APP_VERSION))
    sys.exit(0)

if 'HOME' in os.environ and os.path.isdir(os.environ['HOME']):
    try:
        if not os.path.isdir(str(Path(os.environ['HOME'], '.config'))):
            os.mkdir(str(Path(os.environ['HOME'], '.config')))
    except: # pylint: disable=bare-except
        pass
    try:
        if os.path.isdir(str(Path(os.environ['HOME'], '.AstronciaIPTV'))):
            os.rename(
                str(Path(os.environ['HOME'], '.AstronciaIPTV')),
                str(Path(os.environ['HOME'], '.config', 'astronciaiptv'))
            )
    except: # pylint: disable=bare-except
        pass
    LOCAL_DIR = str(Path(os.environ['HOME'], '.config', 'astronciaiptv'))
    SAVE_FOLDER_DEFAULT = str(Path(os.environ['HOME'], '.config', 'astronciaiptv', 'saves'))
    if not os.path.isdir(LOCAL_DIR):
        os.mkdir(LOCAL_DIR)
    if not os.path.isdir(SAVE_FOLDER_DEFAULT):
        os.mkdir(SAVE_FOLDER_DEFAULT)
else:
    LOCAL_DIR = str(Path(os.path.dirname(__file__), '..', '..', '..', 'local'))
    SAVE_FOLDER_DEFAULT = str(
        Path(os.path.dirname(os.path.abspath(__file__)), 'AstronciaIPTV_saves')
    )

LANG_LOCALE = '?'
try:
    if os.name == 'nt':
        try:
            loc = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
        except: # pylint: disable=bare-except
            loc = locale.getdefaultlocale()[0]
    else:
        loc = locale.getdefaultlocale()[0]
    LANG_LOCALE = loc.split("_")[0]
except: # pylint: disable=bare-except
    pass
print_with_time("System locale: {}".format(LANG_LOCALE))
LANG_DEFAULT = LANG_LOCALE if LANG_LOCALE in lang else 'en'
try:
    settings_file0 = open(str(Path(LOCAL_DIR, 'settings.json')), 'r', encoding="utf8")
    settings_lang0 = json.loads(settings_file0.read())['lang']
    settings_file0.close()
except: # pylint: disable=bare-except
    settings_lang0 = LANG_DEFAULT

try:
    LANG = lang[settings_lang0]['strings'] if settings_lang0 in \
        lang else lang[LANG_DEFAULT]['strings']
except: # pylint: disable=bare-except
    print_with_time("")
    print_with_time("ERROR: No locales found!")
    print_with_time("Execute 'make' for create locale files.")
    print_with_time("")
    sys.exit(1)
LANG_NAME = lang[settings_lang0]['strings']['name'] if settings_lang0 in lang \
    else lang[LANG_DEFAULT]['strings']['name']
print_with_time("Settings locale: {}\n".format(LANG_NAME))

init_lang(LANG['lang_id'])

DEF_DEINTERLACE = True

try:
    if os.path.isfile('/proc/cpuinfo'):
        cpuinfo_file = open('/proc/cpuinfo', 'r')
        cpuinfo_file_contents = cpuinfo_file.read()
        cpuinfo_file.close()
        if 'Raspberry' in cpuinfo_file_contents:
            DEF_DEINTERLACE = False
except: # pylint: disable=bare-except
    pass

def show_exception(e, e_traceback="", prev=""):
    if e_traceback:
        e = e_traceback.strip()
    message = "{}{}\n\n{}\n\n{}".format(
        _('error2'), prev, 'os.name = "{}"'.format(os.name), str(e)
    )
    msg = QtWidgets.QMessageBox(
        qt_icon_critical,
        _('error'), message + '\n\n' + \
        _('foundproblem') + ':\n' + EMAIL_ADDRESS, QtWidgets.QMessageBox.Ok
    )
    msg.exec()

# Used as a decorator to run things in the main loop, from another thread
def idle_function(func):
    def wrapper(*args):
        exInMainThread_partial(partial(func, *args))
    return wrapper

# Used as a decorator to run things in the background
def async_function(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def qt_version_pt1():
    return QtCore.QT_VERSION_STR

def qt_version_pt2():
    try:
        qt_version_1 = QtCore.qVersion()
    except: # pylint: disable=bare-except
        qt_version_1 = "UNKNOWN"
    return qt_version_1

if os.name == 'nt':
    a0 = sys.executable
    if args1.python:
        a0 = args1.python
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = \
        str(Path(os.path.dirname(a0), 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'))

if __name__ == '__main__':
    try:
        os.setpgrp()
    except: # pylint: disable=bare-except
        pass
    try:
        os.environ['GDK_BACKEND'] = 'x11'
    except: # pylint: disable=bare-except
        pass
    print_with_time("Qt init")
    print_with_time("")
    app = QtWidgets.QApplication(sys.argv)
    try:
        app.setStyle("fusion")
    except: # pylint: disable=bare-except
        print_with_time('app.setStyle("fusion") failed')

    # This is necessary since PyQT stomps over the locale settings needed by libmpv.
    # This needs to happen after importing PyQT before creating the first mpv.MPV instance.
    locale.setlocale(locale.LC_NUMERIC, 'C')

    try:
        print_with_time("{} {}...".format(MAIN_WINDOW_TITLE, _('starting')))
        print_with_time("Copyright (C) Astroncia")
        print_with_time("")
        print_with_time(_('foundproblem') + ": " + EMAIL_ADDRESS)
        print_with_time("")
        # Version debugging
        print_with_time("Current version: {}".format(APP_VERSION))
        print_with_time("")
        print_with_time("Using Python {}".format(sys.version.replace('\n', '')))
        # Qt library debugging
        print_with_time("Qt library: {}".format(qt_library))
        try:
            qt_version = qt_version_pt1()
        except: # pylint: disable=bare-except
            qt_version = qt_version_pt2()
        print_with_time("Qt version (runtime): {}".format(qt_version))
        # Qt library debugging (PySide6 only)
        if qt_library == 'PySide6':
            try:
                import PySide6 # pylint: disable=import-error
                print_with_time("Qt version (PySide6 compiled with): {}".format(QtCore.__version__))
                print_with_time("PySide6 version: {}".format(PySide6.__version__))
            except: # pylint: disable=bare-except
                pass
        print_with_time("")

        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        modules_path = str(Path(os.path.dirname(__file__), '..', '..', '..', 'binary_windows'))
        if os.name == 'nt':
            os.environ["PATH"] = modules_path + os.pathsep + os.environ["PATH"]

        m3u = ""
        clockOn = False

        if os.name == 'nt':
            if not (os.path.isfile(str(Path(modules_path, 'ffmpeg.exe'))) and \
                os.path.isfile(str(Path(modules_path, 'mpv-1.dll')))):
                show_exception(_('binarynotfound'))
                sys.exit(1)

        try:
            from thirdparty import mpv
        except: # pylint: disable=bare-except
            print_with_time("Falling back to old mpv library...")
            from thirdparty import mpv_old as mpv

        if not os.path.isdir(LOCAL_DIR):
            os.mkdir(LOCAL_DIR)

        if not os.path.isfile(str(Path(LOCAL_DIR, 'playlist_separate.m3u'))):
            file01 = open(str(Path(LOCAL_DIR, 'playlist_separate.m3u')), 'w', encoding="utf8")
            file01.write('#EXTM3U\n#EXTINF:-1,{}\nhttp://255.255.255.255\n'.format('-'))
            file01.close()

        channel_sets = {}
        prog_ids = {}
        epg_icons = {}
        def save_channel_sets():
            global channel_sets
            file2 = open(str(Path(LOCAL_DIR, 'channels.json')), 'w', encoding="utf8")
            file2.write(json.dumps(channel_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, 'channels.json'))):
            save_channel_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, 'channels.json')), 'r', encoding="utf8")
            channel_sets = json.loads(file1.read())
            file1.close()

        favourite_sets = []
        def save_favourite_sets():
            global favourite_sets
            file2 = open(str(Path(LOCAL_DIR, 'favourites.json')), 'w', encoding="utf8")
            file2.write(json.dumps(favourite_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, 'favourites.json'))):
            save_favourite_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, 'favourites.json')), 'r', encoding="utf8")
            favourite_sets = json.loads(file1.read())
            file1.close()

        tz_offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
        DEF_TIMEZONE = tz_offset / 60 / 60 * -1

        if os.path.isfile(str(Path(LOCAL_DIR, 'settings.json'))):
            settings_file = open(str(Path(LOCAL_DIR, 'settings.json')), 'r', encoding="utf8")
            settings = json.loads(settings_file.read())
            settings_file.close()
        else:
            settings = {
                "m3u": "",
                "epg": "",
                "deinterlace": DEF_DEINTERLACE,
                "udp_proxy": "",
                "save_folder": SAVE_FOLDER_DEFAULT,
                "provider": "",
                "nocache": True,
                "lang": LANG_DEFAULT,
                "timezone": DEF_TIMEZONE,
                "hwaccel": True,
                "sort": 0,
                "cache_secs": 0,
                "useragent": 2,
                "mpv_options": '',
                'donotupdateepg': False,
                'channelsonpage': 100,
                'openprevchan': False,
                'remembervol': True,
                'hidempv': False,
                'chaniconsfromepg': True,
                'hideepgpercentage': False,
                'hidebitrateinfo': False,
                'movedragging': False,
                'volumechangestep': 1,
                'themecompat': False,
                'exp2': DOCK_WIDGET_WIDTH,
                'mouseswitchchannels': False,
                'showplaylistmouse': True,
                'hideplaylistleftclk': False,
                'showcontrolsmouse': True,
                'flpopacity': 0.7,
                'panelposition': 0,
                'playlistsep': False,
                'screenshot': 0,
                'videoaspect': 0,
                'zoom': 0,
                'panscan': 0.0,
                'referer': '',
                'gui': 0
            }
            m3u = ""
        if 'hwaccel' not in settings:
            settings['hwaccel'] = True
        if 'sort' not in settings:
            settings['sort'] = 0
        if 'cache_secs' not in settings:
            settings['cache_secs'] = 0
        if 'timezone' not in settings:
            settings['timezone'] = DEF_TIMEZONE
        if 'useragent' not in settings:
            settings['useragent'] = 2
        if 'mpv_options' not in settings:
            settings['mpv_options'] = ''
        if 'donotupdateepg' not in settings:
            settings['donotupdateepg'] = False
        if 'channelsonpage' not in settings:
            settings['channelsonpage'] = 100
        if 'openprevchan' not in settings:
            settings['openprevchan'] = False
        if 'remembervol' not in settings:
            settings['remembervol'] = True
        if 'hidempv' not in settings:
            settings['hidempv'] = False
        if 'chaniconsfromepg' not in settings:
            settings['chaniconsfromepg'] = True
        if 'hideepgpercentage' not in settings:
            settings['hideepgpercentage'] = False
        if 'hidebitrateinfo' not in settings:
            settings['hidebitrateinfo'] = False
        if 'movedragging' not in settings:
            settings['movedragging'] = False
        if 'volumechangestep' not in settings:
            settings['volumechangestep'] = 1
        if 'themecompat' not in settings:
            settings['themecompat'] = False
        if 'exp2' not in settings:
            settings['exp2'] = DOCK_WIDGET_WIDTH
        if 'mouseswitchchannels' not in settings:
            settings['mouseswitchchannels'] = False
        if 'showplaylistmouse' not in settings:
            settings['showplaylistmouse'] = True
        if 'hideplaylistleftclk' not in settings:
            settings['hideplaylistleftclk'] = False
        if 'showcontrolsmouse' not in settings:
            settings['showcontrolsmouse'] = True
        if 'flpopacity' not in settings:
            settings['flpopacity'] = 0.7
        if 'panelposition' not in settings:
            settings['panelposition'] = 0
        if 'playlistsep' not in settings:
            settings['playlistsep'] = False
        if 'screenshot' not in settings:
            settings['screenshot'] = 0
        if 'videoaspect' not in settings:
            settings['videoaspect'] = 0
        if 'zoom' not in settings:
            settings['zoom'] = 0
        if 'panscan' not in settings:
            settings['panscan'] = 0.0
        if 'gui' not in settings:
            settings['gui'] = 0
        if 'referer' not in settings:
            settings['referer'] = ''
        if settings['hwaccel']:
            print_with_time("{} {}".format(_('hwaccel').replace('\n', ' '), _('enabled')))
        else:
            print_with_time("{} {}".format(_('hwaccel').replace('\n', ' '), _('disabled')))

        # URL override for command line
        if args1.URL:
            settings["m3u"] = args1.URL

        tvguide_sets = {}

        def save_tvguide_sets_proc(tvguide_sets_arg):
            if tvguide_sets_arg:
                file2 = open(str(Path(LOCAL_DIR, 'tvguide.dat')), 'wb')
                file2.write(codecs.encode(bytes(json.dumps(
                    {
                        "tvguide_sets": clean_programme(),
                        "tvguide_url": str(settings["epg"]),
                        "prog_ids": prog_ids,
                        "epg_icons": epg_icons
                    }
                ), 'utf-8'), 'zlib'))
                file2.close()

        epg_thread_2 = None

        def save_tvguide_sets():
            global epg_thread_2, tvguide_sets
            if not os.name == 'nt':
                epg_thread_2 = Process(
                    target=save_tvguide_sets_proc,
                    args=(tvguide_sets,)
                )
                epg_thread_2.start()

        def clean_programme():
            sets1 = tvguide_sets.copy()
            if sets1:
                for prog2 in sets1:
                    sets1[prog2] = [x12 for x12 in sets1[prog2] if \
                        time.time() + 172800 > x12['start'] and \
                            time.time() - 172800 < x12['stop']]
            return sets1

        def is_program_actual(sets0, force=False):
            global epg_ready
            if not epg_ready and not force:
                #print_with_time("is_program_actual override (EPG not ready)")
                return True
            found_prog = False
            if sets0:
                for prog1 in sets0:
                    pr1 = sets0[prog1]
                    for p in pr1:
                        if time.time() > p['start'] and time.time() < p['stop']:
                            found_prog = True
            return found_prog

        first_boot = False
        epg_updating = False

        def force_update_epg():
            global use_local_tvguide, first_boot
            if os.path.exists(str(Path(LOCAL_DIR, 'tvguide.dat'))):
                os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
            use_local_tvguide = False
            if not epg_updating:
                first_boot = False

        use_local_tvguide = True
        epg_ready = False

        def mainwindow_isvisible():
            try:
                return win.isVisible()
            except: # pylint: disable=bare-except
                return False

        #def btn_update_force():
        #    while not mainwindow_isvisible():
        #        time.sleep(0.05)
        #    exInMainThread(epg_loading_hide)
        #    btn_update.click()

        def load_tvguide_dat(epg_dict, settings_epg):
            settings_epg_new = ''
            try:
                file_epg1 = open(str(Path(LOCAL_DIR, 'tvguide.dat')), 'rb')
                file1_json = json.loads(
                    codecs.decode(codecs.decode(file_epg1.read(), 'zlib'), 'utf-8')
                )
                file_epg1.close()
                tvguide_c1 = file1_json["tvguide_url"]
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    cm3uf1 = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r', encoding="utf8")
                    cm3u1 = json.loads(cm3uf1.read())
                    cm3uf1.close()
                    try:
                        epg_url1 = cm3u1['epgurl']
                        if not settings_epg:
                            settings_epg_new = epg_url1
                    except: # pylint: disable=bare-except
                        pass
                if tvguide_c1 != settings_epg:
                    # Ignoring tvguide.dat, EPG URL changed
                    print("Ignoring tvguide.dat, EPG URL changed")
                    os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
                    tvguide_c1 = ""
                    file1_json = {}
            except: # pylint: disable=bare-except
                tvguide_c1 = ""
                file1_json = {}
            epg_dict['out'] = [file1_json, settings_epg_new]

        def epg_loading_hide():
            epg_loading.hide()

        #@async_function
        def update_epg_func():
            global settings, tvguide_sets, prog_ids, epg_icons, programmes, epg_ready
            print_with_time("Reading cached TV guide if exists...")
            tvguide_read_time = time.time()
            programmes_1 = {}
            if not os.path.isfile(str(Path(LOCAL_DIR, 'tvguide.dat'))):
                save_tvguide_sets()
            else:
                # Disregard existed tvguide.dat if EPG url changes
                manager_epg = Manager()
                dict_epg = manager_epg.dict()
                dict_epg['out'] = []
                epg_process = Process(target=load_tvguide_dat, args=(dict_epg, settings['epg'],))
                epg_process.start()
                epg_process.join()
                file1_json, settings_epg_new = dict_epg['out']
                if settings_epg_new:
                    settings['epg'] = settings_epg_new
                # Loading tvguide.dat
                if file1_json:
                    tvguide_json = file1_json
                else:
                    tvguide_json = {"tvguide_sets": {}, "tvguide_url": "", "prog_ids": {}}
                file1_json = {}
                tvguide_sets = tvguide_json["tvguide_sets"]
                programmes_1 = {
                    prog3.lower(): tvguide_sets[prog3] for prog3 in tvguide_sets
                }
                try:
                    prog_ids = tvguide_json["prog_ids"]
                except: # pylint: disable=bare-except
                    pass
                try:
                    epg_icons = tvguide_json["epg_icons"]
                except: # pylint: disable=bare-except
                    pass
            if not is_program_actual(tvguide_sets, force=True):
                print_with_time("EPG cache expired, updating...")
                epg_ready = True
                force_update_epg()
            programmes = programmes_1
            programmes_1 = {}
            epg_ready = True
            print_with_time(
                "TV guide read done, took {} seconds".format(time.time() - tvguide_read_time)
            )
            #btn_update_force()

        # Updating EPG, async
        update_epg_func()

        if settings["themecompat"]:
            ICONS_FOLDER = str(Path('..', '..', '..', 'share', 'astronciaiptv', 'icons_dark'))
        else:
            ICONS_FOLDER = str(Path('..', '..', '..', 'share', 'astronciaiptv', 'icons'))

        main_icon = QtGui.QIcon(str(
            Path(os.path.dirname(__file__), 'astroncia', ICONS_FOLDER, 'tv-blue.png')
        ))
        if os.path.isfile(str(Path(LOCAL_DIR, 'customicon.png'))):
            main_icon = QtGui.QIcon(str(Path(LOCAL_DIR, 'customicon.png')))
        channels = {}
        programmes = {}

        print_with_time("Init m3u editor")
        m3u_editor = Viewer(lang=LANG, iconsFolder=ICONS_FOLDER)
        print_with_time("M3u editor init done")

        def show_m3u_editor():
            if m3u_editor.isVisible():
                m3u_editor.hide()
            else:
                moveWindowToCenter(m3u_editor)
                m3u_editor.show()
                moveWindowToCenter(m3u_editor)

        save_folder = settings['save_folder']

        try:
            if save_folder.startswith(
                    str(Path(os.environ['HOME'], '.AstronciaIPTV'))
            ) and not os.path.isdir(str(Path(save_folder))):
                save_folder = SAVE_FOLDER_DEFAULT
                settings['save_folder'] = SAVE_FOLDER_DEFAULT
                settings_file3 = open(str(Path(LOCAL_DIR, 'settings.json')), 'w', encoding="utf8")
                settings_file3.write(json.dumps(settings))
                settings_file3.close()
        except: # pylint: disable=bare-except
            pass

        if not os.path.isdir(str(Path(save_folder))):
            try:
                os.mkdir(str(Path(save_folder)))
            except: # pylint: disable=bare-except
                print_with_time("Failed to create save folder!")
                save_folder = SAVE_FOLDER_DEFAULT
                if not os.path.isdir(str(Path(save_folder))):
                    os.mkdir(str(Path(save_folder)))

        if not os.path.isdir(str(Path(save_folder, 'screenshots'))):
            os.mkdir(str(Path(save_folder, 'screenshots')))

        if not os.path.isdir(str(Path(save_folder, 'recordings'))):
            os.mkdir(str(Path(save_folder, 'recordings')))

        array = {}
        groups = []

        doSaveSettings = False

        use_cache = settings['m3u'].startswith('http://') or settings['m3u'].startswith('https://')
        if settings['nocache']:
            use_cache = False
        if not use_cache:
            print_with_time(_('nocacheplaylist'))
        if use_cache and os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            pj = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r', encoding="utf8")
            pj1 = json.loads(pj.read())['url']
            pj.close()
            if pj1 != settings['m3u']:
                os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
        if (not use_cache) and os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
        if not os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            print_with_time(_('loadingplaylist'))
            if settings['m3u']:
                # Parsing m3u
                if settings['m3u'].startswith('XTREAM::::::::::::::'):
                    # XTREAM::::::::::::::username::::::::::::::password::::::::::::::url
                    print_with_time("Using XTream API")
                    xtream_sha512 = hashlib.sha512(settings['m3u'].encode('utf-8')).hexdigest()
                    xtream_split = settings['m3u'].split('::::::::::::::')
                    xtream_username = xtream_split[1]
                    xtream_password = xtream_split[2]
                    xtream_url = xtream_split[3]
                    if not os.path.isdir(str(Path(LOCAL_DIR, 'xtream'))):
                        os.mkdir(str(Path(LOCAL_DIR, 'xtream')))
                    xt = XTream(
                        xtream_sha512,
                        xtream_username,
                        xtream_password,
                        xtream_url,
                        str(Path(LOCAL_DIR, 'xtream'))
                    )
                    if xt.auth_data != {}:
                        xt.load_iptv()
                        try:
                            m3u = convert_xtream_to_m3u(xt.channels)
                        except Exception as e3: # pylint: disable=bare-except
                            message2 = "{}\n\n{}".format(
                                _('error2'),
                                str("XTream API: {}\n\n{}".format(_('procerror'), str(e3)))
                            )
                            msg2 = QtWidgets.QMessageBox(
                                qt_icon_warning,
                                _('error'),
                                message2,
                                QtWidgets.QMessageBox.Ok
                            )
                            msg2.exec()
                    else:
                        message1 = "{}\n\n{}".format(
                            _('error2'),
                            str("XTream API: {}".format(_('xtreamnoconn')))
                        )
                        msg1 = QtWidgets.QMessageBox(
                            qt_icon_warning,
                            _('error'),
                            message1,
                            QtWidgets.QMessageBox.Ok
                        )
                        msg1.exec()
                else:
                    if os.path.isfile(settings['m3u']):
                        try:
                            file = open(settings['m3u'], 'r', encoding="utf8")
                            m3u = file.read()
                            file.close()
                        except: # pylint: disable=bare-except
                            print_with_time("Playlist is not UTF-8 encoding")
                            print_with_time("Trying to detect encoding...")
                            file_222_encoding = ''
                            try:
                                file_222 = open(settings['m3u'], 'rb')
                                file_222_encoding = chardet.detect(file_222.read())['encoding']
                                file_222.close()
                            except: # pylint: disable=bare-except
                                pass
                            if file_222_encoding:
                                print_with_time("Guessed encoding: {}".format(file_222_encoding))
                                try:
                                    file_111 = open(
                                        settings['m3u'],
                                        'r',
                                        encoding=file_222_encoding
                                    )
                                    m3u = file_111.read()
                                    file_111.close()
                                except: # pylint: disable=bare-except
                                    print_with_time("Wrong encoding guess!")
                                    show_exception(_('unknownencoding'))
                            else:
                                print_with_time("Unknown encoding!")
                                show_exception(_('unknownencoding'))
                    else:
                        try:
                            m3u = requests.get(
                                settings['m3u'],
                                headers={'User-Agent': user_agent},
                                timeout=3
                            ).text
                        except: # pylint: disable=bare-except
                            m3u = ""

            doSaveSettings = False
            m3u_parser = M3uParser(settings['udp_proxy'])
            epg_url = ""
            if m3u:
                try:
                    is_xspf = '<?xml version="' in m3u and ('http://xspf.org/' in m3u or \
                    'https://xspf.org/' in m3u)
                    if not is_xspf:
                        m3u_data0 = m3u_parser.readM3u(m3u)
                    else:
                        m3u_data0 = parse_xspf(m3u)
                    m3u_data = m3u_data0[0]
                    epg_url = m3u_data0[1]
                    if epg_url and not settings["epg"]:
                        settings["epg"] = epg_url
                        doSaveSettings = True
                    for m3u_line in m3u_data:
                        array[m3u_line['title']] = m3u_line
                        if not m3u_line['tvg-group'] in groups:
                            groups.append(m3u_line['tvg-group'])
                except: # pylint: disable=bare-except
                    print_with_time("Playlist parsing error!")
                    show_exception(_('playlistloaderror'))
                    m3u = ""
                    array = {}
                    groups = []

            a = 'hidden_channels'
            if settings['provider'] in iptv_playlists and a in iptv_playlists[settings['provider']]:
                h1 = iptv_playlists[settings['provider']][a]
                h1 = json.loads(base64.b64decode(bytes(h1, 'utf-8')).decode('utf-8'))
                for ch2 in h1:
                    ch2['tvg-name'] = ch2['tvg-name'] if 'tvg-name' in ch2 else ''
                    ch2['tvg-ID'] = ch2['tvg-ID'] if 'tvg-ID' in ch2 else ''
                    ch2['tvg-logo'] = ch2['tvg-logo'] if 'tvg-logo' in ch2 else ''
                    ch2['tvg-group'] = ch2['tvg-group'] if 'tvg-group' in \
                        ch2 else _('allchannels')
                    array[ch2['title']] = ch2
            print_with_time(_('playlistloaddone'))
            if use_cache:
                print_with_time(_('cachingplaylist'))
                cm3u = json.dumps({
                    'url': settings['m3u'],
                    'array': array,
                    'groups': groups,
                    'm3u': m3u,
                    'epgurl': epg_url
                })
                cm3uf = open(str(Path(LOCAL_DIR, 'playlist.json')), 'w', encoding="utf8")
                cm3uf.write(cm3u)
                cm3uf.close()
                print_with_time(_('playlistcached'))
        else:
            print_with_time(_('usingcachedplaylist'))
            cm3uf = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r', encoding="utf8")
            cm3u = json.loads(cm3uf.read())
            cm3uf.close()
            array = cm3u['array']
            groups = cm3u['groups']
            m3u = cm3u['m3u']
            try:
                epg_url = cm3u['epgurl']
                if epg_url and not settings["epg"]:
                    settings["epg"] = epg_url
            except: # pylint: disable=bare-except
                pass

        for ch3 in array.copy():
            if ch3 in channel_sets:
                if 'group' in channel_sets[ch3]:
                    if channel_sets[ch3]['group']:
                        array[ch3]['tvg-group'] = channel_sets[ch3]['group']
                        if channel_sets[ch3]['group'] not in groups:
                            groups.append(channel_sets[ch3]['group'])
                if 'hidden' in channel_sets[ch3]:
                    if channel_sets[ch3]['hidden']:
                        array.pop(ch3)

        if _('allchannels') in groups:
            groups.remove(_('allchannels'))
        groups = [_('allchannels'), _('favourite')] + groups

        if os.path.isfile(str(Path('..', '..', 'share', 'astronciaiptv', 'channel_icons.json'))):
            icons_file = open(
                str(Path('..', '..', 'share', 'astronciaiptv', 'channel_icons.json')),
                'r',
                encoding="utf8"
            )
            icons = json.loads(icons_file.read())
            icons_file.close()
        else:
            icons = {}

        def sigint_handler(*args): # pylint: disable=unused-argument
            """Handler for the SIGINT signal."""
            global mpris_loop
            if mpris_loop:
                mpris_loop.quit()
            app.quit()

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        TV_ICON = QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'tv.png')))
        ICONS_CACHE = {}
        ICONS_CACHE_FETCHED = {}
        ICONS_CACHE_FETCHED_EPG = {}

        class ScrollLabel(QtWidgets.QScrollArea):
            def __init__(self, *args, **kwargs):
                QtWidgets.QScrollArea.__init__(self, *args, **kwargs)
                self.setWidgetResizable(True)
                content = QtWidgets.QWidget(self)
                bcolor_scrollabel = 'white'
                if settings['themecompat']:
                    bcolor_scrollabel = 'black'
                content.setStyleSheet('background-color: ' + bcolor_scrollabel)
                self.setWidget(content)
                lay = QtWidgets.QVBoxLayout(content)
                self.label = QtWidgets.QLabel(content)
                self.label.setAlignment(QtCore.Qt.AlignCenter)
                self.label.setWordWrap(True)
                self.label.setStyleSheet('background-color: ' + bcolor_scrollabel)
                lay.addWidget(self.label)

            def setText(self, text):
                self.label.setText(text)

            def getText1(self):
                return self.label.text()

            def getLabelHeight(self):
                return self.label.height()

        def get_current_time():
            return time.strftime('%d.%m.%y %H:%M', time.localtime())

        class settings_scrollable_window(QtWidgets.QMainWindow): # pylint: disable=too-few-public-methods
            def __init__(self):
                super().__init__()
                self.initScroll()

            def initScroll(self):
                self.scroll = QtWidgets.QScrollArea()
                self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
                self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
                self.scroll.setWidgetResizable(True)
                self.setCentralWidget(self.scroll)

        def empty_function(arg1): # pylint: disable=unused-argument
            pass

        settings_win = settings_scrollable_window()
        settings_win.resize(720, 500)
        settings_win.setWindowTitle(_('settings'))
        settings_win.setWindowIcon(main_icon)

        selplaylist_win = QtWidgets.QMainWindow()
        selplaylist_win.setWindowTitle(MAIN_WINDOW_TITLE)
        selplaylist_win.setWindowIcon(main_icon)

        streaminfo_win = QtWidgets.QMainWindow()
        streaminfo_win.setWindowIcon(main_icon)

        def add_sep_flag():
            pass

        def del_sep_flag():
            pass

        def sepplaylist_resize_func(is_left, win_width): # pylint: disable=unused-argument
            pass

        sepplaylist_win = ResizableWindow(
            sepPlaylist=True,
            add_sep_flag=add_sep_flag,
            del_sep_flag=del_sep_flag,
            resize_func=sepplaylist_resize_func
        )
        sepplaylist_win.callback = empty_function
        sepplaylist_win.callback_move = empty_function
        sepplaylist_win.setWindowFlags(
            QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
            QtCore.Qt.X11BypassWindowManagerHint
        )
        sepplaylist_win.setWindowTitle('{} ({})'.format(MAIN_WINDOW_TITLE, _('playlist')))
        sepplaylist_win.setWindowIcon(main_icon)

        help_win = QtWidgets.QMainWindow()
        help_win.resize(400, 600)
        help_win.setWindowTitle(_('help'))
        help_win.setWindowIcon(main_icon)

        license_win = QtWidgets.QMainWindow()
        license_win.resize(500, 550)
        license_win.setWindowTitle(_('license'))
        license_win.setWindowIcon(main_icon)

        sort_win = QtWidgets.QMainWindow()
        sort_win.resize(400, 500)
        sort_win.setWindowTitle(_('sort').replace('\n', ' '))
        sort_win.setWindowIcon(main_icon)

        chan_win = QtWidgets.QMainWindow()
        chan_win.resize(400, 250)
        chan_win.setWindowTitle(_('channelsettings'))
        chan_win.setWindowIcon(main_icon)

        ext_win = QtWidgets.QMainWindow()
        ext_win.resize(300, 60)
        ext_win.setWindowTitle(_('openexternal'))
        ext_win.setWindowIcon(main_icon)

        # epg_win

        epg_win = QtWidgets.QMainWindow()
        epg_win.resize(400, 600)
        epg_win.setWindowTitle(_('tvguide'))
        epg_win.setWindowIcon(main_icon)

        tvguide_lbl_2 = ScrollLabel()
        epg_win_widget = QtWidgets.QWidget()
        epg_win_layout = QtWidgets.QVBoxLayout()
        epg_win_layout.addWidget(tvguide_lbl_2)
        epg_win_widget.setLayout(epg_win_layout)
        epg_win.setCentralWidget(epg_win_widget)

        # epg_win_2

        epg_win_2 = QtWidgets.QMainWindow()
        epg_win_2.resize(600, 600)
        epg_win_2.setWindowTitle(_('tvguide'))
        epg_win_2.setWindowIcon(main_icon)

        def epg_win_2_checkbox_changed():
            tvguide_lbl_3.setText(_('notvguideforchannel'))
            try:
                ch_3 = epg_win_2_checkbox.currentText()
                ch_3_guide = update_tvguide(ch_3, True).replace('!@#$%^^&*(', '\n')
                ch_3_guide = ch_3_guide.replace('\n', '<br>').replace('<br>', '', 1)
                ch_3_guide = ch_3_guide.replace(
                    '<span style="color: green;">', '<span style="color: red;">', 1
                )
                tvguide_lbl_3.setText(ch_3_guide)
            except: # pylint: disable=bare-except
                print_with_time("[WARNING] Exception in epg_win_2_checkbox_changed")

        def showonlychplaylist_chk_clk():
            update_tvguide_2()

        showonlychplaylist_lbl = QtWidgets.QLabel()
        showonlychplaylist_lbl.setText('{}:'.format(_('showonlychplaylist')))
        showonlychplaylist_chk = QtWidgets.QCheckBox()
        showonlychplaylist_chk.setChecked(True)
        showonlychplaylist_chk.clicked.connect(showonlychplaylist_chk_clk)
        epg_win_2_checkbox = QtWidgets.QComboBox()
        epg_win_2_checkbox.currentIndexChanged.connect(epg_win_2_checkbox_changed)

        epg_win_2_count = QtWidgets.QLabel()
        epg_win_2_count.setAlignment(QtCore.Qt.AlignCenter)

        epg_win_2_1_widget = QtWidgets.QWidget()
        epg_win_2_1_layout = QtWidgets.QHBoxLayout()
        epg_win_2_1_layout.addWidget(showonlychplaylist_lbl)
        epg_win_2_1_layout.addWidget(showonlychplaylist_chk)
        epg_win_2_1_widget.setLayout(epg_win_2_1_layout)

        tvguide_lbl_3 = ScrollLabel()

        epg_win_2_widget = QtWidgets.QWidget()
        epg_win_2_layout = QtWidgets.QVBoxLayout()
        epg_win_2_layout.addWidget(epg_win_2_1_widget)
        epg_win_2_layout.addWidget(epg_win_2_checkbox)
        epg_win_2_layout.addWidget(epg_win_2_count)
        epg_win_2_layout.addWidget(tvguide_lbl_3)
        epg_win_2_widget.setLayout(epg_win_2_layout)
        epg_win_2.setCentralWidget(epg_win_2_widget)

        xtream_win = QtWidgets.QMainWindow()
        xtream_win.resize(400, 140)
        xtream_win.setWindowTitle("XTream")
        xtream_win.setWindowIcon(main_icon)

        xtream_win_2 = QtWidgets.QMainWindow()
        xtream_win_2.resize(400, 140)
        xtream_win_2.setWindowTitle("XTream")
        xtream_win_2.setWindowIcon(main_icon)

        scheduler_win = QtWidgets.QMainWindow()
        scheduler_win.resize(1000, 600)
        scheduler_win.setWindowTitle(_('scheduler'))
        scheduler_win.setWindowIcon(main_icon)

        archive_win = QtWidgets.QMainWindow()
        archive_win.resize(800, 600)
        archive_win.setWindowTitle(_('timeshift'))
        archive_win.setWindowIcon(main_icon)

        playlists_win = QtWidgets.QMainWindow()
        playlists_win.resize(400, 590)
        playlists_win.setWindowTitle(_('playlists'))
        playlists_win.setWindowIcon(main_icon)

        playlists_win_edit = QtWidgets.QMainWindow()
        playlists_win_edit.resize(500, 180)
        playlists_win_edit.setWindowTitle(_('playlists'))
        playlists_win_edit.setWindowIcon(main_icon)

        epg_select_win = QtWidgets.QMainWindow()
        epg_select_win.resize(400, 500)
        epg_select_win.setWindowTitle(_('tvguide'))
        epg_select_win.setWindowIcon(main_icon)

        class playlists_data: # pylint: disable=too-few-public-methods
            pass

        playlists_data.oldName = ""

        def playlists_win_save():
            try:
                playlists_list.takeItem(
                    playlists_list.row(
                        playlists_list.findItems(playlists_data.oldName, QtCore.Qt.MatchExactly)[0]
                    )
                )
                playlists_data.playlists_used.pop(playlists_data.oldName)
            except: # pylint: disable=bare-except
                pass
            channel_text_prov = name_edit_1.text()
            if channel_text_prov:
                playlists_list.addItem(channel_text_prov)
                playlists_data.playlists_used[channel_text_prov] = {
                    "m3u": m3u_edit_1.text(),
                    "epg": epg_edit_1.text(),
                    "offset": soffset_1.value()
                }
            playlists_save_json()
            playlists_win_edit.hide()

        def epg_edit_1_settext(txt1):
            sepgcombox_1.clear()
            sepgcombox_1.addItems(
                [txt1 if not \
                    txt1.startswith('^^::MULTIPLE::^^') else ''] + EPG_URLS
            )
            epg_edit_1.setText(txt1)

        def m3u_file_1_clicked():
            fname_1 = QtWidgets.QFileDialog.getOpenFileName(
                playlists_win_edit,
                _('selectplaylist'),
                home_folder
            )[0]
            if fname_1:
                m3u_edit_1.setText(fname_1)

        def epg_file_1_clicked():
            fname_2 = QtWidgets.QFileDialog.getOpenFileName(
                playlists_win_edit,
                _('selectepg'),
                home_folder
            )[0]
            if fname_2:
                epg_edit_1_settext(fname_2)

        name_label_1 = QtWidgets.QLabel('{}:'.format(_('provname')))
        m3u_label_1 = QtWidgets.QLabel('{}:'.format(_('m3uplaylist')))
        epg_label_1 = QtWidgets.QLabel('{}:'.format(_('epgaddress')))
        name_edit_1 = QtWidgets.QLineEdit()
        m3u_edit_1 = QtWidgets.QLineEdit()
        m3u_edit_1.setPlaceholderText(_('filepath'))
        epg_edit_1 = QtWidgets.QLineEdit()
        epg_edit_1.setPlaceholderText(_('filepath'))
        sepgcombox_1 = QtWidgets.QComboBox()
        sepgcombox_1.setLineEdit(epg_edit_1)
        m3u_file_1 = QtWidgets.QPushButton()
        m3u_file_1.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'file.png'))))
        m3u_file_1.clicked.connect(m3u_file_1_clicked)
        epg_file_1 = QtWidgets.QPushButton()
        epg_file_1.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'file.png'))))
        epg_file_1.clicked.connect(epg_file_1_clicked)
        save_btn_1 = QtWidgets.QPushButton(_('save'))
        save_btn_1.setStyleSheet('font-weight: bold; color: green;')
        save_btn_1.clicked.connect(playlists_win_save)
        set_label_1 = QtWidgets.QLabel(_('jtvoffsetrecommendation'))
        set_label_1.setStyleSheet('color: #666600')
        soffset_1 = QtWidgets.QDoubleSpinBox()
        soffset_1.setMinimum(-240)
        soffset_1.setMaximum(240)
        soffset_1.setSingleStep(1)
        soffset_1.setDecimals(1)
        offset_label_1 = QtWidgets.QLabel('{}:'.format(_('tvguideoffset')))

        def lo_xtream_select_1():
            xtream_select_1()

        xtream_btn_1 = QtWidgets.QPushButton("XTream")
        xtream_btn_1.clicked.connect(lo_xtream_select_1)

        playlists_win_edit_widget = QtWidgets.QWidget()
        playlists_win_edit_layout = QtWidgets.QGridLayout()
        playlists_win_edit_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        playlists_win_edit_layout.addWidget(name_label_1, 0, 0)
        playlists_win_edit_layout.addWidget(name_edit_1, 0, 1)
        playlists_win_edit_layout.addWidget(m3u_label_1, 1, 0)
        playlists_win_edit_layout.addWidget(m3u_edit_1, 1, 1)
        playlists_win_edit_layout.addWidget(m3u_file_1, 1, 2)
        playlists_win_edit_layout.addWidget(xtream_btn_1, 2, 0)
        playlists_win_edit_layout.addWidget(epg_label_1, 3, 0)
        playlists_win_edit_layout.addWidget(sepgcombox_1, 3, 1)
        playlists_win_edit_layout.addWidget(epg_file_1, 3, 2)
        playlists_win_edit_layout.addWidget(offset_label_1, 4, 0)
        playlists_win_edit_layout.addWidget(soffset_1, 4, 1)
        playlists_win_edit_layout.addWidget(set_label_1, 5, 1)
        playlists_win_edit_layout.addWidget(save_btn_1, 6, 1)
        playlists_win_edit_widget.setLayout(playlists_win_edit_layout)
        playlists_win_edit.setCentralWidget(playlists_win_edit_widget)

        def ihaveplaylist_btn_action():
            selplaylist_win.close()
            show_playlists()
            playlists_win.raise_()
            playlists_win.setFocus(QtCore.Qt.PopupFocusReason)
            playlists_win.activateWindow()

        def setdefaultplaylist_action():
            sprov.setCurrentIndex(1)
            playlists_selected()
            selplaylist_win.close()
            save_settings()

        ihaveplaylist_btn = QtWidgets.QPushButton(_('ihaveplaylist'))
        ihaveplaylist_btn.clicked.connect(ihaveplaylist_btn_action)
        setdefaultplaylist = QtWidgets.QPushButton(_('setdefaultplaylist'))
        setdefaultplaylist.clicked.connect(setdefaultplaylist_action)
        astronciaiptv_icon = QtWidgets.QLabel()
        astronciaiptv_icon.setPixmap(TV_ICON.pixmap(QtCore.QSize(32, 32)))
        astronciaiptv_label = QtWidgets.QLabel()
        myFont6 = QtGui.QFont()
        myFont6.setPointSize(11)
        myFont6.setBold(True)
        astronciaiptv_label.setFont(myFont6)
        astronciaiptv_label.setTextFormat(QtCore.Qt.RichText)
        astronciaiptv_label.setText(
            '<br>&nbsp;<span style="color:green">Astroncia</span>' + \
            ' <span style="color:#b35900">IPTV</span><br>'
        )

        astronciaiptv_widget = QtWidgets.QWidget()
        astronciaiptv_layout = QtWidgets.QHBoxLayout()
        astronciaiptv_layout.addWidget(astronciaiptv_icon)
        astronciaiptv_layout.addWidget(astronciaiptv_label)
        astronciaiptv_widget.setLayout(astronciaiptv_layout)

        selplaylist_widget = QtWidgets.QWidget()
        selplaylist_layout = QtWidgets.QVBoxLayout()
        astronciaiptv_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        selplaylist_layout.addWidget(astronciaiptv_widget)
        selplaylist_layout.addWidget(setdefaultplaylist)
        selplaylist_layout.addWidget(ihaveplaylist_btn)
        selplaylist_widget.setLayout(selplaylist_layout)
        selplaylist_win.setCentralWidget(selplaylist_widget)

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
                epgname_lbl.setText(_('default'))

        esw_input = QtWidgets.QLineEdit()
        esw_input.setPlaceholderText(_('search'))
        esw_button = QtWidgets.QPushButton()
        esw_button.setText(_('search'))
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
        epg_select_win_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        epg_select_win_layout.addWidget(esw_widget, 0)
        epg_select_win_layout.addWidget(esw_select, 1)
        epg_select_win_widget.setLayout(epg_select_win_layout)
        epg_select_win.setCentralWidget(epg_select_win_widget)

        def ext_open_btn_clicked():
            ext_player_file_1 = open(str(Path(LOCAL_DIR, 'extplayer.json')), 'w', encoding="utf8")
            ext_player_file_1.write(json.dumps({"player": ext_player_txt.text()}))
            ext_player_file_1.close()
            subprocess.Popen(ext_player_txt.text().split(' ') + [array[item_selected]['url']])
            ext_win.close()

        ext_player_txt = QtWidgets.QLineEdit()
        player_ext = "mpv"
        if os.path.isfile(str(Path(LOCAL_DIR, 'extplayer.json'))):
            ext_player_file = open(str(Path(LOCAL_DIR, 'extplayer.json')), 'r', encoding="utf8")
            ext_player_file_out = json.loads(ext_player_file.read())
            ext_player_file.close()
            player_ext = ext_player_file_out["player"]
        ext_player_txt.setText(player_ext)
        ext_open_btn = QtWidgets.QPushButton()
        ext_open_btn.clicked.connect(ext_open_btn_clicked)
        ext_open_btn.setText(_('open'))
        ext_widget = QtWidgets.QWidget()
        ext_layout = QtWidgets.QGridLayout()
        ext_layout.addWidget(ext_player_txt, 0, 0)
        ext_layout.addWidget(ext_open_btn, 0, 1)
        ext_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        ext_widget.setLayout(ext_layout)
        ext_win.setCentralWidget(ext_widget)

        def_provider = 0
        def_provider_name = list(iptv_playlists.keys())[def_provider].replace('[Worldwide] ', '')
        playlists_saved = {}

        playlists_saved_default = {}
        playlists_saved_default[def_provider_name] = {
            "m3u": list(iptv_playlists.values())[def_provider]['m3u'],
            "offset": 0
        }
        try:
            playlists_saved_default[def_provider_name]["epg"] = \
                list(iptv_playlists.values())[def_provider]['epg']
        except: # pylint: disable=bare-except
            playlists_saved_default[def_provider_name]["epg"] = ""

        if not os.path.isfile(str(Path(LOCAL_DIR, 'playlists.json'))):
            playlists_saved[def_provider_name] = {
                "m3u": list(iptv_playlists.values())[def_provider]['m3u'],
                "offset": 0
            }
            try:
                playlists_saved[def_provider_name]["epg"] = \
                    list(iptv_playlists.values())[def_provider]['epg']
            except: # pylint: disable=bare-except
                playlists_saved[def_provider_name]["epg"] = ""
        else:
            playlists_json = open(str(Path(LOCAL_DIR, 'playlists.json')), 'r', encoding="utf8")
            playlists_saved = json.loads(playlists_json.read())
            playlists_json.close()

        playlists_list = QtWidgets.QListWidget()
        playlists_select = QtWidgets.QPushButton(_('provselect'))
        playlists_select.setStyleSheet('font-weight: bold; color: green;')
        playlists_add = QtWidgets.QPushButton(_('provadd'))
        playlists_edit = QtWidgets.QPushButton(_('provedit'))
        playlists_delete = QtWidgets.QPushButton(_('provdelete'))
        playlists_favourites = QtWidgets.QPushButton(_('favourite') + '+')
        playlists_reset = QtWidgets.QPushButton(_('resetdefplaylists'))
        playlists_import = QtWidgets.QPushButton(_('importhypnotix'))

        playlists_win_widget = QtWidgets.QWidget()
        playlists_win_layout = QtWidgets.QGridLayout()
        playlists_win_layout.addWidget(playlists_add, 0, 0)
        playlists_win_layout.addWidget(playlists_edit, 0, 1)
        playlists_win_layout.addWidget(playlists_delete, 0, 2)
        playlists_win_layout.addWidget(playlists_favourites, 1, 0)
        playlists_win_layout.addWidget(playlists_reset, 1, 1)
        playlists_win_layout.addWidget(playlists_import, 1, 2)
        playlists_win_widget.setLayout(playlists_win_layout)

        playlists_win_widget_main = QtWidgets.QWidget()
        playlists_win_widget_main_layout = QtWidgets.QVBoxLayout()
        playlists_win_widget_main_layout.addWidget(playlists_list)
        playlists_win_widget_main_layout.addWidget(playlists_select)
        playlists_win_widget_main_layout.addWidget(playlists_win_widget)
        playlists_win_widget_main.setLayout(playlists_win_widget_main_layout)

        playlists_win.setCentralWidget(playlists_win_widget_main)

        def playlists_favourites_do():
            playlists_win.close()
            reset_prov()
            sm3u.setText(str(Path(LOCAL_DIR, 'playlist_separate.m3u')))
            sepg.setText("")
            save_settings()

        playlists_favourites.clicked.connect(playlists_favourites_do)
        if os.name == 'nt':
            playlists_import.hide()

        def playlists_json_save(playlists_save0=None):
            if not playlists_save0:
                playlists_save0 = playlists_saved
            playlists_json1 = open(str(Path(LOCAL_DIR, 'playlists.json')), 'w', encoding="utf8")
            playlists_json1.write(json.dumps(playlists_save0))
            playlists_json1.close()

        time_stop = 0
        autoclosemenu_time = -1

        def moveWindowToCenter(win_arg, force=False): # pylint: disable=unused-argument
            used_screen = QtWidgets.QApplication.primaryScreen()
            if not force:
                try:
                    used_screen = win.screen()
                except: # pylint: disable=bare-except
                    pass
            qr0 = win_arg.frameGeometry()
            qr0.moveCenter(
                QtGui.QScreen.availableGeometry(used_screen).center()
            )
            win_arg.move(qr0.topLeft())

        qr = settings_win.frameGeometry()
        qr.moveCenter(
            QtGui.QScreen.availableGeometry(QtWidgets.QApplication.primaryScreen()).center()
        )
        settings_win_l = qr.topLeft()
        origY = settings_win_l.y() - 150
        settings_win_l.setY(origY)
        #settings_win.move(settings_win_l)
        settings_win.move(qr.topLeft())

        def convert_time(times_1):
            yr = time.strftime('%Y', time.localtime())
            yr = yr[0] + yr[1]
            times_1_sp = times_1.split(' ')
            times_1_sp_0 = times_1_sp[0].split('.')
            times_1_sp_0[2] = yr + times_1_sp_0[2]
            times_1_sp[0] = '.'.join(times_1_sp_0)
            return ' '.join(times_1_sp)

        def programme_clicked(item):
            times = item.text().split('\n')[0]
            start_time = convert_time(times.split(' - ')[0])
            end_time = convert_time(times.split(' - ')[1])
            starttime_w.setDateTime(QtCore.QDateTime.fromString(start_time, 'd.M.yyyy hh:mm'))
            endtime_w.setDateTime(QtCore.QDateTime.fromString(end_time, 'd.M.yyyy hh:mm'))

        def addrecord_clicked():
            selected_chan = choosechannel_ch.currentText()
            if qt_library == 'PySide6':
                start_time_r = starttime_w.dateTime().toPython().strftime('%d.%m.%y %H:%M')
                end_time_r = endtime_w.dateTime().toPython().strftime('%d.%m.%y %H:%M')
            else:
                start_time_r = starttime_w.dateTime().toPyDateTime().strftime('%d.%m.%y %H:%M')
                end_time_r = endtime_w.dateTime().toPyDateTime().strftime('%d.%m.%y %H:%M')
            schedulers.addItem(
                _('channel') + ': ' + selected_chan + '\n' + \
                  '{}: '.format(_('starttime')) + start_time_r + '\n' + \
                  '{}: '.format(_('endtime')) + end_time_r + '\n'
            )

        sch_recordings = {}

        def do_start_record(name1):
            ch_name = name1.split("_")[0]
            ch = ch_name.replace(" ", "_")
            for char in FORBIDDEN_CHARS:
                ch = ch.replace(char, "")
            cur_time = datetime.datetime.now().strftime('%d%m%Y_%H%M%S')
            out_file = str(Path(
                save_folder,
                'recordings',
                'recording_-_' + cur_time + '_-_' + ch + '.mkv'
            ))
            record_url = array[ch_name]['url']
            return [
                record_return(
                    record_url, out_file,
                    ch_name, "Referer: {}".format(settings["referer"])
                ),
                time.time(), out_file, ch_name
            ]

        def do_stop_record(name2):
            if name2 in sch_recordings:
                ffmpeg_process = sch_recordings[name2][0]
                if ffmpeg_process:
                    ffmpeg_process.terminate()
                    try:
                        async_wait_process(ffmpeg_process)
                    except: # pylint: disable=bare-except
                        pass
                    ffmpeg_process = None

        recViaScheduler = False

        @async_function
        def record_post_action():
            while True:
                if is_recording_func() is True:
                    break
                time.sleep(1)
            print_with_time("Record via scheduler ended, executing post-action...")
            # 0 - nothing to do
            if praction_choose.currentIndex() == 1: # 1 - Press Stop
                mpv_stop()
            if praction_choose.currentIndex() == 2: # 2 - Quit program
                key_quit()

        def record_thread_2():
            try:
                global recViaScheduler
                activerec_list_value = activerec_list.verticalScrollBar().value()
                activerec_list.clear()
                for sch0 in sch_recordings:
                    counted_time0 = human_secs(time.time() - sch_recordings[sch0][1])
                    channel_name0 = sch_recordings[sch0][3]
                    file_name0 = sch_recordings[sch0][2]
                    file_size0 = "WAITING"
                    if os.path.isfile(file_name0):
                        file_size0 = convert_size(os.path.getsize(file_name0))
                    activerec_list.addItem(channel_name0 + "\n" + counted_time0 + " " + file_size0)
                activerec_list.verticalScrollBar().setValue(activerec_list_value)
                pl_text = "REC / " + _('smscheduler')
                if activerec_list.count() != 0:
                    recViaScheduler = True
                    lbl2.setText(pl_text)
                    lbl2.show()
                else:
                    if recViaScheduler:
                        print_with_time(
                            "Record via scheduler ended, waiting for ffmpeg process completion..."
                        )
                        record_post_action()
                    recViaScheduler = False
                    if lbl2.text() == pl_text:
                        lbl2.hide()
            except: # pylint: disable=bare-except
                pass

        ffmpeg_processes = []

        def record_thread():
            try:
                global is_recording, ffmpeg_processes
                status = _('recnothing')
                sch_items = [str(schedulers.item(i1).text()) for i1 in range(schedulers.count())]
                i3 = -1
                for sch_item in sch_items:
                    i3 += 1
                    status = _('recwaiting')
                    sch_item = [i2.split(': ')[1] for i2 in sch_item.split('\n') if i2]
                    channel_name_rec = sch_item[0]
                    #ch_url = array[channel_name_rec]['url']
                    current_time = time.strftime('%d.%m.%y %H:%M', time.localtime())
                    start_time_1 = sch_item[1]
                    end_time_1 = sch_item[2]
                    array_name = str(channel_name_rec) + "_" + \
                        str(start_time_1) + "_" + str(end_time_1)
                    if start_time_1 == current_time:
                        if array_name not in sch_recordings:
                            st_planned = \
                                "Starting planned record" + \
                                    " (start_time='{}' end_time='{}' channel='{}')"
                            print_with_time(
                                st_planned.format(start_time_1, end_time_1, channel_name_rec)
                            )
                            sch_recordings[array_name] = do_start_record(array_name)
                            ffmpeg_processes.append(sch_recordings[array_name])
                    if end_time_1 == current_time:
                        if array_name in sch_recordings:
                            schedulers.takeItem(i3)
                            stop_planned = \
                                "Stopping planned record" + \
                                    " (start_time='{}' end_time='{}' channel='{}')"
                            print_with_time(
                                stop_planned.format(start_time_1, end_time_1, channel_name_rec)
                            )
                            do_stop_record(array_name)
                            sch_recordings.pop(array_name)
                    if sch_recordings:
                        status = _('recrecording')
                statusrec_lbl.setText('{}: {}'.format(_('status'), status))
            except: # pylint: disable=bare-except
                pass

        def delrecord_clicked():
            schCurrentRow = schedulers.currentRow()
            if schCurrentRow != -1:
                sch_index = '_'.join([xs.split(': ')[1] for xs in \
                    schedulers.item(schCurrentRow).text().split('\n') if xs])
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
        scheduler_clock.setStyleSheet('color: green')
        plannedrec_lbl = QtWidgets.QLabel('{}:'.format(_('plannedrec')))
        activerec_lbl = QtWidgets.QLabel('{}:'.format(_('activerec')))
        statusrec_lbl = QtWidgets.QLabel()
        myFont5 = QtGui.QFont()
        myFont5.setBold(True)
        statusrec_lbl.setFont(myFont5)
        choosechannel_lbl = QtWidgets.QLabel('{}:'.format(_('choosechannel')))
        choosechannel_ch = QtWidgets.QComboBox()
        tvguide_sch = QtWidgets.QListWidget()
        tvguide_sch.itemClicked.connect(programme_clicked)
        addrecord_btn = QtWidgets.QPushButton(_('addrecord'))
        addrecord_btn.clicked.connect(addrecord_clicked)
        delrecord_btn = QtWidgets.QPushButton(_('delrecord'))
        delrecord_btn.clicked.connect(delrecord_clicked)
        scheduler_layout.addWidget(scheduler_clock, 0, 0)
        scheduler_layout.addWidget(choosechannel_lbl, 1, 0)
        scheduler_layout.addWidget(choosechannel_ch, 2, 0)
        scheduler_layout.addWidget(tvguide_sch, 3, 0)

        starttime_lbl = QtWidgets.QLabel('{}:'.format(_('starttime')))
        endtime_lbl = QtWidgets.QLabel('{}:'.format(_('endtime')))
        starttime_w = QtWidgets.QDateTimeEdit()
        starttime_w.setDateTime(
            QtCore.QDateTime.fromString(
                time.strftime('%d.%m.%Y %H:%M', time.localtime()), 'd.M.yyyy hh:mm'
            )
        )
        endtime_w = QtWidgets.QDateTimeEdit()
        endtime_w.setDateTime(
            QtCore.QDateTime.fromString(
                time.strftime('%d.%m.%Y %H:%M', time.localtime(time.time() + 60)),
                'd.M.yyyy hh:mm'
            )
        )

        praction_lbl = QtWidgets.QLabel('{}:'.format(_('praction')))
        praction_choose = QtWidgets.QComboBox()
        praction_choose.addItem(_('nothingtodo'))
        praction_choose.addItem(_('stoppress'))
        praction_choose.addItem(_('exitprogram'))

        schedulers = QtWidgets.QListWidget()
        activerec_list = QtWidgets.QListWidget()

        scheduler_layout_2 = QtWidgets.QGridLayout()
        scheduler_layout_2.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
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
        scheduler_layout_3.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        scheduler_layout_3.addWidget(statusrec_lbl, 0, 0)
        scheduler_layout_3.addWidget(plannedrec_lbl, 1, 0)
        scheduler_layout_3.addWidget(schedulers, 2, 0)

        scheduler_layout_4 = QtWidgets.QGridLayout()
        scheduler_layout_4.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
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

        warning_lbl = QtWidgets.QLabel(_('warningstr'))
        myFont5 = QtGui.QFont()
        myFont5.setPointSize(11)
        myFont5.setBold(True)
        warning_lbl.setFont(myFont5)
        warning_lbl.setStyleSheet('color: red')
        warning_lbl.setAlignment(QtCore.Qt.AlignCenter)

        scheduler_layout_main = QtWidgets.QVBoxLayout()
        scheduler_layout_main.addWidget(scheduler_widget)
        scheduler_widget_main = QtWidgets.QWidget()
        scheduler_widget_main.setLayout(scheduler_layout_main)

        scheduler_win.setCentralWidget(scheduler_widget_main)

        archive_all = QtWidgets.QListWidget()
        archive_font = QtGui.QFont()
        archive_font.setBold(True)
        archive_channel = QtWidgets.QLabel()
        archive_channel.setFont(archive_font)

        archive_layout_main = QtWidgets.QVBoxLayout()
        archive_layout_main.addWidget(archive_channel)
        archive_layout_main.addWidget(archive_all)

        archive_widget_main = QtWidgets.QWidget()
        archive_widget_main.setLayout(archive_layout_main)
        archive_win.setCentralWidget(archive_widget_main)

        def save_sort():
            global channel_sort
            channel_sort = [sort_list.item(z0).text() for z0 in range(sort_list.count())]
            file4 = open(str(Path(LOCAL_DIR, 'sort.json')), 'w', encoding="utf8")
            file4.write(json.dumps(channel_sort))
            file4.close()
            sort_win.hide()

        close_sort_btn = QtWidgets.QPushButton(_('close'))
        close_sort_btn.clicked.connect(sort_win.hide)
        close_sort_btn.setStyleSheet('color: red;')

        save_sort_btn = QtWidgets.QPushButton(_('save'))
        save_sort_btn.setStyleSheet('font-weight: bold; color: green;')
        save_sort_btn.clicked.connect(save_sort)

        sort_label = QtWidgets.QLabel(_('donotforgetsort'))
        sort_label.setAlignment(QtCore.Qt.AlignCenter)

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
        sort_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        sort_widget_main.setLayout(sort_layout)
        sort_win.setCentralWidget(sort_widget_main)

        home_folder = ""
        try:
            home_folder = os.environ['HOME']
        except: # pylint: disable=bare-except
            pass

        def m3u_select():
            reset_prov()
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win,
                _('selectplaylist'),
                home_folder
            )[0]
            if fname:
                sm3u.setText(fname)

        def epg_select():
            reset_prov()
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win,
                _('selectepg'),
                home_folder
            )[0]
            if fname:
                sepg.setText(fname if not fname.startswith('^^::MULTIPLE::^^') else '')

        def save_folder_select():
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                settings_win,
                _('selectwritefolder'),
                options=QtWidgets.QFileDialog.ShowDirsOnly
            )
            if folder_name:
                sfld.setText(folder_name)

        # Channel settings window
        wid = QtWidgets.QWidget()

        title = QtWidgets.QLabel()
        myFont2 = QtGui.QFont()
        myFont2.setBold(True)
        title.setFont(myFont2)
        title.setAlignment(QtCore.Qt.AlignCenter)

        deinterlace_lbl = QtWidgets.QLabel("{}:".format(_('deinterlace')))
        useragent_lbl = QtWidgets.QLabel("{}:".format(_('useragent')))
        group_lbl = QtWidgets.QLabel("{}:".format(_('group')))
        group_text = QtWidgets.QLineEdit()
        hidden_lbl = QtWidgets.QLabel("{}:".format(_('hide')))
        deinterlace_chk = QtWidgets.QCheckBox()
        hidden_chk = QtWidgets.QCheckBox()
        useragent_choose = QtWidgets.QComboBox()
        useragent_choose.addItem(_('empty'))
        for ua_name in ua_names[1::]:
            useragent_choose.addItem(ua_name)

        def epgname_btn_action():
            prog_ids_0 = []
            for x0 in prog_ids:
                for x1 in prog_ids[x0]:
                    if not x1 in prog_ids_0:
                        prog_ids_0.append(x1)
            esw_select.clear()
            esw_select.addItem('')
            for prog_ids_0_dat in prog_ids_0:
                esw_select.addItem(prog_ids_0_dat)
            esw_input_edit()
            moveWindowToCenter(epg_select_win)
            epg_select_win.show()

        contrast_lbl = QtWidgets.QLabel("{}:".format(_('contrast')))
        brightness_lbl = QtWidgets.QLabel("{}:".format(_('brightness')))
        hue_lbl = QtWidgets.QLabel("{}:".format(_('hue')))
        saturation_lbl = QtWidgets.QLabel("{}:".format(_('saturation')))
        gamma_lbl = QtWidgets.QLabel("{}:".format(_('gamma')))
        videoaspect_lbl = QtWidgets.QLabel("{}:".format(_('videoaspect')))
        zoom_lbl = QtWidgets.QLabel("{}:".format(_('zoom')))
        panscan_lbl = QtWidgets.QLabel("{}:".format(_('panscan')))
        epgname_btn = QtWidgets.QPushButton(_('epgname'))
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
            _('default'): -1,
            '16:9': '16:9',
            '16:10': '16:10',
            '1.85:1': '1.85:1',
            '2.21:1': '2.21:1',
            '2.35:1': '2.35:1',
            '2.39:1': '2.39:1',
            '4:3': '4:3',
            '5:4': '5:4',
            '5:3': '5:3',
            '1:1': '1:1'
        }
        videoaspect_choose = QtWidgets.QComboBox()
        for videoaspect_var in videoaspect_vars:
            videoaspect_choose.addItem(videoaspect_var)

        zoom_choose = QtWidgets.QComboBox()
        zoom_vars = {
            _('default'): 0,
            '1.05': '1.05',
            '1.1': '1.1',
            '1.2': '1.2',
            '1.3': '1.3',
            '1.4': '1.4',
            '1.5': '1.5',
            '1.6': '1.6',
            '1.7': '1.7',
            '1.8': '1.8',
            '1.9': '1.9',
            '2': '2'
        }
        for zoom_var in zoom_vars:
            zoom_choose.addItem(zoom_var)

        panscan_choose = QtWidgets.QDoubleSpinBox()
        panscan_choose.setMinimum(0)
        panscan_choose.setMaximum(1)
        panscan_choose.setSingleStep(0.1)
        panscan_choose.setDecimals(1)

        def_user_agent = uas[settings['useragent']]
        print_with_time("Default user agent: {}".format(def_user_agent))

        def on_bitrate(prop, bitrate):
            try:
                if not bitrate or prop not in ["video-bitrate", "audio-bitrate"]:
                    return

                if _("Average Bitrate") in stream_info.video_properties:
                    if _("Average Bitrate") in stream_info.audio_properties:
                        if not streaminfo_win.isVisible():
                            return

                rates = {"video": stream_info.video_bitrates, "audio": stream_info.audio_bitrates}
                rate = "video"
                if prop == "audio-bitrate":
                    rate = "audio"

                rates[rate].append(int(bitrate) / 1000.0)
                rates[rate] = rates[rate][-30:]
                br = sum(rates[rate]) / float(len(rates[rate]))

                if rate == "video":
                    stream_info.video_properties[_("general")][_("Average Bitrate")] = \
                    ("%.f " + _('bitrate2')) % br
                else:
                    stream_info.audio_properties[_("general")][_("Average Bitrate")] = \
                    ("%.f " + _('bitrate2')) % br
            except: # pylint: disable=bare-except
                pass

        def on_video_params(property1, params): # pylint: disable=unused-argument
            try:
                if not params or not isinstance(params, dict):
                    return
                if "w" in params and "h" in params:
                    stream_info.video_properties[_("general")][_("Dimensions")] = "%sx%s" % (
                        params["w"], params["h"]
                    )
                if "aspect" in params:
                    aspect = round(float(params["aspect"]), 2)
                    stream_info.video_properties[_("general")][_("Aspect")] = \
                    "%s" % aspect
                if "pixelformat" in params:
                    stream_info.video_properties[_("colour")][_("Pixel Format")] = \
                    params["pixelformat"]
                if "gamma" in params:
                    stream_info.video_properties[_("colour")][_("Gamma")] = params["gamma"]
                if "average-bpp" in params:
                    stream_info.video_properties[_("colour")][_("Bits Per Pixel")] = \
                        params["average-bpp"]
            except: # pylint: disable=bare-except
                pass

        def on_video_format(property1, vformat): # pylint: disable=unused-argument
            try:
                if not vformat:
                    return
                stream_info.video_properties[_("general")][_("Codec")] = vformat
            except: # pylint: disable=bare-except
                pass

        def on_audio_params(property1, params): # pylint: disable=unused-argument
            try:
                if not params or not isinstance(params, dict):
                    return
                if "channels" in params:
                    chans = params["channels"]
                    if "5.1" in chans or "7.1" in chans:
                        chans += " " + _("surround sound")
                    stream_info.audio_properties[_("layout")][_("Channels")] = chans
                if "samplerate" in params:
                    sr = float(params["samplerate"]) / 1000.0
                    stream_info.audio_properties[_("general")][_("Sample Rate")] = "%.1f KHz" % sr
                if "format" in params:
                    fmt = params["format"]
                    fmt = AUDIO_SAMPLE_FORMATS.get(fmt, fmt)
                    stream_info.audio_properties[_("general")][_("Format")] = fmt
                if "channel-count" in params:
                    stream_info.audio_properties[_("layout")][_("Channel Count")] = \
                        params["channel-count"]
            except: # pylint: disable=bare-except
                pass

        def on_audio_codec(property1, codec): # pylint: disable=unused-argument
            try:
                if not codec:
                    return
                stream_info.audio_properties[_("general")][_("Codec")] = codec.split()[0]
            except: # pylint: disable=bare-except
                pass

        @async_function
        def monitor_playback():
            try:
                player.wait_until_playing()
                player.observe_property("video-params", on_video_params)
                player.observe_property("video-format", on_video_format)
                player.observe_property("audio-params", on_audio_params)
                player.observe_property("audio-codec", on_audio_codec)
                player.observe_property("video-bitrate", on_bitrate)
                player.observe_property("audio-bitrate", on_bitrate)
            except: # pylint: disable=bare-except
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
            stream_info.video_properties[_("general")] = {}
            stream_info.video_properties[_("colour")] = {}

            stream_info.audio_properties.clear()
            stream_info.audio_properties[_("general")] = {}
            stream_info.audio_properties[_("layout")] = {}

            stream_info.video_bitrates.clear()
            stream_info.audio_bitrates.clear()

        def mpv_override_play(arg_override_play, ua1=''):
            global event_handler
            on_before_play()
            # Parsing User-Agent and Referer in Kodi-like style
            player.user_agent = ua1
            if settings["referer"]:
                player.http_header_fields = "Referer: {}".format(settings["referer"])
            else:
                player.http_header_fields = ""
            if '|' in arg_override_play:
                print_with_time("Found Kodi-style arguments, parsing")
                split_kodi = arg_override_play.split('|')[1]
                if '&' in split_kodi:
                    print_with_time("Multiple")
                    split_kodi = split_kodi.split('&')
                else:
                    print_with_time("Single")
                    split_kodi = [split_kodi]
                for kodi_str in split_kodi:
                    if kodi_str.startswith('User-Agent='):
                        kodi_user_agent = kodi_str.replace('User-Agent=', '', 1)
                        print_with_time("Kodi-style User-Agent found: {}".format(kodi_user_agent))
                        player.user_agent = kodi_user_agent
                    if kodi_str.startswith('Referer='):
                        kodi_referer = kodi_str.replace('Referer=', '', 1)
                        print_with_time("Kodi-style Referer found: {}".format(kodi_referer))
                        player.http_header_fields = "Referer: {}".format(kodi_referer)
                arg_override_play = arg_override_play.split('|')[0]
            #print_with_time("mpv_override_play called")
            player.play(arg_override_play)
            if (not os.name == 'nt') and event_handler:
                try:
                    event_handler.on_title()
                except: # pylint: disable=bare-except
                    pass
                try:
                    event_handler.on_options()
                except: # pylint: disable=bare-except
                    pass
                try:
                    event_handler.on_playback()
                except: # pylint: disable=bare-except
                    pass

        def mpv_override_stop(ignore=False):
            global event_handler
            #print_with_time("mpv_override_stop called")
            player.command('stop')
            if not ignore:
                print_with_time("Disabling deinterlace for main.png")
                player.deinterlace = False
            player.play(str(Path('astroncia', ICONS_FOLDER, 'main.png')))
            if (not os.name == 'nt') and event_handler:
                try:
                    event_handler.on_title()
                except: # pylint: disable=bare-except
                    pass
                try:
                    event_handler.on_options()
                except: # pylint: disable=bare-except
                    pass
                try:
                    event_handler.on_ended()
                except: # pylint: disable=bare-except
                    pass

        firstVolRun = True

        def mpv_override_volume(volume_val):
            global event_handler, firstVolRun
            #print_with_time("mpv_override_volume called")
            player.volume = volume_val
            if settings["remembervol"] and not firstVolRun:
                volfile = open(str(Path(LOCAL_DIR, 'volume.json')), 'w', encoding="utf8")
                volfile.write(json.dumps({"volume": player.volume}))
                volfile.close()
            if (not os.name == 'nt') and event_handler:
                try:
                    event_handler.on_volume()
                except: # pylint: disable=bare-except
                    pass

        def mpv_override_mute(mute_val):
            global event_handler
            #print_with_time("mpv_override_mute called")
            player.mute = mute_val
            if (not os.name == 'nt') and event_handler:
                try:
                    event_handler.on_volume()
                except: # pylint: disable=bare-except
                    pass

        def mpv_override_pause(pause_val):
            global event_handler
            #print_with_time("mpv_override_pause called")
            player.pause = pause_val
            if (not os.name == 'nt') and event_handler:
                try:
                    event_handler.on_playpause()
                except: # pylint: disable=bare-except
                    pass

        def stopPlayer(ignore=False):
            try:
                mpv_override_stop(ignore)
            except: # pylint: disable=bare-except
                player.loop = True
                mpv_override_play(str(Path('astroncia', ICONS_FOLDER, 'main.png')))

        def setVideoAspect(va):
            if va == 0:
                va = -1
            try:
                player.video_aspect_override = va
            except: # pylint: disable=bare-except
                pass
            try:
                player.video_aspect = va
            except: # pylint: disable=bare-except
                pass

        def setZoom(zm):
            player.video_zoom = zm

        def setPanscan(ps):
            player.panscan = ps

        def getVideoAspect():
            try:
                va1 = player.video_aspect_override
            except: # pylint: disable=bare-except
                va1 = player.video_aspect
            return va1

        def doPlay(play_url1, ua_ch=def_user_agent, chan_name_0=''):
            comm_instance.do_play_args = (play_url1, ua_ch, chan_name_0)
            print_with_time("")
            print_with_time("Playing '{}' ('{}')".format(chan_name_0, play_url1))
            # Loading
            loading.setText(_('loading'))
            loading.setStyleSheet('color: #778a30')
            showLoading()
            player.loop = False
            # Optimizations
            if play_url1.startswith("udp://") or play_url1.startswith("rtp://"):
                try:
                    # For low latency on multicast
                    print_with_time("Using multicast optimized settings")
                    player.cache = 'no'
                    player.untimed = True
                    player['cache-pause'] = False
                    player['audio-buffer'] = 0
                    player['vd-lavc-threads'] = 1
                    player['demuxer-lavf-probe-info'] = 'nostreams'
                    player['demuxer-lavf-analyzeduration'] = 0.1
                    player['video-sync'] = 'audio'
                    player['interpolation'] = False
                    player['video-latency-hacks'] = True
                except: # pylint: disable=bare-except
                    print_with_time("Failed to set multicast optimized settings!")
            try:
                player.stream_lavf_o = \
                    '-reconnect=1 -reconnect_at_eof=1 -reconnect_streamed=1 -reconnect_delay_max=2'
            except: # pylint: disable=bare-except
                pass
            # Print user agent
            print_with_time("Using user-agent: {}".format(
                ua_ch if isinstance(ua_ch, str) else uas[ua_ch]
            ))
            # Set user agent and loop
            player.user_agent = ua_ch if isinstance(ua_ch, str) else uas[ua_ch]
            player.loop = True
            # Playing
            mpv_override_play(play_url1, ua_ch if isinstance(ua_ch, str) else uas[ua_ch])
            # Set channel (video) settings
            setPlayerSettings(chan_name_0)
            # Monitor playback (for stream information)
            if not os.name == 'nt':
                monitor_playback()

        def chan_set_save():
            chan_3 = title.text().replace("{}: ".format(_('channel')), "")
            channel_sets[chan_3] = {
                "deinterlace": deinterlace_chk.isChecked(),
                "useragent": useragent_choose.currentIndex(),
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
                "epgname": epgname_lbl.text() if epgname_lbl.text() != _('default') else ''
            }
            save_channel_sets()
            if playing_chan == chan_3:
                player.deinterlace = deinterlace_chk.isChecked()
                player.contrast = contrast_choose.value()
                player.brightness = brightness_choose.value()
                player.hue = hue_choose.value()
                player.saturation = saturation_choose.value()
                player.gamma = gamma_choose.value()
                player.video_zoom = zoom_vars[list(zoom_vars)[zoom_choose.currentIndex()]]
                player.panscan = panscan_choose.value()
                setVideoAspect(
                    videoaspect_vars[list(videoaspect_vars)[videoaspect_choose.currentIndex()]]
                )
            btn_update.click()
            chan_win.close()

        save_btn = QtWidgets.QPushButton(_('savesettings'))
        save_btn.clicked.connect(chan_set_save)

        horizontalLayout = QtWidgets.QHBoxLayout()
        horizontalLayout.addWidget(title)

        horizontalLayout2 = QtWidgets.QHBoxLayout()
        horizontalLayout2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2.addWidget(deinterlace_lbl)
        horizontalLayout2.addWidget(deinterlace_chk)
        horizontalLayout2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_1 = QtWidgets.QHBoxLayout()
        horizontalLayout2_1.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_1.addWidget(useragent_lbl)
        horizontalLayout2_1.addWidget(useragent_choose)
        horizontalLayout2_1.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_1.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_2 = QtWidgets.QHBoxLayout()
        horizontalLayout2_2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_2.addWidget(group_lbl)
        horizontalLayout2_2.addWidget(group_text)
        horizontalLayout2_2.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_2.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_3 = QtWidgets.QHBoxLayout()
        horizontalLayout2_3.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_3.addWidget(hidden_lbl)
        horizontalLayout2_3.addWidget(hidden_chk)
        horizontalLayout2_3.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_3.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_4 = QtWidgets.QHBoxLayout()
        horizontalLayout2_4.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_4.addWidget(contrast_lbl)
        horizontalLayout2_4.addWidget(contrast_choose)
        horizontalLayout2_4.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_4.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_5 = QtWidgets.QHBoxLayout()
        horizontalLayout2_5.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_5.addWidget(brightness_lbl)
        horizontalLayout2_5.addWidget(brightness_choose)
        horizontalLayout2_5.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_5.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_6 = QtWidgets.QHBoxLayout()
        horizontalLayout2_6.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_6.addWidget(hue_lbl)
        horizontalLayout2_6.addWidget(hue_choose)
        horizontalLayout2_6.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_6.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_7 = QtWidgets.QHBoxLayout()
        horizontalLayout2_7.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_7.addWidget(saturation_lbl)
        horizontalLayout2_7.addWidget(saturation_choose)
        horizontalLayout2_7.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_7.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_8 = QtWidgets.QHBoxLayout()
        horizontalLayout2_8.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_8.addWidget(gamma_lbl)
        horizontalLayout2_8.addWidget(gamma_choose)
        horizontalLayout2_8.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_8.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_9 = QtWidgets.QHBoxLayout()
        horizontalLayout2_9.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_9.addWidget(videoaspect_lbl)
        horizontalLayout2_9.addWidget(videoaspect_choose)
        horizontalLayout2_9.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_9.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_10 = QtWidgets.QHBoxLayout()
        horizontalLayout2_10.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_10.addWidget(zoom_lbl)
        horizontalLayout2_10.addWidget(zoom_choose)
        horizontalLayout2_10.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_10.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_11 = QtWidgets.QHBoxLayout()
        horizontalLayout2_11.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_11.addWidget(panscan_lbl)
        horizontalLayout2_11.addWidget(panscan_choose)
        horizontalLayout2_11.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_11.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout2_12 = QtWidgets.QHBoxLayout()
        horizontalLayout2_12.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_12.addWidget(epgname_btn)
        horizontalLayout2_12.addWidget(epgname_lbl)
        horizontalLayout2_12.addWidget(QtWidgets.QLabel("\n"))
        horizontalLayout2_12.setAlignment(QtCore.Qt.AlignCenter)

        horizontalLayout3 = QtWidgets.QHBoxLayout()
        horizontalLayout3.addWidget(save_btn)

        verticalLayout = QtWidgets.QVBoxLayout(wid)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addLayout(horizontalLayout2)
        verticalLayout.addLayout(horizontalLayout2_1)
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
        verticalLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        wid.setLayout(verticalLayout)
        chan_win.setCentralWidget(wid)

        # Settings window
        def save_settings(): # pylint: disable=too-many-branches
            global epg_thread, epg_thread_2, manager
            udp_proxy_text = sudp.text()
            udp_proxy_starts = udp_proxy_text.startswith('http://') or \
                udp_proxy_text.startswith('https://')
            if udp_proxy_text and not udp_proxy_starts:
                udp_proxy_text = 'http://' + udp_proxy_text
            if udp_proxy_text:
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            if settings["timezone"] != soffset.value():
                if os.path.isfile(str(Path(LOCAL_DIR, 'tvguide.dat'))):
                    os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
            if sort_widget.currentIndex() != settings['sort']:
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            lang1 = LANG_DEFAULT
            for lng1 in lang:
                if lang[lng1]['strings']['name'] == slang.currentText():
                    lang1 = lng1
            if lang1 != settings["lang"]:
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            sfld_text = sfld.text()
            HOME_SYMBOL = '~'
            try:
                if 'HOME' in os.environ:
                    HOME_SYMBOL = os.environ['HOME']
            except: # pylint: disable=bare-except
                pass
            try:
                if sfld_text:
                    if sfld_text[0] == '~':
                        sfld_text = sfld_text.replace('~', HOME_SYMBOL, 1)
            except: # pylint: disable=bare-except
                pass
            settings_arr = {
                "m3u": sm3u.text(),
                "epg": sepg.text(),
                "deinterlace": sdei.isChecked(),
                "udp_proxy": udp_proxy_text,
                "save_folder": sfld_text,
                "provider": sprov.currentText() if \
                    sprov.currentText() != '--{}--'.format(_('notselected')) else '',
                "nocache": supdate.isChecked(),
                "lang": lang1,
                "timezone": soffset.value(),
                "hwaccel": shwaccel.isChecked(),
                "sort": sort_widget.currentIndex(),
                "cache_secs": scache1.value(),
                "useragent": useragent_choose_2.currentIndex(),
                "mpv_options": mpv_options.text(),
                'donotupdateepg': donot_flag.isChecked(),
                'channelsonpage': channels_box.value(),
                'openprevchan': openprevchan_flag.isChecked(),
                'remembervol': remembervol_flag.isChecked(),
                'hidempv': hidempv_flag.isChecked(),
                'chaniconsfromepg': chaniconsfromepg_flag.isChecked(),
                'hideepgpercentage': hideepgpercentage_flag.isChecked(),
                'hidebitrateinfo': hidebitrateinfo_flag.isChecked(),
                'movedragging': movedragging_flag.isChecked(),
                'volumechangestep': volumechangestep_choose.value(),
                'themecompat': themecompat_flag.isChecked(),
                'exp2': exp2_input.value(),
                'mouseswitchchannels': mouseswitchchannels_flag.isChecked(),
                'showplaylistmouse': showplaylistmouse_flag.isChecked(),
                'hideplaylistleftclk': hideplaylistleftclk_flag.isChecked(),
                'showcontrolsmouse': showcontrolsmouse_flag.isChecked(),
                'flpopacity': flpopacity_input.value(),
                'panelposition': panelposition_choose.currentIndex(),
                'playlistsep': playlistsep_flag.isChecked(),
                'screenshot': screenshot_choose.currentIndex(),
                'videoaspect': videoaspect_def_choose.currentIndex(),
                'zoom': zoom_def_choose.currentIndex(),
                'panscan': panscan_def_choose.value(),
                'referer': referer_choose.text(),
                'gui': gui_choose.currentIndex()
            }
            settings_file1 = open(str(Path(LOCAL_DIR, 'settings.json')), 'w', encoding="utf8")
            settings_file1.write(json.dumps(settings_arr))
            settings_file1.close()
            settings_win.hide()
            if epg_thread:
                try:
                    epg_thread.kill()
                except: # pylint: disable=bare-except
                    epg_thread.terminate()
            if epg_thread_2:
                try:
                    epg_thread_2.kill()
                except: # pylint: disable=bare-except
                    epg_thread_2.terminate()
            for process_3 in active_children():
                try:
                    process_3.kill()
                except: # pylint: disable=bare-except
                    process_3.terminate()
            if manager:
                manager.shutdown()
            try:
                if channel_icons_data.manager_1:
                    channel_icons_data.manager_1.shutdown()
            except: # pylint: disable=bare-except
                pass
            try:
                if channel_icons_data_epg.manager_1:
                    channel_icons_data_epg.manager_1.shutdown()
            except: # pylint: disable=bare-except
                pass
            win.close()
            settings_win.close()
            help_win.close()
            streaminfo_win.close()
            license_win.close()
            time.sleep(0.1)
            if not os.name == 'nt':
                if args1.python:
                    os.execv(args1.python, ['python'] + sys.argv)
                else:
                    sys_executable = sys.executable
                    if not os.path.isfile(sys_executable):
                        sys_executable = str(
                            Path(os.path.dirname(os.path.abspath(__file__)), 'astroncia_iptv')
                        )
                        os.execv(sys_executable, sys.argv)
                    else:
                        os.execv(
                            sys_executable,
                            ['python'] + sys.argv + ['--python', sys_executable]
                        )
            stop_record()
            if os.name == 'nt':
                try:
                    os._exit(23) # pylint: disable=protected-access
                except: # pylint: disable=bare-except
                    sys.exit(23)
            else:
                sys.exit(0)

        wid2 = QtWidgets.QWidget()

        m3u_label = QtWidgets.QLabel('{}:'.format(_('m3uplaylist')))
        update_label = QtWidgets.QLabel('{}:'.format(_('updateatboot')))
        epg_label = QtWidgets.QLabel('{}:'.format(_('epgaddress')))
        dei_label = QtWidgets.QLabel('{}:'.format(_('deinterlace')))
        hwaccel_label = QtWidgets.QLabel('{}:'.format(_('hwaccel')))
        sort_label = QtWidgets.QLabel('{}:'.format(_('sort')))
        cache_label = QtWidgets.QLabel('{}:'.format(_('cache')))
        udp_label = QtWidgets.QLabel('{}:'.format(_('udpproxy')))
        fld_label = QtWidgets.QLabel('{}:'.format(_('writefolder')))
        lang_label = QtWidgets.QLabel('{}:'.format(_('interfacelang')))
        offset_label = QtWidgets.QLabel('{}:'.format(_('tvguideoffset')))
        #set_label = QtWidgets.QLabel(_('jtvoffsetrecommendation'))
        #set_label.setStyleSheet('color: #666600')
        fastview_label = QtWidgets.QLabel()
        fastview_label.setTextFormat(QtCore.Qt.RichText)
        fastview_label.setSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Minimum
        )
        fastview_label.setWordWrap(True)
        fastview_label.setText(
            '<span style="color:#1D877C;">' + _('fasterview') + '</span><br>'
        )
        hours_label = QtWidgets.QLabel(_('hours'))

        def reset_channel_settings():
            if os.path.isfile(str(Path(LOCAL_DIR, 'channels.json'))):
                os.remove(str(Path(LOCAL_DIR, 'channels.json')))
            if os.path.isfile(str(Path(LOCAL_DIR, 'favourites.json'))):
                os.remove(str(Path(LOCAL_DIR, 'favourites.json')))
            if os.path.isfile(str(Path(LOCAL_DIR, 'sort.json'))):
                os.remove(str(Path(LOCAL_DIR, 'sort.json')))
            save_settings()
        def reset_prov():
            if sprov.currentText() != '--{}--'.format(_('notselected')):
                sprov.setCurrentIndex(0)
        def combo_reset():
            if sepgcombox.currentIndex() != 0:
                reset_prov()

        sm3u = QtWidgets.QLineEdit()
        sm3u.setPlaceholderText(_('filepath'))
        sm3u.setText(settings['m3u'])
        sm3u.textEdited.connect(reset_prov)
        sepg = QtWidgets.QLineEdit()
        sepg.setPlaceholderText(_('filepath'))
        sepg.setText(settings['epg'] if not settings['epg'].startswith('^^::MULTIPLE::^^') else '')
        sepg.textEdited.connect(reset_prov)
        sepgcombox = QtWidgets.QComboBox()
        sepgcombox.setLineEdit(sepg)
        sepgcombox.addItems(
            [settings['epg'] if not \
                settings['epg'].startswith('^^::MULTIPLE::^^') else ''] + EPG_URLS
        )
        sepgcombox.currentIndexChanged.connect(combo_reset)
        sudp = QtWidgets.QLineEdit()
        sudp.setText(settings['udp_proxy'])
        sdei = QtWidgets.QCheckBox()
        sdei.setChecked(settings['deinterlace'])
        shwaccel = QtWidgets.QCheckBox()
        shwaccel.setChecked(settings['hwaccel'])
        supdate = QtWidgets.QCheckBox()
        supdate.setChecked(settings['nocache'])
        sfld = QtWidgets.QLineEdit()
        sfld.setText(settings['save_folder'])
        scache = QtWidgets.QLabel(_('seconds'))
        sselect = QtWidgets.QLabel("{}:".format(_('orselectyourprovider')))
        sselect.setStyleSheet('color: #00008B;')
        ssave = QtWidgets.QPushButton(_('savesettings'))
        ssave.setStyleSheet('font-weight: bold; color: green;')
        ssave.clicked.connect(save_settings)
        sreset = QtWidgets.QPushButton(_('resetchannelsettings'))
        sreset.clicked.connect(reset_channel_settings)
        sort_widget = QtWidgets.QComboBox()
        sort_widget.addItem(_('sortitems1'))
        sort_widget.addItem(_('sortitems2'))
        sort_widget.addItem(_('sortitems3'))
        sort_widget.addItem(_('sortitems4'))
        sort_widget.setCurrentIndex(settings['sort'])
        sprov = QtWidgets.QComboBox()
        slang = QtWidgets.QComboBox()
        lng0 = -1
        for lng in lang:
            lng0 += 1
            slang.addItem(lang[lng]['strings']['name'])
            if lang[lng]['strings']['name'] == LANG_NAME:
                slang.setCurrentIndex(lng0)
        def close_settings():
            settings_win.hide()
            if not win.isVisible():
                current_pid1 = os.getpid()
                if not os.name == 'nt':
                    os.killpg(0, signal.SIGKILL)
                else:
                    os.kill(current_pid1, signal.SIGTERM)
                sys.exit(0)
        def prov_select(self): # pylint: disable=unused-argument
            prov1 = sprov.currentText()
            if prov1 != '--{}--'.format(_('notselected')):
                sm3u.setText(iptv_playlists[prov1]['m3u'])
                if 'epg' in iptv_playlists[prov1]:
                    sepg.setText(iptv_playlists[prov1]['epg'] if not \
                        iptv_playlists[prov1]['epg'].startswith('^^::MULTIPLE::^^') else '')
        sprov.currentIndexChanged.connect(prov_select)
        sprov.addItem('--{}--'.format(_('notselected')))
        provs = {}
        ic3 = 0
        for prov in iptv_playlists:
            ic3 += 1
            provs[prov] = ic3
            sprov.addItem(prov)
        if settings['provider'] and settings['provider'] in provs:
            prov_d = provs[settings['provider']]
            if prov_d and prov_d != -1:
                try:
                    sprov.setCurrentIndex(prov_d)
                except: # pylint: disable=bare-except
                    pass
        sclose = QtWidgets.QPushButton(_('close'))
        sclose.setStyleSheet('color: red;')
        sclose.clicked.connect(close_settings)

        def update_m3u():
            if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            save_settings()

        sm3ufile = QtWidgets.QPushButton()
        sm3ufile.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'file.png'))))
        sm3ufile.clicked.connect(m3u_select)
        sm3uupd = QtWidgets.QPushButton()
        sm3uupd.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'update.png'))))
        sm3uupd.clicked.connect(update_m3u)
        sm3uupd.setToolTip(_('update'))

        sepgfile = QtWidgets.QPushButton()
        sepgfile.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'file.png'))))
        sepgfile.clicked.connect(epg_select)
        sepgupd = QtWidgets.QPushButton()
        sepgupd.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'update.png'))))
        sepgupd.clicked.connect(force_update_epg)
        sepgupd.setToolTip(_('update'))

        sfolder = QtWidgets.QPushButton()
        sfolder.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'file.png'))))
        sfolder.clicked.connect(save_folder_select)

        soffset = QtWidgets.QDoubleSpinBox()
        soffset.setMinimum(-240)
        soffset.setMaximum(240)
        soffset.setSingleStep(1)
        soffset.setDecimals(1)
        soffset.setValue(settings["timezone"])

        scache1 = QtWidgets.QSpinBox()
        scache1.setMinimum(0)
        scache1.setMaximum(120)
        scache1.setValue(settings["cache_secs"])

        def xtream_select():
            sm3u_text = sm3u.text()
            if sm3u_text.startswith('XTREAM::::::::::::::'):
                sm3u_text_sp = sm3u_text.split('::::::::::::::')
                xtr_username_input.setText(sm3u_text_sp[1])
                xtr_password_input.setText(sm3u_text_sp[2])
                xtr_url_input.setText(sm3u_text_sp[3])
                reset_prov()
            moveWindowToCenter(xtream_win)
            xtream_win.show()

        def xtream_select_1():
            m3u_edit_1_text = m3u_edit_1.text()
            if m3u_edit_1_text.startswith('XTREAM::::::::::::::'):
                m3u_edit_1_text_sp = m3u_edit_1_text.split('::::::::::::::')
                xtr_username_input_2.setText(m3u_edit_1_text_sp[1])
                xtr_password_input_2.setText(m3u_edit_1_text_sp[2])
                xtr_url_input_2.setText(m3u_edit_1_text_sp[3])
                reset_prov()
            moveWindowToCenter(xtream_win_2)
            xtream_win_2.show()

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)
        grid.addWidget(fastview_label, 0, 0)

        useragent_lbl_2 = QtWidgets.QLabel("{}:".format(_('useragent')))
        referer_lbl = QtWidgets.QLabel("HTTP Referer:")
        referer_choose = QtWidgets.QLineEdit()
        referer_choose.setText(settings["referer"])
        useragent_choose_2 = QtWidgets.QComboBox()
        useragent_choose_2.addItem(_('empty'))
        for ua_name_2 in ua_names[1::]:
            useragent_choose_2.addItem(ua_name_2)
        useragent_choose_2.setCurrentIndex(settings['useragent'])

        mpv_label = QtWidgets.QLabel("{} ({}):".format(
            _('mpv_options'),
            '<a href="https://mpv.io/manual/master/#options">{}</a>'.format(
                _('list')
            )
        ))
        mpv_label.setOpenExternalLinks(True)
        mpv_label.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse)
        mpv_options = QtWidgets.QLineEdit()
        mpv_options.setText(settings['mpv_options'])
        donot_label = QtWidgets.QLabel("{}:".format(_('donotupdateepg')))
        donot_flag = QtWidgets.QCheckBox()
        donot_flag.setChecked(settings['donotupdateepg'])

        gui_label = QtWidgets.QLabel("{}:".format(_('epg_gui')))
        openprevchan_label = QtWidgets.QLabel("{}:".format(_('openprevchan')))
        remembervol_label = QtWidgets.QLabel("{}:".format(_('remembervol')))
        hidempv_label = QtWidgets.QLabel("{}:".format(_('hidempv')))
        chaniconsfromepg_label = QtWidgets.QLabel("{}:".format(_('chaniconsfromepg')))
        hideepgpercentage_label = QtWidgets.QLabel("{}:".format(_('hideepgpercentage')))
        hidebitrateinfo_label = QtWidgets.QLabel("{}:".format(_('hidebitrateinfo')))
        movedragging_label = QtWidgets.QLabel("{}:".format(_('movedragging')))
        volumechangestep_label = QtWidgets.QLabel("{}:".format(_('volumechangestep')))
        channels_label = QtWidgets.QLabel("{}:".format(_('channelsonpage')))
        channels_box = QtWidgets.QSpinBox()
        channels_box.setSuffix('    ')
        channels_box.setMinimum(1)
        channels_box.setMaximum(100)
        channels_box.setValue(settings["channelsonpage"])
        gui_choose = QtWidgets.QComboBox()
        gui_choose.addItem(_('classic'))
        gui_choose.addItem(_('simple'))
        gui_choose.addItem(_('simple_noicons'))
        gui_choose.setCurrentIndex(settings['gui'])

        openprevchan_flag = QtWidgets.QCheckBox()
        openprevchan_flag.setChecked(settings['openprevchan'])

        remembervol_flag = QtWidgets.QCheckBox()
        remembervol_flag.setChecked(settings['remembervol'])

        hidempv_flag = QtWidgets.QCheckBox()
        hidempv_flag.setChecked(settings['hidempv'])

        chaniconsfromepg_flag = QtWidgets.QCheckBox()
        chaniconsfromepg_flag.setChecked(settings['chaniconsfromepg'])

        hideepgpercentage_flag = QtWidgets.QCheckBox()
        hideepgpercentage_flag.setChecked(settings['hideepgpercentage'])

        hidebitrateinfo_flag = QtWidgets.QCheckBox()
        hidebitrateinfo_flag.setChecked(settings['hidebitrateinfo'])

        movedragging_flag = QtWidgets.QCheckBox()
        movedragging_flag.setChecked(settings['movedragging'])

        themecompat_label = QtWidgets.QLabel("{}:".format(_('themecompat')))
        themecompat_flag = QtWidgets.QCheckBox()
        themecompat_flag.setChecked(settings['themecompat'])

        exp_warning = QtWidgets.QLabel(_('expwarning'))
        exp_warning.setStyleSheet('color:red')
        exp2_label = QtWidgets.QLabel("{}:".format(_('exp2')))
        exp2_input = QtWidgets.QSpinBox()
        exp2_input.setMaximum(9999)
        exp2_input.setValue(settings['exp2'])

        volumechangestep_choose = QtWidgets.QSpinBox()
        volumechangestep_choose.setMinimum(1)
        volumechangestep_choose.setMaximum(50)
        volumechangestep_choose.setValue(settings['volumechangestep'])

        flpopacity_label = QtWidgets.QLabel("{}:".format(_('flpopacity')))
        flpopacity_input = QtWidgets.QDoubleSpinBox()
        flpopacity_input.setMinimum(0.01)
        flpopacity_input.setMaximum(1)
        flpopacity_input.setSingleStep(0.1)
        flpopacity_input.setDecimals(2)
        flpopacity_input.setValue(settings['flpopacity'])

        panelposition_label = QtWidgets.QLabel("{}:".format(_('panelposition')))
        panelposition_choose = QtWidgets.QComboBox()
        panelposition_choose.addItem(_('right'))
        panelposition_choose.addItem(_('left'))
        panelposition_choose.setCurrentIndex(settings['panelposition'])

        playlistsep_label = QtWidgets.QLabel("{}:".format(_('playlistsep')))
        playlistsep_flag = QtWidgets.QCheckBox()
        playlistsep_flag.setChecked(settings['playlistsep'])

        screenshot_label = QtWidgets.QLabel("{}:".format(_('doscreenshotsvia')))
        screenshot_choose = QtWidgets.QComboBox()
        screenshot_choose.addItem('mpv')
        screenshot_choose.addItem('ffmpeg')
        screenshot_choose.setCurrentIndex(settings['screenshot'])

        mouseswitchchannels_label = QtWidgets.QLabel("{}:".format(_('mouseswitchchannels')))
        defaultchangevol_label = QtWidgets.QLabel("({})".format(_('defaultchangevol')))
        defaultchangevol_label.setStyleSheet('color:blue')
        mouseswitchchannels_flag = QtWidgets.QCheckBox()
        mouseswitchchannels_flag.setChecked(settings['mouseswitchchannels'])

        showplaylistmouse_label = QtWidgets.QLabel("{}:".format(_('showplaylistmouse')))
        showplaylistmouse_flag = QtWidgets.QCheckBox()
        showplaylistmouse_flag.setChecked(settings['showplaylistmouse'])
        showcontrolsmouse_label = QtWidgets.QLabel("{}:".format(_('showcontrolsmouse')))
        showcontrolsmouse_flag = QtWidgets.QCheckBox()
        showcontrolsmouse_flag.setChecked(settings['showcontrolsmouse'])

        hideplaylistleftclk_label = QtWidgets.QLabel("{}:".format(_('hideplaylistleftclk')))
        hideplaylistleftclk_flag = QtWidgets.QCheckBox()
        hideplaylistleftclk_flag.setChecked(settings['hideplaylistleftclk'])

        videoaspectdef_label = QtWidgets.QLabel("{}:".format(_('videoaspect')))
        zoomdef_label = QtWidgets.QLabel("{}:".format(_('zoom')))
        panscan_def_label = QtWidgets.QLabel("{}:".format(_('panscan')))

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

        videoaspect_def_choose.setCurrentIndex(settings['videoaspect'])
        zoom_def_choose.setCurrentIndex(settings['zoom'])
        panscan_def_choose.setValue(settings['panscan'])

        tabs = QtWidgets.QTabWidget()

        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        tab5 = QtWidgets.QWidget()
        tab6 = QtWidgets.QWidget()
        tabs.addTab(tab1, _('tab_main'))
        tabs.addTab(tab2, _('tab_video'))
        tabs.addTab(tab3, _('tab_network'))
        tabs.addTab(tab5, _('tab_gui'))
        tabs.addTab(tab6, _('actions'))
        tabs.addTab(tab4, _('tab_other'))
        tab1.layout = QtWidgets.QGridLayout()
        tab1.layout.addWidget(lang_label, 0, 0)
        tab1.layout.addWidget(slang, 0, 1)
        tab1.layout.addWidget(fld_label, 1, 0)
        tab1.layout.addWidget(sfld, 1, 1)
        tab1.layout.addWidget(sfolder, 1, 2)
        tab1.layout.addWidget(sort_label, 2, 0)
        tab1.layout.addWidget(sort_widget, 2, 1)
        tab1.layout.addWidget(update_label, 3, 0)
        tab1.layout.addWidget(supdate, 3, 1)
        tab1.layout.addWidget(openprevchan_label, 4, 0)
        tab1.layout.addWidget(openprevchan_flag, 4, 1)
        tab1.layout.addWidget(remembervol_label, 5, 0)
        tab1.layout.addWidget(remembervol_flag, 5, 1)
        tab1.setLayout(tab1.layout)

        tab2.layout = QtWidgets.QGridLayout()
        tab2.layout.addWidget(dei_label, 0, 0)
        tab2.layout.addWidget(sdei, 0, 1)
        tab2.layout.addWidget(hwaccel_label, 1, 0)
        tab2.layout.addWidget(shwaccel, 1, 1)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 2)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 3)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 4)
        tab2.layout.addWidget(videoaspectdef_label, 2, 0)
        tab2.layout.addWidget(videoaspect_def_choose, 2, 1)
        tab2.layout.addWidget(zoomdef_label, 3, 0)
        tab2.layout.addWidget(zoom_def_choose, 3, 1)
        tab2.layout.addWidget(panscan_def_label, 4, 0)
        tab2.layout.addWidget(panscan_def_choose, 4, 1)
        tab2.layout.addWidget(QtWidgets.QLabel(), 5, 0)
        tab2.setLayout(tab2.layout)

        tab3.layout = QtWidgets.QGridLayout()
        tab3.layout.addWidget(udp_label, 0, 0)
        tab3.layout.addWidget(sudp, 0, 1)
        tab3.layout.addWidget(cache_label, 1, 0)
        tab3.layout.addWidget(scache1, 1, 1)
        tab3.layout.addWidget(scache, 1, 2)
        tab3.layout.addWidget(useragent_lbl_2, 2, 0)
        tab3.layout.addWidget(useragent_choose_2, 2, 1)
        tab3.layout.addWidget(referer_lbl, 3, 0)
        tab3.layout.addWidget(referer_choose, 3, 1)
        tab3.setLayout(tab3.layout)

        tab4.layout = QtWidgets.QGridLayout()
        tab4.layout.addWidget(mpv_label, 0, 0)
        tab4.layout.addWidget(mpv_options, 0, 1)
        tab4.layout.addWidget(donot_label, 1, 0)
        tab4.layout.addWidget(donot_flag, 1, 1)
        tab4.layout.addWidget(themecompat_label, 2, 0)
        tab4.layout.addWidget(themecompat_flag, 2, 1)
        tab4.layout.addWidget(hidempv_label, 3, 0)
        tab4.layout.addWidget(hidempv_flag, 3, 1)
        tab4.layout.addWidget(chaniconsfromepg_label, 4, 0)
        tab4.layout.addWidget(chaniconsfromepg_flag, 4, 1)
        tab4.layout.addWidget(volumechangestep_label, 5, 0)
        tab4.layout.addWidget(volumechangestep_choose, 5, 1)
        tab4.layout.addWidget(screenshot_label, 6, 0)
        tab4.layout.addWidget(screenshot_choose, 6, 1)
        tab4.layout.addWidget(hideplaylistleftclk_label, 7, 0)
        tab4.layout.addWidget(hideplaylistleftclk_flag, 7, 1)
        tab4.setLayout(tab4.layout)

        tab5.layout = QtWidgets.QGridLayout()
        tab5.layout.addWidget(gui_label, 0, 0)
        tab5.layout.addWidget(gui_choose, 0, 1)
        tab5.layout.addWidget(QtWidgets.QLabel(), 0, 2)
        tab5.layout.addWidget(QtWidgets.QLabel(), 0, 3)
        tab5.layout.addWidget(QtWidgets.QLabel(), 0, 4)
        tab5.layout.addWidget(channels_label, 1, 0)
        tab5.layout.addWidget(channels_box, 1, 1)
        #tab5.layout.addWidget(QtWidgets.QLabel(), 3, 0)
        tab5.layout.addWidget(panelposition_label, 2, 0)
        tab5.layout.addWidget(panelposition_choose, 2, 1)
        tab5.layout.addWidget(playlistsep_label, 3, 0)
        tab5.layout.addWidget(playlistsep_flag, 3, 1)
        tab5.layout.addWidget(exp2_label, 4, 0)
        tab5.layout.addWidget(exp2_input, 4, 1)
        tab5.layout.addWidget(hideepgpercentage_label, 5, 0)
        tab5.layout.addWidget(hideepgpercentage_flag, 5, 1)
        tab5.layout.addWidget(hidebitrateinfo_label, 6, 0)
        tab5.layout.addWidget(hidebitrateinfo_flag, 6, 1)
        tab5.layout.addWidget(movedragging_label, 7, 0)
        tab5.layout.addWidget(movedragging_flag, 7, 1)
        #tab5.layout.addWidget(QtWidgets.QLabel(), 8, 0)
        tab5.setLayout(tab5.layout)

        tab6.layout = QtWidgets.QGridLayout()
        tab6.layout.addWidget(mouseswitchchannels_label, 0, 0)
        tab6.layout.addWidget(mouseswitchchannels_flag, 0, 1)
        tab6.layout.addWidget(QtWidgets.QLabel(), 0, 2)
        tab6.layout.addWidget(QtWidgets.QLabel(), 0, 3)
        tab6.layout.addWidget(defaultchangevol_label, 1, 0)
        tab6.layout.addWidget(QtWidgets.QLabel(), 2, 0)
        tab6.layout.addWidget(showplaylistmouse_label, 3, 0)
        tab6.layout.addWidget(showplaylistmouse_flag, 3, 1)
        tab6.layout.addWidget(showcontrolsmouse_label, 4, 0)
        tab6.layout.addWidget(showcontrolsmouse_flag, 4, 1)
        tab6.setLayout(tab6.layout)

        grid2 = QtWidgets.QVBoxLayout()
        grid2.addWidget(tabs)

        grid3 = QtWidgets.QGridLayout()
        grid3.setSpacing(0)

        ssaveclose = QtWidgets.QWidget()
        ssaveclose_layout = QtWidgets.QHBoxLayout()
        ssaveclose_layout.addWidget(ssave)
        ssaveclose_layout.addWidget(sclose)
        ssaveclose.setLayout(ssaveclose_layout)

        grid3.addWidget(ssaveclose, 2, 1)
        grid3.addWidget(sreset, 3, 1)

        layout2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(grid)
        layout2.addLayout(grid2)
        layout2.addLayout(grid3)

        wid2.setLayout(layout2)
        #settings_win.setCentralWidget(wid2)
        settings_win.scroll.setWidget(wid2)

        def xtream_save_btn_action():
            if xtr_username_input.text() and xtr_password_input.text() and xtr_url_input.text():
                xtream_gen_url = 'XTREAM::::::::::::::' + '::::::::::::::'.join(
                    [xtr_username_input.text(), xtr_password_input.text(), xtr_url_input.text()]
                )
                sm3u.setText(xtream_gen_url)
                reset_prov()
            xtream_win.hide()

        def xtream_save_btn_action_2():
            if xtr_username_input_2.text() and \
                xtr_password_input_2.text() and xtr_url_input_2.text():
                xtream_gen_url_2 = 'XTREAM::::::::::::::' + '::::::::::::::'.join(
                    [
                        xtr_username_input_2.text(),
                        xtr_password_input_2.text(),
                        xtr_url_input_2.text()
                    ]
                )
                m3u_edit_1.setText(xtream_gen_url_2)
                reset_prov()
            xtream_win_2.hide()

        wid3 = QtWidgets.QWidget()
        wid4 = QtWidgets.QWidget()

        save_btn_xtream = QtWidgets.QPushButton(_('save'))
        save_btn_xtream.setStyleSheet('font-weight: bold; color: green;')
        save_btn_xtream.clicked.connect(xtream_save_btn_action)
        xtr_username_input = QtWidgets.QLineEdit()
        xtr_password_input = QtWidgets.QLineEdit()
        xtr_url_input = QtWidgets.QLineEdit()

        layout34 = QtWidgets.QGridLayout()
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_('username'))), 0, 0)
        layout34.addWidget(xtr_username_input, 0, 1)
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_('password'))), 1, 0)
        layout34.addWidget(xtr_password_input, 1, 1)
        layout34.addWidget(QtWidgets.QLabel("{}:".format(_('url'))), 2, 0)
        layout34.addWidget(xtr_url_input, 2, 1)
        layout34.addWidget(save_btn_xtream, 3, 1)
        wid3.setLayout(layout34)

        save_btn_xtream_2 = QtWidgets.QPushButton(_('save'))
        save_btn_xtream_2.setStyleSheet('font-weight: bold; color: green;')
        save_btn_xtream_2.clicked.connect(xtream_save_btn_action_2)
        xtr_username_input_2 = QtWidgets.QLineEdit()
        xtr_password_input_2 = QtWidgets.QLineEdit()
        xtr_url_input_2 = QtWidgets.QLineEdit()

        layout35 = QtWidgets.QGridLayout()
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_('username'))), 0, 0)
        layout35.addWidget(xtr_username_input_2, 0, 1)
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_('password'))), 1, 0)
        layout35.addWidget(xtr_password_input_2, 1, 1)
        layout35.addWidget(QtWidgets.QLabel("{}:".format(_('url'))), 2, 0)
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

        license_str = "GPLv3"
        if os.path.isfile(str(Path('astroncia', 'license.txt'))):
            license_file = open(
                str(Path('astroncia', 'license.txt')), 'r', encoding="utf8"
            )
            license_str = license_file.read()
            license_file.close()

        licensebox = QtWidgets.QPlainTextEdit()
        licensebox.setReadOnly(True)
        licensebox.setPlainText(license_str)

        licensebox_close_btn = QtWidgets.QPushButton()
        licensebox_close_btn.setText(_('close'))
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

        class Communicate(QtCore.QObject): # pylint: disable=too-few-public-methods
            winPosition = False
            winPosition2 = False
            do_play_args = ()
            j_save = None
            comboboxIndex = -1
            if qt_library == 'PySide6':
                repaintUpdates = QtCore.Signal(object, object)
                moveSeparatePlaylist = QtCore.Signal(object)
                mainThread = QtCore.Signal(type(lambda x: None))
                mainThread_partial = QtCore.Signal(type(partial(int, 2)))
            else:
                repaintUpdates = QtCore.pyqtSignal(object, object)
                moveSeparatePlaylist = QtCore.pyqtSignal(object)
                mainThread = QtCore.pyqtSignal(type(lambda x: None))
                mainThread_partial = QtCore.pyqtSignal(type(partial(int, 2)))

        #def exInMainThread(m_func):
        #    comm_instance.mainThread.emit(m_func)

        def exInMainThread_partial(m_func_2):
            comm_instance.mainThread_partial.emit(m_func_2)

        @async_function
        def async_webbrowser():
            webbrowser.open(UPDATE_RELEASES_URL)

        def check_for_updates_pt2(last_avail_version_2, noWin):
            if last_avail_version_2:
                if APP_VERSION == '__DEB' + '_VERSION__':
                    fail_version_msg = QtWidgets.QMessageBox(
                        qt_icon_critical,
                        MAIN_WINDOW_TITLE,
                        _('newversiongetfail'),
                        QtWidgets.QMessageBox.Ok
                    )
                    fail_version_msg.exec()
                else:
                    if APP_VERSION == last_avail_version_2:
                        lastversion_installed_msg = QtWidgets.QMessageBox(
                            qt_icon_information,
                            MAIN_WINDOW_TITLE,
                            _('gotlatestversion'),
                            QtWidgets.QMessageBox.Ok
                        )
                        lastversion_installed_msg.exec()
                    else:
                        newversion_avail_msg = QtWidgets.QMessageBox.question(
                            None,
                            MAIN_WINDOW_TITLE,
                            _('newversionavail'),
                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                            QtWidgets.QMessageBox.Yes
                        )
                        if newversion_avail_msg == QtWidgets.QMessageBox.Yes:
                            async_webbrowser()
            else:
                fail_version_msg = QtWidgets.QMessageBox(
                    qt_icon_critical,
                    MAIN_WINDOW_TITLE,
                    _('newversiongetfail'),
                    QtWidgets.QMessageBox.Ok
                )
                fail_version_msg.exec()
            checkupdates_btn.setEnabled(True)
            if not noWin:
                moveWindowToCenter(help_win)
                help_win.show()
                help_win.raise_()
                help_win.setFocus(QtCore.Qt.PopupFocusReason)
                help_win.activateWindow()

        def move_separate_playlist_func(seppl_qpoint):
            print_with_time("Moving separate playlist to QPoint({}, {})".format(
                seppl_qpoint.x(),
                seppl_qpoint.y()
            ))
            sepplaylist_win.move(seppl_qpoint)
            sepplaylist_win.show()
            #sepplaylist_win.raise_()
            #sepplaylist_win.setFocus(QtCore.Qt.PopupFocusReason)
            #sepplaylist_win.activateWindow()

        def comm_instance_main_thread(th_func):
            th_func()

        comm_instance = Communicate()
        comm_instance.repaintUpdates.connect(check_for_updates_pt2)
        comm_instance.moveSeparatePlaylist.connect(move_separate_playlist_func)
        comm_instance.mainThread.connect(comm_instance_main_thread)
        comm_instance.mainThread_partial.connect(comm_instance_main_thread)

        @async_function
        def check_for_updates(self, noWin): # pylint: disable=unused-argument
            last_avail_version = False
            try:
                last_avail_version = json.loads(requests.get(
                    UPDATE_URL,
                    headers={'User-Agent': ''},
                    timeout=2
                ).text)['version'].strip()
            except: # pylint: disable=bare-except
                pass
            comm_instance.repaintUpdates.emit(last_avail_version, noWin)

        def check_for_updates_0(noWin=False):
            checkupdates_btn.setEnabled(False)
            check_for_updates(None, noWin)

        checkupdates_btn = QtWidgets.QPushButton()
        checkupdates_btn.setText(_('checkforupdates'))
        checkupdates_btn.clicked.connect(check_for_updates_0)

        license_btn = QtWidgets.QPushButton()
        license_btn.setText(_('license'))
        license_btn.clicked.connect(show_license)

        def aboutqt_show():
            QtWidgets.QMessageBox.aboutQt(QtWidgets.QWidget(), MAIN_WINDOW_TITLE)
            help_win.raise_()
            help_win.setFocus(QtCore.Qt.PopupFocusReason)
            help_win.activateWindow()

        aboutqt_btn = QtWidgets.QPushButton()
        aboutqt_btn.setText(_('aboutqt'))
        aboutqt_btn.clicked.connect(aboutqt_show)

        close_btn = QtWidgets.QPushButton()
        close_btn.setText(_('close'))
        close_btn.clicked.connect(help_win.close)

        helpwin_widget_btns = QtWidgets.QWidget()
        helpwin_widget_btns_layout = QtWidgets.QHBoxLayout()
        #helpwin_widget_btns_layout.addWidget(checkupdates_btn)
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

        def playlists_selected():
            try:
                prov_data = playlists_data.playlists_used[playlists_list.currentItem().text()]
                prov_m3u = prov_data['m3u']
                prov_epg = ''
                if 'epg' in prov_data:
                    prov_epg = prov_data['epg']
                prov_offset = prov_data['offset']
                sm3u.setText(prov_m3u)
                sepg.setText(prov_epg if not prov_epg.startswith('^^::MULTIPLE::^^') else '')
                soffset.setValue(prov_offset)
                sprov.setCurrentIndex(0)
                playlists_save_json()
                playlists_win.hide()
                playlists_win_edit.hide()
                save_settings()
            except: # pylint: disable=bare-except
                pass

        def playlists_save_json():
            playlists_json_save(playlists_data.playlists_used)

        def playlists_edit_do(ignore0=False):
            try:
                currentItem_text = playlists_list.currentItem().text()
            except: # pylint: disable=bare-except
                currentItem_text = ""
            if ignore0:
                name_edit_1.setText("")
                m3u_edit_1.setText("")
                epg_edit_1_settext("")
                soffset_1.setValue(DEF_TIMEZONE)
                playlists_data.oldName = ""
                moveWindowToCenter(playlists_win_edit)
                playlists_win_edit.show()
            else:
                if currentItem_text:
                    item_m3u = playlists_data.playlists_used[currentItem_text]['m3u']
                    try:
                        item_epg = playlists_data.playlists_used[currentItem_text]['epg']
                    except: # pylint: disable=bare-except
                        item_epg = ""
                    item_offset = playlists_data.playlists_used[currentItem_text]['offset']
                    name_edit_1.setText(currentItem_text)
                    m3u_edit_1.setText(item_m3u)
                    epg_edit_1_settext(item_epg)
                    soffset_1.setValue(item_offset)
                    playlists_data.oldName = currentItem_text
                    moveWindowToCenter(playlists_win_edit)
                    playlists_win_edit.show()

        def playlists_delete_do():
            try:
                currentItem_text = playlists_list.currentItem().text()
            except: # pylint: disable=bare-except
                currentItem_text = ""
            if currentItem_text:
                playlists_list.takeItem(playlists_list.currentRow())
                playlists_data.playlists_used.pop(currentItem_text)
                playlists_save_json()

        def playlists_add_do():
            playlists_edit_do(True)

        def playlists_import_do():
            global playlists_saved
            playlists_hypnotix = {}
            print_with_time("Fetching playlists from Hypnotix...")
            try:
                hypnotix_cmd = "dconf dump /org/x/hypnotix/ 2>/dev/null | grep" + \
                    " '^providers=' | sed 's/^providers=/{\"hypnotix\": /g'" + \
                    " | sed 's/$/}/g' | sed \"s/'/\\\"/g\""
                hypnotix_cmd_eval = subprocess.check_output(
                    hypnotix_cmd, shell=True, text=True
                ).strip()
                if hypnotix_cmd_eval:
                    hypnotix_cmd_eval = json.loads(hypnotix_cmd_eval)['hypnotix']
                    for provider_2 in hypnotix_cmd_eval:
                        provider_2 = provider_2.replace(':' * 9, '^' * 9).split(':::')
                        provider_2[2] = provider_2[2].split('^' * 9)
                        provider_2[2][0] = provider_2[2][0].replace('file://', '')
                        prov_name_2 = provider_2[0]
                        prov_m3u_2 = provider_2[2][0]
                        prov_epg_2 = provider_2[2][1]
                        playlists_hypnotix[prov_name_2] = {
                            "m3u": prov_m3u_2,
                            "epg": prov_epg_2,
                            "offset": DEF_TIMEZONE
                        }
            except: # pylint: disable=bare-except
                print_with_time("Failed fetching playlists from Hypnotix!")
            if playlists_hypnotix:
                try:
                    playlists_list.takeItem(
                        playlists_list.row(
                            playlists_list.findItems(def_provider_name, QtCore.Qt.MatchExactly)[0]
                        )
                    )
                    playlists_data.playlists_used.pop(def_provider_name)
                except: # pylint: disable=bare-except
                    pass
                playlists_data.playlists_used = playlists_hypnotix
                playlists_saved = playlists_hypnotix
                for prov_name_4 in playlists_data.playlists_used:
                    playlists_list.addItem(prov_name_4)
                playlists_save_json()
                print_with_time("Successfully imported playlists from Hypnotix!")
                playlists_win.hide()
                playlists_win_edit.hide()
                save_settings()
            else:
                print_with_time("No Hypnotix playlists found!")
                hypnotix_msg = QtWidgets.QMessageBox(
                    qt_icon_information,
                    MAIN_WINDOW_TITLE,
                    _('nohypnotixpf'),
                    QtWidgets.QMessageBox.Ok
                )
                hypnotix_msg.exec()

        def playlists_reset_do():
            global playlists_saved
            playlists_data.playlists_used = playlists_saved_default
            playlists_saved = playlists_saved_default
            playlists_save_json()
            playlists_win.hide()
            playlists_win_edit.hide()
            save_settings()

        playlists_list.itemDoubleClicked.connect(playlists_selected)
        playlists_select.clicked.connect(playlists_selected)
        playlists_add.clicked.connect(playlists_add_do)
        playlists_edit.clicked.connect(playlists_edit_do)
        playlists_delete.clicked.connect(playlists_delete_do)
        playlists_import.clicked.connect(playlists_import_do)
        playlists_reset.clicked.connect(playlists_reset_do)

        fullscreen = False
        newdockWidgetHeight = False
        newdockWidgetPosition = False

        def init_mpv_player(): # pylint: disable=too-many-branches
            global player
            try:
                player = mpv.MPV(
                    **options,
                    wid=str(int(win.container.winId())),
                    osc=True,
                    script_opts='osc-layout=box,osc-seekbarstyle=bar,' + \
                        'osc-deadzonesize=0,osc-minmousemove=3',
                    ytdl=True,
                    log_handler=my_log,
                    loglevel='info' # debug
                )
            except: # pylint: disable=bare-except
                print_with_time("mpv init with ytdl failed")
                try:
                    player = mpv.MPV(
                        **options,
                        wid=str(int(win.container.winId())),
                        osc=True,
                        script_opts='osc-layout=box,osc-seekbarstyle=bar,' + \
                            'osc-deadzonesize=0,osc-minmousemove=3',
                        log_handler=my_log,
                        loglevel='info' # debug
                    )
                except: # pylint: disable=bare-except
                    print_with_time("mpv init with osc failed")
                    player = mpv.MPV(
                        **options,
                        wid=str(int(win.container.winId())),
                        log_handler=my_log,
                        loglevel='info' # debug
                    )
            if settings["hidempv"]:
                try:
                    player.osc = False
                except: # pylint: disable=bare-except
                    print_with_time("player.osc set failed")
            try:
                player['force-seekable'] = True
            except: # pylint: disable=bare-except
                pass
            if not settings['hwaccel']:
                try:
                    player['x11-bypass-compositor'] = 'yes'
                except: # pylint: disable=bare-except
                    pass
            try:
                player['network-timeout'] = 5
            except: # pylint: disable=bare-except
                pass

            try:
                mpv_version = player.mpv_version
                if not mpv_version.startswith('mpv '):
                    mpv_version = 'mpv ' + mpv_version
            except: # pylint: disable=bare-except
                mpv_version = "unknown mpv version"

            print_with_time("Using {}".format(mpv_version))

            textbox.setText(
                format_about_text(
                    "{} Qt {} ({}) {}\n{} {}\n\n".format(
                        _('using'), qt_version, qt_library, QT_URL,
                        _('using'), mpv_version.replace('mpv ', MPV_URL)
                    ) + \
                    _('helptext').format(APP_VERSION)
                )
            )

            if settings["cache_secs"] != 0:
                try:
                    player['demuxer-readahead-secs'] = settings["cache_secs"]
                    print_with_time('Demuxer cache set to {}s'.format(settings["cache_secs"]))
                except: # pylint: disable=bare-except
                    pass
                try:
                    player['cache-secs'] = settings["cache_secs"]
                    print_with_time('Cache set to {}s'.format(settings["cache_secs"]))
                except: # pylint: disable=bare-except
                    pass
            else:
                print_with_time("Using default cache settings")
            player.user_agent = def_user_agent
            if settings["referer"]:
                player.http_header_fields = "Referer: {}".format(settings["referer"])
                print_with_time("HTTP referer: '{}'".format(settings["referer"]))
            else:
                print_with_time("No HTTP referer set up")
            mpv_override_volume(100)
            player.loop = True

            try:
                populate_menubar(
                    0, win.menu_bar_qt, win, player.track_list, playing_chan, get_keybind,
                    CHECK_UPDATES_ENABLED
                )
                populate_menubar(
                    1, right_click_menu, win, player.track_list, playing_chan, get_keybind,
                    CHECK_UPDATES_ENABLED
                )
            except: # pylint: disable=bare-except
                print_with_time("WARNING: populate_menubar failed")
                show_exception("WARNING: populate_menubar failed\n\n" + traceback.format_exc())
            redraw_menubar()

            @player.event_callback('file-loaded')
            def file_loaded_2(event): # pylint: disable=unused-argument, unused-variable
                file_loaded_callback()

            @player.event_callback('end_file')
            def ready_handler_2(event): # pylint: disable=unused-argument, unused-variable
                if event['event']['error'] != 0:
                    end_file_callback()

            @player.on_key_press('MBTN_RIGHT')
            def my_mouse_right(): # pylint: disable=unused-variable
                my_mouse_right_callback()

            @player.on_key_press('MBTN_LEFT')
            def my_mouse_left(): # pylint: disable=unused-variable
                my_mouse_left_callback()

            try:
                @player.on_key_press('MOUSE_MOVE')
                def mouse_move_event(): # pylint: disable=unused-variable
                    mouse_move_event_callback()
            except: # pylint: disable=bare-except
                print_with_time("Failed to set up mouse move callbacks")

            @player.on_key_press('MBTN_LEFT_DBL')
            def my_leftdbl_binding(): # pylint: disable=unused-variable
                mpv_fullscreen()

            @player.on_key_press('MBTN_FORWARD')
            def my_forward_binding(): # pylint: disable=unused-variable
                next_channel()

            @player.on_key_press('MBTN_BACK')
            def my_back_binding(): # pylint: disable=unused-variable
                prev_channel()

            @player.on_key_press('WHEEL_UP')
            def my_up_binding(): # pylint: disable=unused-variable
                my_up_binding_execute()

            @player.on_key_press('WHEEL_DOWN')
            def my_down_binding(): # pylint: disable=unused-variable
                my_down_binding_execute()

            init_menubar_player(
                player,
                mpv_play,
                mpv_stop,
                prev_channel,
                next_channel,
                mpv_fullscreen,
                showhideeverything,
                main_channel_settings,
                show_app_log,
                show_mpv_log,
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
                    QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'circle.png'))).pixmap(8, 8)
                ),
                check_for_updates_0,
                my_up_binding_execute,
                my_down_binding_execute,
                show_m3u_editor,
                show_playlists,
                show_sort,
                show_exception,
                get_curwindow_pos,
                force_update_epg,
                get_keybind,
                show_tvguide_2
            )

            if settings["remembervol"] and os.path.isfile(str(Path(LOCAL_DIR, 'volume.json'))):
                print_with_time("Set volume to {}".format(vol_remembered))
                label7.setValue(vol_remembered)
                mpv_volume_set()
            else:
                label7.setValue(100)
                mpv_volume_set()

        def move_label(label, x, y):
            label.move(x, y)

        def set_label_width(label, width):
            if width > 0:
                label.setFixedWidth(width)

        def get_global_cursor_position():
            return QtGui.QCursor.pos()

        class MainWindow(QtWidgets.QMainWindow): # pylint: disable=too-many-instance-attributes
            oldpos = None
            oldpos1 = None
            def __init__(self, parent=None):
                super().__init__(parent)
                # Shut up pylint (attribute-defined-outside-init)
                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.container = None
                self.listWidget = None
                self.latestWidth = 0
                self.latestHeight = 0
                self.createMenuBar_mw()
                #
                # == mpv init ==
                #
                self.container = QtWidgets.QWidget(self)
                self.setCentralWidget(self.container)
                self.container.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)
                self.container.setAttribute(QtCore.Qt.WA_NativeWindow)
                self.container.setFocus()
                self.container.setStyleSheet('''
                    background-color: #C0C6CA;
                ''')
            def mousePressEvent(self, s):
                if settings["movedragging"]:
                    self.oldpos = globalPos(s)
            def mouseMoveEvent(self, s):
                if settings["movedragging"]:
                    try:
                        f = QtCore.QPoint(globalPos(s) - self.oldpos)
                        self.move(getX(self) + getX(f), getY(self) + getY(f))
                        self.oldpos = globalPos(s)
                    except: # pylint: disable=bare-except
                        pass
            def updateWindowSize(self):
                if self.width() != self.latestWidth or self.height() != self.latestHeight:
                    self.latestWidth = self.width()
                    self.latestHeight = self.height()
            def update(self): # pylint: disable=too-many-branches
                global l1, tvguide_lbl, fullscreen

                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.updateWindowSize()
                if settings['panelposition'] == 0:
                    move_label(tvguide_lbl, 2, tvguide_lbl_offset)
                else:
                    move_label(tvguide_lbl, win.width() - tvguide_lbl.width(), tvguide_lbl_offset)
                if not fullscreen:
                    if not dockWidget2.isVisible():
                        if settings["playlistsep"]:
                            set_label_width(l1, self.windowWidth)
                            move_label(
                                l1,
                                int(((self.windowWidth - l1.width()) / 2)),
                                int(((self.windowHeight - l1.height()) - 20))
                            )
                            h = 0
                            h2 = 10
                        else:
                            set_label_width(l1, self.windowWidth - dockWidget.width() + 58)
                            move_label(
                                l1,
                                int(
                                    ((self.windowWidth - l1.width()) / 2) - \
                                    (dockWidget.width() / 1.7)
                                ),
                                int(((self.windowHeight - l1.height()) - 20))
                            )
                            h = 0
                            h2 = 10
                    else:
                        set_label_width(l1, self.windowWidth - dockWidget.width() + 58)
                        move_label(
                            l1,
                            int(((self.windowWidth - l1.width()) / 2) - (dockWidget.width() / 1.7)),
                            int(((self.windowHeight - l1.height()) - dockWidget2.height() - 10))
                        )
                        h = dockWidget2.height()
                        h2 = 20
                else:
                    set_label_width(l1, self.windowWidth)
                    move_label(
                        l1,
                        int(((self.windowWidth - l1.width()) / 2)),
                        int(((self.windowHeight - l1.height()) - 20))
                    )
                    h = 0
                    h2 = 10
                if dockWidget.isVisible():
                    if settings['panelposition'] == 0:
                        move_label(lbl2, 0, lbl2_offset)
                    else:
                        move_label(lbl2, tvguide_lbl.width() + lbl2.width(), lbl2_offset)
                else:
                    move_label(lbl2, 0, lbl2_offset)
                if l1.isVisible():
                    l1_h = l1.height()
                else:
                    l1_h = 15
                tvguide_lbl.setFixedHeight(((self.windowHeight - l1_h - h) - 40 - l1_h + h2))
            def moveEvent(self, event):
                try:
                    comm_instance.winPosition2 = {
                        "x": win.pos().x(),
                        "y": win.pos().y()
                    }
                except: # pylint: disable=bare-except
                    pass
                QtWidgets.QMainWindow.moveEvent(self, event)
            def resizeEvent(self, event):
                try:
                    self.update()
                except: # pylint: disable=bare-except
                    pass
                QtWidgets.QMainWindow.resizeEvent(self, event)
            def closeEvent(self, event1): # pylint: disable=unused-argument, no-self-use
                if streaminfo_win.isVisible():
                    streaminfo_win.hide()
                if sepplaylist_win.isVisible():
                    sepplaylist_win.hide()
                if applog_win.isVisible():
                    applog_win.hide()
                if mpvlog_win.isVisible():
                    mpvlog_win.hide()
            def createMenuBar_mw(self):
                self.menu_bar_qt = self.menuBar()
                init_astroncia_menubar(self, app, self.menu_bar_qt)

        win = MainWindow()
        win.setWindowTitle(MAIN_WINDOW_TITLE)
        win.setWindowIcon(main_icon)
        if os.path.isfile(str(Path(LOCAL_DIR, 'windowsize.json'))):
            try:
                ws_file_1 = open(str(Path(LOCAL_DIR, 'windowsize.json')), 'r', encoding="utf8")
                ws_file_1_out = json.loads(ws_file_1.read())
                ws_file_1.close()
                win.resize(ws_file_1_out['w'], ws_file_1_out['h'])
            except: # pylint: disable=bare-except
                win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])
        else:
            win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])

        qr = win.frameGeometry()
        qr.moveCenter(
            QtGui.QScreen.availableGeometry(QtWidgets.QApplication.primaryScreen()).center()
        )
        win.move(qr.topLeft())

        def get_curwindow_pos():
            try:
                win_geometry = win.screen().availableGeometry()
            except: # pylint: disable=bare-except
                win_geometry = QtWidgets.QDesktopWidget().screenGeometry(win)
            win_width = win_geometry.width()
            win_height = win_geometry.height()
            print_with_time("Screen size: {}x{}".format(win_width, win_height))
            return (win_width, win_height,)

        def get_curwindow_pos_actual():
            try:
                win_geometry_1 = win.screen().availableGeometry()
            except: # pylint: disable=bare-except
                win_geometry_1 = QtWidgets.QDesktopWidget().screenGeometry(win)
            return win_geometry_1

        chan = QtWidgets.QLabel(_('nochannelselected'))
        chan.setAlignment(QtCore.Qt.AlignCenter)
        chan.setStyleSheet('color: green')
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(11)
        myFont4.setBold(True)
        chan.setFont(myFont4)
        chan.resize(200, 30)

        def centerwidget(wdg3, offset1=0):
            fg1 = win.frameGeometry()
            xg1 = (fg1.width() - wdg3.width()) / 2
            yg1 = (fg1.height() - wdg3.height()) / 2
            wdg3.move(int(xg1), int(yg1) + int(offset1))

        loading1 = QtWidgets.QLabel(win)
        loading_movie = QtGui.QMovie(str(Path('astroncia', ICONS_FOLDER, 'loading.gif')))
        loading1.setMovie(loading_movie)
        loading1.setStyleSheet('background-color: white;')
        loading1.resize(32, 32)
        loading1.setAlignment(QtCore.Qt.AlignCenter)
        centerwidget(loading1)
        loading1.hide()

        loading2 = QtWidgets.QLabel(win)
        loading_movie2 = QtGui.QMovie(str(Path('astroncia', ICONS_FOLDER, 'recordwait.gif')))
        loading2.setMovie(loading_movie2)
        loading2.setToolTip(_('ffmpeg_processing'))
        loading2.resize(32, 32)
        loading2.setAlignment(QtCore.Qt.AlignCenter)
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
        lbl2.setAlignment(QtCore.Qt.AlignCenter)
        lbl2.setStyleSheet('color: #e0071a')
        lbl2.setWordWrap(True)
        lbl2.resize(200, 30)
        lbl2.move(0, lbl2_offset)
        lbl2.hide()

        playing = False
        playing_chan = ''

        def show_progress(prog):
            global playing_archive, fullscreen
            if prog and not playing_archive:
                prog_percentage = round(
                    (time.time() - prog['start']) / (prog['stop'] - prog['start']) * 100
                )
                prog_title = prog['title']
                prog_start = prog['start']
                prog_stop = prog['stop']
                prog_start_time = datetime.datetime.fromtimestamp(prog_start).strftime('%H:%M')
                prog_stop_time = datetime.datetime.fromtimestamp(prog_stop).strftime('%H:%M')
                progress.setValue(prog_percentage)
                progress.setFormat(str(prog_percentage) + '% ' + prog_title)
                progress.setAlignment(QtCore.Qt.AlignLeft)
                start_label.setText(prog_start_time)
                stop_label.setText(prog_stop_time)
                if not fullscreen:
                    progress.show()
                    start_label.show()
                    stop_label.show()
            else:
                progress.hide()
                start_label.setText('')
                start_label.hide()
                stop_label.setText('')
                stop_label.hide()

        playing_url = ''

        def setChanText(chanText):
            chTextStrip = chanText.strip()
            if chTextStrip:
                win.setWindowTitle(chTextStrip + ' - ' + MAIN_WINDOW_TITLE)
            else:
                win.setWindowTitle(MAIN_WINDOW_TITLE)
            chan.setText(chanText)

        playing_archive = False

        @async_function
        def setPlayerSettings(j): # pylint: disable=too-many-branches
            global playing_chan
            try:
                print_with_time("setPlayerSettings waiting for channel load...")
                try:
                    player.wait_until_playing()
                except: # pylint: disable=bare-except
                    pass
                if j == playing_chan:
                    print_with_time("setPlayerSettings '{}'".format(j))
                    if j in channel_sets:
                        d = channel_sets[j]
                        player.deinterlace = d['deinterlace']
                        if not 'useragent' in d:
                            d['useragent'] = settings['useragent']
                        try:
                            d['useragent'] = uas.index(d['useragent'])
                        except: # pylint: disable=bare-except
                            pass
                        if 'contrast' in d:
                            player.contrast = d['contrast']
                        else:
                            player.contrast = 0
                        if 'brightness' in d:
                            player.brightness = d['brightness']
                        else:
                            player.brightness = 0
                        if 'hue' in d:
                            player.hue = d['hue']
                        else:
                            player.hue = 0
                        if 'saturation' in d:
                            player.saturation = d['saturation']
                        else:
                            player.saturation = 0
                        if 'gamma' in d:
                            player.gamma = d['gamma']
                        else:
                            player.gamma = 0
                        if 'videoaspect' in d:
                            setVideoAspect(
                                videoaspect_vars[list(videoaspect_vars)[d['videoaspect']]]
                            )
                        else:
                            setVideoAspect(
                                videoaspect_vars[
                                    videoaspect_def_choose.itemText(settings['videoaspect'])
                                ]
                            )
                        if 'zoom' in d:
                            setZoom(zoom_vars[list(zoom_vars)[d['zoom']]])
                        else:
                            setZoom(zoom_vars[zoom_def_choose.itemText(settings['zoom'])])
                        if 'panscan' in d:
                            setPanscan(d['panscan'])
                        else:
                            setPanscan(settings['panscan'])
                    else:
                        player.deinterlace = settings['deinterlace']
                        setVideoAspect(
                            videoaspect_vars[
                                videoaspect_def_choose.itemText(settings['videoaspect'])
                            ]
                        )
                        setZoom(zoom_vars[zoom_def_choose.itemText(settings['zoom'])])
                        setPanscan(settings['panscan'])
                        player.gamma = 0
                        player.saturation = 0
                        player.hue = 0
                        player.brightness = 0
                        player.contrast = 0
                    # Print settings
                    if player.deinterlace:
                        print_with_time("Deinterlace: enabled")
                    else:
                        print_with_time("Deinterlace: disabled")
                    print_with_time("Contrast: {}".format(player.contrast))
                    print_with_time("Brightness: {}".format(player.brightness))
                    print_with_time("Hue: {}".format(player.hue))
                    print_with_time("Saturation: {}".format(player.saturation))
                    print_with_time("Gamma: {}".format(player.gamma))
                    print_with_time("Video aspect: {}".format(getVideoAspect()))
                    print_with_time("Zoom: {}".format(player.video_zoom))
                    print_with_time("Panscan: {}".format(player.panscan))
            except: # pylint: disable=bare-except
                pass

        def itemClicked_event(item, custom_url="", archived=False): # pylint: disable=too-many-branches
            global playing, playing_chan, item_selected, playing_url, playing_archive
            #player.command('stop')
            #player.wait_for_playback()
            playing_archive = archived
            try:
                j = item.data(QtCore.Qt.UserRole)
            except: # pylint: disable=bare-except
                j = item
            playing_chan = j
            item_selected = j
            play_url = array[j]['url']
            MAX_CHAN_SIZE = 35
            channel_name = j
            if len(channel_name) > MAX_CHAN_SIZE:
                channel_name = channel_name[:MAX_CHAN_SIZE - 3] + '...'
            setChanText('  ' + channel_name)
            current_prog = None
            jlower = j.lower()
            try:
                jlower = prog_match_arr[jlower]
            except: # pylint: disable=bare-except
                pass
            if settings['epg'] and jlower in programmes:
                for pr in programmes[jlower]:
                    if time.time() > pr['start'] and time.time() < pr['stop']:
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
            if j in channel_sets:
                ua_choose = channel_sets[j]['useragent']
            if not custom_url:
                doPlay(play_url, ua_choose, j)
            else:
                doPlay(custom_url, ua_choose, j)
            btn_update.click()

        item_selected = ''

        def itemSelected_event(item):
            global item_selected
            try:
                n_1 = item.data(QtCore.Qt.UserRole)
                item_selected = n_1
                update_tvguide(n_1)
            except: # pylint: disable=bare-except
                pass

        def mpv_play():
            global autoclosemenu_time
            autoclosemenu_time = -1
            if player.pause:
                label3.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'pause.png'))))
                label3.setToolTip(_('pause'))
                mpv_override_pause(False)
            else:
                label3.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'play.png'))))
                label3.setToolTip(_('play'))
                mpv_override_pause(True)

        def mpv_stop():
            global playing, playing_chan, playing_url
            playing_chan = ''
            playing_url = ''
            hideLoading()
            setChanText('')
            playing = False
            stopPlayer()
            player.loop = True
            player.deinterlace = False
            mpv_override_play(str(Path('astroncia', ICONS_FOLDER, 'main.png')))
            chan.setText(_('nochannelselected'))
            progress.hide()
            start_label.hide()
            stop_label.hide()
            start_label.setText('')
            stop_label.setText('')
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
            win.update()
            btn_update.click()
            redraw_menubar()

        def esc_handler():
            global fullscreen
            if fullscreen:
                mpv_fullscreen()

        currentWidthHeight = [win.width(), win.height()]
        currentMaximized = win.isMaximized()
        currentDockWidgetPos = -1

        isPlaylistVisible = False

        def dockWidget_out_clicked(): # pylint: disable=too-many-branches
            global fullscreen, l1, time_stop, currentWidthHeight, currentMaximized, \
                currentDockWidgetPos, isPlaylistVisible
            if not fullscreen:
                # Entering fullscreen
                if settings["playlistsep"]:
                    isPlaylistVisible = sepplaylist_win.isVisible()
                else:
                    isPlaylistVisible = dockWidget.isVisible()
                del_sep_flag()
                if settings["playlistsep"]:
                    win.show()
                    win.raise_()
                    win.setFocus(QtCore.Qt.PopupFocusReason)
                    win.activateWindow()
                setShortcutState(True)
                del_sep_flag()
                comm_instance.winPosition = win.geometry()
                currentWidthHeight = [win.width(), win.height()]
                currentMaximized = win.isMaximized()
                channelfilter.usePopup = False
                fullscreen = True
                win.menu_bar_qt.hide()
                if settings['playlistsep']:
                    currentDockWidgetPos = sepplaylist_win.pos()
                    print_with_time("Saved separate playlist position - QPoint({}, {})".format(
                        currentDockWidgetPos.x(),
                        currentDockWidgetPos.y()
                    ))
                    sepplaylist_win.hide()
                #l1.show()
                #l1.setText2("{} F".format(_('exitfullscreen')))
                #time_stop = time.time() + 3
                dockWidget.hide()
                chan.hide()
                #progress.hide()
                #start_label.hide()
                #stop_label.hide()
                label11.hide()
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
                del_sep_flag()
                win.showFullScreen()
                if settings['panelposition'] == 1:
                    tvguide_close_lbl.move(
                        get_curwindow_pos()[0] - tvguide_lbl.width() - 40,
                        tvguide_lbl_offset
                    )
                centerwidget(loading1)
                centerwidget(loading2, 50)
            else:
                # Leaving fullscreen
                setShortcutState(False)
                if l1.isVisible() and l1.text().startswith(_('volume')):
                    l1.hide()
                win.menu_bar_qt.show()
                hide_playlist()
                hide_controlpanel()
                dockWidget.setWindowOpacity(1)
                dockWidget.hide()
                dockWidget2.setWindowOpacity(1)
                dockWidget2.hide()
                fullscreen = False
                if l1.text().endswith('{} F'.format(_('exitfullscreen'))):
                    l1.setText2('')
                    if not gl_is_static:
                        l1.hide()
                        win.update()
                if not player.pause and playing and start_label.text():
                    progress.show()
                    start_label.show()
                    stop_label.show()
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
                label11.show()
                label12.show()
                for lbl3 in hlayout2_btns:
                    if lbl3 not in show_lbls_fullscreen:
                        lbl3.show()
                dockWidget2.show()
                if not settings["playlistsep"]:
                    dockWidget.show()
                chan.show()
                win.update()
                if not currentMaximized:
                    win.showNormal()
                else:
                    win.showMaximized()
                win.resize(currentWidthHeight[0], currentWidthHeight[1])
                if comm_instance.winPosition:
                    win.move(comm_instance.winPosition.x(), comm_instance.winPosition.y())
                else:
                    moveWindowToCenter(win, True)
                if settings['playlistsep'] and currentDockWidgetPos != -1:
                    comm_instance.moveSeparatePlaylist.emit(currentDockWidgetPos)
                if not isPlaylistVisible:
                    key_t()
                if settings['panelposition'] == 1:
                    tvguide_close_lbl.move(
                        win.width() - tvguide_lbl.width() - 40,
                        tvguide_lbl_offset
                    )
                centerwidget(loading1)
                centerwidget(loading2, 50)

        dockWidget_out = QtWidgets.QPushButton()
        dockWidget_out.clicked.connect(dockWidget_out_clicked)

        @idle_function
        def mpv_fullscreen(arg11=None): # pylint: disable=unused-argument
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
                    l1.setText2("{}: {}%".format(_('volume'), int(v1)))

        def mpv_mute():
            global old_value, time_stop, l1
            time_stop = time.time() + 3
            if player.mute:
                if old_value > 50:
                    label6.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'volume.png'))))
                else:
                    label6.setIcon(
                        QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'volume-low.png')))
                    )
                mpv_override_mute(False)
                label7.setValue(old_value)
                show_volume(old_value)
            else:
                label6.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'mute.png'))))
                mpv_override_mute(True)
                old_value = label7.value()
                label7.setValue(0)
                show_volume(_('volumeoff'))

        def mpv_volume_set():
            global time_stop, l1, fullscreen
            time_stop = time.time() + 3
            vol = int(label7.value())
            try:
                if vol == 0:
                    show_volume(_('volumeoff'))
                else:
                    show_volume(vol)
            except NameError:
                pass
            mpv_override_volume(vol)
            if vol == 0:
                mpv_override_mute(True)
                label6.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'mute.png'))))
            else:
                mpv_override_mute(False)
                if vol > 50:
                    label6.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'volume.png'))))
                else:
                    label6.setIcon(
                        QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'volume-low.png')))
                    )

        dockWidget = QtWidgets.QDockWidget(win)
        if settings["playlistsep"]:
            dockWidget.hide()
        win.listWidget = QtWidgets.QListWidget()

        class ClickableLabel(QtWidgets.QLabel): # pylint: disable=too-few-public-methods
            def __init__(self, whenClicked, parent=None): # pylint: disable=unused-argument
                QtWidgets.QLabel.__init__(self, win)
                self._whenClicked = whenClicked

            def mouseReleaseEvent(self, event):
                self._whenClicked(event)

        def tvguide_close_lbl_func(arg): # pylint: disable=unused-argument
            hide_tvguide()

        tvguide_lbl = ScrollLabel(win)
        tvguide_lbl.move(0, tvguide_lbl_offset)
        tvguide_lbl.setFixedWidth(TVGUIDE_WIDTH)
        tvguide_lbl.hide()

        tvguide_close_lbl = ClickableLabel(tvguide_close_lbl_func)
        tvguide_close_lbl.setPixmap(
            QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'close.png'))).pixmap(32, 32)
        )
        tvguide_close_lbl.setStyleSheet(
            "background-color: {};".format("black" if settings["themecompat"] else "white")
        )
        tvguide_close_lbl.resize(32, 32)
        if settings['panelposition'] == 0:
            tvguide_close_lbl.move(tvguide_lbl.width() + 5, tvguide_lbl_offset)
        else:
            tvguide_close_lbl.move(win.width() - tvguide_lbl.width() - 40, tvguide_lbl_offset)
            lbl2.move(tvguide_lbl.width() + lbl2.width(), lbl2_offset)
        tvguide_close_lbl.hide()

        class cwdg(QtWidgets.QWidget): # pylint: disable=too-many-instance-attributes
            def __init__(self, parent=None):
                super(cwdg, self).__init__(parent) # pylint: disable=super-with-arguments
                self.tooltip = ""
                self.textQVBoxLayout = QtWidgets.QVBoxLayout()      # QtWidgets
                self.textUpQLabel = QtWidgets.QLabel()         # QtWidgets
                myFont = QtGui.QFont()
                myFont.setBold(True)
                self.textUpQLabel.setFont(myFont)
                self.textDownQLabel = QtWidgets.QLabel()         # QtWidgets
                self.textQVBoxLayout.addWidget(self.textUpQLabel)
                self.textQVBoxLayout.addWidget(self.textDownQLabel)
                self.textQVBoxLayout.setSpacing(5)
                self.allQHBoxLayout = QtWidgets.QGridLayout()      # QtWidgets
                self.iconQLabel = QtWidgets.QLabel()         # QtWidgets
                self.progressLabel = QtWidgets.QLabel()
                self.progressBar = QtWidgets.QProgressBar()
                self.progressBar.setFixedHeight(15)
                self.endLabel = QtWidgets.QLabel()
                self.op = QtWidgets.QGraphicsOpacityEffect()
                self.op.setOpacity(100)
                self.allQHBoxLayout.addWidget(self.iconQLabel, 0, 0)
                self.allQHBoxLayout.addLayout(self.textQVBoxLayout, 0, 1)
                self.allQHBoxLayout.addWidget(self.progressLabel, 3, 0)
                self.allQHBoxLayout.addWidget(self.progressBar, 3, 1)
                self.allQHBoxLayout.addWidget(self.endLabel, 3, 2)
                self.allQHBoxLayout.setSpacing(10)
                self.setLayout(self.allQHBoxLayout)
                # setStyleSheet
                #self.textUpQLabel.setStyleSheet('''
                #    color: rgb(0, 0, 255);
                #''')
                #self.textDownQLabel.setStyleSheet('''
                #    color: rgb(255, 0, 0);
                #''')
                self.progressBar.setStyleSheet('''
                  background-color: #C0C6CA;
                  border: 0px;
                  padding: 0px;
                  height: 5px;
                ''')
                self.setStyleSheet('''
                  QProgressBar::chunk {
                    background: #7D94B0;
                    width:5px
                  }
                ''')

            #def enterEvent(self, event):
            #    print_with_time("hovered", self.tooltip)
            #    QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self.tooltip, win.container)

            #def leaveEvent(self, event):
            #    print_with_time("left")

            def setTextUp(self, text):
                self.textUpQLabel.setText(text)

            def setTextDown(self, text, tooltip):
                progTooltip = tooltip
                self.tooltip = progTooltip
                self.setToolTip(progTooltip)
                self.textDownQLabel.setText(text)

            def setTextProgress(self, text):
                self.progressLabel.setText(text)

            def setTextEnd(self, text):
                self.endLabel.setText(text)

            def setIcon(self, image):
                self.iconQLabel.setPixmap(image.pixmap(QtCore.QSize(32, 32)))

            def setProgress(self, progress_val):
                self.op.setOpacity(100)
                self.progressBar.setGraphicsEffect(self.op)
                self.progressBar.setFormat('')
                self.progressBar.setValue(progress_val)

            def hideProgress(self):
                self.op.setOpacity(0)
                self.progressBar.setGraphicsEffect(self.op)

        class cwdg_simple(QtWidgets.QWidget): # pylint: disable=too-many-instance-attributes
            def __init__(self, parent=None):
                super(cwdg_simple, self).__init__(parent) # pylint: disable=super-with-arguments
                self.textQHBoxLayout = QtWidgets.QHBoxLayout()      # QtWidgets
                self.textUpQLabel = QtWidgets.QLabel()         # QtWidgets
                myFont = QtGui.QFont()
                myFont.setBold(True)
                self.textUpQLabel.setFont(myFont)
                self.iconQLabel = QtWidgets.QLabel()         # QtWidgets
                if settings['gui'] == 1:
                    self.textQHBoxLayout.addWidget(self.iconQLabel)
                self.textQHBoxLayout.addWidget(self.textUpQLabel)
                self.textQHBoxLayout.addStretch()
                self.textQHBoxLayout.setSpacing(15)
                self.setLayout(self.textQHBoxLayout)

            def setTextUp(self, text):
                self.textUpQLabel.setText(text)

            def setTextDown(self, text, tooltip):
                pass

            def setTextProgress(self, text):
                pass

            def setTextEnd(self, text):
                pass

            def setIcon(self, image):
                self.iconQLabel.setPixmap(image.pixmap(QtCore.QSize(32, 20)))

            def setProgress(self, progress_val):
                pass

            def hideProgress(self):
                pass

        current_group = _('allchannels')

        channel_sort = {}
        if os.path.isfile(str(Path(LOCAL_DIR, 'sort.json'))):
            file3 = open(str(Path(LOCAL_DIR, 'sort.json')), 'r', encoding="utf8")
            channel_sort = json.loads(file3.read())
            file3.close()

        def sort_custom(sub):
            try:
                return channel_sort.index(sub)
            except: # pylint: disable=bare-except
                return 0

        def doSort(arr0):
            if settings['sort'] == 0:
                return arr0
            if settings['sort'] == 1:
                return sorted(arr0)
            if settings['sort'] == 2:
                return sorted(arr0, reverse=True)
            if settings['sort'] == 3:
                try:
                    return sorted(arr0, reverse=False, key=sort_custom)
                except: # pylint: disable=bare-except
                    return arr0
            return arr0

        class channel_icons_data: # pylint: disable=too-few-public-methods
            pass

        channel_icons_data.manager_1 = None

        class channel_icons_data_epg: # pylint: disable=too-few-public-methods
            pass

        channel_icons_data_epg.manager_1 = None

        class Pickable_QIcon(QtGui.QIcon):
            def __reduce__(self):
                return type(self), (), self.__getstate__()

            def __getstate__(self):
                ba = QtCore.QByteArray()
                stream = QtCore.QDataStream(ba, QtCore.QIODevice.WriteOnly)
                stream << self # pylint: disable=pointless-statement
                return ba

            def __setstate__(self, ba):
                stream = QtCore.QDataStream(ba, QtCore.QIODevice.ReadOnly)
                stream >> self # pylint: disable=pointless-statement

        def fetch_remote_channel_icon(chan_name, logo_url, return_dict_2):
            base64_enc = base64.b64encode(
                bytes(chan_name + ":::" + logo_url, 'utf-8')
            ).decode('utf-8')
            sha512_hash = str(hashlib.sha512(bytes(base64_enc, 'utf-8')).hexdigest()) + ".cacheimg"
            cache_file = str(Path(LOCAL_DIR, 'channel_icons_cache', sha512_hash))
            if os.path.isfile(cache_file):
                cache_file_2 = open(cache_file, 'rb')
                cache_file_2_read = cache_file_2.read()
                cache_file_2.close()
                req_data = cache_file_2_read
            else:
                try:
                    req_data = requests.get(
                        logo_url,
                        headers={'User-Agent': uas[settings['useragent']]},
                        timeout=(3, 3),
                        stream=True
                    ).content
                    cache_file_2 = open(cache_file, 'wb')
                    cache_file_2.write(req_data)
                    cache_file_2.close()
                except: # pylint: disable=bare-except
                    req_data = None
            try:
                qp_1 = QtGui.QPixmap()
                qp_1.loadFromData(req_data)
                qp_1 = qp_1.scaled(64, 64, QtCore.Qt.KeepAspectRatio)
                fetched_icon = Pickable_QIcon(qp_1)
                return_dict_2[chan_name] = [fetched_icon]
            except: # pylint: disable=bare-except
                return_dict_2[chan_name] = None

        channel_icons_data.load_completed = False
        channel_icons_data.do_next_update = False

        channel_icons_data_epg.load_completed = False
        channel_icons_data_epg.do_next_update = False

        def channel_icons_thread():
            try:
                if channel_icons_data.do_next_update:
                    channel_icons_data.do_next_update = False
                    btn_update.click()
                    print_with_time("Channel icons updated")
                try:
                    if len(channel_icons_data.return_dict) != channel_icons_data.total:
                        print_with_time("Channel icons loaded: {}/{}".format(
                            len(channel_icons_data.return_dict), channel_icons_data.total
                        ))
                        btn_update.click()
                    else:
                        if not channel_icons_data.load_completed:
                            channel_icons_data.load_completed = True
                            channel_icons_data.do_next_update = True
                            print_with_time("Channel icons loaded ({}/{}), took {} seconds".format(
                                len(channel_icons_data.return_dict),
                                channel_icons_data.total,
                                time.time() - channel_icons_data.load_time
                            ))
                except: # pylint: disable=bare-except
                    pass
            except: # pylint: disable=bare-except
                pass

        def channel_icons_thread_epg():
            try:
                if channel_icons_data_epg.do_next_update:
                    channel_icons_data_epg.do_next_update = False
                    btn_update.click()
                    print_with_time("Channel icons (EPG) updated")
                try:
                    if len(channel_icons_data_epg.return_dict) != channel_icons_data_epg.total:
                        print_with_time("Channel icons (EPG) loaded: {}/{}".format(
                            len(channel_icons_data_epg.return_dict), channel_icons_data_epg.total
                        ))
                        btn_update.click()
                    else:
                        if not channel_icons_data_epg.load_completed:
                            channel_icons_data_epg.load_completed = True
                            channel_icons_data_epg.do_next_update = True
                            print_with_time(
                                "Channel icons (EPG) loaded ({}/{}), took {} seconds".format(
                                    len(channel_icons_data_epg.return_dict),
                                    channel_icons_data_epg.total,
                                    time.time() - channel_icons_data_epg.load_time
                                )
                            )
                except: # pylint: disable=bare-except
                    pass
            except: # pylint: disable=bare-except
                pass

        epg_icons_found = False
        epg_icons_aldisabled = False

        def epg_channel_icons_thread():
            global epg_icons, epg_icons_found, epg_icons_aldisabled
            if settings['chaniconsfromepg']:
                if not epg_icons_found:
                    if epg_icons:
                        epg_icons_found = True
                        print_with_time("EPG icons ready")
            else:
                if not epg_icons_aldisabled:
                    epg_icons_aldisabled = True
                    print_with_time("EPG icons disabled")

        @async_function
        def update_channel_icons():
            while not win.isVisible():
                time.sleep(1)
            print_with_time("Loading channel icons...")
            if not os.path.isdir(str(Path(LOCAL_DIR, 'channel_icons_cache'))):
                os.mkdir(str(Path(LOCAL_DIR, 'channel_icons_cache')))
            channel_icons_data.load_time = time.time()
            channel_icons_data.total = 0

            for chan_4 in array:
                chan_4_logo = array[chan_4]['tvg-logo']
                if chan_4_logo:
                    channel_icons_data.total += 1

            for chan_4 in array:
                chan_4_logo = array[chan_4]['tvg-logo']
                if chan_4_logo:
                    #fetching_str = "Fetching channel icon from URL '{}' for channel '{}'"
                    #print_with_time(fetching_str.format(chan_4_logo, chan_4))
                    fetch_remote_channel_icon(
                        chan_4, chan_4_logo, channel_icons_data.return_dict
                    )

        @async_function
        def update_channel_icons_epg():
            global epg_icons_found
            while not win.isVisible():
                time.sleep(1)
            while not epg_icons_found:
                time.sleep(1)
            print_with_time("Loading channel icons (EPG)...")
            if not os.path.isdir(str(Path(LOCAL_DIR, 'channel_icons_cache'))):
                os.mkdir(str(Path(LOCAL_DIR, 'channel_icons_cache')))
            channel_icons_data_epg.load_time = time.time()
            channel_icons_data_epg.total = 0

            for chan_5 in epg_icons:
                chan_5_logo = epg_icons[chan_5]
                if chan_5_logo:
                    channel_icons_data_epg.total += 1

            for chan_5 in epg_icons:
                chan_5_logo = epg_icons[chan_5]
                if chan_5_logo:
                    #fetching_str_2 = "Fetching channel icon from URL '{}' for channel '{}'"
                    #print_with_time(fetching_str_2.format(chan_5_logo, chan_5))
                    fetch_remote_channel_icon(
                        chan_5, chan_5_logo, channel_icons_data_epg.return_dict
                    )

        array_copy = copy.deepcopy(array)
        prog_match_arr = {}

        first_gen_chans = True
        def gen_chans(): # pylint: disable=too-many-locals, too-many-branches
            global ICONS_CACHE, playing_chan, current_group, \
            array, page_box, channelfilter, first_gen_chans, prog_match_arr
            if first_gen_chans:
                first_gen_chans = False
                channel_icons_data.manager_1 = Manager()
                channel_icons_data.return_dict = channel_icons_data.manager_1.dict()
                channel_icons_data_epg.manager_1 = Manager()
                channel_icons_data_epg.return_dict = channel_icons_data_epg.manager_1.dict()
                if os.name == 'nt':
                    channel_icons_data.load_completed = True
                    channel_icons_data_epg.load_completed = True
                else:
                    update_channel_icons()
                    update_channel_icons_epg()
            try:
                idx = (page_box.value() - 1) * settings["channelsonpage"]
            except: # pylint: disable=bare-except
                idx = 0
            try:
                filter_txt = channelfilter.text()
            except: # pylint: disable=bare-except
                filter_txt = ""

            # Group and favourites filter
            array_filtered = {}
            for j1 in array:
                group1 = array[j1]['tvg-group']
                if current_group != _('allchannels'):
                    if current_group == _('favourite'):
                        if not j1 in favourite_sets:
                            continue
                    else:
                        if group1 != current_group:
                            continue
                array_filtered[j1] = array[j1]

            ch_array = {x13: array_filtered[x13] for x13 in array_filtered if \
                unidecode(filter_txt).lower().strip() in unidecode(x13).lower().strip()}
            ch_array = list(ch_array.values())[idx:idx+settings["channelsonpage"]]
            ch_array = dict([(x14['title'], x14) for x14 in ch_array]) # pylint: disable=consider-using-dict-comprehension
            try:
                if filter_txt:
                    page_box.setMaximum(round(len(ch_array) / settings["channelsonpage"]) + 1)
                    of_lbl.setText('{} {}'.format(_('of'), \
                        round(len(ch_array) / settings["channelsonpage"]) + 1))
                else:
                    page_box.setMaximum(round(len(array_filtered) / settings["channelsonpage"]) + 1)
                    of_lbl.setText('{} {}'.format(_('of'), \
                        round(len(array_filtered) / settings["channelsonpage"]) + 1))
            except: # pylint: disable=bare-except
                pass
            res = {}
            l = -1
            k = 0
            for i in doSort(ch_array):
                l += 1
                k += 1
                prog = ''
                prog_desc = ''
                prog_search = i.lower()
                if array_filtered[i]['tvg-ID']:
                    if str(array_filtered[i]['tvg-ID']) in prog_ids:
                        prog_search_lst = prog_ids[str(array_filtered[i]['tvg-ID'])]
                        if prog_search_lst:
                            prog_search = prog_search_lst[0].lower()

                # EPG name override for channel settings
                orig_tvg_name = array_copy[i]['tvg-name']
                if i in channel_sets:
                    if 'epgname' in channel_sets[i]:
                        if channel_sets[i]['epgname']:
                            array_filtered[i]['tvg-name'] = channel_sets[i]['epgname']
                        else:
                            array_filtered[i]['tvg-name'] = orig_tvg_name

                if array_filtered[i]['tvg-name']:
                    if str(array_filtered[i]['tvg-name']).lower() in programmes:
                        prog_search = str(array_filtered[i]['tvg-name']).lower()
                prog_match_arr[i.lower()] = prog_search
                if prog_search in programmes:
                    current_prog = {
                        'start': 0,
                        'stop': 0,
                        'title': '',
                        'desc': ''
                    }
                    for pr in programmes[prog_search]:
                        if time.time() > pr['start'] and time.time() < pr['stop']:
                            current_prog = pr
                            break
                    if current_prog['start'] != 0:
                        start_time = datetime.datetime.fromtimestamp(
                            current_prog['start']
                        ).strftime('%H:%M')
                        stop_time = datetime.datetime.fromtimestamp(
                            current_prog['stop']
                        ).strftime('%H:%M')
                        t_t = time.time()
                        percentage = round(
                            (t_t - current_prog['start']) / (
                                current_prog['stop'] - current_prog['start']
                            ) * 100
                        )
                        if settings['hideepgpercentage']:
                            prog = current_prog['title']
                        else:
                            prog = str(percentage) + '% ' + current_prog['title']
                        try:
                            if current_prog['desc']:
                                prog_desc = '\n\n' + textwrap.fill(current_prog['desc'], 100)
                            else:
                                prog_desc = ''
                        except: # pylint: disable=bare-except
                            prog_desc = ''
                    else:
                        start_time = ''
                        stop_time = ''
                        t_t = time.time()
                        percentage = 0
                        prog = ''
                        prog_desc = ''
                # Create cwdg
                if settings['gui'] == 0:
                    mycwdg = cwdg()
                else:
                    mycwdg = cwdg_simple()
                MAX_SIZE_CHAN = 21
                chan_name = i
                if len(chan_name) > MAX_SIZE_CHAN:
                    chan_name = chan_name[0:MAX_SIZE_CHAN] + "..."
                unicode_play_symbol = chr(9654) + " "
                append_symbol = ""
                if playing_chan == chan_name:
                    append_symbol = unicode_play_symbol
                mycwdg.setTextUp(append_symbol + str(k) + ". " + chan_name)
                MAX_SIZE = 28
                orig_prog = prog
                if len(prog) > MAX_SIZE:
                    prog = prog[0:MAX_SIZE] + "..."
                if prog_search in programmes:
                    mycwdg.setTextDown(
                        prog,
                        (
                            "<b>{}</b>".format(i) + "<br><br>" + \
                            "<i>" + orig_prog + "</i>" + prog_desc
                        ).replace('\n', '<br>')
                    )
                    try:
                        if start_time:
                            mycwdg.setTextProgress(start_time)
                            mycwdg.setTextEnd(stop_time)
                            mycwdg.setProgress(int(percentage))
                        else:
                            mycwdg.hideProgress()
                    except: # pylint: disable=bare-except
                        print_with_time("Async EPG load problem, ignoring")
                else:
                    mycwdg.hideProgress()
                i_icon = i.lower()
                icons_l = {picon.lower(): icons[picon] for picon in icons}
                if i_icon in icons_l:
                    if not icons_l[i_icon] in ICONS_CACHE:
                        ICONS_CACHE[icons_l[i_icon]] = \
                            QtGui.QIcon(str(Path(
                                '..', '..', 'share', 'astronciaiptv',
                                'channel_icons', icons_l[i_icon]
                            )))
                    mycwdg.setIcon(ICONS_CACHE[icons_l[i_icon]])
                else:
                    mycwdg.setIcon(TV_ICON)

                # Icon from playlist
                if i in channel_icons_data.return_dict and channel_icons_data.return_dict[i]:
                    if i in ICONS_CACHE_FETCHED:
                        fetched_icon = ICONS_CACHE_FETCHED[i]
                    else:
                        fetched_icon = channel_icons_data.return_dict[i][0]
                        ICONS_CACHE_FETCHED[i] = fetched_icon
                    mycwdg.setIcon(fetched_icon)

                # Icon from EPG
                if i in channel_icons_data_epg.return_dict and \
                channel_icons_data_epg.return_dict[i]:
                    if i in ICONS_CACHE_FETCHED_EPG:
                        fetched_icon_epg = ICONS_CACHE_FETCHED_EPG[i]
                    else:
                        fetched_icon_epg = channel_icons_data_epg.return_dict[i][0]
                        ICONS_CACHE_FETCHED_EPG[i] = fetched_icon_epg
                    mycwdg.setIcon(fetched_icon_epg)

                # Create QListWidgetItem
                myQListWidgetItem = QtWidgets.QListWidgetItem()
                myQListWidgetItem.setData(QtCore.Qt.UserRole, i)
                # Set size hint
                myQListWidgetItem.setSizeHint(mycwdg.sizeHint())
                res[l] = [myQListWidgetItem, mycwdg, l, i]
            j1 = playing_chan.lower()
            try:
                j1 = prog_match_arr[j1]
            except: # pylint: disable=bare-except
                pass
            if j1:
                current_chan = None
                try:
                    cur = programmes[j1]
                    for pr in cur:
                        if time.time() > pr['start'] and time.time() < pr['stop']:
                            current_chan = pr
                            break
                except: # pylint: disable=bare-except
                    pass
                show_progress(current_chan)
            return res

        row0 = -1

        def redraw_chans():
            channels_1 = gen_chans()
            global row0
            update_tvguide()
            row0 = win.listWidget.currentRow()
            val0 = win.listWidget.verticalScrollBar().value()
            win.listWidget.clear()
            for channel_1 in channels_1.values():
                #chan_3 = channels_1[channel_1]
                chan_3 = channel_1
                #c_name = chan_3[3]
                win.listWidget.addItem(chan_3[0])
                win.listWidget.setItemWidget(chan_3[0], chan_3[1])
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
                sort_list.insertItem(curIndex-1, curItem)
                sort_list.setCurrentRow(curIndex-1)

        def sort_downbtn_clicked():
            curIndex1 = sort_list.currentRow()
            if curIndex1 != -1 and curIndex1 < sort_list.count()-1:
                curItem1 = sort_list.takeItem(curIndex1)
                sort_list.insertItem(curIndex1+1, curItem1)
                sort_list.setCurrentRow(curIndex1+1)

        sort_upbtn = QtWidgets.QPushButton()
        sort_upbtn.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'arrow-up.png'))))
        sort_upbtn.clicked.connect(sort_upbtn_clicked)
        sort_downbtn = QtWidgets.QPushButton()
        sort_downbtn.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'arrow-down.png'))))
        sort_downbtn.clicked.connect(sort_downbtn_clicked)

        sort_widget2 = QtWidgets.QWidget()
        sort_layout2 = QtWidgets.QVBoxLayout()
        sort_layout2.setAlignment(QtCore.Qt.AlignCenter)
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

        sel_item = None

        def select_context_menu():
            itemClicked_event(sel_item)

        def tvguide_context_menu():
            update_tvguide()
            tvguide_lbl.show()
            tvguide_close_lbl.show()

        def settings_context_menu(): # pylint: disable=too-many-branches
            if chan_win.isVisible():
                chan_win.close()
            title.setText(("{}: " + item_selected).format(_('channel')))
            if item_selected in channel_sets:
                deinterlace_chk.setChecked(channel_sets[item_selected]['deinterlace'])
                try:
                    useragent_choose.setCurrentIndex(channel_sets[item_selected]['useragent'])
                except: # pylint: disable=bare-except
                    useragent_choose.setCurrentIndex(settings['useragent'])
                try:
                    group_text.setText(channel_sets[item_selected]['group'])
                except: # pylint: disable=bare-except
                    group_text.setText('')
                try:
                    hidden_chk.setChecked(channel_sets[item_selected]['hidden'])
                except: # pylint: disable=bare-except
                    hidden_chk.setChecked(False)
                try:
                    contrast_choose.setValue(channel_sets[item_selected]['contrast'])
                except: # pylint: disable=bare-except
                    contrast_choose.setValue(0)
                try:
                    brightness_choose.setValue(channel_sets[item_selected]['brightness'])
                except: # pylint: disable=bare-except
                    brightness_choose.setValue(0)
                try:
                    hue_choose.setValue(channel_sets[item_selected]['hue'])
                except: # pylint: disable=bare-except
                    hue_choose.setValue(0)
                try:
                    saturation_choose.setValue(channel_sets[item_selected]['saturation'])
                except: # pylint: disable=bare-except
                    saturation_choose.setValue(0)
                try:
                    gamma_choose.setValue(channel_sets[item_selected]['gamma'])
                except: # pylint: disable=bare-except
                    gamma_choose.setValue(0)
                try:
                    videoaspect_choose.setCurrentIndex(channel_sets[item_selected]['videoaspect'])
                except: # pylint: disable=bare-except
                    videoaspect_choose.setCurrentIndex(0)
                try:
                    zoom_choose.setCurrentIndex(channel_sets[item_selected]['zoom'])
                except: # pylint: disable=bare-except
                    zoom_choose.setCurrentIndex(0)
                try:
                    panscan_choose.setValue(channel_sets[item_selected]['panscan'])
                except: # pylint: disable=bare-except
                    panscan_choose.setValue(0)
                try:
                    epgname_saved = channel_sets[item_selected]['epgname']
                    if not epgname_saved:
                        epgname_saved = _('default')
                    epgname_lbl.setText(epgname_saved)
                except: # pylint: disable=bare-except
                    epgname_lbl.setText(_('default'))
            else:
                deinterlace_chk.setChecked(settings['deinterlace'])
                hidden_chk.setChecked(False)
                contrast_choose.setValue(0)
                brightness_choose.setValue(0)
                hue_choose.setValue(0)
                saturation_choose.setValue(0)
                gamma_choose.setValue(0)
                videoaspect_choose.setCurrentIndex(0)
                zoom_choose.setCurrentIndex(0)
                panscan_choose.setValue(0)
                useragent_choose.setCurrentIndex(settings['useragent'])
                group_text.setText('')
                epgname_lbl.setText(_('default'))
            moveWindowToCenter(chan_win)
            chan_win.show()

        def tvguide_favourites_add():
            if item_selected in favourite_sets:
                favourite_sets.remove(item_selected)
            else:
                favourite_sets.append(item_selected)
            save_favourite_sets()
            btn_update.click()

        def open_external_player():
            moveWindowToCenter(ext_win)
            ext_win.show()

        def tvguide_start_record():
            url2 = array[item_selected]['url']
            if is_recording:
                start_record("", "")
            start_record(item_selected, url2)

        def tvguide_hide():
            if settings['gui'] == 0:
                tvguide_lbl.setText('')
                tvguide_lbl_2.setText('')
                tvguide_lbl.hide()
                tvguide_close_lbl.hide()
            else:
                tvguide_lbl.setText('')
                tvguide_lbl_2.setText('')
                epg_win.hide()

        def favoritesplaylistsep_add():
            ps_data = array[item_selected]
            str1 = "#EXTINF:-1"
            if ps_data['tvg-name']:
                str1 += " tvg-name=\"{}\"".format(ps_data['tvg-name'])
            if ps_data['tvg-ID']:
                str1 += " tvg-id=\"{}\"".format(ps_data['tvg-ID'])
            if ps_data['tvg-logo']:
                str1 += " tvg-logo=\"{}\"".format(ps_data['tvg-logo'])
            if ps_data['tvg-url']:
                str1 += " tvg-url=\"{}\"".format(ps_data['tvg-url'])
            else:
                str1 += " tvg-url=\"{}\"".format(settings['epg'])
            str1 += ",{}\n{}\n".format(item_selected, ps_data['url'])
            file03 = open(str(Path(LOCAL_DIR, 'playlist_separate.m3u')), 'r', encoding="utf8")
            file03_contents = file03.read()
            file03.close()
            if file03_contents == '#EXTM3U\n#EXTINF:-1,{}\nhttp://255.255.255.255\n'.format('-'):
                file04 = open(str(Path(LOCAL_DIR, 'playlist_separate.m3u')), 'w', encoding="utf8")
                file04.write('#EXTM3U\n' + str1)
                file04.close()
            else:
                if str1 in file03_contents:
                    new_data = file03_contents.replace(str1, '')
                    if new_data == '#EXTM3U\n':
                        new_data = '#EXTM3U\n#EXTINF:-1,{}\nhttp://255.255.255.255\n'.format('-')
                    file05 = open(
                        str(Path(LOCAL_DIR, 'playlist_separate.m3u')), 'w', encoding="utf8"
                    )
                    file05.write(new_data)
                    file05.close()
                else:
                    file02 = open(
                        str(Path(LOCAL_DIR, 'playlist_separate.m3u')), 'w', encoding="utf8"
                    )
                    file02.write(file03_contents + str1)
                    file02.close()

        # Fix this, make async
        #def iaepgmatch():
        #    prog_ids_1 = []
        #    for x2 in prog_ids:
        #        for x3 in prog_ids[x2]:
        #            if not x3 in prog_ids_1:
        #                prog_ids_1.append(x3)
        #    for x4_chan in [x3 for x3 in array]: # pylint: disable=unnecessary-comprehension
        #        if x4_chan.lower() not in programmes:
        #            print_with_time("Parsing channel '{}'...".format(x4_chan))
        #            matches = {}
        #            for x4 in prog_ids_1:
        #                x5 = x4.strip().lower()
        #                x5_chan = x4_chan.strip().lower()
        #                matches[(x4_chan, x4)] = damerau_levenshtein(x5_chan, x5)
        #            print_with_time(sorted(matches.items(), key=lambda x6: x6[1])[0][0][1])

        def show_context_menu(pos):
            global sel_item
            self = win.listWidget
            sel_item = self.selectedItems()[0]
            itemSelected_event(sel_item)
            menu = QtWidgets.QMenu()
            menu.addAction(_('select'), select_context_menu)
            menu.addSeparator()
            menu.addAction(_('tvguide'), tvguide_context_menu)
            menu.addAction(_('hidetvguide'), tvguide_hide)
            menu.addAction(_('favourite'), tvguide_favourites_add)
            menu.addAction(_('favoritesplaylistsep'), favoritesplaylistsep_add)
            menu.addAction(_('openexternal'), open_external_player)
            menu.addAction(_('startrecording'), tvguide_start_record)
            menu.addAction(_('channelsettings'), settings_context_menu)
            #menu.addAction(_('iaepgmatch'), iaepgmatch)
            if qt_library == 'PySide6':
                menu.exec(self.mapToGlobal(pos))
            else:
                menu.exec_(self.mapToGlobal(pos))

        win.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        win.listWidget.customContextMenuRequested.connect(show_context_menu)
        win.listWidget.currentItemChanged.connect(itemSelected_event)
        win.listWidget.itemClicked.connect(itemSelected_event)
        win.listWidget.itemDoubleClicked.connect(itemClicked_event)
        def enterPressed():
            itemClicked_event(win.listWidget.currentItem())
        shortcuts = []
        shortcuts.append(QShortcut(
            QtGui.QKeySequence(QtCore.Qt.Key_Return),
            win.listWidget,
            activated=enterPressed
        ))
        def channelfilter_do():
            btn_update.click()
        loading = QtWidgets.QLabel(_('loading'))
        loading.setAlignment(QtCore.Qt.AlignCenter)
        loading.setStyleSheet('color: #778a30')
        hideLoading()

        epg_loading = QtWidgets.QLabel(_('epgloading'))
        epg_loading.setAlignment(QtCore.Qt.AlignCenter)
        epg_loading.setStyleSheet('color: #778a30')
        epg_loading.hide()

        myFont2 = QtGui.QFont()
        myFont2.setPointSize(12)
        myFont2.setBold(True)
        loading.setFont(myFont2)
        epg_loading.setFont(myFont2)
        combobox = QtWidgets.QComboBox()
        combobox.currentIndexChanged.connect(group_change)
        for group in groups:
            combobox.addItem(group)

        def focusOutEvent_after(
                playlist_widget_visible,
                controlpanel_widget_visible,
                channelfiltersearch_has_focus
        ):
            channelfilter.usePopup = False
            playlist_widget.setWindowFlags(
                QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                QtCore.Qt.X11BypassWindowManagerHint #| QtCore.Qt.Popup
            )
            controlpanel_widget.setWindowFlags(
                QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                QtCore.Qt.X11BypassWindowManagerHint #| QtCore.Qt.Popup
            )
            if playlist_widget_visible:
                playlist_widget.show()
            if controlpanel_widget_visible:
                controlpanel_widget.show()
            if channelfiltersearch_has_focus:
                #channelfiltersearch.setDisabled(False)
                channelfiltersearch.click()

        @async_function
        def mainthread_timer_2(t2):
            time.sleep(0.05)
            exInMainThread_partial(t2)

        def mainthread_timer(t1):
            mainthread_timer_2(t1)

        class MyLineEdit(QtWidgets.QLineEdit):
            usePopup = False
            if qt_library == 'PySide6':
                click_event = QtCore.Signal()
            else:
                click_event = QtCore.pyqtSignal()
            def mousePressEvent(self, event1):
                if event1.button() == QtCore.Qt.LeftButton:
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
                        channelfiltersearch_has_focus1
                    )
                    mainthread_timer_1 = partial(
                        mainthread_timer,
                        focusOutEvent_after_partial
                    )
                    exInMainThread_partial(mainthread_timer_1)

        def channelfilter_clicked():
            if fullscreen:
                playlist_widget_visible1 = playlist_widget.isVisible()
                controlpanel_widget_visible1 = controlpanel_widget.isVisible()
                channelfilter.usePopup = True
                playlist_widget.setWindowFlags(
                    QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                    QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Popup
                )
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                    QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Popup
                )
                if playlist_widget_visible1:
                    playlist_widget.show()
                if controlpanel_widget_visible1:
                    controlpanel_widget.show()
            if settings["playlistsep"] and \
            bool(sepplaylist_win.windowFlags() & QtCore.Qt.X11BypassWindowManagerHint) and \
            not fullscreen:
                del_sep_flag()
                sepplaylist_win.show()
                sepplaylist_win.raise_()
                sepplaylist_win.setFocus(QtCore.Qt.PopupFocusReason)
                sepplaylist_win.activateWindow()
                channelfilter.setFocus()

        tvguide_many_win = QtWidgets.QMainWindow()
        tvguide_many_win.setWindowTitle((_('tvguide')))
        tvguide_many_win.setWindowIcon(main_icon)
        tvguide_many_win.resize(1000, 700)

        tvguide_many_widget = QtWidgets.QWidget()
        tvguide_many_layout = QtWidgets.QGridLayout()
        tvguide_many_widget.setLayout(tvguide_many_layout)
        tvguide_many_win.setCentralWidget(tvguide_many_widget)

        tvguide_many_table = QtWidgets.QTableWidget()

#        tvguide_many_table.horizontalHeaderItem(0).setToolTip("Column 1 ")
#        tvguide_many_table.horizontalHeaderItem(1).setToolTip("Column 2 ")
#        tvguide_many_table.horizontalHeaderItem(2).setToolTip("Column 3 ")

#        tvguide_many_table.horizontalHeaderItem(0).setTextAlignment(Qt.AlignLeft)
#        tvguide_many_table.horizontalHeaderItem(1).setTextAlignment(Qt.AlignHCenter)
#        tvguide_many_table.horizontalHeaderItem(2).setTextAlignment(Qt.AlignRight)

        #tvguide_many_table.setItem(0, 0, QtWidgets.QTableWidgetItem("Text in column 1"))
        #tvguide_many_table.setItem(0, 1, QtWidgets.QTableWidgetItem("Text in column 2"))
        #tvguide_many_table.setItem(0, 2, QtWidgets.QTableWidgetItem("Text in column 3"))
        #tvguide_many_table.resizeColumnsToContents()

        tvguide_many_layout.addWidget(tvguide_many_table, 0, 0)

        def tvguide_many_clicked(): # pylint: disable=too-many-locals
            tvguide_many_chans = []
            tvguide_many_chans_names = []
            tvguide_many_i = -1
            for tvguide_m_chan in [x6[0] for x6 in sorted(array.items())]:
                epg_search = tvguide_m_chan.lower()
                if epg_search in prog_match_arr:
                    epg_search = prog_match_arr[epg_search.lower()]
                if epg_search in programmes:
                    tvguide_many_i += 1
                    tvguide_many_chans.append(epg_search)
                    tvguide_many_chans_names.append(tvguide_m_chan)
            tvguide_many_table.setRowCount(len(tvguide_many_chans))
            tvguide_many_table.setVerticalHeaderLabels(tvguide_many_chans_names)
            print_with_time(tvguide_many_table.horizontalHeader()) #.setMinimumSectionSize(300)
            a_1_len_array = []
            a_1_array = {}
            for chan_6 in tvguide_many_chans:
                a_1 = [a_2 for a_2 in programmes[chan_6] if a_2['stop'] > time.time() - 1]
                a_1_array[chan_6] = a_1
                a_1_len_array.append(len(a_1))
            tvguide_many_table.setColumnCount(max(a_1_len_array))
            tvguide_many_i2 = -1
            for chan_7 in tvguide_many_chans:
                tvguide_many_i2 += 1
                a_3_i = -1
                for a_3 in a_1_array[chan_7]:
                    a_3_i += 1
                    start_3_many = datetime.datetime.fromtimestamp(
                        a_3['start']
                    ).strftime('%H:%M') + ' - '
                    #).strftime('%d.%m.%y %H:%M') + ' - '
                    stop_3_many = datetime.datetime.fromtimestamp(
                        a_3['stop']
                    ).strftime('%H:%M') + '\n'
                    #).strftime('%d.%m.%y %H:%M') + '\n'
                    try:
                        title_3_many = a_3['title'] if 'title' in a_3 else ''
                    except: # pylint: disable=bare-except
                        title_3_many = ''
                    try:
                        desc_3_many = ('\n' + a_3['desc'] + '\n') if 'desc' in a_3 else ''
                    except: # pylint: disable=bare-except
                        desc_3_many = ''
                    a_3_text = start_3_many + stop_3_many + title_3_many + desc_3_many
                    #a_3_text = title_3_many
                    tvguide_many_table.setItem(
                        tvguide_many_i2,
                        a_3_i,
                        QtWidgets.QTableWidgetItem(a_3_text)
                    )
            tvguide_many_table.setHorizontalHeaderLabels([
                time.strftime('%H:%M', time.localtime()),
                time.strftime('%H:%M', time.localtime())
            ])
            #tvguide_many_table.resizeColumnsToContents()
            if not tvguide_many_win.isVisible():
                moveWindowToCenter(tvguide_many_win)
                tvguide_many_win.show()
                moveWindowToCenter(tvguide_many_win)
            else:
                tvguide_many_win.hide()

        tvguide_many = QtWidgets.QPushButton()
        tvguide_many.setText(_('tvguide'))
        tvguide_many.clicked.connect(tvguide_many_clicked)

        tvguide_widget = QtWidgets.QWidget()
        tvguide_layout = QtWidgets.QHBoxLayout()
        tvguide_layout.setAlignment(QtCore.Qt.AlignRight)
        tvguide_layout.addWidget(tvguide_many)
        tvguide_widget.setLayout(tvguide_layout)

        channelfilter = MyLineEdit()
        channelfilter.click_event.connect(channelfilter_clicked)
        channelfilter.setPlaceholderText(_('chansearch'))
        channelfiltersearch = QtWidgets.QPushButton()
        channelfiltersearch.setText(_('search'))
        channelfiltersearch.clicked.connect(channelfilter_do)
        widget3 = QtWidgets.QWidget()
        layout3 = QtWidgets.QHBoxLayout()
        layout3.addWidget(channelfilter)
        layout3.addWidget(channelfiltersearch)
        widget3.setLayout(layout3)
        widget4 = QtWidgets.QWidget()
        layout4 = QtWidgets.QHBoxLayout()
        layout4.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        page_lbl = QtWidgets.QLabel('{}:'.format(_('page')))
        of_lbl = QtWidgets.QLabel('{}'.format(_('of')))
        page_box = QtWidgets.QSpinBox()
        page_box.setSuffix('        ')
        page_box.setMinimum(1)
        page_box.setMaximum(round(len(array) / settings["channelsonpage"]) + 1)
        page_box.setStyleSheet('''
            QSpinBox::down-button  {
              subcontrol-origin: margin;
              subcontrol-position: center left;
              left: 1px;
              image: url(''' + str(Path('astroncia', ICONS_FOLDER, 'leftarrow.png')) + ''');
              height: 24px;
              width: 24px;
            }

            QSpinBox::up-button  {
              subcontrol-origin: margin;
              subcontrol-position: center right;
              right: 1px;
              image: url(''' + str(Path('astroncia', ICONS_FOLDER, 'rightarrow.png')) + ''');
              height: 24px;
              width: 24px;
            }
        ''')
        page_box.setAlignment(QtCore.Qt.AlignCenter)
        of_lbl.setText('{} {}'.format(_('of'), \
            round(len(array) / settings["channelsonpage"]) + 1))
        def page_change():
            win.listWidget.verticalScrollBar().setValue(0)
            redraw_chans()
        page_box.valueChanged.connect(page_change)
        layout4.addWidget(page_lbl)
        layout4.addWidget(page_box)
        layout4.addWidget(of_lbl)
        #layout4.addWidget(tvguide_widget)
        widget4.setLayout(layout4)
        layout = QtWidgets.QGridLayout()
        layout.setVerticalSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setSpacing(0)
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.layout().addWidget(QtWidgets.QLabel())
        widget.layout().addWidget(combobox)
        widget.layout().addWidget(widget3)
        widget.layout().addWidget(win.listWidget)
        widget.layout().addWidget(widget4)
        widget.layout().addWidget(chan)
        widget.layout().addWidget(loading)
        widget.layout().addWidget(epg_loading)
        dockWidget.setFixedWidth(DOCK_WIDGET_WIDTH)
        if not settings['playlistsep']:
            dockWidget.setTitleBarWidget(QtWidgets.QWidget())
            dockWidget.setWidget(widget)
            dockWidget.setFloating(False)
            dockWidget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
            if settings['panelposition'] == 0:
                win.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)
            else:
                win.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dockWidget)
        else:
            sepplaylist_win.setCentralWidget(widget)
            sepplaylist_win.show()
            seppl_data = False
            if os.path.isfile(str(Path(LOCAL_DIR, 'sepplheight.json'))):
                try:
                    sepplheight_file_0 = open(
                        str(Path(LOCAL_DIR, 'sepplheight.json')), 'r', encoding="utf8"
                    )
                    seppl_data = json.loads(sepplheight_file_0.read())
                    sepplheight_file_0.close()
                except: # pylint: disable=bare-except
                    pass
            RESIZE_WIDTH = dockWidget.width()
            RESIZE_HEIGHT = win.height()
            if seppl_data:
                sepplaylist_win.move(seppl_data[0], seppl_data[1])
                if len(seppl_data) == 4:
                    RESIZE_WIDTH = seppl_data[2]
                    RESIZE_HEIGHT = seppl_data[3]
            else:
                sepplaylist_win.move(win.pos().x() + win.width() + 30, win.pos().y())
            sepplaylist_win.resize(RESIZE_WIDTH, RESIZE_HEIGHT)
            dockWidget.setTitleBarWidget(QtWidgets.QWidget())
            dockWidget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
            dockWidget.setAllowedAreas(QtCore.Qt.NoDockWidgetArea)

        FORBIDDEN_CHARS = ('"', '*', ':', '<', '>', '?', '\\', '/', '|', '[', ']')

        def do_screenshot():
            global l1, time_stop, playing_chan
            if playing_chan:
                l1.show()
                l1.setText2(_('doingscreenshot'))
                ch = playing_chan.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime('%d%m%Y_%H%M%S')
                file_name = 'screenshot_-_' + cur_time + '_-_' + ch + '.png'
                file_path = str(Path(save_folder, 'screenshots', file_name))
                try:
                    if settings['screenshot'] == 0:
                        pillow_img = player.screenshot_raw()
                        pillow_img.save(file_path)
                    else:
                        make_ffmpeg_screenshot(
                            playing_url, file_path,
                            playing_chan, "Referer: {}".format(settings["referer"])
                        )
                    l1.show()
                    l1.setText2(_('screenshotsaved'))
                except: # pylint: disable=bare-except
                    l1.show()
                    l1.setText2(_('screenshotsaveerror'))
                time_stop = time.time() + 1
            else:
                l1.show()
                l1.setText2("{}!".format(_('nochannelselected')))
                time_stop = time.time() + 1

        def update_tvguide(chan_1='', do_return=False, show_all_guides=False): # pylint: disable=too-many-branches, too-many-locals
            global item_selected
            if not chan_1:
                if item_selected:
                    chan_2 = item_selected
                else:
                    chan_2 = sorted(array.items())[0][0]
            else:
                chan_2 = chan_1
            txt = _('notvguideforchannel')
            chan_2 = chan_2.lower()
            newline_symbol = '\n'
            if do_return:
                newline_symbol = '!@#$%^^&*('
            try:
                chan_3 = prog_match_arr[chan_2]
            except: # pylint: disable=bare-except
                chan_3 = chan_2
            if chan_3 in programmes:
                txt = newline_symbol
                prog = programmes[chan_3]
                for pr in prog:
                    override_this = False
                    if show_all_guides:
                        override_this = pr['start'] < time.time() + 1
                    else:
                        override_this = pr['stop'] > time.time() - 1
                    if override_this:
                        start_2 = datetime.datetime.fromtimestamp(
                            pr['start']
                        ).strftime('%d.%m.%y %H:%M') + ' - '
                        stop_2 = datetime.datetime.fromtimestamp(
                            pr['stop']
                        ).strftime('%d.%m.%y %H:%M') + '\n'
                        try:
                            title_2 = pr['title'] if 'title' in pr else ''
                        except: # pylint: disable=bare-except
                            title_2 = ''
                        try:
                            desc_2 = ('\n' + pr['desc'] + '\n') if 'desc' in pr else ''
                        except: # pylint: disable=bare-except
                            desc_2 = ''
                        start_symbl = ''
                        stop_symbl = ''
                        if settings["themecompat"]:
                            start_symbl = '<span style="color: white;">'
                            stop_symbl = '</span>'
                        txt += '<span style="color: green;">' + start_2 + stop_2 + '</span>' + \
                            start_symbl + '<b>' + title_2 + '</b>' + \
                                desc_2 + stop_symbl + newline_symbol
            if do_return:
                return txt
            txt = txt.replace('\n', '<br>').replace('<br>', '', 1)
            txt = txt.replace('<span style="color: green;">', '<span style="color: red;">', 1)
            tvguide_lbl.setText(txt)
            tvguide_lbl_2.setText(txt)
            return ''

        def show_tvguide():
            if settings['gui'] == 0:
                if tvguide_lbl.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    tvguide_lbl.hide()
                    tvguide_close_lbl.hide()
                else:
                    update_tvguide()
                    tvguide_lbl.show()
                    tvguide_close_lbl.show()
            else:
                if epg_win.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    epg_win.hide()
                else:
                    update_tvguide()
                    epg_win.show()

        def hide_tvguide():
            if settings['gui'] == 0:
                if tvguide_lbl.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    tvguide_lbl.hide()
                    tvguide_close_lbl.hide()
            else:
                if epg_win.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    epg_win.hide()

        def update_tvguide_2():
            epg_win_2_checkbox.clear()
            if showonlychplaylist_chk.isChecked():
                for chan_0 in array:
                    epg_win_2_count.setText('({}: {})'.format(_('channels'), len(array)))
                    epg_win_2_checkbox.addItem(chan_0)
            else:
                for chan_0 in programmes:
                    epg_win_2_count.setText('({}: {})'.format(_('channels'), len(programmes)))
                    epg_win_2_checkbox.addItem(chan_0)

        def show_tvguide_2():
            if epg_win_2.isVisible():
                epg_win_2.hide()
            else:
                update_tvguide_2()
                epg_win_2.show()

        is_recording = False
        recording_time = 0
        record_file = None

        def start_record(ch1, url3):
            global is_recording, record_file, time_stop, recording_time
            orig_channel_name = ch1
            if not is_recording:
                is_recording = True
                lbl2.show()
                lbl2.setText(_('preparingrecord'))
                ch = ch1.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime('%d%m%Y_%H%M%S')
                out_file = str(Path(
                    save_folder,
                    'recordings',
                    'recording_-_' + cur_time + '_-_' + ch + '.mkv'
                ))
                record_file = out_file
                record(url3, out_file, orig_channel_name, "Referer: {}".format(settings["referer"]))
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
                l1.setText2(_('nochannelselforrecord'))

        def my_log(loglevel, component, message):
            print_with_time('[{}] {}: {}'.format(loglevel, component, message), log_mpv=True)

        def playLastChannel():
            global playing_url, playing_chan, combobox, m3u
            isPlayingLast = False
            if os.path.isfile(str(Path(LOCAL_DIR, 'lastchannels.json'))) and \
            settings['openprevchan']:
                try:
                    lastfile_1 = open(
                        str(Path(LOCAL_DIR, 'lastchannels.json')), 'r', encoding="utf8"
                    )
                    lastfile_1_dat = json.loads(lastfile_1.read())
                    lastfile_1.close()
                    if lastfile_1_dat[0] in m3u:
                        isPlayingLast = True
                        player.user_agent = lastfile_1_dat[2]
                        setChanText('  ' + lastfile_1_dat[0])
                        itemClicked_event(lastfile_1_dat[0])
                        setChanText('  ' + lastfile_1_dat[0])
                        try:
                            combobox.setCurrentIndex(lastfile_1_dat[3])
                        except: # pylint: disable=bare-except
                            pass
                        try:
                            win.listWidget.setCurrentRow(lastfile_1_dat[4])
                        except: # pylint: disable=bare-except
                            pass
                except: # pylint: disable=bare-except
                    if os.path.isfile(str(Path(LOCAL_DIR, 'lastchannels.json'))):
                        os.remove(str(Path(LOCAL_DIR, 'lastchannels.json')))
            return isPlayingLast

        if os.name == 'nt':
            DIRECT3D = 'direct3d,'
        else:
            DIRECT3D = ''

        if settings['hwaccel']:
            VIDEO_OUTPUT = 'gpu,vdpau,opengl,{}xv,x11'.format(DIRECT3D)
            HWACCEL = 'auto'
        else:
            VIDEO_OUTPUT = '{}xv,x11'.format(DIRECT3D)
            HWACCEL = 'no'

        # Wayland fix
        try:
            if 'WAYLAND_DISPLAY' in os.environ:
                if os.environ['WAYLAND_DISPLAY']:
                    print_with_time("[NOTE] Applying video output fix for Wayland")
                    VIDEO_OUTPUT = 'x11'
        except: # pylint: disable=bare-except
            pass

        options = {
            'vo': '' if os.name == 'nt' else VIDEO_OUTPUT,
            'hwdec': HWACCEL,
            'cursor-autohide': 1000,
            'force-window': True
        }
        options_orig = options.copy()
        options_2 = {}
        try:
            mpv_options_1 = settings['mpv_options']
            if "=" in mpv_options_1:
                pairs = mpv_options_1.split()
                for pair in pairs:
                    key, value = pair.split("=")
                    options[key.replace('--', '')] = value
                    options_2[key.replace('--', '')] = value
        except Exception as e1:
            print_with_time("Could not parse MPV options!")
            print_with_time(e1)
        print_with_time("Testing custom mpv options...")
        print_with_time(options_2)
        try:
            test_options = mpv.MPV(**options_2)
            print_with_time("mpv options OK")
        except: # pylint: disable=bare-except
            print_with_time("mpv options test failed, ignoring them")
            msg_wrongmpvoptions = QtWidgets.QMessageBox(
                qt_icon_warning,
                MAIN_WINDOW_TITLE,
                _('ignoringmpvoptions') + "\n\n" + str(json.dumps(options_2)),
                QtWidgets.QMessageBox.Ok
            )
            msg_wrongmpvoptions.exec()
            options = options_orig

        print_with_time("Using mpv options: {}".format(json.dumps(options)))

        player = None

        QT_URL = "<a href='https://www.qt.io/'>https://www.qt.io/</a>"
        MPV_URL = "<a href='https://mpv.io/'>mpv</a> "
        CLICKABLE_LINKS = [
            'https://gitlab.com/astroncia',
            'https://unixforum.org/viewtopic.php?f=3&t=151801',
            'https://fontawesome.com/',
            'https://creativecommons.org/licenses/by/4.0/'
        ]

        def format_about_text(about_txt):
            about_txt = about_txt.replace('\n', '<br>')
            for clickable_link in CLICKABLE_LINKS:
                about_txt = about_txt.replace(
                    clickable_link,
                    "<a href='{lnk}'>{lnk}</a>".format(lnk=clickable_link)
                )
            return about_txt

        #print_with_time("")
        #print_with_time("M3U: '{}' EPG: '{}'".format(settings["m3u"], settings["epg"]))
        #print_with_time("")

        def main_channel_settings():
            global item_selected, autoclosemenu_time, playing_chan
            if playing_chan:
                autoclosemenu_time = -1
                item_selected = playing_chan
                settings_context_menu()
            else:
                msg = QtWidgets.QMessageBox(
                    qt_icon_warning,
                    MAIN_WINDOW_TITLE,
                    _('nochannelselected'),
                    QtWidgets.QMessageBox.Ok
                )
                msg.exec()

        @idle_function
        def showhideplaylist(arg33=None): # pylint: disable=unused-argument
            global fullscreen
            if not fullscreen:
                try:
                    key_t()
                except: # pylint: disable=bare-except
                    pass

        @idle_function
        def lowpanel_ch_1(arg33=None): # pylint: disable=unused-argument
            global fullscreen
            if not fullscreen:
                try:
                    lowpanel_ch()
                except: # pylint: disable=bare-except
                    pass

        def showhideeverything():
            global fullscreen
            if not fullscreen:
                if settings['playlistsep']:
                    if sepplaylist_win.isVisible():
                        AstronciaData.compact_mode = True
                        sepplaylist_win.hide()
                        dockWidget2.hide()
                        win.menu_bar_qt.hide()
                    else:
                        AstronciaData.compact_mode = False
                        sepplaylist_win.show()
                        dockWidget2.show()
                        win.menu_bar_qt.show()
                else:
                    if dockWidget.isVisible():
                        AstronciaData.compact_mode = True
                        dockWidget.hide()
                        dockWidget2.hide()
                        win.menu_bar_qt.hide()
                    else:
                        AstronciaData.compact_mode = False
                        if not settings["playlistsep"]:
                            dockWidget.show()
                        dockWidget2.show()
                        win.menu_bar_qt.show()

        stream_info.data = {}

        def process_stream_info(dat_count, name44, stream_props_out, stream_info_lbname):
            bold_fnt = QtGui.QFont()
            bold_fnt.setBold(True)

            if stream_info_lbname:
                la2 = QtWidgets.QLabel()
                la2.setStyleSheet('color:green')
                la2.setFont(bold_fnt)
                la2.setText('\n' + stream_info_lbname + '\n')
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

                if str(dat1) == _("Average Bitrate") and stream_props_out == \
                stream_info.video_properties[_("general")]:
                    stream_info.data['video'] = [wdg2, stream_props_out]

                if str(dat1) == _("Average Bitrate") and stream_props_out == \
                stream_info.audio_properties[_("general")]:
                    stream_info.data['audio'] = [wdg2, stream_props_out]

                layout36.addWidget(wdg1, dat_count, 0)
                layout36.addWidget(wdg2, dat_count, 1)
            return dat_count + 1

        def thread_bitrate():
            try:
                if streaminfo_win.isVisible():
                    if 'video' in stream_info.data:
                        stream_info.data['video'][0].setText(
                            stream_info.data['video'][1][_("Average Bitrate")]
                        )
                    if 'audio' in stream_info.data:
                        stream_info.data['audio'][0].setText(
                            stream_info.data['audio'][1][_("Average Bitrate")]
                        )
            except: # pylint: disable=bare-except
                pass

        def open_stream_info():
            global playing_chan, time_stop
            if playing_chan:
                for stream_info_i in reversed(range(layout36.count())):
                    layout36.itemAt(stream_info_i).widget().setParent(None)

                stream_props = [stream_info.video_properties[_("general")], \
                    stream_info.video_properties[_("colour")], \
                    stream_info.audio_properties[_("general")], \
                    stream_info.audio_properties[_("layout")]]

                dat_count = 1
                stream_info_video_lbl = QtWidgets.QLabel(_("Video") + '\n')
                stream_info_video_lbl.setStyleSheet('color:green')
                bold_fnt_2 = QtGui.QFont()
                bold_fnt_2.setBold(True)
                stream_info_video_lbl.setFont(bold_fnt_2)
                layout36.addWidget(stream_info_video_lbl, 0, 0)
                dat_count = process_stream_info(dat_count, _("general"), stream_props[0], "")
                dat_count = process_stream_info(dat_count, _("colour"), stream_props[1], "")
                dat_count = process_stream_info(
                    dat_count,
                    _("general"),
                    stream_props[2],
                    _("Audio")
                )
                dat_count = process_stream_info(dat_count, _("layout"), stream_props[3], "")

                if not streaminfo_win.isVisible():
                    streaminfo_win.show()
                    moveWindowToCenter(streaminfo_win)
                else:
                    streaminfo_win.hide()
            else:
                l1.show()
                l1.setText2("{}!".format(_('nochannelselected')))
                time_stop = time.time() + 1

        streaminfo_win.setWindowTitle(_('Stream Information'))

        applog_win = QtWidgets.QMainWindow()
        applog_win.setWindowTitle(_('applog'))
        applog_win.setWindowIcon(main_icon)
        applog_win.resize(700, 500)
        moveWindowToCenter(applog_win)
        applog_textarea = QtWidgets.QPlainTextEdit()
        applog_textarea.setReadOnly(True)

        def applog_clipcopy_clicked():
            clip = QtWidgets.QApplication.clipboard()
            clip.clear(mode=clip.Clipboard)
            clip.setText(applog_textarea.toPlainText(), mode=clip.Clipboard)

        def applog_save_clicked():
            applog_fname = QtWidgets.QFileDialog.getSaveFileName(
                applog_win,
                _('choosesavefilename'),
                home_folder,
                '{} (*.log *.txt)'.format(_('logs'))
            )[0]
            if applog_fname:
                try:
                    applog_fname_file = open(applog_fname, 'w', encoding="utf8")
                    applog_fname_file.write(applog_textarea.toPlainText())
                    applog_fname_file.close()
                except: # pylint: disable=bare-except
                    pass

        applog_save = QtWidgets.QPushButton()
        applog_save.setText(_('save'))
        applog_save.clicked.connect(applog_save_clicked)
        applog_clipcopy = QtWidgets.QPushButton()
        applog_clipcopy.setText(_('copytoclipboard'))
        applog_clipcopy.clicked.connect(applog_clipcopy_clicked)
        applog_closebtn = QtWidgets.QPushButton()
        applog_closebtn.setText(_('close'))
        applog_closebtn.clicked.connect(applog_win.hide)

        applog_widget2 = QtWidgets.QWidget()
        applog_layout2 = QtWidgets.QHBoxLayout()
        applog_layout2.addWidget(applog_save)
        applog_layout2.addWidget(applog_clipcopy)
        applog_layout2.addWidget(applog_closebtn)
        applog_widget2.setLayout(applog_layout2)

        applog_widget = QtWidgets.QWidget()
        applog_layout = QtWidgets.QVBoxLayout()
        applog_layout.addWidget(applog_textarea)
        applog_layout.addWidget(applog_widget2)
        applog_widget.setLayout(applog_layout)
        applog_win.setCentralWidget(applog_widget)

        mpvlog_win = QtWidgets.QMainWindow()
        mpvlog_win.setWindowTitle(_('mpvlog'))
        mpvlog_win.setWindowIcon(main_icon)
        mpvlog_win.resize(700, 500)
        moveWindowToCenter(mpvlog_win)
        mpvlog_textarea = QtWidgets.QPlainTextEdit()
        mpvlog_textarea.setReadOnly(True)

        def mpvlog_clipcopy_clicked():
            clip = QtWidgets.QApplication.clipboard()
            clip.clear(mode=clip.Clipboard)
            clip.setText(mpvlog_textarea.toPlainText(), mode=clip.Clipboard)

        def mpvlog_save_clicked():
            mpvlog_fname = QtWidgets.QFileDialog.getSaveFileName(
                mpvlog_win,
                _('choosesavefilename'),
                home_folder,
                '{} (*.log *.txt)'.format(_('logs'))
            )[0]
            if mpvlog_fname:
                try:
                    mpvlog_fname_file = open(mpvlog_fname, 'w', encoding="utf8")
                    mpvlog_fname_file.write(mpvlog_textarea.toPlainText())
                    mpvlog_fname_file.close()
                except: # pylint: disable=bare-except
                    pass

        mpvlog_save = QtWidgets.QPushButton()
        mpvlog_save.setText(_('save'))
        mpvlog_save.clicked.connect(mpvlog_save_clicked)
        mpvlog_clipcopy = QtWidgets.QPushButton()
        mpvlog_clipcopy.setText(_('copytoclipboard'))
        mpvlog_clipcopy.clicked.connect(mpvlog_clipcopy_clicked)
        mpvlog_closebtn = QtWidgets.QPushButton()
        mpvlog_closebtn.setText(_('close'))
        mpvlog_closebtn.clicked.connect(mpvlog_win.hide)

        mpvlog_widget2 = QtWidgets.QWidget()
        mpvlog_layout2 = QtWidgets.QHBoxLayout()
        mpvlog_layout2.addWidget(mpvlog_save)
        mpvlog_layout2.addWidget(mpvlog_clipcopy)
        mpvlog_layout2.addWidget(mpvlog_closebtn)
        mpvlog_widget2.setLayout(mpvlog_layout2)

        mpvlog_widget = QtWidgets.QWidget()
        mpvlog_layout = QtWidgets.QVBoxLayout()
        mpvlog_layout.addWidget(mpvlog_textarea)
        mpvlog_layout.addWidget(mpvlog_widget2)
        mpvlog_widget.setLayout(mpvlog_layout)
        mpvlog_win.setCentralWidget(mpvlog_widget)

        def thread_applog():
            try:
                if applog_win.isVisible():
                    applog_textarea_new = get_app_log()
                    if applog_textarea.toPlainText() != applog_textarea_new:
                        applog_textarea.setPlainText(applog_textarea_new)
                        applog_textarea.moveCursor(QtGui.QTextCursor.End)
                if mpvlog_win.isVisible():
                    mpvlog_textarea_new = get_mpv_log()
                    if mpvlog_textarea.toPlainText() != mpvlog_textarea_new:
                        mpvlog_textarea.setPlainText(mpvlog_textarea_new)
                        mpvlog_textarea.moveCursor(QtGui.QTextCursor.End)
            except: # pylint: disable=bare-except
                pass

        def show_app_log():
            applog_win.show()

        def show_mpv_log():
            mpvlog_win.show()

        def is_recording_func():
            global ffmpeg_processes
            ret_code_rec = False
            if ffmpeg_processes:
                ret_code_array = []
                for ffmpeg_process_1 in ffmpeg_processes:
                    ret_code = ffmpeg_process_1[0].returncode
                    if ret_code == 0:
                        ret_code = 1
                    if ret_code:
                        ret_code_array.append(True)
                        ffmpeg_processes.remove(ffmpeg_process_1)
                    else:
                        ret_code_array.append(False)
                ret_code_rec = False not in ret_code_array
            else:
                ret_code_rec = True
            return ret_code_rec

        win.oldpos = None

        @idle_function
        def mouse_move_event_callback(arg11=None): # pylint: disable=unused-argument
            if settings["movedragging"] and win.oldpos:
                try:
                    globalPos1 = get_global_cursor_position()
                    f = QtCore.QPoint(globalPos1 - win.oldpos)
                    win.move(win.x() + f.x(), win.y() + f.y())
                    win.oldpos = globalPos1
                except: # pylint: disable=bare-except
                    pass

        force_turnoff_osc = False

        def move_window_drag():
            global force_turnoff_osc
            if settings["movedragging"]:
                if not win.oldpos:
                    win.oldpos = get_global_cursor_position()
                    force_turnoff_osc = True
                    try:
                        player.osc = False
                    except: # pylint: disable=bare-except
                        pass
                else:
                    win.oldpos = None
                    force_turnoff_osc = False

        def redraw_menubar():
            global playing_chan
            #print_with_time("redraw_menubar called")
            try:
                update_menubar(
                    player.track_list,
                    playing_chan,
                    settings["m3u"],
                    str(Path(LOCAL_DIR, 'menubar.json'))
                )
            except: # pylint: disable=bare-except
                print_with_time("WARNING: redraw_menubar failed")
                show_exception("WARNING: redraw_menubar failed\n\n" + traceback.format_exc())

        right_click_menu = QtWidgets.QMenu()

        @idle_function
        def end_file_callback(arg11=None): # pylint: disable=unused-argument
            if loading.isVisible():
                loading.setText(_('playerror'))
                loading.setStyleSheet('color: red')
                showLoading()
                loading1.hide()
                loading_movie.stop()

        @idle_function
        def file_loaded_callback(arg11=None): # pylint: disable=unused-argument
            global playing_chan
            if playing_chan:
                redraw_menubar()

        @idle_function
        def my_mouse_right_callback(arg11=None): # pylint: disable=unused-argument
            global right_click_menu
            if qt_library == 'PySide6':
                right_click_menu.exec(QtGui.QCursor.pos())
            else:
                right_click_menu.exec_(QtGui.QCursor.pos())

        @idle_function
        def my_mouse_left_callback(arg11=None): # pylint: disable=unused-argument
            global right_click_menu, fullscreen
            if right_click_menu.isVisible():
                right_click_menu.hide()
            else:
                if settings['hideplaylistleftclk'] and not fullscreen:
                    key_t()
            move_window_drag()

        @idle_function
        def my_up_binding_execute(arg11=None): # pylint: disable=unused-argument
            global l1, time_stop
            if settings["mouseswitchchannels"]:
                next_channel()
            else:
                volume = int(player.volume + settings['volumechangestep'])
                volume = min(volume, 200)
                label7.setValue(volume)
                mpv_volume_set()

        @idle_function
        def my_down_binding_execute(arg11=None): # pylint: disable=unused-argument
            global l1, time_stop, fullscreen
            if settings["mouseswitchchannels"]:
                prev_channel()
            else:
                volume = int(player.volume - settings['volumechangestep'])
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
            if os.name == 'nt':
                webbrowser.open('file:///' + str(absolute_path))
            else:
                xdg_open = subprocess.Popen(['xdg-open', str(absolute_path)])
                xdg_open.wait()

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
        def prev_channel(arg11=None): # pylint: disable=unused-argument
            go_channel(-1)

        @idle_function
        def next_channel(arg11=None): # pylint: disable=unused-argument
            go_channel(1)

        if qt_library == 'PySide6':
            qaction_prio = QtGui.QAction.HighPriority
        else:
            qaction_prio = QtWidgets.QAction.HighPriority

        def get_keybind(func1):
            return main_keybinds[func1][0]

        def archive_all_clicked():
            chan_url = array[archive_channel.text()]['url']
            orig_time = archive_all.currentItem().text().split(' - ')[0]
            print_with_time("orig time: {}".format(orig_time))
            orig_timestamp = time.mktime(time.strptime(orig_time, '%d.%m.%y %H:%M'))
            orig_timestamp_1 = datetime.datetime.fromtimestamp(
                orig_timestamp
            ).strftime('%Y-%m-%d-%H-%M-%S')
            print_with_time("orig timestamp: {}".format(orig_timestamp))
            print_with_time("orig timestamp 1: {}".format(orig_timestamp_1))
            ts1 = time.time()
            utc_offset = (
                datetime.datetime.fromtimestamp(ts1) - datetime.datetime.utcfromtimestamp(ts1)
            ).total_seconds()
            print_with_time("calculated utc offset: {}".format(utc_offset))
            utc_timestamp = int(
                datetime.datetime.fromtimestamp(orig_timestamp).timestamp() - utc_offset - 30
            )
            print_with_time("utc timestamp: {}".format(utc_timestamp))
            utc_converted = datetime.datetime.fromtimestamp(
                utc_timestamp
            ).strftime('%d.%m.%y %H:%M')
            print_with_time("utc converted time: {}".format(utc_converted))
            current_utc = int(datetime.datetime.strftime(datetime.datetime.utcnow(), "%s"))
            print_with_time("current utc timestamp: {}".format(current_utc))
            current_utc_date = datetime.datetime.fromtimestamp(
                current_utc
            ).strftime('%d.%m.%y %H:%M')
            print_with_time("current utc timestamp (human-readable): {}".format(current_utc_date))
            utc_string = "?utc={}&lutc={}&t={}".format(utc_timestamp, current_utc, orig_timestamp_1)
            print_with_time("utc string: {}".format(utc_string))
            play_url = chan_url + utc_string
            itemClicked_event(archive_channel.text(), play_url, True)
            progress.hide()
            start_label.setText('')
            start_label.hide()
            stop_label.setText('')
            stop_label.hide()

        archive_all.itemDoubleClicked.connect(archive_all_clicked)

        def update_timeshift_programme():
            global playing_chan, item_selected, archive_all
            #if playing_chan:
            #    cur_name = playing_chan
            #else:
            if item_selected:
                cur_name = item_selected
            else:
                cur_name = list(array)[0]
            archive_channel.setText(cur_name)
            archive_all.clear()
            tvguide_got_1 = re.sub(
                '<[^<]+?>', '', update_tvguide(cur_name, True, True)
            ).split('!@#$%^^&*(')[2:]
            for tvguide_el_1 in tvguide_got_1:
                if tvguide_el_1:
                    archive_all.addItem(tvguide_el_1)

        def show_timeshift():
            update_timeshift_programme()
            if archive_win.isVisible():
                archive_win.hide()
            else:
                moveWindowToCenter(archive_win)
                archive_win.show()

        stopped = False

        # MPRIS
        mpris_loop = None
        if not os.name == 'nt':
            try:
                class MyAppAdapter(MprisAdapter): # pylint: disable=too-many-public-methods
                    def metadata(self) -> dict:
                        channel_keys = list(array.keys())
                        metadata = {
                            "mpris:trackid": "/org/astroncia/iptv/playlist/" + \
                                str(channel_keys.index(playing_chan) + 1 if \
                                    playing_chan in channel_keys else 0),
                            "xesam:url": playing_url,
                            "xesam:title": playing_chan
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
                        if playing_chan: # pylint: disable=no-else-return
                            if player.pause: # pylint: disable=no-else-return
                                return PlayState.PAUSED
                            else:
                                return PlayState.PLAYING
                        else:
                            return PlayState.STOPPED

                    def seek(self, time: Microseconds): # pylint: disable=redefined-outer-name
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
                        return ''

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
                        return ''

                    def get_next_track(self) -> Track:
                        return ''

                # create mpris adapter and initialize mpris server
                my_adapter = MyAppAdapter()
                mpris = Server('astronciaiptvinstance' + str(os.getpid()), adapter=my_adapter)
                event_handler = EventAdapter(mpris.player, mpris.root)

                def wait_until():
                    global stopped
                    while True:
                        if win.isVisible() or stopped: # pylint: disable=no-else-return
                            return True
                        else:
                            time.sleep(0.1)
                    return False

                def mpris_loop_start():
                    global stopped
                    wait_until()
                    if not stopped:
                        print_with_time("Starting MPRIS loop")
                        try:
                            mpris.publish()
                            mpris_loop.run()
                        except: # pylint: disable=bare-except
                            print_with_time("Failed to start MPRIS loop!")

                mpris_loop = GLib.MainLoop()
                mpris_thread = threading.Thread(target=mpris_loop_start)
                mpris_thread.start()
            except Exception as mpris_e: # pylint: disable=bare-except
                print_with_time(mpris_e)
                print_with_time("Failed to set up MPRIS!")

        def update_scheduler_programme():
            channel_list_2 = [chan_name for chan_name in doSort(array)] # pylint: disable=unnecessary-comprehension
            ch_choosed = choosechannel_ch.currentText()
            tvguide_sch.clear()
            if ch_choosed in channel_list_2:
                tvguide_got = re.sub(
                    '<[^<]+?>', '', update_tvguide(ch_choosed, True)
                ).split('!@#$%^^&*(')[2:]
                for tvguide_el in tvguide_got:
                    if tvguide_el:
                        tvguide_sch.addItem(tvguide_el)

        def show_scheduler():
            if scheduler_win.isVisible():
                scheduler_win.hide()
            else:
                choosechannel_ch.clear()
                channel_list = [chan_name for chan_name in doSort(array)] # pylint: disable=unnecessary-comprehension
                for chan1 in channel_list:
                    choosechannel_ch.addItem(chan1)
                if item_selected in channel_list:
                    choosechannel_ch.setCurrentIndex(channel_list.index(item_selected))
                choosechannel_ch.currentIndexChanged.connect(update_scheduler_programme)
                update_scheduler_programme()
                #starttime_w.setDateTime(
                #    QtCore.QDateTime.fromString(
                #        time.strftime(
                #            '%d.%m.%Y %H:%M', time.localtime()
                #        ), 'd.M.yyyy hh:mm'
                #    )
                #)
                #endtime_w.setDateTime(
                #    QtCore.QDateTime.fromString(
                #        time.strftime(
                #            '%d.%m.%Y %H:%M', time.localtime(time.time() + 60)
                #        ), 'd.M.yyyy hh:mm'
                #    )
                #)
                moveWindowToCenter(scheduler_win)
                scheduler_win.show()

        def mpv_volume_set_custom():
            mpv_volume_set()

        label3 = QtWidgets.QPushButton()
        label3.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'pause.png'))))
        label3.setToolTip(_('pause'))
        label3.clicked.connect(mpv_play)
        label4 = QtWidgets.QPushButton()
        label4.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'stop.png'))))
        label4.setToolTip(_('stop'))
        label4.clicked.connect(mpv_stop)
        label5 = QtWidgets.QPushButton()
        label5.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'fullscreen.png'))))
        label5.setToolTip(_('fullscreen'))
        label5.clicked.connect(mpv_fullscreen)
        label5_0 = QtWidgets.QPushButton()
        label5_0.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'folder.png'))))
        label5_0.setToolTip(_('openrecordingsfolder'))
        label5_0.clicked.connect(open_recording_folder)
        label5_1 = QtWidgets.QPushButton()
        label5_1.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'record.png'))))
        label5_1.setToolTip(_("record"))
        label5_1.clicked.connect(do_record)
        label5_2 = QtWidgets.QPushButton()
        label5_2.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'calendar.png'))))
        label5_2.setToolTip(_("scheduler"))
        label5_2.clicked.connect(show_scheduler)
        label6 = QtWidgets.QPushButton()
        label6.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'volume.png'))))
        label6.setToolTip(_('volume'))
        label6.clicked.connect(mpv_mute)
        LABEL7_SET_WIDTH = 150
        label7 = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        label7.setMinimum(0)
        label7.setMaximum(200)
        label7.setFixedWidth(LABEL7_SET_WIDTH)
        label7.valueChanged.connect(mpv_volume_set_custom)
        label7_1 = QtWidgets.QPushButton()
        label7_1.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'screenshot.png'))))
        label7_1.setToolTip(_('screenshot').capitalize())
        label7_1.clicked.connect(do_screenshot)
        label7_2 = QtWidgets.QPushButton()
        label7_2.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'timeshift.png'))))
        label7_2.setToolTip(_('timeshift'))
        label7_2.clicked.connect(show_timeshift)
        label8 = QtWidgets.QPushButton()
        label8.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'settings.png'))))
        label8.setToolTip(_('settings'))
        label8.clicked.connect(show_settings)
        label8_0 = QtWidgets.QPushButton()
        label8_0.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'tv-blue.png'))))
        label8_0.setToolTip(_('playlists'))
        label8_0.clicked.connect(show_playlists)
        label8_1 = QtWidgets.QPushButton()
        label8_1.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'tvguide.png'))))
        label8_1.setToolTip(_('tvguide'))
        label8_1.clicked.connect(show_tvguide)
        label8_4 = QtWidgets.QPushButton()
        label8_4.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'sort.png'))))
        label8_4.setToolTip(_('sort').replace('\n', ' '))
        label8_4.clicked.connect(show_sort)
        label8_2 = QtWidgets.QPushButton()
        label8_2.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'prev.png'))))
        label8_2.setToolTip(_('prevchannel'))
        label8_2.clicked.connect(prev_channel)
        label8_3 = QtWidgets.QPushButton()
        label8_3.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'next.png'))))
        label8_3.setToolTip(_('nextchannel'))
        label8_3.clicked.connect(next_channel)
        label8_5 = QtWidgets.QPushButton()
        label8_5.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'edit.png'))))
        label8_5.setToolTip(_('m3u_m3ueditor'))
        label8_5.clicked.connect(show_m3u_editor)
        label9 = QtWidgets.QPushButton()
        label9.setIcon(QtGui.QIcon(str(Path('astroncia', ICONS_FOLDER, 'help.png'))))
        label9.setToolTip(_('help'))
        label9.clicked.connect(show_help)

        label12 = QtWidgets.QLabel('')
        label11 = QtWidgets.QLabel()
        myFont3 = QtGui.QFont()
        myFont3.setPointSize(11)
        myFont3.setBold(True)
        label11.setFont(myFont3)
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(12)
        label13 = QtWidgets.QLabel('')
        label13.setMinimumWidth(50)
        label12.setFont(myFont4)
        myFont5 = QtGui.QFont()
        myFont5.setPointSize(12)
        label13.setFont(myFont5)

        progress = QtWidgets.QProgressBar()
        progress.setValue(0)
        start_label = QtWidgets.QLabel()
        stop_label = QtWidgets.QLabel()

        vlayout3 = QtWidgets.QVBoxLayout()
        hlayout1 = QtWidgets.QHBoxLayout()
        hlayout2 = QtWidgets.QHBoxLayout()
        #hlayout3 = QtWidgets.QHBoxLayout()

        hlayout1.addWidget(start_label)
        hlayout1.addWidget(progress)
        hlayout1.addWidget(stop_label)

        all_labels = [
            label3,
            label4,
            label5,
            label5_0,
            label5_1,
            label5_2,
            label6,
            label7,
            label7_1,
            label7_2,
            label8,
            label8_0,
            label8_1,
            label8_2,
            label8_3,
            label8_4,
            label8_5,
            label9
        ]

        hlayout2_btns = [
            label3, label4, label5, label5_1,
            label5_2, label5_0, label6,
            label7, label13, label7_1, label7_2,
            label8_1, label8_2, label8_3
        ]

        show_lbls_fullscreen = [
            label3, label4, label5, label5_1,
            label6, label7, label13, label7_1, label7_2,
            label8_1, label8_2, label8_3
        ]

        fs_widget = QtWidgets.QWidget()
        fs_widget_l = QtWidgets.QHBoxLayout()
        label8.setMaximumWidth(32)
        fs_widget_l.addWidget(label8)
        fs_widget.setLayout(fs_widget_l)

        for hlayout2_btn in hlayout2_btns:
            hlayout2.addWidget(hlayout2_btn)
        hlayout2.addStretch(1000000)
        hlayout2.addWidget(label11)
        hlayout2.addWidget(label12)

        vlayout3.addLayout(hlayout2)
        hlayout2.addStretch(1)
        vlayout3.addLayout(hlayout1)

        widget2 = QtWidgets.QWidget()
        widget2.setLayout(vlayout3)
        dockWidget2.setTitleBarWidget(QtWidgets.QWidget())
        dockWidget2.setWidget(widget2)
        dockWidget2.setFloating(False)
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
        dockWidget2.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget2)

        progress.hide()
        start_label.hide()
        stop_label.hide()
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)

        l1 = QtWidgets.QLabel(win)
        myFont1 = QtGui.QFont()
        myFont1.setPointSize(12)
        myFont1.setBold(True)
        l1.setStyleSheet('background-color: ' + BCOLOR)
        l1.setFont(myFont1)
        l1.setWordWrap(True)
        l1.move(50, 50)
        l1.setAlignment(QtCore.Qt.AlignCenter)

        static_text = ""
        gl_is_static = False

        def set_text_l1(text):
            global static_text, gl_is_static
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
            except: # pylint: disable=bare-except
                userAgent2 = def_user_agent
            return userAgent2

        def saveLastChannel():
            if playing_url:
                current_group_0 = 0
                if combobox.currentIndex() != 0:
                    try:
                        current_group_0 = groups.index(array[playing_chan]['tvg-group'])
                    except: # pylint: disable=bare-except
                        pass
                current_channel_0 = 0
                try:
                    current_channel_0 = win.listWidget.currentRow()
                except: # pylint: disable=bare-except
                    pass
                lastfile = open(str(Path(LOCAL_DIR, 'lastchannels.json')), 'w', encoding="utf8")
                lastfile.write(json.dumps(
                    [playing_chan, playing_url, getUserAgent(), current_group_0, current_channel_0]
                ))
                lastfile.close()
            else:
                if os.path.isfile(str(Path(LOCAL_DIR, 'lastchannels.json'))):
                    os.remove(str(Path(LOCAL_DIR, 'lastchannels.json')))

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

        def myExitHandler(): # pylint: disable=too-many-branches
            global stopped, epg_thread, epg_thread_2, mpris_loop, \
            newdockWidgetHeight, newdockWidgetPosition
            if comm_instance.comboboxIndex != -1:
                combobox_index_file = open(
                    str(Path(LOCAL_DIR, 'comboboxindex.json')), 'w', encoding="utf8"
                )
                combobox_index_file.write(json.dumps({
                    "m3u": settings['m3u'],
                    "index": comm_instance.comboboxIndex
                }))
                combobox_index_file.close()
            try:
                if get_first_run():
                    print_with_time("Saving active vf filters...")
                    vf_filters_file = open(
                        str(Path(LOCAL_DIR, 'menubar.json')), 'w', encoding="utf8"
                    )
                    vf_filters_file.write(json.dumps({
                        "vf_filters": get_active_vf_filters()
                    }))
                    vf_filters_file.close()
                    print_with_time("Active vf filters saved")
            except: # pylint: disable=bare-except
                pass
            try:
                print_with_time("Saving main window position...")
                windowpos_file = open(
                    str(Path(LOCAL_DIR, 'windowpos.json')), 'w', encoding="utf8"
                )
                windowpos_file.write(
                    json.dumps({
                        "x": win.geometry().x(),
                        "y": win.geometry().y()
                    })
                )
                windowpos_file.close()
                print_with_time("Main window position saved")
            except: # pylint: disable=bare-except
                pass
            try:
                print_with_time("Saving main window width / height...")
                window_size = {'w': win.width(), 'h': win.height()}
                ws_file = open(
                    str(Path(LOCAL_DIR, 'windowsize.json')), 'w', encoding="utf8"
                )
                ws_file.write(json.dumps(window_size))
                ws_file.close()
                print_with_time("Main window width / height saved")
            except: # pylint: disable=bare-except
                pass
            if settings['playlistsep']:
                try:
                    sepplheight_file = open(
                        str(Path(LOCAL_DIR, 'sepplheight.json')), 'w', encoding="utf8"
                    )
                    sepplheight_file.write(json.dumps([
                        sepplaylist_win.pos().x(),
                        sepplaylist_win.pos().y(),
                        sepplaylist_win.size().width(),
                        sepplaylist_win.size().height()
                    ]))
                    sepplheight_file.close()
                except: # pylint: disable=bare-except
                    pass
            try:
                expheight_file = open(
                    str(Path(LOCAL_DIR, 'expheight.json')), 'w', encoding="utf8"
                )
                expheight_file.write(
                    json.dumps({
                        "expplaylistheight": newdockWidgetHeight,
                        "expplaylistposition": newdockWidgetPosition,
                        "w_width": cur_win_width(),
                        "w_height": cur_win_height()
                    })
                )
                expheight_file.close()
            except: # pylint: disable=bare-except
                pass
            try:
                with open(str(Path(LOCAL_DIR, 'compactstate.json')), 'w', encoding="utf8") \
                as compactstate_file:
                    compactstate_file.write(json.dumps({
                        "compact_mode": AstronciaData.compact_mode,
                        "playlist_hidden": AstronciaData.playlist_hidden,
                        "controlpanel_hidden": AstronciaData.controlpanel_hidden
                    }))
                    compactstate_file.close()
            except: # pylint: disable=bare-except
                pass
            saveLastChannel()
            stop_record()
            for rec_1 in sch_recordings:
                do_stop_record(rec_1)
            if mpris_loop:
                mpris_loop.quit()
            stopped = True
            if epg_thread:
                try:
                    epg_thread.kill()
                except: # pylint: disable=bare-except
                    epg_thread.terminate()
            if epg_thread_2:
                try:
                    epg_thread_2.kill()
                except: # pylint: disable=bare-except
                    epg_thread_2.terminate()
            for process_3 in active_children():
                try:
                    process_3.kill()
                except: # pylint: disable=bare-except
                    process_3.terminate()
            if manager:
                manager.shutdown()
            try:
                if channel_icons_data.manager_1:
                    channel_icons_data.manager_1.shutdown()
            except: # pylint: disable=bare-except
                pass
            try:
                if channel_icons_data_epg.manager_1:
                    channel_icons_data_epg.manager_1.shutdown()
            except: # pylint: disable=bare-except
                pass
            print_with_time("Stopped")
            # Stopping all childs
            current_pid = os.getpid()
            if not os.name == 'nt':
                os.killpg(0, signal.SIGKILL)
            else:
                os.kill(current_pid, signal.SIGTERM)

        first_boot_1 = True

        epg_thread = None
        manager = None
        return_dict = None
        waiting_for_epg = False
        epg_failed = False

        def thread_tvguide():
            try: # pylint: disable=too-many-nested-blocks
                global stopped, time_stop, first_boot, programmes, btn_update, \
                epg_thread, static_text, manager, tvguide_sets, epg_updating, ic, \
                return_dict, waiting_for_epg, epg_failed, first_boot_1
                if not first_boot:
                    first_boot = True
                    if settings['epg'] and settings['epg'] != 'http://' and not epg_failed:
                        if not use_local_tvguide:
                            update_epg = not settings['donotupdateepg']
                            if not first_boot_1:
                                update_epg = True
                            if update_epg:
                                epg_updating = True
                                l1.setStatic2(True)
                                l1.show()
                                static_text = _('tvguideupdating')
                                l1.setText2("")
                                time_stop = time.time() + 3
                                try:
                                    manager = Manager()
                                    return_dict = manager.dict()
                                    p = Process(target=worker, args=(0, settings, return_dict))
                                    epg_thread = p
                                    p.start()
                                    waiting_for_epg = True
                                except Exception as e1:
                                    epg_failed = True
                                    print_with_time(
                                        "[TV guide, part 1] Caught exception: " + str(e1)
                                    )
                                    l1.setStatic2(False)
                                    l1.show()
                                    l1.setText2(_('tvguideupdatingerror'))
                                    time_stop = time.time() + 3
                                    epg_updating = False
                            else:
                                print_with_time("EPG update at boot disabled")
                            first_boot_1 = False
                        else:
                            programmes = {
                                prog0.lower(): tvguide_sets[prog0] for prog0 in tvguide_sets
                            }
                            btn_update.click() # start update in main thread
            except: # pylint: disable=bare-except
                pass

            ic += 0.1 # pylint: disable=undefined-variable
            if ic > 14.9: # redraw every 15 seconds
                ic = 0
                if channel_icons_data.load_completed:
                    btn_update.click()
                if channel_icons_data_epg.load_completed:
                    btn_update.click()

        def thread_record():
            try:
                global time_stop, gl_is_static, static_text, recording_time, ic1
                ic1 += 0.1  # pylint: disable=undefined-variable
                if ic1 > 0.9:
                    ic1 = 0
                    # executing every second
                    if is_recording:
                        if not recording_time:
                            recording_time = time.time()
                        record_time = human_secs(time.time() - recording_time)
                        if os.path.isfile(record_file):
                            record_size = convert_size(os.path.getsize(record_file))
                            lbl2.setText("REC " + record_time + " - " + record_size)
                        else:
                            recording_time = time.time()
                            lbl2.setText(_('recordwaiting'))
                win.update()
                if(time.time() > time_stop) and time_stop != 0:
                    time_stop = 0
                    if not gl_is_static:
                        l1.hide()
                        win.update()
                    else:
                        l1.setText2("")
            except: # pylint: disable=bare-except
                pass

        x_conn = None

        def do_reconnect():
            global x_conn
            if (playing_chan and not loading.isVisible()) and (player.cache_buffering_state == 0):
                print_with_time("Reconnecting to stream")
                try:
                    doPlay(*comm_instance.do_play_args)
                except: # pylint: disable=bare-except
                    print_with_time("Failed reconnecting to stream - no known URL")
            x_conn = None

        def check_connection():
            global x_conn
            try:
                if (playing_chan and not loading.isVisible()) and \
                (player.cache_buffering_state == 0):
                    if not x_conn:
                        print_with_time("Connection to stream lost, waiting 5 secs...")
                        x_conn = QtCore.QTimer()
                        x_conn.timeout.connect(do_reconnect)
                        x_conn.start(5000)
            except: # pylint: disable=bare-except
                print_with_time("Failed to set connection loss detector!")

        def thread_check_tvguide_obsolete(): # pylint: disable=too-many-branches
            try:
                global first_boot, ic2
                check_connection()
                try:
                    if player.video_bitrate:
                        bitrate_arr = [
                            _('bitrate1'), _('bitrate2'),
                            _('bitrate3'), _('bitrate4'), _('bitrate5')
                        ]
                        video_bitrate = " - " + str(format_bytes(player.video_bitrate, bitrate_arr))
                    else:
                        video_bitrate = ""
                except: # pylint: disable=bare-except
                    video_bitrate = ""
                try:
                    audio_codec = player.audio_codec.split(" ")[0]
                except: # pylint: disable=bare-except
                    audio_codec = 'no audio'
                try:
                    codec = player.video_codec.split(" ")[0]
                    width = player.width
                    height = player.height
                except: # pylint: disable=bare-except
                    codec = 'png'
                    width = 800
                    height = 600
                if (not (codec == 'png' and width == 800 and height == 600)) and (width and height):
                    if settings['hidebitrateinfo']:
                        label12.setText('')
                    else:
                        label12.setText('  {}x{}{} - {} / {}'.format(
                            width, height, video_bitrate,
                            codec, audio_codec
                        ))
                    if loading.text() == _('loading'):
                        hideLoading()
                else:
                    label12.setText('')
                ic2 += 0.1  # pylint: disable=undefined-variable
                if ic2 > 9.9:
                    ic2 = 0
                    if not epg_updating:
                        if not is_program_actual(programmes):
                            force_update_epg()
            except: # pylint: disable=bare-except
                pass

        thread_4_lock = False

        def thread_tvguide_2():
            try:
                global stopped, time_stop, first_boot, programmes, btn_update, \
                epg_thread, static_text, manager, tvguide_sets, epg_updating, ic, \
                return_dict, waiting_for_epg, thread_4_lock, epg_failed, prog_ids, epg_icons
                if not thread_4_lock:
                    thread_4_lock = True
                    if waiting_for_epg and return_dict and len(return_dict) == 7:
                        try:
                            if not return_dict[3]:
                                raise return_dict[4]
                            l1.setStatic2(False)
                            l1.show()
                            l1.setText2(_('tvguideupdatingdone'))
                            time_stop = time.time() + 3
                            values = return_dict.values()
                            programmes = {prog0.lower(): values[1][prog0] for prog0 in values[1]}
                            if not is_program_actual(programmes):
                                raise Exception("Programme not actual")
                            prog_ids = return_dict[5]
                            epg_icons = return_dict[6]
                            tvguide_sets = programmes
                            save_tvguide_sets()
                            btn_update.click() # start update in main thread
                        except Exception as e2:
                            epg_failed = True
                            print_with_time("[TV guide, part 2] Caught exception: " + str(e2))
                            l1.setStatic2(False)
                            l1.show()
                            l1.setText2(_('tvguideupdatingerror'))
                            time_stop = time.time() + 3
                        epg_updating = False
                        waiting_for_epg = False
                    thread_4_lock = False
            except: # pylint: disable=bare-except
                pass

        def thread_update_time():
            try:
                if label11 and clockOn:
                    label11.setText('  ' + time.strftime('%H:%M:%S', time.localtime()))
                scheduler_clock.setText(get_current_time())
            except: # pylint: disable=bare-except
                pass

        def thread_osc():
            try:
                global playing_url, force_turnoff_osc
                if playing_url:
                    if not settings["hidempv"]:
                        try:
                            if not force_turnoff_osc:
                                player.osc = True
                            else:
                                player.osc = False
                        except: # pylint: disable=bare-except
                            pass
                else:
                    try:
                        player.osc = False
                    except: # pylint: disable=bare-except
                        pass
            except: # pylint: disable=bare-except
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
            cursor_offset = QtGui.QCursor.pos().x() - prev_cursor.x() + \
                QtGui.QCursor.pos().y() - prev_cursor.y()
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
                        win.container.setCursor(QtCore.Qt.BlankCursor)
                except: # pylint: disable=bare-except
                    pass
            else:
                try:
                    win.container.unsetCursor()
                except: # pylint: disable=bare-except
                    pass

        def resizeCallback(cal_width):
            global fullscreen, newdockWidgetHeight
            if fullscreen:
                newdockWidgetHeight = cal_width

        def moveCallback(cal_pos):
            global fullscreen, newdockWidgetPosition
            cal_position = cal_pos.pos()
            if cal_position.x() and cal_position.y() and fullscreen:
                newdockWidgetPosition = [cal_position.x(), cal_position.y()]

        playlist_widget = ResizableWindow(sepPlaylist=False)
        playlist_widget.callback = resizeCallback
        playlist_widget.callback_move = moveCallback
        playlist_widget_orig = QtWidgets.QWidget(playlist_widget)
        playlist_widget.setCentralWidget(playlist_widget_orig)
        pl_layout = QtWidgets.QGridLayout()
        pl_layout.setVerticalSpacing(0)
        pl_layout.setContentsMargins(0, 0, 0, 0)
        pl_layout.setAlignment(QtCore.Qt.AlignTop)
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
            if newdockWidgetPosition:
                playlist_widget.move(newdockWidgetPosition[0], newdockWidgetPosition[1])
            else:
                if settings['panelposition'] == 0:
                    playlist_widget.move(maptoglobal(win.width() - dockWidget.width(), 0))
                else:
                    playlist_widget.move(maptoglobal(0, 0))
            playlist_widget.setFixedWidth(dockWidget.width())
            if newdockWidgetHeight:
                playlist_widget_height = newdockWidgetHeight
            else:
                playlist_widget_height = win.height() - 50
            playlist_widget.resize(
                playlist_widget.width(),
                playlist_widget_height
            )
            playlist_widget.setWindowOpacity(0.55)
            playlist_widget.setWindowFlags(
                QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                QtCore.Qt.X11BypassWindowManagerHint #| QtCore.Qt.Popup
            )
            pl_layout.addWidget(widget)
            playlist_widget.show()

        def hide_playlist():
            pl_layout.removeWidget(widget)
            if not settings['playlistsep']:
                dockWidget.setWidget(widget)
            else:
                sepplaylist_win.setCentralWidget(widget)
            playlist_widget.hide()

        LABEL7_WIDTH = False

        def show_controlpanel():
            global LABEL7_WIDTH
            if not LABEL7_WIDTH:
                LABEL7_WIDTH = label7.width()
            label7.setFixedWidth(LABEL7_SET_WIDTH)
            controlpanel_widget.setWindowOpacity(0.55)
            if channelfilter.usePopup:
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                    QtCore.Qt.X11BypassWindowManagerHint | QtCore.Qt.Popup
                )
            else:
                controlpanel_widget.setWindowFlags(
                    QtCore.Qt.CustomizeWindowHint | QtCore.Qt.FramelessWindowHint | \
                    QtCore.Qt.X11BypassWindowManagerHint #| QtCore.Qt.Popup
                )
            #cp_layout.addWidget(fs_widget)
            cp_layout.addWidget(widget2)
            lb2_width = 0
            for lb2_wdg in show_lbls_fullscreen:
                if hlayout2.indexOf(lb2_wdg) != -1:
                    lb2_width += lb2_wdg.width() + 10
            controlpanel_widget.setFixedWidth(
                #int(win.width() / 3) - 100
                #650
                lb2_width
            )
            #p_3 = (get_curwindow_pos_actual().center() - controlpanel_widget.rect().center()).x()
            #controlpanel_widget.move(
            #    p_3,
            #    maptoglobal(0, win.height() - 100).y()
            #)
            p_3 = win.container.frameGeometry().center() - QtCore.QRect(
                QtCore.QPoint(), controlpanel_widget.sizeHint()
            ).center()
            controlpanel_widget.move(maptoglobal(
                p_3.x() - 100, win.height() - 100
            ))
            controlpanel_widget.show()

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
                    if not 'REC / ' in lbl2.text():
                        cur_recording = is_ffmpeg_recording() is False
                    else:
                        cur_recording = not is_recording_func() is True
                    if cur_recording:
                        showLoading2()
                    else:
                        hideLoading2()
            except: # pylint: disable=bare-except
                pass

        win_has_focus = False

        def is_win_has_focus():
            return win.isActiveWindow() or \
                sepplaylist_win.isActiveWindow() or \
                help_win.isActiveWindow() or \
                selplaylist_win.isActiveWindow() or \
                streaminfo_win.isActiveWindow() or \
                license_win.isActiveWindow() or \
                sort_win.isActiveWindow() or \
                chan_win.isActiveWindow() or \
                ext_win.isActiveWindow() or \
                scheduler_win.isActiveWindow() or \
                xtream_win.isActiveWindow() or \
                xtream_win_2.isActiveWindow() or \
                archive_win.isActiveWindow() or \
                playlists_win.isActiveWindow() or \
                playlists_win_edit.isActiveWindow() or \
                epg_select_win.isActiveWindow() or \
                tvguide_many_win.isActiveWindow() or \
                applog_win.isActiveWindow() or \
                mpvlog_win.isActiveWindow() or \
                m3u_editor.isActiveWindow() or \
                settings_win.isActiveWindow()

        menubar_st = False
        AstronciaData.playlist_state = sepplaylist_win.isVisible()
        def thread_shortcuts():
            global fullscreen, menubar_st, win_has_focus
            try: # pylint: disable=too-many-nested-blocks
                if settings["playlistsep"]:
                    cur_has_focus = is_win_has_focus()
                    if cur_has_focus != win_has_focus:
                        win_has_focus = cur_has_focus
                        #print_with_time("win_has_focus changed to {}".format(win_has_focus))
                        if win_has_focus:
                            if not fullscreen:
                                if AstronciaData.playlist_state:
                                    sepplaylist_win.show()
                                win.show()
                                win.raise_()
                                win.setFocus(QtCore.Qt.PopupFocusReason)
                                win.activateWindow()
                        else:
                            if settings["playlistsep"]:
                                AstronciaData.playlist_state = sepplaylist_win.isVisible()
                                sepplaylist_win.hide()
            except: # pylint: disable=bare-except
                pass
            try:
                if not fullscreen:
                    menubar_new_st = win.menuBar().isVisible()
                    if menubar_new_st != menubar_st:
                        menubar_st = menubar_new_st
                        if menubar_st:
                            setShortcutState(False)
                        else:
                            setShortcutState(True)
            except: # pylint: disable=bare-except
                pass

        def thread_mouse(): # pylint: disable=too-many-branches
            try:
                player['cursor-autohide'] = 1000
                player['force-window'] = True
            except: # pylint: disable=bare-except
                pass
            try: # pylint: disable=too-many-nested-blocks
                global fullscreen, key_t_visible, dockWidgetVisible, \
                dockWidget2Visible
                if l1.isVisible() and l1.text().startswith(_('volume')) and \
                  not is_show_volume():
                    l1.hide()
                #label13.setText("{}: {}%".format(_('volumeshort'), int(player.volume)))
                label13.setText("{}%".format(int(player.volume)))
                if fullscreen:
                    dockWidget.setFixedWidth(settings['exp2'])
                else:
                    dockWidget.setFixedWidth(DOCK_WIDGET_WIDTH)
                if fullscreen and not key_t_visible:
                    # Playlist
                    if settings['showplaylistmouse']:
                        cursor_x = win.container.mapFromGlobal(QtGui.QCursor.pos()).x()
                        win_width = win.width()
                        if settings['panelposition'] == 0:
                            is_cursor_x = cursor_x > win_width - (settings['exp2'] + 10)
                        else:
                            is_cursor_x = cursor_x < (settings['exp2'] + 10)
                        if is_cursor_x and cursor_x < win_width:
                            if not dockWidgetVisible:
                                dockWidgetVisible = True
                                show_playlist()
                        else:
                            dockWidgetVisible = False
                            hide_playlist()
                    # Control panel
                    if settings['showcontrolsmouse']:
                        cursor_y = win.container.mapFromGlobal(QtGui.QCursor.pos()).y()
                        win_height = win.height()
                        is_cursor_y = cursor_y > win_height - (dockWidget2.height() + 250)
                        if is_cursor_y and cursor_y < win_height:
                            if not dockWidget2Visible:
                                dockWidget2Visible = True
                                show_controlpanel()
                        else:
                            dockWidget2Visible = False
                            hide_controlpanel()
            except: # pylint: disable=bare-except
                pass

        key_t_visible = False
        def key_t():
            global fullscreen
            if not fullscreen:
                if settings['playlistsep']:
                    if sepplaylist_win.isVisible():
                        AstronciaData.playlist_hidden = True
                        sepplaylist_win.hide()
                    else:
                        AstronciaData.playlist_hidden = False
                        sepplaylist_win.show()
                        selplaylist_win.raise_()
                        selplaylist_win.setFocus(QtCore.Qt.PopupFocusReason)
                        selplaylist_win.activateWindow()
                else:
                    if dockWidget.isVisible():
                        AstronciaData.playlist_hidden = True
                        dockWidget.hide()
                    else:
                        AstronciaData.playlist_hidden = False
                        if not settings["playlistsep"]:
                            dockWidget.show()

        def lowpanel_ch():
            if dockWidget2.isVisible():
                AstronciaData.controlpanel_hidden = True
                dockWidget2.hide()
            else:
                AstronciaData.controlpanel_hidden = False
                dockWidget2.show()

        # Key bindings
        def key_quit():
            settings_win.close()
            win.close()
            help_win.close()
            streaminfo_win.close()
            license_win.close()
            myExitHandler()
            app.quit()

        def show_clock():
            global clockOn
            clockOn = not clockOn
            thread_update_time()
            if not clockOn:
                label11.setText('')

        def dockwidget_resize_thread():
            try:
                if start_label.text() and start_label.isVisible():
                    if dockWidget2.height() != DOCK_WIDGET2_HEIGHT_HIGH:
                        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_HIGH)
                else:
                    if dockWidget2.height() != DOCK_WIDGET2_HEIGHT_LOW:
                        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT_LOW)
            except: # pylint: disable=bare-except
                pass

        def set_playback_speed(spd):
            global playing_chan
            try:
                if playing_chan:
                    print_with_time("Set speed to {}".format(spd))
                    player.speed = spd
            except: # pylint: disable=bare-except
                print_with_time("WARNING: set_playback_speed failed")

        def mpv_seek(secs):
            global playing_chan
            try:
                if playing_chan:
                    print_with_time("Seeking to {} seconds".format(secs))
                    player.command('seek', secs)
            except: # pylint: disable=bare-except
                print_with_time("WARNING: mpv_seek failed")

        funcs = {
            "show_sort": show_sort,
            "key_t": key_t,
            "esc_handler": esc_handler,
            "mpv_fullscreen": mpv_fullscreen,
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
            "show_clock": show_clock,
            # Yes, lambda is REALLY needed here
            # don't ask why
            "(lambda: my_up_binding())": (lambda: my_up_binding()), # pylint: disable=undefined-variable, unnecessary-lambda
            "(lambda: my_down_binding())": (lambda: my_down_binding()), # pylint: disable=undefined-variable, unnecessary-lambda
            "show_timeshift": show_timeshift,
            "show_scheduler": show_scheduler,
            "showhideeverything": showhideeverything,
            "show_settings": show_settings,
            "(lambda: set_playback_speed(1.00))": (lambda: set_playback_speed(1.00)),
            "app.quit": app.quit,
            "show_playlists": show_playlists,
            "force_update_epg": force_update_epg,
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
            "show_tvguide_2": show_tvguide_2
        }

        main_keybinds = {
            "(lambda: mpv_seek(-10))": [
                QtCore.Qt.Key_Left
            ],
            "(lambda: mpv_seek(-60))": [
                QtCore.Qt.Key_Down
            ],
            "(lambda: mpv_seek(-600))": [
                QtCore.Qt.Key_PageDown
            ],
            "(lambda: mpv_seek(10))": [
                QtCore.Qt.Key_Right
            ],
            "(lambda: mpv_seek(60))": [
                QtCore.Qt.Key_Up
            ],
            "(lambda: mpv_seek(600))": [
                QtCore.Qt.Key_PageUp
            ],
            "(lambda: my_down_binding())": [
                QtCore.Qt.Key_VolumeDown
            ],
            "(lambda: my_up_binding())": [
                QtCore.Qt.Key_VolumeUp
            ],
            "(lambda: set_playback_speed(1.00))": [
                QtCore.Qt.Key_Backspace
            ],
            "app.quit": [
                "Ctrl+Q"
            ],
            "do_record": [
                QtCore.Qt.Key_R,
                QtCore.Qt.Key_MediaRecord
            ],
            "do_screenshot": [
                QtCore.Qt.Key_H
            ],
            "esc_handler": [
                QtCore.Qt.Key_Escape
            ],
            "force_update_epg": [
                "Ctrl+U"
            ],
            "key_quit": [
                QtCore.Qt.Key_Q
            ],
            "key_t": [
                QtCore.Qt.Key_T
            ],
            "lowpanel_ch_1": [
                QtCore.Qt.Key_P
            ],
            "main_channel_settings": [
                "Ctrl+S"
            ],
            "mpv_fullscreen": [
                QtCore.Qt.Key_F,
                QtCore.Qt.Key_F11
            ],
            "mpv_mute": [
                QtCore.Qt.Key_M,
                QtCore.Qt.Key_VolumeMute
            ],
            "mpv_play": [
                QtCore.Qt.Key_Space,
                QtCore.Qt.Key_MediaTogglePlayPause,
                QtCore.Qt.Key_MediaPlay,
                QtCore.Qt.Key_MediaPause,
                QtCore.Qt.Key_Play
            ],
            "mpv_stop": [
                QtCore.Qt.Key_S,
                QtCore.Qt.Key_Stop,
                QtCore.Qt.Key_MediaStop
            ],
            "my_down_binding_execute": [
                QtCore.Qt.Key_9
            ],
            "my_up_binding_execute": [
                QtCore.Qt.Key_0
            ],
            "next_channel": [
                QtCore.Qt.Key_N,
                QtCore.Qt.Key_MediaNext
            ],
            "open_stream_info": [
                QtCore.Qt.Key_F2
            ],
            "prev_channel": [
                QtCore.Qt.Key_B,
                QtCore.Qt.Key_MediaPrevious
            ],
            "show_clock": [
                QtCore.Qt.Key_O
            ],
            "show_m3u_editor": [
                "Ctrl+E"
            ],
            "show_playlists": [
                "Ctrl+O"
            ],
            "show_scheduler": [
                QtCore.Qt.Key_D
            ],
            "show_settings": [
                "Ctrl+P"
            ],
            "show_sort": [
                QtCore.Qt.Key_I
            ],
            "show_timeshift": [
                QtCore.Qt.Key_E
            ],
            "show_tvguide": [
                QtCore.Qt.Key_G
            ],
            "showhideeverything": [
                "Ctrl+C"
            ],
            "show_tvguide_2": [
                QtCore.Qt.Key_J
            ]
        }

        seq = get_seq()

        def setShortcutState(st1):
            for shortcut in shortcuts:
                if shortcut.key() in seq:
                    shortcut.setEnabled(st1)

        for kbd1 in main_keybinds:
            for kbd in main_keybinds[kbd1]:
                # Main window
                shortcuts.append(QShortcut(
                    QtGui.QKeySequence(kbd),
                    win,
                    activated=funcs[kbd1]
                ))
                # Control panel widget
                shortcuts.append(QShortcut(
                    QtGui.QKeySequence(kbd),
                    controlpanel_widget,
                    activated=funcs[kbd1]
                ))
                # Playlist widget
                shortcuts.append(QShortcut(
                    QtGui.QKeySequence(kbd),
                    playlist_widget,
                    activated=funcs[kbd1]
                ))
                #if settings["playlistsep"]:
                #    # Separate playlist
                #    QShortcut(
                #        QtGui.QKeySequence(kbd),
                #        sepplaylist_win,
                #        activated=funcs[kbd1]
                #    )

        setShortcutState(False)

        app.aboutToQuit.connect(myExitHandler)

        vol_remembered = 100
        if settings["remembervol"] and os.path.isfile(str(Path(LOCAL_DIR, 'volume.json'))):
            try:
                volfile_1 = open(str(Path(LOCAL_DIR, 'volume.json')), 'r', encoding="utf8")
                volfile_1_out = int(json.loads(volfile_1.read())["volume"])
                volfile_1.close()
            except: # pylint: disable=bare-except
                volfile_1_out = 100
            vol_remembered = volfile_1_out
        firstVolRun = False

        #if doSaveSettings:
        #    save_settings()

        def restore_compact_state():
            if os.path.isfile(str(Path(LOCAL_DIR, 'compactstate.json'))):
                try:
                    with open(str(Path(LOCAL_DIR, 'compactstate.json')), 'r', encoding="utf8") \
                    as compactstate_file_1:
                        compactstate = json.loads(compactstate_file_1.read())
                        compactstate_file_1.close()
                        if compactstate["compact_mode"]:
                            showhideeverything()
                        else:
                            if compactstate["playlist_hidden"]:
                                key_t()
                            if compactstate["controlpanel_hidden"]:
                                lowpanel_ch()
                except: # pylint: disable=bare-except
                    pass

        def read_expheight_json():
            global newdockWidgetHeight, newdockWidgetPosition
            try:
                if os.path.isfile(str(Path(LOCAL_DIR, 'expheight.json'))):
                    print_with_time("Loading expheight.json...")

                    cur_w_width = cur_win_width()
                    cur_w_height = cur_win_height()
                    print_with_time(
                        "Current width / height: {}x{}".format(cur_w_width, cur_w_height)
                    )

                    expheight_file_0 = open(
                        str(Path(LOCAL_DIR, 'expheight.json')), 'r', encoding="utf8"
                    )
                    expheight_file_0_read = json.loads(expheight_file_0.read())

                    expheight_read_continue = True
                    if 'w_width' in expheight_file_0_read and 'w_height' in expheight_file_0_read:
                        read_w_width = expheight_file_0_read['w_width']
                        read_w_height = expheight_file_0_read['w_height']
                        print_with_time(
                            "Remembered width / height: {}x{}".format(read_w_width, read_w_height)
                        )
                        if read_w_width == cur_w_width and read_w_height == cur_w_height:
                            print_with_time("Matched, continue")
                        else:
                            print_with_time("Resolution changed, ignoring old settings")
                            expheight_read_continue = False

                    if expheight_read_continue:
                        newdockWidgetHeight = expheight_file_0_read["expplaylistheight"]
                        try:
                            newdockWidgetPosition = expheight_file_0_read["expplaylistposition"]
                        except: # pylint: disable=bare-except
                            pass
                    expheight_file_0.close()
            except: # pylint: disable=bare-except
                pass

        if settings['m3u'] and m3u:
            win.show()
            init_mpv_player()
            win.raise_()
            win.setFocus(QtCore.Qt.PopupFocusReason)
            win.activateWindow()
            if os.path.isfile(str(Path(LOCAL_DIR, 'windowpos.json'))):
                try:
                    print_with_time("Restoring main window position...")
                    windowpos_file_1 = open(
                        str(Path(LOCAL_DIR, 'windowpos.json')), 'r', encoding="utf8"
                    )
                    windowpos_file_1_out = windowpos_file_1.read()
                    windowpos_file_1.close()
                    windowpos_file_1_json = json.loads(windowpos_file_1_out)
                    win.move(windowpos_file_1_json['x'], windowpos_file_1_json['y'])
                    print_with_time("Main window position restored")
                except: # pylint: disable=bare-except
                    pass
            if os.path.isfile(str(Path(LOCAL_DIR, 'comboboxindex.json'))):
                try:
                    combobox_index_file_1 = open(
                        str(Path(LOCAL_DIR, 'comboboxindex.json')), 'r', encoding="utf8"
                    )
                    combobox_index_file_1_out = combobox_index_file_1.read()
                    combobox_index_file_1.close()
                    combobox_index_file_1_json = json.loads(combobox_index_file_1_out)
                    if combobox_index_file_1_json['m3u'] == settings['m3u']:
                        if combobox_index_file_1_json['index'] < combobox.count():
                            combobox.setCurrentIndex(combobox_index_file_1_json['index'])
                except: # pylint: disable=bare-except
                    pass
            read_expheight_json()
            if not playLastChannel():
                print_with_time("Show splash")
                mpv_override_play(str(Path('astroncia', ICONS_FOLDER, 'main.png')))
            else:
                print_with_time("Playing last channel, splash turned off")
            restore_compact_state()

            ic, ic1, ic2 = 0, 0, 0
            timers_array = {}
            timers = {
                thread_shortcuts: 25,
                thread_mouse: 50,
                thread_cursor: 50,
                thread_applog: 50,
                thread_tvguide: 100,
                thread_record: 100,
                thread_osc: 100,
                thread_check_tvguide_obsolete: 100,
                thread_tvguide_2: 1000,
                thread_update_time: 1000,
                record_thread: 1000,
                record_thread_2: 1000,
                thread_afterrecord: 50,
                channel_icons_thread: 2000,
                channel_icons_thread_epg: 2000,
                thread_bitrate: UPDATE_BR_INTERVAL * 1000,
                epg_channel_icons_thread: 50,
                dockwidget_resize_thread: 50
            }
            for timer in timers:
                timers_array[timer] = QtCore.QTimer()
                timers_array[timer].timeout.connect(timer)
                timers_array[timer].start(timers[timer])
        else:
            if not os.path.isfile(str(Path(LOCAL_DIR, 'settings.json'))):
                selplaylist_win.show()
                selplaylist_win.raise_()
                selplaylist_win.setFocus(QtCore.Qt.PopupFocusReason)
                selplaylist_win.activateWindow()
                moveWindowToCenter(selplaylist_win)
            else:
                show_playlists()
                playlists_win.raise_()
                playlists_win.setFocus(QtCore.Qt.PopupFocusReason)
                playlists_win.activateWindow()

        if qt_library == 'PySide6':
            try:
                sys.exit(app.exec())
            except: # pylint: disable=bare-except
                # Qt 6.0 compatibility
                sys.exit(app.exec_())
        else:
            sys.exit(app.exec_())
    except Exception as e3:
        print_with_time("ERROR")
        print_with_time("")
        e3_traceback = traceback.format_exc()
        print_with_time(e3_traceback)
        show_exception(e3, e3_traceback)
        sys.exit(1)
