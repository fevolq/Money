#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/8/4 14:24
# FileName: 配置关注

import json
import os
import time

from module import bean
from utils import utils


class Focus:

    def __init__(self, mode: str):
        self.mode = mode.lower()
        assert self.mode in ('worth', 'monitor')

        self.adapter = {
            'worth': Worth,
            'monitor': Monitor,
        }[self.mode]()

    def __repr__(self):
        return '关注'

    def action(self, func: str, *args, **kwargs):
        return getattr(self.adapter, func)(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self.action('add', *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.action('get', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.action('delete', *args, **kwargs)


class Worth:
    file_name = 'worth.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '净值'

    @bean.check_money_type(1)
    def add(self, money_type, *, codes: [str]) -> (bool, str):
        assert codes, '缺少有效代码'
        data = load(self.file_name)

        record_codes = data.get(money_type, [])
        sub = set([str(code) for code in codes]) - set(record_codes)  # 取不存在记录中的code
        record_codes.extend(list(filter(lambda code: code, sub)))
        data[money_type] = record_codes

        save(data, self.file_name)
        return True, f'{",".join(sub)}添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, **kwargs) -> (list, str):
        data = load(self.file_name)

        codes = data.get(money_type, [])

        msg = f'已关注: {",".join(codes)}' if codes else '暂无关注'

        return codes, msg

    @bean.check_money_type(1)
    def delete(self, money_type, *, codes: [str]) -> (bool, str):
        assert codes, '缺少有效代码'
        data = load(self.file_name)

        record_codes = data.get(money_type, [])

        hint_codes = []
        for code in codes:
            if str(code) in record_codes:
                hint_codes.append(code)
                record_codes.remove(str(code))
        if len(hint_codes) == 0:
            return False, 'id未匹配'

        data[money_type] = record_codes
        save(data, self.file_name)
        return True, f'{",".join(hint_codes)}删除成功'


class Monitor:
    file_name = 'monitor.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '监控'

    @bean.check_money_type(1)
    def add(self, money_type, *, option: {}, **kwargs) -> (bool, str):
        data = load(self.file_name)

        options = data.setdefault(money_type, [])
        tmp_option = {
            'cost': float(option['cost']) if option.get('cost') is not None else None,  # 成本
            'worth': float(option['worth']) if option.get('worth') is not None else None,  # 净值
            'growth': abs(float(option['growth'])) if option.get('growth') is not None else None,  # 成本增长率
            'lessen': abs(float(option['lessen'])) if option.get('lessen') is not None else None,  # 成本减少率
        }
        if any([tmp_option['growth'], tmp_option['lessen']]):
            assert tmp_option['cost'], '缺少成本'
        if len(list(filter(lambda k: tmp_option[k] is not None, tmp_option))) == 0:
            return False, '缺少有效值'

        ids = [_option['id'] for _option in options]

        def gen_hash_id() -> str:
            hashed = utils.gen_hash(str(time.time()))
            _id = hashed[:6]
            if _id in ids:
                return gen_hash_id()
            return _id

        tmp_option.update({
            'id': gen_hash_id(),
            'code': option['code'],
            'remark': option.get('remark', None),
        })
        options.append(tmp_option)

        save(data, self.file_name)
        return True, '添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, *, code: str = None, **kwargs) -> (list, str):
        data = load(self.file_name)

        options = data.get(money_type, [])
        if code:
            options = list(filter(lambda item: item['code'] == code, options))

        msg = '暂无配置'
        if options:
            msg = '\n'.join([
                f'ID：{option["id"]}，代码：{option["code"]}，成本：{option["cost"]}，净值阈值：{option["worth"]}，'
                f'涨幅：{option["growth"]}，跌幅：{option["lessen"]}，备注：{option["remark"]}'
                for option in options
            ])

        return options, msg

    @bean.check_money_type(1)
    def delete(self, money_type, *, ids: [str], **kwargs) -> (bool, str):
        assert ids, '缺少有效ID'
        data = load(self.file_name)

        options = data.get(money_type, [])
        hint_index = []
        hint_ids = []
        for index, option in enumerate(options):
            if option['id'] in ids:
                hint_index.append(index)
                hint_ids.append(option['id'])

        if len(hint_ids) == 0:
            return False, 'id未匹配'

        for index in hint_index[::-1]:
            options.pop(index)

        data[money_type] = options

        save(data, self.file_name)
        return True, f'{",".join(hint_ids)}删除成功'


# 项目的根路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder_path = os.path.join(root_path, 'data')


def load(file_name):
    path = os.path.join(folder_path, file_name)
    data = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data


def save(data, file_name):
    utils.mkdir(folder_path)
    path = os.path.join(folder_path, file_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
