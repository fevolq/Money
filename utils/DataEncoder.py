#!-*coding:utf-8 -*-
# python3.7
# CreateTime: 2022/10/17 17:38
# FileName: json数据格式转换

import datetime
import json
from decimal import Decimal


class MySQLEncoder(json.JSONEncoder):
    """MySQL类型转json"""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(o, datetime.date):
            return o.strftime("%Y-%m-%d")
        elif isinstance(o, bytes):
            return o.decode()
        elif isinstance(o, Decimal):
            return float(o)
        else:
            return json.JSONEncoder.default(self, o)
