'''
Copyright 2021 Astroncia

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
lang = {
    'en': {
        'name': 'English',
        'strings': {
            'm3u_ready': "Ready",
            'm3u_m3ueditor': "m3u Editor",
            'm3u_noname': 'No Name',
            'm3u_waschanged': 'The document was changed.<br>Do you want to save the changes?',
            'm3u_saveconfirm': 'Save Confirmation',
            'm3u_file': "File",
            'm3u_loadm3u': "Load M3U",
            'm3u_saveas': 'Save as',
            'm3u_find': 'find',
            'm3u_replacewith': 'replace with',
            'm3u_replaceall': "replace all",
            'm3u_deleterow': "delete row",
            'm3u_addrow': "add row",
            'm3u_movedown': "move down",
            'm3u_moveup': "move up",
            'm3u_filtergroup': 'filter group (press Enter)',
            'm3u_searchterm': "insert search term and press enter\n use Selector → to choose column to search",
            'm3u_choosecolumn': "choose column to search",
            'm3u_openfile': "Open File",
            'm3u_playlists': "Playlists (*.m3u)",
            'm3u_loaded': 'loaded',
            'm3u_savefile': 'Save File',
            'm3u_m3ufiles': 'M3U Files (*.m3u)',
            'error': 'Error',
            'playerror': 'Playing error',
            'error2': 'Astroncia IPTV error',
            'starting': 'starting',
            'binarynotfound': 'Binary modules not found!',
            'nocacheplaylist': 'Playlist caching off',
            'loadingplaylist': 'Loading playlist...',
            'playlistloaderror': 'Playlist loading error!',
            'playlistloaddone': 'Playling loading done!',
            'cachingplaylist': 'Caching playlist...',
            'playlistcached': 'Playlist cache saved!',
            'usingcachedplaylist': 'Using cached playlist',
            'settings': 'Settings',
            'help': 'Help',
            'channelsettings': 'Channel settings',
            'selectplaylist': 'Select m3u playlist',
            'selectepg': 'Select EPG file (XMLTV or JTV EPG)',
            'selectwritefolder': 'Select folder for recordings and screenshots',
            'deinterlace': 'Deinterlace',
            'useragent': 'User agent',
            'empty': 'None',
            'channel': 'Channel',
            'savesettings': 'Save settings',
            'save': 'Save',
            'm3uplaylist': 'M3U playlist',
            'updateatboot': 'Update\nat launch',
            'epgaddress': 'TV guide\naddress\n(XMLTV or JTV)',
            'udpproxy': 'UDP proxy',
            'writefolder': 'Folder for recordings\nand screenshots',
            'orselectyourprovider': 'Or select\nprovider',
            'resetchannelsettings': 'Reset channel settings and sorting',
            'notselected': 'Not selected',
            'close': 'Close',
            'nochannelselected': 'No channel selected',
            'pause': 'Pause',
            'play': 'Play',
            'exitfullscreen': 'To exit fullscreen mode press',
            'volume': 'Volume',
            'volumeoff': 'Volume off',
            'select': 'Select',
            'tvguide': 'TV guide',
            'startrecording': 'Start recording',
            'loading': 'Loading...',
            'doingscreenshot': 'Doing screenshot...',
            'screenshotsaved': 'Screenshot saved!',
            'screenshotsaveerror': 'Screenshot saving error!',
            'notvguideforchannel': 'No TV guide for channel',
            'preparingrecord': 'Preparing record',
            'nochannelselforrecord': 'No channel selected for record',
            'stop': 'Stop',
            'fullscreen': 'Fullscreen mode',
            'openrecordingsfolder': 'Open recordings folder',
            'record': 'Record',
            'screenshot': 'Screenshot',
            'prevchannel': 'Previous channel',
            'nextchannel': 'Next channel',
            'tvguideupdating': 'Updating TV guide...',
            'tvguideupdatingerror': 'TV guide update error!',
            'tvguideupdatingdone': 'TV guide update done!',
            'recordwaiting': 'Waiting for record',
            'allchannels': 'All channels',
            'favourite': 'Favourites',
            'interfacelang': 'Interface language',
            'tvguideoffset': 'TV guide offset',
            'hours': 'hours',
            'hwaccel': 'Hardware\nacceleration',
            'sort': 'Channel\nsort',
            'sortitems': ['as in playlist', 'alphabetical order', 'reverse alphabetical order', 'custom'],
            'donotforgetsort': 'Do not forget\nto set custom sort order in settings!',
            'moresettings': 'More settings',
            'lesssettings': 'Less settings',
            'enabled': 'enabled',
            'disabled': 'disabled',
            'seconds': 'seconds.',
            'cache': 'Cache',
            'chansearch': 'Search channel',
            'reconnecting': 'Reconnecting...',
            'group': 'Group',
            'hide': 'Hide channel',
            'contrast': 'Contrast',
            'brightness': 'Brightness',
            'hue': 'Hue',
            'saturation': 'Saturation',
            'gamma': 'Gamma',
            'timeshift': 'Timeshift',
            'jtvoffsetrecommendation': 'Recommended to set 0 here if JTV',
            'tab_main': 'Main',
            'tab_video': 'Video',
            'tab_network': 'Network',
            'tab_other': 'Other',
            'mpv_options': 'mpv options',
            'donotupdateepg': 'Do not update\nEPG at boot',
            'search': 'Search',
            'tab_gui': 'GUI',
            'epg_gui': 'TV guide\ninterface',
            'classic': 'Classic',
            'simple': 'Simple',
            'simple_noicons': 'Simple (no icons)',
            'update': 'Update',
            'bitrates': ['bps', 'kbps', 'Mbps', 'Gbps', 'Tbps'],
            'helptext': '''Astroncia IPTV, version {}    (c) kestral / astroncia

