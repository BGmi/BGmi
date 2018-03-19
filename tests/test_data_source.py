# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals

import os
import unittest

from bgmi.config import unicode_
from bgmi.lib.fetch import website


class ControllersTest(unittest.TestCase):
    def setUp(self):
        self.bangumi_name_1 = unicode_(os.environ.get('BANGUMI_1'))
        self.bangumi_name_2 = unicode_(os.environ.get('BANGUMI_2'))
        self.w = website
        pass

    def test_info(self):
        bs, gs = self.w.fetch_bangumi_calendar_and_subtitle_group()
        b = {}
        for bangumi in bs:
            self.assertIn("status", bangumi)
            self.assertIn("subtitle_group", bangumi)
            self.assertIn("name", bangumi)
            self.assertIn("keyword", bangumi)
            self.assertIn("update_time", bangumi)
            self.assertIn("cover", bangumi)
            if bangumi['name'] == self.bangumi_name_1:
                b = bangumi

        for subtitle_group in gs:
            self.assertIn('id', subtitle_group)
            self.assertIn('name', subtitle_group)
        self.assertTrue(bool(b))
        es = self.w.fetch_episode_of_bangumi(b['keyword'])
        for episode in es:
            self.assertIn('download', episode)
            self.assertIn('subtitle_group', episode)
            self.assertIn('title', episode)
            self.assertIn('episode', episode)
            self.assertIn('time', episode)

    def test_search(self):
        r = self.w.search_by_keyword(self.bangumi_name_1)
        for b in r:
            self.assertIn('name', b)
            self.assertIn('download', b)
            self.assertIn('title', b)
            self.assertIn('episode', b)

    # @staticmethod
    # def setUpClass():
    #     setup()
    #     recreate_source_relatively_table()
