#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:47
# FileName:

import json
from typing import Union, List

import pandas as pd
import numpy as np

from api import eastmoney
from utils import utils, pools
from module import bean, focus, cache
import config


class WorthProcess:
    """净值"""

    expire = 60  # 缓存时间

    @bean.check_money_type(1)
    def __init__(self, money_type, *, codes: Union[str, int, tuple, list, set] = None):
        """

        :param money_type: 类型
        :param codes: 代码
        """
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.codes = codes if isinstance(codes, (tuple, list, set, type(None))) else [str(code) for code in
                                                                                      str(codes).split(',') if code]
        self.title = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.foc = focus.Focus('worth')

        self.datas = self._load()

        # 对原始数据进行展示处理
        self.datas_obj = [get_worth_data_obj(self.money_type)(data) for data in self.datas]

    def _get_codes(self):
        if not self.codes:
            self.codes, _ = self.foc.get(self.money_type)

            assert self.codes, '无关注项，请添加关注后再来。'

        return self.codes

    def _load(self) -> list:
        """获取最新原始数据"""
        codes = self._get_codes()

        def one(code) -> Union[dict, None]:
            key = f'worth.{self.money_type}.{code}'
            if config.WorthUseCache and cache.exist(key):
                return cache.get(key)

            data, ok = self.api.fetch_current(code)
            if config.WorthUseCache and ok:
                cache.set(key, data, expire=WorthProcess.expire)
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

    def get_data(self, is_open=False) -> List:
        """
        获取数据
        :param is_open: 是否过滤掉今日未开市的数据
        :return:
        """
        # return [data_obj.get_data() for data_obj in self.datas_obj if not is_open and data_obj.opening]
        result = []
        for data_obj in self.datas_obj:
            if is_open and not data_obj.opening:
                continue
            result.append(data_obj.get_data())
        return result

    def get_message(self, is_open=False) -> str:
        """
        获取信息
        :param is_open: 是否过滤掉今日未开市的数据
        :return:
        """
        # all_msg = [data_obj.get_message() for data_obj in self.datas_obj if data_obj.opening]
        all_msg = []
        for data_obj in self.datas_obj:
            if is_open and not data_obj.opening:
                continue
            all_msg.append(data_obj.get_message())

        content = '\n\n'.join(all_msg)

        return content

    def get_fields(self):
        return self.datas_obj[0].get_fields() if self.datas_obj else []


@bean.check_money_type(0)
def get_worth_data_obj(money_type):
    return {
        'stock': StockWorthData,
        'fund': FundWorthData,
    }[money_type]


class StockWorthData:
    relate_fields = {
        'code': {'field': 'f57', 'label': '代码'},
        'name': {'field': 'f58', 'label': '名称'},
        'start_worth': {'field': 'f46', 'label': '开始值'},
        'standard_worth': {'field': 'f60', 'label': '基准值'},
        'current_worth': {'field': 'f43', 'label': '当前值'},
        'rate': {'field': '', 'label': '涨跌幅'},
        'time': {'field': 'f86', 'label': '数据时间'},
        'point': {'field': 'f59', 'label': '进制', 'show': False},
    }

    def __init__(self, data):
        self._opening = True  # 是否开市
        self._data = self._resolve_data(data)

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, *, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data):
        data_time = utils.time2str(data[self.get_relate('time')], fmt='%Y-%m-%d', tz=config.CronZone)
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        # 处理原始数据
        result = {field: data.get(field_conf['field'], '') for field, field_conf in self.relate_fields.items()}
        if result['standard_worth'] and result['current_worth']:
            rate = (float(result['current_worth']) - float(result['standard_worth'])) / float(
                result['standard_worth'])
            result['rate'] = f'{"%.2f" % (rate * 100)}%'

        result['time'] = utils.time2str(result['time'], tz=config.CronZone)
        point = 10 ** int(result.pop('point'))
        for field in ('start_worth', 'standard_worth', 'current_worth'):
            result[field] = result[field] / point

        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'{self.get_relate("standard_worth", key="label")}：{self._data["standard_worth"]}\n' \
               f'{self.get_relate("start_worth", key="label")}：{self._data["start_worth"]}\n' \
               f'{self.get_relate("current_worth", key="label")}：{self._data["current_worth"]}\n' \
               f'{self.get_relate("rate", key="label")}：{self._data["rate"]}\n' \
               f'{self.get_relate("time", key="label")}：{self._data["time"]}'

    def get_fields(self):
        return [{'label': field_conf['label'], 'value': field} for field, field_conf in self.relate_fields.items() if
                field_conf.get('show', True)]
        # return {field: field_conf['label'] for field, field_conf in self.relate_fields.items() if
        #         field_conf.get('show', True)}


class FundWorthData:
    relate_fields = {
        'code': {'field': 'fundcode', 'label': '代码'},
        'name': {'field': 'name', 'label': '名称'},
        'start_worth': {'field': 'dwjz', 'label': '开始值'},
        'current_worth': {'field': 'gsz', 'label': '当前值'},
        'rate': {'field': 'gszzl', 'label': '涨跌幅'},
        'time': {'field': 'gztime', 'label': '数据时间'},
    }

    def __init__(self, data):
        self._opening = True  # 是否开市
        self._data = self._resolve_data(data)

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, *, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data):
        data_time = data[self.get_relate('time')].split(' ')[0]
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        # 处理原始数据
        result = {field: data.get(field_conf['field'], '') for field, field_conf in self.relate_fields.items()}
        result['rate'] = f'{result["rate"]}%'
        for field in ('start_worth', 'current_worth'):
            if not result[field]:
                continue
            result[field] = float(result[field])

        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'{self.get_relate("start_worth", key="label")}：{self._data["start_worth"]}\n' \
               f'{self.get_relate("current_worth", key="label")}：{self._data["current_worth"]}\n' \
               f'{self.get_relate("rate", key="label")}：{self._data["rate"]}\n' \
               f'{self.get_relate("time", key="label")}：{self._data["time"]}'

    def get_fields(self):
        return [{'label': field_conf['label'], 'value': field} for field, field_conf in self.relate_fields.items() if
                field_conf.get('show', True)]
        # return {field: field_conf['label'] for field, field_conf in self.relate_fields.items() if
        #         field_conf.get('show', True)}


