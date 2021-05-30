# Astroncia IPTV
### Cross-platform IPTV player

[![license](https://img.shields.io/badge/license-GPL%20v.3-green.svg)](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING) [![PPA](https://img.shields.io/badge/PPA-available-green.svg)](https://launchpad.net/~astroncia/+archive/ubuntu/iptv) [![AUR](https://img.shields.io/aur/version/astronciaiptv)](https://aur.archlinux.org/packages/astronciaiptv/)  

[![GUI](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-en-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-en-screenshot.png)  

## Download

**[Version for Windows](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/Astroncia_IPTV_setup.exe)**  
[deb package](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv.deb)  
[rpm package](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv.rpm)  
  
[rpm package for OpenSUSE](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-opensuse.rpm)  
[rpm package without dependencies](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-nodeps.rpm)  
  
For Ubuntu **recommended** install from [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv -y```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  
  
[Arch Linux (AUR)](https://aur.archlinux.org/packages/astronciaiptv/)  

## Channel icons (nonfree)

[deb](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-channel-icons.deb) | [rpm](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-channel-icons.rpm)  

or execute this command to install:  
```curl -L --output - 'https://gitlab.com/astroncia/channel-icons/-/archive/master/channel-icons-master.tar.gz' | sudo tar -C /usr/share/AstronciaIPTV/ -zxvf - && sudo mv /usr/share/AstronciaIPTV/channel-icons-master/* /usr/share/AstronciaIPTV/data/ && sudo rmdir /usr/share/AstronciaIPTV/channel-icons-master```  

## Information

**32-bit Windows not supported!**  

Software provided **as is**, no guarantees.  

Repository mirrors:  
[GitLab](https://gitlab.com/astroncia/iptv)  
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
Timeshift  
M3U playlist editor  

## Dependencies

- Python 3 (3.6 or newer version)
- Qt 5
- libmpv1 (>= 0.27.2)
- PyQt5 (python3-pyqt5)
- Pillow (python3-pil)
- pandas (python3-pandas)
- PyGObject (python3-gi)
- Python D-Bus (python3-pydbus)
- python3-unidecode
- python3-requests
- ffmpeg

## Installation

**Installing dependencies:**

on Debian/Ubuntu:  
```sudo apt update && sudo apt install ffmpeg git libmpv1 python3 python3-requests python3-pyqt5 python3-pil python3-pandas python3-gi python3-unidecode python3-pydbus python3-pip python3-setuptools python3-dev python3-wheel```

on Windows:  
Install Git from [official website](https://git-scm.com/download/win)  
Install Python 3 from [official website](https://www.python.org/downloads/windows/) - Windows Installer (64-bit) (Recommended)  
(**Check 'Add Python 3 to PATH' at install**)  

**Cloning repository:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

**Installing channel icons:**  

```git clone --depth=1 https://gitlab.com/astroncia/channel-icons.git```  
```cp -R channel-icons/* data/```  

**Installing Python modules:**  

on GNU/Linux:  
```python3 -m pip install -r requirements.txt```  

on Windows:  
```python -m pip install -r requirements.txt```  

**Installing binary dependenices (only for Windows):**

Download files  
[ffmpeg.exe](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/ffmpeg.exe)  
[mpv-1.dll](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/mpv-1.dll)  
and put to folder **astroncia_iptv\data\modules\binary**  

**Starting:**

on Windows: open file ```start_windows.vbs```  

on GNU/Linux: ```./start_linux.sh```

## View recordings

MKV container used for recordings  
For recordings view recommended [VLC media player](https://www.videolan.org/).  

## Program update

```git pull https://gitlab.com/astroncia/iptv.git```  

## Disclaimer

Astroncia IPTV doesn't provide any playlists or other digital content.  
