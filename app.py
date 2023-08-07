#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 15:27
# FileName: 基于FastAPI的app

from enum import Enum
from typing import Union

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, JSONResponse

from module.process import WorthProcess
from module import focus
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


class FocusType(str, Enum):
    add = 'add'
    get = 'get'
    delete = 'delete'


@app.get("/search/{money_type}")
def search(
        money_type: MoneyType,
        codes: Union[str, None] = Query(default=None),
):
    """查询操作"""
    worth = WorthProcess(money_type, codes=codes)
    return {
        'code': 200,
        'data': worth.get_data(),
        'message': f'【{worth.title}】{utils.asia_local_time()}\n\n{worth.get_message()}',
        'fields': worth.get_fields()
    }


@app.get("/focus/worth/{money_type}/{focus_type}")
def focus_worth(
        money_type: MoneyType,
        focus_type: FocusType,
        codes: Union[str, None] = Query(default=None),
):
    """净值配置"""
    if focus_type in ('add', 'delete'):
        assert codes, '缺少参数'

    resp = {'code': 200}
    foc = focus.Focus('worth')

    actions = {
        'add': foc.add,
        'get': foc.get,
        'delete': foc.delete,
    }
    resp['data'], resp['msg'] = actions[focus_type](money_type,
                                                    codes=[str(code) for code in codes.split(',')] if codes else None)

    return resp


@app.get("/focus/monitor/{money_type}/{focus_type}")
def focus_monitor(
        money_type: MoneyType,
        focus_type: FocusType,
        ids: Union[str, None] = Query(default=None),
        code: Union[str, None] = Query(default=None),
        worth: Union[int, float, None] = Query(default=None),
        cost: Union[int, float, None] = Query(default=None),
        growth: Union[int, float, None] = Query(default=None),
        lessen: Union[int, float, None] = Query(default=None),
        remark: Union[str, None] = Query(default=None),
):
    """监控配置"""
    if focus_type == 'add':
        assert code, '缺少参数 code'
        assert worth or (cost and (growth or lessen)), '缺少参数'
    elif focus_type == 'delete':
        assert ids, '缺少参数 ids'

    resp = {'code': 200}
    foc = focus.Focus('monitor')

    actions = {
        'add': foc.add,
        'get': foc.get,
        'delete': foc.delete,
    }
    option = {
        'code': code,
        'worth': worth,
        'cost': cost,
        'growth': growth,
        'lessen': lessen,
        'remark': remark,
    }
    resp['data'], resp['msg'] = actions[focus_type](money_type,
                                                    ids=[str(_id) for _id in ids.split(',')] if ids else None,
                                                    option=option)

    return resp


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8888,
    )
