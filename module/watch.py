#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 11:26
# FileName: 默认关注

import json
import os

from module import bean
from utils import utils

folder_path = 'data'
file_name = 'watch.json'
watch_path = os.path.join(folder_path, file_name)


def load_watch() -> dict:
    data = {}
    if os.path.exists(watch_path):
        with open(watch_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data


def save_watch(data):
    utils.mkdir(folder_path)
    with open(watch_path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)


@bean.check_money_type(0)
def add(money_type, *, codes: [str]):
    assert codes, '缺少有效代码'
    data = load_watch()

    record_codes = data.get(money_type, [])
    sub = set([str(code) for code in codes]) - set(record_codes)  # 取不存在记录中的code
    record_codes.extend(list(filter(lambda code: code, sub)))
    data[money_type] = record_codes

    save_watch(data)
    return True, f'{",".join(sub)}添加成功'


@bean.check_money_type(0)
def get(money_type, **kwargs):
    data = load_watch()

    codes = data.get(money_type, [])

    msg = f'已关注: {",".join(codes)}' if codes else '暂无关注'

    return codes, msg


@bean.check_money_type(0)
def delete(money_type, *, codes: [str]):
    assert codes, '缺少有效代码'
    data = load_watch()

    record_codes = data.get(money_type, [])

    hint_codes = []
    for code in codes:
        if str(code) in record_codes:
            hint_codes.append(code)
            record_codes.remove(str(code))
    data[money_type] = record_codes

    save_watch(data)
    return True, f'{",".join(hint_codes)}删除成功'


if __name__ == '__main__':
    # add('fund', codes=[161725, '000001'])
    get('fund')
    # delete('stock', codes=[600519])
    # delete('fund', codes=[161725])
    get('fund')
    get('fund1')
