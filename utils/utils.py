#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 15:29
# FileName:

import datetime
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
    t = time.time() if t is None else t
    return time.strftime(fmt, time.localtime(t))
