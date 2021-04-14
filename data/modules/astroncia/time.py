import datetime

def print_with_time(str2):
    try:
        cur_time = datetime.datetime.today().strftime('%H:%M:%S')
        print('[{}] {}'.format(cur_time, str2))
    except: # pylint: disable=bare-except
        pass
