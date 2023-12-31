#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/29 14:31
# FileName: 定时推送

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from module import task
import config

# 创建一个异步调度器
scheduler = AsyncIOScheduler()


def add_job():
    jobs = [
        # 当前估值
        {'cron': config.FundWorthCron, 'title': 'Fund Worth',
         'args': ('fund',), 'kwargs': {'task_type': 'worth'}, },
        {'cron': config.StockWorthCron, 'title': 'Stock Worth',
         'args': ('stock',), 'kwargs': {'task_type': 'worth'}, },

        # 阈值监控
        {'cron': config.FundMonitorCron, 'title': 'Fund Monitor',
         'args': ('fund',), 'kwargs': {'task_type': 'monitor'}, },
        {'cron': config.StockMonitorCron, 'title': 'Stock Monitor',
         'args': ('stock',), 'kwargs': {'task_type': 'monitor'}, },

        # 历史涨跌幅监控
        {'cron': config.FundHisMonitorCron, 'title': 'Fund History Monitor',
         'args': ('fund',), 'kwargs': {'task_type': 'history_monitor'}, },
        {'cron': config.StockHisMonitorCron, 'title': 'Stock History Monitor',
         'args': ('stock',), 'kwargs': {'task_type': 'history_monitor'}, },
    ]
    for job in jobs:
        for index, cron in enumerate(job['cron']):
            if not cron:
                continue

            trigger = CronTrigger.from_crontab(cron, config.CronZone)
            logging.info(f'Add job: {job["title"]}, {cron}')

            scheduler.add_job(task.send_money, args=job['args'], kwargs=job['kwargs'],
                              trigger=trigger, id=f'{job["title"].replace(" ", "_").lower()}_{index}',
                              name=f'{job["title"]} Task {index}')


def add_broadcast_job():
    jobs = [
        {'cron': config.BroadMonitorCron, 'title': 'Broad Fund Monitor',
         'args': ('fund',), 'kwargs': {'task_type': 'monitor'}, },
        {'cron': config.BroadMonitorCron, 'title': 'Broad Stock Monitor',
         'args': ('stock',), 'kwargs': {'task_type': 'monitor'}, },

        {'cron': config.HisBroadMonitorCron, 'title': 'Broad Fund History Monitor',
         'args': ('fund',), 'kwargs': {'task_type': 'history_monitor'}, },
        {'cron': config.HisBroadMonitorCron, 'title': 'Broad Stock History Monitor',
         'args': ('stock',), 'kwargs': {'task_type': 'history_monitor'}, },
    ]
    for job in jobs:
        for index, cron in enumerate(job['cron']):
            if not cron:
                continue

            trigger = CronTrigger.from_crontab(cron, config.CronZone)
            logging.info(f'Add job: {job["title"]}, {cron}')

            scheduler.add_job(task.send_money, args=job['args'], kwargs={**job['kwargs'], 'is_broad': True},
                              trigger=trigger, id=f'{job["title"].replace(" ", "_").lower()}_{index}',
                              name=f'{job["title"]} Task {index}')


# 启动调度器
async def start_scheduler():
    logging.info('开启定时任务...')
    add_job()
    add_broadcast_job()
    scheduler.start()


# 停止调度器
async def stop_scheduler():
    logging.info('终止定时任务...')
    scheduler.shutdown()


# 异步运行调度器
async def run_scheduler():
    await start_scheduler()
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await stop_scheduler()


if __name__ == "__main__":
    from utils import log_util

    log_util.init_logging('', datefmt='%Y-%m-%d %H:%M:%S')
    asyncio.run(run_scheduler())
