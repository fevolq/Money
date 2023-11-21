#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/11/21 13:59
# FileName:

import json
import logging
from typing import Union, List

import pandas as pd
import numpy as np

from api import eastmoney
from module.process.worth import StockWorth, FundWorth
from utils import utils, pools
from module import bean, focus, cache
import config


class Monitor:
    """监控"""

    @bean.check_money_type(1)
    def __init__(self, money_type):
        """

        :param money_type: 类型
        """
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.title = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.foc = focus.Focus('monitor')
        self.options, _ = self.foc.get(self.money_type)

        self.adapter = {
            'stock': StockMonitor,
            'fund': FundMonitor,
        }[money_type]

        self.datas = self._load()
        # 对原始数据进行处理
        self.objs = [
            self.adapter(data, self.options)
            for data in self.datas
        ]

    def _load(self) -> list:
        assert self.options, '无监控项，请添加配置后再来。'
        codes = set([option['code'] for option in self.options])

        def one(code) -> Union[dict, None]:
            logging.info(f'开始查询估值：{self.money_type} [{code}]')
            data, ok = self.api.fetch_current(code)
            if ok and data:
                return data
            return None

        # # 单线程
        # datas = []
        # for _code in codes:
        #     _data = one(_code)
        #     if not _data:
        #         continue
        #     datas.append(_data)

        # 多线程
        args_list = [[(_code,)] for _code in codes]
        result = pools.execute_thread(one, args_list)
        datas = list(filter(lambda _data: _data, result))

        return datas

    def get_message(self, is_open=False, **kwargs) -> List:
        all_msg = []
        for obj in self.objs:
            if is_open and not obj.opening:
                continue
            all_msg.extend(obj.get_message(**kwargs))

        return all_msg


class StockMonitor:
    option_fields = {
        'option.id': {'field': 'id', 'label': 'ID'},
        'option.code': {'field': 'code', 'label': '代码'},
        'option.remark': {'field': 'remark', 'label': '备注'},
        'option.cost': {'field': 'cost', 'label': '成本'},
        'option.growth': {'field': 'growth', 'label': '涨幅', 'flag': 0},
        'option.lessen': {'field': 'lessen', 'label': '跌幅', 'flag': 1},
        'option.worth': {'field': 'worth', 'label': '净值阈值', 'flag': 2},
    }
    relate_fields = {
        **StockWorth.relate_fields,
        **option_fields
    }

    def __init__(self, data, options):
        self._opening = True
        self._initial_data = data
        self._options = list(
            filter(lambda option: str(option['code']) == str(data[self.get_relate('code')]), options))
        self._data = self._resolve_data(data)

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, *, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data: dict):
        data_time = utils.time2str(data[self.get_relate('time')], fmt='%Y-%m-%d', tz=config.CronZone)
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        point = 10 ** int(data[self.get_relate('point')])
        for field in ('start_worth', 'standard_worth', 'current_worth'):
            data[self.get_relate(field)] = data[self.get_relate(field)] / point

        data_df = pd.DataFrame([data])
        data_df.rename(
            columns={field_conf['field']: field for field, field_conf in StockWorth.relate_fields.items()},
            inplace=True)
        data_df = data_df.fillna(np.nan)
        df_options = pd.DataFrame(self._options)
        df_options.rename(
            columns={field_conf['field']: field for field, field_conf in FundMonitor.relate_fields.items()},
            inplace=True)
        df_options['option.worth'] = df_options['option.worth'].fillna(np.nan)
        df_options['option.cost'] = df_options['option.cost'].fillna(np.nan)
        df_options['option.growth'] = df_options['option.growth'].fillna(np.nan)
        df_options['option.lessen'] = df_options['option.lessen'].fillna(np.nan)

        df = pd.merge(data_df, df_options, left_on=['code'], right_on=['option.code'], how='outer')
        df.dropna(subset=['code'], axis=0, inplace=True)
        df.dropna(subset=['option.code'], axis=0, inplace=True)

        def solve(row) -> bin:
            flag = 0

            # 去除零值干扰
            if pd.isna(row['current_worth']) or not row['current_worth']:
                return bin(flag)

            # 涨跌幅
            if not pd.isna(row['option.cost']) and not pd.isna(row['current_worth']):
                rate = (float(row['current_worth']) - float(row['option.cost'])) / float(row['option.cost'])
                rate = rate * 100
                if not pd.isna(row['option.growth']) and rate >= abs(float(row['option.growth'])) > 0:
                    flag += 2 ** self.get_relate('option.growth', key='flag')
                if not pd.isna(row['option.lessen']) and rate <= -abs(float(row['option.lessen'])) < 0:
                    flag += 2 ** self.get_relate('option.lessen', key='flag')

            # 净值
            if not pd.isna(row['option.worth']) and not pd.isna(row['current_worth']):
                # 为正数，则大于阈值；为负数，则小于阈值
                if float(row['current_worth']) >= float(row['option.worth']) > 0 or \
                        0 < float(row['current_worth']) <= -float(row['option.worth']):
                    flag += 2 ** self.get_relate('option.worth', key='flag')

            return bin(flag)

        df['flag'] = df.apply(solve, axis=1)
        return json.loads(df.to_json(orient='records'))

    def get_message(self, to_cache: bool = True) -> List[str]:
        """

        :param to_cache: 是否缓存已发送的信息
        :return:
        """
        flag_msgs = {
            2 ** field_conf['flag']: {'data_field': field, **field_conf}
            for field, field_conf in StockMonitor.relate_fields.items()
            if 'flag' in field_conf
        }

        all_msg = []
        for row in self._data:
            row_msg = []
            flag = int(row['flag'], 2)
            for flag_value, flag_conf in flag_msgs.items():
                key = f'monitor:{row["option.id"]}:{flag_value}'
                if to_cache and cache.exist(key):
                    continue
                if int(bin(flag & flag_value), 2):
                    row_msg.append(f'{flag_conf["label"]}：{row[flag_conf["data_field"]]}')
                    if to_cache:
                        bean.set_cache_expire_today(key, True)
            if row_msg:
                row_msg.insert(0,
                               f'【{row["option.id"]}】匹配\n'
                               f'{self._initial_data[self.get_relate("name")]}'
                               f' [{self._initial_data[self.get_relate("code")]}]\n'
                               f'备注：{row["option.remark"]}')
                all_msg.append('\n'.join(row_msg))

        return all_msg


