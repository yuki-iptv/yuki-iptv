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
lang_folder = str(Path(os.getcwd(), 'data', 'lang'))
languages = os.listdir(lang_folder)
lang = {}

po_filename_en = str(Path(lang_folder, 'en', 'LC_MESSAGES', 'astronciaiptv.po'))
po_file_en = open(po_filename_en, 'r', encoding="utf8")
po_contents_en = [x.rstrip().replace('msgid "', '')[:-1] for x in po_file_en.readlines() if x.startswith('msgid "') and x != 'msgid ""\n']
po_file_en.close()
en = gettext.translation('astronciaiptv', lang_folder, languages=['en'])
for language in languages:
    po_filename = str(Path(lang_folder, language, 'LC_MESSAGES', 'astronciaiptv.po'))
    po_file = open(po_filename, 'r', encoding="utf8")
    po_contents = [x.rstrip().replace('msgid "', '')[:-1] for x in po_file.readlines() if x.startswith('msgid "') and x != 'msgid ""\n']
    po_file.close()
    lang[language] = {'strings': {}}
    t = gettext.translation('astronciaiptv', lang_folder, languages=[language])
    for string_literal in po_contents_en:
        if string_literal in po_contents:
            lang[language]['strings'][string_literal] = t.gettext(string_literal)
        else:
            print("[TRANSLATION] Literal '{}' not found in language '{}'".format(string_literal, language))
            lang[language]['strings'][string_literal] = en.gettext(string_literal)
