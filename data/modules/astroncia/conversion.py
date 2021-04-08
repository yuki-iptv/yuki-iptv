'''File size conversion'''
import math

def convert_size(size_bytes):
    '''File size conversion from bytes to human-readable value'''
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i_i = int(math.floor(math.log(size_bytes, 1024)))
    p_p = math.pow(1024, i_i)
    s_s = round(size_bytes / p_p)
    return "%s %s" % (s_s, size_name[i_i])
