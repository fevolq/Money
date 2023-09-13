#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 15:27
# FileName: 基于FastAPI的app

import copy
from enum import Enum
from typing import Union

import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from module.process import WorthProcess
from module import focus, process
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


class Codes(BaseModel):
    codes: str


class MonitorOption(BaseModel):
    code: str
    remark: Union[str, None] = None
    worth: Union[int, float, None] = None
    cost: Union[int, float, None] = None
    growth: Union[int, float, None] = None
    lessen: Union[int, float, None] = None


class MonitorID(BaseModel):
    ids: str


# 估值查询
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
        'fields': worth.get_fields()
        # 'message': f'【{worth.title}】{utils.asia_local_time()}\n\n{worth.get_message()}',
    }


# 估值配置（弃用）
@app.get("/focus/worth/{money_type}/{focus_type}", deprecated=True)
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


# 估值配置查询
@app.get("/focus/worth/{money_type}")
def focus_worth_get(money_type: MoneyType):
    codes = focus.Focus('worth').get(money_type)[0]

    names = process.get_codes_name(money_type, codes)

    return {
        'code': 200,
        'data': [{
            'code': code,
            'name': names[code]
        } for code in codes],
    }


# 估值配置添加
@app.post("/focus/worth/{money_type}")
def focus_worth_add(money_type: MoneyType, codes: Codes):
    res = focus.Focus('worth').add(money_type, codes=[str(code).strip() for code in codes.codes.split(',')])

    return {
        'code': 200,
        'data': res[0],
        'msg': res[1]
    }


# 估值配置删除
@app.delete("/focus/worth/{money_type}")
def focus_worth_del(money_type: MoneyType, codes: Codes):
    res = focus.Focus('worth').delete(money_type, codes=[str(code).strip() for code in codes.codes.split(',')])

    return {
        'code': 200,
        'data': res[0],
        'msg': res[1]
    }


# 监控配置
@app.get("/focus/monitor/{money_type}/{focus_type}", deprecated=True)
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
                                                    code=code,
                                                    option=option)

    return resp


# 监控配置查询
@app.get("/focus/monitor/{money_type}")
def focus_monitor_get(
        money_type: MoneyType,
        code: Union[str, None] = Query(default=None),
):
    res = focus.Focus('monitor').get(money_type, code=code)
    data = copy.deepcopy(res[0])  # 进行拷贝，否则一旦更改，会将缓存数据一并更改

    codes = [row['code'] for row in data]
    names = process.get_codes_name(money_type, codes)

    for row in data:
        row['name'] = names[row['code']]

    return {
        'code': 200,
        'data': data
    }


# 监控配置添加
@app.post("/focus/monitor/{money_type}")
def focus_monitor_add(
        money_type: MoneyType,
        option: MonitorOption,
):
    assert option.worth or (option.cost and (option.growth or option.lessen)), '缺少参数'
    data, msg = focus.Focus('monitor').add(money_type, option=option.__dict__)
    return {
        'code': 200,
        'data': data,
        'msg': msg,
    }


# 监控配置删除
@app.delete("/focus/monitor/{money_type}")
def focus_monitor_del(
        money_type: MoneyType,
        ids: MonitorID,
):
    data, msg = focus.Focus('monitor').delete(money_type, ids=[str(id_).strip() for id_ in ids.ids.split(',')])
    return {
        'code': 200,
        'data': data,
        'msg': msg,
    }


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8888,
    )
