#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 15:30
# FileName: 东方财富api

import json
import time
from typing import List, Union

import requests
import pandas as pd

from api import fetch
from utils import utils


class EastMoney:

    def __init__(self, mode: str):
        """

        :param mode: fund or stock。基金或股票
        """
        assert mode.lower() in ('stock', 'fund'), 'mode not match!'
        self.mode = mode.lower()

        self.headers = {
            'user-agent': fetch.get_user_agent(),
            'Content-Type': 'application/json; charset=utf-8',
        }

        self.adapter = {
            'stock': Stock,
            'fund': Fund,
        }[self.mode]()

    def action(self, func: str, **kwargs):
        return getattr(self.adapter, func)(**kwargs)

    def fetch_current(self, code, **kwargs):
        """
        获取指定代码的当前数据
        :param code:
        :param kwargs:
        :return:
        """
        relation = {
            'stock': 'fetch_stock_current_detail',
            'fund': 'fetch_fund_current_worth',
        }
        return self.action(relation[self.mode], code=code, **kwargs)


class Stock:
    """股票"""

    detail_fields = {
        'f43': 'current',  # 最新（分）
        'f44': 'highest',  # 最高（分）
        'f45': 'lowest',  # 最低（分）
        'f46': 'start',  # 今开（分）
        'f47': 'total_hand',  # 总手
        'f48': 'total_amount',  # 金额（元）
        'f49': 'external_disk',  # 外盘（元）
        'f50': 'volume_ratio',  # 量比（%）
        'f51': 'max_limit',  # 涨停（分）
        'f52': 'min_limit',  # 跌停（分）
        'f57': 'code',  # 代码
        'f58': 'name',  # 名称
        'f86': 'timestamp',  # 时间戳（分钟）
    }

    def __init__(self):
        self.headers = {
            'user-agent': fetch.get_user_agent(),
            'Content-Type': 'application/json; charset=utf-8',
        }

    def get_quote_id(self, code):
        url = 'https://searchadapter.eastmoney.com/api/suggest/get'
        params = {
            'type': 14,
            'input': code,
        }
        resp = requests.get(url, params=params, headers=self.headers)
        if resp.status_code != 200:
            return ''

        data = resp.json()['QuotationCodeTable']['Data']
        return data[0]['QuoteID'] if data else ''

    def fetch_stock_current_detail(self, code, fields: [] = None) -> (Union[dict, None], bool):
        """
        获取指定股票的最新详情
        :param code: 股票代码
        :param fields: 字段
        :return:
        """
        url = f'https://push2.eastmoney.com/api/qt/stock/get'
        params = {
            'secid': self.get_quote_id(code),
            'fields': ','.join(fields or self.detail_fields.keys())
        }
        resp = requests.get(url, params=params, headers=self.headers)
        if resp.status_code != 200:
            return None, False
        data = resp.json()['data']

        return data, True

    def fetch_stocks(self, fields: [] = None, page=1, result: [] = None) -> (Union[List, None], bool):
        """
        获取所有股票
        :return:
        """
        default_fields = {
            'f12': 'code',  # 代码
            'f14': 'name',  # 名称
            # 'f13': 'stock_type',  # 类型
        }
        all_fs = ['m:0', 'm:1', 't:2', 't:3', 't:6', 't:7', 't:23', 't:80', 't:81', 'f:4', 'f:8', 's:3', 's:2048',
                  'b:BK0804', 'b:BK0707', 'b:BK0498']

        result = result or []

        url = 'https://18.push2.eastmoney.com/api/qt/clist/get'
        page_size = 1000
        params = {
            'fields': ','.join(fields or default_fields.keys()),
            'pz': page_size,
            'pn': page,
            'fs': ','.join(all_fs)
        }
        print(f'开始第{page}页')
        resp = requests.get(url, params=params, headers=self.headers)
        if resp.status_code != 200:
            return None, False

        data = resp.json()['data']

        result.extend(list(data['diff'].values()))
        if data['total'] > page * page_size:
            return self.fetch_stocks(fields=fields, page=page + 1, result=result)

        df = pd.DataFrame(result)
        for field in default_fields:
            if field in df.columns:
                df[default_fields[field]] = df[field]
                df.drop(field, axis=1, inplace=True)

        return json.loads(df.to_json(orient='records'))


class Fund:
    """基金"""

    detail_fields = {
        'gsz': 'current',  # 当前值
        'dwjz': 'start',  # 当日初始值
        'gszzl': 'min_limit',  # 涨跌幅
        'fundcode': 'code',  # 代码
        'name': 'name',  # 名称
        'gztime': 'timestamp',  # 时间戳（分钟）
    }

    def __init__(self):
        self.headers = {
            'user-agent': fetch.get_user_agent(),
            'Content-Type': 'application/json; charset=utf-8',
        }

    def fetch_all_fund(self) -> (Union[List, None], bool):
        """
        基金列表
        :return:
        """
        url = 'http://fund.eastmoney.com/js/fundcode_search.js'
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            return None, False
        data = resp.text
        data = data.lstrip('var r = ').rstrip(';')
        data = json.loads(data)
        return data, True

    def fetch_fund_current_worth(self, code) -> (dict, bool):
        """
        指定时刻的基金净值等
        :param code: 基金代码
        :return: {'fundcode': 基金代码, 'name': 基金名称, 'dwjz': 当日初始值, 'gsz': 当前值（收盘前）, 'gszzl': 涨跌幅, 'gztime': 当前数据时间}
        """
        url = f'http://fundgz.1234567.com.cn/js/{code}.js'
        resp = requests.get(url, headers=self.headers)
        if resp.status_code != 200:
            return None, False
        data = resp.text
        data = data.lstrip('jsonpgz(').rstrip(');')
        data = json.loads(data)
        return data, True

    def fetch_fund_history(self, code, start_date=None, end_date=None, page=1, page_size=20):
        """
        获取指定基金的历史数据
        {
            FSRQ: 净值日期,
            DWJZ: 单位净值,
            LJJZ: 累计净值,
            JZZZL: 日增长率,
            SGZT: 申购状态,
            SHZT: 赎回状态,
        }
        :param code: 基金代码
        :param start_date:
        :param end_date:
        :param page:
        :param page_size:
        :return:
        """
        url = 'http://api.fund.eastmoney.com/f10/lsjz'
        params = {
            'fundCode': code,
            'pageIndex': page,
            'pageSize': page_size,
            'startDate': start_date or utils.asia_local_time('%Y-%m-%d'),
            'endDate': end_date or utils.asia_local_time('%Y-%m-%d'),
            '_': int(time.time() * 1000),
        }
        headers = self.headers
        headers.update({'Referer': 'http://fundf10.eastmoney.com/'})
        response = requests.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return None, False
        json_data = response.json()

        if json_data['ErrCode'] != 0:
            return None, False
        result = json_data['Data']['LSJZList']

        if json_data['TotalCount'] > page * page_size:
            next_result, next_ok = self.fetch_fund_history(code, start_date=start_date, end_date=end_date,
                                                           page=page + 1, page_size=page_size)
            if next_ok:
                result.extend(next_result)

        return result, True


if __name__ == '__main__':
    # stocks = Stock().fetch_stocks()
    # with open('stocks.json', 'w', encoding='utf-8') as f:
    #     json.dump(stocks, f, indent=4, ensure_ascii=False)

    Stock().fetch_stock_current_detail('161226')
    # EastMoney('stock').fetch_current('161226')
