#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 15:27
# FileName: 基于FastAPI的app

from enum import Enum
from typing import Union

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from module import process, watch
from utils import utils
import scheduler

app = FastAPI()


# 程序启动
@app.on_event("startup")
async def startup_event():
    await scheduler.start_scheduler()


# 程序终止
@app.on_event("shutdown")
async def shutdown_event():
    await scheduler.stop_scheduler()


# 全局异常捕获
@app.exception_handler(AssertionError)
def custom_exception_handler(request, exc: Exception):
    return JSONResponse({'code': 500, 'msg': str(exc)})


# 全局异常捕获
@app.exception_handler(Exception)
def exception_handler(request, exc: Exception):
    return PlainTextResponse(str(exc), status_code=400)


class MoneyType(str, Enum):
    fund = 'fund'
    stock = 'stock'


class WatchType(str, Enum):
    add = 'add'
    get = 'get'
    delete = 'delete'


@app.get("/search/{money_type}")
def search(
        money_type: MoneyType,
        codes: Union[str, None] = Query(default=None),
):
    """查询操作"""
    processor = process.Process(money_type, codes=codes)
    return {
        'code': 200,
        'data': processor.get_data(),
        'message': f'【{processor.title}】{utils.asia_local_time()}\n\n{processor.get_message()}',
        'fields': processor.get_fields()
    }


@app.get("/watch/{watch_type}")
def do_watch(
        watch_type: WatchType,
        money_type: MoneyType = Query(alias='type'),
        codes: Union[str, None] = Query(default=None),
):
    """关注操作"""
    if watch_type in ('add', 'delete'):
        assert codes, '缺少参数'

    resp = {'code': 200}

    actions = {
        'add': watch.add,
        'get': watch.get,
        'delete': watch.delete,
    }
    resp['data'], resp['msg'] = actions[watch_type](money_type,
                                                    codes=[str(code) for code in codes.split(',')] if codes else None)

    return resp


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8888,
    )
