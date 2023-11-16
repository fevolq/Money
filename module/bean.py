#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 11:29
# FileName:

import logging
import sys
from functools import wraps

import config
from module import cache
from utils import utils


def check_money_type(index=None):
    """
    校验类型是否符合
    :param index: 类型参数在参数的位置
    :return:
    """

    def check(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if index is None:
                money_type = kwargs['money_type']
            else:
                money_type = args[index]
            if money_type not in ('stock', 'fund'):
                logging.exception(f'{money_type} 类型未匹配!')
                sys.exit('类型未匹配!')

            return func(*args, **kwargs)

        return wrapper

    return check


def sys_exit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            # raise e           # 本地测试时可打开
            sys.exit(str(e))

        return result

    return wrapper


def set_cache_expire_today(key, value):
    """
    设置当天失效的缓存
    :param key:
    :param value:
    :return:
    """
    next_date = utils.get_delay_date(delay=1, tz=config.CronZone)
    today_expire = utils.str2time(next_date, fmt="%Y-%m-%d", tz=config.CronZone) - utils.str2time(tz=config.CronZone)
    cache.set(key, value, expire=int(today_expire) + 1)  # 增加1秒的缓冲