Cross-platform IPTV player

Supports TV guide (EPG) only in XMLTV and JTV formats!

Channel not working?
Right mouse button opens channel settings

Hotkeys:

F - fullscreen mode
M - mute
Q - quit program
Space - pause
S - stop playing
H - screenshot
G - tv guide (EPG)
R - start/stop record
P - previous channel
N - next channel
T - open/close channels list
O - show/hide clock
I - channel sort
E - timeshift (only on Linux)
            '''
        }
    },
    'ru': {
        'name': 'Русский',
        'strings': {
            'm3u_ready': "Готов",
            'm3u_m3ueditor': "Редактор плейлистов m3u",
            'm3u_noname': 'Нет имени',
            'm3u_waschanged': 'Плейлист был изменён.<br>Вы хотите сохранить изменения?',
            'm3u_saveconfirm': 'Подтверждение сохранения',
            'm3u_file': "Файл",
            'm3u_loadm3u': "Открыть плейлист M3U",
            'm3u_saveas': 'Сохранить как',
            'm3u_find': 'найти',
            'm3u_replacewith': 'заменить',
            'm3u_replaceall': "заменить всё",
            'm3u_deleterow': "удалить строку",
            'm3u_addrow': "добавить строку",
            'm3u_movedown': "вниз",
            'm3u_moveup': "наверх",
            'm3u_filtergroup': 'фильтр по группам (нажмите Enter)',
            'm3u_searchterm': "введите запрос поиска и нажмите enter\n используйте селектор → чтобы выбрать строку для поиска",
            'm3u_choosecolumn': "выберите строку для поиска",
            'm3u_openfile': "Открыть файл",
            'm3u_playlists': "Плейлисты (*.m3u)",
            'm3u_loaded': 'загружен',
            'm3u_savefile': 'Сохранить файл',
            'm3u_m3ufiles': 'M3U плейлисты (*.m3u)',
            'error': 'Ошибка',
            'playerror': 'Ошибка проигрывания',
            'error2': 'Ошибка Astroncia IPTV',
            'starting': 'запускается',
            'binarynotfound': 'Не найдены бинарные модули!',
            'nocacheplaylist': 'Кэширование плейлиста отключено',
            'loadingplaylist': 'Идёт загрузка плейлиста...',
            'playlistloaderror': 'Ошибка загрузки плейлиста!',
            'playlistloaddone': 'Загрузка плейлиста завершена!',
            'cachingplaylist': 'Кэширую плейлист...',
            'playlistcached': 'Кэш плейлиста сохранён!',
            'usingcachedplaylist': 'Использую кэшированный плейлист',
            'settings': 'Настройки',
            'help': 'Помощь',
            'channelsettings': 'Настройки канала',
            'selectplaylist': 'Выберите m3u плейлист',
            'selectepg': 'Выберите файл телепрограммы (XMLTV / JTV EPG)',
            'selectwritefolder': 'Выберите папку для записи и скриншотов',
            'deinterlace': 'Деинтерлейс',
            'useragent': 'User agent',
            'empty': 'Пустой',
            'channel': 'Канал',
            'savesettings': 'Сохранить настройки',
            'save': 'Сохранить',
            'm3uplaylist': 'M3U плейлист',
            'updateatboot': 'Обновлять\nпри запуске',
            'epgaddress': 'Адрес\nтелепрограммы\n(XMLTV / JTV)',
            'udpproxy': 'UDP прокси',
            'writefolder': 'Папка для записей\nи скриншотов',
            'orselectyourprovider': 'Или выберите\nпровайдера',
            'resetchannelsettings': 'Сбросить настройки каналов и сортировку',
            'notselected': 'не выбрано',
            'close': 'Закрыть',
            'nochannelselected': 'Не выбран канал',
            'pause': 'Пауза',
            'play': 'Воспроизвести',
            'exitfullscreen': 'Для выхода из полноэкранного режима нажмите клавишу',
            'volume': 'Громкость',
            'volumeoff': 'Громкость выкл.',
            'select': 'Выбрать',
            'tvguide': 'Телепрограмма',
            'startrecording': 'Начать запись',
            'loading': 'Загрузка...',
            'doingscreenshot': 'Делаю скриншот...',
            'screenshotsaved': 'Скриншот сохранён!',
            'screenshotsaveerror': 'Ошибка создания скриншота!',
            'notvguideforchannel': 'Нет телепрограммы для канала',
            'preparingrecord': 'Подготовка записи',
            'nochannelselforrecord': 'Не выбран канал для записи',
            'stop': 'Стоп',
            'fullscreen': 'Полноэкранный режим',
            'openrecordingsfolder': 'Открыть папку записей',
            'record': 'Запись',
            'screenshot': 'Скриншот',
            'prevchannel': 'Предыдущий канал',
            'nextchannel': 'Следующий канал',
            'tvguideupdating': 'Обновление телепрограммы...',
            'tvguideupdatingerror': 'Ошибка обновления телепрограммы!',
            'tvguideupdatingdone': 'Обновление телепрограммы завершено!',
            'recordwaiting': 'Ожидание записи',
            'allchannels': 'Все каналы',
            'favourite': 'Избранное',
            'interfacelang': 'Язык интерфейса',
            'tvguideoffset': 'Общая поправка',
            'hours': 'часов',
            'hwaccel': 'Аппаратное\nускорение',
            'sort': 'Сортировка\nканалов',
            'sortitems': ['как в плейлисте', 'по алфавиту', 'по алфавиту в обратном порядке', 'пользовательская'],
            'donotforgetsort': 'Не забудьте указать\nпользовательскую сортировку в настройках!',
            'moresettings': 'Больше настроек!',
            'lesssettings': 'Меньше настроек!',
            'enabled': 'включено',
            'disabled': 'выключено',
            'seconds': 'секунд.',
            'cache': 'Кэш',
            'chansearch': 'Поиск по каналам',
            'reconnecting': 'Переподключение...',
            'group': 'Группа',
            'hide': 'Скрыть канал',
            'contrast': 'Контраст',
            'brightness': 'Яркость',
            'hue': 'Оттенок',
            'saturation': 'Насыщенность',
            'gamma': 'Гамма',
            'timeshift': 'Таймшифт',
            'jtvoffsetrecommendation': 'Рекомендуется указать 0, если JTV',
            'tab_main': 'Общие',
            'tab_video': 'Видео',
            'tab_network': 'Сеть',
            'tab_other': 'Прочее',
            'mpv_options': 'mpv опции',
            'donotupdateepg': 'Не обновлять\nEPG при запуске',
            'search': 'Поиск',
            'tab_gui': 'Интерфейс',
            'epg_gui': 'Вид\nтелепрограммы',
            'classic': 'Классический',
            'simple': 'Упрощённый',
            'simple_noicons': 'Упрощённый (без иконок)',
            'update': 'Обновить',
            'bitrates': ['бит/с', 'Кбит/с', 'Мбит/с', 'Гбит/с', 'Тбит/с'],
            'helptext': '''Astroncia IPTV, версия {}    (c) kestral / astroncia

Поддержка:
https://forum.ubuntu.ru/index.php?topic=314803

Кроссплатформенный плеер
для просмотра интернет-телевидения

Поддерживается телепрограмма (EPG)
только в форматах XMLTV и JTV!

Не работает канал? Правая клавиша мыши открывает настройки канала.

После указания группы в настройках переоткройте приложение.

Если у Вас плейлист IPTV от вашего интернет-провайдера (не приватный),
прошу скинуть мне на эл.почту:
kestraly (at) gmail.com
адрес плейлиста, адрес EPG (если есть), название провайдера, город.
Добавлю в приложение.

Горячие клавиши:

F - полноэкранный режим
M - выключить звук
Q - выйти из программы
Пробел/ПКМ - пауза
S - остановить проигрывание
H - скриншот
G - телепрограмма
R - начать/остановить запись
P - предыдущий канал
N - следующий канал
T - показать/скрыть список каналов
O - показать/скрыть часы
I - сортировка каналов
E - таймшифт (только для Linux)
            '''
        }
    }
}
