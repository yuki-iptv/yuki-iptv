# pylint: disable=missing-module-docstring, missing-function-docstring
# SPDX-License-Identifier: GPL-3.0-only
import os
import os.path
import locale
import gettext
from pathlib import Path
from yuki_iptv.time import print_with_time

class LangData: # pylint: disable=too-few-public-methods
    '''Class for not using globals'''
    LOCALE_CHANGED = False

def init_lang():
    '''Set global lang to specified'''
    lang = 'en'

    local_dir = Path(os.environ['HOME'], '.config', 'yuki-iptv')
    if not os.path.isdir(Path(os.environ['HOME'], '.config')):
        os.mkdir(Path(os.environ['HOME'], '.config'))
    if not os.path.isdir(local_dir):
        os.mkdir(local_dir)
    if not os.path.isfile(Path(local_dir, 'locale.txt')):
        locale_txt = open(Path(local_dir, 'locale.txt'), 'w', encoding='utf-8')
        locale_txt.write(lang + "\n")
        locale_txt.close()
        old_locale = lang
    else:
        locale_txt = open(Path(local_dir, 'locale.txt'), 'r', encoding='utf-8')
        old_locale = locale_txt.read().strip()
        locale_txt.close()

    try:
        locale.setlocale(locale.LC_ALL, "")
        lang = locale.getlocale(locale.LC_MESSAGES)[0]
    except: # pylint: disable=bare-except
        print_with_time("Failed to determine system locale, using default (en)")

    if lang != old_locale:
        locale_txt = open(Path(local_dir, 'locale.txt'), 'w', encoding='utf-8')
        locale_txt.write(lang + "\n")
        locale_txt.close()
        LangData.LOCALE_CHANGED = True

    print_with_time("Locale: {}".format(lang))

    LangData.el = gettext.translation(
        'yuki-iptv',
        str(Path(os.getcwd(), '..', '..', 'share', 'locale')),
        languages=[lang]
    )
    LangData.el.install()

init_lang()

LOCALE_CHANGED = LangData.LOCALE_CHANGED
_ = LangData.el.gettext

def ngettext(str2, str3, num1):
    ret = LangData.el.ngettext(str2, str3, num1)
    if not ret:
        ret = str2
    return ret
