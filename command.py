#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:46
# FileName: 命令行交互

import getopt
import logging
import sys

import config
from module import focus, bean
from module.process import worth
from utils import utils


@bean.sys_exit
def command(cmd, *, money_type, codes: str = None):
    """关注操作"""
    foc = focus.Focus('worth')
    actions = {
        'add': foc.add,
        'get': foc.get,
        'delete': foc.delete,
    }
    assert cmd.lower() in actions, 'command参数错误'

    result, msg = actions[cmd.lower()](money_type, options=[
        {'code': str(code).strip() for code in codes.split(',')}] if codes else [])
    logging.info(msg)


@bean.sys_exit
def search(money_type, *, codes: str = None):
    """查询操作"""
    processor = worth.Worth(money_type, codes=codes)
    logging.info(f'【{processor.title}】{utils.now_time(tz=config.CronZone)}\n\n{processor.get_message()}')


if __name__ == '__main__':
    from utils import log_util

    log_util.init_logging('', datefmt='%Y-%m-%d %H:%M:%S')

    test_money_type = ''
    test_codes = ''
    # test_codes = '600010'
    # test_money_type = 'stock'

    test_cmd = ''

    opts, _ = getopt.getopt(sys.argv[1:], "t:c:", ["type=", "codes=", "command="])
    opts = dict(opts)
    if opts.get("-t"):
        test_money_type = str(opts.get("-t"))
    elif opts.get("--type"):
        test_money_type = str(opts.get("--type"))
    if opts.get("-c"):
        test_codes = str(opts.get("-c"))
    elif opts.get("--code"):
        test_codes = str(opts.get("--code"))

    if opts.get("--command"):
        test_cmd = str(opts.get("--command"))

    if not test_money_type:
        sys.exit('缺少type')

    if test_cmd:
        command(test_cmd, money_type=test_money_type, codes=test_codes)
    else:
        search(test_money_type, codes=test_codes)
