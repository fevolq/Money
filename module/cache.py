#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/8/9 10:21
# FileName: 全局缓存

import threading
import time


class Cache:
    """
    全局缓存，可定时失效
    """
    __lock = threading.Lock()
    instance = None

    def __new__(cls, *args, **kwargs):
        # 构造单例
        if hasattr(cls, 'instance') and cls.instance:
            return cls.instance

        # 线程锁
        with cls.__lock:
            if not hasattr(cls, 'instance') or cls.instance is None:
                cls.instance = super(Cache, cls).__new__(cls)
            return cls.instance

    def __init__(self):
        self.__data = {}

    @property
    def data(self):
        return self.__data

    def set(self, key: str, value, *, expire: int = None):
        """

        :param key:
        :param value:
        :param expire: 失效时间（秒）
        :return:
        """
        with self.__lock:
            # TODO: set重复key时，停止原线程
            self.__data[key] = {
                'value': value,
                'expire': time.time() + expire if expire else float('inf')
            }

            if expire:
                t = threading.Thread(target=self.__expire, args=(key, expire))
                t.start()

    def get(self, key: str):
        with self.__lock:
            if key in self.__data and time.time() < self.__data[key]['expiration']:
                return self.__data[key]['value']
            return None

    def exist(self, key: str):
        with self.__lock:
            return key in self.__data

    def __expire(self, key: str, expire: int):
        time.sleep(expire)
        with self.__lock:
            if key in self.__data:
                del self.__data[key]


cache = None


def get_cache():
    global cache
    if cache is None:
        cache = Cache()
    return cache


def set(key: str, value, *, expire: int = None):
    return get_cache().set(key, value, expire=expire)


def get(key):
    return get_cache().get(key)


def exist(key):
    return get_cache().exist(key)
