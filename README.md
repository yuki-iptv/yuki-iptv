# yuki-iptv

**IPTV player with EPG support (Astroncia IPTV fork)**

[![Screenshot](https://gist.githubusercontent.com/Ame-chan-angel/c37f80c2cb00afbdbd98959186e1ab80/raw/e59228169ace1634fae96f65aace5f4d2d7fa71c/screenshot.png)](https://gist.githubusercontent.com/Ame-chan-angel/c37f80c2cb00afbdbd98959186e1ab80/raw/e59228169ace1634fae96f65aace5f4d2d7fa71c/screenshot.png)

⚠️ Disclaimer: yuki-iptv doesn't provide content or TV channels,  
it is a player application which streams from IPTV providers.  
The channels and pictures in the screenshots are for demonstration purposes only.

## Content

- [Repository mirrors](#repository-mirrors)
- [Features](#features)
- [Ubuntu PPA](#ubuntu-ppa)
- [Open Build Service (rpm packages)](#open-build-service-rpm-packages)
- [Unofficial builds](#unofficial-builds)
- [HowTo make playlists for movies/series](#howto-make-playlists-for-moviesseries)
- [License](#license)
- [Localization](#localization)

## Repository mirrors

[GitHub](https://github.com/yuki-iptv/yuki-iptv) **(main repository)**  
[GitLab](https://gitlab.com/yuki-iptv/yuki-iptv)  
[Codeberg](https://codeberg.org/yuki-iptv/yuki-iptv)  

## Features

- M3u / M3u8 / XSPF playlists support
- XTream API support
- Viewing unencrypted streams UDP (multicast), HTTP, HLS (M3u8)
- TV program (EPG) support in XMLTV and JTV formats
- Save channels as favorites
- Stream recording
- Hotkeys
- Channel search
- Display of technical information - video / audio codec, bitrate, resolution
- Channel groups (from playlist and custom)
- Hide channels
- Sorting channels
- Video settings for each channel - contrast, brightness, hue, saturation, gamma
- Change user agent / HTTP Referer for each channel
- M3u playlist editor
- TV archive / catchup
- MPRIS support
- and many more...

## Ubuntu PPA

Develop PPA: https://launchpad.net/~yuki-iptv/+archive/ubuntu/yuki-iptv-develop  
```
sudo add-apt-repository ppa:yuki-iptv/yuki-iptv-develop
sudo apt update
sudo apt install yuki-iptv
```

## Open Build Service (rpm packages)

https://software.opensuse.org/download.html?project=home%3Aame-chan%3Ayuki-iptv&package=yuki-iptv  
  
**Multimedia codecs:**  
For **Fedora** and **CentOS** you'll need https://rpmfusion.org  
For **openSUSE** you'll need **libopenh264-7** (for h264 decoding) (run ```zypper install libopenh264-7``` as root)  

## Unofficial builds

**Might be outdated!**  
**Use at your own risk!**  
  
AUR: https://aur.archlinux.org/packages/yuki-iptv  
Flatpak: https://flathub.org/apps/io.github.yuki_iptv.yuki-iptv  
(**Known Flatpak issue: [Channel logos not working](https://github.com/flathub/io.github.yuki_iptv.yuki-iptv/issues/3)**)

## HowTo make playlists for movies/series
  
Use group **VOD** for movies  
example:  
  
```
#EXTM3U
#EXTINF:-1 group-title="VOD",Channel 1
https://example.com
#EXTINF:-1 group-title="VOD SomeGroup",Channel 2
https://example.com
```
  
Use **ExxSxx** in your playlist to get it shown as series.  
  
- S01E12 = Season 1 Episode 12  
  
example:  
  
```
#EXTM3U
#EXTINF:-1 tvg-name="SomeName S04E06 Season Title 1" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E06.mp4
#EXTINF:-1 tvg-name="SomeName S04E07 Season Title 2" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E07.mp4
#EXTINF:-1 tvg-name="SomeName S04E09 Season Title 3" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E09.mp4
#EXTINF:-1 tvg-name="SomeName S04E10 Season Title 4" group-title="SERIES SomeName",
file:///home/user/Videos/SomeName_4/SomeName.S04E10.mp4
```

## License

```monospace
yuki-iptv is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

yuki-iptv is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with yuki-iptv. If not, see <https://www.gnu.org/licenses/>.
```

[Clarification](https://github.com/yuki-iptv/yuki-iptv/blob/master/LICENSE-NOTICE.txt)

```monospace
The Font Awesome pictograms are licensed under the CC BY 4.0 License.
Font Awesome Free 5.15.4 by @fontawesome - https://fontawesome.com
License - https://creativecommons.org/licenses/by/4.0/
```

## Localization

To help with localization you can use [Crowdin](https://crowdin.com/project/yuki-iptv) or create pull request with translated .po file.  
To add a new language, write me on the Crowdin page.
