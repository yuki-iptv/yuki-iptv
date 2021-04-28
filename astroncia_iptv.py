#!/usr/bin/env python3
'''Astroncia IPTV - Cross platform IPTV player'''
# pylint: disable=invalid-name, global-statement, missing-docstring, wrong-import-position
# pylint: disable=c-extension-no-member, too-many-lines, line-too-long, ungrouped-imports
# pylint: disable=too-many-statements, broad-except, pointless-string-statement
#
# Icons by Font Awesome ( https://fontawesome.com/ ) ( https://fontawesome.com/license )
#
# The Font Awesome pictograms are licensed under the CC BY 4.0 License - https://creativecommons.org/licenses/by/4.0/
#
'''
Copyright (C) 2021 Astroncia

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
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
import codecs
import ctypes
import webbrowser
import threading
from multiprocessing import Process, Manager, freeze_support
freeze_support()
import requests
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from data.modules.astroncia.lang import lang
from data.modules.astroncia.ua import user_agent, uas
from data.modules.astroncia.epg import worker
from data.modules.astroncia.record import record, record_return, stop_record
from data.modules.astroncia.format import format_seconds_to_hhmmss
from data.modules.astroncia.conversion import convert_size
from data.modules.astroncia.providers import iptv_providers
from data.modules.astroncia.time import print_with_time
from data.modules.astroncia.epgurls import EPG_URLS
from data.modules.astroncia.bitrate import humanbytes
from data.modules.thirdparty.selectionmodel import ReorderableListModel, SelectionModel
from data.modules.thirdparty.m3u import M3uParser
from data.modules.thirdparty.m3ueditor import Viewer
if not os.name == 'nt':
    try:
        from gi.repository import GLib
        from data.modules.thirdparty.mpris_server.adapters import PlayState, MprisAdapter, \
          Microseconds, VolumeDecimal, RateDecimal, Track, DEFAULT_RATE
        from data.modules.thirdparty.mpris_server.events import EventAdapter
        from data.modules.thirdparty.mpris_server.server import Server
    except: # pylint: disable=bare-except
        print("Failed to init MPRIS libraries!")

APP_VERSION = '0.0.23'

if not sys.version_info >= (3, 4, 0):
    print_with_time("Incompatible Python version! Required >= 3.4")
    sys.exit(1)

if not (os.name == 'nt' or os.name == 'posix'):
    print_with_time("Unsupported platform!")
    sys.exit(1)

MAIN_WINDOW_TITLE = 'Astroncia IPTV'
WINDOW_SIZE = (1200, 600)
DOCK_WIDGET2_HEIGHT = int(WINDOW_SIZE[1] / 6)
DOCK_WIDGET_WIDTH = int((WINDOW_SIZE[0] / 2) - 200)
TVGUIDE_WIDTH = int((WINDOW_SIZE[0] / 5))
BCOLOR = "#A2A3A3"
MAX_ON_ONE_PAGE = 100

if DOCK_WIDGET2_HEIGHT < 0:
    DOCK_WIDGET2_HEIGHT = 0

if DOCK_WIDGET_WIDTH < 0:
    DOCK_WIDGET_WIDTH = 0

parser = argparse.ArgumentParser(description='Astroncia IPTV')
parser.add_argument('--python')
args1 = parser.parse_args()

if 'HOME' in os.environ and os.path.isdir(os.environ['HOME']):
    LOCAL_DIR = str(Path(os.environ['HOME'], '.AstronciaIPTV'))
    SAVE_FOLDER_DEFAULT = str(Path(os.environ['HOME'], '.AstronciaIPTV', 'saves'))
    if not os.path.isdir(LOCAL_DIR):
        os.mkdir(LOCAL_DIR)
    if not os.path.isdir(SAVE_FOLDER_DEFAULT):
        os.mkdir(SAVE_FOLDER_DEFAULT)
else:
    LOCAL_DIR = 'local'
    SAVE_FOLDER_DEFAULT = str(Path(os.path.dirname(os.path.abspath(__file__)), 'AstronciaIPTV_saves'))

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

LANG = lang[settings_lang0]['strings'] if settings_lang0 in lang else lang[LANG_DEFAULT]['strings']
LANG_NAME = lang[settings_lang0]['strings']['name'] if settings_lang0 in lang else lang[LANG_DEFAULT]['strings']['name']
print_with_time("Settings locale: {}\n".format(LANG_NAME))

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def show_exception(e):
    eprint("\n{}\n\n{}\n".format(LANG['error2'], str(e)))

# Used as a decorator to run things in the background
def async_function(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

# @async_function

if os.name == 'nt':
    a0 = sys.executable
    if args1.python:
        a0 = args1.python
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(Path(os.path.dirname(a0), 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'))

if __name__ == '__main__':
    try:
        os.environ['GDK_BACKEND'] = 'x11'
    except: # pylint: disable=bare-except
        pass
    try:
        print_with_time("Astroncia IPTV {}...".format(LANG['starting']))
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        modules_path = str(Path(os.path.dirname(__file__), 'data', 'modules', 'binary'))
        if os.name == 'nt':
            os.environ["PATH"] = modules_path + os.pathsep + os.environ["PATH"]

        m3u = ""
        clockOn = False

        if os.name == 'nt':
            if not (os.path.isfile(str(Path(modules_path, 'ffmpeg.exe'))) and os.path.isfile(str(Path(modules_path, 'mpv-1.dll')))):
                show_exception(LANG['binarynotfound'])
                sys.exit(1)

        try:
            from data.modules.thirdparty import mpv
        except: # pylint: disable=bare-except
            print_with_time("Falling back to old mpv library...")
            from data.modules.thirdparty import mpv_old as mpv

        if not os.path.isdir(LOCAL_DIR):
            os.mkdir(LOCAL_DIR)

        channel_sets = {}
        prog_ids = {}
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
                "deinterlace": True,
                "udp_proxy": "",
                "save_folder": SAVE_FOLDER_DEFAULT,
                "provider": "",
                "nocache": True,
                "lang": LANG_DEFAULT,
                "timezone": DEF_TIMEZONE,
                "hwaccel": True,
                "sort": 0,
                "cache_secs": 1,
                "useragent": 2,
                "mpv_options": '',
                'donotupdateepg': False,
                'gui': 0
            }
            m3u = ""
        if 'hwaccel' not in settings:
            settings['hwaccel'] = True
        if 'sort' not in settings:
            settings['sort'] = 0
        if 'cache_secs' not in settings:
            settings['cache_secs'] = 1
        if 'timezone' not in settings:
            settings['timezone'] = DEF_TIMEZONE
        if 'useragent' not in settings:
            settings['useragent'] = 2
        if 'mpv_options' not in settings:
            settings['mpv_options'] = ''
        if 'donotupdateepg' not in settings:
            settings['donotupdateepg'] = False
        if 'gui' not in settings:
            settings['gui'] = 0
        if settings['hwaccel']:
            print_with_time("{} {}".format(LANG['hwaccel'].replace('\n', ' '), LANG['enabled']))
        else:
            print_with_time("{} {}".format(LANG['hwaccel'].replace('\n', ' '), LANG['disabled']))

        if os.path.isfile(str(Path(LOCAL_DIR, 'tvguide.dat'))):
            try:
                tvguide_c = open(str(Path(LOCAL_DIR, 'tvguide.dat')), 'rb')
                tvguide_c1 = json.loads(codecs.decode(codecs.decode(tvguide_c.read(), 'zlib'), 'utf-8'))["tvguide_url"]
                tvguide_c.close()
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    cm3uf1 = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r', encoding="utf8")
                    cm3u1 = json.loads(cm3uf1.read())
                    cm3uf1.close()
                    try:
                        epg_url1 = cm3u1['epgurl']
                        if not settings["epg"]:
                            settings["epg"] = epg_url1
                    except: # pylint: disable=bare-except
                        pass
                if tvguide_c1 != settings["epg"]:
                    os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
            except: # pylint: disable=bare-except
                tvguide_c1 = ""

        tvguide_sets = {}
        def save_tvguide_sets_proc():
            global tvguide_sets
            if tvguide_sets:
                file2 = open(str(Path(LOCAL_DIR, 'tvguide.dat')), 'wb')
                file2.write(codecs.encode(bytes(json.dumps({"tvguide_sets": clean_programme(), "tvguide_url": str(settings["epg"]), "prog_ids": prog_ids}), 'utf-8'), 'zlib'))
                file2.close()

        epg_thread_2 = None

        def save_tvguide_sets():
            global epg_thread_2
            epg_thread_2 = Process(target=save_tvguide_sets_proc)
            epg_thread_2.start()

        if not os.path.isfile(str(Path(LOCAL_DIR, 'tvguide.dat'))):
            save_tvguide_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, 'tvguide.dat')), 'rb')
            try:
                tvguide_json = json.loads(codecs.decode(file1.read(), 'zlib'))
            except: # pylint: disable=bare-except
                tvguide_json = {"tvguide_sets": {}, "tvguide_url": "", "prog_ids": {}}
            tvguide_sets = tvguide_json["tvguide_sets"]
            try:
                prog_ids = tvguide_json["prog_ids"]
            except: # pylint: disable=bare-except
                pass
            file1.close()

        def clean_programme():
            sets1 = tvguide_sets.copy()
            if sets1:
                for prog2 in sets1:
                    sets1[prog2] = [x12 for x12 in sets1[prog2] if time.time() + 172800 > x12['start'] and time.time() - 172800 < x12['stop']]
            return sets1

        def is_program_actual(sets0):
            found_prog = False
            if sets0:
                for prog1 in sets0:
                    pr1 = sets0[prog1]
                    for p in pr1:
                        if time.time() > p['start'] and time.time() < p['stop']:
                            found_prog = True
            return found_prog

        use_local_tvguide = True

        if not is_program_actual(tvguide_sets):
            use_local_tvguide = False

        app = QtWidgets.QApplication(sys.argv)
        main_icon = QtGui.QIcon(str(Path(os.path.dirname(__file__), 'data', 'icons', 'tv.png')))
        channels = {}
        programmes = {}

        m3u_editor = Viewer(lang=LANG)

        def show_m3u_editor():
            if m3u_editor.isVisible():
                m3u_editor.hide()
            else:
                m3u_editor.show()

        save_folder = settings['save_folder']

        if not os.path.isdir(str(Path(save_folder))):
            os.mkdir(str(Path(save_folder)))

        if not os.path.isdir(str(Path(save_folder, 'screenshots'))):
            os.mkdir(str(Path(save_folder, 'screenshots')))

        if not os.path.isdir(str(Path(save_folder, 'recordings'))):
            os.mkdir(str(Path(save_folder, 'recordings')))

        array = {}
        groups = []

        use_cache = settings['m3u'].startswith('http://') or settings['m3u'].startswith('https://')
        if settings['nocache']:
            use_cache = False
        if not use_cache:
            print_with_time(LANG['nocacheplaylist'])
        if use_cache and os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            pj = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r', encoding="utf8")
            pj1 = json.loads(pj.read())['url']
            pj.close()
            if pj1 != settings['m3u']:
                os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
        if (not use_cache) and os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
        if not os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
            print_with_time(LANG['loadingplaylist'])
            if settings['m3u']:
                if os.path.isfile(settings['m3u']):
                    file = open(settings['m3u'], 'r', encoding="utf8")
                    m3u = file.read()
                    file.close()
                else:
                    try:
                        m3u = requests.get(settings['m3u'], headers={'User-Agent': user_agent}, timeout=3).text
                    except: # pylint: disable=bare-except
                        m3u = ""

            m3u_parser = M3uParser(settings['udp_proxy'])
            epg_url = ""
            if m3u:
                try:
                    m3u_data0 = m3u_parser.readM3u(m3u)
                    m3u_data = m3u_data0[0]
                    epg_url = m3u_data0[1]
                    if epg_url and not settings["epg"]:
                        settings["epg"] = epg_url
                    for m3u_line in m3u_data:
                        array[m3u_line['title']] = m3u_line
                        if not m3u_line['tvg-group'] in groups:
                            groups.append(m3u_line['tvg-group'])
                except: # pylint: disable=bare-except
                    print_with_time("Playlist parsing error!")
                    show_exception(LANG['playlistloaderror'])
                    m3u = ""
                    array = {}
                    groups = []

            a = 'hidden_channels'
            if settings['provider'] in iptv_providers and a in iptv_providers[settings['provider']]:
                h1 = iptv_providers[settings['provider']][a]
                h1 = json.loads(base64.b64decode(bytes(h1, 'utf-8')).decode('utf-8'))
                for ch2 in h1:
                    ch2['tvg-name'] = ch2['tvg-name'] if 'tvg-name' in ch2 else ''
                    ch2['tvg-ID'] = ch2['tvg-ID'] if 'tvg-ID' in ch2 else ''
                    ch2['tvg-logo'] = ch2['tvg-logo'] if 'tvg-logo' in ch2 else ''
                    ch2['tvg-group'] = ch2['tvg-group'] if 'tvg-group' in ch2 else LANG['allchannels']
                    array[ch2['title']] = ch2
            print_with_time(LANG['playlistloaddone'])
            if use_cache:
                print_with_time(LANG['cachingplaylist'])
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
                print_with_time(LANG['playlistcached'])
        else:
            print_with_time(LANG['usingcachedplaylist'])
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

        if LANG['allchannels'] in groups:
            groups.remove(LANG['allchannels'])
        groups = [LANG['allchannels'], LANG['favourite']] + groups

        if os.path.isfile(str(Path('data', 'channel_icons.json'))):
            icons_file = open(str(Path('data', 'channel_icons.json')), 'r', encoding="utf8")
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

        TV_ICON = QtGui.QIcon(str(Path('data', 'icons', 'tv.png')))
        ICONS_CACHE = {}

        class ScrollLabel(QtWidgets.QScrollArea):
            def __init__(self, *args, **kwargs):
                QtWidgets.QScrollArea.__init__(self, *args, **kwargs)
                self.setWidgetResizable(True)
                content = QtWidgets.QWidget(self)
                content.setStyleSheet('background-color: white')
                self.setWidget(content)
                lay = QtWidgets.QVBoxLayout(content)
                self.label = QtWidgets.QLabel(content)
                self.label.setAlignment(QtCore.Qt.AlignCenter)
                self.label.setWordWrap(True)
                self.label.setStyleSheet('background-color: white')
                lay.addWidget(self.label)

            def setText(self, text):
                self.label.setText(text)

            def getText1(self):
                return self.label.text()

            def getLabelHeight(self):
                return self.label.height()

        def get_current_time():
            return time.strftime('%d.%m.%y %H:%M', time.localtime())

        settings_win = QtWidgets.QMainWindow()
        settings_win.resize(400, 200)
        settings_win.setWindowTitle(LANG['settings'])
        settings_win.setWindowIcon(main_icon)

        help_win = QtWidgets.QMainWindow()
        help_win.resize(400, 430)
        help_win.setWindowTitle(LANG['help'])
        help_win.setWindowIcon(main_icon)

        sort_win = QtWidgets.QMainWindow()
        sort_win.resize(400, 500)
        sort_win.setWindowTitle(LANG['sort'].replace('\n', ' '))
        sort_win.setWindowIcon(main_icon)

        chan_win = QtWidgets.QMainWindow()
        chan_win.resize(400, 250)
        chan_win.setWindowTitle(LANG['channelsettings'])
        chan_win.setWindowIcon(main_icon)

        epg_win = QtWidgets.QMainWindow()
        epg_win.resize(400, 600)
        epg_win.setWindowTitle(LANG['tvguide'])
        epg_win.setWindowIcon(main_icon)
        tvguide_lbl_2 = ScrollLabel(epg_win)
        tvguide_lbl_2.resize(395, 595)

        scheduler_win = QtWidgets.QMainWindow()
        scheduler_win.resize(1000, 600)
        scheduler_win.setWindowTitle(LANG['scheduler'])
        scheduler_win.setWindowIcon(main_icon)

        providers_win = QtWidgets.QMainWindow()
        providers_win.resize(400, 550)
        providers_win.setWindowTitle(LANG['providers'])
        providers_win.setWindowIcon(main_icon)

        providers_win_edit = QtWidgets.QMainWindow()
        providers_win_edit.resize(500, 180)
        providers_win_edit.setWindowTitle(LANG['providers'])
        providers_win_edit.setWindowIcon(main_icon)

        class providers_data: # pylint: disable=too-few-public-methods
            pass

        providers_data.oldName = ""

        def providers_win_save():
            try:
                providers_list.takeItem(providers_list.row(providers_list.findItems(providers_data.oldName, QtCore.Qt.MatchExactly)[0]))
                providers_data.providers_used.pop(providers_data.oldName)
            except: # pylint: disable=bare-except
                pass
            channel_text_prov = name_edit_1.text()
            if channel_text_prov:
                providers_list.addItem(channel_text_prov)
                providers_data.providers_used[channel_text_prov] = {
                    "m3u": m3u_edit_1.text(),
                    "epg": epg_edit_1.text(),
                    "offset": soffset_1.value()
                }
            providers_save_json()
            providers_win_edit.hide()

        def m3u_file_1_clicked():
            fname_1 = QtWidgets.QFileDialog.getOpenFileName(
                providers_win_edit,
                LANG['selectplaylist'],
                home_folder
            )[0]
            if fname_1:
                m3u_edit_1.setText(fname_1)

        def epg_file_1_clicked():
            fname_2 = QtWidgets.QFileDialog.getOpenFileName(
                providers_win_edit,
                LANG['selectepg'],
                home_folder
            )[0]
            if fname_2:
                epg_edit_1.setText(fname_2)

        name_label_1 = QtWidgets.QLabel('{}:'.format(LANG['provname']))
        m3u_label_1 = QtWidgets.QLabel('{}:'.format(LANG['m3uplaylist']))
        epg_label_1 = QtWidgets.QLabel('{}:'.format(LANG['epgaddress']))
        name_edit_1 = QtWidgets.QLineEdit()
        m3u_edit_1 = QtWidgets.QLineEdit()
        epg_edit_1 = QtWidgets.QLineEdit()
        m3u_file_1 = QtWidgets.QPushButton()
        m3u_file_1.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        m3u_file_1.clicked.connect(m3u_file_1_clicked)
        epg_file_1 = QtWidgets.QPushButton()
        epg_file_1.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        epg_file_1.clicked.connect(epg_file_1_clicked)
        save_btn_1 = QtWidgets.QPushButton(LANG['save'])
        save_btn_1.setStyleSheet('font-weight: bold; color: green;')
        save_btn_1.clicked.connect(providers_win_save)
        set_label_1 = QtWidgets.QLabel(LANG['jtvoffsetrecommendation'])
        set_label_1.setStyleSheet('color: #666600')
        soffset_1 = QtWidgets.QDoubleSpinBox()
        soffset_1.setMinimum(-240)
        soffset_1.setMaximum(240)
        soffset_1.setSingleStep(1)
        soffset_1.setDecimals(1)
        offset_label_1 = QtWidgets.QLabel('{}:'.format(LANG['tvguideoffset']))

        providers_win_edit_widget = QtWidgets.QWidget()
        providers_win_edit_layout = QtWidgets.QGridLayout()
        providers_win_edit_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        providers_win_edit_layout.addWidget(name_label_1, 0, 0)
        providers_win_edit_layout.addWidget(name_edit_1, 0, 1)
        providers_win_edit_layout.addWidget(m3u_label_1, 1, 0)
        providers_win_edit_layout.addWidget(m3u_edit_1, 1, 1)
        providers_win_edit_layout.addWidget(m3u_file_1, 1, 2)
        providers_win_edit_layout.addWidget(epg_label_1, 2, 0)
        providers_win_edit_layout.addWidget(epg_edit_1, 2, 1)
        providers_win_edit_layout.addWidget(epg_file_1, 2, 2)
        providers_win_edit_layout.addWidget(offset_label_1, 3, 0)
        providers_win_edit_layout.addWidget(soffset_1, 3, 1)
        providers_win_edit_layout.addWidget(set_label_1, 4, 1)
        providers_win_edit_layout.addWidget(save_btn_1, 5, 1)
        providers_win_edit_widget.setLayout(providers_win_edit_layout)
        providers_win_edit.setCentralWidget(providers_win_edit_widget)

        def_provider = 0
        def_provider_name = list(iptv_providers.keys())[def_provider].replace('[Worldwide] ', '')
        providers_saved = {}
        if not os.path.isfile(str(Path(LOCAL_DIR, 'providers.json'))):
            providers_saved[def_provider_name] = {
                "m3u": list(iptv_providers.values())[def_provider]['m3u'],
                "offset": 0
            }
            try:
                providers_saved[def_provider_name]["epg"] = list(iptv_providers.values())[def_provider]['epg']
            except: # pylint: disable=bare-except
                providers_saved[def_provider_name]["epg"] = ""
        else:
            providers_json = open(str(Path(LOCAL_DIR, 'providers.json')), 'r', encoding="utf8")
            providers_saved = json.loads(providers_json.read())
            providers_json.close()
        providers_list = QtWidgets.QListWidget(providers_win)
        providers_list.resize(400, 330)
        providers_list.move(0, 0)
        providers_select = QtWidgets.QPushButton(LANG['provselect'], providers_win)
        providers_select.setStyleSheet('font-weight: bold; color: green;')
        providers_select.move(140, 335)
        providers_add = QtWidgets.QPushButton(LANG['provadd'], providers_win)
        providers_add.move(140, 375)
        providers_edit = QtWidgets.QPushButton(LANG['provedit'], providers_win)
        providers_edit.move(140, 415)
        providers_edit.resize(130, 30)
        providers_delete = QtWidgets.QPushButton(LANG['provdelete'], providers_win)
        providers_delete.move(140, 455)
        providers_import = QtWidgets.QPushButton(LANG['importhypnotix'], providers_win)
        providers_import.move(140, 495)
        providers_import.resize(230, 30)

        def providers_json_save(providers_save0=None):
            if not providers_save0:
                providers_save0 = providers_saved
            providers_json1 = open(str(Path(LOCAL_DIR, 'providers.json')), 'w', encoding="utf8")
            providers_json1.write(json.dumps(providers_save0))
            providers_json1.close()

        time_stop = 0

        qr = settings_win.frameGeometry()
        qr.moveCenter(QtWidgets.QDesktopWidget().availableGeometry().center())
        settings_win_l = qr.topLeft()
        origY = settings_win_l.y() - 100
        settings_win_l.setY(origY)
        settings_win.move(settings_win_l)
        help_win.move(qr.topLeft())
        sort_win.move(qr.topLeft())
        chan_win.move(qr.topLeft())
        scheduler_win.move(qr.topLeft())
        providers_win.move(qr.topLeft())
        providers_win_edit.move(qr.topLeft())

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
            start_time_r = starttime_w.dateTime().toPyDateTime().strftime('%d.%m.%y %H:%M')
            end_time_r = endtime_w.dateTime().toPyDateTime().strftime('%d.%m.%y %H:%M')
            schedulers.addItem(
                LANG['channel'] + ': ' + selected_chan + '\n' + \
                  '{}: '.format(LANG['starttime']) + start_time_r + '\n' + \
                  '{}: '.format(LANG['endtime']) + end_time_r + '\n'
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
            return [record_return(record_url, out_file, ch_name), time.time(), out_file, ch_name]

        def do_stop_record(name2):
            if name2 in sch_recordings:
                ffmpeg_process = sch_recordings[name2][0]
                if ffmpeg_process:
                    ffmpeg_process.kill()
                    ffmpeg_process.wait()
                    ffmpeg_process = None

        def record_thread_2():
            activerec_list_value = activerec_list.verticalScrollBar().value()
            activerec_list.clear()
            for sch0 in sch_recordings:
                counted_time0 = format_seconds_to_hhmmss(time.time() - sch_recordings[sch0][1])
                channel_name0 = sch_recordings[sch0][3]
                file_name0 = sch_recordings[sch0][2]
                file_size0 = "WAITING"
                if os.path.isfile(file_name0):
                    file_size0 = convert_size(os.path.getsize(file_name0))
                activerec_list.addItem(channel_name0 + "\n" + counted_time0 + " " + file_size0)
            activerec_list.verticalScrollBar().setValue(activerec_list_value)

        def record_thread():
            global is_recording
            status = LANG['recnothing']
            sch_items = [str(schedulers.item(i1).text()) for i1 in range(schedulers.count())]
            i3 = -1
            for sch_item in sch_items:
                i3 += 1
                status = LANG['recwaiting']
                sch_item = [i2.split(': ')[1] for i2 in sch_item.split('\n') if i2]
                channel_name_rec = sch_item[0]
                #ch_url = array[channel_name_rec]['url']
                current_time = time.strftime('%d.%m.%y %H:%M', time.localtime())
                start_time_1 = sch_item[1]
                end_time_1 = sch_item[2]
                array_name = str(channel_name_rec) + "_" + str(start_time_1) + "_" + str(end_time_1)
                if start_time_1 == current_time:
                    if array_name not in sch_recordings:
                        print_with_time("Starting planned record (start_time='{}' end_time='{}' channel='{}')".format(start_time_1, end_time_1, channel_name_rec))
                        sch_recordings[array_name] = do_start_record(array_name)
                if end_time_1 == current_time:
                    if array_name in sch_recordings:
                        schedulers.takeItem(i3)
                        print_with_time("Stopping planned record (start_time='{}' end_time='{}' channel='{}')".format(start_time_1, end_time_1, channel_name_rec))
                        do_stop_record(array_name)
                        sch_recordings.pop(array_name)
                if sch_recordings:
                    status = LANG['recrecording']
            statusrec_lbl.setText('{}: {}'.format(LANG['status'], status))

        def delrecord_clicked():
            schCurrentRow = schedulers.currentRow()
            if schCurrentRow != -1:
                sch_index = '_'.join([xs.split(': ')[1] for xs in schedulers.item(schCurrentRow).text().split('\n') if xs])
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
        plannedrec_lbl = QtWidgets.QLabel('{}:'.format(LANG['plannedrec']))
        activerec_lbl = QtWidgets.QLabel('{}:'.format(LANG['activerec']))
        statusrec_lbl = QtWidgets.QLabel()
        myFont5 = QtGui.QFont()
        myFont5.setBold(True)
        statusrec_lbl.setFont(myFont5)
        choosechannel_lbl = QtWidgets.QLabel('{}:'.format(LANG['choosechannel']))
        choosechannel_ch = QtWidgets.QComboBox()
        tvguide_sch = QtWidgets.QListWidget()
        tvguide_sch.itemClicked.connect(programme_clicked)
        addrecord_btn = QtWidgets.QPushButton(LANG['addrecord'])
        addrecord_btn.clicked.connect(addrecord_clicked)
        delrecord_btn = QtWidgets.QPushButton(LANG['delrecord'])
        delrecord_btn.clicked.connect(delrecord_clicked)
        scheduler_layout.addWidget(scheduler_clock, 0, 0)
        scheduler_layout.addWidget(choosechannel_lbl, 1, 0)
        scheduler_layout.addWidget(choosechannel_ch, 2, 0)
        scheduler_layout.addWidget(tvguide_sch, 3, 0)

        starttime_lbl = QtWidgets.QLabel('{}:'.format(LANG['starttime']))
        endtime_lbl = QtWidgets.QLabel('{}:'.format(LANG['endtime']))
        starttime_w = QtWidgets.QDateTimeEdit()
        starttime_w.setDateTime(QtCore.QDateTime.fromString(time.strftime('%d.%m.%Y %H:%M', time.localtime()), 'd.M.yyyy hh:mm'))
        endtime_w = QtWidgets.QDateTimeEdit()
        endtime_w.setDateTime(QtCore.QDateTime.fromString(time.strftime('%d.%m.%Y %H:%M', time.localtime(time.time() + 60)), 'd.M.yyyy hh:mm'))

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

        warning_lbl = QtWidgets.QLabel(LANG['warningstr'])
        myFont5 = QtGui.QFont()
        myFont5.setPointSize(11)
        myFont5.setBold(True)
        warning_lbl.setFont(myFont5)
        warning_lbl.setStyleSheet('color: red')
        warning_lbl.setAlignment(QtCore.Qt.AlignCenter)

        scheduler_layout_main = QtWidgets.QVBoxLayout()
        scheduler_layout_main.addWidget(scheduler_widget)
        #scheduler_layout_main.addWidget(warning_lbl)
        scheduler_widget_main = QtWidgets.QWidget()
        scheduler_widget_main.setLayout(scheduler_layout_main)

        scheduler_win.setCentralWidget(scheduler_widget_main)

        def save_sort():
            global channel_sort
            channel_sort = model.getNodes()
            file4 = open(str(Path(LOCAL_DIR, 'sort.json')), 'w', encoding="utf8")
            file4.write(json.dumps(channel_sort))
            file4.close()
            sort_win.hide()

        close_sort_btn = QtWidgets.QPushButton(LANG['close'], sort_win)
        close_sort_btn.move(145, 465)
        close_sort_btn.clicked.connect(sort_win.hide)
        save_sort_btn = QtWidgets.QPushButton(LANG['save'], sort_win)
        save_sort_btn.clicked.connect(save_sort)
        save_sort_btn.move(145, 430)

        home_folder = ""
        try:
            home_folder = os.environ['HOME']
        except: # pylint: disable=bare-except
            pass

        def m3u_select():
            reset_prov()
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win,
                LANG['selectplaylist'],
                home_folder
            )[0]
            if fname:
                sm3u.setText(fname)

        def epg_select():
            reset_prov()
            fname = QtWidgets.QFileDialog.getOpenFileName(
                settings_win,
                LANG['selectepg'],
                home_folder
            )[0]
            if fname:
                sepg.setText(fname)

        def save_folder_select():
            folder_name = QtWidgets.QFileDialog.getExistingDirectory(
                settings_win,
                LANG['selectwritefolder'],
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

        deinterlace_lbl = QtWidgets.QLabel("{}:".format(LANG['deinterlace']))
        useragent_lbl = QtWidgets.QLabel("{}:".format(LANG['useragent']))
        group_lbl = QtWidgets.QLabel("{}:".format(LANG['group']))
        group_text = QtWidgets.QLineEdit()
        hidden_lbl = QtWidgets.QLabel("{}:".format(LANG['hide']))
        deinterlace_chk = QtWidgets.QCheckBox()
        hidden_chk = QtWidgets.QCheckBox()
        useragent_choose = QtWidgets.QComboBox()
        useragent_choose.addItem(LANG['empty'])
        useragent_choose.addItem('Windows Browser')
        useragent_choose.addItem('Android')
        useragent_choose.addItem('iPhone')
        useragent_choose.addItem('Linux Browser')

        contrast_lbl = QtWidgets.QLabel("{}:".format(LANG['contrast']))
        brightness_lbl = QtWidgets.QLabel("{}:".format(LANG['brightness']))
        hue_lbl = QtWidgets.QLabel("{}:".format(LANG['hue']))
        saturation_lbl = QtWidgets.QLabel("{}:".format(LANG['saturation']))
        gamma_lbl = QtWidgets.QLabel("{}:".format(LANG['gamma']))

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

        def_user_agent = uas[settings['useragent']]
        print_with_time("Default user agent: {}".format(def_user_agent))

        def hideLoading():
            loading.hide()
            loading_movie.stop()
            loading1.hide()

        def showLoading():
            loading.show()
            loading_movie.start()
            loading1.show()

        event_handler = None

        def mpv_override_play(arg_override_play):
            global event_handler
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

        def mpv_override_stop():
            global event_handler
            #print_with_time("mpv_override_stop called")
            player.command('stop')
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

        def mpv_override_volume(volume_val):
            global event_handler
            #print_with_time("mpv_override_volume called")
            player.volume = volume_val
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

        def stopPlayer():
            try:
                mpv_override_stop()
            except: # pylint: disable=bare-except
                player.loop = True
                mpv_override_play(str(Path('data', 'icons', 'main.png')))

        def doPlay(play_url1, ua_ch=def_user_agent):
            loading.setText(LANG['loading'])
            loading.setStyleSheet('color: #778a30')
            showLoading()
            player.loop = False
            stopPlayer()
            if play_url1.startswith("udp://") or play_url1.startswith("rtp://"):
                try:
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
                player.stream_lavf_o = '-reconnect=1 -reconnect_at_eof=1 -reconnect_streamed=1 -reconnect_delay_max=2'
            except: # pylint: disable=bare-except
                pass
            print_with_time("Using user-agent: {}".format(ua_ch if isinstance(ua_ch, str) else uas[ua_ch]))
            if player.deinterlace:
                print_with_time("Deinterlace: enabled")
            else:
                print_with_time("Deinterlace: disabled")
            print_with_time("Contrast: {}".format(player.contrast))
            print_with_time("Brightness: {}".format(player.brightness))
            print_with_time("Hue: {}".format(player.hue))
            print_with_time("Saturation: {}".format(player.saturation))
            print_with_time("Gamma: {}".format(player.gamma))
            player.user_agent = ua_ch if isinstance(ua_ch, str) else uas[ua_ch]
            player.loop = True
            mpv_override_stop()
            mpv_override_play(play_url1)

        def chan_set_save():
            chan_3 = title.text().replace("{}: ".format(LANG['channel']), "")
            channel_sets[chan_3] = {
                "deinterlace": deinterlace_chk.isChecked(),
                "useragent": useragent_choose.currentIndex(),
                "group": group_text.text(),
                "hidden": hidden_chk.isChecked(),
                "contrast": contrast_choose.value(),
                "brightness": brightness_choose.value(),
                "hue": hue_choose.value(),
                "saturation": saturation_choose.value(),
                "gamma": gamma_choose.value()
            }
            save_channel_sets()
            if playing_chan == chan_3:
                player.deinterlace = deinterlace_chk.isChecked()
                player.contrast = contrast_choose.value()
                player.brightness = brightness_choose.value()
                player.hue = hue_choose.value()
                player.saturation = saturation_choose.value()
                player.gamma = gamma_choose.value()
                stopPlayer()
                doPlay(playing_url, uas[useragent_choose.currentIndex()])
            chan_win.close()

        save_btn = QtWidgets.QPushButton(LANG['savesettings'])
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
        verticalLayout.addLayout(horizontalLayout3)
        verticalLayout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        wid.setLayout(verticalLayout)
        chan_win.setCentralWidget(wid)

        # Settings window
        def save_settings(): # pylint: disable=too-many-branches
            global epg_thread, epg_thread_2, manager
            udp_proxy_text = sudp.text()
            udp_proxy_starts = udp_proxy_text.startswith('http://') or udp_proxy_text.startswith('https://')
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
            settings_arr = {
                "m3u": sm3u.text(),
                "epg": sepg.text(),
                "deinterlace": sdei.isChecked(),
                "udp_proxy": udp_proxy_text,
                "save_folder": sfld.text(),
                "provider": sprov.currentText() if sprov.currentText() != '--{}--'.format(LANG['notselected']) else '',
                "nocache": supdate.isChecked(),
                "lang": lang1,
                "timezone": soffset.value(),
                "hwaccel": shwaccel.isChecked(),
                "sort": sort_widget.currentIndex(),
                "cache_secs": scache1.value(),
                "useragent": useragent_choose_2.currentIndex(),
                "mpv_options": mpv_options.text(),
                'donotupdateepg': donot_flag.isChecked(),
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
            if manager:
                manager.shutdown()
            win.close()
            settings_win.close()
            help_win.close()
            time.sleep(0.1)
            if not os.name == 'nt':
                if args1.python:
                    os.execv(args1.python, ['python'] + sys.argv)
                else:
                    sys_executable = sys.executable
                    if not os.path.isfile(sys_executable):
                        sys_executable = str(Path(os.path.dirname(os.path.abspath(__file__)), 'astroncia_iptv'))
                        os.execv(sys_executable, sys.argv)
                    else:
                        os.execv(sys_executable, ['python'] + sys.argv + ['--python', sys_executable])
            stop_record()
            if not os.name == 'nt':
                sys.exit(0)
            else:
                try:
                    os._exit(23) # pylint: disable=protected-access
                except: # pylint: disable=bare-except
                    sys.exit(23)

        wid2 = QtWidgets.QWidget()

        m3u_label = QtWidgets.QLabel('{}:'.format(LANG['m3uplaylist']))
        update_label = QtWidgets.QLabel('{}:'.format(LANG['updateatboot']))
        epg_label = QtWidgets.QLabel('{}:'.format(LANG['epgaddress']))
        dei_label = QtWidgets.QLabel('{}:'.format(LANG['deinterlace']))
        hwaccel_label = QtWidgets.QLabel('{}:'.format(LANG['hwaccel']))
        sort_label = QtWidgets.QLabel('{}:'.format(LANG['sort']))
        cache_label = QtWidgets.QLabel('{}:'.format(LANG['cache']))
        udp_label = QtWidgets.QLabel('{}:'.format(LANG['udpproxy']))
        fld_label = QtWidgets.QLabel('{}:'.format(LANG['writefolder']))
        lang_label = QtWidgets.QLabel('{}:'.format(LANG['interfacelang']))
        offset_label = QtWidgets.QLabel('{}:'.format(LANG['tvguideoffset']))
        set_label = QtWidgets.QLabel(LANG['jtvoffsetrecommendation'])
        set_label.setStyleSheet('color: #666600')
        fastview_label = QtWidgets.QLabel(LANG['stableview'])
        fastview_label.setStyleSheet('color: #1D877C')
        hours_label = QtWidgets.QLabel(LANG['hours'])

        def reset_channel_settings():
            if os.path.isfile(str(Path(LOCAL_DIR, 'channels.json'))):
                os.remove(str(Path(LOCAL_DIR, 'channels.json')))
            if os.path.isfile(str(Path(LOCAL_DIR, 'favourites.json'))):
                os.remove(str(Path(LOCAL_DIR, 'favourites.json')))
            if os.path.isfile(str(Path(LOCAL_DIR, 'sort.json'))):
                os.remove(str(Path(LOCAL_DIR, 'sort.json')))
            save_settings()
        def reset_prov():
            if sprov.currentText() != '--{}--'.format(LANG['notselected']):
                sprov.setCurrentIndex(0)
        def combo_reset():
            if sepgcombox.currentIndex() != 0:
                reset_prov()

        sm3u = QtWidgets.QLineEdit()
        sm3u.setText(settings['m3u'])
        sm3u.textEdited.connect(reset_prov)
        sepg = QtWidgets.QLineEdit()
        sepg.setText(settings['epg'])
        sepg.textEdited.connect(reset_prov)
        sepgcombox = QtWidgets.QComboBox()
        sepgcombox.setLineEdit(sepg)
        sepgcombox.addItems([settings['epg']] + EPG_URLS)
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
        scache = QtWidgets.QLabel(LANG['seconds'])
        sselect = QtWidgets.QLabel("{}:".format(LANG['orselectyourprovider']))
        sselect.setStyleSheet('color: #00008B;')
        ssave = QtWidgets.QPushButton(LANG['savesettings'])
        ssave.setStyleSheet('font-weight: bold; color: green;')
        ssave.clicked.connect(save_settings)
        sreset = QtWidgets.QPushButton(LANG['resetchannelsettings'])
        sreset.clicked.connect(reset_channel_settings)
        sort_widget = QtWidgets.QComboBox()
        sort_widget.addItem(LANG['sortitems1'])
        sort_widget.addItem(LANG['sortitems2'])
        sort_widget.addItem(LANG['sortitems3'])
        sort_widget.addItem(LANG['sortitems4'])
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
                sys.exit(0)
        def prov_select(self): # pylint: disable=unused-argument
            prov1 = sprov.currentText()
            if prov1 != '--{}--'.format(LANG['notselected']):
                sm3u.setText(iptv_providers[prov1]['m3u'])
                if 'epg' in iptv_providers[prov1]:
                    sepg.setText(iptv_providers[prov1]['epg'])
        sprov.currentIndexChanged.connect(prov_select)
        sprov.addItem('--{}--'.format(LANG['notselected']))
        provs = {}
        ic3 = 0
        for prov in iptv_providers:
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
        sclose = QtWidgets.QPushButton(LANG['close'])
        sclose.clicked.connect(close_settings)

        def force_update_epg():
            global use_local_tvguide, first_boot
            if os.path.exists(str(Path(LOCAL_DIR, 'tvguide.dat'))):
                os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
            use_local_tvguide = False
            if not epg_updating:
                first_boot = False

        def update_m3u():
            if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            save_settings()

        sm3ufile = QtWidgets.QPushButton(settings_win)
        sm3ufile.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        sm3ufile.clicked.connect(m3u_select)
        sm3uupd = QtWidgets.QPushButton(settings_win)
        sm3uupd.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'update.png'))))
        sm3uupd.clicked.connect(update_m3u)
        sm3uupd.setToolTip(LANG['update'])

        sepgfile = QtWidgets.QPushButton(settings_win)
        sepgfile.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        sepgfile.clicked.connect(epg_select)
        sepgupd = QtWidgets.QPushButton(settings_win)
        sepgupd.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'update.png'))))
        sepgupd.clicked.connect(force_update_epg)
        sepgupd.setToolTip(LANG['update'])

        sfolder = QtWidgets.QPushButton(settings_win)
        sfolder.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        sfolder.clicked.connect(save_folder_select)

        soffset = QtWidgets.QDoubleSpinBox()
        soffset.setMinimum(-240)
        soffset.setMaximum(240)
        soffset.setSingleStep(1)
        soffset.setDecimals(1)
        soffset.setValue(settings["timezone"])

        sframe = QtWidgets.QFrame()
        sframe.setFrameShape(QtWidgets.QFrame.HLine)
        sframe.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe1 = QtWidgets.QFrame()
        sframe1.setFrameShape(QtWidgets.QFrame.HLine)
        sframe1.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe2 = QtWidgets.QFrame()
        sframe2.setFrameShape(QtWidgets.QFrame.HLine)
        sframe2.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe3 = QtWidgets.QFrame()
        sframe3.setFrameShape(QtWidgets.QFrame.HLine)
        sframe3.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe4 = QtWidgets.QFrame()
        sframe4.setFrameShape(QtWidgets.QFrame.HLine)
        sframe4.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe5 = QtWidgets.QFrame()
        sframe5.setFrameShape(QtWidgets.QFrame.HLine)
        sframe5.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe6 = QtWidgets.QFrame()
        sframe6.setFrameShape(QtWidgets.QFrame.HLine)
        sframe6.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe7 = QtWidgets.QFrame()
        sframe7.setFrameShape(QtWidgets.QFrame.HLine)
        sframe7.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe8 = QtWidgets.QFrame()
        sframe8.setFrameShape(QtWidgets.QFrame.HLine)
        sframe8.setFrameShadow(QtWidgets.QFrame.Raised)
        scache1 = QtWidgets.QSpinBox()
        scache1.setMinimum(0)
        scache1.setMaximum(120)
        scache1.setValue(settings["cache_secs"])

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(m3u_label, 1, 0)
        grid.addWidget(sm3u, 1, 1)
        grid.addWidget(sm3ufile, 1, 2)
        grid.addWidget(sm3uupd, 1, 3)

        grid.addWidget(update_label, 2, 0)
        grid.addWidget(supdate, 2, 1)

        grid.addWidget(sframe, 3, 0)
        grid.addWidget(sframe1, 3, 1)
        grid.addWidget(sframe2, 3, 2)
        grid.addWidget(sframe3, 3, 3)

        grid.addWidget(epg_label, 4, 0)
        grid.addWidget(sepgcombox, 4, 1)
        grid.addWidget(sepgfile, 4, 2)
        grid.addWidget(sepgupd, 4, 3)

        grid.addWidget(offset_label, 5, 0)
        grid.addWidget(soffset, 5, 1)
        grid.addWidget(hours_label, 5, 2)

        grid.addWidget(set_label, 6, 1)

        grid.addWidget(fastview_label, 7, 1)

        grid.addWidget(sselect, 8, 1)
        grid.addWidget(sprov, 9, 1)

        grid.addWidget(sframe4, 10, 0)
        grid.addWidget(sframe5, 10, 1)
        grid.addWidget(sframe6, 10, 2)
        grid.addWidget(sframe7, 10, 3)

        useragent_lbl_2 = QtWidgets.QLabel("{}:".format(LANG['useragent']))
        useragent_choose_2 = QtWidgets.QComboBox()
        useragent_choose_2.addItem(LANG['empty'])
        useragent_choose_2.addItem('Windows Browser')
        useragent_choose_2.addItem('Android')
        useragent_choose_2.addItem('iPhone')
        useragent_choose_2.addItem('Linux Browser')
        useragent_choose_2.setCurrentIndex(settings['useragent'])

        mpv_label = QtWidgets.QLabel("{}:".format(LANG['mpv_options']))
        mpv_options = QtWidgets.QLineEdit()
        mpv_options.setText(settings['mpv_options'])
        donot_label = QtWidgets.QLabel("{}:".format(LANG['donotupdateepg']))
        donot_flag = QtWidgets.QCheckBox()
        donot_flag.setChecked(settings['donotupdateepg'])

        gui_label = QtWidgets.QLabel("{}:".format(LANG['epg_gui']))
        gui_choose = QtWidgets.QComboBox()
        gui_choose.addItem(LANG['classic'])
        gui_choose.addItem(LANG['simple'])
        gui_choose.addItem(LANG['simple_noicons'])
        gui_choose.setCurrentIndex(settings['gui'])

        tabs = QtWidgets.QTabWidget()

        tab1 = QtWidgets.QWidget()
        tab2 = QtWidgets.QWidget()
        tab3 = QtWidgets.QWidget()
        tab4 = QtWidgets.QWidget()
        tab5 = QtWidgets.QWidget()
        tabs.addTab(tab1, LANG['tab_main'])
        tabs.addTab(tab2, LANG['tab_video'])
        tabs.addTab(tab3, LANG['tab_network'])
        tabs.addTab(tab5, LANG['tab_gui'])
        tabs.addTab(tab4, LANG['tab_other'])
        tab1.layout = QtWidgets.QGridLayout()
        tab1.layout.addWidget(lang_label, 0, 0)
        tab1.layout.addWidget(slang, 0, 1)
        tab1.layout.addWidget(fld_label, 1, 0)
        tab1.layout.addWidget(sfld, 1, 1)
        tab1.layout.addWidget(sfolder, 1, 2)
        tab1.layout.addWidget(sort_label, 2, 0)
        tab1.layout.addWidget(sort_widget, 2, 1)
        tab1.setLayout(tab1.layout)

        tab2.layout = QtWidgets.QGridLayout()
        tab2.layout.addWidget(dei_label, 0, 0)
        tab2.layout.addWidget(sdei, 0, 1)
        tab2.layout.addWidget(hwaccel_label, 1, 0)
        tab2.layout.addWidget(shwaccel, 1, 1)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 2)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 3)
        tab2.layout.addWidget(QtWidgets.QLabel(), 1, 4)
        tab2.setLayout(tab2.layout)

        tab3.layout = QtWidgets.QGridLayout()
        tab3.layout.addWidget(udp_label, 0, 0)
        tab3.layout.addWidget(sudp, 0, 1)
        tab3.layout.addWidget(cache_label, 1, 0)
        tab3.layout.addWidget(scache1, 1, 1)
        tab3.layout.addWidget(scache, 1, 2)
        tab3.layout.addWidget(useragent_lbl_2, 2, 0)
        tab3.layout.addWidget(useragent_choose_2, 2, 1)
        tab3.setLayout(tab3.layout)

        tab4.layout = QtWidgets.QGridLayout()
        tab4.layout.addWidget(mpv_label, 0, 0)
        tab4.layout.addWidget(mpv_options, 0, 1)
        tab4.layout.addWidget(donot_label, 1, 0)
        tab4.layout.addWidget(donot_flag, 1, 1)
        tab4.setLayout(tab4.layout)

        tab5.layout = QtWidgets.QGridLayout()
        tab5.layout.addWidget(gui_label, 0, 0)
        tab5.layout.addWidget(gui_choose, 0, 1)
        tab5.layout.addWidget(QtWidgets.QLabel(), 1, 2)
        tab5.layout.addWidget(QtWidgets.QLabel(), 1, 3)
        tab5.layout.addWidget(QtWidgets.QLabel(), 1, 4)
        tab5.setLayout(tab5.layout)

        grid2 = QtWidgets.QVBoxLayout()
        grid2.addWidget(tabs)
        grid2.addWidget(sframe8)

        grid3 = QtWidgets.QGridLayout()
        grid3.setSpacing(10)

        grid3.addWidget(ssave, 2, 1)
        grid3.addWidget(sreset, 3, 1)
        grid3.addWidget(sclose, 4, 1)

        layout2 = QtWidgets.QVBoxLayout()
        layout2.addLayout(grid)
        layout2.addLayout(grid2)
        layout2.addLayout(grid3)

        wid2.setLayout(layout2)
        settings_win.setCentralWidget(wid2)

        textbox = QtWidgets.QPlainTextEdit(help_win)
        textbox.resize(390, 400)
        textbox.setReadOnly(True)
        textbox.setPlainText(LANG['helptext'].format(APP_VERSION))
        close_btn = QtWidgets.QPushButton(help_win)
        close_btn.move(140, 400)
        close_btn.setText(LANG['close'])
        close_btn.clicked.connect(help_win.close)

        btn_update = QtWidgets.QPushButton()
        btn_update.hide()

        def show_settings():
            if not settings_win.isVisible():
                settings_win.show()
            else:
                settings_win.hide()

        def show_help():
            if not help_win.isVisible():
                help_win.show()
            else:
                help_win.hide()

        def show_sort():
            if not sort_win.isVisible():
                sort_win.show()
            else:
                sort_win.hide()

        def show_providers():
            if not providers_win.isVisible():
                providers_list.clear()
                providers_data.providers_used = providers_saved
                for item2 in providers_data.providers_used:
                    providers_list.addItem(item2)
                providers_win.show()
            else:
                providers_win.hide()

        def providers_selected():
            try:
                prov_data = providers_data.providers_used[providers_list.currentItem().text()]
                prov_m3u = prov_data['m3u']
                prov_epg = ''
                if 'epg' in prov_data:
                    prov_epg = prov_data['epg']
                prov_offset = prov_data['offset']
                sm3u.setText(prov_m3u)
                sepg.setText(prov_epg)
                soffset.setValue(prov_offset)
                sprov.setCurrentIndex(0)
                providers_save_json()
                providers_win.hide()
                providers_win_edit.hide()
                save_settings()
            except: # pylint: disable=bare-except
                pass

        def providers_save_json():
            providers_json_save(providers_data.providers_used)

        def providers_edit_do(ignore0=False):
            try:
                currentItem_text = providers_list.currentItem().text()
            except: # pylint: disable=bare-except
                currentItem_text = ""
            if ignore0:
                name_edit_1.setText("")
                m3u_edit_1.setText("")
                epg_edit_1.setText("")
                soffset_1.setValue(DEF_TIMEZONE)
                providers_data.oldName = ""
                providers_win_edit.show()
            else:
                if currentItem_text:
                    item_m3u = providers_data.providers_used[currentItem_text]['m3u']
                    try:
                        item_epg = providers_data.providers_used[currentItem_text]['epg']
                    except: # pylint: disable=bare-except
                        item_epg = ""
                    item_offset = providers_data.providers_used[currentItem_text]['offset']
                    name_edit_1.setText(currentItem_text)
                    m3u_edit_1.setText(item_m3u)
                    epg_edit_1.setText(item_epg)
                    soffset_1.setValue(item_offset)
                    providers_data.oldName = currentItem_text
                    providers_win_edit.show()

        def providers_delete_do():
            try:
                currentItem_text = providers_list.currentItem().text()
            except: # pylint: disable=bare-except
                currentItem_text = ""
            if currentItem_text:
                providers_list.takeItem(providers_list.currentRow())
                providers_data.providers_used.pop(currentItem_text)
                providers_save_json()

        def providers_add_do():
            providers_edit_do(True)

        def providers_import_do():
            global providers_saved
            providers_hypnotix = {}
            print("Fetching playlists from Hypnotix...")
            try:
                hypnotix_cmd = "dconf dump /org/x/hypnotix/ 2>/dev/null | grep '^providers=' | sed 's/^providers=/{\"hypnotix\": /g' | sed 's/$/}/g' | sed \"s/'/\\\"/g\""
                hypnotix_cmd_eval = subprocess.check_output(hypnotix_cmd, shell=True, text=True).strip()
                if hypnotix_cmd_eval:
                    hypnotix_cmd_eval = json.loads(hypnotix_cmd_eval)['hypnotix']
                    for provider_2 in hypnotix_cmd_eval:
                        provider_2 = provider_2.replace(':' * 9, '^' * 9).split(':::')
                        provider_2[2] = provider_2[2].split('^' * 9)
                        provider_2[2][0] = provider_2[2][0].replace('file://', '')
                        prov_name_2 = provider_2[0]
                        prov_m3u_2 = provider_2[2][0]
                        prov_epg_2 = provider_2[2][1]
                        providers_hypnotix[prov_name_2] = {
                            "m3u": prov_m3u_2,
                            "epg": prov_epg_2,
                            "offset": DEF_TIMEZONE
                        }
            except: # pylint: disable=bare-except
                print("Failed fetching playlists from Hypnotix!")
            if providers_hypnotix:
                try:
                    providers_list.takeItem(providers_list.row(providers_list.findItems(def_provider_name, QtCore.Qt.MatchExactly)[0]))
                    providers_data.providers_used.pop(def_provider_name)
                except: # pylint: disable=bare-except
                    pass
                providers_data.providers_used = providers_hypnotix
                providers_saved = providers_hypnotix
                for prov_name_4 in providers_data.providers_used:
                    providers_list.addItem(prov_name_4)
                providers_save_json()
                print("Successfully imported playlists from Hypnotix!")
                providers_win.hide()
                providers_win_edit.hide()
                save_settings()
            else:
                print("No Hypnotix playlists found!")

        providers_list.itemDoubleClicked.connect(providers_selected)
        providers_select.clicked.connect(providers_selected)
        providers_add.clicked.connect(providers_add_do)
        providers_edit.clicked.connect(providers_edit_do)
        providers_delete.clicked.connect(providers_delete_do)
        providers_import.clicked.connect(providers_import_do)

        # This is necessary since PyQT stomps over the locale settings needed by libmpv.
        # This needs to happen after importing PyQT before creating the first mpv.MPV instance.
        locale.setlocale(locale.LC_NUMERIC, 'C')

        fullscreen = False

        class MainWindow(QtWidgets.QMainWindow):
            def __init__(self):
                super().__init__()
                # Shut up pylint (attribute-defined-outside-init)
                self.windowWidth = self.width()
                self.windowHeight = self.height()
                self.main_widget = None
                self.listWidget = None
            def update(self):
                global l1, tvguide_lbl, fullscreen

                self.windowWidth = self.width()
                self.windowHeight = self.height()
                tvguide_lbl.move(2, 35)
                if not fullscreen:
                    lbl2.move(0, 5)
                    l1.setFixedWidth(self.windowWidth - dockWidget.width() + 58)
                    l1.move(
                        int(((self.windowWidth - l1.width()) / 2) - (dockWidget.width() / 1.7)),
                        int(((self.windowHeight - l1.height()) - dockWidget2.height() - 10))
                    )
                    h = dockWidget2.height()
                    h2 = 20
                else:
                    lbl2.move(0, 5)
                    l1.setFixedWidth(self.windowWidth)
                    l1.move(
                        int(((self.windowWidth - l1.width()) / 2)),
                        int(((self.windowHeight - l1.height()) - 20))
                    )
                    h = 0
                    h2 = 10
                if tvguide_lbl.isVisible() and not fullscreen:
                    lbl2.move(210, 0)
                if l1.isVisible():
                    l1_h = l1.height()
                else:
                    l1_h = 15
                tvguide_lbl.setFixedHeight(((self.windowHeight - l1_h - h) - 40 - l1_h + h2))
            def resizeEvent(self, event):
                try:
                    self.update()
                except: # pylint: disable=bare-except
                    pass
                QtWidgets.QMainWindow.resizeEvent(self, event)

        win = MainWindow()
        win.setWindowTitle(MAIN_WINDOW_TITLE)
        win.setWindowIcon(main_icon)
        win.resize(WINDOW_SIZE[0], WINDOW_SIZE[1])

        qr = win.frameGeometry()
        qr.moveCenter(QtWidgets.QDesktopWidget().availableGeometry().center())
        win.move(qr.topLeft())

        win.main_widget = QtWidgets.QWidget(win)
        win.main_widget.setFocus()
        win.main_widget.setStyleSheet('''
            background-color: #C0C6CA;
        ''')
        win.setCentralWidget(win.main_widget)

        win.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)
        win.setAttribute(QtCore.Qt.WA_NativeWindow)

        chan = QtWidgets.QLabel(LANG['nochannelselected'])
        chan.setAlignment(QtCore.Qt.AlignCenter)
        chan.setStyleSheet('color: green')
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(11)
        myFont4.setBold(True)
        chan.setFont(myFont4)
        chan.resize(200, 30)

        loading1 = QtWidgets.QLabel(win)
        loading_movie = QtGui.QMovie(str(Path('data', 'icons', 'loading.gif')))
        loading1.setMovie(loading_movie)
        loading1.setStyleSheet('background-color: white;')
        loading1.resize(32, 32)
        loading1.setAlignment(QtCore.Qt.AlignCenter)
        loading1.move(win.rect().center())
        loading1.hide()

        lbl2 = QtWidgets.QLabel(win)
        lbl2.setAlignment(QtCore.Qt.AlignCenter)
        lbl2.setStyleSheet('color: #e0071a')
        lbl2.setWordWrap(True)
        lbl2.resize(200, 30)
        lbl2.move(0, 5)
        lbl2.hide()

        playing = False
        playing_chan = ''

        def show_progress(prog):
            if prog:
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
                progress.show()
                start_label.show()
                stop_label.show()
            else:
                progress.hide()
                start_label.hide()
                stop_label.hide()

        playing_url = ''

        def itemClicked_event(item): # pylint: disable=too-many-branches
            global playing, playing_chan, item_selected, playing_url
            j = item.data(QtCore.Qt.UserRole)
            playing_chan = j
            item_selected = j
            play_url = array[j]['url']
            MAX_CHAN_SIZE = 35
            channel_name = j
            if len(channel_name) > MAX_CHAN_SIZE:
                channel_name = channel_name[:MAX_CHAN_SIZE - 3] + '...'
            chan.setText('  ' + channel_name)
            current_prog = None
            if settings['epg'] and j.lower() in programmes:
                for pr in programmes[j.lower()]:
                    if time.time() > pr['start'] and time.time() < pr['stop']:
                        current_prog = pr
                        break
            show_progress(current_prog)
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT + 20)
            playing = True
            win.update()
            playing_url = play_url
            ua_choose = def_user_agent
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
                ua_choose = d['useragent']
            else:
                player.deinterlace = settings['deinterlace']
            doPlay(play_url, ua_choose)

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
            if player.pause:
                label3.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'pause.png'))))
                label3.setToolTip(LANG['pause'])
                mpv_override_pause(False)
            else:
                label3.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'play.png'))))
                label3.setToolTip(LANG['play'])
                mpv_override_pause(True)

        def mpv_stop():
            global playing, playing_chan, playing_url
            player.osc = False
            playing_chan = ''
            playing_url = ''
            hideLoading()
            chan.setText('')
            playing = False
            stopPlayer()
            player.loop = True
            mpv_override_play(str(Path('data', 'icons', 'main.png')))
            chan.setText(LANG['nochannelselected'])
            progress.hide()
            start_label.hide()
            stop_label.hide()
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 10)
            win.update()

        def esc_handler():
            global fullscreen
            if fullscreen:
                mpv_fullscreen()

        def mpv_fullscreen():
            global fullscreen, l1, time_stop
            if not fullscreen:
                l1.show()
                l1.setText2("{} F".format(LANG['exitfullscreen']))
                time_stop = time.time() + 3
                fullscreen = True
                dockWidget.hide()
                chan.hide()
                #progress.hide()
                #start_label.hide()
                #stop_label.hide()
                dockWidget2.hide()
                dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 10)
                win.update()
                win.showFullScreen()
            else:
                fullscreen = False
                if l1.text().endswith('{} F'.format(LANG['exitfullscreen'])):
                    l1.setText2('')
                    if not gl_is_static:
                        l1.hide()
                        win.update()
                if not player.pause and playing and start_label.text():
                    progress.show()
                    start_label.show()
                    stop_label.show()
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT + 20)
                dockWidget2.show()
                dockWidget.show()
                chan.show()
                win.update()
                win.showNormal()

        old_value = 100

        def mpv_mute():
            global old_value, time_stop, l1
            time_stop = time.time() + 3
            l1.show()
            if player.mute:
                if old_value > 50:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume.png'))))
                else:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume-low.png'))))
                mpv_override_mute(False)
                label7.setValue(old_value)
                l1.setText2("{}: {}%".format(LANG['volume'], int(old_value)))
            else:
                label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'mute.png'))))
                mpv_override_mute(True)
                old_value = label7.value()
                label7.setValue(0)
                l1.setText2(LANG['volumeoff'])

        def mpv_volume_set():
            global time_stop, l1
            time_stop = time.time() + 3
            vol = int(label7.value())
            try:
                l1.show()
                if vol == 0:
                    l1.setText2(LANG['volumeoff'])
                else:
                    l1.setText2("{}: {}%".format(LANG['volume'], vol))
            except NameError:
                pass
            mpv_override_volume(vol)
            if vol == 0:
                mpv_override_mute(True)
                label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'mute.png'))))
            else:
                mpv_override_mute(False)
                if vol > 50:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume.png'))))
                else:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume-low.png'))))

        dockWidget = QtWidgets.QDockWidget(win)
        win.listWidget = QtWidgets.QListWidget()

        tvguide_lbl = ScrollLabel(win)
        tvguide_lbl.move(0, 35)
        tvguide_lbl.setFixedWidth(TVGUIDE_WIDTH)
        tvguide_lbl.hide()

        class QCustomQWidget(QtWidgets.QWidget): # pylint: disable=too-many-instance-attributes
            def __init__(self, parent=None):
                super(QCustomQWidget, self).__init__(parent)
                self.textQVBoxLayout = QtWidgets.QVBoxLayout()      # QtWidgets
                self.textUpQLabel = QtWidgets.QLabel()         # QtWidgets
                myFont = QtGui.QFont()
                myFont.setBold(True)
                self.textUpQLabel.setFont(myFont)
                self.textDownQLabel = QtWidgets.QLabel()         # QtWidgets
                self.textQVBoxLayout.addWidget(self.textUpQLabel)
                self.textQVBoxLayout.addWidget(self.textDownQLabel)
                self.allQHBoxLayout = QtWidgets.QGridLayout()      # QtWidgets
                self.iconQLabel = QtWidgets.QLabel()         # QtWidgets
                self.progressLabel = QtWidgets.QLabel()
                self.progressBar = QtWidgets.QProgressBar()
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

            def setTextUp(self, text):
                self.textUpQLabel.setText(text)

            def setTextDown(self, text):
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

        class QCustomQWidget_simple(QtWidgets.QWidget): # pylint: disable=too-many-instance-attributes
            def __init__(self, parent=None):
                super(QCustomQWidget_simple, self).__init__(parent)
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

            def setTextDown(self, text):
                pass

            def setTextProgress(self, text):
                pass

            def setTextEnd(self, text):
                pass

            def setIcon(self, image):
                self.iconQLabel.setPixmap(image.pixmap(QtCore.QSize(32, 32)))

            def setProgress(self, progress_val):
                pass

            def hideProgress(self):
                pass

        current_group = LANG['allchannels']

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

        #def gen_chans_2():
        #    channels_1 = gen_chans()
        #    items1 = []
        #    for channel_1 in channels_1:
        #        filter_txt = channelfilter.text()
        #        c_name = channels_1[channel_1][3]
        #        # Add QListWidgetItem into QListWidget
        #        if filter_txt.lower().strip() in c_name.lower():
        #            items1.append(channels_1[channel_1])
        #    return items1

        #noclear = len(array) == len(items1) and len(array) == win.listWidget.count()

        def gen_chans(): # pylint: disable=too-many-locals, too-many-branches
            global ICONS_CACHE, playing_chan, current_group, array, page_box, channelfilter
            try:
                idx = (page_box.value() - 1) * MAX_ON_ONE_PAGE
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
                if current_group != LANG['allchannels']:
                    if current_group == LANG['favourite']:
                        if not j1 in favourite_sets:
                            continue
                    else:
                        if group1 != current_group:
                            continue
                array_filtered[j1] = array[j1]

            ch_array = {x13: array_filtered[x13] for x13 in array_filtered if filter_txt.lower().strip() in x13.lower().strip()}
            ch_array = list(ch_array.values())[idx:idx+MAX_ON_ONE_PAGE]
            ch_array = dict([(x14['title'], x14) for x14 in ch_array]) # pylint: disable=consider-using-dict-comprehension
            try:
                if filter_txt:
                    page_box.setMaximum(round(len(ch_array) / MAX_ON_ONE_PAGE) + 1)
                    of_lbl.setText('{} {}'.format(LANG['of'], round(len(ch_array) / MAX_ON_ONE_PAGE) + 1))
                else:
                    page_box.setMaximum(round(len(array_filtered) / MAX_ON_ONE_PAGE) + 1)
                    of_lbl.setText('{} {}'.format(LANG['of'], round(len(array_filtered) / MAX_ON_ONE_PAGE) + 1))
            except: # pylint: disable=bare-except
                pass
            res = {}
            l = -1
            k = 0
            for i in doSort(ch_array):
                l += 1
                k += 1
                prog = ''
                prog_search = i.lower()
                if array_filtered[i]['tvg-ID']:
                    if str(array_filtered[i]['tvg-ID']) in prog_ids:
                        prog_search_lst = prog_ids[str(array_filtered[i]['tvg-ID'])]
                        if prog_search_lst:
                            prog_search = prog_search_lst[0].lower()
                if array_filtered[i]['tvg-name']:
                    if str(array_filtered[i]['tvg-name']) in programmes:
                        prog_search = str(array_filtered[i]['tvg-name']).lower()
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
                        prog = str(percentage) + '% ' + current_prog['title']
                    else:
                        start_time = ''
                        stop_time = ''
                        t_t = time.time()
                        percentage = 0
                        prog = ''
                # Create QCustomQWidget
                if settings['gui'] == 0:
                    myQCustomQWidget = QCustomQWidget()
                else:
                    myQCustomQWidget = QCustomQWidget_simple()
                MAX_SIZE_CHAN = 21
                chan_name = i
                if len(chan_name) > MAX_SIZE_CHAN:
                    chan_name = chan_name[0:MAX_SIZE_CHAN] + "..."
                myQCustomQWidget.setTextUp(str(k) + ". " + chan_name)
                MAX_SIZE = 28
                if len(prog) > MAX_SIZE:
                    prog = prog[0:MAX_SIZE] + "..."
                if prog_search in programmes:
                    myQCustomQWidget.setTextDown(prog)
                    myQCustomQWidget.setTextProgress(start_time)
                    myQCustomQWidget.setTextEnd(stop_time)
                    myQCustomQWidget.setProgress(int(percentage))
                else:
                    myQCustomQWidget.hideProgress()
                i_icon = i.lower()
                icons_l = {picon.lower(): icons[picon] for picon in icons}
                if i_icon in icons_l:
                    if not icons_l[i_icon] in ICONS_CACHE:
                        ICONS_CACHE[icons_l[i_icon]] = QtGui.QIcon(str(Path('data', 'channel_icons', icons_l[i_icon])))
                    myQCustomQWidget.setIcon(ICONS_CACHE[icons_l[i_icon]])
                else:
                    myQCustomQWidget.setIcon(TV_ICON)
                # Create QListWidgetItem
                myQListWidgetItem = QtWidgets.QListWidgetItem()
                myQListWidgetItem.setData(QtCore.Qt.UserRole, i)
                # Set size hint
                myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
                res[l] = [myQListWidgetItem, myQCustomQWidget, l, i]
            j1 = playing_chan.lower()
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

        model = ReorderableListModel()
        if not channel_sort:
            model.setNodes(modelA)
        else:
            model.setNodes(channel_sort)
        selectionModel = SelectionModel(model)
        model.dragDropFinished.connect(selectionModel.onModelItemsReordered)
        sort_label = QtWidgets.QLabel(LANG['donotforgetsort'], sort_win)
        sort_label.resize(400, 50)
        sort_label.setAlignment(QtCore.Qt.AlignCenter)
        sort_list = QtWidgets.QListView(sort_win)
        sort_list.resize(400, 370)
        sort_list.move(0, 50)
        sort_list.setModel(model)
        sort_list.setSelectionModel(selectionModel)
        sort_list.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        sort_list.setDragDropOverwriteMode(False)

        sel_item = None

        def select_context_menu():
            itemClicked_event(sel_item)

        def tvguide_context_menu():
            update_tvguide()
            tvguide_lbl.show()

        def settings_context_menu():
            if chan_win.isVisible():
                chan_win.close()
            title.setText(("{}: " + item_selected).format(LANG['channel']))
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
            else:
                deinterlace_chk.setChecked(True)
                hidden_chk.setChecked(False)
                contrast_choose.setValue(0)
                brightness_choose.setValue(0)
                hue_choose.setValue(0)
                saturation_choose.setValue(0)
                gamma_choose.setValue(0)
                useragent_choose.setCurrentIndex(settings['useragent'])
                group_text.setText('')
            chan_win.show()

        def tvguide_favourites_add():
            if item_selected in favourite_sets:
                favourite_sets.remove(item_selected)
            else:
                favourite_sets.append(item_selected)
            save_favourite_sets()
            btn_update.click()

        def tvguide_start_record():
            url2 = array[item_selected]['url']
            if is_recording:
                start_record("", "")
            start_record(item_selected, url2)

        def show_context_menu(pos):
            global sel_item
            self = win.listWidget
            sel_item = self.selectedItems()[0]
            itemSelected_event(sel_item)
            menu = QtWidgets.QMenu()
            menu.addAction(LANG['select'], select_context_menu)
            menu.addSeparator()
            menu.addAction(LANG['tvguide'], tvguide_context_menu)
            menu.addAction(LANG['favourite'], tvguide_favourites_add)
            menu.addAction(LANG['startrecording'], tvguide_start_record)
            menu.addAction(LANG['channelsettings'], settings_context_menu)
            menu.exec_(self.mapToGlobal(pos))

        win.listWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        win.listWidget.customContextMenuRequested.connect(show_context_menu)
        win.listWidget.currentItemChanged.connect(itemSelected_event)
        win.listWidget.itemClicked.connect(itemSelected_event)
        win.listWidget.itemDoubleClicked.connect(itemClicked_event)
        def enterPressed():
            itemClicked_event(win.listWidget.currentItem())
        QtWidgets.QShortcut(
            QtCore.Qt.Key_Return,
            win.listWidget,
            context=QtCore.Qt.WidgetShortcut,
            activated=enterPressed
        )
        def channelfilter_do():
            btn_update.click()
        loading = QtWidgets.QLabel(LANG['loading'])
        loading.setAlignment(QtCore.Qt.AlignCenter)
        loading.setStyleSheet('color: #778a30')
        hideLoading()
        myFont2 = QtGui.QFont()
        myFont2.setPointSize(12)
        myFont2.setBold(True)
        loading.setFont(myFont2)
        combobox = QtWidgets.QComboBox()
        combobox.currentIndexChanged.connect(group_change)
        for group in groups:
            combobox.addItem(group)
        channelfilter = QtWidgets.QLineEdit()
        channelfilter.setPlaceholderText(LANG['chansearch'])
        channelfiltersearch = QtWidgets.QPushButton()
        channelfiltersearch.setText(LANG['search'])
        channelfiltersearch.clicked.connect(channelfilter_do)
        widget3 = QtWidgets.QWidget()
        layout3 = QtWidgets.QHBoxLayout()
        layout3.addWidget(channelfilter)
        layout3.addWidget(channelfiltersearch)
        widget3.setLayout(layout3)
        widget4 = QtWidgets.QWidget()
        layout4 = QtWidgets.QHBoxLayout()
        layout4.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        page_lbl = QtWidgets.QLabel('{}:'.format(LANG['page']))
        of_lbl = QtWidgets.QLabel('{}'.format(LANG['of']))
        page_box = QtWidgets.QSpinBox()
        page_box.setSuffix('    ')
        page_box.setMinimum(1)
        page_box.setMaximum(round(len(array) / MAX_ON_ONE_PAGE) + 1)
        of_lbl.setText('{} {}'.format(LANG['of'], round(len(array) / MAX_ON_ONE_PAGE) + 1))
        def page_change():
            win.listWidget.verticalScrollBar().setValue(0)
            redraw_chans()
        page_box.valueChanged.connect(page_change)
        layout4.addWidget(page_lbl)
        layout4.addWidget(page_box)
        layout4.addWidget(of_lbl)
        widget4.setLayout(layout4)
        layout = QtWidgets.QGridLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.layout().addWidget(combobox)
        widget.layout().addWidget(widget3)
        widget.layout().addWidget(win.listWidget)
        widget.layout().addWidget(widget4)
        widget.layout().addWidget(chan)
        widget.layout().addWidget(loading)
        dockWidget.setFixedWidth(DOCK_WIDGET_WIDTH)
        dockWidget.setWidget(widget)
        dockWidget.setFloating(False)
        dockWidget.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        win.addDockWidget(QtCore.Qt.RightDockWidgetArea, dockWidget)

        FORBIDDEN_CHARS = ('"', '*', ':', '<', '>', '?', '\\', '/', '|', '[', ']')

        def do_screenshot():
            global l1, time_stop, playing_chan
            if playing_chan:
                l1.show()
                l1.setText2(LANG['doingscreenshot'])
                ch = playing_chan.replace(" ", "_")
                for char in FORBIDDEN_CHARS:
                    ch = ch.replace(char, "")
                cur_time = datetime.datetime.now().strftime('%d%m%Y_%H%M%S')
                file_name = 'screenshot_-_' + cur_time + '_-_' + ch + '.png'
                file_path = str(Path(save_folder, 'screenshots', file_name))
                try:
                    pillow_img = player.screenshot_raw()
                    pillow_img.save(file_path)
                    l1.show()
                    l1.setText2(LANG['screenshotsaved'])
                except: # pylint: disable=bare-except
                    l1.show()
                    l1.setText2(LANG['screenshotsaveerror'])
                time_stop = time.time() + 1
            else:
                l1.show()
                l1.setText2("{}!".format(LANG['nochannelselected']))
                time_stop = time.time() + 1

        def update_tvguide(chan_1='', do_return=False):
            global item_selected
            if not chan_1:
                if item_selected:
                    chan_2 = item_selected
                else:
                    chan_2 = sorted(array.items())[0][0]
            else:
                chan_2 = chan_1
            txt = LANG['notvguideforchannel']
            chan_2 = chan_2.lower()
            newline_symbol = '\n'
            if do_return:
                newline_symbol = '!@#$%^^&*('
            if chan_2 in programmes:
                txt = newline_symbol
                prog = programmes[chan_2]
                for pr in prog:
                    if pr['stop'] > time.time() - 1:
                        start_2 = datetime.datetime.fromtimestamp(
                            pr['start']
                        ).strftime('%d.%m.%y %H:%M') + ' - '
                        stop_2 = datetime.datetime.fromtimestamp(
                            pr['stop']
                        ).strftime('%d.%m.%y %H:%M') + '\n'
                        title_2 = pr['title'] if 'title' in pr else ''
                        desc_2 = ('\n' + pr['desc'] + '\n') if 'desc' in pr else ''
                        txt += start_2 + stop_2 + title_2 + desc_2 + newline_symbol
            if do_return:
                return txt
            tvguide_lbl.setText(txt)
            tvguide_lbl_2.setText(txt)
            return ''

        def show_tvguide():
            if settings['gui'] == 0:
                if tvguide_lbl.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    tvguide_lbl.hide()
                else:
                    update_tvguide()
                    tvguide_lbl.show()
            else:
                if epg_win.isVisible():
                    tvguide_lbl.setText('')
                    tvguide_lbl_2.setText('')
                    epg_win.hide()
                else:
                    update_tvguide()
                    epg_win.show()

        is_recording = False
        recording_time = 0
        record_file = None

        def start_record(ch1, url3):
            global is_recording, record_file, time_stop, recording_time
            orig_channel_name = ch1
            if not is_recording:
                is_recording = True
                lbl2.show()
                lbl2.setText(LANG['preparingrecord'])
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
                record(url3, out_file, orig_channel_name)
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
                l1.setText2(LANG['nochannelselforrecord'])

        def my_log(loglevel, component, message):
            print_with_time('[{}] {}: {}'.format(loglevel, component, message))

        if settings['hwaccel']:
            VIDEO_OUTPUT = 'gpu,vdpau,opengl,direct3d,xv,x11'
            HWACCEL = 'auto'
        else:
            VIDEO_OUTPUT = 'direct3d,xv,x11'
            HWACCEL = 'no'
        options = {
            'vo': '' if os.name == 'nt' else VIDEO_OUTPUT,
            'hwdec': HWACCEL
        }
        try:
            mpv_options_1 = settings['mpv_options']
            if "=" in mpv_options_1:
                pairs = mpv_options_1.split()
                for pair in pairs:
                    key, value = pair.split("=")
                    options[key.replace('--', '')] = value
        except Exception as e1:
            print("Could not parse MPV options!")
            print(e1)
        try:
            player = mpv.MPV(
                **options,
                wid=str(int(win.main_widget.winId())),
                ytdl=False,
                log_handler=my_log,
                loglevel='info' # debug
            )
        except: # pylint: disable=bare-except
            player = mpv.MPV(
                **options,
                wid=str(int(win.main_widget.winId())),
                log_handler=my_log,
                loglevel='info' # debug
            )
        player.osc = False
        player.script_opts = 'osc-visibility=always,osc-barmargin=50'
        if not settings['hwaccel']:
            try:
                player['x11-bypass-compositor'] = 'yes'
            except: # pylint: disable=bare-except
                pass
        try:
            player['network-timeout'] = 5
        except: # pylint: disable=bare-except
            pass

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
        mpv_override_volume(100)
        player.loop = True
        mpv_override_play(str(Path('data', 'icons', 'main.png')))

        @player.event_callback('end_file')
        def ready_handler_2(event): # pylint: disable=unused-argument
            if event['event']['error'] != 0:
                if loading.isVisible():
                    loading.setText(LANG['playerror'])
                    loading.setStyleSheet('color: red')
                    showLoading()
                    loading1.hide()
                    loading_movie.stop()

        @player.on_key_press('MBTN_RIGHT')
        def my_mouse_right():
            if playing_chan:
                mpv_play()

        @player.on_key_press('MBTN_LEFT_DBL')
        def my_leftdbl_binding():
            mpv_fullscreen()

        @player.on_key_press('MBTN_FORWARD')
        def my_forward_binding():
            next_channel()

        @player.on_key_press('MBTN_BACK')
        def my_back_binding():
            prev_channel()

        @player.on_key_press('WHEEL_UP')
        def my_up_binding():
            global l1, time_stop
            volume = int(player.volume + 1)
            if volume > 100:
                volume = 100
            label7.setValue(volume)
            mpv_volume_set()

        @player.on_key_press('WHEEL_DOWN')
        def my_down_binding():
            global l1, time_stop
            volume = int(player.volume - 1)
            if volume < 0:
                volume = 0
            time_stop = time.time() + 3
            l1.show()
            l1.setText2("{}: {}%".format(LANG['volume'], volume))
            label7.setValue(volume)
            mpv_volume_set()

        dockWidget2 = QtWidgets.QDockWidget(win)

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
            if next_row < 0:
                next_row = 0
            if next_row > win.listWidget.count() - 1:
                next_row = win.listWidget.count() - 1
            win.listWidget.setCurrentRow(next_row)
            itemClicked_event(win.listWidget.currentItem())

        def prev_channel():
            go_channel(-1)

        def next_channel():
            go_channel(1)

        def show_timeshift():
            if playing_chan:
                if player.osc:
                    player.osc = False
                else:
                    player.osc = True
            else:
                player.osc = False

        stopped = False

        # MPRIS
        mpris_loop = None
        if not os.name == 'nt':
            try:
                class MyAppAdapter(MprisAdapter): # pylint: disable=too-many-public-methods
                    def metadata(self) -> dict:
                        channel_keys = list(array.keys())
                        metadata = {
                            "mpris:trackid": "/org/astroncia/iptv/playlist/" + str(channel_keys.index(playing_chan) + 1 if playing_chan in channel_keys else 0),
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
                print(mpris_e)
                print_with_time("Failed to set up MPRIS!")

        def update_scheduler_programme():
            channel_list_2 = [chan_name for chan_name in doSort(array)]
            ch_choosed = choosechannel_ch.currentText()
            tvguide_sch.clear()
            if ch_choosed in channel_list_2:
                tvguide_got = update_tvguide(ch_choosed, True).split('!@#$%^^&*(')[2:]
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
                #starttime_w.setDateTime(QtCore.QDateTime.fromString(time.strftime('%d.%m.%Y %H:%M', time.localtime()), 'd.M.yyyy hh:mm'))
                #endtime_w.setDateTime(QtCore.QDateTime.fromString(time.strftime('%d.%m.%Y %H:%M', time.localtime(time.time() + 60)), 'd.M.yyyy hh:mm'))
                scheduler_win.show()

        label3 = QtWidgets.QPushButton()
        label3.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'pause.png'))))
        label3.setToolTip(LANG['pause'])
        label3.clicked.connect(mpv_play)
        label4 = QtWidgets.QPushButton()
        label4.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'stop.png'))))
        label4.setToolTip(LANG['stop'])
        label4.clicked.connect(mpv_stop)
        label5 = QtWidgets.QPushButton()
        label5.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'fullscreen.png'))))
        label5.setToolTip(LANG['fullscreen'])
        label5.clicked.connect(mpv_fullscreen)
        label5_0 = QtWidgets.QPushButton()
        label5_0.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'folder.png'))))
        label5_0.setToolTip(LANG['openrecordingsfolder'])
        label5_0.clicked.connect(open_recording_folder)
        label5_1 = QtWidgets.QPushButton()
        label5_1.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'record.png'))))
        label5_1.setToolTip(LANG["record"])
        label5_1.clicked.connect(do_record)
        label5_2 = QtWidgets.QPushButton()
        label5_2.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'calendar.png'))))
        label5_2.setToolTip(LANG["scheduler"])
        label5_2.clicked.connect(show_scheduler)
        label6 = QtWidgets.QPushButton()
        label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume.png'))))
        label6.setToolTip(LANG['volume'])
        label6.clicked.connect(mpv_mute)
        label7 = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        label7.setMinimum(0)
        label7.setMaximum(100)
        label7.valueChanged.connect(mpv_volume_set)
        label7.setValue(100)
        label7_1 = QtWidgets.QPushButton()
        label7_1.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'screenshot.png'))))
        label7_1.setToolTip(LANG['screenshot'])
        label7_1.clicked.connect(do_screenshot)
        label7_2 = QtWidgets.QPushButton()
        label7_2.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'timeshift.png'))))
        label7_2.setToolTip(LANG['timeshift'])
        label7_2.clicked.connect(show_timeshift)
        label8 = QtWidgets.QPushButton()
        label8.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'settings.png'))))
        label8.setToolTip(LANG['settings'])
        label8.clicked.connect(show_settings)
        label8_0 = QtWidgets.QPushButton()
        label8_0.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'tv-blue.png'))))
        label8_0.setToolTip(LANG['providers'])
        label8_0.clicked.connect(show_providers)
        label8_1 = QtWidgets.QPushButton()
        label8_1.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'tvguide.png'))))
        label8_1.setToolTip(LANG['tvguide'])
        label8_1.clicked.connect(show_tvguide)
        label8_4 = QtWidgets.QPushButton()
        label8_4.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'sort.png'))))
        label8_4.setToolTip(LANG['sort'].replace('\n', ' '))
        label8_4.clicked.connect(show_sort)
        label8_2 = QtWidgets.QPushButton()
        label8_2.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'prev.png'))))
        label8_2.setToolTip(LANG['prevchannel'])
        label8_2.clicked.connect(prev_channel)
        label8_3 = QtWidgets.QPushButton()
        label8_3.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'next.png'))))
        label8_3.setToolTip(LANG['nextchannel'])
        label8_3.clicked.connect(next_channel)
        label8_5 = QtWidgets.QPushButton()
        label8_5.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'edit.png'))))
        label8_5.setToolTip(LANG['m3u_m3ueditor'])
        label8_5.clicked.connect(show_m3u_editor)
        label9 = QtWidgets.QPushButton()
        label9.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'help.png'))))
        label9.setToolTip(LANG['help'])
        label9.clicked.connect(show_help)
        label12 = QtWidgets.QLabel('')
        label10 = QtWidgets.QLabel('© kestral / astroncia')
        label10.setAlignment(QtCore.Qt.AlignCenter)
        label10.setStyleSheet('color: #a60f46')
        label11 = QtWidgets.QLabel()
        myFont3 = QtGui.QFont()
        myFont3.setPointSize(11)
        myFont3.setBold(True)
        label11.setFont(myFont3)
        myFont4 = QtGui.QFont()
        myFont4.setPointSize(12)
        label12.setFont(myFont4)

        progress = QtWidgets.QProgressBar()
        progress.setValue(0)
        start_label = QtWidgets.QLabel()
        stop_label = QtWidgets.QLabel()

        vlayout3 = QtWidgets.QVBoxLayout()
        hlayout1 = QtWidgets.QHBoxLayout()
        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout3 = QtWidgets.QHBoxLayout()
        widget2 = QtWidgets.QWidget()
        widget2.setLayout(vlayout3)

        hlayout1.addWidget(start_label)
        hlayout1.addWidget(progress)
        hlayout1.addWidget(stop_label)

        hlayout2.addWidget(label3)
        hlayout2.addWidget(label4)
        hlayout2.addWidget(label5)
        hlayout2.addWidget(label5_1)
        hlayout2.addWidget(label5_2)
        hlayout2.addWidget(label5_0)
        hlayout2.addWidget(label6)
        hlayout2.addWidget(label7)
        hlayout2.addWidget(label7_1)
        if not os.name == 'nt':
            hlayout2.addWidget(label7_2)
        hlayout2.addWidget(label8_0)
        hlayout2.addWidget(label8)
        hlayout2.addWidget(label8_4)
        hlayout2.addWidget(label8_1)
        hlayout2.addWidget(label8_2)
        hlayout2.addWidget(label8_3)
        hlayout2.addWidget(label8_5)
        hlayout2.addWidget(label9)
        hlayout2.addStretch(100000)
        hlayout2.addWidget(label11)
        hlayout2.addWidget(label12)

        hlayout3.addWidget(label10)

        #hlayout1.addStretch(1)
        vlayout3.addLayout(hlayout2)

        hlayout2.addStretch(1)
        vlayout3.addLayout(hlayout1)

        hlayout2.addStretch(1)
        vlayout3.addLayout(hlayout3)

        dockWidget2.setWidget(widget2)
        dockWidget2.setFloating(False)
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT + 20)
        dockWidget2.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget2)

        progress.hide()
        start_label.hide()
        stop_label.hide()
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 10)

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

        def myExitHandler():
            global stopped, epg_thread, epg_thread_2, mpris_loop
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
            if manager:
                manager.shutdown()
            stop_record()

        first_boot = False
        first_boot_1 = True

        epg_thread = None
        manager = None
        epg_updating = False
        return_dict = None
        waiting_for_epg = False
        epg_failed = False

        def thread_tvguide():
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
                            static_text = LANG['tvguideupdating']
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
                                print_with_time("[TV guide, part 1] Caught exception: " + str(e1))
                                l1.setStatic2(False)
                                l1.show()
                                l1.setText2(LANG['tvguideupdatingerror'])
                                time_stop = time.time() + 3
                                epg_updating = False
                        else:
                            print_with_time("EPG update at boot disabled")
                        first_boot_1 = False
                    else:
                        programmes = {prog0.lower(): tvguide_sets[prog0] for prog0 in tvguide_sets}
                        btn_update.click() # start update in main thread

            ic += 0.1 # pylint: disable=undefined-variable
            if ic > 14.9: # redraw every 15 seconds
                ic = 0
                btn_update.click()

        def thread_record():
            global time_stop, gl_is_static, static_text, recording_time, ic1
            ic1 += 0.1  # pylint: disable=undefined-variable
            if ic1 > 0.9:
                ic1 = 0
                # executing every second
                if is_recording:
                    if not recording_time:
                        recording_time = time.time()
                    record_time = format_seconds_to_hhmmss(time.time() - recording_time)
                    if os.path.isfile(record_file):
                        record_size = convert_size(os.path.getsize(record_file))
                        lbl2.setText("REC " + record_time + " - " + record_size)
                    else:
                        recording_time = time.time()
                        lbl2.setText(LANG['recordwaiting'])
            win.update()
            if(time.time() > time_stop) and time_stop != 0:
                time_stop = 0
                if not gl_is_static:
                    l1.hide()
                    win.update()
                else:
                    l1.setText2("")

        x_conn = None

        def do_reconnect():
            global x_conn
            if (playing_chan and not loading.isVisible()) and (player.cache_buffering_state == 0):
                print_with_time("Reconnecting to stream")
                doPlay(playing_url)
            x_conn = None

        def check_connection():
            global x_conn
            try:
                if (playing_chan and not loading.isVisible()) and (player.cache_buffering_state == 0):
                    if not x_conn:
                        print_with_time("Connection to stream lost, waiting 5 secs...")
                        x_conn = QtCore.QTimer()
                        x_conn.timeout.connect(do_reconnect)
                        x_conn.start(5000)
            except: # pylint: disable=bare-except
                print_with_time("Failed to set connection loss detector!")

        def thread_check_tvguide_obsolete():
            global first_boot, ic2
            check_connection()
            try:
                if player.video_bitrate:
                    bitrate_arr = [LANG['bitrate1'], LANG['bitrate2'], LANG['bitrate3'], LANG['bitrate4'], LANG['bitrate5']]
                    video_bitrate = " - " + str(humanbytes(player.video_bitrate, bitrate_arr))
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
                label12.setText('  {}x{}{} - {} / {}'.format(width, height, video_bitrate, codec, audio_codec))
                if loading.text() == LANG['loading']:
                    hideLoading()
            else:
                label12.setText('')
            ic2 += 0.1  # pylint: disable=undefined-variable
            if ic2 > 9.9:
                ic2 = 0
                if not epg_updating:
                    if not is_program_actual(programmes):
                        force_update_epg()

        thread_4_lock = False

        def thread_tvguide_2():
            global stopped, time_stop, first_boot, programmes, btn_update, \
            epg_thread, static_text, manager, tvguide_sets, epg_updating, ic, \
            return_dict, waiting_for_epg, thread_4_lock, epg_failed, prog_ids
            if not thread_4_lock:
                thread_4_lock = True
                if waiting_for_epg and return_dict and len(return_dict) == 6:
                    try:
                        if not return_dict[3]:
                            raise return_dict[4]
                        l1.setStatic2(False)
                        l1.show()
                        l1.setText2(LANG['tvguideupdatingdone'])
                        time_stop = time.time() + 3
                        values = return_dict.values()
                        programmes = {prog0.lower(): values[1][prog0] for prog0 in values[1]}
                        if not is_program_actual(programmes):
                            raise Exception("Programme not actual")
                        prog_ids = return_dict[5]
                        tvguide_sets = programmes
                        save_tvguide_sets()
                        btn_update.click() # start update in main thread
                    except Exception as e2:
                        epg_failed = True
                        print_with_time("[TV guide, part 2] Caught exception: " + str(e2))
                        l1.setStatic2(False)
                        l1.show()
                        l1.setText2(LANG['tvguideupdatingerror'])
                        time_stop = time.time() + 3
                    epg_updating = False
                    waiting_for_epg = False
                thread_4_lock = False

        def thread_update_time():
            if label11 and clockOn:
                label11.setText('  ' + time.strftime('%H:%M:%S', time.localtime()))
            scheduler_clock.setText(get_current_time())

        def key_t():
            if dockWidget.isVisible():
                dockWidget.hide()
            else:
                dockWidget.show()

        # Key bindings
        def key_quit():
            settings_win.close()
            win.close()

        def show_clock():
            global clockOn
            clockOn = not clockOn
            thread_update_time()
            if not clockOn:
                label11.setText('')

        keybinds = {
            QtCore.Qt.Key_I: show_sort, # i - sort channels
            QtCore.Qt.Key_T: key_t,
            QtCore.Qt.Key_Escape: esc_handler, # escape key
            QtCore.Qt.Key_F: mpv_fullscreen, # f - fullscreen
            QtCore.Qt.Key_F11: mpv_fullscreen,
            QtCore.Qt.Key_M: mpv_mute, # m - mute
            QtCore.Qt.Key_Q: key_quit, # q - quit
            QtCore.Qt.Key_Space: mpv_play, # space - pause
            QtCore.Qt.Key_MediaTogglePlayPause: mpv_play,
            QtCore.Qt.Key_MediaPlay: mpv_play,
            QtCore.Qt.Key_MediaPause: mpv_play,
            QtCore.Qt.Key_Play: mpv_play,
            QtCore.Qt.Key_S: mpv_stop, # s - stop
            QtCore.Qt.Key_Stop: mpv_stop,
            QtCore.Qt.Key_MediaStop: mpv_stop,
            QtCore.Qt.Key_H: do_screenshot, # h - screenshot
            QtCore.Qt.Key_G: show_tvguide, # g - tv guide
            QtCore.Qt.Key_R: do_record, # r - record
            QtCore.Qt.Key_MediaRecord: do_record,
            QtCore.Qt.Key_P: prev_channel, # p - prev channel
            QtCore.Qt.Key_MediaPrevious: prev_channel,
            QtCore.Qt.Key_N: next_channel, # n - next channel
            QtCore.Qt.Key_MediaNext: next_channel,
            QtCore.Qt.Key_O: show_clock, # o - show/hide clock
            QtCore.Qt.Key_VolumeUp: my_up_binding,
            QtCore.Qt.Key_VolumeDown: my_down_binding,
            QtCore.Qt.Key_VolumeMute: mpv_mute,
            QtCore.Qt.Key_E: show_timeshift, # e - show timeshift
            QtCore.Qt.Key_D: show_scheduler # d - record scheduler
        }
        for keybind in keybinds:
            QtWidgets.QShortcut(QtGui.QKeySequence(keybind), win).activated.connect(keybinds[keybind])

        app.aboutToQuit.connect(myExitHandler)

        if settings['m3u'] and m3u:
            win.show()
            win.raise_()
            win.setFocus(QtCore.Qt.PopupFocusReason)
            win.activateWindow()

            ic, ic1, ic2 = 0, 0, 0
            timers_array = {}
            timers = {
                thread_tvguide: 100,
                thread_record: 100,
                thread_check_tvguide_obsolete: 100,
                thread_tvguide_2: 1000,
                thread_update_time: 1000,
                record_thread: 1000,
                record_thread_2: 1000
            }
            for timer in timers:
                timers_array[timer] = QtCore.QTimer()
                timers_array[timer].timeout.connect(timer)
                timers_array[timer].start(timers[timer])
        else:
            settings_win.show()
            settings_win.raise_()
            settings_win.setFocus(QtCore.Qt.PopupFocusReason)
            settings_win.activateWindow()

        sys.exit(app.exec_())
    except Exception as e3:
        show_exception(e3)
        sys.exit(1)
