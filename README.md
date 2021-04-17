# Astroncia IPTV
### Кроссплатформенный плеер для просмотра интернет-телевидения

![Интерфейс](https://img10.lostpic.net/2021/04/16/5e7f7e4f98bd11cecd2594be7420b75f.png)  

## Информация

**32-битная Windows не поддерживается!**  

Программа предоставляется **как есть**, никаких гарантий.  

## Лицензия

Код: GPLv3  
Иконки: CC BY 3.0  

## Скачать

**[Версия для Windows](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/Astroncia_IPTV_setup.exe)**  
[AppImage](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-appimage-x86_64.AppImage)  
[deb-пакет](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv.deb)  
[rpm-пакет](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/astroncia-iptv-0.0.13-2.noarch.rpm)  

Для Ubuntu рекомендуется установка из [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  

## Возможности

Просмотр IPTV (из m3u8 плейлиста)  
Просмотр незашифрованных потоков UDP (мультикаст), HTTP, HLS (m3u8)  
Добавление каналов в избранное  
Запись телепередач (не умеет: записывать по расписанию)  
Горячие клавиши  
Поиск по каналам  
Поддержка телепрограммы (EPG) в форматах XMLTV и JTV  
Отображение технической информации - видео/аудио кодек, битрейт, разрешение  
Группы каналов (из плейлиста и кастомные)  
Скрытие каналов  
Сортировка каналов  
Настройки видео для каждого канала - контраст, яркость, оттенок, насыщенность, гамма  
Смена user agent для каждого канала  
Таймшифт  
Редактор m3u плейлистов  

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
