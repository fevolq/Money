#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/10/26 15:39
# FileName:

import json
import logging
import time

from module import cache, bean
from utils import utils

clients = {}


class Client:

    def __init__(self, websocket):
        self.websocket = websocket
        self.url = f'{websocket.client.host}:{websocket.client.port}'
        self.timestamp = time.time()
        self.key = utils.gen_hash(f'{self.url} {self.timestamp}')[:6]

        clients[self.key] = self

    @classmethod
    async def register(cls, websocket):
        client = Client(websocket)
        await broadcast({'type': 'user', 'value': len(clients)})
        logging.info(f'register ws: {client.key}')
        return client

    @classmethod
    async def unregister(cls, client):
        logging.info(f'unregister ws: {client.key}')
        if clients.get(client.key):
            clients.pop(client.key)
        await broadcast({'type': 'user', 'value': len(clients)})

    async def send(self, data: dict, *, key: str = None):
        """
        发送给当前客户端
        :param data:
        :param key:
        :return:
        """
        if key:
            key = f'client:{self.key}:{key}'
            if cache.exist(key):  # 避免给同一用户发送重复的通知
                return
            else:
                bean.set_cache_expire_today(key, True)

        logging.info(f'ws[{self.key}] send: {data}')
        await self.websocket.send_json(data)

    async def run(self):
        message = await self.websocket.receive_text()
        data = json.loads(message)
        await self.send(data)


async def broadcast(data: dict):
    """
    广播给所有客户端
    :param data:
    :return:
    """
    for _, client in clients.items():
        await client.send(data)


async def broadcast_not_repeat(data: dict, *, key):
    """
    广播给所有客户端，当客户端已发送过key，则不再发送
    :param data:
    :param key:
    :return:
    """
    for _, client in clients.items():
        await client.send(data, key=key)
