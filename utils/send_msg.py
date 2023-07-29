#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/28 21:10
# FileName:

import json
import sys
import typing

import requests

import config


def feishu_robot_msg(robot_url: str, content: typing.Union[dict, str], title=None):
    """飞书 机器人消息"""
    try:
        if not robot_url:
            return

        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False)

        msg = {
            'title': title,
            'content': [
                [
                    {
                        'tag': 'text',
                        'text': content
                    }
                ]
            ]
        }

        data = {
            'msg_type': 'post',
            'content': {
                'post': {
                    'zh-cn': msg
                }
            }
        }
        resp = requests.post(robot_url, json=data)
    except Exception:
        pass


class ServerChan:
    """Server酱"""
    def __init__(self, key):
        self.key = key

    @classmethod
    def __check_length(cls, value, max_len):
        if not value:
            return
        if isinstance(value, str):
            assert len(value) < max_len
        elif isinstance(value, int):
            assert value < max_len

    def send_msg(self, title, content='', short=None):
        """

        :param title:
        :param content:
        :param short:
        :return:
        """
        if not self.key:
            return

        check = [
            {'value': title, 'max': 32},
            {'value': sys.getsizeof(title.encode('utf-8')), 'max': 32 * 1024},      # 32KB
            {'value': short, 'max': 64},
        ]
        for item in check:
            self.__check_length(item['value'], item['max'])

        url = f'https://sctapi.ftqq.com/{self.key}.send'

        data = {
            'title': title,
            'short': short,
            'desp': content,
        }
        resp = requests.post(url, data)


def chan_msg(title, content='', short=None, **options):
    key = options.get('key', config.ChanKey)
    return ServerChan(key).send_msg(title, content=content, short=short)


if __name__ == '__main__':
    pass
    # url_ = ''
    # feishu_robot_msg(url_, 'test.content', title='test.title')

    # key_ = ''
    # chan_msg('test.title', 'test.content', key=key_)
