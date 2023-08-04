#!-*- coding:utf-8 -*-
# python3.7
# CreateTime: 2023/8/4 16:23
# FileName: 关注的测试

import unittest

from module import focus


class TestWorth(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.foc = focus.Focus('worth')

    def test_1_add(self):
        ok, _ = self.foc.add('fund', codes=['000001', '000002'])
        self.assertTrue(ok)

    def test_2_get(self):
        data, _ = self.foc.get('fund')
        self.assertIn('000001', data)
        self.assertIn('000002', data)

    def test_3_delete(self):
        ok, _ = self.foc.delete('fund', codes=['000001', '000002'])
        self.assertTrue(ok)


class TestMonitor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.foc = focus.Focus('monitor')

    def test_1_add(self):
        option = {
            'code': '000001',
            'worth': '1.2',
        }
        ok, _ = self.foc.add('fund', option=option)
        self.assertTrue(ok)

        option = {
            'code': '000001',
            'cost': '1',
            'growth': '10',
        }
        ok, _ = self.foc.add('fund', option=option)
        self.assertTrue(ok)

    def test_2_get(self):
        data, _ = self.foc.get('fund')
        print(data)

    # def test_3_delete(self):
    #     ok, _ = self.foc.delete('fund', ids=[])
    #     self.assertTrue(ok)


if __name__ == '__main__':
    unittest.main()
