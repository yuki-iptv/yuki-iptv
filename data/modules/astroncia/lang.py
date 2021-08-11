'''
Copyright (C) 2021 Astroncia

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
import gettext
from pathlib import Path

class LangData: # pylint: disable=too-few-public-methods
    '''Class for not using globals'''

LangData.lang_folder = str(Path(os.getcwd(), 'data', 'lang'))
LangData.languages = [
    y for y in os.listdir(LangData.lang_folder) if y not \
        in ('astronciaiptv.pot', 'update_translations.sh')
]
LangData.current_lang = 'en'
lang = {}

LangData.en = gettext.translation('astronciaiptv', LangData.lang_folder, languages=['en'])

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
    if str1 == gettext_output:
        gettext_output = LangData.en.gettext(str1)
    return gettext_output
