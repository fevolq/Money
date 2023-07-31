#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 21:16
# FileName:

import os

import yaml

# ---------------------------配置----------------------------------
# 飞书机器人
FeiShuRobotUrl = ''

# Server酱
ChanKey = ''

# 定时任务的时区
CronZone = ''

# 基金任务
FundCron = [

]

# 股票任务
StockCron = [

]
# ----------------------------------------------------------------


# ---------------------------覆盖配置----------------------------------
# 从配置文件读取
try:
    with open('conf/config.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    for k, v in data.items():
        locals()[k] = v
except:
    pass


# 从系统环境中重载变量
for var, var_value in locals().copy().items():
    # 变量命名要求大写开头
    if not var[0].isupper() or callable(var_value):
        continue

    locals()[var] = os.getenv(var, var_value)


# 本地测试时，可增加local_config.py来覆盖配置
try:
    from local_config import *
except:
    pass
# ----------------------------------------------------------------
