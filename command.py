#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/7/27 17:46
# FileName: 命令行

import getopt
import sys

from process import action, watch


def command(cmd, *, money_type, codes: str = None):
    actions = {
        'add': watch.add,
        'get': watch.get,
        'delete': watch.delete,
    }

    if cmd.lower() in actions:
        actions[cmd.lower()](money_type, codes=[str(code) for code in codes.split(',')])


def main(money_type, *, codes: str = None):
    action.Process(money_type, codes=codes).main()


if __name__ == '__main__':
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

    assert test_money_type, '缺少type'

    if test_cmd:
        command(test_cmd, money_type=test_money_type, codes=test_codes)
    else:
        main(test_money_type, codes=test_codes)