class MonitorProcess:
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
        self.datas = self._load()
        # 对原始数据进行展示处理
        self.datas_obj = [get_monitor_data_obj(self.money_type)(data, self.options) for data in self.datas]

    def _load(self) -> list:
        assert self.options, '无监控项，请添加配置后再来。'
        codes = set([option['code'] for option in self.options])

        def one(code) -> Union[dict, None]:
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

    def get_message(self, is_open=False):
        all_msg = []
        for data_obj in self.datas_obj:
            if is_open and not data_obj.opening:
                continue
            all_msg.extend(data_obj.get_message())

        content = '\n\n'.join(all_msg)

        return content


@bean.check_money_type(0)
def get_monitor_data_obj(money_type):
    return {
        'stock': StockMonitorData,
        'fund': FundMonitorData,
    }[money_type]


class StockMonitorData:
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
        **StockWorthData.relate_fields,
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
            columns={field_conf['field']: field for field, field_conf in StockWorthData.relate_fields.items()},
            inplace=True)
        data_df = data_df.fillna(np.nan)
        df_options = pd.DataFrame(self._options)
        df_options.rename(
            columns={field_conf['field']: field for field, field_conf in FundMonitorData.relate_fields.items()},
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

    def get_message(self) -> List[str]:
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
                if cache.exist(key):
                    continue
                if int(bin(flag & flag_value), 2):
                    row_msg.append(f'{flag_conf["label"]}：{row[flag_conf["data_field"]]}')
                    set_cache_expire_today(key, True)
            if row_msg:
                row_msg.insert(0,
                               f'【{row["option.id"]}】匹配\n'
                               f'{self._initial_data[self.get_relate("name")]}'
                               f' [{self._initial_data[self.get_relate("code")]}]\n'
                               f'备注：{row["option.remark"]}')
                all_msg.append('\n'.join(row_msg))

        return all_msg


class FundMonitorData:
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
        **FundWorthData.relate_fields,
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
            columns={field_conf['field']: field for field, field_conf in FundWorthData.relate_fields.items()},
            inplace=True)
        data_df = data_df.fillna(np.nan)
        df_options = pd.DataFrame(self._options)
        df_options.rename(
            columns={field_conf['field']: field for field, field_conf in FundMonitorData.relate_fields.items()},
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

    def get_message(self) -> List[str]:
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
                if cache.exist(key):
                    continue
                if int(bin(flag & flag_value), 2):
                    row_msg.append(f'{flag_conf["label"]}：{row[flag_conf["data_field"]]}')
                    set_cache_expire_today(key, True)
            if row_msg:
                row_msg.insert(0,
                               f'【{row["option.id"]}】匹配\n'
                               f'{self._initial_data[self.get_relate("name")]}'
                               f' [{self._initial_data[self.get_relate("code")]}]\n'
                               f'备注：{row["option.remark"]}')
                all_msg.append('\n'.join(row_msg))

        return all_msg


def set_cache_expire_today(key, value):
    """
    设置当天失效的缓存
    :param key:
    :param value:
    :return:
    """
    next_date = utils.get_delay_date(delay=1, tz=config.CronZone)
    today_expire = utils.str2time(next_date, fmt="%Y-%m-%d", tz=config.CronZone) - utils.str2time(
        tz=config.CronZone)  # 当日剩余时间
    cache.set(key, value, expire=int(today_expire) + 1)


@bean.check_money_type(0)
def get_relate_field(money_type, focus_type, field) -> Union[dict, None]:
    relate = {
        'fund.worth': FundWorthData.relate_fields,
        'stock.worth': StockWorthData.relate_fields,
        'fund.monitor': FundMonitorData.relate_fields,
        'stock.monitor': StockMonitorData.relate_fields,
    }
    return relate.get(f'{money_type}.{focus_type}', {}).get(field, None)


@bean.check_money_type(0)
def get_codes_name(money_type, codes: Union[str, list]) -> dict:
    """
    获取codes的名称
    :param money_type:
    :param codes:
    :return:
    """
    codes = codes if isinstance(codes, list) else [codes]

    key = 'code_name'
    if not cache.exist(key):
        set_cache_expire_today(key, {})
    codes_name = cache.get(key)

    no_name_codes = [code.strip() for code in codes if f'{money_type}.{code}' not in codes_name]
    if no_name_codes:
        east_api = eastmoney.EastMoney(money_type)
        codes_info_data = pools.execute_thread(lambda code: east_api.fetch_current(code),
                                               [[(code,)] for code in no_name_codes])
        name_field = get_relate_field(money_type, 'worth', 'name')

        new_codes_name = {
            f'{money_type}.{code}': codes_info_data[index][0][name_field['field']]
            if codes_info_data[index][0] and name_field else None
            for index, code in enumerate(no_name_codes)
        }
        codes_name.update(new_codes_name)

    return {code: codes_name[f'{money_type}.{code}'] for code in codes}
