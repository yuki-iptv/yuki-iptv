# Astroncia IPTV
### IPTV player with EPG support

[![license](https://img.shields.io/badge/license-GPL%20v.3-green.svg)](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING) [![PPA](https://img.shields.io/badge/PPA-available-green.svg)](https://launchpad.net/~astroncia/+archive/ubuntu/iptv) [![AUR](https://img.shields.io/aur/version/astronciaiptv)](https://aur.archlinux.org/packages/astronciaiptv/) [![Packaging status](https://repology.org/badge/tiny-repos/astronciaiptv.svg)](https://repology.org/project/astronciaiptv/versions)  

[![GUI](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot.png)  

## Download

deb and rpm packages available in [Releases](https://gitlab.com/astroncia/iptv/-/releases)  
  
For Ubuntu / Linux Mint **recommended** install from [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv -y```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  
  
[Arch Linux (AUR)](https://aur.archlinux.org/packages/astronciaiptv/)  

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

## Capabilities

Watching IPTV (from m3u8 playlist)  
Viewing unencrypted streams UDP (multicast), HTTP, HLS (m3u8)  
Adding channels to favorites  
Recording TV programs  
Hotkeys  
Channel search  
TV program (EPG) support in XMLTV and JTV formats  
Display of technical information - video / audio codec, bit rate, resolution  
Channel groups (from playlist and custom)  
Hide channels  
Sorting channels  
Video settings for each channel - contrast, brightness, hue, saturation, gamma  
Change user agent for each channel  
M3U playlist editor  
TV archive  

## Dependencies

- Python 3 *(3.6 or newer version)*
- Qt 6 *(or Qt 5)*
- libmpv1 (>= 0.27.2)
- [PySide6](https://pypi.org/project/PySide6/) *(or PyQt5)*
- [Pillow](https://pypi.org/project/Pillow/) (python3-pil)
- [pandas](https://pypi.org/project/pandas/) (python3-pandas)
- [PyGObject](https://pypi.org/project/PyGObject/) (python3-gi)
- [pydbus](https://pypi.org/project/pydbus/) (python3-pydbus)
- [Unidecode](https://pypi.org/project/Unidecode/) (python3-unidecode)
- [requests](https://pypi.org/project/requests/) (python3-requests)
- [ffmpeg](https://ffmpeg.org/)

## Installation

**Installing dependencies:**

on Debian/Ubuntu:  
```sudo apt update && sudo apt install ffmpeg git libmpv1 python3 python3-requests python3-pil python3-pandas python3-gi python3-unidecode python3-pydbus python3-pip python3-setuptools python3-dev python3-wheel```

**Cloning repository:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astronciaiptv```  
```cd astronciaiptv```  

**Installing Python modules:**  

```python3 -m pip install -r requirements.txt```  

**Create translation files:**  
  
```make```  

**Starting:**

```./start_linux.sh```

## View recordings

MKV container used for recordings  
For recordings view recommended [VLC media player](https://www.videolan.org/).  

## Program update

```git pull https://gitlab.com/astroncia/iptv.git```  

## Disclaimer

Astroncia IPTV doesn't provide any playlists or other digital content.  

## Channel logos (nonfree)

[deb](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.7.deb) | [rpm](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.7-1.noarch.rpm)  

or execute this command to install:  
```curl -L --output - 'https://gitlab.com/astroncia/channel-icons/-/archive/master/channel-icons-master.tar.gz' | sudo tar -C /usr/lib/astronciaiptv/ -zxvf - && sudo mv /usr/lib/astronciaiptv/channel-icons-master/* /usr/share/astronciaiptv/ && sudo rmdir /usr/lib/astronciaiptv/channel-icons-master```  

*All rights to the logos of TV channels belong to their copyright holders.*  
