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
from module import bean, focus, cache
from module.process.worth import StockWorth, FundWorth, StockHistory, FundHistory
from utils import utils, pools
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
        self.type_ = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.title = f'{self.type_} 阈值'
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


class HistoryMonitor:
    MaxLimit = 30  # 数据量

    @bean.check_money_type(1)
    def __init__(self, money_type):
        """

        :param money_type: 类型
        """
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.type_ = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.title = f'{self.type_} 历史涨跌幅'
        self.foc = focus.Focus('history_monitor')
        self.options, _ = self.foc.get(self.money_type)

        self.adapter = {
            'stock': StockHistoryMonitor,
            'fund': FundHistoryMonitor,
        }[money_type]

        self.datas = self._load()
        # 对原始数据进行处理
        self.objs = [
            self.adapter(cur_data, his_data, list(filter(lambda option: option['code'] == code, self.options))[0])
            for code, cur_data, his_data in self.datas
        ]

    def _load(self) -> list:
        """
        加载数据
        :return: [(code, 当前数据、历史数据)]
        """
        assert self.options, '无监控项，请添加配置后再来。'
        codes = list(set([option['code'] for option in self.options]))

        def one(code) -> [Union[dict, None], Union[dict, None]]:
            # 获取当前最新数据，再结合历史数据，处理时需要过滤掉该日期的数据。
            # 不可缓存当前最新数据
            data, ok = self.api.fetch_current(code)
            if not (ok and data):
                return None

            key = f'history_monitor.{self.money_type}.{code}.{HistoryMonitor.MaxLimit}'
            if cache.exist(key):
                return data, cache.get(key)

            # 比较历史数据时，由于第一条可能是当日最新的数据，因此需要多查一条数据。在处理时会过滤掉当日的数据
            res, ok = self.adapter.load(self.api, code, HistoryMonitor.MaxLimit + 1)
            if ok:
                bean.set_cache_expire_today(key, res)
            if ok and res:
                return data, res
            return None

        # # 单线程
        # datas = []
        # for _code in codes:
        #     _data = one(_code)
        #     datas.append(_data)

        # 多线程
        args_list = [[(_code,)] for _code in codes]
        datas = pools.execute_thread(one, args_list)

        return [(codes[index], *datas[index]) for index in range(len(codes)) if datas[index]]

    def get_message(self, is_open=False, **kwargs) -> List:
        all_msg = []
        for obj in self.objs:
            if is_open and not obj.opening:
                continue
            all_msg.extend(obj.get_message(**kwargs))

        return all_msg


