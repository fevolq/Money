#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/8/4 14:24
# FileName:

import json
import os
import time

from module import bean


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
    path = 'data/worth.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '净值'

    @bean.check_money_type(1)
    def add(self, money_type, *, codes: [str]) -> (bool, str):
        assert codes, '缺少有效代码'
        data = load(self.path)

        record_codes = data.get(money_type, [])
        sub = set([str(code) for code in codes]) - set(record_codes)  # 取不存在记录中的code
        record_codes.extend(list(filter(lambda code: code, sub)))
        data[money_type] = record_codes

        save(data, self.path)
        return True, f'{",".join(sub)}添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, **kwargs) -> (list, str):
        data = load(self.path)

        codes = data.get(money_type, [])

        msg = f'已关注: {",".join(codes)}' if codes else '暂无关注'

        return codes, msg

    @bean.check_money_type(1)
    def delete(self, money_type, *, codes: [str]) -> (bool, str):
        assert codes, '缺少有效代码'
        data = load(self.path)

        record_codes = data.get(money_type, [])

        hint_codes = []
        for code in codes:
            if str(code) in record_codes:
                hint_codes.append(code)
                record_codes.remove(str(code))
        data[money_type] = record_codes

        save(data, self.path)
        return True, f'{",".join(hint_codes)}删除成功'


class Monitor:
    path = 'data/monitor.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '监控'

    @bean.check_money_type(1)
    def add(self, money_type, *, option: {}) -> (bool, str):
        data = load(self.path)

        options = data.setdefault(money_type, [])
        tmp_option = {
            'cost': float(option['cost']) if 'cost' in option else None,  # 成本
            'worth': float(option['worth']) if 'worth' in option else None,  # 净值
            'growth': abs(float(option['growth'])) if 'growth' in option else None,  # 成本增长率
            'lessen': abs(float(option['lessen'])) if 'lessen' in option else None,  # 成本减少率
        }
        if any([tmp_option['growth'], tmp_option['lessen']]):
            assert tmp_option['cost'], '缺少成本'
        if len(list(filter(lambda k: tmp_option[k] is not None, tmp_option))) == 0:
            return False, '缺少有效值'

        tmp_option.update({
            'id': str(time.time()),
            'code': option['code'],
        })
        options.append(tmp_option)

        save(data, self.path)
        return True, '添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, **kwargs) -> (list, str):
        data = load(self.path)

        options = data.get(money_type, [])

        msg = '暂无配置'
        if options:
            msg = '\n'.join([
                f'成本：{option["cost"]}，净值阈值：{option["worth"]}，涨幅：{option["growth"]}，跌幅：{option["lessen"]}'
                for option in options
            ])

        return options, msg

    @bean.check_money_type(1)
    def delete(self, money_type, *, ids: [str]) -> (bool, str):
        assert ids, '缺少有效ID'
        data = load(self.path)

        options = data.get(money_type, [])
        hint_index = []
        hint_ids = []
        for index, option in enumerate(options):
            if option['id'] in ids:
                hint_index.append(index)
                hint_ids.append(option['id'])

        for index in hint_index[::-1]:
            options.pop(index)

        data[money_type] = options

        save(data, self.path)
        return True, f'{",".join(hint_ids)}删除成功'


# 项目的根路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    path = os.path.join(root_path, path)
    data = {}
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    return data


def save(data, path):
    path = os.path.join(root_path, path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
