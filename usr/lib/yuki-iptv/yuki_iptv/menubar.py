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
import os
import logging
import gettext
import json
import traceback
from functools import partial
from yuki_iptv.qt import get_qt_library
from yuki_iptv.qt6compat import qaction
from yuki_iptv.options import read_option

qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()
logger = logging.getLogger(__name__)
_ = gettext.gettext


class YukiData:
    menubar_ready = False
    first_run = False
    first_run1 = False
    menubars = {}
    data = {}
    cur_vf_filters = []
    keyboard_sequences = []
    if qt_library == "PyQt6":
        str_offset = " " * 44
    else:
        str_offset = ""


def ast_mpv_seek(secs):
    logger.info(f"Seeking to {secs} seconds")
    YukiData.player.command("seek", secs)


def ast_mpv_speed(spd):
    logger.info(f"Set speed to {spd}")
    YukiData.player.speed = spd


def yuki_trackset(track, type1):
    YukiData.yuki_track_set(track, type1)
    YukiData.redraw_menubar()


def send_mpv_command(name, act, cmd):
    if cmd == "__AST_VFBLACK__":
        cur_window_pos = YukiData.get_curwindow_pos()
        cmd = (
            f"lavfi=[pad=iw:iw*sar/{cur_window_pos[0]}*{cur_window_pos[1]}:0:(oh-ih)/2]"
        )
    if cmd == "__AST_SOFTSCALING__":
        cur_window_pos = YukiData.get_curwindow_pos()
        cmd = f"lavfi=[scale={cur_window_pos[0]}:-2]"
    logger.info(f'Sending mpv command: "{name} {act} \\"{cmd}\\""')
    YukiData.player.command(name, act, cmd)


def get_active_vf_filters():
    return YukiData.cur_vf_filters


def apply_vf_filter(vf_filter, e_l):
    try:
        if e_l.isChecked():
            send_mpv_command(
                vf_filter.split("::::::::")[0], "add", vf_filter.split("::::::::")[1]
            )
            YukiData.cur_vf_filters.append(vf_filter)
        else:
            send_mpv_command(
                vf_filter.split("::::::::")[0], "remove", vf_filter.split("::::::::")[1]
            )
            YukiData.cur_vf_filters.remove(vf_filter)
    except Exception as e_4:
        logger.error("ERROR in vf-filter apply")
        logger.error("")
        e4_traceback = traceback.format_exc()
        logger.error(e4_traceback)
        YukiData.show_exception(e_4, e4_traceback, "\n\n" + _("Error applying filters"))


def get_seq():
    return YukiData.keyboard_sequences


def qkeysequence(seq):
    s_e = QtGui.QKeySequence(seq)
    YukiData.keyboard_sequences.append(s_e)
    return s_e


def kbd(k_1):
    return qkeysequence(YukiData.get_keybind(k_1))


def alwaysontop_action():
    try:
        aot_f = open(YukiData.aot_file, "w", encoding="utf-8")
        aot_f.write(json.dumps({"alwaysontop": YukiData.alwaysontopAction.isChecked()}))
        aot_f.close()
    except Exception:
        pass
    if YukiData.alwaysontopAction.isChecked():
        logger.info("Always on top enabled now")
        YukiData.enable_always_on_top()
    else:
        logger.info("Always on top disabled now")
        YukiData.disable_always_on_top()


