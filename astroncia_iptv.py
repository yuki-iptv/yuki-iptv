#!/usr/bin/env python3
'''Astroncia IPTV - Cross platform IPTV player'''
# pylint: disable=invalid-name, global-statement, missing-docstring, wrong-import-position, c-extension-no-member, too-many-lines, too-many-statements, broad-except, line-too-long
#
# Icons by Font Awesome ( https://fontawesome.com/ )
#
# The Font Awesome pictograms are licensed under the CC BY 3.0 License - http://creativecommons.org/licenses/by/3.0/
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
import codecs
import ctypes
import webbrowser
from tkinter import Tk, messagebox
from multiprocessing import Process, Manager, freeze_support
freeze_support()
import requests
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import QtGui
from data.modules.astroncia.lang import lang
from data.modules.astroncia.ua import user_agent, uas
from data.modules.astroncia.m3u import M3uParser
from data.modules.astroncia.epg import worker
from data.modules.astroncia.record import record, stop_record
from data.modules.astroncia.format import format_seconds_to_hhmmss
from data.modules.astroncia.conversion import convert_size
from data.modules.astroncia.providers import iptv_providers
from data.modules.astroncia.time import print_with_time
from data.modules.astroncia.epgurls import EPG_URLS
from data.modules.astroncia.bitrate import humanbytes
from data.modules.astroncia.selectionmodel import ReorderableListModel, SelectionModel

APP_VERSION = '0.0.13'

if not sys.version_info >= (3, 4, 0):
    print_with_time("Incompatible Python version! Required >= 3.4")
    sys.exit(1)

if not (os.name == 'nt' or os.name == 'posix'):
    print_with_time("Unsupported platform!")
    sys.exit(1)

WINDOW_SIZE = (1200, 600)
DOCK_WIDGET2_HEIGHT = int(WINDOW_SIZE[1] / 6)
DOCK_WIDGET_WIDTH = int((WINDOW_SIZE[0] / 2) - 200)
TVGUIDE_WIDTH = int((WINDOW_SIZE[0] / 5))
BCOLOR = "#A2A3A3"

if DOCK_WIDGET2_HEIGHT < 0:
    DOCK_WIDGET2_HEIGHT = 0

if DOCK_WIDGET_WIDTH < 0:
    DOCK_WIDGET_WIDTH = 0

parser = argparse.ArgumentParser(description='Astroncia IPTV')
parser.add_argument('--python')
args1 = parser.parse_args()

LOCAL_DIR = 'local'
SAVE_FOLDER_DEFAULT = str(Path(os.path.dirname(os.path.abspath(__file__)), 'AstronciaIPTV_saves'))

if os.path.isfile(str(Path(os.path.dirname(os.path.abspath(__file__)), 'libxcb.so.1'))) or os.path.isfile(str(Path(os.path.dirname(os.path.abspath(__file__)), 'INSIDE_DEB'))):
    LOCAL_DIR = str(Path(os.environ['HOME'], '.AstronciaIPTV'))
    SAVE_FOLDER_DEFAULT = str(Path(os.environ['HOME'], '.AstronciaIPTV', 'saves'))
    if not os.path.isdir(LOCAL_DIR):
        os.mkdir(LOCAL_DIR)
    if not os.path.isdir(SAVE_FOLDER_DEFAULT):
        os.mkdir(SAVE_FOLDER_DEFAULT)

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
    settings_file0 = open(str(Path(LOCAL_DIR, 'settings.json')), 'r')
    settings_lang0 = json.loads(settings_file0.read())['lang']
    settings_file0.close()
except: # pylint: disable=bare-except
    settings_lang0 = LANG_DEFAULT

LANG = lang[settings_lang0]['strings'] if settings_lang0 in lang else lang[LANG_DEFAULT]['strings']
LANG_NAME = lang[settings_lang0]['name'] if settings_lang0 in lang else lang[LANG_DEFAULT]['name']
print_with_time("Settings locale: {}\n".format(LANG_NAME))

def show_exception(e):
    window = Tk()
    window.wm_withdraw()
    messagebox.showinfo(title=LANG['error'], message="{}\n\n{}".format(LANG['error2'], str(e)))
    window.destroy()

