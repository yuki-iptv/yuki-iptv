import time

def print_with_time(str2):
    try:
        cur_time = time.strftime('%H:%M:%S', time.localtime())
        print('[{}] {}'.format(cur_time, str2))
    except: # pylint: disable=bare-except
        pass
