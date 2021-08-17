# Astroncia IPTV
### Плеер для просмотра интернет-телевидения

[![license](https://img.shields.io/badge/license-GPL%20v.3-green.svg)](https://gitlab.com/astroncia/iptv/-/blob/master/COPYING) [![PPA](https://img.shields.io/badge/PPA-available-green.svg)](https://launchpad.net/~astroncia/+archive/ubuntu/iptv) [![AUR](https://img.shields.io/aur/version/astronciaiptv)](https://aur.archlinux.org/packages/astronciaiptv/) [![Packaging status](https://repology.org/badge/tiny-repos/astronciaiptv.svg)](https://repology.org/project/astronciaiptv/versions)  
  
[![Интерфейс](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot-thumb.png)](https://gitlab.com/astroncia/iptv/-/raw/master/screenshots/astroncia-iptv-screenshot.png)  

## Скачать

deb и rpm пакеты доступны в [Releases](https://gitlab.com/astroncia/iptv/-/releases)  
  
Для Ubuntu / Linux Mint **рекомендуется** установка из [Launchpad PPA - ppa:astroncia/iptv](https://launchpad.net/~astroncia/+archive/ubuntu/iptv):  
```sudo add-apt-repository ppa:astroncia/iptv -y```  
```sudo apt-get update```  
```sudo apt-get install astroncia-iptv```  
  
[Arch Linux (AUR)](https://aur.archlinux.org/packages/astronciaiptv/)  

## Информация

Программа предоставляется **как есть**, никаких гарантий.  

Зеркала репозитория:  
[GitLab](https://gitlab.com/astroncia/iptv) (**основной репозиторий**)  
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

**Клонируем репозиторий:**

```git clone --depth=1 https://gitlab.com/astroncia/iptv.git astronciaiptv```  
```cd astronciaiptv```  

**Устанавливаем логотипы телеканалов (необязательно):**  

```git clone --depth=1 https://gitlab.com/astroncia/channel-icons.git```  
```cp -R channel-icons/* usr/share/astronciaiptv/```  

**Устанавливаем Python модули:**  

```python3 -m pip install -r requirements.txt```  

**Создание файлов переводов:**  
  
```make```  

**Запускаем:**

```./start_linux.sh```

## Просмотр записей

Для записей телепередач используется контейнер MKV  
Для просмотра записей рекомендуется использовать [VLC media player](https://www.videolan.org/).  

## Обновление программы

```git pull https://gitlab.com/astroncia/iptv.git```  

## Отказ от ответственности

Astroncia IPTV не предоставляет плейлисты или другой цифровой контент.  

## Логотипы телеканалов (несвободные)

[deb](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.7.deb) | [rpm](https://gitlab.com/astroncia/iptv-binaries/-/raw/master/chanicons/astroncia-iptv-channel-icons-0.0.7-1.noarch.rpm)  

или выполните следующую команду, чтобы установить:  
```curl -L --output - 'https://gitlab.com/astroncia/channel-icons/-/archive/master/channel-icons-master.tar.gz' | sudo tar -C /usr/lib/astronciaiptv/ -zxvf - && sudo mv /usr/lib/astronciaiptv/channel-icons-master/* /usr/share/astronciaiptv/ && sudo rmdir /usr/lib/astronciaiptv/channel-icons-master```  

*Все права на логотипы телеканалов принадлежат их правообладателям.*  
