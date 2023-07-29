#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:47
# FileName:

from typing import Union

from api import eastmoney
from utils import utils
from module import bean, watch


class Process:
    relation_fields = {
        'stock': {
            'code': 'f57',
            'name': 'f58',
            'init_worth': 'f46',
            'current_worth': 'f43',
            'rate': '',
            'time': 'f86',
        },
        'fund': {
            'code': 'fundcode',
            'name': 'name',
            'init_worth': 'dwjz',
            'current_worth': 'gsz',
            'rate': '',
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

        self.data = self.get_data()
        self.msg = self.gen_message()

    def _get_codes(self):
        if not self.codes:
            data = watch.load_watch()
            if data.get(self.money_type):
                self.codes = data[self.money_type]

            assert self.codes, '无关注项，请添加关注后再来。'

        return self.codes

    def get_data(self):
        result = []

        codes = self._get_codes()
        for code in codes:
            data, ok = self.api.fetch_current(code)
            if not ok or not data:
                continue

            if self.money_type == 'stock':
                # 将两个模式的数据匹配成相同格式
                data[self.relation_fields[self.money_type]['time']] = utils.time2str(
                    data[self.relation_fields[self.money_type]['time']])
                data[self.relation_fields[self.money_type]['init_worth']] = data[self.relation_fields[self.money_type][
                    'init_worth']] / 1000
                data[self.relation_fields[self.money_type]['current_worth']] = data[self.relation_fields[
                    self.money_type]['current_worth']] / 1000

            tmp_result = {field: data.get(relation, '') for field, relation in
                          self.relation_fields[self.money_type].items()}
            if tmp_result['init_worth'] and tmp_result['current_worth']:
                rate = (float(tmp_result['current_worth']) - float(tmp_result['init_worth'])) / float(
                    tmp_result['init_worth'])
                tmp_result['rate'] = f'{"%.2f" % (rate * 100)}%'

            result.append(tmp_result)

        return result

    def gen_message(self):
        content = f'【{self.title}】{utils.asia_local_time()}\n\n'
        tmp = [f'{row["name"]} [{row["code"]}]\n'
               f'当日基准：{row["init_worth"]}\n'
               f'当前最新：{row["current_worth"]}\n'
               f'涨跌幅：{row["rate"]}\n'
               f'数据时间：{row["time"]}'
               for row in self.data if self.data]
        content += '\n\n'.join(tmp)

        return content
