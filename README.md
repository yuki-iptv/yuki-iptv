# Astroncia IPTV
### IPTV player with EPG support

[![Screenshot](https://gitlab.com/astroncia/iptv/uploads/b59522369ccba3c99f349e397d102c0b/astroncia-iptv-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/uploads/9cb6c1e462a679117f36e67ec98ec8b0/astroncia-iptv-screenshot.png)  

## Download

Downloads (deb/rpm) are available on [Releases](https://gitlab.com/astroncia/iptv/-/releases) page.  
  
For **Ubuntu** / **Linux Mint** recommended install from [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository -y ppa:astroncia/iptv```  
```sudo apt update```  
```sudo apt install astroncia-iptv```  
  
[Installation for **Debian**](https://software.opensuse.org/download/package?package=astronciaiptv&project=home%3Aastroncia)  
  
[**Arch Linux** (AUR) - astronciaiptv](https://aur.archlinux.org/packages/astronciaiptv/)  
[**Arch Linux** (AUR) - astronciaiptv-git](https://aur.archlinux.org/packages/astronciaiptv-git/)  

## Information

Software provided **as is**, no guarantees.  

Repository mirrors:  
[GitLab](https://gitlab.com/astroncia/iptv) (**main repository**)  
[Bitbucket](https://bitbucket.org/astroncia/astroncia-iptv/src/master/)  
[Codeberg](https://codeberg.org/astroncia/iptv)  

## License

Code: [GPLv3](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING)  
Icons: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
  
*Icons by [Font Awesome](https://fontawesome.com/)*  

## Features

- Watching IPTV (from m3u / m3u8 / xspf playlist, local or remote)  
- XTream API support
- Viewing unencrypted streams UDP (multicast), HTTP, HLS (m3u8)  
- Adding channels to favorites  
- Recording TV programs  
- Hotkeys  
- Channel search  
- TV program (EPG) support in XMLTV and JTV formats  
- Display of technical information - video / audio codec, bit rate, resolution  
- Channel groups (from playlist and custom)  
- Hide channels  
- Sorting channels  
- Video settings for each channel - contrast, brightness, hue, saturation, gamma  
- Change user agent for each channel  
- M3U playlist editor  
- TV archive  
- Internalization  
- MPRIS support (and remote control using KDE Connect)  

## Requirements

- [Qt](https://www.qt.io/) 6.2.2 or newer *(or Qt 5.12 or newer)*
- [libmpv1](https://mpv.io/) 0.27.2 or newer
- [ffmpeg](https://ffmpeg.org/) 3.4.8 or newer
- [Python](https://www.python.org/) 3.6 or newer
- [PyQt6](https://pypi.org/project/PyQt6/) 6.2.2 or newer *(or [PyQt5](https://pypi.org/project/PyQt5/) 5.12 or newer)*
- [Pillow](https://pypi.org/project/Pillow/) (python3-pil)
- [pandas](https://pypi.org/project/pandas/) (python3-pandas)
- [PyGObject](https://pypi.org/project/PyGObject/) (python3-gi)
- [pydbus](https://pypi.org/project/pydbus/) (python3-pydbus)
- [Unidecode](https://pypi.org/project/Unidecode/) (python3-unidecode)
- [requests](https://pypi.org/project/requests/) (python3-requests)
- [chardet](https://pypi.org/project/chardet/) (python3-chardet)
- [setproctitle](https://pypi.org/project/setproctitle/) (python3-setproctitle)

## TV Channels and media content

Astroncia IPTV does not provide content or TV channels, it is a player application which streams from IPTV providers.  
  
By default, Astroncia IPTV is configured with one IPTV provider called Free-TV: [https://github.com/Free-TV/IPTV](https://github.com/Free-TV/IPTV).  
  
This provider was chosen because it satisfied the following criterias:  
  
- It only includes free, legal, publicly available content  
- It groups TV channels by countries  
- It doesn't include adult content  
  
Issues relating to TV channels and media content should be addressed directly to the relevant provider.  
  
Note: Feel free to remove Free-TV from Astroncia IPTV if you don't use it, or add any other provider you may have access to or local M3U / XSPF playlists.  
