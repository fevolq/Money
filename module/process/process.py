#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:47
# FileName:

from typing import Union

from api import eastmoney
from module.process.worth import FundWorth, StockWorth
from module.process.monitor import FundMonitor, StockMonitor
from utils import pools
from module import bean, cache


@bean.check_money_type(0)
def get_relate_field(money_type, focus_type, field) -> Union[dict, None]:
    relate = {
        'fund.worth': FundWorth.relate_fields,
        'stock.worth': StockWorth.relate_fields,
        'fund.monitor': FundMonitor.relate_fields,
        'stock.monitor': StockMonitor.relate_fields,
    }
    return relate.get(f'{money_type}.{focus_type}', {}).get(field, None)


@bean.check_money_type(0)
def get_codes_name(money_type, codes: Union[str, list]) -> dict:
    """
    获取codes的名称
    :param money_type:
    :param codes:
    :return: {code: name}
    """
    codes = codes if isinstance(codes, list) else [codes]

    key = 'code_name'
    if not cache.exist(key):
        bean.set_cache_expire_today(key, {})
    codes_name = cache.get(key)

    miss_name_codes = [code.strip() for code in codes if f'{money_type}.{code}' not in codes_name]
    if miss_name_codes:
        east_api = eastmoney.EastMoney(money_type)
        codes_info_data = pools.execute_thread(lambda code: east_api.fetch_current(code),
                                               [[(code,)] for code in miss_name_codes])
        name_field = get_relate_field(money_type, 'worth', 'name')

        new_codes_name = {
            f'{money_type}.{code}': codes_info_data[index][0][name_field['field']]
            if codes_info_data[index][0] and name_field else None
            for index, code in enumerate(miss_name_codes)
        }
        codes_name.update(new_codes_name)

    return {code: codes_name[f'{money_type}.{code}'] for code in codes}
