#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/8/4 14:24
# FileName: 配置关注

import copy
import json
import logging
import os
import time

from module import bean, cache
from utils import utils


class Focus:

    def __init__(self, mode: str):
        self.mode = mode.lower()
        assert self.mode in ('worth', 'monitor', 'history_monitor')

        self.adapter = {
            'worth': Worth,
            'monitor': Monitor,
            'history_monitor': HistoryMonitor,
        }[self.mode]()

    def __repr__(self):
        return '关注'

    def action(self, func: str, *args, **kwargs):
        return getattr(self.adapter, func)(*args, **kwargs)

    def add(self, *args, **kwargs):
        return self.action('add', *args, **kwargs)

    def get(self, *args, **kwargs):
        return self.action('get', *args, **kwargs)

    def update(self, *args, **kwargs):
        return self.action('update', *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.action('delete', *args, **kwargs)


class Worth:
    file_name = 'worth.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '净值'

    @bean.check_money_type(1)
    def add(self, money_type, *, options: [dict]) -> (bool, str):
        assert options, '缺少有效配置'
        data = load(Worth.file_name)

        record_options = data.get(money_type, [])
        record_codes = [option['code'] for option in record_options]

        # sub_options = list(filter(lambda option: option['code'] not in record_codes, options))  # 取不存在记录中的code
        sub_options = []
        for option in options:
            if option['code'] in record_codes:
                continue
            sub_options.append(option)
            record_codes.append(option['code'])  # 避免options中有重复的code

        record_options.extend(sub_options)

        data[money_type] = record_options
        save(data, Worth.file_name)

        info = f'{",".join([option["code"] for option in sub_options])}添加成功'
        logging.info(info)
        return True, info

    @bean.check_money_type(1)
    def get(self, money_type, **kwargs) -> (list, str):
        data = load(Worth.file_name)

        record_options = copy.deepcopy(data.get(money_type, []))

        msg = f'已关注: {",".join([option["code"] for option in record_options])}' if record_options else '暂无关注'

        return record_options, msg

    @bean.check_money_type(1)
    def update(self, money_type, *, option: dict) -> (bool, str):
        assert option, '缺少有效配置'
        data = load(Worth.file_name)

        record_options = data.get(money_type, [])
        hit = False
        for record in record_options:
            if record['code'] != option['code']:
                continue
            record['cost'] = option.get('cost', None)
            hit = True
            break

        data[money_type] = record_options
        save(data, Worth.file_name)

        info = f'{option["code"]} 已更改成功'
        logging.info(info)
        return True if hit else False, info

    @bean.check_money_type(1)
    def delete(self, money_type, *, options: [dict]) -> (bool, str):
        assert options, '缺少有效代码'
        data = load(Worth.file_name)

        record_options = data.get(money_type, [])
        record_codes = [option['code'] for option in record_options]

        hit_codes = []
        for option in options:
            if option['code'] in record_codes:
                hit_codes.append(option['code'])
        if len(hit_codes) == 0:
            return False, 'id未匹配'
        else:
            record_options = list(filter(lambda option: option['code'] not in hit_codes, record_options))

        data[money_type] = record_options
        save(data, Worth.file_name)

        info = f'{",".join(hit_codes)}删除成功'
        logging.info(info)
        return True, info


class Monitor:
    file_name = 'monitor.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '监控'

    @classmethod
    def get_default_option(cls):
        return {
            "id": None,  # 唯一ID
            "code": None,  # 代码
            "remark": None,  # 备注
            "worth": None,  # 净值阈值
            "cost": None,  # 成本
            "growth": None,  # 成本增长率
            "lessen": None,  # 成本减少率
        }

    def _update_option(self, money_type, option, *, record=None):
        def gen_hash_id():
            ids = [item['id'] for item in load(Monitor.file_name).setdefault(money_type, [])]
            hash_id = utils.gen_hash(str(time.time()))[:6]
            if hash_id in ids:
                return gen_hash_id()
            return hash_id

        if not record:
            record = self.get_default_option()

        record['cost'] = float(option['cost']) if 'cost' in option and option['cost'] is not None \
            else option.get('cost', record['cost'])
        record['worth'] = float(option['worth']) if 'worth' in option and option['worth'] is not None \
            else option.get('worth', record['worth'])
        record['growth'] = abs(float(option['growth'])) if 'growth' in option and option['growth'] is not None \
            else option.get('growth', record['growth'])
        record['lessen'] = abs(float(option['lessen'])) if 'lessen' in option and option['lessen'] is not None \
            else option.get('lessen', record['lessen'])
        record['remark'] = option.get('remark', record['remark'])
        assert record['worth'] or (record['cost'] and (record['growth'] or option['lessen'])), '缺少有效值'

        # 初始化的情况
        if record['id'] is None:
            record['id'] = gen_hash_id()
        if record['code'] is None:
            record['code'] = option['code']

        return record

    @bean.check_money_type(1)
    def add(self, money_type, *, option: {}, **kwargs) -> (bool, str):
        data = load(Monitor.file_name)

        record_options = copy.deepcopy(data.get(money_type, []))
        record_options.append(self._update_option(money_type, option))

        data[money_type] = record_options
        save(data, Monitor.file_name)
        return True, '添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, *, code: str = None, **kwargs) -> (list, str):
        data = load(Monitor.file_name)

        options = copy.deepcopy(data.get(money_type, []))
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
    def update(self, money_type, *, hash_id, option: {}, **kwargs) -> (bool, str):
        data = load(Monitor.file_name)

        record_options = data.setdefault(money_type, [])
        hit = False
        for record in record_options:
            if record['id'] != hash_id:
                continue
            self._update_option(money_type, option, record=record)
            hit = True
            break

        if not hit:
            return False, 'id未匹配'

        data[money_type] = record_options
        save(data, Monitor.file_name)

        info = f'{hash_id} 更新成功'
        logging.info(info)
        return True, info

    @bean.check_money_type(1)
    def delete(self, money_type, *, ids: [str], **kwargs) -> (bool, str):
        assert ids, '缺少有效ID'
        data = load(Monitor.file_name)

        record_options = data.get(money_type, [])
        hit_index = []
        hit_ids = []
        for index, option in enumerate(record_options):
            if option['id'] in ids:
                hit_index.append(index)
                hit_ids.append(option['id'])

        if len(hit_ids) == 0:
            return False, 'id未匹配'

        for index in hit_index[::-1]:
            record_options.pop(index)

        data[money_type] = record_options

        save(data, Monitor.file_name)

        info = f'{",".join(hit_ids)}删除成功'
        logging.info(info)
        return True, info


class HistoryMonitor:
    file_name = 'history_monitor.json'

    def __init__(self):
        ...

    def __repr__(self):
        return '历史涨跌幅监控'

    @classmethod
    def get_default_option(cls) -> dict:
        return {
            "code": None,  # 代码
            "3": {'growth': None, 'lessen': None},  # 3天的涨跌幅
            "5": {'growth': None, 'lessen': None},
            "7": {'growth': None, 'lessen': None},
            "15": {'growth': None, 'lessen': None},
            "30": {'growth': None, 'lessen': None},
        }

    def _update_option(self, option, *, record=None):
        if not record:
            record = self.get_default_option()

        valid = False
        for day in ["3", "5", "7", "15", "30"]:
            if day not in option:
                continue
            day_option = option[day]
            if not day_option:
                continue

            record[day]['growth'] = abs(float(day_option['growth'])) \
                if 'growth' in day_option and day_option['growth'] is not None\
                else day_option.get('growth', record[day]['growth'])
            record[day]['lessen'] = abs(float(day_option['lessen'])) \
                if 'lessen' in day_option and day_option['lessen'] is not None \
                else day_option.get('lessen', record[day]['lessen'])
            valid = valid or any([record[day]['growth'], record[day]['lessen']])

        assert valid, '缺少有效值'

        # 初始化的情况
        if record['code'] is None:
            record['code'] = option['code']

        return record

    @bean.check_money_type(1)
    def add(self, money_type, *, option: {}, **kwargs) -> (bool, str):
        data = load(HistoryMonitor.file_name)

        record_options = copy.deepcopy(data.get(money_type, []))
        record_codes = set([record['code'] for record in record_options])
        assert option['code'] not in record_codes, f'已存在{option["code"]}配置，不可添加多条！'

        record_options.append(self._update_option(option))

        data[money_type] = record_options
        save(data, HistoryMonitor.file_name)
        return True, '添加成功'

    @bean.check_money_type(1)
    def get(self, money_type, *, code: str = None, **kwargs) -> (list, str):
        data = load(HistoryMonitor.file_name)

        options = copy.deepcopy(data.get(money_type, []))
        if code:
            options = list(filter(lambda item: item['code'] == code, options))

        msg = '暂无配置'
        if options:
            msg = '\n'.join([
                f'代码：{option["code"]}，'
                f'3日：涨幅：{option["3"]["growth"]}，跌幅：{option["3"]["lessen"]}'
                f'5日：涨幅：{option["5"]["growth"]}，跌幅：{option["5"]["lessen"]}'
                f'7日：涨幅：{option["7"]["growth"]}，跌幅：{option["7"]["lessen"]}'
                f'15日：涨幅：{option["15"]["growth"]}，跌幅：{option["15"]["lessen"]}'
                f'30日：涨幅：{option["30"]["growth"]}，跌幅：{option["30"]["lessen"]}'
                for option in options
            ])

        return options, msg

    @bean.check_money_type(1)
    def update(self, money_type, *, code, option: {}, **kwargs) -> (bool, str):
        data = load(HistoryMonitor.file_name)

        record_options = data.setdefault(money_type, [])
        hit = False
        for record in record_options:
            if record['code'] != code:
                continue
            self._update_option(option, record=record)
            hit = True
            break

        if not hit:
            return False, 'code未匹配'

        data[money_type] = record_options
        save(data, HistoryMonitor.file_name)

        info = f'{code} 更新成功'
        logging.info(info)
        return True, info

    @bean.check_money_type(1)
    def delete(self, money_type, *, codes: [str], **kwargs) -> (bool, str):
        assert codes, '缺少有效ID'
        data = load(HistoryMonitor.file_name)

        record_options = data.get(money_type, [])
        hit_index = []
        hits = []
        for index, option in enumerate(record_options):
            if option['code'] in codes:
                hit_index.append(index)
                hits.append(option['code'])

        if len(hits) == 0:
            return False, 'id未匹配'

        for index in hit_index[::-1]:
            record_options.pop(index)

        data[money_type] = record_options

        save(data, HistoryMonitor.file_name)

        info = f'{",".join(hits)}删除成功'
        logging.info(info)
        return True, info


# 项目的根路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
folder_path = os.path.join(root_path, 'data')


def load(file_name):
    data = cache.get(file_name)
    if not data:
        path = os.path.join(folder_path, file_name)
        data = {}
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        cache.set(file_name, data)

    return data


def save(data, file_name):
    cache.delete(file_name)

    utils.mkdir(folder_path)
    path = os.path.join(folder_path, file_name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False, sort_keys=True)
