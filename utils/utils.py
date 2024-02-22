#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 15:29
# FileName:

import datetime
import hashlib
import os
import time
from typing import Union

import pytz


def now_time(*, fmt="%Y-%m-%d %H:%M:%S", tz="Asia/Shanghai"):
    return datetime.datetime.strftime(datetime.datetime.now(pytz.timezone(tz)), fmt)


def time2str(t: Union[int, float] = None, *, fmt: str = "%Y-%m-%d %H:%M:%S", tz: str = "Asia/Shanghai") -> str:
    """
    时间timestamp转字符串
    :param t: 时间戳
    :param fmt:
    :param tz: 时区
    :return:
    """
    tz = pytz.timezone(tz)
    dt = datetime.datetime.fromtimestamp(time.time() if t is None else t, tz=tz)
    return dt.strftime(fmt)


def str2time(t: str = None, *, fmt: str = "%Y-%m-%d %H:%M:%S", tz: str = "Asia/Shanghai") -> float:
    """
    字符串转时间戳
    :param t: 时间字符串
    :param fmt:
    :param tz: 时区
    :return:
    """
    if t is None:
        return time.time()

    tz = pytz.timezone(tz)

    # dt = datetime.datetime.strptime(t, fmt).replace(tzinfo=tz).astimezone(tz)  # 上海时间会差6分钟
    dt = datetime.datetime.strptime(t, fmt)
    dt = tz.localize(dt)

    return dt.timestamp()


def get_delay_date(date_str: str = None, fmt="%Y-%m-%d", delay: int = 0, tz: str = "Asia/Shanghai") -> str:
    """
    获取指定日期的几日前或后的日期
    :param date_str: 日期，默认为当前日期。
    :param fmt: date_str的格式
    :param delay: 间隔天数。正数为往后，负数为往前。
    :param tz: date_str为空时的时区
    :return:
    """
    if date_str is None:
        date_str = now_time(fmt=fmt, tz=tz)
    delay_date = datetime.datetime.strptime(date_str, fmt) + datetime.timedelta(days=delay)
    return datetime.datetime.strftime(delay_date, "%Y-%m-%d")


def get_delay_month(delay, date_str: str = None, fmt="%Y-%m-%d", tz: str = "Asia/Shanghai") -> str:
    """
    获取指定日期的几月前或后的日期
    :param delay: 间隔月份。正数为往后，负数为往前。
    :param date_str: 日期，默认为当前日期。
    :param fmt: date_str的格式
    :param tz: date_str为空时的时区
    :return:
    """
    if date_str is None:
        date_str = now_time(fmt=fmt, tz=tz)
    dt = datetime.datetime.strptime(date_str, fmt)
    year_offset = (dt.month + delay - 1) // 12
    month = (dt.month + delay - 1) % 12 + 1
    year = dt.year + year_offset
    months_ago = dt.replace(year=year, month=month)
    return datetime.datetime.strftime(months_ago, "%Y-%m-%d")


def get_delay(a, b, fmt="%Y-%m-%d") -> int:
    """
    获取两日期的相差数。a - b
    :param a:
    :param b:
    :param fmt:
    :return:
    """
    delay = datetime.datetime.strptime(a, fmt) - datetime.datetime.strptime(b, fmt)
    return delay.days


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def gen_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
