# Astroncia IPTV
### IPTV player with EPG support

[![Screenshot](https://gitlab.com/astroncia/iptv/uploads/3af0979a9fcf688332b995475689a60f/astronciaiptv-screenshot-thumbnail.png)](https://gitlab.com/astroncia/iptv/uploads/5d36d4b259c0d2a5781603867d0f2454/astronciaiptv-screenshot.png)  
  
⚠️ Disclaimer: Astroncia IPTV doesn't provide any playlists or other digital content.  
The channels and pictures in the screenshots are for demonstration purposes only.  

## Download

Downloads (deb/rpm) are available on [Releases](https://gitlab.com/astroncia/iptv/-/releases) page.  
  
For **Ubuntu** / **Linux Mint** recommended install from [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository -y ppa:astroncia/iptv```  
```sudo apt update```  
```sudo apt install astronciaiptv```  
  
[Installation for **Debian**](https://software.opensuse.org/download/package?package=astronciaiptv&project=home%3Aastroncia)  
  
[**Arch Linux** (AUR) - astronciaiptv](https://aur.archlinux.org/packages/astronciaiptv/)  
[**Arch Linux** (AUR) - astronciaiptv-git](https://aur.archlinux.org/packages/astronciaiptv-git/)  

## Information

Software provided **as is**, no guarantees.  

## License

Code: [GPL-3.0-only](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING)  
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
- TV archive / catchup  
- Internalization  
- MPRIS support  

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
