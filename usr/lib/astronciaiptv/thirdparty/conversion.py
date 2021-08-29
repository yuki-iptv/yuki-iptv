# pylint: disable=no-else-return, inconsistent-return-statements
import math

def format_bytes(bytes, hbnames):
   idx = 0
   while bytes >= 1024 and idx+1 < len(hbnames):
      bytes = bytes / 1024
      idx += 1
   return f"{bytes:.1f} {hbnames[idx]}"

def convert_size(size_bytes):
    return format_bytes(size_bytes, ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"])

def human_secs(scds):
    hrs = scds // (60*60)
    scds %= (60*60)
    mnts = scds // 60
    scds %= 60
    return "%02i:%02i:%02i" % (hrs, mnts, scds)
