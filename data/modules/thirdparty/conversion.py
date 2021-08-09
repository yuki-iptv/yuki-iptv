# pylint: disable=no-else-return, inconsistent-return-statements
import math

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i_i = int(math.floor(math.log(size_bytes, 1024)))
    p_p = math.pow(1024, i_i)
    s_s = round(size_bytes / p_p)
    return "%s %s" % (s_s, size_name[i_i])

def humanbytes(B, hbnames):
    B = float(B)
    kilobytes = float(1024)
    megabytes = float(kilobytes ** 2)
    gigabytes = float(kilobytes ** 3)
    terabytes = float(kilobytes ** 4)
    if B < kilobytes:
        return '{0} {1}'.format(B, hbnames[0] if 0 == B > 1 else hbnames[0])
    elif kilobytes <= B < megabytes:
        return '{0:.2f}'.format(B/kilobytes) + " " + hbnames[1]
    elif megabytes <= B < gigabytes:
        return '{0:.2f}'.format(B/megabytes) + " " + hbnames[2]
    elif gigabytes <= B < terabytes:
        return '{0:.2f}'.format(B/gigabytes) + " " + hbnames[3]
    elif terabytes <= B:
        return '{0:.2f}'.format(B/terabytes) + " " + hbnames[4]

def format_seconds_to_hhmmss(seconds_dat):
    '''Formating seconds to HH:MM:SS'''
    hours_dat = seconds_dat // (60*60)
    seconds_dat %= (60*60)
    minutes_dat = seconds_dat // 60
    seconds_dat %= 60
    return "%02i:%02i:%02i" % (hours_dat, minutes_dat, seconds_dat)
