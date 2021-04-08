'''Astroncia IPTV - EPG parsing'''
# pylint: disable=broad-except, too-many-locals, import-error
import os
import gzip
import datetime
import xml.etree.ElementTree as ET
import requests
from data.modules.astroncia.ua import user_agent

def load_epg(settings):
    '''Load EPG file'''
    if os.path.isfile(settings['epg']):
        epg_file = open(settings['epg'], 'rb')
        epg = epg_file.read()
        epg_file.close()
    else:
        epg = requests.get(
            settings['epg'],
            headers={'User-Agent': user_agent},
            stream=True,
            timeout=5
        ).content
    try:
        tree = ET.ElementTree(ET.fromstring(epg))
    except ET.ParseError:
        tree = ET.ElementTree(ET.fromstring(gzip.decompress(epg)))
    return tree

def fetch_epg(settings):
    '''Parsing EPG'''
    ids = {}
    programmes_epg = {}
    epg_ok = True
    exc = None
    try:
        tree = load_epg(settings)
        for channel_epg in tree.findall('./channel'):
            for display_name in channel_epg.findall('./display-name'):
                if not channel_epg.attrib['id'] in ids:
                    ids[channel_epg.attrib['id']] = []
                ids[channel_epg.attrib['id']].append(display_name.text)
        for programme in tree.findall('./programme'):
            start = datetime.datetime.strptime(
                programme.attrib['start'].split(" ")[0], '%Y%m%d%H%M%S'
            ).timestamp()
            stop = datetime.datetime.strptime(
                programme.attrib['stop'].split(" ")[0], '%Y%m%d%H%M%S'
            ).timestamp()
            chans = ids[programme.attrib['channel']]
            for channel_epg_1 in chans:
                day_start = (
                    datetime.datetime.now() - datetime.timedelta(days=1)
                ).replace(hour=0, minute=0, second=0).timestamp()
                day_end = (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).replace(hour=23, minute=59, second=59).timestamp()
                if not channel_epg_1 in programmes_epg:
                    programmes_epg[channel_epg_1] = []
                if start > day_start and stop < day_end:
                    try:
                        prog_title = programme.find('./title').text
                    except: # pylint: disable=bare-except
                        prog_title = ""
                    try:
                        prog_desc = programme.find('./desc').text
                    except: # pylint: disable=bare-except
                        prog_desc = ""
                    programmes_epg[channel_epg_1].append({
                        "start": start,
                        "stop": stop,
                        "title": prog_title,
                        "desc": prog_desc
                    })
    except Exception as exc0:
        epg_ok = False
        exc = exc0
    return [{}, programmes_epg, epg_ok, exc]

def worker(procnum, sys_settings, return_dict1): # pylint: disable=unused-argument
    '''Worker running from multiprocess'''
    epg = fetch_epg(sys_settings)
    return_dict1[0] = epg[0]
    return_dict1[1] = epg[1]
    return_dict1[2] = True
    return_dict1[3] = epg[2]
    return_dict1[4] = epg[3]
