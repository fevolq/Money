#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 15:29
# FileName:

import datetime
import hashlib
import os
import time

import pytz


def asia_local_time(fmt="%Y-%m-%d %H:%M:%S", tz="Asia/Shanghai"):
    return datetime.datetime.strftime(datetime.datetime.now(pytz.timezone(tz)), fmt)


def time2str(t=None, fmt="%Y-%m-%d %H:%M:%S") -> str:
    """
    时间timestamp转字符串
    :param t: 时间戳
    :param fmt:
    :return:
    """
    return time.strftime(fmt, time.localtime(time.time() if t is None else t))


def str2time(t=None, fmt="%Y-%m-%d %H:%M:%S") -> float:
    """
    字符串转时间戳
    :param t: 时间字符串
    :param fmt:
    :return:
    """
    return time.time() if t is None else time.mktime(time.strptime(t, fmt))


def get_delay_date(date_str: str = None, fmt="%Y-%m-%d", delay: int = 0):
    """
    获取指定日期的几日前或后的日期
    :param date_str: 日期，默认为当前日期。
    :param fmt: date_str的格式
    :param delay: 间隔天数。正数为往后，负数为往前。
    :return:
    """
    if date_str is None:
        date_str = str(datetime.datetime.now().date())
    delay_date = datetime.datetime.strptime(date_str, fmt) + datetime.timedelta(days=delay)
    return datetime.datetime.strftime(delay_date, "%Y-%m-%d")


def mkdir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def gen_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()