class StockHistoryMonitor:
    relate_fields = {
        **StockHistory.relate_fields,
    }

    def __init__(self, cur_data, his_data: dict, option: dict):
        self._opening = True
        self.code = option['code']
        # self.name = process.process.get_codes_name('stock', self.code)[self.code]
        self.name = cur_data[StockMonitor.get_relate('name')]
        self.option = option
        self._data = self._resolve_data(cur_data, his_data)

    def __repr__(self):
        return f'{self.name} [{self.code}]'

    @classmethod
    def load(cls, api, code, limit):
        logging.info(f'开始查询历史数据：stock [{code}]')
        return api.fetch_history(code, limit=limit)

    @property
    def opening(self):
        return self._opening

    def _resolve_data(self, cur_data: dict, his_data: dict) -> Union[List[dict], None]:
        # 判断是否开市
        if not his_data:
            self._opening = False
            return
        else:
            date_time = utils.time2str(cur_data[StockMonitor.get_relate('time')], fmt='%Y-%m-%d', tz=config.CronZone)
            if date_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
                self._opening = False
                return
            point = 10 ** int(cur_data[StockMonitor.get_relate('point')])
            current_worth = cur_data[StockMonitor.get_relate('current_worth')] / point

        rename_cols = {field_conf['field']: field for field, field_conf in StockHistoryMonitor.relate_fields.items()
                       if field_conf['field']}

        data_df = pd.DataFrame(his_data['klines'][::-1])
        data_df.rename(columns=rename_cols, inplace=True)
        data_df = data_df.loc[data_df['date'] != date_time, rename_cols.values()]
        data_df = data_df.fillna(np.nan).reset_index().assign(index=(lambda x: 1 + np.arange(len(x))))
        data_df = data_df.loc[:(HistoryMonitor.MaxLimit - 1), :]
        if data_df.empty:
            return None
        data_df['relative.rate'] = data_df.apply(
            lambda item: 100 * (current_worth - float(item['end_worth'])) / float(item['end_worth']),
            axis=1)

        return solve_history_monitor_data(data_df, self.option)

    def get_message(self, to_cache: bool = True) -> List[str]:
        all_msg = []
        if not self._data:
            return all_msg

        for item in self._data:
            key = f'history_monitor.stock.{self.code}.{item["target"]}.{item["type"]}'
            if to_cache and cache.exist(key):
                continue
            if to_cache:
                bean.set_cache_expire_today(key, True)
            data = item['data']
            mode = {'growth': '涨幅', 'lessen': '跌幅'}
            info = f'{self.name} [{self.code}]\n' \
                   f'{item["target"]}日 {mode[item["type"]]}：{item["option"][item["type"]]}\n\n' \
                   f'历史日期：{data["date"]}\n' \
                   f'净值：{data["end_worth"]}\n' \
                   f'幅度：{"%.2f" % (data["relative.rate"])} %'
            all_msg.append(info)

        return all_msg


def solve_history_monitor_data(his_df: pd.DataFrame, options: dict) -> List[dict]:
    """
    处理历史涨跌幅的数据，用于匹配历史监控
    :param his_df: 历史数据。col: {index: 索引、date: 日期、end_worth: 收盘值、relative.rate: 相对涨跌幅}
    :param options: 监控配置
    :return:
    """
    res = []

    # # 模式一：3: 1~3; 5: 4~5; 7: 6~7; 15: 8~15; 30: 16~30
    # data = his_df.to_dict(orient='records')
    # record = set()  # 若同一个规则有多条数据符合，则只取最近的一条
    # for row in data:
    #     index = row['index']
    #     if index <= 3:
    #         target = 3
    #     elif 3 < index <= 7:
    #         target = 7
    #     elif 7 < index <= 15:
    #         target = 15
    #     else:
    #         target = 30
    #     option = options[str(target)]
    #     growth, lessen = option['growth'], option['lessen']
    #
    #     rate = row['relative.rate']
    #
    #     if growth and rate >= growth and f'{target}.growth' not in record:
    #         res.append({'target': target, 'option': option, 'type': 'growth', 'data': row})
    #         record.add(f'{target}.growth')
    #     if lessen and 0 > -lessen > rate and f'{target}.lessen' not in record:
    #         res.append({'target': target, 'option': option, 'type': 'lessen', 'data': row})
    #         record.add(f'{target}.lessen')

    # 模式二：3: 1~3; 5: 1~5; 7: 1~7; 15: 1~15; 30: 1~30
    for day, option in options.items():
        if day == 'code':
            continue
        if not any(option.values()):
            continue
        target = int(day)
        option_item_datas = [{'index': index, **option} for index in range(1, target + 1)]
        option_df = pd.DataFrame(option_item_datas).fillna(np.nan)
        df = pd.merge(his_df, option_df, on='index', how='left')

        growth_df = df.loc[df['relative.rate'] >= df['growth'], :].head(1)
        lessen_df = df.loc[(0 > -df['lessen']) & (-df['lessen'] >= df['relative.rate']), :].head(1)
        if not growth_df.empty:
            res.append({'target': target, 'option': option, 'type': 'growth',
                        'data': growth_df.to_dict(orient='records')[0]})
        if not lessen_df.empty:
            res.append({'target': target, 'option': option, 'type': 'lessen',
                        'data': lessen_df.to_dict(orient='records')[0]})

    return res


