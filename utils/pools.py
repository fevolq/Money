#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/31 22:05
# FileName:

import concurrent.futures

THREAD_POOL_SIZE = 4


# 线程池
def execute_thread(func, args_list, pools: int = 4, force_pool: bool = False):
    # 获取 max_workers
    if pools > THREAD_POOL_SIZE and not force_pool:
        pools = THREAD_POOL_SIZE
    if len(args_list) <= pools:
        pools = len(args_list)

    # 解析参数
    def get_params(params):
        item_args = params[0] if any([isinstance(params[0], tuple), isinstance(params[0], list)]) else []
        item_kwargs = params[-1] if isinstance(params[-1], dict) else {}
        return item_args, item_kwargs

    with concurrent.futures.ThreadPoolExecutor(max_workers=pools) as executor:
        futures = []
        for i in range(len(args_list)):
            args, kwargs = get_params(args_list[i])
            future = executor.submit(func, *args, **kwargs)
            futures.append(future)

        # 获取任务的结果
        result = [future.result() for future in futures]
    return result
