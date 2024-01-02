#
# Copyright (c) 2021, 2022 Astroncia <kestraly@gmail.com>
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
# https://fontawesome.com/
# https://creativecommons.org/licenses/by/4.0/
#
from yuki_iptv.qt import get_qt_library

qt_library, QtWidgets, QtCore, QtGui, QShortcut, QtOpenGLWidgets = get_qt_library()

main_keybinds_internal = {
    "do_record_1_INTERNAL": QtCore.Qt.Key.Key_MediaRecord,
    "mpv_mute_1_INTERNAL": QtCore.Qt.Key.Key_VolumeMute,
    "mpv_play_1_INTERNAL": QtCore.Qt.Key.Key_MediaTogglePlayPause,
    "mpv_play_2_INTERNAL": QtCore.Qt.Key.Key_MediaPlay,
    "mpv_play_3_INTERNAL": QtCore.Qt.Key.Key_MediaPause,
    "mpv_play_4_INTERNAL": QtCore.Qt.Key.Key_Play,
    "mpv_stop_1_INTERNAL": QtCore.Qt.Key.Key_Stop,
    "mpv_stop_2_INTERNAL": QtCore.Qt.Key.Key_MediaStop,
    "next_channel_1_INTERNAL": QtCore.Qt.Key.Key_MediaNext,
    "prev_channel_1_INTERNAL": QtCore.Qt.Key.Key_MediaPrevious,
    "(lambda: my_down_binding())_INTERNAL": QtCore.Qt.Key.Key_VolumeDown,
    "(lambda: my_up_binding())_INTERNAL": QtCore.Qt.Key.Key_VolumeUp,
}

main_keybinds_default = {
    "mpv_play": QtCore.Qt.Key.Key_Space,
    "mpv_stop": QtCore.Qt.Key.Key_S,
    "mpv_mute": QtCore.Qt.Key.Key_M,
    "my_down_binding_execute": QtCore.Qt.Key.Key_9,
    "my_up_binding_execute": QtCore.Qt.Key.Key_0,
    "prev_channel": QtCore.Qt.Key.Key_B,
    "next_channel": QtCore.Qt.Key.Key_N,
    "key_quit": QtCore.Qt.Key.Key_Q,
    "app.quit": "Ctrl+Q",
    "do_record": QtCore.Qt.Key.Key_R,
    "do_screenshot": QtCore.Qt.Key.Key_H,
    "esc_handler": QtCore.Qt.Key.Key_Escape,
    "force_update_epg": "Ctrl+U",
    "key_t": QtCore.Qt.Key.Key_T,
    "lowpanel_ch_1": QtCore.Qt.Key.Key_P,
    "main_channel_settings": "Ctrl+S",
    "mpv_fullscreen": QtCore.Qt.Key.Key_F,
    "mpv_fullscreen_2": QtCore.Qt.Key.Key_F11,
    "open_stream_info": QtCore.Qt.Key.Key_F2,
    "show_m3u_editor": "Ctrl+E",
    "show_playlists": "Ctrl+O",
    "reload_playlist": "Ctrl+R",
    "show_scheduler": QtCore.Qt.Key.Key_D,
    "show_settings": "Ctrl+P",
    "show_sort": QtCore.Qt.Key.Key_I,
    "show_timeshift": QtCore.Qt.Key.Key_E,
    "show_tvguide": QtCore.Qt.Key.Key_G,
    "showhideeverything": "Ctrl+C",
    "show_tvguide_2": QtCore.Qt.Key.Key_J,
    "alwaysontop": QtCore.Qt.Key.Key_A,
    "(lambda: mpv_seek(-10))": QtCore.Qt.Key.Key_Left,
    "(lambda: mpv_seek(-60))": QtCore.Qt.Key.Key_Down,
    "(lambda: mpv_seek(-600))": QtCore.Qt.Key.Key_PageDown,
    "(lambda: mpv_seek(10))": QtCore.Qt.Key.Key_Right,
    "(lambda: mpv_seek(60))": QtCore.Qt.Key.Key_Up,
    "(lambda: mpv_seek(600))": QtCore.Qt.Key.Key_PageUp,
    "(lambda: set_playback_speed(1.00))": QtCore.Qt.Key.Key_Backspace,
    "mpv_frame_step": QtCore.Qt.Key.Key_Period,
    "mpv_frame_back_step": QtCore.Qt.Key.Key_Comma,
}
