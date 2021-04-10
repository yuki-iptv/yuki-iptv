'''Astroncia IPTV - EPG parsing'''
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
    epg_ok = True
    exc = None
    try:
        epg = load_epg(settings)
        try:
            programmes_epg = parse_as_xmltv(epg, settings)
        except: # pylint: disable=bare-except
            programmes_epg = parse_jtv(epg, settings)
        print_with_time("Parsing done!")
        print_with_time("Parsing EPG...")
    except Exception as exc0:
        epg_ok = False
        exc = exc0
    print_with_time("Parsing EPG done!")
    return [{}, programmes_epg, epg_ok, exc]

def worker(procnum, sys_settings, return_dict1): # pylint: disable=unused-argument
    '''Worker running from multiprocess'''
    epg = fetch_epg(sys_settings)
    return_dict1[0] = epg[0]
    return_dict1[1] = epg[1]
    return_dict1[2] = True
    return_dict1[3] = epg[2]
    return_dict1[4] = epg[3]
