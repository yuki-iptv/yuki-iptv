# Astroncia IPTV
### Кроссплатформенный плеер для просмотра интернет-телевидения

![Интерфейс](https://s8.hostingkartinok.com/uploads/images/2021/04/c5ae434d884088779a645d1f8b8d5685.png)  

## Информация

**32-битная Windows не поддерживается!**  

Программа предоставляется **как есть**, никаких гарантий.  

## Скачать

**[Версия для Windows](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/Astroncia_IPTV_setup.exe)**  
[AppImage](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-appimage-x86_64.AppImage)  
[deb-пакет](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv.deb)  

Для Ubuntu рекомендуется установка из [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  

## Возможности

Просмотр IPTV от вашего провайдера (если он предоставляет m3u8 плейлист)  
Просмотр незашифрованных потоков UDP (мультикаст), HTTP, HLS (m3u8)  
Добавление каналов в избранное  
Запись телепередач (не умеет: записывать по расписанию)  
Горячие клавиши  
Поддержка телепрограммы (EPG) в форматах XMLTV и JTV  
Группы каналов  

## Зависимости

- Python 3 (3.6 или более новая версия)
- Qt 5
- libmpv1 (>= 0.27.2)
- PyQt5 (python3-pyqt5)
- Pillow (python3-pil)
- Tkinter (python3-tk)
- pandas (python3-pandas)
- python3-requests
- ffmpeg

## Установка

**Устанавливаем зависимости:**

на Debian/Ubuntu:  
```sudo apt install ffmpeg git libmpv1 python3 python3-requests python3-pyqt5 python3-pil python3-tk python3-pandas python3-pip python3-setuptools python3-dev qt5-default python3-wheel```

на Windows:  
Устанавливаем Git с [официального сайта](https://git-scm.com/download/win)  
Устанавливаем Python 3 с [официального сайта](https://www.python.org/downloads/windows/) - Windows Installer (64-bit) (Recommended)  
(**поставьте галочку Add Python 3 to PATH при установке**)  

**Клонируем репозиторий:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

ИЛИ  

```git clone --depth=1 https://github.com/rootalc/astroncia_iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

**Устанавливаем иконки для телеканалов:**  

```git clone --depth=1 https://gitlab.com/astroncia/channel-icons.git```  
```cp -R channel-icons/* data/```  

**Устанавливаем Python модули:**  

```python3 -m pip install -r requirements.txt```  

**Устанавливаем бинарные зависимости (только для Windows):**

Скачайте файлы  
[ffmpeg.exe](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/ffmpeg.exe)  
[mpv-1.dll](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/mpv-1.dll)  
и поместите их в папку **astroncia_iptv\data\modules\binary**

**Запускаем:**

на Windows: запускайте файл ```start_windows.vbs```  
( можете создать ярлык: **ПКМ** -> **Отправить** -> **Рабочий стол (создать ярлык)** )

на Linux: ```./start_linux.sh```

## Просмотр записей

Для записей телепередач используется контейнер MKV  
Для просмотра записей рекомендуется использовать [VLC media player](https://www.videolan.org/).  

## Обновление программы

Удалите папку local в astroncia_iptv  
```git pull```  
