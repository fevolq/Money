#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/11/21 13:58
# FileName:

import json
import logging
from typing import Union, List

import pandas as pd

from api import eastmoney
from utils import utils, pools
from module import bean, focus, cache, process
import config


class Worth:
    """估值"""

    expire = 60  # 缓存时间

    @bean.check_money_type(1)
    def __init__(self, money_type, *, codes: Union[str, int, tuple, list, set] = None):
        """

        :param money_type: 类型
        :param codes: 代码
        """
        logging.info(f'估值查询：{money_type}, {codes}')
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.codes = codes if isinstance(codes, (tuple, list, set, type(None))) \
            else [str(code) for code in str(codes).split(',') if code]
        self.type_ = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.title = f'{self.type_} 估值'
        self.foc = focus.Focus('worth')

        self.adapter = {
            'stock': StockWorth,
            'fund': FundWorth,
        }[money_type]

        self.datas: List[dict] = self._load()
        # 对原始数据进行处理
        self.objs = [
            self.adapter(data)
            for data in self.datas
        ]

    def _get_options(self):
        options = []

        record_options, _ = self.foc.get(self.money_type)
        if not self.codes:
            options = record_options
        else:
            record_codes = {option['code']: option for option in record_options}
            for code in self.codes:
                option = record_codes.get(code, {'code': code})
                options.append(option)

        assert options, '无关注项，请添加关注后再来。'

        return options

    def _load(self) -> [dict]:
        """获取最新原始数据"""
        options = self._get_options()

        def one(code) -> Union[dict, None]:
            key = f'worth.{self.money_type}.{code}'
            if config.WorthUseCache and cache.exist(key):
                return cache.get(key)

            logging.info(f'开始查询估值：{self.money_type} [{code}]')
            res, ok = self.api.fetch_current(code)
            if config.WorthUseCache and ok:
                cache.set(key, res, expire=Worth.expire)
            if ok and res:
                return res
            return None

        # # 单线程
        # result = []
        # for option in options:
        #     res = one(option['code'])
        #     if not res:
        #         continue
        #     result.append(res)

        # 多线程
        args_list = [[(option['code'],)] for option in options]
        result = pools.execute_thread(one, args_list)

        datas = []
        for index, option in enumerate(options):
            data = result[index]
            if not data:
                continue
            datas.append({
                'option': option,
                'data': data
            })
        return datas

    def get_data(self, is_open=False, **options) -> List:
        """
        获取数据
        :param is_open: 是否过滤掉今日未开市的数据
        :return:
        """
        # return [obj.get_data() for obj in self.objs if not is_open and obj.opening]
        result = []
        for obj in self.objs:
            if is_open and not obj.opening:
                continue
            result.append(obj.get_data(**options))
        return result

    def get_message(self, is_open=False, **kwargs) -> List:
        """
        获取信息
        :param is_open: 是否过滤掉今日未开市的数据
        :return:
        """
        all_msg = []
        for obj in self.objs:
            if is_open and not obj.opening:
                continue
            all_msg.append(obj.get_message())

        return all_msg

    def get_fields(self):
        return self.adapter.get_fields()


class StockWorth:
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
    option_fields = {
        'cost': {'field': 'cost', 'label': '成本'},
        'profit': {'field': 'profit', 'label': '盈利'},
        'regression': {'field': 'regression', 'label': '成本回归'},
    }

    def __init__(self, data: dict):
        self._opening = True  # 是否开市
        self._data = self._resolve_data(data['data'], data['option'])

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, *, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data, option):
        data_time = utils.time2str(data[self.get_relate('time')], fmt='%Y-%m-%d', tz=config.CronZone)
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        # 处理原始数据
        result = {field: data.get(field_conf['field'], '')
                  for field, field_conf in StockWorth.relate_fields.items()}
        if result['standard_worth'] and result['current_worth']:
            rate = (float(result['current_worth']) - float(result['standard_worth'])) / float(
                result['standard_worth'])
            result['rate'] = f'{"%.2f" % (rate * 100)}%'

        result['time'] = utils.time2str(result['time'], tz=config.CronZone)
        point = 10 ** int(result.pop('point'))
        for field in ('start_worth', 'standard_worth', 'current_worth'):
            result[field] = result[field] / point

        result.update({field: '' for field, field_conf in StockWorth.option_fields.items()})
        if option.get(StockWorth.option_fields['cost']['field'], None):
            # 配置中包含了成本
            current_worth = result['current_worth']
            cost = float(option['cost'])
            result['cost'] = cost

            if cost == 0.0:
                result['profit'] = 'inf'
            else:
                profit = (current_worth - cost) / cost
                result['profit'] = f'{"%.2f" % (profit * 100)}%'

            if current_worth == 0.0:
                result['regression'] = 'inf'
            else:
                regression = (cost / current_worth) - 1
                result['regression'] = f'{"%.2f" % (regression * 100)}%'

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

    @classmethod
    def get_fields(cls):
        fields = {**cls.relate_fields, **cls.option_fields}
        return [{'label': field_conf['label'], 'value': field}
                for field, field_conf in fields.items()
                if field_conf.get('show', True)]


