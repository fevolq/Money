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


def get_delay_date(date_str: str = None, fmt="%Y-%m-%d", delay: int = 0, tz: str = "Asia/Shanghai"):
    """
    获取指定日期的几日前或后的日期
    :param date_str: 日期，默认为当前日期。
    :param fmt: date_str的格式
    :param delay: 间隔天数。正数为往后，负数为往前。
    :param tz: date_str为空时的时区
    :return:
    """
    if date_str is None:
        date_str = time2str(fmt="%Y-%m-%d", tz=tz)
    delay_date = datetime.datetime.strptime(date_str, fmt) + datetime.timedelta(days=delay)
    return datetime.datetime.strftime(delay_date, "%Y-%m-%d")


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def gen_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
