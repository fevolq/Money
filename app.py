#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 15:27
# FileName:

from enum import Enum
from typing import Union

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from process import action, watch

app = FastAPI()


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
    process = action.Process(money_type, codes=codes)
    return {
        'code': 200,
        'data': process.data,
        'message': process.msg,
    }


@app.get("/watch/{watch_type}")
def do_watch(
        watch_type: WatchType,
        money_type: MoneyType = Query(alias='type'),
        codes: Union[str, None] = Query(default=None),
):
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
        port=8000,
    )