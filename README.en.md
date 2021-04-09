# Astroncia IPTV
### Cross-platform IPTV player

## Information

**32-bit Windows not supported!**  

Software provided **as is**, no guarantees.  

Repository mirrors:  
[https://gitlab.com/astroncia/iptv](https://gitlab.com/astroncia/iptv)  
[https://github.com/rootalc/astroncia_iptv](https://github.com/rootalc/astroncia_iptv)  

## Dependencies

- Python 3 (3.7 or newer version)
- Qt 5
- libmpv
- PyQt5 (python3-pyqt5)
- Pillow (python3-pil)
- Tkinter (python3-tk)
- python3-requests
- ffmpeg

## Installation

**Installing dependencies:**

on Debian/Ubuntu:  
```sudo apt install ffmpeg git libmpv1 python3 python3-requests python3-pyqt5 python3-pil python3-tk```

on Windows:  
Install Git from [official website](https://git-scm.com/download/win)  
Install Python 3 from [official website](https://www.python.org/downloads/windows/) - Windows Installer (64-bit) (Recommended)  
(**Check 'Add Python 3 to PATH' at install**)  

**Cloning repository:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

OR  

```git clone --depth=1 https://github.com/rootalc/astroncia_iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

**Installing Python modules:**  

```pip3 install -r requirements.txt```  

**Installing binary dependenices (only for Windows):**

Download files  
[ffmpeg.exe](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/ffmpeg.exe)  
[mpv-1.dll](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/mpv-1.dll)  
and put to folder **astroncia_iptv\data\modules\binary**  

**Starting:**

on Windows: open file ```start_windows.vbs```  

on Linux: ```./start_linux.sh```

## View recordings

MKV container used for recordings  
For recordings view recommended [VLC media player](https://www.videolan.org/).  

## Program update

Delete folder local in astroncia_iptv  
```git pull```  
