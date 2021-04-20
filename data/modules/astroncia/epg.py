'''Astroncia IPTV - EPG parsing'''
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
# pylint: disable=broad-except, too-many-locals, import-error
import os
import datetime
import requests
from data.modules.astroncia.ua import user_agent
from data.modules.astroncia.jtv import parse_jtv
from data.modules.astroncia.xmltv import parse_as_xmltv
from data.modules.astroncia.time import print_with_time

def load_epg(settings):
    '''Load EPG file'''
    print_with_time("Loading EPG...")
    if os.path.isfile(settings['epg']):
        epg_file = open(settings['epg'], 'rb')
        epg = epg_file.read()
        epg_file.close()
    else:
        epg = requests.get(
            settings['epg'],
            headers={'User-Agent': user_agent},
            stream=True,
            timeout=35
        ).content
    print_with_time("EPG loaded")
    return epg

def fetch_epg(settings):
    '''Parsing EPG'''
    programmes_epg = {}
    prog_ids = {}
    epg_ok = True
    exc = None
    try:
        epg = load_epg(settings)
        try:
            pr_xmltv = parse_as_xmltv(epg, settings)
            programmes_epg = pr_xmltv[0]
            prog_ids = pr_xmltv[1]
        except: # pylint: disable=bare-except
            programmes_epg = parse_jtv(epg, settings)
        print_with_time("Parsing done!")
        print_with_time("Parsing EPG...")
    except Exception as exc0:
        epg_ok = False
        exc = exc0
    print_with_time("Parsing EPG done!")
    return [{}, programmes_epg, epg_ok, exc, prog_ids]

def worker(procnum, sys_settings, return_dict1): # pylint: disable=unused-argument
    '''Worker running from multiprocess'''
    epg = fetch_epg(sys_settings)
    return_dict1[0] = epg[0]
    return_dict1[1] = epg[1]
    return_dict1[2] = True
    return_dict1[3] = epg[2]
    return_dict1[4] = epg[3]
    return_dict1[5] = epg[4]