def reload_menubar_shortcuts():
    YukiData.playlists.setShortcut(kbd("show_playlists"))
    YukiData.reloadPlaylist.setShortcut(kbd("reload_playlist"))
    YukiData.m3uEditor.setShortcut(kbd("show_m3u_editor"))
    YukiData.exitAction.setShortcut(kbd("app.quit"))
    YukiData.playpause.setShortcut(kbd("mpv_play"))
    YukiData.stop.setShortcut(kbd("mpv_stop"))
    YukiData.normalSpeed.setShortcut(kbd("(lambda: set_playback_speed(1.00))"))
    YukiData.prevchannel.setShortcut(kbd("prev_channel"))
    YukiData.nextchannel.setShortcut(kbd("next_channel"))
    YukiData.fullscreen.setShortcut(kbd("mpv_fullscreen"))
    YukiData.compactmode.setShortcut(kbd("showhideeverything"))
    YukiData.csforchannel.setShortcut(kbd("main_channel_settings"))
    YukiData.screenshot.setShortcut(kbd("do_screenshot"))
    YukiData.muteAction.setShortcut(kbd("mpv_mute"))
    YukiData.volumeMinus.setShortcut(kbd("my_down_binding_execute"))
    YukiData.volumePlus.setShortcut(kbd("my_up_binding_execute"))
    YukiData.showhideplaylistAction.setShortcut(kbd("key_t"))
    YukiData.showhidectrlpanelAction.setShortcut(kbd("lowpanel_ch_1"))
    YukiData.alwaysontopAction.setShortcut(kbd("alwaysontop"))
    YukiData.streaminformationAction.setShortcut(kbd("open_stream_info"))
    YukiData.showepgAction.setShortcut(kbd("show_tvguide_2"))
    YukiData.forceupdateepgAction.setShortcut(kbd("force_update_epg"))
    YukiData.sortAction.setShortcut(kbd("show_sort"))
    YukiData.settingsAction.setShortcut(kbd("show_settings"))
    sec_keys_1 = [
        kbd("(lambda: mpv_seek(-10))"),
        kbd("(lambda: mpv_seek(10))"),
        kbd("(lambda: mpv_seek(-60))"),
        kbd("(lambda: mpv_seek(60))"),
        kbd("(lambda: mpv_seek(-600))"),
        kbd("(lambda: mpv_seek(600))"),
    ]
    sec_i_1 = -1
    for i_1 in YukiData.secs:
        sec_i_1 += 1
        i_1.setShortcut(qkeysequence(sec_keys_1[sec_i_1]))


