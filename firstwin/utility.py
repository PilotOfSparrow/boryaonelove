import datetime


def formatted_current_time():
    cur_year = str(datetime.datetime.now().strftime('%Y'))
    cur_month = str(datetime.datetime.now().strftime('%m'))
    cur_day = str(datetime.datetime.now().strftime('%d'))
    cur_hour = str(datetime.datetime.now().strftime('%H'))
    cur_min = str(datetime.datetime.now().strftime('%M'))
    cur_sec = str(datetime.datetime.now().strftime('%S'))
    cur_time = '%s-%s-%s-%s-%s-%s' % (cur_year, cur_month, cur_day, cur_hour, cur_min, cur_sec)

    return cur_time