if os.name == 'nt':
    a0 = sys.executable
    if args1.python:
        a0 = args1.python
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(Path(os.path.dirname(a0), 'Lib', 'site-packages', 'PyQt5', 'Qt5', 'plugins'))

if __name__ == '__main__':
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
            from data.modules import mpv
        except: # pylint: disable=bare-except
            print_with_time("Falling back to old mpv library...")
            from data.modules import mpv_old as mpv

        if not os.path.isdir(LOCAL_DIR):
            os.mkdir(LOCAL_DIR)

        channel_sets = {}
        prog_ids = {}
        def save_channel_sets():
            global channel_sets
            file2 = open(str(Path(LOCAL_DIR, 'channels.json')), 'w')
            file2.write(json.dumps(channel_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, 'channels.json'))):
            save_channel_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, 'channels.json')), 'r')
            channel_sets = json.loads(file1.read())
            file1.close()

        favourite_sets = []
        def save_favourite_sets():
            global favourite_sets
            file2 = open(str(Path(LOCAL_DIR, 'favourites.json')), 'w')
            file2.write(json.dumps(favourite_sets))
            file2.close()

        if not os.path.isfile(str(Path(LOCAL_DIR, 'favourites.json'))):
            save_favourite_sets()
        else:
            file1 = open(str(Path(LOCAL_DIR, 'favourites.json')), 'r')
            favourite_sets = json.loads(file1.read())
            file1.close()

        if os.path.isfile(str(Path(LOCAL_DIR, 'settings.json'))):
            settings_file = open(str(Path(LOCAL_DIR, 'settings.json')), 'r')
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
                "nocache": False,
                "lang": LANG_DEFAULT,
                "offset": 0,
                "hwaccel": True,
                "sort": 0,
                "cache_secs": 1
            }
            m3u = ""
        if 'hwaccel' not in settings:
            settings['hwaccel'] = True
        if 'sort' not in settings:
            settings['sort'] = 0
        if 'cache_secs' not in settings:
            settings['cache_secs'] = 1
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
                    cm3uf1 = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r')
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
            pj = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r')
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
                    file = open(settings['m3u'], 'r')
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
                cm3uf = open(str(Path(LOCAL_DIR, 'playlist.json')), 'w')
                cm3uf.write(cm3u)
                cm3uf.close()
                print_with_time(LANG['playlistcached'])
        else:
            print_with_time(LANG['usingcachedplaylist'])
            cm3uf = open(str(Path(LOCAL_DIR, 'playlist.json')), 'r')
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

        if LANG['allchannels'] in groups:
            groups.remove(LANG['allchannels'])
        groups = [LANG['allchannels'], LANG['favourite']] + groups

        if os.path.isfile(str(Path('data', 'channel_icons.json'))):
            icons_file = open(str(Path('data', 'channel_icons.json')), 'r')
            icons = json.loads(icons_file.read())
            icons_file.close()
        else:
            icons = {}

        def sigint_handler(*args): # pylint: disable=unused-argument
            """Handler for the SIGINT signal."""
            app.quit()

        signal.signal(signal.SIGINT, sigint_handler)

        timer = QtCore.QTimer()
        timer.start(500)
        timer.timeout.connect(lambda: None)

        TV_ICON = QtGui.QIcon(str(Path('data', 'icons', 'tv.png')))
        ICONS_CACHE = {}

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

        time_stop = 0

        qr = settings_win.frameGeometry()
        qr.moveCenter(QtWidgets.QDesktopWidget().availableGeometry().center())
        settings_win_l = qr.topLeft()
        origY = settings_win_l.y() - 60
        settings_win_l.setY(origY)
        settings_win.move(settings_win_l)
        help_win.move(qr.topLeft())
        sort_win.move(qr.topLeft())
        chan_win.move(qr.topLeft())

        def save_sort():
            global channel_sort
            channel_sort = model.getNodes()
            file4 = open(str(Path(LOCAL_DIR, 'sort.json')), 'w')
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
        deinterlace_chk = QtWidgets.QCheckBox()
        useragent_choose = QtWidgets.QComboBox()
        useragent_choose.addItem(LANG['empty'])
        useragent_choose.addItem('Windows Browser')
        useragent_choose.addItem('Android')
        useragent_choose.addItem('iPhone')
        useragent_choose.addItem('Linux Browser')

        def hideLoading():
            loading.hide()
            loading_movie.stop()
            loading1.hide()

        def showLoading():
            loading.show()
            loading_movie.start()
            loading1.show()

        def stopPlayer():
            try:
                player.stop()
            except: # pylint: disable=bare-except
                player.loop = True
                player.play(str(Path('data', 'icons', 'main.png')))

        def doPlay(play_url1, ua_ch=user_agent):
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
            print_with_time("Using user-agent: {}".format(ua_ch))
            player.user_agent = ua_ch
            player.loop = True
            player.play(play_url1)

        def chan_set_save():
            chan_3 = title.text().replace("{}: ".format(LANG['channel']), "")
            channel_sets[chan_3] = {
                "deinterlace": deinterlace_chk.isChecked(),
                "useragent": useragent_choose.currentIndex()
            }
            save_channel_sets()
            if playing_chan == chan_3:
                player.deinterlace = deinterlace_chk.isChecked()
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

        horizontalLayout3 = QtWidgets.QHBoxLayout()
        horizontalLayout3.addWidget(save_btn)

        verticalLayout = QtWidgets.QVBoxLayout(wid)
        verticalLayout.addLayout(horizontalLayout)
        verticalLayout.addLayout(horizontalLayout2)
        verticalLayout.addLayout(horizontalLayout2_1)
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
            if settings["offset"] != soffset.value():
                if os.path.isfile(str(Path(LOCAL_DIR, 'tvguide.dat'))):
                    os.remove(str(Path(LOCAL_DIR, 'tvguide.dat')))
            if sort_widget.currentIndex() != settings['sort']:
                if os.path.isfile(str(Path(LOCAL_DIR, 'playlist.json'))):
                    os.remove(str(Path(LOCAL_DIR, 'playlist.json')))
            lang1 = LANG_DEFAULT
            for lng1 in lang:
                if lang[lng1]['name'] == slang.currentText():
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
                "offset": soffset.value(),
                "hwaccel": shwaccel.isChecked(),
                "sort": sort_widget.currentIndex(),
                "cache_secs": scache1.value()
            }
            settings_file1 = open(str(Path(LOCAL_DIR, 'settings.json')), 'w')
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
        for sortI in LANG['sortitems']:
            sort_widget.addItem(sortI)
        sort_widget.setCurrentIndex(settings['sort'])
        sprov = QtWidgets.QComboBox()
        slang = QtWidgets.QComboBox()
        lng0 = -1
        for lng in lang:
            lng0 += 1
            slang.addItem(lang[lng]['name'])
            if lang[lng]['name'] == LANG_NAME:
                slang.setCurrentIndex(lng0)
        def close_settings():
            settings_win.hide()
            if not win.isVisible():
                sys.exit(0)
        def prov_select(self): # pylint: disable=unused-argument
            prov1 = sprov.currentText()
            if prov1 != '--{}--'.format(LANG['notselected']):
                sm3u.setText(iptv_providers[prov1]['m3u'])
                sepg.setText(iptv_providers[prov1]['epg'])
        sprov.currentIndexChanged.connect(prov_select)
        sprov.addItem('--{}--'.format(LANG['notselected']))
        provs = {}
        ic3 = 0
        for prov in iptv_providers:
            ic3 += 1
            provs[prov] = ic3
            sprov.addItem(prov)
        if settings['provider']:
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

        sepgfile = QtWidgets.QPushButton(settings_win)
        sepgfile.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        sepgfile.clicked.connect(epg_select)
        sepgupd = QtWidgets.QPushButton(settings_win)
        sepgupd.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'update.png'))))
        sepgupd.clicked.connect(force_update_epg)

        sfolder = QtWidgets.QPushButton(settings_win)
        sfolder.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'file.png'))))
        sfolder.clicked.connect(save_folder_select)

        soffset = QtWidgets.QSpinBox()
        soffset.setMinimum(-240)
        soffset.setMaximum(240)
        soffset.setValue(settings["offset"])

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
        sframe9 = QtWidgets.QFrame()
        sframe9.setFrameShape(QtWidgets.QFrame.HLine)
        sframe9.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe10 = QtWidgets.QFrame()
        sframe10.setFrameShape(QtWidgets.QFrame.HLine)
        sframe10.setFrameShadow(QtWidgets.QFrame.Raised)
        sframe11 = QtWidgets.QFrame()
        sframe11.setFrameShape(QtWidgets.QFrame.HLine)
        sframe11.setFrameShadow(QtWidgets.QFrame.Raised)

        morebtn = QtWidgets.QPushButton(LANG["moresettings"])

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

        grid.addWidget(sselect, 6, 1)
        grid.addWidget(sprov, 7, 1)

        grid.addWidget(sframe4, 8, 0)
        grid.addWidget(sframe5, 8, 1)
        grid.addWidget(sframe6, 8, 2)
        grid.addWidget(sframe7, 8, 3)

        grid.addWidget(morebtn, 9, 1)

        grid.addWidget(sframe8, 10, 0)
        grid.addWidget(sframe9, 10, 1)
        grid.addWidget(sframe10, 10, 2)
        grid.addWidget(sframe11, 10, 3)

        grid.addWidget(lang_label, 11, 0)
        grid.addWidget(slang, 11, 1)

        grid.addWidget(fld_label, 12, 0)
        grid.addWidget(sfld, 12, 1)
        grid.addWidget(sfolder, 12, 2)

        grid.addWidget(udp_label, 13, 0)
        grid.addWidget(sudp, 13, 1)

        grid.addWidget(dei_label, 14, 0)
        grid.addWidget(sdei, 14, 1)

        grid.addWidget(hwaccel_label, 15, 0)
        grid.addWidget(shwaccel, 15, 1)

        grid.addWidget(cache_label, 16, 0)
        grid.addWidget(scache1, 16, 1)
        grid.addWidget(scache, 16, 2)

        grid.addWidget(sort_label, 17, 0)
        grid.addWidget(sort_widget, 17, 1)

        grid.addWidget(ssave, 18, 1)
        grid.addWidget(sreset, 19, 1)
        grid.addWidget(sclose, 20, 1)
        wid2.setLayout(grid)
        settings_win.setCentralWidget(wid2)


        lbls = [lang_label, slang, fld_label, sfld, sfolder, udp_label, sudp, dei_label, sdei, hwaccel_label, shwaccel, cache_label, scache1, scache, sort_label, sort_widget]
        def hideMoreSettings():
            morebtn.setText(LANG["moresettings"])
            global lbls
            for lbl in lbls:
                lbl.hide()
            settings_win.setMaximumSize(400, 200)
            settings_win.resize(400, 200)
            settings_win_l.setY(origY)
            settings_win.move(settings_win_l)

        def showMoreSettings():
            morebtn.setText(LANG["lesssettings"])
            global lbls
            for lbl in lbls:
                lbl.show()
            settings_win.setMaximumSize(597, 619)
            settings_win.resize(597, 619)
            settings_win_l.setY(0)
            settings_win.move(settings_win_l)

        def more_settings():
            if lbls[0].isVisible():
                hideMoreSettings()
            else:
                showMoreSettings()
        morebtn.clicked.connect(more_settings)
        hideMoreSettings()

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
                    lbl2.move(0, 35)
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
        win.setWindowTitle('Astroncia IPTV')
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

        chan = QtWidgets.QLabel(LANG['nochannelselected'], win)
        chan.setAlignment(QtCore.Qt.AlignCenter)
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
        lbl2.move(0, 35)
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

        def itemClicked_event(item):
            global playing, playing_chan, item_selected, playing_url
            j = item.data(QtCore.Qt.UserRole)
            playing_chan = j
            item_selected = j
            play_url = array[j]['url']
            chan.setText('  ' + j)
            current_prog = None
            if settings['epg'] and j in programmes:
                for pr in programmes[j]:
                    if time.time() > pr['start'] and time.time() < pr['stop']:
                        current_prog = pr
                        break
            show_progress(current_prog)
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT)
            playing = True
            win.update()
            playing_url = play_url
            ua_choose = user_agent
            if j in channel_sets:
                d = channel_sets[j]
                player.deinterlace = d['deinterlace']
                if not 'useragent' in d:
                    d['useragent'] = 0
                try:
                    d['useragent'] = uas[d['useragent']]
                except: # pylint: disable=bare-except
                    pass
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
                player.pause = False
            else:
                label3.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'play.png'))))
                label3.setToolTip(LANG['play'])
                player.pause = True

        def mpv_stop():
            global playing, playing_chan, playing_url
            playing_chan = ''
            playing_url = ''
            hideLoading()
            chan.setText('')
            playing = False
            stopPlayer()
            player.loop = True
            player.play(str(Path('data', 'icons', 'main.png')))
            chan.setText(LANG['nochannelselected'])
            progress.hide()
            start_label.hide()
            stop_label.hide()
            dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 30)
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
                dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 30)
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
                    dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT)
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
                player.mute = False
                label7.setValue(old_value)
                l1.setText2("{}: {}%".format(LANG['volume'], int(old_value)))
            else:
                label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'mute.png'))))
                player.mute = True
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
            player.volume = vol
            if vol == 0:
                player.mute = True
                label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'mute.png'))))
            else:
                player.mute = False
                if vol > 50:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume.png'))))
                else:
                    label6.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'volume-low.png'))))

        dockWidget = QtWidgets.QDockWidget(win)
        win.listWidget = QtWidgets.QListWidget()

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
                self.progressBar.setFormat('')
                self.progressBar.setValue(progress_val)

        current_group = LANG['allchannels']

        channel_sort = {}
        if os.path.isfile(str(Path(LOCAL_DIR, 'sort.json'))):
            file3 = open(str(Path(LOCAL_DIR, 'sort.json')), 'r')
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

        def gen_chans(): # pylint: disable=too-many-locals, too-many-branches
            global ICONS_CACHE, playing_chan, current_group, array
            ch_array = array
            res = {}
            l = -1
            k = 0
            for i in doSort(ch_array):
                group1 = array[i]['tvg-group']
                if current_group != LANG['allchannels']:
                    if current_group == LANG['favourite']:
                        if not i in favourite_sets:
                            continue
                    else:
                        if group1 != current_group:
                            continue
                l += 1
                k += 1
                prog = ''
                prog_search = i
                if array[i]['tvg-ID']:
                    if str(array[i]['tvg-ID']) in prog_ids:
                        prog_search_lst = prog_ids[str(array[i]['tvg-ID'])]
                        if prog_search_lst:
                            prog_search = prog_search_lst[0]
                if array[i]['tvg-name']:
                    if str(array[i]['tvg-name']) in programmes:
                        prog_search = str(array[i]['tvg-name'])
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
                myQCustomQWidget = QCustomQWidget()
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
                if i in icons:
                    if not icons[i] in ICONS_CACHE:
                        ICONS_CACHE[icons[i]] = QtGui.QIcon(str(Path('data', 'channel_icons', icons[i])))
                    myQCustomQWidget.setIcon(ICONS_CACHE[icons[i]])
                else:
                    myQCustomQWidget.setIcon(TV_ICON)
                # Create QListWidgetItem
                myQListWidgetItem = QtWidgets.QListWidgetItem()
                myQListWidgetItem.setData(QtCore.Qt.UserRole, i)
                # Set size hint
                myQListWidgetItem.setSizeHint(myQCustomQWidget.sizeHint())
                res[l] = [myQListWidgetItem, myQCustomQWidget, l, i]
            if playing_chan:
                current_chan = None
                try:
                    cur = programmes[playing_chan]
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
            global row0
            update_tvguide()
            row0 = win.listWidget.currentRow()
            val0 = win.listWidget.verticalScrollBar().value()
            win.listWidget.clear()
            channels_1 = gen_chans()
            for channel_1 in channels_1:
                filter_txt = channelfilter.text()
                c_name = channels_1[channel_1][3]
                # Add QListWidgetItem into QListWidget
                if filter_txt.lower().strip() in c_name.lower():
                    win.listWidget.addItem(channels_1[channel_1][0])
                    win.listWidget.setItemWidget(channels_1[channel_1][0], channels_1[channel_1][1])
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
                    pass
            else:
                deinterlace_chk.setChecked(True)
                useragent_choose.setCurrentIndex(0)
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
            redraw_chans()
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
        channelfilter.textChanged.connect(channelfilter_do)
        layout = QtWidgets.QGridLayout()
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)
        widget.layout().addWidget(combobox)
        widget.layout().addWidget(channelfilter)
        widget.layout().addWidget(win.listWidget)
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

        def update_tvguide(chan_1=''):
            global item_selected
            if not chan_1:
                if item_selected:
                    chan_2 = item_selected
                else:
                    chan_2 = sorted(array.items())[0][0]
            else:
                chan_2 = chan_1
            txt = LANG['notvguideforchannel']
            if chan_2 in programmes:
                txt = '\n'
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
                        txt += start_2 + stop_2 + title_2 + desc_2 + '\n'
            tvguide_lbl.setText(txt)

        def show_tvguide():
            if tvguide_lbl.isVisible():
                tvguide_lbl.setText('')
                tvguide_lbl.hide()
            else:
                update_tvguide()
                tvguide_lbl.show()

        is_recording = False
        recording_time = 0
        record_file = None

        def start_record(ch1, url3):
            global is_recording, record_file, time_stop, recording_time
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
                record(url3, out_file)
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
            VIDEO_OUTPUT = 'gpu,direct3d,xv,x11'
            HWACCEL = True
        else:
            VIDEO_OUTPUT = 'direct3d,xv,x11'
            HWACCEL = False
        try:
            player = mpv.MPV(
                wid=str(int(win.main_widget.winId())),
                ytdl=False,
                vo='' if os.name == 'nt' else VIDEO_OUTPUT,
                hwdec=HWACCEL,
                log_handler=my_log,
                loglevel='info' # debug
            )
        except: # pylint: disable=bare-except
            player = mpv.MPV(
                wid=str(int(win.main_widget.winId())),
                vo='' if os.name == 'nt' else VIDEO_OUTPUT,
                hwdec=HWACCEL,
                log_handler=my_log,
                loglevel='info' # debug
            )
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
                player['cache-secs'] = settings["cache_secs"]
                print_with_time('Cache set to {}s'.format(settings["cache_secs"]))
            except: # pylint: disable=bare-except
                pass
        else:
            print_with_time("Using default cache settings")
        player.user_agent = user_agent
        player.volume = 100
        player.loop = True
        player.play(str(Path('data', 'icons', 'main.png')))

        @player.event_callback('end_file')
        def ready_handler_2(event): # pylint: disable=unused-argument
            if event['event']['error'] != 0:
                if loading.isVisible():
                    loading.setText(LANG['playerror'])
                    loading.setStyleSheet('color: red')
                    showLoading()
                    loading1.hide()
                    loading_movie.stop()

        @player.on_key_press('MBTN_LEFT_DBL')
        def my_leftdbl_binding():
            mpv_fullscreen()

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
                subprocess.Popen(['xdg-open', str(absolute_path)])

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
        label8 = QtWidgets.QPushButton()
        label8.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'settings.png'))))
        label8.setToolTip(LANG['settings'])
        label8.clicked.connect(show_settings)
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
        label9 = QtWidgets.QPushButton()
        label9.setIcon(QtGui.QIcon(str(Path('data', 'icons', 'help.png'))))
        label9.setToolTip(LANG['help'])
        label9.clicked.connect(show_help)
        label12 = QtWidgets.QLabel('')
        label10 = QtWidgets.QLabel('  (c) kestral / astroncia')
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
        widget2 = QtWidgets.QWidget()
        widget2.setLayout(vlayout3)

        hlayout1.addWidget(start_label)
        hlayout1.addWidget(progress)
        hlayout1.addWidget(stop_label)

        hlayout2.addWidget(label3)
        hlayout2.addWidget(label4)
        hlayout2.addWidget(label5)
        hlayout2.addWidget(label5_1)
        hlayout2.addWidget(label5_0)
        hlayout2.addWidget(label6)
        hlayout2.addWidget(label7)
        hlayout2.addWidget(label7_1)
        hlayout2.addWidget(label8)
        hlayout2.addWidget(label8_4)
        hlayout2.addWidget(label8_1)
        hlayout2.addWidget(label8_2)
        hlayout2.addWidget(label8_3)
        hlayout2.addWidget(label9)
        hlayout2.addWidget(label11)
        hlayout2.addWidget(label10)
        hlayout2.addWidget(label12)

        #hlayout1.addStretch(1)
        vlayout3.addLayout(hlayout1)

        hlayout2.addStretch(1)
        vlayout3.addLayout(hlayout2)

        dockWidget2.setWidget(widget2)
        dockWidget2.setFloating(False)
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT)
        dockWidget2.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
        win.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dockWidget2)

        progress.hide()
        start_label.hide()
        stop_label.hide()
        dockWidget2.setFixedHeight(DOCK_WIDGET2_HEIGHT - 30)

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

        stopped = False

        def myExitHandler():
            global stopped, epg_thread, epg_thread_2
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

        epg_thread = None
        manager = None
        epg_updating = False
        return_dict = None
        waiting_for_epg = False
        epg_failed = False

        def thread_tvguide():
            global stopped, time_stop, first_boot, programmes, btn_update, \
            epg_thread, static_text, manager, tvguide_sets, epg_updating, ic, \
            return_dict, waiting_for_epg, epg_failed
            if not first_boot:
                first_boot = True
                if settings['epg'] and not epg_failed:
                    if not use_local_tvguide:
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
                        programmes = tvguide_sets
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
                    video_bitrate = " - " + str(humanbytes(player.video_bitrate, LANG['bitrates']))
                else:
                    video_bitrate = ""
            except: # pylint: disable=bare-except
                video_bitrate = ""
            try:
                audio_codec = player.audio_codec.split(" ")[0]
            except: # pylint: disable=bare-except
                audio_codec = 'audio'
            try:
                codec = player.video_codec.split(" ")[0]
                width = player.width
                height = player.height
            except: # pylint: disable=bare-except
                codec = 'png'
                width = 800
                height = 600
            if (not (codec == 'png' and width == 800 and height == 600)) and (width and height):
                label12.setText('    {}x{}{} - {} / {}'.format(width, height, video_bitrate, codec, audio_codec))
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
                        programmes = values[1]
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

        def key_t():
            if dockWidget.isVisible():
                dockWidget.hide()
            else:
                dockWidget.show()

        # Key bindings
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_I), win).activated.connect(show_sort) # i - sort channels
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_T), win).activated.connect(key_t)
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), win).activated.connect(esc_handler) # escape key
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_F), win).activated.connect(mpv_fullscreen) # f - fullscreen
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_M), win).activated.connect(mpv_mute) # m - mute

        def key_quit():
            settings_win.close()
            win.close()

        def show_clock():
            global clockOn
            clockOn = not clockOn
            thread_update_time()
            if not clockOn:
                label11.setText('')

        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Q), win).activated.connect(key_quit) # q - quit
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), win).activated.connect(mpv_play) # space - pause
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_S), win).activated.connect(mpv_stop) # s - stop
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_H), win).activated.connect(do_screenshot) # h - screenshot
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_G), win).activated.connect(show_tvguide) # g - tv guide
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_R), win).activated.connect(do_record) # r - record
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_P), win).activated.connect(prev_channel) # p - prev channel
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_N), win).activated.connect(next_channel) # n - next channel
        QtWidgets.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_O), win).activated.connect(show_clock) # o - show/hide clock

        app.aboutToQuit.connect(myExitHandler)

        if settings['m3u'] and m3u:
            win.show()
            win.raise_()
            win.setFocus(QtCore.Qt.PopupFocusReason)
            win.activateWindow()

            ic = 0
            x = QtCore.QTimer()
            x.timeout.connect(thread_tvguide)
            x.start(100)

            ic1 = 0
            x2 = QtCore.QTimer()
            x2.timeout.connect(thread_record)
            x2.start(100)

            ic2 = 0
            x3 = QtCore.QTimer()
            x3.timeout.connect(thread_check_tvguide_obsolete)
            x3.start(100)

            x4 = QtCore.QTimer()
            x4.timeout.connect(thread_tvguide_2)
            x4.start(1000)

            x5 = QtCore.QTimer()
            x5.timeout.connect(thread_update_time)
            x5.start(1000)
        else:
            settings_win.show()
            settings_win.raise_()
            settings_win.setFocus(QtCore.Qt.PopupFocusReason)
            settings_win.activateWindow()

        sys.exit(app.exec_())
    except Exception as e3:
        show_exception(e3)
        sys.exit(1)
