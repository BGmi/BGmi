# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import unittest

from bgmi.controllers import *
from bgmi.main import setup
from bgmi.models import Bangumi


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = '时间支配者'
        self.bangumi_name_2 = '哆啦A梦'
        Bangumi.recreate_source_relatively_table()
        pass

    def test_add(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')

    def test_mark(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')

        r = mark(self.bangumi_name_1, 1)
        self.assertEqual(r['status'], 'success')
        r = mark(self.bangumi_name_1, None)
        self.assertEqual(r['status'], 'info')
        r = mark(self.bangumi_name_2, 0)
        self.assertEqual(r['status'], 'error')

    def test_delete(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')
        r = delete()
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_2)
        self.assertEqual(r['status'], 'error')
        r = delete(clear_all=True, batch=True)
        self.assertEqual(r['status'], 'warning')

    def test_cal(self):
        r = cal(force_update=True)
        self.assertIsInstance(r, dict)
        for day in Bangumi.week:
            self.assertIn(day.lower(), r.keys())
            self.assertIsInstance(r[day], list)

    def test_config(self):
        r = config(None, None)
        self.assertEqual(r['status'], 'info')
        r = config('DANMAKU_API_URL', '233')
        self.assertEqual(r['status'], 'success')
        r = config('DATA_SOURCE', '233')
        self.assertEqual(r['status'], 'error')
        r = config('WRONG_CONFIG_NAME', '233')
        self.assertEqual(r['status'], 'error')

    def test_search(self):
        r = search(self.bangumi_name_1, dupe=False)
        # for episode in r:
        #     self.assertNotEqual(episode['title'].find(self.bangumi_name_1), -1)

    def test_download(self):
        pass

    def source(self):
        pass

    @staticmethod
    def setUpClass():
        setup()
