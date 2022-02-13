# pylint: disable=missing-module-docstring
# SPDX-License-Identifier: GPL-3.0-only
import os
import glob
import gettext
from pathlib import Path
#from astroncia.time import print_with_time

class LangData: # pylint: disable=too-few-public-methods
    '''Class for not using globals'''
    delimiter = '/'

LangData.lang_folder = str(Path(os.getcwd(), '..', '..', 'share', 'locale'))
#LangData.languages = os.listdir(LangData.lang_folder)
LangData.languages = [l1.split(LangData.delimiter)[::-1][2] for l1 in \
    glob.glob(str(Path(LangData.lang_folder, '*', 'LC_MESSAGES', 'astronciaiptv.mo')))]
#print_with_time("Available languages: {}".format(str(LangData.languages)))
#print_with_time("")
LangData.current_lang = 'en'
lang = {}

LangData.en = None
try:
    LangData.en = gettext.translation('astronciaiptv', LangData.lang_folder, languages=['en'])
except: # pylint: disable=bare-except
    pass

for language in LangData.languages:
    t = gettext.translation('astronciaiptv', LangData.lang_folder, languages=[language])
    lang[language] = {'strings': {
        "lang_id": language,
        "lang_gettext": t,
        "name": t.gettext("name")
    }}

def init_lang(lng):
    '''Set global lang to specified'''
    LangData.current_lang = lng

def _(str1):
    gettext_output = lang[LangData.current_lang]['strings']['lang_gettext'].gettext(str1)
    if LangData.en:
        if str1 == gettext_output:
            gettext_output = LangData.en.gettext(str1)
    return gettext_output

def __(str2, str3, num1):
    gettext_output = lang[LangData.current_lang]['strings']['lang_gettext'].ngettext(
        str2, str3, num1
    )
    if LangData.en:
        if str2 == gettext_output or not gettext_output:
            gettext_output = LangData.en.ngettext(str2, str3, num1)
    return gettext_output
