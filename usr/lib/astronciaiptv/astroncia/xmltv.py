# pylint: disable=missing-module-docstring
import gzip
import lzma
import time
import datetime
import xml.etree.ElementTree as ET
from astroncia.time import print_with_time

def parse_xmltv_date(date_str):
    '''Parse date - convert it to UTC and back to current timezone'''
    time_zone = date_str[-5:]
    dt_notz = date_str[:-6]
    offset_tz = int(time_zone)
    if offset_tz:
        if offset_tz < 0:
            sign_tz = -1
            offset_tz = -offset_tz
        else:
            sign_tz = 1
        offset_tz = sign_tz * ((offset_tz // 100) * 3600 + (offset_tz % 100) * 60)
    time1 = datetime.datetime.strptime(dt_notz, '%Y%m%d%H%M%S')
    time1 -= datetime.timedelta(seconds=offset_tz)
    time1 = time1.timestamp() + (
        3600 * (
            (time.timezone if (time.localtime().tm_isdst == 0) else time.altzone) / 60 / 60 * -1
        )
    )
    return time1

def parse_as_xmltv(epg, settings, catchup_days1): # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    '''Load EPG file'''
    print_with_time("Trying parsing as XMLTV...")
    print_with_time("catchup-days = {}".format(catchup_days1))
    try:
        tree = ET.ElementTree(ET.fromstring(epg))
    except ET.ParseError:
        try:
            print_with_time("Trying to unpack as gzip...")
            tree = ET.ElementTree(ET.fromstring(gzip.decompress(epg)))
        except: # pylint: disable=bare-except
            print_with_time("Trying to unpack as xz...")
            tree = ET.ElementTree(ET.fromstring(
                lzma.LZMADecompressor().decompress(epg)
            ))
    ids = {}
    programmes_epg = {}
    icons = {}
    for channel_epg in tree.findall('./channel'): # pylint: disable=too-many-nested-blocks
        for display_name in channel_epg.findall('./display-name'):
            if not channel_epg.attrib['id'].strip() in ids:
                ids[channel_epg.attrib['id'].strip()] = []
            ids[channel_epg.attrib['id'].strip()].append(display_name.text.strip())
            try:
                all_icons = channel_epg.findall('./icon')
                if all_icons:
                    for icon in all_icons:
                        try:
                            if 'src' in icon.attrib:
                                icons[display_name.text.strip()] = icon.attrib['src'].strip()
                        except: # pylint: disable=bare-except
                            pass
            except: # pylint: disable=bare-except
                pass
    for programme in tree.findall('./programme'):
        try:
            start = parse_xmltv_date(programme.attrib['start']) + (3600 * settings["epgoffset"])
        except: # pylint: disable=bare-except
            start = 0
        try:
            stop = parse_xmltv_date(programme.attrib['stop']) + (3600 * settings["epgoffset"])
        except: # pylint: disable=bare-except
            stop = 0
        try:
            chans = ids[programme.attrib['channel'].strip()]
            catchup_id = ''
            try:
                if 'catchup-id' in programme.attrib:
                    catchup_id = programme.attrib['catchup-id']
            except: # pylint: disable=bare-except
                pass
            for channel_epg_1 in chans:
                day_start = (
                    datetime.datetime.now() - datetime.timedelta(days=catchup_days1)
                ).replace(
                    hour=0, minute=0, second=0
                ).timestamp() + (3600 * settings["epgoffset"])
                day_end = (
                    datetime.datetime.now() + datetime.timedelta(days=1)
                ).replace(
                    hour=23, minute=59, second=59
                ).timestamp() + (3600 * settings["epgoffset"])
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
                        "desc": prog_desc,
                        'catchup-id': catchup_id
                    })
        except: # pylint: disable=bare-except
            pass
    return [programmes_epg, ids, icons]
