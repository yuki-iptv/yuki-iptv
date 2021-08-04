# Astroncia IPTV
### Плеер для просмотра интернет-телевидения

[![license](https://img.shields.io/badge/license-GPL%20v.3-green.svg)](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING) [![PPA](https://img.shields.io/badge/PPA-available-green.svg)](https://launchpad.net/~astroncia/+archive/ubuntu/iptv) [![AUR](https://img.shields.io/aur/version/astronciaiptv)](https://aur.archlinux.org/packages/astronciaiptv/) [![Packaging status](https://repology.org/badge/tiny-repos/astronciaiptv.svg)](https://repology.org/project/astronciaiptv/versions)  
  
[![Интерфейс](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot.png)  

## Скачать

**[Версия для Windows](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/Astroncia_IPTV_setup.exe)**  
deb и rpm пакеты доступны в [Releases](https://gitlab.com/astroncia/iptv/-/releases)  
  
Для Ubuntu / Linux Mint **рекомендуется** установка из [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv -y```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  
  
[Arch Linux (AUR)](https://aur.archlinux.org/packages/astronciaiptv/)  

## Информация

**32-битная Windows не поддерживается!**  

Программа предоставляется **как есть**, никаких гарантий.  

Зеркала репозитория:  
[GitLab](https://gitlab.com/astroncia/iptv)  
[Bitbucket](https://bitbucket.org/astroncia/astroncia-iptv/src/master/)  
[Codeberg](https://codeberg.org/astroncia/iptv)  

## Лицензия

Код: [GPLv3](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING)  
Иконки: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)  
  
*Иконки от [Font Awesome](https://fontawesome.com/)*  

## Возможности

Просмотр IPTV (из m3u8 плейлиста)  
Просмотр незашифрованных потоков UDP (мультикаст), HTTP, HLS (m3u8)  
Добавление каналов в избранное  
Запись телепередач  
Горячие клавиши  
Поиск по каналам  
Поддержка телепрограммы (EPG) в форматах XMLTV и JTV  
Отображение технической информации - видео/аудио кодек, битрейт, разрешение  
Группы каналов (из плейлиста и кастомные)  
Скрытие каналов  
Сортировка каналов  
Настройки видео для каждого канала - контраст, яркость, оттенок, насыщенность, гамма  
Смена user agent для каждого канала  
Редактор m3u плейлистов  
TV архив  

## Зависимости

- Python 3 (3.6 или более новая версия)
- Qt 5
- libmpv1 (>= 0.27.2)
- PyQt5 (python3-pyqt5)
- Pillow (python3-pil)
- pandas (python3-pandas)
- PyGObject (python3-gi)
- python3-pydbus
- python3-unidecode
- python3-requests
- ffmpeg

## Установка

**Устанавливаем зависимости:**

на Debian/Ubuntu:  
```sudo apt update && sudo apt install ffmpeg git libmpv1 python3 python3-requests python3-pyqt5 python3-pil python3-pandas python3-gi python3-unidecode python3-pydbus python3-pip python3-setuptools python3-dev python3-wheel```

на Windows:  
Устанавливаем Git с [официального сайта](https://git-scm.com/download/win)  
Устанавливаем Python 3 с [официального сайта](https://www.python.org/downloads/windows/) - Windows Installer (64-bit) (Recommended)  
(**поставьте галочку Add Python 3 to PATH при установке**)  

**Клонируем репозиторий:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astroncia_iptv```  
```cd astroncia_iptv```  

**Устанавливаем логотипы телеканалов (необязательно):**  

```git clone --depth=1 https://gitlab.com/astroncia/channel-icons.git```  
```cp -R channel-icons/* data/```  

**Устанавливаем Python модули:**  

на GNU/Linux:  
```python3 -m pip install -r requirements.txt```  

на Windows:  
```python -m pip install -r requirements.txt```  

**Устанавливаем бинарные зависимости (только для Windows):**

Скачайте файлы  
[ffmpeg.exe](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/ffmpeg.exe)  
[mpv-1.dll](https://gitlab.com/astroncia/iptv-binary-deps/-/raw/master/mpv-1.dll)  
и поместите их в папку **astroncia_iptv\data\modules\binary**

**Создание файлов переводов (для Windows придётся генерировать mo файлы вручную):**  
  
```make```  

**Запускаем:**

на Windows: запускайте файл ```start_windows.vbs```  
( можете создать ярлык: **ПКМ** -> **Отправить** -> **Рабочий стол (создать ярлык)** )

на GNU/Linux: ```./start_linux.sh```

## Просмотр записей

Для записей телепередач используется контейнер MKV  
Для просмотра записей рекомендуется использовать [VLC media player](https://www.videolan.org/).  

## Обновление программы

```git pull https://gitlab.com/astroncia/iptv.git```  

## Отказ от ответственности

Astroncia IPTV не предоставляет плейлисты или другой цифровой контент.  

## Логотипы телеканалов (несвободные)

[deb](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.4.deb) | [rpm](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.4-1.noarch.rpm)  

или выполните следующую команду, чтобы установить:  
```curl -L --output - 'https://gitlab.com/astroncia/channel-icons/-/archive/master/channel-icons-master.tar.gz' | sudo tar -C /usr/lib/astronciaiptv/ -zxvf - && sudo mv /usr/lib/astronciaiptv/channel-icons-master/* /usr/lib/astronciaiptv/data/ && sudo rmdir /usr/lib/astronciaiptv/channel-icons-master```  

*Все права на логотипы телеканалов принадлежат их правообладателям.*  
