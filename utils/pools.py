#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/31 22:05
# FileName:

import concurrent.futures
from typing import List

THREAD_POOL_SIZE = 4


# 线程池
def execute_thread(callback, args_list: List = None, *, times: int = 0, maxsize: int = 4, force_pool: bool = False):
    """
    多线程
    :param callback: 单线程的执行方法
    :param args_list: 单线程的参数组成的数组。[[(args1, args2,), {'key1': value1, 'key2': value2}], ]
    :param times: 执行的次数。当args_list为空时，生效，否则使用args_list的数量来判断
    :param maxsize: 线程池数量
    :param force_pool: 当pools大于设定的最大限制时，是否强制使用pools
    :return:
    """
    # 获取 max_workers
    if maxsize > THREAD_POOL_SIZE and not force_pool:
        maxsize = THREAD_POOL_SIZE

    # 获取执行次数
    args_length = len(args_list) if args_list else 0
    times = args_length or times
    assert times > 0, '参数异常，导致执行次数为0'
    maxsize = min(times, maxsize)

    # 解析参数
    def get_params(params):
        args = params[0] if isinstance(params[0], (tuple, list)) else []
        kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return args, kwargs

    with concurrent.futures.ThreadPoolExecutor(max_workers=maxsize) as executor:
        futures = []
        for i in range(times):
            if args_list:
                item_args, item_kwargs = get_params(args_list[i])
                future = executor.submit(callback, *item_args, **item_kwargs)
            else:
                future = executor.submit(callback)
            futures.append(future)

        # 获取任务的结果
        result = [future.result() for future in futures]
    return result
