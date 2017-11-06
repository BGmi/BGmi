# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import unittest

from bgmi.controllers import *
from bgmi.main import setup, unicode_


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = unicode_(os.environ.get('BANGUMI_1'))
        self.bangumi_name_2 = unicode_(os.environ.get('BANGUMI_2'))
        pass

    def test_a_cal(self):
        r = cal(force_update=True)
        self.assertIsInstance(r, dict)
        for day in Bangumi.week:
            self.assertIn(day.lower(), r.keys())
            self.assertIsInstance(r[day], list)

    def test_b_add(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'warning')
        r = delete(self.bangumi_name_1)
        self.assertEqual(r['status'], 'warning')

    def test_c_mark(self):
        r = add(self.bangumi_name_1, 0)
        self.assertEqual(r['status'], 'success')

        r = mark(self.bangumi_name_1, 1)
        self.assertEqual(r['status'], 'success')
        r = mark(self.bangumi_name_1, None)
        self.assertEqual(r['status'], 'info')
        r = mark(self.bangumi_name_2, 0)
        self.assertEqual(r['status'], 'error')

    def test_d_delete(self):
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

    def test_e_search(self):
        r = search(self.bangumi_name_1, dupe=False)

    def test_config(self):
        r = config(None, None)
        self.assertEqual(r['status'], 'info')
        r = config('DANMAKU_API_URL', '233')
        self.assertEqual(r['status'], 'success')
        r = config('DATA_SOURCE', '233')
        self.assertEqual(r['status'], 'error')
        r = config('WRONG_CONFIG_NAME', '233')
        self.assertEqual(r['status'], 'error')

    def test_download(self):
        pass

    def source(self):
        pass

    @staticmethod
    def setUpClass():
        setup()
        recreate_source_relatively_table()
