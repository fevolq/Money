#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/29 14:36
# FileName: 调度任务

import asyncio

from module.process import WorthProcess, MonitorProcess
from utils import send_msg, utils
import config


async def send_money(money_type, *, task_type, choke=False):
    """

    :param money_type: 基金/股票
    :param task_type: 任务类型。worth: 净值; monitor: 监控
    :param choke: 是否阻塞。避免单线的定时调度相互阻塞
    :return:
    """
    process_task = {'worth': WorthProcess, 'monitor': MonitorProcess}
    assert task_type in process_task, 'error task_type'

    print(f'{utils.now_time(tz=config.CronZone)}: Start send {task_type} —— {money_type}')

    async def send(processor: process_task[task_type]):
        if processor and processor.datas:
            message = processor.get_message(is_open=True)
            if not message:
                return
            send_msg.feishu_robot_msg(config.FeiShuRobotUrl, content=message,
                                      title=f'【{processor.title}】{utils.now_time(tz=config.CronZone)}')
            send_msg.chan_msg(processor.title, content=message, key=config.ChanKey)

    async def money():
        try:
            processor = process_task[task_type](money_type)
        except AssertionError:
            processor = None
        await send(processor)

    if choke:
        await money()
    else:
        asyncio.create_task(money())


if __name__ == '__main__':
    asyncio.run(send_money('stock', task_type='worth', choke=True))
