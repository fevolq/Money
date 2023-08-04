#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/29 14:31
# FileName: 定时推送

import asyncio

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from module import task
import config

# 创建一个异步调度器
scheduler = AsyncIOScheduler()

# 注册定时任务
for index, cron in enumerate(config.FundCron):
    if not cron:
        continue

    trigger = CronTrigger.from_crontab(cron, config.CronZone)

    scheduler.add_job(task.worth, args=('fund',), trigger=trigger, id=f'fund_{index}', name=f'Fund Task {index}')

for index, cron in enumerate(config.StockCron):
    if not cron:
        continue

    trigger = CronTrigger.from_crontab(cron, config.CronZone)

    scheduler.add_job(task.worth, args=('stock',), trigger=trigger, id=f'stock_{index}',
                      name=f'Stock Task {index}')


# 启动调度器
async def start_scheduler():
    print(f'开启定时任务...')
    scheduler.start()


# 停止调度器
async def stop_scheduler():
    print(f'终止定时任务...')
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
    asyncio.run(run_scheduler())