def init_menubar(data):
    # File

    YukiData.playlists = qaction(_("&Playlists"), data)
    YukiData.playlists.setShortcut(kbd("show_playlists"))
    YukiData.playlists.triggered.connect(lambda: YukiData.show_playlists())

    YukiData.reloadPlaylist = qaction(_("&Update current playlist"), data)
    YukiData.reloadPlaylist.setShortcut(kbd("reload_playlist"))
    YukiData.reloadPlaylist.triggered.connect(lambda: YukiData.reload_playlist())

    YukiData.m3uEditor = qaction(_("&m3u Editor") + YukiData.str_offset, data)
    YukiData.m3uEditor.setShortcut(kbd("show_m3u_editor"))
    YukiData.m3uEditor.triggered.connect(lambda: YukiData.show_m3u_editor())

    YukiData.exitAction = qaction(_("&Exit"), data)
    YukiData.exitAction.setShortcut(kbd("app.quit"))
    YukiData.exitAction.triggered.connect(lambda: YukiData.app_quit())

    # Play

    YukiData.playpause = qaction(_("&Play / Pause"), data)
    YukiData.playpause.setShortcut(kbd("mpv_play"))
    YukiData.playpause.triggered.connect(lambda: YukiData.mpv_play())

    YukiData.stop = qaction(_("&Stop"), data)
    YukiData.stop.setShortcut(kbd("mpv_stop"))
    YukiData.stop.triggered.connect(lambda: YukiData.mpv_stop())

    YukiData.secs = []
    sec_keys = [
        kbd("(lambda: mpv_seek(-10))"),
        kbd("(lambda: mpv_seek(10))"),
        kbd("(lambda: mpv_seek(-60))"),
        kbd("(lambda: mpv_seek(60))"),
        kbd("(lambda: mpv_seek(-600))"),
        kbd("(lambda: mpv_seek(600))"),
    ]
    sec_i18n = [
        gettext.ngettext("-%d second", "-%d seconds", 10) % 10,
        gettext.ngettext("+%d second", "+%d seconds", 10) % 10,
        gettext.ngettext("-%d minute", "-%d minutes", 1) % 1,
        gettext.ngettext("+%d minute", "+%d minutes", 1) % 1,
        gettext.ngettext("-%d minute", "-%d minutes", 10) % 10,
        gettext.ngettext("+%d minute", "+%d minutes", 10) % 10,
    ]
    sec_i = -1
    for i in ((10, "seconds", 10), (1, "minutes", 60), (10, "minutes", 600)):
        for k in ("-", "+"):
            sec_i += 1
            sec = qaction(sec_i18n[sec_i], data)
            sec.setShortcut(qkeysequence(sec_keys[sec_i]))
            sec.triggered.connect(
                partial(ast_mpv_seek, i[2] * -1 if k == "-" else i[2])
            )
            YukiData.secs.append(sec)

    YukiData.normalSpeed = qaction(_("&Normal speed"), data)
    YukiData.normalSpeed.triggered.connect(partial(ast_mpv_speed, 1.00))
    YukiData.normalSpeed.setShortcut(kbd("(lambda: set_playback_speed(1.00))"))

    YukiData.spds = []

    for spd in (0.25, 0.5, 0.75, 1.25, 1.5, 1.75):
        spd_action = qaction(f"{spd}x", data)
        spd_action.triggered.connect(partial(ast_mpv_speed, spd))
        YukiData.spds.append(spd_action)

    YukiData.prevchannel = qaction(_("&Previous"), data)
    YukiData.prevchannel.triggered.connect(lambda: YukiData.prev_channel())
    YukiData.prevchannel.setShortcut(kbd("prev_channel"))

    YukiData.nextchannel = qaction(_("&Next"), data)
    YukiData.nextchannel.triggered.connect(lambda: YukiData.next_channel())
    YukiData.nextchannel.setShortcut(kbd("next_channel"))

    # Video
    YukiData.fullscreen = qaction(_("&Fullscreen"), data)
    YukiData.fullscreen.triggered.connect(lambda: YukiData.mpv_fullscreen())
    YukiData.fullscreen.setShortcut(kbd("mpv_fullscreen"))

    YukiData.compactmode = qaction(_("&Compact mode"), data)
    YukiData.compactmode.triggered.connect(lambda: YukiData.showhideeverything())
    YukiData.compactmode.setShortcut(kbd("showhideeverything"))

    YukiData.csforchannel = qaction(_("&Video settings") + YukiData.str_offset, data)
    YukiData.csforchannel.triggered.connect(lambda: YukiData.main_channel_settings())
    YukiData.csforchannel.setShortcut(kbd("main_channel_settings"))

    YukiData.screenshot = qaction(_("&Screenshot"), data)
    YukiData.screenshot.triggered.connect(lambda: YukiData.do_screenshot())
    YukiData.screenshot.setShortcut(kbd("do_screenshot"))

    # Video filters
    YukiData.vf_postproc = qaction(_("&Postprocessing"), data)
    YukiData.vf_postproc.setCheckable(True)

    YukiData.vf_deblock = qaction(_("&Deblock"), data)
    YukiData.vf_deblock.setCheckable(True)

    YukiData.vf_dering = qaction(_("De&ring"), data)
    YukiData.vf_dering.setCheckable(True)

    YukiData.vf_debanding = qaction(
        _("Debanding (&gradfun)") + YukiData.str_offset, data
    )
    YukiData.vf_debanding.setCheckable(True)

    YukiData.vf_noise = qaction(_("Add n&oise"), data)
    YukiData.vf_noise.setCheckable(True)

    YukiData.vf_black = qaction(_("Add &black borders"), data)
    YukiData.vf_black.setCheckable(True)

    YukiData.vf_softscaling = qaction(_("Soft&ware scaling"), data)
    YukiData.vf_softscaling.setCheckable(True)

    YukiData.vf_phase = qaction(_("&Autodetect phase"), data)
    YukiData.vf_phase.setCheckable(True)

    # Audio

    YukiData.muteAction = qaction(_("&Mute audio"), data)
    YukiData.muteAction.triggered.connect(lambda: YukiData.mpv_mute())
    YukiData.muteAction.setShortcut(kbd("mpv_mute"))

    YukiData.volumeMinus = qaction(_("V&olume -"), data)
    YukiData.volumeMinus.triggered.connect(lambda: YukiData.my_down_binding_execute())
    YukiData.volumeMinus.setShortcut(kbd("my_down_binding_execute"))

    YukiData.volumePlus = qaction(_("Vo&lume +"), data)
    YukiData.volumePlus.triggered.connect(lambda: YukiData.my_up_binding_execute())
    YukiData.volumePlus.setShortcut(kbd("my_up_binding_execute"))

    # Audio filters

    YukiData.af_extrastereo = qaction(_("&Extrastereo"), data)
    YukiData.af_extrastereo.setCheckable(True)

    YukiData.af_karaoke = qaction(_("&Karaoke"), data)
    YukiData.af_karaoke.setCheckable(True)

    YukiData.af_earvax = qaction(
        _("&Headphone optimization") + YukiData.str_offset, data
    )
    YukiData.af_earvax.setCheckable(True)

    YukiData.af_volnorm = qaction(_("Volume &normalization"), data)
    YukiData.af_volnorm.setCheckable(True)

    # View

    YukiData.showhideplaylistAction = qaction(_("Show/hide playlist"), data)
    YukiData.showhideplaylistAction.triggered.connect(
        lambda: YukiData.showhideplaylist()
    )
    YukiData.showhideplaylistAction.setShortcut(kbd("key_t"))

    YukiData.showhidectrlpanelAction = qaction(_("Show/hide controls panel"), data)
    YukiData.showhidectrlpanelAction.triggered.connect(lambda: YukiData.lowpanel_ch_1())
    YukiData.showhidectrlpanelAction.setShortcut(kbd("lowpanel_ch_1"))

    YukiData.alwaysontopAction = qaction(_("Window always on top"), data)
    YukiData.alwaysontopAction.triggered.connect(alwaysontop_action)
    YukiData.alwaysontopAction.setCheckable(True)
    YukiData.alwaysontopAction.setShortcut(kbd("alwaysontop"))
    if qt_library == "PyQt6":
        YukiData.alwaysontopAction.setVisible(False)

    YukiData.streaminformationAction = qaction(_("Stream Information"), data)
    YukiData.streaminformationAction.triggered.connect(
        lambda: YukiData.open_stream_info()
    )
    YukiData.streaminformationAction.setShortcut(kbd("open_stream_info"))

    YukiData.showepgAction = qaction(_("TV guide"), data)
    YukiData.showepgAction.triggered.connect(lambda: YukiData.show_tvguide_2())
    YukiData.showepgAction.setShortcut(kbd("show_tvguide_2"))

    YukiData.forceupdateepgAction = qaction(_("&Update TV guide"), data)
    YukiData.forceupdateepgAction.triggered.connect(lambda: YukiData.force_update_epg())
    YukiData.forceupdateepgAction.setShortcut(kbd("force_update_epg"))

    # Options

    YukiData.sortAction = qaction(_("&Channel sort"), data)
    YukiData.sortAction.triggered.connect(lambda: YukiData.show_sort())
    YukiData.sortAction.setShortcut(kbd("show_sort"))

    YukiData.shortcutsAction = qaction("&" + _("Shortcuts"), data)
    YukiData.shortcutsAction.triggered.connect(lambda: YukiData.show_shortcuts())

    YukiData.settingsAction = qaction(_("&Settings"), data)
    YukiData.settingsAction.triggered.connect(lambda: YukiData.show_settings())
    YukiData.settingsAction.setShortcut(kbd("show_settings"))

    # Help

    YukiData.aboutAction = qaction(_("&About yuki-iptv"), data)
    YukiData.aboutAction.triggered.connect(lambda: YukiData.show_help())

    # Empty (track list)
    YukiData.empty_action = qaction("<{}>".format(_("empty")), data)
    YukiData.empty_action.setEnabled(False)
    YukiData.empty_action1 = qaction("<{}>".format(_("empty")), data)
    YukiData.empty_action1.setEnabled(False)
    YukiData.empty_action2 = qaction("<{}>".format(_("empty")), data)
    YukiData.empty_action2.setEnabled(False)

    # Filters mapping
    YukiData.filter_mapping = {
        "vf::::::::lavfi=[pp]": YukiData.vf_postproc,
        "vf::::::::lavfi=[pp=vb/hb]": YukiData.vf_deblock,
        "vf::::::::lavfi=[pp=dr]": YukiData.vf_dering,
        "vf::::::::lavfi=[gradfun]": YukiData.vf_debanding,
        "vf::::::::lavfi=[noise=alls=9:allf=t]": YukiData.vf_noise,
        "vf::::::::__AST_VFBLACK__": YukiData.vf_black,
        "vf::::::::__AST_SOFTSCALING__": YukiData.vf_softscaling,
        "vf::::::::lavfi=[phase=A]": YukiData.vf_phase,
        "af::::::::lavfi=[extrastereo]": YukiData.af_extrastereo,
        "af::::::::lavfi=[stereotools=mlev=0.015625]": YukiData.af_karaoke,
        "af::::::::lavfi=[earwax]": YukiData.af_earvax,
        "af::::::::lavfi=[acompressor]": YukiData.af_volnorm,
    }
    for vf_filter in YukiData.filter_mapping:
        YukiData.filter_mapping[vf_filter].triggered.connect(
            partial(apply_vf_filter, vf_filter, YukiData.filter_mapping[vf_filter])
        )
    return YukiData.alwaysontopAction