class FundMonitor:
    option_fields = {
        'option.id': {'field': 'id', 'label': 'ID'},
        'option.code': {'field': 'code', 'label': '代码'},
        'option.remark': {'field': 'remark', 'label': '备注'},
        'option.cost': {'field': 'cost', 'label': '成本'},
        'option.growth': {'field': 'growth', 'label': '涨幅', 'flag': 0},
        'option.lessen': {'field': 'lessen', 'label': '跌幅', 'flag': 1},
        'option.worth': {'field': 'worth', 'label': '净值阈值', 'flag': 2},
    }
    relate_fields = {
        **FundWorth.relate_fields,
        **option_fields
    }

    def __init__(self, data, options):
        self._opening = True
        self._initial_data = data
        self._options = list(
            filter(lambda option: str(option['code']) == str(data[self.get_relate('code')]), options))
        self._data: List[dict] = self._resolve_data(data)

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data: dict):
        data_time = data[self.get_relate('time')].split(' ')[0]
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        data_df = pd.DataFrame([data])
        data_df.rename(
            columns={field_conf['field']: field for field, field_conf in FundWorth.relate_fields.items()},
            inplace=True)
        data_df = data_df.fillna(np.nan)
        df_options = pd.DataFrame(self._options)
        df_options.rename(
            columns={field_conf['field']: field for field, field_conf in FundMonitor.relate_fields.items()},
            inplace=True)
        df_options['option.worth'] = df_options['option.worth'].fillna(np.nan)
        df_options['option.cost'] = df_options['option.cost'].fillna(np.nan)
        df_options['option.growth'] = df_options['option.growth'].fillna(np.nan)
        df_options['option.lessen'] = df_options['option.lessen'].fillna(np.nan)

        df = pd.merge(data_df, df_options, left_on=['code'], right_on=['option.code'], how='outer')
        df.dropna(subset=['code'], axis=0, inplace=True)
        df.dropna(subset=['option.code'], axis=0, inplace=True)

        def solve(row) -> bin:
            flag = 0

            if pd.isna(row['current_worth']) or not row['current_worth']:
                return bin(flag)

            # 涨跌幅
            if not pd.isna(row['option.cost']) and not pd.isna(row['current_worth']):
                rate = (float(row['current_worth']) - float(row['option.cost'])) / float(row['option.cost'])
                rate = rate * 100
                if not pd.isna(row['option.growth']) and rate >= abs(float(row['option.growth'])) > 0:
                    flag += 2 ** self.get_relate('option.growth', key='flag')
                if not pd.isna(row['option.lessen']) and rate <= -abs(float(row['option.lessen'])) < 0:
                    flag += 2 ** self.get_relate('option.lessen', key='flag')

            # 净值
            if not pd.isna(row['option.worth']) and not pd.isna(row['current_worth']):
                if float(row['current_worth']) >= float(row['option.worth']) > 0 or \
                        0 < float(row['current_worth']) <= -float(row['option.worth']):
                    flag += 2 ** self.get_relate('option.worth', key='flag')

            return bin(flag)

        df['flag'] = df.apply(solve, axis=1)
        return json.loads(df.to_json(orient='records'))

    def get_message(self, to_cache: bool = True) -> List[str]:
        """

        :param to_cache: 是否缓存已发送的信息
        :return:
        """
        flag_msgs = {
            2 ** field_conf['flag']: {'data_field': field, **field_conf}
            for field, field_conf in self.relate_fields.items()
            if 'flag' in field_conf
        }

        all_msg = []
        for row in self._data:
            row_msg = []
            flag = int(row['flag'], 2)
            for flag_value, flag_conf in flag_msgs.items():
                key = f'monitor:{row["option.id"]}:{flag_value}'
                if to_cache and cache.exist(key):
                    continue
                if int(bin(flag & flag_value), 2):
                    row_msg.append(f'{flag_conf["label"]}：{row[flag_conf["data_field"]]}')
                    if to_cache:
                        bean.set_cache_expire_today(key, True)
            if row_msg:
                row_msg.insert(0,
                               f'【{row["option.id"]}】匹配\n'
                               f'{self._initial_data[self.get_relate("name")]}'
                               f' [{self._initial_data[self.get_relate("code")]}]\n'
                               f'备注：{row["option.remark"]}')
                all_msg.append('\n'.join(row_msg))

        return all_msg
