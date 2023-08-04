#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:47
# FileName:

from typing import Union, List

from api import eastmoney
from utils import utils, pools
from module import bean, focus


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
        self.foc = focus.Focus('worth')

        self.datas = self.load()

        # 对原始数据进行展示处理
        self.datas_obj = [get_money_data_obj(self.money_type, data) for data in self.datas]

    def _get_codes(self):
        if not self.codes:
            self.codes, _ = self.foc.get(self.money_type)

            assert self.codes, '无关注项，请添加关注后再来。'

        return self.codes

    def load(self):
        """获取最新原始数据"""
        codes = self._get_codes()

        def one(code):
            data, ok = self.api.fetch_current(code)
            if ok and data:
                return data

        # # 单线程
        # datas = []
        # for code_ in codes:
        #     data_ = one(code_)
        #     datas.append(data_)

        # 多线程
        args_list = [[(code_,)] for code_ in codes]
        datas = pools.execute_thread(one, args_list)
        return datas

    def get_data(self) -> List:
        return [data_obj.get_data() for data_obj in self.datas_obj]

    def get_message(self) -> str:
        all_msg = [data_obj.get_message() for data_obj in self.datas_obj]
        content = '\n\n'.join(all_msg)

        return content

    def get_fields(self):
        return self.datas_obj[0].get_fields() if self.datas_obj else {}


@bean.check_money_type(0)
def get_money_data_obj(money_type, data):
    return {
        'stock': StockData,
        'fund': FundData,
    }[money_type](data)


class StockData:
    relate_fields = {
        'code': {'field': 'f57', 'label': '代码'},
        'name': {'field': 'f58', 'label': '名称'},
        'start_worth': {'field': 'f46', 'label': '开始值'},
        'standard_worth': {'field': 'f60', 'label': '基准值'},
        'current_worth': {'field': 'f43', 'label': '当前值'},
        'rate': {'field': '', 'label': '涨跌幅'},
        'time': {'field': 'f86', 'label': '数据时间'},
    }

    def __init__(self, data):
        self._data = self._resolve_data(data)

    def _get_relate_field(self, field):
        return self.relate_fields[field]['field'] if field in self.relate_fields else ''

    def _get_relate_label(self, field):
        return self.relate_fields[field]['label'] if field in self.relate_fields else ''

    def _resolve_data(self, data):
        # 处理原始数据
        data[self._get_relate_field('time')] = utils.time2str(data[self._get_relate_field('time')])
        point = 10 ** int(data['f59'])
        for field in ('start_worth', 'standard_worth', 'current_worth'):
            data[self._get_relate_field(field)] = data[self._get_relate_field(field)] / point

        # 获取指定数据
        result = {field: data.get(self._get_relate_field(field), '') for field in self.relate_fields}
        if result['standard_worth'] and result['current_worth']:
            rate = (float(result['current_worth']) - float(result['standard_worth'])) / float(
                result['standard_worth'])
            result['rate'] = f'{"%.2f" % (rate * 100)}%'

        return result

    def get_data(self):
        return self._data

    def get_message(self):
        return f'{self._data["name"]} [{self._data["code"]}]\n' \
               f'{self._get_relate_label("standard_worth")}：{self._data["standard_worth"]}\n' \
               f'{self._get_relate_label("start_worth")}：{self._data["start_worth"]}\n' \
               f'{self._get_relate_label("current_worth")}：{self._data["current_worth"]}\n' \
               f'{self._get_relate_label("rate")}：{self._data["rate"]}\n' \
               f'{self._get_relate_label("time")}：{self._data["time"]}'

    def get_fields(self):
        return {field: self.relate_fields[field]['label'] for field in self.relate_fields}


class FundData:
    relate_fields = {
        'code': {'field': 'fundcode', 'label': '代码'},
        'name': {'field': 'name', 'label': '名称'},
        'start_worth': {'field': 'dwjz', 'label': '开始值'},
        'current_worth': {'field': 'gsz', 'label': '当前值'},
        'rate': {'field': 'gszzl', 'label': '涨跌幅'},
        'time': {'field': 'gztime', 'label': '数据时间'},
    }

    def __init__(self, data):
        self._data = self._resolve_data(data)

    def _get_relate_field(self, field):
        return self.relate_fields[field]['field'] if field in self.relate_fields else ''

    def _get_relate_label(self, field):
        return self.relate_fields[field]['label'] if field in self.relate_fields else ''

    def _resolve_data(self, data):
        # 获取指定数据
        result = {field: data.get(self._get_relate_field(field), '') for field in self.relate_fields}
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
               f'{self._get_relate_label("start_worth")}：{self._data["start_worth"]}\n' \
               f'{self._get_relate_label("current_worth")}：{self._data["current_worth"]}\n' \
               f'{self._get_relate_label("rate")}：{self._data["rate"]}\n' \
               f'{self._get_relate_label("time")}：{self._data["time"]}'

    def get_fields(self):
        return {field: self.relate_fields[field]['label'] for field in self.relate_fields}
