#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:47
# FileName:

from typing import Union, List

from api import eastmoney
from utils import utils
from module import bean, watch


class Process:
    relation_fields = {
        'stock': {
            'code': 'f57',
            'name': 'f58',
            'start_worth': 'f46',
            'standard_worth': 'f60',
            'current_worth': 'f43',
            'rate': '',
            'time': 'f86',
        },
        'fund': {
            'code': 'fundcode',
            'name': 'name',
            'start_worth': 'dwjz',
            'current_worth': 'gsz',
            'rate': 'gszzl',
            'time': 'gztime',
        }
    }

    @bean.check_money_type(1)
    def __init__(self, money_type, *, codes: Union[str, int] = None):
        """

        :param money_type: 类型
        :param codes: 代码
        """
        self.api = eastmoney.EastMoney(money_type)
        self.money_type = money_type
        self.codes = codes if isinstance(codes, (list, type(None))) else [str(code) for code in codes.split(',') if
                                                                          code]
        self.title = {
            'stock': '股票',
            'fund': '基金',
        }[self.money_type]

        self.datas = self.load()

        # 对原始数据进行展示处理
        self.datas_obj = [get_money_data_obj(self.money_type, data) for data in self.datas]

    def _get_codes(self):
        if not self.codes:
            data = watch.load_watch()
            if data.get(self.money_type):
                self.codes = data[self.money_type]

            assert self.codes, '无关注项，请添加关注后再来。'

        return self.codes

    def load(self):
        """获取最新原始数据"""
        datas = []
        codes = self._get_codes()
        for code in codes:
            data, ok = self.api.fetch_current(code)
            if not ok or not data:
                continue

            datas.append(data)
        return datas

    def get_data(self) -> List:
        return [data_obj.get_data() for data_obj in self.datas_obj]

    def get_message(self) -> str:
        all_msg = [data_obj.get_message() for data_obj in self.datas_obj]
        content = '\n\n'.join(all_msg)

        return content


@bean.check_money_type(0)
def get_money_data_obj(money_type, data):
    return {
        'stock': StockData,
        'fund': FundData,
    }[money_type](data)


class StockData:
    relate_fields = {
        'code': 'f57',
        'name': 'f58',
        'start_worth': 'f46',
        'standard_worth': 'f60',
        'current_worth': 'f43',
        'rate': '',
        'time': 'f86',
    }

    def __init__(self, data):
        self._data = self._resolve_data(data)

    def _resolve_data(self, data):
        # 处理原始数据
        data['time'] = utils.time2str(data[self.relate_fields['time']])
        point = 10 ** int(data['f59'])
        for field in ('start_worth', 'standard_worth', 'current_worth'):
            data[self.relate_fields[field]] = data[self.relate_fields[field]] / point

        # 获取指定数据
        result = {field: data.get(relation, '') for field, relation in self.relate_fields.items()}
        if result['standard_worth'] and result['current_worth']:
            rate = (float(result['current_worth']) - float(result['standard_worth'])) / float(
                result['standard_worth'])
            result['rate'] = f'{"%.2f" % (rate * 100)}%'

        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'当日基准：{self._data["standard_worth"]}\n' \
               f'当日初始：{self._data["start_worth"]}\n' \
               f'当前最新：{self._data["current_worth"]}\n' \
               f'涨跌幅：{self._data["rate"]}\n' \
               f'数据时间：{self._data["time"]}'


class FundData:
    relate_fields = {
        'code': 'fundcode',
        'name': 'name',
        'start_worth': 'dwjz',
        'current_worth': 'gsz',
        'rate': 'gszzl',
        'time': 'gztime',
    }

    def __init__(self, data):
        self._data = self._resolve_data(data)

    def _resolve_data(self, data):
        # 获取指定数据
        result = {field: data.get(relation, '') for field, relation in self.relate_fields.items()}
        result['rate'] = f'{result["rate"]}%'

        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'当日初始：{self._data["start_worth"]}\n' \
               f'当前最新：{self._data["current_worth"]}\n' \
               f'涨跌幅：{self._data["rate"]}\n' \
               f'数据时间：{self._data["time"]}'
