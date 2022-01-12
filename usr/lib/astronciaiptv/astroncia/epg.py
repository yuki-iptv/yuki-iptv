'''Astroncia IPTV - EPG parsing'''
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
# pylint: disable=broad-except, too-many-locals, import-error
import os
import datetime
import requests
from astroncia.ua import uas
from astroncia.jtv import parse_jtv
from astroncia.xmltv import parse_as_xmltv
from astroncia.time import print_with_time

def load_epg(epg_url, user_agent):
    '''Load EPG file'''
    print_with_time("Loading EPG...")
    print_with_time("Address: '{}'".format(epg_url))
    if os.path.isfile(epg_url):
        epg_file = open(epg_url, 'rb')
        epg = epg_file.read()
        epg_file.close()
    else:
        epg = requests.get(
            epg_url,
            headers={'User-Agent': user_agent},
            stream=True,
            timeout=35
        ).content
    print_with_time("EPG loaded")
    return epg

def merge_two_dicts(x, y):
    z = x.copy()
    z.update(y)
    return z

def fetch_epg(settings):
    '''Parsing EPG'''
    programmes_epg = {}
    prog_ids = {}
    epg_ok = True
    exc = None
    epg_failures = []
    epg_exceptions = []
    epg_icons = {}
    epg_settings_url = [settings['epg']]
    if epg_settings_url[0].startswith('^^::MULTIPLE::^^'):
        epg_settings_url = epg_settings_url[0].replace('^^::MULTIPLE::^^', '').split(':::^^^:::')
    for epg_url_1 in epg_settings_url:
        try:
            epg = load_epg(epg_url_1, uas[settings["useragent"]])
            try:
                pr_xmltv = parse_as_xmltv(epg, settings)
                programmes_epg = merge_two_dicts(programmes_epg, pr_xmltv[0])
                prog_ids = pr_xmltv[1]
            except: # pylint: disable=bare-except
                programmes_epg = merge_two_dicts(programmes_epg, parse_jtv(epg, settings))
            try:
                epg_icons = pr_xmltv[2]
            except: # pylint: disable=bare-except
                pass
            epg_failures.append(False)
            print_with_time("Parsing done!")
            print_with_time("Parsing EPG...")
        except Exception as exc0:
            print_with_time("Failed parsing EPG!")
            epg_failures.append(True)
            epg_exceptions.append(exc0)
    if not False in epg_failures:
        epg_ok = False
        exc = epg_exceptions[0]
    print_with_time("Parsing EPG done!")
    return [{}, programmes_epg, epg_ok, exc, prog_ids, epg_icons]

def worker(procnum, sys_settings, return_dict1): # pylint: disable=unused-argument
    '''Worker running from multiprocess'''
    epg = fetch_epg(sys_settings)
    return_dict1[0] = epg[0]
    return_dict1[1] = epg[1]
    return_dict1[2] = True
    return_dict1[3] = epg[2]
    return_dict1[4] = epg[3]
    return_dict1[5] = epg[4]
    return_dict1[6] = epg[5]
