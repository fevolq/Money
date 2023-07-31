#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/29 14:36
# FileName: 调度任务

import asyncio

from module import process
from utils import send_msg, utils
import config


async def send_watch(money_type, choke=False):
    """

    :param money_type:
    :param choke: 是否阻塞。避免单线的定时调度相互阻塞
    :return:
    """
    print(f'{utils.asia_local_time()}: Start send watch —— {money_type}')

    async def send(processor: process.Process):
        if processor and processor.datas:
            send_msg.feishu_robot_msg(config.FeiShuRobotUrl, content=processor.get_message(),
                                      title=f'【{processor.title}】{utils.asia_local_time()}')
            send_msg.chan_msg(processor.title, processor.get_message(), key=config.ChanKey)

    async def money():
        try:
            processor = process.Process(money_type)
        except AssertionError:
            processor = None
        await send(processor)

    if choke:
        await money()
    else:
        asyncio.create_task(money())


if __name__ == '__main__':
    asyncio.run(send_watch('stock', choke=True))
