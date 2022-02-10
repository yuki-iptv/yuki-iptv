# pylint: disable=no-member, unnecessary-lambda, unused-argument, import-error
# pylint: disable=missing-class-docstring, missing-function-docstring
'''
Copyright (c) 2021-2022 Astroncia

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
import json
import traceback
from functools import partial
from astroncia.time import print_with_time
from astroncia.qt import get_qt_library
from astroncia.lang import _, __
from astroncia.qt6compat import qaction
qt_library, QtWidgets, QtCore, QtGui, QShortcut = get_qt_library()

class AstronciaData: # pylint: disable=too-few-public-methods
    menubar_ready = False
    first_run = False
    first_run1 = False
    menubars = {}
    data = {}
    cur_vf_filters = []
    keyboard_sequences = []
    if qt_library == 'PyQt6':
        str_offset = ' ' * 44
    else:
        str_offset = ''

def ast_mpv_seek(secs):
    print_with_time("Seeking to {} seconds".format(secs))
    AstronciaData.player.command('seek', secs)

def ast_mpv_speed(spd):
    print_with_time("Set speed to {}".format(spd))
    AstronciaData.player.speed = spd

def ast_trackset(track, type1):
    print_with_time("Set {} track to {}".format(type1, track))
    if type1 == 'vid':
        AstronciaData.player.vid = track
    else:
        AstronciaData.player.aid = track
    AstronciaData.redraw_menubar()

def send_mpv_command(name, act, cmd):
    if cmd == '__AST_VFBLACK__':
        cur_window_pos = AstronciaData.get_curwindow_pos()
        cmd = 'lavfi=[pad=iw:iw*sar/{}*{}:0:(oh-ih)/2]'.format(
            cur_window_pos[0], cur_window_pos[1]
        )
    if cmd == '__AST_SOFTSCALING__':
        cur_window_pos = AstronciaData.get_curwindow_pos()
        cmd = 'lavfi=[scale={}:-2]'.format(cur_window_pos[0])
    print_with_time("Sending mpv command: \"{} {} \\\"{}\\\"\"".format(name, act, cmd))
    AstronciaData.player.command(name, act, cmd)

def get_active_vf_filters():
    return AstronciaData.cur_vf_filters

def apply_vf_filter(vf_filter, e_l):
    try:
        if e_l.isChecked():
            send_mpv_command(vf_filter.split('::::::::')[0], 'add', vf_filter.split('::::::::')[1])
            AstronciaData.cur_vf_filters.append(vf_filter)
        else:
            send_mpv_command(
                vf_filter.split('::::::::')[0], 'remove', vf_filter.split('::::::::')[1]
            )
            AstronciaData.cur_vf_filters.remove(vf_filter)
    except Exception as e_4: # pylint: disable=broad-except
        print_with_time("ERROR in vf-filter apply")
        print_with_time("")
        e4_traceback = traceback.format_exc()
        print_with_time(e4_traceback)
        AstronciaData.show_exception(e_4, e4_traceback, '\n\n' + _('errorvfapply'))

def get_seq():
    return AstronciaData.keyboard_sequences

def qkeysequence(seq):
    s_e = QtGui.QKeySequence(seq)
    AstronciaData.keyboard_sequences.append(s_e)
    return s_e

def kbd(k_1):
    return qkeysequence(AstronciaData.get_keybind(k_1))

def alwaysontop_action():
    try:
        aot_f = open(AstronciaData.aot_file, 'w', encoding='utf-8')
        aot_f.write(json.dumps({
            "alwaysontop": AstronciaData.alwaysontopAction.isChecked()
        }))
        aot_f.close()
    except: # pylint: disable=bare-except
        pass
    if AstronciaData.alwaysontopAction.isChecked():
        print_with_time("Always on top enabled now")
        AstronciaData.enable_always_on_top()
    else:
        print_with_time("Always on top disabled now")
        AstronciaData.disable_always_on_top()

def reload_menubar_shortcuts():
    AstronciaData.playlists.setShortcut(kbd("show_playlists"))
    AstronciaData.reloadPlaylist.setShortcut(kbd("reload_playlist"))
    AstronciaData.m3uEditor.setShortcut(kbd("show_m3u_editor"))
    AstronciaData.exitAction.setShortcut(kbd("app.quit"))
    AstronciaData.playpause.setShortcut(kbd("mpv_play"))
    AstronciaData.stop.setShortcut(kbd("mpv_stop"))
    AstronciaData.normalSpeed.setShortcut(kbd("(lambda: set_playback_speed(1.00))"))
    AstronciaData.prevchannel.setShortcut(kbd("prev_channel"))
    AstronciaData.nextchannel.setShortcut(kbd("next_channel"))
    AstronciaData.fullscreen.setShortcut(kbd("mpv_fullscreen"))
    AstronciaData.compactmode.setShortcut(kbd("showhideeverything"))
    AstronciaData.csforchannel.setShortcut(kbd("main_channel_settings"))
    AstronciaData.screenshot.setShortcut(kbd("do_screenshot"))
    AstronciaData.muteAction.setShortcut(kbd("mpv_mute"))
    AstronciaData.volumeMinus.setShortcut(kbd("my_down_binding_execute"))
    AstronciaData.volumePlus.setShortcut(kbd("my_up_binding_execute"))
    AstronciaData.showhideplaylistAction.setShortcut(kbd("key_t"))
    AstronciaData.showhidectrlpanelAction.setShortcut(kbd("lowpanel_ch_1"))
    AstronciaData.alwaysontopAction.setShortcut(kbd("alwaysontop"))
    AstronciaData.streaminformationAction.setShortcut(kbd("open_stream_info"))
    AstronciaData.showepgAction.setShortcut(kbd("show_tvguide_2"))
    AstronciaData.forceupdateepgAction.setShortcut(kbd("force_update_epg"))
    AstronciaData.sortAction.setShortcut(kbd("show_sort"))
    AstronciaData.settingsAction.setShortcut(kbd("show_settings"))
    sec_keys_1 = [
        kbd("(lambda: mpv_seek(-10))"),
        kbd("(lambda: mpv_seek(10))"),
        kbd("(lambda: mpv_seek(-60))"),
        kbd("(lambda: mpv_seek(60))"),
        kbd("(lambda: mpv_seek(-600))"),
        kbd("(lambda: mpv_seek(600))")
    ]
    sec_i_1 = -1
    for i_1 in AstronciaData.secs:
        sec_i_1 += 1
        i_1.setShortcut(qkeysequence(sec_keys_1[sec_i_1]))

def init_menubar(data): # pylint: disable=too-many-statements
    # File

    AstronciaData.playlists = qaction(_('menubar_playlists'), data)
    AstronciaData.playlists.setShortcut(kbd("show_playlists"))
    AstronciaData.playlists.triggered.connect(lambda: AstronciaData.show_playlists())

    AstronciaData.reloadPlaylist = qaction(_('updcurplaylist'), data)
    AstronciaData.reloadPlaylist.setShortcut(kbd("reload_playlist"))
    AstronciaData.reloadPlaylist.triggered.connect(lambda: AstronciaData.reload_playlist())

    AstronciaData.m3uEditor = qaction(_('menubar_m3ueditor') + AstronciaData.str_offset, data)
    AstronciaData.m3uEditor.setShortcut(kbd("show_m3u_editor"))
    AstronciaData.m3uEditor.triggered.connect(lambda: AstronciaData.show_m3u_editor())

    AstronciaData.exitAction = qaction(_('menubar_exit'), data)
    AstronciaData.exitAction.setShortcut(kbd("app.quit"))
    AstronciaData.exitAction.triggered.connect(lambda: AstronciaData.app_quit())

    # Play

    AstronciaData.playpause = qaction(_('menubar_playpause'), data)
    AstronciaData.playpause.setShortcut(kbd("mpv_play"))
    AstronciaData.playpause.triggered.connect(lambda: AstronciaData.mpv_play())

    AstronciaData.stop = qaction(_('menubar_stop'), data)
    AstronciaData.stop.setShortcut(kbd("mpv_stop"))
    AstronciaData.stop.triggered.connect(lambda: AstronciaData.mpv_stop())

    AstronciaData.secs = []
    sec_keys = [
        kbd("(lambda: mpv_seek(-10))"),
        kbd("(lambda: mpv_seek(10))"),
        kbd("(lambda: mpv_seek(-60))"),
        kbd("(lambda: mpv_seek(60))"),
        kbd("(lambda: mpv_seek(-600))"),
        kbd("(lambda: mpv_seek(600))")
    ]
    sec_i = -1
    for i in (
        (10, "seconds_plural", 10),
        (1, "minutes_plural", 60),
        (10, "minutes_plural", 600)
    ):
        for k in ("-", "+"):
            sec_i += 1
            sec = qaction(
                "{}{} {}".format(k, i[0], __(i[1], "", i[0])),
                data
            )
            sec.setShortcut(qkeysequence(sec_keys[sec_i]))
            sec.triggered.connect(partial(ast_mpv_seek, i[2] * -1 if k == '-' else i[2]))
            AstronciaData.secs.append(sec)

    AstronciaData.normalSpeed = qaction(_('menubar_normalspeed'), data)
    AstronciaData.normalSpeed.triggered.connect(partial(ast_mpv_speed, 1.00))
    AstronciaData.normalSpeed.setShortcut(kbd("(lambda: set_playback_speed(1.00))"))

    AstronciaData.spds = []

    for spd in (0.25, 0.5, 0.75, 1.25, 1.5, 1.75):
        spd_action = qaction("{}x".format(spd), data)
        spd_action.triggered.connect(partial(ast_mpv_speed, spd))
        AstronciaData.spds.append(spd_action)

    AstronciaData.prevchannel = qaction(_('menubar_previous'), data)
    AstronciaData.prevchannel.triggered.connect(lambda: AstronciaData.prev_channel())
    AstronciaData.prevchannel.setShortcut(kbd("prev_channel"))

    AstronciaData.nextchannel = qaction(_('menubar_next'), data)
    AstronciaData.nextchannel.triggered.connect(lambda: AstronciaData.next_channel())
    AstronciaData.nextchannel.setShortcut(kbd("next_channel"))

    # Video
    AstronciaData.fullscreen = qaction(_('menubar_fullscreen'), data)
    AstronciaData.fullscreen.triggered.connect(lambda: AstronciaData.mpv_fullscreen())
    AstronciaData.fullscreen.setShortcut(kbd("mpv_fullscreen"))

    AstronciaData.compactmode = qaction(_('menubar_compactmode'), data)
    AstronciaData.compactmode.triggered.connect(lambda: AstronciaData.showhideeverything())
    AstronciaData.compactmode.setShortcut(kbd("showhideeverything"))

    AstronciaData.csforchannel = qaction(_('menubar_csforchannel') + AstronciaData.str_offset, data)
    AstronciaData.csforchannel.triggered.connect(lambda: AstronciaData.main_channel_settings())
    AstronciaData.csforchannel.setShortcut(kbd("main_channel_settings"))

    AstronciaData.screenshot = qaction(_('menubar_screenshot'), data)
    AstronciaData.screenshot.triggered.connect(lambda: AstronciaData.do_screenshot())
    AstronciaData.screenshot.setShortcut(kbd("do_screenshot"))

    # Video filters
    AstronciaData.vf_postproc = qaction(_('menubar_postproc'), data)
    AstronciaData.vf_postproc.setCheckable(True)

    AstronciaData.vf_deblock = qaction(_('menubar_deblock'), data)
    AstronciaData.vf_deblock.setCheckable(True)

    AstronciaData.vf_dering = qaction(_('menubar_dering'), data)
    AstronciaData.vf_dering.setCheckable(True)

    AstronciaData.vf_debanding = qaction(_('menubar_debanding') + AstronciaData.str_offset, data)
    AstronciaData.vf_debanding.setCheckable(True)

    AstronciaData.vf_noise = qaction(_('menubar_noise'), data)
    AstronciaData.vf_noise.setCheckable(True)

    AstronciaData.vf_black = qaction(_('menubar_black'), data)
    AstronciaData.vf_black.setCheckable(True)

    AstronciaData.vf_softscaling = qaction(_('menubar_softscaling'), data)
    AstronciaData.vf_softscaling.setCheckable(True)

    AstronciaData.vf_phase = qaction(_('menubar_phase'), data)
    AstronciaData.vf_phase.setCheckable(True)

    # Audio

    AstronciaData.muteAction = qaction(_('menubar_mute'), data)
    AstronciaData.muteAction.triggered.connect(lambda: AstronciaData.mpv_mute())
    AstronciaData.muteAction.setShortcut(kbd("mpv_mute"))

    AstronciaData.volumeMinus = qaction(_('menubar_volumeminus'), data)
    AstronciaData.volumeMinus.triggered.connect(lambda: AstronciaData.my_down_binding_execute())
    AstronciaData.volumeMinus.setShortcut(kbd("my_down_binding_execute"))

    AstronciaData.volumePlus = qaction(_('menubar_volumeplus'), data)
    AstronciaData.volumePlus.triggered.connect(lambda: AstronciaData.my_up_binding_execute())
    AstronciaData.volumePlus.setShortcut(kbd("my_up_binding_execute"))

    # Audio filters

    AstronciaData.af_extrastereo = qaction(_('menubar_extrastereo'), data)
    AstronciaData.af_extrastereo.setCheckable(True)

    AstronciaData.af_karaoke = qaction(_('menubar_karaoke'), data)
    AstronciaData.af_karaoke.setCheckable(True)

    AstronciaData.af_earvax = qaction(_('menubar_earvax') + AstronciaData.str_offset, data)
    AstronciaData.af_earvax.setCheckable(True)

    AstronciaData.af_volnorm = qaction(_('menubar_volnorm'), data)
    AstronciaData.af_volnorm.setCheckable(True)

    # View

    AstronciaData.showhideplaylistAction = qaction(_('showhideplaylist'), data)
    AstronciaData.showhideplaylistAction.triggered.connect(lambda: AstronciaData.showhideplaylist())
    AstronciaData.showhideplaylistAction.setShortcut(kbd("key_t"))

    AstronciaData.showhidectrlpanelAction = qaction(_('showhidectrlpanel'), data)
    AstronciaData.showhidectrlpanelAction.triggered.connect(lambda: AstronciaData.lowpanel_ch_1())
    AstronciaData.showhidectrlpanelAction.setShortcut(kbd("lowpanel_ch_1"))

    AstronciaData.alwaysontopAction = qaction(_('alwaysontop'), data)
    AstronciaData.alwaysontopAction.triggered.connect(alwaysontop_action)
    AstronciaData.alwaysontopAction.setCheckable(True)
    AstronciaData.alwaysontopAction.setShortcut(kbd("alwaysontop"))
    if qt_library == 'PyQt6':
        AstronciaData.alwaysontopAction.setVisible(False)

    AstronciaData.streaminformationAction = qaction(_('Stream Information'), data)
    AstronciaData.streaminformationAction.triggered.connect(
        lambda: AstronciaData.open_stream_info()
    )
    AstronciaData.streaminformationAction.setShortcut(kbd("open_stream_info"))

    AstronciaData.showepgAction = qaction(_('tvguide'), data)
    AstronciaData.showepgAction.triggered.connect(
        lambda: AstronciaData.show_tvguide_2()
    )
    AstronciaData.showepgAction.setShortcut(kbd("show_tvguide_2"))

    AstronciaData.forceupdateepgAction = qaction(_('menubar_updateepg'), data)
    AstronciaData.forceupdateepgAction.triggered.connect(
        lambda: AstronciaData.force_update_epg()
    )
    AstronciaData.forceupdateepgAction.setShortcut(kbd("force_update_epg"))

    AstronciaData.applogAction = qaction(_('applog'), data)
    AstronciaData.applogAction.triggered.connect(lambda: AstronciaData.show_app_log())

    AstronciaData.mpvlogAction = qaction(_('mpvlog'), data)
    AstronciaData.mpvlogAction.triggered.connect(lambda: AstronciaData.show_mpv_log())

    # Options

    AstronciaData.sortAction = qaction(_('menubar_channelsort'), data)
    AstronciaData.sortAction.triggered.connect(lambda: AstronciaData.show_sort())
    AstronciaData.sortAction.setShortcut(kbd("show_sort"))

    AstronciaData.shortcutsAction = qaction('&' + _('shortcuts'), data)
    AstronciaData.shortcutsAction.triggered.connect(lambda: AstronciaData.show_shortcuts())

    AstronciaData.settingsAction = qaction(_('menubar_settings'), data)
    AstronciaData.settingsAction.triggered.connect(lambda: AstronciaData.show_settings())
    AstronciaData.settingsAction.setShortcut(kbd("show_settings"))

    # Help

    AstronciaData.aboutAction = qaction(_('menubar_about'), data)
    AstronciaData.aboutAction.triggered.connect(lambda: AstronciaData.show_help())

    # Empty (track list)
    AstronciaData.empty_action = qaction('<{}>'.format(_('empty_sm')), data)
    AstronciaData.empty_action.setEnabled(False)
    AstronciaData.empty_action1 = qaction('<{}>'.format(_('empty_sm')), data)
    AstronciaData.empty_action1.setEnabled(False)

    # Filters mapping
    AstronciaData.filter_mapping = {
        "vf::::::::lavfi=[pp]": AstronciaData.vf_postproc,
        "vf::::::::lavfi=[pp=vb/hb]": AstronciaData.vf_deblock,
        "vf::::::::lavfi=[pp=dr]": AstronciaData.vf_dering,
        "vf::::::::lavfi=[gradfun]": AstronciaData.vf_debanding,
        "vf::::::::lavfi=[noise=alls=9:allf=t]": AstronciaData.vf_noise,
        "vf::::::::__AST_VFBLACK__": AstronciaData.vf_black,
        "vf::::::::__AST_SOFTSCALING__": AstronciaData.vf_softscaling,
        "vf::::::::lavfi=[phase=A]": AstronciaData.vf_phase,
        "af::::::::lavfi=[extrastereo]": AstronciaData.af_extrastereo,
        "af::::::::lavfi=[stereotools=mlev=0.015625]": AstronciaData.af_karaoke,
        "af::::::::lavfi=[earwax]": AstronciaData.af_earvax,
        "af::::::::lavfi=[acompressor]": AstronciaData.af_volnorm
    }
    for vf_filter in AstronciaData.filter_mapping:
        AstronciaData.filter_mapping[vf_filter].triggered.connect(
            partial(apply_vf_filter, vf_filter, AstronciaData.filter_mapping[vf_filter])
        )
    return AstronciaData.alwaysontopAction

def populate_menubar(
    i, menubar, data, track_list=None, playing_chan=None,
    get_keybind=None
): # pylint: disable=too-many-statements, too-many-arguments, too-many-locals
    #print_with_time("populate_menubar called")
    # File

    if get_keybind:
        AstronciaData.get_keybind = get_keybind

    aot_action = None

    if not AstronciaData.menubar_ready:
        aot_action = init_menubar(data)
        AstronciaData.menubar_ready = True

    file_menu = menubar.addMenu(_('menubar_title_file'))
    file_menu.addAction(AstronciaData.playlists)
    file_menu.addSeparator()
    file_menu.addAction(AstronciaData.reloadPlaylist)
    file_menu.addAction(AstronciaData.forceupdateepgAction)
    file_menu.addSeparator()
    file_menu.addAction(AstronciaData.m3uEditor)
    file_menu.addAction(AstronciaData.exitAction)

    # Play

    play_menu = menubar.addMenu(_('menubar_title_play'))
    play_menu.addAction(AstronciaData.playpause)
    play_menu.addAction(AstronciaData.stop)
    play_menu.addSeparator()
    for sec in AstronciaData.secs:
        play_menu.addAction(sec)
    play_menu.addSeparator()

    speed_menu = play_menu.addMenu(_('speed'))
    speed_menu.addAction(AstronciaData.normalSpeed)
    for spd_action1 in AstronciaData.spds:
        speed_menu.addAction(spd_action1)
    play_menu.addSeparator()
    play_menu.addAction(AstronciaData.prevchannel)
    play_menu.addAction(AstronciaData.nextchannel)

    # Video

    video_menu = menubar.addMenu(_('menubar_video'))
    video_track_menu = video_menu.addMenu(_('menubar_track'))
    video_track_menu.clear()
    video_menu.addAction(AstronciaData.fullscreen)
    video_menu.addAction(AstronciaData.compactmode)
    video_menu.addAction(AstronciaData.csforchannel)
    AstronciaData.video_menu_filters = video_menu.addMenu(_('menubar_filters'))
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_postproc)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_deblock)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_dering)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_debanding)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_noise)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_black)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_softscaling)
    AstronciaData.video_menu_filters.addAction(AstronciaData.vf_phase)
    video_menu.addSeparator()
    video_menu.addAction(AstronciaData.screenshot)

    # Audio

    audio_menu = menubar.addMenu(_('menubar_audio'))
    audio_track_menu = audio_menu.addMenu(_('menubar_track'))
    audio_track_menu.clear()
    AstronciaData.audio_menu_filters = audio_menu.addMenu(_('menubar_filters'))
    AstronciaData.audio_menu_filters.addAction(AstronciaData.af_extrastereo)
    AstronciaData.audio_menu_filters.addAction(AstronciaData.af_karaoke)
    AstronciaData.audio_menu_filters.addAction(AstronciaData.af_earvax)
    AstronciaData.audio_menu_filters.addAction(AstronciaData.af_volnorm)
    audio_menu.addSeparator()
    audio_menu.addAction(AstronciaData.muteAction)
    audio_menu.addSeparator()
    audio_menu.addAction(AstronciaData.volumeMinus)
    audio_menu.addAction(AstronciaData.volumePlus)

    # View

    view_menu = menubar.addMenu(_('menubar_view'))
    view_menu.addAction(AstronciaData.showhideplaylistAction)
    view_menu.addAction(AstronciaData.showhidectrlpanelAction)
    view_menu.addAction(AstronciaData.alwaysontopAction)
    view_menu.addAction(AstronciaData.streaminformationAction)
    view_menu.addAction(AstronciaData.showepgAction)
    view_menu.addSection(_('logs'))
    view_menu.addAction(AstronciaData.applogAction)
    view_menu.addAction(AstronciaData.mpvlogAction)

    # Options

    options_menu = menubar.addMenu(_('menubar_options'))
    options_menu.addAction(AstronciaData.sortAction)
    options_menu.addSeparator()
    options_menu.addAction(AstronciaData.shortcutsAction)
    options_menu.addAction(AstronciaData.settingsAction)

    # Help

    help_menu = menubar.addMenu(_('menubar_help'))
    help_menu.addAction(AstronciaData.aboutAction)

    AstronciaData.menubars[i] = [video_track_menu, audio_track_menu]

    return aot_action

# Preventing memory leak
def clear_menu(menu):
    for mb_action in menu.actions():
        if mb_action.isSeparator():
            mb_action.deleteLater()
        #elif mb_action.menu():
        #    clear_menu(mb_action.menu())
        #    mb_action.menu().deleteLater()
        else:
            if mb_action.text() != '<{}>'.format(_('empty_sm')):
                mb_action.deleteLater()

def recursive_filter_setstate(state):
    for act in AstronciaData.video_menu_filters.actions():
        if not act.isSeparator(): #or act.menu():
            act.setEnabled(state)
    for act1 in AstronciaData.audio_menu_filters.actions():
        if not act1.isSeparator(): #or act1.menu():
            act1.setEnabled(state)

def get_first_run():
    return AstronciaData.first_run

def update_menubar(track_list, playing_chan, m3u, file, aot_file): # pylint: disable=too-many-branches, too-many-statements
    # Filters enable / disable
    if playing_chan:
        recursive_filter_setstate(True)
        #print(playing_chan + '::::::::::::::' + m3u)
        if not AstronciaData.first_run:
            AstronciaData.first_run = True
            print_with_time("AstronciaData.first_run")
            try:
                file_1 = open(file, 'r', encoding='utf-8')
                file_1_out = json.loads(file_1.read())['vf_filters']
                file_1.close()
                for dat in file_1_out:
                    if dat in AstronciaData.filter_mapping:
                        AstronciaData.filter_mapping[dat].setChecked(True)
                        apply_vf_filter(dat, AstronciaData.filter_mapping[dat])
            except: # pylint: disable=bare-except
                pass
    else:
        recursive_filter_setstate(False)
    # Always on top
    if not AstronciaData.first_run1:
        AstronciaData.first_run1 = True
        try:
            if os.path.isfile(aot_file):
                file_2 = open(aot_file, 'r', encoding='utf-8')
                file_2_out = file_2.read()
                file_2.close()
                aot_state = json.loads(file_2_out)["alwaysontop"]
                if aot_state:
                    AstronciaData.alwaysontopAction.setChecked(True)
                else:
                    AstronciaData.alwaysontopAction.setChecked(False)
        except: # pylint: disable=bare-except
            pass
    # Track list
    for i in AstronciaData.menubars:
        clear_menu(AstronciaData.menubars[i][0])
        clear_menu(AstronciaData.menubars[i][1])
        AstronciaData.menubars[i][0].clear()
        AstronciaData.menubars[i][1].clear()
        if track_list and playing_chan:
            if not [x for x in track_list if x['type'] == 'video']:
                AstronciaData.menubars[i][0].addAction(AstronciaData.empty_action)
            if not [x for x in track_list if x['type'] == 'audio']:
                AstronciaData.menubars[i][1].addAction(AstronciaData.empty_action1)
            for track in track_list:
                if track['type'] == 'video':
                    trk = qaction(str(track['id']), AstronciaData.data)
                    if track['id'] == AstronciaData.player.vid:
                        trk.setIcon(AstronciaData.circle_icon)
                    trk.triggered.connect(partial(ast_trackset, track['id'], 'vid'))
                    AstronciaData.menubars[i][0].addAction(trk)
                if track['type'] == 'audio':
                    trk1 = qaction(str(track['id']), AstronciaData.data)
                    if track['id'] == AstronciaData.player.aid:
                        trk1.setIcon(AstronciaData.circle_icon)
                    trk1.triggered.connect(partial(ast_trackset, track['id'], 'aid'))
                    AstronciaData.menubars[i][1].addAction(trk1)
        else:
            AstronciaData.menubars[i][0].addAction(AstronciaData.empty_action)
            AstronciaData.menubars[i][1].addAction(AstronciaData.empty_action1)

def init_astroncia_menubar(data, app, menubar):
    AstronciaData.data = data

def init_menubar_player( # pylint: disable=too-many-arguments, too-many-locals
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
    aot_file
):
    for func in locals().items():
        setattr(AstronciaData, func[0], func[1])