class FundWorth:
    relate_fields = {
        'code': {'field': 'fundcode', 'label': '代码'},
        'name': {'field': 'name', 'label': '名称'},
        'start_worth': {'field': 'dwjz', 'label': '开始值'},
        'current_worth': {'field': 'gsz', 'label': '当前值'},
        'rate': {'field': 'gszzl', 'label': '涨跌幅'},
        'time': {'field': 'gztime', 'label': '数据时间'},
    }
    option_fields = {
        'cost': {'field': 'cost', 'label': '成本'},
        'profit': {'field': 'profit', 'label': '盈利'},
        'regression': {'field': 'regression', 'label': '成本回归'},
    }

    def __init__(self, data: dict):
        self._opening = True  # 是否开市
        self._data = self._resolve_data(data['data'], data['option'])

    @property
    def opening(self):
        return self._opening

    @classmethod
    def get_relate(cls, field, *, key='field'):
        return cls.relate_fields[field][key] if field in cls.relate_fields else ''

    def _resolve_data(self, data, option):
        data_time = data[self.get_relate('time')].split(' ')[0]
        if data_time != utils.now_time(fmt='%Y-%m-%d', tz=config.CronZone):
            self._opening = False

        # 处理原始数据
        result = {field: data.get(field_conf['field'], '') for field, field_conf in FundWorth.relate_fields.items()}
        result['rate'] = f'{result["rate"]}%'
        for field in ('start_worth', 'current_worth'):
            if not result[field]:
                continue
            result[field] = float(result[field])

        result.update({field: '' for field, field_conf in FundWorth.option_fields.items()})
        if option.get(FundWorth.option_fields['cost']['field'], None):
            # 配置中包含了成本
            current_worth = result['current_worth']
            cost = float(option['cost'])
            result['cost'] = cost

            profit = (current_worth - cost) / cost
            result['profit'] = f'{"%.2f" % (profit * 100)}%'

            regression = (cost / current_worth) - 1
            result['regression'] = f'{"%.2f" % (regression * 100)}%'
        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'{self.get_relate("start_worth", key="label")}：{self._data["start_worth"]}\n' \
               f'{self.get_relate("current_worth", key="label")}：{self._data["current_worth"]}\n' \
               f'{self.get_relate("rate", key="label")}：{self._data["rate"]}\n' \
               f'{self.get_relate("time", key="label")}：{self._data["time"]}'

    @classmethod
    def get_fields(cls):
        fields = {**cls.relate_fields, **cls.option_fields}
        return [{'label': field_conf['label'], 'value': field}
                for field, field_conf in fields.items()
                if field_conf.get('show', True)]


class History:

    DefaultMonth = 1

    @bean.check_money_type(1)
    def __init__(self, money_type, *, codes: Union[str, int, tuple, list, set] = None, month: Union[str, int] = None):
        """

        :param money_type: 类型
        :param codes: 代码
        """
        logging.info(f'历史查询：{money_type}, {codes}')
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.codes = codes if isinstance(codes, (tuple, list, set, type(None))) \
            else [str(code) for code in str(codes).split(',') if code]
        self.month = int(month or History.DefaultMonth)
        self.type_ = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]
        self.title = f'{self.type_} 历史数据'
        self.foc = focus.Focus('worth')

        self.adapter = {
            'stock': StockHistory,
            'fund': FundHistory,
        }[money_type]

        self.datas: List[dict] = self._load()
        # 对原始数据进行处理
        self.objs = [
            self.adapter(code, data)
            for code, data in self.datas
        ]

    def _get_codes(self):
        if not self.codes:
            record_options, _ = self.foc.get(self.money_type)
            self.codes = [option['code'] for option in record_options]

        assert self.codes, '无关注项，请添加关注后再来。'

        return self.codes

    def _load(self) -> List:
        """加载数据"""
        codes = self._get_codes()
        limit = utils.get_delay(utils.now_time(fmt='%Y-%m-%d'), utils.get_delay_month(-self.month))

        def one(code):
            key = f'history.{self.money_type}.{code}.{limit}'
            if cache.exist(key):
                return cache.get(key)

            logging.info(f'开始查询历史：{self.money_type} [{code}]')
            res, ok = self.adapter.load(self.api, code, limit)
            if ok:
                bean.set_cache_expire_today(key, res)
            if ok and res:
                return res
            return None

        # result = []
        # for code in codes:
        #     result.append(one(code))

        args_list = [[(code,)] for code in codes]
        result = pools.execute_thread(one, args_list)

        return [(codes[index], result[index]) for index in range(len(codes)) if result[index]]

    def get_data(self) -> List:
        """
        获取数据
        :return:
        """
        result = []
        for obj in self.objs:
            data = obj.get_data()
            if data:
                result.append({
                    'code': obj.code,
                    'name': obj.name,
                    'data': data,
                })
        return result

    def get_fields(self):
        return self.adapter.get_fields()


