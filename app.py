#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 15:27
# FileName: 基于FastAPI的app

from enum import Enum
from typing import Union, List

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


# 估值关注的单个配置
class FocusWorthOption(BaseModel):
    code: str
    cost: Union[int, float, None] = Query(default=None, gt=0)


class FocusWorthOptions(BaseModel):
    options: List[FocusWorthOption]


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
        'fields': worth.get_fields(),
        # 'message': f'【{worth.title}】{utils.asia_local_time()}\n\n{worth.get_message()}',
    }


# 估值配置查询
@app.get("/focus/worth/{money_type}")
def focus_worth_get(money_type: MoneyType):
    options = focus.Focus('worth').get(money_type)[0]
    codes = [option['code'] for option in options]

    names = process.get_codes_name(money_type, codes)

    for option in options:
        option['name'] = names.get(option['code'], '')

    return {
        'code': 200,
        'data': options,
    }


# 估值配置添加
@app.post("/focus/worth/{money_type}")
def focus_worth_add(money_type: MoneyType, data: FocusWorthOptions):
    res = focus.Focus('worth').add(money_type, options=[option.model_dump() for option in data.options])

    return {
        'code': 200,
        'data': res[0],
        'msg': res[1]
    }


# 估值配置更新
@app.put("/focus/worth/{money_type}")
def focus_worth_update(money_type: MoneyType, data: FocusWorthOption):
    res = focus.Focus('worth').update(money_type, option=data.model_dump())

    return {
        'code': 200,
        'data': res[0],
        'msg': res[1]
    }


# 估值配置删除
@app.delete("/focus/worth/{money_type}")
def focus_worth_del(money_type: MoneyType, data: FocusWorthOptions):
    res = focus.Focus('worth').delete(money_type, options=[option.model_dump() for option in data.options])

    return {
        'code': 200,
        'data': res[0],
        'msg': res[1]
    }


class MonitorOption(BaseModel):
    code: str
    remark: Union[str, None] = None
    worth: Union[int, float, None] = None
    cost: Union[int, float, None] = None
    growth: Union[int, float, None] = None
    lessen: Union[int, float, None] = None


class MonitorUpdate(BaseModel):
    id: str
    option: MonitorOption


class MonitorDelete(BaseModel):
    ids: str


# 监控配置查询
@app.get("/focus/monitor/{money_type}")
def focus_monitor_get(
        money_type: MoneyType,
        code: Union[str, None] = Query(default=None),
):
    data = focus.Focus('monitor').get(money_type, code=code)[0]

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
    data, msg = focus.Focus('monitor').add(money_type, option=option.model_dump())
    return {
        'code': 200,
        'data': data,
        'msg': msg,
    }


# 监控配置更新
@app.put("/focus/monitor/{money_type}")
def focus_monitor_update(
        money_type: MoneyType,
        data: MonitorUpdate,
):
    option = data.option
    hash_id = data.id
    assert option.worth or (option.cost and (option.growth or option.lessen)), '缺少参数'
    data, msg = focus.Focus('monitor').update(money_type, hash_id=hash_id, option=option.model_dump())
    return {
        'code': 200,
        'data': data,
        'msg': msg,
    }


# 监控配置删除
@app.delete("/focus/monitor/{money_type}")
def focus_monitor_del(
        money_type: MoneyType,
        data: MonitorDelete,
):
    res, msg = focus.Focus('monitor').delete(money_type, ids=[str(id_).strip() for id_ in data.ids.split(',')])
    return {
        'code': 200,
        'data': res,
        'msg': msg,
    }


if __name__ == '__main__':
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=8888,
    )