class FundHistoryMonitor:
    relate_fields = {
        **FundHistory.relate_fields,
    }

    def __init__(self, cur_data: dict, his_data: dict, option: dict):
        self._opening = True
        self.code = option['code']
        self.name = cur_data[FundMonitor.get_relate('name')]
        self.option = option
        self._data = self._resolve_data(cur_data, his_data)

    @property
    def opening(self):
        return self._opening

    @classmethod
    def load(cls, api, code, limit):
        logging.info(f'开始查询历史数据：fund [{code}]')
        start_date = utils.get_delay_date(delay=-limit, tz=config.CronZone)
        res, ok = api.fetch_history(code, start_date=start_date)
        max_times = 5

        def supplement(success: bool, last_date, times=0):
            """
            补充数据的数量（由于休市，导致数据量不足limit）
            :param success: 上次的查询是否成功
            :param last_date: 上次查询的开始日期
            :param times: 重试次数
            :return:
            """
            # 未避免极端情况导致的死递归，故限制最大递归次数
            if success and len(res) < limit and times < max_times:
                next_start_date = utils.get_delay_date(last_date, delay=len(res) - limit)
                next_res, next_ok = api.fetch_history(code,
                                                      start_date=next_start_date,
                                                      end_date=utils.get_delay_date(last_date, delay=-1), )
                if next_ok:
                    res.extend(next_res)
                # 当此次递归的日期内均为休市情况，则next_res为空，需要继续往前递归。所以success只能以next_ok来判断。
                return supplement(next_ok, next_start_date, times + 1)

        supplement(res and ok, start_date, 0)
        return res, ok

    def _resolve_data(self, cur_data, his_data) -> Union[List[dict], None]:
        rename_cols = {field_conf['field']: field for field, field_conf in FundHistoryMonitor.relate_fields.items()
                       if field_conf['field']}

        # 判断是否开市
        if not his_data:
            self._opening = False
            return
        else:
            date_time = cur_data[FundMonitor.get_relate('time')].split(' ')[0]
            if date_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
                self._opening = False
                return
            current_worth = float(cur_data[FundMonitor.get_relate('current_worth')])

        data_df = pd.DataFrame(his_data)
        data_df.rename(columns=rename_cols, inplace=True)

        data_df = data_df.loc[data_df['date'] != date_time, rename_cols.values()]
        data_df = data_df.fillna(np.nan).reset_index().assign(index=(lambda x: 1 + np.arange(len(x))))  # 行索引从1开始
        data_df = data_df.loc[:(HistoryMonitor.MaxLimit - 1), :]  # 只需要前 HistoryMonitor.MaxLimit 行数据
        if data_df.empty:
            return None
        data_df['relative.rate'] = data_df.apply(
            lambda item: 100 * (current_worth - float(item['end_worth'])) / float(item['end_worth']),
            axis=1)

        return solve_history_monitor_data(data_df, self.option)

    def get_message(self, to_cache: bool = True) -> List[str]:
        all_msg = []
        if not self._data:
            return all_msg

        for item in self._data:
            key = f'history_monitor.fund.{self.code}.{item["target"]}.{item["type"]}'
            if to_cache and cache.exist(key):
                continue
            if to_cache:
                bean.set_cache_expire_today(key, True)
            data = item['data']
            mode = {'growth': '涨幅', 'lessen': '跌幅'}
            info = f'{self.name} [{self.code}]\n' \
                   f'{item["target"]}日 {mode[item["type"]]}：{item["option"][item["type"]]}\n\n' \
                   f'历史日期：{data["date"]}\n' \
                   f'净值：{data["end_worth"]}\n' \
                   f'幅度：{"%.2f" % (data["relative.rate"])} %'
            all_msg.append(info)

        return all_msg


if __name__ == '__main__':
    from utils import log_util

    log_util.init_logging()

    monitor = HistoryMonitor('fund')
    print(monitor.get_message(is_open=True))