def populate_menubar(
    i, menubar, data, track_list=None, playing_chan=None, get_keybind=None
):
    # logger.info("populate_menubar called")
    # File

    if get_keybind:
        YukiData.get_keybind = get_keybind

    aot_action = None

    if not YukiData.menubar_ready:
        aot_action = init_menubar(data)
        YukiData.menubar_ready = True

    file_menu = menubar.addMenu(_("&File"))
    file_menu.addAction(YukiData.playlists)
    file_menu.addSeparator()
    file_menu.addAction(YukiData.reloadPlaylist)
    file_menu.addAction(YukiData.forceupdateepgAction)
    file_menu.addSeparator()
    file_menu.addAction(YukiData.m3uEditor)
    file_menu.addAction(YukiData.exitAction)

    # Play

    play_menu = menubar.addMenu(_("&Play"))
    play_menu.addAction(YukiData.playpause)
    play_menu.addAction(YukiData.stop)
    play_menu.addSeparator()
    for sec in YukiData.secs:
        play_menu.addAction(sec)
    play_menu.addSeparator()

    speed_menu = play_menu.addMenu(_("Speed"))
    speed_menu.addAction(YukiData.normalSpeed)
    for spd_action1 in YukiData.spds:
        speed_menu.addAction(spd_action1)
    play_menu.addSeparator()
    play_menu.addAction(YukiData.prevchannel)
    play_menu.addAction(YukiData.nextchannel)

    # Video

    video_menu = menubar.addMenu(_("&Video"))
    video_track_menu = video_menu.addMenu(_("&Track"))
    video_track_menu.clear()
    video_menu.addAction(YukiData.fullscreen)
    video_menu.addAction(YukiData.compactmode)
    video_menu.addAction(YukiData.csforchannel)
    YukiData.video_menu_filters = video_menu.addMenu(_("F&ilters"))
    YukiData.video_menu_filters.addAction(YukiData.vf_postproc)
    YukiData.video_menu_filters.addAction(YukiData.vf_deblock)
    YukiData.video_menu_filters.addAction(YukiData.vf_dering)
    YukiData.video_menu_filters.addAction(YukiData.vf_debanding)
    YukiData.video_menu_filters.addAction(YukiData.vf_noise)
    YukiData.video_menu_filters.addAction(YukiData.vf_black)
    YukiData.video_menu_filters.addAction(YukiData.vf_softscaling)
    YukiData.video_menu_filters.addAction(YukiData.vf_phase)
    video_menu.addSeparator()
    video_menu.addAction(YukiData.screenshot)

    # Audio

    audio_menu = menubar.addMenu(_("&Audio"))
    audio_track_menu = audio_menu.addMenu(_("&Track"))
    audio_track_menu.clear()
    YukiData.audio_menu_filters = audio_menu.addMenu(_("F&ilters"))
    YukiData.audio_menu_filters.addAction(YukiData.af_extrastereo)
    YukiData.audio_menu_filters.addAction(YukiData.af_karaoke)
    YukiData.audio_menu_filters.addAction(YukiData.af_earvax)
    YukiData.audio_menu_filters.addAction(YukiData.af_volnorm)
    audio_menu.addSeparator()
    audio_menu.addAction(YukiData.muteAction)
    audio_menu.addSeparator()
    audio_menu.addAction(YukiData.volumeMinus)
    audio_menu.addAction(YukiData.volumePlus)

    # Subtitles
    subtitles_menu = menubar.addMenu(_("&Subtitles"))
    sub_track_menu = subtitles_menu.addMenu(_("&Track"))
    sub_track_menu.clear()

    # View

    view_menu = menubar.addMenu(_("Vie&w"))
    view_menu.addAction(YukiData.showhideplaylistAction)
    view_menu.addAction(YukiData.showhidectrlpanelAction)
    view_menu.addAction(YukiData.alwaysontopAction)
    view_menu.addAction(YukiData.streaminformationAction)
    view_menu.addAction(YukiData.showepgAction)

    # Options

    options_menu = menubar.addMenu(_("&Options"))
    options_menu.addAction(YukiData.sortAction)
    options_menu.addSeparator()
    options_menu.addAction(YukiData.shortcutsAction)
    options_menu.addAction(YukiData.settingsAction)

    # Help

    help_menu = menubar.addMenu(_("&Help"))
    help_menu.addAction(YukiData.aboutAction)

    YukiData.menubars[i] = [video_track_menu, audio_track_menu, sub_track_menu]

    return aot_action


