# Astroncia IPTV
### IPTV player with EPG support

[![Screenshot](https://gitlab.com/astroncia/iptv/uploads/b59522369ccba3c99f349e397d102c0b/astroncia-iptv-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/uploads/9cb6c1e462a679117f36e67ec98ec8b0/astroncia-iptv-screenshot.png)  

## Download

Downloads are available on [Releases](https://gitlab.com/astroncia/iptv/-/releases) page.  
  
For **Ubuntu** / **Linux Mint** recommended install from [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv -y```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  
  
[Installation for **Debian**](https://software.opensuse.org/download/package?package=astronciaiptv&project=home%3Aastroncia)  
  
[**Arch Linux** (AUR)](https://aur.archlinux.org/packages/astronciaiptv/)  

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

## Requirements

- Qt 6 *(or Qt 5)*
- libmpv1 (>= 0.27.2)
- [ffmpeg](https://ffmpeg.org/)
- Python 3 (>= 3.6)
- [PySide6](https://pypi.org/project/PySide6/) *(or PyQt5)*
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
  
Note: Feel free to remove Free-TV from Astroncia IPTV if you don't use it, or add any other provider you may have access to or local M3U playlists.  
