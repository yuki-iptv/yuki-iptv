import logging
import zipfile
import io
import datetime
import struct

logger = logging.getLogger(__name__)


def ft_to_dt(time, settings):
    '''Convert filetime to datetime'''
    if len(time) == 8:
        datetime_ret = round(
            (
                datetime.datetime(1601, 1, 1) + datetime.timedelta(
                    microseconds=struct.unpack("<Q", time)[0] / 10
                )
            ).timestamp() + (3600 * settings["epgoffset"])
        )
    else:
        logger.warning("broken JTV time detected!")
        datetime_ret = 0
    return datetime_ret


def unpack_struct(inf1):
    '''Unpack data struct'''
    return struct.unpack('<H', inf1[0:2])[0]


def parse_titles(inf1, encoding="cp1251"):
    '''Parse titles'''
    jtv_headers = [
        b"JTV 3.x TV Program Data\x0a\x0a\x0a",
        b"JTV 3.x TV Program Data\xa0\xa0\xa0"
    ]
    if inf1[0:26] not in jtv_headers:
        raise Exception('Not a JTV')
    inf1 = inf1[26:]
    titles = []
    while inf1:
        title_length = int(unpack_struct(inf1))
        inf1 = inf1[2:]
        title = inf1[0:title_length].decode(encoding)
        inf1 = inf1[title_length:]
        titles.append(title)
    return titles


def parse_schedule(inf1, settings):
    '''Parse schedule'''
    schedules = []
    records_num = unpack_struct(inf1)
    inf1 = inf1[2:]
    i = 0
    while i < records_num:
        i += 1
        record = inf1[0:12]
        inf1 = inf1[12:]
        schedules.append(ft_to_dt(record[2:-2], settings))
    return schedules


def fix_zip_filename(filename):
    '''Fix zip filename (encoding)'''
    try:
        name_unicode = str(
            bytes(filename, encoding='cp437'),
            encoding='cp866'
        )
    except UnicodeEncodeError:
        name_unicode = filename
    return name_unicode


def parse_jtv(jtv_inf1, settings):
    '''Main parse function'''
    logger.info("Trying parsing as JTV...")
    zip_file = zipfile.ZipFile(io.BytesIO(jtv_inf1), "r")
    array = {}
    for fileinfo in zip_file.infolist():
        file_name = fix_zip_filename(fileinfo.filename)
        if file_name.endswith('.pdt'):
            file_name1 = file_name[0:-4].replace('_', ' ')
            if file_name1 not in array:
                array[file_name1] = {}
            try:
                array[file_name1]['titles'] = parse_titles(zip_file.read(fileinfo))
            except:
                # Support UTF-8 encoding
                array[file_name1]['titles'] = parse_titles(zip_file.read(fileinfo), 'utf-8')
        if file_name.endswith('.ndx'):
            file_name1 = file_name[0:-4].replace('_', ' ')
            if file_name1 not in array:
                array[file_name1] = {}
            array[file_name1]['schedules'] = parse_schedule(zip_file.read(fileinfo), settings)
    array_out = {}
    for chan in array:
        array_out[chan] = []
        count1 = -1
        for title in array[chan]['titles']:
            count1 += 1
            start_dt = array[chan]['schedules'][count1]
            try:
                stop_dt = array[chan]['schedules'][count1 + 1]
                try:
                    title = bytes(title, 'cp1251').decode('utf-8')
                except:
                    pass
                array_out[chan].append({
                    'start': start_dt,
                    'stop': stop_dt,
                    'title': title,
                    'desc': ' '
                })
            except:
                pass
    return array_out
