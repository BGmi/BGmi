# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import unittest

from bgmi.lib.controllers import *
from bgmi.main import setup
from bgmi.lib.constants import unicode_


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = unicode_(os.environ.get('BANGUMI_1'))
        self.bangumi_name_2 = unicode_(os.environ.get('BANGUMI_2'))
        pass

    def test_a_cal(self):
        r = cal()
        self.assertIsInstance(r, dict)
        for day in r.keys():
            self.assertIn(day.lower(), [x.lower() for x in Bangumi.week])
            self.assertIsInstance(r[day], list)
            for bangumi in r[day]:
                self.assertIn("status", bangumi)
                self.assertIn("subtitle_group", bangumi)
                self.assertIn("name", bangumi)
                self.assertIn("keyword", bangumi)
                self.assertIn("update_time", bangumi)
                self.assertIn("cover", bangumi)

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

    @staticmethod
    def setUpClass():
        setup()
        recreate_source_relatively_table()
