#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 11:29
# FileName:

import sys
from functools import wraps


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
            if money_type.lower() not in ('stock', 'fund'):
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
