import os
import re
import json
import locale
import ctypes
import re
from pathlib import Path
from data.modules.astroncia.lang import lang, _
from data.modules.astroncia.extgrp import parse_extgrp

class M3uParser:
    
    def __init__(self, udp_proxy):
        self.files = []
        self.udp_proxy = udp_proxy
        LANG_LOCALE = '?'
        try:
            if os.name == 'nt':
                try:
                    loc = locale.windows_locale[ctypes.windll.kernel32.GetUserDefaultUILanguage()]
                except: # pylint: disable=bare-except
                    loc = locale.getdefaultlocale()[0]
            else:
                loc = locale.getdefaultlocale()[0]
            LANG_LOCALE = loc.split("_")[0]
        except: # pylint: disable=bare-except
            pass
        print("System locale: {}".format(LANG_LOCALE))
        LANG_DEFAULT = LANG_LOCALE if LANG_LOCALE in lang else 'en'
        try:
            settings_file0 = open(str(Path('local', 'settings.json')), 'r', encoding="utf8")
            settings_lang0 = json.loads(settings_file0.read())['lang']
            settings_file0.close()
        except:
            settings_lang0 = LANG_DEFAULT

        LANG = lang[settings_lang0]['strings'] if settings_lang0 in lang else lang[LANG_DEFAULT]['strings']
        self.allchannels = _('allchannels')
    
    #Read the file from the given path
    def readM3u(self, filename):
        self.epg_url = ''
        self.filename = filename
        self.readAllLines()
        self.parseFile()
        self.epg_array = []
        for chan_1 in self.files:
            tvgurl = chan_1['tvg-url']
            if tvgurl:
                if not tvgurl in self.epg_array:
                    self.epg_array.append(tvgurl)
        if self.epg_array and not self.epg_url:
            self.epg_url = '^^::MULTIPLE::^^' + ':::^^^:::'.join(self.epg_array)
        return [self.files, self.epg_url]

    #Read all file lines
    def readAllLines(self):
        self.lines = [line.rstrip('\n').rstrip() for line in self.filename.strip().split('\n')]
        if not self.lines[-1]:
            self.lines.pop()
        if self.lines[0].startswith('#EXTM3U'):
            self.epg_url = ""
            if 'x-tvg-url="' in self.lines[0]:
                try:
                    self.epg_url = re.findall('x-tvg-url="(.*?)"', self.lines[0])[0]
                except: # pylint: disable=bare-except
                    pass
            else:
                if 'tvg-url="' in self.lines[0]:
                    try:
                        self.epg_url = re.findall('tvg-url="(.*?)"', self.lines[0])[0]
                    except: # pylint: disable=bare-except
                        pass
                else:
                    try:
                        self.epg_url = re.findall('url-tvg="(.*?)"', self.lines[0])[0]
                    except: # pylint: disable=bare-except
                        pass
            # No dead URLs, please
            self.epg_url = self.epg_url if self.epg_url != 'http://server/jtv.zip' else ''
            self.lines.pop(0)
        self.lines = [x.rstrip() for x in self.lines if not x.startswith('#EXTVLCOPT:')]
        self.lines = ['#EXTM3U'] + [x0 for x0 in self.lines if x0]
        self.lines = parse_extgrp(self.lines)
        return len(self.lines)
    
    def parseFile(self):
        numLine = len(self.lines)
        for n in range(numLine):
            line = self.lines[n]
            if line[0] == "#":
                self.manageLine(n)
    
    def manageLine(self, n):
        lineInfo = self.lines[n]
        lineLink = self.lines[n+1]
        if lineInfo != "#EXTM3U":
            m = re.search("tvg-name=\"(.*?)\"", lineInfo)
            try:
                name = m.group(1)
            except AttributeError:
                name = ""
            m = re.search("tvg-id=\"(.*?)\"", lineInfo)
            try:
                id = m.group(1)
            except AttributeError:
                id = ""
            m = re.search("tvg-logo=\"(.*?)\"", lineInfo)
            try:
                logo = m.group(1)
            except AttributeError:
                logo = ""
            m = re.search("tvg-url=\"(.*?)\"", lineInfo)
            try:
                tvg_url = m.group(1)
            except AttributeError:
                tvg_url = ""
            m = re.search("group-title=\"(.*?)\"", lineInfo)
            try:
                group = m.group(1)
            except AttributeError:
                group = self.allchannels
            if not group:
                group = self.allchannels
            m = re.search("[,](?!.*[,])(.*?)$", lineInfo)
            try:
                title = m.group(1)
            except AttributeError:
                title = ""
            # ~ print(name+"||"+id+"||"+logo+"||"+group+"||"+title)

            up = self.udp_proxy
            if up and (lineLink.startswith('udp://') or lineLink.startswith('rtp://')):
                lineLink = up + "/" + lineLink.replace("udp://", "udp/").replace("rtp://", "rtp/")
                lineLink = lineLink.replace('//udp/', '/udp/').replace('//rtp/', '/rtp/')    

            test = {
                "title": title,
                "tvg-name": name,
                "tvg-ID": id,
                "tvg-logo": logo,
                "tvg-group": group,
                "tvg-url": tvg_url,
                "url": lineLink
            }
            self.files.append(test)
