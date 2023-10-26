#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/29 14:36
# FileName: 调度任务

import asyncio

from module.process import WorthProcess, MonitorProcess
import sockets
from utils import send_msg, utils
import config


async def send_money(money_type, *, task_type, choke=False, is_broad=False):
    """

    :param money_type: 基金/股票
    :param task_type: 任务类型。worth: 净值; monitor: 监控
    :param choke: 是否阻塞。避免单线的定时调度相互阻塞
    :param is_broad: 是否广播
    :return:
    """
    process_task = {'worth': WorthProcess, 'monitor': MonitorProcess}
    assert task_type in process_task, 'error task_type'

    if is_broad and not sockets.clients:  # 无客户端连接时，跳过广播的定时任务
        return
    print(f'{utils.now_time(tz=config.CronZone)}: Start send {task_type} —— {money_type}')

    async def send(processor: process_task[task_type]):
        if processor and processor.datas:
            messages = processor.get_message(is_open=True, to_cache=not is_broad)
            if not messages:
                return
            if is_broad:
                for message in messages:
                    await sockets.broadcast_not_repeat(dict(
                        type=task_type,
                        money_type=money_type,
                        title=f'【{processor.title}】{utils.now_time(tz=config.CronZone)}',
                        content=message,
                    ), key=utils.gen_hash(message))
            else:
                for message in messages:
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
