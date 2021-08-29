# pylint: disable=no-else-return, inconsistent-return-statements
import math

def format_bytes(B, hbnames):
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

def convert_size(size_bytes):
    return format_bytes(size_bytes, ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"])

def human_secs(scds):
    hrs = scds // (60*60)
    scds %= (60*60)
    mnts = scds // 60
    scds %= 60
    return "%02i:%02i:%02i" % (hrs, mnts, scds)