class StockHistory:
    relate_fields = {
        'date': {'field': 'f51', 'label': '数据时间'},
        'start_worth': {'field': 'f52', 'label': '开盘值'},
        'end_worth': {'field': 'f53', 'label': '收盘值'},
        'rate': {'field': 'f59', 'label': '涨跌幅'},
        'change': {'field': 'f60', 'label': '涨跌额', 'show': False},
        'standard': {'field': '', 'label': '基准值'}
    }

    def __init__(self, code, data: dict):
        self.code = code
        self.name = None
        self._data = self._resolve_data(data)

    @classmethod
    def load(cls, api, code, limit):
        logging.info(f'开始查询历史数据：stock [{code}]')
        return api.fetch_history(code, limit=limit)

    def _resolve_data(self, data):
        if not data or not data['klines']:
            return
        self.code = data['code']
        self.name = data['name']
        decimal = f'%.{data["decimal"]}f'

        df = pd.DataFrame(data['klines'][::-1])
        rename_fields = {option['field']: field for field, option in StockHistory.relate_fields.items()
                         if option['field']}
        df.rename(rename_fields, axis=1, inplace=True)
        df['standard'] = df.apply(lambda x: decimal % (float(x['end_worth']) - float(x['change'])), axis=1)

        df = df.loc[:, [field for field, option in StockHistory.relate_fields.items() if option.get('show', True)]]
        return json.loads(df.to_json(orient='records'))

    def get_data(self):
        return self._data

    @classmethod
    def get_fields(cls):
        return [{'label': field_conf['label'], 'value': field}
                for field, field_conf in cls.relate_fields.items()
                if field_conf.get('show', True)]


class FundHistory:
    relate_fields = {
        'date': {'field': 'FSRQ', 'label': '数据时间'},
        'start_worth': {'field': '', 'label': '开盘值'},
        'end_worth': {'field': 'DWJZ', 'label': '收盘值'},
        'rate': {'field': 'JZZZL', 'label': '涨跌幅'},
    }

    def __init__(self, code, data: dict):
        self.code = code
        self.name = process.process.get_codes_name('fund', code).get(code, None)
        self._data = self._resolve_data(data)

    @classmethod
    def load(cls, api, code, limit):
        logging.info(f'开始查询历史数据：fund [{code}]')
        return api.fetch_history(code, start_date=utils.get_delay_date(delay=-limit, tz=config.CronZone))

    def _resolve_data(self, data):
        if not data:
            return

        df = pd.DataFrame(data)
        rename_fields = {option['field']: field for field, option in FundHistory.relate_fields.items()
                         if option['field']}
        df.rename(rename_fields, axis=1, inplace=True)
        # df['start_worth'] = df.apply(lambda x: float(x['end_worth']) / (1 + float(x['rate']) / 100), axis=1)
        # 匹配相同精度
        df['start_worth'] = df.apply(lambda x: f'%.{len(x["end_worth"].split(".")[-1])}f' %
                                               (float(x['end_worth']) / (1 + float(x['rate']) / 100)), axis=1)

        df = df.loc[:, [field for field, option in FundHistory.relate_fields.items() if option.get('show', True)]]
        return json.loads(df.to_json(orient='records'))

    def get_data(self):
        return self._data

    @classmethod
    def get_fields(cls):
        return [{'label': field_conf['label'], 'value': field}
                for field, field_conf in cls.relate_fields.items()
                if field_conf.get('show', True)]