# Preventing memory leak
def clear_menu(menu):
    for mb_action in menu.actions():
        if mb_action.isSeparator():
            mb_action.deleteLater()
        # elif mb_action.menu():
        #    clear_menu(mb_action.menu())
        #    mb_action.menu().deleteLater()
        else:
            if mb_action.text() != "<{}>".format(_("empty")):
                mb_action.deleteLater()


def recursive_filter_setstate(state):
    for act in YukiData.video_menu_filters.actions():
        if not act.isSeparator():  # or act.menu():
            act.setEnabled(state)
    for act1 in YukiData.audio_menu_filters.actions():
        if not act1.isSeparator():  # or act1.menu():
            act1.setEnabled(state)


def get_first_run():
    return YukiData.first_run


def update_menubar(track_list, playing_chan, m3u, aot_file):
    # Filters enable / disable
    if playing_chan:
        recursive_filter_setstate(True)
        # print(playing_chan + '::::::::::::::' + m3u)
        if not YukiData.first_run:
            YukiData.first_run = True
            logger.info("YukiData.first_run")
            try:
                vf_filters_read = read_option("vf_filters")
                if vf_filters_read:
                    for dat in vf_filters_read:
                        if dat in YukiData.filter_mapping:
                            YukiData.filter_mapping[dat].setChecked(True)
                            apply_vf_filter(dat, YukiData.filter_mapping[dat])
            except Exception:
                pass
    else:
        recursive_filter_setstate(False)
    # Always on top
    if not YukiData.first_run1:
        YukiData.first_run1 = True
        try:
            if os.path.isfile(aot_file):
                file_2 = open(aot_file, "r", encoding="utf-8")
                file_2_out = file_2.read()
                file_2.close()
                aot_state = json.loads(file_2_out)["alwaysontop"]
                if aot_state:
                    YukiData.alwaysontopAction.setChecked(True)
                else:
                    YukiData.alwaysontopAction.setChecked(False)
        except Exception:
            pass
    # Track list
    for i in YukiData.menubars:
        clear_menu(YukiData.menubars[i][0])
        clear_menu(YukiData.menubars[i][1])
        clear_menu(YukiData.menubars[i][2])
        YukiData.menubars[i][0].clear()
        YukiData.menubars[i][1].clear()
        YukiData.menubars[i][2].clear()
        if track_list and playing_chan:
            if not [x for x in track_list if x["type"] == "video"]:
                YukiData.menubars[i][0].addAction(YukiData.empty_action)
            if not [x for x in track_list if x["type"] == "audio"]:
                YukiData.menubars[i][1].addAction(YukiData.empty_action1)
            # Subtitles off
            sub_off_action = qaction(_("None"), YukiData.data)
            if YukiData.player.sid == "no" or not YukiData.player.sid:
                sub_off_action.setIcon(YukiData.circle_icon)
            sub_off_action.triggered.connect(partial(yuki_trackset, "no", "sid"))
            YukiData.menubars[i][2].addAction(sub_off_action)
            for track in track_list:
                if track["type"] == "video":
                    trk = qaction(str(track["id"]), YukiData.data)
                    if track["id"] == YukiData.player.vid:
                        trk.setIcon(YukiData.circle_icon)
                    trk.triggered.connect(partial(yuki_trackset, track["id"], "vid"))
                    YukiData.menubars[i][0].addAction(trk)
                if track["type"] == "audio":
                    if "lang" in track:
                        trk1 = qaction(
                            "{} ({})".format(track["id"], track["lang"]), YukiData.data
                        )
                    else:
                        trk1 = qaction(str(track["id"]), YukiData.data)
                    if track["id"] == YukiData.player.aid:
                        trk1.setIcon(YukiData.circle_icon)
                    trk1.triggered.connect(partial(yuki_trackset, track["id"], "aid"))
                    YukiData.menubars[i][1].addAction(trk1)
                if track["type"] == "sub":
                    if "lang" in track:
                        trk2 = qaction(
                            "{} ({})".format(track["id"], track["lang"]), YukiData.data
                        )
                    else:
                        trk2 = qaction(str(track["id"]), YukiData.data)
                    if track["id"] == YukiData.player.sid:
                        trk2.setIcon(YukiData.circle_icon)
                    trk2.triggered.connect(partial(yuki_trackset, track["id"], "sid"))
                    YukiData.menubars[i][2].addAction(trk2)
        else:
            YukiData.menubars[i][0].addAction(YukiData.empty_action)
            YukiData.menubars[i][1].addAction(YukiData.empty_action1)
            YukiData.menubars[i][2].addAction(YukiData.empty_action2)


def init_yuki_iptv_menubar(data, app, menubar):
    YukiData.data = data


def init_menubar_player(
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
    app_quit,
    redraw_menubar,
    circle_icon,
    my_up_binding_execute,
    my_down_binding_execute,
    show_m3u_editor,
    show_playlists,
    show_sort,
    show_exception,
    get_curwindow_pos,
    force_update_epg,
    get_keybind,
    show_tvguide_2,
    enable_always_on_top,
    disable_always_on_top,
    reload_playlist,
    show_shortcuts,
    aot_file,
    yuki_track_set,
):
    for func in locals().items():
        setattr(YukiData, func[0], func[1])
