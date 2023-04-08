# yuki-iptv
### IPTV player with EPG support (Astroncia IPTV fork)

[![Screenshot](https://gist.githubusercontent.com/yuki-chan-nya/c37f80c2cb00afbdbd98959186e1ab80/raw/71a5c9c177130154a7bd1ad31d7465096cc102bb/yuki-iptv.png)](https://gist.githubusercontent.com/yuki-chan-nya/c37f80c2cb00afbdbd98959186e1ab80/raw/71a5c9c177130154a7bd1ad31d7465096cc102bb/yuki-iptv.png)  
  
⚠️ Disclaimer: yuki-iptv doesn't provide any playlists or other digital content.  
The channels and pictures in the screenshots are for demonstration purposes only.  
  
**Looking for testers and translators!**

## Download

[Ubuntu Launchpad PPA (stable)](https://launchpad.net/~yuki-iptv/+archive/ubuntu/yuki-iptv-stable):  
```
sudo add-apt-repository ppa:yuki-iptv/yuki-iptv-stable
sudo apt update
sudo apt install yuki-iptv
```

[Ubuntu Launchpad PPA (develop)](https://launchpad.net/~yuki-iptv/+archive/ubuntu/yuki-iptv-develop):  
```
sudo add-apt-repository ppa:yuki-iptv/yuki-iptv-develop
sudo apt update
sudo apt install yuki-iptv
```

[Arch Linux AUR (stable)](https://aur.archlinux.org/packages/yuki-iptv)  
[Arch Linux AUR (develop)](https://aur.archlinux.org/packages/yuki-iptv-git)  

## License

Code: [GPL-3.0-or-later](https://github.com/yuki-chan-nya/yuki-iptv/blob/stable/COPYING)  
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
- Change user agent / HTTP Referer for each channel  
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
